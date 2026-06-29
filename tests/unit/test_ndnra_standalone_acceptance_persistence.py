"""Tests for standalone acceptance persistence and restart proof."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import fields, replace
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    BRAIN_SCHEMA_VERSION,
    STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA,
    STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION,
    StandaloneAcceptanceAuthority,
    StandaloneAcceptanceLoadResult,
    StandaloneAcceptanceLoadStatus,
    StandaloneAcceptanceRestartProofResult,
    load_standalone_acceptance_result,
    prove_standalone_acceptance_restart,
    run_standalone_acceptance,
    save_standalone_acceptance_result,
    validate_standalone_acceptance_restart_proof_result,
)


def test_store_round_trips_exact_result_and_writes_deterministic_ascii(
    tmp_path: Path,
) -> None:
    result = run_standalone_acceptance()
    first_path = tmp_path / "nested" / "first.json"
    second_path = tmp_path / "nested" / "second.json"

    first_save = save_standalone_acceptance_result(first_path, result)
    second_save = save_standalone_acceptance_result(second_path, result)
    loaded = load_standalone_acceptance_result(first_path)

    assert first_save.schema == STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA
    assert first_save.schema_version == STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION
    assert first_save.payload_checksum_sha256 == second_save.payload_checksum_sha256
    assert first_save.result_identity == result.result_identity
    assert first_save.bytes_written == second_save.bytes_written
    assert not first_save.temporary_file_remaining
    assert not second_save.temporary_file_remaining
    assert not first_path.with_name(f"{first_path.name}.tmp").exists()
    assert first_path.read_bytes() == second_path.read_bytes()
    assert first_path.read_bytes().decode("ascii")
    assert loaded.status is StandaloneAcceptanceLoadStatus.LOADED
    assert loaded.result == result
    assert loaded.payload_checksum_sha256 == first_save.payload_checksum_sha256
    assert loaded.result_identity == result.result_identity
    assert loaded.checksum_verified
    assert not loaded.used_fallback
    assert loaded.acceptance_proof_available
    assert not loaded.has_authority


def test_restart_proof_includes_exact_reload_and_deterministic_rerun(
    tmp_path: Path,
) -> None:
    result = run_standalone_acceptance()

    proof = prove_standalone_acceptance_restart(tmp_path / "restart.json", result)

    assert proof.source_result == result
    assert proof.restored_result == result
    assert proof.rerun_result == result
    assert proof.load_status is StandaloneAcceptanceLoadStatus.LOADED
    assert proof.checksum_verified
    assert proof.exact_round_trip
    assert proof.rerun_equivalent
    assert not proof.bounded_imagination_persisted
    assert not proof.main_brain_schema_changed
    assert not any(getattr(proof.authority, item.name) for item in fields(proof.authority))
    assert all(getattr(proof.deltas, item.name) == 0.0 for item in fields(proof.deltas))
    assert proof.pass_gate
    assert not result.checkpoint_restart_proof_included
    validate_standalone_acceptance_restart_proof_result(proof)


def test_missing_state_is_explicit_non_proof_fallback(tmp_path: Path) -> None:
    loaded = load_standalone_acceptance_result(tmp_path / "missing.json")

    assert loaded.status is StandaloneAcceptanceLoadStatus.MISSING_FALLBACK
    assert loaded.result is None
    assert loaded.payload_checksum_sha256 is None
    assert loaded.result_identity is None
    assert not loaded.checksum_verified
    assert loaded.used_fallback
    assert not loaded.acceptance_proof_available
    assert not loaded.has_authority


def test_malformed_json_is_corrupt_non_proof_fallback(tmp_path: Path) -> None:
    path = tmp_path / "malformed.json"
    path.write_text("{broken\n", encoding="ascii")

    loaded = load_standalone_acceptance_result(path)

    assert loaded.status is StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK
    assert loaded.result is None
    assert loaded.used_fallback
    assert not loaded.acceptance_proof_available


def test_checksum_tampering_is_corrupt_non_proof_fallback(tmp_path: Path) -> None:
    path = tmp_path / "checksum.json"
    save_standalone_acceptance_result(path, run_standalone_acceptance())
    envelope = _read_envelope(path)
    payload = _payload(envelope)
    payload["pass_gate"] = False
    _write_envelope(path, envelope)

    loaded = load_standalone_acceptance_result(path)

    assert loaded.status is StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK
    assert loaded.result is None


def test_rechecks_nested_shape_after_valid_checksum(tmp_path: Path) -> None:
    path = tmp_path / "nested-shape.json"
    save_standalone_acceptance_result(path, run_standalone_acceptance())
    envelope = _read_envelope(path)
    payload = _payload(envelope)
    multieffect = _object(payload["multieffect_result"])
    multieffect["selected_window_actions"] = "open_window"
    envelope["payload_checksum_sha256"] = _payload_checksum(payload)
    _write_envelope(path, envelope)

    loaded = load_standalone_acceptance_result(path)

    assert loaded.status is StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK
    assert loaded.result is None


@pytest.mark.parametrize("field", ["schema", "schema_version"])
def test_incompatible_schema_is_explicit_non_proof_fallback(
    tmp_path: Path,
    field: str,
) -> None:
    path = tmp_path / f"incompatible-{field}.json"
    save_standalone_acceptance_result(path, run_standalone_acceptance())
    envelope = _read_envelope(path)
    if field == "schema":
        envelope[field] = "seedmind.ndnra.other"
    else:
        envelope[field] = STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION + 1
    _write_envelope(path, envelope)

    loaded = load_standalone_acceptance_result(path)

    assert loaded.status is StandaloneAcceptanceLoadStatus.INCOMPATIBLE_FALLBACK
    assert loaded.result is None
    assert loaded.used_fallback
    assert not loaded.acceptance_proof_available


def test_result_identity_tampering_is_corrupt_even_with_valid_payload(tmp_path: Path) -> None:
    path = tmp_path / "identity.json"
    save_standalone_acceptance_result(path, run_standalone_acceptance())
    envelope = _read_envelope(path)
    envelope["result_identity"] = "0" * 64
    _write_envelope(path, envelope)

    loaded = load_standalone_acceptance_result(path)

    assert loaded.status is StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK
    assert loaded.result is None


def test_unknown_envelope_or_payload_fields_are_rejected(tmp_path: Path) -> None:
    result = run_standalone_acceptance()
    envelope_path = tmp_path / "extra-envelope.json"
    payload_path = tmp_path / "extra-payload.json"
    save_standalone_acceptance_result(envelope_path, result)
    save_standalone_acceptance_result(payload_path, result)

    envelope = _read_envelope(envelope_path)
    envelope["unexpected"] = False
    _write_envelope(envelope_path, envelope)

    payload_envelope = _read_envelope(payload_path)
    payload = _payload(payload_envelope)
    payload["unexpected"] = False
    payload_envelope["payload_checksum_sha256"] = _payload_checksum(payload)
    _write_envelope(payload_path, payload_envelope)

    assert load_standalone_acceptance_result(envelope_path).status is (
        StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK
    )
    assert load_standalone_acceptance_result(payload_path).status is (
        StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK
    )


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda proof: replace(proof, exact_round_trip=False),
            "exact round-trip equivalence",
        ),
        (
            lambda proof: replace(proof, rerun_equivalent=False),
            "deterministic rerun equivalence",
        ),
        (
            lambda proof: replace(proof, bounded_imagination_persisted=True),
            "cannot persist bounded imagination",
        ),
        (
            lambda proof: replace(proof, main_brain_schema_changed=True),
            "cannot change the main brain schema",
        ),
        (
            lambda proof: replace(
                proof,
                authority=StandaloneAcceptanceAuthority(
                    action_selection_authority=True,
                    production_action_authority=False,
                    recommendation_authority=False,
                    scheduling_authority=False,
                    execution_authority=False,
                    persistence_authority=False,
                    live_integration_authority=False,
                    promotion_authority=False,
                ),
            ),
            "cannot grant authority",
        ),
    ],
)
def test_restart_proof_rejects_tampering(
    tmp_path: Path,
    mutator: Callable[
        [StandaloneAcceptanceRestartProofResult],
        StandaloneAcceptanceRestartProofResult,
    ],
    message: str,
) -> None:
    proof = prove_standalone_acceptance_restart(
        tmp_path / "proof.json",
        run_standalone_acceptance(),
    )

    with pytest.raises(ValueError, match=message):
        validate_standalone_acceptance_restart_proof_result(mutator(proof))


def test_load_result_shape_cannot_claim_partial_or_authoritative_fallback() -> None:
    with pytest.raises(ValueError, match="cannot expose a partial result"):
        StandaloneAcceptanceLoadResult(
            status=StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK,
            result=run_standalone_acceptance(),
            payload_checksum_sha256=None,
            result_identity=None,
            checksum_verified=False,
            used_fallback=True,
            acceptance_proof_available=False,
        )
    with pytest.raises(ValueError, match="cannot grant authority"):
        StandaloneAcceptanceLoadResult(
            status=StandaloneAcceptanceLoadStatus.MISSING_FALLBACK,
            result=None,
            payload_checksum_sha256=None,
            result_identity=None,
            checksum_verified=False,
            used_fallback=True,
            acceptance_proof_available=False,
            has_authority=True,
        )


def test_persistence_module_is_isolated_from_brain_and_imagination_authority() -> None:
    source = Path("src/seedmind/research/ndnra/standalone_acceptance_persistence.py").read_text(
        encoding="ascii"
    )
    lowered = source.lower()

    assert BRAIN_SCHEMA_VERSION > 0
    assert "brain_schema_version" not in lowered
    assert "from seedmind.research.ndnra.bounded_imagination" not in lowered
    assert "import seedmind.research.ndnra.bounded_imagination" not in lowered
    assert "sqlite3" not in lowered
    assert "seedmind.integration" not in lowered
    assert "asyncio" not in lowered
    assert "threading" not in lowered
    assert "subprocess" not in lowered
    assert "schedule(" not in lowered
    assert "execute(" not in lowered
    assert "recommend(" not in lowered
    assert "promote(" not in lowered


def _read_envelope(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="ascii"))
    return _object(value)


def _write_envelope(path: Path, envelope: dict[str, object]) -> None:
    path.write_text(
        json.dumps(
            envelope,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        + "\n",
        encoding="ascii",
    )


def _payload(envelope: dict[str, object]) -> dict[str, object]:
    return _object(envelope["payload"])


def _object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return value


def _payload_checksum(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()
