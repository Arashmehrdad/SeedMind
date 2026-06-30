"""Tests for Week 9 Default-vs-NDNRA comparative evidence."""

from __future__ import annotations

from seedmind.contribution import run_week9_contribution_evaluation


def test_week9_parallel_comparison_covers_every_production_step() -> None:
    result = run_week9_contribution_evaluation()
    comparison = result.parallel_comparison
    report = comparison.report

    assert report.pass_gate
    assert report.total_production_steps == result.acceptance_report.executed_step_count
    assert len(comparison.steps) == report.total_production_steps
    assert report.default_proposal_count == report.total_production_steps
    assert report.ndnra_observation_count == report.total_production_steps
    assert report.ndnra_proposal_count > 0
    assert (
        report.ndnra_proposal_count + report.ndnra_abstention_count == report.total_production_steps
    )
    assert report.comparison_count == report.ndnra_proposal_count
    assert report.disagreement_comparison_count == report.disagreement_count
    assert report.disagreement_comparison_coverage == 1.0
    assert all(step.default_executed for step in comparison.steps)
    assert all(not step.ndnra_executed for step in comparison.steps)
    assert all(step.compared for step in comparison.steps if step.ndnra_action is not None)
    assert all(step.compared for step in comparison.steps if step.disagreement)
    assert (
        report.default_better_count + report.ndnra_better_count + report.tied_count
        == report.comparison_count
    )
    assert report.production_action_replacements == 0
    assert report.authority_violations == 0
    assert report.automatic_promotions == 0


def test_week9_parallel_comparison_reports_separate_task_outcomes() -> None:
    result = run_week9_contribution_evaluation()
    comparison = result.parallel_comparison
    report = comparison.report

    assert report.default_task_successes == result.acceptance_report.total_successes
    assert report.default_task_success_rate == result.acceptance_report.independent_success_rate
    assert len(comparison.ndnra_rollouts) == result.acceptance_report.total_attempts
    assert report.ndnra_rollout_attempts == result.acceptance_report.total_attempts
    assert report.ndnra_rollout_successes == sum(
        rollout.success for rollout in comparison.ndnra_rollouts
    )
    assert 0.0 <= report.ndnra_rollout_success_rate <= 1.0
    assert report.learned_assembly_count > 0
    assert report.effect_dimension_count > 0
    assert len(comparison.scenarios) == result.acceptance_report.total_attempts
