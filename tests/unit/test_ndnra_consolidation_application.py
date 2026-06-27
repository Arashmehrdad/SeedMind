"""Tests for bounded atomic NDNRA consolidation proposal application."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationApplicationState,
    ConsolidationEligibility,
    ConsolidationEligibilityPolicy,
    ConsolidationStateSnapshot,
    ConsolidationStructureState,
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
)

_LESSON = LessonIdentity("reduce_heat", "cooling", 1.0)
_ASSEMBLIES = ("assembly:a", "assembly:b")
_ROUTES = ("route:a", "route:b")


def _trace(index: int, *, route_id: str, transfer_succeeded: bool) -> ContextualExperienceTrace:
    assembly_id = "assembly:a" if route_id == "route:a" else "assembly:b"
    return ContextualExperienceTrace(
        identity=EventIdentity("test", f"episode:{index}", index),
        correlation_group_id=f"group:{index}",
        assembly_id=assembly_id,
        route_id=route_id,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code="reduce_heat",
            sensor_values=(float(index),),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(EffectObservation("cooling", 1.0, 1.0),),
        transfer_attempted=True,
        transfer_succeeded=transfer_succeeded,
    )


def _ledger() -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    for trace in (
        _trace(0, route_id="route:a", transfer_succeeded=True),
        _trace(1, route_id="route:b", transfer_succeeded=True),
        _trace(2, route_id="route:a", transfer_succeeded=False),
    ):
        ledger.record(trace)
    return ledger


def _eligibility() -> ConsolidationEligibility:
    ledger = _ledger()
    return ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=ledger.mastery_profile(_LESSON),
        available_assembly_ids=_ASSEMBLIES,
        available_route_ids=_ROUTES,
    )


def _state() -> ConsolidationApplicationState:
    return ConsolidationApplicationState.from_identifiers(
        assembly_ids=(*_ASSEMBLIES, "assembly:untouched"),
        route_ids=(*_ROUTES, "route:untouched"),
        initial_stability=0.20,
        initial_plasticity=0.80,
    )


def test_eligible_candidate_applies_bounded_changes_and_preserves_evidence() -> None:
    eligibility = _eligibility()
    assert eligibility.candidate is not None
    state = _state()

    result = state.apply(eligibility)

    assert result.candidate == eligibility.candidate
    assert result.candidate.source_event_ids == eligibility.candidate.source_event_ids
    assert result.candidate.assembly_ids == _ASSEMBLIES
    assert result.candidate.route_ids == _ROUTES
    assert result.before.assembly_state("assembly:a").stability == pytest.approx(0.20)
    assert result.after.assembly_state("assembly:a").stability == pytest.approx(0.30)
    assert result.after.assembly_state("assembly:a").plasticity == pytest.approx(0.70)
    assert result.after.route_state("route:b").stability == pytest.approx(0.30)
    assert result.after.route_state("route:b").plasticity == pytest.approx(0.70)
    assert result.after == state.snapshot()
    assert result.candidate.candidate_id in result.after.applied_candidate_ids


def test_non_target_structures_remain_unchanged() -> None:
    state = _state()

    result = state.apply(_eligibility())

    assert result.before.assembly_state("assembly:untouched") == result.after.assembly_state(
        "assembly:untouched"
    )
    assert result.before.route_state("route:untouched") == result.after.route_state(
        "route:untouched"
    )


def test_application_clamps_stability_and_plasticity_to_unit_bounds() -> None:
    state = ConsolidationApplicationState.from_states(
        assembly_states=(
            ConsolidationStructureState("assembly:a", stability=0.95, plasticity=0.05),
            ConsolidationStructureState("assembly:b", stability=0.95, plasticity=0.05),
        ),
        route_states=(
            ConsolidationStructureState("route:a", stability=0.95, plasticity=0.05),
            ConsolidationStructureState("route:b", stability=0.95, plasticity=0.05),
        ),
    )

    result = state.apply(_eligibility())

    for structure_id in _ASSEMBLIES:
        after = result.after.assembly_state(structure_id)
        assert after.stability == 1.0
        assert after.plasticity == 0.0
    for structure_id in _ROUTES:
        after = result.after.route_state(structure_id)
        assert after.stability == 1.0
        assert after.plasticity == 0.0


def test_missing_structure_fails_before_any_mutation() -> None:
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=("assembly:a",),
        route_ids=_ROUTES,
    )
    before = state.snapshot()

    with pytest.raises(ValueError, match="unknown assemblies"):
        state.apply(_eligibility())

    assert state.snapshot() == before


def test_ineligible_result_fails_before_any_mutation() -> None:
    ledger = ContextualExperienceLedger()
    trace = _trace(0, route_id="route:a", transfer_succeeded=True)
    ledger.record(trace)
    eligibility = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=ledger.mastery_profile(_LESSON),
        available_assembly_ids=("assembly:a",),
        available_route_ids=("route:a",),
    )
    state = _state()
    before = state.snapshot()

    with pytest.raises(RuntimeError, match="only an eligible"):
        state.apply(eligibility)

    assert state.snapshot() == before


def test_duplicate_candidate_application_is_blocked_atomically() -> None:
    state = _state()
    eligibility = _eligibility()
    state.apply(eligibility)
    before_duplicate = state.snapshot()

    with pytest.raises(RuntimeError, match="already been applied"):
        state.apply(eligibility)

    assert state.snapshot() == before_duplicate


def test_tampered_request_above_policy_cap_is_rejected_atomically() -> None:
    eligibility = _eligibility()
    assert eligibility.candidate is not None
    tampered_candidate = replace(
        eligibility.candidate,
        requested_stability_increment=0.30,
    )
    tampered = replace(eligibility, candidate=tampered_candidate)
    state = _state()
    before = state.snapshot()

    with pytest.raises(ValueError, match="stability request exceeds"):
        state.apply(tampered)

    assert state.snapshot() == before


def test_tampered_lesson_or_mastery_snapshot_is_rejected() -> None:
    eligibility = _eligibility()
    assert eligibility.candidate is not None
    state = _state()
    before = state.snapshot()

    wrong_lesson = replace(
        eligibility,
        candidate=replace(
            eligibility.candidate,
            lesson_identity=LessonIdentity("reduce_heat", "cooling", -1.0),
        ),
    )
    with pytest.raises(ValueError, match="lesson does not match"):
        state.apply(wrong_lesson)

    wrong_mastery = replace(
        eligibility,
        candidate=replace(
            eligibility.candidate,
            mastery_snapshot=replace(
                eligibility.candidate.mastery_snapshot,
                mastery_score=0.80,
            ),
        ),
    )
    with pytest.raises(ValueError, match="mastery snapshot does not match"):
        state.apply(wrong_mastery)

    assert state.snapshot() == before


def test_registration_rejects_duplicate_or_overlapping_identities() -> None:
    with pytest.raises(ValueError, match="unique identities"):
        ConsolidationApplicationState.from_identifiers(
            assembly_ids=("assembly:a", "assembly:a"),
            route_ids=("route:a",),
        )
    with pytest.raises(ValueError, match="must not overlap"):
        ConsolidationApplicationState.from_identifiers(
            assembly_ids=("shared:id",),
            route_ids=("shared:id",),
        )


def test_snapshot_is_immutable_and_deterministically_ordered() -> None:
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=("assembly:b", "assembly:a"),
        route_ids=("route:b", "route:a"),
    )

    snapshot = state.snapshot()

    assert isinstance(snapshot, ConsolidationStateSnapshot)
    assert tuple(item.structure_id for item in snapshot.assembly_states) == _ASSEMBLIES
    assert tuple(item.structure_id for item in snapshot.route_states) == _ROUTES


def test_consolidation_application_has_no_sqlite_or_replay_dependency() -> None:
    path = Path("src/seedmind/research/ndnra/consolidation_application.py")
    source = path.read_text(encoding="utf-8").lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
    assert "from seedmind.research.ndnra.replay" not in source
    assert ".replay(" not in source
