"""Tests for bounded NDNRA consolidation proposal lifecycle management."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationProposalDisposition,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalManagedRecord,
    ConsolidationProposalManagementAction,
    ConsolidationProposalManagementDecision,
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
        assembly_id = assemblies[0] if route_id == routes[0] else assemblies[1]
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity(
                    "management_test",
                    f"episode:{prefix}:{index}",
                    index,
                ),
                correlation_group_id=f"group:{prefix}:{index}",
                assembly_id=assembly_id,
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
    schedule = ConsolidationSchedulingPolicy(
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
    assert schedule.proposal is not None
    return schedule.proposal


def _review_request(
    proposal: ConsolidationScheduleProposal,
    *,
    action: ConsolidationProposalReviewAction,
    decision_episode: int,
    reason_code: str,
    defer_until_episode: int | None = None,
) -> ConsolidationProposalReviewRequest:
    return ConsolidationProposalReviewRequest(
        proposal=proposal,
        action=action,
        decision_episode=decision_episode,
        reviewer_code="human:operator",
        reason_code=reason_code,
        defer_until_episode=defer_until_episode,
    )


def _management_request(
    proposal: ConsolidationScheduleProposal,
    *,
    action: ConsolidationProposalManagementAction,
    decision_episode: int,
    reason_code: str,
    replacement_proposal: ConsolidationScheduleProposal | None = None,
    expected_candidate_id: str | None = None,
) -> ConsolidationProposalManagementRequest:
    return ConsolidationProposalManagementRequest(
        target_proposal_id=proposal.proposal_id,
        expected_candidate_id=(
            proposal.candidate.candidate_id
            if expected_candidate_id is None
            else expected_candidate_id
        ),
        action=action,
        decision_episode=decision_episode,
        reviewer_code="human:operator",
        reason_code=reason_code,
        replacement_proposal=replacement_proposal,
    )


def test_registry_adds_pending_record_with_bounded_capacity() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    clean = _proposal(prefix="clean", lesson=_CLEAN, proposed_episode=100)
    empty = ConsolidationProposalLifecycleRegistry(maximum_active_records=1)

    registry = empty.add(heat)

    assert empty.records == ()
    assert len(registry.records) == 1
    assert registry.active_records[0].proposal is heat
    assert (
        registry.active_records[0].lifecycle.status is ConsolidationProposalLifecycleStatus.PENDING
    )
    assert not registry.has_execution_authority
    with pytest.raises(ValueError, match="capacity reached"):
        registry.add(clean)


def test_rejection_releases_capacity_but_preserves_record() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    clean = _proposal(prefix="clean", lesson=_CLEAN, proposed_episode=100)
    registry = ConsolidationProposalLifecycleRegistry(maximum_active_records=1).add(heat)

    rejected = registry.review(
        _review_request(
            heat,
            action=ConsolidationProposalReviewAction.REJECT,
            decision_episode=101,
            reason_code="insufficient_evidence",
        )
    )
    expanded = rejected.add(clean)

    assert len(rejected.active_records) == 0
    assert (
        rejected.record_for(heat.proposal_id).lifecycle.status
        is ConsolidationProposalLifecycleStatus.REJECTED
    )
    assert len(expanded.records) == 2
    assert expanded.active_records[0].proposal is clean


def test_accepted_record_continues_to_consume_capacity() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    clean = _proposal(prefix="clean", lesson=_CLEAN, proposed_episode=100)
    accepted = (
        ConsolidationProposalLifecycleRegistry(maximum_active_records=1)
        .add(heat)
        .review(
            _review_request(
                heat,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=101,
                reason_code="evidence_review_passed",
            )
        )
    )

    assert len(accepted.active_records) == 1
    with pytest.raises(ValueError, match="capacity reached"):
        accepted.add(clean)


def test_deferred_record_can_be_reviewed_when_due_through_registry() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    deferred = (
        ConsolidationProposalLifecycleRegistry()
        .add(heat)
        .review(
            _review_request(
                heat,
                action=ConsolidationProposalReviewAction.DEFER,
                decision_episode=101,
                reason_code="collect_more_contexts",
                defer_until_episode=120,
            )
        )
    )

    accepted = deferred.review(
        _review_request(
            heat,
            action=ConsolidationProposalReviewAction.ACCEPT,
            decision_episode=120,
            reason_code="additional_evidence_passed",
        )
    )

    assert (
        deferred.record_for(heat.proposal_id).lifecycle.status
        is ConsolidationProposalLifecycleStatus.DEFERRED
    )
    accepted_record = accepted.record_for(heat.proposal_id)
    assert accepted_record.lifecycle.status is ConsolidationProposalLifecycleStatus.ACCEPTED
    assert len(accepted_record.lifecycle.decisions) == 2


def test_expiry_is_deterministic_preserves_history_and_releases_capacity() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    clean = _proposal(prefix="clean", lesson=_CLEAN, proposed_episode=100)
    registry = ConsolidationProposalLifecycleRegistry(maximum_active_records=1).add(heat)
    request = _management_request(
        heat,
        action=ConsolidationProposalManagementAction.EXPIRE,
        decision_episode=101,
        reason_code="evidence_window_closed",
    )

    first = registry.manage(request)
    second = registry.manage(request)
    expired = first.record_for(heat.proposal_id)
    expanded = first.add(clean)

    assert first == second
    assert expired.disposition is ConsolidationProposalDisposition.EXPIRED
    assert expired.management_decision is not None
    assert expired.management_decision.action is ConsolidationProposalManagementAction.EXPIRE
    assert expired.lifecycle.proposal is heat
    assert not expired.is_active
    assert not expired.management_decision.has_execution_authority
    assert len(expanded.records) == 2


def test_replacement_preserves_old_and_new_proposals_with_one_active_record() -> None:
    old = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    new = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=130)
    registry = ConsolidationProposalLifecycleRegistry(maximum_active_records=1).add(old)

    replaced = registry.manage(
        _management_request(
            old,
            action=ConsolidationProposalManagementAction.REPLACE,
            decision_episode=131,
            reason_code="newer_mastery_snapshot",
            replacement_proposal=new,
        )
    )

    old_record = replaced.record_for(old.proposal_id)
    new_record = replaced.record_for(new.proposal_id)
    assert len(replaced.records) == 2
    assert len(replaced.active_records) == 1
    assert old_record.disposition is ConsolidationProposalDisposition.REPLACED
    assert old_record.management_decision is not None
    assert old_record.management_decision.replacement_proposal is new
    assert not old_record.is_active
    assert new_record.disposition is ConsolidationProposalDisposition.ACTIVE
    assert new_record.lifecycle.status is ConsolidationProposalLifecycleStatus.PENDING
    assert new_record.is_active
    assert old_record.proposal.proposal_id != new_record.proposal.proposal_id


def test_replacement_rejects_wrong_lesson_old_or_future_proposal() -> None:
    old = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    wrong_lesson = _proposal(prefix="clean", lesson=_CLEAN, proposed_episode=130)
    older = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=90)
    future = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=140)
    registry = ConsolidationProposalLifecycleRegistry().add(old)

    with pytest.raises(ValueError, match="same lesson"):
        registry.manage(
            _management_request(
                old,
                action=ConsolidationProposalManagementAction.REPLACE,
                decision_episode=131,
                reason_code="wrong_lesson",
                replacement_proposal=wrong_lesson,
            )
        )
    with pytest.raises(ValueError, match="newer"):
        registry.manage(
            _management_request(
                old,
                action=ConsolidationProposalManagementAction.REPLACE,
                decision_episode=131,
                reason_code="older_proposal",
                replacement_proposal=older,
            )
        )
    with pytest.raises(ValueError, match="after management decision"):
        registry.manage(
            _management_request(
                old,
                action=ConsolidationProposalManagementAction.REPLACE,
                decision_episode=131,
                reason_code="future_proposal",
                replacement_proposal=future,
            )
        )


def test_registry_rejects_stale_target_and_candidate_mismatch() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    registry = ConsolidationProposalLifecycleRegistry().add(heat)

    with pytest.raises(ValueError, match="stale proposal identity"):
        registry.manage(
            ConsolidationProposalManagementRequest(
                target_proposal_id="consolidation-schedule:missing",
                expected_candidate_id=heat.candidate.candidate_id,
                action=ConsolidationProposalManagementAction.EXPIRE,
                decision_episode=101,
                reviewer_code="human:operator",
                reason_code="missing_target",
            )
        )
    with pytest.raises(ValueError, match="candidate identity mismatch"):
        registry.manage(
            _management_request(
                heat,
                action=ConsolidationProposalManagementAction.EXPIRE,
                decision_episode=101,
                reason_code="stale_candidate_view",
                expected_candidate_id="consolidation:wrong-candidate",
            )
        )


def test_registry_rejects_management_of_closed_record() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    expired = (
        ConsolidationProposalLifecycleRegistry()
        .add(heat)
        .manage(
            _management_request(
                heat,
                action=ConsolidationProposalManagementAction.EXPIRE,
                decision_episode=101,
                reason_code="evidence_window_closed",
            )
        )
    )

    with pytest.raises(ValueError, match="not active"):
        expired.manage(
            _management_request(
                heat,
                action=ConsolidationProposalManagementAction.EXPIRE,
                decision_episode=102,
                reason_code="duplicate_expiry",
            )
        )
    with pytest.raises(ValueError, match="not active"):
        expired.review(
            _review_request(
                heat,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=102,
                reason_code="closed_review",
            )
        )


def test_management_must_follow_latest_review_episode() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    deferred = (
        ConsolidationProposalLifecycleRegistry()
        .add(heat)
        .review(
            _review_request(
                heat,
                action=ConsolidationProposalReviewAction.DEFER,
                decision_episode=110,
                reason_code="collect_more_contexts",
                defer_until_episode=120,
            )
        )
    )

    with pytest.raises(ValueError, match="follow lifecycle history"):
        deferred.manage(
            _management_request(
                heat,
                action=ConsolidationProposalManagementAction.EXPIRE,
                decision_episode=110,
                reason_code="ambiguous_order",
            )
        )


def test_registry_rejects_duplicate_proposal_and_active_lesson() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    newer_heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=130)
    registry = ConsolidationProposalLifecycleRegistry(maximum_active_records=2).add(heat)

    with pytest.raises(ValueError, match="already exists"):
        registry.add(heat)
    with pytest.raises(ValueError, match="already exists for this lesson"):
        registry.add(newer_heat)


def test_management_request_and_decision_validate_replacement_contract() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    newer = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=130)

    with pytest.raises(ValueError, match="requires replacement_proposal"):
        _management_request(
            heat,
            action=ConsolidationProposalManagementAction.REPLACE,
            decision_episode=131,
            reason_code="missing_replacement",
        )
    with pytest.raises(ValueError, match="only replacement action"):
        _management_request(
            heat,
            action=ConsolidationProposalManagementAction.EXPIRE,
            decision_episode=131,
            reason_code="unexpected_replacement",
            replacement_proposal=newer,
        )

    with pytest.raises(ValueError, match="never have execution authority"):
        ConsolidationProposalManagementDecision(
            decision_id="consolidation-management:test",
            target_proposal_id=heat.proposal_id,
            target_candidate_id=heat.candidate.candidate_id,
            action=ConsolidationProposalManagementAction.EXPIRE,
            disposition=ConsolidationProposalDisposition.EXPIRED,
            decision_episode=131,
            reviewer_code="human:operator",
            reason_code="forbidden_authority",
            has_execution_authority=True,
        )


def test_registry_snapshot_is_ascii_and_preserves_archived_records() -> None:
    old = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)
    new = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=130)
    replaced = (
        ConsolidationProposalLifecycleRegistry()
        .add(old)
        .manage(
            _management_request(
                old,
                action=ConsolidationProposalManagementAction.REPLACE,
                decision_episode=131,
                reason_code="newer_mastery_snapshot",
                replacement_proposal=new,
            )
        )
    )

    snapshot = replaced.snapshot()

    assert snapshot["active_record_count"] == 1
    assert snapshot["records"] == tuple(record.snapshot() for record in replaced.records)
    assert snapshot["has_execution_authority"] is False
    assert str(snapshot).isascii()


def test_managed_record_rejects_execution_authority() -> None:
    heat = _proposal(prefix="heat", lesson=_HEAT, proposed_episode=100)

    with pytest.raises(ValueError, match="never have execution authority"):
        ConsolidationProposalManagedRecord(
            lifecycle=ConsolidationProposalManagedRecord.pending(heat).lifecycle,
            has_execution_authority=True,
        )


def test_management_module_has_no_execution_persistence_timer_or_sql_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_proposal_management.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "consolidation_application" not in source
    assert "rollback_consolidation" not in source
    assert ".apply(" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert "seedmind.integration" not in source
