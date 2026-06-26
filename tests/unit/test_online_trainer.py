"""Tests for one-step online predictive training."""

from collections.abc import Callable
from math import isfinite

import pytest
import torch

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.environment import AgentState, NurseryRuntime, NurseryState
from seedmind.environment.scenario import NurseryScenarioFactory
from seedmind.perception import SymbolicInputSpec
from seedmind.training import (
    OnlinePredictiveTrainer,
    OnlineTrainerConfig,
    collect_experience,
)


def create_runtime(*, episode_id: str = "episode-1") -> NurseryRuntime:
    state = NurseryState(
        width=4,
        height=4,
        agent=AgentState(
            position=GridPosition(1, 1),
            orientation=Direction.EAST,
        ),
        entities=(),
    )
    return NurseryRuntime(initial_state=state, episode_id=episode_id)


def create_trainer(runtime: NurseryRuntime) -> OnlinePredictiveTrainer:
    sensor_size = len(runtime.observe().sensor_values)
    input_spec = SymbolicInputSpec(sensor_size=sensor_size)
    core = PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=input_spec.input_size,
            sensor_size=sensor_size,
            action_count=len(PrimitiveAction),
            observation_embedding_size=12,
            action_embedding_size=6,
            hidden_size=16,
        )
    )
    return OnlinePredictiveTrainer(
        core,
        input_spec,
        config=OnlineTrainerConfig(learning_rate=1e-2),
    )


def test_train_transition_updates_parameters_and_returns_metrics() -> None:
    torch.manual_seed(3)
    runtime = create_runtime()
    trainer = create_trainer(runtime)
    experience = collect_experience(runtime, PrimitiveAction.MOVE_FORWARD)
    before = tuple(parameter.detach().clone() for parameter in trainer.core.parameters())

    metrics = trainer.train_transition(experience)
    after = tuple(parameter.detach() for parameter in trainer.core.parameters())

    assert metrics.episode_id == "episode-1"
    assert metrics.source_step_id == 0
    assert metrics.terminated is False
    assert isfinite(metrics.total_loss)
    assert isfinite(metrics.sensor_prediction_loss)
    assert isfinite(metrics.controllable_change_loss)
    assert isfinite(metrics.confidence_calibration_loss)
    assert isfinite(metrics.mean_absolute_error)
    assert isfinite(metrics.mean_confidence)
    assert isfinite(metrics.gradient_norm)
    assert any(
        not torch.equal(previous, current) for previous, current in zip(before, after, strict=True)
    )
    assert trainer.active_episode_id == "episode-1"
    assert trainer.recurrent_state.grad_fn is None


def test_trainer_consumes_scenario_resource_channel() -> None:
    scenario = NurseryScenarioFactory(step_budget=4).create(seed=13)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=scenario.scenario_id,
        resource_state_provider=scenario.resource_state,
    )
    initial_observation = runtime.observe()
    input_spec = SymbolicInputSpec(
        sensor_size=len(initial_observation.sensor_values),
        resource_state_size=1,
    )
    core = PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=input_spec.input_size,
            sensor_size=input_spec.sensor_size,
            action_count=len(PrimitiveAction),
            observation_embedding_size=12,
            action_embedding_size=6,
            hidden_size=16,
        )
    )
    trainer = OnlinePredictiveTrainer(core, input_spec)

    experience = collect_experience(runtime, PrimitiveAction.WAIT)
    metrics = trainer.train_transition(experience)

    assert experience.observation.resource_state == (1.0,)
    assert experience.next_observation.resource_state == (0.75,)
    assert isfinite(metrics.total_loss)


def test_trainer_preserves_recurrent_state_across_ordered_experience() -> None:
    runtime = create_runtime()
    trainer = create_trainer(runtime)
    first_experience = collect_experience(runtime, PrimitiveAction.WAIT)
    second_experience = collect_experience(runtime, PrimitiveAction.TURN_LEFT)

    trainer.train_transition(first_experience)
    first_state = trainer.recurrent_state.clone()
    second_metrics = trainer.train_transition(second_experience)

    assert second_metrics.source_step_id == 1
    assert not torch.equal(trainer.recurrent_state, first_state)


def test_reset_episode_clears_short_term_state_and_sequence_identity() -> None:
    runtime = create_runtime()
    trainer = create_trainer(runtime)
    trainer.train_transition(collect_experience(runtime, PrimitiveAction.WAIT))

    trainer.reset_episode()

    assert trainer.active_episode_id is None
    torch.testing.assert_close(
        trainer.recurrent_state,
        torch.zeros_like(trainer.recurrent_state),
    )


def test_trainer_rejects_temporal_discontinuity() -> None:
    runtime = create_runtime()
    trainer = create_trainer(runtime)
    trainer.train_transition(collect_experience(runtime, PrimitiveAction.WAIT))
    restarted_runtime = create_runtime()
    repeated_step_zero = collect_experience(
        restarted_runtime,
        PrimitiveAction.WAIT,
    )

    with pytest.raises(ValueError, match="temporally continuous"):
        trainer.train_transition(repeated_step_zero)


def test_trainer_rejects_episode_change_without_reset() -> None:
    runtime = create_runtime()
    trainer = create_trainer(runtime)
    trainer.train_transition(collect_experience(runtime, PrimitiveAction.WAIT))
    other_runtime = create_runtime(episode_id="episode-2")
    other_experience = collect_experience(other_runtime, PrimitiveAction.WAIT)

    with pytest.raises(ValueError, match="episode changed"):
        trainer.train_transition(other_experience)


def test_termination_requires_episode_reset_before_more_training() -> None:
    runtime = create_runtime()
    trainer = create_trainer(runtime)
    terminal_experience = collect_experience(runtime, PrimitiveAction.STOP)
    trainer.train_transition(terminal_experience)
    replacement_runtime = create_runtime(episode_id="episode-2")
    replacement_experience = collect_experience(
        replacement_runtime,
        PrimitiveAction.WAIT,
    )

    with pytest.raises(RuntimeError, match="reset_episode"):
        trainer.train_transition(replacement_experience)


def test_reset_allows_training_a_new_episode() -> None:
    runtime = create_runtime()
    trainer = create_trainer(runtime)
    trainer.train_transition(collect_experience(runtime, PrimitiveAction.STOP))
    trainer.reset_episode()
    next_runtime = create_runtime(episode_id="episode-2")

    metrics = trainer.train_transition(collect_experience(next_runtime, PrimitiveAction.WAIT))

    assert metrics.episode_id == "episode-2"


def test_trainer_rejects_incompatible_input_specification() -> None:
    runtime = create_runtime()
    sensor_size = len(runtime.observe().sensor_values)
    core = PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=sensor_size,
            sensor_size=sensor_size,
            action_count=len(PrimitiveAction),
        )
    )

    with pytest.raises(ValueError, match="observation input size"):
        OnlinePredictiveTrainer(
            core,
            SymbolicInputSpec(sensor_size=sensor_size, resource_state_size=1),
        )


def test_trainer_rejects_action_count_mismatch() -> None:
    runtime = create_runtime()
    sensor_size = len(runtime.observe().sensor_values)
    core = PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=sensor_size,
            sensor_size=sensor_size,
            action_count=1,
        )
    )

    with pytest.raises(ValueError, match="action count"):
        OnlinePredictiveTrainer(core, SymbolicInputSpec(sensor_size=sensor_size))


@pytest.mark.parametrize(
    ("factory", "message"),
    [
        (lambda: OnlineTrainerConfig(learning_rate=0.0), "learning_rate"),
        (lambda: OnlineTrainerConfig(weight_decay=-0.1), "weight_decay"),
        (
            lambda: OnlineTrainerConfig(controllable_change_weight=-0.1),
            "controllable_change_weight",
        ),
        (lambda: OnlineTrainerConfig(confidence_weight=-0.1), "confidence_weight"),
        (lambda: OnlineTrainerConfig(max_gradient_norm=0.0), "max_gradient_norm"),
    ],
)
def test_trainer_config_rejects_invalid_values(
    factory: Callable[[], OnlineTrainerConfig],
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        factory()
