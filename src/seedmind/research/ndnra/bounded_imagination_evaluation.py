"""Pure non-authoritative need alignment for bounded imagined routes."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.bounded_imagination import ImaginedActionSequence
from seedmind.research.ndnra.bounded_imagination_candidates import (
    ImaginedCandidateGenerationStep,
    ImaginedGeneratedCandidate,
)
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectNeed, EffectObservation, NeedDimension


class ImaginedAlignmentDirection(StrEnum):
    """Per-effect need alignment without candidate ranking or selection."""

    IMPROVING = "improving"
    NEUTRAL = "neutral"
    WORSENING = "worsening"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class BoundedRouteEvaluationConfig:
    """Finite limits for pure imagined-route annotation."""

    maximum_candidates: int = 8
    maximum_steps_per_candidate: int = 3
    maximum_need_dimensions: int = 16
    maximum_total_alignments: int = 384
    neutral_tolerance: float = 0.05

    def __post_init__(self) -> None:
        for name, value in (
            ("maximum_candidates", self.maximum_candidates),
            ("maximum_steps_per_candidate", self.maximum_steps_per_candidate),
            ("maximum_need_dimensions", self.maximum_need_dimensions),
            ("maximum_total_alignments", self.maximum_total_alignments),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        _validate_unit("neutral_tolerance", self.neutral_tolerance)

    def snapshot(self) -> dict[str, object]:
        return {
            "maximum_candidates": self.maximum_candidates,
            "maximum_steps_per_candidate": self.maximum_steps_per_candidate,
            "maximum_need_dimensions": self.maximum_need_dimensions,
            "maximum_total_alignments": self.maximum_total_alignments,
            "neutral_tolerance": self.neutral_tolerance,
        }


@dataclass(frozen=True, slots=True)
class ImaginedRouteEvaluationRequest:
    """Explicit need semantics and caller-ordered imagined candidates."""

    need: EffectNeed
    candidates: tuple[ImaginedGeneratedCandidate, ...]
    config: BoundedRouteEvaluationConfig = field(default_factory=BoundedRouteEvaluationConfig)
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if len(self.candidates) > self.config.maximum_candidates:
            raise ValueError("candidate bound exceeded")
        candidate_ids = tuple(candidate.candidate_id for candidate in self.candidates)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("route evaluation candidates must be unique")
        if len(self.need.dimensions) > self.config.maximum_need_dimensions:
            raise ValueError("need-dimension bound exceeded")
        total_alignments = 0
        for candidate in self.candidates:
            if candidate.origin is not ExperienceOrigin.IMAGINED:
                raise ValueError("route evaluation accepts imagined candidates only")
            if len(candidate.steps) > self.config.maximum_steps_per_candidate:
                raise ValueError("candidate step bound exceeded")
            if any(
                step.context.active_need_code != self.need.need_code for step in candidate.steps
            ):
                raise ValueError("candidate active need does not match evaluation need")
            total_alignments += len(candidate.steps) * len(self.need.dimensions)
        if total_alignments > self.config.maximum_total_alignments:
            raise ValueError("total alignment bound exceeded")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("route evaluation requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("route evaluation requests cannot control production actions")

    @property
    def request_id(self) -> str:
        return _identity("imagined-route-evaluation-request", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"request_id": self.request_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "need": _need_snapshot(self.need),
            "candidates": [candidate.snapshot() for candidate in self.candidates],
            "config": self.config.snapshot(),
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ImaginedEffectAlignment:
    """One need dimension evaluated for one exact imagined step."""

    alignment_id: str
    origin: ExperienceOrigin
    step_index: int
    effect_code: str
    predicted_value: float | None
    prediction_confidence: float
    desired_direction: float
    intensity: float
    signed_alignment: float | None
    direction: ImaginedAlignmentDirection
    neutral_tolerance: float
    source_step_id: str
    source_prediction_id: str
    supporting_real_event_ids: tuple[str, ...]
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("alignment_id", self.alignment_id)
        _validate_ascii_code("effect_code", self.effect_code)
        _validate_ascii_code("source_step_id", self.source_step_id)
        _validate_ascii_code("source_prediction_id", self.source_prediction_id)
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("imagined effect alignments require imagined origin")
        if (
            isinstance(self.step_index, bool)
            or not isinstance(self.step_index, int)
            or self.step_index < 0
        ):
            raise ValueError("step_index must be a non-negative integer")
        _validate_signed_nonzero("desired_direction", self.desired_direction)
        _validate_positive_unit("intensity", self.intensity)
        _validate_unit("neutral_tolerance", self.neutral_tolerance)
        _validate_sorted_unique_codes("supporting_real_event_ids", self.supporting_real_event_ids)
        if self.predicted_value is None:
            if self.prediction_confidence != 0.0 or self.signed_alignment is not None:
                raise ValueError("unknown alignment cannot carry predicted evidence")
            if self.direction is not ImaginedAlignmentDirection.UNKNOWN:
                raise ValueError("missing predicted effect must remain unknown")
        else:
            _validate_signed("predicted_value", self.predicted_value)
            _validate_unit("prediction_confidence", self.prediction_confidence)
            if self.signed_alignment is None:
                raise ValueError("known predicted effect requires signed alignment")
            _validate_signed("signed_alignment", self.signed_alignment)
            expected = self.predicted_value * self.desired_direction * self.prediction_confidence
            if abs(self.signed_alignment - expected) > 1e-12:
                raise ValueError("signed alignment is inconsistent")
            if self.signed_alignment > self.neutral_tolerance:
                expected_direction = ImaginedAlignmentDirection.IMPROVING
            elif self.signed_alignment < -self.neutral_tolerance:
                expected_direction = ImaginedAlignmentDirection.WORSENING
            else:
                expected_direction = ImaginedAlignmentDirection.NEUTRAL
            if self.direction is not expected_direction:
                raise ValueError("alignment direction is inconsistent")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined effect alignments cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("imagined effect alignments cannot control production actions")
        if self.alignment_id != _identity("imagined-effect-alignment", self._identity_payload()):
            raise ValueError("imagined effect alignment identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"alignment_id": self.alignment_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "step_index": self.step_index,
            "effect_code": self.effect_code,
            "predicted_value": self.predicted_value,
            "prediction_confidence": self.prediction_confidence,
            "desired_direction": self.desired_direction,
            "intensity": self.intensity,
            "signed_alignment": self.signed_alignment,
            "direction": self.direction.value,
            "neutral_tolerance": self.neutral_tolerance,
            "source_step_id": self.source_step_id,
            "source_prediction_id": self.source_prediction_id,
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ImaginedRouteStepEvaluation:
    """Per-step vector of need alignments without cross-step aggregation."""

    step_evaluation_id: str
    origin: ExperienceOrigin
    candidate_id: str
    step_index: int
    context: ContextSignature
    action_code: str
    predicted_next_context: ContextSignature
    source_step_id: str
    source_record_id: str
    source_prediction_id: str
    supporting_real_event_ids: tuple[str, ...]
    alignments: tuple[ImaginedEffectAlignment, ...]
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("step_evaluation_id", self.step_evaluation_id)
        _validate_ascii_code("candidate_id", self.candidate_id)
        _validate_ascii_code("action_code", self.action_code)
        _validate_ascii_code("source_step_id", self.source_step_id)
        _validate_ascii_code("source_record_id", self.source_record_id)
        _validate_ascii_code("source_prediction_id", self.source_prediction_id)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("route step evaluations require imagined origin")
        if (
            isinstance(self.step_index, bool)
            or not isinstance(self.step_index, int)
            or self.step_index < 0
        ):
            raise ValueError("step_index must be a non-negative integer")
        effect_codes = tuple(item.effect_code for item in self.alignments)
        _validate_sorted_unique_codes("alignment effect codes", effect_codes)
        if any(item.step_index != self.step_index for item in self.alignments):
            raise ValueError("alignment step index mismatch")
        if any(item.source_step_id != self.source_step_id for item in self.alignments):
            raise ValueError("alignment source step mismatch")
        if any(item.source_prediction_id != self.source_prediction_id for item in self.alignments):
            raise ValueError("alignment source prediction mismatch")
        if any(
            item.predicted_value is not None
            and item.supporting_real_event_ids != self.supporting_real_event_ids
            for item in self.alignments
        ):
            raise ValueError("known alignment provenance mismatch")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("route step evaluations cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("route step evaluations cannot control production actions")
        if self.step_evaluation_id != _identity(
            "imagined-route-step-evaluation", self._identity_payload()
        ):
            raise ValueError("route step evaluation identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {
            "step_evaluation_id": self.step_evaluation_id,
            **self._identity_payload(),
        }

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "candidate_id": self.candidate_id,
            "step_index": self.step_index,
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "predicted_next_context": self.predicted_next_context.snapshot(),
            "source_step_id": self.source_step_id,
            "source_record_id": self.source_record_id,
            "source_prediction_id": self.source_prediction_id,
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
            "alignments": [item.snapshot() for item in self.alignments],
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ImaginedRouteEvaluation:
    """One caller-ordered candidate annotated without an overall score."""

    evaluation_id: str
    origin: ExperienceOrigin
    candidate_id: str
    sequence: ImaginedActionSequence
    step_evaluations: tuple[ImaginedRouteStepEvaluation, ...]
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("evaluation_id", self.evaluation_id)
        _validate_ascii_code("candidate_id", self.candidate_id)
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("imagined route evaluations require imagined origin")
        if not self.step_evaluations:
            raise ValueError("route evaluation requires at least one step")
        if len(self.step_evaluations) != len(self.sequence.action_codes):
            raise ValueError("route evaluation must preserve sequence depth")
        for index, item in enumerate(self.step_evaluations):
            if item.step_index != index:
                raise ValueError("route evaluation step indexes must be contiguous")
            if item.action_code != self.sequence.action_codes[index]:
                raise ValueError("route evaluation actions must preserve candidate order")
            if item.candidate_id != self.candidate_id:
                raise ValueError("route step candidate identity mismatch")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined route evaluations cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("imagined route evaluations cannot control production actions")
        if self.evaluation_id != _identity("imagined-route-evaluation", self._identity_payload()):
            raise ValueError("imagined route evaluation identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"evaluation_id": self.evaluation_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "candidate_id": self.candidate_id,
            "sequence": self.sequence.snapshot(),
            "step_evaluations": [item.snapshot() for item in self.step_evaluations],
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ImaginedRouteEvaluationResult:
    """Deterministic caller-ordered route annotations with no winner."""

    result_id: str
    request: ImaginedRouteEvaluationRequest
    evaluations: tuple[ImaginedRouteEvaluation, ...]
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("result_id", self.result_id)
        if len(self.evaluations) != len(self.request.candidates):
            raise ValueError("route evaluation count must preserve caller candidates")
        for index, evaluation in enumerate(self.evaluations):
            if evaluation.candidate_id != self.request.candidates[index].candidate_id:
                raise ValueError("route evaluations must preserve caller order")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("route evaluation results cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("route evaluation results cannot control production actions")
        if self.result_id != _identity(
            "imagined-route-evaluation-result", self._identity_payload()
        ):
            raise ValueError("imagined route evaluation result identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "evaluations": [item.snapshot() for item in self.evaluations],
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class BoundedImaginedRouteEvaluator:
    """Annotate exact imagined candidates without ranking or selection."""

    def evaluate(
        self,
        request: ImaginedRouteEvaluationRequest,
    ) -> ImaginedRouteEvaluationResult:
        dimensions = tuple(sorted(request.need.dimensions, key=lambda item: item.effect_code))
        evaluations = tuple(
            self._evaluate_candidate(candidate, dimensions, request.config)
            for candidate in request.candidates
        )
        payload = {
            "request": request.snapshot(),
            "evaluations": [item.snapshot() for item in evaluations],
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedRouteEvaluationResult(
            result_id=_identity("imagined-route-evaluation-result", payload),
            request=request,
            evaluations=evaluations,
        )

    def _evaluate_candidate(
        self,
        candidate: ImaginedGeneratedCandidate,
        dimensions: tuple[NeedDimension, ...],
        config: BoundedRouteEvaluationConfig,
    ) -> ImaginedRouteEvaluation:
        step_evaluations = tuple(
            self._evaluate_step(candidate.candidate_id, step, dimensions, config)
            for step in candidate.steps
        )
        payload = {
            "origin": ExperienceOrigin.IMAGINED.value,
            "candidate_id": candidate.candidate_id,
            "sequence": candidate.sequence.snapshot(),
            "step_evaluations": [item.snapshot() for item in step_evaluations],
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedRouteEvaluation(
            evaluation_id=_identity("imagined-route-evaluation", payload),
            origin=ExperienceOrigin.IMAGINED,
            candidate_id=candidate.candidate_id,
            sequence=candidate.sequence,
            step_evaluations=step_evaluations,
        )

    def _evaluate_step(
        self,
        candidate_id: str,
        step: ImaginedCandidateGenerationStep,
        dimensions: tuple[NeedDimension, ...],
        config: BoundedRouteEvaluationConfig,
    ) -> ImaginedRouteStepEvaluation:
        effects = {effect.effect_code: effect for effect in step.predicted_effects}
        alignments = tuple(
            _alignment_for(
                step=step,
                dimension=dimension,
                effect=effects.get(dimension.effect_code),
                neutral_tolerance=config.neutral_tolerance,
            )
            for dimension in dimensions
        )
        payload = {
            "origin": ExperienceOrigin.IMAGINED.value,
            "candidate_id": candidate_id,
            "step_index": step.step_index,
            "context": step.context.snapshot(),
            "action_code": step.action_code,
            "predicted_next_context": step.predicted_next_context.snapshot(),
            "source_step_id": step.step_id,
            "source_record_id": step.source_record_id,
            "source_prediction_id": step.source_prediction_id,
            "supporting_real_event_ids": list(step.supporting_real_event_ids),
            "alignments": [item.snapshot() for item in alignments],
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedRouteStepEvaluation(
            step_evaluation_id=_identity("imagined-route-step-evaluation", payload),
            origin=ExperienceOrigin.IMAGINED,
            candidate_id=candidate_id,
            step_index=step.step_index,
            context=step.context,
            action_code=step.action_code,
            predicted_next_context=step.predicted_next_context,
            source_step_id=step.step_id,
            source_record_id=step.source_record_id,
            source_prediction_id=step.source_prediction_id,
            supporting_real_event_ids=step.supporting_real_event_ids,
            alignments=alignments,
        )


def _alignment_for(
    *,
    step: ImaginedCandidateGenerationStep,
    dimension: NeedDimension,
    effect: EffectObservation | None,
    neutral_tolerance: float,
) -> ImaginedEffectAlignment:
    if effect is None:
        value = None
        confidence = 0.0
        signed_alignment = None
        direction = ImaginedAlignmentDirection.UNKNOWN
        supporting_real_event_ids: tuple[str, ...] = ()
    else:
        value = effect.value
        confidence = effect.confidence
        signed_alignment = value * dimension.desired_direction * confidence
        if signed_alignment > neutral_tolerance:
            direction = ImaginedAlignmentDirection.IMPROVING
        elif signed_alignment < -neutral_tolerance:
            direction = ImaginedAlignmentDirection.WORSENING
        else:
            direction = ImaginedAlignmentDirection.NEUTRAL
        supporting_real_event_ids = step.supporting_real_event_ids
    payload = {
        "origin": ExperienceOrigin.IMAGINED.value,
        "step_index": step.step_index,
        "effect_code": dimension.effect_code,
        "predicted_value": value,
        "prediction_confidence": confidence,
        "desired_direction": dimension.desired_direction,
        "intensity": dimension.intensity,
        "signed_alignment": signed_alignment,
        "direction": direction.value,
        "neutral_tolerance": neutral_tolerance,
        "source_step_id": step.step_id,
        "source_prediction_id": step.source_prediction_id,
        "supporting_real_event_ids": list(supporting_real_event_ids),
        "factual_confidence_change": 0.0,
        "mastery_change": 0.0,
        "competence_change": 0.0,
        "growth_pressure_change": 0.0,
        "replay_evidence_change": 0.0,
        "real_observation_change": 0.0,
        "has_action_selection_authority": False,
        "has_production_action_authority": False,
    }
    return ImaginedEffectAlignment(
        alignment_id=_identity("imagined-effect-alignment", payload),
        origin=ExperienceOrigin.IMAGINED,
        step_index=step.step_index,
        effect_code=dimension.effect_code,
        predicted_value=value,
        prediction_confidence=confidence,
        desired_direction=dimension.desired_direction,
        intensity=dimension.intensity,
        signed_alignment=signed_alignment,
        direction=direction,
        neutral_tolerance=neutral_tolerance,
        source_step_id=step.step_id,
        source_prediction_id=step.source_prediction_id,
        supporting_real_event_ids=supporting_real_event_ids,
    )


def _need_snapshot(need: EffectNeed) -> dict[str, object]:
    dimensions = tuple(sorted(need.dimensions, key=lambda item: item.effect_code))
    return {
        "need_code": need.need_code,
        "primary_effect_code": need.primary_effect_code,
        "dimensions": [
            {
                "effect_code": item.effect_code,
                "desired_direction": item.desired_direction,
                "intensity": item.intensity,
            }
            for item in dimensions
        ],
        "satisfaction_threshold": need.satisfaction_threshold,
    }


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    return f"{prefix}:{hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()}"


def _validate_ascii_code(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError(f"{name} must be a non-empty ASCII string")


def _validate_sorted_unique_codes(name: str, values: Sequence[str]) -> None:
    if any(not isinstance(value, str) or not value or not value.isascii() for value in values):
        raise ValueError(f"{name} must contain non-empty ASCII strings")
    if tuple(values) != tuple(sorted(values)):
        raise ValueError(f"{name} must be sorted")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique")


def _validate_signed_nonzero(name: str, value: float) -> None:
    _validate_signed(name, value)
    if value == 0.0:
        raise ValueError(f"{name} must not be zero")


def _validate_positive_unit(name: str, value: float) -> None:
    _validate_unit(name, value)
    if value == 0.0:
        raise ValueError(f"{name} must be above zero")


def _validate_signed(name: str, value: float) -> None:
    if not isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between negative one and one")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _validate_zero_delta(name: str, value: float) -> None:
    if not isinstance(value, float) or not isfinite(value) or value != 0.0:
        raise ValueError(f"{name} must remain exactly zero")


__all__ = [
    "BoundedImaginedRouteEvaluator",
    "BoundedRouteEvaluationConfig",
    "ImaginedAlignmentDirection",
    "ImaginedEffectAlignment",
    "ImaginedRouteEvaluation",
    "ImaginedRouteEvaluationRequest",
    "ImaginedRouteEvaluationResult",
    "ImaginedRouteStepEvaluation",
]
