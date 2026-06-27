"""Tests for pure proposal-only NDNRA consolidation scheduling."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationScheduleProposal,
    ConsolidationScheduleRequest,
    ConsolidationScheduleStatus,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
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


def _trace(
    index: int,
    *,
    route_id: str,
    transfer_succeeded: bool,
) -> ContextualExperienceTrace:
    assembly_id = "assembly:a" if route_id == "route:a" else "assembly:b"
    return ContextualExperienceTrace(
        identity=EventIdentity("schedule_test", f"episode:{index}", index),
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


def _mastered_ledger() -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    for trace in (
        _trace(0, route_id="route:a", transfer_succeeded=True),
        _trace(1, route_id="route:b", transfer_succeeded=True),
        _trace(2, route_id="route:a", transfer_succeeded=False),
    ):
        ledger.record(trace)
    return ledger


def _request() -> ConsolidationScheduleRequest:
    return ConsolidationScheduleRequest(
        lesson=_LESSON,
        available_assembly_ids=_ASSEMBLIES,
        available_route_ids=_ROUTES,
    )


def test_due_mastery_produces_deterministic_non_authoritative_proposal() -> None:
    ledger = _mastered_ledger()
    before = ledger.snapshot()
    policy = ConsolidationSchedulingPolicy()
    context = ConsolidationSchedulingContext(episode_index=100)

    first = policy.evaluate(ledger=ledger, request=_request(), context=context)
    second = policy.evaluate(ledger=ledger, request=_request(), context=context)

    assert first.status is ConsolidationScheduleStatus.PROPOSED
    assert first.proposed
    assert first.proposal is not None
    assert second.proposal is not None
    assert first.proposal == second.proposal
    assert first.proposal.proposal_id.startswith("consolidation-schedule:")
    assert first.proposal.proposed_episode == 100
    assert first.proposal.due_episode == 100
    assert not first.proposal.has_execution_authority
    assert ledger.snapshot() == before


def test_before_first_window_exposes_eligibility_without_proposing() -> None:
    decision = ConsolidationSchedulingPolicy().evaluate(
        ledger=_mastered_ledger(),
        request=_request(),
        context=ConsolidationSchedulingContext(episode_index=99),
    )

    assert decision.status is ConsolidationScheduleStatus.BEFORE_FIRST_WINDOW
    assert decision.eligibility.eligible
    assert decision.due_episode == 100
    assert not decision.proposed


def test_completed_episode_enforces_explicit_cooldown() -> None:
    policy = ConsolidationSchedulingPolicy(
        first_eligible_episode=20,
        minimum_interval_episodes=50,
    )
    ledger = _mastered_ledger()

    cooling_down = policy.evaluate(
        ledger=ledger,
        request=_request(),
        context=ConsolidationSchedulingContext(
            episode_index=149,
            last_completed_episode=100,
        ),
    )
    due = policy.evaluate(
        ledger=ledger,
        request=_request(),
        context=ConsolidationSchedulingContext(
            episode_index=150,
            last_completed_episode=100,
        ),
    )

    assert cooling_down.status is ConsolidationScheduleStatus.COOLDOWN_ACTIVE
    assert cooling_down.due_episode == 150
    assert due.status is ConsolidationScheduleStatus.PROPOSED
    assert due.proposal is not None
    assert due.proposal.due_episode == 150


def test_due_but_unmastered_lesson_returns_eligibility_reasons() -> None:
    ledger = ContextualExperienceLedger()
    ledger.record(_trace(0, route_id="route:a", transfer_succeeded=True))

    decision = ConsolidationSchedulingPolicy().evaluate(
        ledger=ledger,
        request=_request(),
        context=ConsolidationSchedulingContext(episode_index=100),
    )

    assert decision.status is ConsolidationScheduleStatus.NOT_ELIGIBLE
    assert not decision.eligibility.eligible
    assert decision.eligibility.reasons
    assert decision.proposal is None


def test_active_candidate_is_not_proposed_twice() -> None:
    policy = ConsolidationSchedulingPolicy()
    ledger = _mastered_ledger()
    first = policy.evaluate(
        ledger=ledger,
        request=_request(),
        context=ConsolidationSchedulingContext(episode_index=100),
    )
    assert first.proposal is not None

    repeated = policy.evaluate(
        ledger=ledger,
        request=_request(),
        context=ConsolidationSchedulingContext(
            episode_index=100,
            active_candidate_ids=(first.proposal.candidate.candidate_id,),
        ),
    )

    assert repeated.status is ConsolidationScheduleStatus.CANDIDATE_ALREADY_ACTIVE
    assert repeated.proposal is None


def test_active_capacity_blocks_unrelated_candidate_without_mutation() -> None:
    ledger = _mastered_ledger()
    before = ledger.snapshot()

    decision = ConsolidationSchedulingPolicy(maximum_active_candidates=1).evaluate(
        ledger=ledger,
        request=_request(),
        context=ConsolidationSchedulingContext(
            episode_index=100,
            active_candidate_ids=("consolidation:other",),
        ),
    )

    assert decision.status is ConsolidationScheduleStatus.ACTIVE_CAPACITY_REACHED
    assert decision.eligibility.eligible
    assert decision.proposal is None
    assert ledger.snapshot() == before


def test_context_rejects_future_completion_episode() -> None:
    with pytest.raises(ValueError, match="cannot exceed"):
        ConsolidationSchedulingContext(
            episode_index=99,
            last_completed_episode=100,
        )


def test_schedule_proposal_rejects_execution_authority() -> None:
    decision = ConsolidationSchedulingPolicy().evaluate(
        ledger=_mastered_ledger(),
        request=_request(),
        context=ConsolidationSchedulingContext(episode_index=100),
    )
    assert decision.proposal is not None

    with pytest.raises(ValueError, match="never have execution authority"):
        ConsolidationScheduleProposal(
            proposal_id=decision.proposal.proposal_id,
            candidate=decision.proposal.candidate,
            proposed_episode=decision.proposal.proposed_episode,
            due_episode=decision.proposal.due_episode,
            has_execution_authority=True,
        )


def test_scheduling_module_has_no_timer_executor_sql_or_integration_dependency() -> None:
    path = Path("src/seedmind/research/ndnra/consolidation_scheduling.py")
    source = path.read_text(encoding="utf-8").lower()

    assert "import time" not in source
    assert "datetime" not in source
    assert "sleep(" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "sqlite3" not in source
    assert "consolidation_application" not in source
    assert "seedmind.integration" not in source
    assert "persistence" not in source
