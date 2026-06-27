"""Deterministic strategy comparison for NDNRA proposal lifecycle management."""

from __future__ import annotations

import json
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from seedmind.research.ndnra.consolidation_proposal_lifecycle import (
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewRequest,
)
from seedmind.research.ndnra.consolidation_proposal_management import (
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalManagementAction,
    ConsolidationProposalManagementRequest,
)
from seedmind.research.ndnra.consolidation_scheduling import (
    ConsolidationScheduleProposal,
    ConsolidationScheduleRequest,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
)
from seedmind.research.ndnra.contextual_memory import (
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EventIdentity,
    LessonIdentity,
)
from seedmind.research.ndnra.effects import EffectObservation


class ConsolidationProposalLifecycleStrategy(StrEnum):
    """Lifecycle strategies compared under identical proposal evolution."""

    AUTOMATIC_ACCEPTANCE = "automatic_acceptance"
    PERMANENT_DEFERRAL = "permanent_deferral"
    EVIDENCE_AWARE_EXPLICIT = "evidence_aware_explicit"


@dataclass(frozen=True, slots=True)
class ConsolidationProposalLifecycleEvent:
    """One inspectable lifecycle event with no execution authority."""

    strategy: ConsolidationProposalLifecycleStrategy
    episode_index: int
    event_code: str
    proposal_id: str
    candidate_id: str
    lifecycle_status: ConsolidationProposalLifecycleStatus
    retained_record_count: int
    active_record_count: int
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        _validate_nonnegative_int("episode_index", self.episode_index)
        _validate_code("event_code", self.event_code)
        _validate_code("proposal_id", self.proposal_id)
        _validate_code("candidate_id", self.candidate_id)
        _validate_nonnegative_int("retained_record_count", self.retained_record_count)
        _validate_nonnegative_int("active_record_count", self.active_record_count)
        if self.active_record_count > self.retained_record_count:
            raise ValueError("active records cannot exceed retained records")
        if self.has_execution_authority:
            raise ValueError("lifecycle events cannot have execution authority")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe event evidence."""
        return {
            "strategy": self.strategy.value,
            "episode_index": self.episode_index,
            "event_code": self.event_code,
            "proposal_id": self.proposal_id,
            "candidate_id": self.candidate_id,
            "lifecycle_status": self.lifecycle_status.value,
            "retained_record_count": self.retained_record_count,
            "active_record_count": self.active_record_count,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationProposalLifecycleStrategyResult:
    """Metrics for one lifecycle strategy under shared proposal evolution."""

    strategy: ConsolidationProposalLifecycleStrategy
    events: tuple[ConsolidationProposalLifecycleEvent, ...]
    final_registry: ConsolidationProposalLifecycleRegistry
    stale_acceptance_count: int
    unnecessary_rejection_count: int
    current_review_delay_episodes: int
    duplicate_decision_count: int
    current_proposal_blocked_count: int
    retained_record_count: int
    retained_history_event_count: int
    active_record_count: int
    accepted_current_proposal: bool
    applied_candidate_count: int = 0
    action_authority_violations: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("stale_acceptance_count", self.stale_acceptance_count),
            ("unnecessary_rejection_count", self.unnecessary_rejection_count),
            ("current_review_delay_episodes", self.current_review_delay_episodes),
            ("duplicate_decision_count", self.duplicate_decision_count),
            ("current_proposal_blocked_count", self.current_proposal_blocked_count),
            ("retained_record_count", self.retained_record_count),
            ("retained_history_event_count", self.retained_history_event_count),
            ("active_record_count", self.active_record_count),
            ("applied_candidate_count", self.applied_candidate_count),
            ("action_authority_violations", self.action_authority_violations),
        ):
            _validate_nonnegative_int(name, value)
        if self.retained_record_count != len(self.final_registry.records):
            raise ValueError("retained_record_count must match the final registry")
        if self.active_record_count != len(self.final_registry.active_records):
            raise ValueError("active_record_count must match the final registry")
        if any(event.strategy is not self.strategy for event in self.events):
            raise ValueError("lifecycle events must match the strategy result")
        if self.applied_candidate_count != 0:
            raise ValueError("lifecycle strategies cannot apply candidates")
        if self.action_authority_violations != 0:
            raise ValueError("lifecycle strategies cannot have action authority")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic strategy evidence."""
        return {
            "strategy": self.strategy.value,
            "events": [event.snapshot() for event in self.events],
            "final_registry": self.final_registry.snapshot(),
            "stale_acceptance_count": self.stale_acceptance_count,
            "unnecessary_rejection_count": self.unnecessary_rejection_count,
            "current_review_delay_episodes": self.current_review_delay_episodes,
            "duplicate_decision_count": self.duplicate_decision_count,
            "current_proposal_blocked_count": self.current_proposal_blocked_count,
            "retained_record_count": self.retained_record_count,
            "retained_history_event_count": self.retained_history_event_count,
            "active_record_count": self.active_record_count,
            "accepted_current_proposal": self.accepted_current_proposal,
            "applied_candidate_count": self.applied_candidate_count,
            "action_authority_violations": self.action_authority_violations,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationProposalLifecycleExperimentResult:
    """Complete deterministic lifecycle comparison with no execution authority."""

    old_proposal_id: str
    old_candidate_id: str
    current_proposal_id: str
    current_candidate_id: str
    strategy_results: tuple[ConsolidationProposalLifecycleStrategyResult, ...]
    ledger_unchanged_by_lifecycle: bool
    applied_candidate_count: int = 0
    action_authority_violations: int = 0
    sqlite_cognitive_dependency: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("old_proposal_id", self.old_proposal_id),
            ("old_candidate_id", self.old_candidate_id),
            ("current_proposal_id", self.current_proposal_id),
            ("current_candidate_id", self.current_candidate_id),
        ):
            _validate_code(name, value)
        strategies = tuple(result.strategy for result in self.strategy_results)
        if strategies != tuple(ConsolidationProposalLifecycleStrategy):
            raise ValueError("strategy results must use complete stable enum ordering")
        if self.old_proposal_id == self.current_proposal_id:
            raise ValueError("proposal evolution requires different proposal identities")
        if self.old_candidate_id == self.current_candidate_id:
            raise ValueError("proposal evolution requires different candidate identities")
        if self.applied_candidate_count != 0:
            raise ValueError("the lifecycle experiment cannot apply candidates")
        if self.action_authority_violations != 0:
            raise ValueError("the lifecycle experiment cannot have action authority")
        if self.sqlite_cognitive_dependency:
            raise ValueError("SQLite cannot participate in lifecycle cognition")

    @property
    def evidence_aware_is_best(self) -> bool:
        """Return whether explicit evidence-aware management dominates key errors."""
        automatic, deferred, evidence_aware = self.strategy_results
        return bool(
            automatic.stale_acceptance_count > evidence_aware.stale_acceptance_count
            and deferred.current_review_delay_episodes
            > evidence_aware.current_review_delay_episodes
            and automatic.current_proposal_blocked_count
            > evidence_aware.current_proposal_blocked_count
            and deferred.current_proposal_blocked_count
            > evidence_aware.current_proposal_blocked_count
            and evidence_aware.unnecessary_rejection_count == 0
            and evidence_aware.duplicate_decision_count == 0
            and evidence_aware.accepted_current_proposal
            and evidence_aware.retained_record_count == 2
            and evidence_aware.retained_history_event_count == 3
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic experiment evidence."""
        return {
            "old_proposal_id": self.old_proposal_id,
            "old_candidate_id": self.old_candidate_id,
            "current_proposal_id": self.current_proposal_id,
            "current_candidate_id": self.current_candidate_id,
            "strategy_results": [result.snapshot() for result in self.strategy_results],
            "ledger_unchanged_by_lifecycle": self.ledger_unchanged_by_lifecycle,
            "applied_candidate_count": self.applied_candidate_count,
            "action_authority_violations": self.action_authority_violations,
            "sqlite_cognitive_dependency": self.sqlite_cognitive_dependency,
            "evidence_aware_is_best": self.evidence_aware_is_best,
        }


def run_consolidation_proposal_lifecycle_experiment() -> (
    ConsolidationProposalLifecycleExperimentResult
):
    """Compare lifecycle strategies under identical proposal evolution."""
    ledger, old_proposal, current_proposal = _evolving_proposals()
    before = ledger.snapshot()
    results = tuple(
        _run_strategy(
            strategy,
            old_proposal=old_proposal,
            current_proposal=current_proposal,
            final_episode=10,
        )
        for strategy in ConsolidationProposalLifecycleStrategy
    )
    return ConsolidationProposalLifecycleExperimentResult(
        old_proposal_id=old_proposal.proposal_id,
        old_candidate_id=old_proposal.candidate.candidate_id,
        current_proposal_id=current_proposal.proposal_id,
        current_candidate_id=current_proposal.candidate.candidate_id,
        strategy_results=results,
        ledger_unchanged_by_lifecycle=ledger.snapshot() == before,
    )


def export_consolidation_proposal_lifecycle_experiment(
    result: ConsolidationProposalLifecycleExperimentResult,
    path: Path,
) -> None:
    """Write ASCII JSON lifecycle evidence for inspection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.snapshot(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )


def _run_strategy(
    strategy: ConsolidationProposalLifecycleStrategy,
    *,
    old_proposal: ConsolidationScheduleProposal,
    current_proposal: ConsolidationScheduleProposal,
    final_episode: int,
) -> ConsolidationProposalLifecycleStrategyResult:
    registry = ConsolidationProposalLifecycleRegistry(maximum_active_records=1).add(old_proposal)
    events = [_event(strategy, 3, "proposal_added", registry, old_proposal.proposal_id)]
    current_blocked_count = 0

    if strategy is ConsolidationProposalLifecycleStrategy.AUTOMATIC_ACCEPTANCE:
        registry = registry.review(
            _review_request(
                old_proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                episode=4,
                reason="automatic_first_valid",
            )
        )
        events.append(_event(strategy, 4, "proposal_accepted", registry, old_proposal.proposal_id))
        current_blocked_count = 1
        events.append(
            _event(strategy, 6, "current_proposal_blocked", registry, old_proposal.proposal_id)
        )
    elif strategy is ConsolidationProposalLifecycleStrategy.PERMANENT_DEFERRAL:
        registry = registry.review(
            _review_request(
                old_proposal,
                action=ConsolidationProposalReviewAction.DEFER,
                episode=4,
                reason="indefinite_review_delay",
                defer_until=20,
            )
        )
        events.append(_event(strategy, 4, "proposal_deferred", registry, old_proposal.proposal_id))
        current_blocked_count = 1
        events.append(
            _event(strategy, 6, "current_proposal_blocked", registry, old_proposal.proposal_id)
        )
    else:
        registry = registry.review(
            _review_request(
                old_proposal,
                action=ConsolidationProposalReviewAction.DEFER,
                episode=4,
                reason="await_new_evidence",
                defer_until=6,
            )
        )
        events.append(_event(strategy, 4, "proposal_deferred", registry, old_proposal.proposal_id))
        registry = registry.manage(
            ConsolidationProposalManagementRequest(
                target_proposal_id=old_proposal.proposal_id,
                expected_candidate_id=old_proposal.candidate.candidate_id,
                action=ConsolidationProposalManagementAction.REPLACE,
                decision_episode=6,
                reviewer_code="policy:evidence_aware",
                reason_code="newer_mastery_snapshot",
                replacement_proposal=current_proposal,
            )
        )
        events.append(
            _event(strategy, 6, "proposal_replaced", registry, current_proposal.proposal_id)
        )
        registry = registry.review(
            _review_request(
                current_proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                episode=7,
                reason="current_evidence_review_passed",
            )
        )
        events.append(
            _event(strategy, 7, "current_proposal_accepted", registry, current_proposal.proposal_id)
        )

    return _strategy_result(
        strategy=strategy,
        events=tuple(events),
        registry=registry,
        current_proposal=current_proposal,
        final_episode=final_episode,
        current_blocked_count=current_blocked_count,
    )


def _strategy_result(
    *,
    strategy: ConsolidationProposalLifecycleStrategy,
    events: tuple[ConsolidationProposalLifecycleEvent, ...],
    registry: ConsolidationProposalLifecycleRegistry,
    current_proposal: ConsolidationScheduleProposal,
    final_episode: int,
    current_blocked_count: int,
) -> ConsolidationProposalLifecycleStrategyResult:
    accepted = tuple(
        record
        for record in registry.records
        if record.lifecycle.status is ConsolidationProposalLifecycleStatus.ACCEPTED
    )
    rejected = tuple(
        record
        for record in registry.records
        if record.lifecycle.status is ConsolidationProposalLifecycleStatus.REJECTED
    )
    decision_ids = tuple(
        decision.decision_id
        for record in registry.records
        for decision in record.lifecycle.decisions
    )
    management_ids = tuple(
        record.management_decision.decision_id
        for record in registry.records
        if record.management_decision is not None
    )
    accepted_current = any(
        record.proposal.proposal_id == current_proposal.proposal_id
        and record.lifecycle.status is ConsolidationProposalLifecycleStatus.ACCEPTED
        for record in registry.records
    )
    acceptance_episodes = tuple(
        decision.decision_episode
        for record in registry.records
        if record.proposal.proposal_id == current_proposal.proposal_id
        for decision in record.lifecycle.decisions
        if decision.status is ConsolidationProposalLifecycleStatus.ACCEPTED
    )
    delay = (
        acceptance_episodes[0] - current_proposal.proposed_episode
        if acceptance_episodes
        else final_episode - current_proposal.proposed_episode
    )
    return ConsolidationProposalLifecycleStrategyResult(
        strategy=strategy,
        events=events,
        final_registry=registry,
        stale_acceptance_count=sum(
            record.proposal.proposal_id != current_proposal.proposal_id for record in accepted
        ),
        unnecessary_rejection_count=len(rejected),
        current_review_delay_episodes=delay,
        duplicate_decision_count=(
            len((*decision_ids, *management_ids)) - len(set((*decision_ids, *management_ids)))
        ),
        current_proposal_blocked_count=current_blocked_count,
        retained_record_count=len(registry.records),
        retained_history_event_count=len(decision_ids) + len(management_ids),
        active_record_count=len(registry.active_records),
        accepted_current_proposal=accepted_current,
    )


def _event(
    strategy: ConsolidationProposalLifecycleStrategy,
    episode: int,
    event_code: str,
    registry: ConsolidationProposalLifecycleRegistry,
    proposal_id: str,
) -> ConsolidationProposalLifecycleEvent:
    record = registry.record_for(proposal_id)
    return ConsolidationProposalLifecycleEvent(
        strategy=strategy,
        episode_index=episode,
        event_code=event_code,
        proposal_id=record.proposal.proposal_id,
        candidate_id=record.proposal.candidate.candidate_id,
        lifecycle_status=record.lifecycle.status,
        retained_record_count=len(registry.records),
        active_record_count=len(registry.active_records),
    )


def _review_request(
    proposal: ConsolidationScheduleProposal,
    *,
    action: ConsolidationProposalReviewAction,
    episode: int,
    reason: str,
    defer_until: int | None = None,
) -> ConsolidationProposalReviewRequest:
    return ConsolidationProposalReviewRequest(
        proposal=proposal,
        action=action,
        decision_episode=episode,
        reviewer_code="policy:lifecycle_experiment",
        reason_code=reason,
        defer_until_episode=defer_until,
    )


def _evolving_proposals() -> tuple[
    ContextualExperienceLedger,
    ConsolidationScheduleProposal,
    ConsolidationScheduleProposal,
]:
    lesson = LessonIdentity("reduce_heat", "cooling", 1.0)
    assemblies = ("assembly:heat:a", "assembly:heat:b")
    routes = ("route:heat:a", "route:heat:b")
    ledger = ContextualExperienceLedger()
    for trace in (
        _trace(0, assemblies[0], routes[0], True),
        _trace(1, assemblies[1], routes[1], True),
        _trace(2, assemblies[0], routes[0], False),
    ):
        ledger.record(trace)
    request = ConsolidationScheduleRequest(
        lesson=lesson,
        available_assembly_ids=assemblies,
        available_route_ids=routes,
    )
    policy = ConsolidationSchedulingPolicy(
        first_eligible_episode=0,
        minimum_interval_episodes=1,
        maximum_active_candidates=1,
    )
    old_decision = policy.evaluate(
        ledger=ledger,
        request=request,
        context=ConsolidationSchedulingContext(episode_index=3),
    )
    if old_decision.proposal is None:
        raise RuntimeError("old lifecycle proposal was not eligible")
    for trace in (
        _trace(3, assemblies[1], routes[1], True),
        _trace(4, assemblies[0], routes[0], True),
    ):
        ledger.record(trace)
    current_decision = policy.evaluate(
        ledger=ledger,
        request=request,
        context=ConsolidationSchedulingContext(episode_index=6),
    )
    if current_decision.proposal is None:
        raise RuntimeError("current lifecycle proposal was not eligible")
    return ledger, old_decision.proposal, current_decision.proposal


def _trace(
    index: int,
    assembly_id: str,
    route_id: str,
    transfer_succeeded: bool,
) -> ContextualExperienceTrace:
    return ContextualExperienceTrace(
        identity=EventIdentity("lifecycle_experiment", f"episode:{index}", index),
        correlation_group_id=f"group:lifecycle:{index}",
        assembly_id=assembly_id,
        route_id=route_id,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code="reduce_heat",
            sensor_values=(float(index), float(index + 1)),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(EffectObservation("cooling", 1.0, 1.0),),
        transfer_attempted=True,
        transfer_succeeded=transfer_succeeded,
    )


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
