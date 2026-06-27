"""Immutable in-memory history for NDNRA consolidation proposal review."""

from __future__ import annotations

from dataclasses import dataclass

from seedmind.research.ndnra.consolidation_proposal_lifecycle import (
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewDecision,
    ConsolidationProposalReviewPolicy,
    ConsolidationProposalReviewRequest,
)
from seedmind.research.ndnra.consolidation_scheduling import (
    ConsolidationScheduleProposal,
)


@dataclass(frozen=True, slots=True)
class ConsolidationProposalLifecycleRecord:
    """One immutable proposal plus its complete ordered review history."""

    proposal: ConsolidationScheduleProposal
    status: ConsolidationProposalLifecycleStatus
    decisions: tuple[ConsolidationProposalReviewDecision, ...] = ()
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_execution_authority:
            raise ValueError("lifecycle records must never have execution authority")
        _validate_history(
            proposal=self.proposal,
            status=self.status,
            decisions=self.decisions,
        )

    @classmethod
    def pending(
        cls,
        proposal: ConsolidationScheduleProposal,
    ) -> ConsolidationProposalLifecycleRecord:
        """Create an empty pending lifecycle record for one proposal."""
        return cls(
            proposal=proposal,
            status=ConsolidationProposalLifecycleStatus.PENDING,
        )

    @property
    def current_defer_until_episode(self) -> int | None:
        """Return the active review boundary when the record is deferred."""
        if self.status is not ConsolidationProposalLifecycleStatus.DEFERRED:
            return None
        if not self.decisions:
            raise RuntimeError("deferred lifecycle record requires history")
        return self.decisions[-1].defer_until_episode

    def review(
        self,
        request: ConsolidationProposalReviewRequest,
        *,
        policy: ConsolidationProposalReviewPolicy | None = None,
    ) -> ConsolidationProposalLifecycleRecord:
        """Return a new record containing one validated review decision."""
        if request.proposal != self.proposal:
            raise ValueError("review request proposal does not match lifecycle proposal")
        if self.status in {
            ConsolidationProposalLifecycleStatus.ACCEPTED,
            ConsolidationProposalLifecycleStatus.REJECTED,
        }:
            raise ValueError("accepted and rejected lifecycle records are terminal")
        if self.decisions:
            previous = self.decisions[-1]
            if request.decision_episode <= previous.decision_episode:
                raise ValueError("review decision episodes must increase strictly")
            if (
                self.status is ConsolidationProposalLifecycleStatus.DEFERRED
                and previous.defer_until_episode is not None
                and request.decision_episode < previous.defer_until_episode
            ):
                raise ValueError("deferred proposal cannot be reviewed before its review episode")

        decision = (policy or ConsolidationProposalReviewPolicy()).evaluate(request)
        if decision.decision_id in {item.decision_id for item in self.decisions}:
            raise ValueError("duplicate lifecycle decision identity")
        return ConsolidationProposalLifecycleRecord(
            proposal=self.proposal,
            status=decision.status,
            decisions=(*self.decisions, decision),
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe lifecycle evidence."""
        return {
            "proposal": self.proposal.snapshot(),
            "status": self.status.value,
            "decisions": tuple(decision.snapshot() for decision in self.decisions),
            "current_defer_until_episode": self.current_defer_until_episode,
            "has_execution_authority": self.has_execution_authority,
        }


def _validate_history(
    *,
    proposal: ConsolidationScheduleProposal,
    status: ConsolidationProposalLifecycleStatus,
    decisions: tuple[ConsolidationProposalReviewDecision, ...],
) -> None:
    if not decisions:
        if status is not ConsolidationProposalLifecycleStatus.PENDING:
            raise ValueError("empty lifecycle history must remain pending")
        return
    if status is ConsolidationProposalLifecycleStatus.PENDING:
        raise ValueError("pending lifecycle record cannot contain review decisions")

    decision_ids: set[str] = set()
    previous: ConsolidationProposalReviewDecision | None = None
    for decision in decisions:
        if decision.proposal != proposal:
            raise ValueError("lifecycle history contains a different proposal")
        if decision.decision_id in decision_ids:
            raise ValueError("lifecycle history contains duplicate decision identities")
        decision_ids.add(decision.decision_id)
        if previous is not None:
            if previous.status in {
                ConsolidationProposalLifecycleStatus.ACCEPTED,
                ConsolidationProposalLifecycleStatus.REJECTED,
            }:
                raise ValueError("terminal lifecycle decisions cannot have successors")
            if decision.decision_episode <= previous.decision_episode:
                raise ValueError("lifecycle decision episodes must increase strictly")
            if (
                previous.status is ConsolidationProposalLifecycleStatus.DEFERRED
                and previous.defer_until_episode is not None
                and decision.decision_episode < previous.defer_until_episode
            ):
                raise ValueError("lifecycle history reviews a deferred proposal too early")
        previous = decision

    if decisions[-1].status is not status:
        raise ValueError("lifecycle status must match the latest review decision")
