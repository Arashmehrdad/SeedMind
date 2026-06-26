"""One-step online predictive training for SeedMind."""

from dataclasses import dataclass
from math import isfinite

import torch
from torch import Tensor
from torch.nn.utils import clip_grad_norm_
from torch.optim import AdamW, Optimizer

from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveSeedCore, prediction_objective
from seedmind.perception import SymbolicInputSpec
from seedmind.training.experience import ExperienceTransition


@dataclass(frozen=True, slots=True)
class OnlineTrainerConfig:
    """Hyperparameters for one-step online predictive learning."""

    learning_rate: float = 1e-3
    weight_decay: float = 1e-4
    controllable_change_weight: float = 0.25
    confidence_weight: float = 0.1
    max_gradient_norm: float = 1.0

    def __post_init__(self) -> None:
        """Validate finite and non-negative trainer settings."""
        for name, value in (
            ("learning_rate", self.learning_rate),
            ("weight_decay", self.weight_decay),
            ("controllable_change_weight", self.controllable_change_weight),
            ("confidence_weight", self.confidence_weight),
            ("max_gradient_norm", self.max_gradient_norm),
        ):
            if not isfinite(value):
                raise ValueError(f"{name} must be finite")

        if self.learning_rate <= 0.0:
            raise ValueError("learning_rate must be positive")

        if self.weight_decay < 0.0:
            raise ValueError("weight_decay must not be negative")

        if self.controllable_change_weight < 0.0:
            raise ValueError("controllable_change_weight must not be negative")

        if self.confidence_weight < 0.0:
            raise ValueError("confidence_weight must not be negative")

        if self.max_gradient_norm <= 0.0:
            raise ValueError("max_gradient_norm must be positive")


@dataclass(frozen=True, slots=True)
class OnlineTrainingMetrics:
    """Inspectable measurements from one optimizer update."""

    episode_id: str
    source_step_id: int
    total_loss: float
    sensor_prediction_loss: float
    controllable_change_loss: float
    confidence_calibration_loss: float
    mean_absolute_error: float
    mean_confidence: float
    gradient_norm: float
    terminated: bool


class OnlinePredictiveTrainer:
    """Train the predictive core from temporally ordered transitions."""

    def __init__(
        self,
        core: PredictiveSeedCore,
        input_spec: SymbolicInputSpec,
        *,
        config: OnlineTrainerConfig | None = None,
        optimizer: Optimizer | None = None,
    ) -> None:
        """Bind one predictive core to its fixed body interface."""
        self.core = core
        self.input_spec = input_spec
        self.config = OnlineTrainerConfig() if config is None else config
        self._validate_interface()
        self.optimizer = (
            AdamW(
                self.core.parameters(),
                lr=self.config.learning_rate,
                weight_decay=self.config.weight_decay,
            )
            if optimizer is None
            else optimizer
        )
        self._action_indices = {action: index for index, action in enumerate(PrimitiveAction)}
        self._recurrent_state = self.core.initial_state(batch_size=1)
        self._active_episode_id: str | None = None
        self._expected_step_id: int | None = None
        self._episode_complete = False

    @property
    def recurrent_state(self) -> Tensor:
        """Return the detached short-term recurrent state."""
        return self._recurrent_state

    @property
    def active_episode_id(self) -> str | None:
        """Return the episode currently associated with recurrent state."""
        return self._active_episode_id

    def reset_episode(self) -> None:
        """Clear short-term state before starting another episode."""
        self._recurrent_state = self.core.initial_state(batch_size=1)
        self._active_episode_id = None
        self._expected_step_id = None
        self._episode_complete = False

    def train_transition(
        self,
        experience: ExperienceTransition,
    ) -> OnlineTrainingMetrics:
        """Perform one prediction, comparison, and optimizer update."""
        self._validate_sequence(experience)
        parameter = next(self.core.parameters())
        device = parameter.device
        dtype = parameter.dtype

        current_vector = self.input_spec.vectorize(
            experience.observation,
            device=device,
            dtype=dtype,
        ).unsqueeze(0)
        next_sensor = torch.tensor(
            experience.next_observation.sensor_values,
            device=device,
            dtype=dtype,
        ).unsqueeze(0)
        current_sensor = torch.tensor(
            experience.observation.sensor_values,
            device=device,
            dtype=dtype,
        ).unsqueeze(0)
        action_index = torch.tensor(
            (self._action_indices[experience.action],),
            device=device,
            dtype=torch.long,
        )
        self._recurrent_state = self._recurrent_state.to(
            device=device,
            dtype=dtype,
        )

        self.core.train()
        self.optimizer.zero_grad(set_to_none=True)
        output = self.core(
            current_vector,
            action_index,
            self._recurrent_state,
        )
        loss = prediction_objective(
            output,
            next_sensor,
            current_sensor=current_sensor,
            controllable_change_weight=self.config.controllable_change_weight,
            confidence_weight=self.config.confidence_weight,
        )
        loss.total.backward()  # type: ignore[no-untyped-call]
        gradient_norm_tensor = clip_grad_norm_(
            self.core.parameters(),
            max_norm=self.config.max_gradient_norm,
        )
        self.optimizer.step()

        self._recurrent_state = output.recurrent_state.detach()
        self._active_episode_id = experience.observation.episode_id
        self._expected_step_id = experience.next_observation.step_id
        self._episode_complete = experience.terminated

        return OnlineTrainingMetrics(
            episode_id=experience.observation.episode_id,
            source_step_id=experience.observation.step_id,
            total_loss=float(loss.total.detach().cpu().item()),
            sensor_prediction_loss=float(loss.sensor_prediction.detach().cpu().item()),
            controllable_change_loss=float(loss.controllable_change.detach().cpu().item()),
            confidence_calibration_loss=float(loss.confidence_calibration.detach().cpu().item()),
            mean_absolute_error=float(
                loss.comparison.mean_absolute_error.mean().detach().cpu().item()
            ),
            mean_confidence=float(output.confidence.mean().detach().cpu().item()),
            gradient_norm=float(gradient_norm_tensor.detach().cpu().item()),
            terminated=experience.terminated,
        )

    def _validate_interface(self) -> None:
        """Ensure model, action, and observation dimensions agree."""
        if self.input_spec.input_size != self.core.config.observation_input_size:
            raise ValueError("input specification does not match core observation input size")

        if self.input_spec.sensor_size != self.core.config.sensor_size:
            raise ValueError("input specification does not match core sensor size")

        if self.core.config.action_count != len(PrimitiveAction):
            raise ValueError("core action count does not match primitive actions")

    def _validate_sequence(self, experience: ExperienceTransition) -> None:
        """Protect recurrent state from episode or timestep discontinuities."""
        if self._episode_complete:
            raise RuntimeError("reset_episode is required after termination")

        if self._active_episode_id is None:
            return

        if experience.observation.episode_id != self._active_episode_id:
            raise ValueError("experience episode changed without reset_episode")

        if experience.observation.step_id != self._expected_step_id:
            raise ValueError("experience step is not temporally continuous")
