"""Dynamically expanding sparse effect memory for NDNRA research."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from math import isfinite


@dataclass(frozen=True, slots=True)
class EffectObservation:
    """One observed consequence with signed direction and confidence."""

    effect_code: str
    value: float
    confidence: float = 1.0

    def __post_init__(self) -> None:
        _validate_code("effect_code", self.effect_code)
        _validate_signed_unit("value", self.value)
        _validate_unit_interval("confidence", self.confidence)


@dataclass(slots=True)
class EffectEstimate:
    """Locally accumulated estimate for one learned effect dimension."""

    value: float
    confidence: float
    evidence_count: int = 1

    def __post_init__(self) -> None:
        _validate_signed_unit("value", self.value)
        _validate_unit_interval("confidence", self.confidence)
        if self.evidence_count <= 0:
            raise ValueError("evidence_count must be positive")

    @classmethod
    def from_snapshot(cls, snapshot: object) -> EffectEstimate:
        """Restore one validated local estimate from inspectable state."""
        values = _require_mapping("effect estimate", snapshot)
        return cls(
            value=_require_float(values, "value"),
            confidence=_require_float(values, "confidence"),
            evidence_count=_require_int(values, "evidence_count"),
        )

    def observe(self, observation: EffectObservation) -> None:
        """Update this dimension without changing unrelated dimensions."""
        old_weight = self.confidence * self.evidence_count
        new_weight = observation.confidence
        total_weight = old_weight + new_weight
        if total_weight > 0.0:
            self.value = (self.value * old_weight + observation.value * new_weight) / total_weight
        agreement = 1.0 - min(1.0, abs(self.value - observation.value) / 2.0)
        accumulated = 1.0 - (1.0 - self.confidence) * (1.0 - observation.confidence)
        self.confidence = max(0.0, min(1.0, accumulated * agreement))
        self.evidence_count += 1


@dataclass(slots=True)
class SparseEffectMemory:
    """Sparse local memory whose dimensionality grows with observed effects."""

    _dimensions: dict[str, EffectEstimate] = field(default_factory=dict)

    @property
    def dimension_count(self) -> int:
        return len(self._dimensions)

    @property
    def effect_codes(self) -> tuple[str, ...]:
        return tuple(sorted(self._dimensions))

    def estimate(self, effect_code: str) -> EffectEstimate | None:
        """Return one learned dimension without manufacturing missing effects."""
        _validate_code("effect_code", effect_code)
        return self._dimensions.get(effect_code)

    @classmethod
    def from_snapshot(cls, snapshot: object) -> SparseEffectMemory:
        """Restore sparse dimensions without creating unobserved effects."""
        values = _require_mapping("effect memory", snapshot)
        raw_dimensions = _require_mapping("effect dimensions", values.get("dimensions"))
        dimensions: dict[str, EffectEstimate] = {}
        for effect_code, raw_estimate in raw_dimensions.items():
            _validate_code("effect_code", effect_code)
            dimensions[effect_code] = EffectEstimate.from_snapshot(raw_estimate)
        expected_count = _require_int(values, "dimension_count")
        if expected_count != len(dimensions):
            raise ValueError("effect memory dimension count does not match contents")
        return cls(_dimensions=dimensions)

    def observe(self, observation: EffectObservation) -> bool:
        """Learn one effect and report whether a new dimension was created."""
        existing = self._dimensions.get(observation.effect_code)
        if existing is None:
            self._dimensions[observation.effect_code] = EffectEstimate(
                value=observation.value,
                confidence=observation.confidence,
            )
            return True
        existing.observe(observation)
        return False

    def observe_many(self, observations: Iterable[EffectObservation]) -> int:
        """Learn multiple consequences and return dimensions newly created."""
        created = 0
        for observation in observations:
            created += int(self.observe(observation))
        return created

    def compatibility(self, need: EffectNeed) -> float:
        """Compare this local effect memory with a sparse current need."""
        score = 0.0
        for dimension in need.dimensions:
            estimate = self._dimensions.get(dimension.effect_code)
            if estimate is None:
                continue
            score += (
                estimate.value
                * dimension.desired_direction
                * estimate.confidence
                * dimension.intensity
            )
        return score

    def projected_values(self) -> dict[str, float]:
        """Return deterministic signed effects for composition evidence."""
        return {
            effect_code: estimate.value * estimate.confidence
            for effect_code, estimate in sorted(self._dimensions.items())
        }

    def snapshot(self) -> dict[str, object]:
        return {
            "dimension_count": self.dimension_count,
            "dimensions": {
                effect_code: {
                    "value": estimate.value,
                    "confidence": estimate.confidence,
                    "evidence_count": estimate.evidence_count,
                }
                for effect_code, estimate in sorted(self._dimensions.items())
            },
        }


@dataclass(frozen=True, slots=True)
class NeedDimension:
    """One desired direction in a sparse multidimensional need pulse."""

    effect_code: str
    desired_direction: float
    intensity: float

    def __post_init__(self) -> None:
        _validate_code("effect_code", self.effect_code)
        _validate_signed_unit("desired_direction", self.desired_direction)
        if self.desired_direction == 0.0:
            raise ValueError("desired_direction must not be zero")
        _validate_unit_interval("intensity", self.intensity)
        if self.intensity == 0.0:
            raise ValueError("intensity must be above zero")


@dataclass(frozen=True, slots=True)
class EffectNeed:
    """Current need represented by only the effect dimensions that matter."""

    need_code: str
    primary_effect_code: str
    dimensions: tuple[NeedDimension, ...]
    satisfaction_threshold: float

    def __post_init__(self) -> None:
        _validate_code("need_code", self.need_code)
        _validate_code("primary_effect_code", self.primary_effect_code)
        _validate_unit_interval("satisfaction_threshold", self.satisfaction_threshold)
        if not self.dimensions:
            raise ValueError("dimensions must not be empty")
        effect_codes = tuple(item.effect_code for item in self.dimensions)
        if len(effect_codes) != len(set(effect_codes)):
            raise ValueError("need dimensions must be unique")
        if self.primary_effect_code not in effect_codes:
            raise ValueError("primary_effect_code must be present in dimensions")

    def score_projected_effects(self, effects: dict[str, float]) -> float:
        """Score a composed candidate against desired and avoided effects."""
        return sum(
            effects.get(dimension.effect_code, 0.0)
            * dimension.desired_direction
            * dimension.intensity
            for dimension in self.dimensions
        )

    def primary_satisfaction(self, effects: dict[str, float]) -> float:
        """Return aligned progress on the primary need dimension."""
        primary = next(
            item for item in self.dimensions if item.effect_code == self.primary_effect_code
        )
        return max(
            0.0,
            effects.get(primary.effect_code, 0.0) * primary.desired_direction,
        )


@dataclass(slots=True)
class LocalEffectLink:
    """Synapse-like local association with its own expanding effect memory."""

    source_id: str
    target_id: str
    effect_memory: SparseEffectMemory = field(default_factory=SparseEffectMemory)
    usage_count: int = 0

    def __post_init__(self) -> None:
        _validate_code("source_id", self.source_id)
        _validate_code("target_id", self.target_id)
        if self.source_id == self.target_id:
            raise ValueError("source_id and target_id must differ")
        if self.usage_count < 0:
            raise ValueError("usage_count must not be negative")

    @property
    def link_id(self) -> str:
        return f"{self.source_id}->{self.target_id}"

    @classmethod
    def from_snapshot(cls, snapshot: object) -> LocalEffectLink:
        """Restore one synapse-like local association."""
        values = _require_mapping("effect link", snapshot)
        link = cls(
            source_id=_require_string(values, "source_id"),
            target_id=_require_string(values, "target_id"),
            effect_memory=SparseEffectMemory.from_snapshot(values.get("effect_memory")),
            usage_count=_require_int(values, "usage_count"),
        )
        stored_link_id = values.get("link_id")
        if stored_link_id is not None and stored_link_id != link.link_id:
            raise ValueError("effect link identifier does not match endpoints")
        return link

    def observe_effects(self, observations: Iterable[EffectObservation]) -> int:
        self.usage_count += 1
        return self.effect_memory.observe_many(observations)


def combine_projected_effects(
    current: dict[str, float],
    additional: dict[str, float],
) -> dict[str, float]:
    """Combine local effects while keeping every dimension bounded."""
    combined = dict(current)
    for effect_code, value in additional.items():
        combined[effect_code] = max(
            -1.0,
            min(1.0, combined.get(effect_code, 0.0) + value),
        )
    return combined


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
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


def _validate_code(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    if not value.isascii():
        raise ValueError(f"{name} must be ASCII")


def _validate_unit_interval(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _validate_signed_unit(name: str, value: float) -> None:
    if not isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between negative one and one")
