"""Tests for non-authoritative imagined route comparison semantics."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from seedmind.research.ndnra import (
    BoundedCandidateGenerationConfig,
    BoundedExactCandidateGenerator,
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
    ImaginedRouteComparisonRequest,
    ImaginedRouteComparisonResult,
    ImaginedRouteDimensionRelation,
    ImaginedRouteEvaluationRequest,
    ImaginedRouteEvaluationResult,
    ImaginedRouteIncomparabilityReason,
    ImaginedRoutePairRelation,
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


def _observe(
    model: LearnedConsequenceModel,
    *,
    event_id: str,
    context: ContextSignature,
    action: str,
    next_context: ContextSignature,
    heat: EffectObservation,
    energy: EffectObservation | None = None,
) -> None:
    effects = (heat,) if energy is None else (energy, heat)
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


def _need(
    *,
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


def _result_for(
    actions: tuple[tuple[str, EffectObservation, EffectObservation | None], ...],
    *,
    effects: tuple[str, ...] = ("energy_delta", "heat_delta"),
    maximum_sequence_depth: int = 1,
    need: EffectNeed | None = None,
    neutral_tolerance: float = 0.05,
) -> tuple[LearnedConsequenceModel, ImaginedRouteEvaluationResult]:
    start = _context(0.9, tuple(action for action, _, _ in actions))
    model = LearnedConsequenceModel()
    for index, (action, heat, energy) in enumerate(actions):
        _observe(
            model,
            event_id=f"real:comparison:{action}:{index:04d}",
            context=start,
            action=action,
            next_context=_context(0.9 + heat.value, ("rest",)),
            heat=heat,
            energy=energy,
        )
    candidates = (
        BoundedExactCandidateGenerator(model)
        .generate(
            ImaginedCandidateGenerationRequest(
                context=start,
                requested_effect_codes=effects,
                config=BoundedCandidateGenerationConfig(
                    maximum_sequence_depth=maximum_sequence_depth,
                    maximum_branch_actions_per_prefix=max(1, len(actions)),
                    maximum_generated_candidates=8,
                ),
            )
        )
        .candidates
    )
    evaluation_result = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need() if need is None else need,
            candidates=candidates,
            config=BoundedRouteEvaluationConfig(neutral_tolerance=neutral_tolerance),
        )
    )
    return model, evaluation_result


def _comparison(
    result: ImaginedRouteEvaluationResult,
    config: BoundedRouteComparisonConfig | None = None,
) -> ImaginedRouteComparisonResult:
    return BoundedImaginedRouteComparator().compare(
        ImaginedRouteComparisonRequest(
            source_result=result,
            config=BoundedRouteComparisonConfig() if config is None else config,
        )
    )


def _two_step_result() -> ImaginedRouteEvaluationResult:
    start = _context(0.9, ("cool",))
    middle = _context(0.4, ("rest",))
    final = _context(0.3, ("stop",))
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:comparison:two-step:cool",
        context=start,
        action="cool",
        next_context=middle,
        heat=EffectObservation("heat_delta", -0.5, 1.0),
        energy=EffectObservation("energy_delta", 0.0, 1.0),
    )
    _observe(
        model,
        event_id="real:comparison:two-step:rest",
        context=middle,
        action="rest",
        next_context=final,
        heat=EffectObservation("heat_delta", -0.1, 1.0),
        energy=EffectObservation("energy_delta", 0.0, 1.0),
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
    two_step = next(candidate for candidate in candidates if len(candidate.steps) == 2)
    return BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(need=_need(), candidates=(two_step,))
    )


def test_left_strictly_dominates_right_without_hidden_route_score() -> None:
    _, result = _result_for(
        (
            (
                "cool",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "wait",
                EffectObservation("heat_delta", 0.0, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )

    comparison = _comparison(result)
    pair = comparison.pair_comparisons[0]

    assert pair.relation is ImaginedRoutePairRelation.LEFT_DOMINATES_RIGHT
    assert pair.incomparability_reasons == ()
    assert "score" not in str(comparison.snapshot())


def test_right_dominance_is_symmetric() -> None:
    _, result = _result_for(
        (
            (
                "a_wait",
                EffectObservation("heat_delta", 0.0, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "z_cool",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )

    assert _comparison(result).pair_comparisons[0].relation is (
        ImaginedRoutePairRelation.RIGHT_DOMINATES_LEFT
    )


def test_conflicting_tradeoffs_are_incomparable() -> None:
    _, result = _result_for(
        (
            (
                "cool",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", -0.4, 1.0),
            ),
            (
                "save",
                EffectObservation("heat_delta", -0.2, 1.0),
                EffectObservation("energy_delta", 0.2, 1.0),
            ),
        )
    )

    pair = _comparison(result).pair_comparisons[0]

    assert pair.relation is ImaginedRoutePairRelation.INCOMPARABLE
    assert pair.incomparability_reasons == (
        ImaginedRouteIncomparabilityReason.CONFLICTING_TRADEOFF,
    )


def test_unknown_alignment_blocks_dominance() -> None:
    _, result = _result_for(
        (
            ("cool", EffectObservation("heat_delta", -0.5, 1.0), None),
            ("wait", EffectObservation("heat_delta", 0.0, 1.0), None),
        ),
        effects=("heat_delta",),
    )

    pair = _comparison(result).pair_comparisons[0]

    assert pair.relation is ImaginedRoutePairRelation.INCOMPARABLE
    assert ImaginedRouteIncomparabilityReason.UNKNOWN_ALIGNMENT in pair.incomparability_reasons


def test_zero_confidence_known_alignment_is_low_confidence_by_default() -> None:
    _, result = _result_for(
        (
            (
                "weak",
                EffectObservation("heat_delta", -0.5, 0.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "wait",
                EffectObservation("heat_delta", 0.0, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )

    pair = _comparison(result).pair_comparisons[0]

    assert pair.relation is ImaginedRoutePairRelation.INCOMPARABLE
    assert ImaginedRouteIncomparabilityReason.LOW_CONFIDENCE in pair.incomparability_reasons


def test_configured_confidence_floor_blocks_low_confidence_comparison() -> None:
    _, result = _result_for(
        (
            (
                "cool",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "wait",
                EffectObservation("heat_delta", 0.0, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )

    pair = _comparison(
        result,
        BoundedRouteComparisonConfig(confidence_floor=0.3),
    ).pair_comparisons[0]

    assert pair.relation is ImaginedRoutePairRelation.INCOMPARABLE
    assert ImaginedRouteIncomparabilityReason.LOW_CONFIDENCE in pair.incomparability_reasons


def test_different_route_depths_are_incomparable() -> None:
    start = _context(0.9, ("cool", "wait"))
    middle = _context(0.4, ("rest",))
    final = _context(0.3, ("stop",))
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:comparison:cool",
        context=start,
        action="cool",
        next_context=middle,
        heat=EffectObservation("heat_delta", -0.5, 1.0),
        energy=EffectObservation("energy_delta", 0.0, 1.0),
    )
    _observe(
        model,
        event_id="real:comparison:wait",
        context=start,
        action="wait",
        next_context=_context(0.9, ("rest",)),
        heat=EffectObservation("heat_delta", 0.0, 1.0),
        energy=EffectObservation("energy_delta", 0.0, 1.0),
    )
    _observe(
        model,
        event_id="real:comparison:rest",
        context=middle,
        action="rest",
        next_context=final,
        heat=EffectObservation("heat_delta", -0.1, 1.0),
        energy=EffectObservation("energy_delta", 0.0, 1.0),
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
    one_step_candidate = next(item for item in candidates if len(item.steps) == 1)
    two_step_candidate = next(item for item in candidates if len(item.steps) == 2)
    result = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need(),
            candidates=(one_step_candidate, two_step_candidate),
        )
    )

    pair = _comparison(result).pair_comparisons[0]

    assert pair.relation is ImaginedRoutePairRelation.INCOMPARABLE
    assert ImaginedRouteIncomparabilityReason.DIFFERENT_ROUTE_DEPTH in (
        pair.incomparability_reasons
    )


def test_two_neutral_alignments_with_different_raw_values_remain_equivalent() -> None:
    _, result = _result_for(
        (
            (
                "small",
                EffectObservation("heat_delta", -0.01, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "tiny",
                EffectObservation("heat_delta", -0.02, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        ),
        neutral_tolerance=0.05,
    )

    heat = next(
        item
        for item in _comparison(result).pair_comparisons[0].dimension_comparisons
        if item.effect_code == "heat_delta"
    )

    assert heat.relation is ImaginedRouteDimensionRelation.EQUIVALENT


def test_improving_and_worsening_alignments_compare_by_signed_magnitude() -> None:
    _, improving = _result_for(
        (
            (
                "strong",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "weak",
                EffectObservation("heat_delta", -0.2, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    _, worsening = _result_for(
        (
            (
                "bad",
                EffectObservation("heat_delta", 0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "less_bad",
                EffectObservation("heat_delta", 0.2, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )

    improving_heat = next(
        item
        for item in _comparison(improving).pair_comparisons[0].dimension_comparisons
        if item.effect_code == "heat_delta"
    )
    worsening_heat = next(
        item
        for item in _comparison(worsening).pair_comparisons[0].dimension_comparisons
        if item.effect_code == "heat_delta"
    )

    assert improving_heat.relation is ImaginedRouteDimensionRelation.LEFT_BETTER
    assert worsening_heat.relation is ImaginedRouteDimensionRelation.RIGHT_BETTER


def test_identical_alignment_vectors_with_distinct_provenance_remain_separate() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )

    pair = _comparison(result).pair_comparisons[0]

    assert pair.relation is ImaginedRoutePairRelation.ALIGNMENT_EQUIVALENT
    assert pair.left_evaluation_id != pair.right_evaluation_id
    assert pair.left_candidate_id != pair.right_candidate_id


def test_duplicate_evaluation_ids_are_rejected() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    object.__setattr__(result, "evaluations", (result.evaluations[0], result.evaluations[0]))

    with pytest.raises(ValueError, match="evaluation IDs"):
        ImaginedRouteComparisonRequest(source_result=result)


def test_source_result_caller_order_cannot_be_rewritten() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    object.__setattr__(result, "evaluations", tuple(reversed(result.evaluations)))

    with pytest.raises(ValueError, match="source caller order"):
        ImaginedRouteComparisonRequest(source_result=result)


def test_dimension_comparison_rejects_incomplete_source_shape() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    dimension = _comparison(result).pair_comparisons[0].dimension_comparisons[0]

    with pytest.raises(ValueError, match="missing left step"):
        replace(dimension, left_step_evaluation_id=None)


def test_pair_relation_must_match_dimension_relations() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    pair = _comparison(result).pair_comparisons[0]

    with pytest.raises(ValueError, match="pair relation"):
        replace(pair, relation=ImaginedRoutePairRelation.ALIGNMENT_EQUIVALENT)


def test_result_rejects_tampered_pair_source_reference() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    comparison = _comparison(result)
    object.__setattr__(
        comparison.pair_comparisons[0],
        "left_candidate_id",
        "imagined-generated-candidate:tampered",
    )

    with pytest.raises(ValueError, match="source references"):
        ImaginedRouteComparisonResult(
            result_id=comparison.result_id,
            request=comparison.request,
            pair_comparisons=comparison.pair_comparisons,
        )


def test_mixed_active_needs_are_rejected_atomically() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    step = result.evaluations[0].step_evaluations[0]
    object.__setattr__(step, "context", _context(0.9, ("left",), need="cleanliness"))

    with pytest.raises(ValueError, match="active need"):
        ImaginedRouteComparisonRequest(source_result=result)


@pytest.mark.parametrize(
    ("field", "value", "match"),
    [
        ("desired_direction", 1.0, "desired-direction"),
        ("intensity", 0.25, "intensity"),
        ("neutral_tolerance", 0.2, "neutral-tolerance"),
    ],
)
def test_alignment_semantic_mismatches_are_rejected_atomically(
    field: str,
    value: float,
    match: str,
) -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    alignment = result.evaluations[0].step_evaluations[0].alignments[0]
    object.__setattr__(alignment, field, value if field != "desired_direction" else -1.0)

    with pytest.raises(ValueError, match=match):
        ImaginedRouteComparisonRequest(source_result=result)


def test_effect_set_mismatch_is_rejected_atomically() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    step = result.evaluations[0].step_evaluations[0]
    object.__setattr__(step, "alignments", step.alignments[:1])

    with pytest.raises(ValueError, match="effect semantics"):
        ImaginedRouteComparisonRequest(source_result=result)


def test_empty_source_result_returns_deterministic_empty_result() -> None:
    empty = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(need=_need(), candidates=())
    )

    first = _comparison(empty)
    second = _comparison(empty)

    assert first.pair_comparisons == ()
    assert first.result_id == second.result_id
    assert first.snapshot_json_ascii() == second.snapshot_json_ascii()


def test_bounds_reject_atomically() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "third",
                EffectObservation("heat_delta", -0.3, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )

    with pytest.raises(ValueError, match="evaluation bound"):
        ImaginedRouteComparisonRequest(
            source_result=result,
            config=BoundedRouteComparisonConfig(maximum_evaluations=1),
        )
    with pytest.raises(ValueError, match="pair bound"):
        ImaginedRouteComparisonRequest(
            source_result=result,
            config=BoundedRouteComparisonConfig(maximum_pairs=1),
        )
    two_step_result = _two_step_result()
    with pytest.raises(ValueError, match="step bound"):
        ImaginedRouteComparisonRequest(
            source_result=two_step_result,
            config=BoundedRouteComparisonConfig(maximum_steps_per_evaluation=1),
        )
    with pytest.raises(ValueError, match="dimension bound"):
        ImaginedRouteComparisonRequest(
            source_result=result,
            config=BoundedRouteComparisonConfig(maximum_dimensions_per_step=1),
        )
    with pytest.raises(ValueError, match="total dimension-comparison bound"):
        ImaginedRouteComparisonRequest(
            source_result=result,
            config=BoundedRouteComparisonConfig(maximum_total_dimension_comparisons=1),
        )
    support_step = result.evaluations[0].step_evaluations[0]
    excessive_support = tuple(f"real:source:{index:02d}" for index in range(65))
    object.__setattr__(support_step, "supporting_real_event_ids", excessive_support)
    for support_alignment in support_step.alignments:
        if support_alignment.predicted_value is not None:
            object.__setattr__(
                support_alignment,
                "supporting_real_event_ids",
                excessive_support,
            )
    with pytest.raises(ValueError, match="provenance bound"):
        ImaginedRouteComparisonRequest(source_result=result)


def test_pair_order_is_deterministic_caller_index_order() -> None:
    _, result = _result_for(
        (
            ("a", EffectObservation("heat_delta", -0.3, 1.0), None),
            ("b", EffectObservation("heat_delta", -0.2, 1.0), None),
            ("c", EffectObservation("heat_delta", -0.1, 1.0), None),
        ),
        effects=("heat_delta",),
        need=_need(dimensions=(NeedDimension("heat_delta", -1.0, 1.0),)),
    )

    assert [
        (item.left_caller_index, item.right_caller_index)
        for item in _comparison(result).pair_comparisons
    ] == [(0, 1), (0, 2), (1, 2)]


def test_repeated_requests_have_stable_ascii_identities_and_source_ids_resolve() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )

    first = _comparison(result)
    second = _comparison(result)
    pair = first.pair_comparisons[0]
    dimension = pair.dimension_comparisons[0]

    assert first.result_id == second.result_id
    assert first.snapshot_json_ascii() == second.snapshot_json_ascii()
    assert first.snapshot_json_ascii().decode("ascii")
    assert pair.left_evaluation_id == result.evaluations[0].evaluation_id
    assert pair.right_evaluation_id == result.evaluations[1].evaluation_id
    assert (
        dimension.left_step_evaluation_id
        == result.evaluations[0].step_evaluations[0].step_evaluation_id
    )
    assert (
        dimension.left_alignment_id
        == result.evaluations[0].step_evaluations[0].alignments[0].alignment_id
    )


def test_zero_deltas_and_authority_remain_exact_on_all_layers() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    request = ImaginedRouteComparisonRequest(source_result=result)
    comparison = BoundedImaginedRouteComparator().compare(request)

    layers: list[Any] = [request, comparison, *comparison.pair_comparisons]
    layers.extend(
        dimension
        for pair in comparison.pair_comparisons
        for dimension in pair.dimension_comparisons
    )
    for layer in layers:
        assert layer.factual_confidence_change == 0.0
        assert layer.mastery_change == 0.0
        assert layer.competence_change == 0.0
        assert layer.growth_pressure_change == 0.0
        assert layer.replay_evidence_change == 0.0
        assert layer.real_observation_change == 0.0
        assert layer.has_action_selection_authority is False
        assert layer.has_production_action_authority is False


def test_actual_comparison_objects_cannot_update_real_consequence_evidence() -> None:
    model, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    comparison = _comparison(result)
    before = model.snapshot()

    with pytest.raises((ValueError, AttributeError)):
        model.observe(cast(Any, comparison))

    assert model.snapshot() == before


def test_snapshots_exclude_scoring_ranking_selection_and_execution_fields() -> None:
    _, result = _result_for(
        (
            (
                "left",
                EffectObservation("heat_delta", -0.5, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
            (
                "right",
                EffectObservation("heat_delta", -0.4, 1.0),
                EffectObservation("energy_delta", 0.0, 1.0),
            ),
        )
    )
    snapshot = str(_comparison(result).snapshot())

    for forbidden in (
        "score",
        "utility",
        "rank",
        "winner",
        "selected_candidate",
        "recommended_candidate",
        "schedule",
        "promotion",
        "execution",
    ):
        assert forbidden not in snapshot


def test_static_ast_import_checks_exclude_forbidden_subsystems() -> None:
    source = Path("src/seedmind/research/ndnra/bounded_imagination_comparison.py").read_text(
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
        "optimise(",
        "optimize(",
        "execute(",
        "recommend",
        "safe_experiment",
    ):
        assert forbidden not in lowered
