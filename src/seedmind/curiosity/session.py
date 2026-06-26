"""Live curiosity-guided predictive training in the SeedMind nursery."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from statistics import fmean
from typing import Protocol

from seedmind.contracts import PrimitiveAction
from seedmind.curiosity.policy import (
    CuriosityConfig,
    CuriositySelection,
    CuriositySubsystem,
)
from seedmind.environment import NurseryRuntime, NurseryScenario
from seedmind.training import OnlinePredictiveTrainer, OnlineTrainingMetrics, collect_experience


class ScenarioFactory(Protocol):
    """Construct a deterministic nursery scenario from an integer seed."""

    def create(self, seed: int) -> NurseryScenario:
        """Return one scenario for the supplied seed."""
        ...


@dataclass(frozen=True, slots=True)
class CuriosityTrainingConfig:
    """Seed and bounded curiosity policy for one live nursery session."""

    seed: int = 7
    curiosity: CuriosityConfig = field(default_factory=CuriosityConfig)

    def __post_init__(self) -> None:
        """Reject invalid deterministic scenario seeds."""
        if self.seed < 0:
            raise ValueError("seed must not be negative")


@dataclass(frozen=True, slots=True)
class CuriosityTrainingStepRecord:
    """Selection evidence and predictive metrics from one live experiment."""

    step_index: int
    episode_id: str
    source_step_id: int
    action: PrimitiveAction
    remaining_budget: int
    selected_score: float
    learning_progress: float
    novelty: float
    uncertainty: float
    information_gain: float
    repetition_penalty: float
    stagnation_penalty: float
    prediction_error: float
    total_loss: float
    sensor_prediction_loss: float
    controllable_change_loss: float
    external_change_mean_absolute: float
    mean_confidence: float
    gradient_norm: float
    terminated: bool

    @classmethod
    def from_selection_and_metrics(
        cls,
        selection: CuriositySelection,
        metrics: OnlineTrainingMetrics,
    ) -> CuriosityTrainingStepRecord:
        """Combine pre-action curiosity evidence with post-action learner metrics."""
        candidate = selection.selected_candidate
        return cls(
            step_index=selection.step_index,
            episode_id=metrics.episode_id,
            source_step_id=metrics.source_step_id,
            action=selection.selected_action,
            remaining_budget=selection.remaining_budget,
            selected_score=candidate.score,
            learning_progress=candidate.learning_progress,
            novelty=candidate.novelty,
            uncertainty=candidate.uncertainty,
            information_gain=candidate.information_gain,
            repetition_penalty=candidate.repetition_penalty,
            stagnation_penalty=candidate.stagnation_penalty,
            prediction_error=metrics.mean_absolute_error,
            total_loss=metrics.total_loss,
            sensor_prediction_loss=metrics.sensor_prediction_loss,
            controllable_change_loss=metrics.controllable_change_loss,
            external_change_mean_absolute=metrics.external_change_mean_absolute,
            mean_confidence=metrics.mean_confidence,
            gradient_norm=metrics.gradient_norm,
            terminated=metrics.terminated,
        )


@dataclass(frozen=True, slots=True)
class CuriosityTrainingResult:
    """Complete bounded live experiment timeline and predictive evidence."""

    config: CuriosityTrainingConfig
    scenario_id: str
    selections: tuple[CuriositySelection, ...]
    records: tuple[CuriosityTrainingStepRecord, ...]

    def __post_init__(self) -> None:
        """Validate complete matched selection and metric histories."""
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")

        expected_count = self.config.curiosity.play_budget
        if len(self.selections) != expected_count or len(self.records) != expected_count:
            raise ValueError("result does not cover the complete curiosity play budget")

        for step_index, (selection, record) in enumerate(
            zip(self.selections, self.records, strict=True)
        ):
            if selection.step_index != step_index or record.step_index != step_index:
                raise ValueError("curiosity timeline step indices are not contiguous")

            if selection.selected_action is not record.action:
                raise ValueError("selection action does not match training record")

            expected_remaining = expected_count - step_index - 1
            if (
                selection.remaining_budget != expected_remaining
                or record.remaining_budget != expected_remaining
            ):
                raise ValueError("remaining budget does not match timeline position")

    @property
    def selection_count(self) -> int:
        """Return the number of completed live experiments."""
        return len(self.records)

    @property
    def mean_prediction_error(self) -> float:
        """Return the mean pre-update prediction error across the session."""
        return fmean(record.prediction_error for record in self.records)

    @property
    def initial_prediction_error(self) -> float:
        """Return prediction error from the first selected experiment."""
        return self.records[0].prediction_error

    @property
    def final_prediction_error(self) -> float:
        """Return prediction error from the final selected experiment."""
        return self.records[-1].prediction_error

    @property
    def action_counts(self) -> tuple[tuple[PrimitiveAction, int], ...]:
        """Return stable action counts in configured experiment order."""
        counts = Counter(record.action for record in self.records)
        return tuple(
            (action, counts[action])
            for action in self.config.curiosity.experiment_actions
            if counts[action] > 0
        )


class CuriosityTrainingSession:
    """Select, execute, and learn from bounded curiosity experiments online."""

    def __init__(
        self,
        trainer: OnlinePredictiveTrainer,
        scenario_factory: ScenarioFactory,
        config: CuriosityTrainingConfig,
    ) -> None:
        """Bind one predictive learner, scenario, and curiosity policy."""
        self.trainer = trainer
        self.config = config
        self.scenario = scenario_factory.create(config.seed)
        if config.curiosity.play_budget > self.scenario.step_budget:
            raise ValueError("curiosity play budget exceeds scenario step budget")

    def run(self) -> CuriosityTrainingResult:
        """Run one fresh live episode until the curiosity budget is exhausted."""
        curiosity = CuriositySubsystem(self.config.curiosity)
        runtime = NurseryRuntime(
            initial_state=self.scenario.initial_state,
            episode_id=f"{self.scenario.scenario_id}-curiosity",
            resource_state_provider=self.scenario.resource_state,
            world_processes=self.scenario.world_processes,
        )
        selections: list[CuriositySelection] = []
        records: list[CuriosityTrainingStepRecord] = []
        self.trainer.reset_episode()

        while not curiosity.budget_exhausted:
            observation = runtime.observe()
            selection = curiosity.select(observation.available_actions)
            experience = collect_experience(runtime, selection.selected_action)
            metrics = self.trainer.train_transition(experience)
            curiosity.observe(selection.selected_action, metrics.mean_absolute_error)
            selections.append(selection)
            records.append(
                CuriosityTrainingStepRecord.from_selection_and_metrics(
                    selection,
                    metrics,
                )
            )

            if experience.terminated:
                raise RuntimeError("curiosity experiment terminated before budget exhaustion")

        self.trainer.reset_episode()
        return CuriosityTrainingResult(
            config=self.config,
            scenario_id=self.scenario.scenario_id,
            selections=tuple(selections),
            records=tuple(records),
        )


def export_curiosity_training_json(
    result: CuriosityTrainingResult,
    path: Path,
) -> None:
    """Write an ASCII live experiment timeline with candidates and metrics."""
    payload = {
        "scenario_id": result.scenario_id,
        "seed": result.config.seed,
        "play_budget": result.config.curiosity.play_budget,
        "selection_count": result.selection_count,
        "mean_prediction_error": result.mean_prediction_error,
        "initial_prediction_error": result.initial_prediction_error,
        "final_prediction_error": result.final_prediction_error,
        "action_counts": {action.value: count for action, count in result.action_counts},
        "timeline": [
            {
                "step_index": record.step_index,
                "source_step_id": record.source_step_id,
                "selected_action": record.action.value,
                "remaining_budget": record.remaining_budget,
                "selected_score": record.selected_score,
                "learning_progress": record.learning_progress,
                "novelty": record.novelty,
                "uncertainty": record.uncertainty,
                "information_gain": record.information_gain,
                "repetition_penalty": record.repetition_penalty,
                "stagnation_penalty": record.stagnation_penalty,
                "prediction_error": record.prediction_error,
                "total_loss": record.total_loss,
                "sensor_prediction_loss": record.sensor_prediction_loss,
                "controllable_change_loss": record.controllable_change_loss,
                "external_change_mean_absolute": (record.external_change_mean_absolute),
                "mean_confidence": record.mean_confidence,
                "gradient_norm": record.gradient_norm,
                "terminated": record.terminated,
                "candidates": [
                    {
                        "action": candidate.action.value,
                        "sample_count": candidate.sample_count,
                        "learning_progress": candidate.learning_progress,
                        "novelty": candidate.novelty,
                        "uncertainty": candidate.uncertainty,
                        "information_gain": candidate.information_gain,
                        "repetition_penalty": candidate.repetition_penalty,
                        "stagnation_penalty": candidate.stagnation_penalty,
                        "score": candidate.score,
                    }
                    for candidate in selection.candidates
                ],
            }
            for selection, record in zip(
                result.selections,
                result.records,
                strict=True,
            )
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def export_curiosity_training_csv(
    result: CuriosityTrainingResult,
    path: Path,
) -> None:
    """Write one ASCII row per selected live nursery experiment."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    with temporary_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "episode_id",
                "source_step_id",
                "action",
                "remaining_budget",
                "selected_score",
                "learning_progress",
                "novelty",
                "uncertainty",
                "information_gain",
                "repetition_penalty",
                "stagnation_penalty",
                "prediction_error",
                "total_loss",
                "sensor_prediction_loss",
                "controllable_change_loss",
                "external_change_mean_absolute",
                "mean_confidence",
                "gradient_norm",
                "terminated",
            )
        )
        for record in result.records:
            writer.writerow(
                (
                    record.step_index,
                    record.episode_id,
                    record.source_step_id,
                    record.action.value,
                    record.remaining_budget,
                    record.selected_score,
                    record.learning_progress,
                    record.novelty,
                    record.uncertainty,
                    record.information_gain,
                    record.repetition_penalty,
                    record.stagnation_penalty,
                    record.prediction_error,
                    record.total_loss,
                    record.sensor_prediction_loss,
                    record.controllable_change_loss,
                    record.external_change_mean_absolute,
                    record.mean_confidence,
                    record.gradient_norm,
                    record.terminated,
                )
            )
    temporary_path.replace(path)
