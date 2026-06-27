"""Tests for the proposal-only consolidation scheduling experiment."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationSchedulingExperimentConfig,
    ConsolidationSchedulingExperimentResult,
    ConsolidationSchedulingStrategy,
    ConsolidationSchedulingStrategyResult,
    export_consolidation_scheduling_experiment,
    run_consolidation_scheduling_experiment,
)


def _by_strategy() -> tuple[
    ConsolidationSchedulingExperimentResult,
    dict[ConsolidationSchedulingStrategy, ConsolidationSchedulingStrategyResult],
]:
    result = run_consolidation_scheduling_experiment()
    return result, {item.strategy: item for item in result.strategy_results}


def test_fixed_interval_creates_false_and_late_proposals() -> None:
    _, strategies = _by_strategy()
    fixed = strategies[ConsolidationSchedulingStrategy.FIXED_INTERVAL]

    assert fixed.proposal_count == 12
    assert fixed.eligible_proposal_count == 5
    assert fixed.false_proposal_count == 7
    assert fixed.redundant_proposal_count == 3
    assert fixed.missed_eligible_window_count == 4
    assert fixed.capacity_pressure_count == 8
    assert fixed.proposal_precision == pytest.approx(5 / 12)


def test_eligibility_only_is_precise_but_highly_repetitive() -> None:
    _, strategies = _by_strategy()
    eligibility_only = strategies[ConsolidationSchedulingStrategy.ELIGIBILITY_ONLY]

    assert eligibility_only.proposal_count == 15
    assert eligibility_only.eligible_proposal_count == 15
    assert eligibility_only.false_proposal_count == 0
    assert eligibility_only.redundant_proposal_count == 13
    assert eligibility_only.missed_eligible_window_count == 0
    assert eligibility_only.capacity_pressure_count == 6
    assert eligibility_only.proposal_precision == 1.0


def test_evidence_aware_scheduling_is_precise_bounded_and_non_redundant() -> None:
    result, strategies = _by_strategy()
    evidence_aware = strategies[ConsolidationSchedulingStrategy.EVIDENCE_AWARE_BOUNDED]

    assert evidence_aware.proposal_count == 2
    assert evidence_aware.eligible_proposal_count == 2
    assert evidence_aware.false_proposal_count == 0
    assert evidence_aware.redundant_proposal_count == 0
    assert evidence_aware.missed_eligible_window_count == 0
    assert evidence_aware.capacity_pressure_count == 0
    assert evidence_aware.proposal_precision == 1.0
    assert result.evidence_aware_is_best


def test_controlled_evidence_arrival_has_two_mastered_lessons() -> None:
    result = run_consolidation_scheduling_experiment()

    assert result.eligibility_onsets == (
        ("reduce_heat|cooling|positive", 3),
        ("remove_dirt|cleanliness|positive", 6),
    )
    evidence_aware = result.strategy_results[2]
    assert tuple(record.episode_index for record in evidence_aware.proposal_records) == (3, 6)
    assert tuple(record.lesson_key for record in evidence_aware.proposal_records) == (
        "reduce_heat|cooling|positive",
        "remove_dirt|cleanliness|positive",
    )


def test_experiment_is_exactly_deterministic() -> None:
    first = run_consolidation_scheduling_experiment()
    second = run_consolidation_scheduling_experiment()

    assert first == second
    assert first.snapshot() == second.snapshot()


def test_experiment_never_applies_or_authorizes_consolidation() -> None:
    result = run_consolidation_scheduling_experiment()

    assert result.ledger_unchanged_by_scheduling
    assert result.applied_candidate_count == 0
    assert result.action_authority_violations == 0
    assert not result.sqlite_cognitive_dependency
    assert all(
        not record.has_execution_authority
        for strategy in result.strategy_results
        for record in strategy.proposal_records
    )


def test_experiment_export_is_ascii_and_inspectable(tmp_path: Path) -> None:
    result = run_consolidation_scheduling_experiment()
    path = tmp_path / "scheduling_experiment.json"

    export_consolidation_scheduling_experiment(result, path)

    raw = path.read_bytes()
    payload = json.loads(raw.decode("ascii"))
    assert raw.isascii()
    assert payload["evidence_aware_is_best"] is True
    assert payload["applied_candidate_count"] == 0
    assert len(payload["strategy_results"]) == 3


def test_experiment_config_rejects_invalid_values() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        ConsolidationSchedulingExperimentConfig(fixed_interval_episodes=0)
    with pytest.raises(ValueError, match="positive integer"):
        ConsolidationSchedulingExperimentConfig(proposal_capacity_per_episode=0)
    with pytest.raises(ValueError, match="cannot exceed"):
        ConsolidationSchedulingExperimentConfig(
            final_episode=5,
            fixed_first_episode=6,
        )


def test_experiment_module_has_no_application_persistence_or_integration_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_scheduling_experiment.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "consolidation_application" not in source
    assert "rollback_consolidation" not in source
    assert "seedmind.integration" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert ".apply(" not in source
