"""Tests for deterministic Nursery v0 scenario construction."""

import random
from dataclasses import replace

import pytest

from seedmind.environment import EntityRole, NurseryState
from seedmind.environment.scenario import (
    NurseryScenario,
    NurseryScenarioFactory,
    detect_target_occupancy,
)


def test_same_seed_produces_identical_scenario() -> None:
    factory = NurseryScenarioFactory()

    first = factory.create(seed=17)
    second = factory.create(seed=17)

    assert first == second


def test_different_seeds_produce_different_layouts() -> None:
    factory = NurseryScenarioFactory()

    first = factory.create(seed=17)
    second = factory.create(seed=18)

    assert first.initial_state != second.initial_state


def test_factory_does_not_mutate_global_random_state() -> None:
    factory = NurseryScenarioFactory()
    random.seed(1234)
    expected = random.random()
    random.seed(1234)

    factory.create(seed=99)
    actual = random.random()

    assert actual == expected


def test_factory_builds_valid_perimeter_and_distinct_interior_layout() -> None:
    scenario = NurseryScenarioFactory(width=7, height=7).create(seed=5)
    state = scenario.initial_state
    walls = tuple(
        entity for entity in state.entities if entity.role is EntityRole.WALL
    )
    blocking_positions = tuple(
        entity.position for entity in state.entities if entity.blocks_movement
    )

    assert len(walls) == 24
    assert len(blocking_positions) == len(set(blocking_positions))
    assert state.agent.position not in blocking_positions
    assert all(
        wall.position.x in (0, state.width - 1)
        or wall.position.y in (0, state.height - 1)
        for wall in walls
    )


def test_scenario_contains_two_raw_shape_objects_and_two_targets() -> None:
    state = NurseryScenarioFactory().create(seed=11).initial_state
    objects = tuple(
        entity for entity in state.entities if entity.role is EntityRole.OBJECT
    )
    targets = tuple(
        entity for entity in state.entities if entity.role is EntityRole.TARGET
    )

    assert len(objects) == 2
    assert len(targets) == 2
    assert objects[0].shape_code != objects[1].shape_code
    assert all(target.blocks_movement is False for target in targets)


def test_resource_state_tracks_normalized_remaining_budget() -> None:
    scenario = NurseryScenarioFactory(step_budget=10).create(seed=3)

    assert scenario.resource_state(scenario.initial_state) == (1.0,)
    assert scenario.resource_state(replace(scenario.initial_state, step_count=5)) == (
        0.5,
    )
    assert scenario.resource_state(replace(scenario.initial_state, step_count=10)) == (
        0.0,
    )
    assert scenario.resource_state(replace(scenario.initial_state, step_count=12)) == (
        0.0,
    )


def test_target_occupancy_detects_object_on_target() -> None:
    scenario = NurseryScenarioFactory().create(seed=7)
    state = scenario.initial_state
    object_entity = next(
        entity for entity in state.entities if entity.role is EntityRole.OBJECT
    )
    target_entity = next(
        entity for entity in state.entities if entity.role is EntityRole.TARGET
    )
    moved_object = object_entity.moved_to(target_entity.position)
    updated = state.replace_entity(object_entity.entity_id, moved_object)

    occupancy = detect_target_occupancy(updated)

    assert occupancy.target_count == 2
    assert occupancy.occupied_count == 1
    assert occupancy.occupied_target_ids == (target_entity.entity_id,)
    assert occupancy.object_target_pairs == (
        (object_entity.entity_id, target_entity.entity_id),
    )
    assert occupancy.all_targets_occupied is False


def test_target_occupancy_requires_at_least_one_target_for_completion() -> None:
    reference = NurseryScenarioFactory(width=5, height=5).create(seed=1)
    empty = NurseryState(
        width=5,
        height=5,
        agent=reference.initial_state.agent,
        entities=(),
    )

    occupancy = detect_target_occupancy(empty)

    assert occupancy.target_count == 0
    assert occupancy.all_targets_occupied is False


@pytest.mark.parametrize(
    "factory",
    [
        NurseryScenarioFactory(width=5, height=5, step_budget=1),
    ],
)
def test_minimum_supported_factory_dimensions(factory: NurseryScenarioFactory) -> None:
    scenario = factory.create(seed=0)

    assert scenario.initial_state.width == 5
    assert scenario.initial_state.height == 5


@pytest.mark.parametrize(
    ("width", "height", "step_budget", "message"),
    [
        (4, 7, 150, "at least 5"),
        (7, 4, 150, "at least 5"),
        (7, 7, 0, "positive"),
    ],
)
def test_factory_rejects_invalid_configuration(
    width: int,
    height: int,
    step_budget: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        NurseryScenarioFactory(
            width=width,
            height=height,
            step_budget=step_budget,
        )


def test_factory_rejects_negative_seed() -> None:
    with pytest.raises(ValueError, match="seed"):
        NurseryScenarioFactory().create(seed=-1)


def test_scenario_rejects_invalid_metadata() -> None:
    baseline = NurseryScenarioFactory().create(seed=1)

    with pytest.raises(ValueError, match="scenario_id"):
        NurseryScenario(
            scenario_id=" ",
            seed=baseline.seed,
            initial_state=baseline.initial_state,
            step_budget=baseline.step_budget,
        )


def test_scenario_resource_evaluation_is_state_based() -> None:
    scenario = NurseryScenarioFactory(step_budget=20).create(seed=4)
    unrelated_state = replace(scenario.initial_state, step_count=7)

    assert scenario.remaining_steps(unrelated_state) == 13
    assert scenario.target_occupancy(unrelated_state) == detect_target_occupancy(
        unrelated_state
    )
