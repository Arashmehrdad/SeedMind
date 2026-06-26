"""Deterministic teacher demonstrations for SeedMind Nursery v0."""

from __future__ import annotations

from dataclasses import dataclass, replace

from seedmind.contracts import Direction, GridPosition
from seedmind.environment.entities import (
    AgentState,
    EntityRole,
    EntityState,
    ShapeCode,
)
from seedmind.environment.processes import (
    WorldProcessEvent,
    WorldProcessOutcome,
    WorldProcessResult,
)
from seedmind.environment.scenario import NurseryScenario
from seedmind.environment.state import NurseryState


@dataclass(frozen=True, slots=True)
class TeacherPushDemonstrationProcess:
    """Move a teacher and raw movable entity through one repeated outcome."""

    process_id: str
    teacher_id: str
    object_id: str
    target_id: str
    direction: Direction
    demonstration_steps: int = 2

    def __post_init__(self) -> None:
        for name, value in (
            ("process_id", self.process_id),
            ("teacher_id", self.teacher_id),
            ("object_id", self.object_id),
            ("target_id", self.target_id),
        ):
            if not value.strip():
                raise ValueError(f"{name} must not be empty")
        if self.demonstration_steps <= 0:
            raise ValueError("demonstration_steps must be positive")

    def validate(self, state: NurseryState) -> None:
        teacher = _entity_by_id(state, self.teacher_id)
        movable = _entity_by_id(state, self.object_id)
        target = _entity_by_id(state, self.target_id)
        if teacher.role is not EntityRole.TEACHER:
            raise ValueError("teacher_id must identify a teacher entity")
        if movable.role is not EntityRole.OBJECT or not movable.movable:
            raise ValueError("object_id must identify a movable object entity")
        if target.role is not EntityRole.TARGET:
            raise ValueError("target_id must identify a target entity")
        if teacher.position.moved(self.direction) != movable.position:
            raise ValueError("teacher must start directly behind the object")
        expected_target = movable.position
        for _ in range(self.demonstration_steps):
            expected_target = expected_target.moved(self.direction)
        if target.position != expected_target:
            raise ValueError("target must match the scripted demonstration endpoint")

    def advance(self, state: NurseryState) -> WorldProcessResult:
        if not 1 <= state.step_count <= self.demonstration_steps:
            return WorldProcessResult(state=state)
        teacher = _entity_by_id(state, self.teacher_id)
        movable = _entity_by_id(state, self.object_id)
        teacher_destination = movable.position
        object_destination = movable.position.moved(self.direction)
        if state.agent.position in (teacher_destination, object_destination):
            event = WorldProcessEvent(
                process_id=self.process_id,
                entity_id=self.object_id,
                outcome=WorldProcessOutcome.BLOCKED_AGENT,
                source_position=movable.position,
                destination_position=object_destination,
                changed=False,
            )
            return WorldProcessResult(state=state, events=(event,))
        blocker = next(
            (
                entity
                for entity in state.entities_at(object_destination)
                if entity.entity_id not in (self.teacher_id, self.object_id, self.target_id)
                and entity.blocks_movement
            ),
            None,
        )
        if blocker is not None:
            event = WorldProcessEvent(
                process_id=self.process_id,
                entity_id=self.object_id,
                outcome=WorldProcessOutcome.BLOCKED_ENTITY,
                source_position=movable.position,
                destination_position=object_destination,
                changed=False,
            )
            return WorldProcessResult(state=state, events=(event,))
        updated = state.replace_entity(
            self.teacher_id,
            replace(teacher, position=teacher_destination),
        )
        updated = updated.replace_entity(self.object_id, movable.moved_to(object_destination))
        return WorldProcessResult(
            state=updated,
            events=(
                WorldProcessEvent(
                    process_id=self.process_id,
                    entity_id=self.teacher_id,
                    outcome=WorldProcessOutcome.ENTITY_MOVED,
                    source_position=teacher.position,
                    destination_position=teacher_destination,
                    changed=True,
                ),
                WorldProcessEvent(
                    process_id=self.process_id,
                    entity_id=self.object_id,
                    outcome=WorldProcessOutcome.ENTITY_MOVED,
                    source_position=movable.position,
                    destination_position=object_destination,
                    changed=True,
                ),
            ),
        )


@dataclass(frozen=True, slots=True)
class TeacherDemonstrationScenarioFactory:
    """Create a repeatable raw object-control demonstration scenario."""

    width: int = 7
    height: int = 7
    step_budget: int = 8

    def __post_init__(self) -> None:
        if self.width < 7 or self.height < 7:
            raise ValueError("Teacher demonstration dimensions must be at least 7 by 7")
        if self.step_budget < 2:
            raise ValueError("step_budget must allow the two-step demonstration")

    def create(self, seed: int) -> NurseryScenario:
        if seed < 0:
            raise ValueError("seed must not be negative")
        entities = (
            *self._wall_entities(),
            EntityState(
                entity_id="teacher_0",
                role=EntityRole.TEACHER,
                position=GridPosition(1, 3),
                blocks_movement=True,
                movable=False,
            ),
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=GridPosition(2, 3),
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ROUND,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=GridPosition(4, 3),
                blocks_movement=False,
                movable=False,
            ),
        )
        initial_state = NurseryState(
            width=self.width,
            height=self.height,
            agent=AgentState(position=GridPosition(1, 1), orientation=Direction.NORTH),
            entities=entities,
        )
        process = TeacherPushDemonstrationProcess(
            process_id="teacher-push-demonstration",
            teacher_id="teacher_0",
            object_id="object_0",
            target_id="target_0",
            direction=Direction.EAST,
        )
        return NurseryScenario(
            scenario_id=f"nursery-v0-teacher-demo-seed-{seed}",
            seed=seed,
            initial_state=initial_state,
            step_budget=self.step_budget,
            world_processes=(process,),
        )

    def _wall_entities(self) -> tuple[EntityState, ...]:
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


def _entity_by_id(state: NurseryState, entity_id: str) -> EntityState:
    for entity in state.entities:
        if entity.entity_id == entity_id:
            return entity
    raise ValueError(f"Unknown teacher demonstration entity: {entity_id!r}")
