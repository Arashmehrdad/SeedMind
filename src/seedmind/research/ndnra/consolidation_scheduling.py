"""Pure proposal-only scheduling policy for bounded NDNRA consolidation."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.consolidation import (
    ConsolidationCandidate,
    ConsolidationEligibility,
    ConsolidationEligibilityPolicy,
)
from seedmind.research.ndnra.contextual_memory import (
    ContextualExperienceLedger,
    LessonIdentity,
)


class ConsolidationScheduleStatus(StrEnum):
    """Deterministic outcome of one proposal-only scheduling evaluation."""

    PROPOSED = "proposed"
    BEFORE_FIRST_WINDOW = "before_first_window"
    COOLDOWN_ACTIVE = "cooldown_active"
    NOT_ELIGIBLE = "not_eligible"
    CANDIDATE_ALREADY_ACTIVE = "candidate_already_active"
    ACTIVE_CAPACITY_REACHED = "active_capacity_reached"


@dataclass(frozen=True, slots=True)
class ConsolidationScheduleRequest:
    """One explicitly supplied lesson request with no implicit discovery or timer."""

    lesson: LessonIdentity
    available_assembly_ids: tuple[str, ...]
    available_route_ids: tuple[str, ...]
    requested_stability_increment: float = 0.10
    requested_plasticity_reduction: float = 0.10

    def __post_init__(self) -> None:
        _validate_sorted_unique_codes(
            "available_assembly_ids",
            self.available_assembly_ids,
            allow_empty=False,
        )
        _validate_sorted_unique_codes(
            "available_route_ids",
            self.available_route_ids,
            allow_empty=False,
        )
        _validate_positive_unit(
            "requested_stability_increment",
            self.requested_stability_increment,
        )
        _validate_positive_unit(
            "requested_plasticity_reduction",
            self.requested_plasticity_reduction,
        )


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingContext:
    """Caller-owned deterministic scheduling context for one lesson."""

    episode_index: int
    last_completed_episode: int | None = None
    active_candidate_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_nonnegative_int("episode_index", self.episode_index)
        if self.last_completed_episode is not None:
            _validate_nonnegative_int(
                "last_completed_episode",
                self.last_completed_episode,
            )
            if self.last_completed_episode > self.episode_index:
                raise ValueError("last_completed_episode cannot exceed episode_index")
        _validate_sorted_unique_codes(
            "active_candidate_ids",
            self.active_candidate_ids,
            allow_empty=True,
        )


@dataclass(frozen=True, slots=True)
class ConsolidationScheduleProposal:
    """Immutable consolidation proposal with explicitly absent execution authority."""

    proposal_id: str
    candidate: ConsolidationCandidate
    proposed_episode: int
    due_episode: int
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("proposal_id", self.proposal_id)
        _validate_nonnegative_int("proposed_episode", self.proposed_episode)
        _validate_nonnegative_int("due_episode", self.due_episode)
        if self.proposed_episode < self.due_episode:
            raise ValueError("proposal cannot precede its due episode")
        if self.has_execution_authority:
            raise ValueError("scheduling proposals must never have execution authority")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable proposal evidence."""
        return {
            "proposal_id": self.proposal_id,
            "candidate": self.candidate.snapshot(),
            "proposed_episode": self.proposed_episode,
            "due_episode": self.due_episode,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationScheduleDecision:
    """Complete pure result for one scheduling evaluation."""

    status: ConsolidationScheduleStatus
    eligibility: ConsolidationEligibility
    proposal: ConsolidationScheduleProposal | None
    episode_index: int
    due_episode: int

    def __post_init__(self) -> None:
        _validate_nonnegative_int("episode_index", self.episode_index)
        _validate_nonnegative_int("due_episode", self.due_episode)
        if self.status is ConsolidationScheduleStatus.PROPOSED:
            if self.proposal is None:
                raise ValueError("proposed decisions require one proposal")
            if not self.eligibility.eligible:
                raise ValueError("proposed decisions require eligible consolidation")
            if self.proposal.proposed_episode != self.episode_index:
                raise ValueError("proposal episode must match decision episode")
            if self.proposal.due_episode != self.due_episode:
                raise ValueError("proposal due episode must match decision due episode")
        elif self.proposal is not None:
            raise ValueError("non-proposed decisions cannot contain a proposal")

    @property
    def proposed(self) -> bool:
        """Return whether this decision contains a non-authoritative proposal."""
        return self.proposal is not None


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingPolicy:
    """Evaluate explicit episode cadence and eligibility without executing work."""

    first_eligible_episode: int = 100
    minimum_interval_episodes: int = 100
    maximum_active_candidates: int = 1
    eligibility_policy: ConsolidationEligibilityPolicy = field(
        default_factory=ConsolidationEligibilityPolicy
    )

    def __post_init__(self) -> None:
        _validate_nonnegative_int("first_eligible_episode", self.first_eligible_episode)
        _validate_positive_int(
            "minimum_interval_episodes",
            self.minimum_interval_episodes,
        )
        _validate_positive_int(
            "maximum_active_candidates",
            self.maximum_active_candidates,
        )

    def evaluate(
        self,
        *,
        ledger: ContextualExperienceLedger,
        request: ConsolidationScheduleRequest,
        context: ConsolidationSchedulingContext,
    ) -> ConsolidationScheduleDecision:
        """Return one proposal-only decision without mutating evidence or state."""
        profile = ledger.mastery_profile(request.lesson)
        eligibility = self.eligibility_policy.evaluate(
            ledger=ledger,
            lesson=request.lesson,
            mastery_profile=profile,
            requested_stability_increment=request.requested_stability_increment,
            requested_plasticity_reduction=request.requested_plasticity_reduction,
            available_assembly_ids=request.available_assembly_ids,
            available_route_ids=request.available_route_ids,
        )
        due_episode = self._due_episode(context.last_completed_episode)
        if context.episode_index < due_episode:
            status = (
                ConsolidationScheduleStatus.BEFORE_FIRST_WINDOW
                if context.last_completed_episode is None
                else ConsolidationScheduleStatus.COOLDOWN_ACTIVE
            )
            return ConsolidationScheduleDecision(
                status=status,
                eligibility=eligibility,
                proposal=None,
                episode_index=context.episode_index,
                due_episode=due_episode,
            )
        if not eligibility.eligible or eligibility.candidate is None:
            return ConsolidationScheduleDecision(
                status=ConsolidationScheduleStatus.NOT_ELIGIBLE,
                eligibility=eligibility,
                proposal=None,
                episode_index=context.episode_index,
                due_episode=due_episode,
            )

        candidate = eligibility.candidate
        if candidate.candidate_id in context.active_candidate_ids:
            return ConsolidationScheduleDecision(
                status=ConsolidationScheduleStatus.CANDIDATE_ALREADY_ACTIVE,
                eligibility=eligibility,
                proposal=None,
                episode_index=context.episode_index,
                due_episode=due_episode,
            )
        if len(context.active_candidate_ids) >= self.maximum_active_candidates:
            return ConsolidationScheduleDecision(
                status=ConsolidationScheduleStatus.ACTIVE_CAPACITY_REACHED,
                eligibility=eligibility,
                proposal=None,
                episode_index=context.episode_index,
                due_episode=due_episode,
            )

        proposal = ConsolidationScheduleProposal(
            proposal_id=_proposal_id(
                candidate=candidate,
                proposed_episode=context.episode_index,
                due_episode=due_episode,
                policy=self,
            ),
            candidate=candidate,
            proposed_episode=context.episode_index,
            due_episode=due_episode,
        )
        return ConsolidationScheduleDecision(
            status=ConsolidationScheduleStatus.PROPOSED,
            eligibility=eligibility,
            proposal=proposal,
            episode_index=context.episode_index,
            due_episode=due_episode,
        )

    def _due_episode(self, last_completed_episode: int | None) -> int:
        if last_completed_episode is None:
            return self.first_eligible_episode
        return last_completed_episode + self.minimum_interval_episodes


def _proposal_id(
    *,
    candidate: ConsolidationCandidate,
    proposed_episode: int,
    due_episode: int,
    policy: ConsolidationSchedulingPolicy,
) -> str:
    payload = {
        "candidate_id": candidate.candidate_id,
        "proposed_episode": proposed_episode,
        "due_episode": due_episode,
        "first_eligible_episode": policy.first_eligible_episode,
        "minimum_interval_episodes": policy.minimum_interval_episodes,
        "maximum_active_candidates": policy.maximum_active_candidates,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"consolidation-schedule:{hashlib.sha256(canonical).hexdigest()}"


def _validate_sorted_unique_codes(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> None:
    if not allow_empty and not values:
        raise ValueError(f"{name} must not be empty")
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
    for value in values:
        _validate_code(name, value)


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_positive_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 < value <= 1.0:
        raise ValueError(f"{name} must be finite, positive, and at most one")
