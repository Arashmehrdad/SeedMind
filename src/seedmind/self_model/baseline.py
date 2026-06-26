"""Matched-budget body-discovery comparison against random exploration."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from math import isfinite
from pathlib import Path
from random import Random
from statistics import fmean
from typing import Protocol

from seedmind.contracts import PrimitiveAction
from seedmind.environment import NurseryRuntime, NurseryScenario
from seedmind.self_model.action_effects import (
    SelfModelConfig,
    SelfModelRegistry,
    SelfModelSnapshot,
)
from seedmind.training import ExperienceTransition, collect_experience

_SAFE_PRIMITIVE_ACTIONS = tuple(
    action for action in PrimitiveAction if action is not PrimitiveAction.STOP
)


class ScenarioFactory(Protocol):
    """Construct deterministic nursery scenarios for comparison trials."""

    def create(self, seed: int) -> NurseryScenario:
        """Return one scenario for the supplied seed."""
        ...


@dataclass(frozen=True, slots=True)
class BodyDiscoveryBaselineConfig:
    """Settings for a matched-budget targeted-versus-random comparison."""

    scenario_seed: int = 7
    random_seed: int = 29
    transition_budget: int = 12
    random_trials: int = 16
    minimum_samples: int = 4
    effect_threshold: float = 1e-6
    prediction_tolerance: float = 1e-6
    body_score_threshold: float = 0.6
    targeted_actions: tuple[PrimitiveAction, ...] = (
        PrimitiveAction.TURN_LEFT,
        PrimitiveAction.TURN_RIGHT,
        PrimitiveAction.MOVE_FORWARD,
    )
    random_actions: tuple[PrimitiveAction, ...] = _SAFE_PRIMITIVE_ACTIONS

    def __post_init__(self) -> None:
        """Validate budgets, thresholds, and safe action pools."""
        if self.scenario_seed < 0:
            raise ValueError("scenario_seed must not be negative")

        if self.random_seed < 0:
            raise ValueError("random_seed must not be negative")

        if self.transition_budget <= 0:
            raise ValueError("transition_budget must be positive")

        if self.random_trials <= 0:
            raise ValueError("random_trials must be positive")

        if self.minimum_samples <= 0:
            raise ValueError("minimum_samples must be positive")

        for name, value in (
            ("effect_threshold", self.effect_threshold),
            ("prediction_tolerance", self.prediction_tolerance),
        ):
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")

        if not isfinite(self.body_score_threshold) or not 0.0 <= self.body_score_threshold <= 1.0:
            raise ValueError("body_score_threshold must be between zero and one")

        self._validate_action_pool("targeted_actions", self.targeted_actions)
        self._validate_action_pool("random_actions", self.random_actions)

        if not set(self.targeted_actions).issubset(self.random_actions):
            raise ValueError("targeted_actions must be included in random_actions")

    @staticmethod
    def _validate_action_pool(
        name: str,
        actions: tuple[PrimitiveAction, ...],
    ) -> None:
        """Reject empty, duplicate, or terminal action pools."""
        if not actions:
            raise ValueError(f"{name} must not be empty")

        if len(actions) != len(set(actions)):
            raise ValueError(f"{name} must contain unique actions")

        if PrimitiveAction.STOP in actions:
            raise ValueError(f"{name} must not contain stop")


@dataclass(frozen=True, slots=True)
class ActionSampleCount:
    """Number of matched-budget observations allocated to one action."""

    action: PrimitiveAction
    count: int

    def __post_init__(self) -> None:
        """Reject negative action counts."""
        if self.count < 0:
            raise ValueError("count must not be negative")


@dataclass(frozen=True, slots=True)
class BodyDiscoveryStrategyMetrics:
    """Held-out body-effect and body-channel metrics for one strategy."""

    strategy: str
    trial_index: int | None
    transition_count: int
    action_counts: tuple[ActionSampleCount, ...]
    trusted_action_count: int
    body_sensor_indices: tuple[int, ...]
    body_precision: float
    body_recall: float
    body_f1: float
    body_effect_mean_absolute_error: float
    body_effect_recall: float
    mean_body_controllability: float

    def __post_init__(self) -> None:
        """Validate stable identity, matched budget, and normalized metrics."""
        if not self.strategy.strip():
            raise ValueError("strategy must not be empty")

        if self.trial_index is not None and self.trial_index < 0:
            raise ValueError("trial_index must not be negative")

        if self.transition_count <= 0:
            raise ValueError("transition_count must be positive")

        if sum(item.count for item in self.action_counts) != self.transition_count:
            raise ValueError("action counts must sum to transition_count")

        if self.trusted_action_count < 0:
            raise ValueError("trusted_action_count must not be negative")

        for value in (
            self.body_precision,
            self.body_recall,
            self.body_f1,
            self.body_effect_recall,
            self.mean_body_controllability,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("strategy metrics must be between zero and one")

        if (
            not isfinite(self.body_effect_mean_absolute_error)
            or self.body_effect_mean_absolute_error < 0.0
        ):
            raise ValueError("body effect error must be finite and non-negative")


@dataclass(frozen=True, slots=True)
class BodyDiscoveryComparisonResult:
    """Targeted strategy, random trials, and the Week 3 comparison gate."""

    config: BodyDiscoveryBaselineConfig
    oracle_body_sensor_indices: tuple[int, ...]
    active_effect_count: int
    targeted: BodyDiscoveryStrategyMetrics
    random_trials: tuple[BodyDiscoveryStrategyMetrics, ...]
    random_mean_body_effect_error: float
    random_mean_body_effect_recall: float
    random_mean_body_f1: float
    pass_gate: bool

    def __post_init__(self) -> None:
        """Validate trial coverage, matched budgets, and aggregate ranges."""
        if not self.oracle_body_sensor_indices:
            raise ValueError("oracle body sensor indices must not be empty")

        if self.active_effect_count <= 0:
            raise ValueError("active_effect_count must be positive")

        if len(self.random_trials) != self.config.random_trials:
            raise ValueError("random trial count does not match config")

        metrics = (self.targeted, *self.random_trials)
        if any(metric.transition_count != self.config.transition_budget for metric in metrics):
            raise ValueError("all strategies must use the matched transition budget")

        if not isfinite(self.random_mean_body_effect_error):
            raise ValueError("random mean body effect error must be finite")

        for value in (
            self.random_mean_body_effect_recall,
            self.random_mean_body_f1,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("random aggregate metrics must be normalized")


class BodyDiscoveryBaselineExperiment:
    """Compare deliberate body probes with random safe primitive actions."""

    def __init__(
        self,
        scenario_factory: ScenarioFactory,
        config: BodyDiscoveryBaselineConfig | None = None,
    ) -> None:
        """Bind one deterministic scenario and matched-budget configuration."""
        self.config = BodyDiscoveryBaselineConfig() if config is None else config
        self.scenario = scenario_factory.create(self.config.scenario_seed)
        interface_runtime = self._runtime("interface")
        self.sensor_size = interface_runtime.sensor_size
        self.self_model_config = SelfModelConfig(
            sensor_size=self.sensor_size,
            minimum_samples=self.config.minimum_samples,
            effect_threshold=self.config.effect_threshold,
            body_score_threshold=self.config.body_score_threshold,
            body_probe_actions=self.config.targeted_actions,
        )
        self.evaluation_experiences = tuple(
            self._experience(action, f"evaluation-{action.value}")
            for action in self.config.targeted_actions
        )
        self.oracle_body_sensor_indices = self._oracle_body_sensor_indices()
        self.active_effect_count = sum(
            1
            for experience in self.evaluation_experiences
            for change in experience.controllable_sensor_change
            if abs(change) > self.config.effect_threshold
        )
        if not self.oracle_body_sensor_indices or self.active_effect_count == 0:
            raise ValueError("targeted actions produce no body effects in this scenario")

    def run(self) -> BodyDiscoveryComparisonResult:
        """Run one targeted schedule and repeated deterministic random trials."""
        targeted_actions = tuple(
            self.config.targeted_actions[index % len(self.config.targeted_actions)]
            for index in range(self.config.transition_budget)
        )
        targeted = self._run_strategy(
            strategy="targeted",
            trial_index=None,
            actions=targeted_actions,
        )
        random_trials = tuple(
            self._run_random_trial(trial_index) for trial_index in range(self.config.random_trials)
        )
        random_mean_error = fmean(
            metric.body_effect_mean_absolute_error for metric in random_trials
        )
        random_mean_recall = fmean(metric.body_effect_recall for metric in random_trials)
        random_mean_f1 = fmean(metric.body_f1 for metric in random_trials)
        pass_gate = (
            targeted.body_effect_mean_absolute_error < random_mean_error
            and targeted.body_effect_recall > random_mean_recall
            and targeted.body_f1 > random_mean_f1
        )
        return BodyDiscoveryComparisonResult(
            config=self.config,
            oracle_body_sensor_indices=self.oracle_body_sensor_indices,
            active_effect_count=self.active_effect_count,
            targeted=targeted,
            random_trials=random_trials,
            random_mean_body_effect_error=random_mean_error,
            random_mean_body_effect_recall=random_mean_recall,
            random_mean_body_f1=random_mean_f1,
            pass_gate=pass_gate,
        )

    def _run_random_trial(self, trial_index: int) -> BodyDiscoveryStrategyMetrics:
        """Run one independently seeded uniform safe-action baseline."""
        rng = Random(self.config.random_seed + trial_index)
        actions = tuple(
            rng.choice(self.config.random_actions) for _ in range(self.config.transition_budget)
        )
        return self._run_strategy(
            strategy="random",
            trial_index=trial_index,
            actions=actions,
        )

    def _run_strategy(
        self,
        *,
        strategy: str,
        trial_index: int | None,
        actions: tuple[PrimitiveAction, ...],
    ) -> BodyDiscoveryStrategyMetrics:
        """Collect matched evidence and score held-out body-effect predictions."""
        if len(actions) != self.config.transition_budget:
            raise ValueError("strategy actions do not match transition budget")

        registry = SelfModelRegistry(self.self_model_config)
        action_counts = {action: 0 for action in PrimitiveAction}
        for transition_index, action in enumerate(actions):
            registry.observe(
                self._experience(
                    action,
                    f"{strategy}-{trial_index}-{transition_index:04d}",
                )
            )
            action_counts[action] += 1

        snapshot = registry.snapshot()
        predictions, trusted_action_count = self._trusted_predictions(snapshot)
        effect_error, effect_recall = self._effect_prediction_metrics(predictions)
        precision, recall, f1 = _set_metrics(
            predicted=snapshot.body_sensor_indices,
            expected=self.oracle_body_sensor_indices,
        )
        return BodyDiscoveryStrategyMetrics(
            strategy=strategy,
            trial_index=trial_index,
            transition_count=len(actions),
            action_counts=tuple(
                ActionSampleCount(action=action, count=action_counts[action])
                for action in PrimitiveAction
                if action_counts[action] > 0
            ),
            trusted_action_count=trusted_action_count,
            body_sensor_indices=snapshot.body_sensor_indices,
            body_precision=precision,
            body_recall=recall,
            body_f1=f1,
            body_effect_mean_absolute_error=effect_error,
            body_effect_recall=effect_recall,
            mean_body_controllability=snapshot.mean_body_controllability,
        )

    def _trusted_predictions(
        self,
        snapshot: SelfModelSnapshot,
    ) -> tuple[dict[PrimitiveAction, tuple[float, ...]], int]:
        """Return mean effects only for actions with enough repeated evidence."""
        effects = {estimate.action: estimate for estimate in snapshot.action_effects}
        predictions: dict[PrimitiveAction, tuple[float, ...]] = {}
        trusted_count = 0
        for action in self.config.targeted_actions:
            estimate = effects.get(action)
            if estimate is not None and estimate.sample_count >= self.config.minimum_samples:
                predictions[action] = estimate.mean_controllable_change
                trusted_count += 1
            else:
                predictions[action] = (0.0,) * self.sensor_size
        return predictions, trusted_count

    def _effect_prediction_metrics(
        self,
        predictions: dict[PrimitiveAction, tuple[float, ...]],
    ) -> tuple[float, float]:
        """Score predictions only where held-out body effects are non-zero."""
        absolute_errors: list[float] = []
        correct_effects = 0
        for experience in self.evaluation_experiences:
            prediction = predictions[experience.action]
            for predicted, actual in zip(
                prediction,
                experience.controllable_sensor_change,
                strict=True,
            ):
                if abs(actual) <= self.config.effect_threshold:
                    continue
                absolute_errors.append(abs(predicted - actual))
                if abs(predicted - actual) <= self.config.prediction_tolerance:
                    correct_effects += 1

        if not absolute_errors:
            raise ValueError("evaluation contains no active body effects")

        return (
            fmean(absolute_errors),
            correct_effects / len(absolute_errors),
        )

    def _oracle_body_sensor_indices(self) -> tuple[int, ...]:
        """Derive evaluator-only body channels from held-out causal snapshots."""
        return tuple(
            sensor_index
            for sensor_index in range(self.sensor_size)
            if any(
                abs(experience.controllable_sensor_change[sensor_index])
                > self.config.effect_threshold
                for experience in self.evaluation_experiences
            )
        )

    def _experience(
        self,
        action: PrimitiveAction,
        episode_suffix: str,
    ) -> ExperienceTransition:
        """Collect one isolated action effect from the same initial state."""
        return collect_experience(
            self._runtime(episode_suffix),
            action,
        )

    def _runtime(self, episode_suffix: str) -> NurseryRuntime:
        """Create a fresh runtime so every action starts in the same context."""
        return NurseryRuntime(
            initial_state=self.scenario.initial_state,
            episode_id=f"{self.scenario.scenario_id}-{episode_suffix}",
            resource_state_provider=self.scenario.resource_state,
            world_processes=self.scenario.world_processes,
        )


def export_body_discovery_baseline_json(
    result: BodyDiscoveryComparisonResult,
    path: Path,
) -> None:
    """Write an ASCII baseline report with config, metrics, and gate verdict."""
    payload = {
        "config": {
            "scenario_seed": result.config.scenario_seed,
            "random_seed": result.config.random_seed,
            "transition_budget": result.config.transition_budget,
            "random_trials": result.config.random_trials,
            "minimum_samples": result.config.minimum_samples,
            "effect_threshold": result.config.effect_threshold,
            "prediction_tolerance": result.config.prediction_tolerance,
            "body_score_threshold": result.config.body_score_threshold,
            "targeted_actions": [action.value for action in result.config.targeted_actions],
            "random_actions": [action.value for action in result.config.random_actions],
        },
        "oracle_body_sensor_indices": list(result.oracle_body_sensor_indices),
        "active_effect_count": result.active_effect_count,
        "targeted": _strategy_payload(result.targeted),
        "random_summary": {
            "mean_body_effect_mean_absolute_error": (result.random_mean_body_effect_error),
            "mean_body_effect_recall": result.random_mean_body_effect_recall,
            "mean_body_f1": result.random_mean_body_f1,
        },
        "random_trials": [_strategy_payload(metric) for metric in result.random_trials],
        "pass_gate": result.pass_gate,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def export_body_discovery_baseline_csv(
    result: BodyDiscoveryComparisonResult,
    path: Path,
) -> None:
    """Write targeted and random trial metrics as flat ASCII CSV rows."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    with temporary_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "strategy",
                "trial_index",
                "transition_count",
                "trusted_action_count",
                "body_sensor_indices",
                "body_precision",
                "body_recall",
                "body_f1",
                "body_effect_mean_absolute_error",
                "body_effect_recall",
                "mean_body_controllability",
                "action_counts",
            )
        )
        for metric in (result.targeted, *result.random_trials):
            writer.writerow(
                (
                    metric.strategy,
                    "" if metric.trial_index is None else metric.trial_index,
                    metric.transition_count,
                    metric.trusted_action_count,
                    ";".join(str(index) for index in metric.body_sensor_indices),
                    metric.body_precision,
                    metric.body_recall,
                    metric.body_f1,
                    metric.body_effect_mean_absolute_error,
                    metric.body_effect_recall,
                    metric.mean_body_controllability,
                    ";".join(f"{item.action.value}:{item.count}" for item in metric.action_counts),
                )
            )
    temporary_path.replace(path)


def _strategy_payload(metric: BodyDiscoveryStrategyMetrics) -> dict[str, object]:
    """Convert one typed strategy result to JSON-safe primitive values."""
    return {
        "strategy": metric.strategy,
        "trial_index": metric.trial_index,
        "transition_count": metric.transition_count,
        "action_counts": {item.action.value: item.count for item in metric.action_counts},
        "trusted_action_count": metric.trusted_action_count,
        "body_sensor_indices": list(metric.body_sensor_indices),
        "body_precision": metric.body_precision,
        "body_recall": metric.body_recall,
        "body_f1": metric.body_f1,
        "body_effect_mean_absolute_error": (metric.body_effect_mean_absolute_error),
        "body_effect_recall": metric.body_effect_recall,
        "mean_body_controllability": metric.mean_body_controllability,
    }


def _set_metrics(
    *,
    predicted: tuple[int, ...],
    expected: tuple[int, ...],
) -> tuple[float, float, float]:
    """Return precision, recall, and F1 for discovered body channels."""
    predicted_set = set(predicted)
    expected_set = set(expected)
    true_positive_count = len(predicted_set & expected_set)
    precision = true_positive_count / len(predicted_set) if predicted_set else 0.0
    recall = true_positive_count / len(expected_set) if expected_set else 0.0
    f1 = 2.0 * precision * recall / (precision + recall) if precision + recall > 0.0 else 0.0
    return precision, recall, f1
