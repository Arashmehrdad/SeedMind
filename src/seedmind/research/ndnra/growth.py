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
    pressure_learning_rate: float = 0.50
    growth_threshold: float = 0.75
    minimum_attempts: int = 3
    maximum_specialists: int = 1
    specialist_confidence: float = 0.95

    def __post_init__(self) -> None:
        for name, value in (
            ("trace_decay", self.trace_decay),
            ("pressure_learning_rate", self.pressure_learning_rate),
            ("growth_threshold", self.growth_threshold),
            ("specialist_confidence", self.specialist_confidence),
        ):
            _validate_unit(name, value)
        if self.minimum_attempts <= 0:
            raise ValueError("minimum_attempts must be positive")
        if self.maximum_specialists <= 0:
            raise ValueError("maximum_specialists must be positive")


@dataclass(frozen=True, slots=True)
class GrowthAttemptRecord:
    """One unresolved interaction observation and its local growth state."""

    attempt_index: int
    active_assembly_ids: tuple[str, ...]
    predicted_effect: float
    actual_effect: float
    residual_effect: float
    unresolved_error: float
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
    _last_active_members: tuple[str, ...] = ()

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
        capacity_saturation: float,
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
            ("capacity_saturation", capacity_saturation),
        ):
            _validate_unit(name, value)

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
        pressure = self.pressure.update(
            unresolved_error=unresolved,
            curiosity=curiosity,
            ambition_relevance=ambition_relevance,
            capacity_saturation=capacity_saturation,
            learning_rate=self.config.pressure_learning_rate,
        )
        record = GrowthAttemptRecord(
            attempt_index=self.attempt_count + 1,
            active_assembly_ids=members,
            predicted_effect=predicted_effect,
            actual_effect=actual_effect,
            residual_effect=residual,
            unresolved_error=unresolved,
            growth_pressure=pressure,
            growth_ready=(
                self.attempt_count + 1 >= self.config.minimum_attempts
                and pressure >= self.config.growth_threshold
                and self.graph.specialist_count < self.config.maximum_specialists
            ),
            eligibility_traces=self.eligibility_traces,
        )
        self._attempts.append(record)
        return record

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
        residual = sum(self._residuals) / len(self._residuals)
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
