"""Transparent significance scoring for episodic memory."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from seedmind.memory.models import SignificanceFeatures


@dataclass(frozen=True, slots=True)
class SignificanceConfig:
    """Non-negative normalized weights for developmentally relevant events."""

    prediction_error_weight: float = 0.20
    novelty_weight: float = 0.20
    learning_progress_weight: float = 0.15
    ambition_relevance_weight: float = 0.20
    human_relevance_weight: float = 0.10
    outcome_magnitude_weight: float = 0.15

    def __post_init__(self) -> None:
        weights = self.weights
        if any(not isfinite(value) or value < 0.0 for value in weights):
            raise ValueError("significance weights must be finite and non-negative")
        if sum(weights) <= 0.0:
            raise ValueError("at least one significance weight must be positive")

    @property
    def weights(self) -> tuple[float, ...]:
        """Return weights in the same order as SignificanceFeatures fields."""
        return (
            self.prediction_error_weight,
            self.novelty_weight,
            self.learning_progress_weight,
            self.ambition_relevance_weight,
            self.human_relevance_weight,
            self.outcome_magnitude_weight,
        )


class SignificanceScorer:
    """Compute one reproducible normalized memory-significance score."""

    def __init__(self, config: SignificanceConfig | None = None) -> None:
        self.config = SignificanceConfig() if config is None else config

    def score(self, features: SignificanceFeatures) -> float:
        """Return the weighted normalized significance of one event."""
        values = (
            features.prediction_error,
            features.novelty,
            features.learning_progress,
            features.ambition_relevance,
            features.human_relevance,
            features.outcome_magnitude,
        )
        weighted_sum = sum(
            weight * value for weight, value in zip(self.config.weights, values, strict=True)
        )
        return weighted_sum / sum(self.config.weights)
