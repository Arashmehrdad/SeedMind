"""Focused tests for original Week 10 capacity diagnosis."""

from __future__ import annotations

import filecmp
from pathlib import Path

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    NurseryObservationAdapter,
    NurseryRuntime,
    NurseryState,
    ShapeCode,
    TransitionOutcome,
)
from seedmind.growth import (
    DiagnosticStepCode,
    LearningAttempt,
    LearningProgressThresholds,
    PlateauClassification,
    Week10RunResult,
    Week10ScenarioDiagnosis,
    build_learning_progress_windows,
    run_week10_capacity_diagnosis,
)


def test_cube_like_raw_dynamics_differ_from_ball_without_breaking_ball_push() -> None:
    round_outcome = _push_outcome(_state(ShapeCode.ROUND, near_wall=True))
    angular_wall_outcome = _push_outcome(_state(ShapeCode.ANGULAR, near_wall=True))
    angular_open_outcome = _push_outcome(_state(ShapeCode.ANGULAR, near_wall=False))

    assert round_outcome is TransitionOutcome.PUSHED
    assert angular_wall_outcome is TransitionOutcome.PUSH_INEFFECTIVE_CONTACT
    assert angular_open_outcome is TransitionOutcome.PUSHED


def test_policy_facing_observation_has_raw_shape_not_privileged_cube_label() -> None:
    state = _state(ShapeCode.ANGULAR, near_wall=False)
    packet = NurseryObservationAdapter(width=6, height=6).observe(state, episode_id="obs")

    assert all(isinstance(value, float) for value in packet.sensor_values)
    assert "cube" not in repr(packet).lower()
    assert max(packet.sensor_values) == 1.0


def test_frozen_week8_skill_record_is_not_modified_or_recompiled() -> None:
    result = run_week10_capacity_diagnosis()

    assert result.acceptance_report.frozen_skill_preservation_pass
    assert (
        result.acceptance_report.frozen_skill_sha256_before
        == result.acceptance_report.frozen_skill_sha256_after
    )
    assert result.familiar_control_success_rate == 1.0


def test_learning_progress_windows_are_deterministic_and_require_minimum_evidence() -> None:
    thresholds = LearningProgressThresholds()
    attempts = tuple(
        LearningAttempt(
            attempt_index=index,
            scenario_family="early",
            strategy="frozen_skill",
            success=False,
            task_progress=0.05,
            steps_used=4,
            prediction_error=0.60,
            invalid_or_ineffective_actions=1,
        )
        for index in range(4)
    )

    first = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="early",
        strategy_variants_exhausted=False,
        replay_attempted=False,
        help_or_demonstration_considered=False,
    )
    second = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="early",
        strategy_variants_exhausted=False,
        replay_attempted=False,
        help_or_demonstration_considered=False,
    )

    assert first == second
    assert first[-1].classification is PlateauClassification.INSUFFICIENT_EVIDENCE


def test_one_failure_and_improving_sequence_do_not_create_sustained_blockage() -> None:
    result = run_week10_capacity_diagnosis()
    early = _diagnosis(result, "early_cube_evidence")
    temporary = _diagnosis(result, "temporary_cube_recovery")

    assert early.classification is PlateauClassification.INSUFFICIENT_EVIDENCE
    assert early.proposal_generated is False
    assert temporary.classification is PlateauClassification.IMPROVING
    assert temporary.proposal_generated is False
    assert temporary.replay.progress_resumed
    assert temporary.help.performance_improved_afterward


def test_sustained_blockage_requires_multiple_windows_and_full_ladder() -> None:
    result = run_week10_capacity_diagnosis()
    sustained = _diagnosis(result, "sustained_cube_blockage")

    assert len(sustained.windows) == 3
    assert sustained.classification is PlateauClassification.SUSTAINED_BLOCKAGE
    assert sustained.ladder.completed_for_growth_proposal
    assert tuple(step.code for step in sustained.ladder.steps) == (
        DiagnosticStepCode.CONFIRM_TASK,
        DiagnosticStepCode.SAFE_EXPLORATION,
        DiagnosticStepCode.RETRIEVE_MEMORY,
        DiagnosticStepCode.ATTEMPT_EXISTING_SKILL,
        DiagnosticStepCode.TRY_STRATEGIES,
        DiagnosticStepCode.REQUEST_HELP,
        DiagnosticStepCode.MEMORY_REPLAY,
        DiagnosticStepCode.CHECK_PREDICTION,
        DiagnosticStepCode.CHECK_IMPROVEMENT,
        DiagnosticStepCode.INFER_LIMITATION,
        DiagnosticStepCode.PRODUCE_PROPOSAL,
    )


def test_growth_cannot_be_proposed_before_non_growth_checks_pass() -> None:
    result = run_week10_capacity_diagnosis()

    assert _diagnosis(result, "early_cube_evidence").proposal_generated is False
    assert _diagnosis(result, "temporary_cube_recovery").proposal_generated is False
    assert _diagnosis(result, "ambiguous_non_capacity_blockage").proposal_generated is False
    assert _diagnosis(result, "sustained_cube_blockage").proposal_generated is True


def test_ambiguous_unsafe_impossible_or_resource_limited_cases_do_not_produce_growth() -> None:
    result = run_week10_capacity_diagnosis()
    non_capacity = _diagnosis(result, "ambiguous_non_capacity_blockage")

    assert non_capacity.proposal_generated is False
    assert non_capacity.ladder.stopped_early
    assert (
        non_capacity.non_capacity_reason == "ambiguous_goal_resource_limit_or_impossible_geometry"
    )
    assert result.acceptance_report.non_capacity_blockage_pass


def test_memory_replay_uses_grounded_main_memory_and_can_block_growth() -> None:
    result = run_week10_capacity_diagnosis()
    temporary = _diagnosis(result, "temporary_cube_recovery")

    assert temporary.replay.relevant_memory_ids
    assert all("grounded-contact" in event_id for event_id in temporary.replay.relevant_memory_ids)
    assert temporary.replay.changed_strategy
    assert temporary.replay.progress_resumed
    assert temporary.proposal_generated is False


def test_help_and_demonstration_record_provenance_and_outcomes() -> None:
    result = run_week10_capacity_diagnosis()
    temporary = _diagnosis(result, "temporary_cube_recovery")
    sustained = _diagnosis(result, "sustained_cube_blockage")

    assert temporary.help.help_requested
    assert temporary.help.demonstration_available
    assert temporary.help.demonstration_provenance == "protected_teacher_response_policy"
    assert temporary.help.performance_improved_afterward
    assert sustained.help.help_requested
    assert sustained.help.demonstration_applied
    assert sustained.help.blockage_remained


def test_strategy_variants_are_bounded_and_do_not_create_specialists_or_mutate_skill() -> None:
    result = run_week10_capacity_diagnosis()

    assert len(result.strategy_variants) == 4
    assert all(
        variant.attempts <= variant.safe_attempt_budget for variant in result.strategy_variants
    )
    assert all(not variant.created_specialist for variant in result.strategy_variants)
    assert all(not variant.mutated_frozen_skill for variant in result.strategy_variants)


def test_exactly_sustained_blockage_creates_one_non_authoritative_proposal() -> None:
    result = run_week10_capacity_diagnosis()
    proposed = [diagnosis for diagnosis in result.diagnoses if diagnosis.proposal_generated]

    assert [diagnosis.scenario_family for diagnosis in proposed] == ["sustained_cube_blockage"]
    assert result.proposal.candidate.created is False
    assert result.proposal.status.value == "proposed_not_authorised"
    assert result.proposal.candidate.type == "skill_expert"
    assert result.proposal.candidate.parent_module == "general_push_controller"
    assert result.acceptance_report.specialist_created is False
    assert result.acceptance_report.router_created is False
    assert result.acceptance_report.week11_started is False


def test_acceptance_is_independent_of_ndnra_and_week10_imports_no_ndnra() -> None:
    result = run_week10_capacity_diagnosis()
    growth_sources = "\n".join(
        path.read_text(encoding="utf-8") for path in Path("src/seedmind/growth").glob("*.py")
    )

    assert result.acceptance_report.ndnra_required is False
    assert result.acceptance_report.frozen_ndnra_boundary_pass
    assert "seedmind.research.ndnra" not in growth_sources
    assert "parallel_comparison" not in growth_sources
    assert "parallel_operation" not in growth_sources


def test_visualisation_and_json_artifacts_are_deterministic_and_leave_no_tmp_files(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_week10_capacity_diagnosis(output_dir=first)
    run_week10_capacity_diagnosis(output_dir=second)

    expected = (
        "diagnostic_report.json",
        "growth_proposal_record.json",
        "learning_progress_windows.json",
        "plateau_visualisation.svg",
        "week10_acceptance_report.json",
    )
    for name in expected:
        assert (first / name).exists()
        assert filecmp.cmp(first / name, second / name, shallow=False)
    assert not tuple(first.glob("*.tmp"))
    assert not tuple(second.glob("*.tmp"))
    svg = (first / "plateau_visualisation.svg").read_text(encoding="ascii")
    windows_json = (first / "learning_progress_windows.json").read_text(encoding="ascii")
    assert "temporary recovery/improving" in svg
    assert "sustained blockage" in svg
    assert "temporary_cube_recovery-window-03" in windows_json
    assert "sustained_cube_blockage-window-03" in windows_json


def test_week10_acceptance_uses_separate_fields_without_ambiguous_pass_gate() -> None:
    result = run_week10_capacity_diagnosis()
    payload = result.acceptance_report.to_json()

    assert "pass_gate" not in payload
    assert payload["environment_extension_pass"] is True
    assert payload["learning_progress_pass"] is True
    assert payload["temporary_failure_classification_pass"] is True
    assert payload["sustained_blockage_classification_pass"] is True
    assert payload["diagnostic_ladder_pass"] is True
    assert payload["growth_delay_pass"] is True
    assert payload["week10_main_milestone_pass"] is True


def _diagnosis(result: Week10RunResult, scenario_family: str) -> Week10ScenarioDiagnosis:
    return next(
        diagnosis for diagnosis in result.diagnoses if diagnosis.scenario_family == scenario_family
    )


def _push_outcome(state: NurseryState) -> TransitionOutcome:
    return NurseryRuntime(state, "week10-test").step(PrimitiveAction.PUSH).transition.outcome


def _state(shape: ShapeCode, *, near_wall: bool) -> NurseryState:
    y = 1 if near_wall else 2
    return NurseryState(
        width=6,
        height=6,
        agent=AgentState(position=GridPosition(1, y), orientation=Direction.EAST),
        entities=(
            *_walls(),
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=GridPosition(2, y),
                blocks_movement=True,
                movable=True,
                shape_code=shape,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=GridPosition(3, y),
                blocks_movement=False,
                movable=False,
            ),
        ),
    )


def _walls() -> tuple[EntityState, ...]:
    return tuple(
        EntityState(
            entity_id=f"wall_{index:03d}",
            role=EntityRole.WALL,
            position=position,
            blocks_movement=True,
            movable=False,
        )
        for index, position in enumerate(
            GridPosition(x, y) for y in range(6) for x in range(6) if x in (0, 5) or y in (0, 5)
        )
    )
