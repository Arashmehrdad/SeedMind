"""Tests for contradiction-driven reopening and atomic consolidation rollback."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationApplicationResult,
    ConsolidationApplicationState,
    ConsolidationEligibility,
    ConsolidationEligibilityPolicy,
    ConsolidationReopeningPolicy,
    ConsolidationReopeningTrigger,
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
    rollback_consolidation,
)

_LESSON = LessonIdentity("reduce_heat", "cooling", 1.0)
_ASSEMBLIES = ("assembly:a", "assembly:b")
_ROUTES = ("route:a", "route:b")


def _trace(
    index: int,
    *,
    route_id: str,
    effect_value: float = 1.0,
    transfer_attempted: bool = True,
    transfer_succeeded: bool = True,
    correlation_group_id: str | None = None,
) -> ContextualExperienceTrace:
    assembly_id = "assembly:a" if route_id == "route:a" else "assembly:b"
    return ContextualExperienceTrace(
        identity=EventIdentity("reopening_test", f"episode:{index}", index),
        correlation_group_id=correlation_group_id or f"group:{index}",
        assembly_id=assembly_id,
        route_id=route_id,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code="reduce_heat",
            sensor_values=(float(index),),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(EffectObservation("cooling", effect_value, 1.0),),
        transfer_attempted=transfer_attempted,
        transfer_succeeded=transfer_succeeded,
    )


def _mastered_ledger() -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    for trace in (
        _trace(0, route_id="route:a", transfer_succeeded=True),
        _trace(1, route_id="route:b", transfer_succeeded=True),
        _trace(2, route_id="route:a", transfer_succeeded=False),
    ):
        ledger.record(trace)
    return ledger


def _eligibility(
    ledger: ContextualExperienceLedger,
    *,
    stability_increment: float = 0.10,
    plasticity_reduction: float = 0.10,
) -> ConsolidationEligibility:
    return ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=ledger.mastery_profile(_LESSON),
        requested_stability_increment=stability_increment,
        requested_plasticity_reduction=plasticity_reduction,
        available_assembly_ids=_ASSEMBLIES,
        available_route_ids=_ROUTES,
    )


def _application(
    ledger: ContextualExperienceLedger,
) -> tuple[ConsolidationApplicationState, ConsolidationApplicationResult]:
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=(*_ASSEMBLIES, "assembly:untouched"),
        route_ids=(*_ROUTES, "route:untouched"),
        initial_stability=0.20,
        initial_plasticity=0.80,
    )
    return state, state.apply(_eligibility(ledger))


def _add_contradiction(
    ledger: ContextualExperienceLedger,
    *,
    value: float = -1.0,
    index: int = 3,
    correlation_group_id: str | None = None,
) -> ContextualExperienceTrace:
    trace = _trace(
        index,
        route_id="route:b",
        effect_value=value,
        transfer_attempted=False,
        transfer_succeeded=False,
        correlation_group_id=correlation_group_id,
    )
    ledger.record(trace)
    return trace


def test_new_independent_contradiction_reopens_without_mutation() -> None:
    ledger = _mastered_ledger()
    eligibility = _eligibility(ledger)
    assert eligibility.candidate is not None
    source_before = ledger.snapshot()
    contradiction = _add_contradiction(ledger)
    evidence_before = ledger.snapshot()

    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=eligibility.candidate,
    )

    assert decision.reopen
    assert decision.triggers == (
        ConsolidationReopeningTrigger.NEW_INDEPENDENT_CONTRADICTION,
        ConsolidationReopeningTrigger.CAUSAL_CONSISTENCY_DROP,
        ConsolidationReopeningTrigger.MASTERY_SCORE_DROP,
    )
    assert decision.new_source_event_ids == (contradiction.identity.key,)
    assert decision.new_contradiction_event_ids == (contradiction.identity.key,)
    assert decision.new_independent_contradiction_count == 1
    assert decision.causal_consistency_drop == pytest.approx(0.25)
    assert decision.mastery_score_drop == pytest.approx(0.05)
    assert ledger.snapshot() == evidence_before
    assert source_before["trace_count"] == 3


def test_positive_new_evidence_does_not_reopen() -> None:
    ledger = _mastered_ledger()
    eligibility = _eligibility(ledger)
    assert eligibility.candidate is not None
    ledger.record(_trace(3, route_id="route:b", effect_value=1.0))

    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=eligibility.candidate,
    )

    assert not decision.reopen
    assert decision.new_independent_contradiction_count == 0
    assert decision.new_contradiction_event_ids == ()
    assert ConsolidationReopeningTrigger.NEW_INDEPENDENT_CONTRADICTION not in decision.triggers


def test_small_contradiction_is_visible_but_below_reopening_threshold() -> None:
    ledger = _mastered_ledger()
    eligibility = _eligibility(ledger)
    assert eligibility.candidate is not None
    contradiction = _add_contradiction(ledger, value=-0.10)

    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=eligibility.candidate,
    )

    assert not decision.reopen
    assert decision.new_contradiction_event_ids == (contradiction.identity.key,)
    assert decision.triggers == (ConsolidationReopeningTrigger.NEW_INDEPENDENT_CONTRADICTION,)
    assert decision.causal_consistency_drop < 0.10
    assert decision.mastery_score_drop < 0.05


def test_correlated_contradiction_copies_do_not_inflate_independent_count() -> None:
    ledger = _mastered_ledger()
    eligibility = _eligibility(ledger)
    assert eligibility.candidate is not None
    _add_contradiction(ledger, index=3, correlation_group_id="group:copied_contradiction")
    _add_contradiction(ledger, index=4, correlation_group_id="group:copied_contradiction")

    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=eligibility.candidate,
    )

    assert decision.reopen
    assert len(decision.new_contradiction_event_ids) == 2
    assert decision.new_independent_contradiction_count == 1


def test_reopening_requires_original_candidate_sources_to_remain_resolvable() -> None:
    original = _mastered_ledger()
    eligibility = _eligibility(original)
    assert eligibility.candidate is not None
    incomplete = ContextualExperienceLedger()
    incomplete.record(_trace(0, route_id="route:a"))
    _add_contradiction(incomplete)

    with pytest.raises(ValueError, match="preserves all consolidation sources"):
        ConsolidationReopeningPolicy().evaluate(
            ledger=incomplete,
            candidate=eligibility.candidate,
        )


def test_rollback_restores_candidate_state_and_preserves_unrelated_state() -> None:
    ledger = _mastered_ledger()
    eligibility = _eligibility(ledger)
    assert eligibility.candidate is not None
    state, application = _application(ledger)
    untouched_before = state.snapshot().assembly_state("assembly:untouched")
    _add_contradiction(ledger)
    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=eligibility.candidate,
    )

    result = rollback_consolidation(
        state=state,
        application=application,
        decision=decision,
    )

    assert result.before == application.after
    assert result.after == state.snapshot()
    assert result.after.assembly_state("assembly:a") == application.before.assembly_state(
        "assembly:a"
    )
    assert result.after.route_state("route:b") == application.before.route_state("route:b")
    assert result.after.assembly_state("assembly:untouched") == untouched_before
    assert application.candidate.candidate_id not in result.after.applied_candidate_ids
    assert result.rollback_id.startswith("rollback:")


def test_rollback_is_deterministic_for_identical_evidence() -> None:
    def execute() -> str:
        ledger = _mastered_ledger()
        eligibility = _eligibility(ledger)
        assert eligibility.candidate is not None
        state, application = _application(ledger)
        _add_contradiction(ledger)
        decision = ConsolidationReopeningPolicy().evaluate(
            ledger=ledger,
            candidate=eligibility.candidate,
        )
        return rollback_consolidation(
            state=state,
            application=application,
            decision=decision,
        ).rollback_id

    assert execute() == execute()


def test_rollback_is_blocked_when_reopening_gate_does_not_pass() -> None:
    ledger = _mastered_ledger()
    eligibility = _eligibility(ledger)
    assert eligibility.candidate is not None
    state, application = _application(ledger)
    _add_contradiction(ledger, value=-0.10)
    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=eligibility.candidate,
    )
    before = state.snapshot()

    with pytest.raises(RuntimeError, match="gate has not passed"):
        rollback_consolidation(
            state=state,
            application=application,
            decision=decision,
        )

    assert state.snapshot() == before


def test_duplicate_rollback_is_blocked_without_further_mutation() -> None:
    ledger = _mastered_ledger()
    eligibility = _eligibility(ledger)
    assert eligibility.candidate is not None
    state, application = _application(ledger)
    _add_contradiction(ledger)
    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=eligibility.candidate,
    )
    rollback_consolidation(state=state, application=application, decision=decision)
    after_first = state.snapshot()

    with pytest.raises(RuntimeError, match="not currently applied"):
        rollback_consolidation(state=state, application=application, decision=decision)

    assert state.snapshot() == after_first


def test_stale_target_state_blocks_rollback_atomically() -> None:
    ledger = _mastered_ledger()
    first_eligibility = _eligibility(ledger)
    assert first_eligibility.candidate is not None
    state, first_application = _application(ledger)
    second_eligibility = _eligibility(
        ledger,
        stability_increment=0.05,
        plasticity_reduction=0.05,
    )
    state.apply(second_eligibility)
    _add_contradiction(ledger)
    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=first_eligibility.candidate,
    )
    before = state.snapshot()

    with pytest.raises(RuntimeError, match="changed after application"):
        rollback_consolidation(
            state=state,
            application=first_application,
            decision=decision,
        )

    assert state.snapshot() == before


def test_mismatched_decision_and_application_are_rejected() -> None:
    ledger = _mastered_ledger()
    first_eligibility = _eligibility(ledger)
    second_eligibility = _eligibility(
        ledger,
        stability_increment=0.05,
        plasticity_reduction=0.05,
    )
    assert first_eligibility.candidate is not None
    assert second_eligibility.candidate is not None
    state, first_application = _application(ledger)
    _add_contradiction(ledger)
    wrong_decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=second_eligibility.candidate,
    )
    before = state.snapshot()

    with pytest.raises(ValueError, match="does not match"):
        rollback_consolidation(
            state=state,
            application=first_application,
            decision=wrong_decision,
        )

    assert state.snapshot() == before


def test_reopening_and_rollback_have_no_sql_or_integration_dependency() -> None:
    files = (
        Path("src/seedmind/research/ndnra/consolidation_reopening.py"),
        Path("src/seedmind/research/ndnra/consolidation_application.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
    assert "seedmind.integration" not in source
    assert "persistence" not in source
