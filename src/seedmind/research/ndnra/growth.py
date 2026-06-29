"""Evidence-driven structural growth for the isolated NDNRA prototype."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from math import isfinite
from random import Random

from seedmind.research.ndnra.composition import (
    MultidimensionalExperienceGraph,
    SpecialistInteraction,
)
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.models import GrowthPressure


@dataclass(frozen=True, slots=True)
class StructuralGrowthConfig:
    """Bounded thresholds for local evidence-driven structural growth."""

    trace_decay: float = 0.80
    pressure_learning_rate: float = 1.00
    growth_threshold: float = 0.75
    minimum_attempts: int = 3
    maximum_specialists: int = 1
    specialist_confidence: float = 0.95
    minimum_active_eligibility_for_saturation: float = 0.75

    def __post_init__(self) -> None:
        for name, value in (
            ("trace_decay", self.trace_decay),
            ("pressure_learning_rate", self.pressure_learning_rate),
            ("growth_threshold", self.growth_threshold),
            ("specialist_confidence", self.specialist_confidence),
            (
                "minimum_active_eligibility_for_saturation",
                self.minimum_active_eligibility_for_saturation,
            ),
        ):
            _validate_unit(name, value)
        if self.minimum_attempts <= 0:
            raise ValueError("minimum_attempts must be positive")
        if self.maximum_specialists <= 0:
            raise ValueError("maximum_specialists must be positive")


@dataclass(frozen=True, slots=True)
class LocalSaturationReport:
    """Deterministic local saturation evidence derived from current graph state only."""

    active_assembly_ids: tuple[str, ...]
    active_eligibility_before: tuple[tuple[str, float], ...]
    assembly_count: int
    specialist_count: int
    maximum_specialists: int
    remaining_specialist_slots: int
    capacity_available: bool
    duplicate_membership_exists: bool
    minimum_active_eligibility_for_saturation: float
    minimum_active_eligibility: float
    mean_active_eligibility: float
    locally_saturated: bool
    saturation: float

    def __post_init__(self) -> None:
        if len(self.active_assembly_ids) < 2:
            raise ValueError("active_assembly_ids must contain at least two assemblies")
        if self.active_assembly_ids != tuple(sorted(self.active_assembly_ids)):
            raise ValueError("active_assembly_ids must use stable sorted order")
        if len(self.active_assembly_ids) != len(set(self.active_assembly_ids)):
            raise ValueError("active_assembly_ids must be unique")
        if any(
            not assembly_id.strip() or not assembly_id.isascii()
            for assembly_id in self.active_assembly_ids
        ):
            raise ValueError("active_assembly_ids must be non-empty ASCII identities")
        if len(self.active_eligibility_before) != len(self.active_assembly_ids):
            raise ValueError("active_eligibility_before must match active_assembly_ids")
        if self.assembly_count < len(self.active_assembly_ids):
            raise ValueError("assembly_count cannot be smaller than active members")
        if self.specialist_count < 0:
            raise ValueError("specialist_count must not be negative")
        if self.maximum_specialists <= 0:
            raise ValueError("maximum_specialists must be positive")
        expected_remaining = max(0, self.maximum_specialists - self.specialist_count)
        if self.remaining_specialist_slots != expected_remaining:
            raise ValueError("remaining_specialist_slots must match specialist capacity")
        if self.capacity_available != (self.remaining_specialist_slots > 0):
            raise ValueError("capacity_available must match remaining_specialist_slots")
        for name, value in (
            (
                "minimum_active_eligibility_for_saturation",
                self.minimum_active_eligibility_for_saturation,
            ),
            ("minimum_active_eligibility", self.minimum_active_eligibility),
            ("mean_active_eligibility", self.mean_active_eligibility),
            ("saturation", self.saturation),
        ):
            _validate_unit(name, value)
        ordered_ids = tuple(assembly_id for assembly_id, _ in self.active_eligibility_before)
        if ordered_ids != self.active_assembly_ids:
            raise ValueError("active_eligibility_before must align with active_assembly_ids")
        eligibility_values = tuple(value for _, value in self.active_eligibility_before)
        for value in eligibility_values:
            _validate_unit("active_eligibility_before", value)
        expected_minimum = min(eligibility_values)
        expected_mean = sum(eligibility_values) / len(eligibility_values)
        if abs(self.minimum_active_eligibility - expected_minimum) > 1e-12:
            raise ValueError("minimum_active_eligibility must match local traces")
        if abs(self.mean_active_eligibility - expected_mean) > 1e-12:
            raise ValueError("mean_active_eligibility must match local traces")
        expected_locally_saturated = (
            self.capacity_available
            and not self.duplicate_membership_exists
            and expected_minimum >= self.minimum_active_eligibility_for_saturation
        )
        if self.locally_saturated != expected_locally_saturated:
            raise ValueError("locally_saturated must match local saturation rule")
        expected_saturation = expected_minimum if expected_locally_saturated else 0.0
        if abs(self.saturation - expected_saturation) > 1e-12:
            raise ValueError("saturation must match local saturation rule")


@dataclass(frozen=True, slots=True)
class GrowthAttemptRecord:
    """One unresolved interaction observation and its local growth state."""

    attempt_index: int
    active_assembly_ids: tuple[str, ...]
    predicted_effect: float
    actual_effect: float
    residual_effect: float
    unresolved_error: float
    local_saturation: LocalSaturationReport
    growth_pressure: float
    growth_ready: bool
    eligibility_traces: tuple[tuple[str, float], ...]


@dataclass(frozen=True, slots=True)
class GrowthOutcome:
    """Result of adding one targeted or random specialist interaction."""

    specialist_id: str
    member_assembly_ids: tuple[str, ...]
    origin_code: str
    residual_effect: float
    structural_nodes_before: int
    structural_nodes_after: int
    old_assembly_count_preserved: bool


@dataclass(slots=True)
class EvidenceDrivenGrowthController:
    """Grow only after repeated unexplained effects and local eligibility."""

    graph: MultidimensionalExperienceGraph
    config: StructuralGrowthConfig = field(default_factory=StructuralGrowthConfig)
    pressure: GrowthPressure = field(default_factory=GrowthPressure)
    _eligibility: dict[str, float] = field(default_factory=dict)
    _residuals: list[float] = field(default_factory=list)
    _attempts: list[GrowthAttemptRecord] = field(default_factory=list)
    _latest_local_saturation: LocalSaturationReport | None = None
    _last_active_members: tuple[str, ...] = ()
    _growth_cursor: int = 0

    @property
    def attempt_count(self) -> int:
        return len(self._attempts)

    @property
    def attempts(self) -> tuple[GrowthAttemptRecord, ...]:
        return tuple(self._attempts)

    @property
    def growth_ready(self) -> bool:
        return (
            self.attempt_count >= self.config.minimum_attempts
            and self.pressure.value >= self.config.growth_threshold
            and self._latest_local_saturation is not None
            and self._latest_local_saturation.locally_saturated
            and self.graph.specialist_count < self.config.maximum_specialists
        )

    @property
    def eligibility_traces(self) -> tuple[tuple[str, float], ...]:
        return tuple(sorted(self._eligibility.items()))

    def observe_unresolved_interaction(
        self,
        *,
        active_assembly_ids: Iterable[str],
        predicted_effect: float,
        actual_effect: float,
        curiosity: float,
        ambition_relevance: float,
    ) -> GrowthAttemptRecord:
        """Accumulate pressure and mark only participating assemblies locally."""
        members = tuple(active_assembly_ids)
        if len(members) < 2 or len(members) != len(set(members)):
            raise ValueError("active_assembly_ids must contain at least two unique members")
        for assembly_id in members:
            self.graph.assembly(assembly_id)
        for name, value in (
            ("predicted_effect", predicted_effect),
            ("actual_effect", actual_effect),
        ):
            _validate_signed(name, value)
        for name, value in (
            ("curiosity", curiosity),
            ("ambition_relevance", ambition_relevance),
        ):
            _validate_unit(name, value)

        local_saturation = self._derive_local_saturation_report(members)
        for assembly_id in tuple(self._eligibility):
            self._eligibility[assembly_id] *= self.config.trace_decay
        for assembly_id in members:
            self._eligibility[assembly_id] = min(
                1.0,
                self._eligibility.get(assembly_id, 0.0) + 1.0,
            )
        self._last_active_members = members

        residual = max(-1.0, min(1.0, actual_effect - predicted_effect))
        unresolved = abs(residual)
        self._residuals.append(residual)
        self._latest_local_saturation = local_saturation
        pressure = self.pressure.update(
            unresolved_error=unresolved,
            curiosity=curiosity,
            ambition_relevance=ambition_relevance,
            capacity_saturation=local_saturation.saturation,
            learning_rate=self.config.pressure_learning_rate,
        )
        record = GrowthAttemptRecord(
            attempt_index=self.attempt_count + 1,
            active_assembly_ids=members,
            predicted_effect=predicted_effect,
            actual_effect=actual_effect,
            residual_effect=residual,
            unresolved_error=unresolved,
            local_saturation=local_saturation,
            growth_pressure=pressure,
            growth_ready=(
                self.attempt_count + 1 >= self.config.minimum_attempts
                and pressure >= self.config.growth_threshold
                and local_saturation.locally_saturated
                and self.graph.specialist_count < self.config.maximum_specialists
            ),
            eligibility_traces=self.eligibility_traces,
        )
        self._attempts.append(record)
        return record

    def _derive_local_saturation_report(
        self,
        active_assembly_ids: tuple[str, ...],
    ) -> LocalSaturationReport:
        active_ids = tuple(sorted(active_assembly_ids))
        eligibility_before = tuple(
            (assembly_id, self._eligibility.get(assembly_id, 0.0)) for assembly_id in active_ids
        )
        minimum_active_eligibility = min(value for _, value in eligibility_before)
        mean_active_eligibility = sum(value for _, value in eligibility_before) / len(
            eligibility_before
        )
        remaining_specialist_slots = max(
            0,
            self.config.maximum_specialists - self.graph.specialist_count,
        )
        ordered_members = tuple(assembly_id for assembly_id, _ in eligibility_before)
        duplicate_membership_exists = any(
            tuple(sorted(specialist.member_assembly_ids)) == ordered_members
            for specialist in self.graph.specialists
        )
        return LocalSaturationReport(
            active_assembly_ids=ordered_members,
            active_eligibility_before=eligibility_before,
            assembly_count=self.graph.assembly_count,
            specialist_count=self.graph.specialist_count,
            maximum_specialists=self.config.maximum_specialists,
            remaining_specialist_slots=remaining_specialist_slots,
            capacity_available=remaining_specialist_slots > 0,
            duplicate_membership_exists=duplicate_membership_exists,
            minimum_active_eligibility_for_saturation=(
                self.config.minimum_active_eligibility_for_saturation
            ),
            minimum_active_eligibility=minimum_active_eligibility,
            mean_active_eligibility=mean_active_eligibility,
            locally_saturated=(
                remaining_specialist_slots > 0
                and not duplicate_membership_exists
                and minimum_active_eligibility
                >= self.config.minimum_active_eligibility_for_saturation
            ),
            saturation=(
                minimum_active_eligibility
                if (
                    remaining_specialist_slots > 0
                    and not duplicate_membership_exists
                    and minimum_active_eligibility
                    >= self.config.minimum_active_eligibility_for_saturation
                )
                else 0.0
            ),
        )

    def grow_targeted_specialist(
        self,
        *,
        specialist_id: str,
        effect_code: str,
    ) -> GrowthOutcome:
        """Create one specialist from the strongest locally eligible memories."""
        if not self.growth_ready:
            raise RuntimeError("growth evidence gate has not passed")
        ranked = sorted(
            self._eligibility.items(),
            key=lambda item: (-item[1], item[0]),
        )
        selected_ids = {assembly_id for assembly_id, trace in ranked[:2] if trace > 0.0}
        members = tuple(
            assembly_id for assembly_id in self._last_active_members if assembly_id in selected_ids
        )
        if len(members) < 2:
            raise RuntimeError("insufficient eligible members for specialist growth")
        if any(specialist.member_assembly_ids == members for specialist in self.graph.specialists):
            raise RuntimeError("duplicate specialist membership is blocked")
        recent_residuals = self._residuals[self._growth_cursor :]
        if not recent_residuals:
            raise RuntimeError("no new unresolved evidence since the previous growth")
        residual = sum(recent_residuals) / len(recent_residuals)
        before_nodes = self.graph.structural_node_count
        before_assemblies = self.graph.assembly_count
        specialist = self.graph.grow_specialist_interaction(
            specialist_id=specialist_id,
            member_assembly_ids=members,
            origin_code="eligibility_targeted_growth",
            observed_effects=(
                EffectObservation(
                    effect_code=effect_code,
                    value=residual,
                    confidence=self.config.specialist_confidence,
                ),
            ),
        )
        self._growth_cursor = len(self._residuals)
        return GrowthOutcome(
            specialist_id=specialist.specialist_id,
            member_assembly_ids=specialist.member_assembly_ids,
            origin_code=specialist.origin_code,
            residual_effect=residual,
            structural_nodes_before=before_nodes,
            structural_nodes_after=self.graph.structural_node_count,
            old_assembly_count_preserved=self.graph.assembly_count == before_assemblies,
        )


def grow_random_specialist(
    graph: MultidimensionalExperienceGraph,
    *,
    seed: int,
    specialist_id: str = "specialist:random_capacity",
) -> SpecialistInteraction:
    """Add equal structural capacity without evidence-targeted useful memory."""
    assembly_ids = [assembly.assembly_id for assembly in graph.assemblies]
    if len(assembly_ids) < 2:
        raise ValueError("random growth requires at least two assemblies")
    random = Random(seed)
    members = tuple(sorted(random.sample(assembly_ids, 2)))
    return graph.grow_specialist_interaction(
        specialist_id=specialist_id,
        member_assembly_ids=members,
        origin_code="random_untrained_growth",
        observed_effects=(EffectObservation("novelty", 0.25, 0.50),),
    )


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _validate_signed(name: str, value: float) -> None:
    if not isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between negative one and one")
