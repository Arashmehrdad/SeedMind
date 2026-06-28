"""Restart-safe persistence for controlled replay and restoration evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from seedmind.research.ndnra.activity_maintenance import ActivityMaintenanceLedger
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
    ControlledReplayRestorationPermitTransitionDecision,
    ControlledReplayRestorationPermitTransitionRequest,
)

if TYPE_CHECKING:
    from seedmind.research.ndnra.controlled_retention_replay import (
        ControlledRetentionReplayItemReceipt,
        ControlledRetentionReplayReceipt,
        ControlledRetentionReplayResult,
    )

REPLAY_RESTORATION_SCHEMA = "seedmind.ndnra.replay_restoration"
REPLAY_RESTORATION_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class ControlledCheckpointRestorationReceipt:
    """Audit evidence for one exact complete-envelope restoration."""

    receipt_id: str
    permit_id: str
    target_id: str
    source_checkpoint_id: str
    source_checkpoint_checksum: str
    previous_checkpoint_id: str
    previous_checkpoint_checksum: str
    restoration_episode: int
    actor_code: str
    reason_code: str
    source_schema_version: int
    restored_complete_envelope: bool = True
    partial_restoration_count: int = 0
    has_replay_authority: bool = False
    has_restoration_authority: bool = False
    has_cognitive_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("receipt_id", self.receipt_id),
            ("permit_id", self.permit_id),
            ("target_id", self.target_id),
            ("source_checkpoint_id", self.source_checkpoint_id),
            ("previous_checkpoint_id", self.previous_checkpoint_id),
            ("actor_code", self.actor_code),
            ("reason_code", self.reason_code),
        ):
            _validate_code(name, value)
        _validate_checksum("source_checkpoint_checksum", self.source_checkpoint_checksum)
        _validate_checksum("previous_checkpoint_checksum", self.previous_checkpoint_checksum)
        _validate_nonnegative_int("restoration_episode", self.restoration_episode)
        _validate_nonnegative_int("source_schema_version", self.source_schema_version)
        if self.source_schema_version < 1:
            raise ValueError("source_schema_version must be positive")
        if self.actor_code != "operation:checkpoint_restoration":
            raise ValueError(
                "checkpoint restoration receipt requires operation:checkpoint_restoration actor"
            )
        if not self.restored_complete_envelope:
            raise ValueError("checkpoint restoration must restore a complete envelope")
        if self.partial_restoration_count != 0:
            raise ValueError("checkpoint restoration cannot contain partial restorations")
        _reject_authority(
            has_replay_authority=self.has_replay_authority,
            has_restoration_authority=self.has_restoration_authority,
            has_cognitive_authority=self.has_cognitive_authority,
            has_production_action_authority=self.has_production_action_authority,
        )
        if self.receipt_id != _identity("checkpoint-restoration-receipt", self._payload()):
            raise ValueError("checkpoint restoration receipt identity is inconsistent")

    @classmethod
    def create(
        cls,
        *,
        permit_id: str,
        target_id: str,
        source_checkpoint_id: str,
        source_checkpoint_checksum: str,
        previous_checkpoint_id: str,
        previous_checkpoint_checksum: str,
        restoration_episode: int,
        actor_code: str,
        reason_code: str,
        source_schema_version: int,
    ) -> ControlledCheckpointRestorationReceipt:
        payload: dict[str, object] = {
            "permit_id": permit_id,
            "target_id": target_id,
            "source_checkpoint_id": source_checkpoint_id,
            "source_checkpoint_checksum": source_checkpoint_checksum,
            "previous_checkpoint_id": previous_checkpoint_id,
            "previous_checkpoint_checksum": previous_checkpoint_checksum,
            "restoration_episode": restoration_episode,
            "actor_code": actor_code,
            "reason_code": reason_code,
            "source_schema_version": source_schema_version,
            "restored_complete_envelope": True,
            "partial_restoration_count": 0,
            "has_replay_authority": False,
            "has_restoration_authority": False,
            "has_cognitive_authority": False,
            "has_production_action_authority": False,
        }
        return cls(
            receipt_id=_identity("checkpoint-restoration-receipt", payload),
            permit_id=permit_id,
            target_id=target_id,
            source_checkpoint_id=source_checkpoint_id,
            source_checkpoint_checksum=source_checkpoint_checksum,
            previous_checkpoint_id=previous_checkpoint_id,
            previous_checkpoint_checksum=previous_checkpoint_checksum,
            restoration_episode=restoration_episode,
            actor_code=actor_code,
            reason_code=reason_code,
            source_schema_version=source_schema_version,
        )

    def snapshot(self) -> dict[str, object]:
        return {"receipt_id": self.receipt_id, **self._payload()}

    def _payload(self) -> dict[str, object]:
        return {
            "permit_id": self.permit_id,
            "target_id": self.target_id,
            "source_checkpoint_id": self.source_checkpoint_id,
            "source_checkpoint_checksum": self.source_checkpoint_checksum,
            "previous_checkpoint_id": self.previous_checkpoint_id,
            "previous_checkpoint_checksum": self.previous_checkpoint_checksum,
            "restoration_episode": self.restoration_episode,
            "actor_code": self.actor_code,
            "reason_code": self.reason_code,
            "source_schema_version": self.source_schema_version,
            "restored_complete_envelope": self.restored_complete_envelope,
            "partial_restoration_count": self.partial_restoration_count,
            "has_replay_authority": self.has_replay_authority,
            "has_restoration_authority": self.has_restoration_authority,
            "has_cognitive_authority": self.has_cognitive_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class NDNRAReplayRestorationCheckpoint:
    """Complete active activity state plus monotonic controlled-operation audit history."""

    permit_registry: ControlledReplayRestorationPermitLifecycleRegistry = field(
        default_factory=ControlledReplayRestorationPermitLifecycleRegistry
    )
    activity_ledger: ActivityMaintenanceLedger = field(default_factory=ActivityMaintenanceLedger)
    replay_receipts: tuple[ControlledRetentionReplayReceipt, ...] = ()
    restoration_receipts: tuple[ControlledCheckpointRestorationReceipt, ...] = ()
    automatic_replay_count: int = 0
    automatic_restoration_count: int = 0
    has_replay_authority: bool = False
    has_restoration_authority: bool = False
    has_cognitive_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.automatic_replay_count != 0:
            raise ValueError("replay checkpoints cannot contain automatic replay")
        if self.automatic_restoration_count != 0:
            raise ValueError("replay checkpoints cannot contain automatic restoration")
        _reject_authority(
            has_replay_authority=self.has_replay_authority,
            has_restoration_authority=self.has_restoration_authority,
            has_cognitive_authority=self.has_cognitive_authority,
            has_production_action_authority=self.has_production_action_authority,
        )
        permit_ids = tuple(record.permit.permit_id for record in self.permit_registry.records)
        if permit_ids != tuple(sorted(permit_ids)):
            raise ValueError("controlled-operation permits must use stable ordering")
        replay_ids = tuple(receipt.receipt_id for receipt in self.replay_receipts)
        restoration_ids = tuple(receipt.receipt_id for receipt in self.restoration_receipts)
        if replay_ids != tuple(sorted(replay_ids)):
            raise ValueError("replay receipts must use stable ordering")
        if restoration_ids != tuple(sorted(restoration_ids)):
            raise ValueError("restoration receipts must use stable ordering")
        if len(replay_ids) != len(set(replay_ids)):
            raise ValueError("replay receipt identities must be unique")
        if len(restoration_ids) != len(set(restoration_ids)):
            raise ValueError("restoration receipt identities must be unique")
        receipt_permits = [receipt.permit_id for receipt in self.replay_receipts]
        receipt_permits.extend(receipt.permit_id for receipt in self.restoration_receipts)
        if len(receipt_permits) != len(set(receipt_permits)):
            raise ValueError("one permit cannot have multiple controlled-operation receipts")

        replay_by_permit = {receipt.permit_id: receipt for receipt in self.replay_receipts}
        restoration_by_permit = {
            receipt.permit_id: receipt for receipt in self.restoration_receipts
        }
        registered = set(permit_ids)
        if any(permit_id not in registered for permit_id in receipt_permits):
            raise ValueError("controlled-operation receipt requires its retained permit")
        for record in self.permit_registry.records:
            replay = replay_by_permit.get(record.permit.permit_id)
            restoration = restoration_by_permit.get(record.permit.permit_id)
            receipt = replay if replay is not None else restoration
            if record.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED:
                if receipt is None:
                    raise ValueError("consumed controlled-operation permit requires a receipt")
                if record.decisions[0].consumption_reference_code != receipt.receipt_id:
                    raise ValueError("permit consumption reference must equal receipt identity")
                target = record.permit.target
                if replay is not None:
                    if target.operation is not ControlledReplayRestorationOperation.RETENTION_REPLAY:
                        raise ValueError("replay receipt requires a replay-scoped permit")
                    if replay.target_id != target.target_id:
                        raise ValueError("replay receipt targets a different replay target")
                else:
                    assert restoration is not None
                    if target.operation is not (
                        ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION
                    ):
                        raise ValueError("restoration receipt requires a restoration permit")
                    if restoration.target_id != target.target_id:
                        raise ValueError("restoration receipt targets a different target")
                    if restoration.source_checkpoint_id != target.source_checkpoint_id:
                        raise ValueError("restoration receipt source checkpoint differs")
                    if restoration.source_checkpoint_checksum != target.source_checkpoint_checksum:
                        raise ValueError("restoration receipt source checksum differs")
                    if restoration.previous_checkpoint_id != target.expected_current_checkpoint_id:
                        raise ValueError("restoration receipt previous checkpoint differs")
                    if restoration.previous_checkpoint_checksum != (
                        target.expected_current_checkpoint_checksum
                    ):
                        raise ValueError("restoration receipt previous checksum differs")
            elif receipt is not None:
                raise ValueError("only a consumed permit may have an operation receipt")

    @classmethod
    def empty(cls) -> NDNRAReplayRestorationCheckpoint:
        return cls()

    @classmethod
    def with_issued_permit(
        cls,
        permit: ControlledReplayRestorationPermit,
        *,
        previous: NDNRAReplayRestorationCheckpoint | None = None,
    ) -> NDNRAReplayRestorationCheckpoint:
        checkpoint = cls.empty() if previous is None else previous
        return cls(
            permit_registry=_canonical_registry(checkpoint.permit_registry.add(permit)),
            activity_ledger=checkpoint.activity_ledger,
            replay_receipts=checkpoint.replay_receipts,
            restoration_receipts=checkpoint.restoration_receipts,
        )

    def record_replay(
        self,
        result: ControlledRetentionReplayResult,
    ) -> NDNRAReplayRestorationCheckpoint:
        permit_id = result.receipt.permit_id
        prior = self.permit_registry.record_for(permit_id)
        if prior.status is not ControlledReplayRestorationPermitLifecycleStatus.ISSUED:
            raise ValueError("durable replay requires a previously issued permit")
        if prior.permit.target.operation is not (
            ControlledReplayRestorationOperation.RETENTION_REPLAY
        ):
            raise ValueError("durable replay requires a replay-scoped permit")
        expected_ids = {record.permit.permit_id for record in self.permit_registry.records}
        result_ids = {record.permit.permit_id for record in result.lifecycle_registry.records}
        if expected_ids != result_ids:
            raise ValueError("replay result must preserve the complete permit registry")
        if any(receipt.permit_id == permit_id for receipt in self.replay_receipts):
            raise ValueError("durable replay receipt already exists for permit")
        for item in result.receipt.items:
            persisted = result.activity_ledger.decision_for(item.replay_activity_event_id)
            if persisted.decision_id != item.maintenance_decision_id:
                raise ValueError("replay receipt must match persisted activity decision")
        return NDNRAReplayRestorationCheckpoint(
            permit_registry=_canonical_registry(result.lifecycle_registry),
            activity_ledger=result.activity_ledger,
            replay_receipts=tuple(
                sorted(
                    (*self.replay_receipts, result.receipt),
                    key=lambda receipt: receipt.receipt_id,
                )
            ),
            restoration_receipts=self.restoration_receipts,
        )

    def record_restoration(
        self,
        *,
        consumed_registry: ControlledReplayRestorationPermitLifecycleRegistry,
        receipt: ControlledCheckpointRestorationReceipt,
        restored_activity_ledger: ActivityMaintenanceLedger,
    ) -> NDNRAReplayRestorationCheckpoint:
        prior = self.permit_registry.record_for(receipt.permit_id)
        if prior.status is not ControlledReplayRestorationPermitLifecycleStatus.ISSUED:
            raise ValueError("durable restoration requires a previously issued permit")
        expected_ids = {record.permit.permit_id for record in self.permit_registry.records}
        result_ids = {record.permit.permit_id for record in consumed_registry.records}
        if expected_ids != result_ids:
            raise ValueError("restoration must preserve the complete current permit registry")
        return NDNRAReplayRestorationCheckpoint(
            permit_registry=_canonical_registry(consumed_registry),
            activity_ledger=restored_activity_ledger,
            replay_receipts=self.replay_receipts,
            restoration_receipts=tuple(
                sorted(
                    (*self.restoration_receipts, receipt),
                    key=lambda item: item.receipt_id,
                )
            ),
        )

    def audit_contains(self, earlier: NDNRAReplayRestorationCheckpoint) -> bool:
        current_records = {
            record.permit.permit_id: record for record in self.permit_registry.records
        }
        for earlier_record in earlier.permit_registry.records:
            current = current_records.get(earlier_record.permit.permit_id)
            if current is None or current.permit != earlier_record.permit:
                return False
            if earlier_record.is_terminal and current != earlier_record:
                return False
        current_replay = {item.receipt_id: item for item in self.replay_receipts}
        current_restoration = {
            item.receipt_id: item for item in self.restoration_receipts
        }
        return bool(
            all(current_replay.get(item.receipt_id) == item for item in earlier.replay_receipts)
            and all(
                current_restoration.get(item.receipt_id) == item
                for item in earlier.restoration_receipts
            )
        )

    def active_state_snapshot(self) -> dict[str, object]:
        return {"activity_ledger": self.activity_ledger.snapshot()}

    def snapshot(self) -> dict[str, object]:
        return {
            "schema": REPLAY_RESTORATION_SCHEMA,
            "schema_version": REPLAY_RESTORATION_SCHEMA_VERSION,
            "permit_registry": self.permit_registry.snapshot(),
            "activity_ledger": self.activity_ledger.snapshot(),
            "replay_receipts": [receipt.snapshot() for receipt in self.replay_receipts],
            "restoration_receipts": [
                receipt.snapshot() for receipt in self.restoration_receipts
            ],
            "automatic_replay_count": self.automatic_replay_count,
            "automatic_restoration_count": self.automatic_restoration_count,
            "has_replay_authority": self.has_replay_authority,
            "has_restoration_authority": self.has_restoration_authority,
            "has_cognitive_authority": self.has_cognitive_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> NDNRAReplayRestorationCheckpoint:
        values = _require_mapping("replay/restoration checkpoint", snapshot)
        if _require_string(values, "schema") != REPLAY_RESTORATION_SCHEMA:
            raise ValueError("replay/restoration checkpoint schema is incompatible")
        if _require_int(values, "schema_version") != REPLAY_RESTORATION_SCHEMA_VERSION:
            raise ValueError("replay/restoration checkpoint version is incompatible")
        checkpoint = cls(
            permit_registry=_restore_registry(values.get("permit_registry")),
            activity_ledger=ActivityMaintenanceLedger.from_snapshot(
                values.get("activity_ledger")
            ),
            replay_receipts=tuple(
                sorted(
                    (
                        _restore_replay_receipt(item)
                        for item in _require_list(values, "replay_receipts")
                    ),
                    key=lambda receipt: receipt.receipt_id,
                )
            ),
            restoration_receipts=tuple(
                sorted(
                    (
                        _restore_restoration_receipt(item)
                        for item in _require_list(values, "restoration_receipts")
                    ),
                    key=lambda receipt: receipt.receipt_id,
                )
            ),
            automatic_replay_count=_require_int(values, "automatic_replay_count"),
            automatic_restoration_count=_require_int(values, "automatic_restoration_count"),
            has_replay_authority=_require_bool(values, "has_replay_authority"),
            has_restoration_authority=_require_bool(values, "has_restoration_authority"),
            has_cognitive_authority=_require_bool(values, "has_cognitive_authority"),
            has_production_action_authority=_require_bool(
                values, "has_production_action_authority"
            ),
        )
        if checkpoint.snapshot() != dict(values):
            raise ValueError("replay/restoration checkpoint did not round-trip exactly")
        return checkpoint


def _canonical_registry(
    registry: ControlledReplayRestorationPermitLifecycleRegistry,
) -> ControlledReplayRestorationPermitLifecycleRegistry:
    return ControlledReplayRestorationPermitLifecycleRegistry(
        records=tuple(sorted(registry.records, key=lambda record: record.permit.permit_id))
    )


def _restore_registry(
    snapshot: object,
) -> ControlledReplayRestorationPermitLifecycleRegistry:
    values = _require_mapping("controlled-operation permit registry", snapshot)
    registry = ControlledReplayRestorationPermitLifecycleRegistry(
        records=tuple(
            sorted(
                (_restore_record(item) for item in _require_list(values, "records")),
                key=lambda record: record.permit.permit_id,
            )
        ),
        has_replay_authority=_require_bool(values, "has_replay_authority"),
        has_restoration_authority=_require_bool(values, "has_restoration_authority"),
        has_cognitive_authority=_require_bool(values, "has_cognitive_authority"),
        has_production_action_authority=_require_bool(
            values, "has_production_action_authority"
        ),
    )
    if _require_int(values, "consumption_count") != registry.consumption_count:
        raise ValueError("persisted controlled-operation consumption count is inconsistent")
    if _require_int(values, "replay_consumption_count") != registry.replay_consumption_count:
        raise ValueError("persisted replay consumption count is inconsistent")
    if _require_int(values, "restoration_consumption_count") != (
        registry.restoration_consumption_count
    ):
        raise ValueError("persisted restoration consumption count is inconsistent")
    if registry.snapshot() != dict(values):
        raise ValueError("controlled-operation registry did not round-trip exactly")
    return registry


def _restore_record(snapshot: object) -> ControlledReplayRestorationPermitLifecycleRecord:
    values = _require_mapping("controlled-operation permit record", snapshot)
    permit = _restore_permit(values.get("permit"))
    decisions = tuple(
        _restore_transition(item, permit=permit)
        for item in _require_list(values, "decisions")
    )
    record = ControlledReplayRestorationPermitLifecycleRecord(
        permit=permit,
        status=ControlledReplayRestorationPermitLifecycleStatus(
            _require_string(values, "status")
        ),
        decisions=decisions,
        has_replay_authority=_require_bool(values, "has_replay_authority"),
        has_restoration_authority=_require_bool(values, "has_restoration_authority"),
        has_cognitive_authority=_require_bool(values, "has_cognitive_authority"),
        has_production_action_authority=_require_bool(
            values, "has_production_action_authority"
        ),
    )
    if _require_bool(values, "is_terminal") is not record.is_terminal:
        raise ValueError("persisted controlled-operation terminal state is inconsistent")
    if _require_int(values, "consumption_count") != record.consumption_count:
        raise ValueError("persisted permit consumption count is inconsistent")
    if record.snapshot() != dict(values):
        raise ValueError("controlled-operation permit record did not round-trip exactly")
    return record


def _restore_transition(
    snapshot: object,
    *,
    permit: ControlledReplayRestorationPermit,
) -> ControlledReplayRestorationPermitTransitionDecision:
    values = _require_mapping("controlled-operation permit transition", snapshot)
    if _restore_permit(values.get("permit")) != permit:
        raise ValueError("persisted transition targets a different permit")
    raw_reference = values.get("consumption_reference_code")
    request = ControlledReplayRestorationPermitTransitionRequest(
        target_permit_id=permit.permit_id,
        expected_operation=permit.target.operation,
        expected_target_id=permit.target.target_id,
        expected_source_checkpoint_id=permit.target.source_checkpoint_id,
        expected_source_checkpoint_checksum=permit.target.source_checkpoint_checksum,
        expected_current_checkpoint_id=permit.target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=(
            permit.target.expected_current_checkpoint_checksum
        ),
        expected_evidence_state_id=permit.evidence.evidence_state_id,
        action=ControlledReplayRestorationPermitLifecycleAction(
            _require_string(values, "action")
        ),
        decision_episode=_require_int(values, "decision_episode"),
        actor_code=_require_string(values, "actor_code"),
        reason_code=_require_string(values, "reason_code"),
        consumption_reference_code=(
            None
            if raw_reference is None
            else _require_string(values, "consumption_reference_code")
        ),
    )
    decision = (
        ControlledReplayRestorationPermitLifecycleRecord.issued(permit)
        .transition(request)
        .decisions[0]
    )
    if _require_string(values, "decision_id") != decision.decision_id:
        raise ValueError("persisted controlled-operation transition identity is invalid")
    if _require_string(values, "status") != decision.status.value:
        raise ValueError("persisted controlled-operation transition status is inconsistent")
    if decision.snapshot() != dict(values):
        raise ValueError("controlled-operation transition did not round-trip exactly")
    return decision


def _restore_permit(snapshot: object) -> ControlledReplayRestorationPermit:
    values = _require_mapping("controlled-operation permit", snapshot)
    target = _restore_target(values.get("target"))
    evidence = _restore_evidence(values.get("evidence"))
    request = ControlledReplayRestorationApprovalRequest(
        target=target,
        expected_evidence_state_id=evidence.evidence_state_id,
        approval_episode=_require_int(values, "issued_episode"),
        expires_after_episode=_require_int(values, "expires_after_episode"),
        approver_code=_require_string(values, "approver_code"),
        reason_code=_require_string(values, "reason_code"),
    )
    validity = request.expires_after_episode - request.approval_episode
    permit = ControlledReplayRestorationApprovalPolicy(
        maximum_validity_episodes=validity
    ).evaluate(request=request, evidence=evidence)
    if permit.snapshot() != dict(values):
        raise ValueError("controlled-operation permit did not round-trip exactly")
    return permit


def _restore_target(snapshot: object) -> ControlledReplayRestorationTarget:
    values = _require_mapping("controlled-operation target", snapshot)
    target = ControlledReplayRestorationTarget(
        operation=ControlledReplayRestorationOperation(
            _require_string(values, "operation")
        ),
        target_id=_require_string(values, "target_id"),
        source_checkpoint_id=_require_string(values, "source_checkpoint_id"),
        source_checkpoint_checksum=_require_string(values, "source_checkpoint_checksum"),
        expected_current_checkpoint_id=_require_string(
            values, "expected_current_checkpoint_id"
        ),
        expected_current_checkpoint_checksum=_require_string(
            values, "expected_current_checkpoint_checksum"
        ),
        source_evidence_ids=tuple(_require_string_list(values, "source_evidence_ids")),
        maximum_work_items=_require_int(values, "maximum_work_items"),
        requires_complete_envelope=_require_bool(values, "requires_complete_envelope"),
        allows_partial_restoration=_require_bool(values, "allows_partial_restoration"),
        has_replay_authority=_require_bool(values, "has_replay_authority"),
        has_restoration_authority=_require_bool(values, "has_restoration_authority"),
        has_production_action_authority=_require_bool(
            values, "has_production_action_authority"
        ),
        has_cognitive_authority=_require_bool(values, "has_cognitive_authority"),
    )
    if target.snapshot() != dict(values):
        raise ValueError("controlled-operation target did not round-trip exactly")
    return target


def _restore_evidence(snapshot: object) -> ControlledReplayRestorationEvidence:
    values = _require_mapping("controlled-operation evidence", snapshot)
    checkpoints: list[tuple[str, str]] = []
    for raw_item in _require_list(values, "available_checkpoint_checksums"):
        item = _require_mapping("available checkpoint", raw_item)
        checkpoints.append(
            (
                _require_string(item, "checkpoint_id"),
                _require_string(item, "checksum"),
            )
        )
    evidence = ControlledReplayRestorationEvidence(
        captured_episode=_require_int(values, "captured_episode"),
        current_checkpoint_id=_require_string(values, "current_checkpoint_id"),
        current_checkpoint_checksum=_require_string(
            values, "current_checkpoint_checksum"
        ),
        available_checkpoint_checksums=tuple(checkpoints),
        available_evidence_ids=tuple(
            _require_string_list(values, "available_evidence_ids")
        ),
        checksum_verified=_require_bool(values, "checksum_verified"),
        used_fallback=_require_bool(values, "used_fallback"),
        has_replay_or_restoration_authority=_require_bool(
            values, "has_replay_or_restoration_authority"
        ),
    )
    if _require_string(values, "evidence_state_id") != evidence.evidence_state_id:
        raise ValueError("persisted controlled-operation evidence identity is invalid")
    if evidence.snapshot() != dict(values):
        raise ValueError("controlled-operation evidence did not round-trip exactly")
    return evidence


def _restore_replay_receipt(snapshot: object) -> ControlledRetentionReplayReceipt:
    from seedmind.research.ndnra.controlled_retention_replay import (
        ControlledRetentionReplayReceipt,
    )

    values = _require_mapping("retention replay receipt", snapshot)
    receipt = ControlledRetentionReplayReceipt(
        receipt_id=_require_string(values, "receipt_id"),
        permit_id=_require_string(values, "permit_id"),
        target_id=_require_string(values, "target_id"),
        fresh_evidence_state_id=_require_string(
            values, "fresh_evidence_state_id"
        ),
        operation_episode=_require_int(values, "operation_episode"),
        actor_code=_require_string(values, "actor_code"),
        reason_code=_require_string(values, "reason_code"),
        items=tuple(
            _restore_replay_item_receipt(item)
            for item in _require_list(values, "items")
        ),
        factual_confidence_delta=_require_float(values, "factual_confidence_delta"),
        mastery_delta=_require_float(values, "mastery_delta"),
        has_learning_authority=_require_bool(values, "has_learning_authority"),
        has_action_selection_authority=_require_bool(
            values, "has_action_selection_authority"
        ),
        has_production_action_authority=_require_bool(
            values, "has_production_action_authority"
        ),
    )
    if _require_int(values, "work_item_count") != receipt.work_item_count:
        raise ValueError("persisted replay work-item count is inconsistent")
    if _require_float(values, "total_reactivation") != receipt.total_reactivation:
        raise ValueError("persisted replay total reactivation is inconsistent")
    if receipt.snapshot() != dict(values):
        raise ValueError("retention replay receipt did not round-trip exactly")
    return receipt


def _restore_replay_item_receipt(snapshot: object) -> ControlledRetentionReplayItemReceipt:
    from seedmind.research.ndnra.controlled_retention_replay import (
        ControlledRetentionReplayItemReceipt,
        ControlledRetentionReplayWorkItem,
    )

    values = _require_mapping("retention replay item receipt", snapshot)
    work_values = _require_mapping("replay work item", values.get("work_item"))
    work_item = ControlledRetentionReplayWorkItem(
        work_item_id=_require_string(work_values, "work_item_id"),
        source_evidence_id=_require_string(work_values, "source_evidence_id"),
        structure_ids=tuple(_require_string_list(work_values, "structure_ids")),
        has_learning_authority=_require_bool(work_values, "has_learning_authority"),
        has_action_selection_authority=_require_bool(
            work_values, "has_action_selection_authority"
        ),
        has_production_action_authority=_require_bool(
            work_values, "has_production_action_authority"
        ),
    )
    changes: list[tuple[str, float, float]] = []
    for raw_change in _require_list(values, "structure_changes"):
        change = _require_mapping("replay structure change", raw_change)
        changes.append(
            (
                _require_string(change, "structure_id"),
                _require_float(change, "dormancy_before"),
                _require_float(change, "dormancy_after"),
            )
        )
    item = ControlledRetentionReplayItemReceipt(
        work_item=work_item,
        replay_activity_event_id=_require_string(
            values, "replay_activity_event_id"
        ),
        maintenance_decision_id=_require_string(values, "maintenance_decision_id"),
        structure_changes=tuple(changes),
        reactivation_per_structure=_require_float(
            values, "reactivation_per_structure"
        ),
        factual_confidence_delta=_require_float(values, "factual_confidence_delta"),
        mastery_delta=_require_float(values, "mastery_delta"),
        has_learning_authority=_require_bool(values, "has_learning_authority"),
        has_action_selection_authority=_require_bool(
            values, "has_action_selection_authority"
        ),
        has_production_action_authority=_require_bool(
            values, "has_production_action_authority"
        ),
    )
    if _require_float(values, "total_reactivation") != item.total_reactivation:
        raise ValueError("persisted replay item reactivation is inconsistent")
    if item.snapshot() != dict(values):
        raise ValueError("retention replay item receipt did not round-trip exactly")
    return item


def _restore_restoration_receipt(
    snapshot: object,
) -> ControlledCheckpointRestorationReceipt:
    values = _require_mapping("checkpoint restoration receipt", snapshot)
    receipt = ControlledCheckpointRestorationReceipt(
        receipt_id=_require_string(values, "receipt_id"),
        permit_id=_require_string(values, "permit_id"),
        target_id=_require_string(values, "target_id"),
        source_checkpoint_id=_require_string(values, "source_checkpoint_id"),
        source_checkpoint_checksum=_require_string(
            values, "source_checkpoint_checksum"
        ),
        previous_checkpoint_id=_require_string(values, "previous_checkpoint_id"),
        previous_checkpoint_checksum=_require_string(
            values, "previous_checkpoint_checksum"
        ),
        restoration_episode=_require_int(values, "restoration_episode"),
        actor_code=_require_string(values, "actor_code"),
        reason_code=_require_string(values, "reason_code"),
        source_schema_version=_require_int(values, "source_schema_version"),
        restored_complete_envelope=_require_bool(
            values, "restored_complete_envelope"
        ),
        partial_restoration_count=_require_int(values, "partial_restoration_count"),
        has_replay_authority=_require_bool(values, "has_replay_authority"),
        has_restoration_authority=_require_bool(
            values, "has_restoration_authority"
        ),
        has_cognitive_authority=_require_bool(values, "has_cognitive_authority"),
        has_production_action_authority=_require_bool(
            values, "has_production_action_authority"
        ),
    )
    if receipt.snapshot() != dict(values):
        raise ValueError("checkpoint restoration receipt did not round-trip exactly")
    return receipt


def _identity(prefix: str, payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"{prefix}:{hashlib.sha256(canonical).hexdigest()}"


def _reject_authority(
    *,
    has_replay_authority: bool,
    has_restoration_authority: bool,
    has_cognitive_authority: bool,
    has_production_action_authority: bool,
) -> None:
    if has_replay_authority:
        raise ValueError("replay/restoration checkpoints cannot execute replay")
    if has_restoration_authority:
        raise ValueError("replay/restoration checkpoints cannot restore checkpoints")
    if has_cognitive_authority:
        raise ValueError("replay/restoration checkpoints cannot perform cognition")
    if has_production_action_authority:
        raise ValueError("replay/restoration checkpoints cannot select production actions")


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_list(values: Mapping[str, object], key: str) -> list[object]:
    value = values.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_float(values: Mapping[str, object], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _require_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be boolean")
    return value


def _require_string_list(values: Mapping[str, object], key: str) -> list[str]:
    result: list[str] = []
    for item in _require_list(values, key):
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain strings")
        result.append(item)
    return result


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_checksum(name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 checksum")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


__all__ = [
    "REPLAY_RESTORATION_SCHEMA",
    "REPLAY_RESTORATION_SCHEMA_VERSION",
    "ControlledCheckpointRestorationReceipt",
    "NDNRAReplayRestorationCheckpoint",
]
