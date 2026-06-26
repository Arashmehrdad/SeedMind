"""Second NDNRA experiment: dynamic effects and novel solution composition."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from seedmind.research.ndnra.composition import (
    CompositionCandidate,
    CompositionResult,
    MultidimensionalExperienceGraph,
    NeedDrivenComposer,
)
from seedmind.research.ndnra.effects import (
    EffectNeed,
    EffectObservation,
    NeedDimension,
)

_WINDOW_SOLUTION = ("open_window", "wait_for_cool_wind")
_SHOWER_SOLUTION = ("take_cold_shower",)


@dataclass(frozen=True, slots=True)
class MultieffectExperimentResult:
    """Falsifiable metrics for cross-purpose recall and novel composition."""

    effect_dimension_count: int
    shower_effect_dimension_count: int
    shower_link_dimension_count: int
    shower_origin_need_code: str
    shower_cooling_compatibility: float
    shower_cleaning_success: bool
    shower_reused_for_cooling: bool
    direct_window_solution_success: bool
    composed_window_solution_success: bool
    selected_window_actions: tuple[str, ...]
    complete_window_sequence_was_stored: bool
    window_beats_shower_in_shared_context: bool
    baseline_without_incidental_effect_success: bool
    sqlite_used_for_composition: bool
    selected_window_score: float
    selected_shower_score: float
    explored_state_count: int
    pass_gate: bool


def cooling_need() -> EffectNeed:
    """Return a sparse need that values cooling while avoiding excess cost."""
    return EffectNeed(
        need_code="reduce_temperature",
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
                intensity=0.35,
            ),
            NeedDimension(
                effect_code="time_cost",
                desired_direction=-1.0,
                intensity=0.30,
            ),
        ),
        satisfaction_threshold=0.55,
    )


def cleanliness_need() -> EffectNeed:
    """Return a separate need that can recruit the same shower memory."""
    return EffectNeed(
        need_code="increase_cleanliness",
        primary_effect_code="cleanliness",
        dimensions=(
            NeedDimension(
                effect_code="cleanliness",
                desired_direction=1.0,
                intensity=1.0,
            ),
            NeedDimension(
                effect_code="water_cost",
                desired_direction=-1.0,
                intensity=0.20,
            ),
            NeedDimension(
                effect_code="time_cost",
                desired_direction=-1.0,
                intensity=0.15,
            ),
        ),
        satisfaction_threshold=0.60,
    )


def build_multieffect_graph() -> MultidimensionalExperienceGraph:
    """Learn independent one-action experiences under unrelated original needs."""
    graph = MultidimensionalExperienceGraph()

    graph.learn_experience(
        assembly_id="assembly:cold_shower",
        action_code="take_cold_shower",
        origin_need_code="increase_cleanliness",
        required_facts=("shower_available", "cold_water_available"),
        produced_facts=("body_clean", "body_wet"),
        observed_effects=(
            EffectObservation("cleanliness", 0.90, 0.95),
            EffectObservation("temperature", -0.90, 0.95),
            EffectObservation("wetness", 1.00, 0.95),
            EffectObservation("water_cost", 0.80, 0.90),
            EffectObservation("time_cost", 0.60, 0.90),
        ),
    )
    graph.learn_experience(
        assembly_id="assembly:open_window",
        action_code="open_window",
        origin_need_code="increase_ventilation",
        required_facts=("window_available",),
        produced_facts=("outside_air_access",),
        observed_effects=(
            EffectObservation("airflow", 0.20, 0.80),
            EffectObservation("time_cost", 0.10, 0.90),
        ),
    )
    graph.learn_experience(
        assembly_id="assembly:cool_wind_entry",
        action_code="wait_for_cool_wind",
        origin_need_code="observe_weather_effect",
        required_facts=("outside_air_access", "cool_wind_expected"),
        produced_facts=("room_cooler",),
        observed_effects=(
            EffectObservation("temperature", -0.80, 0.90),
            EffectObservation("airflow", 0.90, 0.90),
            EffectObservation("comfort", 0.50, 0.80),
            EffectObservation("time_cost", 0.15, 0.80),
        ),
    )
    graph.learn_experience(
        assembly_id="assembly:drink_cold_water",
        action_code="drink_cold_water",
        origin_need_code="increase_hydration",
        required_facts=("drinking_water_available",),
        produced_facts=("hydrated",),
        observed_effects=(
            EffectObservation("temperature", -0.30, 0.80),
            EffectObservation("hydration", 0.80, 0.95),
            EffectObservation("water_cost", 0.70, 0.90),
            EffectObservation("time_cost", 0.10, 0.90),
        ),
    )
    graph.learn_experience(
        assembly_id="assembly:hot_shower",
        action_code="take_hot_shower",
        origin_need_code="increase_cleanliness",
        required_facts=("shower_available", "hot_water_available"),
        produced_facts=("body_clean", "body_wet"),
        observed_effects=(
            EffectObservation("cleanliness", 0.90, 0.95),
            EffectObservation("temperature", 0.30, 0.90),
            EffectObservation("wetness", 1.00, 0.95),
            EffectObservation("water_cost", 0.80, 0.90),
            EffectObservation("time_cost", 0.60, 0.90),
        ),
    )
    return graph


def build_intended_effect_only_baseline() -> MultidimensionalExperienceGraph:
    """Build a baseline that discards incidental cooling from showering."""
    graph = MultidimensionalExperienceGraph()
    graph.learn_experience(
        assembly_id="assembly:cold_shower",
        action_code="take_cold_shower",
        origin_need_code="increase_cleanliness",
        required_facts=("shower_available", "cold_water_available"),
        produced_facts=("body_clean", "body_wet"),
        observed_effects=(
            EffectObservation("cleanliness", 0.90, 0.95),
            EffectObservation("wetness", 1.00, 0.95),
            EffectObservation("water_cost", 0.80, 0.90),
            EffectObservation("time_cost", 0.60, 0.90),
        ),
    )
    return graph


def run_ndnra_multieffect_experiment() -> tuple[
    MultieffectExperimentResult,
    MultidimensionalExperienceGraph,
    CompositionResult,
    CompositionResult,
]:
    """Test cross-purpose reuse and a composed undemonstrated cooling plan."""
    graph = build_multieffect_graph()
    cooling = cooling_need()
    cleaning = cleanliness_need()
    composer = NeedDrivenComposer(graph, maximum_depth=3)

    shower_assembly = graph.assembly("assembly:cold_shower")
    shower_link = next(
        link
        for link in graph.links
        if link.source_id == shower_assembly.assembly_id and link.target_id == "fact:body_clean"
    )
    shower_cooling_compatibility = shower_assembly.effect_memory.compatibility(cooling)

    cleaning_result = composer.compose(
        need=cleaning,
        current_facts=("shower_available", "cold_water_available"),
    )
    shower_only_cooling = composer.compose(
        need=cooling,
        current_facts=("shower_available", "cold_water_available"),
    )
    direct_window_result = NeedDrivenComposer(graph, maximum_depth=1).compose(
        need=cooling,
        current_facts=("window_available", "cool_wind_expected"),
    )
    shared_context_result = composer.compose(
        need=cooling,
        current_facts=(
            "window_available",
            "cool_wind_expected",
            "shower_available",
            "cold_water_available",
            "drinking_water_available",
        ),
    )

    baseline = build_intended_effect_only_baseline()
    baseline_result = NeedDrivenComposer(baseline, maximum_depth=2).compose(
        need=cooling,
        current_facts=("shower_available", "cold_water_available"),
    )

    selected_window = shared_context_result.selected
    selected_shower = shower_only_cooling.selected
    stored_sequence = graph.has_stored_action_sequence(_WINDOW_SOLUTION)
    window_beats_shower = bool(
        selected_window is not None
        and selected_shower is not None
        and selected_window.actions == _WINDOW_SOLUTION
        and selected_window.score > selected_shower.score
    )
    pass_gate = bool(
        graph.effect_dimension_codes
        and shower_assembly.effect_memory.dimension_count == 5
        and shower_link.effect_memory.dimension_count == 5
        and shower_assembly.origin_need_code == "increase_cleanliness"
        and shower_cooling_compatibility > 0.0
        and cleaning_result.selected is not None
        and cleaning_result.selected.actions == _SHOWER_SOLUTION
        and selected_shower is not None
        and selected_shower.actions == _SHOWER_SOLUTION
        and not direct_window_result.success
        and selected_window is not None
        and selected_window.actions == _WINDOW_SOLUTION
        and not stored_sequence
        and window_beats_shower
        and not baseline_result.success
    )

    return (
        MultieffectExperimentResult(
            effect_dimension_count=len(graph.effect_dimension_codes),
            shower_effect_dimension_count=shower_assembly.effect_memory.dimension_count,
            shower_link_dimension_count=shower_link.effect_memory.dimension_count,
            shower_origin_need_code=shower_assembly.origin_need_code,
            shower_cooling_compatibility=shower_cooling_compatibility,
            shower_cleaning_success=bool(
                cleaning_result.selected is not None
                and cleaning_result.selected.actions == _SHOWER_SOLUTION
            ),
            shower_reused_for_cooling=bool(
                selected_shower is not None and selected_shower.actions == _SHOWER_SOLUTION
            ),
            direct_window_solution_success=direct_window_result.success,
            composed_window_solution_success=bool(
                selected_window is not None and selected_window.actions == _WINDOW_SOLUTION
            ),
            selected_window_actions=(
                selected_window.actions if selected_window is not None else ()
            ),
            complete_window_sequence_was_stored=stored_sequence,
            window_beats_shower_in_shared_context=window_beats_shower,
            baseline_without_incidental_effect_success=baseline_result.success,
            sqlite_used_for_composition=False,
            selected_window_score=(selected_window.score if selected_window is not None else 0.0),
            selected_shower_score=(selected_shower.score if selected_shower is not None else 0.0),
            explored_state_count=shared_context_result.explored_state_count,
            pass_gate=pass_gate,
        ),
        graph,
        shower_only_cooling,
        shared_context_result,
    )


def export_multieffect_evidence(
    result: MultieffectExperimentResult,
    graph: MultidimensionalExperienceGraph,
    shower_result: CompositionResult,
    shared_result: CompositionResult,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export ASCII evidence for local dimensions and composed solutions."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "multieffect_report.json"
    candidates_path = output_directory / "candidate_solutions.csv"
    graph_path = output_directory / "multidimensional_graph.json"

    _write_ascii_json(report_path, asdict(result))
    _write_ascii_json(graph_path, graph.snapshot())
    with candidates_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "scenario",
                "rank",
                "actions",
                "assembly_ids",
                "score",
                "primary_satisfaction",
                "projected_effects",
            )
        )
        for scenario, composition in (
            ("shower_only_cooling", shower_result),
            ("shared_context_cooling", shared_result),
        ):
            for rank, candidate in enumerate(composition.candidates, start=1):
                writer.writerow(_candidate_row(scenario, rank, candidate))
    return report_path, candidates_path, graph_path


def _candidate_row(
    scenario: str,
    rank: int,
    candidate: CompositionCandidate,
) -> tuple[object, ...]:
    return (
        scenario,
        rank,
        ">".join(candidate.actions),
        ">".join(candidate.assembly_ids),
        candidate.score,
        candidate.primary_satisfaction,
        ";".join(
            f"{effect_code}={value:.8f}" for effect_code, value in candidate.projected_effects
        ),
    )


def _write_ascii_json(path: Path, payload: object) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)
