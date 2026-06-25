"""Internal entities used by the symbolic SeedMind nursery."""

from dataclasses import dataclass, replace
from enum import IntEnum, StrEnum

from seedmind.contracts import Direction, GridPosition


class EntityRole(StrEnum):
    """Internal environment role, not exposed directly to SeedMind."""

    TEACHER = "teacher"
    OBJECT = "object"
    TARGET = "target"
    WALL = "wall"


class ShapeCode(IntEnum):
    """Raw symbolic shape channel used by nursery objects."""

    NONE = 0
    ROUND = 1
    ANGULAR = 2


@dataclass(frozen=True, slots=True)
class AgentState:
    """Physical state of the body controlled by SeedMind."""

    position: GridPosition
    orientation: Direction

    def turned_left(self) -> "AgentState":
        """Return the body state after a left turn."""
        return replace(
            self,
            orientation=self.orientation.turn_left(),
        )

    def turned_right(self) -> "AgentState":
        """Return the body state after a right turn."""
        return replace(
            self,
            orientation=self.orientation.turn_right(),
        )

    def moved_forward(self) -> "AgentState":
        """Return the body state after moving one cell forward."""
        return replace(
            self,
            position=self.position.moved(self.orientation),
        )


@dataclass(frozen=True, slots=True)
class EntityState:
    """Immutable internal state of one nursery entity."""

    entity_id: str
    role: EntityRole
    position: GridPosition
    blocks_movement: bool
    movable: bool
    shape_code: ShapeCode = ShapeCode.NONE

    def __post_init__(self) -> None:
        """Validate stable entity identity."""
        if not self.entity_id.strip():
            raise ValueError("entity_id must not be empty")

    def moved_to(self, position: GridPosition) -> "EntityState":
        """Return the entity at a new position when movement is allowed."""
        if not self.movable:
            raise ValueError(f"Entity {self.entity_id!r} is not movable")

        return replace(
            self,
            position=position,
        )