"""Body-independent observation contracts for SeedMind."""

from dataclasses import dataclass
from math import isfinite

from seedmind.contracts.action import PrimitiveAction


def _validate_channel(name: str, values: tuple[float, ...]) -> None:
    """Validate that a numeric channel contains only finite values."""
    for value in values:
        if not isfinite(value):
            raise ValueError(f"{name} must contain only finite values")


@dataclass(frozen=True, slots=True)
class ObservationPacket:
    """One raw observation delivered from a body adapter to SeedMind."""

    timestamp: int
    episode_id: str
    step_id: int
    sensor_values: tuple[float, ...]
    available_actions: tuple[PrimitiveAction, ...]
    human_signal: tuple[float, ...] = ()
    resource_state: tuple[float, ...] = ()

    def __post_init__(self) -> None:
        """Validate stable identifiers, action availability, and channels."""
        if self.timestamp < 0:
            raise ValueError("timestamp must not be negative")

        if not self.episode_id.strip():
            raise ValueError("episode_id must not be empty")

        if self.step_id < 0:
            raise ValueError("step_id must not be negative")

        if not self.sensor_values:
            raise ValueError("sensor_values must not be empty")

        if not self.available_actions:
            raise ValueError("available_actions must not be empty")

        if len(self.available_actions) != len(set(self.available_actions)):
            raise ValueError("available_actions must be unique")

        _validate_channel("sensor_values", self.sensor_values)
        _validate_channel("human_signal", self.human_signal)
        _validate_channel("resource_state", self.resource_state)
