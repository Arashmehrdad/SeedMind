"""Tests for live learned-consequence acceptance without action authority."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.integration import (
    LearnedConsequenceLivePredictionRecord,
    export_learned_consequence_acceptance,
    run_learned_consequence_acceptance,
)


def test_learned_consequence_acceptance_passes_live_shadow_gate(
    tmp_path: Path,
) -> None:
    evidence = run_learned_consequence_acceptance(tmp_path, play_budget=8)
    result = evidence.result

    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.pretraining_selection_count == 8
    assert result.baseline_selection_count == 8
    assert result.evaluation_selection_count == 8
    assert result.pre_action_prediction_count == 8
    assert result.evaluated_prediction_count == 8
    assert result.minimum_evaluation_accuracy > 0.0
    assert result.uncertainty_reduction_observed
    assert result.contradiction_confidence_reduction_observed
    assert result.context_local_unknown_preserved
    assert result.learned_real_observation_count == 16
    assert result.learned_record_count >= 1
    assert result.checkpoint_automatic_prediction_count == 0
    assert result.authority_violation_count == 0
    assert result.advice_decision_count == 0
    assert result.route_ranking_count == 0
    assert result.growth_attempt_count == 0
    assert result.replay_operation_count == 0
    assert result.restoration_operation_count == 0
    assert not result.sqlite_used_for_learned_consequence_acceptance
    assert result.expanded_architecture_before == 80
    assert result.expanded_architecture_after == 82
    assert result.pass_gate


def test_evaluation_records_are_pre_action_predictions_with_real_calibration(
    tmp_path: Path,
) -> None:
    evidence = run_learned_consequence_acceptance(tmp_path, play_budget=8)

    assert all(record.phase == "evaluation" for record in evidence.evaluation.records)
    assert all(record.evidence_count_before > 0 for record in evidence.evaluation.records)
    assert all(record.predicted_effect_count == 5 for record in evidence.evaluation.records)
    assert all(record.predicted_next_context_available for record in evidence.evaluation.records)
    assert all(record.evaluation_eligible for record in evidence.evaluation.records)
    assert all(record.combined_accuracy is not None for record in evidence.evaluation.records)
    assert any(
        record.uncertainty_after < record.uncertainty_before
        for record in evidence.evaluation.records
    )
    assert not any(
        record.has_action_selection_authority or record.has_production_action_authority
        for record in evidence.evaluation.records
    )


def test_learned_consequence_acceptance_exports_are_ascii_and_inspectable(
    tmp_path: Path,
) -> None:
    evidence = run_learned_consequence_acceptance(tmp_path, play_budget=8)

    report_path, timeline_path, checkpoint_path = export_learned_consequence_acceptance(
        evidence,
        tmp_path,
    )

    report = report_path.read_text(encoding="ascii")
    timeline = timeline_path.read_text(encoding="ascii")
    checkpoint = checkpoint_path.read_text(encoding="ascii")
    assert '"production_actions_unchanged": true' in report
    assert '"pass_gate": true' in report
    assert timeline.startswith("phase,step_index,source_step_id,action_code")
    assert '"schema": "seedmind.ndnra.learned_consequence"' in checkpoint
    assert '"automatic_prediction_count": 0' in checkpoint
    assert '"has_production_action_authority": false' in checkpoint


def test_live_prediction_record_rejects_action_authority() -> None:
    with pytest.raises(ValueError, match="cannot select actions"):
        LearnedConsequenceLivePredictionRecord(
            phase="evaluation",
            step_index=0,
            source_step_id=0,
            action_code="wait",
            event_id="real:test:0001",
            prediction_id="prediction:test",
            evidence_count_before=1,
            predicted_effect_count=1,
            predicted_next_context_available=True,
            confidence_before=0.1,
            confidence_after=0.2,
            uncertainty_before=0.9,
            uncertainty_after=0.8,
            evidence_applied=True,
            evaluation_eligible=True,
            combined_accuracy=1.0,
            calibration_direction="underconfident",
            has_action_selection_authority=True,
        )


def test_learned_consequence_acceptance_has_no_decision_authority_dependencies() -> None:
    source = Path("src/seedmind/integration/learned_consequence_acceptance.py").read_text(
        encoding="utf-8"
    )

    assert "import sqlite3" not in source
    assert "EpisodicSQLiteStore" not in source
    assert "BoundedAdvicePolicy" not in source
    assert "NeedDrivenComposer" not in source
    assert "ControlledReplay" not in source
