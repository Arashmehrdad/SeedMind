"""Sequential experience records collected from SeedMind Nursery v0."""

from dataclasses import dataclass

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.environment.runtime import NurseryRuntime


@dataclass(frozen=True, slots=True)
class ExperienceTransition:
    """Source, agent-only, and final observations for one complete tick."""

    observation: ObservationPacket
    action: PrimitiveAction
    agent_observation: ObservationPacket
    next_observation: ObservationPacket
    terminated: bool

    def __post_init__(self) -> None:
        """Validate temporal continuity and stable numeric channel widths."""
        observations = (
            self.observation,
            self.agent_observation,
            self.next_observation,
        )
        if len({packet.episode_id for packet in observations}) != 1:
            raise ValueError("experience observations must belong to one episode")

        expected_step_id = self.observation.step_id + 1
        if (
            self.agent_observation.step_id != expected_step_id
            or self.next_observation.step_id != expected_step_id
        ):
            raise ValueError("result observations must advance exactly one step")

        if self.action not in self.observation.available_actions:
            raise ValueError("action was not available in the source observation")

        if len({len(packet.sensor_values) for packet in observations}) != 1:
            raise ValueError("sensor width must remain stable across a transition")

        if len({len(packet.human_signal) for packet in observations}) != 1:
            raise ValueError("human signal width must remain stable across a transition")

        if len({len(packet.resource_state) for packet in observations}) != 1:
            raise ValueError("resource state width must remain stable across a transition")

    @property
    def sensor_change(self) -> tuple[float, ...]:
        """Return the final sensor difference after the complete tick."""
        return _sensor_difference(
            self.observation.sensor_values,
            self.next_observation.sensor_values,
        )

    @property
    def controllable_sensor_change(self) -> tuple[float, ...]:
        """Return only the sensor difference caused by the agent action."""
        return _sensor_difference(
            self.observation.sensor_values,
            self.agent_observation.sensor_values,
        )

    @property
    def external_sensor_change(self) -> tuple[float, ...]:
        """Return the sensor difference caused after the agent action."""
        return _sensor_difference(
            self.agent_observation.sensor_values,
            self.next_observation.sensor_values,
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
        agent_observation=result.agent_observation,
        next_observation=result.observation,
        terminated=result.transition.state.terminated,
    )


def _sensor_difference(
    source: tuple[float, ...],
    destination: tuple[float, ...],
) -> tuple[float, ...]:
    """Subtract two already validated sensor vectors."""
    return tuple(
        destination_value - source_value
        for source_value, destination_value in zip(
            source,
            destination,
            strict=True,
        )
    )
