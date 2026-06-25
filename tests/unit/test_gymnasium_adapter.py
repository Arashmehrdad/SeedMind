"""Tests for the Gymnasium-compatible SeedMind Nursery adapter."""

import numpy as np
import pytest
from gymnasium.utils.env_checker import check_env

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import AgentState, NurseryState
from seedmind.environment.gymnasium_adapter import SeedMindNurseryEnv


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


def create_env(*, max_episode_steps: int | None = None) -> SeedMindNurseryEnv:
    return SeedMindNurseryEnv(
        initial_state=create_initial_state(),
        episode_id="episode-1",
        max_episode_steps=max_episode_steps,
    )


def test_reset_returns_float32_observation_inside_declared_space() -> None:
    env = create_env()

    observation, info = env.reset(seed=7)

    assert observation.dtype == np.float32
    assert observation.shape == (env.runtime.sensor_size,)
    assert env.observation_space.contains(observation)
    assert info["episode_id"] == "episode-1"
    assert info["step_id"] == 0
    assert np.array_equal(
        info["action_mask"],
        np.ones(len(PrimitiveAction), dtype=np.int8),
    )


def test_step_maps_action_index_to_primitive_transition() -> None:
    env = create_env()
    env.reset()

    observation, reward, terminated, truncated, info = env.step(
        env.action_index(PrimitiveAction.MOVE_FORWARD)
    )

    assert env.runtime.state.agent.position == GridPosition(2, 1)
    assert env.observation_space.contains(observation)
    assert reward == 0.0
    assert terminated is False
    assert truncated is False
    assert info["step_id"] == 1


def test_stop_terminates_without_external_reward() -> None:
    env = create_env()
    env.reset()

    _, reward, terminated, truncated, info = env.step(
        env.action_index(PrimitiveAction.STOP)
    )

    assert reward == 0.0
    assert terminated is True
    assert truncated is False
    assert np.array_equal(
        info["action_mask"],
        np.zeros(len(PrimitiveAction), dtype=np.int8),
    )

    with pytest.raises(RuntimeError, match="episode completion"):
        env.step(env.action_index(PrimitiveAction.STOP))


def test_deterministic_step_limit_truncates_episode() -> None:
    env = create_env(max_episode_steps=2)
    env.reset()

    first = env.step(env.action_index(PrimitiveAction.WAIT))
    second = env.step(env.action_index(PrimitiveAction.WAIT))

    assert first[3] is False
    assert second[2] is False
    assert second[3] is True
    assert np.array_equal(
        second[4]["action_mask"],
        np.zeros(len(PrimitiveAction), dtype=np.int8),
    )


def test_reset_clears_completion_and_can_change_episode_identifier() -> None:
    env = create_env(max_episode_steps=1)
    env.reset()
    env.step(env.action_index(PrimitiveAction.WAIT))

    observation, info = env.reset(options={"episode_id": "episode-2"})

    assert env.runtime.state.step_count == 0
    assert info["episode_id"] == "episode-2"
    assert info["step_id"] == 0
    assert env.observation_space.contains(observation)


def test_invalid_action_index_is_rejected() -> None:
    env = create_env()
    env.reset()

    with pytest.raises(ValueError, match="Invalid action index"):
        env.step(len(PrimitiveAction))


def test_invalid_reset_episode_identifier_type_is_rejected() -> None:
    env = create_env()

    with pytest.raises(TypeError, match="must be a string"):
        env.reset(options={"episode_id": 123})


def test_max_episode_steps_must_be_positive() -> None:
    with pytest.raises(ValueError, match="positive"):
        create_env(max_episode_steps=0)


def test_adapter_passes_gymnasium_environment_checks() -> None:
    env = create_env(max_episode_steps=10)

    check_env(env, skip_render_check=True)
