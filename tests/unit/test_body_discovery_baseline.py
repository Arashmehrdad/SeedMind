"""Tests for matched-budget body discovery against random exploration."""

from pathlib import Path

import pytest

from seedmind.contracts import PrimitiveAction
from seedmind.environment import DynamicNurseryScenarioFactory
from seedmind.self_model import (
    BodyDiscoveryBaselineConfig,
    BodyDiscoveryBaselineExperiment,
    export_body_discovery_baseline_csv,
    export_body_discovery_baseline_json,
)


def create_config() -> BodyDiscoveryBaselineConfig:
    """Return a compact deterministic comparison configuration."""
    return BodyDiscoveryBaselineConfig(
        scenario_seed=7,
        random_seed=31,
        transition_budget=12,
        random_trials=12,
        minimum_samples=4,
    )


def test_targeted_body_probes_beat_random_exploration() -> None:
    result = BodyDiscoveryBaselineExperiment(
        DynamicNurseryScenarioFactory(),
        create_config(),
    ).run()

    assert result.pass_gate
    assert result.targeted.transition_count == 12
    assert result.targeted.trusted_action_count == 3
    assert result.targeted.body_effect_mean_absolute_error == pytest.approx(0.0)
    assert result.targeted.body_effect_recall == pytest.approx(1.0)
    assert result.targeted.body_precision == pytest.approx(1.0)
    assert result.targeted.body_recall == pytest.approx(1.0)
    assert result.targeted.body_f1 == pytest.approx(1.0)
    assert result.targeted.body_effect_mean_absolute_error < (
        result.random_mean_body_effect_error
    )
    assert result.targeted.body_effect_recall > result.random_mean_body_effect_recall
    assert result.targeted.body_f1 > result.random_mean_body_f1


def test_comparison_is_reproducible() -> None:
    config = create_config()
    factory = DynamicNurseryScenarioFactory()

    first = BodyDiscoveryBaselineExperiment(factory, config).run()
    second = BodyDiscoveryBaselineExperiment(factory, config).run()

    assert first == second


def test_all_strategies_use_the_same_transition_budget() -> None:
    config = create_config()
    result = BodyDiscoveryBaselineExperiment(
        DynamicNurseryScenarioFactory(),
        config,
    ).run()

    assert result.targeted.transition_count == config.transition_budget
    assert all(
        trial.transition_count == config.transition_budget
        for trial in result.random_trials
    )
    assert all(
        sum(item.count for item in trial.action_counts) == config.transition_budget
        for trial in result.random_trials
    )
    assert all(
        item.action is not PrimitiveAction.STOP
        for trial in result.random_trials
        for item in trial.action_counts
    )


def test_targeted_schedule_allocates_equal_probe_evidence() -> None:
    config = create_config()
    result = BodyDiscoveryBaselineExperiment(
        DynamicNurseryScenarioFactory(),
        config,
    ).run()

    counts = {item.action: item.count for item in result.targeted.action_counts}

    assert counts == {
        PrimitiveAction.TURN_LEFT: 4,
        PrimitiveAction.TURN_RIGHT: 4,
        PrimitiveAction.MOVE_FORWARD: 4,
    }


def test_oracle_channels_are_derived_from_active_held_out_effects() -> None:
    experiment = BodyDiscoveryBaselineExperiment(
        DynamicNurseryScenarioFactory(),
        create_config(),
    )
    result = experiment.run()

    expected_indices = tuple(
        index
        for index in range(experiment.sensor_size)
        if any(
            abs(experience.controllable_sensor_change[index])
            > experiment.config.effect_threshold
            for experience in experiment.evaluation_experiences
        )
    )

    assert result.oracle_body_sensor_indices == expected_indices
    assert result.active_effect_count > 0
    assert all(index < 6 for index in result.oracle_body_sensor_indices)


def test_baseline_reports_are_ascii_and_inspectable(tmp_path: Path) -> None:
    result = BodyDiscoveryBaselineExperiment(
        DynamicNurseryScenarioFactory(),
        create_config(),
    ).run()
    json_path = tmp_path / "baseline_report.json"
    csv_path = tmp_path / "baseline_trials.csv"

    export_body_discovery_baseline_json(result, json_path)
    export_body_discovery_baseline_csv(result, csv_path)

    json_text = json_path.read_text(encoding="ascii")
    csv_text = csv_path.read_text(encoding="ascii")
    assert '"pass_gate": true' in json_text
    assert '"targeted"' in json_text
    assert '"random_summary"' in json_text
    assert csv_text.startswith("strategy,trial_index,transition_count")
    assert "targeted,,12,3" in csv_text
    assert "random,0,12" in csv_text


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"scenario_seed": -1}, "scenario_seed"),
        ({"random_seed": -1}, "random_seed"),
        ({"transition_budget": 0}, "transition_budget"),
        ({"random_trials": 0}, "random_trials"),
        ({"minimum_samples": 0}, "minimum_samples"),
        ({"effect_threshold": -1.0}, "effect_threshold"),
        ({"prediction_tolerance": -1.0}, "prediction_tolerance"),
        ({"body_score_threshold": 1.1}, "body_score_threshold"),
        ({"targeted_actions": ()}, "targeted_actions"),
        ({"random_actions": ()}, "random_actions"),
        (
            {
                "targeted_actions": (
                    PrimitiveAction.TURN_LEFT,
                    PrimitiveAction.TURN_LEFT,
                )
            },
            "unique",
        ),
        (
            {"random_actions": (PrimitiveAction.STOP,)},
            "stop",
        ),
        (
            {
                "targeted_actions": (PrimitiveAction.MOVE_FORWARD,),
                "random_actions": (PrimitiveAction.WAIT,),
            },
            "included",
        ),
    ],
)
def test_baseline_config_rejects_invalid_values(
    kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        BodyDiscoveryBaselineConfig(**kwargs)  # type: ignore[arg-type]
