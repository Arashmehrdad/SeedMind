"""Pure multi-lesson prioritisation for NDNRA consolidation proposals."""

from __future__ import annotations

from dataclasses import dataclass, field

from seedmind.research.ndnra.consolidation_scheduling import (
    ConsolidationScheduleDecision,
    ConsolidationScheduleProposal,
    ConsolidationScheduleRequest,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
)
from seedmind.research.ndnra.contextual_memory import ContextualExperienceLedger


@dataclass(frozen=True, slots=True)
class ConsolidationPortfolioItem:
    """One explicit lesson request and its caller-owned scheduling context."""

    request: ConsolidationScheduleRequest
    context: ConsolidationSchedulingContext


@dataclass(frozen=True, slots=True)
class ConsolidationPortfolioItemDecision:
    """One preserved lesson decision plus its deterministic portfolio outcome."""

    item: ConsolidationPortfolioItem
    schedule_decision: ConsolidationScheduleDecision
    proposal_rank: int | None
    selected: bool

    def __post_init__(self) -> None:
        if self.proposal_rank is not None and self.proposal_rank <= 0:
            raise ValueError("proposal_rank must be positive")
        if self.schedule_decision.proposal is None:
            if self.proposal_rank is not None or self.selected:
                raise ValueError("non-proposal decisions cannot be ranked or selected")
        elif self.proposal_rank is None:
            raise ValueError("proposal-ready decisions require a portfolio rank")


@dataclass(frozen=True, slots=True)
class ConsolidationPortfolioDecision:
    """Complete proposal-only result that preserves every lesson decision."""

    item_decisions: tuple[ConsolidationPortfolioItemDecision, ...]
    selected_proposals: tuple[ConsolidationScheduleProposal, ...]
    proposal_ready_count: int
    selection_limit: int

    def __post_init__(self) -> None:
        if not self.item_decisions:
            raise ValueError("item_decisions must not be empty")
        if self.proposal_ready_count < 0:
            raise ValueError("proposal_ready_count must not be negative")
        if self.selection_limit < 0:
            raise ValueError("selection_limit must not be negative")
        ready = tuple(
            decision
            for decision in self.item_decisions
            if decision.schedule_decision.proposal is not None
        )
        if len(ready) != self.proposal_ready_count:
            raise ValueError("proposal_ready_count does not match item decisions")
        selected = tuple(
            decision.schedule_decision.proposal
            for decision in sorted(
                (item for item in ready if item.selected),
                key=lambda item: item.proposal_rank or 0,
            )
        )
        if selected != self.selected_proposals:
            raise ValueError("selected proposals do not match ranked item decisions")
        if len(self.selected_proposals) > self.selection_limit:
            raise ValueError("selected proposals exceed the selection limit")
        proposal_ids = tuple(proposal.proposal_id for proposal in self.selected_proposals)
        if len(proposal_ids) != len(set(proposal_ids)):
            raise ValueError("selected proposal identities must be unique")


@dataclass(frozen=True, slots=True)
class ConsolidationPortfolioPolicy:
    """Rank explicit proposal-ready lessons without executing consolidation."""

    scheduling_policy: ConsolidationSchedulingPolicy = field(
        default_factory=ConsolidationSchedulingPolicy
    )
    maximum_proposals_per_evaluation: int = 1

    def __post_init__(self) -> None:
        if (
            isinstance(self.maximum_proposals_per_evaluation, bool)
            or not isinstance(self.maximum_proposals_per_evaluation, int)
            or self.maximum_proposals_per_evaluation <= 0
        ):
            raise ValueError("maximum_proposals_per_evaluation must be a positive integer")

    def evaluate(
        self,
        *,
        ledger: ContextualExperienceLedger,
        items: tuple[ConsolidationPortfolioItem, ...],
    ) -> ConsolidationPortfolioDecision:
        """Evaluate, rank, and bound proposals without mutating evidence or state."""
        canonical_items = _validated_items(items)
        shared_episode = canonical_items[0].context.episode_index
        shared_active_ids = canonical_items[0].context.active_candidate_ids
        for item in canonical_items[1:]:
            if item.context.episode_index != shared_episode:
                raise ValueError("portfolio items must share one evaluation episode")
            if item.context.active_candidate_ids != shared_active_ids:
                raise ValueError("portfolio items must share active candidate identities")

        evaluated = tuple(
            (
                item,
                self.scheduling_policy.evaluate(
                    ledger=ledger,
                    request=item.request,
                    context=item.context,
                ),
            )
            for item in canonical_items
        )
        proposal_ready = tuple(
            (item, decision) for item, decision in evaluated if decision.proposal is not None
        )
        ranked = tuple(sorted(proposal_ready, key=_priority_key))
        rank_by_proposal_id = {
            decision.proposal.proposal_id: rank
            for rank, (_, decision) in enumerate(ranked, start=1)
            if decision.proposal is not None
        }
        available_capacity = max(
            0,
            self.scheduling_policy.maximum_active_candidates - len(shared_active_ids),
        )
        selection_limit = min(
            self.maximum_proposals_per_evaluation,
            available_capacity,
        )
        selected_ids = frozenset(
            decision.proposal.proposal_id
            for _, decision in ranked[:selection_limit]
            if decision.proposal is not None
        )
        item_decisions = tuple(
            ConsolidationPortfolioItemDecision(
                item=item,
                schedule_decision=decision,
                proposal_rank=(
                    rank_by_proposal_id[decision.proposal.proposal_id]
                    if decision.proposal is not None
                    else None
                ),
                selected=(
                    decision.proposal is not None and decision.proposal.proposal_id in selected_ids
                ),
            )
            for item, decision in evaluated
        )
        selected_proposals = tuple(
            decision.proposal
            for _, decision in ranked[:selection_limit]
            if decision.proposal is not None
        )
        return ConsolidationPortfolioDecision(
            item_decisions=item_decisions,
            selected_proposals=selected_proposals,
            proposal_ready_count=len(proposal_ready),
            selection_limit=selection_limit,
        )


def _validated_items(
    items: tuple[ConsolidationPortfolioItem, ...],
) -> tuple[ConsolidationPortfolioItem, ...]:
    if not items:
        raise ValueError("portfolio items must not be empty")
    lesson_keys = tuple(_lesson_key(item) for item in items)
    if len(lesson_keys) != len(set(lesson_keys)):
        raise ValueError("portfolio lesson identities must be unique")
    return tuple(sorted(items, key=_lesson_key))


def _lesson_key(item: ConsolidationPortfolioItem) -> tuple[str, str, float]:
    lesson = item.request.lesson
    return (
        lesson.need_code,
        lesson.effect_code,
        lesson.desired_direction,
    )


def _priority_key(
    value: tuple[ConsolidationPortfolioItem, ConsolidationScheduleDecision],
) -> tuple[float, float, float, str]:
    _, decision = value
    proposal = decision.proposal
    if proposal is None:
        raise RuntimeError("only proposal-ready decisions may be ranked")
    profile = decision.eligibility.mastery_snapshot
    overdue_episodes = decision.episode_index - decision.due_episode
    return (
        -float(overdue_episodes),
        -profile.mastery_score,
        -profile.effective_support,
        proposal.candidate.candidate_id,
    )
