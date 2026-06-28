"""Tests for human-approved controlled replay and restoration permits."""

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

_CURRENT_CHECKSUM = "a" * 64
_ARCHIVE_CHECKSUM = "b" * 64
_EVIDENCE_IDS = (
    "evidence:retention:ball",
    "evidence:retention:navigation",
)


def _evidence(
    *,
    captured_episode: int = 200,
    current_checkpoint_id: str = "checkpoint:current",
    current_checkpoint_checksum: str = _CURRENT_CHECKSUM,
    checksum_verified: bool = True,
    used_fallback: bool = False,
) -> ControlledReplayRestorationEvidence:
    checkpoints = tuple(
        sorted(
            (
                ("checkpoint:archive", _ARCHIVE_CHECKSUM),
                (current_checkpoint_id, current_checkpoint_checksum),
            )
        )
    )
    return ControlledReplayRestorationEvidence(
        captured_episode=captured_episode,
        current_checkpoint_id=current_checkpoint_id,
        current_checkpoint_checksum=current_checkpoint_checksum,
        available_checkpoint_checksums=checkpoints,
        available_evidence_ids=_EVIDENCE_IDS,
        checksum_verified=checksum_verified,
        used_fallback=used_fallback,
    )


def _replay_target() -> ControlledReplayRestorationTarget:
    return ControlledReplayRestorationTarget(
        operation=ControlledReplayRestorationOperation.RETENTION_REPLAY,
        target_id="replay-target:retention-suite-v1",
        source_checkpoint_id="checkpoint:current",
        source_checkpoint_checksum=_CURRENT_CHECKSUM,
        expected_current_checkpoint_id="checkpoint:current",
        expected_current_checkpoint_checksum=_CURRENT_CHECKSUM,
        source_evidence_ids=_EVIDENCE_IDS,
        maximum_work_items=32,
    )


def _restoration_target() -> ControlledReplayRestorationTarget:
    return ControlledReplayRestorationTarget(
        operation=ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION,
        target_id="restoration-target:archive-v1",
        source_checkpoint_id="checkpoint:archive",
        source_checkpoint_checksum=_ARCHIVE_CHECKSUM,
        expected_current_checkpoint_id="checkpoint:current",
        expected_current_checkpoint_checksum=_CURRENT_CHECKSUM,
        source_evidence_ids=_EVIDENCE_IDS,
        maximum_work_items=0,
    )


def _request(
    target: ControlledReplayRestorationTarget,
    evidence: ControlledReplayRestorationEvidence,
    *,
    approval_episode: int = 200,
    expires_after_episode: int = 201,
    approver_code: str = "human:operator",
    reason_code: str = "approve_bounded_controlled_operation",
) -> ControlledReplayRestorationApprovalRequest:
    return ControlledReplayRestorationApprovalRequest(
        target=target,
        expected_evidence_state_id=evidence.evidence_state_id,
        approval_episode=approval_episode,
        expires_after_episode=expires_after_episode,
        approver_code=approver_code,
        reason_code=reason_code,
    )


def _permit(
    target: ControlledReplayRestorationTarget,
    evidence: ControlledReplayRestorationEvidence,
    *,
    request: ControlledReplayRestorationApprovalRequest | None = None,
) -> ControlledReplayRestorationPermit:
    return ControlledReplayRestorationApprovalPolicy().evaluate(
        request=_request(target, evidence) if request is None else request,
        evidence=evidence,
    )


def test_replay_permit_is_deterministic_bounded_and_non_executable() -> None:
    evidence = _evidence()
    target = _replay_target()
    before = evidence.snapshot()

    first = _permit(target, evidence)
    second = _permit(target, evidence)

    assert first == second
    assert first.permit_id == second.permit_id
    assert first.permit_id.startswith("controlled-replay-restoration-permit:")
    assert first.target == target
    assert first.evidence == evidence
    assert first.authorizes_one_operation
    assert first.single_use
    assert not first.consumed
    assert first.operation_count == 0
    assert not first.has_direct_replay_authority
    assert not first.has_direct_restoration_authority
    assert not first.has_production_action_authority
    assert not first.has_cognitive_authority
    assert evidence.snapshot() == before
    assert str(first.snapshot()).isascii()


def test_restoration_permit_binds_exact_complete_checkpoint_envelope() -> None:
    evidence = _evidence()
    target = _restoration_target()

    permit = _permit(target, evidence)

    assert permit.target.operation is (ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION)
    assert permit.target.source_checkpoint_id == "checkpoint:archive"
    assert permit.target.source_checkpoint_checksum == _ARCHIVE_CHECKSUM
    assert permit.target.expected_current_checkpoint_id == "checkpoint:current"
    assert permit.target.expected_current_checkpoint_checksum == _CURRENT_CHECKSUM
    assert permit.target.requires_complete_envelope
    assert not permit.target.allows_partial_restoration
    assert permit.target.maximum_work_items == 0


def test_permit_validity_window_is_short_and_inspectable() -> None:
    evidence = _evidence()
    permit = _permit(_replay_target(), evidence)

    assert not permit.valid_at(199)
    assert permit.valid_at(200)
    assert permit.valid_at(201)
    assert not permit.valid_at(202)
    assert permit.snapshot()["operation_count"] == 0
    assert permit.snapshot()["has_production_action_authority"] is False


def test_approval_requires_immediate_current_evidence() -> None:
    evidence = _evidence()
    target = _replay_target()

    with pytest.raises(ValueError, match="immediate current-evidence"):
        _permit(
            target,
            evidence,
            request=_request(
                target,
                evidence,
                approval_episode=201,
                expires_after_episode=202,
            ),
        )

    mismatched = replace(
        _request(target, evidence),
        expected_evidence_state_id="controlled-replay-restoration-evidence:wrong",
    )
    with pytest.raises(ValueError, match="different current evidence"):
        _permit(target, evidence, request=mismatched)


def test_approval_window_cannot_exceed_policy_limit() -> None:
    evidence = _evidence()
    target = _replay_target()

    with pytest.raises(ValueError, match="validity exceeds"):
        _permit(
            target,
            evidence,
            request=_request(target, evidence, expires_after_episode=202),
        )


def test_approval_requires_explicit_human_identity() -> None:
    evidence = _evidence()

    with pytest.raises(ValueError, match="explicit human approver"):
        _request(
            _replay_target(),
            evidence,
            approver_code="policy:auto_approver",
        )


def test_unverified_or_fallback_checkpoint_evidence_is_rejected() -> None:
    target = _replay_target()

    unverified = _evidence(checksum_verified=False)
    with pytest.raises(ValueError, match="checksum-verified"):
        _permit(target, unverified)

    fallback = _evidence(used_fallback=True)
    with pytest.raises(ValueError, match="fallback checkpoint evidence"):
        _permit(target, fallback)


def test_target_requires_exact_current_and_source_checkpoint_identities() -> None:
    evidence = _evidence()
    replay = _replay_target()

    with pytest.raises(ValueError, match="different current checkpoint"):
        _permit(
            replace(replay, expected_current_checkpoint_id="checkpoint:other"),
            evidence,
        )
    with pytest.raises(ValueError, match="different current checkpoint checksum"):
        _permit(
            replace(replay, expected_current_checkpoint_checksum="c" * 64),
            evidence,
        )
    with pytest.raises(ValueError, match="source checkpoint checksum is not current"):
        _permit(
            replace(replay, source_checkpoint_checksum="c" * 64),
            evidence,
        )
    with pytest.raises(ValueError, match="not present in current evidence"):
        _permit(
            replace(
                replay,
                source_checkpoint_id="checkpoint:missing",
                source_checkpoint_checksum="c" * 64,
            ),
            evidence,
        )


def test_target_requires_all_exact_source_evidence() -> None:
    evidence = _evidence()
    target = replace(
        _replay_target(),
        source_evidence_ids=tuple(sorted((*_EVIDENCE_IDS, "evidence:retention:missing"))),
    )

    with pytest.raises(ValueError, match="source evidence is not currently available"):
        _permit(target, evidence)


def test_operation_specific_target_bounds_are_enforced() -> None:
    replay = _replay_target()
    restoration = _restoration_target()

    with pytest.raises(ValueError, match="replay-target prefix"):
        replace(replay, target_id="restoration-target:wrong")
    with pytest.raises(ValueError, match="positive work-item bound"):
        replace(replay, maximum_work_items=0)
    with pytest.raises(ValueError, match="restoration-target prefix"):
        replace(restoration, target_id="replay-target:wrong")
    with pytest.raises(ValueError, match="cannot contain replay work items"):
        replace(restoration, maximum_work_items=1)
    with pytest.raises(ValueError, match="must differ from current state"):
        replace(
            restoration,
            source_checkpoint_id="checkpoint:current",
            source_checkpoint_checksum=_CURRENT_CHECKSUM,
        )
    with pytest.raises(ValueError, match="complete checkpoint envelope"):
        replace(replay, requires_complete_envelope=False)
    with pytest.raises(ValueError, match="partial checkpoint restoration is forbidden"):
        replace(restoration, allows_partial_restoration=True)


def test_target_and_permit_reject_all_authority_bearing_state() -> None:
    target = _replay_target()
    evidence = _evidence()
    permit = _permit(target, evidence)

    with pytest.raises(ValueError, match="cannot execute replay"):
        replace(target, has_replay_authority=True)
    with pytest.raises(ValueError, match="cannot restore checkpoints"):
        replace(target, has_restoration_authority=True)
    with pytest.raises(ValueError, match="cannot select production actions"):
        replace(target, has_production_action_authority=True)
    with pytest.raises(ValueError, match="cannot perform cognition"):
        replace(target, has_cognitive_authority=True)

    with pytest.raises(ValueError, match="authorize exactly one"):
        replace(permit, authorizes_one_operation=False)
    with pytest.raises(ValueError, match="single-use"):
        replace(permit, single_use=False)
    with pytest.raises(ValueError, match="already be consumed"):
        replace(permit, consumed=True)
    with pytest.raises(ValueError, match="completed operations"):
        replace(permit, operation_count=1)
    with pytest.raises(ValueError, match="execute replay directly"):
        replace(permit, has_direct_replay_authority=True)
    with pytest.raises(ValueError, match="restore checkpoints directly"):
        replace(permit, has_direct_restoration_authority=True)
    with pytest.raises(ValueError, match="select production actions"):
        replace(permit, has_production_action_authority=True)
    with pytest.raises(ValueError, match="perform cognition"):
        replace(permit, has_cognitive_authority=True)


def test_distinct_human_reason_produces_distinct_permit_identity() -> None:
    evidence = _evidence()
    target = _replay_target()

    first = _permit(target, evidence)
    second = _permit(
        target,
        evidence,
        request=_request(
            target,
            evidence,
            reason_code="approve_after_additional_human_review",
        ),
    )

    assert first.permit_id != second.permit_id
    assert first.target == second.target
    assert first.evidence == second.evidence


def test_approval_module_has_no_execution_persistence_timer_or_sql_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/controlled_replay_restoration_approval.py")
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
