"""Acceptance tests for the deterministic Week 9 contribution runner."""

from __future__ import annotations

from pathlib import Path

from seedmind.contribution import (
    DEFAULT_FAILURE_SEEDS,
    DEFAULT_SUCCESS_SEEDS,
    WEEK9_SUCCESS_TARGET,
    load_contribution_history,
    load_support_state,
    run_week9_contribution_evaluation,
)
from seedmind.human import SupportLevel


def test_week9_runner_proves_support_transitions_and_exports(tmp_path: Path) -> None:
    result = run_week9_contribution_evaluation(output_dir=tmp_path)
    report = result.acceptance_report

    assert report.total_attempts == len(DEFAULT_SUCCESS_SEEDS) + len(DEFAULT_FAILURE_SEEDS)
    assert report.independent_success_rate >= WEEK9_SUCCESS_TARGET
    assert report.first_success_kept_dependent is True
    assert report.reduced_after_repeated_competence is True
    assert report.restored_to_dependent_after_failures is True
    assert report.reduced_again_after_repeated_competence is True
    assert report.skill_discovery_delta == 0
    assert report.compile_count == 0
    assert report.training_count == 0
    assert report.promotion_count == 0
    assert report.production_curiosity_retained_count == report.executed_step_count
    assert report.authority_violations == 0
    assert report.verification_authority_violations == 0
    assert report.support_authority_violations == 0
    assert report.ndnra_automatic_promotions == 0
    assert result.support_state.current_level is SupportLevel.GUIDED_LEARNER
    assert (tmp_path / "human_contribution_demo.json").exists()
    assert (tmp_path / "support_level_report.json").exists()
    assert (tmp_path / "contribution_history.json").exists()
    assert (tmp_path / "week9_acceptance_report.json").exists()


def test_week9_runner_exports_loadable_history_and_support(tmp_path: Path) -> None:
    run_week9_contribution_evaluation(output_dir=tmp_path)
    run_week9_contribution_evaluation(output_dir=tmp_path)

    assert not tuple(tmp_path.glob("*.tmp"))
    history = load_contribution_history(tmp_path / "contribution_history.json")
    support_state = load_support_state(tmp_path / "support_level_report.json")

    assert len(history) == len(DEFAULT_SUCCESS_SEEDS) + len(DEFAULT_FAILURE_SEEDS)
    assert support_state.current_level is SupportLevel.GUIDED_LEARNER
    assert history[0].support_level_before is SupportLevel.DEPENDENT
    assert history[0].support_level_after is SupportLevel.DEPENDENT
    assert history[4].support_level_after is SupportLevel.GUIDED_LEARNER
    assert history[6].support_level_after is SupportLevel.DEPENDENT
    assert all(record.support_level_after is SupportLevel.DEPENDENT for record in history[7:11])
    assert history[11].support_level_after is SupportLevel.GUIDED_LEARNER
    assert support_state.promotion_evidence_start_index == 7
