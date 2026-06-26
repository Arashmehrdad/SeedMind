"""Persistent ambition records, commitment, budgets, and milestones."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any


class AmbitionOrigin(StrEnum):
    """Evidence source that produced an ambition candidate."""

    OBSERVED_DEMONSTRATION = "observed_demonstration"


class AmbitionStatus(StrEnum):
    """Lifecycle state of one persistent ambition."""

    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    RETIRED = "retired"


class MilestoneStatus(StrEnum):
    """Lifecycle state of one developmental milestone."""

    PENDING = "pending"
    ACTIVE = "active"
    COMPLETED = "completed"


class MilestoneCode(StrEnum):
    """Generic causal milestones that do not encode nursery object names."""

    LOCATE_CAUSAL_SOURCE = "locate_causal_source"
    PRODUCE_INTERACTION = "produce_interaction"
    PRODUCE_REPEATABLE_EXTERNAL_CHANGE = "produce_repeatable_external_change"
    MATCH_DEMONSTRATED_OUTCOME = "match_demonstrated_outcome"


@dataclass(frozen=True, slots=True)
class AmbitionMilestone:
    """One ordered evidence threshold inside an ambition plan."""

    code: MilestoneCode
    sequence_index: int
    status: MilestoneStatus
    completion_threshold: float

    def __post_init__(self) -> None:
        if self.sequence_index < 0:
            raise ValueError("sequence_index must not be negative")
        _validate_score("completion_threshold", self.completion_threshold)


@dataclass(frozen=True, slots=True)
class AmbitionCandidate:
    """Evidence-backed capability candidate awaiting commitment."""

    candidate_id: str
    target_capability: str
    origin: AmbitionOrigin
    source_evidence_id: str
    evidence_count: int
    purpose_relevance: float
    expected_value: float
    attainability: float
    proposed_commitment: float
    practice_budget: int
    play_budget: int
    milestone_codes: tuple[MilestoneCode, ...]

    def __post_init__(self) -> None:
        for identifier_name, identifier_value in (
            ("candidate_id", self.candidate_id),
            ("target_capability", self.target_capability),
            ("source_evidence_id", self.source_evidence_id),
        ):
            if not identifier_value.strip():
                raise ValueError(f"{identifier_name} must not be empty")
        if self.evidence_count <= 0:
            raise ValueError("evidence_count must be positive")
        for score_name, score_value in (
            ("purpose_relevance", self.purpose_relevance),
            ("expected_value", self.expected_value),
            ("attainability", self.attainability),
            ("proposed_commitment", self.proposed_commitment),
        ):
            _validate_score(score_name, score_value)
        if self.practice_budget <= 0:
            raise ValueError("practice_budget must be positive")
        if self.play_budget < 0:
            raise ValueError("play_budget must not be negative")
        if not self.milestone_codes:
            raise ValueError("milestone_codes must not be empty")
        if len(self.milestone_codes) != len(set(self.milestone_codes)):
            raise ValueError("milestone_codes must be unique")


@dataclass(frozen=True, slots=True)
class AmbitionRecord:
    """Persistent active ambition state across episodes and restarts."""

    ambition_id: str
    target_capability: str
    origin: AmbitionOrigin
    source_evidence_ids: tuple[str, ...]
    purpose_relevance: float
    expected_value: float
    attainability: float
    commitment: float
    competence: float
    learning_progress: float
    milestones: tuple[AmbitionMilestone, ...]
    current_milestone_index: int
    support_level: int
    practice_budget: int
    remaining_practice_budget: int
    play_budget: int
    remaining_play_budget: int
    status: AmbitionStatus
    adopted_episode_id: str
    last_episode_id: str
    observed_episode_count: int

    def __post_init__(self) -> None:
        for identifier_name, identifier_value in (
            ("ambition_id", self.ambition_id),
            ("target_capability", self.target_capability),
            ("adopted_episode_id", self.adopted_episode_id),
            ("last_episode_id", self.last_episode_id),
        ):
            if not identifier_value.strip():
                raise ValueError(f"{identifier_name} must not be empty")
        if not self.source_evidence_ids:
            raise ValueError("source_evidence_ids must not be empty")
        if len(self.source_evidence_ids) != len(set(self.source_evidence_ids)):
            raise ValueError("source_evidence_ids must be unique")
        for score_name, score_value in (
            ("purpose_relevance", self.purpose_relevance),
            ("expected_value", self.expected_value),
            ("attainability", self.attainability),
            ("commitment", self.commitment),
            ("competence", self.competence),
            ("learning_progress", self.learning_progress),
        ):
            _validate_score(score_name, score_value)
        if not self.milestones:
            raise ValueError("milestones must not be empty")
        if tuple(item.sequence_index for item in self.milestones) != tuple(
            range(len(self.milestones))
        ):
            raise ValueError("milestone sequence indices must be contiguous")
        if not 0 <= self.current_milestone_index < len(self.milestones):
            raise ValueError("current_milestone_index is outside the milestone plan")
        if not 0 <= self.support_level <= 4:
            raise ValueError("support_level must be between zero and four")
        if self.practice_budget <= 0:
            raise ValueError("practice_budget must be positive")
        if not 0 <= self.remaining_practice_budget <= self.practice_budget:
            raise ValueError("remaining_practice_budget must fit inside practice_budget")
        if self.play_budget < 0:
            raise ValueError("play_budget must not be negative")
        if not 0 <= self.remaining_play_budget <= self.play_budget:
            raise ValueError("remaining_play_budget must fit inside play_budget")
        if self.observed_episode_count <= 0:
            raise ValueError("observed_episode_count must be positive")

    @property
    def current_milestone(self) -> AmbitionMilestone:
        """Return the currently active or final milestone."""
        return self.milestones[self.current_milestone_index]


@dataclass(frozen=True, slots=True)
class AmbitionManagerConfig:
    """Adoption weights and evidence thresholds for one active ambition."""

    minimum_evidence_count: int = 3
    adoption_score_threshold: float = 0.65
    purpose_weight: float = 0.30
    value_weight: float = 0.25
    attainability_weight: float = 0.20
    commitment_weight: float = 0.25
    default_support_level: int = 4

    def __post_init__(self) -> None:
        if self.minimum_evidence_count <= 0:
            raise ValueError("minimum_evidence_count must be positive")
        _validate_score("adoption_score_threshold", self.adoption_score_threshold)
        weights = (
            self.purpose_weight,
            self.value_weight,
            self.attainability_weight,
            self.commitment_weight,
        )
        if any(not isfinite(value) or value < 0.0 for value in weights):
            raise ValueError("ambition weights must be finite and non-negative")
        if sum(weights) <= 0.0:
            raise ValueError("at least one ambition weight must be positive")
        if not 0 <= self.default_support_level <= 4:
            raise ValueError("default_support_level must be between zero and four")


class AmbitionManager:
    """Adopt and retain one primary ambition across developmental episodes."""

    def __init__(
        self,
        config: AmbitionManagerConfig | None = None,
        *,
        active_ambition: AmbitionRecord | None = None,
    ) -> None:
        self.config = AmbitionManagerConfig() if config is None else config
        self._active_ambition = active_ambition

    @property
    def active_ambition(self) -> AmbitionRecord | None:
        """Return the current primary ambition, if one has been adopted."""
        return self._active_ambition

    def candidate_score(self, candidate: AmbitionCandidate) -> float:
        """Return a normalized configurable adoption score."""
        weighted = (
            self.config.purpose_weight * candidate.purpose_relevance
            + self.config.value_weight * candidate.expected_value
            + self.config.attainability_weight * candidate.attainability
            + self.config.commitment_weight * candidate.proposed_commitment
        )
        total_weight = (
            self.config.purpose_weight
            + self.config.value_weight
            + self.config.attainability_weight
            + self.config.commitment_weight
        )
        return weighted / total_weight

    def consider(
        self,
        candidate: AmbitionCandidate,
        *,
        episode_id: str,
    ) -> AmbitionRecord | None:
        """Adopt strong evidence or retain the matching active ambition."""
        _validate_identifier("episode_id", episode_id)
        if self._active_ambition is not None:
            if self._active_ambition.target_capability == candidate.target_capability:
                evidence_ids = tuple(
                    dict.fromkeys(
                        (
                            *self._active_ambition.source_evidence_ids,
                            candidate.source_evidence_id,
                        )
                    )
                )
                self._active_ambition = replace(
                    self._active_ambition,
                    source_evidence_ids=evidence_ids,
                    last_episode_id=episode_id,
                    observed_episode_count=(
                        self._active_ambition.observed_episode_count
                        + int(episode_id != self._active_ambition.last_episode_id)
                    ),
                )
            return self._active_ambition
        if candidate.evidence_count < self.config.minimum_evidence_count:
            return None
        if self.candidate_score(candidate) < self.config.adoption_score_threshold:
            return None
        milestones = tuple(
            AmbitionMilestone(
                code=code,
                sequence_index=index,
                status=(MilestoneStatus.ACTIVE if index == 0 else MilestoneStatus.PENDING),
                completion_threshold=0.80,
            )
            for index, code in enumerate(candidate.milestone_codes)
        )
        self._active_ambition = AmbitionRecord(
            ambition_id=f"ambition-{candidate.candidate_id}",
            target_capability=candidate.target_capability,
            origin=candidate.origin,
            source_evidence_ids=(candidate.source_evidence_id,),
            purpose_relevance=candidate.purpose_relevance,
            expected_value=candidate.expected_value,
            attainability=candidate.attainability,
            commitment=candidate.proposed_commitment,
            competence=0.0,
            learning_progress=0.0,
            milestones=milestones,
            current_milestone_index=0,
            support_level=self.config.default_support_level,
            practice_budget=candidate.practice_budget,
            remaining_practice_budget=candidate.practice_budget,
            play_budget=candidate.play_budget,
            remaining_play_budget=candidate.play_budget,
            status=AmbitionStatus.ACTIVE,
            adopted_episode_id=episode_id,
            last_episode_id=episode_id,
            observed_episode_count=1,
        )
        return self._active_ambition

    def begin_episode(self, episode_id: str) -> AmbitionRecord | None:
        """Carry the active ambition into a new episode without resetting it."""
        _validate_identifier("episode_id", episode_id)
        if self._active_ambition is None:
            return None
        if episode_id == self._active_ambition.last_episode_id:
            return self._active_ambition
        self._active_ambition = replace(
            self._active_ambition,
            last_episode_id=episode_id,
            observed_episode_count=self._active_ambition.observed_episode_count + 1,
        )
        return self._active_ambition

    def allocate_practice(self, units: int, *, episode_id: str) -> AmbitionRecord:
        """Consume bounded practice units from the active ambition."""
        if units <= 0:
            raise ValueError("practice units must be positive")
        ambition = self._require_active()
        if units > ambition.remaining_practice_budget:
            raise ValueError("practice allocation exceeds remaining budget")
        self.begin_episode(episode_id)
        ambition = self._require_active()
        self._active_ambition = replace(
            ambition,
            remaining_practice_budget=ambition.remaining_practice_budget - units,
        )
        return self._active_ambition

    def record_progress(
        self,
        progress: float,
        *,
        competence: float,
        episode_id: str,
    ) -> AmbitionRecord:
        """Update learning evidence and advance one achieved milestone."""
        _validate_score("progress", progress)
        _validate_score("competence", competence)
        self.begin_episode(episode_id)
        ambition = self._require_active()
        milestones = list(ambition.milestones)
        current = milestones[ambition.current_milestone_index]
        next_index = ambition.current_milestone_index
        status = ambition.status
        if progress >= current.completion_threshold:
            milestones[next_index] = replace(current, status=MilestoneStatus.COMPLETED)
            if next_index + 1 < len(milestones):
                next_index += 1
                milestones[next_index] = replace(
                    milestones[next_index],
                    status=MilestoneStatus.ACTIVE,
                )
            else:
                status = AmbitionStatus.COMPLETED
        self._active_ambition = replace(
            ambition,
            competence=competence,
            learning_progress=progress,
            milestones=tuple(milestones),
            current_milestone_index=next_index,
            status=status,
        )
        return self._active_ambition

    def _require_active(self) -> AmbitionRecord:
        if self._active_ambition is None:
            raise RuntimeError("no active ambition")
        if self._active_ambition.status is not AmbitionStatus.ACTIVE:
            raise RuntimeError("active ambition is not available for practice")
        return self._active_ambition


def save_ambition_manager(manager: AmbitionManager, path: Path) -> None:
    """Atomically persist the manager and active ambition as ASCII JSON."""
    payload = {
        "config": _config_payload(manager.config),
        "active_ambition": (
            _record_payload(manager.active_ambition)
            if manager.active_ambition is not None
            else None
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def load_ambition_manager(path: Path) -> AmbitionManager:
    """Load a previously persisted ambition manager with strict validation."""
    payload = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(payload, dict):
        raise ValueError("ambition state must contain a JSON object")
    config_payload = _required_mapping(payload, "config")
    active_payload = payload.get("active_ambition")
    config = AmbitionManagerConfig(
        minimum_evidence_count=_required_int(config_payload, "minimum_evidence_count"),
        adoption_score_threshold=_required_float(config_payload, "adoption_score_threshold"),
        purpose_weight=_required_float(config_payload, "purpose_weight"),
        value_weight=_required_float(config_payload, "value_weight"),
        attainability_weight=_required_float(config_payload, "attainability_weight"),
        commitment_weight=_required_float(config_payload, "commitment_weight"),
        default_support_level=_required_int(config_payload, "default_support_level"),
    )
    active = None
    if active_payload is not None:
        if not isinstance(active_payload, dict):
            raise ValueError("active_ambition must be an object or null")
        active = _record_from_payload(active_payload)
    return AmbitionManager(config, active_ambition=active)


def export_ambition_dashboard(manager: AmbitionManager, path: Path) -> None:
    """Write an inspectable ASCII dashboard for the active ambition."""
    active = manager.active_ambition
    payload = {
        "has_active_ambition": active is not None,
        "active_ambition": _record_payload(active) if active is not None else None,
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def _config_payload(config: AmbitionManagerConfig) -> dict[str, object]:
    return {
        "minimum_evidence_count": config.minimum_evidence_count,
        "adoption_score_threshold": config.adoption_score_threshold,
        "purpose_weight": config.purpose_weight,
        "value_weight": config.value_weight,
        "attainability_weight": config.attainability_weight,
        "commitment_weight": config.commitment_weight,
        "default_support_level": config.default_support_level,
    }


def _record_payload(record: AmbitionRecord) -> dict[str, object]:
    return {
        "ambition_id": record.ambition_id,
        "target_capability": record.target_capability,
        "origin": record.origin.value,
        "source_evidence_ids": list(record.source_evidence_ids),
        "purpose_relevance": record.purpose_relevance,
        "expected_value": record.expected_value,
        "attainability": record.attainability,
        "commitment": record.commitment,
        "competence": record.competence,
        "learning_progress": record.learning_progress,
        "milestones": [
            {
                "code": milestone.code.value,
                "sequence_index": milestone.sequence_index,
                "status": milestone.status.value,
                "completion_threshold": milestone.completion_threshold,
            }
            for milestone in record.milestones
        ],
        "current_milestone_index": record.current_milestone_index,
        "support_level": record.support_level,
        "practice_budget": record.practice_budget,
        "remaining_practice_budget": record.remaining_practice_budget,
        "play_budget": record.play_budget,
        "remaining_play_budget": record.remaining_play_budget,
        "status": record.status.value,
        "adopted_episode_id": record.adopted_episode_id,
        "last_episode_id": record.last_episode_id,
        "observed_episode_count": record.observed_episode_count,
    }


def _record_from_payload(payload: dict[str, Any]) -> AmbitionRecord:
    milestone_payloads = _required_list(payload, "milestones")
    milestones: list[AmbitionMilestone] = []
    for item in milestone_payloads:
        if not isinstance(item, dict):
            raise ValueError("milestones must contain objects")
        milestones.append(
            AmbitionMilestone(
                code=MilestoneCode(_required_str(item, "code")),
                sequence_index=_required_int(item, "sequence_index"),
                status=MilestoneStatus(_required_str(item, "status")),
                completion_threshold=_required_float(item, "completion_threshold"),
            )
        )
    evidence_values = _required_list(payload, "source_evidence_ids")
    if any(not isinstance(value, str) for value in evidence_values):
        raise ValueError("source_evidence_ids must contain strings")
    return AmbitionRecord(
        ambition_id=_required_str(payload, "ambition_id"),
        target_capability=_required_str(payload, "target_capability"),
        origin=AmbitionOrigin(_required_str(payload, "origin")),
        source_evidence_ids=tuple(str(value) for value in evidence_values),
        purpose_relevance=_required_float(payload, "purpose_relevance"),
        expected_value=_required_float(payload, "expected_value"),
        attainability=_required_float(payload, "attainability"),
        commitment=_required_float(payload, "commitment"),
        competence=_required_float(payload, "competence"),
        learning_progress=_required_float(payload, "learning_progress"),
        milestones=tuple(milestones),
        current_milestone_index=_required_int(payload, "current_milestone_index"),
        support_level=_required_int(payload, "support_level"),
        practice_budget=_required_int(payload, "practice_budget"),
        remaining_practice_budget=_required_int(payload, "remaining_practice_budget"),
        play_budget=_required_int(payload, "play_budget"),
        remaining_play_budget=_required_int(payload, "remaining_play_budget"),
        status=AmbitionStatus(_required_str(payload, "status")),
        adopted_episode_id=_required_str(payload, "adopted_episode_id"),
        last_episode_id=_required_str(payload, "last_episode_id"),
        observed_episode_count=_required_int(payload, "observed_episode_count"),
    )


def _required_mapping(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise ValueError(f"{key} must be an object")
    return value


def _required_list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _required_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _required_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise ValueError(f"{key} must be an integer")
    return value


def _required_float(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _validate_identifier(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")


def _validate_score(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
