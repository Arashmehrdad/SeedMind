"""Tests for exact restart-safe NDNRA execution checkpoint persistence."""

# ruff: noqa: I001 -- pytest exposes the adjacent support module as top-level.

from __future__ import annotations

import copy
import json
from collections.abc import Callable
from pathlib import Path

import pytest

from ndnra_execution_test_support import (
    build_setup,
    execute_loaded,
    list_value,
    object_value,
    read_object,
    rewrite_checksum,
    save_initial,
)

from seedmind.research.ndnra import (
    BRAIN_SCHEMA_VERSION,
    BrainLoadStatus,
    ConsolidationExecutionPermitLifecycleStatus,
    NDNRABrainStore,
    NDNRAConsolidationCheckpoint,
    NDNRAExecutionCheckpoint,
    NDNRAGrowthState,
    NDNRAProposalLifecycleCheckpoint,
)


def test_issued_checkpoint_round_trips_exactly_and_has_no_authority() -> None:
    setup = build_setup()
    encoded = json.dumps(
        setup.execution_checkpoint.snapshot(),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")

    restored = NDNRAExecutionCheckpoint.from_snapshot(json.loads(encoded))

    assert encoded.isascii()
    assert restored == setup.execution_checkpoint
    assert restored.permit_registry.consumption_count == 0
    assert restored.receipts == ()
    assert restored.automatic_execution_count == 0
    assert not restored.has_execution_authority


def test_schema_v5_round_trips_consumed_permit_receipt_and_application(
    tmp_path: Path,
) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / "brain.json")

    durable, state = execute_loaded(store)
    restarted = store.load()

    assert BRAIN_SCHEMA_VERSION == 6
    assert durable.save_result is not None
    assert not durable.save_result.temporary_file_remaining
    assert restarted.status is BrainLoadStatus.LOADED
    assert restarted.execution_checkpoint == durable.execution_checkpoint
    assert restarted.consolidation_checkpoint == durable.consolidation_checkpoint
    assert restarted.consolidation_checkpoint.state == state.snapshot()
    assert len(restarted.execution_checkpoint.receipts) == 1
    record = restarted.execution_checkpoint.permit_registry.records[0]
    assert record.status is ConsolidationExecutionPermitLifecycleStatus.CONSUMED
    assert record.consumption_count == 1
    receipt = restarted.execution_checkpoint.receipts[0]
    assert receipt.application_count == 1
    assert receipt.replay_trigger_count == 0
    assert receipt.restoration_trigger_count == 0
    assert not receipt.has_production_action_authority


def test_schema_v4_migrates_to_empty_execution_without_inference(tmp_path: Path) -> None:
    setup = build_setup()
    path = tmp_path / "brain_v4.json"
    save_initial(setup, path)
    raw = read_object(path)
    payload = object_value(raw, "payload")
    payload.pop("execution_checkpoint")
    raw["schema_version"] = 4
    rewrite_checksum(path, raw)

    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.migrated_from_version == 4
    assert loaded.proposal_lifecycle_checkpoint.registry.records
    assert loaded.execution_checkpoint == NDNRAExecutionCheckpoint.empty()


def _corrupt_transition_identity(raw: dict[str, object]) -> None:
    execution = _execution(raw)
    registry = object_value(execution, "permit_registry")
    record = list_value(registry, "records")[0]
    assert isinstance(record, dict)
    decision = list_value(record, "decisions")[0]
    assert isinstance(decision, dict)
    decision["decision_id"] = "consolidation-permit-transition:tampered"


def _corrupt_receipt_identity(raw: dict[str, object]) -> None:
    receipt = list_value(_execution(raw), "receipts")[0]
    assert isinstance(receipt, dict)
    receipt["execution_id"] = "consolidation-execution:tampered"


def _corrupt_consumption_reference(raw: dict[str, object]) -> None:
    execution = _execution(raw)
    registry = object_value(execution, "permit_registry")
    record = list_value(registry, "records")[0]
    assert isinstance(record, dict)
    decision = list_value(record, "decisions")[0]
    assert isinstance(decision, dict)
    decision["consumption_reference_code"] = "consolidation-execution:wrong"


def _remove_receipt(raw: dict[str, object]) -> None:
    _execution(raw)["receipts"] = []


def _make_receipt_without_consumed_permit(raw: dict[str, object]) -> None:
    execution = _execution(raw)
    registry = object_value(execution, "permit_registry")
    record = list_value(registry, "records")[0]
    assert isinstance(record, dict)
    record["status"] = "issued"
    record["decisions"] = []
    record["is_terminal"] = False
    record["consumption_count"] = 0
    registry["consumption_count"] = 0


def _duplicate_permit(raw: dict[str, object]) -> None:
    execution = _execution(raw)
    registry = object_value(execution, "permit_registry")
    records = list_value(registry, "records")
    records.append(copy.deepcopy(records[0]))
    registry["consumption_count"] = 2


def _duplicate_receipt(raw: dict[str, object]) -> None:
    receipts = list_value(_execution(raw), "receipts")
    receipts.append(copy.deepcopy(receipts[0]))


def _remove_applied_candidate(raw: dict[str, object]) -> None:
    payload = object_value(raw, "payload")
    consolidation = object_value(payload, "consolidation_checkpoint")
    consolidation["active_applications"] = []
    state = object_value(consolidation, "state")
    state["applied_candidate_ids"] = []


def _execution(raw: dict[str, object]) -> dict[str, object]:
    return object_value(object_value(raw, "payload"), "execution_checkpoint")


@pytest.mark.parametrize(
    "mutator",
    [
        _corrupt_transition_identity,
        _corrupt_receipt_identity,
        _corrupt_consumption_reference,
        _remove_receipt,
        _make_receipt_without_consumed_permit,
        _duplicate_permit,
        _duplicate_receipt,
        _remove_applied_candidate,
    ],
)
def test_relational_corruption_causes_complete_fallback(
    tmp_path: Path,
    mutator: Callable[[dict[str, object]], None],
) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / "source.json")
    execute_loaded(store)
    raw = read_object(store.path)
    mutator(raw)
    target = tmp_path / f"corrupt_{mutator.__name__}.json"
    rewrite_checksum(target, raw)

    loaded = NDNRABrainStore(target).load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.used_fallback
    assert not loaded.checksum_verified
    assert loaded.graph.assembly_count == 0
    assert loaded.growth_state == NDNRAGrowthState()
    assert loaded.consolidation_checkpoint == NDNRAConsolidationCheckpoint.empty()
    assert loaded.proposal_lifecycle_checkpoint == NDNRAProposalLifecycleCheckpoint.empty()
    assert loaded.execution_checkpoint == NDNRAExecutionCheckpoint.empty()


def test_outer_checksum_corruption_causes_complete_fallback(tmp_path: Path) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / "checksum.json")
    raw = read_object(store.path)
    raw["checksum"] = "0" * 64
    store.path.write_text(
        json.dumps(raw, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )

    loaded = store.load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.graph.assembly_count == 0
    assert loaded.execution_checkpoint == NDNRAExecutionCheckpoint.empty()


def test_execution_checkpoint_rejects_authority_and_automatic_execution() -> None:
    with pytest.raises(ValueError, match="automatic executions"):
        NDNRAExecutionCheckpoint(automatic_execution_count=1)
    with pytest.raises(ValueError, match="never have execution authority"):
        NDNRAExecutionCheckpoint(has_execution_authority=True)


def test_execution_persistence_has_no_sqlite_replay_or_action_authority_path() -> None:
    source = "\n".join(
        path.read_text(encoding="utf-8").lower()
        for path in (
            Path("src/seedmind/research/ndnra/consolidation_execution_persistence.py"),
            Path("src/seedmind/research/ndnra/consolidation_execution_durable_commit.py"),
        )
    )

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "replay(" not in source
    assert "select_action" not in source
    assert "route_rank" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "seedmind.integration" not in source
