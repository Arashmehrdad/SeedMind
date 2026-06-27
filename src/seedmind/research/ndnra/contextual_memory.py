"""Contextual experience traces and bounded mastery evidence for NDNRA."""

from __future__ import annotations

from collections import defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from statistics import fmean

from seedmind.research.ndnra.effects import EffectObservation


class ContextualRecordCode(StrEnum):
    """Outcome of recording one contextual experience trace."""

    ACCEPTED_INDEPENDENT = "accepted_independent"
    ACCEPTED_CORRELATED = "accepted_correlated"
    EXACT_DUPLICATE_IGNORED = "exact_duplicate_ignored"


@dataclass(frozen=True, slots=True)
class EventIdentity:
    """Stable occurrence identity used only for exact-event deduplication."""

    source_code: str
    episode_id: str
    step_id: int

    def __post_init__(self) -> None:
        _validate_code("source_code", self.source_code)
        _validate_code("episode_id", self.episode_id)
        if self.step_id < 0:
            raise ValueError("step_id must not be negative")

    @property
    def key(self) -> str:
        """Return a collision-safe length-prefixed identity key."""
        return (
            f"{len(self.source_code)}:{self.source_code}|"
            f"{len(self.episode_id)}:{self.episode_id}|{self.step_id}"
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "source_code": self.source_code,
            "episode_id": self.episode_id,
            "step_id": self.step_id,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> EventIdentity:
        values = _require_mapping("event identity", snapshot)
        return cls(
            source_code=_require_string(values, "source_code"),
            episode_id=_require_string(values, "episode_id"),
            step_id=_require_int(values, "step_id"),
        )


@dataclass(frozen=True, slots=True)
class ContextSignature:
    """Grounded pre-action context without retrospective semantic labels."""

    active_need_code: str
    sensor_bins: tuple[int, ...]
    available_action_codes: tuple[str, ...]
    human_bins: tuple[int, ...] = ()
    resource_bins: tuple[int, ...] = ()

    def __post_init__(self) -> None:
        _validate_code("active_need_code", self.active_need_code)
        if len(self.available_action_codes) != len(set(self.available_action_codes)):
            raise ValueError("available_action_codes must be unique")
        for action_code in self.available_action_codes:
            _validate_code("available_action_code", action_code)
        for name, values in (
            ("sensor_bins", self.sensor_bins),
            ("human_bins", self.human_bins),
            ("resource_bins", self.resource_bins),
        ):
            for value in values:
                if not isinstance(value, int):
                    raise ValueError(f"{name} must contain integers")

    @classmethod
    def from_values(
        cls,
        *,
        active_need_code: str,
        sensor_values: Iterable[float],
        available_action_codes: Iterable[str],
        human_values: Iterable[float] = (),
        resource_values: Iterable[float] = (),
    ) -> ContextSignature:
        return cls(
            active_need_code=active_need_code,
            sensor_bins=tuple(_quantize(value) for value in sensor_values),
            available_action_codes=tuple(sorted(set(available_action_codes))),
            human_bins=tuple(_quantize(value) for value in human_values),
            resource_bins=tuple(_quantize(value) for value in resource_values),
        )

    @property
    def tokens(self) -> frozenset[str]:
        tokens = {f"need:{self.active_need_code}"}
        tokens.update(f"sensor:{index}:{value}" for index, value in enumerate(self.sensor_bins))
        tokens.update(f"action:{code}" for code in self.available_action_codes)
        tokens.update(f"human:{index}:{value}" for index, value in enumerate(self.human_bins))
        tokens.update(f"resource:{index}:{value}" for index, value in enumerate(self.resource_bins))
        return frozenset(tokens)

    def snapshot(self) -> dict[str, object]:
        return {
            "active_need_code": self.active_need_code,
            "sensor_bins": list(self.sensor_bins),
            "available_action_codes": list(self.available_action_codes),
            "human_bins": list(self.human_bins),
            "resource_bins": list(self.resource_bins),
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ContextSignature:
        values = _require_mapping("context signature", snapshot)
        return cls(
            active_need_code=_require_string(values, "active_need_code"),
            sensor_bins=tuple(_require_int_list(values, "sensor_bins")),
            available_action_codes=tuple(_require_string_list(values, "available_action_codes")),
            human_bins=tuple(_require_int_list(values, "human_bins")),
            resource_bins=tuple(_require_int_list(values, "resource_bins")),
        )


@dataclass(frozen=True, slots=True)
class ContextualExperienceTrace:
    """One inspectable contextual occurrence supporting a local neural route."""

    identity: EventIdentity
    correlation_group_id: str
    assembly_id: str
    route_id: str
    action_code: str
    context: ContextSignature
    observed_effects: tuple[EffectObservation, ...]
    transfer_attempted: bool = False
    transfer_succeeded: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("correlation_group_id", self.correlation_group_id),
            ("assembly_id", self.assembly_id),
            ("route_id", self.route_id),
            ("action_code", self.action_code),
        ):
            _validate_code(name, value)
        if not self.observed_effects:
            raise ValueError("observed_effects must not be empty")
        effect_codes = tuple(effect.effect_code for effect in self.observed_effects)
        if len(effect_codes) != len(set(effect_codes)):
            raise ValueError("observed effect dimensions must be unique")
        if self.transfer_succeeded and not self.transfer_attempted:
            raise ValueError("transfer success requires a transfer attempt")

    def snapshot(self) -> dict[str, object]:
        return {
            "identity": self.identity.snapshot(),
            "event_key": self.identity.key,
            "correlation_group_id": self.correlation_group_id,
            "assembly_id": self.assembly_id,
            "route_id": self.route_id,
            "action_code": self.action_code,
            "context": self.context.snapshot(),
            "observed_effects": [
                {
                    "effect_code": effect.effect_code,
                    "value": effect.value,
                    "confidence": effect.confidence,
                }
                for effect in self.observed_effects
            ],
            "transfer_attempted": self.transfer_attempted,
            "transfer_succeeded": self.transfer_succeeded,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ContextualExperienceTrace:
        values = _require_mapping("contextual experience trace", snapshot)
        raw_effects = _require_list(values, "observed_effects")
        effects: list[EffectObservation] = []
        for raw_effect in raw_effects:
            effect = _require_mapping("observed effect", raw_effect)
            effects.append(
                EffectObservation(
                    effect_code=_require_string(effect, "effect_code"),
                    value=_require_float(effect, "value"),
                    confidence=_require_float(effect, "confidence"),
                )
            )
        trace = cls(
            identity=EventIdentity.from_snapshot(values.get("identity")),
            correlation_group_id=_require_string(values, "correlation_group_id"),
            assembly_id=_require_string(values, "assembly_id"),
            route_id=_require_string(values, "route_id"),
            action_code=_require_string(values, "action_code"),
            context=ContextSignature.from_snapshot(values.get("context")),
            observed_effects=tuple(effects),
            transfer_attempted=_require_bool(values, "transfer_attempted"),
            transfer_succeeded=_require_bool(values, "transfer_succeeded"),
        )
        stored_key = values.get("event_key")
        if stored_key is not None and stored_key != trace.identity.key:
            raise ValueError("stored event key does not match event identity")
        return trace


@dataclass(frozen=True, slots=True)
class ContextualLearningResult:
    """Recording result and whether aggregate local evidence may advance."""

    code: ContextualRecordCode
    event_key: str
    evidence_applied: bool
    trace_count: int
    independent_group_count: int


@dataclass(frozen=True, slots=True)
class LessonIdentity:
    """One need-aligned effect whose breadth and mastery are evaluated."""

    need_code: str
    effect_code: str
    desired_direction: float

    def __post_init__(self) -> None:
        _validate_code("need_code", self.need_code)
        _validate_code("effect_code", self.effect_code)
        if not isfinite(self.desired_direction) or not -1.0 <= self.desired_direction <= 1.0:
            raise ValueError("desired_direction must be between negative one and one")
        if self.desired_direction == 0.0:
            raise ValueError("desired_direction must not be zero")


@dataclass(frozen=True, slots=True)
class MasteryProfile:
    """Separate repetition, breadth, route, causality, transfer, and harm evidence."""

    raw_repetition_count: int
    effective_support: float
    unique_context_count: int
    unique_route_count: int
    contradiction_count: int
    repetition_strength: float
    context_diversity: float
    route_diversity: float
    causal_consistency: float
    transfer_success: float
    protective_strength: float
    mastery_score: float
    broad_mastery: bool
    source_event_ids: tuple[str, ...]

    def snapshot(self) -> dict[str, object]:
        return {
            "raw_repetition_count": self.raw_repetition_count,
            "effective_support": self.effective_support,
            "unique_context_count": self.unique_context_count,
            "unique_route_count": self.unique_route_count,
            "contradiction_count": self.contradiction_count,
            "repetition_strength": self.repetition_strength,
            "context_diversity": self.context_diversity,
            "route_diversity": self.route_diversity,
            "causal_consistency": self.causal_consistency,
            "transfer_success": self.transfer_success,
            "protective_strength": self.protective_strength,
            "mastery_score": self.mastery_score,
            "broad_mastery": self.broad_mastery,
            "source_event_ids": list(self.source_event_ids),
        }


@dataclass(frozen=True, slots=True)
class RouteSupport:
    """Context-sensitive evidence for one surviving neural route."""

    route_id: str
    score: float
    effective_support: float
    context_similarity: float
    causal_consistency: float
    independent_group_count: int

    def snapshot(self) -> dict[str, object]:
        return {
            "route_id": self.route_id,
            "score": self.score,
            "effective_support": self.effective_support,
            "context_similarity": self.context_similarity,
            "causal_consistency": self.causal_consistency,
            "independent_group_count": self.independent_group_count,
        }


@dataclass(frozen=True, slots=True)
class _GroupEvidence:
    group_id: str
    route_id: str
    context: ContextSignature
    support: float
    contradiction: float
    transfer_attempted: bool
    transfer_succeeded: bool


@dataclass(slots=True)
class ContextualExperienceLedger:
    """Preserve contextual traces while discounting exact and correlated copies."""

    _traces: dict[str, ContextualExperienceTrace] = field(default_factory=dict)

    @property
    def traces(self) -> tuple[ContextualExperienceTrace, ...]:
        return tuple(self._traces[key] for key in sorted(self._traces))

    @property
    def trace_count(self) -> int:
        return len(self._traces)

    @property
    def independent_group_count(self) -> int:
        return len({trace.correlation_group_id for trace in self._traces.values()})

    def trace(self, event_key: str) -> ContextualExperienceTrace:
        try:
            return self._traces[event_key]
        except KeyError as error:
            raise ValueError(f"unknown event identity: {event_key}") from error

    def classify(self, trace: ContextualExperienceTrace) -> ContextualLearningResult:
        """Classify one trace without mutating the ledger."""
        event_key = trace.identity.key
        existing = self._traces.get(event_key)
        if existing is not None:
            if existing != trace:
                raise ValueError("event identity conflict: payload differs for existing event")
            return ContextualLearningResult(
                code=ContextualRecordCode.EXACT_DUPLICATE_IGNORED,
                event_key=event_key,
                evidence_applied=False,
                trace_count=self.trace_count,
                independent_group_count=self.independent_group_count,
            )

        group = tuple(
            item
            for item in self._traces.values()
            if item.correlation_group_id == trace.correlation_group_id
        )
        if group:
            representative = group[0]
            expected = (
                representative.assembly_id,
                representative.route_id,
                representative.action_code,
            )
            supplied = (trace.assembly_id, trace.route_id, trace.action_code)
            if supplied != expected:
                raise ValueError("correlation group identity conflict")

        evidence_applied = not group
        return ContextualLearningResult(
            code=(
                ContextualRecordCode.ACCEPTED_INDEPENDENT
                if evidence_applied
                else ContextualRecordCode.ACCEPTED_CORRELATED
            ),
            event_key=event_key,
            evidence_applied=evidence_applied,
            trace_count=self.trace_count + 1,
            independent_group_count=(
                self.independent_group_count + 1
                if evidence_applied
                else self.independent_group_count
            ),
        )

    def record(self, trace: ContextualExperienceTrace) -> ContextualLearningResult:
        """Deduplicate only exact identity and discount copied correlation groups."""
        result = self.classify(trace)
        if result.code is not ContextualRecordCode.EXACT_DUPLICATE_IGNORED:
            self._traces[result.event_key] = trace
        return result

    def mastery_profile(self, lesson: LessonIdentity) -> MasteryProfile:
        """Estimate broad mastery from independent breadth rather than raw count."""
        relevant = tuple(
            trace
            for trace in self.traces
            if trace.context.active_need_code == lesson.need_code
            and any(effect.effect_code == lesson.effect_code for effect in trace.observed_effects)
        )
        groups = self._group_evidence(relevant, lesson)
        support = sum(group.support for group in groups)
        contradiction = sum(group.contradiction for group in groups)
        supporting = tuple(group for group in groups if group.support > group.contradiction)
        contexts = {group.context for group in supporting}
        routes = {group.route_id for group in supporting}
        attempts = tuple(group for group in groups if group.transfer_attempted)
        transfer_success = (
            sum(group.transfer_succeeded for group in attempts) / len(attempts) if attempts else 0.0
        )
        causal_consistency = support / (support + contradiction) if support + contradiction else 0.0
        repetition_strength = min(1.0, support / 3.0)
        context_diversity = min(1.0, len(contexts) / 3.0)
        route_diversity = min(1.0, len(routes) / 2.0)
        protective_strength = max(
            (
                max(0.0, effect.value * lesson.desired_direction) * effect.confidence
                for trace in relevant
                for effect in trace.observed_effects
                if effect.effect_code == lesson.effect_code
            ),
            default=0.0,
        )
        mastery_score = (
            0.20 * repetition_strength
            + 0.25 * context_diversity
            + 0.20 * route_diversity
            + 0.20 * causal_consistency
            + 0.15 * transfer_success
        )
        broad_mastery = bool(
            support >= 3.0
            and len(contexts) >= 3
            and len(routes) >= 2
            and causal_consistency >= 0.75
            and transfer_success >= 0.50
            and mastery_score >= 0.75
        )
        return MasteryProfile(
            raw_repetition_count=len(relevant),
            effective_support=support,
            unique_context_count=len(contexts),
            unique_route_count=len(routes),
            contradiction_count=sum(group.contradiction > 0.0 for group in groups),
            repetition_strength=repetition_strength,
            context_diversity=context_diversity,
            route_diversity=route_diversity,
            causal_consistency=causal_consistency,
            transfer_success=transfer_success,
            protective_strength=protective_strength,
            mastery_score=mastery_score,
            broad_mastery=broad_mastery,
            source_event_ids=tuple(trace.identity.key for trace in relevant),
        )

    def rank_routes(
        self,
        lesson: LessonIdentity,
        current_context: ContextSignature,
    ) -> tuple[RouteSupport, ...]:
        """Keep all supported routes and rank them for the present grounded context."""
        relevant = tuple(
            trace
            for trace in self.traces
            if trace.context.active_need_code == lesson.need_code
            and any(effect.effect_code == lesson.effect_code for effect in trace.observed_effects)
        )
        grouped: dict[str, list[_GroupEvidence]] = defaultdict(list)
        for group in self._group_evidence(relevant, lesson):
            grouped[group.route_id].append(group)
        routes: list[RouteSupport] = []
        for route_id, groups in grouped.items():
            support = sum(group.support for group in groups)
            contradiction = sum(group.contradiction for group in groups)
            consistency = support / (support + contradiction) if support + contradiction else 0.0
            similarities = tuple(
                _jaccard(current_context.tokens, group.context.tokens)
                for group in groups
                if group.support > group.contradiction
            )
            similarity = fmean(similarities) if similarities else 0.0
            score = min(1.0, support / 3.0) * (0.25 + 0.75 * similarity) * consistency
            routes.append(
                RouteSupport(
                    route_id=route_id,
                    score=score,
                    effective_support=support,
                    context_similarity=similarity,
                    causal_consistency=consistency,
                    independent_group_count=len(groups),
                )
            )
        return tuple(sorted(routes, key=lambda route: (-route.score, route.route_id)))

    def snapshot(self) -> dict[str, object]:
        return {
            "trace_count": self.trace_count,
            "independent_group_count": self.independent_group_count,
            "traces": [trace.snapshot() for trace in self.traces],
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ContextualExperienceLedger:
        values = _require_mapping("contextual experience ledger", snapshot)
        ledger = cls()
        for raw_trace in _require_list(values, "traces"):
            trace = ContextualExperienceTrace.from_snapshot(raw_trace)
            result = ledger.record(trace)
            if result.code is ContextualRecordCode.EXACT_DUPLICATE_IGNORED:
                raise ValueError("persisted contextual traces must have unique event identities")
        if _require_int(values, "trace_count") != ledger.trace_count:
            raise ValueError("contextual trace count does not match contents")
        if _require_int(values, "independent_group_count") != ledger.independent_group_count:
            raise ValueError("contextual group count does not match contents")
        return ledger

    @staticmethod
    def _group_evidence(
        relevant: tuple[ContextualExperienceTrace, ...],
        lesson: LessonIdentity,
    ) -> tuple[_GroupEvidence, ...]:
        grouped: dict[str, list[ContextualExperienceTrace]] = defaultdict(list)
        for trace in relevant:
            grouped[trace.correlation_group_id].append(trace)
        evidence: list[_GroupEvidence] = []
        for group_id, traces in sorted(grouped.items()):
            ordered = sorted(traces, key=lambda trace: trace.identity.key)
            aligned: list[tuple[float, float]] = []
            for trace in ordered:
                effect = next(
                    item
                    for item in trace.observed_effects
                    if item.effect_code == lesson.effect_code
                )
                aligned.append((effect.value * lesson.desired_direction, effect.confidence))
            total_confidence = sum(confidence for _, confidence in aligned)
            signed = (
                sum(value * confidence for value, confidence in aligned) / total_confidence
                if total_confidence
                else 0.0
            )
            mean_confidence = fmean(confidence for _, confidence in aligned)
            representative = ordered[0]
            evidence.append(
                _GroupEvidence(
                    group_id=group_id,
                    route_id=representative.route_id,
                    context=representative.context,
                    support=max(0.0, signed) * mean_confidence,
                    contradiction=max(0.0, -signed) * mean_confidence,
                    transfer_attempted=any(trace.transfer_attempted for trace in ordered),
                    transfer_succeeded=any(trace.transfer_succeeded for trace in ordered),
                )
            )
        return tuple(evidence)


def _jaccard(left: frozenset[str], right: frozenset[str]) -> float:
    union = left | right
    return len(left & right) / len(union) if union else 1.0


def _quantize(value: float) -> int:
    if not isfinite(value):
        raise ValueError("context values must be finite")
    return round(max(-10.0, min(10.0, value)) * 10.0)


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_list(values: Mapping[str, object], key: str) -> list[object]:
    value = values.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_float(values: Mapping[str, object], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _require_string_list(values: Mapping[str, object], key: str) -> list[str]:
    result: list[str] = []
    for item in _require_list(values, key):
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain strings")
        result.append(item)
    return result


def _require_int_list(values: Mapping[str, object], key: str) -> list[int]:
    result: list[int] = []
    for item in _require_list(values, key):
        if isinstance(item, bool) or not isinstance(item, int):
            raise ValueError(f"{key} must contain integers")
        result.append(item)
    return result
