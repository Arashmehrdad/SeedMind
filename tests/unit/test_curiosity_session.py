"""Tests for live curiosity-guided predictive training sessions."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pytest
import torch

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.curiosity import (
    CuriosityConfig,
    CuriosityTrainingConfig,
    CuriosityTrainingSession,
    export_curiosity_training_csv,
    export_curiosity_training_json,
)
from seedmind.environment import AgentState, NurseryRuntime, NurseryScenario, NurseryState
from seedmind.perception import SymbolicInputSpec
from seedmind.training import OnlinePredictiveTrainer, OnlineTrainerConfig


@dataclass(frozen=True, slots=True)
class TinyCuriosityScenarioFactory:
    """Create a deterministic open nursery for fast curiosity tests."""

    step_budget: int = 12

    def create(self, seed: int) -> NurseryScenario:
        """Return a stable body interface with no external processes."""
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
            scenario_id=f"tiny-curiosity-seed-{seed}",
            seed=seed,
            initial_state=state,
            step_budget=self.step_budget,
        )


def create_config(*, play_budget: int = 6) -> CuriosityTrainingConfig:
    """Return a small bounded live-session configuration."""
    return CuriosityTrainingConfig(
        seed=5,
        curiosity=CuriosityConfig(
            play_budget=play_budget,
            progress_window=2,
            novelty_decay=3.0,
            repetition_horizon=2,
            stagnation_horizon=3,
            experiment_actions=(
                PrimitiveAction.TURN_LEFT,
                PrimitiveAction.TURN_RIGHT,
                PrimitiveAction.WAIT,
            ),
        ),
    )


def create_trainer(
    factory: TinyCuriosityScenarioFactory,
    config: CuriosityTrainingConfig,
    *,
    model_seed: int,
) -> OnlinePredictiveTrainer:
    """Create a deterministic small predictive learner for the test world."""
    scenario = factory.create(config.seed)
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
            learning_rate=2e-2,
            weight_decay=0.0,
            confidence_weight=0.0,
            max_gradient_norm=5.0,
        ),
    )


def test_live_session_consumes_budget_and_trains_predictive_core() -> None:
    factory = TinyCuriosityScenarioFactory()
    config = create_config()
    trainer = create_trainer(factory, config, model_seed=11)
    before = tuple(parameter.detach().clone() for parameter in trainer.core.parameters())

    result = CuriosityTrainingSession(trainer, factory, config).run()
    after = tuple(parameter.detach() for parameter in trainer.core.parameters())

    assert result.selection_count == config.curiosity.play_budget
    assert len(result.selections) == config.curiosity.play_budget
    assert tuple(record.step_index for record in result.records) == tuple(range(6))
    assert tuple(record.source_step_id for record in result.records) == tuple(range(6))
    assert result.records[-1].remaining_budget == 0
    assert sum(count for _, count in result.action_counts) == 6
    assert all(record.action is not PrimitiveAction.STOP for record in result.records)
    assert all(record.prediction_error >= 0.0 for record in result.records)
    assert any(
        not torch.equal(previous, current)
        for previous, current in zip(before, after, strict=True)
    )
    assert trainer.active_episode_id is None


def test_live_session_is_reproducible_for_identical_seeds() -> None:
    factory = TinyCuriosityScenarioFactory()
    config = create_config()
    first_trainer = create_trainer(factory, config, model_seed=17)
    second_trainer = create_trainer(factory, config, model_seed=17)

    first = CuriosityTrainingSession(first_trainer, factory, config).run()
    second = CuriosityTrainingSession(second_trainer, factory, config).run()

    assert tuple(record.action for record in first.records) == tuple(
        record.action for record in second.records
    )
    assert tuple(record.prediction_error for record in first.records) == pytest.approx(
        tuple(record.prediction_error for record in second.records),
        rel=0.0,
        abs=0.0,
    )
    assert first.action_counts == second.action_counts


def test_live_timeline_retains_pre_action_candidates_and_post_action_error() -> None:
    factory = TinyCuriosityScenarioFactory()
    config = create_config(play_budget=3)
    trainer = create_trainer(factory, config, model_seed=3)

    result = CuriosityTrainingSession(trainer, factory, config).run()

    first_selection = result.selections[0]
    first_record = result.records[0]
    assert first_selection.selected_action is first_record.action
    assert first_selection.selected_candidate.sample_count == 0
    assert first_selection.selected_candidate.uncertainty == pytest.approx(1.0)
    assert first_record.prediction_error >= 0.0
    assert first_record.source_step_id == 0


def test_live_training_exports_are_ascii_and_inspectable(tmp_path: Path) -> None:
    factory = TinyCuriosityScenarioFactory()
    config = create_config(play_budget=3)
    trainer = create_trainer(factory, config, model_seed=7)
    result = CuriosityTrainingSession(trainer, factory, config).run()
    json_path = tmp_path / "live_timeline.json"
    csv_path = tmp_path / "live_timeline.csv"

    export_curiosity_training_json(result, json_path)
    export_curiosity_training_csv(result, csv_path)

    json_text = json_path.read_text(encoding="ascii")
    csv_text = csv_path.read_text(encoding="ascii")
    assert '"selection_count": 3' in json_text
    assert '"prediction_error"' in json_text
    assert '"candidates"' in json_text
    assert csv_text.startswith("step_index,episode_id,source_step_id,action")
    assert "tiny-curiosity-seed-5-curiosity" in csv_text


def test_live_session_rejects_budget_above_scenario_limit() -> None:
    factory = TinyCuriosityScenarioFactory(step_budget=2)
    config = create_config(play_budget=3)
    trainer = create_trainer(factory, config, model_seed=5)

    with pytest.raises(ValueError, match="exceeds scenario step budget"):
        CuriosityTrainingSession(trainer, factory, config)


def test_live_training_config_rejects_negative_seed() -> None:
    with pytest.raises(ValueError, match="seed"):
        CuriosityTrainingConfig(seed=-1)
