"""Tests for deterministic Nursery v0 world state."""

import pytest

from seedmind.contracts import Direction, GridPosition
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    NurseryState,
    ShapeCode,
)


def create_state() -> NurseryState:
    return NurseryState(
        width=6,
        height=6,
        agent=AgentState(
            position=GridPosition(1, 1),
            orientation=Direction.EAST,
        ),
        entities=(
            EntityState(
                entity_id="object_1",
                role=EntityRole.OBJECT,
                position=GridPosition(2, 1),
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ROUND,
            ),
            EntityState(
                entity_id="target_1",
                role=EntityRole.TARGET,
                position=GridPosition(4, 1),
                blocks_movement=False,
                movable=False,
            ),
        ),
    )


def test_state_finds_entities_in_stable_order() -> None:
    state = create_state()

    entities = state.entities_at(GridPosition(2, 1))

    assert tuple(entity.entity_id for entity in entities) == ("object_1",)


def test_state_finds_blocking_entity() -> None:
    state = create_state()

    entity = state.blocking_entity_at(GridPosition(2, 1))

    assert entity is not None
    assert entity.entity_id == "object_1"


def test_state_replaces_entity_deterministically() -> None:
    state = create_state()
    original = state.entities[0]
    replacement = original.moved_to(GridPosition(3, 1))

    updated = state.replace_entity(
        entity_id="object_1",
        replacement=replacement,
    )

    assert updated.entities[0].position == GridPosition(3, 1)
    assert state.entities[0].position == GridPosition(2, 1)


def test_state_advances_one_step() -> None:
    state = create_state()

    advanced = state.advanced()

    assert advanced.step_count == 1
    assert state.step_count == 0


def test_state_rejects_duplicate_entity_ids() -> None:
    state = create_state()

    with pytest.raises(ValueError, match="identifiers must be unique"):
        NurseryState(
            width=state.width,
            height=state.height,
            agent=state.agent,
            entities=(state.entities[0], state.entities[0]),
        )


def test_state_rejects_out_of_bounds_agent() -> None:
    with pytest.raises(ValueError, match="Agent position"):
        NurseryState(
            width=5,
            height=5,
            agent=AgentState(
                position=GridPosition(5, 1),
                orientation=Direction.NORTH,
            ),
            entities=(),
        )


def test_replacement_must_preserve_identity() -> None:
    state = create_state()

    replacement = EntityState(
        entity_id="different_id",
        role=EntityRole.OBJECT,
        position=GridPosition(3, 1),
        blocks_movement=True,
        movable=True,
    )

    with pytest.raises(ValueError, match="preserve entity_id"):
        state.replace_entity(
            entity_id="object_1",
            replacement=replacement,
        )