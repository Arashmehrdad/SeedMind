"""Typed episodic-memory and belief records for SeedMind."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from seedmind.contracts import PrimitiveAction

EventPayloadValue = str | int | float | bool | None


class EpisodicEventType(StrEnum):
    """Small stable vocabulary for developmentally relevant events."""

    ACTION = "action"
    EXTERNAL_CHANGE = "external_change"
    HUMAN_GUIDANCE = "human_guidance"
    SUCCESS = "success"
    FAILURE = "failure"
    COUNTEREXAMPLE = "counterexample"


class BeliefEvidencePolarity(StrEnum):
    """Whether one episodic event supports or contradicts a belief."""

    SUPPORTS = "supports"
    CONTRADICTS = "contradicts"


class BeliefStatus(StrEnum):
    """Current confidence category for one evidence-linked belief."""

    CHALLENGED = "challenged"
    TENTATIVE = "tentative"
    SUPPORTED = "supported"


@dataclass(frozen=True, slots=True)
class SignificanceFeatures:
    """Normalized components used to decide whether an event is memorable."""

    prediction_error: float
    novelty: float
    learning_progress: float
    ambition_relevance: float
    human_relevance: float
    outcome_magnitude: float

    def __post_init__(self) -> None:
        for feature_name, feature_value in (
            ("prediction_error", self.prediction_error),
            ("novelty", self.novelty),
            ("learning_progress", self.learning_progress),
            ("ambition_relevance", self.ambition_relevance),
            ("human_relevance", self.human_relevance),
            ("outcome_magnitude", self.outcome_magnitude),
        ):
            _validate_unit_interval(feature_name, feature_value)


@dataclass(frozen=True, slots=True)
class EpisodicEventDraft:
    """One event before significance scoring and SQLite insertion."""

    event_id: str
    episode_id: str
    step_index: int
    event_type: EpisodicEventType
    context_code: str
    outcome_code: str
    features: SignificanceFeatures
    ambition_id: str | None = None
    action: PrimitiveAction | None = None
    success: bool | None = None
    payload: tuple[tuple[str, EventPayloadValue], ...] = ()

    def __post_init__(self) -> None:
        for identifier_name, identifier_value in (
            ("event_id", self.event_id),
            ("episode_id", self.episode_id),
            ("context_code", self.context_code),
            ("outcome_code", self.outcome_code),
        ):
            _validate_identifier(identifier_name, identifier_value)
        if self.ambition_id is not None:
            _validate_identifier("ambition_id", self.ambition_id)
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        payload_keys = tuple(key for key, _ in self.payload)
        if any(not key.strip() for key in payload_keys):
            raise ValueError("payload keys must not be empty")
        if len(payload_keys) != len(set(payload_keys)):
            raise ValueError("payload keys must be unique")
        for _, value in self.payload:
            if isinstance(value, float) and not isfinite(value):
                raise ValueError("payload floats must be finite")


@dataclass(frozen=True, slots=True)
class EpisodicEvent:
    """One durable significant or routine event loaded from SQLite."""

    sequence_id: int
    event_id: str
    episode_id: str
    step_index: int
    event_type: EpisodicEventType
    context_code: str
    outcome_code: str
    significance: float
    features: SignificanceFeatures
    ambition_id: str | None = None
    action: PrimitiveAction | None = None
    success: bool | None = None
    payload: tuple[tuple[str, EventPayloadValue], ...] = ()

    def __post_init__(self) -> None:
        if self.sequence_id <= 0:
            raise ValueError("sequence_id must be positive")
        _validate_unit_interval("significance", self.significance)


@dataclass(frozen=True, slots=True)
class MemoryQuery:
    """Contextual retrieval filters for episodic memory."""

    minimum_significance: float = 0.0
    ambition_id: str | None = None
    context_code: str | None = None
    event_type: EpisodicEventType | None = None
    limit: int = 50

    def __post_init__(self) -> None:
        _validate_unit_interval("minimum_significance", self.minimum_significance)
        if self.ambition_id is not None:
            _validate_identifier("ambition_id", self.ambition_id)
        if self.context_code is not None:
            _validate_identifier("context_code", self.context_code)
        if self.limit <= 0:
            raise ValueError("limit must be positive")


@dataclass(frozen=True, slots=True)
class BeliefProposition:
    """One symbolic proposition whose truth is grounded in episodic evidence."""

    subject_code: str
    relation_code: str
    object_code: str
    expected_value: bool

    def __post_init__(self) -> None:
        for identifier_name, identifier_value in (
            ("subject_code", self.subject_code),
            ("relation_code", self.relation_code),
            ("object_code", self.object_code),
        ):
            _validate_identifier(identifier_name, identifier_value)


@dataclass(frozen=True, slots=True)
class BeliefRecord:
    """Current confidence and evidence totals for one proposition."""

    belief_id: str
    proposition: BeliefProposition
    confidence: float
    support_weight: float
    contradiction_weight: float
    status: BeliefStatus
    created_event_id: str
    last_evidence_event_id: str
    revision_count: int

    def __post_init__(self) -> None:
        _validate_identifier("belief_id", self.belief_id)
        _validate_identifier("created_event_id", self.created_event_id)
        _validate_identifier("last_evidence_event_id", self.last_evidence_event_id)
        _validate_unit_interval("confidence", self.confidence)
        if not isfinite(self.support_weight) or self.support_weight < 0.0:
            raise ValueError("support_weight must be finite and non-negative")
        if not isfinite(self.contradiction_weight) or self.contradiction_weight < 0.0:
            raise ValueError("contradiction_weight must be finite and non-negative")
        if self.revision_count <= 0:
            raise ValueError("revision_count must be positive")


@dataclass(frozen=True, slots=True)
class BeliefEvidence:
    """One explicit link from a belief to an episodic event."""

    belief_id: str
    event_id: str
    polarity: BeliefEvidencePolarity
    weight: float
    observed_value: bool

    def __post_init__(self) -> None:
        _validate_identifier("belief_id", self.belief_id)
        _validate_identifier("event_id", self.event_id)
        if not isfinite(self.weight) or self.weight <= 0.0:
            raise ValueError("weight must be finite and positive")


@dataclass(frozen=True, slots=True)
class ContradictionRecord:
    """A belief-evidence link that opposes the expected proposition value."""

    belief_id: str
    event_id: str
    expected_value: bool
    observed_value: bool
    weight: float

    def __post_init__(self) -> None:
        _validate_identifier("belief_id", self.belief_id)
        _validate_identifier("event_id", self.event_id)
        if self.expected_value == self.observed_value:
            raise ValueError("contradiction must oppose the expected value")
        if not isfinite(self.weight) or self.weight <= 0.0:
            raise ValueError("weight must be finite and positive")


def _validate_identifier(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _validate_unit_interval(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
