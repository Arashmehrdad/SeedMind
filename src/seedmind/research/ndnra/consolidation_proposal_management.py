"""Bounded in-memory management for NDNRA consolidation proposal lifecycles."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from seedmind.research.ndnra.consolidation_proposal_history import (
    ConsolidationProposalLifecycleRecord,
)
from seedmind.research.ndnra.consolidation_proposal_lifecycle import (
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewRequest,
)
from seedmind.research.ndnra.consolidation_scheduling import (
    ConsolidationScheduleProposal,
)


class ConsolidationProposalManagementAction(StrEnum):
    """Explicit caller-supplied management action over one active proposal."""

    EXPIRE = "expire"
    REPLACE = "replace"


class ConsolidationProposalDisposition(StrEnum):
    """Administrative disposition separate from review and execution authority."""

    ACTIVE = "active"
    EXPIRED = "expired"
    REPLACED = "replaced"


@dataclass(frozen=True, slots=True)
class ConsolidationProposalManagementRequest:
    """Explicit expiry or replacement request for one known proposal."""

    target_proposal_id: str
    expected_candidate_id: str
    action: ConsolidationProposalManagementAction
    decision_episode: int
    reviewer_code: str
    reason_code: str
    replacement_proposal: ConsolidationScheduleProposal | None = None

    def __post_init__(self) -> None:
        _validate_code("target_proposal_id", self.target_proposal_id)
        _validate_code("expected_candidate_id", self.expected_candidate_id)
        _validate_nonnegative_int("decision_episode", self.decision_episode)
        _validate_code("reviewer_code", self.reviewer_code)
        _validate_code("reason_code", self.reason_code)
        if self.action is ConsolidationProposalManagementAction.REPLACE:
            if self.replacement_proposal is None:
                raise ValueError("replacement action requires replacement_proposal")
        elif self.replacement_proposal is not None:
            raise ValueError("only replacement action may include replacement_proposal")


@dataclass(frozen=True, slots=True)
class ConsolidationProposalManagementDecision:
    """Immutable management evidence with no consolidation execution authority."""

    decision_id: str
    target_proposal_id: str
    target_candidate_id: str
    action: ConsolidationProposalManagementAction
    disposition: ConsolidationProposalDisposition
    decision_episode: int
    reviewer_code: str
    reason_code: str
    replacement_proposal: ConsolidationScheduleProposal | None = None
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("decision_id", self.decision_id)
        _validate_code("target_proposal_id", self.target_proposal_id)
        _validate_code("target_candidate_id", self.target_candidate_id)
        _validate_nonnegative_int("decision_episode", self.decision_episode)
        _validate_code("reviewer_code", self.reviewer_code)
        _validate_code("reason_code", self.reason_code)
        expected_disposition = _disposition_for(self.action)
        if self.disposition is not expected_disposition:
            raise ValueError("management action and disposition are inconsistent")
        if self.action is ConsolidationProposalManagementAction.REPLACE:
            if self.replacement_proposal is None:
                raise ValueError("replacement decision requires replacement_proposal")
        elif self.replacement_proposal is not None:
            raise ValueError("only replacement decisions may include replacement_proposal")
        if self.has_execution_authority:
            raise ValueError("management decisions must never have execution authority")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe management evidence."""
        return {
            "decision_id": self.decision_id,
            "target_proposal_id": self.target_proposal_id,
            "target_candidate_id": self.target_candidate_id,
            "action": self.action.value,
            "disposition": self.disposition.value,
            "decision_episode": self.decision_episode,
            "reviewer_code": self.reviewer_code,
            "reason_code": self.reason_code,
            "replacement_proposal": (
                None if self.replacement_proposal is None else self.replacement_proposal.snapshot()
            ),
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationProposalManagedRecord:
    """One review lifecycle plus an optional terminal management decision."""

    lifecycle: ConsolidationProposalLifecycleRecord
    disposition: ConsolidationProposalDisposition = ConsolidationProposalDisposition.ACTIVE
    management_decision: ConsolidationProposalManagementDecision | None = None
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_execution_authority:
            raise ValueError("managed records must never have execution authority")
        if self.disposition is ConsolidationProposalDisposition.ACTIVE:
            if self.management_decision is not None:
                raise ValueError("active managed records cannot contain management decisions")
            return
        if self.management_decision is None:
            raise ValueError("closed managed records require a management decision")
        decision = self.management_decision
        if decision.disposition is not self.disposition:
            raise ValueError("managed record disposition must match management decision")
        proposal = self.lifecycle.proposal
        if decision.target_proposal_id != proposal.proposal_id:
            raise ValueError("management decision targets a different proposal")
        if decision.target_candidate_id != proposal.candidate.candidate_id:
            raise ValueError("management decision targets a different candidate")
        if decision.decision_episode <= _latest_lifecycle_episode(self.lifecycle):
            raise ValueError("management decision must follow lifecycle history")

    @classmethod
    def pending(
        cls,
        proposal: ConsolidationScheduleProposal,
    ) -> ConsolidationProposalManagedRecord:
        """Create one active pending managed record."""
        return cls(lifecycle=ConsolidationProposalLifecycleRecord.pending(proposal))

    @property
    def proposal(self) -> ConsolidationScheduleProposal:
        """Return the immutable scheduling proposal."""
        return self.lifecycle.proposal

    @property
    def is_active(self) -> bool:
        """Return whether this record consumes lifecycle capacity."""
        return (
            self.disposition is ConsolidationProposalDisposition.ACTIVE
            and self.lifecycle.status is not ConsolidationProposalLifecycleStatus.REJECTED
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe managed lifecycle evidence."""
        return {
            "lifecycle": self.lifecycle.snapshot(),
            "disposition": self.disposition.value,
            "management_decision": (
                None if self.management_decision is None else self.management_decision.snapshot()
            ),
            "is_active": self.is_active,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationProposalLifecycleRegistry:
    """Immutable bounded collection of proposal lifecycle records."""

    records: tuple[ConsolidationProposalManagedRecord, ...] = ()
    maximum_active_records: int = 1
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        _validate_positive_int("maximum_active_records", self.maximum_active_records)
        if self.has_execution_authority:
            raise ValueError("lifecycle registry must never have execution authority")
        proposal_ids = tuple(record.proposal.proposal_id for record in self.records)
        if len(proposal_ids) != len(set(proposal_ids)):
            raise ValueError("registry proposal identities must be unique")
        active = self.active_records
        if len(active) > self.maximum_active_records:
            raise ValueError("active lifecycle records exceed registry capacity")
        active_lessons = tuple(record.proposal.candidate.lesson_identity for record in active)
        if len(active_lessons) != len(set(active_lessons)):
            raise ValueError("only one active proposal per lesson is permitted")

    @property
    def active_records(self) -> tuple[ConsolidationProposalManagedRecord, ...]:
        """Return records that currently consume bounded lifecycle capacity."""
        return tuple(record for record in self.records if record.is_active)

    def add(
        self,
        proposal: ConsolidationScheduleProposal,
    ) -> ConsolidationProposalLifecycleRegistry:
        """Add one pending proposal without exceeding active capacity."""
        if any(record.proposal.proposal_id == proposal.proposal_id for record in self.records):
            raise ValueError("proposal identity already exists in lifecycle registry")
        if any(
            record.is_active
            and record.proposal.candidate.lesson_identity == proposal.candidate.lesson_identity
            for record in self.records
        ):
            raise ValueError("active proposal already exists for this lesson")
        if len(self.active_records) >= self.maximum_active_records:
            raise ValueError("active lifecycle capacity reached")
        return self._replace_records(
            (*self.records, ConsolidationProposalManagedRecord.pending(proposal))
        )

    def review(
        self,
        request: ConsolidationProposalReviewRequest,
    ) -> ConsolidationProposalLifecycleRegistry:
        """Apply one pure review to an active record and preserve prior registry."""
        index, record = self._target(request.proposal.proposal_id)
        if record.proposal != request.proposal:
            raise ValueError("review request contains stale proposal evidence")
        if not record.is_active:
            raise ValueError("proposal lifecycle record is not active")
        updated = ConsolidationProposalManagedRecord(
            lifecycle=record.lifecycle.review(request),
        )
        return self._replace_at(index, updated)

    def manage(
        self,
        request: ConsolidationProposalManagementRequest,
    ) -> ConsolidationProposalLifecycleRegistry:
        """Expire or replace one active record without executing consolidation."""
        index, record = self._target(request.target_proposal_id)
        proposal = record.proposal
        if proposal.candidate.candidate_id != request.expected_candidate_id:
            raise ValueError("candidate identity mismatch for lifecycle request")
        if not record.is_active:
            raise ValueError("proposal lifecycle record is not active")
        if request.decision_episode <= _latest_lifecycle_episode(record.lifecycle):
            raise ValueError("management decision must follow lifecycle history")

        replacement = request.replacement_proposal
        if request.action is ConsolidationProposalManagementAction.REPLACE:
            if replacement is None:
                raise RuntimeError("validated replacement request lost its proposal")
            _validate_replacement(record.proposal, replacement, request.decision_episode)
            if any(item.proposal.proposal_id == replacement.proposal_id for item in self.records):
                raise ValueError("replacement proposal identity already exists")

        decision = _management_decision(record, request)
        closed = ConsolidationProposalManagedRecord(
            lifecycle=record.lifecycle,
            disposition=decision.disposition,
            management_decision=decision,
        )
        updated_records = (*self.records[:index], closed, *self.records[index + 1 :])
        if replacement is not None:
            updated_records = (
                *updated_records,
                ConsolidationProposalManagedRecord.pending(replacement),
            )
        return self._replace_records(updated_records)

    def record_for(
        self,
        proposal_id: str,
    ) -> ConsolidationProposalManagedRecord:
        """Return one exact record or reject a stale proposal identity."""
        return self._target(proposal_id)[1]

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe registry evidence."""
        return {
            "records": tuple(record.snapshot() for record in self.records),
            "maximum_active_records": self.maximum_active_records,
            "active_record_count": len(self.active_records),
            "has_execution_authority": self.has_execution_authority,
        }

    def _target(
        self,
        proposal_id: str,
    ) -> tuple[int, ConsolidationProposalManagedRecord]:
        _validate_code("proposal_id", proposal_id)
        for index, record in enumerate(self.records):
            if record.proposal.proposal_id == proposal_id:
                return index, record
        raise ValueError("stale proposal identity is not present in lifecycle registry")

    def _replace_at(
        self,
        index: int,
        record: ConsolidationProposalManagedRecord,
    ) -> ConsolidationProposalLifecycleRegistry:
        return self._replace_records((*self.records[:index], record, *self.records[index + 1 :]))

    def _replace_records(
        self,
        records: tuple[ConsolidationProposalManagedRecord, ...],
    ) -> ConsolidationProposalLifecycleRegistry:
        return ConsolidationProposalLifecycleRegistry(
            records=records,
            maximum_active_records=self.maximum_active_records,
        )


def _validate_replacement(
    current: ConsolidationScheduleProposal,
    replacement: ConsolidationScheduleProposal,
    decision_episode: int,
) -> None:
    if replacement.proposal_id == current.proposal_id:
        raise ValueError("replacement proposal must differ from current proposal")
    if replacement.candidate.lesson_identity != current.candidate.lesson_identity:
        raise ValueError("replacement proposal must target the same lesson")
    if replacement.proposed_episode <= current.proposed_episode:
        raise ValueError("replacement proposal must be newer than current proposal")
    if replacement.proposed_episode > decision_episode:
        raise ValueError("replacement proposal cannot originate after management decision")


def _management_decision(
    record: ConsolidationProposalManagedRecord,
    request: ConsolidationProposalManagementRequest,
) -> ConsolidationProposalManagementDecision:
    payload = {
        "target_proposal_id": request.target_proposal_id,
        "expected_candidate_id": request.expected_candidate_id,
        "action": request.action.value,
        "decision_episode": request.decision_episode,
        "reviewer_code": request.reviewer_code,
        "reason_code": request.reason_code,
        "replacement_proposal": (
            None
            if request.replacement_proposal is None
            else request.replacement_proposal.snapshot()
        ),
        "lifecycle": record.lifecycle.snapshot(),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return ConsolidationProposalManagementDecision(
        decision_id=f"consolidation-management:{hashlib.sha256(canonical).hexdigest()}",
        target_proposal_id=request.target_proposal_id,
        target_candidate_id=request.expected_candidate_id,
        action=request.action,
        disposition=_disposition_for(request.action),
        decision_episode=request.decision_episode,
        reviewer_code=request.reviewer_code,
        reason_code=request.reason_code,
        replacement_proposal=request.replacement_proposal,
    )


def _disposition_for(
    action: ConsolidationProposalManagementAction,
) -> ConsolidationProposalDisposition:
    if action is ConsolidationProposalManagementAction.EXPIRE:
        return ConsolidationProposalDisposition.EXPIRED
    return ConsolidationProposalDisposition.REPLACED


def _latest_lifecycle_episode(record: ConsolidationProposalLifecycleRecord) -> int:
    if not record.decisions:
        return record.proposal.proposed_episode
    return record.decisions[-1].decision_episode


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")
