"""Versioned persistence contracts for bounded NDNRA consolidation state."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from math import isfinite

from seedmind.research.ndnra.consolidation import ConsolidationCandidate
from seedmind.research.ndnra.consolidation_application import (
    ConsolidationApplicationResult,
    ConsolidationApplicationState,
    ConsolidationStateSnapshot,
    ConsolidationStructureState,
)
from seedmind.research.ndnra.consolidation_reopening import (
    ConsolidationReopeningTrigger,
    ConsolidationRollbackResult,
)
from seedmind.research.ndnra.contextual_memory import LessonIdentity, MasteryProfile


@dataclass(frozen=True, slots=True)
class ConsolidationRollbackAuditRecord:
    """Compact immutable evidence for one completed consolidation rollback."""

    rollback_id: str
    candidate_id: str
    triggers: tuple[ConsolidationReopeningTrigger, ...]
    new_contradiction_event_ids: tuple[str, ...]
    new_independent_contradiction_count: int
    causal_consistency_drop: float
    mastery_score_drop: float
    before: ConsolidationStateSnapshot
    after: ConsolidationStateSnapshot

    def __post_init__(self) -> None:
        _validate_code("rollback_id", self.rollback_id)
        _validate_code("candidate_id", self.candidate_id)
        expected_triggers = tuple(
            trigger for trigger in ConsolidationReopeningTrigger if trigger in self.triggers
        )
        if self.triggers != expected_triggers or len(self.triggers) != len(set(self.triggers)):
            raise ValueError("rollback triggers must be unique and stably ordered")
        _validate_sorted_unique_codes(
            "new_contradiction_event_ids",
            self.new_contradiction_event_ids,
        )
        if (
            not 0
            < self.new_independent_contradiction_count
            <= len(self.new_contradiction_event_ids)
        ):
            raise ValueError("rollback audit requires bounded contradiction evidence")
        required = ConsolidationReopeningTrigger.NEW_INDEPENDENT_CONTRADICTION
        degradation = {
            ConsolidationReopeningTrigger.CAUSAL_CONSISTENCY_DROP,
            ConsolidationReopeningTrigger.MASTERY_SCORE_DROP,
            ConsolidationReopeningTrigger.BROAD_MASTERY_LOST,
        }
        if required not in self.triggers or not degradation.intersection(self.triggers):
            raise ValueError("rollback audit requires contradiction and degradation triggers")
        _validate_unit("causal_consistency_drop", self.causal_consistency_drop)
        _validate_unit("mastery_score_drop", self.mastery_score_drop)
        if self.candidate_id not in self.before.applied_candidate_ids:
            raise ValueError("rollback candidate must be applied in the before snapshot")
        if self.candidate_id in self.after.applied_candidate_ids:
            raise ValueError("rollback candidate must be absent from the after snapshot")
        if _state_identity_sets(self.before) != _state_identity_sets(self.after):
            raise ValueError("rollback audit must preserve registered identities")

    @classmethod
    def from_result(
        cls,
        result: ConsolidationRollbackResult,
    ) -> ConsolidationRollbackAuditRecord:
        """Capture non-executable audit evidence from one rollback result."""
        decision = result.decision
        return cls(
            rollback_id=result.rollback_id,
            candidate_id=result.candidate.candidate_id,
            triggers=decision.triggers,
            new_contradiction_event_ids=decision.new_contradiction_event_ids,
            new_independent_contradiction_count=(decision.new_independent_contradiction_count),
            causal_consistency_drop=decision.causal_consistency_drop,
            mastery_score_drop=decision.mastery_score_drop,
            before=result.before,
            after=result.after,
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic rollback audit evidence."""
        return {
            "rollback_id": self.rollback_id,
            "candidate_id": self.candidate_id,
            "triggers": [trigger.value for trigger in self.triggers],
            "new_contradiction_event_ids": list(self.new_contradiction_event_ids),
            "new_independent_contradiction_count": (self.new_independent_contradiction_count),
            "causal_consistency_drop": self.causal_consistency_drop,
            "mastery_score_drop": self.mastery_score_drop,
            "before": self.before.snapshot(),
            "after": self.after.snapshot(),
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ConsolidationRollbackAuditRecord:
        values = _require_mapping("consolidation rollback audit", snapshot)
        record = cls(
            rollback_id=_require_string(values, "rollback_id"),
            candidate_id=_require_string(values, "candidate_id"),
            triggers=tuple(
                ConsolidationReopeningTrigger(value)
                for value in _require_string_list(values, "triggers")
            ),
            new_contradiction_event_ids=tuple(
                _require_string_list(values, "new_contradiction_event_ids")
            ),
            new_independent_contradiction_count=_require_int(
                values,
                "new_independent_contradiction_count",
            ),
            causal_consistency_drop=_require_float(
                values,
                "causal_consistency_drop",
            ),
            mastery_score_drop=_require_float(values, "mastery_score_drop"),
            before=_restore_state_snapshot(values.get("before")),
            after=_restore_state_snapshot(values.get("after")),
        )
        if record.snapshot() != dict(values):
            raise ValueError("rollback audit did not round-trip exactly")
        return record


@dataclass(frozen=True, slots=True)
class NDNRAConsolidationCheckpoint:
    """Persistent bounded state and evidence required for safe reversal."""

    state: ConsolidationStateSnapshot | None = None
    active_applications: tuple[ConsolidationApplicationResult, ...] = ()
    rollback_records: tuple[ConsolidationRollbackAuditRecord, ...] = ()

    def __post_init__(self) -> None:
        application_ids = tuple(
            application.candidate.candidate_id for application in self.active_applications
        )
        if application_ids != tuple(sorted(application_ids)):
            raise ValueError("active applications must use stable candidate ordering")
        if len(application_ids) != len(set(application_ids)):
            raise ValueError("active application candidate identifiers must be unique")
        rollback_ids = tuple(record.rollback_id for record in self.rollback_records)
        if rollback_ids != tuple(sorted(rollback_ids)):
            raise ValueError("rollback records must use stable rollback ordering")
        if len(rollback_ids) != len(set(rollback_ids)):
            raise ValueError("rollback identifiers must be unique")
        if self.state is None:
            if self.active_applications or self.rollback_records:
                raise ValueError("non-empty consolidation history requires a state snapshot")
            return
        if tuple(sorted(application_ids)) != self.state.applied_candidate_ids:
            raise ValueError("active applications must exactly match applied candidate state")
        expected_identities = _state_identity_sets(self.state)
        for application in self.active_applications:
            if _state_identity_sets(application.before) != expected_identities:
                raise ValueError("application before-state identities do not match checkpoint")
            if _state_identity_sets(application.after) != expected_identities:
                raise ValueError("application after-state identities do not match checkpoint")
        for record in self.rollback_records:
            if _state_identity_sets(record.before) != expected_identities:
                raise ValueError("rollback before-state identities do not match checkpoint")
            if _state_identity_sets(record.after) != expected_identities:
                raise ValueError("rollback after-state identities do not match checkpoint")

    @classmethod
    def empty(cls) -> NDNRAConsolidationCheckpoint:
        """Return the explicit migration target for schemas without consolidation."""
        return cls()

    def application_state(self) -> ConsolidationApplicationState | None:
        """Reconstruct mutable bounded state without invoking cognition."""
        if self.state is None:
            return None
        return ConsolidationApplicationState.from_snapshot(self.state)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic checkpoint contents."""
        return {
            "state": None if self.state is None else self.state.snapshot(),
            "active_applications": [
                _application_snapshot(application) for application in self.active_applications
            ],
            "rollback_records": [record.snapshot() for record in self.rollback_records],
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> NDNRAConsolidationCheckpoint:
        values = _require_mapping("consolidation checkpoint", snapshot)
        raw_state = values.get("state")
        state = None if raw_state is None else _restore_state_snapshot(raw_state)
        checkpoint = cls(
            state=state,
            active_applications=tuple(
                sorted(
                    (
                        _restore_application(item)
                        for item in _require_list(values, "active_applications")
                    ),
                    key=lambda application: application.candidate.candidate_id,
                )
            ),
            rollback_records=tuple(
                sorted(
                    (
                        ConsolidationRollbackAuditRecord.from_snapshot(item)
                        for item in _require_list(values, "rollback_records")
                    ),
                    key=lambda record: record.rollback_id,
                )
            ),
        )
        if checkpoint.snapshot() != dict(values):
            raise ValueError("consolidation checkpoint did not round-trip exactly")
        return checkpoint


def restore_consolidation_application(
    snapshot: object,
) -> ConsolidationApplicationResult:
    """Restore one exact application result for another versioned codec."""
    return _restore_application(snapshot)


def restore_consolidation_state_snapshot(
    snapshot: object,
) -> ConsolidationStateSnapshot:
    """Restore one exact consolidation state snapshot for another versioned codec."""
    return _restore_state_snapshot(snapshot)


def _application_snapshot(
    application: ConsolidationApplicationResult,
) -> dict[str, object]:
    return {
        "candidate": application.candidate.snapshot(),
        "before": application.before.snapshot(),
        "after": application.after.snapshot(),
    }


def _restore_application(snapshot: object) -> ConsolidationApplicationResult:
    values = _require_mapping("consolidation application", snapshot)
    application = ConsolidationApplicationResult(
        candidate=_restore_candidate(values.get("candidate")),
        before=_restore_state_snapshot(values.get("before")),
        after=_restore_state_snapshot(values.get("after")),
    )
    if _application_snapshot(application) != dict(values):
        raise ValueError("consolidation application did not round-trip exactly")
    return application


def _restore_candidate(snapshot: object) -> ConsolidationCandidate:
    values = _require_mapping("consolidation candidate", snapshot)
    lesson_values = _require_mapping("lesson identity", values.get("lesson_identity"))
    candidate = ConsolidationCandidate(
        candidate_id=_require_string(values, "candidate_id"),
        lesson_identity=LessonIdentity(
            need_code=_require_string(lesson_values, "need_code"),
            effect_code=_require_string(lesson_values, "effect_code"),
            desired_direction=_require_float(lesson_values, "desired_direction"),
        ),
        source_event_ids=tuple(_require_string_list(values, "source_event_ids")),
        assembly_ids=tuple(_require_string_list(values, "assembly_ids")),
        route_ids=tuple(_require_string_list(values, "route_ids")),
        mastery_snapshot=_restore_mastery_profile(values.get("mastery_snapshot")),
        requested_stability_increment=_require_float(
            values,
            "requested_stability_increment",
        ),
        requested_plasticity_reduction=_require_float(
            values,
            "requested_plasticity_reduction",
        ),
    )
    if candidate.mastery_snapshot.source_event_ids != candidate.source_event_ids:
        raise ValueError("candidate mastery sources must match candidate sources")
    if not candidate.mastery_snapshot.broad_mastery:
        raise ValueError("persisted consolidation candidate must preserve broad mastery")
    if candidate.mastery_snapshot.contradiction_count != 0:
        raise ValueError("persisted consolidation candidate must start contradiction-free")
    if candidate.snapshot() != dict(values):
        raise ValueError("consolidation candidate did not round-trip exactly")
    return candidate


def _restore_mastery_profile(snapshot: object) -> MasteryProfile:
    values = _require_mapping("mastery profile", snapshot)
    profile = MasteryProfile(
        raw_repetition_count=_require_nonnegative_int(values, "raw_repetition_count"),
        effective_support=_require_nonnegative_float(values, "effective_support"),
        unique_context_count=_require_nonnegative_int(values, "unique_context_count"),
        unique_route_count=_require_nonnegative_int(values, "unique_route_count"),
        contradiction_count=_require_nonnegative_int(values, "contradiction_count"),
        repetition_strength=_require_unit(values, "repetition_strength"),
        context_diversity=_require_unit(values, "context_diversity"),
        route_diversity=_require_unit(values, "route_diversity"),
        causal_consistency=_require_unit(values, "causal_consistency"),
        transfer_success=_require_unit(values, "transfer_success"),
        protective_strength=_require_unit(values, "protective_strength"),
        mastery_score=_require_unit(values, "mastery_score"),
        broad_mastery=_require_bool(values, "broad_mastery"),
        source_event_ids=tuple(_require_string_list(values, "source_event_ids")),
    )
    _validate_sorted_unique_codes("source_event_ids", profile.source_event_ids)
    if profile.snapshot() != dict(values):
        raise ValueError("mastery profile did not round-trip exactly")
    return profile


def _restore_state_snapshot(snapshot: object) -> ConsolidationStateSnapshot:
    values = _require_mapping("consolidation state", snapshot)
    restored = ConsolidationStateSnapshot(
        assembly_states=tuple(
            _restore_structure_state(item) for item in _require_list(values, "assembly_states")
        ),
        route_states=tuple(
            _restore_structure_state(item) for item in _require_list(values, "route_states")
        ),
        applied_candidate_ids=tuple(_require_string_list(values, "applied_candidate_ids")),
    )
    if restored.snapshot() != dict(values):
        raise ValueError("consolidation state did not round-trip exactly")
    return restored


def _restore_structure_state(snapshot: object) -> ConsolidationStructureState:
    values = _require_mapping("consolidation structure state", snapshot)
    restored = ConsolidationStructureState(
        structure_id=_require_string(values, "structure_id"),
        stability=_require_float(values, "stability"),
        plasticity=_require_float(values, "plasticity"),
    )
    if restored.snapshot() != dict(values):
        raise ValueError("consolidation structure state did not round-trip exactly")
    return restored


def _state_identity_sets(
    state: ConsolidationStateSnapshot,
) -> tuple[frozenset[str], frozenset[str]]:
    return (
        frozenset(item.structure_id for item in state.assembly_states),
        frozenset(item.structure_id for item in state.route_states),
    )


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_list(values: Mapping[str, object], key: str) -> list[object]:
    value = values.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_nonnegative_int(values: Mapping[str, object], key: str) -> int:
    value = _require_int(values, key)
    if value < 0:
        raise ValueError(f"{key} must not be negative")
    return value


def _require_float(values: Mapping[str, object], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{key} must be finite")
    return result


def _require_nonnegative_float(values: Mapping[str, object], key: str) -> float:
    value = _require_float(values, key)
    if value < 0.0:
        raise ValueError(f"{key} must not be negative")
    return value


def _require_unit(values: Mapping[str, object], key: str) -> float:
    value = _require_float(values, key)
    _validate_unit(key, value)
    return value


def _require_string_list(values: Mapping[str, object], key: str) -> list[str]:
    result: list[str] = []
    for item in _require_list(values, key):
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain strings")
        result.append(item)
    return result


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
    for value in values:
        _validate_code(name, value)


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between zero and one")
