"""Bounded caller-driven imagination over exact learned consequence predictions."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from math import isfinite

from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.learned_consequence_model import (
    ConsequencePrediction,
    ConsequencePredictionRequest,
    LearnedConsequenceModel,
)


@dataclass(frozen=True, slots=True)
class BoundedImaginationConfig:
    """Finite request-wide bounds for exact-source-only imagination."""

    maximum_candidate_sequences: int = 8
    maximum_sequence_depth: int = 3
    maximum_total_prediction_steps: int = 24
    maximum_effect_dimensions: int = 16
    maximum_supporting_real_event_ids_per_trace: int = 64

    def __post_init__(self) -> None:
        for name, value in (
            ("maximum_candidate_sequences", self.maximum_candidate_sequences),
            ("maximum_sequence_depth", self.maximum_sequence_depth),
            ("maximum_total_prediction_steps", self.maximum_total_prediction_steps),
            ("maximum_effect_dimensions", self.maximum_effect_dimensions),
            (
                "maximum_supporting_real_event_ids_per_trace",
                self.maximum_supporting_real_event_ids_per_trace,
            ),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    def snapshot(self) -> dict[str, object]:
        return {
            "maximum_candidate_sequences": self.maximum_candidate_sequences,
            "maximum_sequence_depth": self.maximum_sequence_depth,
            "maximum_total_prediction_steps": self.maximum_total_prediction_steps,
            "maximum_effect_dimensions": self.maximum_effect_dimensions,
            "maximum_supporting_real_event_ids_per_trace": (
                self.maximum_supporting_real_event_ids_per_trace
            ),
        }


@dataclass(frozen=True, slots=True)
class ImaginedActionSequence:
    """One caller-supplied ordered candidate action sequence."""

    action_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.action_codes:
            raise ValueError("action_codes must not be empty")
        for action_code in self.action_codes:
            _validate_ascii_code("action_code", action_code)

    def snapshot(self) -> dict[str, object]:
        return {"action_codes": list(self.action_codes)}


@dataclass(frozen=True, slots=True)
class ImaginedConsequenceRequest:
    """Exact-source-only imagination request."""

    context: ContextSignature
    relevant_effect_codes: tuple[str, ...]
    candidate_sequences: tuple[ImaginedActionSequence, ...]
    config: BoundedImaginationConfig = field(default_factory=BoundedImaginationConfig)
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_sorted_unique_codes("relevant_effect_codes", self.relevant_effect_codes)
        if not self.relevant_effect_codes:
            raise ValueError("relevant_effect_codes must not be empty")
        if not self.candidate_sequences:
            raise ValueError("candidate_sequences must not be empty")
        if len(self.candidate_sequences) > self.config.maximum_candidate_sequences:
            raise ValueError("candidate-count bound exceeded")
        total_steps = 0
        identities: set[tuple[str, ...]] = set()
        for sequence in self.candidate_sequences:
            total_steps += len(sequence.action_codes)
            if len(sequence.action_codes) > self.config.maximum_sequence_depth:
                raise ValueError("sequence-depth bound exceeded")
            identity = sequence.action_codes
            if identity in identities:
                raise ValueError("duplicate candidate sequences are not allowed")
            identities.add(identity)
        if total_steps > self.config.maximum_total_prediction_steps:
            raise ValueError("total prediction-step bound exceeded")
        if len(self.relevant_effect_codes) > self.config.maximum_effect_dimensions:
            raise ValueError("effect-dimension bound exceeded")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined consequence requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("imagined consequence requests cannot control production actions")

    @property
    def request_id(self) -> str:
        return _identity("imagined-consequence-request", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"request_id": self.request_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "context": self.context.snapshot(),
            "relevant_effect_codes": list(self.relevant_effect_codes),
            "candidate_sequences": [item.snapshot() for item in self.candidate_sequences],
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
class ImaginedConsequenceStep:
    """One imagined step backed only by exact learned single-step prediction evidence."""

    step_index: int
    origin: ExperienceOrigin
    context: ContextSignature
    action_code: str
    relevant_effect_codes: tuple[str, ...]
    supported: bool
    failure_reason: str | None
    predicted_effects: tuple[EffectObservation, ...]
    predicted_next_context: ContextSignature | None
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
        if (
            isinstance(self.step_index, bool)
            or not isinstance(self.step_index, int)
            or self.step_index < 0
        ):
            raise ValueError("step_index must be a non-negative integer")
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("imagined consequence steps require imagined origin")
        _validate_ascii_code("action_code", self.action_code)
        _validate_sorted_unique_codes("relevant_effect_codes", self.relevant_effect_codes)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        _validate_effects("predicted_effects", self.predicted_effects, allow_empty=True)
        if self.failure_reason is not None:
            _validate_ascii_code("failure_reason", self.failure_reason)
        if self.supported:
            if self.failure_reason is not None:
                raise ValueError("supported imagined steps cannot have a failure reason")
            if self.predicted_next_context is None:
                raise ValueError("supported imagined steps require a predicted next context")
            predicted_codes = tuple(effect.effect_code for effect in self.predicted_effects)
            if predicted_codes != self.relevant_effect_codes:
                raise ValueError("supported imagined steps require complete exact effect evidence")
        else:
            if self.failure_reason is None:
                raise ValueError("unsupported imagined steps require a failure reason")
        _validate_ascii_code("source_prediction_id", self.source_prediction_id)
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined consequence steps cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("imagined consequence steps cannot control production actions")

    def snapshot(self) -> dict[str, object]:
        return {
            "step_index": self.step_index,
            "origin": self.origin.value,
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "relevant_effect_codes": list(self.relevant_effect_codes),
            "supported": self.supported,
            "failure_reason": self.failure_reason,
            "predicted_effects": [_effect_snapshot(item) for item in self.predicted_effects],
            "predicted_next_context": (
                None
                if self.predicted_next_context is None
                else self.predicted_next_context.snapshot()
            ),
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
class ImaginedConsequenceTrace:
    """One exact caller-supplied candidate rollout outcome."""

    trace_id: str
    origin: ExperienceOrigin
    candidate_sequence: ImaginedActionSequence
    supported: bool
    final_context: ContextSignature | None
    steps: tuple[ImaginedConsequenceStep, ...]
    source_prediction_ids: tuple[str, ...]
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
        _validate_ascii_code("trace_id", self.trace_id)
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("imagined consequence traces require imagined origin")
        _validate_sorted_unique_codes("source_prediction_ids", self.source_prediction_ids)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        if not self.steps:
            raise ValueError("imagined consequence traces require at least one step")
        for index, step in enumerate(self.steps):
            if step.step_index != index:
                raise ValueError("imagined consequence step indexes must be contiguous")
            if step.action_code != self.candidate_sequence.action_codes[index]:
                raise ValueError("imagined consequence step order must match the caller sequence")
            if index > 0 and self.steps[index - 1].predicted_next_context != step.context:
                raise ValueError("imagined consequence step continuity is disconnected")
        if self.supported:
            if self.final_context is None:
                raise ValueError("supported imagined traces require a final context")
            if not all(step.supported for step in self.steps):
                raise ValueError("supported imagined traces require all steps to be supported")
            if self.final_context != self.steps[-1].predicted_next_context:
                raise ValueError("supported imagined trace final context is inconsistent")
        else:
            if self.final_context is not None:
                raise ValueError("unsupported imagined traces cannot expose a final context")
            supported_prefix = True
            failure_count = 0
            for step in self.steps:
                if step.supported:
                    if not supported_prefix:
                        raise ValueError("unsupported imagined traces cannot resume after failure")
                else:
                    supported_prefix = False
                    failure_count += 1
            if failure_count != 1 or self.steps[-1].supported:
                raise ValueError("unsupported imagined traces must end at the first failing step")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined consequence traces cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("imagined consequence traces cannot control production actions")
        if self.trace_id != _identity("imagined-consequence-trace", self._identity_payload()):
            raise ValueError("imagined consequence trace identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"trace_id": self.trace_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "candidate_sequence": self.candidate_sequence.snapshot(),
            "supported": self.supported,
            "final_context": None if self.final_context is None else self.final_context.snapshot(),
            "steps": [item.snapshot() for item in self.steps],
            "source_prediction_ids": list(self.source_prediction_ids),
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
class BoundedImaginationResult:
    """Deterministic result for one exact-source-only imagination request."""

    result_id: str
    request: ImaginedConsequenceRequest
    traces: tuple[ImaginedConsequenceTrace, ...]
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
        if len(self.traces) != len(self.request.candidate_sequences):
            raise ValueError("result traces must preserve the caller candidate count")
        for index, trace in enumerate(self.traces):
            if trace.candidate_sequence != self.request.candidate_sequences[index]:
                raise ValueError("result traces must preserve caller order exactly")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("bounded imagination results cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("bounded imagination results cannot control production actions")
        if self.result_id != _identity("bounded-imagination-result", self._identity_payload()):
            raise ValueError("bounded imagination result identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "traces": [item.snapshot() for item in self.traces],
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(slots=True)
class BoundedConsequenceImagination:
    """Exact-source-only multi-step imagination over a learned consequence model."""

    learned_model: LearnedConsequenceModel

    def imagine(self, request: ImaginedConsequenceRequest) -> BoundedImaginationResult:
        before_snapshot = self.learned_model.snapshot()
        traces = tuple(
            self._trace_for_sequence(
                start_context=request.context,
                relevant_effect_codes=request.relevant_effect_codes,
                sequence=sequence,
                config=request.config,
            )
            for sequence in request.candidate_sequences
        )
        if before_snapshot != self.learned_model.snapshot():
            raise RuntimeError("bounded imagination must not mutate the learned model")
        payload = {
            "request": request.snapshot(),
            "traces": [item.snapshot() for item in traces],
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        result = BoundedImaginationResult(
            result_id=_identity("bounded-imagination-result", payload),
            request=request,
            traces=traces,
        )
        if before_snapshot != self.learned_model.snapshot():
            raise RuntimeError("bounded imagination must leave the learned model unchanged")
        return result

    def _trace_for_sequence(
        self,
        *,
        start_context: ContextSignature,
        relevant_effect_codes: tuple[str, ...],
        sequence: ImaginedActionSequence,
        config: BoundedImaginationConfig,
    ) -> ImaginedConsequenceTrace:
        steps: list[ImaginedConsequenceStep] = []
        current_context = start_context
        supporting_real_event_ids: set[str] = set()
        source_prediction_ids: set[str] = set()
        final_context: ContextSignature | None = None
        supported = True
        for index, action_code in enumerate(sequence.action_codes):
            if action_code not in current_context.available_action_codes:
                step = self._unsupported_step(
                    step_index=index,
                    context=current_context,
                    action_code=action_code,
                    relevant_effect_codes=relevant_effect_codes,
                    failure_reason="action_unavailable",
                )
                steps.append(step)
                supported = False
                break
            prediction = self.learned_model.predict(
                ConsequencePredictionRequest(
                    context=current_context,
                    action_code=action_code,
                    relevant_effect_codes=relevant_effect_codes,
                )
            )
            proposed_supporting_real_event_ids = supporting_real_event_ids | set(
                prediction.supporting_real_event_ids
            )
            if (
                len(proposed_supporting_real_event_ids)
                > config.maximum_supporting_real_event_ids_per_trace
            ):
                steps.append(
                    ImaginedConsequenceStep(
                        step_index=index,
                        origin=ExperienceOrigin.IMAGINED,
                        context=current_context,
                        action_code=action_code,
                        relevant_effect_codes=relevant_effect_codes,
                        supported=False,
                        failure_reason="supporting_source_event_bound_exceeded",
                        predicted_effects=(),
                        predicted_next_context=None,
                        source_prediction_id=prediction.prediction_id,
                        supporting_real_event_ids=(),
                    )
                )
                source_prediction_ids.add(prediction.prediction_id)
                supported = False
                break
            step = self._step_from_prediction(
                step_index=index,
                context=current_context,
                relevant_effect_codes=relevant_effect_codes,
                prediction=prediction,
            )
            steps.append(step)
            supporting_real_event_ids = proposed_supporting_real_event_ids
            source_prediction_ids.add(step.source_prediction_id)
            if not step.supported:
                supported = False
                break
            final_context = step.predicted_next_context
            assert final_context is not None
            current_context = final_context
        trace_payload = {
            "origin": ExperienceOrigin.IMAGINED.value,
            "candidate_sequence": sequence.snapshot(),
            "supported": supported,
            "final_context": None
            if final_context is None or not supported
            else final_context.snapshot(),
            "steps": [item.snapshot() for item in steps],
            "source_prediction_ids": sorted(source_prediction_ids),
            "supporting_real_event_ids": sorted(supporting_real_event_ids),
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedConsequenceTrace(
            trace_id=_identity("imagined-consequence-trace", trace_payload),
            origin=ExperienceOrigin.IMAGINED,
            candidate_sequence=sequence,
            supported=supported,
            final_context=final_context if supported else None,
            steps=tuple(steps),
            source_prediction_ids=tuple(sorted(source_prediction_ids)),
            supporting_real_event_ids=tuple(sorted(supporting_real_event_ids)),
        )

    def _unsupported_step(
        self,
        *,
        step_index: int,
        context: ContextSignature,
        action_code: str,
        relevant_effect_codes: tuple[str, ...],
        failure_reason: str,
    ) -> ImaginedConsequenceStep:
        payload: dict[str, object] = {
            "request": ConsequencePredictionRequest(
                context=context,
                action_code=action_code,
                relevant_effect_codes=relevant_effect_codes,
            ).snapshot(),
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
        return ImaginedConsequenceStep(
            step_index=step_index,
            origin=ExperienceOrigin.IMAGINED,
            context=context,
            action_code=action_code,
            relevant_effect_codes=relevant_effect_codes,
            supported=False,
            failure_reason=failure_reason,
            predicted_effects=(),
            predicted_next_context=None,
            source_prediction_id=_identity("consequence-prediction", payload),
            supporting_real_event_ids=(),
        )

    def _step_from_prediction(
        self,
        *,
        step_index: int,
        context: ContextSignature,
        relevant_effect_codes: tuple[str, ...],
        prediction: ConsequencePrediction,
    ) -> ImaginedConsequenceStep:
        predicted_codes = tuple(effect.effect_code for effect in prediction.predicted_effects)
        failure_reason: str | None = None
        supported = True
        if predicted_codes != relevant_effect_codes:
            failure_reason = "missing_exact_evidence"
            supported = False
        elif prediction.predicted_next_context is None:
            failure_reason = "missing_exact_next_context"
            supported = False
        return ImaginedConsequenceStep(
            step_index=step_index,
            origin=ExperienceOrigin.IMAGINED,
            context=context,
            action_code=prediction.request.action_code,
            relevant_effect_codes=relevant_effect_codes,
            supported=supported,
            failure_reason=failure_reason,
            predicted_effects=prediction.predicted_effects,
            predicted_next_context=prediction.predicted_next_context if supported else None,
            source_prediction_id=prediction.prediction_id,
            supporting_real_event_ids=prediction.supporting_real_event_ids,
        )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    return f"{prefix}:{hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()}"


def _effect_snapshot(effect: EffectObservation) -> dict[str, object]:
    return {
        "effect_code": effect.effect_code,
        "value": effect.value,
        "confidence": effect.confidence,
    }


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


def _validate_effects(
    name: str,
    effects: Sequence[EffectObservation],
    *,
    allow_empty: bool,
) -> None:
    if not allow_empty and not effects:
        raise ValueError(f"{name} must not be empty")
    effect_codes = tuple(effect.effect_code for effect in effects)
    if len(effect_codes) != len(set(effect_codes)):
        raise ValueError(f"{name} effect dimensions must be unique")


def _validate_zero_delta(name: str, value: float) -> None:
    if not isinstance(value, float) or not isfinite(value) or value != 0.0:
        raise ValueError(f"{name} must remain exactly zero")


__all__ = [
    "BoundedConsequenceImagination",
    "BoundedImaginationConfig",
    "BoundedImaginationResult",
    "ImaginedActionSequence",
    "ImaginedConsequenceRequest",
    "ImaginedConsequenceStep",
    "ImaginedConsequenceTrace",
]
