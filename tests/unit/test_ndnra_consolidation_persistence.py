"""Tests for schema-v3 NDNRA consolidation checkpoint persistence."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from seedmind.research.ndnra import (
    BRAIN_SCHEMA,
    BRAIN_SCHEMA_VERSION,
    BrainLoadStatus,
    ConsolidationApplicationResult,
    ConsolidationApplicationState,
    ConsolidationEligibilityPolicy,
    ConsolidationReopeningPolicy,
    ConsolidationRollbackAuditRecord,
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
    NDNRABrainStore,
    NDNRAConsolidationCheckpoint,
    build_capacity_limited_graph,
    rollback_consolidation,
)

_LESSON = LessonIdentity("reduce_heat", "cooling", 1.0)
_ASSEMBLIES = ("assembly:a", "assembly:b")
_ROUTES = ("route:a", "route:b")


def _trace(index: int, *, route_id: str, effect_value: float = 1.0) -> ContextualExperienceTrace:
    return ContextualExperienceTrace(
        identity=EventIdentity("persistence_test", f"episode:{index}", index),
        correlation_group_id=f"group:{index}",
        assembly_id="assembly:a" if route_id == "route:a" else "assembly:b",
        route_id=route_id,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code="reduce_heat",
            sensor_values=(float(index),),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(EffectObservation("cooling", effect_value, 1.0),),
        transfer_attempted=effect_value > 0.0,
        transfer_succeeded=effect_value > 0.0 and index < 2,
    )


def _ledger() -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    for trace in (
        _trace(0, route_id="route:a"),
        _trace(1, route_id="route:b"),
        _trace(2, route_id="route:a"),
    ):
        ledger.record(trace)
    return ledger


def _application(
    ledger: ContextualExperienceLedger,
) -> tuple[ConsolidationApplicationState, ConsolidationApplicationResult]:
    eligibility = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=ledger.mastery_profile(_LESSON),
        available_assembly_ids=_ASSEMBLIES,
        available_route_ids=_ROUTES,
    )
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=_ASSEMBLIES,
        route_ids=_ROUTES,
        initial_stability=0.20,
        initial_plasticity=0.80,
    )
    return state, state.apply(eligibility)


def _active_checkpoint(
    ledger: ContextualExperienceLedger,
) -> tuple[NDNRAConsolidationCheckpoint, ConsolidationApplicationResult]:
    state, application = _application(ledger)
    return (
        NDNRAConsolidationCheckpoint(
            state=state.snapshot(),
            active_applications=(application,),
        ),
        application,
    )


def _rewrite_version(path: Path, version: int, *, drop_checkpoint: bool) -> None:
    raw: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(raw, dict)
    payload = raw["payload"]
    assert isinstance(payload, dict)
    if drop_checkpoint:
        payload.pop("consolidation_checkpoint", None)
    body: dict[str, object] = {
        "schema": BRAIN_SCHEMA,
        "schema_version": version,
        "payload": payload,
    }
    raw["schema_version"] = version
    raw["checksum"] = hashlib.sha256(
        json.dumps(
            body,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()
    path.write_text(
        json.dumps(raw, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )


def _rewrite_checksum(path: Path) -> None:
    raw: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(raw, dict)
    body: dict[str, object] = {
        "schema": raw["schema"],
        "schema_version": raw["schema_version"],
        "payload": raw["payload"],
    }
    raw["checksum"] = hashlib.sha256(
        json.dumps(
            body,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()
    path.write_text(
        json.dumps(raw, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )


def test_schema_v4_round_trips_active_consolidation_checkpoint(tmp_path: Path) -> None:
    ledger = _ledger()
    checkpoint, application = _active_checkpoint(ledger)
    graph = build_capacity_limited_graph()
    store = NDNRABrainStore(tmp_path / "brain.json")

    saved = store.save(graph, consolidation_checkpoint=checkpoint)
    loaded = store.load()

    assert BRAIN_SCHEMA_VERSION == 7
    assert saved.schema_version == 7
    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.checksum_verified
    assert loaded.consolidation_checkpoint == checkpoint
    assert loaded.consolidation_checkpoint.active_applications == (application,)
    restored_state = loaded.consolidation_checkpoint.application_state()
    assert restored_state is not None
    assert restored_state.snapshot() == checkpoint.state


def test_loaded_active_application_can_be_reopened_and_rolled_back(tmp_path: Path) -> None:
    ledger = _ledger()
    checkpoint, _ = _active_checkpoint(ledger)
    path = tmp_path / "brain.json"
    NDNRABrainStore(path).save(
        build_capacity_limited_graph(),
        consolidation_checkpoint=checkpoint,
    )
    loaded = NDNRABrainStore(path).load()
    state = loaded.consolidation_checkpoint.application_state()
    assert state is not None
    application = loaded.consolidation_checkpoint.active_applications[0]
    ledger.record(_trace(3, route_id="route:b", effect_value=-1.0))
    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=application.candidate,
    )

    result = rollback_consolidation(
        state=state,
        application=application,
        decision=decision,
    )

    assert result.after == state.snapshot()
    assert application.candidate.candidate_id not in result.after.applied_candidate_ids


def test_schema_v3_round_trips_compact_rollback_audit(tmp_path: Path) -> None:
    ledger = _ledger()
    state, application = _application(ledger)
    ledger.record(_trace(3, route_id="route:b", effect_value=-1.0))
    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=application.candidate,
    )
    rollback = rollback_consolidation(
        state=state,
        application=application,
        decision=decision,
    )
    record = ConsolidationRollbackAuditRecord.from_result(rollback)
    checkpoint = NDNRAConsolidationCheckpoint(
        state=state.snapshot(),
        rollback_records=(record,),
    )
    path = tmp_path / "brain.json"

    NDNRABrainStore(path).save(
        build_capacity_limited_graph(),
        consolidation_checkpoint=checkpoint,
    )
    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.consolidation_checkpoint == checkpoint
    assert loaded.consolidation_checkpoint.rollback_records == (record,)
    assert loaded.consolidation_checkpoint.active_applications == ()


def test_schema_v2_migrates_to_explicit_empty_consolidation_checkpoint(
    tmp_path: Path,
) -> None:
    path = tmp_path / "brain_v2.json"
    NDNRABrainStore(path).save(build_capacity_limited_graph())
    _rewrite_version(path, 2, drop_checkpoint=True)

    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.migrated_from_version == 2
    assert loaded.consolidation_checkpoint == NDNRAConsolidationCheckpoint.empty()
    assert loaded.consolidation_checkpoint.application_state() is None


def test_default_schema_v3_save_uses_empty_checkpoint(tmp_path: Path) -> None:
    path = tmp_path / "brain.json"

    NDNRABrainStore(path).save(build_capacity_limited_graph())
    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.consolidation_checkpoint == NDNRAConsolidationCheckpoint.empty()


def test_inconsistent_checkpoint_falls_back_without_partial_state(tmp_path: Path) -> None:
    ledger = _ledger()
    checkpoint, _ = _active_checkpoint(ledger)
    path = tmp_path / "brain.json"
    NDNRABrainStore(path).save(
        build_capacity_limited_graph(),
        consolidation_checkpoint=checkpoint,
    )
    raw: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(raw, dict)
    payload = raw["payload"]
    assert isinstance(payload, dict)
    consolidation = payload["consolidation_checkpoint"]
    assert isinstance(consolidation, dict)
    consolidation["active_applications"] = []
    path.write_text(
        json.dumps(raw, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    _rewrite_checksum(path)

    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.used_fallback
    assert loaded.graph.assembly_count == 0
    assert loaded.consolidation_checkpoint == NDNRAConsolidationCheckpoint.empty()


def test_schema_v3_checkpoint_encoding_is_deterministic(tmp_path: Path) -> None:
    checkpoint, _ = _active_checkpoint(_ledger())
    graph = build_capacity_limited_graph()
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    NDNRABrainStore(first).save(graph, consolidation_checkpoint=checkpoint)
    NDNRABrainStore(second).save(graph, consolidation_checkpoint=checkpoint)

    assert first.read_bytes() == second.read_bytes()


def test_consolidation_persistence_has_no_sqlite_cognitive_dependency() -> None:
    files = (
        Path("src/seedmind/research/ndnra/consolidation_persistence.py"),
        Path("src/seedmind/research/ndnra/persistence.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
