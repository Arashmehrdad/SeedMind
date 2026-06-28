"""Tests for live controlled replay and restoration stage acceptance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from seedmind.integration import (
    ControlledReplayRestorationAcceptanceEvidence,
    export_controlled_replay_restoration_acceptance,
    run_controlled_replay_restoration_acceptance,
)
from seedmind.research.ndnra import (
    BRAIN_SCHEMA_VERSION,
    ControlledReplayRestorationPermitLifecycleStatus,
    NDNRABrainStore,
)


@pytest.fixture(scope="module")
def evidence(
    tmp_path_factory: pytest.TempPathFactory,
) -> ControlledReplayRestorationAcceptanceEvidence:
    return run_controlled_replay_restoration_acceptance(
        tmp_path_factory.mktemp("controlled-replay-restoration-acceptance"),
        play_budget=8,
    )


def test_acceptance_consumes_exactly_one_replay_and_restoration_permit(
    evidence: ControlledReplayRestorationAcceptanceEvidence,
) -> None:
    result = evidence.result
    loaded = NDNRABrainStore(evidence.restoration_current_brain_path).load()
    records = loaded.replay_restoration_checkpoint.permit_registry.records

    assert result.brain_schema_version == BRAIN_SCHEMA_VERSION == 6
    assert result.explicit_human_approval_count == 2
    assert result.replay_consumed_permit_count == 1
    assert result.restoration_consumed_permit_count == 1
    assert result.replay_receipt_count == 1
    assert result.restoration_receipt_count == 1
    assert result.automatic_replay_count == 0
    assert result.automatic_restoration_count == 0
    assert (
        sum(
            record.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED
            for record in records
        )
        == 2
    )
    assert loaded.replay_restoration_checkpoint.replay_receipts == (evidence.replay_receipt,)
    assert loaded.replay_restoration_checkpoint.restoration_receipts == (
        evidence.restoration_receipt,
    )


def test_replay_changes_only_bounded_non_authoritative_accessibility(
    evidence: ControlledReplayRestorationAcceptanceEvidence,
) -> None:
    result = evidence.result

    assert result.production_actions_unchanged_after_replay
    assert result.prediction_errors_unchanged_after_replay
    assert result.developmental_signals_unchanged_after_replay
    assert result.replay_graph_learning_unchanged
    assert result.replay_non_dormancy_growth_unchanged
    assert result.replay_suggestion_difference_count >= 0
    assert evidence.replay_receipt.factual_confidence_delta == 0.0
    assert evidence.replay_receipt.mastery_delta == 0.0
    assert not evidence.replay_receipt.has_learning_authority
    assert not evidence.replay_receipt.has_action_selection_authority
    assert not evidence.replay_receipt.has_production_action_authority


def test_restoration_reproduces_source_state_and_live_behaviour(
    evidence: ControlledReplayRestorationAcceptanceEvidence,
) -> None:
    result = evidence.result

    assert result.restored_active_state_matches_source
    assert result.restoration_actions_unchanged
    assert result.restoration_suggestions_unchanged
    assert result.restoration_prediction_errors_unchanged
    assert result.restoration_signals_unchanged
    assert result.restoration_graph_learning_unchanged
    assert result.restoration_growth_unchanged
    assert evidence.restoration_receipt.restored_complete_envelope
    assert evidence.restoration_receipt.partial_restoration_count == 0
    assert not evidence.restoration_receipt.has_replay_authority
    assert not evidence.restoration_receipt.has_restoration_authority
    assert not evidence.restoration_receipt.has_cognitive_authority
    assert not evidence.restoration_receipt.has_production_action_authority


def test_acceptance_exercises_all_failure_and_restart_paths(
    evidence: ControlledReplayRestorationAcceptanceEvidence,
) -> None:
    result = evidence.result

    assert result.cancelled_permit_count == 1
    assert result.expired_permit_count == 1
    assert result.stale_evidence_rejected
    assert result.duplicate_replay_rejected_after_restart
    assert result.restoration_reuse_rejected_after_restart
    assert result.cancellation_terminal_enforced
    assert result.expiry_terminal_enforced
    assert result.replay_interruption_preserved_old_state
    assert result.restoration_interruption_recovered_complete_new_state
    assert result.corrupt_source_rejected_without_mutation
    assert result.replay_restart_round_trip_exact
    assert result.restoration_restart_round_trip_exact
    assert result.action_authority_violation_count == 0
    assert not result.temporary_file_remaining
    assert not result.sqlite_used_for_acceptance
    assert result.pass_gate


def test_acceptance_exports_ascii_inspectable_evidence(
    evidence: ControlledReplayRestorationAcceptanceEvidence,
    tmp_path: Path,
) -> None:
    report_path, replay_path, restoration_path, receipts_path = (
        export_controlled_replay_restoration_acceptance(evidence, tmp_path)
    )
    report_raw = report_path.read_bytes()
    replay_raw = replay_path.read_bytes()
    restoration_raw = restoration_path.read_bytes()
    receipts_raw = receipts_path.read_bytes()
    report = json.loads(report_raw.decode("ascii"))
    receipts = json.loads(receipts_raw.decode("ascii"))

    assert report_raw.isascii()
    assert replay_raw.isascii()
    assert restoration_raw.isascii()
    assert receipts_raw.isascii()
    assert report["pass_gate"] is True
    assert report["replay_consumed_permit_count"] == 1
    assert report["restoration_consumed_permit_count"] == 1
    assert replay_raw.startswith(b"step_index,first_action,second_action")
    assert restoration_raw.startswith(b"step_index,first_action,second_action")
    assert receipts["replay"]["receipt_id"] == evidence.replay_receipt.receipt_id
    assert receipts["restoration"]["receipt_id"] == (evidence.restoration_receipt.receipt_id)


def test_acceptance_has_no_autonomous_or_sqlite_operation_path() -> None:
    source = (
        Path("src/seedmind/integration/controlled_replay_restoration_acceptance.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "background" not in source
    assert "has_production_action_authority=true" not in source.replace(" ", "")
    assert "automatic_replay_count=0" not in source.replace(" ", "")
    assert "automatic_restoration_count=0" not in source.replace(" ", "")
