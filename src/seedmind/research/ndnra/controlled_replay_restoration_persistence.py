"""Restart-safe persistence for bounded controlled replay evidence."""

from __future__ import annotations

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
class NDNRAReplayRestorationCheckpoint:
    """Active activity state plus monotonic replay permit and receipt evidence."""

    permit_registry: ControlledReplayRestorationPermitLifecycleRegistry = field(
        default_factory=ControlledReplayRestorationPermitLifecycleRegistry
    )
    activity_ledger: ActivityMaintenanceLedger = field(default_factory=ActivityMaintenanceLedger)
    replay_receipts: tuple[ControlledRetentionReplayReceipt, ...] = ()
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
        receipt_ids = tuple(receipt.receipt_id for receipt in self.replay_receipts)
        if receipt_ids != tuple(sorted(receipt_ids)):
            raise ValueError("replay receipts must use stable ordering")
        if len(receipt_ids) != len(set(receipt_ids)):
            raise ValueError("replay receipt identities must be unique")
        receipt_permit_ids = tuple(receipt.permit_id for receipt in self.replay_receipts)
        if len(receipt_permit_ids) != len(set(receipt_permit_ids)):
            raise ValueError("one replay permit cannot have multiple receipts")

        receipts = {receipt.permit_id: receipt for receipt in self.replay_receipts}
        registered = set(permit_ids)
        if any(permit_id not in registered for permit_id in receipts):
            raise ValueError("replay receipt requires its retained permit")
        for record in self.permit_registry.records:
            receipt = receipts.get(record.permit.permit_id)
            if record.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED:
                if record.permit.target.operation is not (
                    ControlledReplayRestorationOperation.RETENTION_REPLAY
                ):
                    raise ValueError(
                        "durable restoration consumption is outside the replay-only batch"
                    )
                if receipt is None:
                    raise ValueError("consumed replay permit requires a receipt")
                if record.decisions[0].consumption_reference_code != receipt.receipt_id:
                    raise ValueError("permit consumption reference must equal receipt identity")
                if receipt.target_id != record.permit.target.target_id:
                    raise ValueError("replay receipt targets a different replay target")
            elif receipt is not None:
                raise ValueError("only a consumed replay permit may have a receipt")

    @classmethod
    def empty(cls) -> NDNRAReplayRestorationCheckpoint:
        """Return the explicit migration target for older brain schemas."""
        return cls()

    @classmethod
    def with_issued_permit(
        cls,
        permit: ControlledReplayRestorationPermit,
        *,
        previous: NDNRAReplayRestorationCheckpoint | None = None,
    ) -> NDNRAReplayRestorationCheckpoint:
        """Retain one issued approval without executing its operation."""
        checkpoint = cls.empty() if previous is None else previous
        return cls(
            permit_registry=_canonical_registry(checkpoint.permit_registry.add(permit)),
            activity_ledger=checkpoint.activity_ledger,
            replay_receipts=checkpoint.replay_receipts,
        )

    def record_replay(
        self,
        result: ControlledRetentionReplayResult,
    ) -> NDNRAReplayRestorationCheckpoint:
        """Record one successful replay and its consumed single-use permit."""
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
        )

    def active_state_snapshot(self) -> dict[str, object]:
        """Return active memory state separately from approval and audit metadata."""
        return {"activity_ledger": self.activity_ledger.snapshot()}

    def snapshot(self) -> dict[str, object]:
        """Return deterministic replay persistence evidence."""
        return {
            "schema": REPLAY_RESTORATION_SCHEMA,
            "schema_version": REPLAY_RESTORATION_SCHEMA_VERSION,
            "permit_registry": self.permit_registry.snapshot(),
            "activity_ledger": self.activity_ledger.snapshot(),
            "replay_receipts": [receipt.snapshot() for receipt in self.replay_receipts],
            "automatic_replay_count": self.automatic_replay_count,
            "automatic_restoration_count": self.automatic_restoration_count,
            "has_replay_authority": self.has_replay_authority,
            "has_restoration_authority": self.has_restoration_authority,
            "has_cognitive_authority": self.has_cognitive_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> NDNRAReplayRestorationCheckpoint:
        """Restore exact replay history without executing any operation."""
        values = _require_mapping("replay checkpoint", snapshot)
        if _require_string(values, "schema") != REPLAY_RESTORATION_SCHEMA:
            raise ValueError("replay checkpoint schema is incompatible")
        if _require_int(values, "schema_version") != REPLAY_RESTORATION_SCHEMA_VERSION:
            raise ValueError("replay checkpoint version is incompatible")
        checkpoint = cls(
            permit_registry=_restore_registry(values.get("permit_registry")),
            activity_ledger=ActivityMaintenanceLedger.from_snapshot(values.get("activity_ledger")),
            replay_receipts=tuple(
                sorted(
                    (
                        _restore_replay_receipt(item)
                        for item in _require_list(values, "replay_receipts")
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
            raise ValueError("replay checkpoint did not round-trip exactly")
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
        has_production_action_authority=_require_bool(values, "has_production_action_authority"),
    )
    if _require_int(values, "consumption_count") != registry.consumption_count:
        raise ValueError("persisted controlled-operation consumption count is inconsistent")
    if _require_int(values, "replay_consumption_count") != (registry.replay_consumption_count):
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
        _restore_transition(item, permit=permit) for item in _require_list(values, "decisions")
    )
    record = ControlledReplayRestorationPermitLifecycleRecord(
        permit=permit,
        status=ControlledReplayRestorationPermitLifecycleStatus(_require_string(values, "status")),
        decisions=decisions,
        has_replay_authority=_require_bool(values, "has_replay_authority"),
        has_restoration_authority=_require_bool(values, "has_restoration_authority"),
        has_cognitive_authority=_require_bool(values, "has_cognitive_authority"),
        has_production_action_authority=_require_bool(values, "has_production_action_authority"),
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
        expected_current_checkpoint_checksum=(permit.target.expected_current_checkpoint_checksum),
        expected_evidence_state_id=permit.evidence.evidence_state_id,
        action=ControlledReplayRestorationPermitLifecycleAction(_require_string(values, "action")),
        decision_episode=_require_int(values, "decision_episode"),
        actor_code=_require_string(values, "actor_code"),
        reason_code=_require_string(values, "reason_code"),
        consumption_reference_code=(
            None if raw_reference is None else _require_string(values, "consumption_reference_code")
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
    permit = ControlledReplayRestorationApprovalPolicy(maximum_validity_episodes=validity).evaluate(
        request=request, evidence=evidence
    )
    if permit.snapshot() != dict(values):
        raise ValueError("controlled-operation permit did not round-trip exactly")
    return permit


def _restore_target(snapshot: object) -> ControlledReplayRestorationTarget:
    values = _require_mapping("controlled-operation target", snapshot)
    target = ControlledReplayRestorationTarget(
        operation=ControlledReplayRestorationOperation(_require_string(values, "operation")),
        target_id=_require_string(values, "target_id"),
        source_checkpoint_id=_require_string(values, "source_checkpoint_id"),
        source_checkpoint_checksum=_require_string(values, "source_checkpoint_checksum"),
        expected_current_checkpoint_id=_require_string(values, "expected_current_checkpoint_id"),
        expected_current_checkpoint_checksum=_require_string(
            values, "expected_current_checkpoint_checksum"
        ),
        source_evidence_ids=tuple(_require_string_list(values, "source_evidence_ids")),
        maximum_work_items=_require_int(values, "maximum_work_items"),
        requires_complete_envelope=_require_bool(values, "requires_complete_envelope"),
        allows_partial_restoration=_require_bool(values, "allows_partial_restoration"),
        has_replay_authority=_require_bool(values, "has_replay_authority"),
        has_restoration_authority=_require_bool(values, "has_restoration_authority"),
        has_production_action_authority=_require_bool(values, "has_production_action_authority"),
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
        current_checkpoint_checksum=_require_string(values, "current_checkpoint_checksum"),
        available_checkpoint_checksums=tuple(checkpoints),
        available_evidence_ids=tuple(_require_string_list(values, "available_evidence_ids")),
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
        fresh_evidence_state_id=_require_string(values, "fresh_evidence_state_id"),
        operation_episode=_require_int(values, "operation_episode"),
        actor_code=_require_string(values, "actor_code"),
        reason_code=_require_string(values, "reason_code"),
        items=tuple(_restore_replay_item_receipt(item) for item in _require_list(values, "items")),
        factual_confidence_delta=_require_float(values, "factual_confidence_delta"),
        mastery_delta=_require_float(values, "mastery_delta"),
        has_learning_authority=_require_bool(values, "has_learning_authority"),
        has_action_selection_authority=_require_bool(values, "has_action_selection_authority"),
        has_production_action_authority=_require_bool(values, "has_production_action_authority"),
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
        has_action_selection_authority=_require_bool(work_values, "has_action_selection_authority"),
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
        replay_activity_event_id=_require_string(values, "replay_activity_event_id"),
        maintenance_decision_id=_require_string(values, "maintenance_decision_id"),
        structure_changes=tuple(changes),
        reactivation_per_structure=_require_float(values, "reactivation_per_structure"),
        factual_confidence_delta=_require_float(values, "factual_confidence_delta"),
        mastery_delta=_require_float(values, "mastery_delta"),
        has_learning_authority=_require_bool(values, "has_learning_authority"),
        has_action_selection_authority=_require_bool(values, "has_action_selection_authority"),
        has_production_action_authority=_require_bool(values, "has_production_action_authority"),
    )
    if _require_float(values, "total_reactivation") != item.total_reactivation:
        raise ValueError("persisted replay item reactivation is inconsistent")
    if item.snapshot() != dict(values):
        raise ValueError("retention replay item receipt did not round-trip exactly")
    return item


def _reject_authority(
    *,
    has_replay_authority: bool,
    has_restoration_authority: bool,
    has_cognitive_authority: bool,
    has_production_action_authority: bool,
) -> None:
    if has_replay_authority:
        raise ValueError("replay checkpoints cannot execute replay")
    if has_restoration_authority:
        raise ValueError("replay checkpoints cannot restore checkpoints")
    if has_cognitive_authority:
        raise ValueError("replay checkpoints cannot perform cognition")
    if has_production_action_authority:
        raise ValueError("replay checkpoints cannot select production actions")


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


__all__ = [
    "REPLAY_RESTORATION_SCHEMA",
    "REPLAY_RESTORATION_SCHEMA_VERSION",
    "NDNRAReplayRestorationCheckpoint",
]
