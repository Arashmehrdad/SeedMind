"""Deterministic uncertainty audit over imagined route comparisons."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.bounded_imagination_comparison import (
    ImaginedRouteComparisonResult,
    ImaginedRouteDimensionRelation,
    ImaginedRouteIncomparabilityReason,
    ImaginedRoutePairComparison,
    ImaginedRoutePairRelation,
)
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin


class ImaginedComparisonIssueScope(StrEnum):
    """The exact comparison level at which uncertainty remains."""

    DIMENSION = "dimension"
    PAIR = "pair"


@dataclass(frozen=True, slots=True)
class BoundedComparisonUncertaintyConfig:
    """Finite limits for non-authoritative uncertainty inspection."""

    maximum_pairs: int = 28
    maximum_dimension_issues: int = 1344
    maximum_pair_issues: int = 28
    maximum_total_issues: int = 1372
    maximum_reasons_per_issue: int = 4

    def __post_init__(self) -> None:
        for name, value in (
            ("maximum_pairs", self.maximum_pairs),
            ("maximum_dimension_issues", self.maximum_dimension_issues),
            ("maximum_pair_issues", self.maximum_pair_issues),
            ("maximum_total_issues", self.maximum_total_issues),
            ("maximum_reasons_per_issue", self.maximum_reasons_per_issue),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")

    def snapshot(self) -> dict[str, object]:
        return {
            "maximum_pairs": self.maximum_pairs,
            "maximum_dimension_issues": self.maximum_dimension_issues,
            "maximum_pair_issues": self.maximum_pair_issues,
            "maximum_total_issues": self.maximum_total_issues,
            "maximum_reasons_per_issue": self.maximum_reasons_per_issue,
        }


@dataclass(frozen=True, slots=True)
class ImaginedComparisonUncertaintyRequest:
    """One complete Batch 4 comparison result to inspect without action authority."""

    source_result: ImaginedRouteComparisonResult
    config: BoundedComparisonUncertaintyConfig = field(
        default_factory=BoundedComparisonUncertaintyConfig
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
        _revalidate_source_result(self.source_result)
        if len(self.source_result.pair_comparisons) > self.config.maximum_pairs:
            raise ValueError("pair bound exceeded")
        dimension_issues = 0
        pair_issues = 0
        for pair in self.source_result.pair_comparisons:
            unknown_dimensions = tuple(
                item
                for item in pair.dimension_comparisons
                if item.relation is ImaginedRouteDimensionRelation.UNKNOWN
            )
            has_tradeoff = (
                ImaginedRouteIncomparabilityReason.CONFLICTING_TRADEOFF
                in pair.incomparability_reasons
            )
            dimension_issues += len(unknown_dimensions)
            if has_tradeoff:
                pair_issues += 1
            if pair.relation is ImaginedRoutePairRelation.INCOMPARABLE:
                if not unknown_dimensions and not has_tradeoff:
                    raise ValueError("incomparable source pair has no auditable reason")
            elif unknown_dimensions or pair.incomparability_reasons:
                raise ValueError("comparable source pair cannot carry uncertainty")
            for dimension in unknown_dimensions:
                if len(dimension.incomparability_reasons) > self.config.maximum_reasons_per_issue:
                    raise ValueError("reason bound exceeded")
        if dimension_issues > self.config.maximum_dimension_issues:
            raise ValueError("dimension-issue bound exceeded")
        if pair_issues > self.config.maximum_pair_issues:
            raise ValueError("pair-issue bound exceeded")
        if dimension_issues + pair_issues > self.config.maximum_total_issues:
            raise ValueError("total-issue bound exceeded")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("uncertainty audit requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("uncertainty audit requests cannot control production actions")

    @property
    def request_id(self) -> str:
        return _identity("imagined-comparison-uncertainty-request", self._identity_payload())

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


@dataclass(frozen=True, slots=True)
class ImaginedComparisonUncertaintyIssue:
    """One exact unresolved comparison issue with no proposed action."""

    issue_id: str
    origin: ExperienceOrigin
    scope: ImaginedComparisonIssueScope
    pair_comparison_id: str
    left_caller_index: int
    right_caller_index: int
    left_evaluation_id: str
    right_evaluation_id: str
    left_candidate_id: str
    right_candidate_id: str
    dimension_comparison_id: str | None
    step_index: int | None
    effect_code: str | None
    reasons: tuple[ImaginedRouteIncomparabilityReason, ...]
    related_dimension_comparison_ids: tuple[str, ...]
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("issue_id", self.issue_id)
        _validate_ascii_code("pair_comparison_id", self.pair_comparison_id)
        _validate_index("left_caller_index", self.left_caller_index)
        _validate_index("right_caller_index", self.right_caller_index)
        if self.left_caller_index >= self.right_caller_index:
            raise ValueError("uncertainty issue indexes must be caller ordered")
        _validate_ascii_code("left_evaluation_id", self.left_evaluation_id)
        _validate_ascii_code("right_evaluation_id", self.right_evaluation_id)
        _validate_ascii_code("left_candidate_id", self.left_candidate_id)
        _validate_ascii_code("right_candidate_id", self.right_candidate_id)
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("comparison uncertainty issues require imagined origin")
        _validate_sorted_unique_reasons("reasons", self.reasons)
        if not self.reasons:
            raise ValueError("comparison uncertainty issue requires a reason")
        _validate_unique_ascii_codes(
            "related_dimension_comparison_ids",
            self.related_dimension_comparison_ids,
        )
        if self.scope is ImaginedComparisonIssueScope.DIMENSION:
            if self.dimension_comparison_id is None:
                raise ValueError("dimension uncertainty requires a dimension comparison ID")
            _validate_ascii_code("dimension_comparison_id", self.dimension_comparison_id)
            if self.step_index is None:
                raise ValueError("dimension uncertainty requires a step index")
            _validate_index("step_index", self.step_index)
            if self.effect_code is None:
                raise ValueError("dimension uncertainty requires an effect code")
            _validate_ascii_code("effect_code", self.effect_code)
            if self.related_dimension_comparison_ids:
                raise ValueError("dimension uncertainty cannot carry related dimensions")
            if ImaginedRouteIncomparabilityReason.CONFLICTING_TRADEOFF in self.reasons:
                raise ValueError("conflicting trade-off is a pair-level issue")
        elif self.scope is ImaginedComparisonIssueScope.PAIR:
            if any(
                value is not None
                for value in (
                    self.dimension_comparison_id,
                    self.step_index,
                    self.effect_code,
                )
            ):
                raise ValueError("pair uncertainty cannot claim one dimension")
            if self.reasons != (ImaginedRouteIncomparabilityReason.CONFLICTING_TRADEOFF,):
                raise ValueError("pair uncertainty requires conflicting trade-off")
            if not self.related_dimension_comparison_ids:
                raise ValueError("pair trade-off requires related dimensions")
        else:
            raise ValueError("unsupported comparison uncertainty scope")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("comparison uncertainty issues cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("comparison uncertainty issues cannot control production actions")
        if self.issue_id != _identity(
            "imagined-comparison-uncertainty-issue",
            self._identity_payload(),
        ):
            raise ValueError("comparison uncertainty issue identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"issue_id": self.issue_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "scope": self.scope.value,
            "pair_comparison_id": self.pair_comparison_id,
            "left_caller_index": self.left_caller_index,
            "right_caller_index": self.right_caller_index,
            "left_evaluation_id": self.left_evaluation_id,
            "right_evaluation_id": self.right_evaluation_id,
            "left_candidate_id": self.left_candidate_id,
            "right_candidate_id": self.right_candidate_id,
            "dimension_comparison_id": self.dimension_comparison_id,
            "step_index": self.step_index,
            "effect_code": self.effect_code,
            "reasons": [item.value for item in self.reasons],
            "related_dimension_comparison_ids": list(self.related_dimension_comparison_ids),
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
class ImaginedComparisonUncertaintyResult:
    """Ordered uncertainty issues with no experiment or action proposal."""

    result_id: str
    request: ImaginedComparisonUncertaintyRequest
    issues: tuple[ImaginedComparisonUncertaintyIssue, ...]
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
        expected = BoundedImaginedComparisonUncertaintyAuditor()._issues_for(
            self.request.source_result
        )
        if self.issues != expected:
            raise ValueError("comparison uncertainty issues are inconsistent with source")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("uncertainty audit results cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("uncertainty audit results cannot control production actions")
        if self.result_id != _identity(
            "imagined-comparison-uncertainty-result",
            self._identity_payload(),
        ):
            raise ValueError("comparison uncertainty result identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "issues": [item.snapshot() for item in self.issues],
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
class BoundedImaginedComparisonUncertaintyAuditor:
    """Expose unresolved comparison evidence without proposing what to do."""

    def audit(
        self,
        request: ImaginedComparisonUncertaintyRequest,
    ) -> ImaginedComparisonUncertaintyResult:
        issues = self._issues_for(request.source_result)
        payload = {
            "request": request.snapshot(),
            "issues": [item.snapshot() for item in issues],
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedComparisonUncertaintyResult(
            result_id=_identity("imagined-comparison-uncertainty-result", payload),
            request=request,
            issues=issues,
        )

    def _issues_for(
        self,
        source_result: ImaginedRouteComparisonResult,
    ) -> tuple[ImaginedComparisonUncertaintyIssue, ...]:
        issues: list[ImaginedComparisonUncertaintyIssue] = []
        for pair in source_result.pair_comparisons:
            issues.extend(self._dimension_issues(pair))
            if ImaginedRouteIncomparabilityReason.CONFLICTING_TRADEOFF in (
                pair.incomparability_reasons
            ):
                issues.append(self._tradeoff_issue(pair))
        return tuple(issues)

    def _dimension_issues(
        self,
        pair: ImaginedRoutePairComparison,
    ) -> tuple[ImaginedComparisonUncertaintyIssue, ...]:
        issues: list[ImaginedComparisonUncertaintyIssue] = []
        for dimension in pair.dimension_comparisons:
            if dimension.relation is not ImaginedRouteDimensionRelation.UNKNOWN:
                continue
            payload = _issue_payload(
                scope=ImaginedComparisonIssueScope.DIMENSION,
                pair=pair,
                dimension_comparison_id=dimension.dimension_comparison_id,
                step_index=dimension.step_index,
                effect_code=dimension.effect_code,
                reasons=dimension.incomparability_reasons,
                related_dimension_comparison_ids=(),
            )
            issues.append(
                ImaginedComparisonUncertaintyIssue(
                    issue_id=_identity(
                        "imagined-comparison-uncertainty-issue",
                        payload,
                    ),
                    origin=ExperienceOrigin.IMAGINED,
                    scope=ImaginedComparisonIssueScope.DIMENSION,
                    pair_comparison_id=pair.pair_comparison_id,
                    left_caller_index=pair.left_caller_index,
                    right_caller_index=pair.right_caller_index,
                    left_evaluation_id=pair.left_evaluation_id,
                    right_evaluation_id=pair.right_evaluation_id,
                    left_candidate_id=pair.left_candidate_id,
                    right_candidate_id=pair.right_candidate_id,
                    dimension_comparison_id=dimension.dimension_comparison_id,
                    step_index=dimension.step_index,
                    effect_code=dimension.effect_code,
                    reasons=dimension.incomparability_reasons,
                    related_dimension_comparison_ids=(),
                )
            )
        return tuple(issues)

    def _tradeoff_issue(
        self,
        pair: ImaginedRoutePairComparison,
    ) -> ImaginedComparisonUncertaintyIssue:
        related = tuple(
            item.dimension_comparison_id
            for item in pair.dimension_comparisons
            if item.relation
            in (
                ImaginedRouteDimensionRelation.LEFT_BETTER,
                ImaginedRouteDimensionRelation.RIGHT_BETTER,
            )
        )
        reasons = (ImaginedRouteIncomparabilityReason.CONFLICTING_TRADEOFF,)
        payload = _issue_payload(
            scope=ImaginedComparisonIssueScope.PAIR,
            pair=pair,
            dimension_comparison_id=None,
            step_index=None,
            effect_code=None,
            reasons=reasons,
            related_dimension_comparison_ids=related,
        )
        return ImaginedComparisonUncertaintyIssue(
            issue_id=_identity("imagined-comparison-uncertainty-issue", payload),
            origin=ExperienceOrigin.IMAGINED,
            scope=ImaginedComparisonIssueScope.PAIR,
            pair_comparison_id=pair.pair_comparison_id,
            left_caller_index=pair.left_caller_index,
            right_caller_index=pair.right_caller_index,
            left_evaluation_id=pair.left_evaluation_id,
            right_evaluation_id=pair.right_evaluation_id,
            left_candidate_id=pair.left_candidate_id,
            right_candidate_id=pair.right_candidate_id,
            dimension_comparison_id=None,
            step_index=None,
            effect_code=None,
            reasons=reasons,
            related_dimension_comparison_ids=related,
        )


def _issue_payload(
    *,
    scope: ImaginedComparisonIssueScope,
    pair: ImaginedRoutePairComparison,
    dimension_comparison_id: str | None,
    step_index: int | None,
    effect_code: str | None,
    reasons: tuple[ImaginedRouteIncomparabilityReason, ...],
    related_dimension_comparison_ids: tuple[str, ...],
) -> dict[str, object]:
    return {
        "origin": ExperienceOrigin.IMAGINED.value,
        "scope": scope.value,
        "pair_comparison_id": pair.pair_comparison_id,
        "left_caller_index": pair.left_caller_index,
        "right_caller_index": pair.right_caller_index,
        "left_evaluation_id": pair.left_evaluation_id,
        "right_evaluation_id": pair.right_evaluation_id,
        "left_candidate_id": pair.left_candidate_id,
        "right_candidate_id": pair.right_candidate_id,
        "dimension_comparison_id": dimension_comparison_id,
        "step_index": step_index,
        "effect_code": effect_code,
        "reasons": [item.value for item in reasons],
        "related_dimension_comparison_ids": list(related_dimension_comparison_ids),
        "factual_confidence_change": 0.0,
        "mastery_change": 0.0,
        "competence_change": 0.0,
        "growth_pressure_change": 0.0,
        "replay_evidence_change": 0.0,
        "real_observation_change": 0.0,
        "has_action_selection_authority": False,
        "has_production_action_authority": False,
    }


def _revalidate_source_result(source: ImaginedRouteComparisonResult) -> None:
    ImaginedRouteComparisonResult(
        result_id=source.result_id,
        request=source.request,
        pair_comparisons=source.pair_comparisons,
        factual_confidence_change=source.factual_confidence_change,
        mastery_change=source.mastery_change,
        competence_change=source.competence_change,
        growth_pressure_change=source.growth_pressure_change,
        replay_evidence_change=source.replay_evidence_change,
        real_observation_change=source.real_observation_change,
        has_action_selection_authority=source.has_action_selection_authority,
        has_production_action_authority=source.has_production_action_authority,
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


def _validate_ascii_code(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError(f"{name} must be a non-empty ASCII string")


def _validate_index(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_sorted_unique_reasons(
    name: str,
    values: Sequence[ImaginedRouteIncomparabilityReason],
) -> None:
    serialized = tuple(value.value for value in values)
    if serialized != tuple(sorted(serialized)):
        raise ValueError(f"{name} must be sorted")
    if len(serialized) != len(set(serialized)):
        raise ValueError(f"{name} must be unique")


def _validate_unique_ascii_codes(name: str, values: Sequence[str]) -> None:
    if any(not isinstance(value, str) or not value or not value.isascii() for value in values):
        raise ValueError(f"{name} must contain non-empty ASCII strings")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique")


def _validate_zero_delta(name: str, value: float) -> None:
    if not isinstance(value, float) or not isfinite(value) or value != 0.0:
        raise ValueError(f"{name} must remain exactly zero")


__all__ = [
    "BoundedComparisonUncertaintyConfig",
    "BoundedImaginedComparisonUncertaintyAuditor",
    "ImaginedComparisonIssueScope",
    "ImaginedComparisonUncertaintyIssue",
    "ImaginedComparisonUncertaintyRequest",
    "ImaginedComparisonUncertaintyResult",
]
