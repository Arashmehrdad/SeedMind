"""Tests for restart-safe proposal memory acceptance."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from seedmind.integration import (
    RestartSafeProposalMemoryAcceptanceEvidence,
    export_restart_safe_proposal_memory_acceptance,
    run_restart_safe_proposal_memory_acceptance,
)
from seedmind.research.ndnra import (
    BRAIN_SCHEMA_VERSION,
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalRevalidationStatus,
)


@pytest.fixture(scope="module")
def evidence(
    tmp_path_factory: pytest.TempPathFactory,
) -> RestartSafeProposalMemoryAcceptanceEvidence:
    return run_restart_safe_proposal_memory_acceptance(
        tmp_path_factory.mktemp("restart-safe-proposal-memory"),
        play_budget=8,
    )


def test_restart_acceptance_round_trips_exact_state(
    evidence: RestartSafeProposalMemoryAcceptanceEvidence,
) -> None:
    result = evidence.result
    record = evidence.accepted_checkpoint.registry.records[0]

    assert result.brain_schema_version == BRAIN_SCHEMA_VERSION == 4
    assert result.exact_graph_round_trip
    assert result.exact_growth_round_trip
    assert result.exact_lifecycle_round_trip
    assert result.exact_review_history_round_trip
    assert result.checksum_verified
    assert not result.temporary_file_remaining
    assert record.lifecycle.status is ConsolidationProposalLifecycleStatus.ACCEPTED
    assert len(record.lifecycle.decisions) == 1


def test_restart_acceptance_migrates_and_falls_back_safely(
    evidence: RestartSafeProposalMemoryAcceptanceEvidence,
) -> None:
    result = evidence.result

    assert result.legacy_v1_migrated_empty
    assert result.legacy_v2_migrated_empty
    assert result.legacy_v3_migrated_empty
    assert result.checksum_corruption_fallback_complete
    assert result.relational_corruption_fallback_complete


def test_restart_acceptance_detects_stale_accepted_proposal(
    evidence: RestartSafeProposalMemoryAcceptanceEvidence,
) -> None:
    result = evidence.result
    clean = evidence.clean_restart_report.decisions[0]
    stale = evidence.stale_restart_report.decisions[0]

    assert result.current_after_clean_restart
    assert clean.status is ConsolidationProposalRevalidationStatus.CURRENT
    assert clean.candidate_identity_current
    assert result.stale_after_additional_evidence
    assert stale.status is ConsolidationProposalRevalidationStatus.STALE
    assert not stale.candidate_identity_current
    assert stale.current_candidate is not None
    assert stale.current_candidate.candidate_id != stale.proposal.candidate.candidate_id
    assert result.stale_registry_unchanged


def test_restart_revalidation_does_not_change_live_seedmind(
    evidence: RestartSafeProposalMemoryAcceptanceEvidence,
) -> None:
    result = evidence.result

    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.suggestion_sequence_unchanged
    assert result.live_signals_unchanged
    assert result.learned_graphs_equal
    assert result.growth_states_equal
    assert result.revalidation_evaluation_count == 8
    assert result.current_revalidation_count == 8
    assert result.revalidation_registry_mutation_count == 0
    assert result.revalidation_ledger_mutation_count == 0
    assert all(
        observation.status is ConsolidationProposalRevalidationStatus.CURRENT
        for observation in evidence.observations
    )
    assert all(observation.registry_unchanged for observation in evidence.observations)
    assert all(
        observation.ledger_unchanged_by_revalidation for observation in evidence.observations
    )


def test_restart_acceptance_retains_zero_authority(
    evidence: RestartSafeProposalMemoryAcceptanceEvidence,
) -> None:
    result = evidence.result

    assert result.authority_violation_count == 0
    assert result.consolidation_application_count == 0
    assert result.replay_trigger_count == 0
    assert result.restoration_trigger_count == 0
    assert not result.sqlite_used_for_restart_acceptance
    assert all(not observation.has_execution_authority for observation in evidence.observations)
    assert not evidence.clean_restart_report.has_execution_authority
    assert not evidence.stale_restart_report.has_execution_authority
    assert result.pass_gate


def test_restart_acceptance_exports_are_ascii_and_inspectable(
    evidence: RestartSafeProposalMemoryAcceptanceEvidence,
    tmp_path: Path,
) -> None:
    report_path, timeline_path, decisions_path = export_restart_safe_proposal_memory_acceptance(
        evidence, tmp_path
    )

    report_raw = report_path.read_bytes()
    timeline_raw = timeline_path.read_bytes()
    decisions_raw = decisions_path.read_bytes()
    report = json.loads(report_raw.decode("ascii"))
    decisions = json.loads(decisions_raw.decode("ascii"))

    assert report_raw.isascii()
    assert timeline_raw.isascii()
    assert decisions_raw.isascii()
    assert report["pass_gate"] is True
    assert report["current_revalidation_count"] == 8
    assert timeline_raw.decode("ascii").startswith("step_index,baseline_action,persisted_action")
    assert decisions["clean_restart"]["decisions"][0]["status"] == "current"
    assert decisions["stale_restart"]["decisions"][0]["status"] == "stale"


def test_restart_acceptance_has_no_execution_replay_or_sqlite_path() -> None:
    source = (
        Path("src/seedmind/integration/restart_safe_proposal_memory_acceptance.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "consolidationapplicationstate" not in source
    assert "rollback_consolidation" not in source
    assert ".apply(" not in source
    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "has_execution_authority=true" not in source.replace(" ", "")
