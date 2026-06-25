"""Tests for prediction error and confidence calibration."""

import pytest
import torch

from seedmind.contracts import PrimitiveAction
from seedmind.core import (
    PredictiveCoreConfig,
    PredictiveSeedCore,
    compare_prediction,
    prediction_objective,
)


def create_core() -> PredictiveSeedCore:
    return PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=8,
            sensor_size=6,
            action_count=len(PrimitiveAction),
            observation_embedding_size=5,
            action_embedding_size=4,
            hidden_size=7,
        )
    )


def test_exact_prediction_has_zero_error_and_full_confidence_target() -> None:
    actual = torch.tensor((0.0, 0.5, 1.0))

    comparison = compare_prediction(actual, actual)

    torch.testing.assert_close(
        comparison.absolute_error,
        torch.zeros((1, 3)),
    )
    torch.testing.assert_close(
        comparison.mean_squared_error,
        torch.zeros((1, 1)),
    )
    torch.testing.assert_close(
        comparison.confidence_target,
        torch.ones((1, 1)),
    )


def test_prediction_comparison_reports_per_feature_and_reduced_error() -> None:
    predicted = torch.zeros((2, 3))
    actual = torch.ones((2, 3))

    comparison = compare_prediction(predicted, actual)

    torch.testing.assert_close(comparison.absolute_error, torch.ones((2, 3)))
    torch.testing.assert_close(comparison.squared_error, torch.ones((2, 3)))
    torch.testing.assert_close(
        comparison.mean_absolute_error,
        torch.ones((2, 1)),
    )
    torch.testing.assert_close(
        comparison.mean_squared_error,
        torch.ones((2, 1)),
    )
    torch.testing.assert_close(
        comparison.confidence_target,
        torch.exp(torch.tensor(-1.0)).repeat(2, 1),
    )


def test_prediction_objective_is_differentiable_without_task_reward() -> None:
    core = create_core()
    output = core(
        torch.rand((2, 8)),
        torch.tensor((-1, 2)),
        core.initial_state(batch_size=2),
    )
    actual_sensor = torch.rand((2, 6))

    loss = prediction_objective(output, actual_sensor)
    loss.total.backward()

    assert loss.total.ndim == 0
    assert loss.sensor_prediction.ndim == 0
    assert loss.confidence_calibration.ndim == 0
    assert torch.isfinite(loss.total)
    assert any(
        parameter.grad is not None
        for parameter in core.parameters()
    )


def test_prediction_objective_rejects_negative_confidence_weight() -> None:
    core = create_core()
    output = core(
        torch.rand((1, 8)),
        torch.tensor((-1,)),
        core.initial_state(batch_size=1),
    )

    with pytest.raises(ValueError, match="confidence_weight"):
        prediction_objective(
            output,
            torch.rand((1, 6)),
            confidence_weight=-0.1,
        )


def test_prediction_comparison_rejects_shape_mismatch() -> None:
    with pytest.raises(ValueError, match="shapes"):
        compare_prediction(torch.zeros((1, 3)), torch.zeros((1, 4)))

    with pytest.raises(ValueError, match="vectors"):
        compare_prediction(torch.zeros((1, 1, 3)), torch.zeros((1, 1, 3)))
