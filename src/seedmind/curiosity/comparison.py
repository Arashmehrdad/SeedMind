"""Matched live comparison of curiosity and random nursery exploration."""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import dataclass, field
from math import isfinite
from pathlib import Path
from random import Random
from statistics import fmean
from typing import Protocol

from seedmind.contracts import PrimitiveAction
from seedmind.curiosity.policy import CuriosityConfig, CuriositySubsystem
from seedmind.environment import NurseryRuntime, NurseryScenario
from seedmind.self_model import SelfModelConfig, SelfModelRegistry, SelfModelSnapshot
from seedmind.training import (
    ExperienceTransition,
    OnlineTrainingMetrics,
    collect_experience,
)


class ScenarioFactory(Protocol):
    """Construct the deterministic nursery used by every matched trial."""

    def create(self, seed: int) -> NurseryScenario:
        """Return one scenario for the supplied seed."""
        ...


class PredictiveTrainer(Protocol):
    """Small trainer boundary required by the exploration comparison."""

    def reset_episode(self) -> None:
        """Clear recurrent state before or after a comparison episode."""
        ...

    def train_transition(
        self,
        experience: ExperienceTransition,
    ) -> OnlineTrainingMetrics:
        """Train from one transition and return pre-update error metrics."""
        ...


class TrainerFactory(Protocol):
    """Create identically configured trainers from explicit model seeds."""

    def __call__(
        self,
        model_seed: int,
        scenario: NurseryScenario,
    ) -> PredictiveTrainer:
        """Return a fresh predictive trainer for one matched trial."""
        ...


_DEFAULT_EXPERIMENT_ACTIONS = (
    PrimitiveAction.TURN_LEFT,
    PrimitiveAction.TURN_RIGHT,
    PrimitiveAction.MOVE_FORWARD,
    PrimitiveAction.INSPECT,
    PrimitiveAction.PUSH,
    PrimitiveAction.WAIT,
)
_DEFAULT_BODY_PROBES = (
    PrimitiveAction.TURN_LEFT,
    PrimitiveAction.TURN_RIGHT,
    PrimitiveAction.MOVE_FORWARD,
)


@dataclass(frozen=True, slots=True)
class CuriosityComparisonConfig:
    """Matched budgets, seeds, discovery thresholds, and noise bounds."""

    scenario_seed: int = 7
    model_seed: int = 41
    random_seed: int = 97
    trial_count: int = 8
    curiosity: CuriosityConfig = field(
        default_factory=lambda: CuriosityConfig(
            play_budget=24,
            experiment_actions=_DEFAULT_EXPERIMENT_ACTIONS,
        )
    )
    body_probe_actions: tuple[PrimitiveAction, ...] = _DEFAULT_BODY_PROBES
    minimum_effect_samples: int = 4
    minimum_effect_frequency: float = 0.25
    effect_threshold: float = 1e-6
    body_score_threshold: float = 0.2
    noise_action: PrimitiveAction = PrimitiveAction.WAIT
    maximum_noise_share: float = 0.35
    maximum_noise_streak: int = 2

    def __post_init__(self) -> None:
        """Validate deterministic seeds, discovery settings, and action sets."""
        for seed_name, seed_value in (
            ("scenario_seed", self.scenario_seed),
            ("model_seed", self.model_seed),
            ("random_seed", self.random_seed),
        ):
            if seed_value < 0:
                raise ValueError(f"{seed_name} must not be negative")

        if self.trial_count <= 0:
            raise ValueError("trial_count must be positive")

        if self.minimum_effect_samples <= 0:
            raise ValueError("minimum_effect_samples must be positive")

        for threshold_name, threshold_value in (
            ("minimum_effect_frequency", self.minimum_effect_frequency),
            ("body_score_threshold", self.body_score_threshold),
            ("maximum_noise_share", self.maximum_noise_share),
        ):
            if not isfinite(threshold_value) or not 0.0 <= threshold_value <= 1.0:
                raise ValueError(f"{threshold_name} must be between zero and one")

        if not isfinite(self.effect_threshold) or self.effect_threshold < 0.0:
            raise ValueError("effect_threshold must be finite and non-negative")

        if self.maximum_noise_streak <= 0:
            raise ValueError("maximum_noise_streak must be positive")

        if not self.body_probe_actions:
            raise ValueError("body_probe_actions must not be empty")

        if len(self.body_probe_actions) != len(set(self.body_probe_actions)):
            raise ValueError("body_probe_actions must be unique")

        experiment_actions = set(self.curiosity.experiment_actions)
        if not set(self.body_probe_actions).issubset(experiment_actions):
            raise ValueError("body_probe_actions must be curiosity experiments")

        if self.noise_action not in experiment_actions:
            raise ValueError("noise_action must be a curiosity experiment")


@dataclass(frozen=True, slots=True)
class ExplorationActionCount:
    """Number of times one primitive experiment was selected."""

    action: PrimitiveAction
    count: int

    def __post_init__(self) -> None:
        """Reject negative action counts."""
        if self.count < 0:
            raise ValueError("count must not be negative")


@dataclass(frozen=True, slots=True)
class DiscoveryTimelinePoint:
    """Independent causal-discovery evidence after one exploration step."""

    step_number: int
    action: PrimitiveAction
    prediction_error: float
    discovered_effect_actions: tuple[PrimitiveAction, ...]
    effect_recall: float
    discovery_progress: float
    body_sensor_indices: tuple[int, ...]
    body_precision: float
    body_recall: float
    body_f1: float
    noise_streak: int
    maximum_noise_streak: int

    def __post_init__(self) -> None:
        """Validate timeline position, normalized metrics, and finite error."""
        if self.step_number <= 0:
            raise ValueError("step_number must be positive")

        if not isfinite(self.prediction_error) or self.prediction_error < 0.0:
            raise ValueError("prediction_error must be finite and non-negative")

        for metric in (
            self.effect_recall,
            self.discovery_progress,
            self.body_precision,
            self.body_recall,
            self.body_f1,
        ):
            if not 0.0 <= metric <= 1.0:
                raise ValueError("discovery metrics must be between zero and one")

        if self.noise_streak < 0 or self.maximum_noise_streak < 0:
            raise ValueError("noise streaks must not be negative")

        if self.noise_streak > self.maximum_noise_streak:
            raise ValueError("noise_streak must not exceed maximum_noise_streak")


@dataclass(frozen=True, slots=True)
class ExplorationTrialMetrics:
    """One curiosity or random trial under the same exploration budget."""

    strategy: str
    trial_index: int
    model_seed: int
    action_counts: tuple[ExplorationActionCount, ...]
    timeline: tuple[DiscoveryTimelinePoint, ...]
    discovery_auc: float
    final_effect_recall: float
    full_discovery_step: int | None
    final_body_f1: float
    mean_prediction_error: float
    noise_selection_count: int
    maximum_noise_streak: int
    final_noise_streak: int

    def __post_init__(self) -> None:
        """Validate complete trial history and aggregate metric consistency."""
        if not self.strategy.strip():
            raise ValueError("strategy must not be empty")

        if self.trial_index < 0:
            raise ValueError("trial_index must not be negative")

        if self.model_seed < 0:
            raise ValueError("model_seed must not be negative")

        if not self.timeline:
            raise ValueError("timeline must not be empty")

        if sum(item.count for item in self.action_counts) != len(self.timeline):
            raise ValueError("action counts must cover the complete timeline")

        for step_number, point in enumerate(self.timeline, start=1):
            if point.step_number != step_number:
                raise ValueError("timeline step numbers must be contiguous")

        for metric in (
            self.discovery_auc,
            self.final_effect_recall,
            self.final_body_f1,
        ):
            if not 0.0 <= metric <= 1.0:
                raise ValueError("trial summary metrics must be between zero and one")

        if self.full_discovery_step is not None and not (
            1 <= self.full_discovery_step <= len(self.timeline)
        ):
            raise ValueError("full_discovery_step must be inside the trial budget")

        if not isfinite(self.mean_prediction_error) or self.mean_prediction_error < 0.0:
            raise ValueError("mean_prediction_error must be finite and non-negative")

        if not 0 <= self.noise_selection_count <= len(self.timeline):
            raise ValueError("noise_selection_count must fit inside the trial budget")

        if self.maximum_noise_streak < 0 or self.final_noise_streak < 0:
            raise ValueError("noise streaks must not be negative")

        if self.final_noise_streak > self.maximum_noise_streak:
            raise ValueError("final_noise_streak must not exceed maximum_noise_streak")

    @property
    def effective_full_discovery_step(self) -> int:
        """Return budget plus one when full discovery was not reached."""
        return (
            self.full_discovery_step
            if self.full_discovery_step is not None
            else len(self.timeline) + 1
        )

    @property
    def noise_share(self) -> float:
        """Return the fraction of selections spent on the no-control action."""
        return self.noise_selection_count / len(self.timeline)


@dataclass(frozen=True, slots=True)
class CuriosityComparisonResult:
    """Repeated matched trials and the complete Week 4 comparison verdict."""

    config: CuriosityComparisonConfig
    scenario_id: str
    oracle_effect_actions: tuple[PrimitiveAction, ...]
    oracle_body_sensor_indices: tuple[int, ...]
    curiosity_trials: tuple[ExplorationTrialMetrics, ...]
    random_trials: tuple[ExplorationTrialMetrics, ...]
    curiosity_mean_discovery_auc: float
    random_mean_discovery_auc: float
    curiosity_mean_final_effect_recall: float
    random_mean_final_effect_recall: float
    curiosity_mean_full_discovery_step: float
    random_mean_full_discovery_step: float
    curiosity_mean_final_body_f1: float
    random_mean_final_body_f1: float
    curiosity_mean_noise_share: float
    random_mean_noise_share: float
    curiosity_maximum_noise_streak: int
    noise_loop_avoided: bool
    pass_gate: bool

    def __post_init__(self) -> None:
        """Validate paired trial counts, oracle evidence, and aggregates."""
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")

        if not self.oracle_effect_actions:
            raise ValueError("oracle_effect_actions must not be empty")

        if not self.oracle_body_sensor_indices:
            raise ValueError("oracle_body_sensor_indices must not be empty")

        if len(self.curiosity_trials) != self.config.trial_count:
            raise ValueError("curiosity trial count does not match config")

        if len(self.random_trials) != self.config.trial_count:
            raise ValueError("random trial count does not match config")

        normalized_metrics = (
            self.curiosity_mean_discovery_auc,
            self.random_mean_discovery_auc,
            self.curiosity_mean_final_effect_recall,
            self.random_mean_final_effect_recall,
            self.curiosity_mean_final_body_f1,
            self.random_mean_final_body_f1,
            self.curiosity_mean_noise_share,
            self.random_mean_noise_share,
        )
        if any(not 0.0 <= metric <= 1.0 for metric in normalized_metrics):
            raise ValueError("comparison metrics must be between zero and one")

        if self.curiosity_mean_full_discovery_step <= 0.0:
            raise ValueError("curiosity discovery step must be positive")

        if self.random_mean_full_discovery_step <= 0.0:
            raise ValueError("random discovery step must be positive")

        if self.curiosity_maximum_noise_streak < 0:
            raise ValueError("curiosity_maximum_noise_streak must not be negative")


class CuriosityRandomComparisonExperiment:
    """Run paired live curiosity and random exploration trials."""

    def __init__(
        self,
        scenario_factory: ScenarioFactory,
        trainer_factory: TrainerFactory,
        config: CuriosityComparisonConfig | None = None,
    ) -> None:
        """Bind deterministic factories and derive evaluator-only oracles."""
        self.config = CuriosityComparisonConfig() if config is None else config
        self.scenario = scenario_factory.create(self.config.scenario_seed)
        self.trainer_factory = trainer_factory
        if self.config.curiosity.play_budget > self.scenario.step_budget:
            raise ValueError("curiosity play budget exceeds scenario step budget")

        interface_runtime = self._runtime("interface")
        self.sensor_size = interface_runtime.sensor_size
        self.oracle_effect_actions, self.oracle_body_sensor_indices = self._derive_oracles()
        if self.config.noise_action in self.oracle_effect_actions:
            raise ValueError("noise_action must have no direct controllable effect")

        self.self_model_config = SelfModelConfig(
            sensor_size=self.sensor_size,
            minimum_samples=self.config.minimum_effect_samples,
            effect_threshold=self.config.effect_threshold,
            body_score_threshold=self.config.body_score_threshold,
            body_probe_actions=self.config.body_probe_actions,
        )

    def run(self) -> CuriosityComparisonResult:
        """Run paired trials, aggregate discovery speed, and evaluate the gate."""
        curiosity_trials: list[ExplorationTrialMetrics] = []
        random_trials: list[ExplorationTrialMetrics] = []
        for trial_index in range(self.config.trial_count):
            model_seed = self.config.model_seed + trial_index
            curiosity_trials.append(
                self._run_trial(
                    strategy="curiosity",
                    trial_index=trial_index,
                    model_seed=model_seed,
                )
            )
            random_trials.append(
                self._run_trial(
                    strategy="random",
                    trial_index=trial_index,
                    model_seed=model_seed,
                )
            )

        curiosity = tuple(curiosity_trials)
        random = tuple(random_trials)
        curiosity_mean_auc = fmean(trial.discovery_auc for trial in curiosity)
        random_mean_auc = fmean(trial.discovery_auc for trial in random)
        curiosity_mean_effect_recall = fmean(trial.final_effect_recall for trial in curiosity)
        random_mean_effect_recall = fmean(trial.final_effect_recall for trial in random)
        curiosity_mean_step = fmean(trial.effective_full_discovery_step for trial in curiosity)
        random_mean_step = fmean(trial.effective_full_discovery_step for trial in random)
        curiosity_mean_body_f1 = fmean(trial.final_body_f1 for trial in curiosity)
        random_mean_body_f1 = fmean(trial.final_body_f1 for trial in random)
        curiosity_mean_noise_share = fmean(trial.noise_share for trial in curiosity)
        random_mean_noise_share = fmean(trial.noise_share for trial in random)
        curiosity_maximum_noise_streak = max(trial.maximum_noise_streak for trial in curiosity)
        noise_loop_avoided = all(
            trial.noise_share <= self.config.maximum_noise_share
            and trial.maximum_noise_streak <= self.config.maximum_noise_streak
            and trial.final_noise_streak <= self.config.maximum_noise_streak
            for trial in curiosity
        )
        pass_gate = (
            curiosity_mean_auc > random_mean_auc
            and curiosity_mean_effect_recall > random_mean_effect_recall
            and curiosity_mean_step < random_mean_step
            and curiosity_mean_body_f1 >= random_mean_body_f1
            and noise_loop_avoided
        )
        return CuriosityComparisonResult(
            config=self.config,
            scenario_id=self.scenario.scenario_id,
            oracle_effect_actions=self.oracle_effect_actions,
            oracle_body_sensor_indices=self.oracle_body_sensor_indices,
            curiosity_trials=curiosity,
            random_trials=random,
            curiosity_mean_discovery_auc=curiosity_mean_auc,
            random_mean_discovery_auc=random_mean_auc,
            curiosity_mean_final_effect_recall=curiosity_mean_effect_recall,
            random_mean_final_effect_recall=random_mean_effect_recall,
            curiosity_mean_full_discovery_step=curiosity_mean_step,
            random_mean_full_discovery_step=random_mean_step,
            curiosity_mean_final_body_f1=curiosity_mean_body_f1,
            random_mean_final_body_f1=random_mean_body_f1,
            curiosity_mean_noise_share=curiosity_mean_noise_share,
            random_mean_noise_share=random_mean_noise_share,
            curiosity_maximum_noise_streak=curiosity_maximum_noise_streak,
            noise_loop_avoided=noise_loop_avoided,
            pass_gate=pass_gate,
        )

    def _run_trial(
        self,
        *,
        strategy: str,
        trial_index: int,
        model_seed: int,
    ) -> ExplorationTrialMetrics:
        """Run one complete live strategy trial with independent discovery."""
        trainer = self.trainer_factory(model_seed, self.scenario)
        trainer.reset_episode()
        runtime = self._runtime(f"{strategy}-{trial_index:04d}")
        registry = SelfModelRegistry(self.self_model_config)
        curiosity = CuriositySubsystem(self.config.curiosity) if strategy == "curiosity" else None
        random = Random(self.config.random_seed + trial_index)
        action_counts: Counter[PrimitiveAction] = Counter()
        timeline: list[DiscoveryTimelinePoint] = []
        noise_streak = 0
        maximum_noise_streak = 0

        for step_index in range(self.config.curiosity.play_budget):
            available_actions = tuple(
                action
                for action in self.config.curiosity.experiment_actions
                if action in runtime.observe().available_actions
            )
            if not available_actions:
                raise RuntimeError("no comparison experiment actions are available")

            if curiosity is not None:
                action = curiosity.select(available_actions).selected_action
            else:
                action = random.choice(available_actions)

            experience = collect_experience(runtime, action)
            metrics = trainer.train_transition(experience)
            registry.observe(experience)
            if curiosity is not None:
                curiosity.observe(action, metrics.mean_absolute_error)

            action_counts[action] += 1
            if action is self.config.noise_action:
                noise_streak += 1
                maximum_noise_streak = max(maximum_noise_streak, noise_streak)
            else:
                noise_streak = 0

            snapshot = registry.snapshot()
            discovered_effect_actions = self._discovered_effect_actions(snapshot)
            effect_recall = len(discovered_effect_actions) / len(self.oracle_effect_actions)
            discovery_progress = self._discovery_progress(snapshot)
            body_precision, body_recall, body_f1 = _set_metrics(
                predicted=snapshot.body_sensor_indices,
                expected=self.oracle_body_sensor_indices,
            )
            timeline.append(
                DiscoveryTimelinePoint(
                    step_number=step_index + 1,
                    action=action,
                    prediction_error=metrics.mean_absolute_error,
                    discovered_effect_actions=discovered_effect_actions,
                    effect_recall=effect_recall,
                    discovery_progress=discovery_progress,
                    body_sensor_indices=snapshot.body_sensor_indices,
                    body_precision=body_precision,
                    body_recall=body_recall,
                    body_f1=body_f1,
                    noise_streak=noise_streak,
                    maximum_noise_streak=maximum_noise_streak,
                )
            )
            if experience.terminated:
                raise RuntimeError("comparison episode terminated before budget exhaustion")

        trainer.reset_episode()
        full_discovery_step = next(
            (point.step_number for point in timeline if point.effect_recall == 1.0),
            None,
        )
        final_point = timeline[-1]
        return ExplorationTrialMetrics(
            strategy=strategy,
            trial_index=trial_index,
            model_seed=model_seed,
            action_counts=tuple(
                ExplorationActionCount(action=action, count=action_counts[action])
                for action in self.config.curiosity.experiment_actions
                if action_counts[action] > 0
            ),
            timeline=tuple(timeline),
            discovery_auc=fmean(point.discovery_progress for point in timeline),
            final_effect_recall=final_point.effect_recall,
            full_discovery_step=full_discovery_step,
            final_body_f1=final_point.body_f1,
            mean_prediction_error=fmean(point.prediction_error for point in timeline),
            noise_selection_count=action_counts[self.config.noise_action],
            maximum_noise_streak=maximum_noise_streak,
            final_noise_streak=noise_streak,
        )

    def _derive_oracles(
        self,
    ) -> tuple[tuple[PrimitiveAction, ...], tuple[int, ...]]:
        """Derive evaluator-only causal effects from isolated initial probes."""
        experiences = tuple(
            collect_experience(
                self._runtime(f"oracle-{action.value}"),
                action,
            )
            for action in self.config.body_probe_actions
        )
        effect_actions = tuple(
            experience.action
            for experience in experiences
            if any(
                abs(change) > self.config.effect_threshold
                for change in experience.controllable_sensor_change
            )
        )
        body_indices = tuple(
            sensor_index
            for sensor_index in range(self.sensor_size)
            if any(
                abs(experience.controllable_sensor_change[sensor_index])
                > self.config.effect_threshold
                for experience in experiences
            )
        )
        if not effect_actions or not body_indices:
            raise ValueError("body probes produce no controllable oracle effects")
        return effect_actions, body_indices

    def _discovered_effect_actions(
        self,
        snapshot: SelfModelSnapshot,
    ) -> tuple[PrimitiveAction, ...]:
        """Return oracle actions with repeated non-trivial causal evidence."""
        estimates = {estimate.action: estimate for estimate in snapshot.action_effects}
        return tuple(
            action
            for action in self.oracle_effect_actions
            if (estimate := estimates.get(action)) is not None
            and estimate.sample_count >= self.config.minimum_effect_samples
            and max(estimate.controllable_effect_frequency) >= self.config.minimum_effect_frequency
        )

    def _discovery_progress(self, snapshot: SelfModelSnapshot) -> float:
        """Return balanced support progress across every oracle effect action."""
        estimates = {estimate.action: estimate for estimate in snapshot.action_effects}
        return min(
            min(
                estimates[action].sample_count / self.config.minimum_effect_samples,
                1.0,
            )
            if action in estimates
            else 0.0
            for action in self.oracle_effect_actions
        )

    def _runtime(self, episode_suffix: str) -> NurseryRuntime:
        """Create a fresh runtime from the immutable matched scenario."""
        return NurseryRuntime(
            initial_state=self.scenario.initial_state,
            episode_id=f"{self.scenario.scenario_id}-{episode_suffix}",
            resource_state_provider=self.scenario.resource_state,
            world_processes=self.scenario.world_processes,
        )


def export_curiosity_comparison_json(
    result: CuriosityComparisonResult,
    path: Path,
) -> None:
    """Write an ASCII comparison report with aggregates and timelines."""
    payload = {
        "scenario_id": result.scenario_id,
        "config": {
            "scenario_seed": result.config.scenario_seed,
            "model_seed": result.config.model_seed,
            "random_seed": result.config.random_seed,
            "trial_count": result.config.trial_count,
            "play_budget": result.config.curiosity.play_budget,
            "experiment_actions": [
                action.value for action in result.config.curiosity.experiment_actions
            ],
            "body_probe_actions": [action.value for action in result.config.body_probe_actions],
            "minimum_effect_samples": result.config.minimum_effect_samples,
            "minimum_effect_frequency": result.config.minimum_effect_frequency,
            "noise_action": result.config.noise_action.value,
            "maximum_noise_share": result.config.maximum_noise_share,
            "maximum_noise_streak": result.config.maximum_noise_streak,
        },
        "oracle_effect_actions": [action.value for action in result.oracle_effect_actions],
        "oracle_body_sensor_indices": list(result.oracle_body_sensor_indices),
        "summary": {
            "curiosity_mean_discovery_auc": result.curiosity_mean_discovery_auc,
            "random_mean_discovery_auc": result.random_mean_discovery_auc,
            "curiosity_mean_final_effect_recall": (result.curiosity_mean_final_effect_recall),
            "random_mean_final_effect_recall": (result.random_mean_final_effect_recall),
            "curiosity_mean_full_discovery_step": (result.curiosity_mean_full_discovery_step),
            "random_mean_full_discovery_step": (result.random_mean_full_discovery_step),
            "curiosity_mean_final_body_f1": result.curiosity_mean_final_body_f1,
            "random_mean_final_body_f1": result.random_mean_final_body_f1,
            "curiosity_mean_noise_share": result.curiosity_mean_noise_share,
            "random_mean_noise_share": result.random_mean_noise_share,
            "curiosity_maximum_noise_streak": (result.curiosity_maximum_noise_streak),
            "noise_loop_avoided": result.noise_loop_avoided,
            "pass_gate": result.pass_gate,
        },
        "curiosity_trials": [_trial_payload(trial) for trial in result.curiosity_trials],
        "random_trials": [_trial_payload(trial) for trial in result.random_trials],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def export_curiosity_comparison_csv(
    result: CuriosityComparisonResult,
    path: Path,
) -> None:
    """Write one ASCII row per trial timeline point for later analysis."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    with temporary_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "strategy",
                "trial_index",
                "model_seed",
                "step_number",
                "action",
                "prediction_error",
                "discovered_effect_actions",
                "effect_recall",
                "discovery_progress",
                "body_sensor_indices",
                "body_precision",
                "body_recall",
                "body_f1",
                "noise_streak",
                "maximum_noise_streak",
            )
        )
        for trial in (*result.curiosity_trials, *result.random_trials):
            for point in trial.timeline:
                writer.writerow(
                    (
                        trial.strategy,
                        trial.trial_index,
                        trial.model_seed,
                        point.step_number,
                        point.action.value,
                        point.prediction_error,
                        ";".join(action.value for action in point.discovered_effect_actions),
                        point.effect_recall,
                        point.discovery_progress,
                        ";".join(str(index) for index in point.body_sensor_indices),
                        point.body_precision,
                        point.body_recall,
                        point.body_f1,
                        point.noise_streak,
                        point.maximum_noise_streak,
                    )
                )
    temporary_path.replace(path)


def _trial_payload(trial: ExplorationTrialMetrics) -> dict[str, object]:
    """Convert one complete trial to JSON-safe primitive values."""
    return {
        "strategy": trial.strategy,
        "trial_index": trial.trial_index,
        "model_seed": trial.model_seed,
        "action_counts": {item.action.value: item.count for item in trial.action_counts},
        "discovery_auc": trial.discovery_auc,
        "final_effect_recall": trial.final_effect_recall,
        "full_discovery_step": trial.full_discovery_step,
        "effective_full_discovery_step": trial.effective_full_discovery_step,
        "final_body_f1": trial.final_body_f1,
        "mean_prediction_error": trial.mean_prediction_error,
        "noise_selection_count": trial.noise_selection_count,
        "noise_share": trial.noise_share,
        "maximum_noise_streak": trial.maximum_noise_streak,
        "final_noise_streak": trial.final_noise_streak,
        "timeline": [
            {
                "step_number": point.step_number,
                "action": point.action.value,
                "prediction_error": point.prediction_error,
                "discovered_effect_actions": [
                    action.value for action in point.discovered_effect_actions
                ],
                "effect_recall": point.effect_recall,
                "discovery_progress": point.discovery_progress,
                "body_sensor_indices": list(point.body_sensor_indices),
                "body_precision": point.body_precision,
                "body_recall": point.body_recall,
                "body_f1": point.body_f1,
                "noise_streak": point.noise_streak,
                "maximum_noise_streak": point.maximum_noise_streak,
            }
            for point in trial.timeline
        ],
    }


def _set_metrics(
    *,
    predicted: tuple[int, ...],
    expected: tuple[int, ...],
) -> tuple[float, float, float]:
    """Return precision, recall, and F1 for anonymous body channels."""
    predicted_set = set(predicted)
    expected_set = set(expected)
    true_positive_count = len(predicted_set & expected_set)
    precision = true_positive_count / len(predicted_set) if predicted_set else 0.0
    recall = true_positive_count / len(expected_set) if expected_set else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall > 0.0 else 0.0
    return precision, recall, f1
