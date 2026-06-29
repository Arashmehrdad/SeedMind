"""Tests for long-horizon interference persistence and restart proof."""

from __future__ import annotations

import hashlib
import json
import tempfile
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import fields, replace
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA,
    LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION,
    LongHorizonInterferenceAuthorityReport,
    LongHorizonInterferenceDeltaReport,
    LongHorizonInterferenceLoadResult,
    LongHorizonInterferenceLoadStatus,
    LongHorizonInterferenceRestartProofResult,
    load_long_horizon_interference_result,
    long_horizon_interference_payload,
    prove_long_horizon_interference_restart,
    restore_long_horizon_interference_result,
    run_long_horizon_interference_experiment,
    save_long_horizon_interference_result,
    validate_long_horizon_interference_restart_proof_result,
)


def test_store_round_trips_exact_result_and_writes_deterministic_ascii() -> None:
    result = run_long_horizon_interference_experiment().result
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        first_path = tmp_path / "nested" / "first.json"
        second_path = tmp_path / "nested" / "second.json"

        first_save = save_long_horizon_interference_result(first_path, result)
        second_save = save_long_horizon_interference_result(second_path, result)
        loaded = load_long_horizon_interference_result(first_path)

        assert first_save.schema == LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA
        assert first_save.schema_version == LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION
        assert first_save.payload_checksum_sha256 == second_save.payload_checksum_sha256
        assert first_save.result_identity == result.sha256_identity
        assert first_save.bytes_written == second_save.bytes_written
        assert not first_save.temporary_file_remaining
        assert not second_save.temporary_file_remaining
        assert not first_path.with_name(f"{first_path.name}.tmp").exists()
        assert first_path.read_bytes() == second_path.read_bytes()
        assert first_path.read_bytes().decode("ascii")
        assert loaded.status is LongHorizonInterferenceLoadStatus.LOADED
        assert loaded.result == result
        assert loaded.payload_checksum_sha256 == first_save.payload_checksum_sha256
        assert loaded.result_identity == result.sha256_identity
        assert loaded.checksum_verified
        assert not loaded.used_fallback
        assert loaded.restart_proof_available
        assert not loaded.has_authority


def test_restart_proof_includes_exact_reload_and_deterministic_rerun() -> None:
    result = run_long_horizon_interference_experiment().result
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        proof = prove_long_horizon_interference_restart(tmp_path / "restart.json", result)

    assert proof.source_result == result
    assert proof.restored_result == result
    assert proof.rerun_result == result
    assert proof.load_status is LongHorizonInterferenceLoadStatus.LOADED
    assert proof.checksum_verified
    assert proof.exact_round_trip
    assert proof.rerun_equivalent
    assert not proof.bounded_imagination_persisted
    assert not proof.main_brain_schema_changed
    assert not proof.standalone_acceptance_schema_changed
    assert not any(getattr(proof.authority, item.name) for item in fields(proof.authority))
    assert all(getattr(proof.deltas, item.name) == 0.0 for item in fields(proof.deltas))
    assert proof.pass_gate
    assert not result.restart_proof_included
    validate_long_horizon_interference_restart_proof_result(proof)


def test_plain_batch_1_result_keeps_restart_proof_false() -> None:
    assert not run_long_horizon_interference_experiment().result.restart_proof_included


def test_missing_state_is_explicit_non_proof_fallback() -> None:
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        loaded = load_long_horizon_interference_result(tmp_path / "missing.json")

    assert loaded.status is LongHorizonInterferenceLoadStatus.MISSING_FALLBACK
    assert loaded.result is None
    assert loaded.payload_checksum_sha256 is None
    assert loaded.result_identity is None
    assert not loaded.checksum_verified
    assert loaded.used_fallback
    assert not loaded.restart_proof_available
    assert not loaded.has_authority


def test_malformed_json_and_non_ascii_are_corrupt_non_proof_fallback() -> None:
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        malformed = tmp_path / "malformed.json"
        malformed.write_text("{broken\n", encoding="ascii")
        non_ascii = tmp_path / "non-ascii.json"
        non_ascii.write_text('{"schema":"caf\\u00e9"}\n', encoding="utf-8")

        assert load_long_horizon_interference_result(malformed).status is (
            LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK
        )
        assert load_long_horizon_interference_result(non_ascii).status is (
            LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK
        )


def test_checksum_and_identity_tampering_are_corrupt_even_with_valid_json() -> None:
    result = run_long_horizon_interference_experiment().result
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        checksum_path = tmp_path / "checksum.json"
        identity_path = tmp_path / "identity.json"
        save_long_horizon_interference_result(checksum_path, result)
        save_long_horizon_interference_result(identity_path, result)

        checksum_envelope = _read_envelope(checksum_path)
        checksum_payload = _payload(checksum_envelope)
        checksum_payload["pass_gate"] = False
        _write_envelope(checksum_path, checksum_envelope)

        identity_envelope = _read_envelope(identity_path)
        identity_envelope["result_identity"] = "0" * 64
        _write_envelope(identity_path, identity_envelope)

        assert load_long_horizon_interference_result(checksum_path).status is (
            LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK
        )
        assert load_long_horizon_interference_result(identity_path).status is (
            LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK
        )


@pytest.mark.parametrize("field", ["schema", "schema_version"])
def test_incompatible_schema_or_version_is_explicit_non_proof_fallback(
    field: str,
) -> None:
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        path = tmp_path / f"incompatible-{field}.json"
        save_long_horizon_interference_result(
            path, run_long_horizon_interference_experiment().result
        )
        envelope = _read_envelope(path)
        if field == "schema":
            envelope[field] = "seedmind.ndnra.other"
        else:
            envelope[field] = LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION + 1
        _write_envelope(path, envelope)

        loaded = load_long_horizon_interference_result(path)

        assert loaded.status is LongHorizonInterferenceLoadStatus.INCOMPATIBLE_FALLBACK
        assert loaded.result is None
        assert loaded.used_fallback
        assert not loaded.restart_proof_available


def test_unknown_envelope_top_level_and_nested_payload_fields_are_rejected() -> None:
    result = run_long_horizon_interference_experiment().result
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        envelope_path = tmp_path / "extra-envelope.json"
        payload_path = tmp_path / "extra-payload.json"
        condition_path = tmp_path / "extra-condition.json"
        timeline_path = tmp_path / "extra-timeline.json"
        memory_path = tmp_path / "extra-memory.json"
        candidate_path = tmp_path / "extra-candidate.json"
        mastery_path = tmp_path / "extra-mastery.json"
        save_long_horizon_interference_result(envelope_path, result)
        save_long_horizon_interference_result(payload_path, result)
        save_long_horizon_interference_result(condition_path, result)
        save_long_horizon_interference_result(timeline_path, result)
        save_long_horizon_interference_result(memory_path, result)
        save_long_horizon_interference_result(candidate_path, result)
        save_long_horizon_interference_result(mastery_path, result)

        envelope = _read_envelope(envelope_path)
        envelope["unexpected"] = False
        _write_envelope(envelope_path, envelope)

        payload_envelope = _read_envelope(payload_path)
        payload = _payload(payload_envelope)
        payload["unexpected"] = False
        payload_envelope["payload_checksum_sha256"] = _payload_checksum(payload)
        _write_envelope(payload_path, payload_envelope)

        condition_envelope = _read_envelope(condition_path)
        condition = _object(_payload(condition_envelope)["no_consolidation"])
        condition["unexpected"] = False
        condition_envelope["payload_checksum_sha256"] = _payload_checksum(
            _payload(condition_envelope)
        )
        _write_envelope(condition_path, condition_envelope)

        timeline_envelope = _read_envelope(timeline_path)
        timeline_items = _list_of_objects(
            _object(_payload(timeline_envelope)["no_consolidation"])["timeline"]
        )
        timeline_step = _object(timeline_items[0])
        timeline_step["unexpected"] = False
        timeline_envelope["payload_checksum_sha256"] = _payload_checksum(
            _payload(timeline_envelope)
        )
        _write_envelope(timeline_path, timeline_envelope)

        memory_envelope = _read_envelope(memory_path)
        memory = _object(
            _object(_payload(memory_envelope)["no_consolidation"])["final_memory_state"]
        )
        memory["unexpected"] = False
        memory_envelope["payload_checksum_sha256"] = _payload_checksum(_payload(memory_envelope))
        _write_envelope(memory_path, memory_envelope)

        candidate_envelope = _read_envelope(candidate_path)
        candidate = _object(_payload(candidate_envelope)["consolidation_candidate"])
        candidate["unexpected"] = False
        candidate_envelope["payload_checksum_sha256"] = _payload_checksum(
            _payload(candidate_envelope)
        )
        _write_envelope(candidate_path, candidate_envelope)

        mastery_envelope = _read_envelope(mastery_path)
        mastery = _object(_payload(mastery_envelope)["old_family_mastery_profile"])
        mastery["unexpected"] = False
        mastery_envelope["payload_checksum_sha256"] = _payload_checksum(_payload(mastery_envelope))
        _write_envelope(mastery_path, mastery_envelope)

        for path in (
            envelope_path,
            payload_path,
            condition_path,
            timeline_path,
            memory_path,
            candidate_path,
            mastery_path,
        ):
            assert load_long_horizon_interference_result(path).status is (
                LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK
            )


def test_restore_rejects_wrong_enum_duplicate_ids_unsorted_memory_and_timeline_tampering() -> None:
    payload = long_horizon_interference_payload(run_long_horizon_interference_experiment().result)

    bad_enum = _clone(payload)
    _object(bad_enum["no_consolidation"])["condition"] = "bad"
    with pytest.raises(ValueError, match="invalid enum value"):
        restore_long_horizon_interference_result(bad_enum)

    duplicate_ids = _clone(payload)
    candidate = _object(duplicate_ids["consolidation_candidate"])
    source_ids = _list_of_strings(candidate["source_event_ids"])
    candidate["source_event_ids"] = [source_ids[0], source_ids[0], source_ids[1]]
    with pytest.raises(ValueError, match="unique"):
        restore_long_horizon_interference_result(duplicate_ids)

    unsorted_memory = _clone(payload)
    memory = _object(_object(unsorted_memory["no_consolidation"])["final_memory_state"])
    route_values = _list_of_objects(memory["route_values"])
    memory["route_values"] = [route_values[1], route_values[0], *route_values[2:]]
    with pytest.raises(ValueError, match="stable sorted route ordering"):
        restore_long_horizon_interference_result(unsorted_memory)

    wrong_timeline = _clone(payload)
    condition = _object(wrong_timeline["no_consolidation"])
    timeline = _list_of_objects(condition["timeline"])
    condition["timeline"] = timeline[:-1]
    with pytest.raises(ValueError, match="exactly 36"):
        restore_long_horizon_interference_result(wrong_timeline)

    wrong_order = _clone(payload)
    order_condition = _object(wrong_order["no_consolidation"])
    order_timeline = order_condition["timeline"]
    assert isinstance(order_timeline, list)
    first = _object(order_timeline[0])
    first["task_family"] = "B"
    with pytest.raises(ValueError, match="task-family order"):
        restore_long_horizon_interference_result(wrong_order)


def test_restore_rejects_semantic_score_pass_gate_authority_and_restart_flag_tampering() -> None:
    payload = long_horizon_interference_payload(run_long_horizon_interference_experiment().result)

    score_tamper = _clone(payload)
    _object(score_tamper["bounded_retention_replay"])["initial_old_family_score"] = 0.0
    with pytest.raises(ValueError, match="initial_old_family_score"):
        restore_long_horizon_interference_result(score_tamper)

    pass_gate_tamper = _clone(payload)
    pass_gate_tamper["pass_gate"] = False
    with pytest.raises(ValueError, match="pass_gate"):
        restore_long_horizon_interference_result(pass_gate_tamper)

    authority_tamper = _clone(payload)
    authority_tamper["action_selection_authority_used"] = True
    with pytest.raises(ValueError, match="action_selection_authority_used"):
        restore_long_horizon_interference_result(authority_tamper)

    restart_flag_tamper = _clone(payload)
    restart_flag_tamper["restart_proof_included"] = True
    with pytest.raises(ValueError, match="restart proof"):
        restore_long_horizon_interference_result(restart_flag_tamper)


def test_load_result_shape_cannot_claim_partial_or_authoritative_fallback() -> None:
    with pytest.raises(ValueError, match="cannot expose a partial result"):
        LongHorizonInterferenceLoadResult(
            status=LongHorizonInterferenceLoadStatus.CORRUPT_FALLBACK,
            result=run_long_horizon_interference_experiment().result,
            payload_checksum_sha256=None,
            result_identity=None,
            checksum_verified=False,
            used_fallback=True,
            restart_proof_available=False,
        )
    with pytest.raises(ValueError, match="cannot grant authority"):
        LongHorizonInterferenceLoadResult(
            status=LongHorizonInterferenceLoadStatus.MISSING_FALLBACK,
            result=None,
            payload_checksum_sha256=None,
            result_identity=None,
            checksum_verified=False,
            used_fallback=True,
            restart_proof_available=False,
            has_authority=True,
        )


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (lambda proof: replace(proof, exact_round_trip=False), "exact round-trip equivalence"),
        (
            lambda proof: replace(proof, rerun_equivalent=False),
            "deterministic rerun equivalence",
        ),
        (
            lambda proof: replace(
                proof,
                source_result=replace(proof.source_result, source_evidence_unchanged=False),
            ),
            "source_evidence_unchanged",
        ),
        (
            lambda proof: replace(
                proof,
                restored_result=replace(proof.restored_result, replay_bounded=False),
            ),
            "replay_bounded",
        ),
        (
            lambda proof: replace(
                proof,
                rerun_result=replace(proof.rerun_result, structure_unchanged=False),
            ),
            "structure_unchanged",
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
            lambda proof: replace(proof, standalone_acceptance_schema_changed=True),
            "cannot change the standalone acceptance schema",
        ),
        (
            lambda proof: replace(
                proof,
                authority=LongHorizonInterferenceAuthorityReport(
                    action_selection_authority=True,
                    production_action_authority=False,
                    recommendation_authority=False,
                    scheduling_authority=False,
                    execution_authority=False,
                    persistence_beyond_isolated_proof_store=False,
                    live_integration_authority=False,
                    promotion_authority=False,
                ),
            ),
            "cannot grant authority",
        ),
        (
            lambda proof: replace(
                proof,
                deltas=LongHorizonInterferenceDeltaReport(
                    factual_confidence_delta=1.0,
                    mastery_delta=0.0,
                    competence_delta=0.0,
                    growth_pressure_delta=0.0,
                    replay_evidence_delta=0.0,
                    real_observations_delta=0.0,
                    specialist_count_delta=0.0,
                    duplicate_memberships_delta=0.0,
                    structural_growth_delta=0.0,
                ),
            ),
            "deltas must remain zero",
        ),
    ],
)
def test_restart_proof_rejects_boundary_and_equivalence_tampering(
    mutator: Callable[
        [LongHorizonInterferenceRestartProofResult],
        LongHorizonInterferenceRestartProofResult,
    ],
    message: str,
) -> None:
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        proof = prove_long_horizon_interference_restart(
            tmp_path / "proof.json",
            run_long_horizon_interference_experiment().result,
        )

        with pytest.raises(ValueError, match=message):
            validate_long_horizon_interference_restart_proof_result(mutator(proof))


def test_restart_proof_rejects_snapshot_identity_and_pass_gate_tampering() -> None:
    with _test_directory() as tmp_dir:
        tmp_path = Path(tmp_dir)
        proof = prove_long_horizon_interference_restart(
            tmp_path / "proof.json",
            run_long_horizon_interference_experiment().result,
        )

        with pytest.raises(ValueError, match="snapshot does not match"):
            validate_long_horizon_interference_restart_proof_result(
                replace(proof, canonical_ascii_snapshot=proof.canonical_ascii_snapshot + "x")
            )
        with pytest.raises(ValueError, match="identity does not match"):
            validate_long_horizon_interference_restart_proof_result(
                replace(proof, proof_identity="0" * 64)
            )
        pass_gate_payload = json.loads(proof.canonical_ascii_snapshot)
        pass_gate_payload["pass_gate"] = False
        pass_gate_snapshot = json.dumps(
            pass_gate_payload,
            ensure_ascii=True,
            sort_keys=True,
            separators=(",", ":"),
        )
        pass_gate_identity = hashlib.sha256(pass_gate_snapshot.encode("ascii")).hexdigest()
        with pytest.raises(ValueError, match="pass gate does not match"):
            validate_long_horizon_interference_restart_proof_result(
                replace(
                    proof,
                    pass_gate=False,
                    canonical_ascii_snapshot=pass_gate_snapshot,
                    proof_identity=pass_gate_identity,
                )
            )


def test_persistence_module_is_isolated_from_disallowed_runtime_surfaces() -> None:
    source = Path("src/seedmind/research/ndnra/long_horizon_interference_persistence.py").read_text(
        encoding="ascii"
    )
    lowered = source.lower()

    for forbidden in (
        "import sqlite3",
        "from seedmind.research.ndnra.persistence",
        "import seedmind.research.ndnra.persistence",
        "standalone_acceptance_persistence",
        "from seedmind.research.ndnra.bounded_imagination",
        "import seedmind.research.ndnra.bounded_imagination",
        "seedmind.integration",
        "asyncio",
        "threading",
        "subprocess",
        "import sched",
        "import time",
        "from time import",
        "import recommendation",
        "from recommendation",
        "executor import",
        "scheduler import",
        "promotion import",
        "production_action_control",
    ):
        assert forbidden not in lowered


def _read_envelope(path: Path) -> dict[str, object]:
    return _object(json.loads(path.read_text(encoding="ascii")))


def _write_envelope(path: Path, envelope: dict[str, object]) -> None:
    path.write_text(
        json.dumps(envelope, ensure_ascii=True, sort_keys=True, separators=(",", ":")) + "\n",
        encoding="ascii",
    )


def _payload(envelope: dict[str, object]) -> dict[str, object]:
    return _object(envelope["payload"])


def _object(value: object) -> dict[str, object]:
    assert isinstance(value, dict)
    assert all(isinstance(key, str) for key in value)
    return value


def _list_of_objects(value: object) -> list[object]:
    assert isinstance(value, list)
    return value


def _list_of_strings(value: object) -> list[str]:
    assert isinstance(value, list)
    assert all(isinstance(item, str) for item in value)
    return value


def _payload_checksum(payload: dict[str, object]) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _clone(value: object) -> dict[str, object]:
    return _object(json.loads(json.dumps(value, ensure_ascii=True, sort_keys=True)))


@contextmanager
def _test_directory() -> Iterator[str]:
    root = Path("tests/unit/.tmp_long_horizon_interference").resolve()
    root.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=root) as directory:
        yield directory
