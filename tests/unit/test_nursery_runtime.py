"""Integration tests for the SeedMind Nursery runtime boundary."""

import pytest

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    AgentState,
    NurseryRuntime,
    NurseryState,
    TransitionOutcome,
)


def create_initial_state() -> NurseryState:
    return NurseryState(
        width=4,
        height=4,
        agent=AgentState(
            position=GridPosition(1, 1),
            orientation=Direction.EAST,
        ),
        entities=(),
    )


def test_runtime_step_connects_state_transition_and_observation() -> None:
    runtime = NurseryRuntime(
        initial_state=create_initial_state(),
        episode_id="episode-1",
    )

    result = runtime.step(PrimitiveAction.MOVE_FORWARD)

    assert result.transition.outcome is TransitionOutcome.MOVED
    assert runtime.state == result.transition.state
    assert runtime.state.agent.position == GridPosition(2, 1)
    assert result.agent_observation.step_id == 1
    assert result.observation.step_id == 1
    assert result.agent_observation.sensor_values == result.observation.sensor_values
    assert result.observation.episode_id == "episode-1"
    assert result.observation.sensor_values == runtime.observe().sensor_values


def test_reset_restores_identical_initial_observation() -> None:
    runtime = NurseryRuntime(
        initial_state=create_initial_state(),
        episode_id="episode-1",
    )
    first = runtime.observe()

    runtime.step(PrimitiveAction.TURN_LEFT)
    runtime.step(PrimitiveAction.MOVE_FORWARD)
    reset = runtime.reset()

    assert runtime.state == runtime.initial_state
    assert reset == first


def test_reset_can_start_a_new_named_episode() -> None:
    runtime = NurseryRuntime(
        initial_state=create_initial_state(),
        episode_id="episode-1",
    )

    reset = runtime.reset(episode_id="episode-2")

    assert runtime.episode_id == "episode-2"
    assert reset.episode_id == "episode-2"
    assert reset.step_id == 0


def test_runtime_passes_auxiliary_channels_to_new_observation() -> None:
    runtime = NurseryRuntime(
        initial_state=create_initial_state(),
        episode_id="episode-1",
    )

    result = runtime.step(
        PrimitiveAction.WAIT,
        human_signal=(1.0, 0.0),
        resource_state=(0.75,),
    )

    assert result.observation.human_signal == (1.0, 0.0)
    assert result.observation.resource_state == (0.75,)


def test_stop_terminates_and_restricts_next_available_action() -> None:
    runtime = NurseryRuntime(
        initial_state=create_initial_state(),
        episode_id="episode-1",
    )

    result = runtime.step(PrimitiveAction.STOP)

    assert runtime.state.terminated is True
    assert result.observation.available_actions == (PrimitiveAction.STOP,)

    with pytest.raises(ValueError, match="not available"):
        runtime.step(PrimitiveAction.MOVE_FORWARD)


def test_repeated_stop_after_termination_is_stable() -> None:
    runtime = NurseryRuntime(
        initial_state=create_initial_state(),
        episode_id="episode-1",
    )
    runtime.step(PrimitiveAction.STOP)
    terminated_state = runtime.state

    result = runtime.step(PrimitiveAction.STOP)

    assert result.transition.outcome is TransitionOutcome.ALREADY_TERMINATED
    assert runtime.state is terminated_state
    assert result.observation.step_id == terminated_state.step_count


@pytest.mark.parametrize(
    ("initial_state", "message"),
    [
        (
            NurseryState(
                width=4,
                height=4,
                agent=AgentState(
                    position=GridPosition(1, 1),
                    orientation=Direction.NORTH,
                ),
                entities=(),
                step_count=1,
            ),
            "step_count",
        ),
        (
            NurseryState(
                width=4,
                height=4,
                agent=AgentState(
                    position=GridPosition(1, 1),
                    orientation=Direction.NORTH,
                ),
                entities=(),
                terminated=True,
            ),
            "terminated",
        ),
    ],
)
def test_runtime_rejects_invalid_reset_baseline(
    initial_state: NurseryState,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        NurseryRuntime(
            initial_state=initial_state,
            episode_id="episode-1",
        )


def test_runtime_rejects_empty_episode_identifier() -> None:
    with pytest.raises(ValueError, match="episode_id"):
        NurseryRuntime(
            initial_state=create_initial_state(),
            episode_id=" ",
        )


def test_invalid_reset_episode_identifier_does_not_mutate_runtime() -> None:
    runtime = NurseryRuntime(
        initial_state=create_initial_state(),
        episode_id="episode-1",
    )
    runtime.step(PrimitiveAction.MOVE_FORWARD)
    state_before_reset = runtime.state

    with pytest.raises(ValueError, match="episode_id"):
        runtime.reset(episode_id=" ")

    assert runtime.episode_id == "episode-1"
    assert runtime.state is state_before_reset


def test_runtime_derives_resource_state_from_current_world_state() -> None:
    def resource_state_provider(state: NurseryState) -> tuple[float, ...]:
        return (1.0 - (state.step_count / 10.0),)

    runtime = NurseryRuntime(
        initial_state=create_initial_state(),
        episode_id="episode-1",
        resource_state_provider=resource_state_provider,
    )

    initial = runtime.observe()
    advanced = runtime.step(PrimitiveAction.WAIT).observation
    overridden = runtime.observe(resource_state=(0.25,))

    assert initial.resource_state == (1.0,)
    assert advanced.resource_state == (0.9,)
    assert overridden.resource_state == (0.25,)
