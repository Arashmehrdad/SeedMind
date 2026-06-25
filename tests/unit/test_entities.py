"""Tests for nursery entities and agent body state."""

import pytest

from seedmind.contracts import Direction, GridPosition
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    ShapeCode,
)


def test_agent_turns_without_changing_position() -> None:
    agent = AgentState(
        position=GridPosition(2, 2),
        orientation=Direction.NORTH,
    )

    turned = agent.turned_right()

    assert turned.position == agent.position
    assert turned.orientation is Direction.EAST


def test_agent_moves_in_current_orientation() -> None:
    agent = AgentState(
        position=GridPosition(2, 2),
        orientation=Direction.WEST,
    )

    moved = agent.moved_forward()

    assert moved.position == GridPosition(1, 2)
    assert moved.orientation is Direction.WEST


def test_movable_entity_returns_updated_copy() -> None:
    entity = EntityState(
        entity_id="object_1",
        role=EntityRole.OBJECT,
        position=GridPosition(2, 2),
        blocks_movement=True,
        movable=True,
        shape_code=ShapeCode.ROUND,
    )

    moved = entity.moved_to(GridPosition(3, 2))

    assert moved.position == GridPosition(3, 2)
    assert entity.position == GridPosition(2, 2)


def test_non_movable_entity_rejects_movement() -> None:
    wall = EntityState(
        entity_id="wall_1",
        role=EntityRole.WALL,
        position=GridPosition(0, 0),
        blocks_movement=True,
        movable=False,
    )

    with pytest.raises(ValueError, match="not movable"):
        wall.moved_to(GridPosition(1, 0))


def test_entity_requires_identifier() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        EntityState(
            entity_id=" ",
            role=EntityRole.TARGET,
            position=GridPosition(1, 1),
            blocks_movement=False,
            movable=False,
        )