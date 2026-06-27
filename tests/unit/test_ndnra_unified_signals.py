"""Tests for live developmental signals and operational restored NDNRA state."""

from __future__ import annotations

from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.integration import (
    LiveDevelopmentalSignals,
    NDNRALiveShadowAdapter,
    export_unified_signal_evidence,
    run_unified_signal_experiment,
)
from seedmind.integration.advice_acceptance import run_advice_acceptance
from seedmind.research.ndnra import (
    EffectObservation,
    MultidimensionalExperienceGraph,
    NDNRAGrowthState,
    NDNRARuntimeAdaptiveState,
)
from seedmind.research.ndnra.multi_growth_experiment import (
    run_multi_growth_experiment,
)


def _signals() -> LiveDevelopmentalSignals:
    return LiveDevelopmentalSignals(
        step_index=-1,
        ambition_relevance=0.8,
        ambition_commitment=0.8,
        ambition_learning_progress=0.2,
        curiosity_value=0.7,
        curiosity_learning_progress=0.2,
        curiosity_uncertainty=0.6,
        self_controllability=0.2,
        body_confidence=0.2,
        help_requested=0.0,
        human_approval=0.0,
        human_correction=0.0,
        human_demonstration=0.0,
        human_clarification=0.0,
        human_signal_magnitude=0.0,
        prediction_error=0.6,
        resource_pressure=0.1,
        need_resolution=0.1,
    )


def _shadow_graph() -> MultidimensionalExperienceGraph:
    graph = MultidimensionalExperienceGraph()
    graph.learn_experience(
        assembly_id="assembly:shadow:turn_left",
        action_code="turn_left",
        origin_need_code="test",
        required_facts=("available:turn_left",),
        produced_facts=("experienced:turn_left",),
        observed_effects=(
            EffectObservation("curiosity_value", 0.8, 1.0),
            EffectObservation("ambition_relevance", 0.7, 1.0),
            EffectObservation("need_resolution", 0.4, 1.0),
        ),
    )
    return graph


def test_restored_dormancy_changes_live_action_accessibility_and_score() -> None:
    graph = _shadow_graph()
    dormant = NDNRAGrowthState(
        dormancy_levels=(("assembly:shadow:turn_left", 0.75),),
    )
    restored = NDNRALiveShadowAdapter(graph=graph, growth_state=dormant)
    reset = NDNRALiveShadowAdapter(graph=graph, growth_state=NDNRAGrowthState())

    restored_access, restored_score = restored.evaluate_action(
        PrimitiveAction.TURN_LEFT,
        _signals(),
    )
    reset_access, reset_score = reset.evaluate_action(
        PrimitiveAction.TURN_LEFT,
        _signals(),
    )

    assert restored_access == 0.25
    assert reset_access == 1.0
    assert restored_score < reset_score


def test_restored_eligibility_and_pressure_continue_instead_of_resetting() -> None:
    graph = _shadow_graph()
    restored = NDNRARuntimeAdaptiveState.from_growth_state(
        graph,
        NDNRAGrowthState(
            pressure=0.4,
            eligibility=(("assembly:shadow:turn_left", 0.3),),
            residuals=(0.1,),
            attempt_count=5,
            last_active_members=("assembly:shadow:turn_left",),
            dormancy_levels=(("assembly:shadow:turn_left", 0.5),),
        ),
    )

    update = restored.observe(
        assembly_id="assembly:shadow:turn_left",
        unresolved_error=0.5,
        curiosity=0.8,
        ambition_relevance=0.7,
        capacity_saturation=1.0,
        residual_effect=0.2,
    )

    assert update.pressure_before == 0.4
    assert update.pressure_after > update.pressure_before
    assert update.attempt_count_before == 5
    assert update.attempt_count_after == 6
    assert update.eligibility_before == 0.3
    assert update.eligibility_after > update.eligibility_before
    assert update.dormancy_before == 0.5
    assert update.dormancy_after == 0.0
    assert restored.to_growth_state().attempt_count == 6


def test_unified_live_signal_gate_passes_without_changing_production(
    tmp_path: Path,
) -> None:
    evidence = run_unified_signal_experiment(tmp_path, play_budget=12)
    result = evidence.result

    assert result.restored_eligibility_continued
    assert result.dormancy_changed_accessibility
    assert result.dormancy_changed_action_score
    assert result.ambition_relevance_varied
    assert result.maximum_self_controllability > 0.0
    assert result.maximum_body_confidence > 0.0
    assert result.help_request_count > 0
    assert result.human_response_count > 0
    assert result.live_signal_dimension_count >= 17
    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.authority_violation_count == 0
    assert not result.sqlite_used_for_signals_or_adaptation
    assert result.pass_gate


def test_unified_live_signal_exports_are_ascii_and_inspectable(
    tmp_path: Path,
) -> None:
    evidence = run_unified_signal_experiment(tmp_path, play_budget=12)
    report_path, timeline_path, adaptive_path = export_unified_signal_evidence(
        evidence,
        tmp_path,
    )

    report = report_path.read_text(encoding="ascii")
    timeline = timeline_path.read_text(encoding="ascii")
    adaptive = adaptive_path.read_text(encoding="ascii")
    assert '"production_actions_unchanged": true' in report
    assert '"ambition_relevance_varied": true' in report
    assert timeline.startswith("step_index,actual_action,suggested_action")
    assert '"dormancy_levels"' in adaptive


def test_complex_goal_retains_pressure_until_second_growth() -> None:
    result = run_multi_growth_experiment()

    assert not result.first_growth_goal_achieved
    assert not result.first_growth_pressure_discharged
    assert result.first_growth_continue_growth
    assert result.second_growth_goal_achieved
    assert result.second_growth_pressure_discharged
    assert not result.second_growth_continue_growth
    assert result.pressure_after_final_discharge < result.pressure_before_final_discharge
    assert result.growth_step_count == 2
    assert result.specialist_count == 2
    assert result.duplicate_membership_blocked
    assert result.pass_gate


def test_bounded_advice_gate_retains_production(tmp_path: Path) -> None:
    evidence = run_advice_acceptance(tmp_path, play_budget=18)
    result = evidence.result

    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.authority_violation_count == 0
    assert result.disagreement_count > 0
    assert result.comparison_count == result.disagreement_count
    assert result.advice_count > 0
    assert result.calibration_observation_count > 0
    assert result.kill_switch_probe_passed
    assert result.fallback_probe_passed
    assert result.risk_veto_probe_passed
    assert result.human_veto_probe_passed
    assert result.weak_evidence_probe_passed
    assert result.first_growth_continue_growth
    assert result.second_growth_pressure_discharged
    assert result.growth_budget_exhaustion_probe_passed
    assert not result.sqlite_used_for_advice_or_growth
    assert result.pass_gate


def test_unified_integration_has_no_sqlite_cognitive_dependency() -> None:
    files = (
        Path("src/seedmind/integration/developmental_signals.py"),
        Path("src/seedmind/integration/unified_shadow.py"),
        Path("src/seedmind/integration/unified_signal_experiment.py"),
        Path("src/seedmind/research/ndnra/adaptive.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
