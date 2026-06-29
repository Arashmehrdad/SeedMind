"""Tests for pure non-authoritative imagined route evaluation."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

import pytest

from seedmind.research.ndnra import (
    BoundedCandidateGenerationConfig,
    BoundedExactCandidateGenerator,
    BoundedImaginedRouteEvaluator,
    BoundedRouteEvaluationConfig,
    ConsequenceModelObservation,
    ContextSignature,
    EffectNeed,
    EffectObservation,
    ExperienceOrigin,
    ImaginedAlignmentDirection,
    ImaginedCandidateGenerationRequest,
    ImaginedGeneratedCandidate,
    ImaginedRouteEvaluationRequest,
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


def _model() -> tuple[LearnedConsequenceModel, ContextSignature]:
    start = _context(0.9, ("cool", "wait"))
    cooled = _context(0.4, ("rest",))
    unchanged = _context(0.9, ("rest",))
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:evaluation:cool",
        context=start,
        action="cool",
        next_context=cooled,
        effects=(
            EffectObservation("energy_delta", -0.2, 1.0),
            EffectObservation("heat_delta", -0.5, 1.0),
        ),
    )
    _observe(
        model,
        event_id="real:evaluation:wait",
        context=start,
        action="wait",
        next_context=unchanged,
        effects=(
            EffectObservation("energy_delta", 0.0, 1.0),
            EffectObservation("heat_delta", 0.0, 1.0),
        ),
    )
    return model, start


def _need(*, code: str = "cooling", energy_intensity: float = 0.5) -> EffectNeed:
    return EffectNeed(
        need_code=code,
        primary_effect_code="heat_delta",
        dimensions=(
            NeedDimension("heat_delta", -1.0, 1.0),
            NeedDimension("energy_delta", 1.0, energy_intensity),
        ),
        satisfaction_threshold=0.5,
    )


def _candidates(
    model: LearnedConsequenceModel,
    start: ContextSignature,
    *,
    effects: tuple[str, ...] = ("energy_delta", "heat_delta"),
) -> tuple[ImaginedGeneratedCandidate, ...]:
    return (
        BoundedExactCandidateGenerator(model)
        .generate(
            ImaginedCandidateGenerationRequest(
                context=start,
                requested_effect_codes=effects,
                config=BoundedCandidateGenerationConfig(maximum_sequence_depth=1),
            )
        )
        .candidates
    )


def _two_step_candidate(
    model: LearnedConsequenceModel,
    start: ContextSignature,
) -> ImaginedGeneratedCandidate:
    middle = _context(0.4, ("rest",))
    final = _context(0.3, ("stop",))
    _observe(
        model,
        event_id="real:evaluation:rest",
        context=middle,
        action="rest",
        next_context=final,
        effects=(
            EffectObservation("energy_delta", 0.1, 1.0),
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
    return next(candidate for candidate in candidates if len(candidate.steps) == 2)


def test_per_effect_alignment_classifies_improving_worsening_and_neutral() -> None:
    model, start = _model()
    candidates = _candidates(model, start)

    result = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need(),
            candidates=candidates,
            config=BoundedRouteEvaluationConfig(neutral_tolerance=0.04),
        )
    )

    cool_step = result.evaluations[0].step_evaluations[0]
    source_step = candidates[0].steps[0]
    cool = cool_step.alignments
    wait = result.evaluations[1].step_evaluations[0].alignments
    cool_by_code = {item.effect_code: item for item in cool}

    assert cool_step.context == source_step.context
    assert cool_step.predicted_next_context == source_step.predicted_next_context
    assert cool_step.source_step_id == source_step.step_id
    assert cool_step.source_record_id == source_step.source_record_id
    assert cool_step.source_prediction_id == source_step.source_prediction_id
    assert cool_step.supporting_real_event_ids == source_step.supporting_real_event_ids

    assert cool_by_code["heat_delta"].direction is ImaginedAlignmentDirection.IMPROVING
    assert cool_by_code["heat_delta"].prediction_confidence == 0.25
    assert cool_by_code["heat_delta"].signed_alignment == 0.125
    assert cool_by_code["energy_delta"].direction is ImaginedAlignmentDirection.WORSENING
    assert cool_by_code["energy_delta"].prediction_confidence == 0.25
    assert cool_by_code["energy_delta"].signed_alignment == -0.05
    assert all(item.direction is ImaginedAlignmentDirection.NEUTRAL for item in wait)


def test_missing_effect_dimension_remains_unknown_not_neutral() -> None:
    model, start = _model()
    candidates = _candidates(model, start, effects=("heat_delta",))

    result = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(need=_need(), candidates=candidates)
    )
    energy = result.evaluations[0].step_evaluations[0].alignments[0]

    assert energy.effect_code == "energy_delta"
    assert energy.direction is ImaginedAlignmentDirection.UNKNOWN
    assert energy.predicted_value is None
    assert energy.signed_alignment is None
    assert energy.prediction_confidence == 0.0
    assert energy.supporting_real_event_ids == ()


def test_evaluation_preserves_caller_candidate_order_without_winner_or_rank() -> None:
    model, start = _model()
    candidates = _candidates(model, start)
    reversed_candidates = tuple(reversed(candidates))

    result = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need(),
            candidates=reversed_candidates,
        )
    )

    assert [item.candidate_id for item in result.evaluations] == [
        item.candidate_id for item in reversed_candidates
    ]
    snapshot_text = str(result.snapshot())
    for forbidden in (
        "route_score",
        "overall_score",
        "rank",
        "winner",
        "selected_candidate",
        "recommended_candidate",
    ):
        assert forbidden not in snapshot_text


def test_intensity_is_inspectable_but_does_not_create_hidden_aggregate() -> None:
    model, start = _model()
    candidate = _candidates(model, start)[0]

    low = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need(energy_intensity=0.2),
            candidates=(candidate,),
        )
    )
    high = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need(energy_intensity=0.9),
            candidates=(candidate,),
        )
    )
    low_energy = low.evaluations[0].step_evaluations[0].alignments[0]
    high_energy = high.evaluations[0].step_evaluations[0].alignments[0]

    assert low_energy.intensity == 0.2
    assert high_energy.intensity == 0.9
    assert low_energy.prediction_confidence == high_energy.prediction_confidence == 0.25
    assert low_energy.signed_alignment == high_energy.signed_alignment == -0.05
    assert "cumulative" not in str(low.snapshot())


def test_candidate_need_mismatch_is_rejected_before_evaluation() -> None:
    model, start = _model()
    candidates = _candidates(model, start)

    with pytest.raises(ValueError, match="active need"):
        ImaginedRouteEvaluationRequest(
            need=_need(code="cleanliness"),
            candidates=candidates,
        )


def test_later_step_need_change_is_rejected_before_evaluation() -> None:
    start = _context(0.9, ("cool",), need="cooling")
    middle = _context(0.4, ("clean",), need="cleanliness")
    final = _context(0.3, ("stop",), need="cleanliness")
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:evaluation:need-change:cool",
        context=start,
        action="cool",
        next_context=middle,
        effects=(EffectObservation("heat_delta", -0.5, 1.0),),
    )
    _observe(
        model,
        event_id="real:evaluation:need-change:clean",
        context=middle,
        action="clean",
        next_context=final,
        effects=(EffectObservation("heat_delta", -0.1, 1.0),),
    )
    candidates = (
        BoundedExactCandidateGenerator(model)
        .generate(
            ImaginedCandidateGenerationRequest(
                context=start,
                requested_effect_codes=("heat_delta",),
                config=BoundedCandidateGenerationConfig(maximum_sequence_depth=2),
            )
        )
        .candidates
    )
    two_step = next(candidate for candidate in candidates if len(candidate.steps) == 2)

    with pytest.raises(ValueError, match="active need"):
        ImaginedRouteEvaluationRequest(need=_need(), candidates=(two_step,))


def test_empty_candidate_request_returns_empty_deterministic_result() -> None:
    request = ImaginedRouteEvaluationRequest(need=_need(), candidates=())

    result = BoundedImaginedRouteEvaluator().evaluate(request)

    assert result.evaluations == ()
    assert result.snapshot_json_ascii().decode("ascii")


def test_request_bounds_are_atomic() -> None:
    model, start = _model()
    candidates = _candidates(model, start)
    candidate = candidates[0]

    with pytest.raises(ValueError, match="candidate bound"):
        ImaginedRouteEvaluationRequest(
            need=_need(),
            candidates=(candidate, candidates[1]),
            config=BoundedRouteEvaluationConfig(maximum_candidates=1),
        )

    two_step_candidate = _two_step_candidate(model, start)
    with pytest.raises(ValueError, match="candidate step bound"):
        ImaginedRouteEvaluationRequest(
            need=_need(),
            candidates=(two_step_candidate,),
            config=BoundedRouteEvaluationConfig(maximum_steps_per_candidate=1),
        )

    many_dimensions = tuple(NeedDimension(f"effect_{index:02d}", 1.0, 1.0) for index in range(17))
    with pytest.raises(ValueError, match="need-dimension bound"):
        ImaginedRouteEvaluationRequest(
            need=EffectNeed(
                need_code="cooling",
                primary_effect_code="effect_00",
                dimensions=many_dimensions,
                satisfaction_threshold=0.5,
            ),
            candidates=(candidate,),
        )


def test_repeated_evaluation_is_identity_stable_and_ascii() -> None:
    model, start = _model()
    candidates = _candidates(model, start)
    request_a = ImaginedRouteEvaluationRequest(need=_need(), candidates=candidates)
    request_b = ImaginedRouteEvaluationRequest(need=_need(), candidates=candidates)

    result_a = BoundedImaginedRouteEvaluator().evaluate(request_a)
    result_b = BoundedImaginedRouteEvaluator().evaluate(request_b)

    assert request_a.request_id == request_b.request_id
    assert result_a.result_id == result_b.result_id
    assert result_a.snapshot_json_ascii() == result_b.snapshot_json_ascii()
    assert result_a.snapshot_json_ascii().decode("ascii")


def test_evaluation_preserves_zero_evidence_and_authority_changes() -> None:
    model, start = _model()
    before = model.snapshot()
    result = BoundedImaginedRouteEvaluator().evaluate(
        ImaginedRouteEvaluationRequest(
            need=_need(),
            candidates=_candidates(model, start),
        )
    )

    assert before == model.snapshot()
    assert result.factual_confidence_change == 0.0
    assert result.mastery_change == 0.0
    assert result.competence_change == 0.0
    assert result.growth_pressure_change == 0.0
    assert result.replay_evidence_change == 0.0
    assert result.real_observation_change == 0.0
    assert result.has_action_selection_authority is False
    assert result.has_production_action_authority is False
    for evaluation in result.evaluations:
        assert evaluation.factual_confidence_change == 0.0
        assert evaluation.mastery_change == 0.0
        assert evaluation.competence_change == 0.0
        assert evaluation.growth_pressure_change == 0.0
        assert evaluation.replay_evidence_change == 0.0
        assert evaluation.real_observation_change == 0.0
        for step in evaluation.step_evaluations:
            assert step.factual_confidence_change == 0.0
            assert step.mastery_change == 0.0
            assert step.competence_change == 0.0
            assert step.growth_pressure_change == 0.0
            assert step.replay_evidence_change == 0.0
            assert step.real_observation_change == 0.0
            assert step.has_action_selection_authority is False
            assert step.has_production_action_authority is False


def test_actual_evaluation_cannot_update_real_consequence_evidence() -> None:
    model, start = _model()
    evaluation = (
        BoundedImaginedRouteEvaluator()
        .evaluate(
            ImaginedRouteEvaluationRequest(
                need=_need(),
                candidates=(_candidates(model, start)[0],),
            )
        )
        .evaluations[0]
    )
    before = model.snapshot()

    with pytest.raises(ValueError, match="only real observations"):
        model.observe(cast(Any, evaluation))

    assert before == model.snapshot()


def test_static_dependencies_exclude_generation_execution_and_storage_surfaces() -> None:
    source = Path("src/seedmind/research/ndnra/bounded_imagination_evaluation.py").read_text(
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
        "seedmind.integration",
        "seedmind.environment",
        "seedmind.curiosity",
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
    assert ".generate(" not in source
    assert ".imagine(" not in source
    assert "optimise(" not in source
    assert "optimize(" not in source
