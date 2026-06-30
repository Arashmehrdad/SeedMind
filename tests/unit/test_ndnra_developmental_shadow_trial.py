"""Tests for NDNRA v0.2 Stage 8 software-only shadow trial evidence."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    AmbitionCapabilityGapEvidence,
    DESAShadowDisposition,
    InspectabilityEvidence,
    LearnedSkillSurvivalEvidence,
    OldTaskRetentionEvidence,
    ResourceBudgetEvidence,
    ShadowBaselineAction,
    ShadowOutcomeState,
    ShadowProposalObservation,
    ShadowTaskFamily,
    StageEightShadowConfig,
    StageEightShadowTrialEvidence,
    TemporarySkillIncubationEvidence,
    run_stage_eight_shadow_trial_acceptance,
)


def test_stage_eight_acceptance_matrix_complete_and_zero_authority() -> None:
    evidence = run_stage_eight_shadow_trial_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.sqlite_cognition_operation_count == 0
    assert evidence.production_action_authority_violations == 0
    assert evidence.external_side_effect_count == 0
    assert all(not item.executed_by_ndnra for item in evidence.proposal_observations)
    assert all(
        not item.production_action_authority_granted for item in evidence.proposal_observations
    )


def test_production_actions_cover_task_families_and_remain_baseline_fixed() -> None:
    actions = run_stage_eight_shadow_trial_acceptance().baseline_actions

    assert {action.family for action in actions} == set(ShadowTaskFamily)
    assert all(
        action.baseline_action_code == action.observed_production_action_code for action in actions
    )
    assert all(not action.ndnra_replaced_action for action in actions)
    with pytest.raises(ValueError, match="identical"):
        replace(actions[0], observed_production_action_code="baseline:different")
    with pytest.raises(ValueError, match="cannot replace"):
        replace(actions[0], ndnra_replaced_action=True)


def test_shadow_proposals_are_context_sensitive_and_non_executable() -> None:
    evidence = run_stage_eight_shadow_trial_acceptance()
    inhibited = [
        item
        for item in evidence.proposal_observations
        if item.outcome_state is ShadowOutcomeState.INHIBITED
    ]

    assert inhibited
    assert all(item.context_sensitivity >= 0.6 for item in evidence.proposal_observations)
    assert all(item.recurrent_activation_support >= 0.6 for item in evidence.proposal_observations)
    assert all(item.proposal.supporting_experience_ids for item in evidence.proposal_observations)
    assert inhibited[0].proposal.prohibited
    assert inhibited[0].proposal.inhibited
    with pytest.raises(ValueError, match="context-sensitive"):
        replace(evidence.proposal_observations[0], context_sensitivity=0.2)
    with pytest.raises(ValueError, match="production authority"):
        replace(evidence.proposal_observations[0], production_action_authority_granted=True)


def test_desa_partitions_delegate_escalate_and_preserve_contributions() -> None:
    traces = run_stage_eight_shadow_trial_acceptance().desa_traces

    assert any(trace.uncertainty_escalated for trace in traces)
    assert any(trace.disposition is DESAShadowDisposition.PROTECTED_INHIBITION for trace in traces)
    assert all(trace.partition_codes for trace in traces)
    assert all(trace.delegated_region_codes for trace in traces)
    assert all(trace.contribution_codes for trace in traces)
    with pytest.raises(ValueError, match="partitions"):
        replace(traces[0], partition_codes=())
    escalated = next(
        trace
        for trace in traces
        if trace.disposition is DESAShadowDisposition.ESCALATED_UNCERTAINTY
    )
    with pytest.raises(ValueError, match="uncertainty_escalated"):
        replace(escalated, uncertainty_escalated=False)


def test_multiple_needs_remain_represented_and_prohibition_inhibits() -> None:
    evidence = run_stage_eight_shadow_trial_acceptance()

    assert all(len(item.active_need_codes) >= 2 for item in evidence.need_evidence)
    assert any(item.protected_inhibition_code is not None for item in evidence.need_evidence)
    with pytest.raises(ValueError, match="multiple represented needs"):
        replace(evidence.need_evidence[0], active_need_codes=("need:accuracy",))
    with pytest.raises(ValueError, match="pass gates failed"):
        replace(
            evidence,
            need_evidence=tuple(
                replace(item, protected_inhibition_code=None) for item in evidence.need_evidence
            ),
        )


def test_skill_survives_maturation_dormancy_dream_and_restart() -> None:
    skill = run_stage_eight_shadow_trial_acceptance().skill_survival

    assert skill.pre_maturation_identity == skill.post_restart_identity
    assert skill.verifier_code
    assert skill.calibration_history_codes
    assert skill.factual_evidence_created_by_dream == 0
    with pytest.raises(ValueError, match="restart exactly"):
        replace(skill, post_restart_identity="skill-identity:changed")
    with pytest.raises(ValueError, match="factual_evidence_created_by_dream"):
        replace(skill, factual_evidence_created_by_dream=1)


def test_ambition_gap_decreases_and_temporary_skill_preserves_unverified_outcome() -> None:
    evidence = run_stage_eight_shadow_trial_acceptance()

    assert evidence.ambition_gap.later_gap < evidence.ambition_gap.initial_gap
    assert evidence.temporary_skill.outcome_state is ShadowOutcomeState.UNVERIFIED_PRESERVED
    assert not evidence.temporary_skill.grounded_feedback_available
    with pytest.raises(ValueError, match="capability gap"):
        replace(evidence.ambition_gap, later_gap=evidence.ambition_gap.initial_gap)
    with pytest.raises(ValueError, match="must guide learning"):
        replace(evidence.ambition_gap, learning_guided_by_gap=False)
    with pytest.raises(ValueError, match="unverified outcome"):
        replace(evidence.temporary_skill, outcome_state=ShadowOutcomeState.BASELINE_OBSERVED)
    with pytest.raises(ValueError, match="cannot be promoted"):
        replace(evidence.temporary_skill, promoted_to_success_without_feedback=True)


def test_retention_resource_and_inspectability_bounds() -> None:
    evidence = run_stage_eight_shadow_trial_acceptance()

    assert evidence.old_task_retention.degradation <= evidence.config.degradation_threshold
    assert evidence.resource_budget.measured_cpu_fraction <= evidence.config.resource_budget
    assert evidence.resource_budget.measured_memory_fraction <= evidence.config.resource_budget
    assert "artifact:proposal_reasons" in evidence.inspectability.artifact_codes
    with pytest.raises(ValueError, match="pass gates failed"):
        replace(
            evidence,
            old_task_retention=OldTaskRetentionEvidence(
                "task:read_only_inspection",
                baseline_success=0.91,
                post_learning_success=0.84,
                degradation=0.07,
            ),
        )
    with pytest.raises(ValueError, match="pass gates failed"):
        replace(
            evidence,
            resource_budget=ResourceBudgetEvidence(
                measured_cpu_fraction=0.8,
                measured_memory_fraction=0.37,
            ),
        )
    with pytest.raises(ValueError, match="missing inspectable"):
        InspectabilityEvidence(("artifact:experiences",))


def test_stage_eight_deterministic_and_config_bounds() -> None:
    first = run_stage_eight_shadow_trial_acceptance(StageEightShadowConfig(seed=808))
    second = run_stage_eight_shadow_trial_acceptance(StageEightShadowConfig(seed=808))

    assert first.evidence_id == second.evidence_id
    assert first.snapshot() == second.snapshot()
    with pytest.raises(ValueError, match="max_shadow_steps"):
        StageEightShadowConfig(max_shadow_steps=0)
    with pytest.raises(ValueError, match="step bound"):
        run_stage_eight_shadow_trial_acceptance(StageEightShadowConfig(max_shadow_steps=5))


def test_stage_eight_integrated_state_rejects_missing_coverage_and_mutation() -> None:
    evidence = run_stage_eight_shadow_trial_acceptance()

    with pytest.raises(ValueError, match="proposal observations"):
        replace(evidence, proposal_observations=evidence.proposal_observations[:-1])
    with pytest.raises(ValueError, match="DESA traces"):
        replace(evidence, desa_traces=evidence.desa_traces[:-1])
    with pytest.raises(ValueError, match="need evidence"):
        replace(evidence, need_evidence=evidence.need_evidence[:-1])
    with pytest.raises(ValueError, match="sqlite_cognition_operation_count"):
        replace(evidence, sqlite_cognition_operation_count=1)
    with pytest.raises(ValueError, match="production_action_authority_violations"):
        replace(evidence, production_action_authority_violations=1)


def test_public_exports_cover_stage_eight_shadow_trial() -> None:
    exported = set(ndnra.__all__)

    assert "AmbitionCapabilityGapEvidence" in exported
    assert "DESAShadowDisposition" in exported
    assert "InspectabilityEvidence" in exported
    assert "LearnedSkillSurvivalEvidence" in exported
    assert "OldTaskRetentionEvidence" in exported
    assert "ResourceBudgetEvidence" in exported
    assert "ShadowBaselineAction" in exported
    assert "ShadowOutcomeState" in exported
    assert "ShadowProposalObservation" in exported
    assert "ShadowTaskFamily" in exported
    assert "StageEightShadowConfig" in exported
    assert "StageEightShadowTrialEvidence" in exported
    assert "TemporarySkillIncubationEvidence" in exported
    assert "run_stage_eight_shadow_trial_acceptance" in exported
    assert StageEightShadowTrialEvidence.__name__ in exported
    assert ShadowProposalObservation.__name__ in exported
    assert ShadowBaselineAction.__name__ in exported
    assert AmbitionCapabilityGapEvidence.__name__ in exported
    assert LearnedSkillSurvivalEvidence.__name__ in exported
    assert TemporarySkillIncubationEvidence.__name__ in exported


def test_developmental_shadow_trial_has_no_forbidden_runtime_dependencies() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_shadow_trial.py"
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
    assert "production action gateway" not in source.lower()
    assert "stage 9" not in source.lower()
