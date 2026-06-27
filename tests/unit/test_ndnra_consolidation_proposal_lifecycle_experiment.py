"""Tests for the NDNRA consolidation proposal lifecycle experiment."""

from __future__ import annotations

import json
from pathlib import Path

from seedmind.research.ndnra import (
    ConsolidationProposalLifecycleExperimentResult,
    ConsolidationProposalLifecycleStrategy,
    ConsolidationProposalLifecycleStrategyResult,
    export_consolidation_proposal_lifecycle_experiment,
    run_consolidation_proposal_lifecycle_experiment,
)


def _by_strategy() -> tuple[
    ConsolidationProposalLifecycleExperimentResult,
    dict[
        ConsolidationProposalLifecycleStrategy,
        ConsolidationProposalLifecycleStrategyResult,
    ],
]:
    result = run_consolidation_proposal_lifecycle_experiment()
    return result, {item.strategy: item for item in result.strategy_results}


def test_automatic_acceptance_keeps_a_stale_candidate() -> None:
    result, strategies = _by_strategy()
    automatic = strategies[ConsolidationProposalLifecycleStrategy.AUTOMATIC_ACCEPTANCE]

    assert result.old_candidate_id != result.current_candidate_id
    assert automatic.stale_acceptance_count == 1
    assert automatic.current_proposal_blocked_count == 1
    assert automatic.current_review_delay_episodes == 4
    assert automatic.retained_record_count == 1
    assert automatic.retained_history_event_count == 1
    assert automatic.active_record_count == 1
    assert not automatic.accepted_current_proposal


def test_permanent_deferral_avoids_acceptance_but_delays_current_review() -> None:
    _, strategies = _by_strategy()
    deferred = strategies[ConsolidationProposalLifecycleStrategy.PERMANENT_DEFERRAL]

    assert deferred.stale_acceptance_count == 0
    assert deferred.current_proposal_blocked_count == 1
    assert deferred.current_review_delay_episodes == 4
    assert deferred.retained_record_count == 1
    assert deferred.retained_history_event_count == 1
    assert deferred.active_record_count == 1
    assert not deferred.accepted_current_proposal


def test_evidence_aware_strategy_replaces_then_accepts_current_proposal() -> None:
    result, strategies = _by_strategy()
    evidence_aware = strategies[ConsolidationProposalLifecycleStrategy.EVIDENCE_AWARE_EXPLICIT]

    assert evidence_aware.stale_acceptance_count == 0
    assert evidence_aware.unnecessary_rejection_count == 0
    assert evidence_aware.current_review_delay_episodes == 1
    assert evidence_aware.duplicate_decision_count == 0
    assert evidence_aware.current_proposal_blocked_count == 0
    assert evidence_aware.retained_record_count == 2
    assert evidence_aware.retained_history_event_count == 3
    assert evidence_aware.active_record_count == 1
    assert evidence_aware.accepted_current_proposal
    assert tuple(event.event_code for event in evidence_aware.events) == (
        "proposal_added",
        "proposal_deferred",
        "proposal_replaced",
        "current_proposal_accepted",
    )
    assert result.evidence_aware_is_best


def test_experiment_is_exactly_deterministic() -> None:
    first = run_consolidation_proposal_lifecycle_experiment()
    second = run_consolidation_proposal_lifecycle_experiment()

    assert first == second
    assert first.snapshot() == second.snapshot()


def test_experiment_preserves_history_without_execution_or_sqlite() -> None:
    result = run_consolidation_proposal_lifecycle_experiment()

    assert result.ledger_unchanged_by_lifecycle
    assert result.applied_candidate_count == 0
    assert result.action_authority_violations == 0
    assert not result.sqlite_cognitive_dependency
    assert all(
        strategy.applied_candidate_count == 0
        and strategy.action_authority_violations == 0
        and all(not event.has_execution_authority for event in strategy.events)
        and not strategy.final_registry.has_execution_authority
        for strategy in result.strategy_results
    )


def test_lifecycle_experiment_export_is_ascii_and_inspectable(tmp_path: Path) -> None:
    result = run_consolidation_proposal_lifecycle_experiment()
    path = tmp_path / "proposal_lifecycle_experiment.json"

    export_consolidation_proposal_lifecycle_experiment(result, path)

    raw = path.read_bytes()
    payload = json.loads(raw.decode("ascii"))
    assert raw.isascii()
    assert payload["evidence_aware_is_best"] is True
    assert payload["applied_candidate_count"] == 0
    assert len(payload["strategy_results"]) == 3


def test_lifecycle_experiment_has_no_application_persistence_or_integration_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_proposal_lifecycle_experiment.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "consolidation_application" not in source
    assert "rollback_consolidation" not in source
    assert "seedmind.integration" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert ".apply(" not in source
