"""Focused tests for the Week 9 contribution engine."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from seedmind.contribution import (
    CapabilityEvidence,
    CapabilityStatus,
    ContributionEngine,
    HumanAuthorityInterruption,
    SupportPolicy,
    SupportState,
    VerificationEvidenceSource,
    VerificationStatus,
)
from seedmind.contribution.week9 import (
    _blocked_failure_scenario,
    _build_request,
    _scenario_context,
)
from seedmind.environment import NurseryRuntime
from seedmind.human import SupportLevel
from seedmind.skills import SkillValidationStatus, Week8ScenarioFactory, read_skill_record


def _evidence(
    contribution_id: str,
    scenario_context: str,
    *,
    success: bool = True,
    verification_status: VerificationStatus = VerificationStatus.VERIFIED,
    evidence_fresh: bool = True,
    contradictory: bool = False,
    degraded: bool = False,
    unsafe: bool = False,
    context_mismatched: bool = False,
) -> CapabilityEvidence:
    return CapabilityEvidence(
        contribution_id=contribution_id,
        familiar_context=True,
        independent_execution=True,
        success=success,
        verification_status=verification_status,
        evidence_fresh=evidence_fresh,
        contradictory=contradictory,
        degraded=degraded,
        unsafe=unsafe,
        context_mismatched=context_mismatched,
        scenario_context=scenario_context,
    )


def test_capability_check_rejects_missing_unvalidated_degraded_and_mismatched_skill() -> None:
    engine = ContributionEngine()
    request = _build_request(request_id="request-capability")
    record = read_skill_record(
        Path("artifacts/week8_reusable_skill/approach_and_push_skill_record.json")
    )

    missing = engine.check_capability(request, None, scenario_context="familiar_row")
    unproven = engine.check_capability(
        request,
        record.with_validation_status(SkillValidationStatus.UNVALIDATED),
        scenario_context="familiar_row",
    )
    degraded = engine.check_capability(
        request,
        record.with_validation_status(SkillValidationStatus.FAILED),
        scenario_context="familiar_row",
    )
    mismatched = engine.check_capability(
        request,
        record,
        scenario_context="unknown_context",
    )

    assert missing.status is CapabilityStatus.UNAVAILABLE
    assert unproven.status is CapabilityStatus.UNPROVEN
    assert degraded.status is CapabilityStatus.DEGRADED
    assert mismatched.status is CapabilityStatus.CONTEXT_MISMATCHED


def test_grounded_verification_rejects_self_report_and_unavailable_evidence() -> None:
    engine = ContributionEngine()
    request = _build_request(request_id="request-verify")
    scenario = Week8ScenarioFactory().create(301)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id="verify-runtime",
        resource_state_provider=scenario.resource_state,
    )

    rejected = engine.verify_grounded_outcome(
        request,
        runtime,
        evidence_sources=(VerificationEvidenceSource.SELF_REPORT,),
        last_transition_outcome=None,
    )

    assert rejected.status is VerificationStatus.REJECTED
    assert rejected.reason_code == "rejected_non_grounded_evidence"


def test_grounded_verification_rejects_other_non_grounded_sources() -> None:
    engine = ContributionEngine()
    request = _build_request(request_id="request-verify-other")
    scenario = Week8ScenarioFactory().create(301)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id="verify-runtime-other",
        resource_state_provider=scenario.resource_state,
    )

    for source in (
        VerificationEvidenceSource.PRODUCER_VERIFIER_AGREEMENT,
        VerificationEvidenceSource.NDNRA_AGREEMENT,
        VerificationEvidenceSource.IMAGINATION,
        VerificationEvidenceSource.UNAVAILABLE,
    ):
        rejected = engine.verify_grounded_outcome(
            request,
            runtime,
            evidence_sources=(source,),
            last_transition_outcome=None,
        )

    assert rejected.status is VerificationStatus.REJECTED
    assert rejected.reason_code == "rejected_non_grounded_evidence"


def test_human_interruptions_are_immediate_and_authoritative() -> None:
    engine = ContributionEngine()
    scenario = Week8ScenarioFactory().create(301)
    record = read_skill_record(
        Path("artifacts/week8_reusable_skill/approach_and_push_skill_record.json")
    )

    for interruption in HumanAuthorityInterruption:
        result = engine.evaluate_request(
            contribution_id=f"interrupt-{interruption.value}",
            request=_build_request(request_id=f"request-{interruption.value}"),
            skill_record=record,
            scenario=scenario,
            scenario_context=_scenario_context(301),
            support_state=SupportState.fresh(),
            interruption=interruption,
        )

        assert result.record.executed_steps == 0
        assert result.record.retained_steps == 0
        assert result.record.independent_execution is False
        assert result.record.evidence.independent_execution is False
        assert result.record.interruption is interruption
        assert result.record.failure_report is not None


def test_support_policy_blocks_reduction_on_one_success_and_restores_after_two_failures() -> None:
    engine = ContributionEngine(SupportPolicy())
    base = SupportState.fresh(engine.policy)
    success = CapabilityEvidence(
        contribution_id="c-001",
        familiar_context=True,
        independent_execution=True,
        success=True,
        verification_status=VerificationStatus.VERIFIED,
        evidence_fresh=True,
        contradictory=False,
        degraded=False,
        unsafe=False,
        context_mismatched=False,
        scenario_context="familiar_row",
    )
    state = engine.evaluate_support(base, success)
    assert state.current_level is SupportLevel.DEPENDENT
    state = replace(state, current_level=SupportLevel.GUIDED_LEARNER)
    failure = CapabilityEvidence(
        contribution_id="c-002",
        familiar_context=True,
        independent_execution=True,
        success=False,
        verification_status=VerificationStatus.REJECTED,
        evidence_fresh=True,
        contradictory=False,
        degraded=False,
        unsafe=False,
        context_mismatched=False,
        scenario_context="familiar_column",
    )
    state = engine.evaluate_support(state, failure)
    state = engine.evaluate_support(state, replace(failure, contribution_id="c-003"))
    assert state.current_level is SupportLevel.DEPENDENT


def test_grounded_blocked_failure_stays_grounded_and_unsuccessful() -> None:
    engine = ContributionEngine()
    scenario = _blocked_failure_scenario(Week8ScenarioFactory().create(321))
    result = engine.evaluate_request(
        contribution_id="failure-001",
        request=_build_request(request_id="request-failure"),
        skill_record=read_skill_record(
            Path("artifacts/week8_reusable_skill/approach_and_push_skill_record.json")
        ),
        scenario=scenario,
        scenario_context=_scenario_context(321),
        support_state=SupportState.fresh(),
    )

    assert result.record.success is False
    assert result.record.failure_report is not None
    assert result.record.capability_check.status is CapabilityStatus.VERIFIED
    assert result.record.verification.status is VerificationStatus.REJECTED
    assert result.record.failure_report.reason == "no_legal_approach_path"
    assert result.record.failure_report.failed_preconditions == ("no_legal_approach_path",)
    assert result.record.failure_report.attempted_capability == "approach_and_push"
    assert result.record.failure_report.uncertainty == "grounded_runtime_outcome_did_not_verify"
    assert result.record.failure_report.requested_support is SupportLevel.DEPENDENT


def test_support_repromotion_requires_five_new_successes_after_regression() -> None:
    engine = ContributionEngine()
    state = SupportState.fresh()
    contexts = ("familiar_row", "familiar_column", "familiar_diagonal")
    for index in range(5):
        state = engine.evaluate_support(
            state,
            _evidence(f"initial-{index}", contexts[index % len(contexts)]),
        )
    assert state.current_level is SupportLevel.GUIDED_LEARNER

    for index in range(2):
        state = engine.evaluate_support(
            state,
            _evidence(
                f"failure-{index}",
                contexts[index],
                success=False,
                verification_status=VerificationStatus.REJECTED,
            ),
        )
    assert state.current_level is SupportLevel.DEPENDENT
    assert state.promotion_evidence_start_index == 7

    for index in range(4):
        state = engine.evaluate_support(
            state,
            _evidence(f"recovery-{index}", contexts[index % len(contexts)]),
        )
        assert state.current_level is SupportLevel.DEPENDENT
    state = engine.evaluate_support(state, _evidence("recovery-4", "familiar_column"))
    assert state.current_level is SupportLevel.GUIDED_LEARNER
    state = engine.evaluate_support(state, _evidence("steady", "familiar_diagonal"))
    assert state.current_level is SupportLevel.GUIDED_LEARNER


def test_weak_or_unverified_evidence_blocks_support_reduction() -> None:
    engine = ContributionEngine()
    contexts = ("familiar_row", "familiar_column", "familiar_diagonal")
    stale_state = SupportState.fresh()
    contradictory_state = SupportState.fresh()
    mismatched_state = SupportState.fresh()
    rejected_state = SupportState.fresh()

    for index in range(5):
        context = contexts[index % len(contexts)]
        stale_evidence = _evidence(f"stale-{index}", context)
        contradictory_evidence = _evidence(f"contradictory-{index}", context)
        mismatched_evidence = _evidence(f"mismatched-{index}", context)
        rejected_evidence = _evidence(f"rejected-{index}", context)

        if index == 4:
            stale_evidence = replace(stale_evidence, evidence_fresh=False)
            contradictory_evidence = replace(contradictory_evidence, contradictory=True)
            mismatched_evidence = replace(mismatched_evidence, context_mismatched=True)
            rejected_evidence = replace(
                rejected_evidence,
                success=False,
                verification_status=VerificationStatus.REJECTED,
            )

        stale_state = engine.evaluate_support(stale_state, stale_evidence)
        contradictory_state = engine.evaluate_support(contradictory_state, contradictory_evidence)
        mismatched_state = engine.evaluate_support(mismatched_state, mismatched_evidence)
        rejected_state = engine.evaluate_support(rejected_state, rejected_evidence)

    assert stale_state.current_level is SupportLevel.DEPENDENT
    assert contradictory_state.current_level is SupportLevel.DEPENDENT
    assert mismatched_state.current_level is SupportLevel.DEPENDENT
    assert rejected_state.current_level is SupportLevel.DEPENDENT


def test_unverified_evidence_blocks_promotion_even_with_five_verified_successes() -> None:
    engine = ContributionEngine()
    contexts = ("familiar_row", "familiar_column", "familiar_diagonal")
    state = engine.evaluate_support(
        SupportState.fresh(),
        _evidence(
            "unverified-first",
            "familiar_row",
            success=False,
            verification_status=VerificationStatus.UNAVAILABLE,
        ),
    )
    for index in range(5):
        state = engine.evaluate_support(
            state,
            _evidence(f"verified-{index}", contexts[index % len(contexts)]),
        )

    assert state.current_level is SupportLevel.DEPENDENT
    assert "unverified_evidence_present" in state.last_evaluation.blocker_codes


def test_degraded_or_unsafe_competence_restores_dependent_support_immediately() -> None:
    engine = ContributionEngine()
    contexts = ("familiar_row", "familiar_column", "familiar_diagonal")
    degraded_state = SupportState.fresh()
    unsafe_state = SupportState.fresh()

    for index in range(5):
        context = contexts[index % len(contexts)]
        degraded_state = engine.evaluate_support(
            degraded_state,
            _evidence(f"promote-degraded-{index}", context),
        )
        unsafe_state = engine.evaluate_support(
            unsafe_state,
            _evidence(f"promote-unsafe-{index}", context),
        )

    assert degraded_state.current_level is SupportLevel.GUIDED_LEARNER
    assert unsafe_state.current_level is SupportLevel.GUIDED_LEARNER

    degraded_regression = replace(
        _evidence(
            "regress-degraded",
            "familiar_row",
            success=False,
            verification_status=VerificationStatus.REJECTED,
        ),
        degraded=True,
    )
    unsafe_regression = replace(
        _evidence(
            "regress-unsafe",
            "familiar_row",
            success=False,
            verification_status=VerificationStatus.REJECTED,
        ),
        unsafe=True,
    )

    degraded_state = engine.evaluate_support(degraded_state, degraded_regression)
    unsafe_state = engine.evaluate_support(unsafe_state, unsafe_regression)

    assert degraded_state.current_level is SupportLevel.DEPENDENT
    assert degraded_state.promotion_evidence_start_index == len(degraded_state.history)
    assert unsafe_state.current_level is SupportLevel.DEPENDENT
    assert unsafe_state.promotion_evidence_start_index == len(unsafe_state.history)
