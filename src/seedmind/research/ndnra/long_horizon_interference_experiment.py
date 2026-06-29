"""Deterministic long-horizon mixed-task interference experiment for NDNRA."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.consolidation import (
    ConsolidationCandidate,
    ConsolidationEligibility,
    ConsolidationEligibilityPolicy,
)
from seedmind.research.ndnra.consolidation_application import (
    ConsolidationApplicationState,
    ConsolidationStateSnapshot,
    ConsolidationStructureState,
)
from seedmind.research.ndnra.contextual_memory import (
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EventIdentity,
    LessonIdentity,
    MasteryProfile,
)
from seedmind.research.ndnra.effects import EffectObservation

_SHARED_ASSEMBLY_ID = "assembly:long_horizon_shared"
_OLD_ROUTE_PRIMARY_ID = "route:family_a_primary"
_OLD_ROUTE_TRANSFER_ID = "route:family_a_transfer"
_B_ROUTE_ID = "route:family_b"
_C_ROUTE_ID = "route:family_c"
_OLD_ROUTE_IDS = (_OLD_ROUTE_PRIMARY_ID, _OLD_ROUTE_TRANSFER_ID)
_NOVEL_ROUTE_IDS = (_B_ROUTE_ID, _C_ROUTE_ID)
_ALL_ROUTE_IDS = (*_OLD_ROUTE_IDS, *_NOVEL_ROUTE_IDS)
_A_ASSEMBLY_TARGET = 0.85
_A_ROUTE_TARGET = 0.85
_B_ASSEMBLY_TARGET = -0.85
_B_ROUTE_TARGET = 0.85
_C_ASSEMBLY_TARGET = -0.85
_C_ROUTE_TARGET = -0.85
_FAMILY_A_LESSON = LessonIdentity(
    need_code="retain_family_a",
    effect_code="family_value",
    desired_direction=1.0,
)
_SCHEDULE_PATTERN = (
    "A",
    "B",
    "A",
    "C",
)
_EXPECTED_TIMELINE_LENGTH = 36

_MemoryRouteSnapshot = tuple[tuple[str, float], ...]
_MemorySnapshot = tuple[float, _MemoryRouteSnapshot]
_LedgerSnapshot = str


class LongHorizonInterferenceCondition(StrEnum):
    """Controlled long-horizon retention and adaptability conditions."""

    NO_CONSOLIDATION = "no_consolidation"
    NAIVE_PROTECTION = "naive_protection"
    BOUNDED_RETENTION_REPLAY = "bounded_retention_replay"


class LongHorizonTaskFamily(StrEnum):
    """One mastered old family and two novel switching families."""

    FAMILY_A = "A"
    FAMILY_B = "B"
    FAMILY_C = "C"


@dataclass(frozen=True, slots=True)
class LongHorizonInterferenceConfig:
    """Finite deterministic configuration for Batch 1."""

    learning_rate: float = 0.32
    stability_protection_weight: float = 0.60
    old_training_passes: int = 5
    horizon_steps: int = 36
    retention_threshold: float = 0.72
    maximum_replays_per_learning_step: int = 1
    maximum_total_replays: int = 12
    minimum_old_family_retention_floor: float = 0.72
    minimum_b_family_novel_learning_floor: float = 0.68
    minimum_c_family_novel_learning_floor: float = 0.68
    minimum_joint_score_advantage: float = 0.03

    def __post_init__(self) -> None:
        for name, value in (
            ("learning_rate", self.learning_rate),
            ("stability_protection_weight", self.stability_protection_weight),
            ("retention_threshold", self.retention_threshold),
            ("minimum_old_family_retention_floor", self.minimum_old_family_retention_floor),
            ("minimum_b_family_novel_learning_floor", self.minimum_b_family_novel_learning_floor),
            ("minimum_c_family_novel_learning_floor", self.minimum_c_family_novel_learning_floor),
            ("minimum_joint_score_advantage", self.minimum_joint_score_advantage),
        ):
            _validate_unit(name, value)
        if (
            isinstance(self.old_training_passes, bool)
            or not isinstance(self.old_training_passes, int)
            or self.old_training_passes <= 0
        ):
            raise ValueError("old_training_passes must be a positive integer")
        if (
            isinstance(self.horizon_steps, bool)
            or not isinstance(self.horizon_steps, int)
            or self.horizon_steps != 36
            or self.horizon_steps % 4 != 0
        ):
            raise ValueError("horizon_steps must equal 36 and be divisible by 4")
        if (
            isinstance(self.maximum_replays_per_learning_step, bool)
            or not isinstance(self.maximum_replays_per_learning_step, int)
            or self.maximum_replays_per_learning_step != 1
        ):
            raise ValueError("maximum_replays_per_learning_step must equal 1")
        learning_steps = self.horizon_steps // 2
        if (
            isinstance(self.maximum_total_replays, bool)
            or not isinstance(self.maximum_total_replays, int)
            or self.maximum_total_replays <= 0
            or self.maximum_total_replays > learning_steps
        ):
            raise ValueError(
                "maximum_total_replays must be positive and no greater than total B/C steps"
            )


@dataclass(frozen=True, slots=True)
class LongHorizonStepRecord:
    """Deterministic inspectable record for one horizon step."""

    step_index: int
    task_family: LongHorizonTaskFamily
    probe_only: bool
    learning_applied: bool
    old_family_score_after: float
    b_family_score_after: float
    c_family_score_after: float
    replay_applied: bool
    replay_source_event_id: str | None
    replay_trigger_old_score: float | None
    specialist_count_before: int
    specialist_count_after: int
    structural_growth_operation_count: int
    duplicate_specialist_membership_count: int
    memory_state_before: _MemorySnapshot
    memory_state_after: _MemorySnapshot

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        if self.probe_only == self.learning_applied:
            raise ValueError("exactly one of probe_only or learning_applied must be true")
        for name, value in (
            ("old_family_score_after", self.old_family_score_after),
            ("b_family_score_after", self.b_family_score_after),
            ("c_family_score_after", self.c_family_score_after),
        ):
            _validate_unit(name, value)
        if self.replay_applied:
            if self.probe_only:
                raise ValueError("probe steps must not replay")
            if self.replay_source_event_id is None or self.replay_trigger_old_score is None:
                raise ValueError("replay steps require exact source id and trigger score")
            _validate_code("replay_source_event_id", self.replay_source_event_id)
            _validate_unit("replay_trigger_old_score", self.replay_trigger_old_score)
        elif self.replay_source_event_id is not None or self.replay_trigger_old_score is not None:
            raise ValueError("non-replay steps must not expose replay evidence")
        for name, value in (
            ("specialist_count_before", self.specialist_count_before),
            ("specialist_count_after", self.specialist_count_after),
            ("structural_growth_operation_count", self.structural_growth_operation_count),
            (
                "duplicate_specialist_membership_count",
                self.duplicate_specialist_membership_count,
            ),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if (
            self.specialist_count_before != 0
            or self.specialist_count_after != 0
            or self.structural_growth_operation_count != 0
            or self.duplicate_specialist_membership_count != 0
        ):
            raise ValueError("Batch 1 step records must preserve zero structural counts")
        _validate_memory_snapshot(self.memory_state_before)
        _validate_memory_snapshot(self.memory_state_after)
        if self.probe_only and self.memory_state_before != self.memory_state_after:
            raise ValueError("family A probes must not mutate memory")

    def snapshot(self) -> dict[str, object]:
        return {
            "step_index": self.step_index,
            "task_family": self.task_family.value,
            "probe_only": self.probe_only,
            "learning_applied": self.learning_applied,
            "old_family_score_after": self.old_family_score_after,
            "b_family_score_after": self.b_family_score_after,
            "c_family_score_after": self.c_family_score_after,
            "replay_applied": self.replay_applied,
            "replay_source_event_id": self.replay_source_event_id,
            "replay_trigger_old_score": self.replay_trigger_old_score,
            "specialist_count_before": self.specialist_count_before,
            "specialist_count_after": self.specialist_count_after,
            "structural_growth_operation_count": self.structural_growth_operation_count,
            "duplicate_specialist_membership_count": self.duplicate_specialist_membership_count,
            "memory_state_before": _memory_snapshot_payload(self.memory_state_before),
            "memory_state_after": _memory_snapshot_payload(self.memory_state_after),
        }


@dataclass(frozen=True, slots=True)
class LongHorizonConditionResult:
    """Inspectable evidence for one controlled condition."""

    condition: LongHorizonInterferenceCondition
    consolidation_applied: bool
    initial_old_family_score: float
    initial_b_family_score: float
    initial_c_family_score: float
    final_old_family_score: float
    final_b_family_score: float
    final_c_family_score: float
    old_family_interference: float
    b_family_learning_gain: float
    c_family_learning_gain: float
    joint_score: float
    timeline: tuple[LongHorizonStepRecord, ...]
    replay_count: int
    replay_source_event_ids: tuple[str, ...]
    replay_trigger_scores: tuple[float, ...]
    replay_step_indices: tuple[int, ...]
    maximum_replays_per_learning_step: int
    maximum_total_replays: int
    replay_bound_held: bool
    specialist_count_before: int
    specialist_count_after: int
    structural_growth_operation_count: int
    duplicate_specialist_membership_count: int
    final_memory_state: _MemorySnapshot
    condition_pass_evidence: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("initial_old_family_score", self.initial_old_family_score),
            ("initial_b_family_score", self.initial_b_family_score),
            ("initial_c_family_score", self.initial_c_family_score),
            ("final_old_family_score", self.final_old_family_score),
            ("final_b_family_score", self.final_b_family_score),
            ("final_c_family_score", self.final_c_family_score),
            ("old_family_interference", self.old_family_interference),
            ("b_family_learning_gain", self.b_family_learning_gain),
            ("c_family_learning_gain", self.c_family_learning_gain),
            ("joint_score", self.joint_score),
        ):
            _validate_unit(name, value)
        if len(self.timeline) != _EXPECTED_TIMELINE_LENGTH:
            raise ValueError("timeline must contain exactly 36 deterministic steps")
        if self.replay_count != len(self.replay_source_event_ids):
            raise ValueError("replay_count must match replay_source_event_ids")
        if self.replay_count != len(self.replay_trigger_scores):
            raise ValueError("replay_count must match replay_trigger_scores")
        if self.replay_count != len(self.replay_step_indices):
            raise ValueError("replay_count must match replay_step_indices")
        if (
            isinstance(self.maximum_replays_per_learning_step, bool)
            or not isinstance(self.maximum_replays_per_learning_step, int)
            or self.maximum_replays_per_learning_step != 1
        ):
            raise ValueError("maximum_replays_per_learning_step must equal 1")
        if (
            isinstance(self.maximum_total_replays, bool)
            or not isinstance(self.maximum_total_replays, int)
            or self.maximum_total_replays <= 0
        ):
            raise ValueError("maximum_total_replays must be positive")
        if (
            self.specialist_count_before != 0
            or self.specialist_count_after != 0
            or self.structural_growth_operation_count != 0
            or self.duplicate_specialist_membership_count != 0
        ):
            raise ValueError("Batch 1 conditions must preserve zero structural counts")
        _validate_memory_snapshot(self.final_memory_state)
        _validate_condition_result_semantics(self)

    def snapshot(self) -> dict[str, object]:
        return {
            "condition": self.condition.value,
            "consolidation_applied": self.consolidation_applied,
            "initial_old_family_score": self.initial_old_family_score,
            "initial_b_family_score": self.initial_b_family_score,
            "initial_c_family_score": self.initial_c_family_score,
            "final_old_family_score": self.final_old_family_score,
            "final_b_family_score": self.final_b_family_score,
            "final_c_family_score": self.final_c_family_score,
            "old_family_interference": self.old_family_interference,
            "b_family_learning_gain": self.b_family_learning_gain,
            "c_family_learning_gain": self.c_family_learning_gain,
            "joint_score": self.joint_score,
            "timeline": [record.snapshot() for record in self.timeline],
            "replay_count": self.replay_count,
            "replay_source_event_ids": list(self.replay_source_event_ids),
            "replay_trigger_scores": list(self.replay_trigger_scores),
            "replay_step_indices": list(self.replay_step_indices),
            "maximum_replays_per_learning_step": self.maximum_replays_per_learning_step,
            "maximum_total_replays": self.maximum_total_replays,
            "replay_bound_held": self.replay_bound_held,
            "specialist_count_before": self.specialist_count_before,
            "specialist_count_after": self.specialist_count_after,
            "structural_growth_operation_count": self.structural_growth_operation_count,
            "duplicate_specialist_membership_count": self.duplicate_specialist_membership_count,
            "final_memory_state": _memory_snapshot_payload(self.final_memory_state),
            "condition_pass_evidence": self.condition_pass_evidence,
        }


@dataclass(frozen=True, slots=True)
class LongHorizonInterferenceResult:
    """Aggregate three-condition result with immutable deterministic identity."""

    config: LongHorizonInterferenceConfig
    no_consolidation: LongHorizonConditionResult
    naive_protection: LongHorizonConditionResult
    bounded_retention_replay: LongHorizonConditionResult
    old_family_mastery_profile: MasteryProfile
    consolidation_candidate: ConsolidationCandidate
    source_trace_count_before: int
    source_trace_count_after: int
    source_mastery_profile_after: MasteryProfile
    source_evidence_unchanged: bool
    source_mastery_unchanged: bool
    replay_sources_resolved: bool
    replay_bounded: bool
    structure_unchanged: bool
    action_authority_violation_count: int
    sqlite_used_for_experiment: bool
    action_selection_authority_used: bool
    recommendation_authority_used: bool
    scheduling_authority_used: bool
    execution_authority_used: bool
    live_integration_used: bool
    promotion_authority_used: bool
    production_action_authority_used: bool
    restart_proof_included: bool
    canonical_snapshot: str
    sha256_identity: str
    pass_gate: bool

    def __post_init__(self) -> None:
        if self.source_trace_count_before < 0 or self.source_trace_count_after < 0:
            raise ValueError("source trace counts must not be negative")
        if self.action_authority_violation_count != 0:
            raise ValueError("Batch 1 must report zero authority violations")
        if self.sqlite_used_for_experiment:
            raise ValueError("Batch 1 must not use SQLite cognition")
        for name, value in (
            ("action_selection_authority_used", self.action_selection_authority_used),
            ("recommendation_authority_used", self.recommendation_authority_used),
            ("scheduling_authority_used", self.scheduling_authority_used),
            ("execution_authority_used", self.execution_authority_used),
            ("live_integration_used", self.live_integration_used),
            ("promotion_authority_used", self.promotion_authority_used),
            ("production_action_authority_used", self.production_action_authority_used),
        ):
            if value:
                raise ValueError(f"{name} must remain false in Batch 1")
        if self.restart_proof_included:
            raise ValueError("restart proof must remain deferred to Batch 2")
        if not self.canonical_snapshot.isascii():
            raise ValueError("canonical_snapshot must be ASCII")
        if len(self.sha256_identity) != 64 or any(
            character not in "0123456789abcdef" for character in self.sha256_identity
        ):
            raise ValueError("sha256_identity must be a lowercase SHA-256 hex digest")

    def snapshot_payload(self) -> dict[str, object]:
        return {
            "config": _config_snapshot(self.config),
            "no_consolidation": self.no_consolidation.snapshot(),
            "naive_protection": self.naive_protection.snapshot(),
            "bounded_retention_replay": self.bounded_retention_replay.snapshot(),
            "old_family_mastery_profile": self.old_family_mastery_profile.snapshot(),
            "consolidation_candidate": self.consolidation_candidate.snapshot(),
            "source_trace_count_before": self.source_trace_count_before,
            "source_trace_count_after": self.source_trace_count_after,
            "source_mastery_profile_after": self.source_mastery_profile_after.snapshot(),
            "source_evidence_unchanged": self.source_evidence_unchanged,
            "source_mastery_unchanged": self.source_mastery_unchanged,
            "replay_sources_resolved": self.replay_sources_resolved,
            "replay_bounded": self.replay_bounded,
            "structure_unchanged": self.structure_unchanged,
            "action_authority_violation_count": self.action_authority_violation_count,
            "sqlite_used_for_experiment": self.sqlite_used_for_experiment,
            "action_selection_authority_used": self.action_selection_authority_used,
            "recommendation_authority_used": self.recommendation_authority_used,
            "scheduling_authority_used": self.scheduling_authority_used,
            "execution_authority_used": self.execution_authority_used,
            "live_integration_used": self.live_integration_used,
            "promotion_authority_used": self.promotion_authority_used,
            "production_action_authority_used": self.production_action_authority_used,
            "restart_proof_included": self.restart_proof_included,
            "pass_gate": self.pass_gate,
        }


@dataclass(frozen=True, slots=True)
class LongHorizonInterferenceEvidence:
    """Result plus immutable source and protection evidence."""

    result: LongHorizonInterferenceResult
    source_ledger_snapshot: _LedgerSnapshot
    source_ledger_snapshot_after: _LedgerSnapshot
    eligibility: ConsolidationEligibility
    unconsolidated_state: ConsolidationStateSnapshot
    protected_state: ConsolidationStateSnapshot
    old_family_source_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        source_before = _validate_ledger_snapshot(self.source_ledger_snapshot)
        source_after = _validate_ledger_snapshot(self.source_ledger_snapshot_after)
        snapshots_equal = self.source_ledger_snapshot == self.source_ledger_snapshot_after
        if self.result.source_evidence_unchanged != snapshots_equal:
            raise ValueError(
                "evidence before/after source snapshots must match unchanged-evidence flag exactly"
            )
        before_count = source_before.get("trace_count")
        after_count = source_after.get("trace_count")
        if before_count != self.result.source_trace_count_before:
            raise ValueError("source snapshot before count must match the result")
        if after_count != self.result.source_trace_count_after:
            raise ValueError("source snapshot after count must match the result")
        if not self.eligibility.eligible or self.eligibility.candidate is None:
            raise ValueError("evidence must preserve an eligible consolidation candidate")
        if self.eligibility.candidate != self.result.consolidation_candidate:
            raise ValueError("eligibility candidate must match the result candidate exactly")
        if self.old_family_source_event_ids != self.result.consolidation_candidate.source_event_ids:
            raise ValueError(
                "old_family_source_event_ids must match the candidate source ids exactly"
            )


@dataclass(slots=True)
class _LongHorizonMemory:
    assembly_value: float
    route_values: dict[str, float]

    @classmethod
    def fresh(cls) -> _LongHorizonMemory:
        return cls(assembly_value=0.0, route_values={route_id: 0.0 for route_id in _ALL_ROUTE_IDS})

    @classmethod
    def from_snapshot(cls, snapshot: _MemorySnapshot) -> _LongHorizonMemory:
        _validate_memory_snapshot(snapshot)
        assembly_value, route_values = snapshot
        return cls(
            assembly_value=float(assembly_value),
            route_values={str(route_id): float(value) for route_id, value in route_values},
        )

    def snapshot(self) -> _MemorySnapshot:
        return (
            self.assembly_value,
            tuple(
                (route_id, self.route_values[route_id]) for route_id in sorted(self.route_values)
            ),
        )

    def family_score(self, family: LongHorizonTaskFamily) -> float:
        if family is LongHorizonTaskFamily.FAMILY_A:
            route_scores = [
                _pair_score(
                    self.assembly_value,
                    self.route_values[route_id],
                    _A_ASSEMBLY_TARGET,
                    _A_ROUTE_TARGET,
                )
                for route_id in _OLD_ROUTE_IDS
            ]
            return sum(route_scores) / len(route_scores)
        if family is LongHorizonTaskFamily.FAMILY_B:
            return _pair_score(
                self.assembly_value,
                self.route_values[_B_ROUTE_ID],
                _B_ASSEMBLY_TARGET,
                _B_ROUTE_TARGET,
            )
        return _pair_score(
            self.assembly_value,
            self.route_values[_C_ROUTE_ID],
            _C_ASSEMBLY_TARGET,
            _C_ROUTE_TARGET,
        )

    def learn(
        self,
        *,
        route_id: str,
        assembly_target: float,
        route_target: float,
        consolidation_state: ConsolidationStateSnapshot,
        config: LongHorizonInterferenceConfig,
    ) -> None:
        assembly_state = consolidation_state.assembly_state(_SHARED_ASSEMBLY_ID)
        route_state = consolidation_state.route_state(route_id)
        assembly_rate = _effective_learning_rate(assembly_state, config)
        route_rate = _effective_learning_rate(route_state, config)
        self.assembly_value = _clamp_signed(
            self.assembly_value + assembly_rate * (assembly_target - self.assembly_value)
        )
        self.route_values[route_id] = _clamp_signed(
            self.route_values[route_id] + route_rate * (route_target - self.route_values[route_id])
        )


def run_long_horizon_interference_experiment(
    config: LongHorizonInterferenceConfig | None = None,
) -> LongHorizonInterferenceEvidence:
    """Run the deterministic 36-step three-family Batch 1 experiment."""
    settings = LongHorizonInterferenceConfig() if config is None else config
    ledger = _build_family_a_ledger()
    source_ledger_snapshot = _ledger_snapshot(ledger.snapshot())
    mastery_before = ledger.mastery_profile(_FAMILY_A_LESSON)
    eligibility = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_FAMILY_A_LESSON,
        mastery_profile=mastery_before,
        requested_stability_increment=0.20,
        requested_plasticity_reduction=0.20,
        available_assembly_ids=(_SHARED_ASSEMBLY_ID,),
        available_route_ids=_OLD_ROUTE_IDS,
    )
    if not eligibility.eligible or eligibility.candidate is None:
        raise RuntimeError("family A must be broadly mastered and eligible before the horizon")
    candidate = eligibility.candidate
    source_traces = tuple(ledger.trace(event_id) for event_id in candidate.source_event_ids)
    base_application = ConsolidationApplicationState.from_identifiers(
        assembly_ids=(_SHARED_ASSEMBLY_ID,),
        route_ids=_ALL_ROUTE_IDS,
    )
    unconsolidated_state = base_application.snapshot()
    protected_state = (
        ConsolidationApplicationState.from_identifiers(
            assembly_ids=(_SHARED_ASSEMBLY_ID,),
            route_ids=_ALL_ROUTE_IDS,
        )
        .apply(eligibility)
        .after
    )
    initial_memory = _pretrain_family_a(
        source_traces=source_traces,
        state=unconsolidated_state,
        config=settings,
    )

    no_consolidation = _run_condition(
        condition=LongHorizonInterferenceCondition.NO_CONSOLIDATION,
        initial_memory=initial_memory,
        consolidation_state=unconsolidated_state,
        source_traces=source_traces,
        config=settings,
    )
    naive_protection = _run_condition(
        condition=LongHorizonInterferenceCondition.NAIVE_PROTECTION,
        initial_memory=initial_memory,
        consolidation_state=protected_state,
        source_traces=source_traces,
        config=settings,
    )
    bounded_retention_replay = _run_condition(
        condition=LongHorizonInterferenceCondition.BOUNDED_RETENTION_REPLAY,
        initial_memory=initial_memory,
        consolidation_state=protected_state,
        source_traces=source_traces,
        config=settings,
    )

    mastery_after = ledger.mastery_profile(_FAMILY_A_LESSON)
    source_ledger_snapshot_after = _ledger_snapshot(ledger.snapshot())
    source_trace_count_before = len(candidate.source_event_ids)
    source_trace_count_after = ledger.trace_count
    replay_sources_resolved = _condition_replay_sources_resolved(
        bounded_retention_replay,
        candidate.source_event_ids,
        source_trace_count_after,
    )
    replay_bounded = _condition_replay_bounded(bounded_retention_replay)
    source_evidence_unchanged = source_ledger_snapshot == source_ledger_snapshot_after
    source_mastery_unchanged = mastery_before == mastery_after
    structure_unchanged = all(
        condition.specialist_count_before == 0
        and condition.specialist_count_after == 0
        and condition.structural_growth_operation_count == 0
        and condition.duplicate_specialist_membership_count == 0
        and all(
            step.specialist_count_before == 0
            and step.specialist_count_after == 0
            and step.structural_growth_operation_count == 0
            and step.duplicate_specialist_membership_count == 0
            for step in condition.timeline
        )
        for condition in (no_consolidation, naive_protection, bounded_retention_replay)
    )
    baseline_joint = max(no_consolidation.joint_score, naive_protection.joint_score)
    pass_gate = bool(
        mastery_before.broad_mastery
        and no_consolidation.final_b_family_score >= settings.minimum_b_family_novel_learning_floor
        and no_consolidation.final_c_family_score >= settings.minimum_c_family_novel_learning_floor
        and no_consolidation.old_family_interference >= 0.25
        and naive_protection.final_old_family_score > no_consolidation.final_old_family_score
        and (
            naive_protection.final_b_family_score < no_consolidation.final_b_family_score
            or naive_protection.final_c_family_score < no_consolidation.final_c_family_score
        )
        and bounded_retention_replay.final_old_family_score
        >= settings.minimum_old_family_retention_floor
        and bounded_retention_replay.final_b_family_score
        >= settings.minimum_b_family_novel_learning_floor
        and bounded_retention_replay.final_c_family_score
        >= settings.minimum_c_family_novel_learning_floor
        and bounded_retention_replay.joint_score
        >= baseline_joint + settings.minimum_joint_score_advantage
        and replay_sources_resolved
        and replay_bounded
        and source_evidence_unchanged
        and source_mastery_unchanged
        and structure_unchanged
    )
    provisional = LongHorizonInterferenceResult(
        config=settings,
        no_consolidation=no_consolidation,
        naive_protection=naive_protection,
        bounded_retention_replay=bounded_retention_replay,
        old_family_mastery_profile=mastery_before,
        consolidation_candidate=candidate,
        source_trace_count_before=source_trace_count_before,
        source_trace_count_after=source_trace_count_after,
        source_mastery_profile_after=mastery_after,
        source_evidence_unchanged=source_evidence_unchanged,
        source_mastery_unchanged=source_mastery_unchanged,
        replay_sources_resolved=replay_sources_resolved,
        replay_bounded=replay_bounded,
        structure_unchanged=structure_unchanged,
        action_authority_violation_count=0,
        sqlite_used_for_experiment=False,
        action_selection_authority_used=False,
        recommendation_authority_used=False,
        scheduling_authority_used=False,
        execution_authority_used=False,
        live_integration_used=False,
        promotion_authority_used=False,
        production_action_authority_used=False,
        restart_proof_included=False,
        canonical_snapshot="",
        sha256_identity="0" * 64,
        pass_gate=pass_gate,
    )
    canonical_snapshot = _canonical_snapshot(provisional.snapshot_payload())
    sha256_identity = hashlib.sha256(canonical_snapshot.encode("ascii")).hexdigest()
    result = LongHorizonInterferenceResult(
        config=settings,
        no_consolidation=no_consolidation,
        naive_protection=naive_protection,
        bounded_retention_replay=bounded_retention_replay,
        old_family_mastery_profile=mastery_before,
        consolidation_candidate=candidate,
        source_trace_count_before=source_trace_count_before,
        source_trace_count_after=source_trace_count_after,
        source_mastery_profile_after=mastery_after,
        source_evidence_unchanged=source_evidence_unchanged,
        source_mastery_unchanged=source_mastery_unchanged,
        replay_sources_resolved=replay_sources_resolved,
        replay_bounded=replay_bounded,
        structure_unchanged=structure_unchanged,
        action_authority_violation_count=0,
        sqlite_used_for_experiment=False,
        action_selection_authority_used=False,
        recommendation_authority_used=False,
        scheduling_authority_used=False,
        execution_authority_used=False,
        live_integration_used=False,
        promotion_authority_used=False,
        production_action_authority_used=False,
        restart_proof_included=False,
        canonical_snapshot=canonical_snapshot,
        sha256_identity=sha256_identity,
        pass_gate=pass_gate,
    )
    validate_long_horizon_interference_result(result)
    return LongHorizonInterferenceEvidence(
        result=result,
        source_ledger_snapshot=source_ledger_snapshot,
        source_ledger_snapshot_after=source_ledger_snapshot_after,
        eligibility=eligibility,
        unconsolidated_state=unconsolidated_state,
        protected_state=protected_state,
        old_family_source_event_ids=candidate.source_event_ids,
    )


def validate_long_horizon_interference_result(result: LongHorizonInterferenceResult) -> None:
    """Reject tampered nested records, snapshots, identities, and authority drift."""
    candidate_source_ids = result.consolidation_candidate.source_event_ids
    if result.source_trace_count_before != len(candidate_source_ids):
        raise ValueError("source_trace_count_before must equal candidate source id count")
    for condition in (
        result.no_consolidation,
        result.naive_protection,
        result.bounded_retention_replay,
    ):
        _validate_condition_result_semantics(condition)
        if (
            condition.maximum_replays_per_learning_step
            != result.config.maximum_replays_per_learning_step
            or condition.maximum_total_replays != result.config.maximum_total_replays
        ):
            raise ValueError("condition replay bounds must match the aggregate config")
        for record in condition.timeline:
            if record.replay_applied:
                assert record.replay_source_event_id is not None
                assert record.replay_trigger_old_score is not None
                if record.replay_source_event_id not in candidate_source_ids:
                    raise ValueError(
                        "replay source ids must resolve to exact candidate source events"
                    )
                if record.replay_trigger_old_score >= result.config.retention_threshold:
                    raise ValueError("replay must trigger only below the retention threshold")
    if result.no_consolidation.condition is not LongHorizonInterferenceCondition.NO_CONSOLIDATION:
        raise ValueError("no_consolidation condition identity must remain exact")
    if result.naive_protection.condition is not LongHorizonInterferenceCondition.NAIVE_PROTECTION:
        raise ValueError("naive_protection condition identity must remain exact")
    if (
        result.bounded_retention_replay.condition
        is not LongHorizonInterferenceCondition.BOUNDED_RETENTION_REPLAY
    ):
        raise ValueError("bounded_retention_replay condition identity must remain exact")
    if result.source_mastery_unchanged != (
        result.old_family_mastery_profile == result.source_mastery_profile_after
    ):
        raise ValueError("source_mastery_unchanged must derive from mastery profile equality")
    if result.source_evidence_unchanged != (
        result.source_trace_count_before == result.source_trace_count_after
    ):
        raise ValueError(
            "source_evidence_unchanged must derive from exact source trace-count equality"
        )
    expected_replay_sources_resolved = _condition_replay_sources_resolved(
        result.bounded_retention_replay,
        candidate_source_ids,
        result.source_trace_count_after,
    )
    if result.replay_sources_resolved != expected_replay_sources_resolved:
        raise ValueError("replay_sources_resolved must reconcile exactly with candidate sources")
    expected_replay_bounded = _condition_replay_bounded(result.bounded_retention_replay)
    if result.replay_bounded != expected_replay_bounded:
        raise ValueError("replay_bounded must reconcile exactly with timeline replay records")
    expected_structure_unchanged = all(
        condition.specialist_count_before == 0
        and condition.specialist_count_after == 0
        and condition.structural_growth_operation_count == 0
        and condition.duplicate_specialist_membership_count == 0
        and all(
            step.specialist_count_before == 0
            and step.specialist_count_after == 0
            and step.structural_growth_operation_count == 0
            and step.duplicate_specialist_membership_count == 0
            for step in condition.timeline
        )
        for condition in (
            result.no_consolidation,
            result.naive_protection,
            result.bounded_retention_replay,
        )
    )
    if result.structure_unchanged != expected_structure_unchanged:
        raise ValueError("structure_unchanged must derive from every condition and step")
    baseline_joint = max(result.no_consolidation.joint_score, result.naive_protection.joint_score)
    expected_pass_gate = bool(
        result.old_family_mastery_profile.broad_mastery
        and result.no_consolidation.final_b_family_score
        >= result.config.minimum_b_family_novel_learning_floor
        and result.no_consolidation.final_c_family_score
        >= result.config.minimum_c_family_novel_learning_floor
        and result.no_consolidation.old_family_interference >= 0.25
        and result.naive_protection.final_old_family_score
        > result.no_consolidation.final_old_family_score
        and (
            result.naive_protection.final_b_family_score
            < result.no_consolidation.final_b_family_score
            or result.naive_protection.final_c_family_score
            < result.no_consolidation.final_c_family_score
        )
        and result.bounded_retention_replay.final_old_family_score
        >= result.config.minimum_old_family_retention_floor
        and result.bounded_retention_replay.final_b_family_score
        >= result.config.minimum_b_family_novel_learning_floor
        and result.bounded_retention_replay.final_c_family_score
        >= result.config.minimum_c_family_novel_learning_floor
        and result.bounded_retention_replay.joint_score
        >= baseline_joint + result.config.minimum_joint_score_advantage
        and result.no_consolidation.condition_pass_evidence
        and result.naive_protection.condition_pass_evidence
        and result.bounded_retention_replay.condition_pass_evidence
        and result.replay_sources_resolved
        and result.replay_bounded
        and result.source_evidence_unchanged
        and result.source_mastery_unchanged
        and result.structure_unchanged
    )
    if result.pass_gate != expected_pass_gate:
        raise ValueError("pass_gate must derive exactly from the aggregate pass criteria")
    expected_snapshot = _canonical_snapshot(result.snapshot_payload())
    if result.canonical_snapshot != expected_snapshot:
        raise ValueError("canonical snapshot does not match result content")
    expected_identity = hashlib.sha256(expected_snapshot.encode("ascii")).hexdigest()
    if result.sha256_identity != expected_identity:
        raise ValueError("sha256 identity does not match canonical snapshot")


def _build_family_a_ledger() -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    specifications = (
        (0, _OLD_ROUTE_PRIMARY_ID, (0.10, 0.20), True),
        (1, _OLD_ROUTE_TRANSFER_ID, (0.50, 0.60), True),
        (2, _OLD_ROUTE_PRIMARY_ID, (0.90, 1.00), False),
    )
    for step, route_id, sensors, transfer_succeeded in specifications:
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity("long_horizon_interference", "family_a_mastery", step),
                correlation_group_id=f"group:family_a:{step}",
                assembly_id=_SHARED_ASSEMBLY_ID,
                route_id=route_id,
                action_code="retain_response",
                context=ContextSignature.from_values(
                    active_need_code=_FAMILY_A_LESSON.need_code,
                    sensor_values=sensors,
                    available_action_codes=("retain_response", "switch_response"),
                ),
                observed_effects=(
                    EffectObservation(
                        effect_code=_FAMILY_A_LESSON.effect_code,
                        value=1.0,
                        confidence=1.0,
                    ),
                ),
                transfer_attempted=True,
                transfer_succeeded=transfer_succeeded,
            )
        )
    return ledger


def _pretrain_family_a(
    *,
    source_traces: tuple[ContextualExperienceTrace, ...],
    state: ConsolidationStateSnapshot,
    config: LongHorizonInterferenceConfig,
) -> _MemorySnapshot:
    memory = _LongHorizonMemory.fresh()
    for _ in range(config.old_training_passes):
        for trace in source_traces:
            memory.learn(
                route_id=trace.route_id,
                assembly_target=_A_ASSEMBLY_TARGET,
                route_target=_A_ROUTE_TARGET,
                consolidation_state=state,
                config=config,
            )
    return memory.snapshot()


def _run_condition(
    *,
    condition: LongHorizonInterferenceCondition,
    initial_memory: _MemorySnapshot,
    consolidation_state: ConsolidationStateSnapshot,
    source_traces: tuple[ContextualExperienceTrace, ...],
    config: LongHorizonInterferenceConfig,
) -> LongHorizonConditionResult:
    memory = _LongHorizonMemory.from_snapshot(initial_memory)
    initial_old = memory.family_score(LongHorizonTaskFamily.FAMILY_A)
    initial_b = memory.family_score(LongHorizonTaskFamily.FAMILY_B)
    initial_c = memory.family_score(LongHorizonTaskFamily.FAMILY_C)
    timeline: list[LongHorizonStepRecord] = []
    replay_source_event_ids: list[str] = []
    replay_trigger_scores: list[float] = []
    replay_step_indices: list[int] = []
    replay_cursor = 0

    for step_index in range(config.horizon_steps):
        family = LongHorizonTaskFamily(_SCHEDULE_PATTERN[step_index % len(_SCHEDULE_PATTERN)])
        memory_before = memory.snapshot()
        replay_source_event_id: str | None = None
        replay_trigger_old_score: float | None = None
        replay_applied = False
        if family is LongHorizonTaskFamily.FAMILY_B:
            memory.learn(
                route_id=_B_ROUTE_ID,
                assembly_target=_B_ASSEMBLY_TARGET,
                route_target=_B_ROUTE_TARGET,
                consolidation_state=consolidation_state,
                config=config,
            )
        elif family is LongHorizonTaskFamily.FAMILY_C:
            memory.learn(
                route_id=_C_ROUTE_ID,
                assembly_target=_C_ASSEMBLY_TARGET,
                route_target=_C_ROUTE_TARGET,
                consolidation_state=consolidation_state,
                config=config,
            )
        if (
            family is not LongHorizonTaskFamily.FAMILY_A
            and condition is LongHorizonInterferenceCondition.BOUNDED_RETENTION_REPLAY
        ):
            current_old_score = memory.family_score(LongHorizonTaskFamily.FAMILY_A)
            if (
                current_old_score < config.retention_threshold
                and len(replay_source_event_ids) < config.maximum_total_replays
            ):
                trace = source_traces[replay_cursor % len(source_traces)]
                replay_cursor += 1
                replay_applied = True
                replay_source_event_id = trace.identity.key
                replay_trigger_old_score = current_old_score
                replay_source_event_ids.append(replay_source_event_id)
                replay_trigger_scores.append(current_old_score)
                replay_step_indices.append(step_index)
                memory.learn(
                    route_id=trace.route_id,
                    assembly_target=_A_ASSEMBLY_TARGET,
                    route_target=_A_ROUTE_TARGET,
                    consolidation_state=consolidation_state,
                    config=config,
                )
        timeline.append(
            LongHorizonStepRecord(
                step_index=step_index,
                task_family=family,
                probe_only=family is LongHorizonTaskFamily.FAMILY_A,
                learning_applied=family is not LongHorizonTaskFamily.FAMILY_A,
                old_family_score_after=memory.family_score(LongHorizonTaskFamily.FAMILY_A),
                b_family_score_after=memory.family_score(LongHorizonTaskFamily.FAMILY_B),
                c_family_score_after=memory.family_score(LongHorizonTaskFamily.FAMILY_C),
                replay_applied=replay_applied,
                replay_source_event_id=replay_source_event_id,
                replay_trigger_old_score=replay_trigger_old_score,
                specialist_count_before=0,
                specialist_count_after=0,
                structural_growth_operation_count=0,
                duplicate_specialist_membership_count=0,
                memory_state_before=memory_before,
                memory_state_after=memory.snapshot(),
            )
        )

    final_old = memory.family_score(LongHorizonTaskFamily.FAMILY_A)
    final_b = memory.family_score(LongHorizonTaskFamily.FAMILY_B)
    final_c = memory.family_score(LongHorizonTaskFamily.FAMILY_C)
    timeline_tuple = tuple(timeline)
    final_memory_state = memory.snapshot()
    consolidation_applied = condition is not LongHorizonInterferenceCondition.NO_CONSOLIDATION
    replay_count = len(replay_source_event_ids)
    replay_source_event_ids_tuple = tuple(replay_source_event_ids)
    replay_trigger_scores_tuple = tuple(replay_trigger_scores)
    replay_step_indices_tuple = tuple(replay_step_indices)
    return LongHorizonConditionResult(
        condition=condition,
        consolidation_applied=consolidation_applied,
        initial_old_family_score=initial_old,
        initial_b_family_score=initial_b,
        initial_c_family_score=initial_c,
        final_old_family_score=final_old,
        final_b_family_score=final_b,
        final_c_family_score=final_c,
        old_family_interference=max(0.0, initial_old - final_old),
        b_family_learning_gain=max(0.0, final_b - initial_b),
        c_family_learning_gain=max(0.0, final_c - initial_c),
        joint_score=min(final_old, final_b, final_c),
        timeline=timeline_tuple,
        replay_count=replay_count,
        replay_source_event_ids=replay_source_event_ids_tuple,
        replay_trigger_scores=replay_trigger_scores_tuple,
        replay_step_indices=replay_step_indices_tuple,
        maximum_replays_per_learning_step=config.maximum_replays_per_learning_step,
        maximum_total_replays=config.maximum_total_replays,
        replay_bound_held=_condition_integrity_predicate(
            condition=condition,
            consolidation_applied=consolidation_applied,
            timeline=timeline_tuple,
            replay_count=replay_count,
            replay_source_event_ids=replay_source_event_ids_tuple,
            replay_trigger_scores=replay_trigger_scores_tuple,
            replay_step_indices=replay_step_indices_tuple,
            maximum_replays_per_learning_step=config.maximum_replays_per_learning_step,
            maximum_total_replays=config.maximum_total_replays,
            final_memory_state=final_memory_state,
        )
        and _condition_replay_bounded_from_summary(
            timeline=timeline_tuple,
            replay_count=replay_count,
            replay_step_indices=replay_step_indices_tuple,
            maximum_replays_per_learning_step=config.maximum_replays_per_learning_step,
            maximum_total_replays=config.maximum_total_replays,
        ),
        specialist_count_before=0,
        specialist_count_after=0,
        structural_growth_operation_count=0,
        duplicate_specialist_membership_count=0,
        final_memory_state=final_memory_state,
        condition_pass_evidence=_condition_integrity_predicate(
            condition=condition,
            consolidation_applied=consolidation_applied,
            timeline=timeline_tuple,
            replay_count=replay_count,
            replay_source_event_ids=replay_source_event_ids_tuple,
            replay_trigger_scores=replay_trigger_scores_tuple,
            replay_step_indices=replay_step_indices_tuple,
            maximum_replays_per_learning_step=config.maximum_replays_per_learning_step,
            maximum_total_replays=config.maximum_total_replays,
            final_memory_state=final_memory_state,
        ),
    )


def _effective_learning_rate(
    structure_state: ConsolidationStructureState,
    config: LongHorizonInterferenceConfig,
) -> float:
    return (
        config.learning_rate
        * structure_state.plasticity
        * (1.0 - config.stability_protection_weight * structure_state.stability)
    )


def _pair_score(
    assembly_value: float,
    route_value: float,
    assembly_target: float,
    route_target: float,
) -> float:
    return max(
        0.0,
        1.0 - (abs(assembly_target - assembly_value) + abs(route_target - route_value)) / 4.0,
    )


def _canonical_snapshot(payload: dict[str, object]) -> str:
    text = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    if not text.isascii():
        raise ValueError("canonical snapshot must serialize to ASCII")
    return text


def _config_snapshot(config: LongHorizonInterferenceConfig) -> dict[str, object]:
    return {
        "learning_rate": config.learning_rate,
        "stability_protection_weight": config.stability_protection_weight,
        "old_training_passes": config.old_training_passes,
        "horizon_steps": config.horizon_steps,
        "retention_threshold": config.retention_threshold,
        "maximum_replays_per_learning_step": config.maximum_replays_per_learning_step,
        "maximum_total_replays": config.maximum_total_replays,
        "minimum_old_family_retention_floor": config.minimum_old_family_retention_floor,
        "minimum_b_family_novel_learning_floor": config.minimum_b_family_novel_learning_floor,
        "minimum_c_family_novel_learning_floor": config.minimum_c_family_novel_learning_floor,
        "minimum_joint_score_advantage": config.minimum_joint_score_advantage,
    }


def _validate_memory_snapshot(snapshot: _MemorySnapshot) -> None:
    if not isinstance(snapshot, tuple) or len(snapshot) != 2:
        raise ValueError(
            "memory snapshot must be an immutable (assembly_value, route_values) tuple"
        )
    assembly_value, route_values = snapshot
    _validate_signed("assembly_value", assembly_value)
    if not isinstance(route_values, tuple):
        raise ValueError("route_values must be an immutable tuple")
    route_ids: list[str] = []
    for item in route_values:
        if not isinstance(item, tuple) or len(item) != 2:
            raise ValueError("route_values must contain immutable (route_id, value) pairs")
        route_id, value = item
        if not isinstance(route_id, str):
            raise ValueError("route id must be a string")
        _validate_code("route_id", route_id)
        _validate_signed("route_value", value)
        route_ids.append(route_id)
    if tuple(route_ids) != tuple(sorted(route_ids)):
        raise ValueError("route_values must use stable sorted route ordering")
    if tuple(route_ids) != _ALL_ROUTE_IDS:
        raise ValueError("memory snapshot must include every route exactly once")


def _memory_snapshot_payload(snapshot: _MemorySnapshot) -> dict[str, object]:
    assembly_value, route_values = snapshot
    return {
        "assembly_value": assembly_value,
        "route_values": [[route_id, value] for route_id, value in route_values],
    }


def _ledger_snapshot(snapshot: dict[str, object]) -> _LedgerSnapshot:
    return _canonical_snapshot(snapshot)


def _validate_ledger_snapshot(snapshot: _LedgerSnapshot) -> dict[str, object]:
    if not isinstance(snapshot, str) or not snapshot.isascii():
        raise ValueError("source ledger snapshot must be canonical ASCII JSON")
    try:
        payload = json.loads(snapshot)
    except json.JSONDecodeError as error:
        raise ValueError("source ledger snapshot must be valid JSON") from error
    if not isinstance(payload, dict):
        raise ValueError("source ledger snapshot must contain a JSON object")
    if _canonical_snapshot(payload) != snapshot:
        raise ValueError("source ledger snapshot must use canonical JSON encoding")
    return payload


def _memory_family_score(snapshot: _MemorySnapshot, family: LongHorizonTaskFamily) -> float:
    return _LongHorizonMemory.from_snapshot(snapshot).family_score(family)


def _condition_expected_consolidation(
    condition: LongHorizonInterferenceCondition,
) -> bool:
    return condition is not LongHorizonInterferenceCondition.NO_CONSOLIDATION


def _condition_replay_bounded_from_summary(
    *,
    timeline: tuple[LongHorizonStepRecord, ...],
    replay_count: int,
    replay_step_indices: tuple[int, ...],
    maximum_replays_per_learning_step: int,
    maximum_total_replays: int,
) -> bool:
    timeline_replay_indices = tuple(step.step_index for step in timeline if step.replay_applied)
    return bool(
        replay_count == len(timeline_replay_indices)
        and replay_step_indices == timeline_replay_indices
        and len(set(replay_step_indices)) == len(replay_step_indices)
        and replay_count <= maximum_total_replays
        and all(
            replay_step_indices.count(step_index) <= maximum_replays_per_learning_step
            for step_index in replay_step_indices
        )
        and all(
            step.task_family is not LongHorizonTaskFamily.FAMILY_A
            for step in timeline
            if step.replay_applied
        )
    )


def _condition_replay_bounded(condition: LongHorizonConditionResult) -> bool:
    return (
        _condition_replay_bounded_from_summary(
            timeline=condition.timeline,
            replay_count=condition.replay_count,
            replay_step_indices=condition.replay_step_indices,
            maximum_replays_per_learning_step=condition.maximum_replays_per_learning_step,
            maximum_total_replays=condition.maximum_total_replays,
        )
        and condition.replay_source_event_ids
        == tuple(step.replay_source_event_id for step in condition.timeline if step.replay_applied)
        and condition.replay_trigger_scores
        == tuple(
            step.replay_trigger_old_score for step in condition.timeline if step.replay_applied
        )
    )


def _condition_replay_sources_resolved(
    condition: LongHorizonConditionResult,
    candidate_source_ids: tuple[str, ...],
    source_trace_count_after: int,
) -> bool:
    candidate_source_set = set(candidate_source_ids)
    return bool(
        condition.replay_count > 0
        and source_trace_count_after == len(candidate_source_ids)
        and all(
            source_id in candidate_source_set for source_id in condition.replay_source_event_ids
        )
    )


def _condition_integrity_predicate(
    *,
    condition: LongHorizonInterferenceCondition,
    consolidation_applied: bool,
    timeline: tuple[LongHorizonStepRecord, ...],
    replay_count: int,
    replay_source_event_ids: tuple[str, ...],
    replay_trigger_scores: tuple[float, ...],
    replay_step_indices: tuple[int, ...],
    maximum_replays_per_learning_step: int,
    maximum_total_replays: int,
    final_memory_state: _MemorySnapshot,
) -> bool:
    if len(timeline) != _EXPECTED_TIMELINE_LENGTH:
        return False
    for index, step in enumerate(timeline):
        expected_family = LongHorizonTaskFamily(_SCHEDULE_PATTERN[index % len(_SCHEDULE_PATTERN)])
        if step.step_index != index or step.task_family is not expected_family:
            return False
        expected_probe = expected_family is LongHorizonTaskFamily.FAMILY_A
        if step.probe_only != expected_probe or step.learning_applied == expected_probe:
            return False
        if index > 0 and step.memory_state_before != timeline[index - 1].memory_state_after:
            return False
        if step.old_family_score_after != _memory_family_score(
            step.memory_state_after, LongHorizonTaskFamily.FAMILY_A
        ):
            return False
        if step.b_family_score_after != _memory_family_score(
            step.memory_state_after, LongHorizonTaskFamily.FAMILY_B
        ):
            return False
        if step.c_family_score_after != _memory_family_score(
            step.memory_state_after, LongHorizonTaskFamily.FAMILY_C
        ):
            return False
    baseline_condition = condition is not LongHorizonInterferenceCondition.BOUNDED_RETENTION_REPLAY
    replay_semantics_hold = replay_count == 0 if baseline_condition else replay_count > 0
    return bool(
        consolidation_applied == _condition_expected_consolidation(condition)
        and replay_semantics_hold
        and final_memory_state == timeline[-1].memory_state_after
        and replay_source_event_ids
        == tuple(step.replay_source_event_id for step in timeline if step.replay_applied)
        and replay_trigger_scores
        == tuple(step.replay_trigger_old_score for step in timeline if step.replay_applied)
        and replay_step_indices
        == tuple(step.step_index for step in timeline if step.replay_applied)
        and _condition_replay_bounded_from_summary(
            timeline=timeline,
            replay_count=replay_count,
            replay_step_indices=replay_step_indices,
            maximum_replays_per_learning_step=maximum_replays_per_learning_step,
            maximum_total_replays=maximum_total_replays,
        )
    )


def _validate_condition_result_semantics(condition: LongHorizonConditionResult) -> None:
    if condition.consolidation_applied != _condition_expected_consolidation(condition.condition):
        raise ValueError("condition consolidation semantics do not match condition identity")
    if tuple(record.step_index for record in condition.timeline) != tuple(
        range(_EXPECTED_TIMELINE_LENGTH)
    ):
        raise ValueError("timeline step indices must be contiguous from zero to thirty-five")
    expected_families = tuple(
        LongHorizonTaskFamily(_SCHEDULE_PATTERN[index % len(_SCHEDULE_PATTERN)])
        for index in range(_EXPECTED_TIMELINE_LENGTH)
    )
    if tuple(record.task_family for record in condition.timeline) != expected_families:
        raise ValueError("timeline task-family order must remain A,B,A,C repeating")
    for index, record in enumerate(condition.timeline):
        expected_probe = record.task_family is LongHorizonTaskFamily.FAMILY_A
        if record.probe_only != expected_probe or record.learning_applied == expected_probe:
            raise ValueError("probe and learning flags must match the task family")
        if (
            index > 0
            and record.memory_state_before != condition.timeline[index - 1].memory_state_after
        ):
            raise ValueError("timeline memory states must be contiguous")
        if record.old_family_score_after != _memory_family_score(
            record.memory_state_after, LongHorizonTaskFamily.FAMILY_A
        ):
            raise ValueError("step old-family score must derive from memory_state_after")
        if record.b_family_score_after != _memory_family_score(
            record.memory_state_after, LongHorizonTaskFamily.FAMILY_B
        ):
            raise ValueError("step B-family score must derive from memory_state_after")
        if record.c_family_score_after != _memory_family_score(
            record.memory_state_after, LongHorizonTaskFamily.FAMILY_C
        ):
            raise ValueError("step C-family score must derive from memory_state_after")
    if condition.condition is LongHorizonInterferenceCondition.BOUNDED_RETENTION_REPLAY:
        if condition.replay_count <= 0:
            raise ValueError("bounded retention replay must contain at least one replay")
    elif condition.replay_count != 0:
        raise ValueError("baseline conditions must not contain replay")
    first_before = condition.timeline[0].memory_state_before
    last_after = condition.timeline[-1].memory_state_after
    if condition.initial_old_family_score != _memory_family_score(
        first_before, LongHorizonTaskFamily.FAMILY_A
    ):
        raise ValueError("initial_old_family_score must derive from the initial memory snapshot")
    if condition.initial_b_family_score != _memory_family_score(
        first_before, LongHorizonTaskFamily.FAMILY_B
    ):
        raise ValueError("initial_b_family_score must derive from the initial memory snapshot")
    if condition.initial_c_family_score != _memory_family_score(
        first_before, LongHorizonTaskFamily.FAMILY_C
    ):
        raise ValueError("initial_c_family_score must derive from the initial memory snapshot")
    if condition.final_old_family_score != _memory_family_score(
        last_after, LongHorizonTaskFamily.FAMILY_A
    ):
        raise ValueError("final_old_family_score must derive from the final memory snapshot")
    if condition.final_b_family_score != _memory_family_score(
        last_after, LongHorizonTaskFamily.FAMILY_B
    ):
        raise ValueError("final_b_family_score must derive from the final memory snapshot")
    if condition.final_c_family_score != _memory_family_score(
        last_after, LongHorizonTaskFamily.FAMILY_C
    ):
        raise ValueError("final_c_family_score must derive from the final memory snapshot")
    if condition.old_family_interference != max(
        0.0, condition.initial_old_family_score - condition.final_old_family_score
    ):
        raise ValueError(
            "old_family_interference must derive exactly from initial and final old-family scores"
        )
    if condition.b_family_learning_gain != max(
        0.0, condition.final_b_family_score - condition.initial_b_family_score
    ):
        raise ValueError(
            "b_family_learning_gain must derive exactly from initial and final B-family scores"
        )
    if condition.c_family_learning_gain != max(
        0.0, condition.final_c_family_score - condition.initial_c_family_score
    ):
        raise ValueError(
            "c_family_learning_gain must derive exactly from initial and final C-family scores"
        )
    if condition.joint_score != min(
        condition.final_old_family_score,
        condition.final_b_family_score,
        condition.final_c_family_score,
    ):
        raise ValueError("joint_score must equal min(final A, final B, final C)")
    if condition.final_memory_state != last_after:
        raise ValueError("final memory state must equal the last timeline state")
    if condition.replay_bound_held != _condition_replay_bounded(condition):
        raise ValueError("replay_bound_held must derive exactly from the timeline replay records")
    if condition.condition_pass_evidence != _condition_integrity_predicate(
        condition=condition.condition,
        consolidation_applied=condition.consolidation_applied,
        timeline=condition.timeline,
        replay_count=condition.replay_count,
        replay_source_event_ids=condition.replay_source_event_ids,
        replay_trigger_scores=condition.replay_trigger_scores,
        replay_step_indices=condition.replay_step_indices,
        maximum_replays_per_learning_step=condition.maximum_replays_per_learning_step,
        maximum_total_replays=condition.maximum_total_replays,
        final_memory_state=condition.final_memory_state,
    ):
        raise ValueError("condition_pass_evidence must equal the deterministic integrity predicate")


def _clamp_signed(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _validate_unit(name: str, value: object) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if not 0.0 <= float(value) <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _validate_signed(name: str, value: object) -> None:
    if not isinstance(value, int | float) or isinstance(value, bool) or not isfinite(value):
        raise ValueError(f"{name} must be a finite number")
    if not -1.0 <= float(value) <= 1.0:
        raise ValueError(f"{name} must be between negative one and one")


def _validate_code(name: str, value: str) -> None:
    if not value or not value.isascii() or not value.strip():
        raise ValueError(f"{name} must be non-empty ASCII")
