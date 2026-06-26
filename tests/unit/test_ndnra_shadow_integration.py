"""Tests for non-authoritative NDNRA integration with the live nursery loop."""

from pathlib import Path

import pytest

from seedmind.integration import (
    NDNRAShadowConfig,
    ShadowSuggestion,
    export_shadow_comparison_evidence,
    run_shadow_comparison,
)


def test_shadow_comparison_preserves_production_actions_and_training() -> None:
    result, shadow = run_shadow_comparison(seed=7, play_budget=6)

    assert result.action_sequence_unchanged
    assert result.prediction_error_sequence_unchanged
    assert result.baseline_selection_count == 6
    assert result.shadow_selection_count == 6
    assert result.observed_transition_count == 6
    assert shadow.authority_violation_count == 0


def test_shadow_learns_effects_and_emits_only_valid_suggestions() -> None:
    result, shadow = run_shadow_comparison(seed=7, play_budget=6)

    assert result.first_suggestion_step == 1
    assert result.suggestion_count == 5
    assert result.valid_suggestion_count == result.suggestion_count
    assert result.learned_assembly_count >= 2
    assert result.effect_dimension_count == 8
    assert result.expected_effect_dimensions_present
    assert all(
        record.suggested_action is None or record.suggestion_was_valid for record in shadow.records
    )


def test_shadow_gate_advances_integration_without_action_authority() -> None:
    (
        result,
        _,
    ) = run_shadow_comparison(seed=7, play_budget=6)

    assert result.authority_violation_count == 0
    assert not result.sqlite_used_for_shadow_decisions
    assert result.integration_percentage_before == 30
    assert result.integration_percentage_after == 45
    assert result.pass_gate


def test_shadow_suggestion_rejects_action_authority() -> None:
    with pytest.raises(ValueError, match="must never have action authority"):
        ShadowSuggestion(
            step_index=0,
            suggested_action=None,
            score=0.0,
            primary_satisfaction=0.0,
            candidate_count=0,
            learned_assembly_count=0,
            effect_dimension_count=0,
            has_action_authority=True,
        )


def test_shadow_config_rejects_multi_action_control_depth() -> None:
    with pytest.raises(ValueError, match="exactly one primitive action"):
        NDNRAShadowConfig(maximum_depth=2)


def test_shadow_exports_are_ascii_and_inspectable(tmp_path: Path) -> None:
    result, shadow = run_shadow_comparison(seed=7, play_budget=4)

    report_path, timeline_path, graph_path = export_shadow_comparison_evidence(
        result,
        shadow,
        tmp_path,
    )

    report = report_path.read_text(encoding="ascii")
    timeline = timeline_path.read_text(encoding="ascii")
    graph = graph_path.read_text(encoding="ascii")
    assert '"action_sequence_unchanged": true' in report
    assert '"authority_violation_count": 0' in report
    assert timeline.startswith("step_index,actual_action,suggested_action")
    assert '"effect_dimensions"' in graph


def test_shadow_integration_has_no_sqlite_decision_dependency() -> None:
    files = (
        Path("src/seedmind/integration/ndnra_shadow.py"),
        Path("src/seedmind/integration/shadow_experiment.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
