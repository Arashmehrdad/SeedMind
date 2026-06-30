"""Tests for NDNRA v0.2 Stage 6 hibernation and restart evidence."""

from __future__ import annotations

import ast
import json
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    CoalitionDormancyState,
    DreamReplayRecord,
    HibernatingCoalitionState,
    StageSixHibernationConfig,
    StageSixLoadStatus,
    load_stage_six_hibernation_evidence,
    prove_stage_six_restart,
    run_stage_six_hibernation_acceptance,
    save_stage_six_hibernation_evidence,
)


def test_stage_six_acceptance_matrix_is_complete_and_zero_authority() -> None:
    evidence = run_stage_six_hibernation_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.sqlite_cognition_operation_count == 0
    assert evidence.external_side_effect_count == 0
    assert evidence.production_action_authority_violations == 0
    assert evidence.dream_replay.action_execution_count == 0
    assert all(not coalition.has_external_action_authority for coalition in evidence.coalitions)


def test_dormant_coalitions_preserve_structure_topology_and_provenance() -> None:
    evidence = run_stage_six_hibernation_acceptance()
    dormant = [
        coalition
        for coalition in evidence.coalitions
        if coalition.dormancy_state
        in {CoalitionDormancyState.DORMANT, CoalitionDormancyState.HIBERNATING}
    ]

    assert dormant
    for coalition in dormant:
        assert coalition.neuron_ids
        assert coalition.topology_edge_codes
        assert set(coalition.weight_by_edge) == set(coalition.topology_edge_codes)
        assert set(coalition.inhibition_by_edge) == set(coalition.topology_edge_codes)
        assert coalition.provenance_experience_ids


def test_recall_can_fail_shallow_but_restore_with_need_relation_or_dream() -> None:
    recall = run_stage_six_hibernation_acceptance().recall_evidence

    assert recall.shallow_recall_access < 0.5
    assert recall.stronger_need_access > recall.shallow_recall_access
    assert recall.related_activation_access > recall.shallow_recall_access
    assert recall.dream_maintained_access > recall.unreplayed_control_access
    assert recall.long_inactivity_retrieval_access >= 0.65
    with pytest.raises(ValueError, match="shallow dormant recall"):
        replace(recall, shallow_recall_access=0.7)


def test_dream_replay_improves_access_without_evidence_or_actions() -> None:
    replay = run_stage_six_hibernation_acceptance().dream_replay

    assert replay.accessibility_delta > replay.matched_control_delta
    assert replay.factual_evidence_delta == 0
    assert replay.action_execution_count == 0
    assert not replay.weakens_protected_prohibition
    assert not replay.autonomous_worker_used
    with pytest.raises(ValueError, match="factual_evidence_delta"):
        replace(replay, factual_evidence_delta=1)
    with pytest.raises(ValueError, match="autonomous"):
        replace(replay, autonomous_worker_used=True)


def test_rare_important_protected_coalition_remains_retrievable_and_protected() -> None:
    evidence = run_stage_six_hibernation_acceptance()
    protected = next(coalition for coalition in evidence.coalitions if coalition.protected)

    assert protected.importance >= 0.8
    assert protected.maturity_state_code == "maturity:mature"
    assert protected.dormancy_state is CoalitionDormancyState.HIBERNATING
    assert evidence.recall_evidence.long_inactivity_retrieval_access >= 0.65


def test_stage_six_save_load_restores_exact_snapshot(tmp_path: Path) -> None:
    path = tmp_path / "stage6.json"
    evidence = run_stage_six_hibernation_acceptance()

    save_stage_six_hibernation_evidence(evidence, path)
    loaded = load_stage_six_hibernation_evidence(path)

    assert loaded.status is StageSixLoadStatus.RESTORED
    assert loaded.restored_evidence is not None
    assert loaded.restored_evidence.evidence_id == evidence.evidence_id
    assert loaded.restored_evidence.snapshot() == evidence.snapshot()


def test_stage_six_corrupt_checksum_and_schema_fall_back_completely(tmp_path: Path) -> None:
    path = tmp_path / "stage6.json"
    evidence = run_stage_six_hibernation_acceptance()
    save_stage_six_hibernation_evidence(evidence, path)
    envelope = json.loads(path.read_text(encoding="ascii"))

    corrupt = tmp_path / "corrupt.json"
    envelope["payload"]["config"]["seed"] = 999
    corrupt.write_text(json.dumps(envelope), encoding="ascii")
    incompatible = tmp_path / "schema.json"
    envelope["checksum"] = "changed"
    envelope["schema_version"] = 999
    incompatible.write_text(json.dumps(envelope), encoding="ascii")
    malformed = tmp_path / "malformed.json"
    malformed.write_text("{", encoding="ascii")

    assert load_stage_six_hibernation_evidence(corrupt).status is StageSixLoadStatus.FALLBACK
    assert load_stage_six_hibernation_evidence(incompatible).status is StageSixLoadStatus.FALLBACK
    assert load_stage_six_hibernation_evidence(malformed).status is StageSixLoadStatus.FALLBACK


def test_stage_six_restart_proof_covers_equivalence_and_fallback(tmp_path: Path) -> None:
    proof = prove_stage_six_restart(tmp_path / "stage6.json")

    assert proof.saved_evidence_id == proof.restored_evidence_id
    assert proof.first_post_restart_recall_matches
    assert proof.protected_network_remains_protected
    assert proof.malformed_load_status is StageSixLoadStatus.FALLBACK
    assert proof.incompatible_schema_load_status is StageSixLoadStatus.FALLBACK


def test_hibernating_coalition_rejects_missing_structure_and_authority() -> None:
    coalition = run_stage_six_hibernation_acceptance().coalitions[0]

    with pytest.raises(ValueError, match="preserve structure"):
        replace(coalition, neuron_ids=())
    with pytest.raises(ValueError, match="weights"):
        replace(coalition, weight_by_edge={})
    with pytest.raises(ValueError, match="external action authority"):
        replace(coalition, has_external_action_authority=True)
    assert isinstance(coalition, HibernatingCoalitionState)


def test_stage_six_config_bounds_and_determinism() -> None:
    first = run_stage_six_hibernation_acceptance(StageSixHibernationConfig(seed=404))
    second = run_stage_six_hibernation_acceptance(StageSixHibernationConfig(seed=404))

    assert first.evidence_id == second.evidence_id
    assert first.snapshot() == second.snapshot()
    with pytest.raises(ValueError, match="maximum_dream_replay_sources"):
        StageSixHibernationConfig(maximum_dream_replay_sources=0)
    with pytest.raises(ValueError, match="dream replay exceeds"):
        run_stage_six_hibernation_acceptance(
            StageSixHibernationConfig(maximum_dream_replay_sources=1)
        )


def test_public_exports_cover_stage_six_hibernation() -> None:
    exported = set(ndnra.__all__)

    assert "CoalitionDormancyState" in exported
    assert "DreamReplayRecord" in exported
    assert "HibernatingCoalitionState" in exported
    assert "StageSixHibernationEvidence" in exported
    assert "StageSixRestartProof" in exported
    assert "load_stage_six_hibernation_evidence" in exported
    assert "prove_stage_six_restart" in exported
    assert "run_stage_six_hibernation_acceptance" in exported
    assert DreamReplayRecord.__name__ in exported


def test_developmental_hibernation_has_no_forbidden_runtime_dependencies() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_hibernation.py"
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
