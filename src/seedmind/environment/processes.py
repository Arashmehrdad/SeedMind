"""Deterministic world processes that advance within a nursery tick."""

from collections.abc import Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import Protocol

from seedmind.contracts import Direction, GridPosition
from seedmind.environment.entities import EntityState
from seedmind.environment.state import NurseryState


class WorldProcessOutcome(StrEnum):
    """Internal diagnostic outcome from an independent world process."""

    ENTITY_MOVED = "entity_moved"
    BLOCKED_BOUNDARY = "blocked_boundary"
    BLOCKED_AGENT = "blocked_agent"
    BLOCKED_ENTITY = "blocked_entity"
    BLOCKING_ENABLED = "blocking_enabled"
    BLOCKING_DISABLED = "blocking_disabled"
    ROUTE_MISMATCH = "route_mismatch"


@dataclass(frozen=True, slots=True)
class WorldProcessEvent:
    """One internal event produced while advancing world processes."""

    process_id: str
    entity_id: str
    outcome: WorldProcessOutcome
    source_position: GridPosition
    destination_position: GridPosition
    changed: bool

    def __post_init__(self) -> None:
        """Validate stable diagnostic identities."""
        if not self.process_id.strip():
            raise ValueError("process_id must not be empty")

        if not self.entity_id.strip():
            raise ValueError("entity_id must not be empty")


@dataclass(frozen=True, slots=True)
class WorldProcessResult:
    """Final state and ordered diagnostics from one process pipeline."""

    state: NurseryState
    events: tuple[WorldProcessEvent, ...] = ()

    @property
    def world_changed(self) -> bool:
        """Return whether any independent process changed the world."""
        return any(event.changed for event in self.events)


class WorldProcess(Protocol):
    """Contract for a deterministic process that runs after the agent action."""

    @property
    def process_id(self) -> str:
        """Return the stable process identifier."""
        ...

    def validate(self, state: NurseryState) -> None:
        """Validate process configuration against an initial nursery state."""
        ...

    def advance(self, state: NurseryState) -> WorldProcessResult:
        """Advance the process within the current simulation tick."""
        ...


@dataclass(frozen=True, slots=True)
class WorldProcessPipeline:
    """Run independent processes in a stable, explicitly ordered sequence."""

    processes: tuple[WorldProcess, ...] = ()

    @classmethod
    def from_sequence(
        cls,
        processes: Sequence[WorldProcess],
    ) -> "WorldProcessPipeline":
        """Freeze an external sequence into deterministic process order."""
        return cls(processes=tuple(processes))

    def validate(self, state: NurseryState) -> None:
        """Validate unique process identities and each process configuration."""
        process_ids = [process.process_id for process in self.processes]

        if len(process_ids) != len(set(process_ids)):
            raise ValueError("World process identifiers must be unique")

        for process in self.processes:
            if not process.process_id.strip():
                raise ValueError("process_id must not be empty")
            process.validate(state)

    def advance(self, state: NurseryState) -> WorldProcessResult:
        """Advance every process once without incrementing simulation time."""
        current_state = state
        events: list[WorldProcessEvent] = []

        for process in self.processes:
            result = process.advance(current_state)

            if result.state.step_count != state.step_count:
                raise ValueError("World processes must not advance step_count")

            current_state = result.state
            events.extend(result.events)

        return WorldProcessResult(
            state=current_state,
            events=tuple(events),
        )


@dataclass(frozen=True, slots=True)
class CyclicEntityPatrolProcess:
    """Move one autonomous entity around an adjacent cyclic route."""

    process_id: str
    entity_id: str
    route: tuple[GridPosition, ...]
    period: int = 1

    def __post_init__(self) -> None:
        """Validate static patrol configuration."""
        if not self.process_id.strip():
            raise ValueError("process_id must not be empty")

        if not self.entity_id.strip():
            raise ValueError("entity_id must not be empty")

        if len(self.route) < 2:
            raise ValueError("route must contain at least two positions")

        if len(self.route) != len(set(self.route)):
            raise ValueError("route positions must be unique")

        if self.period <= 0:
            raise ValueError("period must be positive")

        wrapped_route = (*self.route[1:], self.route[0])
        for source, destination in zip(self.route, wrapped_route, strict=True):
            distance = abs(source.x - destination.x) + abs(source.y - destination.y)
            if distance != 1:
                raise ValueError("consecutive patrol positions must be adjacent")

    def validate(self, state: NurseryState) -> None:
        """Validate the entity and route against the initial state."""
        entity = _entity_by_id(state, self.entity_id)

        if entity.position not in self.route:
            raise ValueError("patrol entity must start on its route")

        if any(not state.is_in_bounds(position) for position in self.route):
            raise ValueError("patrol route must stay inside the nursery")

    def advance(self, state: NurseryState) -> WorldProcessResult:
        """Attempt one adjacent patrol move on scheduled ticks."""
        if state.step_count % self.period != 0:
            return WorldProcessResult(state=state)

        entity = _entity_by_id(state, self.entity_id)

        try:
            route_index = self.route.index(entity.position)
        except ValueError:
            event = WorldProcessEvent(
                process_id=self.process_id,
                entity_id=self.entity_id,
                outcome=WorldProcessOutcome.ROUTE_MISMATCH,
                source_position=entity.position,
                destination_position=entity.position,
                changed=False,
            )
            return WorldProcessResult(state=state, events=(event,))

        destination = self.route[(route_index + 1) % len(self.route)]
        blocked_outcome = _movement_blocked_outcome(
            state,
            entity_id=self.entity_id,
            destination=destination,
        )

        if blocked_outcome is not None:
            return WorldProcessResult(
                state=state,
                events=(
                    _movement_event(
                        process_id=self.process_id,
                        entity=entity,
                        destination=destination,
                        outcome=blocked_outcome,
                        changed=False,
                    ),
                ),
            )

        moved_entity = replace(entity, position=destination)
        updated_state = state.replace_entity(self.entity_id, moved_entity)
        return WorldProcessResult(
            state=updated_state,
            events=(
                _movement_event(
                    process_id=self.process_id,
                    entity=entity,
                    destination=destination,
                    outcome=WorldProcessOutcome.ENTITY_MOVED,
                    changed=True,
                ),
            ),
        )


@dataclass(frozen=True, slots=True)
class DirectionalFlowProcess:
    """Move configured movable entities one cell in a fixed direction."""

    process_id: str
    entity_ids: tuple[str, ...]
    direction: Direction
    period: int = 1

    def __post_init__(self) -> None:
        """Validate static flow configuration."""
        if not self.process_id.strip():
            raise ValueError("process_id must not be empty")

        if not self.entity_ids:
            raise ValueError("entity_ids must not be empty")

        if len(self.entity_ids) != len(set(self.entity_ids)):
            raise ValueError("entity_ids must be unique")

        if any(not entity_id.strip() for entity_id in self.entity_ids):
            raise ValueError("entity_ids must not contain empty values")

        if self.period <= 0:
            raise ValueError("period must be positive")

    def validate(self, state: NurseryState) -> None:
        """Require every flow-controlled entity to be agent-pushable."""
        for entity_id in self.entity_ids:
            entity = _entity_by_id(state, entity_id)
            if not entity.movable:
                raise ValueError("flow-controlled entities must be movable")

    def advance(self, state: NurseryState) -> WorldProcessResult:
        """Move configured entities in stable order on scheduled ticks."""
        if state.step_count % self.period != 0:
            return WorldProcessResult(state=state)

        current_state = state
        events: list[WorldProcessEvent] = []

        for entity_id in self.entity_ids:
            entity = _entity_by_id(current_state, entity_id)
            destination = entity.position.moved(self.direction)
            blocked_outcome = _movement_blocked_outcome(
                current_state,
                entity_id=entity_id,
                destination=destination,
            )

            if blocked_outcome is not None:
                events.append(
                    _movement_event(
                        process_id=self.process_id,
                        entity=entity,
                        destination=destination,
                        outcome=blocked_outcome,
                        changed=False,
                    )
                )
                continue

            moved_entity = replace(entity, position=destination)
            current_state = current_state.replace_entity(entity_id, moved_entity)
            events.append(
                _movement_event(
                    process_id=self.process_id,
                    entity=entity,
                    destination=destination,
                    outcome=WorldProcessOutcome.ENTITY_MOVED,
                    changed=True,
                )
            )

        return WorldProcessResult(
            state=current_state,
            events=tuple(events),
        )


@dataclass(frozen=True, slots=True)
class PeriodicBlockingToggleProcess:
    """Toggle whether one mechanism blocks movement on scheduled ticks."""

    process_id: str
    entity_id: str
    period: int = 2

    def __post_init__(self) -> None:
        """Validate static toggle configuration."""
        if not self.process_id.strip():
            raise ValueError("process_id must not be empty")

        if not self.entity_id.strip():
            raise ValueError("entity_id must not be empty")

        if self.period <= 0:
            raise ValueError("period must be positive")

    def validate(self, state: NurseryState) -> None:
        """Validate that the configured mechanism exists."""
        _entity_by_id(state, self.entity_id)

    def advance(self, state: NurseryState) -> WorldProcessResult:
        """Toggle blocking state without moving the mechanism."""
        if state.step_count % self.period != 0:
            return WorldProcessResult(state=state)

        entity = _entity_by_id(state, self.entity_id)
        enabling = not entity.blocks_movement

        if enabling and state.agent.position == entity.position:
            event = _movement_event(
                process_id=self.process_id,
                entity=entity,
                destination=entity.position,
                outcome=WorldProcessOutcome.BLOCKED_AGENT,
                changed=False,
            )
            return WorldProcessResult(state=state, events=(event,))

        if enabling and any(
            other.entity_id != self.entity_id
            and other.position == entity.position
            and other.blocks_movement
            for other in state.entities
        ):
            event = _movement_event(
                process_id=self.process_id,
                entity=entity,
                destination=entity.position,
                outcome=WorldProcessOutcome.BLOCKED_ENTITY,
                changed=False,
            )
            return WorldProcessResult(state=state, events=(event,))

        updated_entity = replace(entity, blocks_movement=enabling)
        updated_state = state.replace_entity(self.entity_id, updated_entity)
        outcome = (
            WorldProcessOutcome.BLOCKING_ENABLED
            if enabling
            else WorldProcessOutcome.BLOCKING_DISABLED
        )
        event = _movement_event(
            process_id=self.process_id,
            entity=entity,
            destination=entity.position,
            outcome=outcome,
            changed=True,
        )
        return WorldProcessResult(state=updated_state, events=(event,))


def _entity_by_id(state: NurseryState, entity_id: str) -> EntityState:
    for entity in state.entities:
        if entity.entity_id == entity_id:
            return entity

    raise ValueError(f"Unknown world-process entity: {entity_id!r}")


def _movement_blocked_outcome(
    state: NurseryState,
    *,
    entity_id: str,
    destination: GridPosition,
) -> WorldProcessOutcome | None:
    if not state.is_in_bounds(destination):
        return WorldProcessOutcome.BLOCKED_BOUNDARY

    if state.agent.position == destination:
        return WorldProcessOutcome.BLOCKED_AGENT

    if any(
        entity.entity_id != entity_id and entity.position == destination and entity.blocks_movement
        for entity in state.entities
    ):
        return WorldProcessOutcome.BLOCKED_ENTITY

    return None


def _movement_event(
    *,
    process_id: str,
    entity: EntityState,
    destination: GridPosition,
    outcome: WorldProcessOutcome,
    changed: bool,
) -> WorldProcessEvent:
    return WorldProcessEvent(
        process_id=process_id,
        entity_id=entity.entity_id,
        outcome=outcome,
        source_position=entity.position,
        destination_position=destination,
        changed=changed,
    )
