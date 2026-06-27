"""Tests for pure retention-gated NDNRA consolidation eligibility."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationEligibility,
    ConsolidationEligibilityPolicy,
    ConsolidationRejectionReason,
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
)

_LESSON = LessonIdentity("reduce_heat", "cooling", 1.0)


def _trace(
    index: int,
    *,
    correlation_group_id: str | None = None,
    sensor_value: float | None = None,
    route_id: str | None = None,
    effect_value: float = 1.0,
    transfer_attempted: bool = True,
    transfer_succeeded: bool = True,
) -> ContextualExperienceTrace:
    route = route_id or ("route:a" if index % 2 == 0 else "route:b")
    assembly = "assembly:a" if route == "route:a" else "assembly:b"
    return ContextualExperienceTrace(
        identity=EventIdentity("test", f"episode:{index}", index),
        correlation_group_id=correlation_group_id or f"group:{index}",
        assembly_id=assembly,
        route_id=route,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code="reduce_heat",
            sensor_values=(float(index) if sensor_value is None else sensor_value,),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(EffectObservation("cooling", effect_value, 1.0),),
        transfer_attempted=transfer_attempted,
        transfer_succeeded=transfer_succeeded,
    )


def _ledger(*traces: ContextualExperienceTrace) -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    for trace in traces:
        ledger.record(trace)
    return ledger


def _valid_ledger() -> ContextualExperienceLedger:
    return _ledger(
        _trace(0, route_id="route:a", transfer_succeeded=True),
        _trace(1, route_id="route:b", transfer_succeeded=True),
        _trace(2, route_id="route:a", transfer_succeeded=False),
    )


def _evaluate(
    ledger: ContextualExperienceLedger,
    *,
    requested_stability_increment: float = 0.10,
    requested_plasticity_reduction: float = 0.10,
    available_assembly_ids: Iterable[str] | None = None,
    available_route_ids: Iterable[str] | None = None,
) -> ConsolidationEligibility:
    profile = ledger.mastery_profile(_LESSON)
    return ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=profile,
        requested_stability_increment=requested_stability_increment,
        requested_plasticity_reduction=requested_plasticity_reduction,
        available_assembly_ids=available_assembly_ids,
        available_route_ids=available_route_ids,
    )


def test_broad_mastery_is_eligible_deterministic_and_pure() -> None:
    ledger = _valid_ledger()
    profile = ledger.mastery_profile(_LESSON)
    before = ledger.snapshot()
    assemblies = ("assembly:a", "assembly:b")
    routes = ("route:a", "route:b")
    policy = ConsolidationEligibilityPolicy()

    first = policy.evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=profile,
        available_assembly_ids=assemblies,
        available_route_ids=routes,
    )
    second = policy.evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=profile,
        available_assembly_ids=assemblies,
        available_route_ids=routes,
    )

    assert first.eligible
    assert first.reasons == ()
    assert first.candidate is not None
    assert second.candidate is not None
    assert first.candidate.candidate_id == second.candidate.candidate_id
    assert first.candidate.source_event_ids == tuple(sorted(profile.source_event_ids))
    assert first.candidate.assembly_ids == assemblies
    assert first.candidate.route_ids == routes
    assert first.candidate.requested_stability_increment == 0.10
    assert first.candidate.requested_plasticity_reduction == 0.10
    assert ledger.snapshot() == before
    assert ledger.mastery_profile(_LESSON) == profile
    assert assemblies == ("assembly:a", "assembly:b")
    assert routes == ("route:a", "route:b")


def test_copied_replay_volume_does_not_qualify_as_independent_support() -> None:
    replay = _ledger(
        *(
            _trace(
                index,
                correlation_group_id="group:copied",
                sensor_value=1.0,
                route_id="route:a",
            )
            for index in range(6)
        )
    )

    result = _evaluate(replay)

    assert replay.trace_count == 6
    assert replay.mastery_profile(_LESSON).effective_support == 1.0
    assert not result.eligible
    assert ConsolidationRejectionReason.NOT_BROADLY_MASTERED in result.reasons
    assert ConsolidationRejectionReason.INSUFFICIENT_EFFECTIVE_SUPPORT in result.reasons
    assert ConsolidationRejectionReason.INSUFFICIENT_CONTEXT_DIVERSITY in result.reasons
    assert ConsolidationRejectionReason.INSUFFICIENT_ROUTE_DIVERSITY in result.reasons


def test_one_shot_protection_is_not_broad_consolidation_mastery() -> None:
    ledger = _ledger(_trace(0, effect_value=1.0))
    profile = ledger.mastery_profile(_LESSON)

    result = _evaluate(ledger)

    assert profile.protective_strength == 1.0
    assert not profile.broad_mastery
    assert not result.eligible
    assert ConsolidationRejectionReason.NOT_BROADLY_MASTERED in result.reasons
    assert ConsolidationRejectionReason.INSUFFICIENT_EFFECTIVE_SUPPORT in result.reasons


def test_single_context_repetition_is_rejected() -> None:
    ledger = _ledger(
        _trace(0, sensor_value=1.0, route_id="route:a"),
        _trace(1, sensor_value=1.0, route_id="route:b"),
        _trace(2, sensor_value=1.0, route_id="route:a"),
    )

    result = _evaluate(ledger)

    assert ledger.mastery_profile(_LESSON).unique_context_count == 1
    assert ConsolidationRejectionReason.INSUFFICIENT_CONTEXT_DIVERSITY in result.reasons


def test_single_route_learning_is_rejected() -> None:
    ledger = _ledger(
        _trace(0, route_id="route:a"),
        _trace(1, route_id="route:a"),
        _trace(2, route_id="route:a"),
    )

    result = _evaluate(ledger)

    assert ledger.mastery_profile(_LESSON).unique_route_count == 1
    assert ConsolidationRejectionReason.INSUFFICIENT_ROUTE_DIVERSITY in result.reasons


def test_low_causal_consistency_and_contradictions_are_rejected() -> None:
    ledger = _ledger(
        _trace(0, route_id="route:a"),
        _trace(1, route_id="route:b"),
        _trace(2, route_id="route:a"),
        _trace(3, route_id="route:b", effect_value=-1.0),
        _trace(4, route_id="route:a", effect_value=-1.0),
    )
    profile = ledger.mastery_profile(_LESSON)

    result = _evaluate(ledger)

    assert profile.causal_consistency == pytest.approx(0.60)
    assert profile.contradiction_count == 2
    assert ConsolidationRejectionReason.LOW_CAUSAL_CONSISTENCY in result.reasons
    assert ConsolidationRejectionReason.UNRESOLVED_CONTRADICTIONS in result.reasons


def test_failed_transfer_is_rejected() -> None:
    ledger = _ledger(
        _trace(0, route_id="route:a", transfer_succeeded=False),
        _trace(1, route_id="route:b", transfer_succeeded=False),
        _trace(2, route_id="route:a", transfer_succeeded=False),
    )

    result = _evaluate(ledger)

    assert ledger.mastery_profile(_LESSON).transfer_success == 0.0
    assert ConsolidationRejectionReason.LOW_TRANSFER_SUCCESS in result.reasons


def test_supplied_mastery_fields_are_revalidated() -> None:
    ledger = _valid_ledger()
    profile = ledger.mastery_profile(_LESSON)
    cases = (
        (
            replace(profile, broad_mastery=False),
            ConsolidationRejectionReason.NOT_BROADLY_MASTERED,
        ),
        (
            replace(profile, effective_support=2.99),
            ConsolidationRejectionReason.INSUFFICIENT_EFFECTIVE_SUPPORT,
        ),
        (
            replace(profile, unique_context_count=2),
            ConsolidationRejectionReason.INSUFFICIENT_CONTEXT_DIVERSITY,
        ),
        (
            replace(profile, unique_route_count=1),
            ConsolidationRejectionReason.INSUFFICIENT_ROUTE_DIVERSITY,
        ),
        (
            replace(profile, causal_consistency=0.74),
            ConsolidationRejectionReason.LOW_CAUSAL_CONSISTENCY,
        ),
        (
            replace(profile, transfer_success=0.49),
            ConsolidationRejectionReason.LOW_TRANSFER_SUCCESS,
        ),
        (
            replace(profile, mastery_score=0.74),
            ConsolidationRejectionReason.LOW_MASTERY_SCORE,
        ),
        (
            replace(profile, contradiction_count=1),
            ConsolidationRejectionReason.UNRESOLVED_CONTRADICTIONS,
        ),
    )

    for supplied_profile, reason in cases:
        result = ConsolidationEligibilityPolicy().evaluate(
            ledger=ledger,
            lesson=_LESSON,
            mastery_profile=supplied_profile,
        )
        assert not result.eligible
        assert reason in result.reasons


def test_missing_and_duplicate_source_events_are_rejected() -> None:
    ledger = _valid_ledger()
    profile = ledger.mastery_profile(_LESSON)
    missing = replace(profile, source_event_ids=())
    duplicate = replace(
        profile,
        source_event_ids=(profile.source_event_ids[0], *profile.source_event_ids),
    )

    missing_result = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=missing,
    )
    duplicate_result = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=duplicate,
    )

    assert ConsolidationRejectionReason.MISSING_SOURCE_EVENTS in missing_result.reasons
    assert ConsolidationRejectionReason.DUPLICATE_SOURCE_EVENTS in duplicate_result.reasons


def test_unknown_or_unrelated_source_event_is_rejected() -> None:
    ledger = _valid_ledger()
    profile = ledger.mastery_profile(_LESSON)
    unknown = replace(
        profile,
        source_event_ids=(*profile.source_event_ids[:-1], "unknown:event"),
    )

    result = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=unknown,
    )

    assert ConsolidationRejectionReason.MISSING_SOURCE_EVENTS in result.reasons


def test_missing_assembly_and_route_registrations_are_rejected() -> None:
    ledger = _valid_ledger()
    profile = ledger.mastery_profile(_LESSON)
    policy = ConsolidationEligibilityPolicy()

    missing_assembly = policy.evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=profile,
        available_assembly_ids=("assembly:a",),
        available_route_ids=("route:a", "route:b"),
    )
    missing_route = policy.evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=profile,
        available_assembly_ids=("assembly:a", "assembly:b"),
        available_route_ids=("route:a",),
    )

    assert ConsolidationRejectionReason.MISSING_ASSEMBLIES in missing_assembly.reasons
    assert ConsolidationRejectionReason.MISSING_ROUTES in missing_route.reasons


@pytest.mark.parametrize("value", [0.0, -0.1, 0.21, float("inf"), float("nan")])
def test_invalid_stability_requests_are_rejected(value: float) -> None:
    result = _evaluate(_valid_ledger(), requested_stability_increment=value)

    assert ConsolidationRejectionReason.INVALID_STABILITY_REQUEST in result.reasons


@pytest.mark.parametrize("value", [0.0, -0.1, 0.21, float("inf"), float("nan")])
def test_invalid_plasticity_requests_are_rejected(value: float) -> None:
    result = _evaluate(_valid_ledger(), requested_plasticity_reduction=value)

    assert ConsolidationRejectionReason.INVALID_PLASTICITY_REQUEST in result.reasons


def test_non_finite_mastery_fields_cannot_bypass_the_gate() -> None:
    ledger = _valid_ledger()
    profile = replace(
        ledger.mastery_profile(_LESSON),
        effective_support=float("nan"),
        causal_consistency=float("inf"),
    )

    result = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=profile,
    )

    assert ConsolidationRejectionReason.INSUFFICIENT_EFFECTIVE_SUPPORT in result.reasons
    assert ConsolidationRejectionReason.LOW_CAUSAL_CONSISTENCY in result.reasons


def test_consolidation_eligibility_has_no_sqlite_cognitive_dependency() -> None:
    path = Path("src/seedmind/research/ndnra/consolidation.py")
    source = path.read_text(encoding="utf-8").lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
