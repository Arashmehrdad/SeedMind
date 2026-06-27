"""Tests for versioned non-SQL NDNRA brain-state persistence."""

from __future__ import annotations

import json
from pathlib import Path

from seedmind.integration import run_persistent_shadow_experiment
from seedmind.research.ndnra import (
    BRAIN_SCHEMA_VERSION,
    BrainLoadStatus,
    EffectObservation,
    NDNRABrainStore,
    NDNRAGrowthState,
    build_capacity_limited_graph,
)


def test_brain_store_round_trips_graph_specialist_and_adaptive_state(
    tmp_path: Path,
) -> None:
    graph = build_capacity_limited_graph()
    graph.grow_specialist_interaction(
        specialist_id="specialist:persisted_interaction",
        member_assembly_ids=(
            "assembly:apply_wet_cloth",
            "assembly:activate_fan",
        ),
        origin_code="persistence_test",
        observed_effects=(EffectObservation("temperature", -0.55, 0.90),),
    )
    adaptive_state = NDNRAGrowthState(
        pressure=0.80,
        eligibility=(
            ("assembly:apply_wet_cloth", 0.90),
            ("assembly:activate_fan", 0.85),
        ),
        residuals=(-0.55, -0.50),
        attempt_count=2,
        last_active_members=(
            "assembly:apply_wet_cloth",
            "assembly:activate_fan",
        ),
        dormancy_levels=(
            ("assembly:inspect_wall", 0.75),
            ("specialist:persisted_interaction", 0.10),
        ),
    )
    store = NDNRABrainStore(tmp_path / "brain.json")

    saved = store.save(graph, growth_state=adaptive_state)
    loaded = store.load()

    assert saved.schema_version == BRAIN_SCHEMA_VERSION
    assert saved.byte_count > 0
    assert not saved.temporary_file_remaining
    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.checksum_verified
    assert not loaded.used_fallback
    assert loaded.graph.snapshot() == graph.snapshot()
    assert loaded.growth_state == adaptive_state
    assert loaded.graph.specialist_count == 1
    assert loaded.graph.link_count == graph.link_count


def test_missing_corrupt_and_incompatible_states_fall_back_fresh(
    tmp_path: Path,
) -> None:
    missing_store = NDNRABrainStore(tmp_path / "missing.json")
    missing = missing_store.load()
    assert missing.status is BrainLoadStatus.MISSING_FALLBACK
    assert missing.used_fallback
    assert missing.graph.assembly_count == 0

    corrupt_path = tmp_path / "corrupt.json"
    corrupt_path.write_text("broken\n", encoding="ascii")
    corrupt = NDNRABrainStore(corrupt_path).load()
    assert corrupt.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert corrupt.used_fallback
    assert corrupt.graph.assembly_count == 0

    graph = build_capacity_limited_graph()
    compatible_path = tmp_path / "compatible.json"
    NDNRABrainStore(compatible_path).save(graph)
    payload: object = json.loads(compatible_path.read_text(encoding="ascii"))
    assert isinstance(payload, dict)
    payload["schema_version"] = BRAIN_SCHEMA_VERSION + 1
    incompatible_path = tmp_path / "incompatible.json"
    incompatible_path.write_text(
        json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )
    incompatible = NDNRABrainStore(incompatible_path).load()
    assert incompatible.status is BrainLoadStatus.INCOMPATIBLE_FALLBACK
    assert incompatible.used_fallback
    assert incompatible.graph.assembly_count == 0


def test_checksum_tampering_falls_back_without_partial_graph(tmp_path: Path) -> None:
    graph = build_capacity_limited_graph()
    path = tmp_path / "brain.json"
    NDNRABrainStore(path).save(graph)
    payload: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(payload, dict)
    payload["checksum"] = "0" * 64
    path.write_text(
        json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n",
        encoding="ascii",
    )

    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.used_fallback
    assert not loaded.checksum_verified
    assert loaded.graph.assembly_count == 0
    assert loaded.graph.specialist_count == 0


def test_cross_session_shadow_uses_prior_local_memory_at_step_zero(
    tmp_path: Path,
) -> None:
    evidence = run_persistent_shadow_experiment(tmp_path, play_budget=4)
    result = evidence.result

    assert result.load_status == BrainLoadStatus.LOADED.value
    assert result.graph_round_trip_exact
    assert result.growth_state_round_trip_exact
    assert result.loaded_step_zero_suggestion_available
    assert result.loaded_step_zero_suggestion_valid
    assert not result.fresh_step_zero_suggestion_available
    assert result.second_session_action_sequence_unchanged
    assert result.second_session_prediction_errors_unchanged
    assert result.cross_session_evidence_advantage
    assert result.loaded_evidence_count_after > result.fresh_evidence_count_after
    assert not result.sqlite_used_for_persistence_or_recall
    assert result.pass_gate


def test_persistence_path_has_no_sqlite_cognitive_dependency() -> None:
    files = (
        Path("src/seedmind/research/ndnra/persistence.py"),
        Path("src/seedmind/integration/persistent_shadow_experiment.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
