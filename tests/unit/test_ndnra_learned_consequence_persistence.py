"""Tests for learned consequence checkpoint persistence and restart reconstruction."""

# ruff: noqa: I001 -- pytest exposes the adjacent support module as top-level.

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest

from ndnra_execution_test_support import ASSEMBLIES, ROUTES, build_setup, commit_request

from seedmind.research.ndnra import (
    BRAIN_SCHEMA_VERSION,
    BrainLoadStatus,
    ConsequenceChainPredictionRequest,
    ConsequenceModelObservation,
    ConsequencePredictionRequest,
    ConsolidationExecutionDurableCommitPolicy,
    ContextSignature,
    ContextualTransferConfig,
    EffectObservation,
    ExperienceOrigin,
    LearnedConsequenceModel,
    NDNRABrainStore,
    NDNRALearnedConsequenceCheckpoint,
    NDNRAProposalLifecycleCheckpoint,
    NDNRAReplayRestorationCheckpoint,
    ObservedConsequenceChain,
    ObservedConsequenceChainModel,
    build_capacity_limited_graph,
)


def _context(*, inside_heat: float, outside_heat: float = 0.3) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code="reduce_temperature",
        sensor_values=(inside_heat, outside_heat),
        available_action_codes=("open_window", "start_fan", "wait"),
        resource_values=(0.8,),
    )


def _observation(
    *,
    event_id: str,
    context: ContextSignature,
    action_code: str,
    next_context: ContextSignature,
    temperature_effect: float,
    energy_effect: float = 0.0,
) -> ConsequenceModelObservation:
    return ConsequenceModelObservation(
        event_id=event_id,
        origin=ExperienceOrigin.REAL,
        context=context,
        action_code=action_code,
        next_context=next_context,
        observed_effects=(
            EffectObservation("energy_cost", energy_effect, 1.0),
            EffectObservation("temperature", temperature_effect, 1.0),
        ),
    )


def _request(context: ContextSignature) -> ConsequencePredictionRequest:
    return ConsequencePredictionRequest(
        context=context,
        action_code="open_window",
        relevant_effect_codes=("energy_cost", "temperature"),
    )


def _chain_request(start_context: ContextSignature) -> ConsequenceChainPredictionRequest:
    return ConsequenceChainPredictionRequest(
        start_context=start_context,
        action_codes=("open_window", "start_fan"),
        relevant_effect_codes=("energy_cost", "temperature"),
    )


def _checkpoint() -> tuple[
    NDNRALearnedConsequenceCheckpoint,
    ConsequenceModelObservation,
    ObservedConsequenceChain,
]:
    start = _context(inside_heat=0.9)
    middle = _context(inside_heat=0.7)
    final = _context(inside_heat=0.4)
    repeat = _observation(
        event_id="real:persist:model:repeat",
        context=start,
        action_code="open_window",
        next_context=middle,
        temperature_effect=-0.2,
    )
    calibration = replace(repeat, event_id="real:persist:model:calibration")
    chain_step = _observation(
        event_id="real:persist:chain:002",
        context=middle,
        action_code="start_fan",
        next_context=final,
        temperature_effect=-0.3,
        energy_effect=-0.1,
    )
    model = LearnedConsequenceModel()
    model.observe(repeat)
    prior = model.predict(_request(start))
    model.observe(calibration, prior_prediction=prior)
    chain = ObservedConsequenceChain.from_observations((repeat, chain_step))
    chain_model = ObservedConsequenceChainModel()
    chain_model.observe(chain)
    return (
        NDNRALearnedConsequenceCheckpoint(
            consequence_model=model,
            transfer_config=ContextualTransferConfig(maximum_transfer_sources=2),
            observed_chain_model=chain_model,
        ),
        repeat,
        chain,
    )


def _canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _state_payload_from_payload(
    payload: dict[str, object],
    *,
    schema_version: int,
) -> dict[str, object]:
    replay_checkpoint = cast(dict[str, object], payload["replay_restoration_checkpoint"])
    state_payload = {
        "graph": payload["graph"],
        "growth_state": payload["growth_state"],
        "consolidation_checkpoint": payload["consolidation_checkpoint"],
        "proposal_lifecycle_checkpoint": payload["proposal_lifecycle_checkpoint"],
        "execution_checkpoint": payload["execution_checkpoint"],
        "replay_restoration_active_state": {
            "activity_ledger": replay_checkpoint["activity_ledger"]
        },
    }
    if schema_version >= 7:
        state_payload["learned_consequence_checkpoint"] = payload["learned_consequence_checkpoint"]
    return state_payload


def _write_envelope(
    path: Path,
    *,
    schema: str,
    schema_version: int,
    payload: dict[str, object],
) -> None:
    state_checksum = _canonical_checksum(
        _state_payload_from_payload(payload, schema_version=schema_version)
    )
    body: dict[str, object] = {
        "schema": schema,
        "schema_version": schema_version,
        "state_checksum": state_checksum,
        "payload": payload,
    }
    path.write_text(
        json.dumps(
            {**body, "checksum": _canonical_checksum(body)},
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="ascii",
    )


def test_learned_checkpoint_round_trips_exactly_and_has_no_authority() -> None:
    checkpoint, _, _ = _checkpoint()
    snapshot = checkpoint.snapshot()

    restored = NDNRALearnedConsequenceCheckpoint.from_snapshot(snapshot)
    mutated = cast(dict[str, object], snapshot["consequence_model"])
    mutated["real_observation_count"] = 0

    assert restored == checkpoint
    assert restored.snapshot() == checkpoint.snapshot()
    assert restored.automatic_prediction_count == 0
    assert not restored.has_action_selection_authority
    assert not restored.has_production_action_authority
    assert checkpoint.snapshot()["consequence_model"] != mutated


def test_brain_store_schema_7_restores_predictions_and_duplicate_protection(
    tmp_path: Path,
) -> None:
    checkpoint, observation, chain = _checkpoint()
    store = NDNRABrainStore(tmp_path / "brain.json")

    saved = store.save(
        build_capacity_limited_graph(),
        replay_restoration_checkpoint=NDNRAReplayRestorationCheckpoint.empty(),
        learned_consequence_checkpoint=checkpoint,
    )
    first = store.load()
    second = store.load()
    loaded_checkpoint = first.learned_consequence_checkpoint

    assert saved.schema_version == BRAIN_SCHEMA_VERSION == 7
    assert first.status is BrainLoadStatus.LOADED
    assert first.schema_version == 7
    assert first.migrated_from_version is None
    assert loaded_checkpoint.snapshot() == checkpoint.snapshot()
    assert second.learned_consequence_checkpoint.snapshot() == loaded_checkpoint.snapshot()
    assert (
        loaded_checkpoint.consequence_model.predict(_request(observation.context)).snapshot()
        == checkpoint.consequence_model.predict(_request(observation.context)).snapshot()
    )
    assert (
        loaded_checkpoint.observed_chain_model.predict(
            _chain_request(chain.start_context)
        ).snapshot()
        == checkpoint.observed_chain_model.predict(_chain_request(chain.start_context)).snapshot()
    )

    duplicate = loaded_checkpoint.consequence_model.observe(observation)
    assert not duplicate.evidence_applied
    with pytest.raises(ValueError, match="identity conflict"):
        loaded_checkpoint.consequence_model.observe(
            replace(
                observation,
                observed_effects=(
                    EffectObservation("energy_cost", 0.0, 1.0),
                    EffectObservation("temperature", 0.2, 1.0),
                ),
            )
        )
    chain_duplicate = loaded_checkpoint.observed_chain_model.observe(chain)
    assert not chain_duplicate.evidence_applied


def test_schema_6_migrates_to_empty_learned_consequence_checkpoint(
    tmp_path: Path,
) -> None:
    checkpoint, _, _ = _checkpoint()
    path = tmp_path / "brain_v6.json"
    store = NDNRABrainStore(path)
    store.save(
        build_capacity_limited_graph(),
        learned_consequence_checkpoint=checkpoint,
    )
    raw = json.loads(path.read_text(encoding="ascii"))
    payload = dict(raw["payload"])
    payload.pop("learned_consequence_checkpoint")
    _write_envelope(
        path,
        schema=cast(str, raw["schema"]),
        schema_version=6,
        payload=payload,
    )

    loaded = store.load()

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.checksum_verified
    assert not loaded.used_fallback
    assert loaded.schema_version == 6
    assert loaded.migrated_from_version == 6
    assert loaded.learned_consequence_checkpoint == NDNRALearnedConsequenceCheckpoint.empty()


def test_corrupt_truncated_and_oversized_learned_checkpoints_fall_back(
    tmp_path: Path,
) -> None:
    checkpoint, _, _ = _checkpoint()
    path = tmp_path / "brain.json"
    store = NDNRABrainStore(path)
    store.save(
        build_capacity_limited_graph(),
        learned_consequence_checkpoint=checkpoint,
    )
    raw = json.loads(path.read_text(encoding="ascii"))
    payload = cast(dict[str, object], raw["payload"])
    learned = cast(dict[str, object], payload["learned_consequence_checkpoint"])
    model = cast(dict[str, object], learned["consequence_model"])
    config = cast(dict[str, object], model["config"])
    config["maximum_real_observations"] = 1
    _write_envelope(
        path,
        schema=cast(str, raw["schema"]),
        schema_version=7,
        payload=payload,
    )

    oversized = store.load()
    assert oversized.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert oversized.used_fallback
    assert oversized.learned_consequence_checkpoint == NDNRALearnedConsequenceCheckpoint.empty()
    assert checkpoint.snapshot()["consequence_model"] != model

    path.write_text('{"schema":', encoding="ascii")
    truncated = store.load()
    assert truncated.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert truncated.learned_consequence_checkpoint == NDNRALearnedConsequenceCheckpoint.empty()


def test_checksum_valid_conflicting_record_statistics_fall_back(tmp_path: Path) -> None:
    checkpoint, _, _ = _checkpoint()
    path = tmp_path / "conflicting_stats.json"
    store = NDNRABrainStore(path)
    store.save(
        build_capacity_limited_graph(),
        learned_consequence_checkpoint=checkpoint,
    )
    raw = json.loads(path.read_text(encoding="ascii"))
    payload = cast(dict[str, object], raw["payload"])
    learned = cast(dict[str, object], payload["learned_consequence_checkpoint"])
    model = cast(dict[str, object], learned["consequence_model"])
    records = cast(list[object], model["records"])
    record = cast(dict[str, object], records[0])
    effects = cast(dict[str, object], record["effects"])
    temperature = cast(dict[str, object], effects["temperature"])
    temperature.update(
        {
            "weighted_value_sum": 2.0,
            "weighted_square_sum": 2.0,
            "mean": 1.0,
            "variance": 0.0,
            "consistency": 1.0,
            "confidence": 0.5,
        }
    )
    _write_envelope(
        path,
        schema=cast(str, raw["schema"]),
        schema_version=7,
        payload=payload,
    )

    loaded = store.load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.learned_consequence_checkpoint == NDNRALearnedConsequenceCheckpoint.empty()


def test_checksum_valid_conflicting_calibration_totals_fall_back(tmp_path: Path) -> None:
    checkpoint, _, _ = _checkpoint()
    path = tmp_path / "conflicting_calibration.json"
    store = NDNRABrainStore(path)
    store.save(
        build_capacity_limited_graph(),
        learned_consequence_checkpoint=checkpoint,
    )
    raw = json.loads(path.read_text(encoding="ascii"))
    payload = cast(dict[str, object], raw["payload"])
    learned = cast(dict[str, object], payload["learned_consequence_checkpoint"])
    model = cast(dict[str, object], learned["consequence_model"])
    records = cast(list[object], model["records"])
    record = cast(dict[str, object], records[0])
    record["cumulative_prediction_confidence"] = 0.0
    record["mean_prior_confidence"] = 0.0
    _write_envelope(
        path,
        schema=cast(str, raw["schema"]),
        schema_version=7,
        payload=payload,
    )

    loaded = store.load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.learned_consequence_checkpoint == NDNRALearnedConsequenceCheckpoint.empty()


def test_interrupted_save_leaves_previous_checkpoint_intact(tmp_path: Path) -> None:
    checkpoint, _, _ = _checkpoint()
    path = tmp_path / "brain.json"
    store = NDNRABrainStore(path)
    store.save(build_capacity_limited_graph())
    before = path.read_text(encoding="ascii")

    def interrupt(point: str) -> None:
        if point == "before_atomic_replace":
            raise RuntimeError("stop before replace")

    with pytest.raises(RuntimeError, match="stop before replace"):
        store.save(
            build_capacity_limited_graph(),
            learned_consequence_checkpoint=checkpoint,
            interruption_hook=interrupt,
        )

    loaded = store.load()
    assert path.read_text(encoding="ascii") == before
    assert not store.temporary_path.exists()
    assert loaded.learned_consequence_checkpoint == NDNRALearnedConsequenceCheckpoint.empty()


def test_serialization_is_deterministic_ascii_and_rejects_manual_evidence_creation(
    tmp_path: Path,
) -> None:
    checkpoint, _, _ = _checkpoint()
    graph = build_capacity_limited_graph()
    first_path = tmp_path / "first.json"
    second_path = tmp_path / "second.json"

    NDNRABrainStore(first_path).save(graph, learned_consequence_checkpoint=checkpoint)
    NDNRABrainStore(second_path).save(graph, learned_consequence_checkpoint=checkpoint)
    first_text = first_path.read_text(encoding="ascii")
    second_text = second_path.read_text(encoding="ascii")

    assert first_text == second_text
    assert first_text.isascii()
    raw = json.loads(first_text)
    learned = cast(dict[str, object], raw["payload"])["learned_consequence_checkpoint"]
    assert cast(dict[str, object], learned)["automatic_prediction_count"] == 0

    tampered = cast(dict[str, object], raw["payload"])
    learned_payload = cast(dict[str, object], tampered["learned_consequence_checkpoint"])
    learned_payload["automatic_prediction_count"] = 1
    _write_envelope(
        first_path,
        schema=cast(str, raw["schema"]),
        schema_version=7,
        payload=tampered,
    )
    loaded = NDNRABrainStore(first_path).load()
    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK


def test_durable_execution_preserves_existing_learned_checkpoint(tmp_path: Path) -> None:
    checkpoint, _, _ = _checkpoint()
    setup = build_setup()
    store = NDNRABrainStore(tmp_path / "durable_execution.json")
    store.save(
        setup.graph,
        growth_state=setup.growth_state,
        consolidation_checkpoint=setup.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=NDNRAProposalLifecycleCheckpoint(
            registry=setup.proposal_registry
        ),
        execution_checkpoint=setup.execution_checkpoint,
        learned_consequence_checkpoint=checkpoint,
    )
    loaded = store.load()
    state = loaded.consolidation_checkpoint.application_state()
    assert state is not None

    durable = ConsolidationExecutionDurableCommitPolicy().execute_and_save(
        request=commit_request(loaded.execution_checkpoint.permit_registry.records[0].permit),
        proposal_record=loaded.proposal_lifecycle_checkpoint.registry.active_records[0],
        execution_checkpoint=loaded.execution_checkpoint,
        ledger=loaded.graph.contextual_memory,
        application_state=state,
        available_assembly_ids=ASSEMBLIES,
        available_route_ids=ROUTES,
        store=store,
        graph=loaded.graph,
        growth_state=loaded.growth_state,
        consolidation_checkpoint=loaded.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=loaded.proposal_lifecycle_checkpoint,
    )
    restarted = store.load()

    assert durable.save_result is not None
    assert restarted.learned_consequence_checkpoint == checkpoint
    assert restarted.learned_consequence_checkpoint.consequence_model.predict(
        _request(_context(inside_heat=0.9))
    ).supporting_real_event_ids == (
        "real:persist:model:calibration",
        "real:persist:model:repeat",
    )
