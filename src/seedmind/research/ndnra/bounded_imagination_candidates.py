"""Deterministic exact-record imagined candidate enumeration for bounded imagination."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.bounded_imagination import ImaginedActionSequence
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.learned_consequence_model import (
    ConsequencePredictionRequest,
    ContextActionConsequenceRecord,
    LearnedConsequenceModel,
)


class CandidateGenerationTruncationReason(StrEnum):
    """Stable result-level reasons for partial deterministic enumeration."""

    SOURCE_RECORD_BOUND_REACHED = "source_record_bound_reached"
    BRANCH_BOUND_REACHED = "branch_bound_reached"
    CANDIDATE_BOUND_REACHED = "candidate_bound_reached"
    EXPANSION_BOUND_REACHED = "expansion_bound_reached"
    SUPPORTING_SOURCE_EVENT_BOUND_REACHED = "supporting_source_event_bound_reached"


@dataclass(frozen=True, slots=True)
class BoundedCandidateGenerationConfig:
    """Finite bounds for exact-record candidate enumeration."""

    maximum_requested_effect_dimensions: int = 16
    maximum_source_records_considered: int = 32
    maximum_branch_actions_per_prefix: int = 4
    maximum_sequence_depth: int = 3
    maximum_generated_candidates: int = 8
    maximum_total_expansions: int = 24
    maximum_supporting_real_event_ids_per_candidate: int = 64

    def __post_init__(self) -> None:
        for name, value in (
            (
                "maximum_requested_effect_dimensions",
                self.maximum_requested_effect_dimensions,
            ),
            ("maximum_source_records_considered", self.maximum_source_records_considered),
            ("maximum_branch_actions_per_prefix", self.maximum_branch_actions_per_prefix),
            ("maximum_sequence_depth", self.maximum_sequence_depth),
            ("maximum_generated_candidates", self.maximum_generated_candidates),
            ("maximum_total_expansions", self.maximum_total_expansions),
            (
                "maximum_supporting_real_event_ids_per_candidate",
                self.maximum_supporting_real_event_ids_per_candidate,
            ),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    def snapshot(self) -> dict[str, object]:
        return {
            "maximum_requested_effect_dimensions": self.maximum_requested_effect_dimensions,
            "maximum_source_records_considered": self.maximum_source_records_considered,
            "maximum_branch_actions_per_prefix": self.maximum_branch_actions_per_prefix,
            "maximum_sequence_depth": self.maximum_sequence_depth,
            "maximum_generated_candidates": self.maximum_generated_candidates,
            "maximum_total_expansions": self.maximum_total_expansions,
            "maximum_supporting_real_event_ids_per_candidate": (
                self.maximum_supporting_real_event_ids_per_candidate
            ),
        }


@dataclass(frozen=True, slots=True)
class ImaginedCandidateGenerationRequest:
    """Exact starting context and requested effects for deterministic enumeration."""

    context: ContextSignature
    requested_effect_codes: tuple[str, ...]
    config: BoundedCandidateGenerationConfig = field(
        default_factory=BoundedCandidateGenerationConfig
    )
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_sorted_unique_codes("requested_effect_codes", self.requested_effect_codes)
        if not self.requested_effect_codes:
            raise ValueError("requested_effect_codes must not be empty")
        if len(self.requested_effect_codes) > self.config.maximum_requested_effect_dimensions:
            raise ValueError("effect-dimension bound exceeded")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined candidate generation requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError(
                "imagined candidate generation requests cannot control production actions"
            )

    @property
    def request_id(self) -> str:
        return _identity("imagined-candidate-generation-request", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"request_id": self.request_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "context": self.context.snapshot(),
            "requested_effect_codes": list(self.requested_effect_codes),
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
class ImaginedCandidateGenerationStep:
    """One imagined step admitted only from exact record and exact prediction evidence."""

    step_id: str
    step_index: int
    origin: ExperienceOrigin
    context: ContextSignature
    action_code: str
    predicted_effects: tuple[EffectObservation, ...]
    predicted_next_context: ContextSignature
    source_record_id: str
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
        _validate_ascii_code("step_id", self.step_id)
        if (
            isinstance(self.step_index, bool)
            or not isinstance(self.step_index, int)
            or self.step_index < 0
        ):
            raise ValueError("step_index must be a non-negative integer")
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("imagined candidate generation steps require imagined origin")
        _validate_ascii_code("action_code", self.action_code)
        _validate_ascii_code("source_record_id", self.source_record_id)
        _validate_ascii_code("source_prediction_id", self.source_prediction_id)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        _validate_effects("predicted_effects", self.predicted_effects, allow_empty=False)
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined candidate generation steps cannot select actions")
        if self.has_production_action_authority:
            raise ValueError(
                "imagined candidate generation steps cannot control production actions"
            )
        if self.step_id != _identity(
            "imagined-candidate-generation-step", self._identity_payload()
        ):
            raise ValueError("imagined candidate generation step identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"step_id": self.step_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "step_index": self.step_index,
            "origin": self.origin.value,
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "predicted_effects": [_effect_snapshot(item) for item in self.predicted_effects],
            "predicted_next_context": self.predicted_next_context.snapshot(),
            "source_record_id": self.source_record_id,
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
class ImaginedGeneratedCandidate:
    """One fully supported BFS prefix from exact retained learned records."""

    candidate_id: str
    origin: ExperienceOrigin
    sequence: ImaginedActionSequence
    steps: tuple[ImaginedCandidateGenerationStep, ...]
    final_context: ContextSignature
    source_record_ids: tuple[str, ...]
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
        _validate_ascii_code("candidate_id", self.candidate_id)
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("imagined generated candidates require imagined origin")
        if not self.steps:
            raise ValueError("imagined generated candidates require at least one step")
        _validate_sorted_unique_codes("source_record_ids", self.source_record_ids)
        _validate_sorted_unique_codes("source_prediction_ids", self.source_prediction_ids)
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        if self.sequence.action_codes != tuple(step.action_code for step in self.steps):
            raise ValueError("generated candidate sequence must match step actions")
        for index, step in enumerate(self.steps):
            if step.step_index != index:
                raise ValueError("generated candidate steps must use contiguous indexes")
            if index > 0 and self.steps[index - 1].predicted_next_context != step.context:
                raise ValueError("generated candidate steps must be exactly continuous")
        if self.final_context != self.steps[-1].predicted_next_context:
            raise ValueError("generated candidate final context is inconsistent")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined generated candidates cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("imagined generated candidates cannot control production actions")
        if self.candidate_id != _identity("imagined-generated-candidate", self._identity_payload()):
            raise ValueError("imagined generated candidate identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"candidate_id": self.candidate_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "sequence": self.sequence.snapshot(),
            "steps": [item.snapshot() for item in self.steps],
            "final_context": self.final_context.snapshot(),
            "source_record_ids": list(self.source_record_ids),
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
class ImaginedCandidateGenerationResult:
    """Deterministic exact-record BFS enumeration result."""

    result_id: str
    request: ImaginedCandidateGenerationRequest
    candidates: tuple[ImaginedGeneratedCandidate, ...]
    truncated: bool
    truncation_reasons: tuple[CandidateGenerationTruncationReason, ...]
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
        reasons = tuple(reason.value for reason in self.truncation_reasons)
        _validate_sorted_unique_codes("truncation_reasons", reasons)
        if self.truncated != bool(self.truncation_reasons):
            raise ValueError("result truncation flag must match truncation reasons")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("imagined candidate generation results cannot select actions")
        if self.has_production_action_authority:
            raise ValueError(
                "imagined candidate generation results cannot control production actions"
            )
        if self.result_id != _identity(
            "imagined-candidate-generation-result", self._identity_payload()
        ):
            raise ValueError("imagined candidate generation result identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "candidates": [item.snapshot() for item in self.candidates],
            "truncated": self.truncated,
            "truncation_reasons": [item.value for item in self.truncation_reasons],
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
class BoundedExactCandidateGenerator:
    """Enumerate exact supported imagined prefixes in deterministic BFS order."""

    learned_model: LearnedConsequenceModel

    def generate(
        self,
        request: ImaginedCandidateGenerationRequest,
    ) -> ImaginedCandidateGenerationResult:
        before_snapshot = self.learned_model.snapshot()
        reasons: set[CandidateGenerationTruncationReason] = set()
        candidates: list[ImaginedGeneratedCandidate] = []
        total_expansions = 0
        source_records_considered = 0
        queue: deque[_CandidatePrefixState] = deque(
            [
                _CandidatePrefixState(
                    context=request.context,
                    steps=(),
                    source_prediction_ids=(),
                    supporting_real_event_ids=(),
                )
            ]
        )

        while queue:
            prefix = queue.popleft()
            if len(prefix.steps) >= request.config.maximum_sequence_depth:
                continue

            exact_records = self._exact_records_for_context(prefix.context)
            if not exact_records:
                continue
            if total_expansions >= request.config.maximum_total_expansions:
                reasons.add(CandidateGenerationTruncationReason.EXPANSION_BOUND_REACHED)
                break

            total_expansions += 1
            if len(exact_records) > request.config.maximum_branch_actions_per_prefix:
                reasons.add(CandidateGenerationTruncationReason.BRANCH_BOUND_REACHED)
            branch_records = exact_records[: request.config.maximum_branch_actions_per_prefix]

            for record in branch_records:
                if source_records_considered >= request.config.maximum_source_records_considered:
                    reasons.add(CandidateGenerationTruncationReason.SOURCE_RECORD_BOUND_REACHED)
                    queue.clear()
                    break
                source_records_considered += 1
                step = self._admit_step(
                    step_index=len(prefix.steps),
                    prefix_context=prefix.context,
                    record=record,
                    requested_effect_codes=request.requested_effect_codes,
                )
                if step is None:
                    continue
                if step.source_prediction_id in prefix.source_prediction_ids:
                    continue
                supporting_real_event_ids = tuple(
                    sorted(
                        set(prefix.supporting_real_event_ids) | set(step.supporting_real_event_ids)
                    )
                )
                if (
                    len(supporting_real_event_ids)
                    > request.config.maximum_supporting_real_event_ids_per_candidate
                ):
                    reasons.add(
                        CandidateGenerationTruncationReason.SUPPORTING_SOURCE_EVENT_BOUND_REACHED
                    )
                    continue
                if len(candidates) >= request.config.maximum_generated_candidates:
                    reasons.add(CandidateGenerationTruncationReason.CANDIDATE_BOUND_REACHED)
                    queue.clear()
                    break
                steps = (*prefix.steps, step)
                candidates.append(
                    _candidate_from_steps(
                        steps=steps,
                        supporting_real_event_ids=supporting_real_event_ids,
                    )
                )
                queue.append(
                    _CandidatePrefixState(
                        context=step.predicted_next_context,
                        steps=steps,
                        source_prediction_ids=(
                            *prefix.source_prediction_ids,
                            step.source_prediction_id,
                        ),
                        supporting_real_event_ids=supporting_real_event_ids,
                    )
                )

        if before_snapshot != self.learned_model.snapshot():
            raise RuntimeError("candidate generation must not mutate the learned model")

        result = ImaginedCandidateGenerationResult(
            result_id=_identity(
                "imagined-candidate-generation-result",
                {
                    "request": request.snapshot(),
                    "candidates": [item.snapshot() for item in candidates],
                    "truncated": bool(reasons),
                    "truncation_reasons": sorted(reason.value for reason in reasons),
                    "factual_confidence_change": 0.0,
                    "mastery_change": 0.0,
                    "competence_change": 0.0,
                    "growth_pressure_change": 0.0,
                    "replay_evidence_change": 0.0,
                    "real_observation_change": 0.0,
                    "has_action_selection_authority": False,
                    "has_production_action_authority": False,
                },
            ),
            request=request,
            candidates=tuple(candidates),
            truncated=bool(reasons),
            truncation_reasons=tuple(
                CandidateGenerationTruncationReason(reason)
                for reason in sorted(reason.value for reason in reasons)
            ),
        )
        if before_snapshot != self.learned_model.snapshot():
            raise RuntimeError("candidate generation must leave the learned model unchanged")
        return result

    def _exact_records_for_context(
        self,
        context: ContextSignature,
    ) -> tuple[ContextActionConsequenceRecord, ...]:
        return tuple(
            sorted(
                (
                    record
                    for record in self.learned_model.records
                    if record.context == context
                    and record.action_code in context.available_action_codes
                ),
                key=lambda record: (record.action_code, record.record_id),
            )
        )

    def _admit_step(
        self,
        *,
        step_index: int,
        prefix_context: ContextSignature,
        record: ContextActionConsequenceRecord,
        requested_effect_codes: tuple[str, ...],
    ) -> ImaginedCandidateGenerationStep | None:
        if record.context != prefix_context:
            return None
        if record.action_code not in prefix_context.available_action_codes:
            return None
        prediction = self.learned_model.predict(
            ConsequencePredictionRequest(
                context=prefix_context,
                action_code=record.action_code,
                relevant_effect_codes=requested_effect_codes,
            )
        )
        predicted_codes = tuple(effect.effect_code for effect in prediction.predicted_effects)
        if predicted_codes != requested_effect_codes:
            return None
        if prediction.predicted_next_context is None:
            return None
        payload = {
            "step_index": step_index,
            "origin": ExperienceOrigin.IMAGINED.value,
            "context": prefix_context.snapshot(),
            "action_code": record.action_code,
            "predicted_effects": [
                _effect_snapshot(effect) for effect in prediction.predicted_effects
            ],
            "predicted_next_context": prediction.predicted_next_context.snapshot(),
            "source_record_id": record.record_id,
            "source_prediction_id": prediction.prediction_id,
            "supporting_real_event_ids": list(prediction.supporting_real_event_ids),
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedCandidateGenerationStep(
            step_id=_identity("imagined-candidate-generation-step", payload),
            step_index=step_index,
            origin=ExperienceOrigin.IMAGINED,
            context=prefix_context,
            action_code=record.action_code,
            predicted_effects=prediction.predicted_effects,
            predicted_next_context=prediction.predicted_next_context,
            source_record_id=record.record_id,
            source_prediction_id=prediction.prediction_id,
            supporting_real_event_ids=prediction.supporting_real_event_ids,
        )


@dataclass(frozen=True, slots=True)
class _CandidatePrefixState:
    context: ContextSignature
    steps: tuple[ImaginedCandidateGenerationStep, ...]
    source_prediction_ids: tuple[str, ...]
    supporting_real_event_ids: tuple[str, ...]


def _candidate_from_steps(
    *,
    steps: tuple[ImaginedCandidateGenerationStep, ...],
    supporting_real_event_ids: tuple[str, ...],
) -> ImaginedGeneratedCandidate:
    payload = {
        "origin": ExperienceOrigin.IMAGINED.value,
        "sequence": ImaginedActionSequence(tuple(step.action_code for step in steps)).snapshot(),
        "steps": [step.snapshot() for step in steps],
        "final_context": steps[-1].predicted_next_context.snapshot(),
        "source_record_ids": sorted({step.source_record_id for step in steps}),
        "source_prediction_ids": sorted({step.source_prediction_id for step in steps}),
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
    return ImaginedGeneratedCandidate(
        candidate_id=_identity("imagined-generated-candidate", payload),
        origin=ExperienceOrigin.IMAGINED,
        sequence=ImaginedActionSequence(tuple(step.action_code for step in steps)),
        steps=steps,
        final_context=steps[-1].predicted_next_context,
        source_record_ids=tuple(sorted({step.source_record_id for step in steps})),
        source_prediction_ids=tuple(sorted({step.source_prediction_id for step in steps})),
        supporting_real_event_ids=supporting_real_event_ids,
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
    if effect_codes != tuple(sorted(effect_codes)):
        raise ValueError(f"{name} effect dimensions must be sorted")


def _validate_zero_delta(name: str, value: float) -> None:
    if not isinstance(value, float) or not isfinite(value) or value != 0.0:
        raise ValueError(f"{name} must remain exactly zero")


__all__ = [
    "BoundedCandidateGenerationConfig",
    "BoundedExactCandidateGenerator",
    "CandidateGenerationTruncationReason",
    "ImaginedCandidateGenerationRequest",
    "ImaginedCandidateGenerationResult",
    "ImaginedCandidateGenerationStep",
    "ImaginedGeneratedCandidate",
]
