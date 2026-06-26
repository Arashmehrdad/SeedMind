"""Gymnasium adapter for the deterministic SeedMind Nursery runtime."""

from typing import Any, cast

import gymnasium as gym
import numpy as np
from gymnasium import spaces
from numpy.typing import NDArray

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.environment.processes import WorldProcess
from seedmind.environment.runtime import NurseryRuntime, ResourceStateProvider
from seedmind.environment.scenario import NurseryScenario
from seedmind.environment.state import NurseryState

ObservationArray = NDArray[np.float32]
InfoDictionary = dict[str, Any]


class SeedMindNurseryEnv(gym.Env[ObservationArray, int]):
    """Expose Nursery v0 through the standard Gymnasium API.

    The adapter provides raw numeric sensor values and a fixed primitive action
    index. It intentionally supplies no task reward; every transition returns
    zero reward while developmental motivation remains outside this wrapper.
    """

    def __init__(
        self,
        initial_state: NurseryState,
        *,
        episode_id: str = "episode-0",
        max_episode_steps: int | None = None,
        resource_state_provider: ResourceStateProvider | None = None,
        world_processes: tuple[WorldProcess, ...] = (),
    ) -> None:
        """Create an adapter around a deterministic nursery baseline."""
        super().__init__()
        self.metadata = {"render_modes": []}

        if max_episode_steps is not None and max_episode_steps <= 0:
            raise ValueError("max_episode_steps must be positive")

        self._runtime = NurseryRuntime(
            initial_state=initial_state,
            episode_id=episode_id,
            resource_state_provider=resource_state_provider,
            world_processes=world_processes,
        )
        self._primitive_actions = tuple(PrimitiveAction)
        self._max_episode_steps = max_episode_steps
        self._truncated = False

        self.action_space = cast(
            spaces.Space[int],
            spaces.Discrete(len(self._primitive_actions)),
        )
        self.observation_space = cast(
            spaces.Space[ObservationArray],
            spaces.Box(
                low=0.0,
                high=1.0,
                shape=(self._runtime.sensor_size,),
                dtype=np.float32,
            ),
        )

    @classmethod
    def from_scenario(
        cls,
        scenario: NurseryScenario,
        *,
        episode_id: str | None = None,
    ) -> "SeedMindNurseryEnv":
        """Create an environment using a reproducible scenario baseline."""
        return cls(
            initial_state=scenario.initial_state,
            episode_id=scenario.scenario_id if episode_id is None else episode_id,
            max_episode_steps=scenario.step_budget,
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )

    @property
    def runtime(self) -> NurseryRuntime:
        """Return the underlying deterministic runtime for inspection."""
        return self._runtime

    @property
    def primitive_actions(self) -> tuple[PrimitiveAction, ...]:
        """Return the stable mapping from action index to primitive action."""
        return self._primitive_actions

    def reset(
        self,
        *,
        seed: int | None = None,
        options: InfoDictionary | None = None,
    ) -> tuple[ObservationArray, InfoDictionary]:
        """Reset to the exact baseline and return its raw observation."""
        super().reset(seed=seed)

        if seed is not None:
            self.action_space.seed(seed)

        episode_id = self._episode_id_from_options(options)
        packet = self._runtime.reset(episode_id=episode_id)
        self._truncated = False
        return self._observation_array(packet), self._info(packet)

    def step(
        self,
        action: int,
    ) -> tuple[ObservationArray, float, bool, bool, InfoDictionary]:
        """Apply one indexed primitive action with zero external reward."""
        if self._runtime.state.terminated or self._truncated:
            raise RuntimeError("step cannot be called after episode completion")

        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action index: {action!r}")

        primitive_action = self._primitive_actions[int(action)]
        result = self._runtime.step(primitive_action)
        terminated = result.transition.state.terminated
        truncated = self._should_truncate(terminated=terminated)
        self._truncated = truncated

        return (
            self._observation_array(result.observation),
            0.0,
            terminated,
            truncated,
            self._info(
                result.observation,
                episode_complete=terminated or truncated,
            ),
        )

    def action_index(self, action: PrimitiveAction) -> int:
        """Return the stable Gymnasium index for a primitive action."""
        return self._primitive_actions.index(action)

    def _should_truncate(self, *, terminated: bool) -> bool:
        """Apply an optional deterministic episode step limit."""
        if terminated or self._max_episode_steps is None:
            return False

        return self._runtime.state.step_count >= self._max_episode_steps

    def _info(
        self,
        packet: ObservationPacket,
        *,
        episode_complete: bool = False,
    ) -> InfoDictionary:
        """Return non-semantic episode metadata and an action mask."""
        action_mask = np.zeros(len(self._primitive_actions), dtype=np.int8)

        if not episode_complete:
            for action in packet.available_actions:
                action_mask[self.action_index(action)] = 1

        return {
            "action_mask": action_mask,
            "episode_id": packet.episode_id,
            "resource_state": np.asarray(packet.resource_state, dtype=np.float32),
            "step_id": packet.step_id,
        }

    @staticmethod
    def _observation_array(packet: ObservationPacket) -> ObservationArray:
        """Convert immutable sensor values to Gymnasium float32 format."""
        return np.asarray(packet.sensor_values, dtype=np.float32)

    @staticmethod
    def _episode_id_from_options(options: InfoDictionary | None) -> str | None:
        """Read an optional episode identifier from reset options."""
        if options is None or "episode_id" not in options:
            return None

        episode_id = options["episode_id"]

        if not isinstance(episode_id, str):
            raise TypeError("reset option 'episode_id' must be a string")

        return episode_id
