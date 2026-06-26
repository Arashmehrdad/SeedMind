"""Tests for deterministic independent world processes."""

from dataclasses import replace

import pytest

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    AgentState,
    CyclicEntityPatrolProcess,
    DirectionalFlowProcess,
    EntityRole,
    EntityState,
    NurseryRuntime,
    NurseryState,
    PeriodicBlockingToggleProcess,
    TransitionOutcome,
    WorldProcessOutcome,
    WorldProcessPipeline,
)


def make_entity(
    entity_id: str,
    position: GridPosition,
    *,
    role: EntityRole = EntityRole.OBJECT,
    movable: bool = True,
    blocks_movement: bool = True,
) -> EntityState:
    return EntityState(
        entity_id=entity_id,
        role=role,
        position=position,
        blocks_movement=blocks_movement,
        movable=movable,
    )


def make_state(
    *entities: EntityState,
    agent_position: GridPosition | None = None,
    step_count: int = 0,
) -> NurseryState:
    body_position = GridPosition(0, 0) if agent_position is None else agent_position
    return NurseryState(
        width=6,
        height=6,
        agent=AgentState(
            position=body_position,
            orientation=Direction.EAST,
        ),
        entities=tuple(entities),
        step_count=step_count,
    )


def test_wait_tick_can_contain_teacher_motion() -> None:
    teacher = make_entity(
        "teacher",
        GridPosition(1, 1),
        role=EntityRole.TEACHER,
        movable=False,
    )
    patrol = CyclicEntityPatrolProcess(
        process_id="teacher-patrol",
        entity_id="teacher",
        route=(GridPosition(1, 1), GridPosition(2, 1)),
    )
    runtime = NurseryRuntime(
        initial_state=make_state(teacher),
        episode_id="episode-1",
        world_processes=(patrol,),
    )

    result = runtime.step(PrimitiveAction.WAIT)

    assert result.transition.outcome is TransitionOutcome.WAITED
    assert result.transition.world_changed is True
    assert result.external_world_changed is True
    assert runtime.state.agent.position == GridPosition(0, 0)
    assert runtime.state.entities[0].position == GridPosition(2, 1)
    assert runtime.state.step_count == 1
    assert result.process_events[0].outcome is WorldProcessOutcome.ENTITY_MOVED


def test_flow_moves_object_without_agent_contact() -> None:
    floating_object = make_entity("floating", GridPosition(1, 3))
    process = DirectionalFlowProcess(
        process_id="east-current",
        entity_ids=("floating",),
        direction=Direction.EAST,
    )
    runtime = NurseryRuntime(
        initial_state=make_state(floating_object),
        episode_id="episode-1",
        world_processes=(process,),
    )

    result = runtime.step(PrimitiveAction.WAIT)

    assert runtime.state.entities[0].position == GridPosition(2, 3)
    assert result.process_events[0].source_position == GridPosition(1, 3)
    assert result.process_events[0].destination_position == GridPosition(2, 3)


def test_processes_run_in_stable_order() -> None:
    first = make_entity("first", GridPosition(1, 2))
    second = make_entity("second", GridPosition(3, 2))
    pipeline = WorldProcessPipeline.from_sequence(
        (
            DirectionalFlowProcess(
                process_id="first-east",
                entity_ids=("first",),
                direction=Direction.EAST,
            ),
            DirectionalFlowProcess(
                process_id="second-west",
                entity_ids=("second",),
                direction=Direction.WEST,
            ),
        )
    )
    state = make_state(first, second, step_count=1)
    pipeline.validate(state)

    result = pipeline.advance(state)

    assert result.state.entities[0].position == GridPosition(2, 2)
    assert result.state.entities[1].position == GridPosition(3, 2)
    assert result.events[0].outcome is WorldProcessOutcome.ENTITY_MOVED
    assert result.events[1].outcome is WorldProcessOutcome.BLOCKED_ENTITY


def test_world_process_pipeline_does_not_advance_time() -> None:
    floating_object = make_entity("floating", GridPosition(1, 3))
    state = make_state(floating_object, step_count=4)
    pipeline = WorldProcessPipeline.from_sequence(
        (
            DirectionalFlowProcess(
                process_id="flow",
                entity_ids=("floating",),
                direction=Direction.EAST,
            ),
        )
    )
    pipeline.validate(state)

    result = pipeline.advance(state)

    assert result.state.step_count == 4


def test_periodic_mechanism_toggles_only_on_scheduled_ticks() -> None:
    door = make_entity(
        "door",
        GridPosition(3, 3),
        role=EntityRole.WALL,
        movable=False,
        blocks_movement=False,
    )
    toggle = PeriodicBlockingToggleProcess(
        process_id="door-clock",
        entity_id="door",
        period=2,
    )
    toggle.validate(make_state(door))

    inactive = toggle.advance(make_state(door, step_count=1))
    active = toggle.advance(make_state(door, step_count=2))

    assert inactive.state.entities[0].blocks_movement is False
    assert inactive.events == ()
    assert active.state.entities[0].blocks_movement is True
    assert active.events[0].outcome is WorldProcessOutcome.BLOCKING_ENABLED


def test_same_state_and_processes_produce_identical_result() -> None:
    floating_object = make_entity("floating", GridPosition(1, 3))
    state = make_state(floating_object, step_count=1)
    pipeline = WorldProcessPipeline.from_sequence(
        (
            DirectionalFlowProcess(
                process_id="flow",
                entity_ids=("floating",),
                direction=Direction.EAST,
            ),
        )
    )
    pipeline.validate(state)

    first = pipeline.advance(state)
    second = pipeline.advance(replace(state))

    assert first == second


def test_pipeline_rejects_duplicate_process_identifiers() -> None:
    floating_object = make_entity("floating", GridPosition(1, 3))
    pipeline = WorldProcessPipeline.from_sequence(
        (
            DirectionalFlowProcess(
                process_id="duplicate",
                entity_ids=("floating",),
                direction=Direction.EAST,
            ),
            DirectionalFlowProcess(
                process_id="duplicate",
                entity_ids=("floating",),
                direction=Direction.WEST,
            ),
        )
    )

    with pytest.raises(ValueError, match="unique"):
        pipeline.validate(make_state(floating_object))
