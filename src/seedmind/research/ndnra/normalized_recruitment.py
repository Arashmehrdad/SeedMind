"""Deterministic local normalization for competing incoming recruitment."""

from __future__ import annotations

from dataclasses import dataclass
from math import fsum, isfinite

from seedmind.research.ndnra.models import RecallResult


@dataclass(frozen=True, slots=True)
class OrderedLocalIncomingContribution:
    """One ordered local contribution into a target neuron."""

    source_id: str
    local_contribution: float

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.source_id.isascii():
            raise ValueError("source_id must be non-empty ASCII text")
        if not isfinite(self.local_contribution):
            raise ValueError("local_contribution must be finite")


@dataclass(frozen=True, slots=True)
class NormalizedIncomingSupportEvidence:
    """Immutable evidence for one target neuron's local incoming support."""

    target_neuron_id: str
    ordered_contributions: tuple[OrderedLocalIncomingContribution, ...]
    raw_positive_sum: float
    positive_contributor_count: int
    maximum_local_contribution: float
    normalized_support: float
    bounded: bool

    def __post_init__(self) -> None:
        if not self.target_neuron_id.strip() or not self.target_neuron_id.isascii():
            raise ValueError("target_neuron_id must be non-empty ASCII text")
        source_ids = tuple(item.source_id for item in self.ordered_contributions)
        if source_ids != tuple(sorted(source_ids)) or len(source_ids) != len(set(source_ids)):
            raise ValueError("ordered_contributions must use unique sorted source identities")
        if self.positive_contributor_count < 0:
            raise ValueError("positive_contributor_count must not be negative")
        for name, value in (
            ("raw_positive_sum", self.raw_positive_sum),
            ("maximum_local_contribution", self.maximum_local_contribution),
            ("normalized_support", self.normalized_support),
        ):
            if not isfinite(value) or value < 0.0:
                raise ValueError(f"{name} must be finite and non-negative")
        positive_values = tuple(
            item.local_contribution
            for item in self.ordered_contributions
            if item.local_contribution > 0.0
        )
        expected_sum = fsum(positive_values)
        expected_count = len(positive_values)
        expected_maximum = max(positive_values, default=0.0)
        expected_normalized = expected_sum / expected_count if expected_count else 0.0
        expected_bounded = bool(
            all(-1.0 <= item.local_contribution <= 1.0 for item in self.ordered_contributions)
            and 0.0 <= expected_normalized <= 1.0
        )
        if self.raw_positive_sum != expected_sum:
            raise ValueError("raw_positive_sum does not match ordered contributions")
        if self.positive_contributor_count != expected_count:
            raise ValueError("positive_contributor_count does not match ordered contributions")
        if self.maximum_local_contribution != expected_maximum:
            raise ValueError("maximum_local_contribution does not match ordered contributions")
        if self.normalized_support != expected_normalized:
            raise ValueError("normalized_support does not match ordered contributions")
        if self.bounded is not expected_bounded:
            raise ValueError("bounded does not match local contribution limits")


@dataclass(frozen=True, slots=True)
class RecallDepthNormalizationEvidence:
    """Per-depth normalization evidence in deterministic neuron order."""

    depth: int
    neuron_evidence: tuple[NormalizedIncomingSupportEvidence, ...]

    def __post_init__(self) -> None:
        if self.depth <= 0:
            raise ValueError("depth must be positive")
        target_ids = tuple(item.target_neuron_id for item in self.neuron_evidence)
        if target_ids != tuple(sorted(target_ids)) or len(target_ids) != len(set(target_ids)):
            raise ValueError("neuron_evidence must use unique sorted target identities")


@dataclass(frozen=True, slots=True)
class RecallNormalizationEvidence:
    """Complete deterministic normalization evidence for one recall attempt."""

    depth_evidence: tuple[RecallDepthNormalizationEvidence, ...]
    bounded: bool

    def __post_init__(self) -> None:
        depths = tuple(item.depth for item in self.depth_evidence)
        if depths != tuple(range(1, len(depths) + 1)):
            raise ValueError("depth_evidence must be contiguous from depth one")
        expected_bounded = all(
            item.bounded for depth in self.depth_evidence for item in depth.neuron_evidence
        )
        if self.bounded is not expected_bounded:
            raise ValueError("bounded does not match per-neuron normalization evidence")


@dataclass(frozen=True, slots=True)
class RecallWithNormalizationEvidence:
    """Backward-compatible recall result plus immutable normalization evidence."""

    recall_result: RecallResult
    normalization_evidence: RecallNormalizationEvidence

    def __post_init__(self) -> None:
        if len(self.normalization_evidence.depth_evidence) != self.recall_result.depth_used:
            raise ValueError("normalization evidence depth does not match recall depth used")


def normalize_local_incoming_support(
    *,
    target_neuron_id: str,
    ordered_contributions: tuple[OrderedLocalIncomingContribution, ...],
) -> NormalizedIncomingSupportEvidence:
    """Average only positive local incoming contributions, or floor to zero."""
    source_ids = tuple(item.source_id for item in ordered_contributions)
    if source_ids != tuple(sorted(source_ids)) or len(source_ids) != len(set(source_ids)):
        raise ValueError("ordered_contributions must use unique sorted source identities")
    positive_values = tuple(
        contribution.local_contribution
        for contribution in ordered_contributions
        if contribution.local_contribution > 0.0
    )
    raw_positive_sum = fsum(positive_values)
    positive_contributor_count = len(positive_values)
    maximum_local_contribution = max(positive_values, default=0.0)
    normalized_support = (
        raw_positive_sum / positive_contributor_count if positive_contributor_count else 0.0
    )
    bounded = bool(
        all(-1.0 <= item.local_contribution <= 1.0 for item in ordered_contributions)
        and 0.0 <= normalized_support <= 1.0
    )

    return NormalizedIncomingSupportEvidence(
        target_neuron_id=target_neuron_id,
        ordered_contributions=ordered_contributions,
        raw_positive_sum=raw_positive_sum,
        positive_contributor_count=positive_contributor_count,
        maximum_local_contribution=maximum_local_contribution,
        normalized_support=normalized_support,
        bounded=bounded,
    )
