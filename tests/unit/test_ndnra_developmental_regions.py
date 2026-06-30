"""Tests for NDNRA v0.2 Stage 3 regional concurrency evidence."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    ConcurrentNeedPulse,
    CrossRegionMessageKind,
    DevelopmentalRegionConfig,
    DevelopmentalRegionKind,
    RegionalProposal,
    build_stage_three_region_states,
    run_stage_three_regional_concurrency_acceptance,
)


def test_stage_three_acceptance_matrix_is_complete_and_zero_authority() -> None:
    evidence = run_stage_three_regional_concurrency_acceptance()
    results = (
        evidence.compatible_result,
        evidence.protected_inhibition_result,
        evidence.dormant_reemergence_result,
    )

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    for result in results:
        assert result.sqlite_cognition_operation_count == 0
        assert result.external_side_effect_count == 0
        assert result.production_action_authority_violations == 0
        assert not result.permanent_global_scalar_used
        assert all(not region.has_external_action_authority for region in result.region_states)
        assert all(not proposal.has_external_action_authority for proposal in result.proposals)


def test_region_local_pools_are_distinct_and_safety_region_is_protected() -> None:
    regions = build_stage_three_region_states()
    neuron_ids = [neuron_id for region in regions for neuron_id in region.local_neuron_ids]
    safety = next(
        region for region in regions if region.kind is DevelopmentalRegionKind.SAFETY_PERMISSION
    )

    assert len(neuron_ids) == len(set(neuron_ids))
    assert safety.protected_control_plane
    with pytest.raises(ValueError, match="safety and permission"):
        replace(safety, protected_control_plane=False)
    with pytest.raises(ValueError, match="external action authority"):
        replace(regions[0], has_external_action_authority=True)


def test_compatible_needs_remain_simultaneous_and_cooperate_without_erasure() -> None:
    result = run_stage_three_regional_concurrency_acceptance().compatible_result

    assert set(result.represented_need_codes) == {
        "need:clarify_request",
        "need:complete_task",
        "need:conserve_resources",
    }
    assert result.active_proposal_codes == (
        "proposal:ask_clarifying_question",
        "proposal:bounded_task_plan",
        "proposal:reuse_low_cost_path",
    )
    assert {message.kind for message in result.messages} == {
        CrossRegionMessageKind.COMPATIBILITY_SUPPORT,
        CrossRegionMessageKind.RESOURCE_CONSTRAINT,
    }
    assert result.region_local_interference < result.uniform_network_interference


def test_protected_need_inhibits_incompatible_task_without_action_authority() -> None:
    result = run_stage_three_regional_concurrency_acceptance().protected_inhibition_result
    risky = result.proposal_by_code("proposal:direct_destructive_fix")
    safe = result.proposal_by_code("proposal:read_only_diagnosis")

    assert "proposal:direct_destructive_fix" not in result.active_proposal_codes
    assert "need:preserve_user_data" in risky.inhibited_by_need_codes
    assert "authority:human_permission_required" in risky.protected_requirement_codes
    assert safe.activation > risky.activation
    assert {message.kind for message in result.messages}.issuperset(
        {
            CrossRegionMessageKind.CONFLICT_INHIBITION,
            CrossRegionMessageKind.PERMISSION_CONSTRAINT,
            CrossRegionMessageKind.PRESERVATION_CONSTRAINT,
        }
    )


def test_dormant_need_reemerges_after_blocking_need_resolves() -> None:
    result = run_stage_three_regional_concurrency_acceptance().dormant_reemergence_result

    assert result.dormant_need_codes == ("need:curiosity_followup",)
    assert result.reemerged_need_codes == ("need:curiosity_followup",)
    assert "proposal:inspect_after_stop_resolved" in result.active_proposal_codes
    assert CrossRegionMessageKind.STOP_SIGNAL in {message.kind for message in result.messages}


def test_stage_three_rejects_global_scalar_and_worse_region_local_control() -> None:
    evidence = run_stage_three_regional_concurrency_acceptance()

    with pytest.raises(ValueError, match="permanent global scalar"):
        replace(evidence.compatible_result, permanent_global_scalar_used=True)
    with pytest.raises(ValueError, match="pass gates failed"):
        replace(
            evidence,
            compatible_result=replace(
                evidence.compatible_result,
                region_local_interference=evidence.compatible_result.uniform_network_interference,
            ),
        )


def test_cross_region_messages_are_typed_inspectable_and_validated() -> None:
    result = run_stage_three_regional_concurrency_acceptance().compatible_result
    message = result.messages[0]

    assert all(message.message_id for message in result.messages)
    with pytest.raises(ValueError, match="distinct regions"):
        replace(message, target_region_code=message.source_region_code)
    with pytest.raises(ValueError, match="source and target needs"):
        replace(message, provenance_need_codes=(message.source_need_code,))


def test_proposals_and_need_pulses_reject_authority_and_ambiguous_conflicts() -> None:
    with pytest.raises(ValueError, match="typed internal proposals"):
        RegionalProposal(
            "proposal:bad",
            "region:task",
            "need:complete_task",
            0.4,
            typed_internal_only=False,
        )
    with pytest.raises(ValueError, match="external action authority"):
        RegionalProposal(
            "proposal:bad",
            "region:task",
            "need:complete_task",
            0.4,
            has_external_action_authority=True,
        )
    with pytest.raises(ValueError, match="both compatible and conflicting"):
        ConcurrentNeedPulse(
            "need:bad",
            "region:task",
            0.5,
            compatible_need_codes=("need:other",),
            conflicting_need_codes=("need:other",),
        )
    with pytest.raises(ValueError, match="protected needs"):
        ConcurrentNeedPulse("need:bad", "region:safety_permission", 0.5, protected=True)


def test_results_validate_known_regions_needs_sorted_proposals_and_action_counters() -> None:
    evidence = run_stage_three_regional_concurrency_acceptance()
    result = evidence.compatible_result

    with pytest.raises(ValueError, match="known region"):
        replace(
            result,
            need_pulses=(
                replace(result.need_pulses[0], region_code="region:missing"),
                *result.need_pulses[1:],
            ),
        )
    with pytest.raises(ValueError, match="sorted by proposal code"):
        replace(result, proposals=tuple(reversed(result.proposals)))
    with pytest.raises(ValueError, match="production_action_authority_violations"):
        replace(result, production_action_authority_violations=1)
    with pytest.raises(ValueError, match="active proposals"):
        replace(result, active_proposal_codes=("proposal:missing",))


def test_stage_three_acceptance_is_deterministic_and_config_bounded() -> None:
    first = run_stage_three_regional_concurrency_acceptance(DevelopmentalRegionConfig(seed=101))
    second = run_stage_three_regional_concurrency_acceptance(DevelopmentalRegionConfig(seed=101))

    assert first.evidence_id == second.evidence_id
    assert first.snapshot() == second.snapshot()
    assert first.config.maximum_simultaneous_needs == 5
    with pytest.raises(ValueError, match="maximum simultaneous need bound"):
        run_stage_three_regional_concurrency_acceptance(
            DevelopmentalRegionConfig(maximum_simultaneous_needs=2)
        )
    with pytest.raises(ValueError, match="neurons_per_region"):
        DevelopmentalRegionConfig(neurons_per_region=0)
    with pytest.raises(ValueError, match="activation_threshold"):
        DevelopmentalRegionConfig(activation_threshold=1.5)


def test_public_exports_cover_stage_three_regional_concurrency() -> None:
    exported = set(ndnra.__all__)

    assert "ConcurrentNeedActivationResult" in exported
    assert "CrossRegionMessageKind" in exported
    assert "DevelopmentalRegionState" in exported
    assert "RegionalProposal" in exported
    assert "StageThreeRegionalConcurrencyEvidence" in exported
    assert "build_stage_three_region_states" in exported
    assert "run_stage_three_regional_concurrency_acceptance" in exported


def test_developmental_regions_has_no_forbidden_runtime_dependencies() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_regions.py"
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
