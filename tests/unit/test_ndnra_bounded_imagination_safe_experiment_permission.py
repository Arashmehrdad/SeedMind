"""Tests for explicit human review of imagined safe-experiment proposals."""

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
    BoundedRouteComparisonConfig,
    BoundedRouteEvaluationConfig,
    BoundedSafeExperimentPermissionConfig,
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


def _proposal_result() -> tuple[LearnedConsequenceModel, ImaginedSafeExperimentProposalResult]:
    start = _context(0.9, ("cool", "save"))
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:permission:cool",
        context=start,
        action="cool",
        next_context=_context(0.4, ("rest",)),
        effects=(
            EffectObservation("energy_delta", -0.4, 1.0),
            EffectObservation("heat_delta", -0.5, 1.0),
        ),
    )
    _observe(
        model,
        event_id="real:permission:save",
        context=start,
        action="save",
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
            hypothesis="controlled_cooling_may_reduce_tradeoff_ambiguity",
            predicted_benefit="human_reviewed_trial_may_clarify_energy_heat_tradeoffs",
            uncertainty="current_tradeoff_evidence_remains_incomplete",
            possible_harm="trial_may_waste_energy_or_fail_to_reduce_heat",
            reversibility="trial_is_reversible_by_returning_to_rest_state",
            stop_conditions="stop_if_human_observer_records_instability",
            stop_condition_codes=(
                "halt_if_heat_rises",
                "halt_if_stress_spikes",
            ),
            required_permission="human_teacher_explicit_permission_required",
        )
    )
    return model, proposal


def _request(
    source_result: ImaginedSafeExperimentProposalResult | None = None,
    *,
    action: ImaginedSafeExperimentPermissionAction = (
        ImaginedSafeExperimentPermissionAction.APPROVE
    ),
    reviewer_code: str = "human:teacher",
    reason_code: str = "bounded_trial_reviewed",
    expected_proposal_id: str | None = None,
    expected_required_permission: str | None = None,
    acknowledgements: tuple[bool, bool, bool, bool, bool] = (
        True,
        True,
        True,
        True,
        True,
    ),
    config: BoundedSafeExperimentPermissionConfig | None = None,
) -> ImaginedSafeExperimentPermissionRequest:
    result = _proposal_result()[1] if source_result is None else source_result
    proposal = result.proposal
    return ImaginedSafeExperimentPermissionRequest(
        source_result=result,
        expected_proposal_id=(
            proposal.proposal_id if expected_proposal_id is None else expected_proposal_id
        ),
        expected_required_permission=(
            proposal.required_permission
            if expected_required_permission is None
            else expected_required_permission
        ),
        action=action,
        reviewer_code=reviewer_code,
        reason_code=reason_code,
        acknowledges_predicted_benefit=acknowledgements[0],
        acknowledges_uncertainty=acknowledgements[1],
        acknowledges_possible_harm=acknowledgements[2],
        acknowledges_reversibility=acknowledgements[3],
        acknowledges_stop_conditions=acknowledgements[4],
        config=(BoundedSafeExperimentPermissionConfig() if config is None else config),
    )


def _review(
    request: ImaginedSafeExperimentPermissionRequest,
) -> ImaginedSafeExperimentPermissionResult:
    return BoundedImaginedSafeExperimentPermissionReviewer().review(request)


def test_explicit_human_approval_preserves_exact_provenance_without_execution() -> None:
    request = _request()

    result = _review(request)
    decision = result.decision

    assert decision.source_result_id == request.source_result.result_id
    assert decision.source_request_id == request.source_result.request.request_id
    assert decision.source_proposal == request.source_result.proposal
    assert decision.proposal_origin is ExperienceOrigin.IMAGINED
    assert decision.action is ImaginedSafeExperimentPermissionAction.APPROVE
    assert decision.permission_granted
    assert not decision.review_deferred
    assert not decision.authorizes_execution
    assert not decision.authorizes_scheduling
    assert not decision.authorizes_persistence
    assert not decision.authorizes_live_integration
    assert not decision.has_action_selection_authority
    assert not decision.has_production_action_authority


def test_reject_and_defer_are_explicit_non_permission_outcomes() -> None:
    rejected = _review(
        _request(
            action=ImaginedSafeExperimentPermissionAction.REJECT,
            acknowledgements=(False, False, False, False, False),
        )
    ).decision
    deferred = _review(
        _request(
            action=ImaginedSafeExperimentPermissionAction.DEFER,
            acknowledgements=(False, True, True, False, True),
        )
    ).decision

    assert not rejected.permission_granted
    assert not rejected.review_deferred
    assert not deferred.permission_granted
    assert deferred.review_deferred


def test_approval_requires_every_explicit_acknowledgement() -> None:
    for missing_index in range(5):
        acknowledgements = [True] * 5
        acknowledgements[missing_index] = False
        with pytest.raises(ValueError, match="every proposal risk field"):
            _request(
                acknowledgements=cast(tuple[bool, bool, bool, bool, bool], tuple(acknowledgements))
            )


def test_review_requires_explicit_human_identity() -> None:
    with pytest.raises(ValueError, match="explicit human reviewer"):
        _request(reviewer_code="policy:auto_reviewer")


def test_review_action_requires_explicit_permission_enum() -> None:
    with pytest.raises(ValueError, match="permission action"):
        _request(action=cast(Any, "approve"))


def test_proposal_and_required_permission_mismatches_are_rejected() -> None:
    source = _proposal_result()[1]

    with pytest.raises(ValueError, match="different proposal"):
        _request(
            source,
            expected_proposal_id="imagined-safe-experiment-proposal:wrong",
        )
    with pytest.raises(ValueError, match="different required permission"):
        _request(
            source,
            expected_required_permission="human:different_permission",
        )


def test_tampered_source_result_is_rejected_before_review() -> None:
    source = _proposal_result()[1]
    object.__setattr__(source.proposal, "required_permission", "tampered_permission")

    with pytest.raises(ValueError, match="inconsistent with request"):
        _request(source)


def test_permission_review_bounds_are_enforced_atomically() -> None:
    source = _proposal_result()[1]
    snapshot_size = len(source.snapshot_json_ascii())

    with pytest.raises(ValueError, match="byte bound"):
        _request(
            source,
            config=BoundedSafeExperimentPermissionConfig(
                maximum_source_snapshot_bytes=snapshot_size - 1,
            ),
        )
    with pytest.raises(ValueError, match="reviewer_code exceeds"):
        _request(
            source,
            reviewer_code="human:teacher",
            config=BoundedSafeExperimentPermissionConfig(
                maximum_reviewer_code_characters=5,
            ),
        )
    with pytest.raises(ValueError, match="reason_code exceeds"):
        _request(
            source,
            reason_code="bounded_trial_reviewed",
            config=BoundedSafeExperimentPermissionConfig(
                maximum_reason_code_characters=5,
            ),
        )


def test_permission_config_requires_positive_integer_bounds() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        BoundedSafeExperimentPermissionConfig(maximum_source_snapshot_bytes=0)
    with pytest.raises(ValueError, match="positive integer"):
        BoundedSafeExperimentPermissionConfig(maximum_reason_code_characters=True)


def test_repeated_reviews_have_stable_ascii_identities() -> None:
    source = _proposal_result()[1]
    first_request = _request(source)
    second_request = _request(source)

    first = _review(first_request)
    second = _review(second_request)

    assert first_request.request_id == second_request.request_id
    assert first.decision.decision_id == second.decision.decision_id
    assert first.result_id == second.result_id
    assert first.snapshot_json_ascii() == second.snapshot_json_ascii()
    assert first.snapshot_json_ascii().decode("ascii")


def test_distinct_human_dispositions_produce_distinct_identities() -> None:
    source = _proposal_result()[1]
    approved = _review(_request(source))
    rejected = _review(
        _request(
            source,
            action=ImaginedSafeExperimentPermissionAction.REJECT,
            reason_code="risk_not_acceptable",
            acknowledgements=(False, False, True, False, True),
        )
    )

    assert approved.decision.decision_id != rejected.decision.decision_id
    assert approved.result_id != rejected.result_id
    assert approved.decision.source_proposal == rejected.decision.source_proposal


def test_zero_deltas_and_authority_remain_exact_on_every_layer() -> None:
    request = _request()
    result = _review(request)
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


def test_result_rejects_tampered_decision() -> None:
    request = _request()
    result = _review(request)
    object.__setattr__(result.decision, "permission_granted", False)

    with pytest.raises(ValueError, match="inconsistent with request"):
        ImaginedSafeExperimentPermissionResult(
            result_id=result.result_id,
            request=request,
            decision=result.decision,
        )


def test_permission_review_cannot_be_recorded_as_real_consequence_evidence() -> None:
    model, proposal = _proposal_result()
    result = _review(_request(proposal))
    before = model.snapshot()

    with pytest.raises((AttributeError, ValueError)):
        model.observe(cast(Any, result))

    assert model.snapshot() == before


def test_permission_module_has_no_runtime_persistence_or_selection_dependencies() -> None:
    source = Path(
        "src/seedmind/research/ndnra/bounded_imagination_safe_experiment_permission.py"
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
        "execute(",
        "schedule(",
        "persist(",
        "recommend(",
        "optimize(",
        "optimise(",
    ):
        assert forbidden not in lowered
