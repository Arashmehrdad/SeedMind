"""Single-use bounded replay of exact real activity for dormancy maintenance."""

from __future__ import annotations

import hashlib
import json
from copy import deepcopy
from dataclasses import dataclass
from math import isfinite

from seedmind.research.ndnra.activity_maintenance import (
    ActivityMaintenanceDecision,
    ActivityMaintenanceLedger,
    ActivityMaintenanceRequest,
)
from seedmind.research.ndnra.adaptive import (
    ActivityMaintenanceApplication,
    NDNRARuntimeAdaptiveState,
)
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.controlled_replay_restoration_approval import (
    ControlledReplayRestorationEvidence,
    ControlledReplayRestorationOperation,
    ControlledReplayRestorationTarget,
)
from seedmind.research.ndnra.controlled_replay_restoration_permit_lifecycle import (
    ControlledReplayRestorationPermitLifecycleAction,
    ControlledReplayRestorationPermitLifecycleRegistry,
    ControlledReplayRestorationPermitLifecycleStatus,
    ControlledReplayRestorationPermitTransitionRequest,
)


@dataclass(frozen=True, slots=True)
class ControlledRetentionReplayWorkItem:
    """One exact caller-selected real activity occurrence to revisit."""

    work_item_id: str
    source_evidence_id: str
    structure_ids: tuple[str, ...]
    has_learning_authority: bool = False
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("work_item_id", self.work_item_id)
        if not self.work_item_id.startswith("replay-work-item:"):
            raise ValueError("work_item_id must use replay-work-item prefix")
        _validate_code("source_evidence_id", self.source_evidence_id)
        _validate_sorted_unique_codes("structure_ids", self.structure_ids)
        if not self.structure_ids:
            raise ValueError("replay work item structure_ids must not be empty")
        _reject_authority(
            has_learning_authority=self.has_learning_authority,
            has_action_selection_authority=self.has_action_selection_authority,
            has_production_action_authority=self.has_production_action_authority,
            owner="replay work items",
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic caller-selected work evidence."""
        return {
            "work_item_id": self.work_item_id,
            "source_evidence_id": self.source_evidence_id,
            "structure_ids": list(self.structure_ids),
            "has_learning_authority": self.has_learning_authority,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ControlledRetentionReplayRequest:
    """Exact operation request bound to a permit and fresh evidence snapshot."""

    target_permit_id: str
    expected_target_id: str
    expected_source_checkpoint_id: str
    expected_source_checkpoint_checksum: str
    expected_current_checkpoint_id: str
    expected_current_checkpoint_checksum: str
    expected_fresh_evidence_state_id: str
    operation_episode: int
    actor_code: str
    reason_code: str
    work_items: tuple[ControlledRetentionReplayWorkItem, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("target_permit_id", self.target_permit_id),
            ("expected_target_id", self.expected_target_id),
            ("expected_source_checkpoint_id", self.expected_source_checkpoint_id),
            ("expected_current_checkpoint_id", self.expected_current_checkpoint_id),
            ("expected_fresh_evidence_state_id", self.expected_fresh_evidence_state_id),
            ("actor_code", self.actor_code),
            ("reason_code", self.reason_code),
        ):
            _validate_code(name, value)
        _validate_checksum(
            "expected_source_checkpoint_checksum",
            self.expected_source_checkpoint_checksum,
        )
        _validate_checksum(
            "expected_current_checkpoint_checksum",
            self.expected_current_checkpoint_checksum,
        )
        _validate_nonnegative_int("operation_episode", self.operation_episode)
        if self.actor_code != "operation:retention_replay":
            raise ValueError("retention replay requires operation:retention_replay actor")
        if not self.work_items:
            raise ValueError("retention replay requires at least one work item")
        work_item_ids = tuple(item.work_item_id for item in self.work_items)
        if work_item_ids != tuple(sorted(work_item_ids)):
            raise ValueError("replay work items must use stable sorted ordering")
        if len(work_item_ids) != len(set(work_item_ids)):
            raise ValueError("replay work item identities must be unique")
        source_ids = tuple(item.source_evidence_id for item in self.work_items)
        if len(source_ids) != len(set(source_ids)):
            raise ValueError("replay source evidence identities must be unique")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic operation request evidence."""
        return {
            "target_permit_id": self.target_permit_id,
            "expected_target_id": self.expected_target_id,
            "expected_source_checkpoint_id": self.expected_source_checkpoint_id,
            "expected_source_checkpoint_checksum": self.expected_source_checkpoint_checksum,
            "expected_current_checkpoint_id": self.expected_current_checkpoint_id,
            "expected_current_checkpoint_checksum": self.expected_current_checkpoint_checksum,
            "expected_fresh_evidence_state_id": self.expected_fresh_evidence_state_id,
            "operation_episode": self.operation_episode,
            "actor_code": self.actor_code,
            "reason_code": self.reason_code,
            "work_items": [item.snapshot() for item in self.work_items],
        }


@dataclass(frozen=True, slots=True)
class ControlledRetentionReplayItemReceipt:
    """Exact non-learning result for one replayed real activity occurrence."""

    work_item: ControlledRetentionReplayWorkItem
    replay_activity_event_id: str
    maintenance_decision_id: str
    structure_changes: tuple[tuple[str, float, float], ...]
    reactivation_per_structure: float
    factual_confidence_delta: float = 0.0
    mastery_delta: float = 0.0
    has_learning_authority: bool = False
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("replay_activity_event_id", self.replay_activity_event_id)
        _validate_code("maintenance_decision_id", self.maintenance_decision_id)
        _validate_unit("reactivation_per_structure", self.reactivation_per_structure)
        structure_ids = tuple(change[0] for change in self.structure_changes)
        if structure_ids != self.work_item.structure_ids:
            raise ValueError("receipt structure changes must match the replay work item")
        for structure_id, before, after in self.structure_changes:
            _validate_code("structure_id", structure_id)
            _validate_unit("dormancy_before", before)
            _validate_unit("dormancy_after", after)
            if after > before:
                raise ValueError("retention replay cannot increase dormancy")
        if self.factual_confidence_delta != 0.0:
            raise ValueError("retention replay cannot change factual confidence")
        if self.mastery_delta != 0.0:
            raise ValueError("retention replay cannot change mastery")
        _reject_authority(
            has_learning_authority=self.has_learning_authority,
            has_action_selection_authority=self.has_action_selection_authority,
            has_production_action_authority=self.has_production_action_authority,
            owner="replay item receipts",
        )

    @property
    def total_reactivation(self) -> float:
        """Return the exact dormancy reduction achieved across this item."""
        return sum(before - after for _, before, after in self.structure_changes)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic replay item evidence."""
        return {
            "work_item": self.work_item.snapshot(),
            "replay_activity_event_id": self.replay_activity_event_id,
            "maintenance_decision_id": self.maintenance_decision_id,
            "structure_changes": [
                {
                    "structure_id": structure_id,
                    "dormancy_before": before,
                    "dormancy_after": after,
                }
                for structure_id, before, after in self.structure_changes
            ],
            "reactivation_per_structure": self.reactivation_per_structure,
            "total_reactivation": self.total_reactivation,
            "factual_confidence_delta": self.factual_confidence_delta,
            "mastery_delta": self.mastery_delta,
            "has_learning_authority": self.has_learning_authority,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ControlledRetentionReplayReceipt:
    """Deterministic successful receipt used to consume exactly one permit."""

    receipt_id: str
    permit_id: str
    target_id: str
    fresh_evidence_state_id: str
    operation_episode: int
    actor_code: str
    reason_code: str
    items: tuple[ControlledRetentionReplayItemReceipt, ...]
    factual_confidence_delta: float = 0.0
    mastery_delta: float = 0.0
    has_learning_authority: bool = False
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("receipt_id", self.receipt_id),
            ("permit_id", self.permit_id),
            ("target_id", self.target_id),
            ("fresh_evidence_state_id", self.fresh_evidence_state_id),
            ("actor_code", self.actor_code),
            ("reason_code", self.reason_code),
        ):
            _validate_code(name, value)
        _validate_nonnegative_int("operation_episode", self.operation_episode)
        if not self.items:
            raise ValueError("successful retention replay receipt requires items")
        work_item_ids = tuple(item.work_item.work_item_id for item in self.items)
        if work_item_ids != tuple(sorted(work_item_ids)):
            raise ValueError("receipt items must use stable sorted ordering")
        if len(work_item_ids) != len(set(work_item_ids)):
            raise ValueError("receipt work item identities must be unique")
        if self.factual_confidence_delta != 0.0:
            raise ValueError("retention replay receipt cannot change factual confidence")
        if self.mastery_delta != 0.0:
            raise ValueError("retention replay receipt cannot change mastery")
        _reject_authority(
            has_learning_authority=self.has_learning_authority,
            has_action_selection_authority=self.has_action_selection_authority,
            has_production_action_authority=self.has_production_action_authority,
            owner="replay receipts",
        )
        if self.receipt_id != _receipt_id(self._identity_payload()):
            raise ValueError("retention replay receipt identity is inconsistent")

    @property
    def work_item_count(self) -> int:
        return len(self.items)

    @property
    def total_reactivation(self) -> float:
        return sum(item.total_reactivation for item in self.items)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic successful operation evidence."""
        return {"receipt_id": self.receipt_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "permit_id": self.permit_id,
            "target_id": self.target_id,
            "fresh_evidence_state_id": self.fresh_evidence_state_id,
            "operation_episode": self.operation_episode,
            "actor_code": self.actor_code,
            "reason_code": self.reason_code,
            "items": [item.snapshot() for item in self.items],
            "work_item_count": self.work_item_count,
            "total_reactivation": self.total_reactivation,
            "factual_confidence_delta": self.factual_confidence_delta,
            "mastery_delta": self.mastery_delta,
            "has_learning_authority": self.has_learning_authority,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ControlledRetentionReplayResult:
    """New successful state; all caller-supplied input objects remain unchanged."""

    receipt: ControlledRetentionReplayReceipt
    lifecycle_registry: ControlledReplayRestorationPermitLifecycleRegistry
    activity_ledger: ActivityMaintenanceLedger
    adaptive_state: NDNRARuntimeAdaptiveState
    input_state_unchanged: bool

    def __post_init__(self) -> None:
        if not self.input_state_unchanged:
            raise ValueError("controlled replay must preserve all input objects")
        record = self.lifecycle_registry.record_for(self.receipt.permit_id)
        if record.status is not ControlledReplayRestorationPermitLifecycleStatus.CONSUMED:
            raise ValueError("successful replay result requires a consumed permit")
        if record.decisions[0].consumption_reference_code != self.receipt.receipt_id:
            raise ValueError("consumed permit must reference the exact replay receipt")


@dataclass(frozen=True, slots=True)
class ControlledRetentionReplayOperation:
    """Execute one all-or-nothing in-memory replay from exact real activity."""

    def execute(
        self,
        *,
        request: ControlledRetentionReplayRequest,
        fresh_evidence: ControlledReplayRestorationEvidence,
        lifecycle_registry: ControlledReplayRestorationPermitLifecycleRegistry,
        activity_ledger: ActivityMaintenanceLedger,
        adaptive_state: NDNRARuntimeAdaptiveState,
    ) -> ControlledRetentionReplayResult:
        """Return copied success state or raise while leaving all inputs unchanged."""
        lifecycle_before = lifecycle_registry.snapshot()
        activity_before = activity_ledger.snapshot()
        adaptive_before = adaptive_state.to_growth_state()
        graph_before = adaptive_state.graph.snapshot()

        record = lifecycle_registry.record_for(request.target_permit_id)
        if record.status is not ControlledReplayRestorationPermitLifecycleStatus.ISSUED:
            raise ValueError("retention replay requires an issued unused permit")
        permit = record.permit
        target = permit.target
        if target.operation is not ControlledReplayRestorationOperation.RETENTION_REPLAY:
            raise ValueError("retention replay cannot use a restoration permit")
        _validate_request_against_target(request, permit.permit_id, target)
        _validate_fresh_evidence(
            request=request,
            fresh_evidence=fresh_evidence,
            permit_evidence=permit.evidence,
            source_evidence_ids=target.source_evidence_ids,
        )
        if not permit.valid_at(request.operation_episode):
            raise ValueError("retention replay requires an unexpired permit")
        if len(request.work_items) > target.maximum_work_items:
            raise ValueError("retention replay work-item bound exceeded")

        copied_ledger = deepcopy(activity_ledger)
        copied_adaptive = deepcopy(adaptive_state)
        item_receipts: list[ControlledRetentionReplayItemReceipt] = []
        approved_sources = set(target.source_evidence_ids)
        for item in request.work_items:
            if item.source_evidence_id not in approved_sources:
                raise ValueError("replay work item uses unapproved source evidence")
            source = activity_ledger.request_for(item.source_evidence_id)
            if source.origin is not ExperienceOrigin.REAL:
                raise ValueError("retention replay source must be real activity")
            if item.structure_ids != source.structure_ids:
                raise ValueError("replay work item does not exactly reconstruct source structures")
            replay_activity = ActivityMaintenanceRequest(
                event_id=_replay_activity_event_id(
                    permit_id=permit.permit_id,
                    operation_episode=request.operation_episode,
                    item=item,
                ),
                cycle=request.operation_episode,
                origin=ExperienceOrigin.REPLAY,
                structure_ids=item.structure_ids,
                supporting_real_event_ids=(item.source_evidence_id,),
                relevance=source.relevance,
                helpfulness=source.helpfulness,
                prediction_accuracy=source.prediction_accuracy,
                real_evidence_strength=source.real_evidence_strength,
                safety_critical=source.safety_critical,
                rare_use=source.rare_use,
                harmful=source.harmful,
                redundant=source.redundant,
            )
            decision = copied_ledger.consider(replay_activity)
            if not decision.maintenance_applied:
                raise ValueError(f"replay maintenance denied for work item: {decision.reason_code}")
            application = copied_adaptive.apply_activity_maintenance(decision)
            item_receipts.append(_item_receipt(item, decision, application))

        receipt_payload = {
            "permit_id": permit.permit_id,
            "target_id": target.target_id,
            "fresh_evidence_state_id": fresh_evidence.evidence_state_id,
            "operation_episode": request.operation_episode,
            "actor_code": request.actor_code,
            "reason_code": request.reason_code,
            "items": [item.snapshot() for item in item_receipts],
            "work_item_count": len(item_receipts),
            "total_reactivation": sum(item.total_reactivation for item in item_receipts),
            "factual_confidence_delta": 0.0,
            "mastery_delta": 0.0,
            "has_learning_authority": False,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        receipt = ControlledRetentionReplayReceipt(
            receipt_id=_receipt_id(receipt_payload),
            permit_id=permit.permit_id,
            target_id=target.target_id,
            fresh_evidence_state_id=fresh_evidence.evidence_state_id,
            operation_episode=request.operation_episode,
            actor_code=request.actor_code,
            reason_code=request.reason_code,
            items=tuple(item_receipts),
        )
        consumed_registry = lifecycle_registry.transition(
            ControlledReplayRestorationPermitTransitionRequest(
                target_permit_id=permit.permit_id,
                expected_operation=target.operation,
                expected_target_id=target.target_id,
                expected_source_checkpoint_id=target.source_checkpoint_id,
                expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
                expected_current_checkpoint_id=target.expected_current_checkpoint_id,
                expected_current_checkpoint_checksum=(target.expected_current_checkpoint_checksum),
                expected_evidence_state_id=permit.evidence.evidence_state_id,
                action=ControlledReplayRestorationPermitLifecycleAction.CONSUME,
                decision_episode=request.operation_episode,
                actor_code=request.actor_code,
                reason_code="bounded_retention_replay_succeeded",
                consumption_reference_code=receipt.receipt_id,
            )
        )

        unchanged = bool(
            lifecycle_registry.snapshot() == lifecycle_before
            and activity_ledger.snapshot() == activity_before
            and adaptive_state.to_growth_state() == adaptive_before
            and adaptive_state.graph.snapshot() == graph_before
        )
        return ControlledRetentionReplayResult(
            receipt=receipt,
            lifecycle_registry=consumed_registry,
            activity_ledger=copied_ledger,
            adaptive_state=copied_adaptive,
            input_state_unchanged=unchanged,
        )


def _item_receipt(
    item: ControlledRetentionReplayWorkItem,
    decision: ActivityMaintenanceDecision,
    application: ActivityMaintenanceApplication,
) -> ControlledRetentionReplayItemReceipt:
    return ControlledRetentionReplayItemReceipt(
        work_item=item,
        replay_activity_event_id=decision.request.event_id,
        maintenance_decision_id=decision.decision_id,
        structure_changes=application.changes,
        reactivation_per_structure=decision.per_structure_reactivation,
    )


def _validate_request_against_target(
    request: ControlledRetentionReplayRequest,
    permit_id: str,
    target: ControlledReplayRestorationTarget,
) -> None:
    if request.target_permit_id != permit_id:
        raise ValueError("replay request targets a different permit")
    if request.expected_target_id != target.target_id:
        raise ValueError("replay request targets a different replay target")
    if request.expected_source_checkpoint_id != target.source_checkpoint_id:
        raise ValueError("replay request targets a different source checkpoint")
    if request.expected_source_checkpoint_checksum != target.source_checkpoint_checksum:
        raise ValueError("replay request targets a different source checkpoint checksum")
    if request.expected_current_checkpoint_id != target.expected_current_checkpoint_id:
        raise ValueError("replay request targets a different current checkpoint")
    if request.expected_current_checkpoint_checksum != target.expected_current_checkpoint_checksum:
        raise ValueError("replay request targets a different current checkpoint checksum")


def _validate_fresh_evidence(
    *,
    request: ControlledRetentionReplayRequest,
    fresh_evidence: ControlledReplayRestorationEvidence,
    permit_evidence: ControlledReplayRestorationEvidence,
    source_evidence_ids: tuple[str, ...],
) -> None:
    if request.operation_episode != fresh_evidence.captured_episode:
        raise ValueError("replay requires evidence captured in the operation episode")
    if request.expected_fresh_evidence_state_id != fresh_evidence.evidence_state_id:
        raise ValueError("replay request targets different fresh evidence")
    if not fresh_evidence.checksum_verified:
        raise ValueError("replay requires checksum-verified fresh evidence")
    if fresh_evidence.used_fallback:
        raise ValueError("replay cannot use fallback fresh evidence")
    if fresh_evidence.current_checkpoint_id != request.expected_current_checkpoint_id:
        raise ValueError("fresh evidence current checkpoint drifted")
    if fresh_evidence.current_checkpoint_checksum != request.expected_current_checkpoint_checksum:
        raise ValueError("fresh evidence current checkpoint checksum drifted")
    if (
        fresh_evidence.checkpoint_checksum(request.expected_source_checkpoint_id)
        != request.expected_source_checkpoint_checksum
    ):
        raise ValueError("fresh evidence source checkpoint checksum drifted")
    if (
        fresh_evidence.available_checkpoint_checksums
        != permit_evidence.available_checkpoint_checksums
    ):
        raise ValueError("fresh available checkpoint evidence drifted")
    if fresh_evidence.available_evidence_ids != permit_evidence.available_evidence_ids:
        raise ValueError("fresh source evidence identities drifted")
    if set(source_evidence_ids) - set(fresh_evidence.available_evidence_ids):
        raise ValueError("approved replay evidence is missing from fresh evidence")


def _replay_activity_event_id(
    *,
    permit_id: str,
    operation_episode: int,
    item: ControlledRetentionReplayWorkItem,
) -> str:
    return _identity(
        "replay-activity",
        {
            "permit_id": permit_id,
            "operation_episode": operation_episode,
            "work_item": item.snapshot(),
        },
    )


def _receipt_id(payload: dict[str, object]) -> str:
    return _identity("retention-replay-receipt", payload)


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
    has_learning_authority: bool,
    has_action_selection_authority: bool,
    has_production_action_authority: bool,
    owner: str,
) -> None:
    if has_learning_authority:
        raise ValueError(f"{owner} cannot update learning evidence")
    if has_action_selection_authority:
        raise ValueError(f"{owner} cannot select actions")
    if has_production_action_authority:
        raise ValueError(f"{owner} cannot control production actions")


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
    for value in values:
        _validate_code(name, value)


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_checksum(name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 checksum")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
