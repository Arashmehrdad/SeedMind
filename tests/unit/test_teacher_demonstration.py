"""Tests for deterministic repeatable teacher demonstrations."""

from dataclasses import replace

import pytest

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    EntityRole,
    NurseryRuntime,
    TeacherDemonstrationScenarioFactory,
    TeacherPushDemonstrationProcess,
)


def entity_position(runtime: NurseryRuntime, entity_id: str) -> GridPosition:
    return next(
        entity.position for entity in runtime.state.entities if entity.entity_id == entity_id
    )


def test_teacher_demonstration_moves_object_to_target_in_two_steps() -> None:
    scenario = TeacherDemonstrationScenarioFactory().create(7)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id="teacher-demo-0",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    first = runtime.step(PrimitiveAction.WAIT)
    second = runtime.step(PrimitiveAction.WAIT)
    assert entity_position(runtime, "teacher_0") == GridPosition(3, 3)
    assert entity_position(runtime, "object_0") == GridPosition(4, 3)
    assert scenario.target_occupancy(runtime.state).occupied_target_ids == ("target_0",)
    assert len(first.process_events) == 2
    assert len(second.process_events) == 2
    assert all(event.changed for event in (*first.process_events, *second.process_events))


def test_teacher_demonstration_is_repeatable_after_reset() -> None:
    scenario = TeacherDemonstrationScenarioFactory().create(11)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id="teacher-demo-first",
        world_processes=scenario.world_processes,
    )
    first_start = runtime.observe().sensor_values
    runtime.step(PrimitiveAction.WAIT)
    first_end = runtime.step(PrimitiveAction.WAIT).observation.sensor_values
    runtime.reset(episode_id="teacher-demo-second")
    second_start = runtime.observe().sensor_values
    runtime.step(PrimitiveAction.WAIT)
    second_end = runtime.step(PrimitiveAction.WAIT).observation.sensor_values
    assert first_start == second_start
    assert first_end == second_end


def test_teacher_process_rejects_misaligned_initial_geometry() -> None:
    scenario = TeacherDemonstrationScenarioFactory().create(3)
    teacher = next(
        entity for entity in scenario.initial_state.entities if entity.role is EntityRole.TEACHER
    )
    misaligned = scenario.initial_state.replace_entity(
        teacher.entity_id,
        replace(teacher, position=GridPosition(1, 2)),
    )
    process = TeacherPushDemonstrationProcess(
        process_id="demo",
        teacher_id="teacher_0",
        object_id="object_0",
        target_id="target_0",
        direction=Direction.EAST,
    )
    with pytest.raises(ValueError, match="directly behind"):
        process.validate(misaligned)


def test_teacher_process_rejects_empty_identifier() -> None:
    with pytest.raises(ValueError, match="process_id"):
        TeacherPushDemonstrationProcess(
            process_id="",
            teacher_id="teacher_0",
            object_id="object_0",
            target_id="target_0",
            direction=Direction.EAST,
        )


def test_teacher_factory_rejects_small_budget() -> None:
    with pytest.raises(ValueError, match="step_budget"):
        TeacherDemonstrationScenarioFactory(step_budget=1)
