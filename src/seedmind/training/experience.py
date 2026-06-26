"""Sequential experience records collected from SeedMind Nursery v0."""

from dataclasses import dataclass

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.environment.runtime import NurseryRuntime


@dataclass(frozen=True, slots=True)
class ExperienceTransition:
    """One observation, action, and resulting next observation."""

    observation: ObservationPacket
    action: PrimitiveAction
    next_observation: ObservationPacket
    terminated: bool

    def __post_init__(self) -> None:
        """Validate temporal continuity and stable numeric channel widths."""
        if self.observation.episode_id != self.next_observation.episode_id:
            raise ValueError("experience observations must belong to one episode")

        if self.next_observation.step_id != self.observation.step_id + 1:
            raise ValueError("next observation must advance exactly one step")

        if self.action not in self.observation.available_actions:
            raise ValueError("action was not available in the source observation")

        if len(self.observation.sensor_values) != len(self.next_observation.sensor_values):
            raise ValueError("sensor width must remain stable across a transition")

        if len(self.observation.human_signal) != len(self.next_observation.human_signal):
            raise ValueError("human signal width must remain stable across a transition")

        if len(self.observation.resource_state) != len(self.next_observation.resource_state):
            raise ValueError("resource state width must remain stable across a transition")

    @property
    def sensor_change(self) -> tuple[float, ...]:
        """Return the raw sensor difference across this action."""
        return tuple(
            next_value - current_value
            for current_value, next_value in zip(
                self.observation.sensor_values,
                self.next_observation.sensor_values,
                strict=True,
            )
        )


def collect_experience(
    runtime: NurseryRuntime,
    action: PrimitiveAction,
) -> ExperienceTransition:
    """Apply one action and return the resulting experience record."""
    if runtime.state.terminated:
        raise RuntimeError("cannot collect experience after episode termination")

    observation = runtime.observe()
    result = runtime.step(action)

    return ExperienceTransition(
        observation=observation,
        action=action,
        next_observation=result.observation,
        terminated=result.transition.state.terminated,
    )
