"""Runtime orchestration for SeedMind Nursery v0."""

from collections.abc import Callable, Sequence
from dataclasses import dataclass, replace

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.environment.observation import NurseryObservationAdapter
from seedmind.environment.processes import (
    WorldProcess,
    WorldProcessEvent,
    WorldProcessPipeline,
)
from seedmind.environment.state import NurseryState
from seedmind.environment.transition import (
    NurseryTransition,
    NurseryTransitionEngine,
)

ResourceStateProvider = Callable[[NurseryState], Sequence[float]]


@dataclass(frozen=True, slots=True)
class NurseryRuntimeStep:
    """One complete tick with agent-only and final causal snapshots."""

    transition: NurseryTransition
    agent_observation: ObservationPacket
    observation: ObservationPacket
    process_events: tuple[WorldProcessEvent, ...] = ()

    @property
    def external_world_changed(self) -> bool:
        """Return whether an independent process changed this tick."""
        return any(event.changed for event in self.process_events)


class NurseryRuntime:
    """Connect immutable state, agent transitions, and world processes."""

    __slots__ = (
        "_episode_id",
        "_initial_state",
        "_observation_adapter",
        "_resource_state_provider",
        "_state",
        "_transition_engine",
        "_world_process_pipeline",
    )

    def __init__(
        self,
        initial_state: NurseryState,
        episode_id: str,
        *,
        resource_state_provider: ResourceStateProvider | None = None,
        world_processes: Sequence[WorldProcess] = (),
    ) -> None:
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
        self._resource_state_provider = resource_state_provider
        self._world_process_pipeline = WorldProcessPipeline.from_sequence(world_processes)
        self._world_process_pipeline.validate(initial_state)

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

    @property
    def world_processes(self) -> tuple[WorldProcess, ...]:
        """Return independent processes in deterministic run order."""
        return self._world_process_pipeline.processes

    def observe(
        self,
        *,
        human_signal: Sequence[float] = (),
        resource_state: Sequence[float] | None = None,
    ) -> ObservationPacket:
        """Observe the current state without advancing time."""
        return self._observe_state(
            self._state,
            human_signal=human_signal,
            resource_state=resource_state,
        )

    def reset(
        self,
        *,
        episode_id: str | None = None,
        human_signal: Sequence[float] = (),
        resource_state: Sequence[float] | None = None,
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
        resource_state: Sequence[float] | None = None,
    ) -> NurseryRuntimeStep:
        """Advance one tick through the agent action and world processes."""
        current_observation = self.observe()

        if action not in current_observation.available_actions:
            raise ValueError(f"Action {action.value!r} is not available in the current state")

        agent_transition = self._transition_engine.apply(self._state, action)
        agent_state = agent_transition.state
        agent_observation = self._observe_state(
            agent_state,
            human_signal=human_signal,
            resource_state=resource_state,
        )
        final_state = agent_state
        process_events: tuple[WorldProcessEvent, ...] = ()
        external_world_changed = False

        if not final_state.terminated:
            process_result = self._world_process_pipeline.advance(final_state)
            final_state = process_result.state
            process_events = process_result.events
            external_world_changed = process_result.world_changed

        transition = replace(
            agent_transition,
            state=final_state,
            world_changed=(agent_transition.world_changed or external_world_changed),
        )
        self._state = final_state
        observation = self._observe_state(
            final_state,
            human_signal=human_signal,
            resource_state=resource_state,
        )

        return NurseryRuntimeStep(
            transition=transition,
            agent_observation=agent_observation,
            observation=observation,
            process_events=process_events,
        )

    def _observe_state(
        self,
        state: NurseryState,
        *,
        human_signal: Sequence[float],
        resource_state: Sequence[float] | None,
    ) -> ObservationPacket:
        """Observe one causal snapshot without changing active runtime state."""
        return self._observation_adapter.observe(
            state,
            episode_id=self._episode_id,
            human_signal=human_signal,
            resource_state=self._resolve_resource_state(state, resource_state),
        )

    def _resolve_resource_state(
        self,
        state: NurseryState,
        resource_state: Sequence[float] | None,
    ) -> Sequence[float]:
        """Resolve an explicit resource channel or derive it from one state."""
        if resource_state is not None:
            return resource_state

        if self._resource_state_provider is None:
            return ()

        return self._resource_state_provider(state)

    @staticmethod
    def _validate_episode_id(episode_id: str) -> None:
        """Reject empty episode identifiers before mutating runtime state."""
        if not episode_id.strip():
            raise ValueError("episode_id must not be empty")
