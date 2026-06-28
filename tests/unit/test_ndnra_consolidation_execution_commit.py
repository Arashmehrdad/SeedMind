"""Tests for atomic human-approved NDNRA consolidation execution."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationApplicationResult,
    ConsolidationApplicationState,
    ConsolidationEligibility,
    ConsolidationExecutionApprovalPolicy,
    ConsolidationExecutionApprovalRequest,
    ConsolidationExecutionCommitPolicy,
    ConsolidationExecutionCommitRequest,
    ConsolidationExecutionCommitResult,
    ConsolidationExecutionPermit,
    ConsolidationExecutionPermitLifecycleAction,
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
    ConsolidationStateSnapshot,
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


def _trace(index: int, *, effect_value: float = 1.0) -> ContextualExperienceTrace:
    route_id = _ROUTES[index % 2]
    assembly_id = _ASSEMBLIES[0] if route_id == _ROUTES[0] else _ASSEMBLIES[1]
    return ContextualExperienceTrace(
        identity=EventIdentity("execution_commit_test", "episode:mastery", index),
        correlation_group_id=f"group:execution-commit:{index}",
        assembly_id=assembly_id,
        route_id=route_id,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code=_LESSON.need_code,
            sensor_values=(float(index), float(index + 1)),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(EffectObservation(_LESSON.effect_code, effect_value, 1.0),),
        transfer_attempted=True,
        transfer_succeeded=effect_value > 0.0 and index < 2,
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


def _proposal_registry(
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


def _permit(
    ledger: ContextualExperienceLedger,
    proposal_registry: ConsolidationProposalLifecycleRegistry,
) -> ConsolidationExecutionPermit:
    record = proposal_registry.active_records[0]
    return ConsolidationExecutionApprovalPolicy().evaluate(
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


def _state() -> ConsolidationApplicationState:
    return ConsolidationApplicationState.from_identifiers(
        assembly_ids=(*_ASSEMBLIES, "assembly:untouched"),
        route_ids=(*_ROUTES, "route:untouched"),
        initial_stability=0.20,
        initial_plasticity=0.80,
    )


def _setup() -> tuple[
    ContextualExperienceLedger,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationExecutionPermitLifecycleRegistry,
    ConsolidationApplicationState,
    ConsolidationExecutionPermit,
]:
    ledger = _ledger()
    proposal_registry = _proposal_registry(_proposal(ledger))
    permit = _permit(ledger, proposal_registry)
    permit_registry = ConsolidationExecutionPermitLifecycleRegistry().add(permit)
    return ledger, proposal_registry, permit_registry, _state(), permit


def _request(
    permit: ConsolidationExecutionPermit,
    *,
    execution_episode: int = 103,
    executor_code: str = "execution:bounded_commit",
    reason_code: str = "commit_human_approved_consolidation",
) -> ConsolidationExecutionCommitRequest:
    return ConsolidationExecutionCommitRequest(
        target_permit_id=permit.permit_id,
        expected_proposal_id=permit.proposal.proposal_id,
        expected_candidate_id=permit.proposal.candidate.candidate_id,
        execution_episode=execution_episode,
        executor_code=executor_code,
        reason_code=reason_code,
    )


def _execute(
    ledger: ContextualExperienceLedger,
    proposal_registry: ConsolidationProposalLifecycleRegistry,
    permit_registry: ConsolidationExecutionPermitLifecycleRegistry,
    state: ConsolidationApplicationState,
    permit: ConsolidationExecutionPermit,
) -> ConsolidationExecutionCommitResult:
    return ConsolidationExecutionCommitPolicy().execute(
        request=_request(permit),
        proposal_record=proposal_registry.active_records[0],
        permit_registry=permit_registry,
        ledger=ledger,
        application_state=state,
        available_assembly_ids=_ASSEMBLIES,
        available_route_ids=_ROUTES,
    )


def test_successful_commit_applies_once_and_consumes_permit_atomically() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()
    ledger_before = ledger.snapshot()
    proposal_before = proposal_registry.snapshot()
    permit_before = permit_registry.snapshot()
    state_before = state.snapshot()

    result = _execute(ledger, proposal_registry, permit_registry, state, permit)

    receipt = result.receipt
    consumed = result.permit_registry.record_for(permit.permit_id)
    assert receipt.execution_id.startswith("consolidation-execution:")
    assert receipt.application.before == state_before
    assert receipt.application.after == state.snapshot()
    assert receipt.application.candidate == permit.proposal.candidate
    assert receipt.application_count == 1
    assert receipt.replay_trigger_count == 0
    assert receipt.restoration_trigger_count == 0
    assert not receipt.has_production_action_authority
    assert consumed.status is ConsolidationExecutionPermitLifecycleStatus.CONSUMED
    assert consumed.consumption_count == 1
    assert consumed.decisions[0] == receipt.permit_transition
    assert consumed.decisions[0].consumption_reference_code == receipt.execution_id
    assert permit_registry.snapshot() == permit_before
    assert permit_registry.record_for(permit.permit_id).status is (
        ConsolidationExecutionPermitLifecycleStatus.ISSUED
    )
    assert ledger.snapshot() == ledger_before
    assert proposal_registry.snapshot() == proposal_before


def test_commit_changes_only_candidate_structures_within_bounds() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()

    result = _execute(ledger, proposal_registry, permit_registry, state, permit)

    before = result.receipt.application.before
    after = result.receipt.application.after
    for structure_id in _ASSEMBLIES:
        assert after.assembly_state(structure_id).stability == pytest.approx(0.30)
        assert after.assembly_state(structure_id).plasticity == pytest.approx(0.70)
    for structure_id in _ROUTES:
        assert after.route_state(structure_id).stability == pytest.approx(0.30)
        assert after.route_state(structure_id).plasticity == pytest.approx(0.70)
    assert after.assembly_state("assembly:untouched") == before.assembly_state("assembly:untouched")
    assert after.route_state("route:untouched") == before.route_state("route:untouched")
    assert after.applied_candidate_ids == (permit.proposal.candidate.candidate_id,)


def test_identical_fresh_commits_have_deterministic_execution_identity() -> None:
    first_setup = _setup()
    second_setup = _setup()

    first = _execute(*first_setup[:-1], first_setup[-1])
    second = _execute(*second_setup[:-1], second_setup[-1])

    assert first.receipt.execution_id == second.receipt.execution_id
    assert first.receipt.snapshot() == second.receipt.snapshot()
    assert str(first.snapshot()).isascii()


def test_cancelled_permit_blocks_commit_before_state_mutation() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()
    cancelled = permit_registry.transition(
        ConsolidationExecutionPermitTransitionRequest(
            target_permit_id=permit.permit_id,
            expected_proposal_id=permit.proposal.proposal_id,
            expected_candidate_id=permit.proposal.candidate.candidate_id,
            action=ConsolidationExecutionPermitLifecycleAction.CANCEL,
            decision_episode=103,
            actor_code="human:operator",
            reason_code="cancel_before_commit",
        )
    )
    before = state.snapshot()

    with pytest.raises(ValueError, match="requires an issued permit"):
        ConsolidationExecutionCommitPolicy().execute(
            request=_request(permit),
            proposal_record=proposal_registry.active_records[0],
            permit_registry=cancelled,
            ledger=ledger,
            application_state=state,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        )

    assert state.snapshot() == before
    assert cancelled.record_for(permit.permit_id).status is (
        ConsolidationExecutionPermitLifecycleStatus.CANCELLED
    )


def test_expired_or_out_of_window_permit_blocks_commit() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()
    before = state.snapshot()

    with pytest.raises(ValueError, match="outside its validity window"):
        ConsolidationExecutionCommitPolicy().execute(
            request=_request(permit, execution_episode=104),
            proposal_record=proposal_registry.active_records[0],
            permit_registry=permit_registry,
            ledger=ledger,
            application_state=state,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        )

    assert state.snapshot() == before


def test_consumed_permit_cannot_apply_twice() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()
    first = _execute(ledger, proposal_registry, permit_registry, state, permit)
    after_first = state.snapshot()

    with pytest.raises(ValueError, match="requires an issued permit"):
        ConsolidationExecutionCommitPolicy().execute(
            request=_request(permit),
            proposal_record=proposal_registry.active_records[0],
            permit_registry=first.permit_registry,
            ledger=ledger,
            application_state=state,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        )

    assert state.snapshot() == after_first
    assert first.permit_registry.consumption_count == 1


def test_new_evidence_between_approval_and_commit_blocks_stale_permit() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()
    ledger.record(_trace(3))
    state_before = state.snapshot()
    registry_before = permit_registry.snapshot()

    with pytest.raises(ValueError, match="received stale"):
        ConsolidationExecutionCommitPolicy().execute(
            request=_request(permit),
            proposal_record=proposal_registry.active_records[0],
            permit_registry=permit_registry,
            ledger=ledger,
            application_state=state,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        )

    assert state.snapshot() == state_before
    assert permit_registry.snapshot() == registry_before


def test_missing_application_structure_fails_without_consumption_or_mutation() -> None:
    ledger, proposal_registry, permit_registry, _, permit = _setup()
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=(_ASSEMBLIES[0],),
        route_ids=_ROUTES,
        initial_stability=0.20,
        initial_plasticity=0.80,
    )
    before = state.snapshot()
    registry_before = permit_registry.snapshot()

    with pytest.raises(ValueError, match="unknown assemblies"):
        ConsolidationExecutionCommitPolicy().execute(
            request=_request(permit),
            proposal_record=proposal_registry.active_records[0],
            permit_registry=permit_registry,
            ledger=ledger,
            application_state=state,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        )

    assert state.snapshot() == before
    assert permit_registry.snapshot() == registry_before


def test_mismatched_commit_identities_fail_before_application() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()
    request = _request(permit)
    before = state.snapshot()

    cases = (
        (replace(request, target_permit_id="permit:wrong"), "not present"),
        (replace(request, expected_proposal_id="proposal:wrong"), "different proposal"),
        (replace(request, expected_candidate_id="candidate:wrong"), "different candidate"),
    )
    for changed, message in cases:
        with pytest.raises(ValueError, match=message):
            ConsolidationExecutionCommitPolicy().execute(
                request=changed,
                proposal_record=proposal_registry.active_records[0],
                permit_registry=permit_registry,
                ledger=ledger,
                application_state=state,
                available_assembly_ids=_ASSEMBLIES,
                available_route_ids=_ROUTES,
            )
        assert state.snapshot() == before


def test_commit_requires_bounded_execution_gate_identity() -> None:
    _, _, _, _, permit = _setup()

    with pytest.raises(ValueError, match="bounded execution gate"):
        _request(permit, executor_code="human:operator")


class _PostApplyFailureTarget:
    def __init__(self, state: ConsolidationApplicationState) -> None:
        self.state = state

    def snapshot(self) -> ConsolidationStateSnapshot:
        return self.state.snapshot()

    def apply(
        self,
        eligibility: ConsolidationEligibility,
    ) -> ConsolidationApplicationResult:
        self.state.apply(eligibility)
        raise RuntimeError("injected failure after state mutation")

    def restore_snapshot(
        self,
        *,
        expected_current: ConsolidationStateSnapshot,
        replacement: ConsolidationStateSnapshot,
    ) -> None:
        self.state.restore_snapshot(
            expected_current=expected_current,
            replacement=replacement,
        )


def test_post_apply_failure_restores_exact_state_and_leaves_permit_issued() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()
    failing = _PostApplyFailureTarget(state)
    state_before = state.snapshot()
    permit_before = permit_registry.snapshot()
    ledger_before = ledger.snapshot()
    proposal_before = proposal_registry.snapshot()

    with pytest.raises(RuntimeError, match="injected failure"):
        ConsolidationExecutionCommitPolicy().execute(
            request=_request(permit),
            proposal_record=proposal_registry.active_records[0],
            permit_registry=permit_registry,
            ledger=ledger,
            application_state=failing,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        )

    assert state.snapshot() == state_before
    assert permit_registry.snapshot() == permit_before
    assert permit_registry.record_for(permit.permit_id).status is (
        ConsolidationExecutionPermitLifecycleStatus.ISSUED
    )
    assert ledger.snapshot() == ledger_before
    assert proposal_registry.snapshot() == proposal_before


def test_receipt_rejects_tampered_execution_or_transition_identity() -> None:
    ledger, proposal_registry, permit_registry, state, permit = _setup()
    result = _execute(ledger, proposal_registry, permit_registry, state, permit)
    receipt = result.receipt

    with pytest.raises(ValueError, match="reference must equal"):
        replace(receipt, execution_id="consolidation-execution:tampered")
    with pytest.raises(ValueError, match="identity is inconsistent"):
        replace(
            receipt.permit_transition,
            consumption_reference_code="consolidation-execution:wrong",
        )


def test_execution_commit_has_no_replay_growth_advice_sql_or_action_path() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_execution_commit.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "replay(" not in source
    assert "rollback_consolidation" not in source
    assert "advice" not in source
    assert "growth" not in source
    assert "route_rank" not in source
    assert "select_action" not in source
    assert "seedmind.integration" not in source
    assert "threading" not in source
    assert "asyncio" not in source
