"""Tests for graph-locally derived structural-growth saturation."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import LocalSaturationReport
from seedmind.research.ndnra.growth import (
    EvidenceDrivenGrowthController,
    StructuralGrowthConfig,
)
from seedmind.research.ndnra.growth_experiment import build_capacity_limited_graph


def test_first_unresolved_event_has_zero_local_saturation_and_no_pressure() -> None:
    graph = build_capacity_limited_graph()
    controller = EvidenceDrivenGrowthController(graph)
    members = ("assembly:apply_wet_cloth", "assembly:activate_fan")
    predicted = graph.project_effects(members)["temperature"]

    attempt = controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=1.0,
        ambition_relevance=1.0,
    )

    assert attempt.local_saturation.active_assembly_ids == (
        "assembly:activate_fan",
        "assembly:apply_wet_cloth",
    )
    assert attempt.local_saturation.active_eligibility_before == (
        ("assembly:activate_fan", 0.0),
        ("assembly:apply_wet_cloth", 0.0),
    )
    assert attempt.local_saturation.minimum_active_eligibility == 0.0
    assert attempt.local_saturation.mean_active_eligibility == 0.0
    assert not attempt.local_saturation.locally_saturated
    assert attempt.local_saturation.saturation == 0.0
    assert attempt.growth_pressure == 0.0


def test_repeated_identical_local_interaction_builds_deterministic_saturation() -> None:
    graph = build_capacity_limited_graph()
    controller = EvidenceDrivenGrowthController(graph)
    members = ("assembly:apply_wet_cloth", "assembly:activate_fan")
    predicted = graph.project_effects(members)["temperature"]

    first = controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=1.0,
        ambition_relevance=1.0,
    )
    second = controller.observe_unresolved_interaction(
        active_assembly_ids=tuple(reversed(members)),
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=1.0,
        ambition_relevance=1.0,
    )
    third = controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=1.0,
        ambition_relevance=1.0,
    )

    assert first.local_saturation.saturation == 0.0
    assert second.local_saturation.active_assembly_ids == (
        "assembly:activate_fan",
        "assembly:apply_wet_cloth",
    )
    assert second.local_saturation.active_eligibility_before == (
        ("assembly:activate_fan", 1.0),
        ("assembly:apply_wet_cloth", 1.0),
    )
    assert second.local_saturation == third.local_saturation
    assert second.local_saturation.minimum_active_eligibility == 1.0
    assert second.local_saturation.mean_active_eligibility == 1.0
    assert second.local_saturation.locally_saturated
    assert second.local_saturation.saturation == 1.0
    assert second.growth_pressure > first.growth_pressure
    assert third.growth_ready
    assert controller.growth_ready


def test_low_current_saturation_blocks_growth_even_with_preloaded_pressure() -> None:
    graph = build_capacity_limited_graph()
    controller = EvidenceDrivenGrowthController(graph)
    members = ("assembly:apply_wet_cloth", "assembly:activate_fan")
    predicted = graph.project_effects(members)["temperature"]

    controller._eligibility[members[0]] = 0.74
    controller._eligibility[members[1]] = 1.0
    controller.pressure.value = 1.0

    attempt = controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=1.0,
        ambition_relevance=1.0,
    )

    assert attempt.local_saturation.minimum_active_eligibility == 0.74
    assert not attempt.local_saturation.locally_saturated
    assert attempt.local_saturation.saturation == 0.0
    assert not attempt.growth_ready
    assert not controller.growth_ready


def test_zero_residual_high_local_saturation_does_not_increase_pressure() -> None:
    graph = build_capacity_limited_graph()
    controller = EvidenceDrivenGrowthController(graph)
    members = ("assembly:apply_wet_cloth", "assembly:activate_fan")
    predicted = graph.project_effects(members)["temperature"]

    controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=1.0,
        ambition_relevance=1.0,
    )
    pressure_before = controller.pressure.value
    attempt = controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=predicted,
        curiosity=1.0,
        ambition_relevance=1.0,
    )

    assert attempt.local_saturation.locally_saturated
    assert attempt.unresolved_error == 0.0
    assert attempt.growth_pressure == pressure_before


def test_duplicate_membership_and_full_capacity_force_zero_saturation() -> None:
    graph = build_capacity_limited_graph()
    controller = EvidenceDrivenGrowthController(graph)
    members = ("assembly:apply_wet_cloth", "assembly:activate_fan")
    predicted = graph.project_effects(members)["temperature"]

    for _ in range(3):
        controller.observe_unresolved_interaction(
            active_assembly_ids=members,
            predicted_effect=predicted,
            actual_effect=-0.90,
            curiosity=1.0,
            ambition_relevance=1.0,
        )
    controller.grow_targeted_specialist(
        specialist_id="specialist:evaporative_cooling",
        effect_code="temperature",
    )

    duplicate_attempt = controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=1.0,
        ambition_relevance=1.0,
    )

    assert duplicate_attempt.local_saturation.duplicate_membership_exists
    assert not duplicate_attempt.local_saturation.capacity_available
    assert duplicate_attempt.local_saturation.saturation == 0.0

    second_graph = build_capacity_limited_graph()
    full_controller = EvidenceDrivenGrowthController(
        second_graph,
        StructuralGrowthConfig(maximum_specialists=1),
    )
    second_graph.grow_specialist_interaction(
        specialist_id="specialist:other_capacity",
        member_assembly_ids=(
            "assembly:apply_wet_cloth",
            "assembly:inspect_wall",
        ),
        origin_code="unit_test",
    )
    full_controller._eligibility["assembly:apply_wet_cloth"] = 1.0
    full_controller._eligibility["assembly:activate_fan"] = 1.0

    full_attempt = full_controller.observe_unresolved_interaction(
        active_assembly_ids=members,
        predicted_effect=predicted,
        actual_effect=-0.90,
        curiosity=1.0,
        ambition_relevance=1.0,
    )

    assert full_attempt.local_saturation.capacity_available is False
    assert full_attempt.local_saturation.duplicate_membership_exists is False
    assert full_attempt.local_saturation.saturation == 0.0


def test_local_saturation_report_is_sorted_bounded_and_self_validating() -> None:
    report = LocalSaturationReport(
        active_assembly_ids=("assembly:a", "assembly:b"),
        active_eligibility_before=(("assembly:a", 0.8), ("assembly:b", 0.9)),
        assembly_count=3,
        specialist_count=0,
        maximum_specialists=2,
        remaining_specialist_slots=2,
        capacity_available=True,
        duplicate_membership_exists=False,
        minimum_active_eligibility_for_saturation=0.75,
        minimum_active_eligibility=0.8,
        mean_active_eligibility=0.85,
        locally_saturated=True,
        saturation=0.8,
    )

    assert report.saturation == 0.8
    assert report.active_assembly_ids == ("assembly:a", "assembly:b")

    with pytest.raises(ValueError, match="stable sorted order"):
        LocalSaturationReport(
            active_assembly_ids=("assembly:b", "assembly:a"),
            active_eligibility_before=(("assembly:a", 0.8), ("assembly:b", 0.9)),
            assembly_count=3,
            specialist_count=0,
            maximum_specialists=2,
            remaining_specialist_slots=2,
            capacity_available=True,
            duplicate_membership_exists=False,
            minimum_active_eligibility_for_saturation=0.75,
            minimum_active_eligibility=0.8,
            mean_active_eligibility=0.85,
            locally_saturated=True,
            saturation=0.8,
        )

    with pytest.raises(ValueError, match="saturation must match local saturation rule"):
        LocalSaturationReport(
            active_assembly_ids=("assembly:a", "assembly:b"),
            active_eligibility_before=(("assembly:a", 0.6), ("assembly:b", 0.9)),
            assembly_count=3,
            specialist_count=0,
            maximum_specialists=2,
            remaining_specialist_slots=2,
            capacity_available=True,
            duplicate_membership_exists=False,
            minimum_active_eligibility_for_saturation=0.75,
            minimum_active_eligibility=0.6,
            mean_active_eligibility=0.75,
            locally_saturated=False,
            saturation=0.6,
        )


def test_local_saturation_path_has_no_forbidden_runtime_dependencies() -> None:
    source = "\n".join(
        path.read_text(encoding="ascii").lower()
        for path in (
            Path("src/seedmind/research/ndnra/growth.py"),
            Path("src/seedmind/research/ndnra/growth_experiment.py"),
            Path("src/seedmind/research/ndnra/multi_growth_experiment.py"),
        )
    )

    for forbidden in (
        "import sqlite3",
        "seedmind.integration",
        "bounded_imagination",
        "asyncio",
        "threading",
        "subprocess",
        "schedule(",
        "execute(",
        "recommend(",
        "production_action_authority",
    ):
        assert forbidden not in source
