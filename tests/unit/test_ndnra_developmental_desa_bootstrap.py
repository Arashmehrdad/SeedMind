"""Tests for NDNRA v0.2 Stage 1A DESA bootstrap evidence."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    DESABootstrapConfig,
    DESABootstrapRoutingDecision,
    DESABootstrapStrategy,
    DESARoutingDisposition,
    DESARoutingStrategyResult,
    DESAVerifierCalibrationEvidence,
    DESAWorkspaceCoalition,
    EventPartitionLedger,
    OutcomeFidelityState,
    RegionalCalibrationEvidence,
    RegionalCaptainContribution,
    SkillBundleLifecycle,
    StewardGateDecision,
    run_stage_one_a_desa_bootstrap_acceptance,
)


def test_stage_one_a_acceptance_matrix_is_complete_and_zero_authority() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.sqlite_cognition_operation_count == 0
    assert evidence.external_side_effect_count == 0
    assert evidence.production_action_authority_violations == 0
    assert evidence.skill_bundle.has_production_action_authority is False
    assert evidence.snapshot() == evidence.snapshot()


def test_routing_resolves_local_work_and_escalates_uncertainty_conflict_and_failure() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()

    assert evidence.local_decision.disposition is DESARoutingDisposition.LOCAL
    assert evidence.escalation_decision.disposition is DESARoutingDisposition.COUNCIL

    with pytest.raises(ValueError, match="should not escalate"):
        DESABootstrapRoutingDecision(
            decision_code="route:bad_local",
            familiar=True,
            low_risk=True,
            low_confidence=False,
            cross_region_conflict=False,
            important_failure=False,
            disposition=DESARoutingDisposition.COUNCIL,
        )
    with pytest.raises(ValueError, match="must escalate"):
        DESABootstrapRoutingDecision(
            decision_code="route:missed_escalation",
            familiar=False,
            low_risk=False,
            low_confidence=True,
            cross_region_conflict=False,
            important_failure=False,
            disposition=DESARoutingDisposition.LOCAL,
        )


def test_regional_captains_share_workspace_without_monopoly() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()

    assert len({item.region_code for item in evidence.captain_contributions}) >= 2
    assert len(evidence.workspace.workspace_neuron_ids) <= evidence.config.workspace_capacity
    assert any(item.abstained for item in evidence.captain_contributions)
    assert any(item.disagreement > 0.5 for item in evidence.captain_contributions)

    with pytest.raises(ValueError, match="abstaining captain"):
        RegionalCaptainContribution(
            region_code="region:bad",
            confidence=0.2,
            disagreement=0.8,
            competence=0.5,
            cost=1.0,
            contribution_neuron_ids=("n:0",),
            abstained=True,
        )
    with pytest.raises(ValueError, match="exceeds capacity"):
        DESAWorkspaceCoalition(
            coalition_code="workspace:too_large",
            contributor_region_codes=("region:body", "region:need"),
            workspace_neuron_ids=("n:0", "n:1"),
            capacity=1,
        )


def test_minimal_desa_beats_shuffled_and_single_central_controls() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()
    by_strategy = {result.strategy: result for result in evidence.strategy_results}
    minimal = by_strategy[DESABootstrapStrategy.MINIMAL_DESA]
    shuffled = by_strategy[DESABootstrapStrategy.SHUFFLED_ROUTING]
    single = by_strategy[DESABootstrapStrategy.SINGLE_CENTRAL_CAPTAIN]

    assert minimal.usefulness > shuffled.usefulness
    assert minimal.usefulness > single.usefulness
    assert minimal.interference < shuffled.interference
    assert single.monopolized_by_single_region

    with pytest.raises(ValueError, match="non-single-captain"):
        DESARoutingStrategyResult(
            DESABootstrapStrategy.MINIMAL_DESA,
            usefulness=0.5,
            interference=0.2,
            compute_cost=1.0,
            monopolized_by_single_region=True,
        )


def test_optional_steward_and_feedback_learning_are_evidence_bound() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()

    assert evidence.accepted_steward_gate.decision is StewardGateDecision.ACCEPTED
    assert evidence.rejected_steward_gate.decision is StewardGateDecision.REJECTED
    assert (
        evidence.skill_learning.grounded_feedback_success_rate
        > evidence.skill_learning.producer_self_verification_success_rate
    )
    assert evidence.skill_learning.pending_outcome.state is OutcomeFidelityState.UNVERIFIED_OUTCOME

    with pytest.raises(ValueError, match="exceeds configured feedback-iteration bound"):
        run_stage_one_a_desa_bootstrap_acceptance(
            DESABootstrapConfig(maximum_feedback_iterations=1),
        )


def test_temporary_skill_bundle_and_feedback_loop_remain_bounded() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()

    assert evidence.skill_bundle.lifecycle is SkillBundleLifecycle.INCUBATING_SKILL
    assert evidence.feedback_iteration.bundle_id == evidence.skill_bundle.bundle_id
    assert evidence.feedback_iteration.retry_budget <= evidence.config.maximum_feedback_iterations

    mature_bundle = replace(evidence.skill_bundle, lifecycle=SkillBundleLifecycle.MATURE_SKILL)
    with pytest.raises(ValueError, match="temporary incubating skill"):
        replace(evidence, skill_bundle=mature_bundle)
    with pytest.raises(ValueError, match="feedback iteration must bind"):
        replace(evidence, feedback_iteration=replace(evidence.feedback_iteration, bundle_id="bad"))


def test_calibration_beats_raw_activation_and_producer_confidence() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()
    calibration = evidence.calibration_evidence

    assert (
        calibration.regional_calibration.regional_confidence_error
        < calibration.raw_max_activation_error
    )
    assert calibration.verifier_calibrated_error < calibration.raw_max_activation_error
    assert calibration.verifier_calibrated_error < calibration.producer_confidence_error

    with pytest.raises(ValueError, match="producer confidence"):
        DESAVerifierCalibrationEvidence(
            evidence_code="calibration:bad",
            raw_max_activation_error=0.34,
            producer_confidence_error=0.2,
            verifier_calibrated_error=0.25,
            regional_calibration=RegionalCalibrationEvidence(
                evidence_code="calibration:regional_bad",
                raw_max_activation_error=0.34,
                regional_confidence_error=0.18,
            ),
        )


def test_event_partitioning_preserves_raw_chronology_and_improves_recall() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()

    assert evidence.event_ledger.preserved_raw_event_ids == tuple(
        event.event_id for event in evidence.event_ledger.raw_events
    )
    assert (
        evidence.boundary_recall.desa_partition_recall
        > evidence.boundary_recall.one_session_control_recall
    )
    assert (
        evidence.boundary_recall.desa_partition_recall
        > evidence.boundary_recall.every_step_control_recall
    )

    reordered = replace(
        evidence.event_ledger.operations[2],
        raw_event_ids=("stage1a:raw:003", "stage1a:raw:002"),
    )
    with pytest.raises(ValueError, match="cannot reorder raw events"):
        EventPartitionLedger(
            raw_events=evidence.event_ledger.raw_events,
            operations=(
                evidence.event_ledger.operations[0],
                evidence.event_ledger.operations[1],
                reordered,
                *evidence.event_ledger.operations[3:],
            ),
        )


def test_auditor_ambition_and_deterministic_identity_are_separate_and_reproducible() -> None:
    first = run_stage_one_a_desa_bootstrap_acceptance()
    second = run_stage_one_a_desa_bootstrap_acceptance()
    gap_ids = {gap.gap_id for gap in first.temporary_ambition.capability_gaps}

    assert first.evidence_id == second.evidence_id
    assert first.auditor_correction.later_evidence_codes
    assert first.temporary_ambition.value_source.value_source_id not in gap_ids
    assert first.temporary_ambition.has_production_action_authority is False


def test_public_exports_cover_stage_one_a_desa_bootstrap() -> None:
    exported = set(ndnra.__all__)

    assert "DESABootstrapConfig" in exported
    assert "DESABootstrapStrategy" in exported
    assert "DESAVerifierCalibrationEvidence" in exported
    assert "StageOneADESABootstrapEvidence" in exported
    assert "run_stage_one_a_desa_bootstrap_acceptance" in exported


def test_stage_one_a_rejects_failed_gate_and_forbidden_runtime_dependencies() -> None:
    evidence = run_stage_one_a_desa_bootstrap_acceptance()
    with pytest.raises(ValueError, match="external_side_effect_count"):
        replace(evidence, external_side_effect_count=1)
    with pytest.raises(ValueError, match="production_action_authority_violations"):
        replace(evidence, production_action_authority_violations=1)
    with pytest.raises(ValueError, match="sqlite_cognition_operation_count"):
        replace(evidence, sqlite_cognition_operation_count=1)

    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_desa_bootstrap.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = {"asyncio", "concurrent", "queue", "sqlite3", "threading", "time"}
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module.split(".")[0])

    assert imports.isdisjoint(forbidden_roots)
    assert "seedmind.integration" not in source
    assert "ActionGateway" not in source
    assert "learned_consequence" not in source
    assert "bounded_imagination" not in source
