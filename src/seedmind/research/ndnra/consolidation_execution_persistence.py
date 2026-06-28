"""Versioned restart-safe persistence for bounded NDNRA execution evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from itertools import pairwise

from seedmind.research.ndnra.consolidation import ConsolidationRejectionReason
from seedmind.research.ndnra.consolidation_execution_approval import (
    ConsolidationExecutionPermit,
)
from seedmind.research.ndnra.consolidation_execution_commit import (
    ConsolidationExecutionCommitReceipt,
    ConsolidationExecutionCommitResult,
)
from seedmind.research.ndnra.consolidation_execution_permit_lifecycle import (
    ConsolidationExecutionPermitLifecycleAction,
    ConsolidationExecutionPermitLifecycleRecord,
    ConsolidationExecutionPermitLifecycleRegistry,
    ConsolidationExecutionPermitLifecycleStatus,
    ConsolidationExecutionPermitTransitionDecision,
    ConsolidationExecutionPermitTransitionRequest,
)
from seedmind.research.ndnra.consolidation_persistence import (
    NDNRAConsolidationCheckpoint,
    restore_consolidation_application,
)
from seedmind.research.ndnra.consolidation_proposal_persistence import (
    restore_consolidation_candidate,
    restore_consolidation_schedule_proposal,
    restore_mastery_profile,
)
from seedmind.research.ndnra.consolidation_proposal_revalidation import (
    ConsolidationProposalRevalidationDecision,
    ConsolidationProposalRevalidationStatus,
)

EXECUTION_SCHEMA = "seedmind.ndnra.consolidation_execution"
EXECUTION_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class NDNRAExecutionCheckpoint:
    """Complete non-authoritative permit lifecycle and successful receipt evidence."""

    permit_registry: ConsolidationExecutionPermitLifecycleRegistry = field(
        default_factory=ConsolidationExecutionPermitLifecycleRegistry
    )
    receipts: tuple[ConsolidationExecutionCommitReceipt, ...] = ()
    automatic_execution_count: int = 0
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        if self.automatic_execution_count != 0:
            raise ValueError("execution checkpoints cannot contain automatic executions")
        if self.has_execution_authority:
            raise ValueError("execution checkpoints never have execution authority")
        permit_ids = tuple(record.permit.permit_id for record in self.permit_registry.records)
        if permit_ids != tuple(sorted(permit_ids)):
            raise ValueError("execution permits must use stable permit ordering")
        execution_ids = tuple(receipt.execution_id for receipt in self.receipts)
        if execution_ids != tuple(sorted(execution_ids)):
            raise ValueError("execution receipts must use stable execution ordering")
        if len(execution_ids) != len(set(execution_ids)):
            raise ValueError("execution receipt identities must be unique")
        candidate_ids = tuple(
            receipt.application.candidate.candidate_id for receipt in self.receipts
        )
        if len(candidate_ids) != len(set(candidate_ids)):
            raise ValueError("a consolidation candidate cannot have duplicate receipts")

        receipt_by_permit = {receipt.permit.permit_id: receipt for receipt in self.receipts}
        for record in self.permit_registry.records:
            receipt = receipt_by_permit.get(record.permit.permit_id)
            if record.status is ConsolidationExecutionPermitLifecycleStatus.CONSUMED:
                if receipt is None:
                    raise ValueError("consumed permit requires one execution receipt")
                if record.decisions != (receipt.permit_transition,):
                    raise ValueError("consumed transition must exactly match its receipt")
                if record.decisions[0].consumption_reference_code != receipt.execution_id:
                    raise ValueError("consumption reference must equal execution identity")
            elif receipt is not None:
                raise ValueError("only a consumed permit may have an execution receipt")
        registered_permits = set(permit_ids)
        if any(receipt.permit.permit_id not in registered_permits for receipt in self.receipts):
            raise ValueError("execution receipt requires its retained permit lifecycle")

    @classmethod
    def empty(cls) -> NDNRAExecutionCheckpoint:
        """Return the explicit migration target for schemas without execution state."""
        return cls()

    @classmethod
    def with_issued_permit(
        cls,
        permit: ConsolidationExecutionPermit,
        *,
        previous: NDNRAExecutionCheckpoint | None = None,
    ) -> NDNRAExecutionCheckpoint:
        """Retain one newly issued permit without applying consolidation."""
        checkpoint = cls.empty() if previous is None else previous
        registry = checkpoint.permit_registry.add(permit)
        return cls(
            permit_registry=_canonical_registry(registry),
            receipts=checkpoint.receipts,
        )

    def record_commit(
        self,
        result: ConsolidationExecutionCommitResult,
    ) -> NDNRAExecutionCheckpoint:
        """Return complete consumed lifecycle and receipt evidence for one commit."""
        prior = self.permit_registry.record_for(result.receipt.permit.permit_id)
        if prior.status is not ConsolidationExecutionPermitLifecycleStatus.ISSUED:
            raise ValueError("durable execution requires a previously issued permit")
        if prior.permit != result.receipt.permit:
            raise ValueError("durable execution receipt targets a different permit")
        expected_ids = {record.permit.permit_id for record in self.permit_registry.records}
        result_ids = {record.permit.permit_id for record in result.permit_registry.records}
        if expected_ids != result_ids:
            raise ValueError("commit result must preserve the complete permit registry")
        return NDNRAExecutionCheckpoint(
            permit_registry=_canonical_registry(result.permit_registry),
            receipts=tuple(
                sorted((*self.receipts, result.receipt), key=lambda item: item.execution_id)
            ),
        )

    def validate_consolidation_checkpoint(
        self,
        consolidation: NDNRAConsolidationCheckpoint,
    ) -> None:
        """Validate exact receipt-to-application relations without invoking cognition."""
        state = consolidation.state
        if self.receipts and state is None:
            raise ValueError("execution receipts require persisted consolidation state")
        applications = {
            application.candidate.candidate_id: application
            for application in consolidation.active_applications
        }
        permit_candidate_status = {
            record.permit.proposal.candidate.candidate_id: record.status
            for record in self.permit_registry.records
        }
        receipt_candidates = {
            receipt.application.candidate.candidate_id for receipt in self.receipts
        }
        for candidate_id, status in permit_candidate_status.items():
            if candidate_id in applications and status is not (
                ConsolidationExecutionPermitLifecycleStatus.CONSUMED
            ):
                raise ValueError("unconsumed permit candidate cannot already be applied")
            if (
                candidate_id in applications
                and status is ConsolidationExecutionPermitLifecycleStatus.CONSUMED
                and candidate_id not in receipt_candidates
            ):
                raise ValueError("applied consumed candidate requires receipt history")
        for receipt in self.receipts:
            candidate_id = receipt.application.candidate.candidate_id
            if applications.get(candidate_id) != receipt.application:
                raise ValueError("receipt application must match persisted application history")
            assert state is not None
            if candidate_id not in state.applied_candidate_ids:
                raise ValueError("receipt candidate must exist in consolidation state")

        ordered = tuple(
            sorted(self.receipts, key=lambda item: (item.execution_episode, item.execution_id))
        )
        for previous, current in pairwise(ordered):
            if current.application.before != previous.application.after:
                raise ValueError("execution receipt applications must form one exact state chain")
        if ordered and ordered[-1].application.after != state:
            raise ValueError("latest execution receipt must match persisted consolidation state")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe execution persistence evidence."""
        return {
            "schema": EXECUTION_SCHEMA,
            "schema_version": EXECUTION_SCHEMA_VERSION,
            "permit_registry": self.permit_registry.snapshot(),
            "receipts": [receipt.snapshot() for receipt in self.receipts],
            "automatic_execution_count": self.automatic_execution_count,
            "has_execution_authority": self.has_execution_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> NDNRAExecutionCheckpoint:
        """Restore exact permit and receipt evidence without applying anything."""
        values = _require_mapping("execution checkpoint", snapshot)
        if _require_string(values, "schema") != EXECUTION_SCHEMA:
            raise ValueError("execution checkpoint schema is incompatible")
        if _require_int(values, "schema_version") != EXECUTION_SCHEMA_VERSION:
            raise ValueError("execution checkpoint version is incompatible")
        checkpoint = cls(
            permit_registry=_restore_registry(values.get("permit_registry")),
            receipts=tuple(
                sorted(
                    (_restore_receipt(item) for item in _require_list(values, "receipts")),
                    key=lambda item: item.execution_id,
                )
            ),
            automatic_execution_count=_require_int(values, "automatic_execution_count"),
            has_execution_authority=_require_bool(values, "has_execution_authority"),
        )
        if checkpoint.snapshot() != dict(values):
            raise ValueError("execution checkpoint did not round-trip exactly")
        return checkpoint


def _canonical_registry(
    registry: ConsolidationExecutionPermitLifecycleRegistry,
) -> ConsolidationExecutionPermitLifecycleRegistry:
    return ConsolidationExecutionPermitLifecycleRegistry(
        records=tuple(sorted(registry.records, key=lambda item: item.permit.permit_id))
    )


def _restore_registry(snapshot: object) -> ConsolidationExecutionPermitLifecycleRegistry:
    values = _require_mapping("execution permit registry", snapshot)
    registry = ConsolidationExecutionPermitLifecycleRegistry(
        records=tuple(
            sorted(
                (_restore_record(item) for item in _require_list(values, "records")),
                key=lambda item: item.permit.permit_id,
            )
        ),
        has_application_authority=_require_bool(values, "has_application_authority"),
    )
    if _require_int(values, "consumption_count") != registry.consumption_count:
        raise ValueError("persisted permit consumption count is inconsistent")
    if registry.snapshot() != dict(values):
        raise ValueError("execution permit registry did not round-trip exactly")
    return registry


def _restore_record(snapshot: object) -> ConsolidationExecutionPermitLifecycleRecord:
    values = _require_mapping("execution permit lifecycle record", snapshot)
    permit = _restore_permit(values.get("permit"))
    decisions = tuple(
        _restore_transition(item, expected_permit=permit)
        for item in _require_list(values, "decisions")
    )
    record = ConsolidationExecutionPermitLifecycleRecord(
        permit=permit,
        status=ConsolidationExecutionPermitLifecycleStatus(_require_string(values, "status")),
        decisions=decisions,
        has_application_authority=_require_bool(values, "has_application_authority"),
    )
    if _require_bool(values, "is_terminal") is not record.is_terminal:
        raise ValueError("persisted permit terminal state is inconsistent")
    if _require_int(values, "consumption_count") != record.consumption_count:
        raise ValueError("persisted permit record consumption count is inconsistent")
    if record.snapshot() != dict(values):
        raise ValueError("execution permit lifecycle did not round-trip exactly")
    return record


def _restore_transition(
    snapshot: object,
    *,
    expected_permit: ConsolidationExecutionPermit,
) -> ConsolidationExecutionPermitTransitionDecision:
    values = _require_mapping("execution permit transition", snapshot)
    permit = _restore_permit(values.get("permit"))
    if permit != expected_permit:
        raise ValueError("persisted permit transition targets a different permit")
    raw_reference = values.get("consumption_reference_code")
    request = ConsolidationExecutionPermitTransitionRequest(
        target_permit_id=permit.permit_id,
        expected_proposal_id=permit.proposal.proposal_id,
        expected_candidate_id=permit.proposal.candidate.candidate_id,
        action=ConsolidationExecutionPermitLifecycleAction(_require_string(values, "action")),
        decision_episode=_require_int(values, "decision_episode"),
        actor_code=_require_string(values, "actor_code"),
        reason_code=_require_string(values, "reason_code"),
        consumption_reference_code=(
            None if raw_reference is None else _require_string(values, "consumption_reference_code")
        ),
    )
    decision = (
        ConsolidationExecutionPermitLifecycleRecord.issued(permit).transition(request).decisions[0]
    )
    if _require_string(values, "decision_id") != decision.decision_id:
        raise ValueError("persisted permit transition identity is invalid")
    if _require_string(values, "status") != decision.status.value:
        raise ValueError("persisted permit transition status is inconsistent")
    if _require_bool(values, "has_application_authority"):
        raise ValueError("persisted permit transition cannot apply consolidation")
    if decision.snapshot() != dict(values):
        raise ValueError("execution permit transition did not round-trip exactly")
    return decision


def _restore_permit(snapshot: object) -> ConsolidationExecutionPermit:
    values = _require_mapping("execution permit", snapshot)
    proposal = restore_consolidation_schedule_proposal(values.get("proposal"))
    revalidation = _restore_revalidation(values.get("revalidation"))
    accepted_review_decision_id = _require_string(values, "accepted_review_decision_id")
    issued_episode = _require_int(values, "issued_episode")
    expires_after_episode = _require_int(values, "expires_after_episode")
    approver_code = _require_string(values, "approver_code")
    reason_code = _require_string(values, "reason_code")
    authorizes_one_application = _require_bool(values, "authorizes_one_application")
    single_use = _require_bool(values, "single_use")
    payload: dict[str, object] = {
        "proposal": proposal.snapshot(),
        "accepted_review_decision_id": accepted_review_decision_id,
        "revalidation": revalidation.snapshot(),
        "issued_episode": issued_episode,
        "expires_after_episode": expires_after_episode,
        "approver_code": approver_code,
        "reason_code": reason_code,
        "authorizes_one_application": authorizes_one_application,
        "single_use": single_use,
    }
    expected_id = _identity("consolidation-execution-permit", payload)
    if _require_string(values, "permit_id") != expected_id:
        raise ValueError("persisted execution permit identity is invalid")
    permit = ConsolidationExecutionPermit(
        permit_id=expected_id,
        proposal=proposal,
        accepted_review_decision_id=accepted_review_decision_id,
        revalidation=revalidation,
        issued_episode=issued_episode,
        expires_after_episode=expires_after_episode,
        approver_code=approver_code,
        reason_code=reason_code,
        authorizes_one_application=authorizes_one_application,
        single_use=single_use,
        consumed=_require_bool(values, "consumed"),
        application_count=_require_int(values, "application_count"),
        has_direct_execution_authority=_require_bool(values, "has_direct_execution_authority"),
    )
    if permit.snapshot() != dict(values):
        raise ValueError("execution permit did not round-trip exactly")
    return permit


def _restore_revalidation(snapshot: object) -> ConsolidationProposalRevalidationDecision:
    values = _require_mapping("proposal revalidation decision", snapshot)
    proposal = restore_consolidation_schedule_proposal(values.get("proposal"))
    raw_candidate = values.get("current_candidate")
    current_candidate = (
        None if raw_candidate is None else restore_consolidation_candidate(raw_candidate)
    )
    raw_superseding = values.get("superseding_proposal")
    superseding = (
        None
        if raw_superseding is None
        else restore_consolidation_schedule_proposal(raw_superseding)
    )
    reasons = tuple(
        ConsolidationRejectionReason(value)
        for value in _require_string_list(values, "eligibility_reasons")
    )
    payload: dict[str, object] = {
        "status": _require_string(values, "status"),
        "proposal": proposal.snapshot(),
        "current_mastery": restore_mastery_profile(values.get("current_mastery")).snapshot(),
        "current_candidate": (None if current_candidate is None else current_candidate.snapshot()),
        "superseding_proposal": (None if superseding is None else superseding.snapshot()),
        "eligibility_reasons": [reason.value for reason in reasons],
        "source_events_available": _require_bool(values, "source_events_available"),
        "broad_mastery_current": _require_bool(values, "broad_mastery_current"),
        "contradiction_free": _require_bool(values, "contradiction_free"),
        "assemblies_available": _require_bool(values, "assemblies_available"),
        "routes_available": _require_bool(values, "routes_available"),
        "candidate_identity_current": _require_bool(values, "candidate_identity_current"),
    }
    expected_id = _identity("consolidation-revalidation", payload)
    if _require_string(values, "decision_id") != expected_id:
        raise ValueError("persisted proposal revalidation identity is invalid")
    decision = ConsolidationProposalRevalidationDecision(
        decision_id=expected_id,
        status=ConsolidationProposalRevalidationStatus(str(payload["status"])),
        proposal=proposal,
        current_mastery=restore_mastery_profile(values.get("current_mastery")),
        current_candidate=current_candidate,
        superseding_proposal=superseding,
        eligibility_reasons=reasons,
        source_events_available=bool(payload["source_events_available"]),
        broad_mastery_current=bool(payload["broad_mastery_current"]),
        contradiction_free=bool(payload["contradiction_free"]),
        assemblies_available=bool(payload["assemblies_available"]),
        routes_available=bool(payload["routes_available"]),
        candidate_identity_current=bool(payload["candidate_identity_current"]),
        has_execution_authority=_require_bool(values, "has_execution_authority"),
    )
    if decision.snapshot() != dict(values):
        raise ValueError("proposal revalidation did not round-trip exactly")
    return decision


def _restore_receipt(snapshot: object) -> ConsolidationExecutionCommitReceipt:
    values = _require_mapping("execution receipt", snapshot)
    permit = _restore_permit(values.get("permit"))
    transition = _restore_transition(
        values.get("permit_transition"),
        expected_permit=permit,
    )
    receipt = ConsolidationExecutionCommitReceipt(
        execution_id=_require_string(values, "execution_id"),
        permit=permit,
        revalidation=_restore_revalidation(values.get("revalidation")),
        application=restore_consolidation_application(values.get("application")),
        permit_transition=transition,
        execution_episode=_require_int(values, "execution_episode"),
        executor_code=_require_string(values, "executor_code"),
        reason_code=_require_string(values, "reason_code"),
        application_count=_require_int(values, "application_count"),
        replay_trigger_count=_require_int(values, "replay_trigger_count"),
        restoration_trigger_count=_require_int(values, "restoration_trigger_count"),
        has_production_action_authority=_require_bool(values, "has_production_action_authority"),
    )
    if receipt.snapshot() != dict(values):
        raise ValueError("execution receipt did not round-trip exactly")
    return receipt


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"{prefix}:{hashlib.sha256(canonical).hexdigest()}"


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
    if not isinstance(value, str) or not value.strip() or not value.isascii():
        raise ValueError(f"{key} must be non-empty ASCII text")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{key} must be a non-negative integer")
    return value


def _require_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _require_string_list(values: Mapping[str, object], key: str) -> list[str]:
    result: list[str] = []
    for item in _require_list(values, key):
        if not isinstance(item, str) or not item.strip() or not item.isascii():
            raise ValueError(f"{key} must contain non-empty ASCII strings")
        result.append(item)
    return result


__all__ = [
    "EXECUTION_SCHEMA",
    "EXECUTION_SCHEMA_VERSION",
    "NDNRAExecutionCheckpoint",
]
