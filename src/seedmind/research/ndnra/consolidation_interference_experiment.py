"""Bounded experiment for consolidation, interference, and source-gated replay."""

from __future__ import annotations

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

_SHARED_ASSEMBLY_ID = "assembly:shared_response"
_OLD_PRIMARY_ROUTE_ID = "route:lesson_a_primary"
_OLD_TRANSFER_ROUTE_ID = "route:lesson_a_transfer"
_NEW_ROUTE_ID = "route:lesson_b"
_OLD_ROUTE_IDS = (_OLD_PRIMARY_ROUTE_ID, _OLD_TRANSFER_ROUTE_ID)
_ALL_ROUTE_IDS = (*_OLD_ROUTE_IDS, _NEW_ROUTE_ID)
_OLD_TARGET = 1.0
_NEW_TARGET = -1.0
_OLD_LESSON = LessonIdentity(
    need_code="preserve_old_response",
    effect_code="response_value",
    desired_direction=1.0,
)


class ConsolidationInterferenceCondition(StrEnum):
    """Controlled conditions in the bounded interference experiment."""

    NO_CONSOLIDATION = "no_consolidation"
    NAIVE_CONSOLIDATION = "naive_consolidation"
    RETENTION_GATED_REPLAY = "retention_gated_replay"


@dataclass(frozen=True, slots=True)
class ConsolidationInterferenceConfig:
    """Deterministic learning, protection, and replay limits."""

    learning_rate: float = 0.50
    stability_protection_weight: float = 0.50
    old_training_passes: int = 4
    new_training_steps: int = 12
    retention_threshold: float = 0.72
    maximum_replays_per_new_step: int = 1
    minimum_new_learning_score: float = 0.70
    minimum_joint_score_advantage: float = 0.10

    def __post_init__(self) -> None:
        for name, value in (
            ("learning_rate", self.learning_rate),
            ("stability_protection_weight", self.stability_protection_weight),
            ("retention_threshold", self.retention_threshold),
            ("minimum_new_learning_score", self.minimum_new_learning_score),
            ("minimum_joint_score_advantage", self.minimum_joint_score_advantage),
        ):
            _validate_unit(name, value)
        for name, value in (
            ("old_training_passes", self.old_training_passes),
            ("new_training_steps", self.new_training_steps),
            ("maximum_replays_per_new_step", self.maximum_replays_per_new_step),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")


@dataclass(frozen=True, slots=True)
class OverlappingLessonMemorySnapshot:
    """Inspectable scalar memory used only by the interference experiment."""

    assembly_value: float
    route_values: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        _validate_signed("assembly_value", self.assembly_value)
        route_ids = tuple(route_id for route_id, _ in self.route_values)
        if not route_ids:
            raise ValueError("route_values must not be empty")
        if route_ids != tuple(sorted(route_ids)):
            raise ValueError("route_values must use stable sorted ordering")
        if len(route_ids) != len(set(route_ids)):
            raise ValueError("route_values must contain unique route identities")
        for route_id, value in self.route_values:
            _validate_code("route_id", route_id)
            _validate_signed("route_value", value)

    def route_value(self, route_id: str) -> float:
        """Return one route value by exact identity."""
        _validate_code("route_id", route_id)
        for stored_route_id, value in self.route_values:
            if stored_route_id == route_id:
                return value
        raise ValueError(f"unknown route identity: {route_id}")


@dataclass(frozen=True, slots=True)
class ConsolidationInterferenceConditionResult:
    """Retention and learning evidence for one controlled condition."""

    condition: ConsolidationInterferenceCondition
    consolidation_applied: bool
    old_score_before: float
    old_score_after: float
    new_score_before: float
    new_score_after: float
    old_interference: float
    new_learning_gain: float
    joint_retention_learning_score: float
    replay_count: int
    replay_source_event_ids: tuple[str, ...]
    replay_trigger_scores: tuple[float, ...]
    final_memory: OverlappingLessonMemorySnapshot
    consolidation_state: ConsolidationStateSnapshot

    def __post_init__(self) -> None:
        for name, value in (
            ("old_score_before", self.old_score_before),
            ("old_score_after", self.old_score_after),
            ("new_score_before", self.new_score_before),
            ("new_score_after", self.new_score_after),
            ("old_interference", self.old_interference),
            ("new_learning_gain", self.new_learning_gain),
            ("joint_retention_learning_score", self.joint_retention_learning_score),
        ):
            _validate_unit(name, value)
        if self.replay_count < 0:
            raise ValueError("replay_count must not be negative")
        if self.replay_count != len(self.replay_source_event_ids):
            raise ValueError("replay_count must match replay source evidence")
        if self.replay_count != len(self.replay_trigger_scores):
            raise ValueError("replay_count must match replay trigger evidence")
        for event_id in self.replay_source_event_ids:
            _validate_code("replay_source_event_id", event_id)
        for score in self.replay_trigger_scores:
            _validate_unit("replay_trigger_score", score)
        if self.condition is ConsolidationInterferenceCondition.RETENTION_GATED_REPLAY:
            if not self.consolidation_applied or self.replay_count <= 0:
                raise ValueError("retention-gated replay must consolidate and replay")
        elif self.replay_count != 0:
            raise ValueError("non-replay conditions must not replay evidence")


@dataclass(frozen=True, slots=True)
class ConsolidationInterferenceExperimentResult:
    """Three-condition evidence for retention and continued learning."""

    no_consolidation: ConsolidationInterferenceConditionResult
    naive_consolidation: ConsolidationInterferenceConditionResult
    retention_gated_replay: ConsolidationInterferenceConditionResult
    old_mastery_profile: MasteryProfile
    consolidation_candidate: ConsolidationCandidate
    source_trace_count_before: int
    source_trace_count_after: int
    source_mastery_unchanged: bool
    replay_sources_resolved: bool
    replay_bounded: bool
    action_authority_violation_count: int
    sqlite_used_for_replay: bool
    pass_gate: bool

    def __post_init__(self) -> None:
        if self.source_trace_count_before < 0 or self.source_trace_count_after < 0:
            raise ValueError("source trace counts must not be negative")
        if self.action_authority_violation_count < 0:
            raise ValueError("action authority violations must not be negative")


@dataclass(frozen=True, slots=True)
class ConsolidationInterferenceExperimentEvidence:
    """Result plus immutable source, eligibility, and initial-state evidence."""

    result: ConsolidationInterferenceExperimentResult
    source_ledger_snapshot: dict[str, object]
    eligibility: ConsolidationEligibility
    initial_memory: OverlappingLessonMemorySnapshot
    unconsolidated_state: ConsolidationStateSnapshot
    consolidated_state: ConsolidationStateSnapshot


@dataclass(slots=True)
class _OverlappingLessonMemory:
    assembly_value: float
    route_values: dict[str, float]

    @classmethod
    def fresh(cls) -> _OverlappingLessonMemory:
        return cls(
            assembly_value=0.0,
            route_values={route_id: 0.0 for route_id in _ALL_ROUTE_IDS},
        )

    @classmethod
    def from_snapshot(
        cls,
        snapshot: OverlappingLessonMemorySnapshot,
    ) -> _OverlappingLessonMemory:
        return cls(
            assembly_value=snapshot.assembly_value,
            route_values=dict(snapshot.route_values),
        )

    def snapshot(self) -> OverlappingLessonMemorySnapshot:
        return OverlappingLessonMemorySnapshot(
            assembly_value=self.assembly_value,
            route_values=tuple(sorted(self.route_values.items())),
        )

    def prediction(self, route_id: str) -> float:
        try:
            route_value = self.route_values[route_id]
        except KeyError as error:
            raise ValueError(f"unknown route identity: {route_id}") from error
        return 0.50 * self.assembly_value + 0.50 * route_value

    def score(self, route_ids: tuple[str, ...], target: float) -> float:
        if not route_ids:
            raise ValueError("route_ids must not be empty")
        _validate_signed("target", target)
        return sum(
            1.0 - abs(target - self.prediction(route_id)) / 2.0 for route_id in route_ids
        ) / len(route_ids)

    def learn(
        self,
        *,
        route_id: str,
        target: float,
        consolidation_state: ConsolidationStateSnapshot,
        config: ConsolidationInterferenceConfig,
    ) -> None:
        _validate_signed("target", target)
        prediction = self.prediction(route_id)
        error = target - prediction
        assembly_state = consolidation_state.assembly_state(_SHARED_ASSEMBLY_ID)
        route_state = consolidation_state.route_state(route_id)
        assembly_rate = _effective_learning_rate(assembly_state, config)
        route_rate = _effective_learning_rate(route_state, config)
        self.assembly_value = _clamp_signed(self.assembly_value + assembly_rate * error * 0.50)
        self.route_values[route_id] = _clamp_signed(
            self.route_values[route_id] + route_rate * error * 0.50
        )


def run_consolidation_interference_experiment(
    config: ConsolidationInterferenceConfig | None = None,
) -> ConsolidationInterferenceExperimentEvidence:
    """Compare forgetting, naive protection, and retention-triggered replay."""
    settings = ConsolidationInterferenceConfig() if config is None else config
    ledger = _build_old_lesson_ledger()
    source_profile_before = ledger.mastery_profile(_OLD_LESSON)
    eligibility = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_OLD_LESSON,
        mastery_profile=source_profile_before,
        requested_stability_increment=0.20,
        requested_plasticity_reduction=0.20,
        available_assembly_ids=(_SHARED_ASSEMBLY_ID,),
        available_route_ids=_OLD_ROUTE_IDS,
    )
    if not eligibility.eligible or eligibility.candidate is None:
        raise RuntimeError("old lesson did not pass consolidation eligibility")
    candidate = eligibility.candidate

    unconsolidated_application = ConsolidationApplicationState.from_identifiers(
        assembly_ids=(_SHARED_ASSEMBLY_ID,),
        route_ids=_ALL_ROUTE_IDS,
    )
    naive_application = ConsolidationApplicationState.from_identifiers(
        assembly_ids=(_SHARED_ASSEMBLY_ID,),
        route_ids=_ALL_ROUTE_IDS,
    )
    replay_application = ConsolidationApplicationState.from_identifiers(
        assembly_ids=(_SHARED_ASSEMBLY_ID,),
        route_ids=_ALL_ROUTE_IDS,
    )
    naive_state = naive_application.apply(eligibility).after
    replay_state = replay_application.apply(eligibility).after
    unconsolidated_state = unconsolidated_application.snapshot()

    source_traces = tuple(ledger.trace(event_id) for event_id in candidate.source_event_ids)
    initial_memory = _train_old_lesson(
        source_traces=source_traces,
        state=unconsolidated_state,
        config=settings,
    )
    no_consolidation = _run_condition(
        condition=ConsolidationInterferenceCondition.NO_CONSOLIDATION,
        initial_memory=initial_memory,
        consolidation_state=unconsolidated_state,
        source_traces=source_traces,
        config=settings,
    )
    naive_consolidation = _run_condition(
        condition=ConsolidationInterferenceCondition.NAIVE_CONSOLIDATION,
        initial_memory=initial_memory,
        consolidation_state=naive_state,
        source_traces=source_traces,
        config=settings,
    )
    retention_gated_replay = _run_condition(
        condition=ConsolidationInterferenceCondition.RETENTION_GATED_REPLAY,
        initial_memory=initial_memory,
        consolidation_state=replay_state,
        source_traces=source_traces,
        config=settings,
    )

    source_profile_after = ledger.mastery_profile(_OLD_LESSON)
    source_trace_count_before = len(candidate.source_event_ids)
    source_trace_count_after = ledger.trace_count
    replay_source_ids = retention_gated_replay.replay_source_event_ids
    candidate_source_ids = set(candidate.source_event_ids)
    replay_sources_resolved = bool(
        replay_source_ids
        and all(
            event_id in candidate_source_ids and ledger.trace(event_id).identity.key == event_id
            for event_id in replay_source_ids
        )
    )
    replay_bound = settings.new_training_steps * settings.maximum_replays_per_new_step
    replay_bounded = 0 < retention_gated_replay.replay_count <= replay_bound
    source_mastery_unchanged = bool(
        source_profile_before == source_profile_after
        and source_trace_count_before == source_trace_count_after
    )
    baseline_joint = max(
        no_consolidation.joint_retention_learning_score,
        naive_consolidation.joint_retention_learning_score,
    )
    pass_gate = bool(
        source_profile_before.broad_mastery
        and no_consolidation.old_interference >= 0.30
        and no_consolidation.new_score_after >= 0.85
        and naive_consolidation.old_score_after > no_consolidation.old_score_after
        and naive_consolidation.new_score_after < no_consolidation.new_score_after
        and retention_gated_replay.old_score_after >= settings.retention_threshold
        and retention_gated_replay.new_score_after >= settings.minimum_new_learning_score
        and retention_gated_replay.joint_retention_learning_score
        >= baseline_joint + settings.minimum_joint_score_advantage
        and all(
            score < settings.retention_threshold
            for score in retention_gated_replay.replay_trigger_scores
        )
        and replay_sources_resolved
        and replay_bounded
        and source_mastery_unchanged
    )
    result = ConsolidationInterferenceExperimentResult(
        no_consolidation=no_consolidation,
        naive_consolidation=naive_consolidation,
        retention_gated_replay=retention_gated_replay,
        old_mastery_profile=source_profile_before,
        consolidation_candidate=candidate,
        source_trace_count_before=source_trace_count_before,
        source_trace_count_after=source_trace_count_after,
        source_mastery_unchanged=source_mastery_unchanged,
        replay_sources_resolved=replay_sources_resolved,
        replay_bounded=replay_bounded,
        action_authority_violation_count=0,
        sqlite_used_for_replay=False,
        pass_gate=pass_gate,
    )
    return ConsolidationInterferenceExperimentEvidence(
        result=result,
        source_ledger_snapshot=ledger.snapshot(),
        eligibility=eligibility,
        initial_memory=initial_memory,
        unconsolidated_state=unconsolidated_state,
        consolidated_state=replay_state,
    )


def _build_old_lesson_ledger() -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    specifications = (
        (0, _OLD_PRIMARY_ROUTE_ID, (0.10, 0.20), True),
        (1, _OLD_TRANSFER_ROUTE_ID, (0.50, 0.60), True),
        (2, _OLD_PRIMARY_ROUTE_ID, (0.90, 1.00), False),
    )
    for step, route_id, sensors, transfer_succeeded in specifications:
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity("consolidation_interference", "lesson_a", step),
                correlation_group_id=f"group:lesson_a:{step}",
                assembly_id=_SHARED_ASSEMBLY_ID,
                route_id=route_id,
                action_code="old_response",
                context=ContextSignature.from_values(
                    active_need_code=_OLD_LESSON.need_code,
                    sensor_values=sensors,
                    available_action_codes=("old_response", "new_response"),
                ),
                observed_effects=(
                    EffectObservation(
                        effect_code=_OLD_LESSON.effect_code,
                        value=_OLD_TARGET,
                        confidence=1.0,
                    ),
                ),
                transfer_attempted=True,
                transfer_succeeded=transfer_succeeded,
            )
        )
    return ledger


def _train_old_lesson(
    *,
    source_traces: tuple[ContextualExperienceTrace, ...],
    state: ConsolidationStateSnapshot,
    config: ConsolidationInterferenceConfig,
) -> OverlappingLessonMemorySnapshot:
    memory = _OverlappingLessonMemory.fresh()
    for _ in range(config.old_training_passes):
        for trace in source_traces:
            memory.learn(
                route_id=trace.route_id,
                target=_aligned_lesson_target(trace, _OLD_LESSON),
                consolidation_state=state,
                config=config,
            )
    return memory.snapshot()


def _run_condition(
    *,
    condition: ConsolidationInterferenceCondition,
    initial_memory: OverlappingLessonMemorySnapshot,
    consolidation_state: ConsolidationStateSnapshot,
    source_traces: tuple[ContextualExperienceTrace, ...],
    config: ConsolidationInterferenceConfig,
) -> ConsolidationInterferenceConditionResult:
    memory = _OverlappingLessonMemory.from_snapshot(initial_memory)
    old_score_before = memory.score(_OLD_ROUTE_IDS, _OLD_TARGET)
    new_score_before = memory.score((_NEW_ROUTE_ID,), _NEW_TARGET)
    replay_source_event_ids: list[str] = []
    replay_trigger_scores: list[float] = []
    replay_cursor = 0

    for _ in range(config.new_training_steps):
        memory.learn(
            route_id=_NEW_ROUTE_ID,
            target=_NEW_TARGET,
            consolidation_state=consolidation_state,
            config=config,
        )
        if condition is not ConsolidationInterferenceCondition.RETENTION_GATED_REPLAY:
            continue
        for _ in range(config.maximum_replays_per_new_step):
            retention_score = memory.score(_OLD_ROUTE_IDS, _OLD_TARGET)
            if retention_score >= config.retention_threshold:
                break
            trace = source_traces[replay_cursor % len(source_traces)]
            replay_cursor += 1
            replay_trigger_scores.append(retention_score)
            replay_source_event_ids.append(trace.identity.key)
            memory.learn(
                route_id=trace.route_id,
                target=_aligned_lesson_target(trace, _OLD_LESSON),
                consolidation_state=consolidation_state,
                config=config,
            )

    old_score_after = memory.score(_OLD_ROUTE_IDS, _OLD_TARGET)
    new_score_after = memory.score((_NEW_ROUTE_ID,), _NEW_TARGET)
    return ConsolidationInterferenceConditionResult(
        condition=condition,
        consolidation_applied=(
            condition is not ConsolidationInterferenceCondition.NO_CONSOLIDATION
        ),
        old_score_before=old_score_before,
        old_score_after=old_score_after,
        new_score_before=new_score_before,
        new_score_after=new_score_after,
        old_interference=max(0.0, old_score_before - old_score_after),
        new_learning_gain=max(0.0, new_score_after - new_score_before),
        joint_retention_learning_score=min(old_score_after, new_score_after),
        replay_count=len(replay_source_event_ids),
        replay_source_event_ids=tuple(replay_source_event_ids),
        replay_trigger_scores=tuple(replay_trigger_scores),
        final_memory=memory.snapshot(),
        consolidation_state=consolidation_state,
    )


def _aligned_lesson_target(
    trace: ContextualExperienceTrace,
    lesson: LessonIdentity,
) -> float:
    effect = next(
        observation
        for observation in trace.observed_effects
        if observation.effect_code == lesson.effect_code
    )
    return _clamp_signed(effect.value * lesson.desired_direction)


def _effective_learning_rate(
    structure_state: ConsolidationStructureState,
    config: ConsolidationInterferenceConfig,
) -> float:
    return (
        config.learning_rate
        * structure_state.plasticity
        * (1.0 - config.stability_protection_weight * structure_state.stability)
    )


def _clamp_signed(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between zero and one")


def _validate_signed(name: str, value: float) -> None:
    if not isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between negative one and one")
