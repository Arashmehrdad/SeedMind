"""Tests for dynamic local dimensions and undemonstrated solution composition."""

from pathlib import Path

from seedmind.research.ndnra.composition import NeedDrivenComposer
from seedmind.research.ndnra.effects import EffectObservation, SparseEffectMemory
from seedmind.research.ndnra.multieffect_experiment import (
    build_intended_effect_only_baseline,
    build_multieffect_graph,
    cooling_need,
    run_ndnra_multieffect_experiment,
)


def test_sparse_effect_memory_gains_dimensions_from_experience() -> None:
    memory = SparseEffectMemory()

    assert memory.dimension_count == 0
    assert memory.observe(EffectObservation("cleanliness", 0.9, 0.8))
    assert memory.observe(EffectObservation("temperature", -0.6, 0.7))
    assert not memory.observe(EffectObservation("temperature", -0.8, 0.9))

    assert memory.dimension_count == 2
    assert memory.effect_codes == ("cleanliness", "temperature")
    assert memory.estimate("temperature") is not None
    assert memory.estimate("unknown_effect") is None


def test_shower_memory_keeps_all_observed_effects_on_neuron_and_link() -> None:
    graph = build_multieffect_graph()
    shower = graph.assembly("assembly:cold_shower")
    clean_link = next(
        link
        for link in graph.links
        if link.source_id == shower.assembly_id and link.target_id == "fact:body_clean"
    )

    assert shower.origin_need_code == "increase_cleanliness"
    assert shower.effect_memory.dimension_count == 5
    assert clean_link.effect_memory.dimension_count == 5
    assert shower.effect_memory.effect_codes == (
        "cleanliness",
        "temperature",
        "time_cost",
        "water_cost",
        "wetness",
    )
    assert shower.effect_memory.compatibility(cooling_need()) > 0.0


def test_shower_learned_for_cleaning_is_recruited_for_cooling() -> None:
    result, _, shower_result, _ = run_ndnra_multieffect_experiment()

    assert result.shower_cleaning_success
    assert result.shower_reused_for_cooling
    assert shower_result.selected is not None
    assert shower_result.selected.actions == ("take_cold_shower",)
    assert result.shower_origin_need_code == "increase_cleanliness"


def test_separate_window_memories_compose_an_unseen_cooling_solution() -> None:
    result, graph, _, shared_result = run_ndnra_multieffect_experiment()

    assert not graph.has_stored_action_sequence(("open_window", "wait_for_cool_wind"))
    assert not result.direct_window_solution_success
    assert result.composed_window_solution_success
    assert result.selected_window_actions == (
        "open_window",
        "wait_for_cool_wind",
    )
    assert result.window_beats_shower_in_shared_context
    assert shared_result.selected is not None
    assert shared_result.selected.depth == 2


def test_composition_respects_conditions_and_rejects_hot_shower_for_cooling() -> None:
    graph = build_multieffect_graph()
    composer = NeedDrivenComposer(graph, maximum_depth=3)

    no_wind = composer.compose(
        need=cooling_need(),
        current_facts=("window_available",),
    )
    hot_only = composer.compose(
        need=cooling_need(),
        current_facts=("shower_available", "hot_water_available"),
    )

    assert not no_wind.success
    assert not hot_only.success


def test_intended_effect_only_baseline_cannot_reuse_shower_for_cooling() -> None:
    baseline = build_intended_effect_only_baseline()
    result = NeedDrivenComposer(baseline, maximum_depth=2).compose(
        need=cooling_need(),
        current_facts=("shower_available", "cold_water_available"),
    )

    assert not result.success


def test_complete_multieffect_gate_passes_without_sqlite() -> None:
    result, _, _, _ = run_ndnra_multieffect_experiment()

    assert result.effect_dimension_count >= 8
    assert result.explored_state_count > 0
    assert not result.complete_window_sequence_was_stored
    assert not result.baseline_without_incidental_effect_success
    assert not result.sqlite_used_for_composition
    assert result.pass_gate


def test_multieffect_prototype_has_no_sqlite_dependency() -> None:
    files = (
        Path("src/seedmind/research/ndnra/effects.py"),
        Path("src/seedmind/research/ndnra/composition.py"),
        Path("src/seedmind/research/ndnra/multieffect_experiment.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
