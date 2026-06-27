"""Tests for live-shadow consolidation proposal lifecycle acceptance."""

from __future__ import annotations

import json
from pathlib import Path

from seedmind.integration import (
    export_consolidation_proposal_lifecycle_acceptance,
    run_consolidation_proposal_lifecycle_acceptance,
)
from seedmind.research.ndnra import (
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewAction,
    ConsolidationScheduleStatus,
)


def test_live_lifecycle_does_not_change_seedmind_behavior(tmp_path: Path) -> None:
    evidence = run_consolidation_proposal_lifecycle_acceptance(
        tmp_path,
        play_budget=8,
    )
    result = evidence.result

    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.suggestion_sequence_unchanged
    assert result.live_signals_unchanged
    assert result.learned_graphs_equal
    assert result.growth_states_equal
    assert result.authority_violation_count == 0


def test_live_lifecycle_defers_then_accepts_one_proposal(tmp_path: Path) -> None:
    evidence = run_consolidation_proposal_lifecycle_acceptance(
        tmp_path,
        play_budget=8,
    )
    result = evidence.result

    assert result.synthetic_lifecycle_gate_passed
    assert result.live_mastery_eligible
    assert result.live_mastery_source_count == 3
    assert result.live_mastery_route_count == 2
    assert result.lifecycle_evaluation_count == 8
    assert result.scheduled_proposal_count == 1
    assert result.review_decision_count == 2
    assert result.defer_decision_count == 1
    assert result.accept_decision_count == 1
    assert result.retained_registry_record_count == 1
    assert result.retained_lifecycle_history_count == 2
    assert result.final_proposal_accepted

    assert evidence.observations[0].schedule_status is ConsolidationScheduleStatus.PROPOSED
    assert evidence.observations[0].review_action is ConsolidationProposalReviewAction.DEFER
    assert (
        evidence.observations[0].lifecycle_status is ConsolidationProposalLifecycleStatus.DEFERRED
    )
    assert evidence.observations[2].review_action is ConsolidationProposalReviewAction.ACCEPT
    assert (
        evidence.observations[2].lifecycle_status is ConsolidationProposalLifecycleStatus.ACCEPTED
    )
    assert all(
        observation.schedule_status is ConsolidationScheduleStatus.CANDIDATE_ALREADY_ACTIVE
        for observation in evidence.observations[1:]
    )


def test_live_lifecycle_retains_history_without_execution(tmp_path: Path) -> None:
    evidence = run_consolidation_proposal_lifecycle_acceptance(
        tmp_path,
        play_budget=8,
    )
    result = evidence.result
    record = evidence.registry.records[0]

    assert record.lifecycle.status is ConsolidationProposalLifecycleStatus.ACCEPTED
    assert tuple(decision.action for decision in record.lifecycle.decisions) == (
        ConsolidationProposalReviewAction.DEFER,
        ConsolidationProposalReviewAction.ACCEPT,
    )
    assert result.lifecycle_ledger_mutation_count == 0
    assert result.consolidation_application_count == 0
    assert not result.sqlite_used_for_lifecycle_acceptance
    assert all(observation.ledger_unchanged for observation in evidence.observations)
    assert all(not observation.has_execution_authority for observation in evidence.observations)
    assert not evidence.registry.has_execution_authority
    assert result.pass_gate


def test_lifecycle_acceptance_exports_are_ascii_and_inspectable(
    tmp_path: Path,
) -> None:
    evidence = run_consolidation_proposal_lifecycle_acceptance(
        tmp_path,
        play_budget=8,
    )

    report_path, timeline_path, registry_path = export_consolidation_proposal_lifecycle_acceptance(
        evidence,
        tmp_path,
    )

    report_raw = report_path.read_bytes()
    timeline_raw = timeline_path.read_bytes()
    registry_raw = registry_path.read_bytes()
    report = json.loads(report_raw.decode("ascii"))
    registry = json.loads(registry_raw.decode("ascii"))
    assert report_raw.isascii()
    assert timeline_raw.isascii()
    assert registry_raw.isascii()
    assert report["pass_gate"] is True
    assert report["review_decision_count"] == 2
    assert timeline_raw.decode("ascii").startswith("step_index,baseline_action,observed_action")
    assert registry["registry"]["active_record_count"] == 1
    assert registry["observations"][0]["review_action"] == "defer"
    assert registry["observations"][2]["review_action"] == "accept"


def test_lifecycle_acceptance_has_no_application_or_sqlite_path() -> None:
    path = Path("src/seedmind/integration/consolidation_proposal_lifecycle_acceptance.py")
    source = path.read_text(encoding="utf-8").lower()

    assert "consolidationapplicationstate" not in source
    assert "rollback_consolidation" not in source
    assert ".apply(" not in source
    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "has_execution_authority=true" not in source.replace(" ", "")
