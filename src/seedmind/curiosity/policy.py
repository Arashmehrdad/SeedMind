"""Bounded curiosity scoring and primitive experiment selection for SeedMind."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from math import exp, isfinite
from pathlib import Path
from statistics import fmean

from seedmind.contracts import PrimitiveAction

_SAFE_PRIMITIVE_ACTIONS = tuple(
    action for action in PrimitiveAction if action is not PrimitiveAction.STOP
)


@dataclass(frozen=True, slots=True)
class CuriosityConfig:
    """Weights, evidence windows, and resource bounds for curiosity."""

    play_budget: int = 24
    progress_window: int = 3
    novelty_decay: float = 4.0
    error_scale: float = 1.0
    repetition_horizon: int = 3
    stagnation_horizon: int = 6
    learning_progress_weight: float = 1.0
    novelty_weight: float = 0.6
    uncertainty_weight: float = 0.35
    repetition_penalty_weight: float = 0.5
    stagnation_penalty_weight: float = 0.8
    experiment_actions: tuple[PrimitiveAction, ...] = _SAFE_PRIMITIVE_ACTIONS

    def __post_init__(self) -> None:
        """Validate finite weights, positive horizons, and safe actions."""
        for integer_name, integer_value in (
            ("play_budget", self.play_budget),
            ("progress_window", self.progress_window),
            ("repetition_horizon", self.repetition_horizon),
            ("stagnation_horizon", self.stagnation_horizon),
        ):
            if integer_value <= 0:
                raise ValueError(f"{integer_name} must be positive")

        for positive_float_name, positive_float_value in (
            ("novelty_decay", self.novelty_decay),
            ("error_scale", self.error_scale),
        ):
            if not isfinite(positive_float_value) or positive_float_value <= 0.0:
                raise ValueError(f"{positive_float_name} must be finite and positive")

        weights = (
            ("learning_progress_weight", self.learning_progress_weight),
            ("novelty_weight", self.novelty_weight),
            ("uncertainty_weight", self.uncertainty_weight),
            ("repetition_penalty_weight", self.repetition_penalty_weight),
            ("stagnation_penalty_weight", self.stagnation_penalty_weight),
        )
        for weight_name, weight_value in weights:
            if not isfinite(weight_value) or weight_value < 0.0:
                raise ValueError(f"{weight_name} must be finite and non-negative")

        if self.learning_progress_weight + self.novelty_weight + self.uncertainty_weight <= 0.0:
            raise ValueError("at least one information-gain weight must be positive")

        if not self.experiment_actions:
            raise ValueError("experiment_actions must not be empty")

        if len(self.experiment_actions) != len(set(self.experiment_actions)):
            raise ValueError("experiment_actions must be unique")

        if PrimitiveAction.STOP in self.experiment_actions:
            raise ValueError("experiment_actions must not contain stop")


@dataclass(frozen=True, slots=True)
class CuriosityCandidate:
    """Inspectable information-gain score for one primitive experiment."""

    action: PrimitiveAction
    sample_count: int
    learning_progress: float
    novelty: float
    uncertainty: float
    information_gain: float
    repetition_penalty: float
    stagnation_penalty: float
    score: float

    def __post_init__(self) -> None:
        """Validate counts, normalized components, and finite scores."""
        if self.sample_count < 0:
            raise ValueError("sample_count must not be negative")

        for value in (
            self.learning_progress,
            self.novelty,
            self.uncertainty,
            self.repetition_penalty,
            self.stagnation_penalty,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("curiosity components must be between zero and one")

        if not isfinite(self.information_gain) or self.information_gain < 0.0:
            raise ValueError("information_gain must be finite and non-negative")

        if not isfinite(self.score):
            raise ValueError("score must be finite")


@dataclass(frozen=True, slots=True)
class CuriositySelection:
    """One bounded experiment choice and all candidate evidence behind it."""

    step_index: int
    selected_action: PrimitiveAction
    remaining_budget: int
    candidates: tuple[CuriosityCandidate, ...]

    def __post_init__(self) -> None:
        """Validate timeline order, budget, and selected candidate presence."""
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")

        if self.remaining_budget < 0:
            raise ValueError("remaining_budget must not be negative")

        if not self.candidates:
            raise ValueError("candidates must not be empty")

        if self.selected_action not in {candidate.action for candidate in self.candidates}:
            raise ValueError("selected_action must appear in candidates")

    @property
    def selected_candidate(self) -> CuriosityCandidate:
        """Return the score record associated with the chosen action."""
        return next(
            candidate for candidate in self.candidates if candidate.action is self.selected_action
        )


class CuriositySubsystem:
    """Track learning progress and select bounded primitive experiments."""

    def __init__(self, config: CuriosityConfig | None = None) -> None:
        """Create empty action histories and a fresh play budget."""
        self.config = CuriosityConfig() if config is None else config
        self._errors: dict[PrimitiveAction, list[float]] = {
            action: [] for action in self.config.experiment_actions
        }
        self._remaining_budget = self.config.play_budget
        self._selection_count = 0
        self._last_selected_action: PrimitiveAction | None = None
        self._selection_streak = 0

    @property
    def remaining_budget(self) -> int:
        """Return the number of experiment selections still allowed."""
        return self._remaining_budget

    @property
    def selection_count(self) -> int:
        """Return the number of experiments selected so far."""
        return self._selection_count

    @property
    def budget_exhausted(self) -> bool:
        """Return whether no further play selections are permitted."""
        return self._remaining_budget == 0

    def observed_errors(self, action: PrimitiveAction) -> tuple[float, ...]:
        """Return immutable prediction-error history for one experiment."""
        self._require_experiment_action(action)
        return tuple(self._errors[action])

    def observe(self, action: PrimitiveAction, prediction_error: float) -> None:
        """Record one non-negative prediction error after an experiment."""
        self._require_experiment_action(action)
        if not isfinite(prediction_error) or prediction_error < 0.0:
            raise ValueError("prediction_error must be finite and non-negative")
        self._errors[action].append(prediction_error)

    def generate_candidates(
        self,
        available_actions: tuple[PrimitiveAction, ...],
    ) -> tuple[CuriosityCandidate, ...]:
        """Score safe configured actions currently exposed by the body adapter."""
        if not available_actions:
            raise ValueError("available_actions must not be empty")

        candidates = tuple(
            self._candidate(action)
            for action in self.config.experiment_actions
            if action in available_actions
        )
        if not candidates:
            raise ValueError("no configured curiosity experiments are available")
        return candidates

    def select(
        self,
        available_actions: tuple[PrimitiveAction, ...],
    ) -> CuriositySelection:
        """Choose the highest-scoring experiment and consume one play unit."""
        if self.budget_exhausted:
            raise RuntimeError("curiosity play budget is exhausted")

        candidates = self.generate_candidates(available_actions)
        action_rank = {action: index for index, action in enumerate(self.config.experiment_actions)}
        selected = max(
            candidates,
            key=lambda candidate: (
                candidate.score,
                candidate.information_gain,
                -action_rank[candidate.action],
            ),
        )
        step_index = self._selection_count
        self._selection_count += 1
        self._remaining_budget -= 1

        if selected.action is self._last_selected_action:
            self._selection_streak += 1
        else:
            self._last_selected_action = selected.action
            self._selection_streak = 1

        return CuriositySelection(
            step_index=step_index,
            selected_action=selected.action,
            remaining_budget=self._remaining_budget,
            candidates=candidates,
        )

    def _candidate(self, action: PrimitiveAction) -> CuriosityCandidate:
        """Calculate one transparent learning-value score."""
        errors = self._errors[action]
        sample_count = len(errors)
        learning_progress = self._learning_progress(errors)
        novelty = exp(-sample_count / self.config.novelty_decay)
        uncertainty = self._uncertainty(errors)
        repetition_penalty = (
            min(self._selection_streak / self.config.repetition_horizon, 1.0)
            if action is self._last_selected_action
            else 0.0
        )
        stagnation_penalty = self._stagnation_penalty(
            sample_count=sample_count,
            learning_progress=learning_progress,
            uncertainty=uncertainty,
        )
        information_gain = (
            self.config.learning_progress_weight * learning_progress
            + self.config.novelty_weight * novelty
            + self.config.uncertainty_weight * uncertainty
        )
        score = (
            information_gain
            - self.config.repetition_penalty_weight * repetition_penalty
            - self.config.stagnation_penalty_weight * stagnation_penalty
        )
        return CuriosityCandidate(
            action=action,
            sample_count=sample_count,
            learning_progress=learning_progress,
            novelty=novelty,
            uncertainty=uncertainty,
            information_gain=information_gain,
            repetition_penalty=repetition_penalty,
            stagnation_penalty=stagnation_penalty,
            score=score,
        )

    def _learning_progress(self, errors: list[float]) -> float:
        """Compare older and recent error windows, retaining only improvement."""
        window = self.config.progress_window
        if len(errors) < window * 2:
            return 0.0

        older_error = fmean(errors[-(window * 2) : -window])
        recent_error = fmean(errors[-window:])
        if older_error <= 0.0 or recent_error >= older_error:
            return 0.0
        return min((older_error - recent_error) / older_error, 1.0)

    def _uncertainty(self, errors: list[float]) -> float:
        """Use recent normalized prediction error as unresolved uncertainty."""
        if not errors:
            return 1.0
        recent = errors[-self.config.progress_window :]
        return min(fmean(recent) / self.config.error_scale, 1.0)

    def _stagnation_penalty(
        self,
        *,
        sample_count: int,
        learning_progress: float,
        uncertainty: float,
    ) -> float:
        """Discount repeatedly uncertain experiments that show no improvement."""
        evidence_floor = self.config.progress_window * 2
        if sample_count < evidence_floor or learning_progress > 0.0:
            return 0.0
        stalled_samples = sample_count - evidence_floor + 1
        maturity = min(stalled_samples / self.config.stagnation_horizon, 1.0)
        return maturity * uncertainty

    def _require_experiment_action(self, action: PrimitiveAction) -> None:
        """Reject actions outside the configured curiosity boundary."""
        if action not in self._errors:
            raise ValueError(f"action {action.value!r} is not a curiosity experiment")


def export_curiosity_timeline_json(
    selections: tuple[CuriositySelection, ...],
    path: Path,
) -> None:
    """Write an ASCII experiment timeline with full score decomposition."""
    payload = {
        "selection_count": len(selections),
        "timeline": [
            {
                "step_index": selection.step_index,
                "selected_action": selection.selected_action.value,
                "remaining_budget": selection.remaining_budget,
                "candidates": [_candidate_payload(candidate) for candidate in selection.candidates],
            }
            for selection in selections
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def export_curiosity_timeline_csv(
    selections: tuple[CuriositySelection, ...],
    path: Path,
) -> None:
    """Write one ASCII CSV row per candidate and selection step."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    with temporary_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "selected_action",
                "remaining_budget",
                "candidate_action",
                "was_selected",
                "sample_count",
                "learning_progress",
                "novelty",
                "uncertainty",
                "information_gain",
                "repetition_penalty",
                "stagnation_penalty",
                "score",
            )
        )
        for selection in selections:
            for candidate in selection.candidates:
                writer.writerow(
                    (
                        selection.step_index,
                        selection.selected_action.value,
                        selection.remaining_budget,
                        candidate.action.value,
                        candidate.action is selection.selected_action,
                        candidate.sample_count,
                        candidate.learning_progress,
                        candidate.novelty,
                        candidate.uncertainty,
                        candidate.information_gain,
                        candidate.repetition_penalty,
                        candidate.stagnation_penalty,
                        candidate.score,
                    )
                )
    temporary_path.replace(path)


def _candidate_payload(candidate: CuriosityCandidate) -> dict[str, object]:
    """Convert one candidate to JSON-safe primitive values."""
    return {
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
