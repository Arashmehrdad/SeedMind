"""Immutable deterministic world state for SeedMind Nursery v0."""

from dataclasses import dataclass, replace

from seedmind.contracts import GridPosition
from seedmind.environment.entities import AgentState, EntityState


@dataclass(frozen=True, slots=True)
class NurseryState:
    """Complete internal state of one nursery timestep."""

    width: int
    height: int
    agent: AgentState
    entities: tuple[EntityState, ...]
    step_count: int = 0
    terminated: bool = False

    def __post_init__(self) -> None:
        """Validate dimensions, identities, positions, and counters."""
        if self.width < 3 or self.height < 3:
            raise ValueError("Nursery dimensions must be at least 3 by 3")

        if self.step_count < 0:
            raise ValueError("step_count must not be negative")

        entity_ids = [entity.entity_id for entity in self.entities]

        if len(entity_ids) != len(set(entity_ids)):
            raise ValueError("Entity identifiers must be unique")

        if not self.is_in_bounds(self.agent.position):
            raise ValueError("Agent position is outside the nursery")

        for entity in self.entities:
            if not self.is_in_bounds(entity.position):
                raise ValueError(
                    f"Entity {entity.entity_id!r} is outside the nursery"
                )

    def is_in_bounds(self, position: GridPosition) -> bool:
        """Return whether a position is inside the nursery grid."""
        return (
            0 <= position.x < self.width
            and 0 <= position.y < self.height
        )

    def entities_at(
        self,
        position: GridPosition,
    ) -> tuple[EntityState, ...]:
        """Return all entities occupying a position in stable order."""
        return tuple(
            entity
            for entity in self.entities
            if entity.position == position
        )

    def blocking_entity_at(
        self,
        position: GridPosition,
    ) -> EntityState | None:
        """Return the first movement-blocking entity at a position."""
        for entity in self.entities:
            if entity.position == position and entity.blocks_movement:
                return entity

        return None

    def with_agent(self, agent: AgentState) -> "NurseryState":
        """Return the state with an updated agent body."""
        return replace(
            self,
            agent=agent,
        )

    def replace_entity(
        self,
        entity_id: str,
        replacement: EntityState,
    ) -> "NurseryState":
        """Replace one entity while preserving stable identity."""
        if replacement.entity_id != entity_id:
            raise ValueError("Replacement must preserve entity_id")

        found = False
        updated_entities: list[EntityState] = []

        for entity in self.entities:
            if entity.entity_id == entity_id:
                updated_entities.append(replacement)
                found = True
            else:
                updated_entities.append(entity)

        if not found:
            raise KeyError(entity_id)

        return replace(
            self,
            entities=tuple(updated_entities),
        )

    def advanced(self) -> "NurseryState":
        """Return the state advanced by one deterministic timestep."""
        return replace(
            self,
            step_count=self.step_count + 1,
        )