"""Tests for sequential SeedMind experience records."""

from dataclasses import replace

import pytest

from seedmind.contracts import (
    Direction,
    GridPosition,
    ObservationPacket,
    PrimitiveAction,
)
from seedmind.environment import (
    AgentState,
    CyclicEntityPatrolProcess,
    EntityRole,
    EntityState,
    NurseryRuntime,
    NurseryState,
)
from seedmind.training import ExperienceTransition, collect_experience


def create_runtime() -> NurseryRuntime:
    state = NurseryState(
        width=4,
        height=4,
        agent=AgentState(
            position=GridPosition(1, 1),
            orientation=Direction.EAST,
        ),
        entities=(),
    )
    return NurseryRuntime(initial_state=state, episode_id="episode-1")


def create_dynamic_runtime() -> NurseryRuntime:
    teacher = EntityState(
        entity_id="teacher",
        role=EntityRole.TEACHER,
        position=GridPosition(1, 2),
        blocks_movement=True,
        movable=False,
    )
    state = NurseryState(
        width=4,
        height=4,
        agent=AgentState(
            position=GridPosition(1, 1),
            orientation=Direction.EAST,
        ),
        entities=(teacher,),
    )
    patrol = CyclicEntityPatrolProcess(
        process_id="teacher-patrol",
        entity_id="teacher",
        route=(GridPosition(1, 2), GridPosition(2, 2)),
    )
    return NurseryRuntime(
        initial_state=state,
        episode_id="episode-1",
        world_processes=(patrol,),
    )


def create_packet(
    *,
    episode_id: str = "episode-1",
    step_id: int = 0,
    sensor_values: tuple[float, ...] = (0.0, 0.5),
    available_actions: tuple[PrimitiveAction, ...] = tuple(PrimitiveAction),
    human_signal: tuple[float, ...] = (),
    resource_state: tuple[float, ...] = (),
) -> ObservationPacket:
    return ObservationPacket(
        timestamp=step_id,
        episode_id=episode_id,
        step_id=step_id,
        sensor_values=sensor_values,
        available_actions=available_actions,
        human_signal=human_signal,
        resource_state=resource_state,
    )


def test_collect_experience_connects_two_observations_with_one_action() -> None:
    runtime = create_runtime()

    experience = collect_experience(runtime, PrimitiveAction.MOVE_FORWARD)

    assert experience.observation.step_id == 0
    assert experience.agent_observation.step_id == 1
    assert experience.next_observation.step_id == 1
    assert experience.action is PrimitiveAction.MOVE_FORWARD
    assert experience.terminated is False
    assert runtime.state.agent.position == GridPosition(2, 1)
    assert len(experience.sensor_change) == len(experience.observation.sensor_values)
    assert any(change != 0.0 for change in experience.sensor_change)


def test_collect_stop_records_episode_termination() -> None:
    runtime = create_runtime()

    experience = collect_experience(runtime, PrimitiveAction.STOP)

    assert experience.terminated is True
    assert runtime.state.terminated is True

    with pytest.raises(RuntimeError, match="termination"):
        collect_experience(runtime, PrimitiveAction.STOP)


def test_sensor_change_is_next_minus_current() -> None:
    observation = create_packet(sensor_values=(0.25, 0.75))
    agent_observation = create_packet(
        step_id=1,
        sensor_values=(0.25, 0.75),
    )
    next_observation = create_packet(
        step_id=1,
        sensor_values=(0.5, 0.25),
    )
    experience = ExperienceTransition(
        observation=observation,
        action=PrimitiveAction.WAIT,
        agent_observation=agent_observation,
        next_observation=next_observation,
        terminated=False,
    )

    assert experience.sensor_change == (0.25, -0.5)
    assert experience.controllable_sensor_change == (0.0, 0.0)
    assert experience.external_sensor_change == (0.25, -0.5)


def test_wait_separates_external_motion_from_controllable_change() -> None:
    experience = collect_experience(create_dynamic_runtime(), PrimitiveAction.WAIT)

    assert all(change == 0.0 for change in experience.controllable_sensor_change)
    assert any(change != 0.0 for change in experience.sensor_change)
    assert experience.external_sensor_change == experience.sensor_change


def test_move_separates_agent_and_external_changes() -> None:
    experience = collect_experience(
        create_dynamic_runtime(),
        PrimitiveAction.MOVE_FORWARD,
    )

    assert any(change != 0.0 for change in experience.controllable_sensor_change)
    assert any(change != 0.0 for change in experience.external_sensor_change)
    combined = tuple(
        controllable + external
        for controllable, external in zip(
            experience.controllable_sensor_change,
            experience.external_sensor_change,
            strict=True,
        )
    )
    assert combined == pytest.approx(experience.sensor_change)


@pytest.mark.parametrize(
    ("next_observation", "message"),
    [
        (create_packet(episode_id="episode-2", step_id=1), "one episode"),
        (create_packet(step_id=2), "exactly one step"),
        (create_packet(step_id=1, sensor_values=(0.0,)), "sensor width"),
        (create_packet(step_id=1, human_signal=(1.0,)), "human signal"),
        (create_packet(step_id=1, resource_state=(1.0,)), "resource state"),
    ],
)
def test_experience_rejects_invalid_transition_contract(
    next_observation: ObservationPacket,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        ExperienceTransition(
            observation=create_packet(),
            action=PrimitiveAction.WAIT,
            agent_observation=create_packet(step_id=1),
            next_observation=next_observation,
            terminated=False,
        )


def test_experience_rejects_invalid_agent_snapshot() -> None:
    with pytest.raises(ValueError, match="one episode"):
        ExperienceTransition(
            observation=create_packet(),
            action=PrimitiveAction.WAIT,
            agent_observation=create_packet(episode_id="episode-2", step_id=1),
            next_observation=create_packet(step_id=1),
            terminated=False,
        )


def test_experience_rejects_action_unavailable_at_source() -> None:
    observation = replace(
        create_packet(),
        available_actions=(PrimitiveAction.STOP,),
    )

    with pytest.raises(ValueError, match="not available"):
        ExperienceTransition(
            observation=observation,
            action=PrimitiveAction.WAIT,
            agent_observation=create_packet(step_id=1),
            next_observation=create_packet(step_id=1),
            terminated=False,
        )
