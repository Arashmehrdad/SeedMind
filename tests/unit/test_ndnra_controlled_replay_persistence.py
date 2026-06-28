"""Tests for schema-6 durable controlled replay persistence."""

# ruff: noqa: I001 -- pytest exposes the adjacent support module as top-level.

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from ndnra_controlled_replay_test_support import build_replay_scenario

from seedmind.research.ndnra.activity_maintenance import ActivityMaintenanceLedger
from seedmind.research.ndnra.controlled_replay_restoration_persistence import (
    NDNRAReplayRestorationCheckpoint,
)
from seedmind.research.ndnra.persistence import (
    BRAIN_SCHEMA_VERSION,
    BrainLoadStatus,
)


def _canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def test_schema_6_round_trips_issued_permit_and_activity_history(tmp_path: Path) -> None:
    scenario = build_replay_scenario(tmp_path)
    loaded = scenario.store.load()

    assert BRAIN_SCHEMA_VERSION == 6
    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.checksum_verified
    assert not loaded.used_fallback
    assert loaded.schema_version == 6
    assert loaded.migrated_from_version is None
    assert loaded.replay_restoration_checkpoint == scenario.issued_checkpoint
    assert loaded.replay_restoration_checkpoint.activity_ledger.real_activity_count == 1
    assert loaded.replay_restoration_checkpoint.activity_ledger.replay_activity_count == 0
    assert loaded.checksum == scenario.issued_save.checksum
    assert loaded.state_checksum == scenario.issued_save.state_checksum


def test_audit_only_permit_save_does_not_change_active_state_checksum(
    tmp_path: Path,
) -> None:
    scenario = build_replay_scenario(tmp_path)

    assert scenario.initial_save.checksum != scenario.issued_save.checksum
    assert scenario.initial_save.state_checksum == scenario.issued_save.state_checksum
    assert scenario.permit.target.expected_current_checkpoint_checksum == (
        scenario.issued_save.state_checksum
    )


def test_activity_ledger_and_replay_checkpoint_reconstruct_exactly(
    tmp_path: Path,
) -> None:
    scenario = build_replay_scenario(tmp_path)
    ledger_snapshot = scenario.issued_checkpoint.activity_ledger.snapshot()
    checkpoint_snapshot = scenario.issued_checkpoint.snapshot()

    restored_ledger = ActivityMaintenanceLedger.from_snapshot(ledger_snapshot)
    restored_checkpoint = NDNRAReplayRestorationCheckpoint.from_snapshot(checkpoint_snapshot)

    assert restored_ledger == scenario.issued_checkpoint.activity_ledger
    assert restored_ledger.snapshot() == ledger_snapshot
    assert restored_checkpoint == scenario.issued_checkpoint
    assert restored_checkpoint.snapshot() == checkpoint_snapshot
    assert restored_checkpoint.automatic_replay_count == 0
    assert restored_checkpoint.automatic_restoration_count == 0
    assert not restored_checkpoint.has_replay_authority
    assert not restored_checkpoint.has_restoration_authority
    assert not restored_checkpoint.has_cognitive_authority
    assert not restored_checkpoint.has_production_action_authority


def test_active_state_checksum_detects_tampering_even_with_valid_outer_checksum(
    tmp_path: Path,
) -> None:
    scenario = build_replay_scenario(tmp_path)
    raw = json.loads(scenario.store.path.read_text(encoding="ascii"))
    raw["state_checksum"] = "c" * 64
    body = {
        "schema": raw["schema"],
        "schema_version": raw["schema_version"],
        "state_checksum": raw["state_checksum"],
        "payload": raw["payload"],
    }
    raw["checksum"] = _canonical_checksum(body)
    scenario.store.path.write_text(
        json.dumps(raw, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )

    loaded = scenario.store.load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.used_fallback
    assert not loaded.checksum_verified
    assert loaded.state_checksum is None
    assert loaded.error is not None
    assert "active-state checksum" in loaded.error


def test_schema_5_migrates_to_empty_replay_checkpoint(tmp_path: Path) -> None:
    scenario = build_replay_scenario(tmp_path)
    raw = json.loads(scenario.store.path.read_text(encoding="ascii"))
    payload = dict(raw["payload"])
    payload.pop("replay_restoration_checkpoint")
    body = {
        "schema": raw["schema"],
        "schema_version": 5,
        "payload": payload,
    }
    legacy = {**body, "checksum": _canonical_checksum(body)}
    scenario.store.path.write_text(
        json.dumps(legacy, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )

    loaded = scenario.store.load()

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.checksum_verified
    assert not loaded.used_fallback
    assert loaded.schema_version == 5
    assert loaded.state_checksum is None
    assert loaded.migrated_from_version == 5
    assert loaded.replay_restoration_checkpoint == (NDNRAReplayRestorationCheckpoint.empty())
