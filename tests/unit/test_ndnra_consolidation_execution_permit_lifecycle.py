"""Tests for immutable NDNRA execution-permit lifecycle state."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationExecutionApprovalPolicy,
    ConsolidationExecutionApprovalRequest,
    ConsolidationExecutionPermit,
    ConsolidationExecutionPermitLifecycleAction,
    ConsolidationExecutionPermitLifecycleRecord,
    ConsolidationExecutionPermitLifecycleRegistry,
    ConsolidationExecutionPermitLifecycleStatus,
    ConsolidationExecutionPermitTransitionRequest,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalReviewAction,
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
_ASSEMBLIES = ("assembly:heat:a", "assembly:heat:b")
_ROUTES = ("route:heat:a", "route:heat:b")


def _trace(index: int) -> ContextualExperienceTrace:
    route_id = _ROUTES[index % 2]
    assembly_id = _ASSEMBLIES[0] if route_id == _ROUTES[0] else _ASSEMBLIES[1]
    return ContextualExperienceTrace(
        identity=EventIdentity("permit_lifecycle_test", "episode:mastery", index),
        correlation_group_id=f"group:permit-lifecycle:{index}",
        assembly_id=assembly_id,
        route_id=route_id,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code=_LESSON.need_code,
            sensor_values=(float(index), float(index + 1)),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(EffectObservation(_LESSON.effect_code, 1.0, 1.0),),
        transfer_attempted=True,
        transfer_succeeded=index < 2,
    )


def _ledger() -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    for index in range(3):
        ledger.record(_trace(index))
    return ledger


def _proposal(ledger: ContextualExperienceLedger) -> ConsolidationScheduleProposal:
    decision = ConsolidationSchedulingPolicy(
        first_eligible_episode=100,
        minimum_interval_episodes=1,
    ).evaluate(
        ledger=ledger,
        request=ConsolidationScheduleRequest(
            lesson=_LESSON,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        ),
        context=ConsolidationSchedulingContext(episode_index=100),
    )
    assert decision.proposal is not None
    return decision.proposal


def _accepted_registry(
    proposal: ConsolidationScheduleProposal,
) -> ConsolidationProposalLifecycleRegistry:
    return (
        ConsolidationProposalLifecycleRegistry()
        .add(proposal)
        .review(
            ConsolidationProposalReviewRequest(
                proposal=proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=101,
                reviewer_code="human:reviewer",
                reason_code="proposal_review_passed",
            )
        )
    )


def _permit(*, reason_code: str = "approve_bounded_consolidation") -> ConsolidationExecutionPermit:
    ledger = _ledger()
    proposal_registry = _accepted_registry(_proposal(ledger))
    record = proposal_registry.active_records[0]
    return ConsolidationExecutionApprovalPolicy().evaluate(
        request=ConsolidationExecutionApprovalRequest(
            target_proposal_id=record.proposal.proposal_id,
            expected_candidate_id=record.proposal.candidate.candidate_id,
            expected_review_decision_id=record.lifecycle.decisions[-1].decision_id,
            approval_episode=102,
            expires_after_episode=103,
            approver_code="human:operator",
            reason_code=reason_code,
        ),
        record=record,
        ledger=ledger,
        available_assembly_ids=_ASSEMBLIES,
        available_route_ids=_ROUTES,
    )


def _request(
    permit: ConsolidationExecutionPermit,
    action: ConsolidationExecutionPermitLifecycleAction,
    *,
    decision_episode: int,
    actor_code: str = "human:operator",
    reason_code: str = "permit_transition",
    consumption_reference_code: str | None = None,
) -> ConsolidationExecutionPermitTransitionRequest:
    return ConsolidationExecutionPermitTransitionRequest(
        target_permit_id=permit.permit_id,
        expected_proposal_id=permit.proposal.proposal_id,
        expected_candidate_id=permit.proposal.candidate.candidate_id,
        action=action,
        decision_episode=decision_episode,
        actor_code=actor_code,
        reason_code=reason_code,
        consumption_reference_code=consumption_reference_code,
    )


def test_issued_record_is_immutable_and_non_authoritative() -> None:
    permit = _permit()

    record = ConsolidationExecutionPermitLifecycleRecord.issued(permit)

    assert record.permit == permit
    assert record.status is ConsolidationExecutionPermitLifecycleStatus.ISSUED
    assert record.decisions == ()
    assert not record.is_terminal
    assert record.consumption_count == 0
    assert not record.has_application_authority
    assert record.snapshot()["status"] == "issued"
    assert permit.consumed is False
    assert permit.application_count == 0


def test_cancel_transition_is_terminal_and_preserves_issued_record() -> None:
    permit = _permit()
    issued = ConsolidationExecutionPermitLifecycleRecord.issued(permit)

    cancelled = issued.transition(
        _request(
            permit,
            ConsolidationExecutionPermitLifecycleAction.CANCEL,
            decision_episode=103,
            reason_code="human_cancelled_before_commit",
        )
    )

    assert issued.status is ConsolidationExecutionPermitLifecycleStatus.ISSUED
    assert issued.decisions == ()
    assert cancelled.status is ConsolidationExecutionPermitLifecycleStatus.CANCELLED
    assert cancelled.is_terminal
    assert cancelled.consumption_count == 0
    assert len(cancelled.decisions) == 1
    assert cancelled.decisions[0].action is ConsolidationExecutionPermitLifecycleAction.CANCEL
    assert cancelled.decisions[0].consumption_reference_code is None
    assert not cancelled.decisions[0].has_application_authority


def test_consume_transition_is_single_use_and_requires_reference() -> None:
    permit = _permit()
    issued = ConsolidationExecutionPermitLifecycleRecord.issued(permit)

    with pytest.raises(ValueError, match="requires consumption_reference_code"):
        _request(
            permit,
            ConsolidationExecutionPermitLifecycleAction.CONSUME,
            decision_episode=103,
        )

    consumed = issued.transition(
        _request(
            permit,
            ConsolidationExecutionPermitLifecycleAction.CONSUME,
            decision_episode=103,
            actor_code="execution:bounded_commit",
            reason_code="bounded_commit_recorded",
            consumption_reference_code="commit:consolidation:001",
        )
    )

    assert consumed.status is ConsolidationExecutionPermitLifecycleStatus.CONSUMED
    assert consumed.consumption_count == 1
    assert consumed.decisions[0].consumption_reference_code == "commit:consolidation:001"
    assert permit.consumed is False
    assert permit.application_count == 0
    with pytest.raises(ValueError, match="already terminal"):
        consumed.transition(
            _request(
                permit,
                ConsolidationExecutionPermitLifecycleAction.CONSUME,
                decision_episode=103,
                actor_code="execution:bounded_commit",
                reason_code="duplicate_commit_attempt",
                consumption_reference_code="commit:consolidation:002",
            )
        )


def test_expiry_requires_episode_after_validity_window() -> None:
    permit = _permit()
    issued = ConsolidationExecutionPermitLifecycleRecord.issued(permit)

    with pytest.raises(ValueError, match="only after its validity window"):
        issued.transition(
            _request(
                permit,
                ConsolidationExecutionPermitLifecycleAction.EXPIRE,
                decision_episode=103,
            )
        )

    expired = issued.transition(
        _request(
            permit,
            ConsolidationExecutionPermitLifecycleAction.EXPIRE,
            decision_episode=104,
            actor_code="caller:episode_boundary",
            reason_code="permit_window_elapsed",
        )
    )

    assert expired.status is ConsolidationExecutionPermitLifecycleStatus.EXPIRED
    assert expired.is_terminal
    assert expired.consumption_count == 0


def test_cancel_or_consume_after_expiry_window_is_rejected() -> None:
    permit = _permit()
    issued = ConsolidationExecutionPermitLifecycleRecord.issued(permit)

    for action in (
        ConsolidationExecutionPermitLifecycleAction.CANCEL,
        ConsolidationExecutionPermitLifecycleAction.CONSUME,
    ):
        with pytest.raises(ValueError, match="requires an unexpired permit"):
            issued.transition(
                _request(
                    permit,
                    action,
                    decision_episode=104,
                    consumption_reference_code=(
                        "commit:late"
                        if action is ConsolidationExecutionPermitLifecycleAction.CONSUME
                        else None
                    ),
                )
            )


def test_transition_must_follow_permit_issuance() -> None:
    permit = _permit()
    issued = ConsolidationExecutionPermitLifecycleRecord.issued(permit)

    with pytest.raises(ValueError, match="must follow permit issuance"):
        issued.transition(
            _request(
                permit,
                ConsolidationExecutionPermitLifecycleAction.CANCEL,
                decision_episode=102,
            )
        )


def test_nonconsume_transitions_reject_consumption_reference() -> None:
    permit = _permit()

    with pytest.raises(ValueError, match="only consume transition"):
        _request(
            permit,
            ConsolidationExecutionPermitLifecycleAction.CANCEL,
            decision_episode=103,
            consumption_reference_code="commit:not_allowed",
        )


def test_mismatched_permit_proposal_or_candidate_is_rejected() -> None:
    permit = _permit()
    issued = ConsolidationExecutionPermitLifecycleRecord.issued(permit)
    request = _request(
        permit,
        ConsolidationExecutionPermitLifecycleAction.CANCEL,
        decision_episode=103,
    )

    cases = (
        (replace(request, target_permit_id="permit:wrong"), "different permit"),
        (replace(request, expected_proposal_id="proposal:wrong"), "different proposal"),
        (replace(request, expected_candidate_id="candidate:wrong"), "different candidate"),
    )
    for changed, message in cases:
        with pytest.raises(ValueError, match=message):
            issued.transition(changed)


def test_terminal_records_reject_every_conflicting_transition() -> None:
    permit = _permit()
    issued = ConsolidationExecutionPermitLifecycleRecord.issued(permit)
    cancelled = issued.transition(
        _request(
            permit,
            ConsolidationExecutionPermitLifecycleAction.CANCEL,
            decision_episode=103,
        )
    )

    for action, episode in (
        (ConsolidationExecutionPermitLifecycleAction.CANCEL, 103),
        (ConsolidationExecutionPermitLifecycleAction.CONSUME, 103),
        (ConsolidationExecutionPermitLifecycleAction.EXPIRE, 104),
    ):
        with pytest.raises(ValueError, match="already terminal"):
            cancelled.transition(
                _request(
                    permit,
                    action,
                    decision_episode=episode,
                    consumption_reference_code=(
                        "commit:blocked"
                        if action is ConsolidationExecutionPermitLifecycleAction.CONSUME
                        else None
                    ),
                )
            )


def test_transition_identity_is_deterministic_and_tampering_is_rejected() -> None:
    permit = _permit()
    issued = ConsolidationExecutionPermitLifecycleRecord.issued(permit)
    request = _request(
        permit,
        ConsolidationExecutionPermitLifecycleAction.CONSUME,
        decision_episode=103,
        actor_code="execution:bounded_commit",
        reason_code="bounded_commit_recorded",
        consumption_reference_code="commit:consolidation:001",
    )

    first = issued.transition(request)
    second = issued.transition(request)
    decision = first.decisions[0]

    assert first == second
    assert decision.decision_id == second.decisions[0].decision_id
    assert decision.decision_id.startswith("consolidation-permit-transition:")
    assert str(decision.snapshot()).isascii()
    with pytest.raises(ValueError, match="identity is inconsistent"):
        replace(decision, decision_id="consolidation-permit-transition:tampered")


def test_reconstructed_record_rejects_mismatched_status_or_permit() -> None:
    permit = _permit()
    other = _permit(reason_code="approve_after_additional_human_check")
    consumed = ConsolidationExecutionPermitLifecycleRecord.issued(permit).transition(
        _request(
            permit,
            ConsolidationExecutionPermitLifecycleAction.CONSUME,
            decision_episode=103,
            actor_code="execution:bounded_commit",
            reason_code="bounded_commit_recorded",
            consumption_reference_code="commit:consolidation:001",
        )
    )

    with pytest.raises(ValueError, match="status must match"):
        ConsolidationExecutionPermitLifecycleRecord(
            permit=permit,
            status=ConsolidationExecutionPermitLifecycleStatus.CANCELLED,
            decisions=consumed.decisions,
        )
    with pytest.raises(ValueError, match="different permit"):
        ConsolidationExecutionPermitLifecycleRecord(
            permit=other,
            status=ConsolidationExecutionPermitLifecycleStatus.CONSUMED,
            decisions=consumed.decisions,
        )


def test_registry_enforces_unique_permit_identity_and_preserves_other_records() -> None:
    first = _permit()
    second = _permit(reason_code="approve_after_additional_human_check")
    registry = ConsolidationExecutionPermitLifecycleRegistry().add(first).add(second)
    before_second = registry.record_for(second.permit_id)

    consumed = registry.transition(
        _request(
            first,
            ConsolidationExecutionPermitLifecycleAction.CONSUME,
            decision_episode=103,
            actor_code="execution:bounded_commit",
            reason_code="bounded_commit_recorded",
            consumption_reference_code="commit:consolidation:001",
        )
    )

    assert registry.consumption_count == 0
    assert consumed.consumption_count == 1
    assert consumed.record_for(first.permit_id).consumption_count == 1
    assert consumed.record_for(second.permit_id) == before_second
    assert not consumed.has_application_authority
    with pytest.raises(ValueError, match="already exists"):
        registry.add(first)
    with pytest.raises(ValueError, match="not present"):
        registry.record_for("permit:unknown")
    with pytest.raises(ValueError, match="already terminal"):
        consumed.transition(
            _request(
                first,
                ConsolidationExecutionPermitLifecycleAction.CONSUME,
                decision_episode=103,
                actor_code="execution:bounded_commit",
                reason_code="duplicate_commit_attempt",
                consumption_reference_code="commit:consolidation:002",
            )
        )


def test_permit_lifecycle_is_separate_from_proposal_lifecycle() -> None:
    ledger = _ledger()
    proposal_registry = _accepted_registry(_proposal(ledger))
    proposal_before = proposal_registry.snapshot()
    record = proposal_registry.active_records[0]
    permit = ConsolidationExecutionApprovalPolicy().evaluate(
        request=ConsolidationExecutionApprovalRequest(
            target_proposal_id=record.proposal.proposal_id,
            expected_candidate_id=record.proposal.candidate.candidate_id,
            expected_review_decision_id=record.lifecycle.decisions[-1].decision_id,
            approval_episode=102,
            expires_after_episode=103,
            approver_code="human:operator",
            reason_code="approve_bounded_consolidation",
        ),
        record=record,
        ledger=ledger,
        available_assembly_ids=_ASSEMBLIES,
        available_route_ids=_ROUTES,
    )

    cancelled = ConsolidationExecutionPermitLifecycleRecord.issued(permit).transition(
        _request(
            permit,
            ConsolidationExecutionPermitLifecycleAction.CANCEL,
            decision_episode=103,
        )
    )

    assert cancelled.status is ConsolidationExecutionPermitLifecycleStatus.CANCELLED
    assert proposal_registry.snapshot() == proposal_before
    assert proposal_registry.active_records[0].lifecycle.status.value == "accepted"


def test_permit_lifecycle_has_no_application_persistence_timer_or_sql_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_execution_permit_lifecycle.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "consolidation_application" not in source
    assert ".apply(" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "seedmind.integration" not in source
