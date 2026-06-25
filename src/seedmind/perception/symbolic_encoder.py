"""Learned encoding for raw symbolic SeedMind observations."""

from dataclasses import dataclass

import torch
from torch import Tensor, nn

from seedmind.contracts import ObservationPacket


@dataclass(frozen=True, slots=True)
class SymbolicInputSpec:
    """Fixed numeric channel sizes accepted by one seed core."""

    sensor_size: int
    human_signal_size: int = 0
    resource_state_size: int = 0

    def __post_init__(self) -> None:
        """Validate a non-empty sensor stream and optional side channels."""
        if self.sensor_size <= 0:
            raise ValueError("sensor_size must be positive")

        if self.human_signal_size < 0:
            raise ValueError("human_signal_size must not be negative")

        if self.resource_state_size < 0:
            raise ValueError("resource_state_size must not be negative")

    @property
    def input_size(self) -> int:
        """Return the total width of the raw numeric input vector."""
        return (
            self.sensor_size
            + self.human_signal_size
            + self.resource_state_size
        )

    def vectorize(
        self,
        packet: ObservationPacket,
        *,
        device: torch.device | str | None = None,
        dtype: torch.dtype = torch.float32,
    ) -> Tensor:
        """Convert one observation packet into a fixed raw numeric tensor."""
        self._validate_packet(packet)
        values = (
            *packet.sensor_values,
            *packet.human_signal,
            *packet.resource_state,
        )
        return torch.tensor(values, device=device, dtype=dtype)

    def _validate_packet(self, packet: ObservationPacket) -> None:
        """Reject packets that do not match the fixed body interface."""
        if len(packet.sensor_values) != self.sensor_size:
            raise ValueError("sensor_values length does not match sensor_size")

        if len(packet.human_signal) != self.human_signal_size:
            raise ValueError(
                "human_signal length does not match human_signal_size"
            )

        if len(packet.resource_state) != self.resource_state_size:
            raise ValueError(
                "resource_state length does not match resource_state_size"
            )


class SymbolicObservationEncoder(nn.Module):
    """Map raw numeric channels to a compact learned observation embedding."""

    def __init__(self, input_size: int, embedding_size: int) -> None:
        """Create a small body-independent learned encoder."""
        super().__init__()

        if input_size <= 0:
            raise ValueError("input_size must be positive")

        if embedding_size <= 0:
            raise ValueError("embedding_size must be positive")

        self.input_size = input_size
        self.embedding_size = embedding_size
        self.network = nn.Sequential(
            nn.Linear(input_size, embedding_size),
            nn.LayerNorm(embedding_size),
            nn.SiLU(),
        )

    def forward(self, observation: Tensor) -> Tensor:
        """Encode a batch of fixed-width raw observations."""
        if observation.ndim == 1:
            observation = observation.unsqueeze(0)

        if observation.ndim != 2:
            raise ValueError("observation must be a vector or a batch of vectors")

        if observation.shape[-1] != self.input_size:
            raise ValueError("observation width does not match input_size")

        return self.network(observation)
