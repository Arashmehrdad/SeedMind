"""Tests for bounded consolidation interference and source-gated replay."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationInterferenceCondition,
    run_consolidation_interference_experiment,
)


def test_old_lesson_is_mastered_and_eligible_before_interference() -> None:
    evidence = run_consolidation_interference_experiment()
    result = evidence.result

    assert evidence.eligibility.eligible
    assert evidence.eligibility.candidate is not None
    assert result.old_mastery_profile.broad_mastery
    assert result.old_mastery_profile.effective_support >= 3.0
    assert result.old_mastery_profile.unique_context_count >= 3
    assert result.old_mastery_profile.unique_route_count >= 2
    assert result.source_trace_count_before == 3
    assert result.source_trace_count_after == 3


def test_no_consolidation_learns_new_lesson_but_forgets_old_lesson() -> None:
    result = run_consolidation_interference_experiment().result.no_consolidation

    assert result.condition is ConsolidationInterferenceCondition.NO_CONSOLIDATION
    assert not result.consolidation_applied
    assert result.new_score_after >= 0.85
    assert result.new_learning_gain > 0.60
    assert result.old_interference >= 0.30
    assert result.old_score_after < result.old_score_before
    assert result.replay_count == 0


def test_naive_consolidation_trades_new_learning_for_better_retention() -> None:
    result = run_consolidation_interference_experiment().result
    no_consolidation = result.no_consolidation
    naive = result.naive_consolidation

    assert naive.condition is ConsolidationInterferenceCondition.NAIVE_CONSOLIDATION
    assert naive.consolidation_applied
    assert naive.old_score_after > no_consolidation.old_score_after
    assert naive.old_interference < no_consolidation.old_interference
    assert naive.new_score_after < no_consolidation.new_score_after
    assert naive.replay_count == 0


def test_retention_gated_replay_uses_only_candidate_sources_when_needed() -> None:
    evidence = run_consolidation_interference_experiment()
    result = evidence.result
    replay = result.retention_gated_replay
    candidate_ids = set(result.consolidation_candidate.source_event_ids)

    assert replay.condition is ConsolidationInterferenceCondition.RETENTION_GATED_REPLAY
    assert replay.consolidation_applied
    assert replay.replay_count > 0
    assert replay.replay_count == len(replay.replay_source_event_ids)
    assert set(replay.replay_source_event_ids).issubset(candidate_ids)
    assert all(score < 0.72 for score in replay.replay_trigger_scores)
    assert result.replay_sources_resolved
    assert result.replay_bounded


def test_replay_preserves_sources_without_inflating_mastery() -> None:
    evidence = run_consolidation_interference_experiment()
    result = evidence.result

    assert result.source_mastery_unchanged
    assert result.source_trace_count_before == result.source_trace_count_after
    assert evidence.source_ledger_snapshot["trace_count"] == 3
    assert (
        result.old_mastery_profile.source_event_ids
        == result.consolidation_candidate.source_event_ids
    )


def test_retention_gated_replay_balances_retention_and_new_learning() -> None:
    result = run_consolidation_interference_experiment().result
    replay = result.retention_gated_replay
    baseline_joint = max(
        result.no_consolidation.joint_retention_learning_score,
        result.naive_consolidation.joint_retention_learning_score,
    )

    assert replay.old_score_after >= 0.72
    assert replay.new_score_after >= 0.70
    assert replay.joint_retention_learning_score >= baseline_joint + 0.10
    assert replay.old_score_after == pytest.approx(0.7329168638756465)
    assert replay.new_score_after == pytest.approx(0.7342594481549558)


def test_experiment_is_exactly_deterministic() -> None:
    first = run_consolidation_interference_experiment()
    second = run_consolidation_interference_experiment()

    assert first == second
    assert first.result.pass_gate


def test_experiment_remains_non_authoritative_and_non_sql() -> None:
    evidence = run_consolidation_interference_experiment()
    result = evidence.result

    assert result.action_authority_violation_count == 0
    assert not result.sqlite_used_for_replay

    path = Path("src/seedmind/research/ndnra/consolidation_interference_experiment.py")
    source = path.read_text(encoding="utf-8").lower()
    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
    assert "seedmind.integration" not in source
    assert "persistence" not in source
