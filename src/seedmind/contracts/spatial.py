"""Body-independent spatial contracts for the symbolic nursery."""

from dataclasses import dataclass
from enum import IntEnum


class Direction(IntEnum):
    """Cardinal orientation represented as clockwise quarter turns."""

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    def turn_left(self) -> "Direction":
        """Return the orientation after one left turn."""
        return Direction((int(self) - 1) % 4)

    def turn_right(self) -> "Direction":
        """Return the orientation after one right turn."""
        return Direction((int(self) + 1) % 4)

    @property
    def delta(self) -> tuple[int, int]:
        """Return the grid displacement associated with this direction."""
        deltas = {
            Direction.NORTH: (0, -1),
            Direction.EAST: (1, 0),
            Direction.SOUTH: (0, 1),
            Direction.WEST: (-1, 0),
        }
        return deltas[self]


@dataclass(frozen=True, slots=True)
class GridPosition:
    """Immutable position in a two-dimensional grid."""

    x: int
    y: int

    def translated(self, dx: int, dy: int) -> "GridPosition":
        """Return a new position translated by the supplied displacement."""
        return GridPosition(
            x=self.x + dx,
            y=self.y + dy,
        )

    def moved(self, direction: Direction) -> "GridPosition":
        """Return a new position moved one cell in the supplied direction."""
        dx, dy = direction.delta
        return self.translated(dx=dx, dy=dy)
