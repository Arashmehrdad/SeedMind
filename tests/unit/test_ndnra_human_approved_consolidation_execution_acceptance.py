"""Tests for live acceptance of restart-safe human-approved execution."""

from __future__ import annotations

import json
from pathlib import Path

from seedmind.integration import (
    export_human_approved_consolidation_execution_acceptance,
    run_human_approved_consolidation_execution_acceptance,
)
from seedmind.research.ndnra import BRAIN_SCHEMA_VERSION, NDNRABrainStore


def test_one_human_approval_produces_one_durable_application(tmp_path: Path) -> None:
    evidence = run_human_approved_consolidation_execution_acceptance(
        tmp_path,
        play_budget=8,
    )
    result = evidence.result

    assert result.brain_schema_version == BRAIN_SCHEMA_VERSION == 5
    assert result.explicit_human_approval_count == 1
    assert result.current_precommit_revalidation_count == 1
    assert result.control_application_count == 0
    assert result.approved_application_count == 1
    assert result.consumed_permit_count == 1
    assert result.execution_receipt_count == 1
    assert result.automatic_execution_count == 0
    assert result.replay_trigger_count == 0
    assert result.restoration_trigger_count == 0
    assert result.action_authority_violation_count == 0


def test_approved_execution_preserves_live_seedmind_cognition(tmp_path: Path) -> None:
    evidence = run_human_approved_consolidation_execution_acceptance(
        tmp_path,
        play_budget=8,
    )
    result = evidence.result

    assert result.proposal_history_unchanged
    assert result.graph_unchanged_by_execution
    assert result.growth_state_unchanged_by_execution
    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.developmental_signals_unchanged
    assert result.advice_unchanged
    assert result.route_ranking_unchanged
    assert result.unrelated_graph_learning_unchanged
    assert result.growth_states_equal
    assert result.human_dependence_accounting_unchanged
    assert not result.temporary_file_remaining
    assert not result.sqlite_used_for_execution_acceptance
    assert result.pass_gate


def test_live_acceptance_receipt_and_persisted_state_are_exact(tmp_path: Path) -> None:
    evidence = run_human_approved_consolidation_execution_acceptance(
        tmp_path,
        play_budget=8,
    )
    loaded = NDNRABrainStore(evidence.approved_brain_path).load()

    assert loaded.execution_checkpoint.receipts == (evidence.receipt,)
    assert loaded.execution_checkpoint.receipts[0].application_count == 1
    assert loaded.execution_checkpoint.receipts[0].replay_trigger_count == 0
    assert loaded.execution_checkpoint.receipts[0].restoration_trigger_count == 0
    assert not loaded.execution_checkpoint.receipts[0].has_production_action_authority
    assert len(loaded.consolidation_checkpoint.active_applications) == 1


def test_live_acceptance_exports_ascii_inspectable_evidence(tmp_path: Path) -> None:
    evidence = run_human_approved_consolidation_execution_acceptance(
        tmp_path,
        play_budget=8,
    )
    report_path, timeline_path, receipt_path = (
        export_human_approved_consolidation_execution_acceptance(evidence, tmp_path)
    )

    report_raw = report_path.read_bytes()
    timeline_raw = timeline_path.read_bytes()
    receipt_raw = receipt_path.read_bytes()
    report = json.loads(report_raw.decode("ascii"))
    receipt = json.loads(receipt_raw.decode("ascii"))

    assert report_raw.isascii()
    assert timeline_raw.isascii()
    assert receipt_raw.isascii()
    assert report["pass_gate"] is True
    assert report["explicit_human_approval_count"] == 1
    assert report["approved_application_count"] == 1
    assert receipt["application_count"] == 1
    assert receipt["replay_trigger_count"] == 0
    assert timeline_raw.startswith(b"step_index,control_action,approved_action")


def test_live_acceptance_has_no_autonomous_or_sqlite_execution_path() -> None:
    source = Path(
        "src/seedmind/integration/human_approved_consolidation_execution_acceptance.py"
    ).read_text(encoding="utf-8").lower()  # fmt: skip

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "background" not in source
    assert "automatic_execution_count=0" not in source.replace(" ", "")
