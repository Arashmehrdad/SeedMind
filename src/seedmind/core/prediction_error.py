"""Prediction comparison and confidence objective for SeedMind."""

from dataclasses import dataclass

import torch
from torch import Tensor
from torch.nn import functional as functional

from seedmind.core.predictive_state import PredictiveCoreOutput


@dataclass(frozen=True, slots=True)
class PredictionComparison:
    """Per-feature and reduced error between prediction and reality."""

    absolute_error: Tensor
    squared_error: Tensor
    mean_absolute_error: Tensor
    mean_squared_error: Tensor
    confidence_target: Tensor


@dataclass(frozen=True, slots=True)
class PredictionLoss:
    """Differentiable prediction, change, and confidence objective."""

    total: Tensor
    sensor_prediction: Tensor
    controllable_change: Tensor
    confidence_calibration: Tensor
    comparison: PredictionComparison


def compare_prediction(
    predicted_sensor: Tensor,
    actual_sensor: Tensor,
) -> PredictionComparison:
    """Compare predicted next sensor values with the observed next values."""
    if predicted_sensor.shape != actual_sensor.shape:
        raise ValueError("predicted and actual sensor shapes must match")

    if predicted_sensor.ndim == 1:
        predicted_sensor = predicted_sensor.unsqueeze(0)
        actual_sensor = actual_sensor.unsqueeze(0)

    if predicted_sensor.ndim != 2:
        raise ValueError("sensor tensors must be vectors or batches of vectors")

    difference = predicted_sensor - actual_sensor
    absolute_error = difference.abs()
    squared_error = difference.square()
    mean_absolute_error = absolute_error.mean(dim=-1, keepdim=True)
    mean_squared_error = squared_error.mean(dim=-1, keepdim=True)
    confidence_target = torch.exp(-mean_squared_error).detach()

    return PredictionComparison(
        absolute_error=absolute_error,
        squared_error=squared_error,
        mean_absolute_error=mean_absolute_error,
        mean_squared_error=mean_squared_error,
        confidence_target=confidence_target,
    )


def prediction_objective(
    output: PredictiveCoreOutput,
    actual_sensor: Tensor,
    *,
    current_sensor: Tensor | None = None,
    controllable_change_weight: float = 0.25,
    confidence_weight: float = 0.1,
) -> PredictionLoss:
    """Build the first prediction objective without task reward."""
    if controllable_change_weight < 0.0:
        raise ValueError("controllable_change_weight must not be negative")

    if confidence_weight < 0.0:
        raise ValueError("confidence_weight must not be negative")

    comparison = compare_prediction(
        output.predicted_next_sensor,
        actual_sensor,
    )
    sensor_prediction = comparison.mean_squared_error.mean()

    if current_sensor is None:
        controllable_change = torch.zeros(
            (),
            device=actual_sensor.device,
            dtype=actual_sensor.dtype,
        )
    else:
        if current_sensor.shape != actual_sensor.shape:
            raise ValueError("current and actual sensor shapes must match")

        if output.predicted_controllable_change.shape != actual_sensor.shape:
            raise ValueError("predicted controllable change shape must match sensor shape")

        actual_change = actual_sensor - current_sensor
        controllable_change = functional.mse_loss(
            output.predicted_controllable_change,
            actual_change,
        )

    confidence_calibration = functional.mse_loss(
        output.confidence,
        comparison.confidence_target,
    )
    total = (
        sensor_prediction
        + (controllable_change_weight * controllable_change)
        + (confidence_weight * confidence_calibration)
    )

    return PredictionLoss(
        total=total,
        sensor_prediction=sensor_prediction,
        controllable_change=controllable_change,
        confidence_calibration=confidence_calibration,
        comparison=comparison,
    )
