"""Tests for immutable NDNRA consolidation proposal lifecycle history."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationProposalLifecycleRecord,
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewAction,
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

_HEAT = LessonIdentity("reduce_heat", "cooling", 1.0)
_CLEAN = LessonIdentity("remove_dirt", "cleanliness", 1.0)


def _proposal(
    *,
    prefix: str = "heat",
    lesson: LessonIdentity = _HEAT,
    proposed_episode: int = 100,
) -> ConsolidationScheduleProposal:
    ledger = ContextualExperienceLedger()
    assemblies = (f"assembly:{prefix}:a", f"assembly:{prefix}:b")
    routes = (f"route:{prefix}:a", f"route:{prefix}:b")
    for index, route_id, transfer_succeeded in (
        (0, routes[0], True),
        (1, routes[1], True),
        (2, routes[0], False),
    ):
        assembly_id = assemblies[0] if route_id == routes[0] else assemblies[1]
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity(
                    "history_test",
                    f"episode:{prefix}:{index}",
                    index,
                ),
                correlation_group_id=f"group:{prefix}:{index}",
                assembly_id=assembly_id,
                route_id=route_id,
                action_code=f"action:{prefix}",
                context=ContextSignature.from_values(
                    active_need_code=lesson.need_code,
                    sensor_values=(float(index),),
                    available_action_codes=(f"action:{prefix}", "wait"),
                ),
                observed_effects=(
                    EffectObservation(
                        lesson.effect_code,
                        lesson.desired_direction,
                        1.0,
                    ),
                ),
                transfer_attempted=True,
                transfer_succeeded=transfer_succeeded,
            )
        )
    schedule = ConsolidationSchedulingPolicy(
        first_eligible_episode=proposed_episode,
    ).evaluate(
        ledger=ledger,
        request=ConsolidationScheduleRequest(
            lesson=lesson,
            available_assembly_ids=assemblies,
            available_route_ids=routes,
        ),
        context=ConsolidationSchedulingContext(episode_index=proposed_episode),
    )
    assert schedule.proposal is not None
    return schedule.proposal


def _request(
    proposal: ConsolidationScheduleProposal,
    *,
    action: ConsolidationProposalReviewAction,
    decision_episode: int,
    reason_code: str,
    defer_until_episode: int | None = None,
) -> ConsolidationProposalReviewRequest:
    return ConsolidationProposalReviewRequest(
        proposal=proposal,
        action=action,
        decision_episode=decision_episode,
        reviewer_code="human:operator",
        reason_code=reason_code,
        defer_until_episode=defer_until_episode,
    )


def test_pending_record_preserves_original_proposal_without_authority() -> None:
    proposal = _proposal()

    record = ConsolidationProposalLifecycleRecord.pending(proposal)

    assert record.proposal is proposal
    assert record.status is ConsolidationProposalLifecycleStatus.PENDING
    assert record.decisions == ()
    assert record.current_defer_until_episode is None
    assert not record.has_execution_authority


def test_accept_returns_new_record_and_preserves_pending_record() -> None:
    proposal = _proposal()
    pending = ConsolidationProposalLifecycleRecord.pending(proposal)

    accepted = pending.review(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=101,
            reason_code="evidence_review_passed",
        )
    )

    assert pending.status is ConsolidationProposalLifecycleStatus.PENDING
    assert pending.decisions == ()
    assert accepted.status is ConsolidationProposalLifecycleStatus.ACCEPTED
    assert len(accepted.decisions) == 1
    assert accepted.decisions[0].proposal is proposal
    assert not accepted.has_execution_authority


def test_rejected_and_accepted_records_are_terminal() -> None:
    proposal = _proposal()
    pending = ConsolidationProposalLifecycleRecord.pending(proposal)
    rejected = pending.review(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.REJECT,
            decision_episode=101,
            reason_code="insufficient_evidence",
        )
    )
    accepted = pending.review(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=101,
            reason_code="evidence_review_passed",
        )
    )

    for record in (rejected, accepted):
        with pytest.raises(ValueError, match="terminal"):
            record.review(
                _request(
                    proposal,
                    action=ConsolidationProposalReviewAction.DEFER,
                    decision_episode=102,
                    reason_code="conflicting_review",
                    defer_until_episode=120,
                )
            )


def test_deferred_record_can_be_reviewed_at_due_episode() -> None:
    proposal = _proposal()
    pending = ConsolidationProposalLifecycleRecord.pending(proposal)
    deferred = pending.review(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=101,
            reason_code="collect_more_contexts",
            defer_until_episode=120,
        )
    )

    accepted = deferred.review(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=120,
            reason_code="additional_evidence_passed",
        )
    )

    assert deferred.status is ConsolidationProposalLifecycleStatus.DEFERRED
    assert deferred.current_defer_until_episode == 120
    assert accepted.status is ConsolidationProposalLifecycleStatus.ACCEPTED
    assert accepted.current_defer_until_episode is None
    assert len(accepted.decisions) == 2
    assert accepted.decisions[:1] == deferred.decisions


def test_deferred_record_rejects_early_or_non_increasing_review() -> None:
    proposal = _proposal()
    deferred = ConsolidationProposalLifecycleRecord.pending(proposal).review(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=101,
            reason_code="collect_more_contexts",
            defer_until_episode=120,
        )
    )

    with pytest.raises(ValueError, match="before its review episode"):
        deferred.review(
            _request(
                proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=119,
                reason_code="too_early",
            )
        )
    with pytest.raises(ValueError, match="increase strictly"):
        deferred.review(
            _request(
                proposal,
                action=ConsolidationProposalReviewAction.REJECT,
                decision_episode=101,
                reason_code="same_episode",
            )
        )


def test_record_rejects_review_for_different_proposal() -> None:
    heat_proposal = _proposal()
    clean_proposal = _proposal(prefix="clean", lesson=_CLEAN)
    record = ConsolidationProposalLifecycleRecord.pending(heat_proposal)

    with pytest.raises(ValueError, match="does not match"):
        record.review(
            _request(
                clean_proposal,
                action=ConsolidationProposalReviewAction.REJECT,
                decision_episode=101,
                reason_code="wrong_proposal",
            )
        )


def test_constructor_rejects_duplicate_or_terminal_successor_history() -> None:
    proposal = _proposal()
    policy = ConsolidationProposalReviewPolicy()
    deferred = policy.evaluate(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=101,
            reason_code="collect_more_contexts",
            defer_until_episode=120,
        )
    )
    accepted = policy.evaluate(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=120,
            reason_code="evidence_review_passed",
        )
    )
    rejected = policy.evaluate(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.REJECT,
            decision_episode=130,
            reason_code="conflicting_terminal_review",
        )
    )

    with pytest.raises(ValueError, match="duplicate decision"):
        ConsolidationProposalLifecycleRecord(
            proposal=proposal,
            status=ConsolidationProposalLifecycleStatus.DEFERRED,
            decisions=(deferred, deferred),
        )
    with pytest.raises(ValueError, match="terminal lifecycle decisions"):
        ConsolidationProposalLifecycleRecord(
            proposal=proposal,
            status=ConsolidationProposalLifecycleStatus.REJECTED,
            decisions=(deferred, accepted, rejected),
        )


def test_constructor_rejects_status_mismatch_and_early_reconstruction() -> None:
    proposal = _proposal()
    policy = ConsolidationProposalReviewPolicy()
    deferred = policy.evaluate(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=101,
            reason_code="collect_more_contexts",
            defer_until_episode=120,
        )
    )
    accepted_too_early = policy.evaluate(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=119,
            reason_code="too_early",
        )
    )

    with pytest.raises(ValueError, match="status must match"):
        ConsolidationProposalLifecycleRecord(
            proposal=proposal,
            status=ConsolidationProposalLifecycleStatus.REJECTED,
            decisions=(deferred,),
        )
    with pytest.raises(ValueError, match="too early"):
        ConsolidationProposalLifecycleRecord(
            proposal=proposal,
            status=ConsolidationProposalLifecycleStatus.ACCEPTED,
            decisions=(deferred, accepted_too_early),
        )


def test_lifecycle_snapshot_preserves_complete_ascii_history() -> None:
    proposal = _proposal()
    deferred = ConsolidationProposalLifecycleRecord.pending(proposal).review(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=101,
            reason_code="collect_more_contexts",
            defer_until_episode=120,
        )
    )
    accepted = deferred.review(
        _request(
            proposal,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=120,
            reason_code="additional_evidence_passed",
        )
    )

    snapshot = accepted.snapshot()

    assert snapshot["proposal"] == proposal.snapshot()
    assert snapshot["status"] == "accepted"
    assert snapshot["decisions"] == tuple(decision.snapshot() for decision in accepted.decisions)
    assert snapshot["has_execution_authority"] is False
    assert str(snapshot).isascii()


def test_history_module_has_no_execution_persistence_timer_or_sql_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_proposal_history.py")
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
