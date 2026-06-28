"""Tests for explicit human-approved NDNRA consolidation execution permits."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationExecutionApprovalPolicy,
    ConsolidationExecutionApprovalRequest,
    ConsolidationExecutionPermit,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalRevalidationStatus,
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


def _trace(
    index: int,
    *,
    effect_value: float = 1.0,
) -> ContextualExperienceTrace:
    route_id = _ROUTES[index % 2]
    assembly_id = _ASSEMBLIES[0] if route_id == _ROUTES[0] else _ASSEMBLIES[1]
    return ContextualExperienceTrace(
        identity=EventIdentity(
            "execution_approval_test",
            "episode:mastery",
            index,
        ),
        correlation_group_id=f"group:execution-approval:{index}",
        assembly_id=assembly_id,
        route_id=route_id,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code=_LESSON.need_code,
            sensor_values=(float(index), float(index + 1)),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(
            EffectObservation(
                _LESSON.effect_code,
                effect_value,
                1.0,
            ),
        ),
        transfer_attempted=True,
        transfer_succeeded=effect_value > 0.0,
    )


def _ledger() -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    for index in range(3):
        ledger.record(_trace(index))
    return ledger


def _proposal(
    ledger: ContextualExperienceLedger,
    *,
    episode: int = 100,
) -> ConsolidationScheduleProposal:
    decision = ConsolidationSchedulingPolicy(
        first_eligible_episode=episode,
        minimum_interval_episodes=1,
    ).evaluate(
        ledger=ledger,
        request=ConsolidationScheduleRequest(
            lesson=_LESSON,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        ),
        context=ConsolidationSchedulingContext(episode_index=episode),
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


def _request(
    registry: ConsolidationProposalLifecycleRegistry,
    *,
    approval_episode: int = 102,
    expires_after_episode: int = 103,
    approver_code: str = "human:operator",
    reason_code: str = "approve_bounded_consolidation",
) -> ConsolidationExecutionApprovalRequest:
    record = registry.active_records[0]
    accepted_review = record.lifecycle.decisions[-1]
    return ConsolidationExecutionApprovalRequest(
        target_proposal_id=record.proposal.proposal_id,
        expected_candidate_id=record.proposal.candidate.candidate_id,
        expected_review_decision_id=accepted_review.decision_id,
        approval_episode=approval_episode,
        expires_after_episode=expires_after_episode,
        approver_code=approver_code,
        reason_code=reason_code,
    )


def _permit(
    registry: ConsolidationProposalLifecycleRegistry,
    ledger: ContextualExperienceLedger,
    *,
    request: ConsolidationExecutionApprovalRequest | None = None,
) -> ConsolidationExecutionPermit:
    return ConsolidationExecutionApprovalPolicy().evaluate(
        request=_request(registry) if request is None else request,
        record=registry.active_records[0],
        ledger=ledger,
        available_assembly_ids=_ASSEMBLIES,
        available_route_ids=_ROUTES,
    )


def test_current_accepted_proposal_receives_deterministic_human_permit() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))
    before_ledger = ledger.snapshot()
    before_registry = registry.snapshot()

    first = _permit(registry, ledger)
    second = _permit(registry, ledger)

    assert first == second
    assert first.permit_id == second.permit_id
    assert first.permit_id.startswith("consolidation-execution-permit:")
    assert first.proposal == registry.active_records[0].proposal
    assert first.accepted_review_decision_id == (
        registry.active_records[0].lifecycle.decisions[-1].decision_id
    )
    assert first.revalidation.status is ConsolidationProposalRevalidationStatus.CURRENT
    assert first.revalidation.current_candidate == first.proposal.candidate
    assert first.approver_code == "human:operator"
    assert first.authorizes_one_application
    assert first.single_use
    assert not first.consumed
    assert first.application_count == 0
    assert not first.has_direct_execution_authority
    assert ledger.snapshot() == before_ledger
    assert registry.snapshot() == before_registry


def test_permit_validity_window_is_bounded_and_inspectable() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))

    permit = _permit(registry, ledger)

    assert not permit.valid_at(101)
    assert permit.valid_at(102)
    assert permit.valid_at(103)
    assert not permit.valid_at(104)
    assert str(permit.snapshot()).isascii()
    assert permit.snapshot()["application_count"] == 0
    assert permit.snapshot()["has_direct_execution_authority"] is False


def test_approval_requires_explicit_human_identity() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))

    with pytest.raises(ValueError, match="explicit human approver"):
        _request(registry, approver_code="policy:auto_approver")


def test_pending_deferred_and_rejected_records_cannot_receive_permits() -> None:
    ledger = _ledger()
    proposal = _proposal(ledger)
    pending = ConsolidationProposalLifecycleRegistry().add(proposal)
    deferred = pending.review(
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.DEFER,
            decision_episode=101,
            reviewer_code="human:reviewer",
            reason_code="collect_more_evidence",
            defer_until_episode=120,
        )
    )
    rejected = pending.review(
        ConsolidationProposalReviewRequest(
            proposal=proposal,
            action=ConsolidationProposalReviewAction.REJECT,
            decision_episode=101,
            reviewer_code="human:reviewer",
            reason_code="proposal_rejected",
        )
    )

    for registry in (pending, deferred):
        record = registry.records[0]
        request = ConsolidationExecutionApprovalRequest(
            target_proposal_id=proposal.proposal_id,
            expected_candidate_id=proposal.candidate.candidate_id,
            expected_review_decision_id="consolidation-review:unaccepted",
            approval_episode=102,
            expires_after_episode=103,
            approver_code="human:operator",
            reason_code="invalid_execution_attempt",
        )
        with pytest.raises(ValueError, match="accepted lifecycle status"):
            ConsolidationExecutionApprovalPolicy().evaluate(
                request=request,
                record=record,
                ledger=ledger,
                available_assembly_ids=_ASSEMBLIES,
                available_route_ids=_ROUTES,
            )

    request = ConsolidationExecutionApprovalRequest(
        target_proposal_id=proposal.proposal_id,
        expected_candidate_id=proposal.candidate.candidate_id,
        expected_review_decision_id=rejected.records[0].lifecycle.decisions[-1].decision_id,
        approval_episode=102,
        expires_after_episode=103,
        approver_code="human:operator",
        reason_code="invalid_execution_attempt",
    )
    with pytest.raises(ValueError, match="active lifecycle record"):
        ConsolidationExecutionApprovalPolicy().evaluate(
            request=request,
            record=rejected.records[0],
            ledger=ledger,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        )


def test_stale_proposal_fails_immediate_revalidation() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))
    ledger.record(_trace(3))
    before_registry = registry.snapshot()

    with pytest.raises(ValueError, match="received stale"):
        _permit(registry, ledger)

    assert registry.snapshot() == before_registry


def test_invalid_structure_or_contradiction_blocks_approval() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))
    request = _request(registry)

    with pytest.raises(ValueError, match="received invalid_for_review"):
        ConsolidationExecutionApprovalPolicy().evaluate(
            request=request,
            record=registry.active_records[0],
            ledger=ledger,
            available_assembly_ids=(_ASSEMBLIES[0],),
            available_route_ids=_ROUTES,
        )

    ledger.record(_trace(3, effect_value=-1.0))
    with pytest.raises(ValueError, match="received invalid_for_review"):
        _permit(registry, ledger)


def test_mismatched_proposal_candidate_or_review_identity_is_rejected() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))
    request = _request(registry)

    cases = (
        (replace(request, target_proposal_id="consolidation-schedule:wrong"), "different proposal"),
        (replace(request, expected_candidate_id="consolidation:wrong"), "different candidate"),
        (
            replace(request, expected_review_decision_id="consolidation-review:wrong"),
            "different review decision",
        ),
    )
    for changed, message in cases:
        with pytest.raises(ValueError, match=message):
            _permit(registry, ledger, request=changed)


def test_approval_must_follow_review_and_use_short_validity() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))

    with pytest.raises(ValueError, match="must follow accepted review"):
        _permit(
            registry,
            ledger,
            request=_request(
                registry,
                approval_episode=101,
                expires_after_episode=102,
            ),
        )
    with pytest.raises(ValueError, match="validity exceeds"):
        _permit(
            registry,
            ledger,
            request=_request(
                registry,
                approval_episode=102,
                expires_after_episode=104,
            ),
        )


def test_distinct_human_reason_produces_distinct_permit_identity() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))

    first = _permit(registry, ledger)
    second = _permit(
        registry,
        ledger,
        request=_request(registry, reason_code="approve_after_second_check"),
    )

    assert first.permit_id != second.permit_id
    assert first.proposal == second.proposal
    assert first.revalidation == second.revalidation


def test_new_permit_rejects_preconsumed_or_direct_execution_state() -> None:
    ledger = _ledger()
    registry = _accepted_registry(_proposal(ledger))
    permit = _permit(registry, ledger)

    with pytest.raises(ValueError, match="authorize exactly one"):
        replace(permit, authorizes_one_application=False)
    with pytest.raises(ValueError, match="single-use"):
        replace(permit, single_use=False)
    with pytest.raises(ValueError, match="already be consumed"):
        replace(permit, consumed=True)
    with pytest.raises(ValueError, match="cannot contain applications"):
        replace(permit, application_count=1)
    with pytest.raises(ValueError, match="cannot execute"):
        replace(permit, has_direct_execution_authority=True)


def test_approval_module_has_no_application_persistence_timer_or_sql_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_execution_approval.py")
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
