"""Runtime orchestration for SeedMind Nursery v0."""

from collections.abc import Sequence
from dataclasses import dataclass

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.environment.observation import NurseryObservationAdapter
from seedmind.environment.state import NurseryState
from seedmind.environment.transition import (
    NurseryTransition,
    NurseryTransitionEngine,
)


@dataclass(frozen=True, slots=True)
class NurseryRuntimeStep:
    """One applied transition and the observation produced from its new state."""

    transition: NurseryTransition
    observation: ObservationPacket


class NurseryRuntime:
    """Connect immutable state, observation, and transition components."""

    __slots__ = (
        "_episode_id",
        "_initial_state",
        "_observation_adapter",
        "_state",
        "_transition_engine",
    )

    def __init__(self, initial_state: NurseryState, episode_id: str) -> None:
        """Validate the reset baseline and initialize the active episode."""
        if initial_state.step_count != 0:
            raise ValueError("initial_state step_count must be zero")

        if initial_state.terminated:
            raise ValueError("initial_state must not be terminated")

        self._validate_episode_id(episode_id)
        self._initial_state = initial_state
        self._episode_id = episode_id
        self._state = initial_state
        self._observation_adapter = NurseryObservationAdapter(
            width=initial_state.width,
            height=initial_state.height,
        )
        self._transition_engine = NurseryTransitionEngine()

    @property
    def initial_state(self) -> NurseryState:
        """Return the immutable baseline restored by reset."""
        return self._initial_state

    @property
    def episode_id(self) -> str:
        """Return the active externally assigned episode identifier."""
        return self._episode_id

    @property
    def state(self) -> NurseryState:
        """Return the current immutable nursery state."""
        return self._state

    @property
    def sensor_size(self) -> int:
        """Return the fixed sensor width for this runtime."""
        return self._observation_adapter.sensor_size

    def observe(
        self,
        *,
        human_signal: Sequence[float] = (),
        resource_state: Sequence[float] = (),
    ) -> ObservationPacket:
        """Observe the current state without advancing time."""
        return self._observation_adapter.observe(
            self._state,
            episode_id=self._episode_id,
            human_signal=human_signal,
            resource_state=resource_state,
        )

    def reset(
        self,
        *,
        episode_id: str | None = None,
        human_signal: Sequence[float] = (),
        resource_state: Sequence[float] = (),
    ) -> ObservationPacket:
        """Restore the exact initial state and return its first observation."""
        if episode_id is not None:
            self._validate_episode_id(episode_id)
            self._episode_id = episode_id

        self._state = self._initial_state
        return self.observe(
            human_signal=human_signal,
            resource_state=resource_state,
        )

    def step(
        self,
        action: PrimitiveAction,
        *,
        human_signal: Sequence[float] = (),
        resource_state: Sequence[float] = (),
    ) -> NurseryRuntimeStep:
        """Apply one available primitive action and observe the new state."""
        current_observation = self.observe()

        if action not in current_observation.available_actions:
            raise ValueError(
                f"Action {action.value!r} is not available in the current state"
            )

        transition = self._transition_engine.apply(self._state, action)
        self._state = transition.state
        observation = self.observe(
            human_signal=human_signal,
            resource_state=resource_state,
        )

        return NurseryRuntimeStep(
            transition=transition,
            observation=observation,
        )

    @staticmethod
    def _validate_episode_id(episode_id: str) -> None:
        """Reject empty episode identifiers before mutating runtime state."""
        if not episode_id.strip():
            raise ValueError("episode_id must not be empty")
