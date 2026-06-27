"""Bounded experiment for contextual redundancy, transfer, and mastery."""

from __future__ import annotations

from dataclasses import dataclass

from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.research.ndnra.contextual_memory import (
    ContextSignature,
    ContextualLearningResult,
    ContextualRecordCode,
    EventIdentity,
    LessonIdentity,
    RouteSupport,
)
from seedmind.research.ndnra.effects import EffectObservation

_LESSON = LessonIdentity(
    need_code="avoid_heat_harm",
    effect_code="protective_value",
    desired_direction=1.0,
)


@dataclass(frozen=True, slots=True)
class ContextualMasteryExperimentResult:
    """Falsifiable metrics for exact deduplication and broad mastery."""

    exact_duplicate_ignored: bool
    exact_duplicate_evidence_count: int
    identity_conflict_blocked: bool
    legitimate_context_preserved: bool
    replay_trace_count: int
    replay_effective_support: float
    replay_unique_context_count: int
    replay_aggregate_evidence_count: int
    independent_trace_count: int
    independent_effective_support: float
    independent_unique_context_count: int
    independent_unique_route_count: int
    mastery_score_gain: float
    one_shot_protective_strength: float
    one_shot_broad_mastery: bool
    varied_heat_mastery_score: float
    varied_heat_broad_mastery: bool
    contradiction_count_before: int
    contradiction_count_after: int
    causal_consistency_before: float
    causal_consistency_after: float
    mastery_before_contradiction: float
    mastery_after_contradiction: float
    source_traces_preserved: bool
    route_switches_with_context: bool
    pass_gate: bool


@dataclass(frozen=True, slots=True)
class ContextualMasteryExperimentEvidence:
    """Result plus inspectable ledgers, mastery profiles, and route rankings."""

    result: ContextualMasteryExperimentResult
    replay_ledger: dict[str, object]
    one_shot_ledger: dict[str, object]
    varied_ledger: dict[str, object]
    replay_profile: dict[str, object]
    one_shot_profile: dict[str, object]
    varied_profile_before_contradiction: dict[str, object]
    varied_profile_after_contradiction: dict[str, object]
    first_context_routes: tuple[dict[str, object], ...]
    second_context_routes: tuple[dict[str, object], ...]


def run_contextual_mastery_experiment() -> ContextualMasteryExperimentEvidence:
    """Compare copied repetition with independent contextual experience."""
    duplicate_graph = MultidimensionalExperienceGraph()
    duplicate_context = _context(1.0, 0.0, actions=("withdraw",))
    duplicate_identity = EventIdentity("contextual_gate", "duplicate", 0)
    first = _learn(
        duplicate_graph,
        identity=duplicate_identity,
        correlation_group_id="group:duplicate",
        assembly_id="assembly:withdraw",
        route_id="route:withdraw",
        action_code="withdraw",
        context=duplicate_context,
        value=1.0,
    )
    duplicate = _learn(
        duplicate_graph,
        identity=duplicate_identity,
        correlation_group_id="group:duplicate",
        assembly_id="assembly:withdraw",
        route_id="route:withdraw",
        action_code="withdraw",
        context=duplicate_context,
        value=1.0,
    )
    identity_conflict_blocked = _identity_conflict_is_blocked(
        duplicate_graph,
        duplicate_identity,
        duplicate_context,
    )

    replay_graph = MultidimensionalExperienceGraph()
    for step in range(6):
        _learn(
            replay_graph,
            identity=EventIdentity("contextual_gate", "replay", step),
            correlation_group_id="group:single_source_replay",
            assembly_id="assembly:withdraw",
            route_id="route:withdraw",
            action_code="withdraw",
            context=duplicate_context,
            value=1.0,
        )
    replay_profile = replay_graph.contextual_memory.mastery_profile(_LESSON)

    one_shot_graph = MultidimensionalExperienceGraph()
    _learn(
        one_shot_graph,
        identity=EventIdentity("contextual_gate", "one_shot", 0),
        correlation_group_id="group:one_shot",
        assembly_id="assembly:rapid_withdraw",
        route_id="route:rapid_withdraw",
        action_code="rapid_withdraw",
        context=_context(1.0, 0.0, actions=("rapid_withdraw",)),
        value=0.95,
        confidence=1.0,
    )
    one_shot_profile = one_shot_graph.contextual_memory.mastery_profile(_LESSON)

    varied_graph = MultidimensionalExperienceGraph()
    varied_contexts = (
        _context(1.0, 0.0, actions=("withdraw", "cool_surface")),
        _context(0.8, 0.2, actions=("withdraw", "cool_surface")),
        _context(0.2, 0.8, actions=("withdraw", "cool_surface")),
        _context(0.0, 1.0, actions=("withdraw", "cool_surface")),
    )
    route_specs = (
        ("assembly:withdraw", "route:withdraw", "withdraw"),
        ("assembly:withdraw", "route:withdraw", "withdraw"),
        ("assembly:cool_surface", "route:cool_surface", "cool_surface"),
        ("assembly:cool_surface", "route:cool_surface", "cool_surface"),
    )
    for step, (context, route_spec) in enumerate(zip(varied_contexts, route_specs, strict=True)):
        assembly_id, route_id, action_code = route_spec
        _learn(
            varied_graph,
            identity=EventIdentity("contextual_gate", "varied", step),
            correlation_group_id=f"group:independent:{step}",
            assembly_id=assembly_id,
            route_id=route_id,
            action_code=action_code,
            context=context,
            value=1.0,
            transfer_attempted=True,
            transfer_succeeded=True,
        )
    before = varied_graph.contextual_memory.mastery_profile(_LESSON)
    first_routes = varied_graph.contextual_memory.rank_routes(_LESSON, varied_contexts[0])
    second_routes = varied_graph.contextual_memory.rank_routes(_LESSON, varied_contexts[-1])
    source_count_before = varied_graph.contextual_memory.trace_count

    _learn(
        varied_graph,
        identity=EventIdentity("contextual_gate", "varied", 4),
        correlation_group_id="group:independent:contradiction",
        assembly_id="assembly:withdraw",
        route_id="route:withdraw",
        action_code="withdraw",
        context=_context(0.9, 0.1, actions=("withdraw", "cool_surface")),
        value=-1.0,
        transfer_attempted=True,
        transfer_succeeded=False,
    )
    after = varied_graph.contextual_memory.mastery_profile(_LESSON)
    source_traces_preserved = bool(
        source_count_before == 4
        and varied_graph.contextual_memory.trace_count == 5
        and all(
            varied_graph.contextual_memory.trace(event_key).identity.key == event_key
            for event_key in after.source_event_ids
        )
    )
    route_switches = _route_switches(first_routes, second_routes)
    legitimate_context_preserved = bool(
        varied_graph.contextual_memory.trace_count >= 2 and before.unique_context_count >= 2
    )
    score_gain = before.mastery_score - replay_profile.mastery_score
    duplicate_evidence_count = duplicate_graph.assembly("assembly:withdraw").evidence_count
    replay_evidence_count = replay_graph.assembly("assembly:withdraw").evidence_count

    pass_gate = bool(
        first.code is ContextualRecordCode.ACCEPTED_INDEPENDENT
        and duplicate.code is ContextualRecordCode.EXACT_DUPLICATE_IGNORED
        and duplicate_evidence_count == 1
        and identity_conflict_blocked
        and legitimate_context_preserved
        and replay_graph.contextual_memory.trace_count == 6
        and replay_profile.effective_support <= 1.0
        and replay_profile.unique_context_count == 1
        and replay_evidence_count == 1
        and varied_graph.contextual_memory.trace_count == 5
        and before.effective_support >= 4.0
        and before.unique_context_count >= 3
        and before.unique_route_count >= 2
        and score_gain >= 0.30
        and one_shot_profile.protective_strength >= 0.90
        and not one_shot_profile.broad_mastery
        and before.mastery_score >= 0.75
        and before.broad_mastery
        and after.contradiction_count > before.contradiction_count
        and after.causal_consistency < before.causal_consistency
        and after.mastery_score < before.mastery_score
        and source_traces_preserved
        and route_switches
    )
    result = ContextualMasteryExperimentResult(
        exact_duplicate_ignored=(duplicate.code is ContextualRecordCode.EXACT_DUPLICATE_IGNORED),
        exact_duplicate_evidence_count=duplicate_evidence_count,
        identity_conflict_blocked=identity_conflict_blocked,
        legitimate_context_preserved=legitimate_context_preserved,
        replay_trace_count=replay_graph.contextual_memory.trace_count,
        replay_effective_support=replay_profile.effective_support,
        replay_unique_context_count=replay_profile.unique_context_count,
        replay_aggregate_evidence_count=replay_evidence_count,
        independent_trace_count=source_count_before,
        independent_effective_support=before.effective_support,
        independent_unique_context_count=before.unique_context_count,
        independent_unique_route_count=before.unique_route_count,
        mastery_score_gain=score_gain,
        one_shot_protective_strength=one_shot_profile.protective_strength,
        one_shot_broad_mastery=one_shot_profile.broad_mastery,
        varied_heat_mastery_score=before.mastery_score,
        varied_heat_broad_mastery=before.broad_mastery,
        contradiction_count_before=before.contradiction_count,
        contradiction_count_after=after.contradiction_count,
        causal_consistency_before=before.causal_consistency,
        causal_consistency_after=after.causal_consistency,
        mastery_before_contradiction=before.mastery_score,
        mastery_after_contradiction=after.mastery_score,
        source_traces_preserved=source_traces_preserved,
        route_switches_with_context=route_switches,
        pass_gate=pass_gate,
    )
    return ContextualMasteryExperimentEvidence(
        result=result,
        replay_ledger=replay_graph.contextual_memory.snapshot(),
        one_shot_ledger=one_shot_graph.contextual_memory.snapshot(),
        varied_ledger=varied_graph.contextual_memory.snapshot(),
        replay_profile=replay_profile.snapshot(),
        one_shot_profile=one_shot_profile.snapshot(),
        varied_profile_before_contradiction=before.snapshot(),
        varied_profile_after_contradiction=after.snapshot(),
        first_context_routes=_route_snapshots(first_routes),
        second_context_routes=_route_snapshots(second_routes),
    )


def _learn(
    graph: MultidimensionalExperienceGraph,
    *,
    identity: EventIdentity,
    correlation_group_id: str,
    assembly_id: str,
    route_id: str,
    action_code: str,
    context: ContextSignature,
    value: float,
    confidence: float = 1.0,
    transfer_attempted: bool = False,
    transfer_succeeded: bool = False,
) -> ContextualLearningResult:
    return graph.learn_contextual_experience(
        identity=identity,
        correlation_group_id=correlation_group_id,
        assembly_id=assembly_id,
        route_id=route_id,
        action_code=action_code,
        origin_need_code="avoid_heat_harm",
        required_facts=("heat_source_detected",),
        produced_facts=(f"route_used:{route_id}",),
        context_signature=context,
        observed_effects=(EffectObservation("protective_value", value, confidence),),
        transfer_attempted=transfer_attempted,
        transfer_succeeded=transfer_succeeded,
    )


def _identity_conflict_is_blocked(
    graph: MultidimensionalExperienceGraph,
    identity: EventIdentity,
    context: ContextSignature,
) -> bool:
    try:
        _learn(
            graph,
            identity=identity,
            correlation_group_id="group:duplicate",
            assembly_id="assembly:withdraw",
            route_id="route:withdraw",
            action_code="withdraw",
            context=context,
            value=-1.0,
        )
    except ValueError as error:
        return "event identity conflict" in str(error)
    return False


def _context(
    first_sensor: float,
    second_sensor: float,
    *,
    actions: tuple[str, ...],
) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code="avoid_heat_harm",
        sensor_values=(first_sensor, second_sensor),
        available_action_codes=actions,
        human_values=(0.0,),
        resource_values=(1.0,),
    )


def _route_switches(
    first: tuple[RouteSupport, ...],
    second: tuple[RouteSupport, ...],
) -> bool:
    return bool(
        len(first) >= 2
        and len(second) >= 2
        and first[0].route_id == "route:withdraw"
        and second[0].route_id == "route:cool_surface"
    )


def _route_snapshots(routes: tuple[RouteSupport, ...]) -> tuple[dict[str, object], ...]:
    return tuple(route.snapshot() for route in routes)
