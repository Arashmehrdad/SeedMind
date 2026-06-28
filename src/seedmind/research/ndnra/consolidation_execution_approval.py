"""Explicit human approval contracts for bounded NDNRA consolidation execution."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable
from dataclasses import dataclass, field

from seedmind.research.ndnra.consolidation_proposal_lifecycle import (
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewAction,
)
from seedmind.research.ndnra.consolidation_proposal_management import (
    ConsolidationProposalManagedRecord,
)
from seedmind.research.ndnra.consolidation_proposal_revalidation import (
    ConsolidationProposalRevalidationDecision,
    ConsolidationProposalRevalidationPolicy,
    ConsolidationProposalRevalidationStatus,
)
from seedmind.research.ndnra.consolidation_scheduling import (
    ConsolidationScheduleProposal,
)
from seedmind.research.ndnra.contextual_memory import ContextualExperienceLedger


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionApprovalRequest:
    """One explicit human authorization request for one exact proposal."""

    target_proposal_id: str
    expected_candidate_id: str
    expected_review_decision_id: str
    approval_episode: int
    expires_after_episode: int
    approver_code: str
    reason_code: str

    def __post_init__(self) -> None:
        _validate_code("target_proposal_id", self.target_proposal_id)
        _validate_code("expected_candidate_id", self.expected_candidate_id)
        _validate_code(
            "expected_review_decision_id",
            self.expected_review_decision_id,
        )
        _validate_nonnegative_int("approval_episode", self.approval_episode)
        _validate_nonnegative_int(
            "expires_after_episode",
            self.expires_after_episode,
        )
        if self.expires_after_episode <= self.approval_episode:
            raise ValueError("expires_after_episode must follow approval_episode")
        _validate_code("approver_code", self.approver_code)
        if not self.approver_code.startswith("human:"):
            raise ValueError("approver_code must identify an explicit human approver")
        _validate_code("reason_code", self.reason_code)


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionPermit:
    """Single-use authorization evidence that performs no application itself."""

    permit_id: str
    proposal: ConsolidationScheduleProposal
    accepted_review_decision_id: str
    revalidation: ConsolidationProposalRevalidationDecision
    issued_episode: int
    expires_after_episode: int
    approver_code: str
    reason_code: str
    authorizes_one_application: bool = True
    single_use: bool = True
    consumed: bool = False
    application_count: int = 0
    has_direct_execution_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("permit_id", self.permit_id)
        _validate_code(
            "accepted_review_decision_id",
            self.accepted_review_decision_id,
        )
        _validate_nonnegative_int("issued_episode", self.issued_episode)
        _validate_nonnegative_int(
            "expires_after_episode",
            self.expires_after_episode,
        )
        if self.expires_after_episode <= self.issued_episode:
            raise ValueError("permit expiry must follow its issue episode")
        _validate_code("approver_code", self.approver_code)
        if not self.approver_code.startswith("human:"):
            raise ValueError("execution permit requires an explicit human approver")
        _validate_code("reason_code", self.reason_code)
        if not self.authorizes_one_application:
            raise ValueError("execution permit must authorize exactly one application")
        if not self.single_use:
            raise ValueError("execution permit must be single-use")
        if self.consumed:
            raise ValueError("new execution permit cannot already be consumed")
        if self.application_count != 0:
            raise ValueError("new execution permit cannot contain applications")
        if self.has_direct_execution_authority:
            raise ValueError("execution permit cannot execute consolidation directly")
        if self.revalidation.status is not ConsolidationProposalRevalidationStatus.CURRENT:
            raise ValueError("execution permit requires current revalidation")
        if self.revalidation.proposal != self.proposal:
            raise ValueError("execution permit revalidation must match its proposal")
        if self.revalidation.current_candidate != self.proposal.candidate:
            raise ValueError("execution permit requires the exact current candidate")
        if not self.revalidation.candidate_identity_current:
            raise ValueError("execution permit requires current candidate identity")

    def valid_at(self, episode: int) -> bool:
        """Return whether the unused permit remains inside its bounded window."""
        _validate_nonnegative_int("episode", episode)
        return bool(
            not self.consumed and self.issued_episode <= episode <= self.expires_after_episode
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe authorization evidence."""
        return {
            "permit_id": self.permit_id,
            "proposal": self.proposal.snapshot(),
            "accepted_review_decision_id": self.accepted_review_decision_id,
            "revalidation": self.revalidation.snapshot(),
            "issued_episode": self.issued_episode,
            "expires_after_episode": self.expires_after_episode,
            "approver_code": self.approver_code,
            "reason_code": self.reason_code,
            "authorizes_one_application": self.authorizes_one_application,
            "single_use": self.single_use,
            "consumed": self.consumed,
            "application_count": self.application_count,
            "has_direct_execution_authority": self.has_direct_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionApprovalPolicy:
    """Issue bounded human permits only after immediate current revalidation."""

    maximum_validity_episodes: int = 1
    revalidation_policy: ConsolidationProposalRevalidationPolicy = field(
        default_factory=ConsolidationProposalRevalidationPolicy
    )

    def __post_init__(self) -> None:
        if (
            isinstance(self.maximum_validity_episodes, bool)
            or not isinstance(self.maximum_validity_episodes, int)
            or self.maximum_validity_episodes < 1
        ):
            raise ValueError("maximum_validity_episodes must be a positive integer")

    def evaluate(
        self,
        *,
        request: ConsolidationExecutionApprovalRequest,
        record: ConsolidationProposalManagedRecord,
        ledger: ContextualExperienceLedger,
        available_assembly_ids: Iterable[str],
        available_route_ids: Iterable[str],
    ) -> ConsolidationExecutionPermit:
        """Issue authorization evidence without consuming or applying it."""
        if not record.is_active:
            raise ValueError("execution approval requires an active lifecycle record")
        lifecycle = record.lifecycle
        if lifecycle.status is not ConsolidationProposalLifecycleStatus.ACCEPTED:
            raise ValueError("execution approval requires accepted lifecycle status")
        if not lifecycle.decisions:
            raise ValueError("accepted lifecycle record requires review evidence")
        accepted_review = lifecycle.decisions[-1]
        if (
            accepted_review.action is not ConsolidationProposalReviewAction.ACCEPT
            or accepted_review.status is not ConsolidationProposalLifecycleStatus.ACCEPTED
        ):
            raise ValueError("latest lifecycle decision must be an acceptance")

        proposal = record.proposal
        if request.target_proposal_id != proposal.proposal_id:
            raise ValueError("approval request targets a different proposal")
        if request.expected_candidate_id != proposal.candidate.candidate_id:
            raise ValueError("approval request targets a different candidate")
        if request.expected_review_decision_id != accepted_review.decision_id:
            raise ValueError("approval request targets a different review decision")
        if request.approval_episode <= accepted_review.decision_episode:
            raise ValueError("execution approval must follow accepted review")
        if (
            request.expires_after_episode - request.approval_episode
            > self.maximum_validity_episodes
        ):
            raise ValueError("execution approval validity exceeds policy limit")

        ledger_before = ledger.snapshot()
        lifecycle_before = lifecycle.snapshot()
        revalidation = self.revalidation_policy.evaluate(
            record=record,
            ledger=ledger,
            available_assembly_ids=available_assembly_ids,
            available_route_ids=available_route_ids,
        )
        if revalidation.status is not ConsolidationProposalRevalidationStatus.CURRENT:
            raise ValueError(
                "execution approval requires a currently valid proposal; "
                f"received {revalidation.status.value}"
            )
        if revalidation.proposal != proposal:
            raise ValueError("revalidation returned a different proposal")
        if revalidation.current_candidate != proposal.candidate:
            raise ValueError("revalidation returned a different candidate")
        if ledger.snapshot() != ledger_before:
            raise RuntimeError("approval revalidation mutated contextual evidence")
        if lifecycle.snapshot() != lifecycle_before:
            raise RuntimeError("approval revalidation mutated lifecycle history")

        payload = {
            "proposal": proposal.snapshot(),
            "accepted_review_decision_id": accepted_review.decision_id,
            "revalidation": revalidation.snapshot(),
            "issued_episode": request.approval_episode,
            "expires_after_episode": request.expires_after_episode,
            "approver_code": request.approver_code,
            "reason_code": request.reason_code,
            "authorizes_one_application": True,
            "single_use": True,
        }
        return ConsolidationExecutionPermit(
            permit_id=_permit_id(payload),
            proposal=proposal,
            accepted_review_decision_id=accepted_review.decision_id,
            revalidation=revalidation,
            issued_episode=request.approval_episode,
            expires_after_episode=request.expires_after_episode,
            approver_code=request.approver_code,
            reason_code=request.reason_code,
        )


def _permit_id(payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"consolidation-execution-permit:{hashlib.sha256(canonical).hexdigest()}"


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
