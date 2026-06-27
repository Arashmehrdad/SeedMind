"""Goal-gated multi-step structural growth experiment."""

from __future__ import annotations

from dataclasses import dataclass

from seedmind.research.ndnra.adaptive import NDNRARuntimeAdaptiveState
from seedmind.research.ndnra.composition import (
    MultidimensionalExperienceGraph,
    NeedDrivenComposer,
)
from seedmind.research.ndnra.effects import (
    EffectNeed,
    EffectObservation,
    NeedDimension,
)
from seedmind.research.ndnra.growth import (
    EvidenceDrivenGrowthController,
    StructuralGrowthConfig,
)
from seedmind.research.ndnra.growth_cycle import (
    GoalGatedGrowthCycle,
    GrowthCycleConfig,
    GrowthResolution,
)

_A = "assembly:prepare_surface"
_B = "assembly:apply_force"
_C = "assembly:stabilize_result"


@dataclass(frozen=True, slots=True)
class MultiGrowthExperimentResult:
    """Evidence that unresolved complex needs can require repeated growth."""

    base_primary_satisfaction: float
    first_growth_primary_satisfaction: float
    second_growth_primary_satisfaction: float
    satisfaction_threshold: float
    first_growth_goal_achieved: bool
    first_growth_pressure_discharged: bool
    first_growth_continue_growth: bool
    pressure_after_first_growth: float
    second_growth_goal_achieved: bool
    second_growth_pressure_discharged: bool
    second_growth_continue_growth: bool
    pressure_before_final_discharge: float
    pressure_after_final_discharge: float
    growth_step_count: int
    specialist_count: int
    specialist_member_sets: tuple[tuple[str, ...], ...]
    duplicate_membership_blocked: bool
    pass_gate: bool


def run_multi_growth_experiment() -> MultiGrowthExperimentResult:
    """Require two distinct growth steps before pressure can discharge."""
    graph = _build_graph()
    need = _complex_need()
    facts = ("surface_available",)
    controller = EvidenceDrivenGrowthController(
        graph,
        StructuralGrowthConfig(
            pressure_learning_rate=1.0,
            growth_threshold=0.60,
            minimum_attempts=3,
            maximum_specialists=3,
        ),
    )
    adaptive = NDNRARuntimeAdaptiveState.from_growth_state(graph)
    adaptive.pressure = controller.pressure
    cycle = GoalGatedGrowthCycle(
        adaptive,
        GrowthCycleConfig(
            maximum_growth_steps=3,
            continuation_pressure_threshold=0.50,
            minimum_causal_improvement=0.05,
            discharge_amount=0.60,
        ),
    )

    base = _satisfaction(graph, need, facts)
    predicted_ab = graph.project_effects((_A, _B)).get("goal_progress", 0.0)
    for _ in range(3):
        controller.observe_unresolved_interaction(
            active_assembly_ids=(_A, _B),
            predicted_effect=predicted_ab,
            actual_effect=0.45,
            curiosity=1.0,
            ambition_relevance=1.0,
            capacity_saturation=1.0,
        )
    controller.grow_targeted_specialist(
        specialist_id="specialist:surface_force",
        effect_code="goal_progress",
    )
    first = _satisfaction(graph, need, facts)
    first_resolution = cycle.evaluate_growth_step(
        growth_step_index=1,
        goal_satisfaction=first,
        satisfaction_threshold=need.satisfaction_threshold,
        causal_improvement=max(0.0, first - base),
    )

    predicted_bc = graph.project_effects((_B, _C)).get("goal_progress", 0.0)
    for _ in range(3):
        controller.observe_unresolved_interaction(
            active_assembly_ids=(_B, _C),
            predicted_effect=predicted_bc,
            actual_effect=0.70,
            curiosity=1.0,
            ambition_relevance=1.0,
            capacity_saturation=1.0,
        )
    pressure_before_final = controller.pressure.value
    controller.grow_targeted_specialist(
        specialist_id="specialist:force_stability",
        effect_code="goal_progress",
    )
    second = _satisfaction(graph, need, facts)
    duplicate_blocked = _duplicate_membership_is_blocked(controller)
    second_resolution = cycle.evaluate_growth_step(
        growth_step_index=2,
        goal_satisfaction=second,
        satisfaction_threshold=need.satisfaction_threshold,
        causal_improvement=max(0.0, second - first),
    )
    member_sets = tuple(specialist.member_assembly_ids for specialist in graph.specialists)
    pass_gate = bool(
        base < need.satisfaction_threshold
        and not first_resolution.goal_achieved
        and first_resolution.discharge is None
        and first_resolution.continue_growth
        and first_resolution.pressure_after == first_resolution.pressure_before
        and second_resolution.goal_achieved
        and second_resolution.causal_improvement_verified
        and second_resolution.discharge is not None
        and not second_resolution.continue_growth
        and second_resolution.pressure_after < second_resolution.pressure_before
        and graph.specialist_count == 2
        and set(member_sets) == {(_A, _B), (_B, _C)}
        and duplicate_blocked
    )
    return MultiGrowthExperimentResult(
        base_primary_satisfaction=base,
        first_growth_primary_satisfaction=first,
        second_growth_primary_satisfaction=second,
        satisfaction_threshold=need.satisfaction_threshold,
        first_growth_goal_achieved=first_resolution.goal_achieved,
        first_growth_pressure_discharged=first_resolution.discharge is not None,
        first_growth_continue_growth=first_resolution.continue_growth,
        pressure_after_first_growth=first_resolution.pressure_after,
        second_growth_goal_achieved=second_resolution.goal_achieved,
        second_growth_pressure_discharged=second_resolution.discharge is not None,
        second_growth_continue_growth=second_resolution.continue_growth,
        pressure_before_final_discharge=pressure_before_final,
        pressure_after_final_discharge=second_resolution.pressure_after,
        growth_step_count=2,
        specialist_count=graph.specialist_count,
        specialist_member_sets=member_sets,
        duplicate_membership_blocked=duplicate_blocked,
        pass_gate=pass_gate,
    )


def evaluate_unresolved_budget_exhaustion(
    adaptive: NDNRARuntimeAdaptiveState,
) -> GrowthResolution:
    """Return a safe terminal state when bounded growth remains unresolved."""
    adaptive.pressure.value = max(adaptive.pressure.value, 0.80)
    cycle = GoalGatedGrowthCycle(
        adaptive,
        GrowthCycleConfig(maximum_growth_steps=2),
    )
    return cycle.evaluate_growth_step(
        growth_step_index=2,
        goal_satisfaction=0.40,
        satisfaction_threshold=0.80,
        causal_improvement=0.10,
    )


def _build_graph() -> MultidimensionalExperienceGraph:
    graph = MultidimensionalExperienceGraph()
    graph.learn_experience(
        assembly_id=_A,
        action_code="prepare_surface",
        origin_need_code="complex_goal",
        required_facts=("surface_available",),
        produced_facts=("surface_prepared",),
        observed_effects=(EffectObservation("goal_progress", 0.10, 1.0),),
    )
    graph.learn_experience(
        assembly_id=_B,
        action_code="apply_force",
        origin_need_code="complex_goal",
        required_facts=("surface_prepared",),
        produced_facts=("force_applied",),
        observed_effects=(EffectObservation("goal_progress", 0.10, 1.0),),
    )
    graph.learn_experience(
        assembly_id=_C,
        action_code="stabilize_result",
        origin_need_code="complex_goal",
        required_facts=("force_applied",),
        produced_facts=("result_stable",),
        observed_effects=(EffectObservation("goal_progress", 0.10, 1.0),),
    )
    return graph


def _complex_need() -> EffectNeed:
    return EffectNeed(
        need_code="resolve_complex_goal",
        primary_effect_code="goal_progress",
        dimensions=(NeedDimension("goal_progress", 1.0, 1.0),),
        satisfaction_threshold=0.85,
    )


def _satisfaction(
    graph: MultidimensionalExperienceGraph,
    need: EffectNeed,
    facts: tuple[str, ...],
) -> float:
    result = NeedDrivenComposer(graph, maximum_depth=3).compose(
        need=need,
        current_facts=facts,
    )
    if result.selected is not None:
        return result.selected.primary_satisfaction
    effects = graph.project_effects((_A, _B, _C))
    return need.primary_satisfaction(effects)


def _duplicate_membership_is_blocked(
    controller: EvidenceDrivenGrowthController,
) -> bool:
    try:
        controller.grow_targeted_specialist(
            specialist_id="specialist:duplicate_force_stability",
            effect_code="goal_progress",
        )
    except RuntimeError as error:
        return str(error) == "duplicate specialist membership is blocked"
    return False
