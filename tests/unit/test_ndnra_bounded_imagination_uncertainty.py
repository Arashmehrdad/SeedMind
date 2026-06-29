"""Tests for bounded non-authoritative comparison uncertainty auditing."""

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
    BoundedRouteComparisonConfig,
    BoundedRouteEvaluationConfig,
    ConsequenceModelObservation,
    ContextSignature,
    EffectNeed,
    EffectObservation,
    ExperienceOrigin,
    ImaginedCandidateGenerationRequest,
    ImaginedComparisonIssueScope,
    ImaginedComparisonUncertaintyRequest,
    ImaginedComparisonUncertaintyResult,
    ImaginedRouteComparisonRequest,
    ImaginedRouteComparisonResult,
    ImaginedRouteDimensionRelation,
    ImaginedRouteEvaluationRequest,
    ImaginedRouteIncomparabilityReason,
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


def _need(
    dimensions: tuple[NeedDimension, ...] = (
        NeedDimension("energy_delta", 1.0, 0.5),
        NeedDimension("heat_delta", -1.0, 1.0),
    ),
) -> EffectNeed:
    return EffectNeed(
        need_code="cooling",
        primary_effect_code="heat_delta",
        dimensions=dimensions,
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


def _comparison_result(
    actions: tuple[tuple[str, tuple[EffectObservation, ...]], ...],
    *,
    requested_effect_codes: tuple[str, ...] = ("energy_delta", "heat_delta"),
    need: EffectNeed | None = None,
    confidence_floor: float = 0.0,
) -> tuple[LearnedConsequenceModel, ImaginedRouteComparisonResult]:
    start = _context(0.9, tuple(action for action, _ in actions))
    model = LearnedConsequenceModel()
    for index, (action, effects) in enumerate(actions):
        heat = next(item.value for item in effects if item.effect_code == "heat_delta")
        _observe(
            model,
            event_id=f"real:uncertainty:{action}:{index:04d}",
            context=start,
            action=action,
            next_context=_context(0.9 + heat, ("rest",)),
            effects=effects,
        )
    candidates = (
        BoundedExactCandidateGenerator(model)
        .generate(
            ImaginedCandidateGenerationRequest(
                context=start,
                requested_effect_codes=requested_effect_codes,
                config=BoundedCandidateGenerationConfig(
                    maximum_sequence_depth=1,
                    maximum_branch_actions_per_prefix=max(1, len(actions)),
                    maximum_generated_candidates=8,
                ),
            )
        )
        .candidates
    )
    evaluation = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need() if need is None else need,
            candidates=candidates,
            config=BoundedRouteEvaluationConfig(neutral_tolerance=0.05),
        )
    )
    comparison = BoundedImaginedRouteComparator().compare(
        ImaginedRouteComparisonRequest(
            source_result=evaluation,
            config=BoundedRouteComparisonConfig(confidence_floor=confidence_floor),
        )
    )
    return model, comparison


def _audit(
    source: ImaginedRouteComparisonResult,
    config: BoundedComparisonUncertaintyConfig | None = None,
) -> ImaginedComparisonUncertaintyResult:
    return BoundedImaginedComparisonUncertaintyAuditor().audit(
        ImaginedComparisonUncertaintyRequest(
            source_result=source,
            config=(BoundedComparisonUncertaintyConfig() if config is None else config),
        )
    )


def _depth_mismatch_result() -> ImaginedRouteComparisonResult:
    start = _context(0.9, ("cool", "wait"))
    middle = _context(0.4, ("rest",))
    final = _context(0.3, ("stop",))
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:uncertainty:depth:cool",
        context=start,
        action="cool",
        next_context=middle,
        effects=(
            EffectObservation("energy_delta", 0.0, 1.0),
            EffectObservation("heat_delta", -0.5, 1.0),
        ),
    )
    _observe(
        model,
        event_id="real:uncertainty:depth:wait",
        context=start,
        action="wait",
        next_context=_context(0.9, ("rest",)),
        effects=(
            EffectObservation("energy_delta", 0.0, 1.0),
            EffectObservation("heat_delta", 0.0, 1.0),
        ),
    )
    _observe(
        model,
        event_id="real:uncertainty:depth:rest",
        context=middle,
        action="rest",
        next_context=final,
        effects=(
            EffectObservation("energy_delta", 0.0, 1.0),
            EffectObservation("heat_delta", -0.1, 1.0),
        ),
    )
    candidates = (
        BoundedExactCandidateGenerator(model)
        .generate(
            ImaginedCandidateGenerationRequest(
                context=start,
                requested_effect_codes=("energy_delta", "heat_delta"),
                config=BoundedCandidateGenerationConfig(maximum_sequence_depth=2),
            )
        )
        .candidates
    )
    one_step = next(item for item in candidates if len(item.steps) == 1)
    two_step = next(item for item in candidates if len(item.steps) == 2)
    evaluation = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need(),
            candidates=(one_step, two_step),
        )
    )
    return BoundedImaginedRouteComparator().compare(
        ImaginedRouteComparisonRequest(source_result=evaluation)
    )


def test_comparable_pair_emits_no_uncertainty_issue() -> None:
    _, comparison = _comparison_result(
        (
            (
                "cool",
                (
                    EffectObservation("energy_delta", 0.0, 1.0),
                    EffectObservation("heat_delta", -0.5, 1.0),
                ),
            ),
            (
                "wait",
                (
                    EffectObservation("energy_delta", 0.0, 1.0),
                    EffectObservation("heat_delta", 0.0, 1.0),
                ),
            ),
        )
    )

    assert _audit(comparison).issues == ()


def test_unknown_alignment_emits_exact_dimension_issue() -> None:
    _, comparison = _comparison_result(
        (
            ("cool", (EffectObservation("heat_delta", -0.5, 1.0),)),
            ("wait", (EffectObservation("heat_delta", 0.0, 1.0),)),
        ),
        requested_effect_codes=("heat_delta",),
    )

    issue = _audit(comparison).issues[0]
    source_dimension = next(
        item
        for item in comparison.pair_comparisons[0].dimension_comparisons
        if item.effect_code == "energy_delta"
    )

    assert issue.scope is ImaginedComparisonIssueScope.DIMENSION
    assert issue.dimension_comparison_id == source_dimension.dimension_comparison_id
    assert issue.step_index == source_dimension.step_index
    assert issue.effect_code == "energy_delta"
    assert issue.reasons == (ImaginedRouteIncomparabilityReason.UNKNOWN_ALIGNMENT,)
    assert issue.related_dimension_comparison_ids == ()


def test_low_confidence_emits_dimension_issue() -> None:
    _, comparison = _comparison_result(
        (
            (
                "cool",
                (
                    EffectObservation("energy_delta", 0.0, 1.0),
                    EffectObservation("heat_delta", -0.5, 1.0),
                ),
            ),
            (
                "wait",
                (
                    EffectObservation("energy_delta", 0.0, 1.0),
                    EffectObservation("heat_delta", 0.0, 1.0),
                ),
            ),
        ),
        confidence_floor=0.3,
    )

    assert all(
        issue.scope is ImaginedComparisonIssueScope.DIMENSION for issue in _audit(comparison).issues
    )
    assert all(
        issue.reasons == (ImaginedRouteIncomparabilityReason.LOW_CONFIDENCE,)
        for issue in _audit(comparison).issues
    )


def test_route_depth_mismatch_emits_dimension_issues() -> None:
    comparison = _depth_mismatch_result()

    issues = _audit(comparison).issues

    assert issues
    assert all(issue.scope is ImaginedComparisonIssueScope.DIMENSION for issue in issues)
    assert all(
        issue.reasons == (ImaginedRouteIncomparabilityReason.DIFFERENT_ROUTE_DEPTH,)
        for issue in issues
    )


def test_conflicting_tradeoff_emits_one_pair_issue_with_related_dimensions() -> None:
    _, comparison = _comparison_result(
        (
            (
                "cool",
                (
                    EffectObservation("energy_delta", -0.4, 1.0),
                    EffectObservation("heat_delta", -0.5, 1.0),
                ),
            ),
            (
                "save",
                (
                    EffectObservation("energy_delta", 0.2, 1.0),
                    EffectObservation("heat_delta", -0.2, 1.0),
                ),
            ),
        )
    )

    issue = _audit(comparison).issues[0]
    source_pair = comparison.pair_comparisons[0]
    expected_related = tuple(
        item.dimension_comparison_id
        for item in source_pair.dimension_comparisons
        if item.relation
        in (
            ImaginedRouteDimensionRelation.LEFT_BETTER,
            ImaginedRouteDimensionRelation.RIGHT_BETTER,
        )
    )

    assert issue.scope is ImaginedComparisonIssueScope.PAIR
    assert issue.reasons == (ImaginedRouteIncomparabilityReason.CONFLICTING_TRADEOFF,)
    assert issue.related_dimension_comparison_ids == expected_related
    assert issue.dimension_comparison_id is None
    assert issue.step_index is None
    assert issue.effect_code is None


def test_issue_order_preserves_pair_and_dimension_order() -> None:
    _, comparison = _comparison_result(
        (
            ("a", (EffectObservation("heat_delta", -0.3, 1.0),)),
            ("b", (EffectObservation("heat_delta", -0.2, 1.0),)),
            ("c", (EffectObservation("heat_delta", -0.1, 1.0),)),
        ),
        requested_effect_codes=("heat_delta",),
        need=_need(
            (
                NeedDimension("energy_delta", 1.0, 0.5),
                NeedDimension("heat_delta", -1.0, 1.0),
            )
        ),
    )

    issues = _audit(comparison).issues

    assert [
        (issue.left_caller_index, issue.right_caller_index, issue.effect_code) for issue in issues
    ] == [
        (0, 1, "energy_delta"),
        (0, 2, "energy_delta"),
        (1, 2, "energy_delta"),
    ]


def test_empty_source_returns_deterministic_empty_audit() -> None:
    empty_evaluation = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(need=_need(), candidates=())
    )
    empty_comparison = BoundedImaginedRouteComparator().compare(
        ImaginedRouteComparisonRequest(source_result=empty_evaluation)
    )

    first = _audit(empty_comparison)
    second = _audit(empty_comparison)

    assert first.issues == ()
    assert first.result_id == second.result_id
    assert first.snapshot_json_ascii() == second.snapshot_json_ascii()


def test_bounds_reject_atomically() -> None:
    _, comparison = _comparison_result(
        (
            ("a", (EffectObservation("heat_delta", -0.3, 1.0),)),
            ("b", (EffectObservation("heat_delta", -0.2, 1.0),)),
            ("c", (EffectObservation("heat_delta", -0.1, 1.0),)),
        ),
        requested_effect_codes=("heat_delta",),
    )

    with pytest.raises(ValueError, match="pair bound"):
        ImaginedComparisonUncertaintyRequest(
            source_result=comparison,
            config=BoundedComparisonUncertaintyConfig(maximum_pairs=1),
        )
    with pytest.raises(ValueError, match="dimension-issue bound"):
        ImaginedComparisonUncertaintyRequest(
            source_result=comparison,
            config=BoundedComparisonUncertaintyConfig(maximum_dimension_issues=1),
        )
    with pytest.raises(ValueError, match="total-issue bound"):
        ImaginedComparisonUncertaintyRequest(
            source_result=comparison,
            config=BoundedComparisonUncertaintyConfig(maximum_total_issues=1),
        )


def test_tampered_source_result_is_rejected() -> None:
    _, comparison = _comparison_result(
        (
            (
                "cool",
                (
                    EffectObservation("energy_delta", 0.0, 1.0),
                    EffectObservation("heat_delta", -0.5, 1.0),
                ),
            ),
            (
                "wait",
                (
                    EffectObservation("energy_delta", 0.0, 1.0),
                    EffectObservation("heat_delta", 0.0, 1.0),
                ),
            ),
        )
    )
    object.__setattr__(
        comparison.pair_comparisons[0],
        "left_candidate_id",
        "imagined-generated-candidate:tampered",
    )

    with pytest.raises(ValueError, match="source references"):
        ImaginedComparisonUncertaintyRequest(source_result=comparison)


def test_result_rejects_tampered_issue_source_reference() -> None:
    _, comparison = _comparison_result(
        (
            ("cool", (EffectObservation("heat_delta", -0.5, 1.0),)),
            ("wait", (EffectObservation("heat_delta", 0.0, 1.0),)),
        ),
        requested_effect_codes=("heat_delta",),
    )
    result = _audit(comparison)
    tampered = result.issues[0]
    object.__setattr__(
        tampered,
        "pair_comparison_id",
        "imagined-route-pair-comparison:tampered",
    )

    with pytest.raises(ValueError, match="inconsistent with source"):
        ImaginedComparisonUncertaintyResult(
            result_id=result.result_id,
            request=result.request,
            issues=(tampered,),
        )


def test_repeated_requests_have_stable_ascii_identities() -> None:
    _, comparison = _comparison_result(
        (
            ("cool", (EffectObservation("heat_delta", -0.5, 1.0),)),
            ("wait", (EffectObservation("heat_delta", 0.0, 1.0),)),
        ),
        requested_effect_codes=("heat_delta",),
    )
    request_a = ImaginedComparisonUncertaintyRequest(source_result=comparison)
    request_b = ImaginedComparisonUncertaintyRequest(source_result=comparison)

    result_a = BoundedImaginedComparisonUncertaintyAuditor().audit(request_a)
    result_b = BoundedImaginedComparisonUncertaintyAuditor().audit(request_b)

    assert request_a.request_id == request_b.request_id
    assert result_a.result_id == result_b.result_id
    assert result_a.snapshot_json_ascii() == result_b.snapshot_json_ascii()
    assert result_a.snapshot_json_ascii().decode("ascii")


def test_zero_deltas_and_authority_remain_exact_on_all_layers() -> None:
    _, comparison = _comparison_result(
        (
            ("cool", (EffectObservation("heat_delta", -0.5, 1.0),)),
            ("wait", (EffectObservation("heat_delta", 0.0, 1.0),)),
        ),
        requested_effect_codes=("heat_delta",),
    )
    request = ImaginedComparisonUncertaintyRequest(source_result=comparison)
    result = BoundedImaginedComparisonUncertaintyAuditor().audit(request)
    layers: tuple[Any, ...] = (request, result, *result.issues)

    for layer in layers:
        assert layer.factual_confidence_change == 0.0
        assert layer.mastery_change == 0.0
        assert layer.competence_change == 0.0
        assert layer.growth_pressure_change == 0.0
        assert layer.replay_evidence_change == 0.0
        assert layer.real_observation_change == 0.0
        assert layer.has_action_selection_authority is False
        assert layer.has_production_action_authority is False


def test_uncertainty_objects_cannot_update_real_consequence_evidence() -> None:
    model, comparison = _comparison_result(
        (
            ("cool", (EffectObservation("heat_delta", -0.5, 1.0),)),
            ("wait", (EffectObservation("heat_delta", 0.0, 1.0),)),
        ),
        requested_effect_codes=("heat_delta",),
    )
    result = _audit(comparison)
    before = model.snapshot()

    with pytest.raises((ValueError, AttributeError)):
        model.observe(cast(Any, result))

    assert model.snapshot() == before


def test_snapshots_exclude_scoring_proposals_selection_and_execution() -> None:
    _, comparison = _comparison_result(
        (
            ("cool", (EffectObservation("heat_delta", -0.5, 1.0),)),
            ("wait", (EffectObservation("heat_delta", 0.0, 1.0),)),
        ),
        requested_effect_codes=("heat_delta",),
    )
    snapshot = str(_audit(comparison).snapshot()).lower()

    for forbidden in (
        "score",
        "utility",
        "rank",
        "winner",
        "selected_candidate",
        "recommended_candidate",
        "experiment_proposal",
        "schedule",
        "promotion",
        "execution",
    ):
        assert forbidden not in snapshot


def test_static_dependencies_exclude_generation_execution_and_storage_surfaces() -> None:
    source = Path("src/seedmind/research/ndnra/bounded_imagination_uncertainty.py").read_text(
        encoding="ascii"
    )
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
        "seedmind.research.ndnra.bounded_imagination",
        "seedmind.research.ndnra.bounded_imagination_candidates",
        "seedmind.research.ndnra.bounded_imagination_evaluation",
        "seedmind.research.ndnra.learned_consequence_model",
        "seedmind.research.ndnra.contextual_consequence_transfer",
        "seedmind.research.ndnra.observed_consequence_chains",
        "seedmind.research.ndnra.composition",
        "seedmind.research.ndnra.persistence",
        "seedmind.research.ndnra.growth",
        "seedmind.research.ndnra.controlled_retention_replay",
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
        "optimise(",
        "optimize(",
        "execute(",
        "recommend",
        "safe_experiment",
    ):
        assert forbidden not in lowered
