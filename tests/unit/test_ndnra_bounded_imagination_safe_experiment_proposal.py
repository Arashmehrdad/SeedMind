"""Tests for bounded caller-nominated safe-experiment proposal contracts."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any

import pytest

from seedmind.research.ndnra import (
    BoundedCandidateGenerationConfig,
    BoundedComparisonUncertaintyConfig,
    BoundedExactCandidateGenerator,
    BoundedImaginedComparisonUncertaintyAuditor,
    BoundedImaginedRouteComparator,
    BoundedImaginedRouteEvaluator,
    BoundedImaginedSafeExperimentProposer,
    BoundedRouteComparisonConfig,
    BoundedRouteEvaluationConfig,
    ConsequenceModelObservation,
    ContextSignature,
    EffectNeed,
    EffectObservation,
    ExperienceOrigin,
    ImaginedCandidateGenerationRequest,
    ImaginedComparisonUncertaintyRequest,
    ImaginedComparisonUncertaintyResult,
    ImaginedRouteComparisonRequest,
    ImaginedRouteEvaluationRequest,
    ImaginedSafeExperimentProposalRequest,
    ImaginedSafeExperimentProposalResult,
    LearnedConsequenceModel,
    NeedDimension,
)


def _context(
    heat: float,
    actions: tuple[str, ...],
    *,
    need: str = "cooling",
) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code=need,
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


def _source_result() -> ImaginedComparisonUncertaintyResult:
    start = _context(0.9, ("cool", "save"))
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:proposal:cool",
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
        event_id="real:proposal:save",
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
    return BoundedImaginedComparisonUncertaintyAuditor().audit(
        ImaginedComparisonUncertaintyRequest(
            source_result=comparison,
            config=BoundedComparisonUncertaintyConfig(),
        )
    )


def _request(
    source_result: ImaginedComparisonUncertaintyResult | None = None,
    *,
    issue_id: str | None = None,
    stop_condition_codes: tuple[str, ...] = ("halt_if_heat_rises", "halt_if_stress_spikes"),
) -> ImaginedSafeExperimentProposalRequest:
    result = _source_result() if source_result is None else source_result
    nominated_issue_id = result.issues[0].issue_id if issue_id is None else issue_id
    return ImaginedSafeExperimentProposalRequest(
        source_result=result,
        issue_id=nominated_issue_id,
        hypothesis="controlled_cooling_may_reduce_tradeoff_ambiguity",
        predicted_benefit="human_reviewed_trial_may_clarify_energy_heat_tradeoffs",
        uncertainty="current_tradeoff_evidence_remains_incomplete",
        possible_harm="trial_may_waste_energy_or_fail_to_reduce_heat",
        reversibility="trial_is_reversible_by_returning_to_rest_state",
        stop_conditions="stop_if_human_observer_records_instability",
        stop_condition_codes=stop_condition_codes,
        required_permission="human_teacher_explicit_permission_required",
    )


def test_valid_proposal_creation_preserves_exact_provenance() -> None:
    request = _request()
    result = BoundedImaginedSafeExperimentProposer().propose(request)

    assert result.proposal.source_result_id == request.source_result.result_id
    assert result.proposal.source_request_id == request.source_result.request.request_id
    assert result.proposal.source_issue.issue_id == request.issue_id
    assert result.proposal.source_issue == request.nominated_issue
    assert result.proposal.hypothesis == request.hypothesis
    assert result.proposal.stop_condition_codes == request.stop_condition_codes


def test_missing_issue_is_rejected() -> None:
    with pytest.raises(ValueError, match="issue_id must match exactly one"):
        _request(issue_id="imagined-comparison-uncertainty-issue:missing")


def test_tampered_source_result_is_rejected_before_proposal_construction() -> None:
    source_result = _source_result()
    object.__setattr__(
        source_result.issues[0],
        "pair_comparison_id",
        "imagined-route-pair-comparison:tampered",
    )

    with pytest.raises(ValueError, match="inconsistent with source"):
        _request(source_result)


def test_duplicate_stop_condition_codes_are_rejected() -> None:
    with pytest.raises(ValueError, match="stop_condition_codes must be unique"):
        _request(stop_condition_codes=("halt_if_heat_rises", "halt_if_heat_rises"))


def test_unsorted_stop_condition_codes_are_rejected() -> None:
    with pytest.raises(ValueError, match="stop_condition_codes must be sorted"):
        _request(stop_condition_codes=("halt_if_stress_spikes", "halt_if_heat_rises"))


def test_repeated_requests_have_stable_ascii_identities() -> None:
    request_a = _request()
    request_b = _request(request_a.source_result, issue_id=request_a.issue_id)

    result_a = BoundedImaginedSafeExperimentProposer().propose(request_a)
    result_b = BoundedImaginedSafeExperimentProposer().propose(request_b)

    assert request_a.request_id == request_b.request_id
    assert result_a.proposal.proposal_id == result_b.proposal.proposal_id
    assert result_a.result_id == result_b.result_id
    assert result_a.snapshot_json_ascii() == result_b.snapshot_json_ascii()
    assert result_a.snapshot_json_ascii().decode("ascii")


def test_zero_deltas_and_authority_remain_exact_on_all_layers() -> None:
    request = _request()
    result = BoundedImaginedSafeExperimentProposer().propose(request)
    layers: tuple[Any, ...] = (request, result.proposal, result)

    for layer in layers:
        assert layer.factual_confidence_change == 0.0
        assert layer.mastery_change == 0.0
        assert layer.competence_change == 0.0
        assert layer.growth_pressure_change == 0.0
        assert layer.replay_evidence_change == 0.0
        assert layer.real_observation_change == 0.0
        assert layer.has_action_selection_authority is False
        assert layer.has_production_action_authority is False


def test_snapshots_exclude_ranking_scheduling_execution_and_persistence_fields() -> None:
    snapshot = str(BoundedImaginedSafeExperimentProposer().propose(_request()).snapshot()).lower()

    for forbidden in (
        "rank",
        "ranking",
        "recommend",
        "optimiz",
        "schedule",
        "execute",
        "persist",
        "promotion",
        "integrat",
        "winner",
        "selected_candidate",
        "production_authority",
    ):
        assert forbidden not in snapshot


def test_result_rejects_tampered_proposal() -> None:
    request = _request()
    result = BoundedImaginedSafeExperimentProposer().propose(request)
    tampered = result.proposal
    object.__setattr__(tampered, "required_permission", "tampered_permission")

    with pytest.raises(ValueError, match="inconsistent with request"):
        ImaginedSafeExperimentProposalResult(
            result_id=result.result_id,
            request=request,
            proposal=tampered,
        )


def test_static_dependencies_exclude_earlier_stage_calls_and_runtime_surfaces() -> None:
    source = Path(
        "src/seedmind/research/ndnra/bounded_imagination_safe_experiment_proposal.py"
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
        "seedmind.research.ndnra.bounded_imagination",
        "seedmind.research.ndnra.bounded_imagination_candidates",
        "seedmind.research.ndnra.bounded_imagination_evaluation",
        "seedmind.research.ndnra.bounded_imagination_comparison",
        "seedmind.research.ndnra.persistence",
        "seedmind.research.ndnra.consolidation",
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
        "optimize(",
        "optimise(",
        "schedule(",
        "sqlite",
        "asyncio",
    ):
        assert forbidden not in lowered
