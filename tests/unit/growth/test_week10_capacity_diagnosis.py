"""Grounded tests for original Week 10 capacity diagnosis."""

from __future__ import annotations

import filecmp
from pathlib import Path

import pytest

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
    GroundedEpisodeTrace,
    LearningAttempt,
    LearningProgressThresholds,
    PlateauClassification,
    Week10RunResult,
    Week10ScenarioDiagnosis,
    build_learning_progress_windows,
    build_week10_growth_proposal,
    run_week10_capacity_diagnosis,
)


def test_cube_like_raw_dynamics_differ_from_ball_without_breaking_ball_push() -> None:
    assert _push_outcome(_state(ShapeCode.ROUND, near_wall=True)) is TransitionOutcome.PUSHED
    assert (
        _push_outcome(_state(ShapeCode.ANGULAR, near_wall=True))
        is TransitionOutcome.PUSH_INEFFECTIVE_CONTACT
    )
    assert _push_outcome(_state(ShapeCode.ANGULAR, near_wall=False)) is TransitionOutcome.PUSHED


def test_policy_facing_observation_has_raw_shape_not_privileged_cube_label() -> None:
    packet = NurseryObservationAdapter(width=6, height=6).observe(
        _state(ShapeCode.ANGULAR, near_wall=False),
        episode_id="obs",
    )

    assert all(isinstance(value, float) for value in packet.sensor_values)
    assert "cube" not in repr(packet).lower()
    assert max(packet.sensor_values) == 1.0


def test_every_learning_attempt_references_executed_episode_trace() -> None:
    result = run_week10_capacity_diagnosis()
    traces = {trace.episode_id: trace for trace in result.episode_traces}

    for diagnosis in result.diagnoses:
        for attempt in diagnosis.attempts:
            assert attempt.has_grounded_provenance
            assert attempt.episode_id in traces
            assert attempt.trace_digest == traces[attempt.episode_id].trace_digest
            assert attempt.success is traces[attempt.episode_id].success
            assert attempt.task_progress == pytest.approx(
                _recalculated_progress(traces[attempt.episode_id])
            )


def test_episode_traces_have_primitive_actions_real_outcomes_and_prediction_evidence() -> None:
    result = run_week10_capacity_diagnosis()

    for trace in result.episode_traces:
        assert trace.actions
        assert trace.transition_outcomes
        assert len(trace.actions) == len(trace.step_traces)
        assert len(trace.transition_outcomes) == len(trace.step_traces)
        for step in trace.step_traces:
            assert step.action.value in trace.actions
            assert step.transition_outcome.value in trace.transition_outcomes
            assert step.prediction.evidence_available
            assert step.prediction.predicted_source.endswith("compare_prediction")
            assert step.prediction.mean_absolute_error >= 0.0


def test_temporary_and_sustained_seed_sets_are_consumed() -> None:
    result = run_week10_capacity_diagnosis()
    temporary = _diagnosis(result, "temporary_cube_recovery")
    sustained = _diagnosis(result, "sustained_cube_blockage")

    assert {attempt.episode_id.split("-")[2] for attempt in temporary.attempts} == {
        str(seed) for seed in range(410, 422)
    }
    assert {attempt.episode_id.split("-")[2] for attempt in sustained.attempts} == {
        str(seed) for seed in range(510, 522)
    }


def test_temporary_failure_improves_from_executed_replay_and_demonstration() -> None:
    result = run_week10_capacity_diagnosis()
    temporary = _diagnosis(result, "temporary_cube_recovery")

    assert temporary.classification is PlateauClassification.IMPROVING
    assert temporary.proposal_generated is False
    assert temporary.replay.relevant_memory_ids
    assert temporary.replay.progress_resumed
    assert temporary.help.demonstration_completed_task
    assert temporary.help.after_mean_progress > temporary.help.before_mean_progress
    assert temporary.help.performance_improved_afterward


def test_sustained_blockage_uses_real_windows_full_ladder_and_reachability_proof() -> None:
    result = run_week10_capacity_diagnosis()
    sustained = _diagnosis(result, "sustained_cube_blockage")

    assert len(sustained.windows) == 3
    assert sustained.classification is PlateauClassification.SUSTAINED_BLOCKAGE
    assert sustained.ladder.completed_for_growth_proposal
    assert sustained.help.demonstration_completed_task
    assert sustained.help.blockage_remained
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


def test_replay_memory_ids_resolve_to_committed_source_episodes() -> None:
    result = run_week10_capacity_diagnosis()
    trace_ids = {trace.episode_id for trace in result.episode_traces}

    for family in ("temporary_cube_recovery", "sustained_cube_blockage"):
        replay = _diagnosis(result, family).replay
        assert replay.relevant_memory_ids
        assert set(replay.source_episode_ids).issubset(trace_ids)
        assert set(replay.replay_influenced_episode_ids).issubset(trace_ids)


def test_strategy_variants_actually_execute_without_growth_or_skill_mutation() -> None:
    result = run_week10_capacity_diagnosis()
    trace_ids = {trace.episode_id for trace in result.episode_traces}

    assert result.strategy_variants
    for variant in result.strategy_variants:
        assert variant.executed_episode_ids
        assert set(variant.executed_episode_ids).issubset(trace_ids)
        assert variant.attempts == len(variant.executed_episode_ids)
        assert variant.attempts <= variant.safe_attempt_budget
        assert not variant.created_specialist
        assert not variant.mutated_frozen_skill


def test_non_capacity_cases_are_separate_grounded_stops_without_proposal() -> None:
    result = run_week10_capacity_diagnosis()
    non_capacity = _diagnosis(result, "non_capacity_blockage")

    assert non_capacity.proposal_generated is False
    assert non_capacity.ladder.stopped_early
    assert non_capacity.non_capacity_reason == (
        "ambiguous_request,impossible_geometry,resource_budget_exhaustion,unsafe_permission_blocked"
    )
    assert {attempt.strategy for attempt in non_capacity.attempts} == {
        "ambiguous_request",
        "impossible_geometry",
        "resource_budget_exhaustion",
        "unsafe_permission_blocked",
    }


def test_proposal_is_evidence_derived_and_rejects_incomplete_evidence() -> None:
    result = run_week10_capacity_diagnosis()
    sustained = _diagnosis(result, "sustained_cube_blockage")

    assert result.proposal is not None
    assert sustained.proposal_generated
    assert result.proposal.status.value == "proposed_not_authorised"
    assert result.proposal.candidate.created is False
    with pytest.raises(ValueError, match="grounded replay"):
        build_week10_growth_proposal(
            scenario_family=sustained.scenario_family,
            classification=sustained.classification,
            ladder=sustained.ladder,
            windows=sustained.windows,
            grounded_replay_pass=False,
            reachability_proven=True,
            strategy_variant_count=3,
            help_requested=True,
            demonstration_attempted=True,
            prediction_evidence_resolved=True,
            competence_still_improving=False,
            ambiguity_resolved=True,
            safety_or_permission_clear=True,
            impossible_task=False,
            resource_limit=False,
        )


def test_familiar_skill_retention_and_no_week11_or_ndnra_dependency() -> None:
    result = run_week10_capacity_diagnosis()

    assert result.familiar_control_success_rate == 1.0
    assert result.acceptance_report.frozen_skill_preservation_pass
    assert (
        result.acceptance_report.frozen_skill_sha256_before
        == result.acceptance_report.frozen_skill_sha256_after
    )
    assert result.acceptance_report.specialist_created is False
    assert result.acceptance_report.router_created is False
    assert result.acceptance_report.week11_started is False
    assert result.acceptance_report.ndnra_required is False
    growth_imports = "\n".join(
        line
        for path in Path("src/seedmind/growth").glob("*.py")
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(("import ", "from "))
    )
    assert "seedmind.research.ndnra" not in growth_imports


def test_visualisation_and_json_artifacts_are_deterministic_and_leave_no_tmp_files(
    tmp_path: Path,
) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    run_week10_capacity_diagnosis(output_dir=first)
    run_week10_capacity_diagnosis(output_dir=second)

    expected = (
        "grounded_episode_traces.json",
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


def test_synthetic_rows_are_limited_to_pure_window_classifier() -> None:
    thresholds = LearningProgressThresholds()
    attempts = tuple(
        LearningAttempt(
            attempt_index=index,
            scenario_family="classifier_only",
            strategy="synthetic_unit_test",
            success=False,
            task_progress=0.05,
            steps_used=4,
            prediction_error=0.60,
            invalid_or_ineffective_actions=1,
        )
        for index in range(4)
    )

    windows = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="classifier_only",
        strategy_variants_exhausted=False,
        replay_attempted=False,
        help_or_demonstration_considered=False,
    )

    assert not attempts[0].has_grounded_provenance
    assert windows[-1].classification is PlateauClassification.INSUFFICIENT_EVIDENCE


def test_modifying_runtime_outcomes_changes_diagnosis() -> None:
    baseline = run_week10_capacity_diagnosis()
    altered = run_week10_capacity_diagnosis(temporary_seeds=tuple(range(700, 712)))

    assert [trace.trace_digest for trace in baseline.episode_traces] != [
        trace.trace_digest for trace in altered.episode_traces
    ]
    assert _diagnosis(altered, "temporary_cube_recovery").classification is (
        PlateauClassification.IMPROVING
    )


def _diagnosis(result: Week10RunResult, scenario_family: str) -> Week10ScenarioDiagnosis:
    return next(
        diagnosis for diagnosis in result.diagnoses if diagnosis.scenario_family == scenario_family
    )


def _recalculated_progress(trace: GroundedEpisodeTrace) -> float:
    if trace.initial_distance <= 0:
        return 1.0
    return max(
        0.0, min(1.0, (trace.initial_distance - trace.final_distance) / trace.initial_distance)
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
