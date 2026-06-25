"""Tests for symbolic spatial contracts."""

from dataclasses import FrozenInstanceError

import pytest

from seedmind.contracts import Direction, GridPosition


def test_turning_right_cycles_clockwise() -> None:
    direction = Direction.NORTH

    for _ in range(4):
        direction = direction.turn_right()

    assert direction is Direction.NORTH


def test_turning_left_cycles_counterclockwise() -> None:
    assert Direction.NORTH.turn_left() is Direction.WEST
    assert Direction.WEST.turn_left() is Direction.SOUTH


@pytest.mark.parametrize(
    ("direction", "expected"),
    [
        (Direction.NORTH, GridPosition(3, 2)),
        (Direction.EAST, GridPosition(4, 3)),
        (Direction.SOUTH, GridPosition(3, 4)),
        (Direction.WEST, GridPosition(2, 3)),
    ],
)
def test_position_moves_one_cell(
    direction: Direction,
    expected: GridPosition,
) -> None:
    position = GridPosition(3, 3)

    assert position.moved(direction) == expected


def test_position_is_immutable() -> None:
    position = GridPosition(1, 2)

    with pytest.raises(FrozenInstanceError):
        position.__setattr__("x", 5)
