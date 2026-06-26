"""Reproducible familiar-sequence training sessions for SeedMind."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Protocol, cast

import torch

from seedmind.contracts import PrimitiveAction
from seedmind.environment import NurseryRuntime, NurseryScenario
from seedmind.training.experience import collect_experience
from seedmind.training.online_trainer import (
    OnlinePredictiveTrainer,
    OnlineTrainingMetrics,
)

_CHECKPOINT_FORMAT_VERSION = 1
_ENVIRONMENT_VERSION = "nursery-v0"


class ScenarioFactory(Protocol):
    """Construct deterministic nursery scenarios from integer seeds."""

    def create(self, seed: int) -> NurseryScenario:
        """Return the scenario associated with one seed."""
        ...


@dataclass(frozen=True, slots=True)
class FamiliarSequenceConfig:
    """Configuration for repeated training on one deterministic sequence."""

    seed: int = 0
    episode_count: int = 12
    action_sequence: tuple[PrimitiveAction, ...] = (
        PrimitiveAction.TURN_LEFT,
        PrimitiveAction.WAIT,
        PrimitiveAction.TURN_RIGHT,
        PrimitiveAction.MOVE_FORWARD,
        PrimitiveAction.INSPECT,
        PrimitiveAction.ACKNOWLEDGE,
    )
    checkpoint_every_episodes: int = 1

    def __post_init__(self) -> None:
        """Reject invalid or terminal familiar-sequence settings."""
        if self.seed < 0:
            raise ValueError("seed must not be negative")

        if self.episode_count <= 0:
            raise ValueError("episode_count must be positive")

        if not self.action_sequence:
            raise ValueError("action_sequence must not be empty")

        if PrimitiveAction.STOP in self.action_sequence:
            raise ValueError("action_sequence must not contain stop")

        if self.checkpoint_every_episodes <= 0:
            raise ValueError("checkpoint_every_episodes must be positive")


@dataclass(frozen=True, slots=True)
class TrainingStepRecord:
    """Serializable metrics for one action in a repeated training session."""

    episode_index: int
    sequence_index: int
    episode_id: str
    source_step_id: int
    action: PrimitiveAction
    total_loss: float
    sensor_prediction_loss: float
    controllable_change_loss: float
    confidence_calibration_loss: float
    mean_absolute_error: float
    external_change_mean_absolute: float
    mean_confidence: float
    gradient_norm: float
    terminated: bool

    @classmethod
    def from_metrics(
        cls,
        *,
        episode_index: int,
        sequence_index: int,
        action: PrimitiveAction,
        metrics: OnlineTrainingMetrics,
    ) -> TrainingStepRecord:
        """Create one durable history record from trainer metrics."""
        return cls(
            episode_index=episode_index,
            sequence_index=sequence_index,
            episode_id=metrics.episode_id,
            source_step_id=metrics.source_step_id,
            action=action,
            total_loss=metrics.total_loss,
            sensor_prediction_loss=metrics.sensor_prediction_loss,
            controllable_change_loss=metrics.controllable_change_loss,
            confidence_calibration_loss=metrics.confidence_calibration_loss,
            mean_absolute_error=metrics.mean_absolute_error,
            external_change_mean_absolute=metrics.external_change_mean_absolute,
            mean_confidence=metrics.mean_confidence,
            gradient_norm=metrics.gradient_norm,
            terminated=metrics.terminated,
        )


@dataclass(frozen=True, slots=True)
class TrainingSessionResult:
    """Completed or partially completed familiar-sequence training evidence."""

    config: FamiliarSequenceConfig
    completed_episodes: int
    records: tuple[TrainingStepRecord, ...]

    def __post_init__(self) -> None:
        """Validate episode bounds and complete per-episode history."""
        if self.completed_episodes <= 0:
            raise ValueError("completed_episodes must be positive")

        if self.completed_episodes > self.config.episode_count:
            raise ValueError("completed_episodes exceeds configured episode_count")

        expected_records = self.completed_episodes * len(self.config.action_sequence)
        if len(self.records) != expected_records:
            raise ValueError("records do not cover every completed sequence step")

    @property
    def episode_mean_absolute_errors(self) -> tuple[float, ...]:
        """Return mean prediction error for each completed episode."""
        errors: list[float] = []
        for episode_index in range(self.completed_episodes):
            episode_errors = [
                record.mean_absolute_error
                for record in self.records
                if record.episode_index == episode_index
            ]
            if len(episode_errors) != len(self.config.action_sequence):
                raise ValueError("history is missing an episode sequence step")
            errors.append(sum(episode_errors) / len(episode_errors))
        return tuple(errors)

    @property
    def initial_mean_absolute_error(self) -> float:
        """Return mean prediction error from the first familiar episode."""
        return self.episode_mean_absolute_errors[0]

    @property
    def final_mean_absolute_error(self) -> float:
        """Return mean prediction error from the latest familiar episode."""
        return self.episode_mean_absolute_errors[-1]

    @property
    def prediction_error_improved(self) -> bool:
        """Return whether the latest familiar episode beats the first."""
        return self.final_mean_absolute_error < self.initial_mean_absolute_error


class FamiliarSequenceTrainingSession:
    """Train continuously across repeated deterministic nursery episodes."""

    def __init__(
        self,
        trainer: OnlinePredictiveTrainer,
        scenario_factory: ScenarioFactory,
        config: FamiliarSequenceConfig,
    ) -> None:
        """Bind a trainer, deterministic scenario factory, and session config."""
        self.trainer = trainer
        self.config = config
        self.scenario = scenario_factory.create(config.seed)
        if len(config.action_sequence) > self.scenario.step_budget:
            raise ValueError("action_sequence exceeds scenario step budget")

    def run(
        self,
        *,
        checkpoint_path: Path | None = None,
        resume: bool = False,
        max_episodes: int | None = None,
    ) -> TrainingSessionResult:
        """Run new episodes or resume from an episode-boundary checkpoint."""
        if resume and checkpoint_path is None:
            raise ValueError("checkpoint_path is required when resume is true")

        if max_episodes is not None and max_episodes <= 0:
            raise ValueError("max_episodes must be positive")

        completed_episodes = 0
        records: list[TrainingStepRecord] = []

        if resume:
            assert checkpoint_path is not None
            completed_episodes, loaded_records = load_training_checkpoint(
                checkpoint_path,
                trainer=self.trainer,
                config=self.config,
                scenario=self.scenario,
            )
            records.extend(loaded_records)
        else:
            self.trainer.reset_episode()

        remaining_episodes = self.config.episode_count - completed_episodes
        episodes_to_run = (
            remaining_episodes
            if max_episodes is None
            else min(max_episodes, remaining_episodes)
        )
        if episodes_to_run == 0:
            return TrainingSessionResult(
                config=self.config,
                completed_episodes=completed_episodes,
                records=tuple(records),
            )

        stop_episode = completed_episodes + episodes_to_run
        for episode_index in range(completed_episodes, stop_episode):
            self._run_episode(episode_index, records)
            completed_episodes = episode_index + 1
            self.trainer.reset_episode()

            if (
                checkpoint_path is not None
                and completed_episodes % self.config.checkpoint_every_episodes == 0
            ):
                save_training_checkpoint(
                    checkpoint_path,
                    trainer=self.trainer,
                    config=self.config,
                    scenario=self.scenario,
                    completed_episodes=completed_episodes,
                    records=records,
                )

        if checkpoint_path is not None:
            save_training_checkpoint(
                checkpoint_path,
                trainer=self.trainer,
                config=self.config,
                scenario=self.scenario,
                completed_episodes=completed_episodes,
                records=records,
            )

        return TrainingSessionResult(
            config=self.config,
            completed_episodes=completed_episodes,
            records=tuple(records),
        )

    def _run_episode(
        self,
        episode_index: int,
        records: list[TrainingStepRecord],
    ) -> None:
        """Run one seeded episode through the fixed familiar action sequence."""
        runtime = NurseryRuntime(
            initial_state=self.scenario.initial_state,
            episode_id=f"{self.scenario.scenario_id}-familiar-{episode_index:04d}",
            resource_state_provider=self.scenario.resource_state,
            world_processes=self.scenario.world_processes,
        )
        self.trainer.reset_episode()

        for sequence_index, action in enumerate(self.config.action_sequence):
            experience = collect_experience(runtime, action)
            metrics = self.trainer.train_transition(experience)
            records.append(
                TrainingStepRecord.from_metrics(
                    episode_index=episode_index,
                    sequence_index=sequence_index,
                    action=action,
                    metrics=metrics,
                )
            )

            if experience.terminated:
                raise RuntimeError("familiar action sequence terminated early")


def save_training_checkpoint(
    path: Path,
    *,
    trainer: OnlinePredictiveTrainer,
    config: FamiliarSequenceConfig,
    scenario: NurseryScenario,
    completed_episodes: int,
    records: Sequence[TrainingStepRecord],
) -> None:
    """Atomically save model, optimizer, progress, and metric history."""
    if trainer.active_episode_id is not None:
        raise RuntimeError("training checkpoints require an episode boundary")

    _validate_checkpoint_progress(config, completed_episodes, records)
    payload: dict[str, Any] = {
        "format_version": _CHECKPOINT_FORMAT_VERSION,
        "environment_version": _ENVIRONMENT_VERSION,
        "session_identity": _session_identity(config),
        "scenario_identity": _scenario_identity(scenario),
        "completed_episodes": completed_episodes,
        "records": [_record_to_payload(record) for record in records],
        "core_config": asdict(trainer.core.config),
        "input_spec": asdict(trainer.input_spec),
        "trainer_config": asdict(trainer.config),
        "core_state": trainer.core.state_dict(),
        "optimizer_state": trainer.optimizer.state_dict(),
        "torch_rng_state": torch.random.get_rng_state(),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    torch.save(payload, temporary_path)
    temporary_path.replace(path)


def load_training_checkpoint(
    path: Path,
    *,
    trainer: OnlinePredictiveTrainer,
    config: FamiliarSequenceConfig,
    scenario: NurseryScenario,
) -> tuple[int, tuple[TrainingStepRecord, ...]]:
    """Restore a compatible episode-boundary checkpoint into one trainer."""
    if not path.is_file():
        raise FileNotFoundError(path)

    parameter = next(trainer.core.parameters())
    payload = cast(
        dict[str, Any],
        torch.load(
            path,
            map_location=parameter.device,
            weights_only=True,
        ),
    )
    if payload.get("format_version") != _CHECKPOINT_FORMAT_VERSION:
        raise ValueError("unsupported training checkpoint format")

    if payload.get("environment_version") != _ENVIRONMENT_VERSION:
        raise ValueError("checkpoint environment version does not match runtime")

    if payload.get("session_identity") != _session_identity(config):
        raise ValueError("checkpoint does not match familiar sequence config")

    if payload.get("scenario_identity") != _scenario_identity(scenario):
        raise ValueError("checkpoint scenario does not match runtime")

    if payload.get("core_config") != asdict(trainer.core.config):
        raise ValueError("checkpoint core config does not match trainer")

    if payload.get("input_spec") != asdict(trainer.input_spec):
        raise ValueError("checkpoint input spec does not match trainer")

    if payload.get("trainer_config") != asdict(trainer.config):
        raise ValueError("checkpoint trainer config does not match trainer")

    completed_episodes = _required_int(payload, "completed_episodes")
    raw_records = _required_sequence(payload, "records")
    records = tuple(_record_from_payload(item) for item in raw_records)
    _validate_checkpoint_progress(config, completed_episodes, records)

    rng_state = payload.get("torch_rng_state")
    if not isinstance(rng_state, torch.Tensor):
        raise ValueError("checkpoint torch_rng_state must be a tensor")

    trainer.core.load_state_dict(_required_mapping(payload, "core_state"))
    trainer.optimizer.load_state_dict(_required_mapping(payload, "optimizer_state"))
    torch.random.set_rng_state(rng_state.cpu())
    trainer.reset_episode()
    return completed_episodes, records


def export_training_history_csv(
    result: TrainingSessionResult,
    path: Path,
) -> None:
    """Write complete transition-level training history as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    with temporary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "episode_index",
                "sequence_index",
                "episode_id",
                "source_step_id",
                "action",
                "total_loss",
                "sensor_prediction_loss",
                "controllable_change_loss",
                "confidence_calibration_loss",
                "mean_absolute_error",
                "external_change_mean_absolute",
                "mean_confidence",
                "gradient_norm",
                "terminated",
            )
        )
        for record in result.records:
            writer.writerow(
                (
                    record.episode_index,
                    record.sequence_index,
                    record.episode_id,
                    record.source_step_id,
                    record.action.value,
                    record.total_loss,
                    record.sensor_prediction_loss,
                    record.controllable_change_loss,
                    record.confidence_calibration_loss,
                    record.mean_absolute_error,
                    record.external_change_mean_absolute,
                    record.mean_confidence,
                    record.gradient_norm,
                    record.terminated,
                )
            )
    temporary_path.replace(path)


def export_prediction_error_svg(
    result: TrainingSessionResult,
    path: Path,
    *,
    width: int = 800,
    height: int = 420,
) -> None:
    """Write a dependency-free SVG of episode mean prediction error."""
    if width < 320 or height < 240:
        raise ValueError("SVG dimensions are too small")

    errors = result.episode_mean_absolute_errors
    margin_left = 70.0
    margin_right = 30.0
    margin_top = 35.0
    margin_bottom = 60.0
    plot_width = width - margin_left - margin_right
    plot_height = height - margin_top - margin_bottom
    maximum_error = max(errors)
    y_maximum = maximum_error * 1.05 if maximum_error > 0.0 else 1.0

    def x_position(index: int) -> float:
        if len(errors) == 1:
            return margin_left + plot_width / 2.0
        return margin_left + plot_width * index / (len(errors) - 1)

    def y_position(error: float) -> float:
        return margin_top + plot_height * (1.0 - error / y_maximum)

    points = " ".join(
        f"{x_position(index):.2f},{y_position(error):.2f}"
        for index, error in enumerate(errors)
    )
    circles = "\n".join(
        (
            f'  <circle cx="{x_position(index):.2f}" cy="{y_position(error):.2f}" '
            'r="3" fill="#111111" />'
        )
        for index, error in enumerate(errors)
    )
    svg = f"""<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect width="100%" height="100%" fill="#ffffff" />
  <text x="{width / 2:.2f}" y="22" text-anchor="middle" font-family="sans-serif" font-size="16">SeedMind familiar-sequence prediction error</text>
  <line x1="{margin_left:.2f}" y1="{margin_top:.2f}" x2="{margin_left:.2f}" y2="{margin_top + plot_height:.2f}" stroke="#111111" />
  <line x1="{margin_left:.2f}" y1="{margin_top + plot_height:.2f}" x2="{margin_left + plot_width:.2f}" y2="{margin_top + plot_height:.2f}" stroke="#111111" />
  <text x="{margin_left - 8:.2f}" y="{margin_top + 5:.2f}" text-anchor="end" font-family="sans-serif" font-size="11">{y_maximum:.6f}</text>
  <text x="{margin_left - 8:.2f}" y="{margin_top + plot_height + 4:.2f}" text-anchor="end" font-family="sans-serif" font-size="11">0</text>
  <text x="{width / 2:.2f}" y="{height - 15}" text-anchor="middle" font-family="sans-serif" font-size="12">Completed episode</text>
  <text x="18" y="{height / 2:.2f}" text-anchor="middle" font-family="sans-serif" font-size="12" transform="rotate(-90 18 {height / 2:.2f})">Mean absolute error</text>
  <polyline points="{points}" fill="none" stroke="#111111" stroke-width="2" />
{circles}
  <text x="{margin_left:.2f}" y="{margin_top + plot_height + 20:.2f}" text-anchor="middle" font-family="sans-serif" font-size="11">1</text>
  <text x="{margin_left + plot_width:.2f}" y="{margin_top + plot_height + 20:.2f}" text-anchor="middle" font-family="sans-serif" font-size="11">{result.completed_episodes}</text>
</svg>
"""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(svg, encoding="ascii")
    temporary_path.replace(path)


def _scenario_identity(scenario: NurseryScenario) -> dict[str, object]:
    """Return a stable fingerprint for the seeded environment definition."""
    canonical = {
        "scenario_id": scenario.scenario_id,
        "seed": scenario.seed,
        "step_budget": scenario.step_budget,
        "initial_state": repr(scenario.initial_state),
        "world_processes": [repr(process) for process in scenario.world_processes],
    }
    encoded = json.dumps(
        canonical,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    return {
        "scenario_id": scenario.scenario_id,
        "fingerprint": hashlib.sha256(encoded).hexdigest(),
    }


def _session_identity(config: FamiliarSequenceConfig) -> dict[str, object]:
    """Return checkpoint fields that must remain fixed while resuming."""
    return {
        "seed": config.seed,
        "action_sequence": [action.value for action in config.action_sequence],
    }


def _record_to_payload(record: TrainingStepRecord) -> dict[str, object]:
    """Convert one typed history record to safe primitive checkpoint data."""
    return {
        "episode_index": record.episode_index,
        "sequence_index": record.sequence_index,
        "episode_id": record.episode_id,
        "source_step_id": record.source_step_id,
        "action": record.action.value,
        "total_loss": record.total_loss,
        "sensor_prediction_loss": record.sensor_prediction_loss,
        "controllable_change_loss": record.controllable_change_loss,
        "confidence_calibration_loss": record.confidence_calibration_loss,
        "mean_absolute_error": record.mean_absolute_error,
        "external_change_mean_absolute": record.external_change_mean_absolute,
        "mean_confidence": record.mean_confidence,
        "gradient_norm": record.gradient_norm,
        "terminated": record.terminated,
    }


def _record_from_payload(value: object) -> TrainingStepRecord:
    """Validate and rebuild one history record from checkpoint data."""
    if not isinstance(value, Mapping):
        raise ValueError("checkpoint record must be a mapping")

    action_value = value.get("action")
    if not isinstance(action_value, str):
        raise ValueError("checkpoint action must be a string")

    try:
        action = PrimitiveAction(action_value)
    except ValueError as error:
        raise ValueError("checkpoint action is invalid") from error

    return TrainingStepRecord(
        episode_index=_mapping_int(value, "episode_index"),
        sequence_index=_mapping_int(value, "sequence_index"),
        episode_id=_mapping_str(value, "episode_id"),
        source_step_id=_mapping_int(value, "source_step_id"),
        action=action,
        total_loss=_mapping_float(value, "total_loss"),
        sensor_prediction_loss=_mapping_float(value, "sensor_prediction_loss"),
        controllable_change_loss=_mapping_float(value, "controllable_change_loss"),
        confidence_calibration_loss=_mapping_float(
            value,
            "confidence_calibration_loss",
        ),
        mean_absolute_error=_mapping_float(value, "mean_absolute_error"),
        external_change_mean_absolute=_mapping_float(
            value,
            "external_change_mean_absolute",
        ),
        mean_confidence=_mapping_float(value, "mean_confidence"),
        gradient_norm=_mapping_float(value, "gradient_norm"),
        terminated=_mapping_bool(value, "terminated"),
    )


def _validate_checkpoint_progress(
    config: FamiliarSequenceConfig,
    completed_episodes: int,
    records: Sequence[TrainingStepRecord],
) -> None:
    """Ensure progress and history represent complete episode boundaries."""
    if completed_episodes < 0 or completed_episodes > config.episode_count:
        raise ValueError("checkpoint completed_episodes is out of range")

    expected_records = completed_episodes * len(config.action_sequence)
    if len(records) != expected_records:
        raise ValueError("checkpoint records do not match completed episodes")

    for record_index, record in enumerate(records):
        episode_index, sequence_index = divmod(
            record_index,
            len(config.action_sequence),
        )
        if record.episode_index != episode_index:
            raise ValueError("checkpoint episode history is not ordered")
        if record.sequence_index != sequence_index:
            raise ValueError("checkpoint sequence history is not ordered")
        if record.action is not config.action_sequence[sequence_index]:
            raise ValueError("checkpoint action history does not match config")


def _required_int(payload: Mapping[str, object], key: str) -> int:
    """Read one exact integer checkpoint field."""
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"checkpoint {key} must be an integer")
    return value


def _required_sequence(
    payload: Mapping[str, object],
    key: str,
) -> Sequence[object]:
    """Read one non-string sequence checkpoint field."""
    value = payload.get(key)
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        raise ValueError(f"checkpoint {key} must be a sequence")
    return cast(Sequence[object], value)


def _required_mapping(
    payload: Mapping[str, object],
    key: str,
) -> dict[str, Any]:
    """Read one dictionary checkpoint field."""
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"checkpoint {key} must be a dictionary")
    return cast(dict[str, Any], value)


def _mapping_int(value: Mapping[object, object], key: str) -> int:
    """Read one exact integer from a generic mapping."""
    item = value.get(key)
    if not isinstance(item, int) or isinstance(item, bool):
        raise ValueError(f"checkpoint record {key} must be an integer")
    return item


def _mapping_float(value: Mapping[object, object], key: str) -> float:
    """Read one numeric float from a generic mapping."""
    item = value.get(key)
    if not isinstance(item, (int, float)) or isinstance(item, bool):
        raise ValueError(f"checkpoint record {key} must be numeric")
    return float(item)


def _mapping_str(value: Mapping[object, object], key: str) -> str:
    """Read one string from a generic mapping."""
    item = value.get(key)
    if not isinstance(item, str):
        raise ValueError(f"checkpoint record {key} must be a string")
    return item


def _mapping_bool(value: Mapping[object, object], key: str) -> bool:
    """Read one boolean from a generic mapping."""
    item = value.get(key)
    if not isinstance(item, bool):
        raise ValueError(f"checkpoint record {key} must be a boolean")
    return item
