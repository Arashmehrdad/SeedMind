"""Action-effect evidence and initial self-model discovery for SeedMind."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass, field
from math import isfinite
from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.training.experience import ExperienceTransition


@dataclass(frozen=True, slots=True)
class SelfModelConfig:
    """Thresholds for online action-effect and body-channel discovery."""

    sensor_size: int
    minimum_samples: int = 4
    effect_threshold: float = 1e-6
    body_score_threshold: float = 0.6
    body_probe_actions: tuple[PrimitiveAction, ...] = (
        PrimitiveAction.TURN_LEFT,
        PrimitiveAction.TURN_RIGHT,
        PrimitiveAction.MOVE_FORWARD,
    )

    def __post_init__(self) -> None:
        """Validate finite thresholds and a non-empty probe action set."""
        if self.sensor_size <= 0:
            raise ValueError("sensor_size must be positive")

        if self.minimum_samples <= 0:
            raise ValueError("minimum_samples must be positive")

        if not isfinite(self.effect_threshold) or self.effect_threshold < 0.0:
            raise ValueError("effect_threshold must be finite and non-negative")

        if not isfinite(self.body_score_threshold) or not 0.0 <= self.body_score_threshold <= 1.0:
            raise ValueError("body_score_threshold must be between zero and one")

        if not self.body_probe_actions:
            raise ValueError("body_probe_actions must not be empty")

        if len(self.body_probe_actions) != len(set(self.body_probe_actions)):
            raise ValueError("body_probe_actions must be unique")

        if PrimitiveAction.STOP in self.body_probe_actions:
            raise ValueError("body_probe_actions must not contain stop")


@dataclass(frozen=True, slots=True)
class ActionEffectEstimate:
    """Learned causal effect statistics for one primitive action."""

    action: PrimitiveAction
    sample_count: int
    mean_controllable_change: tuple[float, ...]
    controllable_change_variance: tuple[float, ...]
    controllable_effect_frequency: tuple[float, ...]
    external_effect_frequency: tuple[float, ...]
    controllability_score: tuple[float, ...]

    def __post_init__(self) -> None:
        """Validate stable widths and normalized effect metrics."""
        if self.sample_count <= 0:
            raise ValueError("sample_count must be positive")

        widths = {
            len(self.mean_controllable_change),
            len(self.controllable_change_variance),
            len(self.controllable_effect_frequency),
            len(self.external_effect_frequency),
            len(self.controllability_score),
        }
        if len(widths) != 1:
            raise ValueError("action-effect vectors must have matching widths")

        for values in (
            self.controllable_effect_frequency,
            self.external_effect_frequency,
            self.controllability_score,
        ):
            if any(not 0.0 <= value <= 1.0 for value in values):
                raise ValueError("action-effect metrics must be between zero and one")


@dataclass(frozen=True, slots=True)
class BodySensorEstimate:
    """Evidence that one anonymous sensor channel belongs to the body."""

    sensor_index: int
    controllability_score: float
    external_effect_frequency: float
    evidence_actions: tuple[PrimitiveAction, ...]
    best_action: PrimitiveAction | None
    is_body_candidate: bool

    def __post_init__(self) -> None:
        """Validate sensor identity and normalized evidence values."""
        if self.sensor_index < 0:
            raise ValueError("sensor_index must not be negative")

        if not 0.0 <= self.controllability_score <= 1.0:
            raise ValueError("controllability_score must be between zero and one")

        if not 0.0 <= self.external_effect_frequency <= 1.0:
            raise ValueError("external_effect_frequency must be between zero and one")


@dataclass(frozen=True, slots=True)
class SelfModelSnapshot:
    """Inspectable initial registry of action effects and body candidates."""

    sensor_size: int
    experience_count: int
    action_coverage: float
    action_effects: tuple[ActionEffectEstimate, ...]
    sensor_estimates: tuple[BodySensorEstimate, ...]
    body_sensor_indices: tuple[int, ...]
    mean_body_controllability: float
    mean_external_effect_frequency: float

    def __post_init__(self) -> None:
        """Validate snapshot dimensions and normalized summary metrics."""
        if self.sensor_size <= 0:
            raise ValueError("sensor_size must be positive")

        if self.experience_count < 0:
            raise ValueError("experience_count must not be negative")

        if len(self.sensor_estimates) != self.sensor_size:
            raise ValueError("sensor_estimates must cover every sensor channel")

        for value in (
            self.action_coverage,
            self.mean_body_controllability,
            self.mean_external_effect_frequency,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("snapshot summary metrics must be between zero and one")

        expected_indices = tuple(
            estimate.sensor_index
            for estimate in self.sensor_estimates
            if estimate.is_body_candidate
        )
        if self.body_sensor_indices != expected_indices:
            raise ValueError("body_sensor_indices do not match sensor estimates")


@dataclass(slots=True)
class _ActionAccumulator:
    """Mutable Welford statistics retained internally for one action."""

    sensor_size: int
    sample_count: int = 0
    mean_change: list[float] = field(default_factory=list)
    change_m2: list[float] = field(default_factory=list)
    controllable_effect_count: list[int] = field(default_factory=list)
    external_effect_count: list[int] = field(default_factory=list)
    controllable_absolute_sum: list[float] = field(default_factory=list)
    external_absolute_sum: list[float] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Initialize all per-sensor running vectors at a fixed width."""
        if self.sensor_size <= 0:
            raise ValueError("sensor_size must be positive")

        if not self.mean_change:
            self.mean_change = [0.0] * self.sensor_size
            self.change_m2 = [0.0] * self.sensor_size
            self.controllable_effect_count = [0] * self.sensor_size
            self.external_effect_count = [0] * self.sensor_size
            self.controllable_absolute_sum = [0.0] * self.sensor_size
            self.external_absolute_sum = [0.0] * self.sensor_size

    def update(
        self,
        controllable_change: tuple[float, ...],
        external_change: tuple[float, ...],
        *,
        threshold: float,
    ) -> None:
        """Update causal effect magnitudes, frequencies, means, and variance."""
        if len(controllable_change) != self.sensor_size:
            raise ValueError("controllable change width does not match sensor_size")

        if len(external_change) != self.sensor_size:
            raise ValueError("external change width does not match sensor_size")

        self.sample_count += 1
        for index, (controllable, external) in enumerate(
            zip(controllable_change, external_change, strict=True)
        ):
            previous_mean = self.mean_change[index]
            delta = controllable - previous_mean
            updated_mean = previous_mean + delta / self.sample_count
            self.mean_change[index] = updated_mean
            self.change_m2[index] += delta * (controllable - updated_mean)

            controllable_absolute = abs(controllable)
            external_absolute = abs(external)
            self.controllable_absolute_sum[index] += controllable_absolute
            self.external_absolute_sum[index] += external_absolute

            if controllable_absolute > threshold:
                self.controllable_effect_count[index] += 1

            if external_absolute > threshold:
                self.external_effect_count[index] += 1


class SelfModelRegistry:
    """Accumulate causal evidence and infer anonymous body sensor channels."""

    def __init__(self, config: SelfModelConfig) -> None:
        """Create an empty online registry for a fixed sensor interface."""
        self.config = config
        self._experience_count = 0
        self._accumulators: dict[PrimitiveAction, _ActionAccumulator] = {}
        self._external_effect_count = [0] * config.sensor_size

    @property
    def experience_count(self) -> int:
        """Return the number of causal transitions observed."""
        return self._experience_count

    def observe(self, experience: ExperienceTransition) -> None:
        """Update the registry from one source, agent-only, and final transition."""
        if len(experience.observation.sensor_values) != self.config.sensor_size:
            raise ValueError("experience sensor width does not match self-model")

        accumulator = self._accumulators.setdefault(
            experience.action,
            _ActionAccumulator(sensor_size=self.config.sensor_size),
        )
        controllable_change = experience.controllable_sensor_change
        external_change = experience.external_sensor_change
        accumulator.update(
            controllable_change,
            external_change,
            threshold=self.config.effect_threshold,
        )
        self._experience_count += 1

        for index, external in enumerate(external_change):
            if abs(external) > self.config.effect_threshold:
                self._external_effect_count[index] += 1

    def snapshot(self) -> SelfModelSnapshot:
        """Freeze current online evidence into an inspectable self-model view."""
        action_effects = tuple(
            self._action_estimate(action, accumulator)
            for action in PrimitiveAction
            if (accumulator := self._accumulators.get(action)) is not None
        )
        action_effect_by_action = {estimate.action: estimate for estimate in action_effects}
        sensor_estimates = tuple(
            self._sensor_estimate(index, action_effect_by_action)
            for index in range(self.config.sensor_size)
        )
        body_sensor_indices = tuple(
            estimate.sensor_index for estimate in sensor_estimates if estimate.is_body_candidate
        )
        mean_body_controllability = (
            sum(sensor_estimates[index].controllability_score for index in body_sensor_indices)
            / len(body_sensor_indices)
            if body_sensor_indices
            else 0.0
        )
        mean_external_effect_frequency = (
            sum(count / self._experience_count for count in self._external_effect_count)
            / self.config.sensor_size
            if self._experience_count > 0
            else 0.0
        )
        return SelfModelSnapshot(
            sensor_size=self.config.sensor_size,
            experience_count=self._experience_count,
            action_coverage=len(action_effects) / len(PrimitiveAction),
            action_effects=action_effects,
            sensor_estimates=sensor_estimates,
            body_sensor_indices=body_sensor_indices,
            mean_body_controllability=mean_body_controllability,
            mean_external_effect_frequency=mean_external_effect_frequency,
        )

    def _action_estimate(
        self,
        action: PrimitiveAction,
        accumulator: _ActionAccumulator,
    ) -> ActionEffectEstimate:
        """Convert one mutable accumulator to normalized causal statistics."""
        count = accumulator.sample_count
        support = min(count / self.config.minimum_samples, 1.0)
        variance = tuple(value / count for value in accumulator.change_m2)
        controllable_frequency = tuple(
            value / count for value in accumulator.controllable_effect_count
        )
        external_frequency = tuple(value / count for value in accumulator.external_effect_count)
        scores = tuple(
            self._controllability_score(
                support=support,
                controllable_count=accumulator.controllable_effect_count[index],
                external_count=accumulator.external_effect_count[index],
                controllable_absolute=accumulator.controllable_absolute_sum[index],
                external_absolute=accumulator.external_absolute_sum[index],
                sample_count=count,
            )
            for index in range(self.config.sensor_size)
        )
        return ActionEffectEstimate(
            action=action,
            sample_count=count,
            mean_controllable_change=tuple(accumulator.mean_change),
            controllable_change_variance=variance,
            controllable_effect_frequency=controllable_frequency,
            external_effect_frequency=external_frequency,
            controllability_score=scores,
        )

    def _sensor_estimate(
        self,
        sensor_index: int,
        action_effects: dict[PrimitiveAction, ActionEffectEstimate],
    ) -> BodySensorEstimate:
        """Infer body membership from configured primitive body probes."""
        probe_evidence = tuple(
            (
                action,
                action_effects[action].controllability_score[sensor_index],
            )
            for action in self.config.body_probe_actions
            if action in action_effects
        )
        evidence_actions = tuple(action for action, score in probe_evidence if score > 0.0)
        best_action: PrimitiveAction | None = None
        best_score = 0.0
        for action, score in probe_evidence:
            if score > best_score:
                best_action = action
                best_score = score

        external_frequency = (
            self._external_effect_count[sensor_index] / self._experience_count
            if self._experience_count > 0
            else 0.0
        )
        return BodySensorEstimate(
            sensor_index=sensor_index,
            controllability_score=best_score,
            external_effect_frequency=external_frequency,
            evidence_actions=evidence_actions,
            best_action=best_action,
            is_body_candidate=best_score >= self.config.body_score_threshold,
        )

    @staticmethod
    def _controllability_score(
        *,
        support: float,
        controllable_count: int,
        external_count: int,
        controllable_absolute: float,
        external_absolute: float,
        sample_count: int,
    ) -> float:
        """Score repeatable causal effects with support and external purity."""
        if controllable_count == 0 or sample_count <= 0:
            return 0.0

        effect_frequency = controllable_count / sample_count
        occurrence_total = controllable_count + external_count
        occurrence_purity = controllable_count / occurrence_total
        magnitude_total = controllable_absolute + external_absolute
        magnitude_purity = controllable_absolute / magnitude_total if magnitude_total > 0.0 else 0.0
        return support * effect_frequency * (occurrence_purity + magnitude_purity) / 2.0


def export_self_model_json(snapshot: SelfModelSnapshot, path: Path) -> None:
    """Write an ASCII JSON dashboard for one self-model snapshot."""
    payload = {
        "sensor_size": snapshot.sensor_size,
        "experience_count": snapshot.experience_count,
        "action_coverage": snapshot.action_coverage,
        "body_sensor_indices": list(snapshot.body_sensor_indices),
        "mean_body_controllability": snapshot.mean_body_controllability,
        "mean_external_effect_frequency": snapshot.mean_external_effect_frequency,
        "actions": [
            {
                "action": estimate.action.value,
                "sample_count": estimate.sample_count,
                "mean_controllable_change": list(estimate.mean_controllable_change),
                "controllable_change_variance": list(estimate.controllable_change_variance),
                "controllable_effect_frequency": list(estimate.controllable_effect_frequency),
                "external_effect_frequency": list(estimate.external_effect_frequency),
                "controllability_score": list(estimate.controllability_score),
            }
            for estimate in snapshot.action_effects
        ],
        "sensors": [
            {
                "sensor_index": estimate.sensor_index,
                "controllability_score": estimate.controllability_score,
                "external_effect_frequency": estimate.external_effect_frequency,
                "evidence_actions": [action.value for action in estimate.evidence_actions],
                "best_action": (
                    estimate.best_action.value if estimate.best_action is not None else None
                ),
                "is_body_candidate": estimate.is_body_candidate,
            }
            for estimate in snapshot.sensor_estimates
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def export_action_effects_csv(snapshot: SelfModelSnapshot, path: Path) -> None:
    """Write one row per observed action and anonymous sensor channel."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    with temporary_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "action",
                "sample_count",
                "sensor_index",
                "mean_controllable_change",
                "controllable_change_variance",
                "controllable_effect_frequency",
                "external_effect_frequency",
                "controllability_score",
            )
        )
        for estimate in snapshot.action_effects:
            for sensor_index in range(snapshot.sensor_size):
                writer.writerow(
                    (
                        estimate.action.value,
                        estimate.sample_count,
                        sensor_index,
                        estimate.mean_controllable_change[sensor_index],
                        estimate.controllable_change_variance[sensor_index],
                        estimate.controllable_effect_frequency[sensor_index],
                        estimate.external_effect_frequency[sensor_index],
                        estimate.controllability_score[sensor_index],
                    )
                )
    temporary_path.replace(path)
