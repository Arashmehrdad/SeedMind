"""Tests for live-shadow acceptance of reversible consolidation checkpoints."""

from __future__ import annotations

from pathlib import Path

from seedmind.integration import (
    export_consolidation_acceptance,
    run_consolidation_acceptance,
)


def test_consolidation_acceptance_preserves_production_behavior(tmp_path: Path) -> None:
    evidence = run_consolidation_acceptance(tmp_path, play_budget=8)
    result = evidence.result

    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.suggestion_sequence_unchanged
    assert result.learned_graphs_equal
    assert result.authority_violation_count == 0
    assert result.checkpoint_unchanged_during_shadow


def test_consolidation_acceptance_round_trips_live_checkpoint(tmp_path: Path) -> None:
    evidence = run_consolidation_acceptance(tmp_path, play_budget=8)
    result = evidence.result

    assert result.synthetic_interference_gate_passed
    assert result.live_mastery_eligible
    assert result.live_mastery_source_count == 3
    assert result.live_mastery_route_count == 2
    assert result.saved_schema_version == 3
    assert result.active_checkpoint_round_trip_exact
    assert result.baseline_checkpoint_empty
    assert result.loaded_graphs_equal
    assert result.loaded_growth_states_equal


def test_loaded_checkpoint_reopens_and_restores_after_new_contradiction(
    tmp_path: Path,
) -> None:
    evidence = run_consolidation_acceptance(tmp_path, play_budget=8)
    result = evidence.result

    assert result.post_restart_reopening_passed
    assert result.post_restart_restoration_exact
    assert result.source_events_preserved
    assert result.rollback_audit_round_trip_exact
    assert evidence.candidate_id.startswith("consolidation:")
    assert evidence.rollback_id.startswith("rollback:")
    assert result.pass_gate


def test_consolidation_acceptance_exports_are_ascii_and_inspectable(
    tmp_path: Path,
) -> None:
    evidence = run_consolidation_acceptance(tmp_path, play_budget=8)

    report_path, timeline_path, checkpoint_path = export_consolidation_acceptance(
        evidence,
        tmp_path,
    )

    report = report_path.read_text(encoding="ascii")
    timeline = timeline_path.read_text(encoding="ascii")
    checkpoint = checkpoint_path.read_text(encoding="ascii")
    assert '"production_actions_unchanged": true' in report
    assert '"post_restart_restoration_exact": true' in report
    assert timeline.startswith("step_index,baseline_action,tracked_action")
    assert '"rollback_records"' in checkpoint
    assert '"active_applications": []' in checkpoint


def test_consolidation_acceptance_has_no_sqlite_or_action_authority_dependency(
    tmp_path: Path,
) -> None:
    evidence = run_consolidation_acceptance(tmp_path, play_budget=8)
    result = evidence.result

    assert not result.sqlite_used_for_consolidation_acceptance
    files = (
        Path("src/seedmind/integration/consolidation_acceptance.py"),
        Path("src/seedmind/research/ndnra/consolidation_persistence.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()
    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
    assert "has_action_authority=true" not in source.replace(" ", "")
