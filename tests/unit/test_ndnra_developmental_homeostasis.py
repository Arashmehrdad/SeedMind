"""Tests for NDNRA v0.2 Stage 5 homeostasis and saturation evidence."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    ExpansionProposalStatus,
    HomeostasisControlCondition,
    HomeostaticCoalitionState,
    StageFiveHomeostasisConfig,
    StructuralExpansionProposal,
    run_stage_five_homeostasis_acceptance,
)


def test_stage_five_acceptance_matrix_is_complete_and_zero_authority() -> None:
    evidence = run_stage_five_homeostasis_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.sqlite_cognition_operation_count == 0
    assert evidence.external_side_effect_count == 0
    assert evidence.production_action_authority_violations == 0
    assert all(not coalition.has_external_action_authority for coalition in evidence.coalitions)
    assert not evidence.expansion_proposal.has_external_action_authority
    assert not evidence.duplicate_proposal.has_external_action_authority
    assert not evidence.exhausted_budget_proposal.has_external_action_authority


def test_activation_settles_and_coalitions_remain_sparse_within_edge_budget() -> None:
    evidence = run_stage_five_homeostasis_acceptance()

    for coalition in evidence.coalitions:
        assert coalition.settled
        assert len(coalition.activation_trace) <= evidence.config.maximum_settling_cycles
        assert coalition.sparsity <= evidence.config.sparse_coalition_budget
        assert coalition.edge_density <= evidence.config.regional_edge_density_budget
        assert coalition.unrelated_context_activation < coalition.activation_trace[-1]


def test_homeostasis_controls_show_inhibition_and_homeostasis_are_needed() -> None:
    evidence = run_stage_five_homeostasis_acceptance()
    by_condition = {result.condition: result for result in evidence.control_results}
    proposed = by_condition[HomeostasisControlCondition.PROPOSED_HOMEOSTASIS]
    no_inhibition = by_condition[HomeostasisControlCondition.INHIBITION_REMOVED]
    no_homeostasis = by_condition[HomeostasisControlCondition.HOMEOSTASIS_REMOVED]
    global_shrink = by_condition[HomeostasisControlCondition.GLOBAL_SHRINK_ONLY]

    assert no_inhibition.selectivity_score < proposed.selectivity_score
    assert no_homeostasis.stability_score < proposed.stability_score
    assert proposed.relative_preference_preserved
    assert not global_shrink.relative_preference_preserved
    with pytest.raises(ValueError, match="global shrink"):
        replace(global_shrink, relative_preference_preserved=True)


def test_idle_capacity_is_recruited_before_structural_expansion() -> None:
    evidence = run_stage_five_homeostasis_acceptance()
    idle = evidence.idle_capacity_evidence

    assert set(idle.recruited_idle_neuron_ids).issubset(set(idle.idle_neuron_ids))
    assert not idle.structural_expansion_requested_before_idle_exhausted
    with pytest.raises(ValueError, match="idle capacity"):
        replace(idle, structural_expansion_requested_before_idle_exhausted=True)
    with pytest.raises(ValueError, match="idle capacity"):
        replace(idle, recruited_idle_neuron_ids=("task:missing",))


def test_one_anomaly_cannot_trigger_expansion_but_repeated_saturation_can() -> None:
    evidence = run_stage_five_homeostasis_acceptance()
    anomaly = evidence.single_anomaly_observation
    saturation_codes = tuple(obs.observation_code for obs in evidence.saturation_observations)

    assert anomaly.anomaly_only
    assert anomaly.observation_code not in evidence.expansion_proposal.causal_observation_codes
    assert len(evidence.saturation_observations) >= evidence.config.saturation_observation_minimum
    assert evidence.expansion_proposal.status is ExpansionProposalStatus.CANDIDATE
    assert evidence.expansion_proposal.causal_observation_codes == saturation_codes
    assert evidence.expansion_proposal.proposed_new_neuron_count == 1


def test_duplicate_expansion_is_rejected_and_budget_exhaustion_preserves_need() -> None:
    evidence = run_stage_five_homeostasis_acceptance()
    duplicate = evidence.duplicate_proposal
    exhausted = evidence.exhausted_budget_proposal

    assert duplicate.status is ExpansionProposalStatus.DUPLICATE_REJECTED
    assert duplicate.duplicate_of_proposal_code == evidence.expansion_proposal.proposal_code
    assert exhausted.status is ExpansionProposalStatus.BUDGET_EXHAUSTED_UNRESOLVED
    assert exhausted.unresolved_need_code == "need:handle_persistent_saturation"
    assert exhausted.help_requested
    with pytest.raises(ValueError, match="duplicate proposal reference"):
        replace(duplicate, duplicate_of_proposal_code=None)
    with pytest.raises(ValueError, match="unresolved need and help"):
        replace(exhausted, help_requested=False)


def test_expansion_proposals_reject_missing_causal_evidence_and_authority() -> None:
    evidence = run_stage_five_homeostasis_acceptance()
    proposal = evidence.expansion_proposal

    with pytest.raises(ValueError, match="causal evidence"):
        replace(proposal, causal_observation_codes=())
    with pytest.raises(ValueError, match="action authority"):
        replace(proposal, has_external_action_authority=True)


def test_mutated_homeostasis_evidence_rejects_failed_pass_gates() -> None:
    evidence = run_stage_five_homeostasis_acceptance()

    with pytest.raises(ValueError, match="pass gates failed"):
        replace(
            evidence,
            coalitions=(
                replace(
                    evidence.coalitions[0],
                    activation_trace=(0.1, 0.7, 0.2, 0.8),
                ),
                *evidence.coalitions[1:],
            ),
        )
    with pytest.raises(ValueError, match="persistent saturation"):
        replace(
            evidence,
            saturation_observations=evidence.saturation_observations[:1],
        )


def test_homeostatic_coalition_rejects_capacity_and_edge_violations() -> None:
    coalition = run_stage_five_homeostasis_acceptance().coalitions[0]

    with pytest.raises(ValueError, match="region size"):
        replace(coalition, total_region_neurons=1)
    with pytest.raises(ValueError, match="edge capacity"):
        replace(coalition, edge_count=coalition.edge_capacity + 1)
    with pytest.raises(ValueError, match="external action authority"):
        replace(coalition, has_external_action_authority=True)
    assert isinstance(coalition, HomeostaticCoalitionState)


def test_stage_five_acceptance_is_deterministic_and_config_bounded() -> None:
    first = run_stage_five_homeostasis_acceptance(StageFiveHomeostasisConfig(seed=303))
    second = run_stage_five_homeostasis_acceptance(StageFiveHomeostasisConfig(seed=303))

    assert first.evidence_id == second.evidence_id
    assert first.snapshot() == second.snapshot()
    with pytest.raises(ValueError, match="maximum_settling_cycles"):
        StageFiveHomeostasisConfig(maximum_settling_cycles=0)
    with pytest.raises(ValueError, match="regional_edge_density_budget"):
        StageFiveHomeostasisConfig(regional_edge_density_budget=1.5)


def test_public_exports_cover_stage_five_homeostasis() -> None:
    exported = set(ndnra.__all__)

    assert "ExpansionProposalStatus" in exported
    assert "HomeostasisControlCondition" in exported
    assert "HomeostasisControlResult" in exported
    assert "HomeostaticCoalitionState" in exported
    assert "IdleCapacityRecruitmentEvidence" in exported
    assert "StageFiveHomeostasisEvidence" in exported
    assert "StructuralExpansionProposal" in exported
    assert "run_stage_five_homeostasis_acceptance" in exported
    assert StructuralExpansionProposal.__name__ in exported


def test_developmental_homeostasis_has_no_forbidden_runtime_dependencies() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_homeostasis.py"
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
    assert "bounded_imagination" not in source
    assert "learned_consequence" not in source
