"""Bounded single-step consequence learning from exact real context-action evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite, sqrt

from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectObservation


class CalibrationDirection(StrEnum):
    """How prior confidence compared with one later real outcome."""

    UNKNOWN = "unknown"
    OVERCONFIDENT = "overconfident"
    CALIBRATED = "calibrated"
    UNDERCONFIDENT = "underconfident"


@dataclass(frozen=True, slots=True)
class LearnedConsequenceModelConfig:
    """Finite evidence, dimensionality, and calibration bounds."""

    evidence_target: int = 4
    calibration_target: int = 4
    calibration_tolerance: float = 0.05
    maximum_records: int = 256
    maximum_real_observations: int = 4096
    maximum_effect_dimensions_per_record: int = 16
    maximum_next_contexts_per_record: int = 16

    def __post_init__(self) -> None:
        for name, value in (
            ("evidence_target", self.evidence_target),
            ("calibration_target", self.calibration_target),
            ("maximum_records", self.maximum_records),
            ("maximum_real_observations", self.maximum_real_observations),
            (
                "maximum_effect_dimensions_per_record",
                self.maximum_effect_dimensions_per_record,
            ),
            ("maximum_next_contexts_per_record", self.maximum_next_contexts_per_record),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        _validate_unit("calibration_tolerance", self.calibration_tolerance)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable model limits."""
        return {
            "evidence_target": self.evidence_target,
            "calibration_target": self.calibration_target,
            "calibration_tolerance": self.calibration_tolerance,
            "maximum_records": self.maximum_records,
            "maximum_real_observations": self.maximum_real_observations,
            "maximum_effect_dimensions_per_record": (self.maximum_effect_dimensions_per_record),
            "maximum_next_contexts_per_record": self.maximum_next_contexts_per_record,
        }


@dataclass(frozen=True, slots=True)
class ConsequenceModelObservation:
    """One exact observed transition offered to the learned model."""

    event_id: str
    origin: ExperienceOrigin
    context: ContextSignature
    action_code: str
    next_context: ContextSignature
    observed_effects: tuple[EffectObservation, ...]
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("event_id", self.event_id)
        _validate_code("action_code", self.action_code)
        _validate_effects("observed_effects", self.observed_effects, allow_empty=False)
        if self.has_action_selection_authority:
            raise ValueError("consequence observations cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("consequence observations cannot control production actions")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic source-labelled transition evidence."""
        return {
            "event_id": self.event_id,
            "origin": self.origin.value,
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "next_context": self.next_context.snapshot(),
            "observed_effects": [_effect_snapshot(item) for item in self.observed_effects],
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsequencePredictionRequest:
    """Explicit bounded request for relevant effects under one exact context and action."""

    context: ContextSignature
    action_code: str
    relevant_effect_codes: tuple[str, ...]
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("action_code", self.action_code)
        _validate_sorted_unique_codes("relevant_effect_codes", self.relevant_effect_codes)
        if not self.relevant_effect_codes:
            raise ValueError("relevant_effect_codes must not be empty")
        if self.has_action_selection_authority:
            raise ValueError("prediction requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("prediction requests cannot control production actions")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic non-authoritative prediction input."""
        return {
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "relevant_effect_codes": list(self.relevant_effect_codes),
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsequencePrediction:
    """One inspectable single-step prediction with explicit uncertainty."""

    prediction_id: str
    request: ConsequencePredictionRequest
    predicted_effects: tuple[EffectObservation, ...]
    predicted_next_context: ContextSignature | None
    effect_coverage: float
    evidence_coverage: float
    raw_confidence: float
    calibrated_confidence: float
    uncertainty: float
    supporting_real_event_ids: tuple[str, ...]
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("prediction_id", self.prediction_id)
        _validate_effects("predicted_effects", self.predicted_effects, allow_empty=True)
        for name, value in (
            ("effect_coverage", self.effect_coverage),
            ("evidence_coverage", self.evidence_coverage),
            ("raw_confidence", self.raw_confidence),
            ("calibrated_confidence", self.calibrated_confidence),
            ("uncertainty", self.uncertainty),
        ):
            _validate_unit(name, value)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        predicted_codes = tuple(effect.effect_code for effect in self.predicted_effects)
        if set(predicted_codes) - set(self.request.relevant_effect_codes):
            raise ValueError("prediction contains an unrequested effect dimension")
        if self.uncertainty != 1.0 - self.calibrated_confidence:
            raise ValueError("uncertainty must equal one minus calibrated confidence")
        if self.has_action_selection_authority:
            raise ValueError("consequence predictions cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("consequence predictions cannot control production actions")
        if self.prediction_id != _prediction_id(self._identity_payload()):
            raise ValueError("consequence prediction identity is inconsistent")

    @property
    def evidence_count(self) -> int:
        """Return unique real events supporting this exact context-action record."""
        return len(self.supporting_real_event_ids)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable prediction evidence."""
        return {"prediction_id": self.prediction_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "predicted_effects": [_effect_snapshot(item) for item in self.predicted_effects],
            "predicted_next_context": (
                None
                if self.predicted_next_context is None
                else self.predicted_next_context.snapshot()
            ),
            "effect_coverage": self.effect_coverage,
            "evidence_coverage": self.evidence_coverage,
            "raw_confidence": self.raw_confidence,
            "calibrated_confidence": self.calibrated_confidence,
            "uncertainty": self.uncertainty,
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
            "evidence_count": self.evidence_count,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsequencePredictionEvaluation:
    """Pure comparison between one prior prediction and one later real observation."""

    prediction_id: str
    event_id: str
    effect_accuracy: float
    next_context_accuracy: float
    combined_accuracy: float
    prior_confidence: float
    calibration_error: float
    calibration_direction: CalibrationDirection
    calibration_eligible: bool

    def __post_init__(self) -> None:
        _validate_code("prediction_id", self.prediction_id)
        _validate_code("event_id", self.event_id)
        for name, value in (
            ("effect_accuracy", self.effect_accuracy),
            ("next_context_accuracy", self.next_context_accuracy),
            ("combined_accuracy", self.combined_accuracy),
            ("prior_confidence", self.prior_confidence),
            ("calibration_error", self.calibration_error),
        ):
            _validate_unit(name, value)
        if not self.calibration_eligible:
            if self.calibration_direction is not CalibrationDirection.UNKNOWN:
                raise ValueError("ineligible calibration must have unknown direction")
            if self.calibration_error != 0.0:
                raise ValueError("ineligible calibration must have zero error")
        elif self.calibration_direction is CalibrationDirection.UNKNOWN:
            raise ValueError("eligible calibration requires a known direction")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic comparison evidence."""
        return {
            "prediction_id": self.prediction_id,
            "event_id": self.event_id,
            "effect_accuracy": self.effect_accuracy,
            "next_context_accuracy": self.next_context_accuracy,
            "combined_accuracy": self.combined_accuracy,
            "prior_confidence": self.prior_confidence,
            "calibration_error": self.calibration_error,
            "calibration_direction": self.calibration_direction.value,
            "calibration_eligible": self.calibration_eligible,
        }


@dataclass(frozen=True, slots=True)
class ConsequenceModelUpdate:
    """Before-and-after evidence from one unique real model observation."""

    event_id: str
    record_id: str
    evidence_applied: bool
    real_observation_count_before: int
    real_observation_count_after: int
    confidence_before: float
    confidence_after: float
    evaluation: ConsequencePredictionEvaluation | None = None

    def __post_init__(self) -> None:
        _validate_code("event_id", self.event_id)
        _validate_code("record_id", self.record_id)
        for name, value in (
            ("real_observation_count_before", self.real_observation_count_before),
            ("real_observation_count_after", self.real_observation_count_after),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        _validate_unit("confidence_before", self.confidence_before)
        _validate_unit("confidence_after", self.confidence_after)
        expected_after = self.real_observation_count_before + int(self.evidence_applied)
        if self.real_observation_count_after != expected_after:
            raise ValueError("observation count change is inconsistent")


@dataclass(slots=True)
class _EffectStatistics:
    """Weighted real evidence for one effect dimension."""

    observation_count: int = 0
    weight_sum: float = 0.0
    weighted_value_sum: float = 0.0
    weighted_square_sum: float = 0.0

    def observe(self, observation: EffectObservation) -> None:
        weight = observation.confidence
        self.observation_count += 1
        self.weight_sum += weight
        self.weighted_value_sum += observation.value * weight
        self.weighted_square_sum += observation.value * observation.value * weight

    @property
    def mean(self) -> float:
        if self.weight_sum == 0.0:
            return 0.0
        return self.weighted_value_sum / self.weight_sum

    @property
    def variance(self) -> float:
        if self.weight_sum == 0.0:
            return 1.0
        second_moment = self.weighted_square_sum / self.weight_sum
        return max(0.0, min(1.0, second_moment - self.mean * self.mean))

    @property
    def consistency(self) -> float:
        return max(0.0, min(1.0, 1.0 - sqrt(self.variance)))

    def support(self, config: LearnedConsequenceModelConfig) -> float:
        return min(1.0, self.weight_sum / config.evidence_target)

    def confidence(self, config: LearnedConsequenceModelConfig) -> float:
        return self.support(config) * self.consistency

    def snapshot(self, config: LearnedConsequenceModelConfig) -> dict[str, object]:
        return {
            "observation_count": self.observation_count,
            "mean": self.mean,
            "variance": self.variance,
            "consistency": self.consistency,
            "support": self.support(config),
            "confidence": self.confidence(config),
        }


@dataclass(slots=True)
class ContextActionConsequenceRecord:
    """Exact-context single-action transition model learned from real events only."""

    context: ContextSignature
    action_code: str
    _real_event_ids: list[str] = field(default_factory=list)
    _effects: dict[str, _EffectStatistics] = field(default_factory=dict)
    _next_contexts: dict[str, ContextSignature] = field(default_factory=dict)
    _next_context_counts: dict[str, int] = field(default_factory=dict)
    calibration_count: int = 0
    cumulative_prediction_accuracy: float = 0.0
    cumulative_prediction_confidence: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("action_code", self.action_code)
        _validate_sorted_unique_codes("real_event_ids", tuple(self._real_event_ids))
        if self.calibration_count < 0:
            raise ValueError("calibration_count must not be negative")
        for name, value in (
            ("cumulative_prediction_accuracy", self.cumulative_prediction_accuracy),
            ("cumulative_prediction_confidence", self.cumulative_prediction_confidence),
        ):
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        if self.has_action_selection_authority:
            raise ValueError("consequence records cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("consequence records cannot control production actions")

    @property
    def record_id(self) -> str:
        """Return stable identity for one exact context and action."""
        return _record_id(self.context, self.action_code)

    @property
    def real_observation_count(self) -> int:
        return len(self._real_event_ids)

    @property
    def real_event_ids(self) -> tuple[str, ...]:
        return tuple(self._real_event_ids)

    @property
    def mean_calibration_accuracy(self) -> float:
        if self.calibration_count == 0:
            return 0.0
        return self.cumulative_prediction_accuracy / self.calibration_count

    @property
    def mean_prior_confidence(self) -> float:
        if self.calibration_count == 0:
            return 0.0
        return self.cumulative_prediction_confidence / self.calibration_count

    def predict(
        self,
        request: ConsequencePredictionRequest,
        config: LearnedConsequenceModelConfig,
    ) -> ConsequencePrediction:
        """Predict only requested effects plus the most frequent exact next context."""
        if request.context != self.context or request.action_code != self.action_code:
            raise ValueError("prediction request does not match consequence record")
        predicted_effects: list[EffectObservation] = []
        support_total = 0.0
        confidence_total = 0.0
        for effect_code in request.relevant_effect_codes:
            statistics = self._effects.get(effect_code)
            if statistics is None:
                continue
            support_total += statistics.support(config)
            confidence = statistics.confidence(config)
            confidence_total += confidence
            predicted_effects.append(
                EffectObservation(
                    effect_code=effect_code,
                    value=statistics.mean,
                    confidence=confidence,
                )
            )

        next_context, next_support, next_confidence = self._next_context_prediction(config)
        requested_count = len(request.relevant_effect_codes)
        effect_coverage = len(predicted_effects) / requested_count
        evidence_coverage = (support_total + next_support) / (requested_count + 1)
        raw_confidence = (confidence_total + next_confidence) / (requested_count + 1)
        calibrated_confidence = self._calibrated_confidence(
            raw_confidence,
            evidence_coverage,
            config,
        )
        payload = {
            "request": request.snapshot(),
            "predicted_effects": [_effect_snapshot(item) for item in predicted_effects],
            "predicted_next_context": (None if next_context is None else next_context.snapshot()),
            "effect_coverage": effect_coverage,
            "evidence_coverage": evidence_coverage,
            "raw_confidence": raw_confidence,
            "calibrated_confidence": calibrated_confidence,
            "uncertainty": 1.0 - calibrated_confidence,
            "supporting_real_event_ids": list(self.real_event_ids),
            "evidence_count": self.real_observation_count,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ConsequencePrediction(
            prediction_id=_prediction_id(payload),
            request=request,
            predicted_effects=tuple(predicted_effects),
            predicted_next_context=next_context,
            effect_coverage=effect_coverage,
            evidence_coverage=evidence_coverage,
            raw_confidence=raw_confidence,
            calibrated_confidence=calibrated_confidence,
            uncertainty=1.0 - calibrated_confidence,
            supporting_real_event_ids=self.real_event_ids,
        )

    def observe(
        self,
        observation: ConsequenceModelObservation,
        evaluation: ConsequencePredictionEvaluation | None,
        config: LearnedConsequenceModelConfig,
    ) -> None:
        """Apply one already-validated unique real transition."""
        if observation.context != self.context:
            raise ValueError("observation context does not match consequence record")
        if observation.action_code != self.action_code:
            raise ValueError("observation action does not match consequence record")
        new_effect_codes = {effect.effect_code for effect in observation.observed_effects} - set(
            self._effects
        )
        if len(self._effects) + len(new_effect_codes) > config.maximum_effect_dimensions_per_record:
            raise ValueError("consequence record effect-dimension bound exceeded")
        next_key = _context_id(observation.next_context)
        if (
            next_key not in self._next_contexts
            and len(self._next_contexts) >= config.maximum_next_contexts_per_record
        ):
            raise ValueError("consequence record next-context bound exceeded")

        for effect in observation.observed_effects:
            self._effects.setdefault(effect.effect_code, _EffectStatistics()).observe(effect)
        self._next_contexts[next_key] = observation.next_context
        self._next_context_counts[next_key] = self._next_context_counts.get(next_key, 0) + 1
        self._real_event_ids.append(observation.event_id)
        self._real_event_ids.sort()
        if evaluation is not None and evaluation.calibration_eligible:
            self.calibration_count += 1
            self.cumulative_prediction_accuracy += evaluation.combined_accuracy
            self.cumulative_prediction_confidence += evaluation.prior_confidence

    def snapshot(self, config: LearnedConsequenceModelConfig) -> dict[str, object]:
        """Return deterministic inspectable learned state."""
        return {
            "record_id": self.record_id,
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "real_observation_count": self.real_observation_count,
            "real_event_ids": list(self.real_event_ids),
            "effects": {
                effect_code: statistics.snapshot(config)
                for effect_code, statistics in sorted(self._effects.items())
            },
            "next_contexts": [
                {
                    "context_id": context_id,
                    "context": self._next_contexts[context_id].snapshot(),
                    "count": self._next_context_counts[context_id],
                }
                for context_id in sorted(self._next_contexts)
            ],
            "calibration_count": self.calibration_count,
            "mean_calibration_accuracy": self.mean_calibration_accuracy,
            "mean_prior_confidence": self.mean_prior_confidence,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    def _next_context_prediction(
        self,
        config: LearnedConsequenceModelConfig,
    ) -> tuple[ContextSignature | None, float, float]:
        if not self._next_context_counts:
            return None, 0.0, 0.0
        top_key = min(
            self._next_context_counts,
            key=lambda key: (-self._next_context_counts[key], key),
        )
        top_count = self._next_context_counts[top_key]
        support = min(1.0, self.real_observation_count / config.evidence_target)
        probability = top_count / self.real_observation_count
        return self._next_contexts[top_key], support, probability * support

    def _calibrated_confidence(
        self,
        raw_confidence: float,
        evidence_coverage: float,
        config: LearnedConsequenceModelConfig,
    ) -> float:
        if self.calibration_count == 0:
            return raw_confidence
        calibration_support = min(
            1.0,
            self.calibration_count / config.calibration_target,
        )
        adjusted = (
            raw_confidence * (1.0 - calibration_support)
            + self.mean_calibration_accuracy * calibration_support
        )
        return max(0.0, min(evidence_coverage, adjusted))


@dataclass(slots=True)
class LearnedConsequenceModel:
    """Bounded exact-context single-step model with no action authority."""

    config: LearnedConsequenceModelConfig = field(default_factory=LearnedConsequenceModelConfig)
    _observations: dict[str, ConsequenceModelObservation] = field(default_factory=dict)
    _records: dict[str, ContextActionConsequenceRecord] = field(default_factory=dict)
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_action_selection_authority:
            raise ValueError("learned consequence model cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("learned consequence model cannot control production actions")

    @property
    def real_observation_count(self) -> int:
        return len(self._observations)

    @property
    def record_count(self) -> int:
        return len(self._records)

    def predict(self, request: ConsequencePredictionRequest) -> ConsequencePrediction:
        """Return an exact-context prediction or explicit complete uncertainty."""
        self._validate_prediction_request(request)
        record = self._records.get(_record_id(request.context, request.action_code))
        if record is not None:
            return record.predict(request, self.config)
        payload: dict[str, object] = {
            "request": request.snapshot(),
            "predicted_effects": [],
            "predicted_next_context": None,
            "effect_coverage": 0.0,
            "evidence_coverage": 0.0,
            "raw_confidence": 0.0,
            "calibrated_confidence": 0.0,
            "uncertainty": 1.0,
            "supporting_real_event_ids": [],
            "evidence_count": 0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ConsequencePrediction(
            prediction_id=_prediction_id(payload),
            request=request,
            predicted_effects=(),
            predicted_next_context=None,
            effect_coverage=0.0,
            evidence_coverage=0.0,
            raw_confidence=0.0,
            calibrated_confidence=0.0,
            uncertainty=1.0,
            supporting_real_event_ids=(),
        )

    def evaluate(
        self,
        prediction: ConsequencePrediction,
        observation: ConsequenceModelObservation,
    ) -> ConsequencePredictionEvaluation:
        """Compare a prior prediction with one later real transition without learning."""
        self._validate_prediction_request(prediction.request)
        if observation.origin is not ExperienceOrigin.REAL:
            raise ValueError("only real observations may evaluate consequence predictions")
        if prediction.request.context != observation.context:
            raise ValueError("prediction context does not match observation")
        if prediction.request.action_code != observation.action_code:
            raise ValueError("prediction action does not match observation")

        predicted = {item.effect_code: item for item in prediction.predicted_effects}
        observed = {item.effect_code: item for item in observation.observed_effects}
        effect_scores: list[float] = []
        for effect_code in prediction.request.relevant_effect_codes:
            predicted_effect = predicted.get(effect_code)
            observed_effect = observed.get(effect_code)
            if predicted_effect is None or observed_effect is None:
                continue
            effect_scores.append(
                1.0
                - min(
                    1.0,
                    abs(predicted_effect.value - observed_effect.value) / 2.0,
                )
            )
        effect_accuracy = 0.0 if not effect_scores else sum(effect_scores) / len(effect_scores)
        next_context_accuracy = float(
            prediction.predicted_next_context is not None
            and prediction.predicted_next_context == observation.next_context
        )
        components: list[float] = []
        if effect_scores:
            components.append(effect_accuracy)
        if prediction.predicted_next_context is not None:
            components.append(next_context_accuracy)
        all_predicted_effects_observed = all(
            effect.effect_code in observed for effect in prediction.predicted_effects
        )
        eligible = bool(effect_scores) and all_predicted_effects_observed
        combined = 0.0 if not components else sum(components) / len(components)
        if not eligible:
            direction = CalibrationDirection.UNKNOWN
            calibration_error = 0.0
        else:
            difference = prediction.calibrated_confidence - combined
            calibration_error = abs(difference)
            if difference > self.config.calibration_tolerance:
                direction = CalibrationDirection.OVERCONFIDENT
            elif difference < -self.config.calibration_tolerance:
                direction = CalibrationDirection.UNDERCONFIDENT
            else:
                direction = CalibrationDirection.CALIBRATED
        return ConsequencePredictionEvaluation(
            prediction_id=prediction.prediction_id,
            event_id=observation.event_id,
            effect_accuracy=effect_accuracy,
            next_context_accuracy=next_context_accuracy,
            combined_accuracy=combined,
            prior_confidence=prediction.calibrated_confidence,
            calibration_error=calibration_error,
            calibration_direction=direction,
            calibration_eligible=eligible,
        )

    def observe(
        self,
        observation: ConsequenceModelObservation,
        *,
        prior_prediction: ConsequencePrediction | None = None,
    ) -> ConsequenceModelUpdate:
        """Apply one unique real transition and optional prior-prediction calibration."""
        if observation.origin is not ExperienceOrigin.REAL:
            raise ValueError("only real observations may update the consequence model")
        if len(observation.observed_effects) > self.config.maximum_effect_dimensions_per_record:
            raise ValueError("consequence record effect-dimension bound exceeded")
        if prior_prediction is not None:
            self._validate_prediction_request(prior_prediction.request)
        existing = self._observations.get(observation.event_id)
        record_id = _record_id(observation.context, observation.action_code)
        record = self._records.get(record_id)
        if existing is not None:
            if existing != observation:
                raise ValueError("consequence model event identity conflict")
            if record is None:
                raise RuntimeError("record missing for retained consequence observation")
            relevant_codes = (
                tuple(effect.effect_code for effect in observation.observed_effects)
                if prior_prediction is None
                else prior_prediction.request.relevant_effect_codes
            )
            confidence = record.predict(
                ConsequencePredictionRequest(
                    context=observation.context,
                    action_code=observation.action_code,
                    relevant_effect_codes=relevant_codes,
                ),
                self.config,
            ).calibrated_confidence
            return ConsequenceModelUpdate(
                event_id=observation.event_id,
                record_id=record_id,
                evidence_applied=False,
                real_observation_count_before=record.real_observation_count,
                real_observation_count_after=record.real_observation_count,
                confidence_before=confidence,
                confidence_after=confidence,
            )
        if self.real_observation_count >= self.config.maximum_real_observations:
            raise ValueError("consequence model real-observation bound exceeded")
        if record is None and self.record_count >= self.config.maximum_records:
            raise ValueError("consequence model record bound exceeded")

        relevant_codes = (
            tuple(effect.effect_code for effect in observation.observed_effects)
            if prior_prediction is None
            else prior_prediction.request.relevant_effect_codes
        )
        request = ConsequencePredictionRequest(
            context=observation.context,
            action_code=observation.action_code,
            relevant_effect_codes=relevant_codes,
        )
        if prior_prediction is not None and prior_prediction.request != request:
            raise ValueError("prior prediction does not match observation request")
        before_prediction = self.predict(request)
        evaluation = (
            None if prior_prediction is None else self.evaluate(prior_prediction, observation)
        )
        target = (
            ContextActionConsequenceRecord(
                context=observation.context,
                action_code=observation.action_code,
            )
            if record is None
            else record
        )
        count_before = target.real_observation_count
        target.observe(observation, evaluation, self.config)
        if record is None:
            self._records[record_id] = target
        self._observations[observation.event_id] = observation
        after_prediction = target.predict(request, self.config)
        return ConsequenceModelUpdate(
            event_id=observation.event_id,
            record_id=record_id,
            evidence_applied=True,
            real_observation_count_before=count_before,
            real_observation_count_after=target.real_observation_count,
            confidence_before=before_prediction.calibrated_confidence,
            confidence_after=after_prediction.calibrated_confidence,
            evaluation=evaluation,
        )

    def _validate_prediction_request(
        self,
        request: ConsequencePredictionRequest,
    ) -> None:
        if len(request.relevant_effect_codes) > self.config.maximum_effect_dimensions_per_record:
            raise ValueError("prediction request effect-dimension bound exceeded")

    def record_for(
        self,
        context: ContextSignature,
        action_code: str,
    ) -> ContextActionConsequenceRecord:
        """Return one exact retained context-action record."""
        _validate_code("action_code", action_code)
        try:
            return self._records[_record_id(context, action_code)]
        except KeyError as error:
            raise ValueError("no consequence record exists for this context and action") from error

    def snapshot(self) -> dict[str, object]:
        """Return deterministic learned state without granting execution authority."""
        return {
            "config": self.config.snapshot(),
            "real_observation_count": self.real_observation_count,
            "record_count": self.record_count,
            "real_event_ids": sorted(self._observations),
            "records": [self._records[key].snapshot(self.config) for key in sorted(self._records)],
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


def _record_id(context: ContextSignature, action_code: str) -> str:
    return _identity(
        "context-action-consequence",
        {"context": context.snapshot(), "action_code": action_code},
    )


def _context_id(context: ContextSignature) -> str:
    return _identity("next-context", context.snapshot())


def _prediction_id(payload: Mapping[str, object]) -> str:
    return _identity("consequence-prediction", payload)


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"{prefix}:{hashlib.sha256(canonical).hexdigest()}"


def _effect_snapshot(effect: EffectObservation) -> dict[str, object]:
    return {
        "effect_code": effect.effect_code,
        "value": effect.value,
        "confidence": effect.confidence,
    }


def _validate_effects(
    name: str,
    effects: tuple[EffectObservation, ...],
    *,
    allow_empty: bool,
) -> None:
    if not effects and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    effect_codes = tuple(effect.effect_code for effect in effects)
    _validate_sorted_unique_codes(name, effect_codes)


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    for value in values:
        _validate_code(name, value)
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique values")
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


__all__ = [
    "CalibrationDirection",
    "ConsequenceModelObservation",
    "ConsequenceModelUpdate",
    "ConsequencePrediction",
    "ConsequencePredictionEvaluation",
    "ConsequencePredictionRequest",
    "ContextActionConsequenceRecord",
    "LearnedConsequenceModel",
    "LearnedConsequenceModelConfig",
]
