"""Tests for the main SeedMind Week 8 reusable skill."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    NurseryState,
    ShapeCode,
)
from seedmind.skills import (
    ApproachAndPushSkillController,
    SkillAttemptSource,
    SkillCompileFailure,
    SkillEpisodeEvidence,
    SkillExecutionStatus,
    SkillRecord,
    SkillStepDecision,
    SkillStepEvidence,
    compile_approach_and_push_skill,
    read_skill_record,
    retain_skill_candidate_through_curiosity,
    write_skill_record,
)


def successful_episode(seed: int, *, source: SkillAttemptSource) -> SkillEpisodeEvidence:
    return SkillEpisodeEvidence(
        episode_id=f"episode-{seed}",
        seed=seed,
        source=source,
        target_object_id="object_0",
        target_id="target_0",
        steps=(
            SkillStepEvidence(
                action=PrimitiveAction.MOVE_FORWARD,
                outcome="moved",
                action_available=True,
                world_changed=True,
            ),
            SkillStepEvidence(
                action=PrimitiveAction.PUSH,
                outcome="pushed",
                action_available=True,
                world_changed=True,
            ),
        ),
        success=True,
    )


def compile_record() -> SkillRecord:
    result = compile_approach_and_push_skill(
        tuple(
            successful_episode(seed, source=SkillAttemptSource.GROUNDED_PRODUCTION)
            for seed in (1, 2, 3)
        )
    )
    assert result.record is not None
    return result.record


def test_compiler_requires_repeated_grounded_success() -> None:
    result = compile_approach_and_push_skill(
        (successful_episode(1, source=SkillAttemptSource.GROUNDED_PRODUCTION),),
    )

    assert result.compiled is False
    assert result.failure is SkillCompileFailure.INSUFFICIENT_EVIDENCE


def test_compiler_rejects_incomplete_sequence() -> None:
    incomplete = replace(
        successful_episode(1, source=SkillAttemptSource.GROUNDED_PRODUCTION),
        steps=(
            SkillStepEvidence(
                action=PrimitiveAction.PUSH,
                outcome="pushed",
                action_available=True,
                world_changed=True,
            ),
        ),
    )

    result = compile_approach_and_push_skill((incomplete, incomplete, incomplete))

    assert result.failure is SkillCompileFailure.INCOMPLETE_SEQUENCE


def test_compiler_rejects_contradictory_target_task() -> None:
    first = successful_episode(1, source=SkillAttemptSource.GROUNDED_PRODUCTION)
    second = replace(
        successful_episode(2, source=SkillAttemptSource.GROUNDED_PRODUCTION),
        target_id="target_1",
    )

    result = compile_approach_and_push_skill((first, second, first))

    assert result.failure is SkillCompileFailure.CONTRADICTORY_SEQUENCE


def test_compiler_rejects_unavailable_or_unsafe_primitive() -> None:
    bad = replace(
        successful_episode(1, source=SkillAttemptSource.GROUNDED_PRODUCTION),
        steps=(
            SkillStepEvidence(
                action=PrimitiveAction.PUSH,
                outcome="pushed",
                action_available=False,
                world_changed=True,
            ),
        ),
    )

    result = compile_approach_and_push_skill((bad, bad, bad))

    assert result.failure is SkillCompileFailure.UNSAFE_OR_UNAVAILABLE_ACTION


def test_compiler_rejects_imagination_and_evaluation_evidence() -> None:
    imagined = successful_episode(1, source=SkillAttemptSource.BOUNDED_IMAGINATION)
    evaluation = replace(
        successful_episode(2, source=SkillAttemptSource.EVALUATION),
        used_for_evaluation=True,
    )

    imagined_result = compile_approach_and_push_skill((imagined, imagined, imagined))
    evaluation_result = compile_approach_and_push_skill((evaluation, evaluation, evaluation))

    assert imagined_result.failure is SkillCompileFailure.NON_GROUNDED_SOURCE
    assert evaluation_result.failure is SkillCompileFailure.NON_GROUNDED_SOURCE


def test_controller_detects_preconditions_and_termination() -> None:
    controller = ApproachAndPushSkillController(compile_record())
    state = create_state(
        agent=GridPosition(1, 1),
        ball=GridPosition(3, 3),
        target=GridPosition(3, 3),
    )

    decision = controller.decide(state, tuple(PrimitiveAction))

    assert decision.status is SkillExecutionStatus.TERMINATED
    assert decision.reason_code == "target_occupied"


def test_controller_fails_when_task_or_target_changes_incompatibly() -> None:
    record = compile_record()
    controller = ApproachAndPushSkillController(record, target_id="target_1")
    state = create_state(
        agent=GridPosition(1, 1),
        ball=GridPosition(3, 3),
        target=GridPosition(4, 3),
    )

    decision = controller.decide(state, tuple(PrimitiveAction))

    assert decision.status is SkillExecutionStatus.FAILED
    assert decision.reason_code == "target_missing"


def test_controller_reports_unavailable_required_action_without_executing() -> None:
    controller = ApproachAndPushSkillController(compile_record())
    state = create_state(
        agent=GridPosition(1, 1),
        ball=GridPosition(3, 3),
        target=GridPosition(4, 3),
    )

    decision = controller.decide(state, (PrimitiveAction.WAIT,))

    assert decision.status is SkillExecutionStatus.FAILED
    assert decision.reason_code == "required_action_unavailable"


def test_controller_interrupts_on_human_or_safety_stop() -> None:
    controller = ApproachAndPushSkillController(compile_record())
    state = create_state(
        agent=GridPosition(1, 1),
        ball=GridPosition(3, 3),
        target=GridPosition(4, 3),
    )

    decision = controller.decide(state, tuple(PrimitiveAction), human_interrupt=True)

    assert decision.status is SkillExecutionStatus.INTERRUPTED
    assert decision.reason_code == "human_or_safety_interrupt"


def test_skill_candidate_must_pass_through_production_curiosity() -> None:
    decision = SkillStepDecision(
        status=SkillExecutionStatus.ACTION,
        action=PrimitiveAction.MOVE_FORWARD,
        reason_code="candidate",
        skill_invoked=True,
    )

    retained = retain_skill_candidate_through_curiosity(decision)

    assert retained.retained_by == "production_curiosity"
    assert retained.retained_action is PrimitiveAction.MOVE_FORWARD


def test_skill_decision_rejects_action_authority_bypass() -> None:
    with pytest.raises(ValueError, match="action authority"):
        SkillStepDecision(
            status=SkillExecutionStatus.ACTION,
            action=PrimitiveAction.PUSH,
            reason_code="candidate",
            skill_invoked=True,
            action_authority_violation=True,
        )


def test_corrupted_skill_record_is_not_partially_accepted(tmp_path: Path) -> None:
    path = tmp_path / "skill.json"
    write_skill_record(compile_record(), path)
    payload = path.read_text(encoding="ascii").replace(
        '"schema_version": 1', '"schema_version": 99'
    )
    path.write_text(payload, encoding="ascii")

    with pytest.raises(ValueError, match="schema"):
        read_skill_record(path)


def create_state(
    *,
    agent: GridPosition,
    ball: GridPosition,
    target: GridPosition,
) -> NurseryState:
    return NurseryState(
        width=7,
        height=7,
        agent=AgentState(position=agent, orientation=Direction.EAST),
        entities=(
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=ball,
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ROUND,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=target,
                blocks_movement=False,
                movable=False,
            ),
        ),
    )
