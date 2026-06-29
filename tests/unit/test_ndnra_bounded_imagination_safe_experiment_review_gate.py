"""Tests for explicit training review and configured non-training bypass."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

import pytest

from seedmind.research.ndnra import (
    BoundedCandidateGenerationConfig,
    BoundedComparisonUncertaintyConfig,
    BoundedExactCandidateGenerator,
    BoundedImaginedComparisonUncertaintyAuditor,
    BoundedImaginedRouteComparator,
    BoundedImaginedRouteEvaluator,
    BoundedImaginedSafeExperimentPermissionReviewer,
    BoundedImaginedSafeExperimentProposer,
    BoundedImaginedSafeExperimentReviewGate,
    BoundedRouteComparisonConfig,
    BoundedRouteEvaluationConfig,
    BoundedSafeExperimentReviewGateConfig,
    ConsequenceModelObservation,
    ContextSignature,
    EffectNeed,
    EffectObservation,
    ExperienceOrigin,
    ImaginedCandidateGenerationRequest,
    ImaginedComparisonUncertaintyRequest,
    ImaginedRouteComparisonRequest,
    ImaginedRouteEvaluationRequest,
    ImaginedSafeExperimentPermissionAction,
    ImaginedSafeExperimentPermissionRequest,
    ImaginedSafeExperimentPermissionResult,
    ImaginedSafeExperimentProposalRequest,
    ImaginedSafeExperimentProposalResult,
    ImaginedSafeExperimentReviewGateRequest,
    ImaginedSafeExperimentReviewGateResult,
    ImaginedSafeExperimentReviewGateStatus,
    ImaginedSafeExperimentReviewMode,
    LearnedConsequenceModel,
    NeedDimension,
)


def _context(heat: float, actions: tuple[str, ...]) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code="cooling",
        sensor_values=(heat,),
        available_action_codes=actions,
    )


def _need() -> EffectNeed:
    return EffectNeed(
        need_code="cooling",
        primary_effect_code="heat_delta",
        dimensions=(
            NeedDimension("energy_delta", 1.0, 0.5),
            NeedDimension("heat_delta", -1.0, 1.0),
        ),
        satisfaction_threshold=0.5,
    )


def _observe(
    model: LearnedConsequenceModel,
    *,
    event_id: str,
    context: ContextSignature,
    action: str,
    next_context: ContextSignature,
    effects: tuple[EffectObservation, ...],
) -> None:
    model.observe(
        ConsequenceModelObservation(
            event_id=event_id,
            origin=ExperienceOrigin.REAL,
            context=context,
            action_code=action,
            next_context=next_context,
            observed_effects=effects,
        )
    )


def _proposal_result(
    tag: str = "primary",
) -> tuple[LearnedConsequenceModel, ImaginedSafeExperimentProposalResult]:
    cool_action = f"cool_{tag}"
    save_action = f"save_{tag}"
    start = _context(0.9, (cool_action, save_action))
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id=f"real:review-gate:{tag}:cool",
        context=start,
        action=cool_action,
        next_context=_context(0.4, ("rest",)),
        effects=(
            EffectObservation("energy_delta", -0.4, 1.0),
            EffectObservation("heat_delta", -0.5, 1.0),
        ),
    )
    _observe(
        model,
        event_id=f"real:review-gate:{tag}:save",
        context=start,
        action=save_action,
        next_context=_context(0.7, ("rest",)),
        effects=(
            EffectObservation("energy_delta", 0.2, 1.0),
            EffectObservation("heat_delta", -0.2, 1.0),
        ),
    )
    candidates = (
        BoundedExactCandidateGenerator(model)
        .generate(
            ImaginedCandidateGenerationRequest(
                context=start,
                requested_effect_codes=("energy_delta", "heat_delta"),
                config=BoundedCandidateGenerationConfig(
                    maximum_sequence_depth=1,
                    maximum_branch_actions_per_prefix=2,
                    maximum_generated_candidates=2,
                ),
            )
        )
        .candidates
    )
    evaluation = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need(),
            candidates=candidates,
            config=BoundedRouteEvaluationConfig(neutral_tolerance=0.05),
        )
    )
    comparison = BoundedImaginedRouteComparator().compare(
        ImaginedRouteComparisonRequest(
            source_result=evaluation,
            config=BoundedRouteComparisonConfig(confidence_floor=0.0),
        )
    )
    uncertainty = BoundedImaginedComparisonUncertaintyAuditor().audit(
        ImaginedComparisonUncertaintyRequest(
            source_result=comparison,
            config=BoundedComparisonUncertaintyConfig(),
        )
    )
    proposal = BoundedImaginedSafeExperimentProposer().propose(
        ImaginedSafeExperimentProposalRequest(
            source_result=uncertainty,
            issue_id=uncertainty.issues[0].issue_id,
            hypothesis=f"controlled_{tag}_trial_may_reduce_ambiguity",
            predicted_benefit="bounded_trial_may_clarify_tradeoffs",
            uncertainty="current_tradeoff_evidence_remains_incomplete",
            possible_harm="trial_may_waste_energy_or_fail_to_reduce_heat",
            reversibility="trial_is_reversible_by_returning_to_rest_state",
            stop_conditions="stop_if_observed_instability_is_recorded",
            stop_condition_codes=("halt_if_heat_rises", "halt_if_stress_spikes"),
            required_permission="human_teacher_training_permission",
        )
    )
    return model, proposal


def _permission_result(
    source: ImaginedSafeExperimentProposalResult,
    action: ImaginedSafeExperimentPermissionAction,
) -> ImaginedSafeExperimentPermissionResult:
    approved = action is ImaginedSafeExperimentPermissionAction.APPROVE
    return BoundedImaginedSafeExperimentPermissionReviewer().review(
        ImaginedSafeExperimentPermissionRequest(
            source_result=source,
            expected_proposal_id=source.proposal.proposal_id,
            expected_required_permission=source.proposal.required_permission,
            action=action,
            reviewer_code="human:teacher",
            reason_code=f"training_{action.value}",
            acknowledges_predicted_benefit=approved,
            acknowledges_uncertainty=True,
            acknowledges_possible_harm=True,
            acknowledges_reversibility=approved,
            acknowledges_stop_conditions=True,
        )
    )


def _resolve(
    source: ImaginedSafeExperimentProposalResult,
    *,
    mode: ImaginedSafeExperimentReviewMode,
    permission: ImaginedSafeExperimentPermissionResult | None = None,
    bypass_requested: bool = False,
    bypass_policy_code: str | None = None,
    allow_bypass: bool = False,
) -> ImaginedSafeExperimentReviewGateResult:
    return BoundedImaginedSafeExperimentReviewGate().resolve(
        ImaginedSafeExperimentReviewGateRequest(
            source_result=source,
            mode=mode,
            permission_result=permission,
            bypass_requested=bypass_requested,
            bypass_policy_code=bypass_policy_code,
            config=BoundedSafeExperimentReviewGateConfig(
                allow_non_training_bypass=allow_bypass,
            ),
        )
    )


def test_training_without_review_remains_explicitly_required() -> None:
    source = _proposal_result()[1]

    decision = _resolve(source, mode=ImaginedSafeExperimentReviewMode.TRAINING).decision

    assert decision.status is ImaginedSafeExperimentReviewGateStatus.REVIEW_REQUIRED
    assert decision.review_required
    assert not decision.review_satisfied
    assert not decision.bypass_applied
    assert decision.permission_result_id is None
    assert decision.bypass_policy_code is None


def test_training_approval_is_review_evidence_without_execution() -> None:
    source = _proposal_result()[1]
    permission = _permission_result(
        source,
        ImaginedSafeExperimentPermissionAction.APPROVE,
    )

    decision = _resolve(
        source,
        mode=ImaginedSafeExperimentReviewMode.TRAINING,
        permission=permission,
    ).decision

    assert decision.status is ImaginedSafeExperimentReviewGateStatus.REVIEW_APPROVED
    assert decision.review_satisfied
    assert decision.permission_result_id == permission.result_id
    assert decision.permission_decision_id == permission.decision.decision_id
    assert not decision.authorizes_execution
    assert not decision.authorizes_scheduling
    assert not decision.authorizes_persistence
    assert not decision.authorizes_live_integration


def test_training_reject_and_defer_remain_distinct_non_approval_outcomes() -> None:
    source = _proposal_result()[1]
    rejected = _resolve(
        source,
        mode=ImaginedSafeExperimentReviewMode.TRAINING,
        permission=_permission_result(
            source,
            ImaginedSafeExperimentPermissionAction.REJECT,
        ),
    ).decision
    deferred = _resolve(
        source,
        mode=ImaginedSafeExperimentReviewMode.TRAINING,
        permission=_permission_result(
            source,
            ImaginedSafeExperimentPermissionAction.DEFER,
        ),
    ).decision

    assert rejected.status is ImaginedSafeExperimentReviewGateStatus.REVIEW_REJECTED
    assert deferred.status is ImaginedSafeExperimentReviewGateStatus.REVIEW_DEFERRED
    assert not rejected.review_satisfied
    assert not deferred.review_satisfied
    assert not rejected.bypass_applied
    assert not deferred.bypass_applied


def test_explicit_non_training_bypass_requires_enabled_policy() -> None:
    source = _proposal_result()[1]

    decision = _resolve(
        source,
        mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
        bypass_requested=True,
        bypass_policy_code="runtime-policy:autonomous_operation_v1",
        allow_bypass=True,
    ).decision

    assert decision.status is (ImaginedSafeExperimentReviewGateStatus.EXPLICIT_NON_TRAINING_BYPASS)
    assert decision.bypass_applied
    assert not decision.review_required
    assert not decision.review_satisfied
    assert decision.bypass_policy_code == "runtime-policy:autonomous_operation_v1"
    assert decision.permission_result_id is None
    assert not decision.authorizes_execution


def test_missing_review_is_never_an_implicit_bypass() -> None:
    source = _proposal_result()[1]

    decision = _resolve(
        source,
        mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
        allow_bypass=True,
    ).decision

    assert decision.status is ImaginedSafeExperimentReviewGateStatus.REVIEW_REQUIRED
    assert decision.review_required
    assert not decision.bypass_applied


def test_training_bypass_is_forbidden_even_when_policy_capability_is_enabled() -> None:
    source = _proposal_result()[1]

    with pytest.raises(ValueError, match="forbidden in training"):
        _resolve(
            source,
            mode=ImaginedSafeExperimentReviewMode.TRAINING,
            bypass_requested=True,
            bypass_policy_code="runtime-policy:not_valid_for_training",
            allow_bypass=True,
        )


def test_non_training_bypass_must_be_enabled_and_explicitly_identified() -> None:
    source = _proposal_result()[1]

    with pytest.raises(ValueError, match="disabled by policy"):
        _resolve(
            source,
            mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
            bypass_requested=True,
            bypass_policy_code="runtime-policy:disabled",
        )
    with pytest.raises(ValueError, match="requires a policy code"):
        _resolve(
            source,
            mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
            bypass_requested=True,
            allow_bypass=True,
        )
    with pytest.raises(ValueError, match="explicit runtime policy"):
        _resolve(
            source,
            mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
            bypass_requested=True,
            bypass_policy_code="human:implicit_override",
            allow_bypass=True,
        )


def test_policy_code_without_bypass_request_is_rejected() -> None:
    source = _proposal_result()[1]

    with pytest.raises(ValueError, match="requires an explicit bypass request"):
        _resolve(
            source,
            mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
            bypass_policy_code="runtime-policy:unused",
            allow_bypass=True,
        )


def test_bypass_cannot_be_combined_with_permission_evidence() -> None:
    source = _proposal_result()[1]
    permission = _permission_result(
        source,
        ImaginedSafeExperimentPermissionAction.APPROVE,
    )

    with pytest.raises(ValueError, match="cannot be combined"):
        _resolve(
            source,
            mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
            permission=permission,
            bypass_requested=True,
            bypass_policy_code="runtime-policy:exclusive_path",
            allow_bypass=True,
        )


def test_permission_result_must_target_the_exact_proposal_result() -> None:
    source = _proposal_result("primary")[1]
    other = _proposal_result("other")[1]
    other_permission = _permission_result(
        other,
        ImaginedSafeExperimentPermissionAction.APPROVE,
    )

    with pytest.raises(ValueError, match="different proposal result"):
        _resolve(
            source,
            mode=ImaginedSafeExperimentReviewMode.TRAINING,
            permission=other_permission,
        )


def test_review_gate_bounds_and_types_are_enforced() -> None:
    source = _proposal_result()[1]
    snapshot_size = len(source.snapshot_json_ascii())

    with pytest.raises(ValueError, match="byte bound"):
        BoundedImaginedSafeExperimentReviewGate().resolve(
            ImaginedSafeExperimentReviewGateRequest(
                source_result=source,
                mode=ImaginedSafeExperimentReviewMode.TRAINING,
                config=BoundedSafeExperimentReviewGateConfig(
                    maximum_source_snapshot_bytes=snapshot_size - 1,
                ),
            )
        )
    with pytest.raises(ValueError, match="character bound"):
        ImaginedSafeExperimentReviewGateRequest(
            source_result=source,
            mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
            bypass_requested=True,
            bypass_policy_code="runtime-policy:too_long",
            config=BoundedSafeExperimentReviewGateConfig(
                allow_non_training_bypass=True,
                maximum_bypass_policy_code_characters=5,
            ),
        )
    with pytest.raises(ValueError, match="review mode"):
        ImaginedSafeExperimentReviewGateRequest(
            source_result=source,
            mode=cast(Any, "training"),
        )
    with pytest.raises(ValueError, match="must be boolean"):
        BoundedSafeExperimentReviewGateConfig(
            allow_non_training_bypass=cast(Any, "yes"),
        )


def test_repeated_gate_resolutions_have_stable_ascii_identities() -> None:
    source = _proposal_result()[1]
    first_request = ImaginedSafeExperimentReviewGateRequest(
        source_result=source,
        mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
        bypass_requested=True,
        bypass_policy_code="runtime-policy:stable",
        config=BoundedSafeExperimentReviewGateConfig(
            allow_non_training_bypass=True,
        ),
    )
    second_request = ImaginedSafeExperimentReviewGateRequest(
        source_result=source,
        mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
        bypass_requested=True,
        bypass_policy_code="runtime-policy:stable",
        config=BoundedSafeExperimentReviewGateConfig(
            allow_non_training_bypass=True,
        ),
    )

    first = BoundedImaginedSafeExperimentReviewGate().resolve(first_request)
    second = BoundedImaginedSafeExperimentReviewGate().resolve(second_request)

    assert first_request.request_id == second_request.request_id
    assert first.decision.decision_id == second.decision.decision_id
    assert first.result_id == second.result_id
    assert first.snapshot_json_ascii() == second.snapshot_json_ascii()
    assert first.snapshot_json_ascii().decode("ascii")


def test_zero_deltas_and_authority_remain_exact_on_every_layer() -> None:
    source = _proposal_result()[1]
    request = ImaginedSafeExperimentReviewGateRequest(
        source_result=source,
        mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
        bypass_requested=True,
        bypass_policy_code="runtime-policy:bounded",
        config=BoundedSafeExperimentReviewGateConfig(
            allow_non_training_bypass=True,
        ),
    )
    result = BoundedImaginedSafeExperimentReviewGate().resolve(request)
    layers: tuple[Any, ...] = (request, result.decision, result)

    for layer in layers:
        assert layer.factual_confidence_change == 0.0
        assert layer.mastery_change == 0.0
        assert layer.competence_change == 0.0
        assert layer.growth_pressure_change == 0.0
        assert layer.replay_evidence_change == 0.0
        assert layer.real_observation_change == 0.0
        assert layer.has_action_selection_authority is False
        assert layer.has_production_action_authority is False


def test_result_rejects_tampered_gate_decision() -> None:
    source = _proposal_result()[1]
    result = _resolve(source, mode=ImaginedSafeExperimentReviewMode.TRAINING)
    object.__setattr__(result.decision, "review_required", False)

    with pytest.raises(ValueError, match="inconsistent with request"):
        ImaginedSafeExperimentReviewGateResult(
            result_id=result.result_id,
            request=result.request,
            decision=result.decision,
        )


def test_review_gate_result_cannot_be_recorded_as_real_consequence_evidence() -> None:
    model, proposal = _proposal_result()
    result = _resolve(
        proposal,
        mode=ImaginedSafeExperimentReviewMode.NON_TRAINING,
        bypass_requested=True,
        bypass_policy_code="runtime-policy:no_evidence",
        allow_bypass=True,
    )
    before = model.snapshot()

    with pytest.raises((AttributeError, ValueError)):
        model.observe(cast(Any, result))

    assert model.snapshot() == before


def test_review_gate_has_no_execution_persistence_or_selection_dependencies() -> None:
    source = Path(
        "src/seedmind/research/ndnra/bounded_imagination_safe_experiment_review_gate.py"
    ).read_text(encoding="ascii")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_prefixes = (
        "sqlite3",
        "asyncio",
        "threading",
        "time",
        "queue",
        "seedmind.integration",
        "seedmind.environment",
        "seedmind.curiosity",
        "seedmind.research.ndnra.persistence",
        "seedmind.research.ndnra.consolidation",
        "seedmind.research.ndnra.bounded_imagination_candidates",
        "seedmind.research.ndnra.bounded_imagination_evaluation",
        "seedmind.research.ndnra.bounded_imagination_comparison",
        "seedmind.research.ndnra.bounded_imagination_uncertainty",
    )
    for forbidden in forbidden_prefixes:
        assert not any(
            module == forbidden or module.startswith(f"{forbidden}.") for module in imported_modules
        )

    lowered = source.lower()
    for forbidden in (
        ".generate(",
        ".imagine(",
        ".evaluate(",
        ".compare(",
        ".audit(",
        ".propose(",
        ".review(",
        "execute(",
        "schedule(",
        "persist(",
        "recommend(",
        "optimize(",
        "optimise(",
    ):
        assert forbidden not in lowered
