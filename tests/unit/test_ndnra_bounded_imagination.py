"""Tests for exact-source-only bounded imagination."""

from __future__ import annotations

from pathlib import Path
from typing import Any, cast

import pytest

from seedmind.research.ndnra import (
    BoundedConsequenceImagination,
    BoundedImaginationConfig,
    ConsequenceModelObservation,
    ConsequencePredictionRequest,
    ContextSignature,
    EffectObservation,
    ExperienceOrigin,
    ImaginedActionSequence,
    ImaginedConsequenceRequest,
    LearnedConsequenceModel,
    LearnedConsequenceModelConfig,
)


def _context(
    *,
    heat: float,
    actions: tuple[str, ...],
    need: str = "cooling",
) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code=need,
        sensor_values=(heat, 0.0),
        available_action_codes=actions,
    )


def _observation(
    *,
    event_id: str,
    context: ContextSignature,
    action_code: str,
    next_context: ContextSignature,
    effects: tuple[EffectObservation, ...],
) -> ConsequenceModelObservation:
    return ConsequenceModelObservation(
        event_id=event_id,
        origin=ExperienceOrigin.REAL,
        context=context,
        action_code=action_code,
        next_context=next_context,
        observed_effects=effects,
    )


def _trained_model() -> tuple[
    LearnedConsequenceModel, ContextSignature, ContextSignature, ContextSignature
]:
    start = _context(heat=0.8, actions=("cool", "wait"))
    middle = _context(heat=0.4, actions=("fan", "wait"))
    final = _context(heat=0.1, actions=("wait",))
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:cool:1",
            context=start,
            action_code="cool",
            next_context=middle,
            effects=(
                EffectObservation("energy_delta", -0.2, 1.0),
                EffectObservation("heat_delta", -0.6, 1.0),
            ),
        )
    )
    model.observe(
        _observation(
            event_id="real:fan:1",
            context=middle,
            action_code="fan",
            next_context=final,
            effects=(
                EffectObservation("energy_delta", -0.1, 1.0),
                EffectObservation("heat_delta", -0.3, 1.0),
            ),
        )
    )
    return model, start, middle, final


def test_valid_two_step_trace_preserves_order_continuity_and_provenance() -> None:
    model, start, middle, final = _trained_model()
    request = ImaginedConsequenceRequest(
        context=start,
        relevant_effect_codes=("energy_delta", "heat_delta"),
        candidate_sequences=(ImaginedActionSequence(("cool", "fan")),),
    )

    result = BoundedConsequenceImagination(model).imagine(request)

    assert result.request.request_id == request.request_id
    assert len(result.traces) == 1
    trace = result.traces[0]
    assert trace.supported is True
    assert trace.candidate_sequence.action_codes == ("cool", "fan")
    assert trace.final_context == final
    assert trace.steps[0].origin is ExperienceOrigin.IMAGINED
    assert trace.steps[1].origin is ExperienceOrigin.IMAGINED
    assert trace.steps[0].context == start
    assert trace.steps[0].predicted_next_context == middle
    assert trace.steps[1].context == middle
    assert trace.steps[1].predicted_next_context == final
    assert (
        trace.steps[0].source_prediction_id
        == model.predict(request=_prediction_request(start, "cool")).prediction_id
    )
    assert (
        trace.steps[1].source_prediction_id
        == model.predict(request=_prediction_request(middle, "fan")).prediction_id
    )
    assert trace.steps[0].supporting_real_event_ids == ("real:cool:1",)
    assert trace.steps[1].supporting_real_event_ids == ("real:fan:1",)
    assert trace.supporting_real_event_ids == ("real:cool:1", "real:fan:1")


def test_reversed_order_remains_distinct_without_ranking_or_selection_fields() -> None:
    model, start, _, _ = _trained_model()
    request = ImaginedConsequenceRequest(
        context=start,
        relevant_effect_codes=("energy_delta", "heat_delta"),
        candidate_sequences=(
            ImaginedActionSequence(("cool", "fan")),
            ImaginedActionSequence(("fan", "cool")),
        ),
    )

    result = BoundedConsequenceImagination(model).imagine(request)

    assert tuple(trace.candidate_sequence.action_codes for trace in result.traces) == (
        ("cool", "fan"),
        ("fan", "cool"),
    )
    assert result.traces[0].trace_id != result.traces[1].trace_id
    assert result.traces[0].supported is True
    assert result.traces[1].supported is False
    snapshot = result.snapshot()
    for forbidden_key in ("score", "selected_candidate", "recommended_candidate", "execution"):
        assert forbidden_key not in snapshot


def test_unsupported_failures_stop_at_first_missing_step_without_final_context() -> None:
    model, start, middle, _ = _trained_model()

    class MissingNextContextModel:
        def __init__(self, base: LearnedConsequenceModel) -> None:
            self._base = base

        def snapshot(self) -> dict[str, object]:
            return self._base.snapshot()

        def predict(self, request: Any) -> Any:
            prediction = self._base.predict(request)
            return type(
                "PredictionWithoutNextContext",
                (),
                {
                    "request": prediction.request,
                    "predicted_effects": prediction.predicted_effects,
                    "predicted_next_context": None,
                    "prediction_id": prediction.prediction_id,
                    "supporting_real_event_ids": prediction.supporting_real_event_ids,
                },
            )()

    nextless_start = _context(heat=0.3, actions=("wait",))
    nextless_final = _context(heat=0.2, actions=("wait",))
    nextless_model = LearnedConsequenceModel()
    nextless_model.observe(
        _observation(
            event_id="real:wait:1",
            context=nextless_start,
            action_code="wait",
            next_context=nextless_final,
            effects=(EffectObservation("heat_delta", -0.1, 1.0),),
        )
    )

    unavailable = (
        BoundedConsequenceImagination(model)
        .imagine(
            ImaginedConsequenceRequest(
                context=start,
                relevant_effect_codes=("energy_delta", "heat_delta"),
                candidate_sequences=(ImaginedActionSequence(("fan",)),),
            )
        )
        .traces[0]
    )
    missing_evidence = (
        BoundedConsequenceImagination(model)
        .imagine(
            ImaginedConsequenceRequest(
                context=middle,
                relevant_effect_codes=("energy_delta", "heat_delta", "water_delta"),
                candidate_sequences=(ImaginedActionSequence(("fan",)),),
            )
        )
        .traces[0]
    )
    missing_next_context = (
        BoundedConsequenceImagination(cast(Any, MissingNextContextModel(nextless_model)))
        .imagine(
            ImaginedConsequenceRequest(
                context=nextless_start,
                relevant_effect_codes=("heat_delta",),
                candidate_sequences=(ImaginedActionSequence(("wait",)),),
            )
        )
        .traces[0]
    )

    assert unavailable.final_context is None
    assert unavailable.steps[-1].failure_reason == "action_unavailable"
    assert len(unavailable.steps) == 1
    assert missing_evidence.final_context is None
    assert missing_evidence.steps[-1].failure_reason == "missing_exact_evidence"
    assert len(missing_evidence.steps) == 1
    assert missing_next_context.final_context is None
    assert missing_next_context.steps[-1].failure_reason == "missing_exact_next_context"
    assert len(missing_next_context.steps) == 1


def test_partial_effects_remain_partial_without_cumulative_aggregate() -> None:
    start = _context(heat=0.8, actions=("cool",))
    next_context = _context(heat=0.5, actions=("wait",))
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:cool:partial",
            context=start,
            action_code="cool",
            next_context=next_context,
            effects=(EffectObservation("heat_delta", -0.4, 1.0),),
        )
    )

    trace = (
        BoundedConsequenceImagination(model)
        .imagine(
            ImaginedConsequenceRequest(
                context=start,
                relevant_effect_codes=("energy_delta", "heat_delta"),
                candidate_sequences=(ImaginedActionSequence(("cool",)),),
            )
        )
        .traces[0]
    )

    assert trace.supported is False
    assert tuple(effect.effect_code for effect in trace.steps[0].predicted_effects) == (
        "heat_delta",
    )
    assert trace.snapshot().get("cumulative_effects") is None


def test_transfer_like_context_stays_unsupported_and_model_is_unchanged() -> None:
    model, _, _, _ = _trained_model()
    shifted = _context(heat=0.95, actions=("cool", "wait"))
    before = model.snapshot()

    trace = (
        BoundedConsequenceImagination(model)
        .imagine(
            ImaginedConsequenceRequest(
                context=shifted,
                relevant_effect_codes=("energy_delta", "heat_delta"),
                candidate_sequences=(ImaginedActionSequence(("cool",)),),
            )
        )
        .traces[0]
    )

    assert trace.supported is False
    assert trace.steps[0].failure_reason == "missing_exact_evidence"
    assert before == model.snapshot()


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        (
            {
                "candidate_sequences": tuple(
                    ImaginedActionSequence((f"cool_{index}",)) for index in range(9)
                )
            },
            "candidate-count",
        ),
        (
            {"candidate_sequences": (ImaginedActionSequence(("cool", "fan", "wait", "rest")),)},
            "sequence-depth",
        ),
        (
            {
                "candidate_sequences": (
                    ImaginedActionSequence(("cool", "fan")),
                    ImaginedActionSequence(("cool", "fan")),
                )
            },
            "duplicate candidate sequences",
        ),
        (
            {
                "config": BoundedImaginationConfig(maximum_total_prediction_steps=23),
                "candidate_sequences": tuple(
                    ImaginedActionSequence((f"cool_{index}", f"fan_{index}", f"wait_{index}"))
                    for index in range(8)
                ),
            },
            "total prediction-step",
        ),
        (
            {"relevant_effect_codes": tuple(f"effect_{index:02d}" for index in range(17))},
            "effect-dimension",
        ),
    ],
)
def test_request_bounds_reject_without_mutation(
    kwargs: dict[str, object],
    message: str,
) -> None:
    model, start, _, _ = _trained_model()
    before = model.snapshot()
    base_kwargs: dict[str, object] = {
        "context": start,
        "relevant_effect_codes": ("energy_delta", "heat_delta"),
        "candidate_sequences": (ImaginedActionSequence(("cool",)),),
    }
    base_kwargs.update(kwargs)

    with pytest.raises(ValueError, match=message):
        ImaginedConsequenceRequest(**cast(Any, base_kwargs))
    assert before == model.snapshot()


def test_runtime_bounds_return_unsupported_trace_without_mutation() -> None:
    _, start, _, _ = _trained_model()
    constrained = LearnedConsequenceModel(
        config=LearnedConsequenceModelConfig(maximum_real_observations=64)
    )
    constrained.observe(
        _observation(
            event_id="real:alpha",
            context=start,
            action_code="cool",
            next_context=_context(heat=0.5, actions=("wait",)),
            effects=(
                EffectObservation("energy_delta", -0.2, 1.0),
                EffectObservation("heat_delta", -0.4, 1.0),
            ),
        )
    )
    constrained.observe(
        _observation(
            event_id="real:beta",
            context=start,
            action_code="cool",
            next_context=_context(heat=0.5, actions=("wait",)),
            effects=(
                EffectObservation("energy_delta", -0.2, 1.0),
                EffectObservation("heat_delta", -0.4, 1.0),
            ),
        )
    )
    before = constrained.snapshot()
    request = ImaginedConsequenceRequest(
        context=start,
        relevant_effect_codes=("energy_delta", "heat_delta"),
        candidate_sequences=(ImaginedActionSequence(("cool",)),),
        config=BoundedImaginationConfig(maximum_supporting_real_event_ids_per_trace=1),
    )

    trace = BoundedConsequenceImagination(constrained).imagine(request).traces[0]

    assert trace.origin is ExperienceOrigin.IMAGINED
    assert trace.supported is False
    assert trace.final_context is None
    assert trace.steps[-1].failure_reason == "supporting_source_event_bound_exceeded"
    assert trace.supporting_real_event_ids == ()
    assert before == constrained.snapshot()


def test_duplicate_candidate_sequences_are_rejected() -> None:
    _, start, _, _ = _trained_model()

    with pytest.raises(ValueError, match="duplicate candidate sequences"):
        ImaginedConsequenceRequest(
            context=start,
            relevant_effect_codes=("energy_delta", "heat_delta"),
            candidate_sequences=(
                ImaginedActionSequence(("cool", "fan")),
                ImaginedActionSequence(("cool", "fan")),
            ),
        )


def test_identical_requests_produce_identical_ids_and_ascii_snapshots() -> None:
    model, start, _, _ = _trained_model()
    imagination = BoundedConsequenceImagination(model)
    request_a = ImaginedConsequenceRequest(
        context=start,
        relevant_effect_codes=("energy_delta", "heat_delta"),
        candidate_sequences=(ImaginedActionSequence(("cool", "fan")),),
    )
    request_b = ImaginedConsequenceRequest(
        context=start,
        relevant_effect_codes=("energy_delta", "heat_delta"),
        candidate_sequences=(ImaginedActionSequence(("cool", "fan")),),
    )

    result_a = imagination.imagine(request_a)
    result_b = imagination.imagine(request_b)

    assert request_a.request_id == request_b.request_id
    assert result_a.result_id == result_b.result_id
    assert result_a.traces[0].trace_id == result_b.traces[0].trace_id
    assert result_a.snapshot_json_ascii() == result_b.snapshot_json_ascii()
    assert request_a.snapshot_json_ascii().decode("ascii")
    assert result_a.snapshot_json_ascii().decode("ascii")


def test_imagination_changes_no_real_evidence_or_authority_state() -> None:
    model, start, _, _ = _trained_model()
    before = model.snapshot()

    result = BoundedConsequenceImagination(model).imagine(
        ImaginedConsequenceRequest(
            context=start,
            relevant_effect_codes=("energy_delta", "heat_delta"),
            candidate_sequences=(ImaginedActionSequence(("cool", "fan")),),
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


def test_static_dependencies_exclude_forbidden_integration_surfaces() -> None:
    source = Path("src/seedmind/research/ndnra/bounded_imagination.py").read_text(encoding="ascii")

    for forbidden in (
        "import sqlite3",
        "from sqlite3",
        "import asyncio",
        "from asyncio",
        "import threading",
        "from threading",
        "import time",
        "from time import",
    ):
        assert forbidden not in source


def test_snapshots_encode_as_ascii() -> None:
    model, start, _, _ = _trained_model()
    result = BoundedConsequenceImagination(model).imagine(
        ImaginedConsequenceRequest(
            context=start,
            relevant_effect_codes=("energy_delta", "heat_delta"),
            candidate_sequences=(ImaginedActionSequence(("cool",)),),
        )
    )

    result.snapshot_json_ascii().decode("ascii")
    result.request.snapshot_json_ascii().decode("ascii")


def test_imagined_types_cannot_be_accepted_as_real_consequence_evidence() -> None:
    model, start, _, _ = _trained_model()

    with pytest.raises(ValueError, match="only real observations"):
        model.observe(
            ConsequenceModelObservation(
                event_id="imagined:not-real",
                origin=ExperienceOrigin.IMAGINED,
                context=start,
                action_code="cool",
                next_context=start,
                observed_effects=(EffectObservation("heat_delta", -0.1, 1.0),),
            )
        )


def _prediction_request(
    context: ContextSignature,
    action_code: str,
) -> ConsequencePredictionRequest:
    return ConsequencePredictionRequest(
        context=context,
        action_code=action_code,
        relevant_effect_codes=("energy_delta", "heat_delta"),
    )
