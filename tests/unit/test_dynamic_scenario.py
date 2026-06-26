"""Tests for the reproducible dynamic nursery scenario."""

import pytest

from seedmind.contracts import PrimitiveAction
from seedmind.environment import (
    DynamicNurseryScenarioFactory,
    NurseryRuntime,
    SeedMindNurseryEnv,
)


def entity_position(runtime: NurseryRuntime, entity_id: str) -> tuple[int, int]:
    entity = next(entity for entity in runtime.state.entities if entity.entity_id == entity_id)
    return entity.position.x, entity.position.y


def entity_blocks(runtime: NurseryRuntime, entity_id: str) -> bool:
    entity = next(entity for entity in runtime.state.entities if entity.entity_id == entity_id)
    return entity.blocks_movement


def test_same_seed_produces_identical_dynamic_scenario() -> None:
    factory = DynamicNurseryScenarioFactory()

    first = factory.create(seed=21)
    second = factory.create(seed=21)

    assert first == second
    assert len(first.world_processes) == 3


def test_dynamic_scenario_changes_during_wait() -> None:
    scenario = DynamicNurseryScenarioFactory().create(seed=4)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=scenario.scenario_id,
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    teacher_before = entity_position(runtime, "teacher_0")
    object_before = entity_position(runtime, "object_0")

    first_tick = runtime.step(PrimitiveAction.WAIT)

    assert entity_position(runtime, "teacher_0") != teacher_before
    assert entity_position(runtime, "object_0") != object_before
    assert first_tick.external_world_changed is True
    assert len(first_tick.process_events) == 2
    assert runtime.state.step_count == 1


def test_periodic_door_changes_on_second_tick() -> None:
    scenario = DynamicNurseryScenarioFactory().create(seed=4)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=scenario.scenario_id,
        world_processes=scenario.world_processes,
    )

    assert entity_blocks(runtime, "door_0") is False
    runtime.step(PrimitiveAction.WAIT)
    assert entity_blocks(runtime, "door_0") is False
    second_tick = runtime.step(PrimitiveAction.WAIT)

    assert entity_blocks(runtime, "door_0") is True
    assert len(second_tick.process_events) == 3
    assert runtime.state.step_count == 2


def test_reset_restores_dynamic_world_and_process_phase() -> None:
    scenario = DynamicNurseryScenarioFactory().create(seed=8)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=scenario.scenario_id,
        world_processes=scenario.world_processes,
    )
    initial_teacher = entity_position(runtime, "teacher_0")
    initial_object = entity_position(runtime, "object_0")

    runtime.step(PrimitiveAction.WAIT)
    runtime.step(PrimitiveAction.WAIT)
    runtime.reset()

    assert entity_position(runtime, "teacher_0") == initial_teacher
    assert entity_position(runtime, "object_0") == initial_object
    assert entity_blocks(runtime, "door_0") is False
    assert runtime.state.step_count == 0


def test_gymnasium_environment_carries_scenario_processes() -> None:
    scenario = DynamicNurseryScenarioFactory(step_budget=4).create(seed=2)
    env = SeedMindNurseryEnv.from_scenario(scenario)
    teacher_before = entity_position(env.runtime, "teacher_0")

    env.reset()
    env.step(env.action_index(PrimitiveAction.WAIT))

    assert len(env.runtime.world_processes) == 3
    assert entity_position(env.runtime, "teacher_0") != teacher_before


@pytest.mark.parametrize(
    ("width", "height", "step_budget", "message"),
    [
        (6, 7, 150, "at least 7"),
        (7, 6, 150, "at least 7"),
        (7, 7, 0, "positive"),
    ],
)
def test_dynamic_factory_rejects_invalid_configuration(
    width: int,
    height: int,
    step_budget: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        DynamicNurseryScenarioFactory(
            width=width,
            height=height,
            step_budget=step_budget,
        )


def test_dynamic_factory_rejects_negative_seed() -> None:
    with pytest.raises(ValueError, match="seed"):
        DynamicNurseryScenarioFactory().create(seed=-1)
