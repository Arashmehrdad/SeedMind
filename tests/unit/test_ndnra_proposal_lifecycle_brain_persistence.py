"""Tests for schema-v4 proposal lifecycle persistence in the NDNRA brain store."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    BRAIN_SCHEMA,
    BRAIN_SCHEMA_VERSION,
    BrainLoadStatus,
    ConsolidationApplicationState,
    ConsolidationEligibilityPolicy,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewRequest,
    ConsolidationScheduleProposal,
    ConsolidationScheduleRequest,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
    NDNRABrainStore,
    NDNRAConsolidationCheckpoint,
    NDNRAGrowthState,
    NDNRAProposalLifecycleCheckpoint,
    build_capacity_limited_graph,
)

_LESSON = LessonIdentity("reduce_heat", "cooling", 1.0)


def _proposal() -> ConsolidationScheduleProposal:
    ledger = ContextualExperienceLedger()
    assemblies = ("assembly:heat:a", "assembly:heat:b")
    routes = ("route:heat:a", "route:heat:b")
    for index, route_id, transfer_succeeded in (
        (0, routes[0], True),
        (1, routes[1], True),
        (2, routes[0], False),
    ):
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity(
                    "brain_lifecycle_persistence",
                    "episode:mastery",
                    index,
                ),
                correlation_group_id=f"group:brain-lifecycle:{index}",
                assembly_id=(assemblies[0] if route_id == routes[0] else assemblies[1]),
                route_id=route_id,
                action_code="cool",
                context=ContextSignature.from_values(
                    active_need_code=_LESSON.need_code,
                    sensor_values=(float(index),),
                    available_action_codes=("cool", "wait"),
                ),
                observed_effects=(EffectObservation(_LESSON.effect_code, 1.0, 1.0),),
                transfer_attempted=True,
                transfer_succeeded=transfer_succeeded,
            )
        )
    decision = ConsolidationSchedulingPolicy(first_eligible_episode=100).evaluate(
        ledger=ledger,
        request=ConsolidationScheduleRequest(
            lesson=_LESSON,
            available_assembly_ids=assemblies,
            available_route_ids=routes,
        ),
        context=ConsolidationSchedulingContext(episode_index=100),
    )
    assert decision.proposal is not None
    return decision.proposal


def _consolidation_checkpoint() -> NDNRAConsolidationCheckpoint:
    ledger = ContextualExperienceLedger()
    assemblies = ("assembly:heat:a", "assembly:heat:b")
    routes = ("route:heat:a", "route:heat:b")
    for index, route_id, transfer_succeeded in (
        (0, routes[0], True),
        (1, routes[1], True),
        (2, routes[0], False),
    ):
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity(
                    "brain_consolidation_persistence",
                    "episode:mastery",
                    index,
                ),
                correlation_group_id=f"group:brain-consolidation:{index}",
                assembly_id=(assemblies[0] if route_id == routes[0] else assemblies[1]),
                route_id=route_id,
                action_code="cool",
                context=ContextSignature.from_values(
                    active_need_code=_LESSON.need_code,
                    sensor_values=(float(index),),
                    available_action_codes=("cool", "wait"),
                ),
                observed_effects=(EffectObservation(_LESSON.effect_code, 1.0, 1.0),),
                transfer_attempted=True,
                transfer_succeeded=transfer_succeeded,
            )
        )
    eligibility = ConsolidationEligibilityPolicy().evaluate(
        ledger=ledger,
        lesson=_LESSON,
        mastery_profile=ledger.mastery_profile(_LESSON),
        available_assembly_ids=assemblies,
        available_route_ids=routes,
    )
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=assemblies,
        route_ids=routes,
        initial_stability=0.20,
        initial_plasticity=0.80,
    )
    application = state.apply(eligibility)
    return NDNRAConsolidationCheckpoint(
        state=state.snapshot(),
        active_applications=(application,),
    )


def _lifecycle_checkpoint() -> NDNRAProposalLifecycleCheckpoint:
    proposal = _proposal()
    registry = (
        ConsolidationProposalLifecycleRegistry(maximum_active_records=1)
        .add(proposal)
        .review(
            ConsolidationProposalReviewRequest(
                proposal=proposal,
                action=ConsolidationProposalReviewAction.DEFER,
                decision_episode=101,
                reviewer_code="human:operator",
                reason_code="restart_review_window",
                defer_until_episode=120,
            )
        )
        .review(
            ConsolidationProposalReviewRequest(
                proposal=proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=120,
                reviewer_code="human:operator",
                reason_code="restart_review_passed",
            )
        )
    )
    return NDNRAProposalLifecycleCheckpoint(registry=registry)


def _rewrite_as_legacy(path: Path, version: int) -> None:
    raw: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(raw, dict)
    payload = raw["payload"]
    assert isinstance(payload, dict)
    payload.pop("proposal_lifecycle_checkpoint", None)
    if version < 3:
        payload.pop("consolidation_checkpoint", None)
    if version == 1:
        graph = payload["graph"]
        assert isinstance(graph, dict)
        graph.pop("contextual_memory", None)
    raw["schema_version"] = version
    _rewrite_checksum_payload(path, raw)


def _rewrite_checksum_payload(path: Path, raw: dict[str, object]) -> None:
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


def test_schema_v4_round_trips_lifecycle_with_other_brain_state(
    tmp_path: Path,
) -> None:
    graph = build_capacity_limited_graph()
    growth = NDNRAGrowthState(
        pressure=0.25,
        attempt_count=2,
        residuals=(-0.10, 0.20),
    )
    consolidation = _consolidation_checkpoint()
    lifecycle = _lifecycle_checkpoint()
    store = NDNRABrainStore(tmp_path / "brain.json")

    saved = store.save(
        graph,
        growth_state=growth,
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=lifecycle,
    )
    loaded = store.load()

    assert BRAIN_SCHEMA_VERSION == 6
    assert saved.schema == BRAIN_SCHEMA
    assert saved.schema_version == 6
    assert not saved.temporary_file_remaining
    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.checksum_verified
    assert not loaded.used_fallback
    assert loaded.graph.snapshot() == graph.snapshot()
    assert loaded.growth_state == growth
    assert loaded.consolidation_checkpoint == consolidation
    assert loaded.proposal_lifecycle_checkpoint == lifecycle
    assert loaded.proposal_lifecycle_checkpoint.registry.records[0].lifecycle.decisions == (
        lifecycle.registry.records[0].lifecycle.decisions
    )


def test_default_schema_v4_save_uses_empty_lifecycle_checkpoint(
    tmp_path: Path,
) -> None:
    path = tmp_path / "brain.json"

    NDNRABrainStore(path).save(build_capacity_limited_graph())
    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.proposal_lifecycle_checkpoint == NDNRAProposalLifecycleCheckpoint.empty()


@pytest.mark.parametrize("legacy_version", [1, 2, 3])
def test_legacy_schemas_migrate_to_empty_lifecycle_checkpoint(
    tmp_path: Path,
    legacy_version: int,
) -> None:
    path = tmp_path / f"brain_v{legacy_version}.json"
    consolidation = _consolidation_checkpoint()
    NDNRABrainStore(path).save(
        build_capacity_limited_graph(),
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=_lifecycle_checkpoint(),
    )
    _rewrite_as_legacy(path, legacy_version)

    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.migrated_from_version == legacy_version
    assert loaded.checksum_verified
    assert not loaded.used_fallback
    assert loaded.consolidation_checkpoint == (
        consolidation if legacy_version == 3 else NDNRAConsolidationCheckpoint.empty()
    )
    assert loaded.proposal_lifecycle_checkpoint == NDNRAProposalLifecycleCheckpoint.empty()
    assert loaded.proposal_lifecycle_checkpoint.registry.records == ()


def test_schema_v4_missing_lifecycle_payload_falls_back_completely(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing_lifecycle.json"
    NDNRABrainStore(path).save(
        build_capacity_limited_graph(),
        proposal_lifecycle_checkpoint=_lifecycle_checkpoint(),
    )
    raw: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(raw, dict)
    payload = raw["payload"]
    assert isinstance(payload, dict)
    payload.pop("proposal_lifecycle_checkpoint")
    _rewrite_checksum_payload(path, raw)

    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.used_fallback
    assert loaded.graph.assembly_count == 0
    assert loaded.growth_state == NDNRAGrowthState()
    assert loaded.consolidation_checkpoint == NDNRAConsolidationCheckpoint.empty()
    assert loaded.proposal_lifecycle_checkpoint == NDNRAProposalLifecycleCheckpoint.empty()


def test_schema_v4_inconsistent_lifecycle_falls_back_without_partial_graph(
    tmp_path: Path,
) -> None:
    path = tmp_path / "bad_lifecycle.json"
    NDNRABrainStore(path).save(
        build_capacity_limited_graph(),
        proposal_lifecycle_checkpoint=_lifecycle_checkpoint(),
    )
    raw: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(raw, dict)
    payload = raw["payload"]
    assert isinstance(payload, dict)
    lifecycle = payload["proposal_lifecycle_checkpoint"]
    assert isinstance(lifecycle, dict)
    registry = lifecycle["registry"]
    assert isinstance(registry, dict)
    registry["active_record_count"] = 0
    _rewrite_checksum_payload(path, raw)

    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.used_fallback
    assert loaded.graph.assembly_count == 0
    assert loaded.proposal_lifecycle_checkpoint.registry.records == ()
    assert not loaded.checksum_verified


def test_schema_v4_outer_checksum_tampering_discards_lifecycle(
    tmp_path: Path,
) -> None:
    path = tmp_path / "tampered.json"
    NDNRABrainStore(path).save(
        build_capacity_limited_graph(),
        proposal_lifecycle_checkpoint=_lifecycle_checkpoint(),
    )
    raw: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(raw, dict)
    raw["checksum"] = "0" * 64
    path.write_text(
        json.dumps(raw, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )

    loaded = NDNRABrainStore(path).load()

    assert loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
    assert loaded.graph.assembly_count == 0
    assert loaded.proposal_lifecycle_checkpoint.registry.records == ()


def test_schema_v4_lifecycle_encoding_is_deterministic(tmp_path: Path) -> None:
    graph = build_capacity_limited_graph()
    lifecycle = _lifecycle_checkpoint()
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"

    NDNRABrainStore(first).save(
        graph,
        proposal_lifecycle_checkpoint=lifecycle,
    )
    NDNRABrainStore(second).save(
        graph,
        proposal_lifecycle_checkpoint=lifecycle,
    )

    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes().isascii()


def test_schema_v4_lifecycle_persistence_has_no_sqlite_or_execution_dependency() -> None:
    source = Path("src/seedmind/research/ndnra/persistence.py").read_text(encoding="utf-8").lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "consolidation_application" not in source
    assert "rollback_consolidation" not in source
    assert ".apply(" not in source
