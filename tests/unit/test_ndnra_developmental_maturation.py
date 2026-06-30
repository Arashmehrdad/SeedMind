"""Tests for NDNRA v0.2 Stage 4 maturation, skill, and ambition evidence."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    AmbitionPressureState,
    DevelopmentalRegionKind,
    MaturationComparisonStrategy,
    RegionalMaturityProfile,
    RegionalMaturityState,
    StageFourMaturationConfig,
    run_stage_four_maturation_acceptance,
)


def test_stage_four_acceptance_matrix_is_complete_and_zero_authority() -> None:
    evidence = run_stage_four_maturation_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.relearning_evidence.sqlite_cognition_operation_count == 0
    assert evidence.relearning_evidence.external_side_effect_count == 0
    assert evidence.relearning_evidence.production_action_authority_violations == 0
    assert not evidence.child_region.has_external_action_authority
    assert not evidence.mature_region.has_external_action_authority
    assert not evidence.skill_evidence.mature_bundle.has_production_action_authority
    assert not evidence.ambition_evidence.ambition.has_production_action_authority


def test_child_and_mature_regions_use_distinct_local_maturity_controls() -> None:
    evidence = run_stage_four_maturation_acceptance()

    assert evidence.child_region.maturity_state is RegionalMaturityState.CHILD
    assert evidence.mature_region.maturity_state is RegionalMaturityState.MATURE
    assert evidence.child_region.plasticity > evidence.mature_region.plasticity
    assert evidence.mature_region.permanence_threshold > evidence.child_region.permanence_threshold
    with pytest.raises(ValueError, match="child regions require high plasticity"):
        replace(evidence.child_region, plasticity=0.2)
    with pytest.raises(ValueError, match="one global maturity switch"):
        replace(evidence.mature_region, uses_global_maturity_switch=True)


def test_maturation_controls_show_regional_control_beats_required_baselines() -> None:
    evidence = run_stage_four_maturation_acceptance()
    by_strategy = {result.strategy: result for result in evidence.comparison_results}
    high = by_strategy[MaturationComparisonStrategy.PERMANENT_HIGH_PLASTICITY]
    low = by_strategy[MaturationComparisonStrategy.PERMANENT_LOW_PLASTICITY]
    global_control = by_strategy[MaturationComparisonStrategy.GLOBAL_MATURITY_STATE]
    proposed = by_strategy[MaturationComparisonStrategy.REGIONAL_DEVELOPMENTAL_CONTROL]

    assert high.new_association_steps < low.new_association_steps
    assert proposed.mature_retention_after_conflict > high.mature_retention_after_conflict
    assert proposed.cross_task_interference < high.cross_task_interference
    assert proposed.useful_adaptation_score > low.useful_adaptation_score
    assert global_control.uses_global_maturity_switch
    assert not proposed.uses_global_maturity_switch


def test_promotion_requires_varied_context_retention_low_interference_and_low_correction() -> None:
    evidence = run_stage_four_maturation_acceptance()
    skill = evidence.skill_evidence

    assert len(skill.varied_context_codes) >= evidence.config.promotion_minimum_contexts
    assert skill.retention_score >= evidence.config.mature_retention_threshold
    assert skill.interference_score <= 0.2
    assert skill.teacher_correction_rate <= 0.15
    with pytest.raises(ValueError, match="varied-context success"):
        replace(skill, varied_context_codes=("context:python",))
    with pytest.raises(ValueError, match="old skills"):
        replace(skill, old_skill_validation_passed=False)


def test_relearning_zone_is_bounded_and_rollback_restores_exact_state() -> None:
    evidence = run_stage_four_maturation_acceptance()
    relearning = evidence.relearning_evidence

    assert len(relearning.relearning_region.relearning_zone_codes) <= (
        evidence.config.maximum_relearning_zone_size
    )
    assert (
        relearning.mature_region_before.protected_core_connection_codes
        == relearning.relearning_region.protected_core_connection_codes
    )
    assert relearning.pre_consolidation_checksum == relearning.post_rollback_checksum
    with pytest.raises(ValueError, match="protected core"):
        replace(
            relearning,
            relearning_region=replace(
                relearning.relearning_region,
                protected_core_connection_codes=("core:task_read_only",),
            ),
        )
    with pytest.raises(ValueError, match="restore the pre-consolidation"):
        replace(relearning, post_rollback_checksum="checksum:changed")


def test_value_sources_and_capability_gaps_are_complete_and_separate() -> None:
    evidence = run_stage_four_maturation_acceptance().ambition_evidence

    assert {source.kind for source in evidence.accepted_value_sources} == set(ndnra.ValueSourceKind)
    assert {gap.source for gap in evidence.capability_gaps} == set(ndnra.CapabilityGapSource)
    assert all(
        gap.obstacle_code != evidence.ambition.value_source.source_code
        for gap in evidence.capability_gaps
    )
    assert evidence.progress_measurements == (0.18, 0.42, 0.67)
    assert evidence.feasible_nursery_opportunity_codes


def test_ambition_pressure_reduces_after_pause_satisfaction_and_retirement() -> None:
    ambition = run_stage_four_maturation_acceptance().ambition_evidence
    pressures = ambition.pressure_by_state

    assert pressures[AmbitionPressureState.PAUSED] < pressures[AmbitionPressureState.ACCEPTED]
    assert pressures[AmbitionPressureState.SATISFIED] < pressures[AmbitionPressureState.ACCEPTED]
    assert pressures[AmbitionPressureState.RETIRED] <= pressures[AmbitionPressureState.SATISFIED]
    assert not ambition.curiosity_owns_commitment
    with pytest.raises(ValueError, match="curiosity"):
        replace(ambition, curiosity_owns_commitment=True)
    with pytest.raises(ValueError, match="measurable progress"):
        replace(ambition, progress_measurements=(0.2, 0.2))


def test_skill_verifier_beats_producer_and_reopens_after_drift() -> None:
    evidence = run_stage_four_maturation_acceptance()
    skill = evidence.skill_evidence

    assert skill.verifier_accuracy > skill.producer_self_judgement_accuracy
    assert skill.verifier_scope_codes == ("scope:changed_files", "scope:declared_tests")
    assert skill.reopened_verifier_zone_codes == ("verifier-zone:context-drift",)
    assert skill.context_drift_rate >= evidence.config.verifier_reopen_drift_threshold
    with pytest.raises(ValueError, match="producer self-judgement"):
        replace(skill, verifier_accuracy=skill.producer_self_judgement_accuracy)
    with pytest.raises(ValueError, match="bounded verifier zone"):
        replace(skill, reopened_verifier_zone_codes=())


def test_stage_four_config_bounds_are_enforced() -> None:
    evidence = run_stage_four_maturation_acceptance()

    with pytest.raises(ValueError, match="maximum_relearning_zone_size"):
        StageFourMaturationConfig(maximum_relearning_zone_size=0)
    with pytest.raises(ValueError, match="mature_retention_threshold"):
        StageFourMaturationConfig(mature_retention_threshold=1.2)
    with pytest.raises(ValueError, match="relearning zone exceeds configured bound"):
        replace(
            evidence,
            config=StageFourMaturationConfig(maximum_relearning_zone_size=0 + 1),
            relearning_evidence=replace(
                evidence.relearning_evidence,
                relearning_region=RegionalMaturityProfile(
                    "region:task",
                    DevelopmentalRegionKind.TASK,
                    RegionalMaturityState.RELEARNING,
                    plasticity=0.44,
                    exploration=0.38,
                    teacher_influence=0.46,
                    permanence_threshold=0.82,
                    inhibition_strength=0.7,
                    protected_core_connection_codes=(
                        "core:task_read_only",
                        "core:task_request_permission",
                    ),
                    relearning_zone_codes=("zone:a", "zone:b"),
                ),
            ),
        )


def test_stage_four_acceptance_is_deterministic() -> None:
    first = run_stage_four_maturation_acceptance(StageFourMaturationConfig(seed=202))
    second = run_stage_four_maturation_acceptance(StageFourMaturationConfig(seed=202))

    assert first.evidence_id == second.evidence_id
    assert first.snapshot() == second.snapshot()


def test_public_exports_cover_stage_four_maturation() -> None:
    exported = set(ndnra.__all__)

    assert "AmbitionPressureState" in exported
    assert "MaturationComparisonStrategy" in exported
    assert "PersistentAmbitionEvidence" in exported
    assert "RegionalMaturityProfile" in exported
    assert "RegionalMaturityState" in exported
    assert "SkillMaturationEvidence" in exported
    assert "StageFourMaturationEvidence" in exported
    assert "run_stage_four_maturation_acceptance" in exported


def test_developmental_maturation_has_no_forbidden_runtime_dependencies() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_maturation.py"
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
