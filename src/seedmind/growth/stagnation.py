"""Learning-progress windows and plateau classification for Week 10."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class PlateauClassification(StrEnum):
    """Inspectable diagnosis for one learning-progress window."""

    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    IMPROVING = "improving"
    TEMPORARY_FAILURE = "temporary_failure"
    SUSTAINED_BLOCKAGE = "sustained_blockage"


@dataclass(frozen=True, slots=True)
class LearningProgressThresholds:
    """Predeclared thresholds for developmental blockage detection."""

    window_size: int = 4
    minimum_windows_for_blockage: int = 3
    minimum_attempts_for_blockage: int = 12
    improvement_threshold: float = 0.10
    progress_resume_threshold: float = 0.20
    sustained_success_rate_ceiling: float = 0.25
    sustained_progress_ceiling: float = 0.30

    def __post_init__(self) -> None:
        if self.window_size <= 1:
            raise ValueError("window_size must require repeated attempts")
        if self.minimum_windows_for_blockage <= 1:
            raise ValueError("minimum_windows_for_blockage must require repeated windows")
        if self.minimum_attempts_for_blockage < self.window_size:
            raise ValueError("minimum_attempts_for_blockage must cover at least one window")
        for name, value in (
            ("improvement_threshold", self.improvement_threshold),
            ("progress_resume_threshold", self.progress_resume_threshold),
            ("sustained_success_rate_ceiling", self.sustained_success_rate_ceiling),
            ("sustained_progress_ceiling", self.sustained_progress_ceiling),
        ):
            _validate_unit_interval(name, value)

    def to_json(self) -> dict[str, object]:
        return {
            "improvement_threshold": self.improvement_threshold,
            "minimum_attempts_for_blockage": self.minimum_attempts_for_blockage,
            "minimum_windows_for_blockage": self.minimum_windows_for_blockage,
            "progress_resume_threshold": self.progress_resume_threshold,
            "sustained_progress_ceiling": self.sustained_progress_ceiling,
            "sustained_success_rate_ceiling": self.sustained_success_rate_ceiling,
            "window_size": self.window_size,
        }


@dataclass(frozen=True, slots=True)
class LearningAttempt:
    """One bounded task attempt used to build a progress window."""

    attempt_index: int
    scenario_family: str
    strategy: str
    success: bool
    task_progress: float
    steps_used: int
    prediction_error: float
    invalid_or_ineffective_actions: int
    help_requested: bool = False
    replay_involved: bool = False
    demonstration_involved: bool = False

    def __post_init__(self) -> None:
        if self.attempt_index < 0:
            raise ValueError("attempt_index must not be negative")
        if not self.scenario_family.strip() or not self.scenario_family.isascii():
            raise ValueError("scenario_family must be non-empty ASCII")
        if not self.strategy.strip() or not self.strategy.isascii():
            raise ValueError("strategy must be non-empty ASCII")
        if self.steps_used <= 0:
            raise ValueError("steps_used must be positive")
        if self.invalid_or_ineffective_actions < 0:
            raise ValueError("invalid_or_ineffective_actions must not be negative")
        _validate_unit_interval("task_progress", self.task_progress)
        _validate_unit_interval("prediction_error", self.prediction_error)


@dataclass(frozen=True, slots=True)
class LearningProgressWindow:
    """Deterministic aggregate over a bounded sequence of attempts."""

    window_id: str
    scenario_family: str
    attempt_start: int
    attempt_end: int
    total_attempts: int
    successes: int
    success_rate: float
    mean_task_progress: float
    mean_steps: float
    mean_prediction_error: float
    invalid_or_ineffective_action_count: int
    help_requests: int
    strategy: str
    replay_involved: bool
    demonstration_involved: bool
    improvement: float | None
    classification: PlateauClassification

    def __post_init__(self) -> None:
        if self.attempt_end < self.attempt_start:
            raise ValueError("attempt range is invalid")
        if self.total_attempts <= 0:
            raise ValueError("total_attempts must be positive")
        if not 0 <= self.successes <= self.total_attempts:
            raise ValueError("success count must fit attempts")
        for name, value in (
            ("success_rate", self.success_rate),
            ("mean_task_progress", self.mean_task_progress),
            ("mean_prediction_error", self.mean_prediction_error),
        ):
            _validate_unit_interval(name, value)
        if not isfinite(self.mean_steps) or self.mean_steps <= 0:
            raise ValueError("mean_steps must be finite and positive")
        if self.invalid_or_ineffective_action_count < 0 or self.help_requests < 0:
            raise ValueError("window counts must not be negative")

    def to_json(self) -> dict[str, object]:
        return {
            "attempt_end": self.attempt_end,
            "attempt_start": self.attempt_start,
            "classification": self.classification.value,
            "demonstration_involved": self.demonstration_involved,
            "help_requests": self.help_requests,
            "improvement": self.improvement,
            "invalid_or_ineffective_action_count": self.invalid_or_ineffective_action_count,
            "mean_prediction_error": self.mean_prediction_error,
            "mean_steps": self.mean_steps,
            "mean_task_progress": self.mean_task_progress,
            "replay_involved": self.replay_involved,
            "scenario_family": self.scenario_family,
            "strategy": self.strategy,
            "success_rate": self.success_rate,
            "successes": self.successes,
            "total_attempts": self.total_attempts,
            "window_id": self.window_id,
        }


def build_learning_progress_windows(
    attempts: tuple[LearningAttempt, ...],
    thresholds: LearningProgressThresholds,
    *,
    scenario_family: str,
    strategy_variants_exhausted: bool,
    replay_attempted: bool,
    help_or_demonstration_considered: bool,
    ambiguity_resolved: bool = True,
    safety_or_permission_clear: bool = True,
    resource_limit: bool = False,
) -> tuple[LearningProgressWindow, ...]:
    """Aggregate attempts and classify windows with predeclared thresholds."""
    if not attempts:
        raise ValueError("at least one attempt is required")
    if any(attempt.scenario_family != scenario_family for attempt in attempts):
        raise ValueError("all attempts must belong to the requested scenario family")

    windows: list[LearningProgressWindow] = []
    previous_progress: float | None = None
    chunks = [
        attempts[index : index + thresholds.window_size]
        for index in range(0, len(attempts), thresholds.window_size)
    ]

    for window_index, chunk in enumerate(chunks):
        progress = _mean(tuple(attempt.task_progress for attempt in chunk))
        improvement = None if previous_progress is None else progress - previous_progress
        classification = _classify_window(
            chunk,
            thresholds,
            progress=progress,
            improvement=improvement,
            completed_window_count=window_index + 1,
            total_observed_attempts=sum(len(candidate) for candidate in chunks[: window_index + 1]),
            strategy_variants_exhausted=strategy_variants_exhausted,
            replay_attempted=replay_attempted,
            help_or_demonstration_considered=help_or_demonstration_considered,
            ambiguity_resolved=ambiguity_resolved,
            safety_or_permission_clear=safety_or_permission_clear,
            resource_limit=resource_limit,
            previous_windows=tuple(windows),
        )
        windows.append(
            LearningProgressWindow(
                window_id=f"{scenario_family}-window-{window_index + 1:02d}",
                scenario_family=scenario_family,
                attempt_start=chunk[0].attempt_index,
                attempt_end=chunk[-1].attempt_index,
                total_attempts=len(chunk),
                successes=sum(1 for attempt in chunk if attempt.success),
                success_rate=sum(1 for attempt in chunk if attempt.success) / len(chunk),
                mean_task_progress=progress,
                mean_steps=_mean(tuple(float(attempt.steps_used) for attempt in chunk)),
                mean_prediction_error=_mean(tuple(attempt.prediction_error for attempt in chunk)),
                invalid_or_ineffective_action_count=sum(
                    attempt.invalid_or_ineffective_actions for attempt in chunk
                ),
                help_requests=sum(1 for attempt in chunk if attempt.help_requested),
                strategy=chunk[-1].strategy,
                replay_involved=any(attempt.replay_involved for attempt in chunk),
                demonstration_involved=any(attempt.demonstration_involved for attempt in chunk),
                improvement=improvement,
                classification=classification,
            )
        )
        previous_progress = progress
    return tuple(windows)


def final_classification(windows: tuple[LearningProgressWindow, ...]) -> PlateauClassification:
    """Return the last window's classification."""
    if not windows:
        raise ValueError("at least one window is required")
    return windows[-1].classification


def _classify_window(
    chunk: tuple[LearningAttempt, ...],
    thresholds: LearningProgressThresholds,
    *,
    progress: float,
    improvement: float | None,
    completed_window_count: int,
    total_observed_attempts: int,
    strategy_variants_exhausted: bool,
    replay_attempted: bool,
    help_or_demonstration_considered: bool,
    ambiguity_resolved: bool,
    safety_or_permission_clear: bool,
    resource_limit: bool,
    previous_windows: tuple[LearningProgressWindow, ...],
) -> PlateauClassification:
    if (
        total_observed_attempts < thresholds.minimum_attempts_for_blockage
        or completed_window_count < thresholds.minimum_windows_for_blockage
    ):
        if improvement is not None and improvement >= thresholds.improvement_threshold:
            return PlateauClassification.IMPROVING
        return PlateauClassification.INSUFFICIENT_EVIDENCE

    if improvement is not None and improvement >= thresholds.improvement_threshold:
        return PlateauClassification.IMPROVING

    if (
        any(attempt.success for attempt in chunk)
        or progress >= thresholds.progress_resume_threshold
    ):
        return PlateauClassification.TEMPORARY_FAILURE

    prerequisites_met = (
        strategy_variants_exhausted
        and replay_attempted
        and help_or_demonstration_considered
        and ambiguity_resolved
        and safety_or_permission_clear
        and not resource_limit
    )
    if not prerequisites_met:
        return PlateauClassification.TEMPORARY_FAILURE

    plateau_candidates = (*previous_windows[-(thresholds.minimum_windows_for_blockage - 1) :],)
    low_success = all(
        window.success_rate <= thresholds.sustained_success_rate_ceiling
        for window in plateau_candidates
    ) and (sum(1 for attempt in chunk if attempt.success) / len(chunk)) <= (
        thresholds.sustained_success_rate_ceiling
    )
    low_progress = (
        all(
            window.mean_task_progress <= thresholds.sustained_progress_ceiling
            for window in plateau_candidates
        )
        and progress <= thresholds.sustained_progress_ceiling
    )
    low_improvement = all(
        window.improvement is None or window.improvement < thresholds.improvement_threshold
        for window in plateau_candidates
    ) and (improvement is None or improvement < thresholds.improvement_threshold)
    if low_success and low_progress and low_improvement:
        return PlateauClassification.SUSTAINED_BLOCKAGE
    return PlateauClassification.TEMPORARY_FAILURE


def _mean(values: tuple[float, ...]) -> float:
    if not values:
        raise ValueError("cannot average an empty sequence")
    return sum(values) / len(values)


def _validate_unit_interval(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
