"""Isolated persistence and restart proof for long-horizon interference Batch 2."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Mapping
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum, StrEnum
from pathlib import Path

from seedmind.research.ndnra.long_horizon_interference_experiment import (
    LongHorizonInterferenceResult,
    long_horizon_interference_payload,
    restore_long_horizon_interference_result,
    run_long_horizon_interference_experiment,
    validate_long_horizon_interference_result,
)

LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA = "seedmind.ndnra.long_horizon_interference"
LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION = 1
_EXPECTED_ENVELOPE_FIELDS = frozenset(
    {"schema", "schema_version", "payload_checksum_sha256", "result_identity", "payload"}
)


class LongHorizonInterferenceLoadStatus(StrEnum):
    LOADED = "loaded"
    MISSING_FALLBACK = "missing_fallback"
    CORRUPT_FALLBACK = "corrupt_fallback"
    INCOMPATIBLE_FALLBACK = "incompatible_fallback"


@dataclass(frozen=True, slots=True)
class LongHorizonInterferenceSaveResult:
    path: Path
    schema: str
    schema_version: int
    payload_checksum_sha256: str
    result_identity: str
    bytes_written: int
    temporary_file_remaining: bool


@dataclass(frozen=True, slots=True)
class LongHorizonInterferenceLoadResult:
    status: LongHorizonInterferenceLoadStatus
    result: LongHorizonInterferenceResult | None
    payload_checksum_sha256: str | None
    result_identity: str | None
    checksum_verified: bool
    used_fallback: bool
    restart_proof_available: bool
    has_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_authority:
            raise ValueError("long-horizon interference loading cannot grant authority")
        if self.status is LongHorizonInterferenceLoadStatus.LOADED:
            if self.result is None:
                raise ValueError("loaded long-horizon state requires one exact result")
            if self.payload_checksum_sha256 is None or self.result_identity is None:
                raise ValueError("loaded long-horizon state requires complete identities")
            _validate_sha256("payload_checksum_sha256", self.payload_checksum_sha256)
            _validate_sha256("result_identity", self.result_identity)
            if not self.checksum_verified:
                raise ValueError("loaded long-horizon state requires checksum verification")
            if self.used_fallback:
                raise ValueError("loaded long-horizon state cannot use fallback")
            if not self.restart_proof_available:
                raise ValueError("loaded long-horizon state must expose restart proof availability")
            validate_long_horizon_interference_result(self.result)
            if self.result.sha256_identity != self.result_identity:
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
        if self.restart_proof_available:
            raise ValueError("fallback load state cannot expose restart proof")


@dataclass(frozen=True, slots=True)
class LongHorizonInterferenceAuthorityReport:
    action_selection_authority: bool
    production_action_authority: bool
    recommendation_authority: bool
    scheduling_authority: bool
    execution_authority: bool
    persistence_beyond_isolated_proof_store: bool
    live_integration_authority: bool
    promotion_authority: bool


@dataclass(frozen=True, slots=True)
class LongHorizonInterferenceDeltaReport:
    factual_confidence_delta: float
    mastery_delta: float
    competence_delta: float
    growth_pressure_delta: float
    replay_evidence_delta: float
    real_observations_delta: float
    specialist_count_delta: float
    duplicate_memberships_delta: float
    structural_growth_delta: float


@dataclass(frozen=True, slots=True)
class LongHorizonInterferenceRestartProofResult:
    source_result: LongHorizonInterferenceResult
    restored_result: LongHorizonInterferenceResult
    rerun_result: LongHorizonInterferenceResult
    load_status: LongHorizonInterferenceLoadStatus
    checksum_verified: bool
    exact_round_trip: bool
    rerun_equivalent: bool
    bounded_imagination_persisted: bool
    main_brain_schema_changed: bool
    standalone_acceptance_schema_changed: bool
    authority: LongHorizonInterferenceAuthorityReport
    deltas: LongHorizonInterferenceDeltaReport
    canonical_ascii_snapshot: str
    proof_identity: str
    pass_gate: bool


def save_long_horizon_interference_result(
    path: Path,
    result: LongHorizonInterferenceResult,
) -> LongHorizonInterferenceSaveResult:
    validate_long_horizon_interference_result(result)
    payload = long_horizon_interference_payload(result)
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
    return LongHorizonInterferenceSaveResult(
        path=path,
        schema=LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA,
        schema_version=LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION,
        payload_checksum_sha256=payload_checksum,
        result_identity=result.sha256_identity,
        bytes_written=len(encoded),
        temporary_file_remaining=temporary_path.exists(),
    )


def load_long_horizon_interference_result(path: Path) -> LongHorizonInterferenceLoadResult:
    if not path.exists():
        return _failed_load(LongHorizonInterferenceLoadStatus.MISSING_FALLBACK)
    try:
        envelope = json.loads(path.read_text(encoding="ascii"))
        values = _require_mapping("long-horizon interference envelope", envelope)
        if set(values) != _EXPECTED_ENVELOPE_FIELDS:
            return _failed_load(LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK)
        if _require_ascii(values, "schema") != LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA:
            return _failed_load(LongHorizonInterferenceLoadStatus.INCOMPATIBLE_FALLBACK)
        if (
            _require_int(values, "schema_version")
            != LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION
        ):
            return _failed_load(LongHorizonInterferenceLoadStatus.INCOMPATIBLE_FALLBACK)
        payload = dict(_require_mapping("long-horizon interference payload", values["payload"]))
        payload_checksum = _require_sha256(values, "payload_checksum_sha256")
        if payload_checksum != _checksum_payload(payload):
            return _failed_load(LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK)
        restored = restore_long_horizon_interference_result(payload)
        result_identity = _require_sha256(values, "result_identity")
        if restored.sha256_identity != result_identity:
            return _failed_load(LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK)
        if _envelope_payload(restored, payload_checksum) != dict(values):
            return _failed_load(LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK)
        return LongHorizonInterferenceLoadResult(
            status=LongHorizonInterferenceLoadStatus.LOADED,
            result=restored,
            payload_checksum_sha256=payload_checksum,
            result_identity=result_identity,
            checksum_verified=True,
            used_fallback=False,
            restart_proof_available=True,
        )
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, TypeError, ValueError):
        return _failed_load(LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK)


def prove_long_horizon_interference_restart(
    path: Path,
    result: LongHorizonInterferenceResult,
) -> LongHorizonInterferenceRestartProofResult:
    validate_long_horizon_interference_result(result)
    save_long_horizon_interference_result(path, result)
    load_result = load_long_horizon_interference_result(path)
    if (
        load_result.status is not LongHorizonInterferenceLoadStatus.LOADED
        or load_result.result is None
    ):
        raise ValueError("restart proof requires one successfully reloaded long-horizon result")
    rerun_result = run_long_horizon_interference_experiment().result
    authority = _zero_authority()
    deltas = _zero_deltas()
    exact_round_trip = load_result.result == result
    rerun_equivalent = rerun_result == load_result.result
    pass_gate = _expected_pass_gate(
        source_result=result,
        restored_result=load_result.result,
        rerun_result=rerun_result,
        checksum_verified=load_result.checksum_verified,
        exact_round_trip=exact_round_trip,
        rerun_equivalent=rerun_equivalent,
        bounded_imagination_persisted=False,
        main_brain_schema_changed=False,
        standalone_acceptance_schema_changed=False,
        authority=authority,
        deltas=deltas,
    )
    seed = LongHorizonInterferenceRestartProofResult(
        source_result=result,
        restored_result=load_result.result,
        rerun_result=rerun_result,
        load_status=load_result.status,
        checksum_verified=load_result.checksum_verified,
        exact_round_trip=exact_round_trip,
        rerun_equivalent=rerun_equivalent,
        bounded_imagination_persisted=False,
        main_brain_schema_changed=False,
        standalone_acceptance_schema_changed=False,
        authority=authority,
        deltas=deltas,
        canonical_ascii_snapshot="",
        proof_identity="",
        pass_gate=pass_gate,
    )
    snapshot = _canonical_restart_proof_snapshot(seed)
    proof = LongHorizonInterferenceRestartProofResult(
        source_result=result,
        restored_result=load_result.result,
        rerun_result=rerun_result,
        load_status=load_result.status,
        checksum_verified=load_result.checksum_verified,
        exact_round_trip=exact_round_trip,
        rerun_equivalent=rerun_equivalent,
        bounded_imagination_persisted=False,
        main_brain_schema_changed=False,
        standalone_acceptance_schema_changed=False,
        authority=authority,
        deltas=deltas,
        canonical_ascii_snapshot=snapshot,
        proof_identity=hashlib.sha256(snapshot.encode("ascii")).hexdigest(),
        pass_gate=pass_gate,
    )
    validate_long_horizon_interference_restart_proof_result(proof)
    return proof


def validate_long_horizon_interference_restart_proof_result(
    result: LongHorizonInterferenceRestartProofResult,
) -> None:
    validate_long_horizon_interference_result(result.source_result)
    validate_long_horizon_interference_result(result.restored_result)
    validate_long_horizon_interference_result(result.rerun_result)
    for item in (result.source_result, result.restored_result, result.rerun_result):
        if item.restart_proof_included:
            raise ValueError("plain Batch 1 results must keep restart_proof_included false")
        if not item.pass_gate:
            raise ValueError("restart proof requires pass_gate true for all compared results")
        if not item.source_evidence_unchanged or not item.source_mastery_unchanged:
            raise ValueError("restart proof requires source evidence and mastery unchanged")
        if not item.replay_bounded or not item.replay_sources_resolved:
            raise ValueError("restart proof requires replay bounded and resolved")
        if not item.structure_unchanged:
            raise ValueError("restart proof requires zero structure drift")
        if item.sqlite_used_for_experiment:
            raise ValueError("restart proof cannot use SQLite cognition")
    if result.load_status is not LongHorizonInterferenceLoadStatus.LOADED:
        raise ValueError("restart proof requires loaded long-horizon evidence")
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
    if result.standalone_acceptance_schema_changed:
        raise ValueError("restart proof cannot change the standalone acceptance schema")
    if not _authority_is_zero(result.authority):
        raise ValueError("restart proof cannot grant authority")
    if not _deltas_are_zero(result.deltas):
        raise ValueError("restart proof deltas must remain zero")
    expected_snapshot = _canonical_restart_proof_snapshot(result)
    if result.canonical_ascii_snapshot != expected_snapshot:
        raise ValueError("restart proof snapshot does not match proof content")
    expected_identity = hashlib.sha256(expected_snapshot.encode("ascii")).hexdigest()
    if result.proof_identity != expected_identity:
        raise ValueError("restart proof identity does not match canonical snapshot")
    expected_pass_gate = _expected_pass_gate(
        source_result=result.source_result,
        restored_result=result.restored_result,
        rerun_result=result.rerun_result,
        checksum_verified=result.checksum_verified,
        exact_round_trip=result.exact_round_trip,
        rerun_equivalent=result.rerun_equivalent,
        bounded_imagination_persisted=result.bounded_imagination_persisted,
        main_brain_schema_changed=result.main_brain_schema_changed,
        standalone_acceptance_schema_changed=result.standalone_acceptance_schema_changed,
        authority=result.authority,
        deltas=result.deltas,
    )
    if result.pass_gate is not expected_pass_gate:
        raise ValueError("restart proof pass gate does not match proof evidence")


def _expected_pass_gate(
    *,
    source_result: LongHorizonInterferenceResult,
    restored_result: LongHorizonInterferenceResult,
    rerun_result: LongHorizonInterferenceResult,
    checksum_verified: bool,
    exact_round_trip: bool,
    rerun_equivalent: bool,
    bounded_imagination_persisted: bool,
    main_brain_schema_changed: bool,
    standalone_acceptance_schema_changed: bool,
    authority: LongHorizonInterferenceAuthorityReport,
    deltas: LongHorizonInterferenceDeltaReport,
) -> bool:
    return bool(
        source_result.pass_gate
        and restored_result.pass_gate
        and rerun_result.pass_gate
        and not source_result.restart_proof_included
        and not restored_result.restart_proof_included
        and not rerun_result.restart_proof_included
        and source_result.source_evidence_unchanged
        and source_result.source_mastery_unchanged
        and restored_result.source_evidence_unchanged
        and restored_result.source_mastery_unchanged
        and rerun_result.source_evidence_unchanged
        and rerun_result.source_mastery_unchanged
        and source_result.replay_bounded
        and restored_result.replay_bounded
        and rerun_result.replay_bounded
        and source_result.structure_unchanged
        and restored_result.structure_unchanged
        and rerun_result.structure_unchanged
        and checksum_verified
        and exact_round_trip
        and rerun_equivalent
        and not bounded_imagination_persisted
        and not main_brain_schema_changed
        and not standalone_acceptance_schema_changed
        and _authority_is_zero(authority)
        and _deltas_are_zero(deltas)
    )


def _canonical_restart_proof_snapshot(result: LongHorizonInterferenceRestartProofResult) -> str:
    payload = {
        field.name: _json_ready(getattr(result, field.name))
        for field in fields(result)
        if field.name not in {"canonical_ascii_snapshot", "proof_identity"}
    }
    return _canonical_ascii_json(payload)


def _envelope_payload(
    result: LongHorizonInterferenceResult,
    payload_checksum: str,
) -> dict[str, object]:
    return {
        "schema": LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA,
        "schema_version": LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION,
        "payload_checksum_sha256": payload_checksum,
        "result_identity": result.sha256_identity,
        "payload": long_horizon_interference_payload(result),
    }


def _failed_load(status: LongHorizonInterferenceLoadStatus) -> LongHorizonInterferenceLoadResult:
    if status is LongHorizonInterferenceLoadStatus.LOADED:
        raise ValueError("loaded status cannot be used for fallback")
    return LongHorizonInterferenceLoadResult(
        status=status,
        result=None,
        payload_checksum_sha256=None,
        result_identity=None,
        checksum_verified=False,
        used_fallback=True,
        restart_proof_available=False,
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


def _require_ascii(values: Mapping[str, object], key: str) -> str:
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
    value = _require_ascii(values, key)
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


def _zero_authority() -> LongHorizonInterferenceAuthorityReport:
    return LongHorizonInterferenceAuthorityReport(
        action_selection_authority=False,
        production_action_authority=False,
        recommendation_authority=False,
        scheduling_authority=False,
        execution_authority=False,
        persistence_beyond_isolated_proof_store=False,
        live_integration_authority=False,
        promotion_authority=False,
    )


def _zero_deltas() -> LongHorizonInterferenceDeltaReport:
    return LongHorizonInterferenceDeltaReport(
        factual_confidence_delta=0.0,
        mastery_delta=0.0,
        competence_delta=0.0,
        growth_pressure_delta=0.0,
        replay_evidence_delta=0.0,
        real_observations_delta=0.0,
        specialist_count_delta=0.0,
        duplicate_memberships_delta=0.0,
        structural_growth_delta=0.0,
    )


def _authority_is_zero(authority: LongHorizonInterferenceAuthorityReport) -> bool:
    return not any(getattr(authority, field.name) for field in fields(authority))


def _deltas_are_zero(deltas: LongHorizonInterferenceDeltaReport) -> bool:
    return all(getattr(deltas, field.name) == 0.0 for field in fields(deltas))


__all__ = [
    "LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA",
    "LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION",
    "LongHorizonInterferenceAuthorityReport",
    "LongHorizonInterferenceDeltaReport",
    "LongHorizonInterferenceLoadResult",
    "LongHorizonInterferenceLoadStatus",
    "LongHorizonInterferenceRestartProofResult",
    "LongHorizonInterferenceSaveResult",
    "load_long_horizon_interference_result",
    "prove_long_horizon_interference_restart",
    "save_long_horizon_interference_result",
    "validate_long_horizon_interference_restart_proof_result",
]
