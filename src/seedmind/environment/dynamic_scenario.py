"""Reproducible Nursery v0 scenario with independent world processes."""

from dataclasses import dataclass
from random import Random

from seedmind.contracts import Direction, GridPosition
from seedmind.environment.entities import (
    AgentState,
    EntityRole,
    EntityState,
    ShapeCode,
)
from seedmind.environment.processes import (
    CyclicEntityPatrolProcess,
    DirectionalFlowProcess,
    PeriodicBlockingToggleProcess,
)
from seedmind.environment.scenario import NurseryScenario
from seedmind.environment.state import NurseryState


@dataclass(frozen=True, slots=True)
class DynamicNurseryScenarioFactory:
    """Build a deterministic nursery where the world changes independently."""

    width: int = 7
    height: int = 7
    step_budget: int = 150

    def __post_init__(self) -> None:
        """Validate enough space for separated dynamic mechanisms."""
        if self.width < 7 or self.height < 7:
            raise ValueError("Dynamic scenario dimensions must be at least 7 by 7")

        if self.step_budget <= 0:
            raise ValueError("step_budget must be positive")

    def create(self, seed: int) -> NurseryScenario:
        """Create one seeded dynamic scenario with three external processes."""
        if seed < 0:
            raise ValueError("seed must not be negative")

        rng = Random(seed)
        base_route = (
            GridPosition(2, 2),
            GridPosition(3, 2),
            GridPosition(3, 3),
            GridPosition(2, 3),
        )
        route_offset = rng.randrange(len(base_route))
        patrol_route = (
            *base_route[route_offset:],
            *base_route[:route_offset],
        )
        teacher_position = patrol_route[0]
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
                position=GridPosition(1, 4),
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ROUND,
            ),
            EntityState(
                entity_id="object_1",
                role=EntityRole.OBJECT,
                position=GridPosition(4, 1),
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ANGULAR,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=GridPosition(5, 4),
                blocks_movement=False,
                movable=False,
            ),
            EntityState(
                entity_id="target_1",
                role=EntityRole.TARGET,
                position=GridPosition(5, 1),
                blocks_movement=False,
                movable=False,
            ),
            EntityState(
                entity_id="door_0",
                role=EntityRole.WALL,
                position=GridPosition(4, 3),
                blocks_movement=False,
                movable=False,
            ),
        )
        state = NurseryState(
            width=self.width,
            height=self.height,
            agent=AgentState(
                position=GridPosition(1, 1),
                orientation=rng.choice(tuple(Direction)),
            ),
            entities=entities,
        )
        world_processes = (
            CyclicEntityPatrolProcess(
                process_id="teacher-patrol",
                entity_id="teacher_0",
                route=patrol_route,
                period=1,
            ),
            DirectionalFlowProcess(
                process_id="east-current",
                entity_ids=("object_0",),
                direction=Direction.EAST,
                period=1,
            ),
            PeriodicBlockingToggleProcess(
                process_id="door-clock",
                entity_id="door_0",
                period=2,
            ),
        )
        return NurseryScenario(
            scenario_id=f"nursery-v0-dynamic-seed-{seed}",
            seed=seed,
            initial_state=state,
            step_budget=self.step_budget,
            world_processes=world_processes,
        )

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
