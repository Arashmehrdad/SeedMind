"""Recurrent predictive state core for SeedMind v0.1."""

from dataclasses import dataclass

import torch
from torch import Tensor, nn

from seedmind.perception import SymbolicObservationEncoder


@dataclass(frozen=True, slots=True)
class PredictiveCoreConfig:
    """Dimensions for the first recurrent predictive seed core."""

    observation_input_size: int
    sensor_size: int
    action_count: int
    observation_embedding_size: int = 64
    action_embedding_size: int = 16
    hidden_size: int = 128

    def __post_init__(self) -> None:
        """Validate all model dimensions."""
        for name, value in (
            ("observation_input_size", self.observation_input_size),
            ("sensor_size", self.sensor_size),
            ("action_count", self.action_count),
            ("observation_embedding_size", self.observation_embedding_size),
            ("action_embedding_size", self.action_embedding_size),
            ("hidden_size", self.hidden_size),
        ):
            if value <= 0:
                raise ValueError(f"{name} must be positive")

        if self.sensor_size > self.observation_input_size:
            raise ValueError("sensor_size must not exceed observation_input_size")


@dataclass(frozen=True, slots=True)
class PredictiveCoreOutput:
    """One recurrent update and its prediction heads."""

    recurrent_state: Tensor
    predicted_next_sensor: Tensor
    predicted_controllable_change: Tensor
    confidence: Tensor


class PredictiveSeedCore(nn.Module):
    """Update recurrent state from raw observation and previous action."""

    def __init__(self, config: PredictiveCoreConfig) -> None:
        """Build the observation encoder, recurrent unit, and prediction heads."""
        super().__init__()
        self.config = config
        self.observation_encoder = SymbolicObservationEncoder(
            input_size=config.observation_input_size,
            embedding_size=config.observation_embedding_size,
        )
        self.action_embedding = nn.Embedding(
            num_embeddings=config.action_count + 1,
            embedding_dim=config.action_embedding_size,
        )
        self.recurrent = nn.GRUCell(
            input_size=(config.observation_embedding_size + config.action_embedding_size),
            hidden_size=config.hidden_size,
        )
        self.next_sensor_head = nn.Linear(config.hidden_size, config.sensor_size)
        self.controllable_change_head = nn.Linear(
            config.hidden_size,
            config.sensor_size,
        )
        self.confidence_head = nn.Linear(config.hidden_size, 1)

    def initial_state(
        self,
        batch_size: int,
        *,
        device: torch.device | str | None = None,
        dtype: torch.dtype | None = None,
    ) -> Tensor:
        """Return a zero recurrent state matching the model by default."""
        if batch_size <= 0:
            raise ValueError("batch_size must be positive")

        parameter = next(self.parameters())
        resolved_device = parameter.device if device is None else device
        resolved_dtype = parameter.dtype if dtype is None else dtype
        return torch.zeros(
            (batch_size, self.config.hidden_size),
            device=resolved_device,
            dtype=resolved_dtype,
        )

    def forward(
        self,
        observation: Tensor,
        action: Tensor,
        recurrent_state: Tensor,
    ) -> PredictiveCoreOutput:
        """Predict the next sensors for an action applied after observation."""
        observation = self._as_batch(observation)
        action = self._validate_actions(
            action,
            batch_size=observation.shape[0],
            device=observation.device,
        )
        self._validate_recurrent_state(
            recurrent_state,
            batch_size=observation.shape[0],
        )

        observation_embedding = self.observation_encoder(observation)
        action_embedding = self.action_embedding(action + 1)
        recurrent_input = torch.cat(
            (observation_embedding, action_embedding),
            dim=-1,
        )
        updated_state = self.recurrent(recurrent_input, recurrent_state)

        return PredictiveCoreOutput(
            recurrent_state=updated_state,
            predicted_next_sensor=torch.sigmoid(self.next_sensor_head(updated_state)),
            predicted_controllable_change=torch.tanh(self.controllable_change_head(updated_state)),
            confidence=torch.sigmoid(self.confidence_head(updated_state)),
        )

    def _as_batch(self, observation: Tensor) -> Tensor:
        """Normalize one observation or a batch to a two-dimensional tensor."""
        if observation.ndim == 1:
            observation = observation.unsqueeze(0)

        if observation.ndim != 2:
            raise ValueError("observation must be a vector or batch of vectors")

        if observation.shape[-1] != self.config.observation_input_size:
            raise ValueError("observation width does not match observation_input_size")

        return observation

    def _validate_actions(
        self,
        action: Tensor,
        *,
        batch_size: int,
        device: torch.device,
    ) -> Tensor:
        """Validate action indices, where -1 means no action."""
        if action.ndim == 0:
            action = action.unsqueeze(0)

        if action.ndim != 1:
            raise ValueError("action must be a scalar or vector")

        if action.shape[0] != batch_size:
            raise ValueError("action batch size does not match observation")

        action = action.to(device=device, dtype=torch.long)
        minimum_action = int(action.min().item())
        maximum_action = int(action.max().item())

        if minimum_action < -1 or maximum_action >= self.config.action_count:
            raise ValueError("action contains an invalid action index")

        return action

    def _validate_recurrent_state(
        self,
        recurrent_state: Tensor,
        *,
        batch_size: int,
    ) -> None:
        """Validate recurrent state batch and hidden dimensions."""
        expected_shape = (batch_size, self.config.hidden_size)

        if tuple(recurrent_state.shape) != expected_shape:
            raise ValueError("recurrent_state shape does not match batch and hidden size")
