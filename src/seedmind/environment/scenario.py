"""Deterministic scenario construction and evaluation for Nursery v0."""

from dataclasses import dataclass
from random import Random

from seedmind.contracts import Direction, GridPosition
from seedmind.environment.entities import (
    AgentState,
    EntityRole,
    EntityState,
    ShapeCode,
)
from seedmind.environment.processes import WorldProcess, WorldProcessPipeline
from seedmind.environment.state import NurseryState


@dataclass(frozen=True, slots=True)
class TargetOccupancy:
    """Internal evaluation result for object occupancy of target cells."""

    target_count: int
    occupied_target_ids: tuple[str, ...]
    object_target_pairs: tuple[tuple[str, str], ...]

    @property
    def occupied_count(self) -> int:
        """Return the number of targets occupied by at least one object."""
        return len(self.occupied_target_ids)

    @property
    def all_targets_occupied(self) -> bool:
        """Return whether every configured target contains an object."""
        return self.target_count > 0 and self.occupied_count == self.target_count


def detect_target_occupancy(state: NurseryState) -> TargetOccupancy:
    """Evaluate target occupancy using internal roles only."""
    targets = tuple(entity for entity in state.entities if entity.role is EntityRole.TARGET)
    objects = tuple(entity for entity in state.entities if entity.role is EntityRole.OBJECT)
    occupied_target_ids: list[str] = []
    object_target_pairs: list[tuple[str, str]] = []

    for target in targets:
        colocated = tuple(entity for entity in objects if entity.position == target.position)

        if colocated:
            occupied_target_ids.append(target.entity_id)
            object_target_pairs.extend((entity.entity_id, target.entity_id) for entity in colocated)

    return TargetOccupancy(
        target_count=len(targets),
        occupied_target_ids=tuple(occupied_target_ids),
        object_target_pairs=tuple(object_target_pairs),
    )


@dataclass(frozen=True, slots=True)
class NurseryScenario:
    """Immutable deterministic nursery baseline and resource boundary."""

    scenario_id: str
    seed: int
    initial_state: NurseryState
    step_budget: int
    world_processes: tuple[WorldProcess, ...] = ()

    def __post_init__(self) -> None:
        """Validate scenario identity, baseline state, and resource budget."""
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")

        if self.seed < 0:
            raise ValueError("seed must not be negative")

        if self.step_budget <= 0:
            raise ValueError("step_budget must be positive")

        if self.initial_state.step_count != 0:
            raise ValueError("initial_state step_count must be zero")

        if self.initial_state.terminated:
            raise ValueError("initial_state must not be terminated")

        WorldProcessPipeline(self.world_processes).validate(self.initial_state)

    def remaining_steps(self, state: NurseryState) -> int:
        """Return the non-negative number of steps left in this scenario."""
        return max(self.step_budget - state.step_count, 0)

    def resource_state(self, state: NurseryState) -> tuple[float, ...]:
        """Return normalized remaining step budget as a raw resource channel."""
        return (self.remaining_steps(state) / self.step_budget,)

    def target_occupancy(self, state: NurseryState) -> TargetOccupancy:
        """Return internal target occupancy for evaluation and evidence."""
        return detect_target_occupancy(state)


@dataclass(frozen=True, slots=True)
class NurseryScenarioFactory:
    """Create reproducible symbolic Nursery v0 layouts from integer seeds."""

    width: int = 7
    height: int = 7
    step_budget: int = 150

    def __post_init__(self) -> None:
        """Validate enough interior capacity for the fixed nursery entities."""
        if self.width < 5 or self.height < 5:
            raise ValueError("Scenario dimensions must be at least 5 by 5")

        if self.step_budget <= 0:
            raise ValueError("step_budget must be positive")

    def create(self, seed: int) -> NurseryScenario:
        """Create one deterministic scenario without changing global RNG state."""
        if seed < 0:
            raise ValueError("seed must not be negative")

        rng = Random(seed)
        selected = rng.sample(self._interior_positions(), k=6)
        agent_position, teacher_position, *remaining = selected
        object_positions = remaining[:2]
        target_positions = remaining[2:]
        orientation = rng.choice(tuple(Direction))
        entities = (
            *self._wall_entities(),
            EntityState(
                entity_id="teacher_0",
                role=EntityRole.TEACHER,
                position=teacher_position,
                blocks_movement=True,
                movable=False,
            ),
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=object_positions[0],
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ROUND,
            ),
            EntityState(
                entity_id="object_1",
                role=EntityRole.OBJECT,
                position=object_positions[1],
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ANGULAR,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=target_positions[0],
                blocks_movement=False,
                movable=False,
            ),
            EntityState(
                entity_id="target_1",
                role=EntityRole.TARGET,
                position=target_positions[1],
                blocks_movement=False,
                movable=False,
            ),
        )
        state = NurseryState(
            width=self.width,
            height=self.height,
            agent=AgentState(
                position=agent_position,
                orientation=orientation,
            ),
            entities=entities,
        )
        return NurseryScenario(
            scenario_id=f"nursery-v0-seed-{seed}",
            seed=seed,
            initial_state=state,
            step_budget=self.step_budget,
        )

    def _interior_positions(self) -> list[GridPosition]:
        """Return all non-wall cells in stable row-major order."""
        return [
            GridPosition(x=x, y=y)
            for y in range(1, self.height - 1)
            for x in range(1, self.width - 1)
        ]

    def _wall_entities(self) -> tuple[EntityState, ...]:
        """Return stable row-major perimeter walls."""
        positions = (
            GridPosition(x=x, y=y)
            for y in range(self.height)
            for x in range(self.width)
            if x in (0, self.width - 1) or y in (0, self.height - 1)
        )
        return tuple(
            EntityState(
                entity_id=f"wall_{index:03d}",
                role=EntityRole.WALL,
                position=position,
                blocks_movement=True,
                movable=False,
            )
            for index, position in enumerate(positions)
        )
