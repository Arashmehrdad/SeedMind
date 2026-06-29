"""Pairwise non-authoritative comparison over imagined route evaluations."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.bounded_imagination_evaluation import (
    ImaginedAlignmentDirection,
    ImaginedEffectAlignment,
    ImaginedRouteEvaluation,
    ImaginedRouteEvaluationResult,
    ImaginedRouteStepEvaluation,
)
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin


class ImaginedRoutePairRelation(StrEnum):
    """Pairwise relation that is not a global rank or route selection."""

    LEFT_DOMINATES_RIGHT = "left_dominates_right"
    RIGHT_DOMINATES_LEFT = "right_dominates_left"
    ALIGNMENT_EQUIVALENT = "alignment_equivalent"
    INCOMPARABLE = "incomparable"


class ImaginedRouteDimensionRelation(StrEnum):
    """Local per-step, per-effect relation between two route evaluations."""

    LEFT_BETTER = "left_better"
    RIGHT_BETTER = "right_better"
    EQUIVALENT = "equivalent"
    UNKNOWN = "unknown"


class ImaginedRouteIncomparabilityReason(StrEnum):
    """Explicit reasons dominance is blocked for a pair comparison."""

    UNKNOWN_ALIGNMENT = "unknown_alignment"
    LOW_CONFIDENCE = "low_confidence"
    DIFFERENT_ROUTE_DEPTH = "different_route_depth"
    CONFLICTING_TRADEOFF = "conflicting_tradeoff"


@dataclass(frozen=True, slots=True)
class BoundedRouteComparisonConfig:
    """Finite limits for pure pairwise imagined-route comparison."""

    maximum_evaluations: int = 8
    maximum_pairs: int = 28
    maximum_steps_per_evaluation: int = 3
    maximum_dimensions_per_step: int = 16
    maximum_total_dimension_comparisons: int = 1344
    maximum_unique_supporting_real_event_ids_per_evaluation: int = 64
    confidence_floor: float = 0.0
    comparison_epsilon: float = 1e-12

    def __post_init__(self) -> None:
        for name, value in (
            ("maximum_evaluations", self.maximum_evaluations),
            ("maximum_pairs", self.maximum_pairs),
            ("maximum_steps_per_evaluation", self.maximum_steps_per_evaluation),
            ("maximum_dimensions_per_step", self.maximum_dimensions_per_step),
            (
                "maximum_total_dimension_comparisons",
                self.maximum_total_dimension_comparisons,
            ),
            (
                "maximum_unique_supporting_real_event_ids_per_evaluation",
                self.maximum_unique_supporting_real_event_ids_per_evaluation,
            ),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        _validate_unit("confidence_floor", self.confidence_floor)
        if (
            not isfinite(self.comparison_epsilon)
            or self.comparison_epsilon < 0.0
            or self.comparison_epsilon > 1e-6
        ):
            raise ValueError("comparison_epsilon must be finite between zero and 1e-6")

    def snapshot(self) -> dict[str, object]:
        return {
            "maximum_evaluations": self.maximum_evaluations,
            "maximum_pairs": self.maximum_pairs,
            "maximum_steps_per_evaluation": self.maximum_steps_per_evaluation,
            "maximum_dimensions_per_step": self.maximum_dimensions_per_step,
            "maximum_total_dimension_comparisons": self.maximum_total_dimension_comparisons,
            "maximum_unique_supporting_real_event_ids_per_evaluation": (
                self.maximum_unique_supporting_real_event_ids_per_evaluation
            ),
            "confidence_floor": self.confidence_floor,
            "comparison_epsilon": self.comparison_epsilon,
        }


@dataclass(frozen=True, slots=True)
class ImaginedRouteComparisonRequest:
    """One complete Batch 3 result to compare pairwise without authority."""

    source_result: ImaginedRouteEvaluationResult
    config: BoundedRouteComparisonConfig = field(default_factory=BoundedRouteComparisonConfig)
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        evaluations = self.source_result.evaluations
        if len(evaluations) > self.config.maximum_evaluations:
            raise ValueError("evaluation bound exceeded")
        evaluation_ids = tuple(evaluation.evaluation_id for evaluation in evaluations)
        if len(evaluation_ids) != len(set(evaluation_ids)):
            raise ValueError("route comparison evaluation IDs must be unique")
        candidate_ids = tuple(evaluation.candidate_id for evaluation in evaluations)
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("route comparison candidate IDs must be unique")
        if any(evaluation.origin is not ExperienceOrigin.IMAGINED for evaluation in evaluations):
            raise ValueError("route comparison accepts imagined evaluations only")
        source_candidates = self.source_result.request.candidates
        if len(evaluations) != len(source_candidates):
            raise ValueError("route comparison source result is incomplete")
        for index, evaluation in enumerate(evaluations):
            if evaluation.candidate_id != source_candidates[index].candidate_id:
                raise ValueError("route comparison must preserve source caller order")
        _validate_zero_delta(
            "source factual_confidence_change",
            self.source_result.factual_confidence_change,
        )
        _validate_zero_delta("source mastery_change", self.source_result.mastery_change)
        _validate_zero_delta("source competence_change", self.source_result.competence_change)
        _validate_zero_delta(
            "source growth_pressure_change",
            self.source_result.growth_pressure_change,
        )
        _validate_zero_delta(
            "source replay_evidence_change",
            self.source_result.replay_evidence_change,
        )
        _validate_zero_delta(
            "source real_observation_change",
            self.source_result.real_observation_change,
        )
        if self.source_result.has_action_selection_authority:
            raise ValueError("source route evaluation result cannot select actions")
        if self.source_result.has_production_action_authority:
            raise ValueError("source route evaluation result cannot control production actions")
        pair_count = len(evaluations) * (len(evaluations) - 1) // 2
        if pair_count > self.config.maximum_pairs:
            raise ValueError("pair bound exceeded")
        dimensions = _need_dimensions(self.source_result)
        if len(dimensions) > self.config.maximum_dimensions_per_step:
            raise ValueError("dimension bound exceeded")
        self._validate_evaluations(evaluations, dimensions)
        total_dimension_comparisons = _required_dimension_comparison_count(evaluations)
        if total_dimension_comparisons > self.config.maximum_total_dimension_comparisons:
            raise ValueError("total dimension-comparison bound exceeded")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("route comparison requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("route comparison requests cannot control production actions")

    @property
    def request_id(self) -> str:
        return _identity("imagined-route-comparison-request", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"request_id": self.request_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "source_result": self.source_result.snapshot(),
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

    def _validate_evaluations(
        self,
        evaluations: tuple[ImaginedRouteEvaluation, ...],
        dimensions: dict[str, tuple[float, float]],
    ) -> None:
        need_code = self.source_result.request.need.need_code
        expected_effect_codes = tuple(sorted(dimensions))
        expected_tolerance = self.source_result.request.config.neutral_tolerance
        for evaluation in evaluations:
            if len(evaluation.step_evaluations) > self.config.maximum_steps_per_evaluation:
                raise ValueError("step bound exceeded")
            support: set[str] = set()
            for step in evaluation.step_evaluations:
                if step.context.active_need_code != need_code:
                    raise ValueError("route comparison active need mismatch")
                alignments = tuple(step.alignments)
                if len(alignments) > self.config.maximum_dimensions_per_step:
                    raise ValueError("dimension bound exceeded")
                if tuple(item.effect_code for item in alignments) != expected_effect_codes:
                    raise ValueError("route comparison effect semantics mismatch")
                for alignment in alignments:
                    desired_direction, intensity = dimensions[alignment.effect_code]
                    if alignment.desired_direction != desired_direction:
                        raise ValueError("route comparison desired-direction mismatch")
                    if alignment.intensity != intensity:
                        raise ValueError("route comparison intensity mismatch")
                    if alignment.neutral_tolerance != expected_tolerance:
                        raise ValueError("route comparison neutral-tolerance mismatch")
                    if alignment.step_index != step.step_index:
                        raise ValueError("route comparison alignment step mismatch")
                    if alignment.source_step_id != step.source_step_id:
                        raise ValueError("route comparison alignment source-step mismatch")
                    if alignment.source_prediction_id != step.source_prediction_id:
                        raise ValueError("route comparison alignment source-prediction mismatch")
                    if (
                        alignment.predicted_value is not None
                        and alignment.supporting_real_event_ids != step.supporting_real_event_ids
                    ):
                        raise ValueError("route comparison known alignment provenance mismatch")
                    if alignment.predicted_value is not None:
                        support.update(alignment.supporting_real_event_ids)
            if len(support) > self.config.maximum_unique_supporting_real_event_ids_per_evaluation:
                raise ValueError("supporting-real-event provenance bound exceeded")


@dataclass(frozen=True, slots=True)
class ImaginedRouteDimensionComparison:
    """One local per-step, per-effect comparison without copied provenance."""

    dimension_comparison_id: str
    origin: ExperienceOrigin
    left_caller_index: int
    right_caller_index: int
    left_evaluation_id: str
    right_evaluation_id: str
    step_index: int
    effect_code: str
    left_step_evaluation_id: str | None
    right_step_evaluation_id: str | None
    left_alignment_id: str | None
    right_alignment_id: str | None
    left_direction: ImaginedAlignmentDirection | None
    right_direction: ImaginedAlignmentDirection | None
    left_signed_alignment: float | None
    right_signed_alignment: float | None
    left_prediction_confidence: float | None
    right_prediction_confidence: float | None
    desired_direction: float
    intensity: float
    neutral_tolerance: float
    relation: ImaginedRouteDimensionRelation
    incomparability_reasons: tuple[ImaginedRouteIncomparabilityReason, ...]
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("dimension_comparison_id", self.dimension_comparison_id)
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("route dimension comparisons require imagined origin")
        _validate_index("left_caller_index", self.left_caller_index)
        _validate_index("right_caller_index", self.right_caller_index)
        if self.left_caller_index >= self.right_caller_index:
            raise ValueError("route comparison indexes must be caller ordered")
        _validate_ascii_code("left_evaluation_id", self.left_evaluation_id)
        _validate_ascii_code("right_evaluation_id", self.right_evaluation_id)
        _validate_index("step_index", self.step_index)
        _validate_ascii_code("effect_code", self.effect_code)
        for name, value in (
            ("left_step_evaluation_id", self.left_step_evaluation_id),
            ("right_step_evaluation_id", self.right_step_evaluation_id),
            ("left_alignment_id", self.left_alignment_id),
            ("right_alignment_id", self.right_alignment_id),
        ):
            if value is not None:
                _validate_ascii_code(name, value)
        if self.left_signed_alignment is not None:
            _validate_signed("left_signed_alignment", self.left_signed_alignment)
        if self.right_signed_alignment is not None:
            _validate_signed("right_signed_alignment", self.right_signed_alignment)
        _validate_signed_nonzero("desired_direction", self.desired_direction)
        _validate_positive_unit("intensity", self.intensity)
        _validate_unit("neutral_tolerance", self.neutral_tolerance)
        if self.left_prediction_confidence is not None:
            _validate_unit("left_prediction_confidence", self.left_prediction_confidence)
        if self.right_prediction_confidence is not None:
            _validate_unit("right_prediction_confidence", self.right_prediction_confidence)
        _validate_dimension_side_shape(
            side="left",
            step_evaluation_id=self.left_step_evaluation_id,
            alignment_id=self.left_alignment_id,
            direction=self.left_direction,
            signed_alignment=self.left_signed_alignment,
            prediction_confidence=self.left_prediction_confidence,
        )
        _validate_dimension_side_shape(
            side="right",
            step_evaluation_id=self.right_step_evaluation_id,
            alignment_id=self.right_alignment_id,
            direction=self.right_direction,
            signed_alignment=self.right_signed_alignment,
            prediction_confidence=self.right_prediction_confidence,
        )
        _validate_sorted_unique_enum_values(
            "incomparability_reasons",
            self.incomparability_reasons,
        )
        if (
            self.relation is not ImaginedRouteDimensionRelation.UNKNOWN
            and self.incomparability_reasons
        ):
            raise ValueError("known dimension relation cannot carry incomparability reasons")
        if (
            self.relation is ImaginedRouteDimensionRelation.UNKNOWN
            and not self.incomparability_reasons
        ):
            raise ValueError("unknown dimension relation requires a reason")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("route dimension comparisons cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("route dimension comparisons cannot control production actions")
        if self.dimension_comparison_id != _identity(
            "imagined-route-dimension-comparison",
            self._identity_payload(),
        ):
            raise ValueError("route dimension comparison identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"dimension_comparison_id": self.dimension_comparison_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "left_caller_index": self.left_caller_index,
            "right_caller_index": self.right_caller_index,
            "left_evaluation_id": self.left_evaluation_id,
            "right_evaluation_id": self.right_evaluation_id,
            "step_index": self.step_index,
            "effect_code": self.effect_code,
            "left_step_evaluation_id": self.left_step_evaluation_id,
            "right_step_evaluation_id": self.right_step_evaluation_id,
            "left_alignment_id": self.left_alignment_id,
            "right_alignment_id": self.right_alignment_id,
            "left_direction": None if self.left_direction is None else self.left_direction.value,
            "right_direction": None if self.right_direction is None else self.right_direction.value,
            "left_signed_alignment": self.left_signed_alignment,
            "right_signed_alignment": self.right_signed_alignment,
            "left_prediction_confidence": self.left_prediction_confidence,
            "right_prediction_confidence": self.right_prediction_confidence,
            "desired_direction": self.desired_direction,
            "intensity": self.intensity,
            "neutral_tolerance": self.neutral_tolerance,
            "relation": self.relation.value,
            "incomparability_reasons": [item.value for item in self.incomparability_reasons],
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
class ImaginedRoutePairComparison:
    """One caller-order pairwise route comparison, not a route ranking."""

    pair_comparison_id: str
    origin: ExperienceOrigin
    left_caller_index: int
    right_caller_index: int
    left_evaluation_id: str
    right_evaluation_id: str
    left_candidate_id: str
    right_candidate_id: str
    relation: ImaginedRoutePairRelation
    incomparability_reasons: tuple[ImaginedRouteIncomparabilityReason, ...]
    dimension_comparisons: tuple[ImaginedRouteDimensionComparison, ...]
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("pair_comparison_id", self.pair_comparison_id)
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("route pair comparisons require imagined origin")
        _validate_index("left_caller_index", self.left_caller_index)
        _validate_index("right_caller_index", self.right_caller_index)
        if self.left_caller_index >= self.right_caller_index:
            raise ValueError("route pair indexes must be caller ordered")
        _validate_ascii_code("left_evaluation_id", self.left_evaluation_id)
        _validate_ascii_code("right_evaluation_id", self.right_evaluation_id)
        _validate_ascii_code("left_candidate_id", self.left_candidate_id)
        _validate_ascii_code("right_candidate_id", self.right_candidate_id)
        _validate_sorted_unique_enum_values(
            "incomparability_reasons",
            self.incomparability_reasons,
        )
        if not self.dimension_comparisons:
            raise ValueError("route pair comparison requires at least one dimension")
        dimension_keys = tuple(
            (item.step_index, item.effect_code) for item in self.dimension_comparisons
        )
        if dimension_keys != tuple(sorted(dimension_keys)):
            raise ValueError("dimension comparisons must preserve sorted key order")
        if len(dimension_keys) != len(set(dimension_keys)):
            raise ValueError("dimension comparison keys must be unique")
        for item in self.dimension_comparisons:
            if item.left_caller_index != self.left_caller_index:
                raise ValueError("dimension comparison left caller index mismatch")
            if item.right_caller_index != self.right_caller_index:
                raise ValueError("dimension comparison right caller index mismatch")
            if item.left_evaluation_id != self.left_evaluation_id:
                raise ValueError("dimension comparison left evaluation mismatch")
            if item.right_evaluation_id != self.right_evaluation_id:
                raise ValueError("dimension comparison right evaluation mismatch")
        expected_relation, expected_reasons = _pair_relation(self.dimension_comparisons)
        if self.relation is not expected_relation:
            raise ValueError("route pair relation is inconsistent with dimensions")
        if self.incomparability_reasons != expected_reasons:
            raise ValueError("route pair reasons are inconsistent with dimensions")
        if self.relation is ImaginedRoutePairRelation.INCOMPARABLE:
            if not self.incomparability_reasons:
                raise ValueError("incomparable pair requires a reason")
        elif self.incomparability_reasons:
            raise ValueError("comparable pair cannot carry incomparability reasons")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("route pair comparisons cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("route pair comparisons cannot control production actions")
        if self.pair_comparison_id != _identity(
            "imagined-route-pair-comparison",
            self._identity_payload(),
        ):
            raise ValueError("route pair comparison identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"pair_comparison_id": self.pair_comparison_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "left_caller_index": self.left_caller_index,
            "right_caller_index": self.right_caller_index,
            "left_evaluation_id": self.left_evaluation_id,
            "right_evaluation_id": self.right_evaluation_id,
            "left_candidate_id": self.left_candidate_id,
            "right_candidate_id": self.right_candidate_id,
            "relation": self.relation.value,
            "incomparability_reasons": [item.value for item in self.incomparability_reasons],
            "dimension_comparisons": [item.snapshot() for item in self.dimension_comparisons],
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
class ImaginedRouteComparisonResult:
    """Deterministic pairwise comparison result with no ranking or winner."""

    result_id: str
    request: ImaginedRouteComparisonRequest
    pair_comparisons: tuple[ImaginedRoutePairComparison, ...]
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
        evaluation_count = len(self.request.source_result.evaluations)
        expected_pair_count = evaluation_count * (evaluation_count - 1) // 2
        if len(self.pair_comparisons) != expected_pair_count:
            raise ValueError("route comparison pair count is inconsistent")
        expected_indexes = tuple(
            (left_index, right_index)
            for left_index in range(evaluation_count)
            for right_index in range(left_index + 1, evaluation_count)
        )
        actual_indexes = tuple(
            (item.left_caller_index, item.right_caller_index) for item in self.pair_comparisons
        )
        if actual_indexes != expected_indexes:
            raise ValueError("route comparison pairs must preserve caller-index order")
        expected_pair_comparisons = tuple(
            BoundedImaginedRouteComparator()._compare_pair(
                request=self.request,
                left_index=left_index,
                right_index=right_index,
            )
            for left_index, right_index in expected_indexes
        )
        if self.pair_comparisons != expected_pair_comparisons:
            raise ValueError("route comparison source references or relations are inconsistent")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("route comparison results cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("route comparison results cannot control production actions")
        if self.result_id != _identity(
            "imagined-route-comparison-result", self._identity_payload()
        ):
            raise ValueError("route comparison result identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "pair_comparisons": [item.snapshot() for item in self.pair_comparisons],
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
class BoundedImaginedRouteComparator:
    """Compare Batch 3 route evaluations pairwise without ranking them."""

    def compare(
        self,
        request: ImaginedRouteComparisonRequest,
    ) -> ImaginedRouteComparisonResult:
        evaluations = request.source_result.evaluations
        pair_comparisons = tuple(
            self._compare_pair(
                request=request,
                left_index=left_index,
                right_index=right_index,
            )
            for left_index in range(len(evaluations))
            for right_index in range(left_index + 1, len(evaluations))
        )
        payload = {
            "request": request.snapshot(),
            "pair_comparisons": [item.snapshot() for item in pair_comparisons],
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedRouteComparisonResult(
            result_id=_identity("imagined-route-comparison-result", payload),
            request=request,
            pair_comparisons=pair_comparisons,
        )

    def _compare_pair(
        self,
        *,
        request: ImaginedRouteComparisonRequest,
        left_index: int,
        right_index: int,
    ) -> ImaginedRoutePairComparison:
        left = request.source_result.evaluations[left_index]
        right = request.source_result.evaluations[right_index]
        keys = _comparison_keys(left, right)
        dimensions = _need_dimensions(request.source_result)
        dimension_comparisons = tuple(
            _compare_dimension(
                left_index=left_index,
                right_index=right_index,
                left=left,
                right=right,
                key=key,
                dimensions=dimensions,
                neutral_tolerance=request.source_result.request.config.neutral_tolerance,
                config=request.config,
            )
            for key in keys
        )
        relation, reasons = _pair_relation(dimension_comparisons)
        payload = {
            "origin": ExperienceOrigin.IMAGINED.value,
            "left_caller_index": left_index,
            "right_caller_index": right_index,
            "left_evaluation_id": left.evaluation_id,
            "right_evaluation_id": right.evaluation_id,
            "left_candidate_id": left.candidate_id,
            "right_candidate_id": right.candidate_id,
            "relation": relation.value,
            "incomparability_reasons": [item.value for item in reasons],
            "dimension_comparisons": [item.snapshot() for item in dimension_comparisons],
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedRoutePairComparison(
            pair_comparison_id=_identity("imagined-route-pair-comparison", payload),
            origin=ExperienceOrigin.IMAGINED,
            left_caller_index=left_index,
            right_caller_index=right_index,
            left_evaluation_id=left.evaluation_id,
            right_evaluation_id=right.evaluation_id,
            left_candidate_id=left.candidate_id,
            right_candidate_id=right.candidate_id,
            relation=relation,
            incomparability_reasons=reasons,
            dimension_comparisons=dimension_comparisons,
        )


def _compare_dimension(
    *,
    left_index: int,
    right_index: int,
    left: ImaginedRouteEvaluation,
    right: ImaginedRouteEvaluation,
    key: tuple[int, str],
    dimensions: dict[str, tuple[float, float]],
    neutral_tolerance: float,
    config: BoundedRouteComparisonConfig,
) -> ImaginedRouteDimensionComparison:
    step_index, effect_code = key
    left_step = _step_at(left, step_index)
    right_step = _step_at(right, step_index)
    left_alignment = None if left_step is None else _alignment_for(left_step, effect_code)
    right_alignment = None if right_step is None else _alignment_for(right_step, effect_code)
    relation, reasons = _dimension_relation(left_alignment, right_alignment, config)
    desired_direction, intensity = dimensions[effect_code]
    payload = {
        "origin": ExperienceOrigin.IMAGINED.value,
        "left_caller_index": left_index,
        "right_caller_index": right_index,
        "left_evaluation_id": left.evaluation_id,
        "right_evaluation_id": right.evaluation_id,
        "step_index": step_index,
        "effect_code": effect_code,
        "left_step_evaluation_id": None if left_step is None else left_step.step_evaluation_id,
        "right_step_evaluation_id": None if right_step is None else right_step.step_evaluation_id,
        "left_alignment_id": None if left_alignment is None else left_alignment.alignment_id,
        "right_alignment_id": None if right_alignment is None else right_alignment.alignment_id,
        "left_direction": None if left_alignment is None else left_alignment.direction.value,
        "right_direction": None if right_alignment is None else right_alignment.direction.value,
        "left_signed_alignment": (
            None if left_alignment is None else left_alignment.signed_alignment
        ),
        "right_signed_alignment": (
            None if right_alignment is None else right_alignment.signed_alignment
        ),
        "left_prediction_confidence": (
            None if left_alignment is None else left_alignment.prediction_confidence
        ),
        "right_prediction_confidence": (
            None if right_alignment is None else right_alignment.prediction_confidence
        ),
        "desired_direction": desired_direction,
        "intensity": intensity,
        "neutral_tolerance": neutral_tolerance,
        "relation": relation.value,
        "incomparability_reasons": [item.value for item in reasons],
        "factual_confidence_change": 0.0,
        "mastery_change": 0.0,
        "competence_change": 0.0,
        "growth_pressure_change": 0.0,
        "replay_evidence_change": 0.0,
        "real_observation_change": 0.0,
        "has_action_selection_authority": False,
        "has_production_action_authority": False,
    }
    return ImaginedRouteDimensionComparison(
        dimension_comparison_id=_identity("imagined-route-dimension-comparison", payload),
        origin=ExperienceOrigin.IMAGINED,
        left_caller_index=left_index,
        right_caller_index=right_index,
        left_evaluation_id=left.evaluation_id,
        right_evaluation_id=right.evaluation_id,
        step_index=step_index,
        effect_code=effect_code,
        left_step_evaluation_id=None if left_step is None else left_step.step_evaluation_id,
        right_step_evaluation_id=None if right_step is None else right_step.step_evaluation_id,
        left_alignment_id=None if left_alignment is None else left_alignment.alignment_id,
        right_alignment_id=None if right_alignment is None else right_alignment.alignment_id,
        left_direction=None if left_alignment is None else left_alignment.direction,
        right_direction=None if right_alignment is None else right_alignment.direction,
        left_signed_alignment=None if left_alignment is None else left_alignment.signed_alignment,
        right_signed_alignment=(
            None if right_alignment is None else right_alignment.signed_alignment
        ),
        left_prediction_confidence=(
            None if left_alignment is None else left_alignment.prediction_confidence
        ),
        right_prediction_confidence=(
            None if right_alignment is None else right_alignment.prediction_confidence
        ),
        desired_direction=desired_direction,
        intensity=intensity,
        neutral_tolerance=neutral_tolerance,
        relation=relation,
        incomparability_reasons=reasons,
    )


def _dimension_relation(
    left: ImaginedEffectAlignment | None,
    right: ImaginedEffectAlignment | None,
    config: BoundedRouteComparisonConfig,
) -> tuple[ImaginedRouteDimensionRelation, tuple[ImaginedRouteIncomparabilityReason, ...]]:
    reasons: set[ImaginedRouteIncomparabilityReason] = set()
    if left is None or right is None:
        reasons.add(ImaginedRouteIncomparabilityReason.DIFFERENT_ROUTE_DEPTH)
        return ImaginedRouteDimensionRelation.UNKNOWN, _sorted_reasons(reasons)
    if (
        left.direction is ImaginedAlignmentDirection.UNKNOWN
        or right.direction is ImaginedAlignmentDirection.UNKNOWN
    ):
        reasons.add(ImaginedRouteIncomparabilityReason.UNKNOWN_ALIGNMENT)
    if (
        left.direction is not ImaginedAlignmentDirection.UNKNOWN
        and left.prediction_confidence <= config.confidence_floor
    ) or (
        right.direction is not ImaginedAlignmentDirection.UNKNOWN
        and right.prediction_confidence <= config.confidence_floor
    ):
        reasons.add(ImaginedRouteIncomparabilityReason.LOW_CONFIDENCE)
    if reasons:
        return ImaginedRouteDimensionRelation.UNKNOWN, _sorted_reasons(reasons)
    if (
        left.direction is ImaginedAlignmentDirection.NEUTRAL
        and right.direction is ImaginedAlignmentDirection.NEUTRAL
    ):
        return ImaginedRouteDimensionRelation.EQUIVALENT, ()
    left_order = _direction_order(left.direction)
    right_order = _direction_order(right.direction)
    if left_order > right_order:
        return ImaginedRouteDimensionRelation.LEFT_BETTER, ()
    if right_order > left_order:
        return ImaginedRouteDimensionRelation.RIGHT_BETTER, ()
    if left.signed_alignment is None or right.signed_alignment is None:
        raise ValueError("known non-neutral alignment lacks signed alignment")
    difference = left.signed_alignment - right.signed_alignment
    if abs(difference) <= config.comparison_epsilon:
        return ImaginedRouteDimensionRelation.EQUIVALENT, ()
    if difference > 0.0:
        return ImaginedRouteDimensionRelation.LEFT_BETTER, ()
    return ImaginedRouteDimensionRelation.RIGHT_BETTER, ()


def _pair_relation(
    dimensions: tuple[ImaginedRouteDimensionComparison, ...],
) -> tuple[ImaginedRoutePairRelation, tuple[ImaginedRouteIncomparabilityReason, ...]]:
    reasons = {reason for item in dimensions for reason in item.incomparability_reasons}
    if any(item.relation is ImaginedRouteDimensionRelation.UNKNOWN for item in dimensions):
        return ImaginedRoutePairRelation.INCOMPARABLE, _sorted_reasons(reasons)
    left_better = any(
        item.relation is ImaginedRouteDimensionRelation.LEFT_BETTER for item in dimensions
    )
    right_better = any(
        item.relation is ImaginedRouteDimensionRelation.RIGHT_BETTER for item in dimensions
    )
    if left_better and right_better:
        reasons.add(ImaginedRouteIncomparabilityReason.CONFLICTING_TRADEOFF)
        return ImaginedRoutePairRelation.INCOMPARABLE, _sorted_reasons(reasons)
    if left_better:
        return ImaginedRoutePairRelation.LEFT_DOMINATES_RIGHT, ()
    if right_better:
        return ImaginedRoutePairRelation.RIGHT_DOMINATES_LEFT, ()
    return ImaginedRoutePairRelation.ALIGNMENT_EQUIVALENT, ()


def _need_dimensions(result: ImaginedRouteEvaluationResult) -> dict[str, tuple[float, float]]:
    return {
        dimension.effect_code: (dimension.desired_direction, dimension.intensity)
        for dimension in sorted(result.request.need.dimensions, key=lambda item: item.effect_code)
    }


def _required_dimension_comparison_count(
    evaluations: tuple[ImaginedRouteEvaluation, ...],
) -> int:
    total = 0
    for left_index in range(len(evaluations)):
        for right_index in range(left_index + 1, len(evaluations)):
            total += len(_comparison_keys(evaluations[left_index], evaluations[right_index]))
    return total


def _comparison_keys(
    left: ImaginedRouteEvaluation,
    right: ImaginedRouteEvaluation,
) -> tuple[tuple[int, str], ...]:
    keys = {
        (step.step_index, alignment.effect_code)
        for evaluation in (left, right)
        for step in evaluation.step_evaluations
        for alignment in step.alignments
    }
    return tuple(sorted(keys))


def _step_at(
    evaluation: ImaginedRouteEvaluation,
    step_index: int,
) -> ImaginedRouteStepEvaluation | None:
    for step in evaluation.step_evaluations:
        if step.step_index == step_index:
            return step
    return None


def _alignment_for(
    step: ImaginedRouteStepEvaluation,
    effect_code: str,
) -> ImaginedEffectAlignment | None:
    for alignment in step.alignments:
        if alignment.effect_code == effect_code:
            return alignment
    return None


def _direction_order(direction: ImaginedAlignmentDirection) -> int:
    if direction is ImaginedAlignmentDirection.WORSENING:
        return 0
    if direction is ImaginedAlignmentDirection.NEUTRAL:
        return 1
    if direction is ImaginedAlignmentDirection.IMPROVING:
        return 2
    raise ValueError("unknown alignment has no comparable direction order")


def _sorted_reasons(
    reasons: set[ImaginedRouteIncomparabilityReason],
) -> tuple[ImaginedRouteIncomparabilityReason, ...]:
    return tuple(sorted(reasons, key=lambda item: item.value))


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


def _validate_index(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_sorted_unique_enum_values(
    name: str,
    values: Sequence[ImaginedRouteIncomparabilityReason],
) -> None:
    serialized = tuple(value.value for value in values)
    if serialized != tuple(sorted(serialized)):
        raise ValueError(f"{name} must be sorted")
    if len(serialized) != len(set(serialized)):
        raise ValueError(f"{name} must be unique")


def _validate_dimension_side_shape(
    *,
    side: str,
    step_evaluation_id: str | None,
    alignment_id: str | None,
    direction: ImaginedAlignmentDirection | None,
    signed_alignment: float | None,
    prediction_confidence: float | None,
) -> None:
    if step_evaluation_id is None:
        if any(
            value is not None
            for value in (
                alignment_id,
                direction,
                signed_alignment,
                prediction_confidence,
            )
        ):
            raise ValueError(f"missing {side} step cannot expose alignment evidence")
        return
    if alignment_id is None or direction is None or prediction_confidence is None:
        raise ValueError(f"present {side} step requires complete alignment identity")
    if direction is ImaginedAlignmentDirection.UNKNOWN:
        if signed_alignment is not None or prediction_confidence != 0.0:
            raise ValueError(f"unknown {side} alignment cannot carry predicted evidence")
        return
    if signed_alignment is None:
        raise ValueError(f"known {side} alignment requires signed alignment")


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
    "BoundedImaginedRouteComparator",
    "BoundedRouteComparisonConfig",
    "ImaginedRouteComparisonRequest",
    "ImaginedRouteComparisonResult",
    "ImaginedRouteDimensionComparison",
    "ImaginedRouteDimensionRelation",
    "ImaginedRouteIncomparabilityReason",
    "ImaginedRoutePairComparison",
    "ImaginedRoutePairRelation",
]
