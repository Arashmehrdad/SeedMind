"""Versioned persistence for standalone NDNRA acceptance proof evidence."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum, StrEnum
from pathlib import Path

from seedmind.research.ndnra.standalone_acceptance import (
    StandaloneAcceptanceAuthority,
    StandaloneAcceptanceDeltaReport,
    StandaloneAcceptanceResult,
    restore_standalone_acceptance_result,
    run_standalone_acceptance,
    standalone_acceptance_payload,
    validate_standalone_acceptance_result,
)

STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA = "seedmind.ndnra.standalone_acceptance"
STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION = 1
_EXPECTED_ENVELOPE_FIELDS = frozenset(
    {
        "schema",
        "schema_version",
        "payload_checksum_sha256",
        "result_identity",
        "payload",
    }
)


class StandaloneAcceptanceLoadStatus(StrEnum):
    """Explicit load outcomes for the standalone acceptance store."""

    LOADED = "loaded"
    MISSING_FALLBACK = "missing_fallback"
    CORRUPT_FALLBACK = "corrupt_fallback"
    INCOMPATIBLE_FALLBACK = "incompatible_fallback"


@dataclass(frozen=True, slots=True)
class StandaloneAcceptanceSaveResult:
    """Deterministic save metadata for one validated acceptance result."""

    path: Path
    schema: str
    schema_version: int
    payload_checksum_sha256: str
    result_identity: str
    bytes_written: int
    temporary_file_remaining: bool


@dataclass(frozen=True, slots=True)
class StandaloneAcceptanceLoadResult:
    """Exact load outcome with no synthesized acceptance evidence."""

    status: StandaloneAcceptanceLoadStatus
    result: StandaloneAcceptanceResult | None
    payload_checksum_sha256: str | None
    result_identity: str | None
    checksum_verified: bool
    used_fallback: bool
    acceptance_proof_available: bool
    has_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_authority:
            raise ValueError("standalone acceptance loading cannot grant authority")
        if self.status is StandaloneAcceptanceLoadStatus.LOADED:
            if self.result is None:
                raise ValueError("loaded acceptance state requires one exact result")
            if self.payload_checksum_sha256 is None or self.result_identity is None:
                raise ValueError("loaded acceptance state requires complete identities")
            _validate_sha256("payload_checksum_sha256", self.payload_checksum_sha256)
            _validate_sha256("result_identity", self.result_identity)
            if not self.checksum_verified:
                raise ValueError("loaded acceptance state requires checksum verification")
            if self.used_fallback:
                raise ValueError("loaded acceptance state cannot use fallback")
            if not self.acceptance_proof_available:
                raise ValueError("loaded acceptance state must expose acceptance proof")
            validate_standalone_acceptance_result(self.result)
            if self.result.result_identity != self.result_identity:
                raise ValueError("loaded result identity does not match result content")
            return
        if self.result is not None:
            raise ValueError("fallback load state cannot expose a partial result")
        if self.payload_checksum_sha256 is not None or self.result_identity is not None:
            raise ValueError("fallback load state cannot expose partial identities")
        if self.checksum_verified:
            raise ValueError("fallback load state cannot claim checksum verification")
        if not self.used_fallback:
            raise ValueError("non-loaded state must be an explicit fallback")
        if self.acceptance_proof_available:
            raise ValueError("fallback load state cannot expose acceptance proof")


@dataclass(frozen=True, slots=True)
class StandaloneAcceptanceRestartProofResult:
    """Evidence that saved acceptance state survives restart and rerun exactly."""

    source_result: StandaloneAcceptanceResult
    restored_result: StandaloneAcceptanceResult
    rerun_result: StandaloneAcceptanceResult
    load_status: StandaloneAcceptanceLoadStatus
    checksum_verified: bool
    exact_round_trip: bool
    rerun_equivalent: bool
    bounded_imagination_persisted: bool
    main_brain_schema_changed: bool
    authority: StandaloneAcceptanceAuthority
    deltas: StandaloneAcceptanceDeltaReport
    canonical_ascii_snapshot: str
    result_identity: str
    pass_gate: bool


def save_standalone_acceptance_result(
    path: Path,
    result: StandaloneAcceptanceResult,
) -> StandaloneAcceptanceSaveResult:
    """Persist one validated Batch 1 result as canonical checksum-protected JSON."""

    validate_standalone_acceptance_result(result)
    payload = standalone_acceptance_payload(result)
    payload_checksum = _checksum_payload(payload)
    envelope = _envelope_payload(result, payload_checksum)
    encoded = (_canonical_ascii_json(envelope) + "\n").encode("ascii")
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    try:
        with temporary_path.open("wb") as handle:
            handle.write(encoded)
            handle.flush()
            os.fsync(handle.fileno())
        temporary_path.replace(path)
    except BaseException:
        _remove_temporary_file(temporary_path)
        raise
    return StandaloneAcceptanceSaveResult(
        path=path,
        schema=STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA,
        schema_version=STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION,
        payload_checksum_sha256=payload_checksum,
        result_identity=result.result_identity,
        bytes_written=len(encoded),
        temporary_file_remaining=temporary_path.exists(),
    )


def load_standalone_acceptance_result(path: Path) -> StandaloneAcceptanceLoadResult:
    """Load exact acceptance evidence or return one explicit non-proof fallback."""

    if not path.exists():
        return _failed_load(StandaloneAcceptanceLoadStatus.MISSING_FALLBACK)
    try:
        envelope = json.loads(path.read_text(encoding="ascii"))
        values = _require_mapping("standalone acceptance envelope", envelope)
        if set(values) != _EXPECTED_ENVELOPE_FIELDS:
            return _failed_load(StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK)
        if _require_string(values, "schema") != STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA:
            return _failed_load(StandaloneAcceptanceLoadStatus.INCOMPATIBLE_FALLBACK)
        if (
            _require_int(values, "schema_version")
            != STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION
        ):
            return _failed_load(StandaloneAcceptanceLoadStatus.INCOMPATIBLE_FALLBACK)
        payload = dict(_require_mapping("standalone acceptance payload", values["payload"]))
        payload_checksum = _require_sha256(values, "payload_checksum_sha256")
        if payload_checksum != _checksum_payload(payload):
            return _failed_load(StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK)
        restored = restore_standalone_acceptance_result(payload)
        result_identity = _require_sha256(values, "result_identity")
        if restored.result_identity != result_identity:
            return _failed_load(StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK)
        if _envelope_payload(restored, payload_checksum) != dict(values):
            return _failed_load(StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK)
        return StandaloneAcceptanceLoadResult(
            status=StandaloneAcceptanceLoadStatus.LOADED,
            result=restored,
            payload_checksum_sha256=payload_checksum,
            result_identity=result_identity,
            checksum_verified=True,
            used_fallback=False,
            acceptance_proof_available=True,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return _failed_load(StandaloneAcceptanceLoadStatus.CORRUPT_FALLBACK)


def prove_standalone_acceptance_restart(
    path: Path,
    result: StandaloneAcceptanceResult,
) -> StandaloneAcceptanceRestartProofResult:
    """Persist, reload, and rerun one Batch 1 result to prove equivalence."""

    save_standalone_acceptance_result(path, result)
    load_result = load_standalone_acceptance_result(path)
    if (
        load_result.status is not StandaloneAcceptanceLoadStatus.LOADED
        or load_result.result is None
    ):
        raise ValueError("restart proof requires one successfully reloaded acceptance result")
    rerun_result = run_standalone_acceptance()
    exact_round_trip = load_result.result == result
    rerun_equivalent = rerun_result == load_result.result
    authority = _zero_authority()
    deltas = _zero_deltas()
    pass_gate = bool(
        result.pass_gate
        and exact_round_trip
        and rerun_equivalent
        and load_result.checksum_verified
        and _authority_is_zero(authority)
        and _deltas_are_zero(deltas)
    )
    seed = StandaloneAcceptanceRestartProofResult(
        source_result=result,
        restored_result=load_result.result,
        rerun_result=rerun_result,
        load_status=load_result.status,
        checksum_verified=load_result.checksum_verified,
        exact_round_trip=exact_round_trip,
        rerun_equivalent=rerun_equivalent,
        bounded_imagination_persisted=False,
        main_brain_schema_changed=False,
        authority=authority,
        deltas=deltas,
        canonical_ascii_snapshot="",
        result_identity="",
        pass_gate=pass_gate,
    )
    snapshot = _canonical_restart_proof_snapshot(seed)
    proof = StandaloneAcceptanceRestartProofResult(
        source_result=result,
        restored_result=load_result.result,
        rerun_result=rerun_result,
        load_status=load_result.status,
        checksum_verified=load_result.checksum_verified,
        exact_round_trip=exact_round_trip,
        rerun_equivalent=rerun_equivalent,
        bounded_imagination_persisted=False,
        main_brain_schema_changed=False,
        authority=authority,
        deltas=deltas,
        canonical_ascii_snapshot=snapshot,
        result_identity=hashlib.sha256(snapshot.encode("ascii")).hexdigest(),
        pass_gate=pass_gate,
    )
    validate_standalone_acceptance_restart_proof_result(proof)
    return proof


def validate_standalone_acceptance_restart_proof_result(
    result: StandaloneAcceptanceRestartProofResult,
) -> None:
    """Reject restart proof that weakens evidence or authority boundaries."""

    validate_standalone_acceptance_result(result.source_result)
    validate_standalone_acceptance_result(result.restored_result)
    validate_standalone_acceptance_result(result.rerun_result)
    if any(
        item.checkpoint_restart_proof_included
        for item in (result.source_result, result.restored_result, result.rerun_result)
    ):
        raise ValueError("plain Batch 1 results must not claim restart proof")
    if result.load_status is not StandaloneAcceptanceLoadStatus.LOADED:
        raise ValueError("restart proof requires loaded acceptance evidence")
    if not result.checksum_verified:
        raise ValueError("restart proof requires checksum verification")
    if not result.exact_round_trip or result.restored_result != result.source_result:
        raise ValueError("restart proof requires exact round-trip equivalence")
    if not result.rerun_equivalent or result.rerun_result != result.restored_result:
        raise ValueError("restart proof requires deterministic rerun equivalence")
    if result.bounded_imagination_persisted:
        raise ValueError("restart proof cannot persist bounded imagination")
    if result.main_brain_schema_changed:
        raise ValueError("restart proof cannot change the main brain schema")
    if not _authority_is_zero(result.authority):
        raise ValueError("restart proof cannot grant authority")
    if not _deltas_are_zero(result.deltas):
        raise ValueError("restart proof deltas must remain zero")
    expected_snapshot = _canonical_restart_proof_snapshot(result)
    if result.canonical_ascii_snapshot != expected_snapshot:
        raise ValueError("restart proof snapshot does not match proof content")
    expected_identity = hashlib.sha256(expected_snapshot.encode("ascii")).hexdigest()
    if result.result_identity != expected_identity:
        raise ValueError("restart proof identity does not match canonical snapshot")
    expected_pass_gate = bool(
        result.source_result.pass_gate
        and result.checksum_verified
        and result.exact_round_trip
        and result.rerun_equivalent
        and not result.bounded_imagination_persisted
        and not result.main_brain_schema_changed
        and _authority_is_zero(result.authority)
        and _deltas_are_zero(result.deltas)
    )
    if result.pass_gate is not expected_pass_gate:
        raise ValueError("restart proof pass gate does not match proof evidence")


def _canonical_restart_proof_snapshot(result: StandaloneAcceptanceRestartProofResult) -> str:
    payload = {
        field.name: _json_ready(getattr(result, field.name))
        for field in fields(result)
        if field.name not in {"canonical_ascii_snapshot", "result_identity"}
    }
    return _canonical_ascii_json(payload)


def _envelope_payload(
    result: StandaloneAcceptanceResult,
    payload_checksum: str,
) -> dict[str, object]:
    return {
        "schema": STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA,
        "schema_version": STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION,
        "payload_checksum_sha256": payload_checksum,
        "result_identity": result.result_identity,
        "payload": standalone_acceptance_payload(result),
    }


def _failed_load(status: StandaloneAcceptanceLoadStatus) -> StandaloneAcceptanceLoadResult:
    if status is StandaloneAcceptanceLoadStatus.LOADED:
        raise ValueError("loaded status cannot be used for fallback")
    return StandaloneAcceptanceLoadResult(
        status=status,
        result=None,
        payload_checksum_sha256=None,
        result_identity=None,
        checksum_verified=False,
        used_fallback=True,
        acceptance_proof_available=False,
    )


def _checksum_payload(payload: dict[str, object]) -> str:
    return hashlib.sha256(_canonical_ascii_json(payload).encode("ascii")).hexdigest()


def _canonical_ascii_json(payload: object) -> str:
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _json_ready(value: object) -> object:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {field.name: _json_ready(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, Path):
        return str(value)
    return value


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.isascii() or not value.strip():
        raise ValueError(f"{key} must be non-empty ASCII text")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_sha256(values: Mapping[str, object], key: str) -> str:
    value = _require_string(values, key)
    _validate_sha256(key, value)
    return value


def _validate_sha256(name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 hexadecimal digest")


def _remove_temporary_file(path: Path) -> None:
    try:
        path.unlink(missing_ok=True)
    except OSError:
        return


def _zero_authority() -> StandaloneAcceptanceAuthority:
    return StandaloneAcceptanceAuthority(
        action_selection_authority=False,
        production_action_authority=False,
        recommendation_authority=False,
        scheduling_authority=False,
        execution_authority=False,
        persistence_authority=False,
        live_integration_authority=False,
        promotion_authority=False,
    )


def _zero_deltas() -> StandaloneAcceptanceDeltaReport:
    return StandaloneAcceptanceDeltaReport(
        factual_confidence_delta=0.0,
        mastery_delta=0.0,
        competence_delta=0.0,
        growth_delta=0.0,
        replay_delta=0.0,
        real_observation_delta=0.0,
    )


def _authority_is_zero(authority: StandaloneAcceptanceAuthority) -> bool:
    return not any(getattr(authority, field.name) for field in fields(authority))


def _deltas_are_zero(deltas: StandaloneAcceptanceDeltaReport) -> bool:
    return all(getattr(deltas, field.name) == 0.0 for field in fields(deltas))


__all__ = [
    "STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA",
    "STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION",
    "StandaloneAcceptanceLoadResult",
    "StandaloneAcceptanceLoadStatus",
    "StandaloneAcceptanceRestartProofResult",
    "StandaloneAcceptanceSaveResult",
    "load_standalone_acceptance_result",
    "prove_standalone_acceptance_restart",
    "save_standalone_acceptance_result",
    "validate_standalone_acceptance_restart_proof_result",
]
