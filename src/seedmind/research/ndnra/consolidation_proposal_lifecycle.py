"""Pure review-only lifecycle decisions for NDNRA consolidation proposals."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from seedmind.research.ndnra.consolidation_scheduling import (
    ConsolidationScheduleProposal,
)


class ConsolidationProposalReviewAction(StrEnum):
    """Explicit caller-supplied review action for one pending proposal."""

    ACCEPT = "accept"
    REJECT = "reject"
    DEFER = "defer"


class ConsolidationProposalLifecycleStatus(StrEnum):
    """Review state of one proposal without any execution meaning."""

    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"
    DEFERRED = "deferred"


@dataclass(frozen=True, slots=True)
class ConsolidationProposalReviewRequest:
    """One explicit review request over one immutable scheduling proposal."""

    proposal: ConsolidationScheduleProposal
    action: ConsolidationProposalReviewAction
    decision_episode: int
    reviewer_code: str
    reason_code: str
    defer_until_episode: int | None = None

    def __post_init__(self) -> None:
        _validate_nonnegative_int("decision_episode", self.decision_episode)
        if self.decision_episode < self.proposal.proposed_episode:
            raise ValueError("decision_episode cannot precede the proposal episode")
        _validate_code("reviewer_code", self.reviewer_code)
        _validate_code("reason_code", self.reason_code)
        if self.action is ConsolidationProposalReviewAction.DEFER:
            if self.defer_until_episode is None:
                raise ValueError("deferred review requires defer_until_episode")
            _validate_nonnegative_int(
                "defer_until_episode",
                self.defer_until_episode,
            )
            if self.defer_until_episode <= self.decision_episode:
                raise ValueError("defer_until_episode must follow decision_episode")
        elif self.defer_until_episode is not None:
            raise ValueError("only deferred review may set defer_until_episode")


@dataclass(frozen=True, slots=True)
class ConsolidationProposalReviewDecision:
    """Immutable review evidence with explicitly absent execution authority."""

    decision_id: str
    proposal: ConsolidationScheduleProposal
    action: ConsolidationProposalReviewAction
    status: ConsolidationProposalLifecycleStatus
    decision_episode: int
    reviewer_code: str
    reason_code: str
    defer_until_episode: int | None = None
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("decision_id", self.decision_id)
        _validate_nonnegative_int("decision_episode", self.decision_episode)
        if self.decision_episode < self.proposal.proposed_episode:
            raise ValueError("decision_episode cannot precede the proposal episode")
        _validate_code("reviewer_code", self.reviewer_code)
        _validate_code("reason_code", self.reason_code)
        expected_status = _status_for(self.action)
        if self.status is not expected_status:
            raise ValueError("review action and lifecycle status are inconsistent")
        if self.action is ConsolidationProposalReviewAction.DEFER:
            if self.defer_until_episode is None:
                raise ValueError("deferred decision requires defer_until_episode")
            _validate_nonnegative_int(
                "defer_until_episode",
                self.defer_until_episode,
            )
            if self.defer_until_episode <= self.decision_episode:
                raise ValueError("defer_until_episode must follow decision_episode")
        elif self.defer_until_episode is not None:
            raise ValueError("only deferred decisions may set defer_until_episode")
        if self.has_execution_authority:
            raise ValueError("proposal review decisions must never have execution authority")

    @property
    def accepted_for_future_consideration(self) -> bool:
        """Return review approval without implying application authority."""
        return self.status is ConsolidationProposalLifecycleStatus.ACCEPTED

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe review evidence."""
        return {
            "decision_id": self.decision_id,
            "proposal": self.proposal.snapshot(),
            "action": self.action.value,
            "status": self.status.value,
            "decision_episode": self.decision_episode,
            "reviewer_code": self.reviewer_code,
            "reason_code": self.reason_code,
            "defer_until_episode": self.defer_until_episode,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationProposalReviewPolicy:
    """Return one pure deterministic review decision without applying work."""

    def evaluate(
        self,
        request: ConsolidationProposalReviewRequest,
    ) -> ConsolidationProposalReviewDecision:
        """Review one pending proposal without mutating proposal or cognition."""
        return ConsolidationProposalReviewDecision(
            decision_id=_decision_id(request),
            proposal=request.proposal,
            action=request.action,
            status=_status_for(request.action),
            decision_episode=request.decision_episode,
            reviewer_code=request.reviewer_code,
            reason_code=request.reason_code,
            defer_until_episode=request.defer_until_episode,
        )


def _status_for(
    action: ConsolidationProposalReviewAction,
) -> ConsolidationProposalLifecycleStatus:
    if action is ConsolidationProposalReviewAction.ACCEPT:
        return ConsolidationProposalLifecycleStatus.ACCEPTED
    if action is ConsolidationProposalReviewAction.REJECT:
        return ConsolidationProposalLifecycleStatus.REJECTED
    return ConsolidationProposalLifecycleStatus.DEFERRED


def _decision_id(request: ConsolidationProposalReviewRequest) -> str:
    payload = {
        "proposal": request.proposal.snapshot(),
        "action": request.action.value,
        "decision_episode": request.decision_episode,
        "reviewer_code": request.reviewer_code,
        "reason_code": request.reason_code,
        "defer_until_episode": request.defer_until_episode,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"consolidation-review:{hashlib.sha256(canonical).hexdigest()}"


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
