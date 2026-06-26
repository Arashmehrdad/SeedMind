"""Tests for learning-progress curiosity and bounded experiment selection."""

from pathlib import Path

import pytest

from seedmind.contracts import PrimitiveAction
from seedmind.curiosity import (
    CuriosityCandidate,
    CuriosityConfig,
    CuriositySubsystem,
    export_curiosity_timeline_csv,
    export_curiosity_timeline_json,
)


def create_config(**overrides: object) -> CuriosityConfig:
    """Return a compact deterministic curiosity configuration."""
    values: dict[str, object] = {
        "play_budget": 8,
        "progress_window": 2,
        "novelty_decay": 4.0,
        "error_scale": 1.0,
        "repetition_horizon": 2,
        "stagnation_horizon": 3,
        "experiment_actions": (
            PrimitiveAction.TURN_LEFT,
            PrimitiveAction.TURN_RIGHT,
            PrimitiveAction.WAIT,
        ),
    }
    values.update(overrides)
    return CuriosityConfig(**values)  # type: ignore[arg-type]


def candidate_for(
    subsystem: CuriositySubsystem,
    action: PrimitiveAction,
) -> CuriosityCandidate:
    """Return one candidate from the complete configured action set."""
    candidates = subsystem.generate_candidates(subsystem.config.experiment_actions)
    return next(candidate for candidate in candidates if candidate.action is action)


def test_learning_progress_is_positive_only_when_recent_error_improves() -> None:
    subsystem = CuriositySubsystem(create_config())
    for error in (1.0, 0.8, 0.5, 0.3):
        subsystem.observe(PrimitiveAction.TURN_LEFT, error)
    for error in (0.8, 0.8, 0.8, 0.8):
        subsystem.observe(PrimitiveAction.WAIT, error)

    improving = candidate_for(subsystem, PrimitiveAction.TURN_LEFT)
    stalled = candidate_for(subsystem, PrimitiveAction.WAIT)

    assert improving.learning_progress == pytest.approx(0.5555555556)
    assert stalled.learning_progress == 0.0
    assert improving.information_gain > stalled.information_gain


def test_novelty_decays_with_repeated_observations() -> None:
    subsystem = CuriositySubsystem(create_config())
    unseen = candidate_for(subsystem, PrimitiveAction.TURN_LEFT)

    subsystem.observe(PrimitiveAction.TURN_LEFT, 0.5)
    observed = candidate_for(subsystem, PrimitiveAction.TURN_LEFT)

    assert unseen.novelty == pytest.approx(1.0)
    assert observed.novelty < unseen.novelty
    assert observed.sample_count == 1


def test_repetition_penalty_rotates_equal_unseen_candidates() -> None:
    subsystem = CuriositySubsystem(create_config(play_budget=3))
    actions = subsystem.config.experiment_actions

    first = subsystem.select(actions)
    second = subsystem.select(actions)

    assert first.selected_action is PrimitiveAction.TURN_LEFT
    assert second.selected_action is PrimitiveAction.TURN_RIGHT
    repeated = next(
        candidate
        for candidate in second.candidates
        if candidate.action is PrimitiveAction.TURN_LEFT
    )
    assert repeated.repetition_penalty == pytest.approx(0.5)


def test_stagnation_penalty_discounts_persistent_unlearnable_error() -> None:
    subsystem = CuriositySubsystem(create_config())
    for _ in range(8):
        subsystem.observe(PrimitiveAction.WAIT, 1.0)

    noisy = candidate_for(subsystem, PrimitiveAction.WAIT)
    novel = candidate_for(subsystem, PrimitiveAction.TURN_LEFT)

    assert noisy.learning_progress == 0.0
    assert noisy.stagnation_penalty == pytest.approx(1.0)
    assert noisy.score < novel.score


def test_recent_prediction_error_is_normalized_as_uncertainty() -> None:
    subsystem = CuriositySubsystem(create_config(error_scale=2.0))
    subsystem.observe(PrimitiveAction.TURN_LEFT, 0.5)
    subsystem.observe(PrimitiveAction.TURN_LEFT, 1.5)

    candidate = candidate_for(subsystem, PrimitiveAction.TURN_LEFT)

    assert candidate.uncertainty == pytest.approx(0.5)


def test_selection_consumes_bounded_play_budget() -> None:
    subsystem = CuriositySubsystem(create_config(play_budget=2))
    actions = subsystem.config.experiment_actions

    first = subsystem.select(actions)
    second = subsystem.select(actions)

    assert first.remaining_budget == 1
    assert second.remaining_budget == 0
    assert subsystem.selection_count == 2
    assert subsystem.budget_exhausted
    with pytest.raises(RuntimeError, match="exhausted"):
        subsystem.select(actions)


def test_unavailable_or_unconfigured_actions_are_not_candidates() -> None:
    subsystem = CuriositySubsystem(create_config())

    candidates = subsystem.generate_candidates(
        (PrimitiveAction.TURN_RIGHT, PrimitiveAction.STOP)
    )

    assert tuple(candidate.action for candidate in candidates) == (
        PrimitiveAction.TURN_RIGHT,
    )
    with pytest.raises(ValueError, match="no configured"):
        subsystem.generate_candidates((PrimitiveAction.STOP,))
    with pytest.raises(ValueError, match="not a curiosity experiment"):
        subsystem.observe(PrimitiveAction.INSPECT, 0.1)


def test_curiosity_timeline_exports_are_ascii_and_inspectable(
    tmp_path: Path,
) -> None:
    subsystem = CuriositySubsystem(create_config(play_budget=2))
    actions = subsystem.config.experiment_actions
    first = subsystem.select(actions)
    subsystem.observe(first.selected_action, 1.0)
    second = subsystem.select(actions)
    selections = (first, second)
    json_path = tmp_path / "timeline.json"
    csv_path = tmp_path / "timeline.csv"

    export_curiosity_timeline_json(selections, json_path)
    export_curiosity_timeline_csv(selections, csv_path)

    json_text = json_path.read_text(encoding="ascii")
    csv_text = csv_path.read_text(encoding="ascii")
    assert '"selection_count": 2' in json_text
    assert '"selected_action": "turn_left"' in json_text
    assert csv_text.startswith("step_index,selected_action,remaining_budget")
    assert "turn_left" in csv_text


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"play_budget": 0}, "play_budget"),
        ({"progress_window": 0}, "progress_window"),
        ({"novelty_decay": 0.0}, "novelty_decay"),
        ({"error_scale": 0.0}, "error_scale"),
        ({"repetition_horizon": 0}, "repetition_horizon"),
        ({"stagnation_horizon": 0}, "stagnation_horizon"),
        ({"learning_progress_weight": -1.0}, "learning_progress_weight"),
        ({"novelty_weight": -1.0}, "novelty_weight"),
        ({"uncertainty_weight": -1.0}, "uncertainty_weight"),
        ({"repetition_penalty_weight": -1.0}, "repetition_penalty_weight"),
        ({"stagnation_penalty_weight": -1.0}, "stagnation_penalty_weight"),
        (
            {
                "learning_progress_weight": 0.0,
                "novelty_weight": 0.0,
                "uncertainty_weight": 0.0,
            },
            "information-gain",
        ),
        ({"experiment_actions": ()}, "experiment_actions"),
        (
            {
                "experiment_actions": (
                    PrimitiveAction.TURN_LEFT,
                    PrimitiveAction.TURN_LEFT,
                )
            },
            "unique",
        ),
        (
            {"experiment_actions": (PrimitiveAction.STOP,)},
            "stop",
        ),
    ],
)
def test_curiosity_config_rejects_invalid_values(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        CuriosityConfig(**kwargs)  # type: ignore[arg-type]


def test_observe_rejects_invalid_prediction_error() -> None:
    subsystem = CuriositySubsystem(create_config())

    with pytest.raises(ValueError, match="prediction_error"):
        subsystem.observe(PrimitiveAction.TURN_LEFT, -0.1)
    with pytest.raises(ValueError, match="prediction_error"):
        subsystem.observe(PrimitiveAction.TURN_LEFT, float("nan"))
