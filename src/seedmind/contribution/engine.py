"""Week 9 contribution evaluation against the frozen Week 8 skill record."""

from __future__ import annotations

from dataclasses import dataclass, replace

from seedmind.contribution.contracts import (
    CapabilityCheck,
    CapabilityEvidence,
    CapabilityStatus,
    ContributionRecord,
    ContributionShadowAudit,
    GroundedOutcomeVerification,
    HonestFailureReport,
    HumanAuthorityInterruption,
    HumanContributionRequest,
    SupportEvaluation,
    SupportPolicy,
    SupportState,
    VerificationEvidenceSource,
    VerificationStatus,
)
from seedmind.environment import NurseryRuntime, NurseryScenario, detect_target_occupancy
from seedmind.human.contracts import SupportLevel
from seedmind.skills import (
    ApproachAndPushSkillController,
    SkillExecutionStatus,
    SkillRecord,
    SkillValidationStatus,
    retain_skill_candidate_through_curiosity,
)


@dataclass(frozen=True, slots=True)
class ContributionEvaluationResult:
    """Complete result of one Week 9 contribution attempt."""

    record: ContributionRecord
    support_state: SupportState


class ContributionEngine:
    """Evaluate one human contribution request without mutating Week 8 skills."""

    __slots__ = ("_policy",)

    def __init__(self, policy: SupportPolicy | None = None) -> None:
        self._policy = policy or SupportPolicy()

    @property
    def policy(self) -> SupportPolicy:
        """Return the declared Week 9 support policy."""
        return self._policy

    def check_capability(
        self,
        request: HumanContributionRequest,
        skill_record: SkillRecord | None,
        *,
        scenario_context: str,
    ) -> CapabilityCheck:
        """Inspect the frozen Week 8 skill record for one request."""
        context_matched = scenario_context in request.learned_context
        if skill_record is None:
            return CapabilityCheck(
                status=CapabilityStatus.UNAVAILABLE,
                target_capability=request.target_capability,
                checked_skill_id=None,
                expected_outcome_matched=False,
                target_object_matched=False,
                target_matched=False,
                learned_context_matched=context_matched,
                reason_codes=("skill_missing",),
                failed_preconditions=("frozen_skill_record_missing",),
            )

        snapshot = skill_record.deterministic_snapshot
        capability_matched = skill_record.name == request.target_capability
        expected_outcome_matched = skill_record.expected_outcome == request.expected_outcome
        target_object_matched = snapshot.get("target_object_id") == request.target_object_id
        target_matched = snapshot.get("target_id") == request.target_id
        if not capability_matched:
            return CapabilityCheck(
                status=CapabilityStatus.UNAVAILABLE,
                target_capability=request.target_capability,
                checked_skill_id=skill_record.skill_id,
                expected_outcome_matched=expected_outcome_matched,
                target_object_matched=target_object_matched,
                target_matched=target_matched,
                learned_context_matched=context_matched,
                reason_codes=("capability_missing",),
                failed_preconditions=("target_capability_not_compiled",),
            )
        if skill_record.last_validation_status is SkillValidationStatus.UNVALIDATED:
            return CapabilityCheck(
                status=CapabilityStatus.UNPROVEN,
                target_capability=request.target_capability,
                checked_skill_id=skill_record.skill_id,
                expected_outcome_matched=expected_outcome_matched,
                target_object_matched=target_object_matched,
                target_matched=target_matched,
                learned_context_matched=context_matched,
                reason_codes=("skill_unvalidated",),
                failed_preconditions=("week8_skill_not_validated",),
            )
        if skill_record.last_validation_status is SkillValidationStatus.FAILED:
            return CapabilityCheck(
                status=CapabilityStatus.DEGRADED,
                target_capability=request.target_capability,
                checked_skill_id=skill_record.skill_id,
                expected_outcome_matched=expected_outcome_matched,
                target_object_matched=target_object_matched,
                target_matched=target_matched,
                learned_context_matched=context_matched,
                reason_codes=("skill_degraded",),
                failed_preconditions=("week8_skill_validation_failed",),
            )
        if not all(
            (
                expected_outcome_matched,
                target_object_matched,
                target_matched,
                context_matched,
            )
        ):
            failed: list[str] = []
            if not expected_outcome_matched:
                failed.append("expected_outcome_mismatched")
            if not target_object_matched:
                failed.append("target_object_mismatched")
            if not target_matched:
                failed.append("target_mismatched")
            if not context_matched:
                failed.append("learned_context_mismatched")
            return CapabilityCheck(
                status=CapabilityStatus.CONTEXT_MISMATCHED,
                target_capability=request.target_capability,
                checked_skill_id=skill_record.skill_id,
                expected_outcome_matched=expected_outcome_matched,
                target_object_matched=target_object_matched,
                target_matched=target_matched,
                learned_context_matched=context_matched,
                reason_codes=("context_mismatched",),
                failed_preconditions=tuple(failed),
            )
        return CapabilityCheck(
            status=CapabilityStatus.VERIFIED,
            target_capability=request.target_capability,
            checked_skill_id=skill_record.skill_id,
            expected_outcome_matched=True,
            target_object_matched=True,
            target_matched=True,
            learned_context_matched=True,
            reason_codes=("verified",),
            failed_preconditions=(),
        )

    def verify_grounded_outcome(
        self,
        request: HumanContributionRequest,
        runtime: NurseryRuntime,
        *,
        evidence_sources: tuple[VerificationEvidenceSource, ...],
        last_transition_outcome: str | None,
    ) -> GroundedOutcomeVerification:
        """Verify success using runtime state and actual transitions only."""
        rejected_sources = {
            VerificationEvidenceSource.SELF_REPORT,
            VerificationEvidenceSource.PRODUCER_VERIFIER_AGREEMENT,
            VerificationEvidenceSource.NDNRA_AGREEMENT,
            VerificationEvidenceSource.IMAGINATION,
            VerificationEvidenceSource.UNAVAILABLE,
        }
        if any(source in rejected_sources for source in evidence_sources):
            return GroundedOutcomeVerification(
                status=VerificationStatus.REJECTED,
                evidence_sources=evidence_sources,
                reason_code="rejected_non_grounded_evidence",
                target_achieved=False,
            )
        occupancy = detect_target_occupancy(runtime.state)
        target_achieved = occupancy.object_target_pairs == (
            (request.target_object_id, request.target_id),
        )
        if not target_achieved:
            return GroundedOutcomeVerification(
                status=VerificationStatus.REJECTED,
                evidence_sources=evidence_sources,
                reason_code="runtime_state_did_not_confirm_outcome",
                target_achieved=False,
            )
        if VerificationEvidenceSource.ACTUAL_TRANSITION not in evidence_sources:
            return GroundedOutcomeVerification(
                status=VerificationStatus.REJECTED,
                evidence_sources=evidence_sources,
                reason_code="actual_transition_missing",
                target_achieved=True,
            )
        if last_transition_outcome != "pushed":
            return GroundedOutcomeVerification(
                status=VerificationStatus.REJECTED,
                evidence_sources=evidence_sources,
                reason_code="transition_outcome_not_grounded_push",
                target_achieved=True,
            )
        return GroundedOutcomeVerification(
            status=VerificationStatus.VERIFIED,
            evidence_sources=evidence_sources,
            reason_code="grounded_runtime_transition_verified",
            target_achieved=True,
        )

    def evaluate_support(
        self,
        state: SupportState,
        new_evidence: CapabilityEvidence,
    ) -> SupportState:
        """Evaluate support state conservatively using post-regression evidence."""
        history = (*state.history, new_evidence)
        promotion_history = history[state.promotion_evidence_start_index :]
        recent = promotion_history[-self.policy.recent_evidence_window :]
        blockers = self._blocker_codes(recent)
        recent_successes = tuple(
            item
            for item in recent
            if item.familiar_context
            and item.independent_execution
            and item.success
            and item.verification_status is VerificationStatus.VERIFIED
        )
        recent_attempts = tuple(
            item for item in recent if item.familiar_context and item.independent_execution
        )
        trailing_grounded_failures = 0
        for item in reversed(history):
            grounded_failure = (
                item.familiar_context
                and item.independent_execution
                and not item.success
                and item.verification_status is VerificationStatus.REJECTED
            )
            if not grounded_failure:
                break
            trailing_grounded_failures += 1
        success_rate = len(recent_successes) / len(recent_attempts) if recent_attempts else 0.0
        distinct_contexts = len({item.scenario_context for item in recent_successes})
        next_level = state.current_level
        next_promotion_start = state.promotion_evidence_start_index
        severe_regression = new_evidence.degraded or new_evidence.unsafe
        if state.current_level is SupportLevel.GUIDED_LEARNER and (
            severe_regression
            or trailing_grounded_failures >= self.policy.grounded_failures_to_restore_dependent
        ):
            next_level = SupportLevel.DEPENDENT
            next_promotion_start = len(history)
        elif (
            state.current_level is SupportLevel.DEPENDENT
            and not blockers
            and (
                len(recent_successes) >= self.policy.minimum_verified_independent_familiar_successes
                and success_rate >= self.policy.minimum_success_rate
                and distinct_contexts >= self.policy.minimum_distinct_scenario_contexts
            )
        ):
            next_level = SupportLevel.GUIDED_LEARNER
        evaluation = SupportEvaluation(
            previous_level=state.current_level,
            next_level=next_level,
            blocker_codes=tuple(blockers) if blockers else ("none",),
            recent_verified_independent_familiar_successes=len(recent_successes),
            recent_success_rate=success_rate,
            distinct_scenario_contexts=distinct_contexts,
            recent_grounded_familiar_failures=trailing_grounded_failures,
        )
        return SupportState(
            current_level=next_level,
            policy=state.policy,
            history=history,
            promotion_evidence_start_index=next_promotion_start,
            last_evaluation=evaluation,
        )

    def evaluate_request(
        self,
        *,
        contribution_id: str,
        request: HumanContributionRequest,
        skill_record: SkillRecord | None,
        scenario: NurseryScenario,
        scenario_context: str,
        support_state: SupportState,
        interruption: HumanAuthorityInterruption | None = None,
    ) -> ContributionEvaluationResult:
        """Execute one Week 9 contribution attempt through the frozen controller."""
        capability_check = self.check_capability(
            request,
            skill_record,
            scenario_context=scenario_context,
        )
        if capability_check.status is not CapabilityStatus.VERIFIED or skill_record is None:
            record = self._build_pre_execution_failure(
                contribution_id=contribution_id,
                request=request,
                scenario=scenario,
                scenario_context=scenario_context,
                support_state=support_state,
                capability_check=capability_check,
                interruption=interruption,
            )
            updated = self.evaluate_support(support_state, record.evidence)
            return ContributionEvaluationResult(
                record=replace(record, support_level_after=updated.current_level),
                support_state=updated,
            )
        if interruption is not None:
            record = self._build_pre_execution_failure(
                contribution_id=contribution_id,
                request=request,
                scenario=scenario,
                scenario_context=scenario_context,
                support_state=support_state,
                capability_check=capability_check,
                interruption=interruption,
            )
            updated = self.evaluate_support(support_state, record.evidence)
            return ContributionEvaluationResult(
                record=replace(record, support_level_after=updated.current_level),
                support_state=updated,
            )

        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=contribution_id,
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )
        controller = ApproachAndPushSkillController(
            skill_record,
            target_object_id=request.target_object_id,
            target_id=request.target_id,
        )
        action_trace: list[str] = []
        outcome_trace: list[str] = []
        retained_steps = 0
        audit = ContributionShadowAudit()
        failure_reason: str | None = None
        last_transition_outcome: str | None = None
        while scenario.remaining_steps(runtime.state) > 0:
            audit = replace(audit, observations=audit.observations + 1)
            decision = controller.decide(
                runtime.state,
                runtime.observe().available_actions,
            )
            if decision.status is SkillExecutionStatus.TERMINATED:
                break
            if decision.status is not SkillExecutionStatus.ACTION or decision.action is None:
                failure_reason = decision.reason_code
                break
            retained = retain_skill_candidate_through_curiosity(decision)
            retained_action = retained.retained_action
            if retained_action is None:
                failure_reason = "retained_action_missing"
                break
            retained_steps += 1
            audit = replace(
                audit, production_actions_retained=audit.production_actions_retained + 1
            )
            if retained_action is not decision.action:
                audit = replace(
                    audit,
                    production_action_replacements=audit.production_action_replacements + 1,
                    authority_violations=audit.authority_violations + 1,
                )
            step = runtime.step(retained_action)
            action_trace.append(retained_action.value)
            last_transition_outcome = (
                "pushed"
                if step.transition.outcome.value == "pushed"
                else step.transition.outcome.value
            )
            outcome_trace.append(last_transition_outcome)
            if detect_target_occupancy(runtime.state).object_target_pairs == (
                (request.target_object_id, request.target_id),
            ):
                break
        verification = self.verify_grounded_outcome(
            request,
            runtime,
            evidence_sources=(
                VerificationEvidenceSource.RUNTIME_STATE,
                VerificationEvidenceSource.ACTUAL_TRANSITION,
            ),
            last_transition_outcome=last_transition_outcome,
        )
        success = verification.status is VerificationStatus.VERIFIED and audit.accepted
        if not success and failure_reason is None:
            failure_reason = verification.reason_code
        evidence = CapabilityEvidence(
            contribution_id=contribution_id,
            familiar_context=scenario_context in request.learned_context,
            independent_execution=True,
            success=success,
            verification_status=verification.status,
            evidence_fresh=True,
            contradictory=False,
            degraded=False,
            unsafe=not audit.accepted,
            context_mismatched=False,
            scenario_context=scenario_context,
        )
        failure_report = None
        if not success:
            failure_report = HonestFailureReport(
                reason=failure_reason or "unknown_failure",
                attempted_capability=request.target_capability,
                failed_preconditions=(
                    capability_check.failed_preconditions
                    or ((failure_reason,) if failure_reason is not None else ())
                ),
                interruption=None,
                uncertainty="grounded_runtime_outcome_did_not_verify",
                requested_support=request.requested_support_level,
                verification_status=verification.status,
                authority_audit=audit,
            )
        record = ContributionRecord(
            contribution_id=contribution_id,
            request=request,
            scenario_id=scenario.scenario_id,
            scenario_context=scenario_context,
            seed=scenario.seed,
            attempted_capability=request.target_capability,
            support_level_before=support_state.current_level,
            support_level_after=support_state.current_level,
            requested_support=request.requested_support_level,
            capability_check=capability_check,
            verification=verification,
            success=success,
            independent_execution=True,
            familiar_context=scenario_context in request.learned_context,
            executed_steps=len(action_trace),
            retained_steps=retained_steps,
            interruption=None,
            authority_audit=audit,
            failure_report=failure_report,
            evidence=evidence,
            action_trace=tuple(action_trace),
            outcome_trace=tuple(outcome_trace),
        )
        updated = self.evaluate_support(support_state, evidence)
        return ContributionEvaluationResult(
            record=replace(record, support_level_after=updated.current_level),
            support_state=updated,
        )

    def _blocker_codes(self, evidence: tuple[CapabilityEvidence, ...]) -> list[str]:
        blockers: list[str] = []
        if any(not item.evidence_fresh for item in evidence):
            blockers.append("stale_evidence_present")
        if any(item.contradictory for item in evidence):
            blockers.append("contradictory_evidence_present")
        if any(item.degraded for item in evidence):
            blockers.append("degraded_evidence_present")
        if any(item.unsafe for item in evidence):
            blockers.append("unsafe_evidence_present")
        if any(item.context_mismatched for item in evidence):
            blockers.append("context_mismatched_evidence_present")
        if any(item.verification_status is not VerificationStatus.VERIFIED for item in evidence):
            blockers.append("unverified_evidence_present")
        if (
            len(
                [
                    item
                    for item in evidence
                    if item.familiar_context
                    and item.independent_execution
                    and item.success
                    and item.verification_status is VerificationStatus.VERIFIED
                ]
            )
            < self.policy.minimum_verified_independent_familiar_successes
        ):
            blockers.append("insufficient_verified_successes")
        return blockers

    def _build_pre_execution_failure(
        self,
        *,
        contribution_id: str,
        request: HumanContributionRequest,
        scenario: NurseryScenario,
        scenario_context: str,
        support_state: SupportState,
        capability_check: CapabilityCheck,
        interruption: HumanAuthorityInterruption | None,
    ) -> ContributionRecord:
        reason = (
            interruption.value if interruption is not None else capability_check.reason_codes[0]
        )
        verification_status = (
            VerificationStatus.UNAVAILABLE
            if interruption is not None
            else VerificationStatus.REJECTED
        )
        verification = GroundedOutcomeVerification(
            status=verification_status,
            evidence_sources=(VerificationEvidenceSource.UNAVAILABLE,),
            reason_code="no_grounded_execution",
            target_achieved=False,
        )
        audit = ContributionShadowAudit()
        evidence = CapabilityEvidence(
            contribution_id=contribution_id,
            familiar_context=scenario_context in request.learned_context,
            independent_execution=False,
            success=False,
            verification_status=verification_status,
            evidence_fresh=True,
            contradictory=False,
            degraded=capability_check.status is CapabilityStatus.DEGRADED,
            unsafe=False,
            context_mismatched=capability_check.status is CapabilityStatus.CONTEXT_MISMATCHED,
            scenario_context=scenario_context,
        )
        failure_report = HonestFailureReport(
            reason=reason,
            attempted_capability=request.target_capability,
            failed_preconditions=capability_check.failed_preconditions,
            interruption=interruption,
            uncertainty="execution_did_not_start",
            requested_support=request.requested_support_level,
            verification_status=verification.status,
            authority_audit=audit,
        )
        return ContributionRecord(
            contribution_id=contribution_id,
            request=request,
            scenario_id=scenario.scenario_id,
            scenario_context=scenario_context,
            seed=scenario.seed,
            attempted_capability=request.target_capability,
            support_level_before=support_state.current_level,
            support_level_after=support_state.current_level,
            requested_support=request.requested_support_level,
            capability_check=capability_check,
            verification=verification,
            success=False,
            independent_execution=False,
            familiar_context=scenario_context in request.learned_context,
            executed_steps=0,
            retained_steps=0,
            interruption=interruption,
            authority_audit=audit,
            failure_report=failure_report,
            evidence=evidence,
            action_trace=(),
            outcome_trace=(),
        )
