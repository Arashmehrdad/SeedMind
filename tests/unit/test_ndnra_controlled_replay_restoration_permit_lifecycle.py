"""Tests for immutable controlled replay/restoration permit lifecycles."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra.controlled_replay_restoration_approval import (
    ControlledReplayRestorationApprovalPolicy,
    ControlledReplayRestorationApprovalRequest,
    ControlledReplayRestorationEvidence,
    ControlledReplayRestorationOperation,
    ControlledReplayRestorationPermit,
    ControlledReplayRestorationTarget,
)
from seedmind.research.ndnra.controlled_replay_restoration_permit_lifecycle import (
    ControlledReplayRestorationPermitLifecycleAction,
    ControlledReplayRestorationPermitLifecycleRecord,
    ControlledReplayRestorationPermitLifecycleRegistry,
    ControlledReplayRestorationPermitLifecycleStatus,
    ControlledReplayRestorationPermitTransitionRequest,
)

_CURRENT_CHECKSUM = "a" * 64
_ARCHIVE_CHECKSUM = "b" * 64
_EVIDENCE_IDS = (
    "evidence:retention:ball",
    "evidence:retention:navigation",
)


def _evidence() -> ControlledReplayRestorationEvidence:
    return ControlledReplayRestorationEvidence(
        captured_episode=200,
        current_checkpoint_id="checkpoint:current",
        current_checkpoint_checksum=_CURRENT_CHECKSUM,
        available_checkpoint_checksums=(
            ("checkpoint:archive", _ARCHIVE_CHECKSUM),
            ("checkpoint:current", _CURRENT_CHECKSUM),
        ),
        available_evidence_ids=_EVIDENCE_IDS,
    )


def _target(
    operation: ControlledReplayRestorationOperation,
) -> ControlledReplayRestorationTarget:
    if operation is ControlledReplayRestorationOperation.RETENTION_REPLAY:
        return ControlledReplayRestorationTarget(
            operation=operation,
            target_id="replay-target:retention-suite-v1",
            source_checkpoint_id="checkpoint:current",
            source_checkpoint_checksum=_CURRENT_CHECKSUM,
            expected_current_checkpoint_id="checkpoint:current",
            expected_current_checkpoint_checksum=_CURRENT_CHECKSUM,
            source_evidence_ids=_EVIDENCE_IDS,
            maximum_work_items=32,
        )
    return ControlledReplayRestorationTarget(
        operation=operation,
        target_id="restoration-target:archive-v1",
        source_checkpoint_id="checkpoint:archive",
        source_checkpoint_checksum=_ARCHIVE_CHECKSUM,
        expected_current_checkpoint_id="checkpoint:current",
        expected_current_checkpoint_checksum=_CURRENT_CHECKSUM,
        source_evidence_ids=_EVIDENCE_IDS,
        maximum_work_items=0,
    )


def _permit(
    operation: ControlledReplayRestorationOperation = (
        ControlledReplayRestorationOperation.RETENTION_REPLAY
    ),
    *,
    reason_code: str = "approve_bounded_controlled_operation",
) -> ControlledReplayRestorationPermit:
    evidence = _evidence()
    target = _target(operation)
    return ControlledReplayRestorationApprovalPolicy().evaluate(
        request=ControlledReplayRestorationApprovalRequest(
            target=target,
            expected_evidence_state_id=evidence.evidence_state_id,
            approval_episode=200,
            expires_after_episode=201,
            approver_code="human:operator",
            reason_code=reason_code,
        ),
        evidence=evidence,
    )


def _request(
    permit: ControlledReplayRestorationPermit,
    action: ControlledReplayRestorationPermitLifecycleAction,
    *,
    decision_episode: int,
    actor_code: str = "human:operator",
    reason_code: str = "permit_transition",
    consumption_reference_code: str | None = None,
) -> ControlledReplayRestorationPermitTransitionRequest:
    target = permit.target
    return ControlledReplayRestorationPermitTransitionRequest(
        target_permit_id=permit.permit_id,
        expected_operation=target.operation,
        expected_target_id=target.target_id,
        expected_source_checkpoint_id=target.source_checkpoint_id,
        expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
        expected_current_checkpoint_id=target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=(target.expected_current_checkpoint_checksum),
        expected_evidence_state_id=permit.evidence.evidence_state_id,
        action=action,
        decision_episode=decision_episode,
        actor_code=actor_code,
        reason_code=reason_code,
        consumption_reference_code=consumption_reference_code,
    )


def test_issued_record_is_immutable_and_non_authoritative() -> None:
    permit = _permit()

    record = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)

    assert record.permit == permit
    assert record.status is ControlledReplayRestorationPermitLifecycleStatus.ISSUED
    assert record.decisions == ()
    assert not record.is_terminal
    assert record.consumption_count == 0
    assert not record.has_replay_authority
    assert not record.has_restoration_authority
    assert not record.has_cognitive_authority
    assert not record.has_production_action_authority
    assert permit.consumed is False
    assert permit.operation_count == 0


def test_cancel_transition_is_terminal_and_preserves_issued_record() -> None:
    permit = _permit()
    issued = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)

    cancelled = issued.transition(
        _request(
            permit,
            ControlledReplayRestorationPermitLifecycleAction.CANCEL,
            decision_episode=201,
            reason_code="human_cancelled_before_operation",
        )
    )

    assert issued.status is ControlledReplayRestorationPermitLifecycleStatus.ISSUED
    assert issued.decisions == ()
    assert cancelled.status is ControlledReplayRestorationPermitLifecycleStatus.CANCELLED
    assert cancelled.is_terminal
    assert cancelled.consumption_count == 0
    assert len(cancelled.decisions) == 1
    assert cancelled.decisions[0].consumption_reference_code is None


def test_consume_transition_requires_operation_actor_and_receipt_reference() -> None:
    permit = _permit()
    issued = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)

    with pytest.raises(ValueError, match="requires consumption_reference_code"):
        _request(
            permit,
            ControlledReplayRestorationPermitLifecycleAction.CONSUME,
            decision_episode=201,
            actor_code="operation:retention_replay",
        )
    with pytest.raises(ValueError, match="requires an operation actor"):
        _request(
            permit,
            ControlledReplayRestorationPermitLifecycleAction.CONSUME,
            decision_episode=201,
            actor_code="human:operator",
            consumption_reference_code="replay-receipt:001",
        )

    consumed = issued.transition(
        _request(
            permit,
            ControlledReplayRestorationPermitLifecycleAction.CONSUME,
            decision_episode=201,
            actor_code="operation:retention_replay",
            reason_code="bounded_replay_recorded",
            consumption_reference_code="replay-receipt:001",
        )
    )

    assert consumed.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED
    assert consumed.consumption_count == 1
    assert consumed.decisions[0].consumption_reference_code == "replay-receipt:001"
    assert permit.consumed is False
    assert permit.operation_count == 0
    with pytest.raises(ValueError, match="already terminal"):
        consumed.transition(
            _request(
                permit,
                ControlledReplayRestorationPermitLifecycleAction.CONSUME,
                decision_episode=201,
                actor_code="operation:retention_replay",
                consumption_reference_code="replay-receipt:002",
            )
        )


def test_expiry_requires_episode_after_validity_window() -> None:
    permit = _permit()
    issued = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)

    with pytest.raises(ValueError, match="only after its validity window"):
        issued.transition(
            _request(
                permit,
                ControlledReplayRestorationPermitLifecycleAction.EXPIRE,
                decision_episode=201,
            )
        )

    expired = issued.transition(
        _request(
            permit,
            ControlledReplayRestorationPermitLifecycleAction.EXPIRE,
            decision_episode=202,
            actor_code="caller:episode_boundary",
            reason_code="permit_window_elapsed",
        )
    )

    assert expired.status is ControlledReplayRestorationPermitLifecycleStatus.EXPIRED
    assert expired.is_terminal
    assert expired.consumption_count == 0


def test_cancel_or_consume_after_expiry_window_is_rejected() -> None:
    permit = _permit()
    issued = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)

    with pytest.raises(ValueError, match="requires an unexpired permit"):
        issued.transition(
            _request(
                permit,
                ControlledReplayRestorationPermitLifecycleAction.CANCEL,
                decision_episode=202,
            )
        )
    with pytest.raises(ValueError, match="requires an unexpired permit"):
        issued.transition(
            _request(
                permit,
                ControlledReplayRestorationPermitLifecycleAction.CONSUME,
                decision_episode=202,
                actor_code="operation:retention_replay",
                consumption_reference_code="replay-receipt:late",
            )
        )


def test_transition_must_follow_permit_issuance() -> None:
    permit = _permit()
    issued = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)

    with pytest.raises(ValueError, match="must follow permit issuance"):
        issued.transition(
            _request(
                permit,
                ControlledReplayRestorationPermitLifecycleAction.CANCEL,
                decision_episode=200,
            )
        )


def test_nonconsume_transitions_reject_consumption_reference() -> None:
    permit = _permit()

    with pytest.raises(ValueError, match="only consume transition"):
        _request(
            permit,
            ControlledReplayRestorationPermitLifecycleAction.CANCEL,
            decision_episode=201,
            consumption_reference_code="receipt:not_allowed",
        )


def test_transition_requires_every_exact_authority_identity() -> None:
    permit = _permit()
    issued = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)
    request = _request(
        permit,
        ControlledReplayRestorationPermitLifecycleAction.CANCEL,
        decision_episode=201,
    )

    cases = (
        (replace(request, target_permit_id="permit:wrong"), "different permit"),
        (
            replace(
                request,
                expected_operation=(ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION),
            ),
            "different operation",
        ),
        (replace(request, expected_target_id="replay-target:wrong"), "operation target"),
        (
            replace(request, expected_source_checkpoint_id="checkpoint:wrong"),
            "source checkpoint",
        ),
        (
            replace(request, expected_source_checkpoint_checksum="c" * 64),
            "source checkpoint checksum",
        ),
        (
            replace(request, expected_current_checkpoint_id="checkpoint:wrong"),
            "current checkpoint",
        ),
        (
            replace(request, expected_current_checkpoint_checksum="c" * 64),
            "current checkpoint checksum",
        ),
        (
            replace(
                request,
                expected_evidence_state_id=("controlled-replay-restoration-evidence:wrong"),
            ),
            "different approval evidence",
        ),
    )
    for changed, message in cases:
        with pytest.raises(ValueError, match=message):
            issued.transition(changed)


def test_terminal_records_reject_all_conflicting_transitions() -> None:
    permit = _permit()
    cancelled = ControlledReplayRestorationPermitLifecycleRecord.issued(permit).transition(
        _request(
            permit,
            ControlledReplayRestorationPermitLifecycleAction.CANCEL,
            decision_episode=201,
        )
    )

    for action, episode in (
        (ControlledReplayRestorationPermitLifecycleAction.CANCEL, 201),
        (ControlledReplayRestorationPermitLifecycleAction.CONSUME, 201),
        (ControlledReplayRestorationPermitLifecycleAction.EXPIRE, 202),
    ):
        with pytest.raises(ValueError, match="already terminal"):
            cancelled.transition(
                _request(
                    permit,
                    action,
                    decision_episode=episode,
                    actor_code=(
                        "operation:retention_replay"
                        if action is ControlledReplayRestorationPermitLifecycleAction.CONSUME
                        else "human:operator"
                    ),
                    consumption_reference_code=(
                        "replay-receipt:blocked"
                        if action is ControlledReplayRestorationPermitLifecycleAction.CONSUME
                        else None
                    ),
                )
            )


def test_transition_identity_is_deterministic_and_tampering_is_rejected() -> None:
    permit = _permit()
    issued = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)
    request = _request(
        permit,
        ControlledReplayRestorationPermitLifecycleAction.CONSUME,
        decision_episode=201,
        actor_code="operation:retention_replay",
        reason_code="bounded_replay_recorded",
        consumption_reference_code="replay-receipt:001",
    )

    first = issued.transition(request)
    second = issued.transition(request)
    decision = first.decisions[0]

    assert first == second
    assert decision.decision_id == second.decisions[0].decision_id
    assert decision.decision_id.startswith("controlled-operation-permit-transition:")
    assert str(decision.snapshot()).isascii()
    with pytest.raises(ValueError, match="identity is inconsistent"):
        replace(decision, decision_id="controlled-operation-permit-transition:tampered")


def test_registry_enforces_unique_permits_and_tracks_operation_counts() -> None:
    replay = _permit()
    restoration = _permit(
        ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION,
        reason_code="approve_exact_checkpoint_restoration",
    )
    registry = ControlledReplayRestorationPermitLifecycleRegistry().add(replay).add(restoration)
    before_restoration = registry.record_for(restoration.permit_id)

    replay_consumed = registry.transition(
        _request(
            replay,
            ControlledReplayRestorationPermitLifecycleAction.CONSUME,
            decision_episode=201,
            actor_code="operation:retention_replay",
            consumption_reference_code="replay-receipt:001",
        )
    )
    all_consumed = replay_consumed.transition(
        _request(
            restoration,
            ControlledReplayRestorationPermitLifecycleAction.CONSUME,
            decision_episode=201,
            actor_code="operation:checkpoint_restoration",
            consumption_reference_code="restoration-receipt:001",
        )
    )

    assert registry.consumption_count == 0
    assert replay_consumed.consumption_count == 1
    assert replay_consumed.replay_consumption_count == 1
    assert replay_consumed.restoration_consumption_count == 0
    assert replay_consumed.record_for(restoration.permit_id) == before_restoration
    assert all_consumed.consumption_count == 2
    assert all_consumed.replay_consumption_count == 1
    assert all_consumed.restoration_consumption_count == 1
    assert not all_consumed.has_replay_authority
    assert not all_consumed.has_restoration_authority
    with pytest.raises(ValueError, match="already exists"):
        registry.add(replay)
    with pytest.raises(ValueError, match="not present"):
        registry.record_for("permit:unknown")


def test_reconstructed_record_rejects_mismatched_status_or_permit() -> None:
    permit = _permit()
    other = _permit(reason_code="approve_after_additional_human_check")
    consumed = ControlledReplayRestorationPermitLifecycleRecord.issued(permit).transition(
        _request(
            permit,
            ControlledReplayRestorationPermitLifecycleAction.CONSUME,
            decision_episode=201,
            actor_code="operation:retention_replay",
            consumption_reference_code="replay-receipt:001",
        )
    )

    with pytest.raises(ValueError, match="status must match"):
        ControlledReplayRestorationPermitLifecycleRecord(
            permit=permit,
            status=ControlledReplayRestorationPermitLifecycleStatus.CANCELLED,
            decisions=consumed.decisions,
        )
    with pytest.raises(ValueError, match="different permit"):
        ControlledReplayRestorationPermitLifecycleRecord(
            permit=other,
            status=ControlledReplayRestorationPermitLifecycleStatus.CONSUMED,
            decisions=consumed.decisions,
        )


def test_lifecycle_objects_reject_all_authority_bearing_state() -> None:
    permit = _permit()
    record = ControlledReplayRestorationPermitLifecycleRecord.issued(permit)
    registry = ControlledReplayRestorationPermitLifecycleRegistry().add(permit)

    with pytest.raises(ValueError, match="cannot execute replay"):
        replace(record, has_replay_authority=True)
    with pytest.raises(ValueError, match="cannot restore checkpoints"):
        replace(record, has_restoration_authority=True)
    with pytest.raises(ValueError, match="cannot perform cognition"):
        replace(registry, has_cognitive_authority=True)
    with pytest.raises(ValueError, match="cannot select production actions"):
        replace(registry, has_production_action_authority=True)


def test_lifecycle_has_no_operation_persistence_timer_or_sql_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/controlled_replay_restoration_permit_lifecycle.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert ".apply(" not in source
    assert ".restore_snapshot(" not in source
    assert "rollback_consolidation" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "seedmind.integration" not in source
