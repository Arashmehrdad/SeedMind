"""Tests for the bounded exact-context learned consequence model."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.learned_consequence_model import (
    CalibrationDirection,
    ConsequenceModelObservation,
    ConsequencePredictionRequest,
    LearnedConsequenceModel,
    LearnedConsequenceModelConfig,
)


def _context(*, inside_heat: float, outside_heat: float) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code="reduce_temperature",
        sensor_values=(inside_heat, outside_heat),
        available_action_codes=("open_window", "start_fan"),
        resource_values=(0.8,),
    )


def _observation(
    *,
    event_id: str,
    context: ContextSignature,
    next_context: ContextSignature,
    temperature_effect: float,
    energy_effect: float = 0.0,
    action_code: str = "open_window",
    origin: ExperienceOrigin = ExperienceOrigin.REAL,
) -> ConsequenceModelObservation:
    return ConsequenceModelObservation(
        event_id=event_id,
        origin=origin,
        context=context,
        action_code=action_code,
        next_context=next_context,
        observed_effects=(
            EffectObservation("energy_cost", energy_effect, 1.0),
            EffectObservation("temperature", temperature_effect, 1.0),
        ),
    )


def _request(
    context: ContextSignature,
    *,
    action_code: str = "open_window",
    effect_codes: tuple[str, ...] = ("energy_cost", "temperature"),
) -> ConsequencePredictionRequest:
    return ConsequencePredictionRequest(
        context=context,
        action_code=action_code,
        relevant_effect_codes=effect_codes,
    )


def test_unknown_context_action_reports_complete_uncertainty() -> None:
    model = LearnedConsequenceModel()
    request = _request(_context(inside_heat=0.8, outside_heat=0.3))

    prediction = model.predict(request)

    assert prediction.predicted_effects == ()
    assert prediction.predicted_next_context is None
    assert prediction.effect_coverage == 0.0
    assert prediction.evidence_coverage == 0.0
    assert prediction.raw_confidence == 0.0
    assert prediction.calibrated_confidence == 0.0
    assert prediction.uncertainty == 1.0
    assert prediction.supporting_real_event_ids == ()
    assert prediction.evidence_count == 0
    assert not prediction.has_action_selection_authority
    assert not prediction.has_production_action_authority


def test_one_real_transition_creates_a_single_step_prediction() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()

    update = model.observe(
        _observation(
            event_id="real:model:001",
            context=before,
            next_context=after,
            temperature_effect=-0.4,
        )
    )
    prediction = model.predict(_request(before))

    assert update.evidence_applied
    assert update.real_observation_count_before == 0
    assert update.real_observation_count_after == 1
    assert model.real_observation_count == 1
    assert model.record_count == 1
    assert prediction.predicted_next_context == after
    assert tuple(effect.effect_code for effect in prediction.predicted_effects) == (
        "energy_cost",
        "temperature",
    )
    assert prediction.predicted_effects[0].value == 0.0
    assert prediction.predicted_effects[1].value == pytest.approx(-0.4)
    assert prediction.effect_coverage == 1.0
    assert prediction.evidence_coverage == pytest.approx(0.25)
    assert prediction.raw_confidence == pytest.approx(0.25)
    assert prediction.calibrated_confidence == pytest.approx(0.25)
    assert prediction.uncertainty == pytest.approx(0.75)
    assert prediction.supporting_real_event_ids == ("real:model:001",)


def test_consistent_real_outcomes_increase_support_and_correct_underconfidence() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:model:consistent:0",
            context=before,
            next_context=after,
            temperature_effect=-0.4,
        )
    )
    prior = model.predict(_request(before))

    update = model.observe(
        _observation(
            event_id="real:model:consistent:1",
            context=before,
            next_context=after,
            temperature_effect=-0.4,
        ),
        prior_prediction=prior,
    )
    prediction = model.predict(_request(before))

    assert update.evaluation is not None
    assert update.evaluation.combined_accuracy == 1.0
    assert update.evaluation.calibration_direction is CalibrationDirection.UNDERCONFIDENT
    assert update.confidence_after > update.confidence_before
    assert prediction.raw_confidence == pytest.approx(0.5)
    assert prediction.evidence_coverage == pytest.approx(0.5)
    assert prediction.calibrated_confidence == pytest.approx(0.5)
    assert prediction.calibrated_confidence <= prediction.evidence_coverage
    record = model.record_for(before, "open_window")
    assert record.calibration_count == 1
    assert record.mean_calibration_accuracy == 1.0
    assert record.mean_prior_confidence == pytest.approx(0.25)


def test_contradiction_reduces_confidence_and_marks_prior_overconfidence() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    cool_after = _context(inside_heat=0.4, outside_heat=0.3)
    hot_after = _context(inside_heat=0.9, outside_heat=0.9)
    model = LearnedConsequenceModel()

    for index in range(4):
        prior = model.predict(_request(before)) if index else None
        model.observe(
            _observation(
                event_id=f"real:model:stable:{index}",
                context=before,
                next_context=cool_after,
                temperature_effect=-0.5,
            ),
            prior_prediction=prior,
        )
    confident = model.predict(_request(before))

    update = model.observe(
        _observation(
            event_id="real:model:contradiction",
            context=before,
            next_context=hot_after,
            temperature_effect=0.5,
        ),
        prior_prediction=confident,
    )
    corrected = model.predict(_request(before))

    assert confident.calibrated_confidence > 0.8
    assert update.evaluation is not None
    assert update.evaluation.calibration_direction is CalibrationDirection.OVERCONFIDENT
    assert update.evaluation.next_context_accuracy == 0.0
    assert update.evaluation.effect_accuracy < 1.0
    assert corrected.raw_confidence < confident.raw_confidence
    assert corrected.calibrated_confidence < confident.calibrated_confidence
    assert corrected.uncertainty > confident.uncertainty


def test_most_frequent_exact_next_context_is_predicted_deterministically() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    common = _context(inside_heat=0.4, outside_heat=0.3)
    rare = _context(inside_heat=0.7, outside_heat=0.3)
    model = LearnedConsequenceModel()

    for index, next_context in enumerate((common, rare, common)):
        model.observe(
            _observation(
                event_id=f"real:model:next:{index}",
                context=before,
                next_context=next_context,
                temperature_effect=-0.3,
            )
        )

    prediction = model.predict(_request(before))

    assert prediction.predicted_next_context == common
    record_snapshot = model.record_for(before, "open_window").snapshot(model.config)
    next_contexts = cast(list[dict[str, object]], record_snapshot["next_contexts"])
    assert sum(cast(int, item["count"]) for item in next_contexts) == 3


def test_contexts_and_actions_never_share_model_evidence() -> None:
    cool_outside = _context(inside_heat=0.8, outside_heat=0.3)
    hot_outside = _context(inside_heat=0.8, outside_heat=0.9)
    cool_after = _context(inside_heat=0.4, outside_heat=0.3)
    hot_after = _context(inside_heat=0.9, outside_heat=0.9)
    model = LearnedConsequenceModel()

    model.observe(
        _observation(
            event_id="real:model:cool-window",
            context=cool_outside,
            next_context=cool_after,
            temperature_effect=-0.5,
        )
    )
    model.observe(
        _observation(
            event_id="real:model:hot-window",
            context=hot_outside,
            next_context=hot_after,
            temperature_effect=0.4,
        )
    )
    model.observe(
        _observation(
            event_id="real:model:fan",
            context=hot_outside,
            next_context=cool_after,
            temperature_effect=-0.6,
            energy_effect=-0.2,
            action_code="start_fan",
        )
    )

    cool_prediction = model.predict(_request(cool_outside))
    hot_prediction = model.predict(_request(hot_outside))
    fan_prediction = model.predict(_request(hot_outside, action_code="start_fan"))

    assert model.record_count == 3
    assert cool_prediction.predicted_effects[1].value < 0.0
    assert hot_prediction.predicted_effects[1].value > 0.0
    assert fan_prediction.predicted_effects[1].value < 0.0
    assert cool_prediction.supporting_real_event_ids == ("real:model:cool-window",)
    assert hot_prediction.supporting_real_event_ids == ("real:model:hot-window",)
    assert fan_prediction.supporting_real_event_ids == ("real:model:fan",)


def test_missing_requested_dimension_stays_unknown_and_limits_coverage() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    model.observe(
        ConsequenceModelObservation(
            event_id="real:model:partial-effect",
            origin=ExperienceOrigin.REAL,
            context=before,
            action_code="open_window",
            next_context=after,
            observed_effects=(EffectObservation("temperature", -0.4, 1.0),),
        )
    )

    prediction = model.predict(_request(before))

    assert tuple(effect.effect_code for effect in prediction.predicted_effects) == ("temperature",)
    assert prediction.effect_coverage == pytest.approx(0.5)
    assert prediction.evidence_coverage < 0.25
    assert prediction.calibrated_confidence <= prediction.evidence_coverage


def test_zero_confidence_effect_does_not_increase_effect_support() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    model.observe(
        ConsequenceModelObservation(
            event_id="real:model:zero-confidence",
            origin=ExperienceOrigin.REAL,
            context=before,
            action_code="open_window",
            next_context=after,
            observed_effects=(EffectObservation("temperature", -0.4, 0.0),),
        )
    )

    prediction = model.predict(_request(before, effect_codes=("temperature",)))
    record_snapshot = model.record_for(before, "open_window").snapshot(model.config)
    effects = cast(dict[str, dict[str, object]], record_snapshot["effects"])

    assert prediction.predicted_effects[0].confidence == 0.0
    assert effects["temperature"]["observation_count"] == 1
    assert effects["temperature"]["support"] == 0.0


def test_unobserved_outcome_dimension_remains_unknown_during_evaluation() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:model:known-effects",
            context=before,
            next_context=after,
            temperature_effect=-0.4,
            energy_effect=-0.8,
        )
    )
    prediction = model.predict(_request(before))
    later = ConsequenceModelObservation(
        event_id="real:model:partial-evaluation",
        origin=ExperienceOrigin.REAL,
        context=before,
        action_code="open_window",
        next_context=after,
        observed_effects=(EffectObservation("temperature", -0.4, 1.0),),
    )

    evaluation = model.evaluate(prediction, later)

    assert evaluation.effect_accuracy == 1.0
    assert evaluation.next_context_accuracy == 1.0
    assert evaluation.combined_accuracy == 1.0
    assert not evaluation.calibration_eligible
    assert evaluation.calibration_direction is CalibrationDirection.UNKNOWN


def test_prediction_request_respects_effect_dimension_bound() -> None:
    context = _context(inside_heat=0.8, outside_heat=0.3)
    model = LearnedConsequenceModel(
        config=LearnedConsequenceModelConfig(
            maximum_effect_dimensions_per_record=1,
        )
    )

    with pytest.raises(ValueError, match="prediction request effect-dimension bound"):
        model.predict(_request(context))


def test_prediction_evaluation_is_pure_and_requires_exact_real_transition() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    observation = _observation(
        event_id="real:model:evaluate",
        context=before,
        next_context=after,
        temperature_effect=-0.4,
    )
    model.observe(observation)
    prediction = model.predict(_request(before))
    snapshot_before = model.snapshot()

    evaluation = model.evaluate(
        prediction,
        replace(observation, event_id="real:model:evaluate:later"),
    )

    assert evaluation.calibration_eligible
    assert model.snapshot() == snapshot_before
    with pytest.raises(ValueError, match="only real observations"):
        model.evaluate(
            prediction,
            replace(
                observation,
                event_id="replay:model:evaluate",
                origin=ExperienceOrigin.REPLAY,
            ),
        )
    with pytest.raises(ValueError, match="context does not match"):
        model.evaluate(
            prediction,
            replace(
                observation,
                event_id="real:model:other-context",
                context=_context(inside_heat=0.8, outside_heat=0.9),
            ),
        )


def test_replay_and_imagination_cannot_update_the_model() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()

    for origin in (ExperienceOrigin.REPLAY, ExperienceOrigin.IMAGINED):
        with pytest.raises(ValueError, match="only real observations"):
            model.observe(
                _observation(
                    event_id=f"{origin.value}:model:001",
                    origin=origin,
                    context=before,
                    next_context=after,
                    temperature_effect=-0.4,
                )
            )

    assert model.real_observation_count == 0
    assert model.record_count == 0


def test_exact_duplicate_is_ignored_and_identity_conflict_is_rejected() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    observation = _observation(
        event_id="real:model:duplicate",
        context=before,
        next_context=after,
        temperature_effect=-0.4,
    )
    model = LearnedConsequenceModel()

    first = model.observe(observation)
    duplicate = model.observe(observation)

    assert first.evidence_applied
    assert not duplicate.evidence_applied
    assert model.real_observation_count == 1
    assert model.record_for(before, "open_window").real_observation_count == 1

    conflicting = replace(
        observation,
        observed_effects=(
            EffectObservation("energy_cost", 0.0, 1.0),
            EffectObservation("temperature", 0.4, 1.0),
        ),
    )
    with pytest.raises(ValueError, match="identity conflict"):
        model.observe(conflicting)


def test_record_and_observation_bounds_fail_before_model_insertion() -> None:
    first_context = _context(inside_heat=0.8, outside_heat=0.3)
    second_context = _context(inside_heat=0.9, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    first_observation = _observation(
        event_id="real:model:bounded:0",
        context=first_context,
        next_context=after,
        temperature_effect=-0.4,
    )

    observation_bounded = LearnedConsequenceModel(
        config=LearnedConsequenceModelConfig(
            maximum_records=2,
            maximum_real_observations=1,
        )
    )
    observation_bounded.observe(first_observation)
    observation_snapshot = observation_bounded.snapshot()
    with pytest.raises(ValueError, match="real-observation bound"):
        observation_bounded.observe(
            _observation(
                event_id="real:model:observation-bound:1",
                context=second_context,
                next_context=after,
                temperature_effect=-0.4,
            )
        )
    assert observation_bounded.snapshot() == observation_snapshot

    record_bounded = LearnedConsequenceModel(
        config=LearnedConsequenceModelConfig(
            maximum_records=1,
            maximum_real_observations=2,
        )
    )
    record_bounded.observe(first_observation)
    record_snapshot = record_bounded.snapshot()
    with pytest.raises(ValueError, match="record bound"):
        record_bounded.observe(
            _observation(
                event_id="real:model:record-bound:1",
                context=second_context,
                next_context=after,
                temperature_effect=-0.4,
            )
        )
    assert record_bounded.snapshot() == record_snapshot


def test_effect_dimension_and_next_context_bounds_are_atomic() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    first_after = _context(inside_heat=0.4, outside_heat=0.3)
    second_after = _context(inside_heat=0.5, outside_heat=0.3)
    model = LearnedConsequenceModel(
        config=LearnedConsequenceModelConfig(
            maximum_effect_dimensions_per_record=1,
            maximum_next_contexts_per_record=1,
        )
    )
    first = ConsequenceModelObservation(
        event_id="real:model:dimension-bound:0",
        origin=ExperienceOrigin.REAL,
        context=before,
        action_code="open_window",
        next_context=first_after,
        observed_effects=(EffectObservation("temperature", -0.4, 1.0),),
    )
    model.observe(first)
    snapshot_before = model.snapshot()

    with pytest.raises(ValueError, match="effect-dimension bound"):
        model.observe(
            ConsequenceModelObservation(
                event_id="real:model:dimension-bound:1",
                origin=ExperienceOrigin.REAL,
                context=before,
                action_code="open_window",
                next_context=first_after,
                observed_effects=(
                    EffectObservation("energy_cost", -0.1, 1.0),
                    EffectObservation("temperature", -0.4, 1.0),
                ),
            )
        )
    assert model.snapshot() == snapshot_before

    with pytest.raises(ValueError, match="next-context bound"):
        model.observe(
            ConsequenceModelObservation(
                event_id="real:model:context-bound:1",
                origin=ExperienceOrigin.REAL,
                context=before,
                action_code="open_window",
                next_context=second_after,
                observed_effects=(EffectObservation("temperature", -0.4, 1.0),),
            )
        )
    assert model.snapshot() == snapshot_before


def test_stable_ordering_and_authority_contracts_are_enforced() -> None:
    context = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)

    with pytest.raises(ValueError, match="stable sorted"):
        ConsequencePredictionRequest(
            context=context,
            action_code="open_window",
            relevant_effect_codes=("temperature", "energy_cost"),
        )
    with pytest.raises(ValueError, match="cannot select actions"):
        replace(_request(context), has_action_selection_authority=True)
    with pytest.raises(ValueError, match="cannot control production actions"):
        replace(
            _observation(
                event_id="real:model:authority",
                context=context,
                next_context=after,
                temperature_effect=-0.4,
            ),
            has_production_action_authority=True,
        )
    with pytest.raises(ValueError, match="cannot select actions"):
        LearnedConsequenceModel(has_action_selection_authority=True)


def test_snapshots_are_deterministic_ascii_and_non_authoritative() -> None:
    before = _context(inside_heat=0.8, outside_heat=0.3)
    after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:model:snapshot",
            context=before,
            next_context=after,
            temperature_effect=-0.4,
        )
    )

    first = model.snapshot()
    second = model.snapshot()
    prediction = model.predict(_request(before)).snapshot()

    assert first == second
    assert str(first).isascii()
    assert str(prediction).isascii()
    assert first["real_event_ids"] == ["real:model:snapshot"]
    assert first["has_action_selection_authority"] is False
    assert first["has_production_action_authority"] is False


def test_model_has_no_execution_persistence_timer_or_imagination_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/learned_consequence_model.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert ".step(" not in source
    assert ".compose(" not in source
    assert ".apply(" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "optimizer" not in source
    assert "rollout" not in source
    assert "seedmind.integration" not in source
