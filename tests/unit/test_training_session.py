"""Tests for reproducible familiar-sequence training sessions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
import torch

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.environment import AgentState, NurseryRuntime, NurseryScenario, NurseryState
from seedmind.perception import SymbolicInputSpec
from seedmind.training import (
    FamiliarSequenceConfig,
    FamiliarSequenceTrainingSession,
    OnlinePredictiveTrainer,
    OnlineTrainerConfig,
    export_prediction_error_svg,
    export_training_history_csv,
)


@dataclass(frozen=True, slots=True)
class TinyScenarioFactory:
    """Create a small deterministic world for fast training tests."""

    step_budget: int = 20

    def create(self, seed: int) -> NurseryScenario:
        """Return the same simple body interface for one seed."""
        state = NurseryState(
            width=4,
            height=4,
            agent=AgentState(
                position=GridPosition(1, 1),
                orientation=Direction.EAST,
            ),
            entities=(),
        )
        return NurseryScenario(
            scenario_id=f"tiny-seed-{seed}",
            seed=seed,
            initial_state=state,
            step_budget=self.step_budget,
        )


def create_trainer(
    factory: TinyScenarioFactory,
    *,
    scenario_seed: int,
    model_seed: int,
) -> OnlinePredictiveTrainer:
    """Create a small deterministic trainer matching the test scenario."""
    scenario = factory.create(scenario_seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-interface",
        resource_state_provider=scenario.resource_state,
    )
    observation = runtime.observe()
    input_spec = SymbolicInputSpec(
        sensor_size=len(observation.sensor_values),
        resource_state_size=len(observation.resource_state),
    )
    torch.manual_seed(model_seed)
    core = PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=input_spec.input_size,
            sensor_size=input_spec.sensor_size,
            action_count=len(PrimitiveAction),
            observation_embedding_size=8,
            action_embedding_size=4,
            hidden_size=12,
        )
    )
    return OnlinePredictiveTrainer(
        core,
        input_spec,
        config=OnlineTrainerConfig(
            learning_rate=3e-2,
            weight_decay=0.0,
            controllable_change_weight=0.1,
            confidence_weight=0.0,
            max_gradient_norm=5.0,
        ),
    )


def test_familiar_sequence_prediction_error_decreases() -> None:
    factory = TinyScenarioFactory()
    config = FamiliarSequenceConfig(
        seed=5,
        episode_count=12,
        action_sequence=(PrimitiveAction.WAIT,) * 3,
    )
    trainer = create_trainer(factory, scenario_seed=config.seed, model_seed=11)

    result = FamiliarSequenceTrainingSession(trainer, factory, config).run()

    assert result.completed_episodes == 12
    assert len(result.records) == 36
    assert result.prediction_error_improved
    assert result.final_mean_absolute_error < result.initial_mean_absolute_error


def test_checkpoint_resume_matches_uninterrupted_training(tmp_path: Path) -> None:
    factory = TinyScenarioFactory()
    config = FamiliarSequenceConfig(
        seed=3,
        episode_count=6,
        action_sequence=(PrimitiveAction.WAIT,) * 2,
    )

    full_trainer = create_trainer(factory, scenario_seed=config.seed, model_seed=17)
    full_result = FamiliarSequenceTrainingSession(
        full_trainer,
        factory,
        config,
    ).run()

    checkpoint_path = tmp_path / "checkpoint.pt"
    interrupted_trainer = create_trainer(
        factory,
        scenario_seed=config.seed,
        model_seed=17,
    )
    partial_result = FamiliarSequenceTrainingSession(
        interrupted_trainer,
        factory,
        config,
    ).run(
        checkpoint_path=checkpoint_path,
        max_episodes=2,
    )
    assert partial_result.completed_episodes == 2

    resumed_trainer = create_trainer(
        factory,
        scenario_seed=config.seed,
        model_seed=999,
    )
    resumed_result = FamiliarSequenceTrainingSession(
        resumed_trainer,
        factory,
        config,
    ).run(
        checkpoint_path=checkpoint_path,
        resume=True,
    )

    assert resumed_result.records == full_result.records
    for resumed_parameter, full_parameter in zip(
        resumed_trainer.core.parameters(),
        full_trainer.core.parameters(),
        strict=True,
    ):
        torch.testing.assert_close(resumed_parameter, full_parameter, rtol=0.0, atol=0.0)


def test_history_and_prediction_chart_exports(tmp_path: Path) -> None:
    factory = TinyScenarioFactory()
    config = FamiliarSequenceConfig(
        seed=2,
        episode_count=2,
        action_sequence=(PrimitiveAction.WAIT,),
    )
    trainer = create_trainer(factory, scenario_seed=config.seed, model_seed=7)
    result = FamiliarSequenceTrainingSession(trainer, factory, config).run()
    csv_path = tmp_path / "history.csv"
    svg_path = tmp_path / "prediction_error.svg"

    export_training_history_csv(result, csv_path)
    export_prediction_error_svg(result, svg_path)

    csv_text = csv_path.read_text(encoding="utf-8")
    svg_text = svg_path.read_text(encoding="ascii")
    assert csv_text.startswith("episode_index,sequence_index,episode_id")
    assert ",wait," in csv_text
    assert svg_text.startswith('<?xml version="1.0"')
    assert "SeedMind familiar-sequence prediction error" in svg_text
    assert "Mean absolute error" in svg_text


def test_resume_rejects_different_action_sequence(tmp_path: Path) -> None:
    factory = TinyScenarioFactory()
    original_config = FamiliarSequenceConfig(
        seed=1,
        episode_count=2,
        action_sequence=(PrimitiveAction.WAIT,),
    )
    trainer = create_trainer(factory, scenario_seed=1, model_seed=5)
    checkpoint_path = tmp_path / "checkpoint.pt"
    FamiliarSequenceTrainingSession(
        trainer,
        factory,
        original_config,
    ).run(
        checkpoint_path=checkpoint_path,
        max_episodes=1,
    )

    incompatible_config = FamiliarSequenceConfig(
        seed=1,
        episode_count=2,
        action_sequence=(PrimitiveAction.INSPECT,),
    )
    replacement_trainer = create_trainer(factory, scenario_seed=1, model_seed=5)

    with pytest.raises(ValueError, match="familiar sequence config"):
        FamiliarSequenceTrainingSession(
            replacement_trainer,
            factory,
            incompatible_config,
        ).run(
            checkpoint_path=checkpoint_path,
            resume=True,
        )


def test_resume_rejects_changed_scenario(tmp_path: Path) -> None:
    original_factory = TinyScenarioFactory(step_budget=20)
    config = FamiliarSequenceConfig(
        seed=1,
        episode_count=2,
        action_sequence=(PrimitiveAction.WAIT,),
    )
    checkpoint_path = tmp_path / "checkpoint.pt"
    trainer = create_trainer(original_factory, scenario_seed=1, model_seed=5)
    FamiliarSequenceTrainingSession(
        trainer,
        original_factory,
        config,
    ).run(
        checkpoint_path=checkpoint_path,
        max_episodes=1,
    )

    changed_factory = TinyScenarioFactory(step_budget=21)
    replacement_trainer = create_trainer(
        changed_factory,
        scenario_seed=1,
        model_seed=5,
    )

    with pytest.raises(ValueError, match="checkpoint scenario"):
        FamiliarSequenceTrainingSession(
            replacement_trainer,
            changed_factory,
            config,
        ).run(
            checkpoint_path=checkpoint_path,
            resume=True,
        )


@pytest.mark.parametrize(
    ("config_kwargs", "message"),
    [
        ({"seed": -1}, "seed"),
        ({"episode_count": 0}, "episode_count"),
        ({"action_sequence": ()}, "action_sequence"),
        ({"action_sequence": (PrimitiveAction.STOP,)}, "stop"),
        ({"checkpoint_every_episodes": 0}, "checkpoint_every_episodes"),
    ],
)
def test_familiar_sequence_config_rejects_invalid_values(
    config_kwargs: dict[str, object],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        FamiliarSequenceConfig(**config_kwargs)  # type: ignore[arg-type]
