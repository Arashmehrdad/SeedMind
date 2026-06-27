"""Tests for live-shadow consolidation scheduling acceptance."""

from __future__ import annotations

import json
from pathlib import Path

from seedmind.integration import (
    export_consolidation_scheduling_acceptance,
    run_consolidation_scheduling_acceptance,
)
from seedmind.research.ndnra import ConsolidationScheduleStatus


def test_live_scheduler_does_not_change_seedmind_behavior(tmp_path: Path) -> None:
    evidence = run_consolidation_scheduling_acceptance(tmp_path, play_budget=8)
    result = evidence.result

    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.suggestion_sequence_unchanged
    assert result.live_signals_unchanged
    assert result.learned_graphs_equal
    assert result.growth_states_equal
    assert result.authority_violation_count == 0


def test_live_scheduler_proposes_once_without_repetition(tmp_path: Path) -> None:
    evidence = run_consolidation_scheduling_acceptance(tmp_path, play_budget=8)
    result = evidence.result

    assert result.synthetic_scheduling_gate_passed
    assert result.live_mastery_eligible
    assert result.live_mastery_source_count == 3
    assert result.live_mastery_route_count == 2
    assert result.schedule_evaluation_count == 8
    assert result.proposal_count == 1
    assert result.unique_candidate_count == 1
    assert result.redundant_proposal_count == 0
    assert evidence.observations[0].status is ConsolidationScheduleStatus.PROPOSED
    assert all(
        observation.status is ConsolidationScheduleStatus.CANDIDATE_ALREADY_ACTIVE
        for observation in evidence.observations[1:]
    )


def test_live_scheduler_remains_read_only_and_non_authoritative(tmp_path: Path) -> None:
    evidence = run_consolidation_scheduling_acceptance(tmp_path, play_budget=8)
    result = evidence.result

    assert result.scheduler_ledger_mutation_count == 0
    assert result.consolidation_application_count == 0
    assert not result.sqlite_used_for_scheduling_acceptance
    assert all(observation.ledger_unchanged for observation in evidence.observations)
    assert all(not observation.has_execution_authority for observation in evidence.observations)
    assert result.pass_gate


def test_scheduling_acceptance_exports_are_ascii_and_inspectable(
    tmp_path: Path,
) -> None:
    evidence = run_consolidation_scheduling_acceptance(tmp_path, play_budget=8)

    report_path, timeline_path, proposals_path = export_consolidation_scheduling_acceptance(
        evidence, tmp_path
    )

    report_raw = report_path.read_bytes()
    timeline_raw = timeline_path.read_bytes()
    proposals_raw = proposals_path.read_bytes()
    report = json.loads(report_raw.decode("ascii"))
    proposals = json.loads(proposals_raw.decode("ascii"))
    assert report_raw.isascii()
    assert timeline_raw.isascii()
    assert proposals_raw.isascii()
    assert report["pass_gate"] is True
    assert report["proposal_count"] == 1
    assert timeline_raw.decode("ascii").startswith("step_index,baseline_action,observed_action")
    assert proposals[0]["status"] == "proposed"
    assert proposals[0]["has_execution_authority"] is False


def test_scheduling_acceptance_has_no_application_or_sqlite_path() -> None:
    path = Path("src/seedmind/integration/consolidation_scheduling_acceptance.py")
    source = path.read_text(encoding="utf-8").lower()

    assert "consolidationapplicationstate" not in source
    assert "rollback_consolidation" not in source
    assert ".apply(" not in source
    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "has_execution_authority=true" not in source.replace(" ", "")
