"""Tests for restart-safe NDNRA proposal lifecycle checkpoint encoding."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    PROPOSAL_LIFECYCLE_SCHEMA,
    PROPOSAL_LIFECYCLE_SCHEMA_VERSION,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalManagementAction,
    ConsolidationProposalManagementRequest,
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
    NDNRAProposalLifecycleCheckpoint,
)

_HEAT = LessonIdentity("reduce_heat", "cooling", 1.0)
_CLEAN = LessonIdentity("remove_dirt", "cleanliness", 1.0)


def _proposal(
    *,
    prefix: str,
    lesson: LessonIdentity,
    proposed_episode: int,
) -> ConsolidationScheduleProposal:
    ledger = ContextualExperienceLedger()
    assemblies = (f"assembly:{prefix}:a", f"assembly:{prefix}:b")
    routes = (f"route:{prefix}:a", f"route:{prefix}:b")
    for index, route_id, transfer_succeeded in (
        (0, routes[0], True),
        (1, routes[1], True),
        (2, routes[0], False),
    ):
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity(
                    "proposal_persistence_test",
                    f"episode:{prefix}:{index}",
                    index,
                ),
                correlation_group_id=f"group:{prefix}:{index}",
                assembly_id=(assemblies[0] if route_id == routes[0] else assemblies[1]),
                route_id=route_id,
                action_code=f"action:{prefix}",
                context=ContextSignature.from_values(
                    active_need_code=lesson.need_code,
                    sensor_values=(float(index),),
                    available_action_codes=(f"action:{prefix}", "wait"),
                ),
                observed_effects=(
                    EffectObservation(
                        lesson.effect_code,
                        lesson.desired_direction,
                        1.0,
                    ),
                ),
                transfer_attempted=True,
                transfer_succeeded=transfer_succeeded,
            )
        )
    decision = ConsolidationSchedulingPolicy(
        first_eligible_episode=proposed_episode,
    ).evaluate(
        ledger=ledger,
        request=ConsolidationScheduleRequest(
            lesson=lesson,
            available_assembly_ids=assemblies,
            available_route_ids=routes,
        ),
        context=ConsolidationSchedulingContext(episode_index=proposed_episode),
    )
    assert decision.proposal is not None
    return decision.proposal


def _review(
    proposal: ConsolidationScheduleProposal,
    *,
    action: ConsolidationProposalReviewAction,
    episode: int,
    reason: str,
    defer_until: int | None = None,
) -> ConsolidationProposalReviewRequest:
    return ConsolidationProposalReviewRequest(
        proposal=proposal,
        action=action,
        decision_episode=episode,
        reviewer_code="human:operator",
        reason_code=reason,
        defer_until_episode=defer_until,
    )


def _managed_registry() -> ConsolidationProposalLifecycleRegistry:
    old_heat = _proposal(
        prefix="heat-old",
        lesson=_HEAT,
        proposed_episode=100,
    )
    new_heat = _proposal(
        prefix="heat-new",
        lesson=_HEAT,
        proposed_episode=130,
    )
    clean = _proposal(
        prefix="clean",
        lesson=_CLEAN,
        proposed_episode=100,
    )
    registry = (
        ConsolidationProposalLifecycleRegistry(maximum_active_records=2)
        .add(old_heat)
        .add(clean)
        .review(
            _review(
                old_heat,
                action=ConsolidationProposalReviewAction.DEFER,
                episode=101,
                reason="collect_more_contexts",
                defer_until=130,
            )
        )
        .manage(
            ConsolidationProposalManagementRequest(
                target_proposal_id=old_heat.proposal_id,
                expected_candidate_id=old_heat.candidate.candidate_id,
                action=ConsolidationProposalManagementAction.REPLACE,
                decision_episode=131,
                reviewer_code="human:operator",
                reason_code="newer_mastery_snapshot",
                replacement_proposal=new_heat,
            )
        )
        .review(
            _review(
                new_heat,
                action=ConsolidationProposalReviewAction.ACCEPT,
                episode=132,
                reason="current_evidence_review_passed",
            )
        )
        .manage(
            ConsolidationProposalManagementRequest(
                target_proposal_id=clean.proposal_id,
                expected_candidate_id=clean.candidate.candidate_id,
                action=ConsolidationProposalManagementAction.EXPIRE,
                decision_episode=133,
                reviewer_code="human:operator",
                reason_code="review_window_closed",
            )
        )
    )
    return registry


def _json_snapshot(
    checkpoint: NDNRAProposalLifecycleCheckpoint,
) -> dict[str, object]:
    raw: object = json.loads(
        json.dumps(
            checkpoint.snapshot(),
            ensure_ascii=True,
            sort_keys=True,
        )
    )
    assert isinstance(raw, dict)
    return raw


def test_empty_checkpoint_round_trips_exactly() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint.empty()

    restored = NDNRAProposalLifecycleCheckpoint.from_snapshot(_json_snapshot(checkpoint))

    assert PROPOSAL_LIFECYCLE_SCHEMA == "seedmind.ndnra.proposal_lifecycle"
    assert PROPOSAL_LIFECYCLE_SCHEMA_VERSION == 1
    assert restored == checkpoint
    assert restored.registry.records == ()
    assert not restored.has_execution_authority


def test_complete_registry_round_trips_exactly() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=_managed_registry())

    restored = NDNRAProposalLifecycleCheckpoint.from_snapshot(_json_snapshot(checkpoint))

    assert restored == checkpoint
    assert restored.snapshot() == checkpoint.snapshot()
    assert len(restored.registry.records) == 3
    assert len(restored.registry.active_records) == 1
    assert restored.registry.maximum_active_records == 2


def test_round_trip_preserves_all_review_and_management_identities() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=_managed_registry())
    restored = NDNRAProposalLifecycleCheckpoint.from_snapshot(_json_snapshot(checkpoint))

    original_records = checkpoint.registry.records
    restored_records = restored.registry.records

    assert tuple(record.proposal.proposal_id for record in restored_records) == tuple(
        record.proposal.proposal_id for record in original_records
    )
    assert tuple(record.proposal.candidate.candidate_id for record in restored_records) == tuple(
        record.proposal.candidate.candidate_id for record in original_records
    )
    assert tuple(
        decision.decision_id
        for record in restored_records
        for decision in record.lifecycle.decisions
    ) == tuple(
        decision.decision_id
        for record in original_records
        for decision in record.lifecycle.decisions
    )
    assert tuple(
        record.management_decision.decision_id
        for record in restored_records
        if record.management_decision is not None
    ) == tuple(
        record.management_decision.decision_id
        for record in original_records
        if record.management_decision is not None
    )
    assert tuple(
        decision.reviewer_code
        for record in restored_records
        for decision in record.lifecycle.decisions
    ) == ("human:operator", "human:operator")
    assert tuple(
        decision.reason_code
        for record in restored_records
        for decision in record.lifecycle.decisions
    ) == ("collect_more_contexts", "current_evidence_review_passed")


def test_checkpoint_encoding_is_deterministic_and_ascii() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=_managed_registry())

    first = json.dumps(
        checkpoint.snapshot(),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")
    second = json.dumps(
        checkpoint.snapshot(),
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")

    assert first == second
    assert first.isascii()


def test_checkpoint_rejects_incompatible_schema_or_version() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint.empty()
    wrong_schema = _json_snapshot(checkpoint)
    wrong_schema["schema"] = "seedmind.ndnra.other"
    wrong_version = _json_snapshot(checkpoint)
    wrong_version["schema_version"] = 2

    with pytest.raises(ValueError, match="schema is incompatible"):
        NDNRAProposalLifecycleCheckpoint.from_snapshot(wrong_schema)
    with pytest.raises(ValueError, match="version is incompatible"):
        NDNRAProposalLifecycleCheckpoint.from_snapshot(wrong_version)


def test_checkpoint_rejects_tampered_review_identity_or_reason() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=_managed_registry())
    bad_identity = copy.deepcopy(_json_snapshot(checkpoint))
    records = bad_identity["registry"]
    assert isinstance(records, dict)
    record_list = records["records"]
    assert isinstance(record_list, list)
    old_record = record_list[0]
    assert isinstance(old_record, dict)
    lifecycle = old_record["lifecycle"]
    assert isinstance(lifecycle, dict)
    decisions = lifecycle["decisions"]
    assert isinstance(decisions, list)
    first_decision = decisions[0]
    assert isinstance(first_decision, dict)
    first_decision["decision_id"] = "consolidation-review:tampered"

    with pytest.raises(ValueError, match="review decision identity"):
        NDNRAProposalLifecycleCheckpoint.from_snapshot(bad_identity)

    bad_reason = copy.deepcopy(_json_snapshot(checkpoint))
    registry_values = bad_reason["registry"]
    assert isinstance(registry_values, dict)
    stored_records = registry_values["records"]
    assert isinstance(stored_records, list)
    stored_record = stored_records[0]
    assert isinstance(stored_record, dict)
    stored_lifecycle = stored_record["lifecycle"]
    assert isinstance(stored_lifecycle, dict)
    stored_decisions = stored_lifecycle["decisions"]
    assert isinstance(stored_decisions, list)
    stored_decision = stored_decisions[0]
    assert isinstance(stored_decision, dict)
    stored_decision["reason_code"] = "tampered_reason"

    with pytest.raises(ValueError, match="review decision identity"):
        NDNRAProposalLifecycleCheckpoint.from_snapshot(bad_reason)


def test_checkpoint_rejects_tampered_management_identity() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=_managed_registry())
    snapshot = copy.deepcopy(_json_snapshot(checkpoint))
    registry_values = snapshot["registry"]
    assert isinstance(registry_values, dict)
    records = registry_values["records"]
    assert isinstance(records, list)
    old_record = records[0]
    assert isinstance(old_record, dict)
    management = old_record["management_decision"]
    assert isinstance(management, dict)
    management["decision_id"] = "consolidation-management:tampered"

    with pytest.raises(ValueError, match="management decision identity"):
        NDNRAProposalLifecycleCheckpoint.from_snapshot(snapshot)


def test_checkpoint_rejects_missing_replacement_record() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=_managed_registry())
    snapshot = copy.deepcopy(_json_snapshot(checkpoint))
    registry_values = snapshot["registry"]
    assert isinstance(registry_values, dict)
    records = registry_values["records"]
    assert isinstance(records, list)
    records.pop()
    registry_values["active_record_count"] = 0

    with pytest.raises(ValueError, match="exact retained record"):
        NDNRAProposalLifecycleCheckpoint.from_snapshot(snapshot)


def test_checkpoint_rejects_derived_count_and_authority_tampering() -> None:
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=_managed_registry())
    wrong_count = copy.deepcopy(_json_snapshot(checkpoint))
    registry_values = wrong_count["registry"]
    assert isinstance(registry_values, dict)
    registry_values["active_record_count"] = 0

    with pytest.raises(ValueError, match="active lifecycle count"):
        NDNRAProposalLifecycleCheckpoint.from_snapshot(wrong_count)

    authority = copy.deepcopy(_json_snapshot(checkpoint))
    authority["has_execution_authority"] = True
    with pytest.raises(ValueError, match="never have execution authority"):
        NDNRAProposalLifecycleCheckpoint.from_snapshot(authority)


def test_checkpoint_constructor_rejects_unretained_replacement() -> None:
    registry = _managed_registry()
    old_record = registry.records[0]
    clean_record = registry.records[1]
    broken = ConsolidationProposalLifecycleRegistry(
        records=(old_record, clean_record),
        maximum_active_records=2,
    )

    with pytest.raises(ValueError, match="exact retained record"):
        NDNRAProposalLifecycleCheckpoint(registry=broken)


def test_checkpoint_codec_has_no_file_sql_execution_or_integration_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_proposal_persistence.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "pathlib" not in source
    assert "import os" not in source
    assert ".open(" not in source
    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "consolidation_application" not in source
    assert "rollback_consolidation" not in source
    assert ".apply(" not in source
    assert "seedmind.integration" not in source
