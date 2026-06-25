"""Tests for the recurrent SeedMind predictive core."""

import pytest
import torch

from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore


def create_config() -> PredictiveCoreConfig:
    return PredictiveCoreConfig(
        observation_input_size=8,
        sensor_size=6,
        action_count=len(PrimitiveAction),
        observation_embedding_size=5,
        action_embedding_size=4,
        hidden_size=7,
    )


def test_core_output_shapes_and_ranges() -> None:
    torch.manual_seed(4)
    core = PredictiveSeedCore(create_config())
    observation = torch.rand((3, 8))
    previous_action = torch.tensor((-1, 0, 3))
    state = core.initial_state(batch_size=3)

    output = core(observation, previous_action, state)

    assert output.recurrent_state.shape == (3, 7)
    assert output.predicted_next_sensor.shape == (3, 6)
    assert output.predicted_controllable_change.shape == (3, 6)
    assert output.confidence.shape == (3, 1)
    assert torch.all((0.0 <= output.predicted_next_sensor))
    assert torch.all((output.predicted_next_sensor <= 1.0))
    assert torch.all((-1.0 <= output.predicted_controllable_change))
    assert torch.all((output.predicted_controllable_change <= 1.0))
    assert torch.all((0.0 <= output.confidence))
    assert torch.all((output.confidence <= 1.0))


def test_core_accepts_single_observation_and_no_previous_action() -> None:
    core = PredictiveSeedCore(create_config())

    output = core(
        torch.rand(8),
        torch.tensor(-1),
        core.initial_state(batch_size=1),
    )

    assert output.recurrent_state.shape == (1, 7)
    assert output.predicted_next_sensor.shape == (1, 6)


def test_recurrent_state_updates_across_timesteps() -> None:
    core = PredictiveSeedCore(create_config())
    observation = torch.rand((1, 8))
    action = torch.tensor((1,))
    initial = core.initial_state(batch_size=1)

    first = core(observation, action, initial)
    second = core(observation, action, first.recurrent_state)

    assert not torch.equal(first.recurrent_state, initial)
    assert not torch.equal(second.recurrent_state, first.recurrent_state)


def test_identical_seed_produces_identical_initial_predictions() -> None:
    observation = torch.rand((2, 8))
    actions = torch.tensor((-1, 2))

    torch.manual_seed(99)
    first_core = PredictiveSeedCore(create_config())
    first = first_core(
        observation,
        actions,
        first_core.initial_state(batch_size=2),
    )

    torch.manual_seed(99)
    second_core = PredictiveSeedCore(create_config())
    second = second_core(
        observation,
        actions,
        second_core.initial_state(batch_size=2),
    )

    torch.testing.assert_close(
        first.predicted_next_sensor,
        second.predicted_next_sensor,
    )
    torch.testing.assert_close(first.recurrent_state, second.recurrent_state)


@pytest.mark.parametrize(
    ("action", "message"),
    [
        (torch.tensor((-2,)), "invalid action"),
        (torch.tensor((len(PrimitiveAction),)), "invalid action"),
        (torch.tensor((0, 1)), "batch size"),
    ],
)
def test_core_rejects_invalid_previous_action(
    action: torch.Tensor,
    message: str,
) -> None:
    core = PredictiveSeedCore(create_config())

    with pytest.raises(ValueError, match=message):
        core(
            torch.rand((1, 8)),
            action,
            core.initial_state(batch_size=1),
        )


def test_core_rejects_invalid_observation_and_state_shapes() -> None:
    core = PredictiveSeedCore(create_config())

    with pytest.raises(ValueError, match="width"):
        core(
            torch.rand((1, 7)),
            torch.tensor((0,)),
            core.initial_state(batch_size=1),
        )

    with pytest.raises(ValueError, match="recurrent_state"):
        core(
            torch.rand((1, 8)),
            torch.tensor((0,)),
            torch.zeros((1, 6)),
        )


def test_core_rejects_invalid_config_dimensions() -> None:
    with pytest.raises(ValueError, match="sensor_size"):
        PredictiveCoreConfig(
            observation_input_size=4,
            sensor_size=5,
            action_count=1,
        )

    with pytest.raises(ValueError, match="hidden_size"):
        PredictiveCoreConfig(
            observation_input_size=4,
            sensor_size=4,
            action_count=1,
            hidden_size=0,
        )


def test_initial_state_matches_model_dtype() -> None:
    core = PredictiveSeedCore(create_config()).to(dtype=torch.float64)

    state = core.initial_state(batch_size=2)

    assert state.dtype is torch.float64
    assert state.shape == (2, 7)
