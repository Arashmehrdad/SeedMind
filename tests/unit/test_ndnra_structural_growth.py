"""Tests for evidence-driven NDNRA specialist-neuron growth."""

from pathlib import Path

import pytest

from seedmind.research.ndnra.composition import NeedDrivenComposer
from seedmind.research.ndnra.growth import EvidenceDrivenGrowthController
from seedmind.research.ndnra.growth_experiment import (
    build_capacity_limited_graph,
    run_ndnra_structural_growth_experiment,
    structural_cooling_need,
)


def test_interaction_specialist_adds_non_additive_effect_once() -> None:
    graph = build_capacity_limited_graph()
    members = (
        "assembly:apply_wet_cloth",
        "assembly:activate_fan",
    )
    before = graph.project_effects(members)["temperature"]
    graph.grow_specialist_interaction(
        specialist_id="specialist:test_evaporation",
        member_assembly_ids=members,
        origin_code="unit_test",
        observed_effects=(),
    )
    empty_specialist = graph.project_effects(members)["temperature"]

    assert empty_specialist == pytest.approx(before)
    assert graph.specialist_count == 1
    assert graph.structural_node_count == graph.assembly_count + 1


def test_growth_does_not_trigger_from_one_failure() -> None:
    graph = build_capacity_limited_graph()
    controller = EvidenceDrivenGrowthController(graph)
    members = (
        "assembly:apply_wet_cloth",
        "assembly:activate_fan",
    )
    predicted = graph.project_effects(members)["temperature"]

    attempt = controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=0.95,
        ambition_relevance=1.0,
        capacity_saturation=1.0,
    )

    assert not attempt.growth_ready
    assert not controller.growth_ready
    with pytest.raises(RuntimeError, match="evidence gate"):
        controller.grow_targeted_specialist(
            specialist_id="specialist:too_early",
            effect_code="temperature",
        )


def test_targeted_growth_uses_high_eligibility_members() -> None:
    result, targeted_graph, _, attempts = run_ndnra_structural_growth_experiment()

    assert result.first_growth_ready_attempt == 3
    assert result.premature_growth_blocked
    assert result.targeted_specialist_members == (
        "assembly:apply_wet_cloth",
        "assembly:activate_fan",
    )
    assert all(
        dict(attempt.eligibility_traces).get("assembly:inspect_wall", 0.0) == 0.0
        for attempt in attempts
    )
    assert targeted_graph.specialist_count == 1


def test_targeted_growth_solves_blockage_and_random_capacity_does_not() -> None:
    result, targeted_graph, random_graph, _ = run_ndnra_structural_growth_experiment()

    assert not result.before_growth_success
    assert result.targeted_solution_success
    assert result.targeted_actions == ("apply_wet_cloth", "activate_fan")
    assert not result.random_solution_success
    assert result.targeted_beats_random
    assert targeted_graph.structural_node_count == random_graph.structural_node_count


def test_old_assemblies_are_preserved_without_pruning() -> None:
    result, targeted_graph, _, _ = run_ndnra_structural_growth_experiment()

    assert result.targeted_old_assemblies_preserved
    assert targeted_graph.assembly_count == result.base_assembly_count
    assert result.targeted_structural_nodes_after == result.base_structural_node_count + 1
    assert result.duplicate_growth_blocked


def test_complete_structural_growth_gate_passes() -> None:
    result, _, _, _ = run_ndnra_structural_growth_experiment()

    assert result.final_growth_pressure >= 0.75
    assert result.targeted_primary_satisfaction >= structural_cooling_need().satisfaction_threshold
    assert not result.sqlite_used_for_growth
    assert result.pass_gate


def test_structural_growth_prototype_has_no_sqlite_dependency() -> None:
    files = (
        Path("src/seedmind/research/ndnra/growth.py"),
        Path("src/seedmind/research/ndnra/growth_experiment.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source


def test_base_graph_still_fails_without_specialist() -> None:
    graph = build_capacity_limited_graph()
    result = NeedDrivenComposer(graph, maximum_depth=2).compose(
        need=structural_cooling_need(),
        current_facts=("wet_cloth_available", "fan_available", "wall_visible"),
    )

    assert not result.success
