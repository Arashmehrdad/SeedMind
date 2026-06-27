"""Pure retention-gated consolidation eligibility contracts for NDNRA."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from typing import TypeGuard

from seedmind.research.ndnra.contextual_memory import (
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    LessonIdentity,
    MasteryProfile,
)


class ConsolidationRejectionReason(StrEnum):
    """Explicit reasons why a contextual lesson cannot consolidate yet."""

    NOT_BROADLY_MASTERED = "not_broadly_mastered"
    INSUFFICIENT_EFFECTIVE_SUPPORT = "insufficient_effective_support"
    INSUFFICIENT_CONTEXT_DIVERSITY = "insufficient_context_diversity"
    INSUFFICIENT_ROUTE_DIVERSITY = "insufficient_route_diversity"
    LOW_CAUSAL_CONSISTENCY = "low_causal_consistency"
    LOW_TRANSFER_SUCCESS = "low_transfer_success"
    LOW_MASTERY_SCORE = "low_mastery_score"
    UNRESOLVED_CONTRADICTIONS = "unresolved_contradictions"
    MISSING_SOURCE_EVENTS = "missing_source_events"
    DUPLICATE_SOURCE_EVENTS = "duplicate_source_events"
    MISSING_ASSEMBLIES = "missing_assemblies"
    MISSING_ROUTES = "missing_routes"
    INVALID_STABILITY_REQUEST = "invalid_stability_request"
    INVALID_PLASTICITY_REQUEST = "invalid_plasticity_request"


@dataclass(frozen=True, slots=True)
class ConsolidationCandidate:
    """Immutable proposal that does not apply any neural-state change."""

    candidate_id: str
    lesson_identity: LessonIdentity
    source_event_ids: tuple[str, ...]
    assembly_ids: tuple[str, ...]
    route_ids: tuple[str, ...]
    mastery_snapshot: MasteryProfile
    requested_stability_increment: float
    requested_plasticity_reduction: float

    def __post_init__(self) -> None:
        _validate_code("candidate_id", self.candidate_id)
        for name, values in (
            ("source_event_ids", self.source_event_ids),
            ("assembly_ids", self.assembly_ids),
            ("route_ids", self.route_ids),
        ):
            _validate_sorted_unique_codes(name, values)
            if not values:
                raise ValueError(f"{name} must not be empty")
        _validate_positive_unit(
            "requested_stability_increment",
            self.requested_stability_increment,
        )
        _validate_positive_unit(
            "requested_plasticity_reduction",
            self.requested_plasticity_reduction,
        )

    def snapshot(self) -> dict[str, object]:
        """Return a deterministic inspectable proposal snapshot."""
        return {
            "candidate_id": self.candidate_id,
            "lesson_identity": {
                "need_code": self.lesson_identity.need_code,
                "effect_code": self.lesson_identity.effect_code,
                "desired_direction": self.lesson_identity.desired_direction,
            },
            "source_event_ids": list(self.source_event_ids),
            "assembly_ids": list(self.assembly_ids),
            "route_ids": list(self.route_ids),
            "mastery_snapshot": self.mastery_snapshot.snapshot(),
            "requested_stability_increment": self.requested_stability_increment,
            "requested_plasticity_reduction": self.requested_plasticity_reduction,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationEligibilityPolicy:
    """Typed thresholds for pure consolidation-candidate eligibility."""

    minimum_effective_support: float = 3.0
    minimum_context_count: int = 3
    minimum_route_count: int = 2
    minimum_causal_consistency: float = 0.75
    minimum_transfer_success: float = 0.50
    minimum_mastery_score: float = 0.75
    maximum_unresolved_contradictions: int = 0
    minimum_source_event_count: int = 3
    maximum_stability_increment: float = 0.20
    maximum_plasticity_reduction: float = 0.20

    def __post_init__(self) -> None:
        if not _is_finite_number(self.minimum_effective_support):
            raise ValueError("minimum_effective_support must be finite")
        if self.minimum_effective_support <= 0.0:
            raise ValueError("minimum_effective_support must be positive")
        for count_name, count_value in (
            ("minimum_context_count", self.minimum_context_count),
            ("minimum_route_count", self.minimum_route_count),
            ("minimum_source_event_count", self.minimum_source_event_count),
        ):
            if isinstance(count_value, bool) or not isinstance(count_value, int) or count_value < 1:
                raise ValueError(f"{count_name} must be a positive integer")
        if (
            isinstance(self.maximum_unresolved_contradictions, bool)
            or not isinstance(self.maximum_unresolved_contradictions, int)
            or self.maximum_unresolved_contradictions < 0
        ):
            raise ValueError("maximum_unresolved_contradictions must not be negative")
        for threshold_name, threshold_value in (
            ("minimum_causal_consistency", self.minimum_causal_consistency),
            ("minimum_transfer_success", self.minimum_transfer_success),
            ("minimum_mastery_score", self.minimum_mastery_score),
        ):
            _validate_unit(threshold_name, threshold_value)
        _validate_positive_unit(
            "maximum_stability_increment",
            self.maximum_stability_increment,
        )
        _validate_positive_unit(
            "maximum_plasticity_reduction",
            self.maximum_plasticity_reduction,
        )

    def evaluate(
        self,
        *,
        ledger: ContextualExperienceLedger,
        lesson: LessonIdentity,
        mastery_profile: MasteryProfile,
        requested_stability_increment: float = 0.10,
        requested_plasticity_reduction: float = 0.10,
        available_assembly_ids: Iterable[str] | None = None,
        available_route_ids: Iterable[str] | None = None,
    ) -> ConsolidationEligibility:
        """Evaluate eligibility without mutating evidence or neural state."""
        reasons: list[ConsolidationRejectionReason] = []
        current_profile = ledger.mastery_profile(lesson)
        _append_profile_rejections(reasons, mastery_profile, self)
        _append_profile_rejections(reasons, current_profile, self)

        supplied_source_ids = _validated_source_ids(mastery_profile, reasons)
        current_source_ids = current_profile.source_event_ids
        if len(current_source_ids) < self.minimum_source_event_count:
            _add_reason(reasons, ConsolidationRejectionReason.MISSING_SOURCE_EVENTS)
        if supplied_source_ids and set(supplied_source_ids) != set(current_source_ids):
            _add_reason(reasons, ConsolidationRejectionReason.MISSING_SOURCE_EVENTS)

        resolved_traces = _resolve_supporting_traces(
            ledger=ledger,
            lesson=lesson,
            source_event_ids=supplied_source_ids,
            reasons=reasons,
        )
        source_resolution_complete = bool(supplied_source_ids) and (
            len(resolved_traces) == len(supplied_source_ids)
            and len(supplied_source_ids) == len(set(supplied_source_ids))
            and set(supplied_source_ids) == set(current_source_ids)
        )

        assembly_ids: tuple[str, ...] = ()
        route_ids: tuple[str, ...] = ()
        if source_resolution_complete:
            assembly_ids = tuple(sorted({trace.assembly_id for trace in resolved_traces}))
            route_ids = tuple(sorted({trace.route_id for trace in resolved_traces}))
            if not assembly_ids:
                _add_reason(reasons, ConsolidationRejectionReason.MISSING_ASSEMBLIES)
            if not route_ids:
                _add_reason(reasons, ConsolidationRejectionReason.MISSING_ROUTES)

            available_assemblies = _available_codes(
                "available_assembly_ids",
                available_assembly_ids,
                assembly_ids,
            )
            available_routes = _available_codes(
                "available_route_ids",
                available_route_ids,
                route_ids,
            )
            if not set(assembly_ids).issubset(available_assemblies):
                _add_reason(reasons, ConsolidationRejectionReason.MISSING_ASSEMBLIES)
            if not set(route_ids).issubset(available_routes):
                _add_reason(reasons, ConsolidationRejectionReason.MISSING_ROUTES)

        if not _valid_requested_change(
            requested_stability_increment,
            self.maximum_stability_increment,
        ):
            _add_reason(reasons, ConsolidationRejectionReason.INVALID_STABILITY_REQUEST)
        if not _valid_requested_change(
            requested_plasticity_reduction,
            self.maximum_plasticity_reduction,
        ):
            _add_reason(reasons, ConsolidationRejectionReason.INVALID_PLASTICITY_REQUEST)

        ordered_reasons = tuple(
            reason for reason in ConsolidationRejectionReason if reason in reasons
        )
        if ordered_reasons:
            return ConsolidationEligibility(
                eligible=False,
                reasons=ordered_reasons,
                candidate=None,
                evaluated_lesson=lesson,
                mastery_snapshot=current_profile,
                policy=self,
            )

        source_event_ids = tuple(sorted(current_source_ids))
        candidate = ConsolidationCandidate(
            candidate_id=_candidate_id(
                lesson=lesson,
                source_event_ids=source_event_ids,
                assembly_ids=assembly_ids,
                route_ids=route_ids,
                mastery_profile=current_profile,
                requested_stability_increment=requested_stability_increment,
                requested_plasticity_reduction=requested_plasticity_reduction,
            ),
            lesson_identity=lesson,
            source_event_ids=source_event_ids,
            assembly_ids=assembly_ids,
            route_ids=route_ids,
            mastery_snapshot=current_profile,
            requested_stability_increment=requested_stability_increment,
            requested_plasticity_reduction=requested_plasticity_reduction,
        )
        return ConsolidationEligibility(
            eligible=True,
            reasons=(),
            candidate=candidate,
            evaluated_lesson=lesson,
            mastery_snapshot=current_profile,
            policy=self,
        )


@dataclass(frozen=True, slots=True)
class ConsolidationEligibility:
    """Pure eligibility result with all rejection reasons preserved."""

    eligible: bool
    reasons: tuple[ConsolidationRejectionReason, ...]
    candidate: ConsolidationCandidate | None
    evaluated_lesson: LessonIdentity
    mastery_snapshot: MasteryProfile
    policy: ConsolidationEligibilityPolicy

    def __post_init__(self) -> None:
        if self.eligible:
            if self.reasons or self.candidate is None:
                raise ValueError("eligible results require one candidate and no reasons")
        elif not self.reasons or self.candidate is not None:
            raise ValueError("ineligible results require reasons and no candidate")
        if len(self.reasons) != len(set(self.reasons)):
            raise ValueError("eligibility reasons must be unique")


def _append_profile_rejections(
    reasons: list[ConsolidationRejectionReason],
    profile: MasteryProfile,
    policy: ConsolidationEligibilityPolicy,
) -> None:
    if profile.broad_mastery is not True:
        _add_reason(reasons, ConsolidationRejectionReason.NOT_BROADLY_MASTERED)
    if not _meets_minimum(profile.effective_support, policy.minimum_effective_support):
        _add_reason(reasons, ConsolidationRejectionReason.INSUFFICIENT_EFFECTIVE_SUPPORT)
    if not _count_meets_minimum(profile.unique_context_count, policy.minimum_context_count):
        _add_reason(reasons, ConsolidationRejectionReason.INSUFFICIENT_CONTEXT_DIVERSITY)
    if not _count_meets_minimum(profile.unique_route_count, policy.minimum_route_count):
        _add_reason(reasons, ConsolidationRejectionReason.INSUFFICIENT_ROUTE_DIVERSITY)
    if not _unit_meets_minimum(
        profile.causal_consistency,
        policy.minimum_causal_consistency,
    ):
        _add_reason(reasons, ConsolidationRejectionReason.LOW_CAUSAL_CONSISTENCY)
    if not _unit_meets_minimum(profile.transfer_success, policy.minimum_transfer_success):
        _add_reason(reasons, ConsolidationRejectionReason.LOW_TRANSFER_SUCCESS)
    if not _unit_meets_minimum(profile.mastery_score, policy.minimum_mastery_score):
        _add_reason(reasons, ConsolidationRejectionReason.LOW_MASTERY_SCORE)
    contradiction_count = profile.contradiction_count
    if (
        isinstance(contradiction_count, bool)
        or not isinstance(contradiction_count, int)
        or contradiction_count < 0
        or contradiction_count > policy.maximum_unresolved_contradictions
    ):
        _add_reason(reasons, ConsolidationRejectionReason.UNRESOLVED_CONTRADICTIONS)


def _validated_source_ids(
    profile: MasteryProfile,
    reasons: list[ConsolidationRejectionReason],
) -> tuple[str, ...]:
    source_event_ids = profile.source_event_ids
    if not isinstance(source_event_ids, tuple) or not source_event_ids:
        _add_reason(reasons, ConsolidationRejectionReason.MISSING_SOURCE_EVENTS)
        return ()
    if any(not _is_valid_code(event_id) for event_id in source_event_ids):
        _add_reason(reasons, ConsolidationRejectionReason.MISSING_SOURCE_EVENTS)
        return ()
    if len(source_event_ids) != len(set(source_event_ids)):
        _add_reason(reasons, ConsolidationRejectionReason.DUPLICATE_SOURCE_EVENTS)
    return source_event_ids


def _resolve_supporting_traces(
    *,
    ledger: ContextualExperienceLedger,
    lesson: LessonIdentity,
    source_event_ids: tuple[str, ...],
    reasons: list[ConsolidationRejectionReason],
) -> tuple[ContextualExperienceTrace, ...]:
    traces: list[ContextualExperienceTrace] = []
    for event_id in source_event_ids:
        try:
            trace = ledger.trace(event_id)
        except ValueError:
            _add_reason(reasons, ConsolidationRejectionReason.MISSING_SOURCE_EVENTS)
            continue
        if trace.context.active_need_code != lesson.need_code or not any(
            effect.effect_code == lesson.effect_code for effect in trace.observed_effects
        ):
            _add_reason(reasons, ConsolidationRejectionReason.MISSING_SOURCE_EVENTS)
            continue
        traces.append(trace)
    return tuple(traces)


def _available_codes(
    name: str,
    supplied: Iterable[str] | None,
    default: tuple[str, ...],
) -> frozenset[str]:
    if supplied is None:
        return frozenset(default)
    values = tuple(supplied)
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
    for value in values:
        _validate_code(name, value)
    return frozenset(values)


def _candidate_id(
    *,
    lesson: LessonIdentity,
    source_event_ids: tuple[str, ...],
    assembly_ids: tuple[str, ...],
    route_ids: tuple[str, ...],
    mastery_profile: MasteryProfile,
    requested_stability_increment: float,
    requested_plasticity_reduction: float,
) -> str:
    payload = {
        "lesson": {
            "need_code": lesson.need_code,
            "effect_code": lesson.effect_code,
            "desired_direction": lesson.desired_direction,
        },
        "source_event_ids": list(source_event_ids),
        "assembly_ids": list(assembly_ids),
        "route_ids": list(route_ids),
        "mastery_profile": mastery_profile.snapshot(),
        "requested_stability_increment": requested_stability_increment,
        "requested_plasticity_reduction": requested_plasticity_reduction,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"consolidation:{hashlib.sha256(canonical).hexdigest()}"


def _add_reason(
    reasons: list[ConsolidationRejectionReason],
    reason: ConsolidationRejectionReason,
) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _valid_requested_change(value: object, maximum: float) -> bool:
    return _is_finite_number(value) and 0.0 < float(value) <= maximum


def _meets_minimum(value: object, minimum: float) -> bool:
    return _is_finite_number(value) and float(value) >= minimum


def _unit_meets_minimum(value: object, minimum: float) -> bool:
    return _is_finite_number(value) and 0.0 <= float(value) <= 1.0 and float(value) >= minimum


def _count_meets_minimum(value: object, minimum: int) -> bool:
    return not isinstance(value, bool) and isinstance(value, int) and value >= minimum


def _is_finite_number(value: object) -> TypeGuard[int | float]:
    return not isinstance(value, bool) and isinstance(value, int | float) and isfinite(value)


def _validate_unit(name: str, value: object) -> None:
    if not _is_finite_number(value) or not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{name} must be finite and between zero and one")


def _validate_positive_unit(name: str, value: object) -> None:
    if not _is_finite_number(value) or not 0.0 < float(value) <= 1.0:
        raise ValueError(f"{name} must be finite, positive, and at most one")


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
    for value in values:
        _validate_code(name, value)


def _validate_code(name: str, value: str) -> None:
    if not _is_valid_code(value):
        raise ValueError(f"{name} must contain non-empty ASCII identities")


def _is_valid_code(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip()) and value.isascii()
