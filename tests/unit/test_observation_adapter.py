"""Tests for the deterministic nursery observation adapter."""

from dataclasses import replace

import pytest

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    NurseryObservationAdapter,
    NurseryState,
    ShapeCode,
)


def create_state(*, terminated: bool = False) -> NurseryState:
    return NurseryState(
        width=3,
        height=3,
        agent=AgentState(
            position=GridPosition(1, 1),
            orientation=Direction.EAST,
        ),
        entities=(
            EntityState(
                entity_id="entity-a",
                role=EntityRole.OBJECT,
                position=GridPosition(2, 0),
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ROUND,
            ),
        ),
        step_count=4,
        terminated=terminated,
    )


def test_adapter_emits_fixed_deterministic_layout() -> None:
    adapter = NurseryObservationAdapter(width=3, height=3)
    state = create_state()

    first = adapter.observe(state, episode_id="episode-1")
    second = adapter.observe(state, episode_id="episode-1")

    assert first == second
    assert len(first.sensor_values) == adapter.sensor_size == 42
    assert first.sensor_values[:6] == (0.5, 0.5, 0.0, 1.0, 0.0, 0.0)

    cell_offset = 6 + ((0 * 3 + 2) * 4)
    assert first.sensor_values[cell_offset : cell_offset + 4] == (
        1.0,
        1.0,
        1.0,
        0.5,
    )


def test_adapter_passes_through_raw_auxiliary_channels() -> None:
    adapter = NurseryObservationAdapter(width=3, height=3)

    packet = adapter.observe(
        create_state(),
        episode_id="episode-1",
        timestamp=9,
        human_signal=(0.0, 1.0),
        resource_state=(0.75,),
    )

    assert packet.timestamp == 9
    assert packet.step_id == 4
    assert packet.human_signal == (0.0, 1.0)
    assert packet.resource_state == (0.75,)


def test_active_state_exposes_all_primitive_actions_in_enum_order() -> None:
    adapter = NurseryObservationAdapter(width=3, height=3)

    packet = adapter.observe(create_state(), episode_id="episode-1")

    assert packet.available_actions == tuple(PrimitiveAction)


def test_terminated_state_exposes_only_stop() -> None:
    adapter = NurseryObservationAdapter(width=3, height=3)

    packet = adapter.observe(
        create_state(terminated=True),
        episode_id="episode-1",
    )

    assert packet.available_actions == (PrimitiveAction.STOP,)


def test_adapter_rejects_state_with_different_dimensions() -> None:
    adapter = NurseryObservationAdapter(width=4, height=4)

    with pytest.raises(ValueError, match="dimensions"):
        adapter.observe(create_state(), episode_id="episode-1")


def test_sensor_values_do_not_expose_entity_identity_or_role() -> None:
    adapter = NurseryObservationAdapter(width=3, height=3)
    original = create_state()
    original_entity = original.entities[0]
    relabelled_entity = replace(
        original_entity,
        entity_id="different-id",
        role=EntityRole.TEACHER,
    )
    relabelled = replace(original, entities=(relabelled_entity,))

    original_packet = adapter.observe(original, episode_id="episode-1")
    relabelled_packet = adapter.observe(relabelled, episode_id="episode-1")

    assert original_packet.sensor_values == relabelled_packet.sensor_values
