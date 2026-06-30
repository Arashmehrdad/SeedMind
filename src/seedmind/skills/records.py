"""Inspectable main-project reusable skill records."""

from __future__ import annotations

import json
from dataclasses import dataclass, replace
from enum import StrEnum
from pathlib import Path
from typing import Any

from seedmind.contracts import PrimitiveAction

SKILL_SCHEMA_VERSION = 1


class SkillValidationStatus(StrEnum):
    """Last validation state for a compiled skill."""

    UNVALIDATED = "unvalidated"
    PASSED = "passed"
    FAILED = "failed"


class SkillAttemptSource(StrEnum):
    """Source boundary for experience used by the main skill compiler."""

    GROUNDED_PRODUCTION = "grounded_production"
    BOUNDED_IMAGINATION = "bounded_imagination"
    EVALUATION = "evaluation"


class SkillCompileFailure(StrEnum):
    """Machine-readable reasons why compilation is rejected."""

    INSUFFICIENT_EVIDENCE = "insufficient_evidence"
    INCOMPLETE_SEQUENCE = "incomplete_sequence"
    CONTRADICTORY_SEQUENCE = "contradictory_sequence"
    UNSAFE_OR_UNAVAILABLE_ACTION = "unsafe_or_unavailable_action"
    NON_GROUNDED_SOURCE = "non_grounded_source"


@dataclass(frozen=True, slots=True)
class SkillStepEvidence:
    """One primitive production transition used as skill evidence."""

    action: PrimitiveAction
    outcome: str
    action_available: bool
    world_changed: bool

    def __post_init__(self) -> None:
        if not self.outcome.strip() or not self.outcome.isascii():
            raise ValueError("outcome must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "action": self.action.value,
            "action_available": self.action_available,
            "outcome": self.outcome,
            "world_changed": self.world_changed,
        }

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> SkillStepEvidence:
        """Load one step and reject partial or incompatible data."""
        return cls(
            action=PrimitiveAction(str(payload["action"])),
            outcome=str(payload["outcome"]),
            action_available=bool(payload["action_available"]),
            world_changed=bool(payload["world_changed"]),
        )


@dataclass(frozen=True, slots=True)
class SkillEpisodeEvidence:
    """Grounded episode that may support compiling a reusable skill."""

    episode_id: str
    seed: int
    source: SkillAttemptSource
    target_object_id: str
    target_id: str
    steps: tuple[SkillStepEvidence, ...]
    success: bool
    used_for_evaluation: bool = False

    def __post_init__(self) -> None:
        if not self.episode_id.strip() or not self.episode_id.isascii():
            raise ValueError("episode_id must be non-empty ASCII")
        if self.seed < 0:
            raise ValueError("seed must not be negative")
        if not self.target_object_id.strip() or not self.target_id.strip():
            raise ValueError("target identities must not be empty")
        if self.success and not self.steps:
            raise ValueError("successful evidence must include grounded steps")

    @property
    def has_push_success(self) -> bool:
        """Return whether this episode contains a grounded successful push."""
        return any(
            step.action is PrimitiveAction.PUSH and step.outcome == "pushed" and step.world_changed
            for step in self.steps
        )

    @property
    def has_approach_contact_push_sequence(self) -> bool:
        """Return whether approach, contact, and push behaviors all appear."""
        actions = tuple(step.action for step in self.steps)
        return (
            PrimitiveAction.MOVE_FORWARD in actions
            and PrimitiveAction.PUSH in actions
            and self.has_push_success
        )

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "episode_id": self.episode_id,
            "seed": self.seed,
            "source": self.source.value,
            "steps": [step.to_json() for step in self.steps],
            "success": self.success,
            "target_id": self.target_id,
            "target_object_id": self.target_object_id,
            "used_for_evaluation": self.used_for_evaluation,
        }


@dataclass(frozen=True, slots=True)
class SkillRecord:
    """Compiled main SeedMind reusable skill."""

    skill_id: str
    name: str
    version: str
    schema_version: int
    provenance_episode_ids: tuple[str, ...]
    provenance_seeds: tuple[int, ...]
    preconditions: tuple[str, ...]
    primitive_policy: str
    expected_outcome: str
    termination_conditions: tuple[str, ...]
    failure_conditions: tuple[str, ...]
    success_evidence_count: int
    attempt_evidence_count: int
    compilation_threshold: int
    reuse_count: int
    discovery_count: int
    last_validation_status: SkillValidationStatus
    deterministic_snapshot: dict[str, object]

    def __post_init__(self) -> None:
        if self.schema_version != SKILL_SCHEMA_VERSION:
            raise ValueError("unsupported skill schema version")
        if self.name != "approach_and_push":
            raise ValueError("Week 8 skill name must be approach_and_push")
        if not self.skill_id.strip() or not self.version.strip():
            raise ValueError("skill identity and version must not be empty")
        if self.success_evidence_count < self.compilation_threshold:
            raise ValueError("success evidence count is below compilation threshold")
        if self.attempt_evidence_count < self.success_evidence_count:
            raise ValueError("attempt evidence count cannot be below success evidence count")
        if self.reuse_count < 0 or self.discovery_count < 0:
            raise ValueError("skill counters must not be negative")
        if not self.preconditions or not self.termination_conditions or not self.failure_conditions:
            raise ValueError("skill conditions must be explicit")

    def with_reuse(self, count: int = 1) -> SkillRecord:
        """Return a copy with the reuse counter incremented."""
        if count <= 0:
            raise ValueError("reuse increment must be positive")
        return replace(self, reuse_count=self.reuse_count + count)

    def with_validation_status(self, status: SkillValidationStatus) -> SkillRecord:
        """Return a copy with updated validation status."""
        return replace(self, last_validation_status=status)

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "attempt_evidence_count": self.attempt_evidence_count,
            "compilation_threshold": self.compilation_threshold,
            "deterministic_snapshot": self.deterministic_snapshot,
            "discovery_count": self.discovery_count,
            "expected_outcome": self.expected_outcome,
            "failure_conditions": list(self.failure_conditions),
            "last_validation_status": self.last_validation_status.value,
            "name": self.name,
            "preconditions": list(self.preconditions),
            "primitive_policy": self.primitive_policy,
            "provenance_episode_ids": list(self.provenance_episode_ids),
            "provenance_seeds": list(self.provenance_seeds),
            "reuse_count": self.reuse_count,
            "schema_version": self.schema_version,
            "skill_id": self.skill_id,
            "success_evidence_count": self.success_evidence_count,
            "termination_conditions": list(self.termination_conditions),
            "version": self.version,
        }

    @classmethod
    def from_json(cls, payload: dict[str, Any]) -> SkillRecord:
        """Load a skill record and reject partial or incompatible data."""
        required = {
            "attempt_evidence_count",
            "compilation_threshold",
            "deterministic_snapshot",
            "discovery_count",
            "expected_outcome",
            "failure_conditions",
            "last_validation_status",
            "name",
            "preconditions",
            "primitive_policy",
            "provenance_episode_ids",
            "provenance_seeds",
            "reuse_count",
            "schema_version",
            "skill_id",
            "success_evidence_count",
            "termination_conditions",
            "version",
        }
        if set(payload) != required:
            raise ValueError("skill record fields do not match the supported schema")
        return cls(
            skill_id=str(payload["skill_id"]),
            name=str(payload["name"]),
            version=str(payload["version"]),
            schema_version=int(payload["schema_version"]),
            provenance_episode_ids=tuple(str(value) for value in payload["provenance_episode_ids"]),
            provenance_seeds=tuple(int(value) for value in payload["provenance_seeds"]),
            preconditions=tuple(str(value) for value in payload["preconditions"]),
            primitive_policy=str(payload["primitive_policy"]),
            expected_outcome=str(payload["expected_outcome"]),
            termination_conditions=tuple(str(value) for value in payload["termination_conditions"]),
            failure_conditions=tuple(str(value) for value in payload["failure_conditions"]),
            success_evidence_count=int(payload["success_evidence_count"]),
            attempt_evidence_count=int(payload["attempt_evidence_count"]),
            compilation_threshold=int(payload["compilation_threshold"]),
            reuse_count=int(payload["reuse_count"]),
            discovery_count=int(payload["discovery_count"]),
            last_validation_status=SkillValidationStatus(str(payload["last_validation_status"])),
            deterministic_snapshot=dict(payload["deterministic_snapshot"]),
        )


@dataclass(frozen=True, slots=True)
class SkillCompileResult:
    """Result of trying to compile a skill from episode evidence."""

    record: SkillRecord | None
    failure: SkillCompileFailure | None

    @property
    def compiled(self) -> bool:
        """Return whether compilation succeeded."""
        return self.record is not None

    def __post_init__(self) -> None:
        if (self.record is None) == (self.failure is None):
            raise ValueError("compile result must contain exactly one outcome")


def write_skill_record(record: SkillRecord, path: Path) -> None:
    """Atomically write a deterministic ASCII skill record."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(record.to_json(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def read_skill_record(path: Path) -> SkillRecord:
    """Read a deterministic skill record, rejecting partial acceptance."""
    payload = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(payload, dict):
        raise ValueError("skill record payload must be an object")
    return SkillRecord.from_json(payload)
