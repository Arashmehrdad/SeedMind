"""Tests for curiosity versus random causal-discovery comparison."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from pathlib import Path

import pytest

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.curiosity import (
    CuriosityComparisonConfig,
    CuriosityConfig,
    CuriosityRandomComparisonExperiment,
    export_curiosity_comparison_csv,
    export_curiosity_comparison_json,
)
from seedmind.environment import AgentState, NurseryScenario, NurseryState
from seedmind.training import ExperienceTransition, OnlineTrainingMetrics


@dataclass(frozen=True, slots=True)
class TinyComparisonScenarioFactory:
    """Create one open deterministic body-discovery benchmark world."""

    step_budget: int = 24

    def create(self, seed: int) -> NurseryScenario:
        """Return a stable east-facing body in an empty five-cell room."""
        state = NurseryState(
            width=5,
            height=5,
            agent=AgentState(
                position=GridPosition(2, 2),
                orientation=Direction.EAST,
            ),
            entities=(),
        )
        return NurseryScenario(
            scenario_id=f"tiny-comparison-seed-{seed}",
            seed=seed,
            initial_state=state,
            step_budget=self.step_budget,
        )


class ControlledPredictiveTrainer:
    """Return learnable body errors and persistent no-control noise."""

    def __init__(self, model_seed: int) -> None:
        self.model_seed = model_seed
        self._counts: Counter[PrimitiveAction] = Counter()

    def reset_episode(self) -> None:
        """Start one comparison episode with empty learning history."""
        self._counts.clear()

    def train_transition(
        self,
        experience: ExperienceTransition,
    ) -> OnlineTrainingMetrics:
        """Produce deterministic pre-update error for one selected action."""
        self._counts[experience.action] += 1
        sample_count = self._counts[experience.action]
        if experience.action is PrimitiveAction.WAIT:
            prediction_error = 1.0
        else:
            learning_curve = (1.0, 0.72, 0.42, 0.22, 0.12, 0.08)
            prediction_error = learning_curve[min(sample_count - 1, len(learning_curve) - 1)]
        return OnlineTrainingMetrics(
            episode_id=experience.observation.episode_id,
            source_step_id=experience.observation.step_id,
            total_loss=prediction_error,
            sensor_prediction_loss=prediction_error,
            controllable_change_loss=prediction_error,
            confidence_calibration_loss=0.0,
            mean_absolute_error=prediction_error,
            external_change_mean_absolute=0.0,
            mean_confidence=max(0.0, 1.0 - prediction_error),
            gradient_norm=prediction_error,
            terminated=experience.terminated,
        )


def create_trainer(
    model_seed: int,
    scenario: NurseryScenario,
) -> ControlledPredictiveTrainer:
    """Create one controlled learner while accepting the matched scenario."""
    assert scenario.step_budget > 0
    return ControlledPredictiveTrainer(model_seed)


def create_config(**overrides: object) -> CuriosityComparisonConfig:
    """Return a compact deterministic matched comparison configuration."""
    values: dict[str, object] = {
        "scenario_seed": 5,
        "model_seed": 17,
        "random_seed": 31,
        "trial_count": 12,
        "curiosity": CuriosityConfig(
            play_budget=12,
            progress_window=2,
            novelty_decay=3.0,
            error_scale=10.0,
            repetition_horizon=2,
            stagnation_horizon=2,
            learning_progress_weight=1.0,
            novelty_weight=1.0,
            uncertainty_weight=0.1,
            repetition_penalty_weight=0.8,
            stagnation_penalty_weight=1.0,
            experiment_actions=(
                PrimitiveAction.TURN_LEFT,
                PrimitiveAction.TURN_RIGHT,
                PrimitiveAction.MOVE_FORWARD,
                PrimitiveAction.WAIT,
            ),
        ),
        "minimum_effect_samples": 3,
        "minimum_effect_frequency": 0.25,
        "body_score_threshold": 0.15,
        "maximum_noise_share": 0.34,
        "maximum_noise_streak": 2,
    }
    values.update(overrides)
    return CuriosityComparisonConfig(**values)  # type: ignore[arg-type]


def test_curiosity_discovers_controllable_effects_faster_than_random() -> None:
    result = CuriosityRandomComparisonExperiment(
        TinyComparisonScenarioFactory(),
        create_trainer,
        create_config(),
    ).run()

    assert result.pass_gate, (
        result.curiosity_mean_discovery_auc,
        result.random_mean_discovery_auc,
        result.curiosity_mean_final_effect_recall,
        result.random_mean_final_effect_recall,
        result.curiosity_mean_full_discovery_step,
        result.random_mean_full_discovery_step,
        result.curiosity_mean_final_body_f1,
        result.random_mean_final_body_f1,
        result.noise_loop_avoided,
    )
    assert result.curiosity_mean_discovery_auc > result.random_mean_discovery_auc
    assert result.curiosity_mean_final_effect_recall > (result.random_mean_final_effect_recall)
    assert result.curiosity_mean_full_discovery_step < (result.random_mean_full_discovery_step)
    assert result.curiosity_mean_final_body_f1 >= result.random_mean_final_body_f1
    assert result.oracle_effect_actions == (
        PrimitiveAction.TURN_LEFT,
        PrimitiveAction.TURN_RIGHT,
        PrimitiveAction.MOVE_FORWARD,
    )
    assert result.oracle_body_sensor_indices


def test_curiosity_avoids_persistent_wait_loop() -> None:
    config = create_config()
    result = CuriosityRandomComparisonExperiment(
        TinyComparisonScenarioFactory(),
        create_trainer,
        config,
    ).run()

    assert result.noise_loop_avoided
    assert result.curiosity_maximum_noise_streak <= config.maximum_noise_streak
    assert all(trial.noise_share <= config.maximum_noise_share for trial in result.curiosity_trials)
    assert all(
        trial.final_noise_streak <= config.maximum_noise_streak for trial in result.curiosity_trials
    )


def test_comparison_uses_paired_models_and_matched_budgets() -> None:
    config = create_config(trial_count=4)
    result = CuriosityRandomComparisonExperiment(
        TinyComparisonScenarioFactory(),
        create_trainer,
        config,
    ).run()

    for curiosity_trial, random_trial in zip(
        result.curiosity_trials,
        result.random_trials,
        strict=True,
    ):
        assert curiosity_trial.trial_index == random_trial.trial_index
        assert curiosity_trial.model_seed == random_trial.model_seed
        assert len(curiosity_trial.timeline) == config.curiosity.play_budget
        assert len(random_trial.timeline) == config.curiosity.play_budget
        assert sum(item.count for item in curiosity_trial.action_counts) == (
            config.curiosity.play_budget
        )
        assert sum(item.count for item in random_trial.action_counts) == (
            config.curiosity.play_budget
        )


def test_comparison_is_reproducible() -> None:
    config = create_config(trial_count=4)
    factory = TinyComparisonScenarioFactory()

    first = CuriosityRandomComparisonExperiment(
        factory,
        create_trainer,
        config,
    ).run()
    second = CuriosityRandomComparisonExperiment(
        factory,
        create_trainer,
        config,
    ).run()

    assert first == second


def test_comparison_exports_are_ascii_and_inspectable(tmp_path: Path) -> None:
    result = CuriosityRandomComparisonExperiment(
        TinyComparisonScenarioFactory(),
        create_trainer,
        create_config(trial_count=3),
    ).run()
    json_path = tmp_path / "comparison.json"
    csv_path = tmp_path / "comparison.csv"

    export_curiosity_comparison_json(result, json_path)
    export_curiosity_comparison_csv(result, csv_path)

    json_text = json_path.read_text(encoding="ascii")
    csv_text = csv_path.read_text(encoding="ascii")
    assert '"pass_gate": true' in json_text
    assert '"noise_loop_avoided": true' in json_text
    assert '"curiosity_trials"' in json_text
    assert csv_text.startswith("strategy,trial_index,model_seed,step_number")
    assert "curiosity" in csv_text
    assert "random" in csv_text


def test_comparison_rejects_budget_above_scenario_limit() -> None:
    config = create_config(
        curiosity=CuriosityConfig(
            play_budget=13,
            experiment_actions=(
                PrimitiveAction.TURN_LEFT,
                PrimitiveAction.TURN_RIGHT,
                PrimitiveAction.MOVE_FORWARD,
                PrimitiveAction.WAIT,
            ),
        )
    )

    with pytest.raises(ValueError, match="exceeds scenario step budget"):
        CuriosityRandomComparisonExperiment(
            TinyComparisonScenarioFactory(step_budget=12),
            create_trainer,
            config,
        )


def test_comparison_rejects_noise_action_with_direct_effect() -> None:
    config = create_config(noise_action=PrimitiveAction.MOVE_FORWARD)

    with pytest.raises(ValueError, match="no direct controllable effect"):
        CuriosityRandomComparisonExperiment(
            TinyComparisonScenarioFactory(),
            create_trainer,
            config,
        )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"scenario_seed": -1}, "scenario_seed"),
        ({"model_seed": -1}, "model_seed"),
        ({"random_seed": -1}, "random_seed"),
        ({"trial_count": 0}, "trial_count"),
        ({"minimum_effect_samples": 0}, "minimum_effect_samples"),
        ({"minimum_effect_frequency": -0.1}, "minimum_effect_frequency"),
        ({"effect_threshold": -0.1}, "effect_threshold"),
        ({"body_score_threshold": 1.1}, "body_score_threshold"),
        ({"maximum_noise_share": 1.1}, "maximum_noise_share"),
        ({"maximum_noise_streak": 0}, "maximum_noise_streak"),
        ({"body_probe_actions": ()}, "body_probe_actions"),
        (
            {
                "body_probe_actions": (
                    PrimitiveAction.TURN_LEFT,
                    PrimitiveAction.TURN_LEFT,
                )
            },
            "unique",
        ),
        (
            {"body_probe_actions": (PrimitiveAction.ACKNOWLEDGE,)},
            "curiosity experiments",
        ),
        ({"noise_action": PrimitiveAction.ACKNOWLEDGE}, "noise_action"),
    ],
)
def test_comparison_config_rejects_invalid_values(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        create_config(**kwargs)
