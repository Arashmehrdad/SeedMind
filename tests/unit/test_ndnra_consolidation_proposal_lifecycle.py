"""Tests for pure review-only consolidation proposal lifecycle decisions."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewDecision,
    ConsolidationProposalReviewPolicy,
    ConsolidationProposalReviewRequest,
    ConsolidationScheduleProposal,
    ConsolidationScheduleRequest,
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


def _proposal() -> tuple[ContextualExperienceLedger, ConsolidationScheduleProposal]:
    ledger = ContextualExperienceLedger()
    for index, route_id, transfer_succeeded in (
        (0, "route:a", True),
        (1, "route:b", True),
        (2, "route:a", False),
    ):
        assembly_id = "assembly:a" if route_id == "route:a" else "assembly:b"
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity("review_test", f"episode:{index}", index),
                correlation_group_id=f"group:{index}",
                assembly_id=assembly_id,
                route_id=route_id,
                action_code="cool",
                context=ContextSignature.from_values(
                    active_need_code=_LESSON.need_code,
                    sensor_values=(float(index),),
                    available_action_codes=("cool", "wait"),
                ),
                observed_effects=(EffectObservation(_LESSON.effect_code, 1.0, 1.0),),
                transfer_attempted=True,
                transfer_succeeded=transfer_succeeded,
            )
        )
    decision = ConsolidationSchedulingPolicy().evaluate(
        ledger=ledger,
        request=ConsolidationScheduleRequest(
            lesson=_LESSON,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        ),
        context=ConsolidationSchedulingContext(episode_index=100),
    )
    assert decision.proposal is not None
    return ledger, decision.proposal


def test_accept_is_deterministic_and_non_authoritative() -> None:
    ledger, proposal = _proposal()
    before_ledger = ledger.snapshot()
    before_proposal = proposal.snapshot()
    request = ConsolidationProposalReviewRequest(
        proposal=proposal,
        action=ConsolidationProposalReviewAction.ACCEPT,
        decision_episode=101,
        reviewer_code="human:operator",
        reason_code="evidence_review_passed",
    )
    policy = ConsolidationProposalReviewPolicy()

    first = policy.evaluate(request)
    second = policy.evaluate(request)

    assert first == second
    assert first.decision_id.startswith("consolidation-review:")
    assert first.status is ConsolidationProposalLifecycleStatus.ACCEPTED
    assert first.accepted_for_future_consideration
    assert not first.has_execution_authority
    assert first.proposal.snapshot() == before_proposal
    assert ledger.snapshot() == before_ledger


def test_reject_preserves_proposal_and_reason() -> None:
    _, proposal = _proposal()

    decision = ConsolidationProposalReviewPolicy().evaluate(
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.REJECT,
            decision_episode=102,
            reviewer_code="policy:review",
            reason_code="insufficient_operational_evidence",
        )
    )

    assert decision.status is ConsolidationProposalLifecycleStatus.REJECTED
    assert decision.reason_code == "insufficient_operational_evidence"
    assert decision.proposal is proposal
    assert not decision.accepted_for_future_consideration


def test_defer_requires_future_review_episode() -> None:
    _, proposal = _proposal()

    decision = ConsolidationProposalReviewPolicy().evaluate(
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=103,
            reviewer_code="human:operator",
            reason_code="collect_more_contexts",
            defer_until_episode=150,
        )
    )

    assert decision.status is ConsolidationProposalLifecycleStatus.DEFERRED
    assert decision.defer_until_episode == 150
    assert not decision.has_execution_authority

    with pytest.raises(ValueError, match="requires defer_until_episode"):
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=103,
            reviewer_code="human:operator",
            reason_code="collect_more_contexts",
        )
    with pytest.raises(ValueError, match="must follow"):
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=103,
            reviewer_code="human:operator",
            reason_code="collect_more_contexts",
            defer_until_episode=103,
        )


def test_non_deferred_review_rejects_defer_episode() -> None:
    _, proposal = _proposal()

    with pytest.raises(ValueError, match="only deferred review"):
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=101,
            reviewer_code="human:operator",
            reason_code="evidence_review_passed",
            defer_until_episode=150,
        )


def test_review_cannot_precede_proposal() -> None:
    _, proposal = _proposal()

    with pytest.raises(ValueError, match="cannot precede"):
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.REJECT,
            decision_episode=99,
            reviewer_code="policy:review",
            reason_code="invalid_timing",
        )


def test_review_decision_rejects_execution_authority_and_status_mismatch() -> None:
    _, proposal = _proposal()
    accepted = ConsolidationProposalReviewPolicy().evaluate(
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=101,
            reviewer_code="human:operator",
            reason_code="evidence_review_passed",
        )
    )

    with pytest.raises(ValueError, match="never have execution authority"):
        ConsolidationProposalReviewDecision(
            decision_id=accepted.decision_id,
            proposal=proposal,
            action=accepted.action,
            status=accepted.status,
            decision_episode=accepted.decision_episode,
            reviewer_code=accepted.reviewer_code,
            reason_code=accepted.reason_code,
            has_execution_authority=True,
        )
    with pytest.raises(ValueError, match="inconsistent"):
        ConsolidationProposalReviewDecision(
            decision_id=accepted.decision_id,
            proposal=proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            status=ConsolidationProposalLifecycleStatus.REJECTED,
            decision_episode=accepted.decision_episode,
            reviewer_code=accepted.reviewer_code,
            reason_code=accepted.reason_code,
        )


def test_review_snapshot_is_ascii_inspectable() -> None:
    _, proposal = _proposal()
    decision = ConsolidationProposalReviewPolicy().evaluate(
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=103,
            reviewer_code="human:operator",
            reason_code="collect_more_contexts",
            defer_until_episode=150,
        )
    )

    snapshot = decision.snapshot()

    assert snapshot["proposal"] == proposal.snapshot()
    assert snapshot["status"] == "deferred"
    assert snapshot["has_execution_authority"] is False
    assert str(snapshot).isascii()


def test_review_module_has_no_execution_timer_persistence_or_sql_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_proposal_lifecycle.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "consolidation_application" not in source
    assert "rollback_consolidation" not in source
    assert ".apply(" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert "seedmind.integration" not in source
