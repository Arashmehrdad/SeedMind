"""Third NDNRA experiment: evidence-driven specialist neuron growth."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

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
    GrowthAttemptRecord,
    GrowthOutcome,
    grow_random_specialist,
)

_WET_ASSEMBLY_ID = "assembly:apply_wet_cloth"
_FAN_ASSEMBLY_ID = "assembly:activate_fan"
_DISTRACTOR_ASSEMBLY_ID = "assembly:inspect_wall"
_TARGET_SEQUENCE = (_WET_ASSEMBLY_ID, _FAN_ASSEMBLY_ID)
_TARGET_ACTIONS = ("apply_wet_cloth", "activate_fan")


@dataclass(frozen=True, slots=True)
class StructuralGrowthExperimentResult:
    """Falsifiable metrics for targeted growth versus random capacity."""

    base_assembly_count: int
    base_specialist_count: int
    base_structural_node_count: int
    base_predicted_temperature_effect: float
    actual_temperature_effect: float
    residual_temperature_effect: float
    before_growth_success: bool
    growth_attempt_count: int
    first_growth_ready_attempt: int
    premature_growth_blocked: bool
    final_growth_pressure: float
    targeted_specialist_id: str
    targeted_specialist_members: tuple[str, ...]
    targeted_specialist_effect: float
    targeted_structural_nodes_after: int
    targeted_old_assemblies_preserved: bool
    targeted_solution_success: bool
    targeted_actions: tuple[str, ...]
    targeted_primary_satisfaction: float
    random_specialist_members: tuple[str, ...]
    random_structural_nodes_after: int
    random_solution_success: bool
    random_primary_satisfaction: float
    targeted_beats_random: bool
    duplicate_growth_blocked: bool
    sqlite_used_for_growth: bool
    pass_gate: bool


def structural_cooling_need() -> EffectNeed:
    """Require more cooling than the base additive graph can represent."""
    return EffectNeed(
        need_code="resolve_persistent_heat",
        primary_effect_code="temperature",
        dimensions=(
            NeedDimension(
                effect_code="temperature",
                desired_direction=-1.0,
                intensity=1.0,
            ),
            NeedDimension(
                effect_code="water_cost",
                desired_direction=-1.0,
                intensity=0.15,
            ),
            NeedDimension(
                effect_code="energy_cost",
                desired_direction=-1.0,
                intensity=0.15,
            ),
        ),
        satisfaction_threshold=0.70,
    )


def build_capacity_limited_graph() -> MultidimensionalExperienceGraph:
    """Create useful local memories without the wetness-airflow interaction."""
    graph = MultidimensionalExperienceGraph()
    graph.learn_experience(
        assembly_id=_WET_ASSEMBLY_ID,
        action_code="apply_wet_cloth",
        origin_need_code="reduce_skin_heat",
        required_facts=("wet_cloth_available",),
        produced_facts=("body_wet",),
        observed_effects=(
            EffectObservation("temperature", -0.18, 0.95),
            EffectObservation("wetness", 0.90, 0.95),
            EffectObservation("water_cost", 0.20, 0.90),
        ),
    )
    graph.learn_experience(
        assembly_id=_FAN_ASSEMBLY_ID,
        action_code="activate_fan",
        origin_need_code="increase_airflow",
        required_facts=("fan_available", "body_wet"),
        produced_facts=("airflow",),
        observed_effects=(
            EffectObservation("temperature", -0.18, 0.95),
            EffectObservation("airflow", 0.90, 0.95),
            EffectObservation("energy_cost", 0.15, 0.90),
        ),
    )
    graph.learn_experience(
        assembly_id=_DISTRACTOR_ASSEMBLY_ID,
        action_code="inspect_wall",
        origin_need_code="curiosity",
        required_facts=("wall_visible",),
        produced_facts=("wall_inspected",),
        observed_effects=(
            EffectObservation("novelty", 0.20, 0.60),
            EffectObservation("attention_cost", 0.10, 0.80),
        ),
    )
    return graph


def run_ndnra_structural_growth_experiment() -> tuple[
    StructuralGrowthExperimentResult,
    MultidimensionalExperienceGraph,
    MultidimensionalExperienceGraph,
    tuple[GrowthAttemptRecord, ...],
]:
    """Grow one targeted specialist and compare it with random capacity."""
    need = structural_cooling_need()
    current_facts = (
        "wet_cloth_available",
        "fan_available",
        "wall_visible",
    )
    targeted_graph = build_capacity_limited_graph()
    random_graph = build_capacity_limited_graph()
    composer = NeedDrivenComposer(targeted_graph, maximum_depth=2)
    before_growth = composer.compose(need=need, current_facts=current_facts)

    base_snapshots = {
        assembly.assembly_id: assembly.snapshot() for assembly in targeted_graph.assemblies
    }
    base_nodes = targeted_graph.structural_node_count
    predicted_effects = targeted_graph.project_effects(_TARGET_SEQUENCE)
    predicted_temperature = predicted_effects.get("temperature", 0.0)
    actual_temperature = -0.90
    residual_temperature = actual_temperature - predicted_temperature

    controller = EvidenceDrivenGrowthController(targeted_graph)
    attempts: list[GrowthAttemptRecord] = []
    for _ in range(3):
        attempts.append(
            controller.observe_unresolved_interaction(
                active_assembly_ids=_TARGET_SEQUENCE,
                predicted_effect=predicted_temperature,
                actual_effect=actual_temperature,
                curiosity=0.95,
                ambition_relevance=1.00,
                capacity_saturation=1.00,
            )
        )

    ready_attempts = [attempt.attempt_index for attempt in attempts if attempt.growth_ready]
    first_ready_attempt = ready_attempts[0] if ready_attempts else 0
    premature_growth_blocked = all(not attempt.growth_ready for attempt in attempts[:2])
    growth_outcome = controller.grow_targeted_specialist(
        specialist_id="specialist:evaporative_cooling",
        effect_code="temperature",
    )
    targeted_after = NeedDrivenComposer(targeted_graph, maximum_depth=2).compose(
        need=need,
        current_facts=current_facts,
    )

    random_specialist = grow_random_specialist(random_graph, seed=7)
    random_after = NeedDrivenComposer(random_graph, maximum_depth=2).compose(
        need=need,
        current_facts=current_facts,
    )

    assemblies_preserved = all(
        targeted_graph.assembly(assembly_id).snapshot() == snapshot
        for assembly_id, snapshot in base_snapshots.items()
    )
    duplicate_growth_blocked = _duplicate_growth_is_blocked(
        targeted_graph,
        growth_outcome,
    )
    targeted_selected = targeted_after.selected
    random_selected = random_after.selected
    targeted_satisfaction = (
        targeted_selected.primary_satisfaction if targeted_selected is not None else 0.0
    )
    random_satisfaction = (
        random_selected.primary_satisfaction if random_selected is not None else 0.0
    )
    targeted_beats_random = (
        targeted_after.success
        and not random_after.success
        and targeted_satisfaction > random_satisfaction
    )
    specialist_effect = targeted_graph.specialists[0].effect_memory.estimate("temperature")
    specialist_effect_value = specialist_effect.value if specialist_effect is not None else 0.0

    pass_gate = bool(
        not before_growth.success
        and controller.attempt_count == 3
        and first_ready_attempt == 3
        and premature_growth_blocked
        and controller.pressure.value >= controller.config.growth_threshold
        and growth_outcome.member_assembly_ids == _TARGET_SEQUENCE
        and growth_outcome.structural_nodes_before == base_nodes
        and growth_outcome.structural_nodes_after == base_nodes + 1
        and growth_outcome.old_assembly_count_preserved
        and assemblies_preserved
        and targeted_selected is not None
        and targeted_selected.actions == _TARGET_ACTIONS
        and targeted_selected.primary_satisfaction >= need.satisfaction_threshold
        and random_graph.structural_node_count == base_nodes + 1
        and not random_after.success
        and targeted_beats_random
        and duplicate_growth_blocked
    )

    result = StructuralGrowthExperimentResult(
        base_assembly_count=targeted_graph.assembly_count,
        base_specialist_count=0,
        base_structural_node_count=base_nodes,
        base_predicted_temperature_effect=predicted_temperature,
        actual_temperature_effect=actual_temperature,
        residual_temperature_effect=residual_temperature,
        before_growth_success=before_growth.success,
        growth_attempt_count=controller.attempt_count,
        first_growth_ready_attempt=first_ready_attempt,
        premature_growth_blocked=premature_growth_blocked,
        final_growth_pressure=controller.pressure.value,
        targeted_specialist_id=growth_outcome.specialist_id,
        targeted_specialist_members=growth_outcome.member_assembly_ids,
        targeted_specialist_effect=specialist_effect_value,
        targeted_structural_nodes_after=targeted_graph.structural_node_count,
        targeted_old_assemblies_preserved=assemblies_preserved,
        targeted_solution_success=targeted_after.success,
        targeted_actions=(targeted_selected.actions if targeted_selected is not None else ()),
        targeted_primary_satisfaction=targeted_satisfaction,
        random_specialist_members=random_specialist.member_assembly_ids,
        random_structural_nodes_after=random_graph.structural_node_count,
        random_solution_success=random_after.success,
        random_primary_satisfaction=random_satisfaction,
        targeted_beats_random=targeted_beats_random,
        duplicate_growth_blocked=duplicate_growth_blocked,
        sqlite_used_for_growth=False,
        pass_gate=pass_gate,
    )
    return result, targeted_graph, random_graph, tuple(attempts)


def export_structural_growth_evidence(
    result: StructuralGrowthExperimentResult,
    targeted_graph: MultidimensionalExperienceGraph,
    random_graph: MultidimensionalExperienceGraph,
    attempts: tuple[GrowthAttemptRecord, ...],
    output_directory: Path,
) -> tuple[Path, Path, Path, Path]:
    """Export the growth report, pressure timeline, and both graph states."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "structural_growth_report.json"
    timeline_path = output_directory / "growth_pressure_timeline.csv"
    targeted_path = output_directory / "targeted_growth_graph.json"
    random_path = output_directory / "random_growth_graph.json"

    _write_ascii_json(report_path, asdict(result))
    _write_ascii_json(targeted_path, targeted_graph.snapshot())
    _write_ascii_json(random_path, random_graph.snapshot())
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "attempt_index",
                "active_assembly_ids",
                "predicted_effect",
                "actual_effect",
                "residual_effect",
                "unresolved_error",
                "growth_pressure",
                "growth_ready",
                "eligibility_traces",
            )
        )
        for attempt in attempts:
            writer.writerow(
                (
                    attempt.attempt_index,
                    ">".join(attempt.active_assembly_ids),
                    attempt.predicted_effect,
                    attempt.actual_effect,
                    attempt.residual_effect,
                    attempt.unresolved_error,
                    attempt.growth_pressure,
                    str(attempt.growth_ready).lower(),
                    ";".join(
                        f"{assembly_id}={trace:.8f}"
                        for assembly_id, trace in attempt.eligibility_traces
                    ),
                )
            )
    return report_path, timeline_path, targeted_path, random_path


def _duplicate_growth_is_blocked(
    graph: MultidimensionalExperienceGraph,
    outcome: GrowthOutcome,
) -> bool:
    try:
        graph.grow_specialist_interaction(
            specialist_id=outcome.specialist_id,
            member_assembly_ids=outcome.member_assembly_ids,
            origin_code="duplicate_test",
        )
    except ValueError:
        return True
    return False


def _write_ascii_json(path: Path, payload: object) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)
