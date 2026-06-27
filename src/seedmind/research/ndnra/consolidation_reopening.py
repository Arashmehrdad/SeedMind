"""Pure contradiction-driven reopening and atomic consolidation rollback."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.consolidation import ConsolidationCandidate
from seedmind.research.ndnra.consolidation_application import (
    ConsolidationApplicationResult,
    ConsolidationApplicationState,
    ConsolidationStateSnapshot,
    ConsolidationStructureState,
)
from seedmind.research.ndnra.contextual_memory import (
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    MasteryProfile,
)


class ConsolidationReopeningTrigger(StrEnum):
    """Evidence that a previously consolidated lesson should become plastic again."""

    NEW_INDEPENDENT_CONTRADICTION = "new_independent_contradiction"
    CAUSAL_CONSISTENCY_DROP = "causal_consistency_drop"
    MASTERY_SCORE_DROP = "mastery_score_drop"
    BROAD_MASTERY_LOST = "broad_mastery_lost"


@dataclass(frozen=True, slots=True)
class ConsolidationReopeningPolicy:
    """Thresholds for reopening a consolidated lesson after new evidence."""

    minimum_new_contradictions: int = 1
    minimum_causal_consistency_drop: float = 0.10
    minimum_mastery_score_drop: float = 0.05
    reopen_on_broad_mastery_loss: bool = True

    def __post_init__(self) -> None:
        if (
            isinstance(self.minimum_new_contradictions, bool)
            or not isinstance(self.minimum_new_contradictions, int)
            or self.minimum_new_contradictions <= 0
        ):
            raise ValueError("minimum_new_contradictions must be a positive integer")
        _validate_unit(
            "minimum_causal_consistency_drop",
            self.minimum_causal_consistency_drop,
        )
        _validate_unit("minimum_mastery_score_drop", self.minimum_mastery_score_drop)

    def evaluate(
        self,
        *,
        ledger: ContextualExperienceLedger,
        candidate: ConsolidationCandidate,
    ) -> ConsolidationReopeningDecision:
        """Evaluate reopening without mutating evidence or consolidation state."""
        before = candidate.mastery_snapshot
        current = ledger.mastery_profile(candidate.lesson_identity)
        candidate_source_ids = set(candidate.source_event_ids)
        current_source_ids = set(current.source_event_ids)
        if not candidate_source_ids.issubset(current_source_ids):
            raise ValueError("current ledger no longer preserves all consolidation sources")

        for event_id in candidate.source_event_ids:
            trace = ledger.trace(event_id)
            _validate_trace_matches_candidate(trace, candidate)

        new_source_event_ids = tuple(sorted(current_source_ids - candidate_source_ids))
        new_contradiction_event_ids = tuple(
            event_id
            for event_id in new_source_event_ids
            if _trace_is_contradictory(ledger.trace(event_id), candidate)
        )
        contradiction_increase = max(
            0,
            current.contradiction_count - before.contradiction_count,
        )
        causal_consistency_drop = max(
            0.0,
            before.causal_consistency - current.causal_consistency,
        )
        mastery_score_drop = max(0.0, before.mastery_score - current.mastery_score)

        triggers: list[ConsolidationReopeningTrigger] = []
        if contradiction_increase >= self.minimum_new_contradictions:
            triggers.append(ConsolidationReopeningTrigger.NEW_INDEPENDENT_CONTRADICTION)
        if causal_consistency_drop + 1e-12 >= self.minimum_causal_consistency_drop:
            triggers.append(ConsolidationReopeningTrigger.CAUSAL_CONSISTENCY_DROP)
        if mastery_score_drop + 1e-12 >= self.minimum_mastery_score_drop:
            triggers.append(ConsolidationReopeningTrigger.MASTERY_SCORE_DROP)
        if self.reopen_on_broad_mastery_loss and before.broad_mastery and not current.broad_mastery:
            triggers.append(ConsolidationReopeningTrigger.BROAD_MASTERY_LOST)

        ordered_triggers = tuple(
            trigger for trigger in ConsolidationReopeningTrigger if trigger in triggers
        )
        degradation_triggers = {
            ConsolidationReopeningTrigger.CAUSAL_CONSISTENCY_DROP,
            ConsolidationReopeningTrigger.MASTERY_SCORE_DROP,
            ConsolidationReopeningTrigger.BROAD_MASTERY_LOST,
        }
        reopen = bool(
            ConsolidationReopeningTrigger.NEW_INDEPENDENT_CONTRADICTION in ordered_triggers
            and degradation_triggers.intersection(ordered_triggers)
        )
        return ConsolidationReopeningDecision(
            reopen=reopen,
            triggers=ordered_triggers,
            candidate=candidate,
            previous_mastery=before,
            current_mastery=current,
            new_source_event_ids=new_source_event_ids,
            new_contradiction_event_ids=new_contradiction_event_ids,
            new_independent_contradiction_count=contradiction_increase,
            causal_consistency_drop=causal_consistency_drop,
            mastery_score_drop=mastery_score_drop,
            policy=self,
        )


@dataclass(frozen=True, slots=True)
class ConsolidationReopeningDecision:
    """Pure evidence decision for reopening one consolidation candidate."""

    reopen: bool
    triggers: tuple[ConsolidationReopeningTrigger, ...]
    candidate: ConsolidationCandidate
    previous_mastery: MasteryProfile
    current_mastery: MasteryProfile
    new_source_event_ids: tuple[str, ...]
    new_contradiction_event_ids: tuple[str, ...]
    new_independent_contradiction_count: int
    causal_consistency_drop: float
    mastery_score_drop: float
    policy: ConsolidationReopeningPolicy

    def __post_init__(self) -> None:
        if len(self.triggers) != len(set(self.triggers)):
            raise ValueError("reopening triggers must be unique")
        expected_order = tuple(
            trigger for trigger in ConsolidationReopeningTrigger if trigger in self.triggers
        )
        if self.triggers != expected_order:
            raise ValueError("reopening triggers must use stable enum ordering")
        _validate_sorted_unique_codes("new_source_event_ids", self.new_source_event_ids)
        _validate_sorted_unique_codes(
            "new_contradiction_event_ids",
            self.new_contradiction_event_ids,
        )
        if not set(self.new_contradiction_event_ids).issubset(self.new_source_event_ids):
            raise ValueError("contradiction events must be new source events")
        if self.new_independent_contradiction_count < 0:
            raise ValueError("new contradiction count must not be negative")
        _validate_unit("causal_consistency_drop", self.causal_consistency_drop)
        _validate_unit("mastery_score_drop", self.mastery_score_drop)
        required = ConsolidationReopeningTrigger.NEW_INDEPENDENT_CONTRADICTION
        degradation = {
            ConsolidationReopeningTrigger.CAUSAL_CONSISTENCY_DROP,
            ConsolidationReopeningTrigger.MASTERY_SCORE_DROP,
            ConsolidationReopeningTrigger.BROAD_MASTERY_LOST,
        }
        if self.reopen and (
            required not in self.triggers or not degradation.intersection(self.triggers)
        ):
            raise ValueError("reopening requires contradiction and degradation evidence")


@dataclass(frozen=True, slots=True)
class ConsolidationRollbackResult:
    """Immutable audit evidence for one successful targeted rollback."""

    rollback_id: str
    candidate: ConsolidationCandidate
    decision: ConsolidationReopeningDecision
    before: ConsolidationStateSnapshot
    after: ConsolidationStateSnapshot

    def __post_init__(self) -> None:
        _validate_code("rollback_id", self.rollback_id)
        if not self.decision.reopen:
            raise ValueError("rollback requires an affirmative reopening decision")
        if self.decision.candidate != self.candidate:
            raise ValueError("rollback candidate must match reopening decision")
        candidate_id = self.candidate.candidate_id
        if candidate_id not in self.before.applied_candidate_ids:
            raise ValueError("candidate must be applied before rollback")
        if candidate_id in self.after.applied_candidate_ids:
            raise ValueError("candidate must be removed after rollback")
        if _snapshot_ids(self.before.assembly_states) != _snapshot_ids(self.after.assembly_states):
            raise ValueError("rollback must preserve all assembly identities")
        if _snapshot_ids(self.before.route_states) != _snapshot_ids(self.after.route_states):
            raise ValueError("rollback must preserve all route identities")


def rollback_consolidation(
    *,
    state: ConsolidationApplicationState,
    application: ConsolidationApplicationResult,
    decision: ConsolidationReopeningDecision,
) -> ConsolidationRollbackResult:
    """Atomically restore only the reopened candidate's bounded state."""
    candidate = application.candidate
    if not decision.reopen:
        raise RuntimeError("consolidation reopening gate has not passed")
    if decision.candidate != candidate:
        raise ValueError("reopening decision does not match consolidation application")

    current = state.snapshot()
    if candidate.candidate_id not in current.applied_candidate_ids:
        raise RuntimeError("consolidation candidate is not currently applied")
    if not set(application.after.applied_candidate_ids).issubset(current.applied_candidate_ids):
        raise RuntimeError("consolidation application history no longer matches current state")

    updated_assemblies = {item.structure_id: item for item in current.assembly_states}
    updated_routes = {item.structure_id: item for item in current.route_states}
    for assembly_id in candidate.assembly_ids:
        current_state = current.assembly_state(assembly_id)
        expected_state = application.after.assembly_state(assembly_id)
        if current_state != expected_state:
            raise RuntimeError("consolidated assembly changed after application")
        updated_assemblies[assembly_id] = application.before.assembly_state(assembly_id)
    for route_id in candidate.route_ids:
        current_state = current.route_state(route_id)
        expected_state = application.after.route_state(route_id)
        if current_state != expected_state:
            raise RuntimeError("consolidated route changed after application")
        updated_routes[route_id] = application.before.route_state(route_id)

    applied_candidate_ids = set(current.applied_candidate_ids)
    applied_candidate_ids.remove(candidate.candidate_id)
    replacement = ConsolidationStateSnapshot(
        assembly_states=tuple(updated_assemblies[key] for key in sorted(updated_assemblies)),
        route_states=tuple(updated_routes[key] for key in sorted(updated_routes)),
        applied_candidate_ids=tuple(sorted(applied_candidate_ids)),
    )
    result = ConsolidationRollbackResult(
        rollback_id=_rollback_id(candidate, decision, current, replacement),
        candidate=candidate,
        decision=decision,
        before=current,
        after=replacement,
    )
    state.restore_snapshot(expected_current=current, replacement=replacement)
    return result


def _validate_trace_matches_candidate(
    trace: ContextualExperienceTrace,
    candidate: ConsolidationCandidate,
) -> None:
    lesson = candidate.lesson_identity
    if trace.context.active_need_code != lesson.need_code or not any(
        effect.effect_code == lesson.effect_code for effect in trace.observed_effects
    ):
        raise ValueError("consolidation source does not match candidate lesson")


def _trace_is_contradictory(
    trace: ContextualExperienceTrace,
    candidate: ConsolidationCandidate,
) -> bool:
    _validate_trace_matches_candidate(trace, candidate)
    lesson = candidate.lesson_identity
    effect = next(item for item in trace.observed_effects if item.effect_code == lesson.effect_code)
    return effect.value * lesson.desired_direction < 0.0 and effect.confidence > 0.0


def _rollback_id(
    candidate: ConsolidationCandidate,
    decision: ConsolidationReopeningDecision,
    before: ConsolidationStateSnapshot,
    after: ConsolidationStateSnapshot,
) -> str:
    payload = {
        "candidate_id": candidate.candidate_id,
        "triggers": [trigger.value for trigger in decision.triggers],
        "new_contradiction_event_ids": list(decision.new_contradiction_event_ids),
        "before": _snapshot_payload(before),
        "after": _snapshot_payload(after),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"rollback:{hashlib.sha256(canonical).hexdigest()}"


def _snapshot_payload(snapshot: ConsolidationStateSnapshot) -> dict[str, object]:
    return {
        "assembly_states": [_state_payload(item) for item in snapshot.assembly_states],
        "route_states": [_state_payload(item) for item in snapshot.route_states],
        "applied_candidate_ids": list(snapshot.applied_candidate_ids),
    }


def _state_payload(state: ConsolidationStructureState) -> dict[str, object]:
    return {
        "structure_id": state.structure_id,
        "stability": state.stability,
        "plasticity": state.plasticity,
    }


def _snapshot_ids(states: tuple[ConsolidationStructureState, ...]) -> set[str]:
    return {state.structure_id for state in states}


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
