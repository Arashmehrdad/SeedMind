"""Operational adaptive state restored alongside an NDNRA local graph."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.research.ndnra.models import GrowthPressure
from seedmind.research.ndnra.persistence import NDNRAGrowthState


@dataclass(frozen=True, slots=True)
class AdaptiveRuntimeConfig:
    """Bounded decay, reactivation, and pressure settings."""

    eligibility_decay: float = 0.80
    dormancy_increment: float = 0.08
    reactivation_amount: float = 0.60
    pressure_learning_rate: float = 0.25
    residual_history_limit: int = 64

    def __post_init__(self) -> None:
        for name, value in (
            ("eligibility_decay", self.eligibility_decay),
            ("dormancy_increment", self.dormancy_increment),
            ("reactivation_amount", self.reactivation_amount),
            ("pressure_learning_rate", self.pressure_learning_rate),
        ):
            _validate_unit(name, value)
        if self.residual_history_limit <= 0:
            raise ValueError("residual_history_limit must be positive")


@dataclass(frozen=True, slots=True)
class AdaptiveUpdate:
    """Inspectable result of one live adaptive-state update."""

    assembly_id: str
    pressure_before: float
    pressure_after: float
    attempt_count_before: int
    attempt_count_after: int
    eligibility_before: float
    eligibility_after: float
    dormancy_before: float
    dormancy_after: float
    residual_effect: float

    def __post_init__(self) -> None:
        if not self.assembly_id.strip():
            raise ValueError("assembly_id must not be empty")
        for name, value in (
            ("pressure_before", self.pressure_before),
            ("pressure_after", self.pressure_after),
            ("eligibility_before", self.eligibility_before),
            ("eligibility_after", self.eligibility_after),
            ("dormancy_before", self.dormancy_before),
            ("dormancy_after", self.dormancy_after),
        ):
            _validate_unit(name, value)
        _validate_signed("residual_effect", self.residual_effect)
        if self.attempt_count_before < 0:
            raise ValueError("attempt_count_before must not be negative")
        if self.attempt_count_after != self.attempt_count_before + 1:
            raise ValueError("attempt count must advance by exactly one")


@dataclass(slots=True)
class NDNRARuntimeAdaptiveState:
    """Apply persisted eligibility, dormancy, and pressure during live use."""

    graph: MultidimensionalExperienceGraph
    config: AdaptiveRuntimeConfig = field(default_factory=AdaptiveRuntimeConfig)
    pressure: GrowthPressure = field(default_factory=GrowthPressure)
    _eligibility: dict[str, float] = field(default_factory=dict)
    _residuals: list[float] = field(default_factory=list)
    _last_active_members: tuple[str, ...] = ()
    _dormancy: dict[str, float] = field(default_factory=dict)

    @classmethod
    def from_growth_state(
        cls,
        graph: MultidimensionalExperienceGraph,
        growth_state: NDNRAGrowthState | None = None,
        *,
        config: AdaptiveRuntimeConfig | None = None,
    ) -> NDNRARuntimeAdaptiveState:
        """Rehydrate operational state instead of treating metadata as archival."""
        persisted = NDNRAGrowthState() if growth_state is None else growth_state
        runtime = cls(
            graph=graph,
            config=AdaptiveRuntimeConfig() if config is None else config,
            pressure=GrowthPressure(
                value=persisted.pressure,
                update_count=persisted.attempt_count,
            ),
            _eligibility=dict(persisted.eligibility),
            _residuals=list(persisted.residuals),
            _last_active_members=persisted.last_active_members,
            _dormancy=dict(persisted.dormancy_levels),
        )
        runtime._validate_structure_references()
        return runtime

    @property
    def attempt_count(self) -> int:
        return self.pressure.update_count

    @property
    def eligibility(self) -> tuple[tuple[str, float], ...]:
        return tuple(sorted(self._eligibility.items()))

    @property
    def dormancy_levels(self) -> tuple[tuple[str, float], ...]:
        return tuple(sorted(self._dormancy.items()))

    @property
    def residuals(self) -> tuple[float, ...]:
        return tuple(self._residuals)

    @property
    def last_active_members(self) -> tuple[str, ...]:
        return self._last_active_members

    def accessibility(self, structure_id: str) -> float:
        """Return reversible access strength without changing stored memory."""
        return 1.0 - self._dormancy.get(structure_id, 0.0)

    def accessibility_map(self) -> dict[str, float]:
        """Return accessibility for every current graph structure."""
        identifiers = {
            *(assembly.assembly_id for assembly in self.graph.assemblies),
            *(link.link_id for link in self.graph.links),
            *(specialist.specialist_id for specialist in self.graph.specialists),
        }
        return {
            structure_id: self.accessibility(structure_id) for structure_id in sorted(identifiers)
        }

    def observe(
        self,
        *,
        assembly_id: str,
        unresolved_error: float,
        curiosity: float,
        ambition_relevance: float,
        capacity_saturation: float,
        residual_effect: float,
    ) -> AdaptiveUpdate:
        """Continue adaptive state from its restored values after one transition."""
        self.graph.assembly(assembly_id)
        for name, value in (
            ("unresolved_error", unresolved_error),
            ("curiosity", curiosity),
            ("ambition_relevance", ambition_relevance),
            ("capacity_saturation", capacity_saturation),
        ):
            _validate_unit(name, value)
        _validate_signed("residual_effect", residual_effect)

        pressure_before = self.pressure.value
        attempts_before = self.pressure.update_count
        eligibility_before = self._eligibility.get(assembly_id, 0.0)
        dormancy_before = self._dormancy.get(assembly_id, 0.0)

        for identifier in tuple(self._eligibility):
            self._eligibility[identifier] *= self.config.eligibility_decay
        self._eligibility[assembly_id] = min(
            1.0,
            self._eligibility.get(assembly_id, 0.0) + curiosity,
        )
        self._last_active_members = (assembly_id,)

        active_structures = {assembly_id}
        active_structures.update(
            link.link_id for link in self.graph.links if link.source_id == assembly_id
        )
        for structure_id in self.accessibility_map():
            current = self._dormancy.get(structure_id, 0.0)
            if structure_id in active_structures:
                self._dormancy[structure_id] = max(
                    0.0,
                    current - self.config.reactivation_amount,
                )
            else:
                self._dormancy[structure_id] = min(
                    1.0,
                    current + self.config.dormancy_increment,
                )

        self._residuals.append(residual_effect)
        if len(self._residuals) > self.config.residual_history_limit:
            del self._residuals[: -self.config.residual_history_limit]
        pressure_after = self.pressure.update(
            unresolved_error=unresolved_error,
            curiosity=curiosity,
            ambition_relevance=ambition_relevance,
            capacity_saturation=capacity_saturation,
            learning_rate=self.config.pressure_learning_rate,
        )
        return AdaptiveUpdate(
            assembly_id=assembly_id,
            pressure_before=pressure_before,
            pressure_after=pressure_after,
            attempt_count_before=attempts_before,
            attempt_count_after=self.pressure.update_count,
            eligibility_before=eligibility_before,
            eligibility_after=self._eligibility[assembly_id],
            dormancy_before=dormancy_before,
            dormancy_after=self._dormancy[assembly_id],
            residual_effect=residual_effect,
        )

    def to_growth_state(self) -> NDNRAGrowthState:
        """Freeze the currently operational state for another restart."""
        return NDNRAGrowthState(
            pressure=self.pressure.value,
            eligibility=self.eligibility,
            residuals=self.residuals,
            attempt_count=self.pressure.update_count,
            last_active_members=self._last_active_members,
            dormancy_levels=self.dormancy_levels,
        )

    def _validate_structure_references(self) -> None:
        assembly_ids = {assembly.assembly_id for assembly in self.graph.assemblies}
        invalid_eligibility = set(self._eligibility) - assembly_ids
        if invalid_eligibility:
            raise ValueError("persisted eligibility references unknown assemblies")
        structure_ids = {
            *assembly_ids,
            *(link.link_id for link in self.graph.links),
            *(specialist.specialist_id for specialist in self.graph.specialists),
        }
        invalid_dormancy = set(self._dormancy) - structure_ids
        if invalid_dormancy:
            raise ValueError("persisted dormancy references unknown structures")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _validate_signed(name: str, value: float) -> None:
    if not isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between negative one and one")
