"""Bounded contextual transfer over exact learned consequence records."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from statistics import fmean

from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.learned_consequence_model import (
    ConsequencePrediction,
    ConsequencePredictionRequest,
    ContextActionConsequenceRecord,
    LearnedConsequenceModel,
)


class ConsequencePredictionMode(StrEnum):
    """Whether a prediction is exact, transferred, or unsupported."""

    EXACT = "exact"
    TRANSFERRED = "transferred"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ContextualTransferConfig:
    """Finite similarity, source, and confidence limits for transfer."""

    minimum_context_similarity: float = 0.75
    transfer_confidence_scale: float = 0.50
    maximum_transferred_confidence: float = 0.60
    minimum_source_confidence: float = 0.05
    maximum_transfer_sources: int = 4
    maximum_contexts_considered: int = 64
    context_bin_distance_scale: float = 10.0
    sensor_weight: float = 0.50
    action_weight: float = 0.20
    human_weight: float = 0.15
    resource_weight: float = 0.15
    neutral_effect_tolerance: float = 0.05

    def __post_init__(self) -> None:
        for name, value in (
            ("minimum_context_similarity", self.minimum_context_similarity),
            ("transfer_confidence_scale", self.transfer_confidence_scale),
            ("maximum_transferred_confidence", self.maximum_transferred_confidence),
            ("minimum_source_confidence", self.minimum_source_confidence),
            ("neutral_effect_tolerance", self.neutral_effect_tolerance),
        ):
            _validate_unit(name, value)
        for name, value in (
            ("maximum_transfer_sources", self.maximum_transfer_sources),
            ("maximum_contexts_considered", self.maximum_contexts_considered),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if not isfinite(self.context_bin_distance_scale) or self.context_bin_distance_scale <= 0.0:
            raise ValueError("context_bin_distance_scale must be finite and positive")
        weights = (
            self.sensor_weight,
            self.action_weight,
            self.human_weight,
            self.resource_weight,
        )
        if any(not isfinite(value) or value < 0.0 for value in weights):
            raise ValueError("context component weights must be finite and non-negative")
        if sum(weights) <= 0.0:
            raise ValueError("at least one context component weight must be positive")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable transfer limits."""
        return {
            "minimum_context_similarity": self.minimum_context_similarity,
            "transfer_confidence_scale": self.transfer_confidence_scale,
            "maximum_transferred_confidence": self.maximum_transferred_confidence,
            "minimum_source_confidence": self.minimum_source_confidence,
            "maximum_transfer_sources": self.maximum_transfer_sources,
            "maximum_contexts_considered": self.maximum_contexts_considered,
            "context_bin_distance_scale": self.context_bin_distance_scale,
            "sensor_weight": self.sensor_weight,
            "action_weight": self.action_weight,
            "human_weight": self.human_weight,
            "resource_weight": self.resource_weight,
            "neutral_effect_tolerance": self.neutral_effect_tolerance,
        }


@dataclass(frozen=True, slots=True)
class ContextSimilarityEvidence:
    """Explicit structured comparison between one target and source context."""

    source_record_id: str
    target_context: ContextSignature
    source_context: ContextSignature
    action_code: str
    active_need_match: bool
    action_available_in_target: bool
    action_available_in_source: bool
    shape_compatible: bool
    sensor_similarity: float | None
    action_similarity: float | None
    human_similarity: float | None
    resource_similarity: float | None
    combined_similarity: float
    eligible: bool

    def __post_init__(self) -> None:
        _validate_code("source_record_id", self.source_record_id)
        _validate_code("action_code", self.action_code)
        for name, value in (
            ("sensor_similarity", self.sensor_similarity),
            ("action_similarity", self.action_similarity),
            ("human_similarity", self.human_similarity),
            ("resource_similarity", self.resource_similarity),
        ):
            if value is not None:
                _validate_unit(name, value)
        _validate_unit("combined_similarity", self.combined_similarity)
        if self.eligible and not (
            self.active_need_match
            and self.action_available_in_target
            and self.action_available_in_source
            and self.shape_compatible
        ):
            raise ValueError("eligible context similarity lacks required structural matches")

    @property
    def source_context_id(self) -> str:
        return _context_id(self.source_context)

    @property
    def target_context_id(self) -> str:
        return _context_id(self.target_context)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable similarity evidence."""
        return {
            "source_record_id": self.source_record_id,
            "source_context_id": self.source_context_id,
            "target_context_id": self.target_context_id,
            "target_context": self.target_context.snapshot(),
            "source_context": self.source_context.snapshot(),
            "action_code": self.action_code,
            "active_need_match": self.active_need_match,
            "action_available_in_target": self.action_available_in_target,
            "action_available_in_source": self.action_available_in_source,
            "shape_compatible": self.shape_compatible,
            "sensor_similarity": self.sensor_similarity,
            "action_similarity": self.action_similarity,
            "human_similarity": self.human_similarity,
            "resource_similarity": self.resource_similarity,
            "combined_similarity": self.combined_similarity,
            "eligible": self.eligible,
        }


@dataclass(frozen=True, slots=True)
class ContextTransferSourceEvidence:
    """One exact source prediction admitted into a transferred estimate."""

    source_record_id: str
    source_context: ContextSignature
    similarity: ContextSimilarityEvidence
    source_prediction_id: str
    source_confidence: float
    attenuation: float
    effective_confidence: float
    source_effects: tuple[EffectObservation, ...]
    supporting_real_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_code("source_record_id", self.source_record_id)
        _validate_code("source_prediction_id", self.source_prediction_id)
        for name, value in (
            ("source_confidence", self.source_confidence),
            ("attenuation", self.attenuation),
            ("effective_confidence", self.effective_confidence),
        ):
            _validate_unit(name, value)
        _validate_effects("source_effects", self.source_effects, allow_empty=False)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        if self.source_record_id != self.similarity.source_record_id:
            raise ValueError("source record does not match similarity evidence")
        if self.source_context != self.similarity.source_context:
            raise ValueError("source context does not match similarity evidence")
        if not self.similarity.eligible:
            raise ValueError("transfer source similarity must be eligible")
        if self.effective_confidence > self.source_confidence:
            raise ValueError("effective confidence cannot exceed source confidence")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic exact-source transfer evidence."""
        return {
            "source_record_id": self.source_record_id,
            "source_context": self.source_context.snapshot(),
            "similarity": self.similarity.snapshot(),
            "source_prediction_id": self.source_prediction_id,
            "source_confidence": self.source_confidence,
            "attenuation": self.attenuation,
            "effective_confidence": self.effective_confidence,
            "source_effects": [_effect_snapshot(item) for item in self.source_effects],
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
        }


@dataclass(frozen=True, slots=True)
class TransferredEffectEvidence:
    """One transferred effect with explicit source agreement and contradiction."""

    effect_code: str
    value: float
    confidence: float
    source_count: int
    contradiction_score: float
    source_record_ids: tuple[str, ...]
    supporting_real_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_code("effect_code", self.effect_code)
        _validate_signed_unit("value", self.value)
        _validate_unit("confidence", self.confidence)
        _validate_unit("contradiction_score", self.contradiction_score)
        if isinstance(self.source_count, bool) or self.source_count <= 0:
            raise ValueError("source_count must be a positive integer")
        _validate_sorted_unique_codes("source_record_ids", self.source_record_ids)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        if self.source_count != len(self.source_record_ids):
            raise ValueError("source_count must match source_record_ids")

    @property
    def observation(self) -> EffectObservation:
        """Expose the transferred estimate in the common effect shape."""
        return EffectObservation(
            effect_code=self.effect_code,
            value=self.value,
            confidence=self.confidence,
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic per-effect transfer evidence."""
        return {
            "effect_code": self.effect_code,
            "value": self.value,
            "confidence": self.confidence,
            "source_count": self.source_count,
            "contradiction_score": self.contradiction_score,
            "source_record_ids": list(self.source_record_ids),
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
        }


@dataclass(frozen=True, slots=True)
class ContextualTransferPrediction:
    """Exact-first prediction with explicitly segregated transfer evidence."""

    prediction_id: str
    mode: ConsequencePredictionMode
    request: ConsequencePredictionRequest
    base_exact_prediction_id: str
    predicted_effects: tuple[EffectObservation, ...]
    predicted_next_context: ContextSignature | None
    effect_coverage: float
    source_coverage: float
    transfer_coverage: float
    confidence: float
    uncertainty: float
    contradiction_score: float
    supporting_real_event_ids: tuple[str, ...]
    considered_similarities: tuple[ContextSimilarityEvidence, ...] = ()
    transfer_sources: tuple[ContextTransferSourceEvidence, ...] = ()
    transferred_effects: tuple[TransferredEffectEvidence, ...] = ()
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("prediction_id", self.prediction_id)
        _validate_code("base_exact_prediction_id", self.base_exact_prediction_id)
        _validate_effects("predicted_effects", self.predicted_effects, allow_empty=True)
        for name, value in (
            ("effect_coverage", self.effect_coverage),
            ("source_coverage", self.source_coverage),
            ("transfer_coverage", self.transfer_coverage),
            ("confidence", self.confidence),
            ("uncertainty", self.uncertainty),
            ("contradiction_score", self.contradiction_score),
        ):
            _validate_unit(name, value)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        predicted_codes = tuple(item.effect_code for item in self.predicted_effects)
        if set(predicted_codes) - set(self.request.relevant_effect_codes):
            raise ValueError("prediction contains an unrequested effect dimension")
        if self.uncertainty != 1.0 - self.confidence:
            raise ValueError("uncertainty must equal one minus confidence")
        if self.has_action_selection_authority:
            raise ValueError("contextual transfer predictions cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("contextual transfer predictions cannot control production actions")
        if self.mode is ConsequencePredictionMode.EXACT:
            if self.transfer_sources or self.transferred_effects or self.considered_similarities:
                raise ValueError("exact predictions cannot contain transfer evidence")
            if self.transfer_coverage != 0.0 or self.contradiction_score != 0.0:
                raise ValueError("exact predictions cannot report transfer metrics")
        elif self.mode is ConsequencePredictionMode.TRANSFERRED:
            if not self.transfer_sources or not self.transferred_effects:
                raise ValueError("transferred predictions require source and effect evidence")
            if self.predicted_next_context is not None:
                raise ValueError("transferred predictions cannot claim an exact next context")
            expected_effects = tuple(item.observation for item in self.transferred_effects)
            if self.predicted_effects != expected_effects:
                raise ValueError("transferred effects do not match predicted effects")
        else:
            if self.predicted_effects or self.predicted_next_context is not None:
                raise ValueError("unknown predictions cannot contain predicted outcomes")
            if self.transfer_sources or self.transferred_effects:
                raise ValueError("unknown predictions cannot contain admitted transfer sources")
            if any(
                value != 0.0
                for value in (
                    self.effect_coverage,
                    self.source_coverage,
                    self.transfer_coverage,
                    self.confidence,
                    self.contradiction_score,
                )
            ):
                raise ValueError("unknown prediction metrics must be zero")
        if self.prediction_id != _prediction_id(self._identity_payload()):
            raise ValueError("contextual transfer prediction identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable exact-or-transfer evidence."""
        return {"prediction_id": self.prediction_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "mode": self.mode.value,
            "request": self.request.snapshot(),
            "base_exact_prediction_id": self.base_exact_prediction_id,
            "predicted_effects": [_effect_snapshot(item) for item in self.predicted_effects],
            "predicted_next_context": (
                None
                if self.predicted_next_context is None
                else self.predicted_next_context.snapshot()
            ),
            "effect_coverage": self.effect_coverage,
            "source_coverage": self.source_coverage,
            "transfer_coverage": self.transfer_coverage,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "contradiction_score": self.contradiction_score,
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
            "considered_similarities": [item.snapshot() for item in self.considered_similarities],
            "transfer_sources": [item.snapshot() for item in self.transfer_sources],
            "transferred_effects": [item.snapshot() for item in self.transferred_effects],
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(slots=True)
class BoundedContextualTransferPolicy:
    """Stateless exact-first transfer policy with conservative attenuation."""

    config: ContextualTransferConfig = field(default_factory=ContextualTransferConfig)
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_action_selection_authority:
            raise ValueError("contextual transfer policy cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("contextual transfer policy cannot control production actions")

    def predict(
        self,
        model: LearnedConsequenceModel,
        request: ConsequencePredictionRequest,
    ) -> ContextualTransferPrediction:
        """Return exact evidence first, otherwise bounded transferred evidence."""
        exact = model.predict(request)
        if exact.evidence_count > 0:
            return self._exact_prediction(exact)

        records = tuple(
            record for record in model.records if record.action_code == request.action_code
        )
        if len(records) > self.config.maximum_contexts_considered:
            raise ValueError("context transfer candidate bound exceeded")
        similarities = tuple(
            self.compare_contexts(
                target_context=request.context,
                source_record=record,
                action_code=request.action_code,
            )
            for record in records
        )
        admitted: list[ContextTransferSourceEvidence] = []
        for record, similarity in zip(records, similarities, strict=True):
            if not similarity.eligible:
                continue
            source_request = ConsequencePredictionRequest(
                context=record.context,
                action_code=request.action_code,
                relevant_effect_codes=request.relevant_effect_codes,
            )
            source_prediction = model.predict(source_request)
            source = self._source_evidence(record, similarity, source_prediction)
            if source is not None:
                admitted.append(source)
        admitted.sort(
            key=lambda item: (
                -item.similarity.combined_similarity,
                -item.effective_confidence,
                item.source_record_id,
            )
        )
        selected = tuple(admitted[: self.config.maximum_transfer_sources])
        if not selected:
            return self._unknown_prediction(exact, similarities)
        transferred_effects = self._aggregate_effects(request, selected)
        if not transferred_effects:
            return self._unknown_prediction(exact, similarities)
        return self._transferred_prediction(
            exact=exact,
            similarities=similarities,
            sources=selected,
            effects=transferred_effects,
            considered_record_count=len(records),
        )

    def compare_contexts(
        self,
        *,
        target_context: ContextSignature,
        source_record: ContextActionConsequenceRecord,
        action_code: str,
    ) -> ContextSimilarityEvidence:
        """Compare grounded context components without semantic extrapolation."""
        _validate_code("action_code", action_code)
        source_context = source_record.context
        active_need_match = target_context.active_need_code == source_context.active_need_code
        action_available_in_target = action_code in target_context.available_action_codes
        action_available_in_source = action_code in source_context.available_action_codes
        shape_compatible = (
            len(target_context.sensor_bins) == len(source_context.sensor_bins)
            and len(target_context.human_bins) == len(source_context.human_bins)
            and len(target_context.resource_bins) == len(source_context.resource_bins)
        )
        sensor_similarity = _vector_similarity(
            target_context.sensor_bins,
            source_context.sensor_bins,
            self.config.context_bin_distance_scale,
        )
        action_similarity = _set_similarity(
            target_context.available_action_codes,
            source_context.available_action_codes,
        )
        human_similarity = _vector_similarity(
            target_context.human_bins,
            source_context.human_bins,
            self.config.context_bin_distance_scale,
        )
        resource_similarity = _vector_similarity(
            target_context.resource_bins,
            source_context.resource_bins,
            self.config.context_bin_distance_scale,
        )
        structurally_valid = (
            active_need_match
            and action_available_in_target
            and action_available_in_source
            and shape_compatible
        )
        combined = (
            _weighted_similarity(
                (
                    (sensor_similarity, self.config.sensor_weight),
                    (action_similarity, self.config.action_weight),
                    (human_similarity, self.config.human_weight),
                    (resource_similarity, self.config.resource_weight),
                )
            )
            if structurally_valid
            else 0.0
        )
        return ContextSimilarityEvidence(
            source_record_id=source_record.record_id,
            target_context=target_context,
            source_context=source_context,
            action_code=action_code,
            active_need_match=active_need_match,
            action_available_in_target=action_available_in_target,
            action_available_in_source=action_available_in_source,
            shape_compatible=shape_compatible,
            sensor_similarity=sensor_similarity,
            action_similarity=action_similarity,
            human_similarity=human_similarity,
            resource_similarity=resource_similarity,
            combined_similarity=combined,
            eligible=structurally_valid and combined >= self.config.minimum_context_similarity,
        )

    def _source_evidence(
        self,
        record: ContextActionConsequenceRecord,
        similarity: ContextSimilarityEvidence,
        prediction: ConsequencePrediction,
    ) -> ContextTransferSourceEvidence | None:
        attenuation = similarity.combined_similarity * self.config.transfer_confidence_scale
        source_effects: list[EffectObservation] = []
        effective_values: list[float] = []
        for effect in prediction.predicted_effects:
            effective = min(effect.confidence, prediction.calibrated_confidence) * attenuation
            if effective <= 0.0:
                continue
            source_effects.append(effect)
            effective_values.append(effective)
        if not source_effects:
            return None
        effective_confidence = max(effective_values)
        if effective_confidence < self.config.minimum_source_confidence:
            return None
        return ContextTransferSourceEvidence(
            source_record_id=record.record_id,
            source_context=record.context,
            similarity=similarity,
            source_prediction_id=prediction.prediction_id,
            source_confidence=prediction.calibrated_confidence,
            attenuation=attenuation,
            effective_confidence=effective_confidence,
            source_effects=tuple(source_effects),
            supporting_real_event_ids=prediction.supporting_real_event_ids,
        )

    def _aggregate_effects(
        self,
        request: ConsequencePredictionRequest,
        sources: tuple[ContextTransferSourceEvidence, ...],
    ) -> tuple[TransferredEffectEvidence, ...]:
        effects: list[TransferredEffectEvidence] = []
        for effect_code in request.relevant_effect_codes:
            entries: list[tuple[ContextTransferSourceEvidence, EffectObservation, float]] = []
            for source in sources:
                source_effect = next(
                    (item for item in source.source_effects if item.effect_code == effect_code),
                    None,
                )
                if source_effect is None:
                    continue
                weight = (
                    min(source_effect.confidence, source.source_confidence) * source.attenuation
                )
                if weight > 0.0:
                    entries.append((source, source_effect, weight))
            if not entries:
                continue
            total_weight = sum(weight for _, _, weight in entries)
            value = (
                sum(source_effect.value * weight for _, source_effect, weight in entries)
                / total_weight
            )
            positive_weight = sum(
                weight
                for _, source_effect, weight in entries
                if source_effect.value > self.config.neutral_effect_tolerance
            )
            negative_weight = sum(
                weight
                for _, source_effect, weight in entries
                if source_effect.value < -self.config.neutral_effect_tolerance
            )
            directional_weight = positive_weight + negative_weight
            contradiction = (
                0.0
                if directional_weight == 0.0
                else 2.0 * min(positive_weight, negative_weight) / directional_weight
            )
            confidence = min(
                self.config.maximum_transferred_confidence,
                total_weight,
            ) * (1.0 - contradiction)
            source_record_ids = tuple(sorted({source.source_record_id for source, _, _ in entries}))
            supporting_event_ids = tuple(
                sorted(
                    {
                        event_id
                        for source, _, _ in entries
                        for event_id in source.supporting_real_event_ids
                    }
                )
            )
            effects.append(
                TransferredEffectEvidence(
                    effect_code=effect_code,
                    value=max(-1.0, min(1.0, value)),
                    confidence=confidence,
                    source_count=len(source_record_ids),
                    contradiction_score=contradiction,
                    source_record_ids=source_record_ids,
                    supporting_real_event_ids=supporting_event_ids,
                )
            )
        return tuple(effects)

    def _exact_prediction(
        self,
        exact: ConsequencePrediction,
    ) -> ContextualTransferPrediction:
        payload = self._prediction_payload(
            mode=ConsequencePredictionMode.EXACT,
            request=exact.request,
            base_exact_prediction_id=exact.prediction_id,
            predicted_effects=exact.predicted_effects,
            predicted_next_context=exact.predicted_next_context,
            effect_coverage=exact.effect_coverage,
            source_coverage=1.0,
            transfer_coverage=0.0,
            confidence=exact.calibrated_confidence,
            contradiction_score=0.0,
            supporting_real_event_ids=exact.supporting_real_event_ids,
            considered_similarities=(),
            transfer_sources=(),
            transferred_effects=(),
        )
        return ContextualTransferPrediction(
            prediction_id=_prediction_id(payload),
            mode=ConsequencePredictionMode.EXACT,
            request=exact.request,
            base_exact_prediction_id=exact.prediction_id,
            predicted_effects=exact.predicted_effects,
            predicted_next_context=exact.predicted_next_context,
            effect_coverage=exact.effect_coverage,
            source_coverage=1.0,
            transfer_coverage=0.0,
            confidence=exact.calibrated_confidence,
            uncertainty=1.0 - exact.calibrated_confidence,
            contradiction_score=0.0,
            supporting_real_event_ids=exact.supporting_real_event_ids,
        )

    def _unknown_prediction(
        self,
        exact: ConsequencePrediction,
        similarities: tuple[ContextSimilarityEvidence, ...],
    ) -> ContextualTransferPrediction:
        payload = self._prediction_payload(
            mode=ConsequencePredictionMode.UNKNOWN,
            request=exact.request,
            base_exact_prediction_id=exact.prediction_id,
            predicted_effects=(),
            predicted_next_context=None,
            effect_coverage=0.0,
            source_coverage=0.0,
            transfer_coverage=0.0,
            confidence=0.0,
            contradiction_score=0.0,
            supporting_real_event_ids=(),
            considered_similarities=similarities,
            transfer_sources=(),
            transferred_effects=(),
        )
        return ContextualTransferPrediction(
            prediction_id=_prediction_id(payload),
            mode=ConsequencePredictionMode.UNKNOWN,
            request=exact.request,
            base_exact_prediction_id=exact.prediction_id,
            predicted_effects=(),
            predicted_next_context=None,
            effect_coverage=0.0,
            source_coverage=0.0,
            transfer_coverage=0.0,
            confidence=0.0,
            uncertainty=1.0,
            contradiction_score=0.0,
            supporting_real_event_ids=(),
            considered_similarities=similarities,
        )

    def _transferred_prediction(
        self,
        *,
        exact: ConsequencePrediction,
        similarities: tuple[ContextSimilarityEvidence, ...],
        sources: tuple[ContextTransferSourceEvidence, ...],
        effects: tuple[TransferredEffectEvidence, ...],
        considered_record_count: int,
    ) -> ContextualTransferPrediction:
        predicted_effects = tuple(item.observation for item in effects)
        effect_coverage = len(effects) / len(exact.request.relevant_effect_codes)
        source_coverage = len(sources) / max(1, considered_record_count)
        mean_similarity = fmean(source.similarity.combined_similarity for source in sources)
        transfer_coverage = effect_coverage * mean_similarity
        confidence = min(
            self.config.maximum_transferred_confidence,
            transfer_coverage,
            sum(effect.confidence for effect in effects) / len(exact.request.relevant_effect_codes),
        )
        contradiction_score = fmean(effect.contradiction_score for effect in effects)
        supporting_event_ids = tuple(
            sorted(
                {event_id for source in sources for event_id in source.supporting_real_event_ids}
            )
        )
        payload = self._prediction_payload(
            mode=ConsequencePredictionMode.TRANSFERRED,
            request=exact.request,
            base_exact_prediction_id=exact.prediction_id,
            predicted_effects=predicted_effects,
            predicted_next_context=None,
            effect_coverage=effect_coverage,
            source_coverage=source_coverage,
            transfer_coverage=transfer_coverage,
            confidence=confidence,
            contradiction_score=contradiction_score,
            supporting_real_event_ids=supporting_event_ids,
            considered_similarities=similarities,
            transfer_sources=sources,
            transferred_effects=effects,
        )
        return ContextualTransferPrediction(
            prediction_id=_prediction_id(payload),
            mode=ConsequencePredictionMode.TRANSFERRED,
            request=exact.request,
            base_exact_prediction_id=exact.prediction_id,
            predicted_effects=predicted_effects,
            predicted_next_context=None,
            effect_coverage=effect_coverage,
            source_coverage=source_coverage,
            transfer_coverage=transfer_coverage,
            confidence=confidence,
            uncertainty=1.0 - confidence,
            contradiction_score=contradiction_score,
            supporting_real_event_ids=supporting_event_ids,
            considered_similarities=similarities,
            transfer_sources=sources,
            transferred_effects=effects,
        )

    @staticmethod
    def _prediction_payload(
        *,
        mode: ConsequencePredictionMode,
        request: ConsequencePredictionRequest,
        base_exact_prediction_id: str,
        predicted_effects: tuple[EffectObservation, ...],
        predicted_next_context: ContextSignature | None,
        effect_coverage: float,
        source_coverage: float,
        transfer_coverage: float,
        confidence: float,
        contradiction_score: float,
        supporting_real_event_ids: tuple[str, ...],
        considered_similarities: tuple[ContextSimilarityEvidence, ...],
        transfer_sources: tuple[ContextTransferSourceEvidence, ...],
        transferred_effects: tuple[TransferredEffectEvidence, ...],
    ) -> dict[str, object]:
        return {
            "mode": mode.value,
            "request": request.snapshot(),
            "base_exact_prediction_id": base_exact_prediction_id,
            "predicted_effects": [_effect_snapshot(item) for item in predicted_effects],
            "predicted_next_context": (
                None if predicted_next_context is None else predicted_next_context.snapshot()
            ),
            "effect_coverage": effect_coverage,
            "source_coverage": source_coverage,
            "transfer_coverage": transfer_coverage,
            "confidence": confidence,
            "uncertainty": 1.0 - confidence,
            "contradiction_score": contradiction_score,
            "supporting_real_event_ids": list(supporting_real_event_ids),
            "considered_similarities": [item.snapshot() for item in considered_similarities],
            "transfer_sources": [item.snapshot() for item in transfer_sources],
            "transferred_effects": [item.snapshot() for item in transferred_effects],
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }


def _vector_similarity(
    left: Sequence[int],
    right: Sequence[int],
    distance_scale: float,
) -> float | None:
    if not left and not right:
        return None
    if len(left) != len(right):
        return 0.0
    return fmean(
        1.0 - min(1.0, abs(first - second) / distance_scale)
        for first, second in zip(left, right, strict=True)
    )


def _set_similarity(left: Sequence[str], right: Sequence[str]) -> float | None:
    left_set = frozenset(left)
    right_set = frozenset(right)
    union = left_set | right_set
    return len(left_set & right_set) / len(union) if union else None


def _weighted_similarity(
    components: tuple[tuple[float | None, float], ...],
) -> float:
    available = tuple(
        (value, weight) for value, weight in components if value is not None and weight > 0.0
    )
    if not available:
        return 0.0
    total_weight = sum(weight for _, weight in available)
    return sum(value * weight for value, weight in available) / total_weight


def _context_id(context: ContextSignature) -> str:
    return _identity("context", context.snapshot())


def _prediction_id(payload: Mapping[str, object]) -> str:
    return _identity("contextual-transfer-prediction", payload)


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
    _validate_sorted_unique_codes(
        name,
        tuple(effect.effect_code for effect in effects),
    )


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


def _validate_signed_unit(name: str, value: float) -> None:
    if not isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between negative one and one")


__all__ = [
    "BoundedContextualTransferPolicy",
    "ConsequencePredictionMode",
    "ContextSimilarityEvidence",
    "ContextTransferSourceEvidence",
    "ContextualTransferConfig",
    "ContextualTransferPrediction",
    "TransferredEffectEvidence",
]
