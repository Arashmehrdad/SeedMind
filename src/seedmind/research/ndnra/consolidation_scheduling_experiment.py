"""Deterministic proposal-only experiment for NDNRA consolidation scheduling."""

from __future__ import annotations

import json
from collections import Counter, defaultdict
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

from seedmind.research.ndnra.consolidation import (
    ConsolidationCandidate,
    ConsolidationEligibilityPolicy,
)
from seedmind.research.ndnra.consolidation_portfolio import (
    ConsolidationPortfolioItem,
    ConsolidationPortfolioPolicy,
)
from seedmind.research.ndnra.consolidation_scheduling import (
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


class ConsolidationSchedulingStrategy(StrEnum):
    """Proposal strategies compared under identical evidence arrival."""

    FIXED_INTERVAL = "fixed_interval"
    ELIGIBILITY_ONLY = "eligibility_only"
    EVIDENCE_AWARE_BOUNDED = "evidence_aware_bounded"


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingExperimentConfig:
    """Deterministic controls for the bounded scheduling comparison."""

    final_episode: int = 11
    fixed_first_episode: int = 2
    fixed_interval_episodes: int = 3
    proposal_capacity_per_episode: int = 1

    def __post_init__(self) -> None:
        for name, value in (
            ("final_episode", self.final_episode),
            ("fixed_first_episode", self.fixed_first_episode),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        for name, value in (
            ("fixed_interval_episodes", self.fixed_interval_episodes),
            ("proposal_capacity_per_episode", self.proposal_capacity_per_episode),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.fixed_first_episode > self.final_episode:
            raise ValueError("fixed_first_episode cannot exceed final_episode")


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingProposalRecord:
    """One inspectable proposal signal with no execution authority."""

    strategy: ConsolidationSchedulingStrategy
    episode_index: int
    lesson_key: str
    eligible: bool
    candidate_id: str | None
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        if (
            isinstance(self.episode_index, bool)
            or not isinstance(self.episode_index, int)
            or self.episode_index < 0
        ):
            raise ValueError("episode_index must be a non-negative integer")
        if not self.lesson_key.strip() or not self.lesson_key.isascii():
            raise ValueError("lesson_key must be non-empty ASCII")
        if self.eligible != (self.candidate_id is not None):
            raise ValueError("eligible proposal records require a candidate identity")
        if self.candidate_id is not None and (
            not self.candidate_id.strip() or not self.candidate_id.isascii()
        ):
            raise ValueError("candidate_id must be non-empty ASCII")
        if self.has_execution_authority:
            raise ValueError("experiment proposals cannot have execution authority")

    def snapshot(self) -> dict[str, object]:
        return {
            "strategy": self.strategy.value,
            "episode_index": self.episode_index,
            "lesson_key": self.lesson_key,
            "eligible": self.eligible,
            "candidate_id": self.candidate_id,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingStrategyResult:
    """Metrics for one proposal strategy under shared evidence arrival."""

    strategy: ConsolidationSchedulingStrategy
    proposal_records: tuple[ConsolidationSchedulingProposalRecord, ...]
    proposal_count: int
    eligible_proposal_count: int
    false_proposal_count: int
    redundant_proposal_count: int
    missed_eligible_window_count: int
    capacity_pressure_count: int
    proposal_precision: float

    def __post_init__(self) -> None:
        if self.proposal_count != len(self.proposal_records):
            raise ValueError("proposal_count must match proposal records")
        if self.eligible_proposal_count < 0 or self.false_proposal_count < 0:
            raise ValueError("proposal counts must not be negative")
        if self.eligible_proposal_count + self.false_proposal_count != self.proposal_count:
            raise ValueError("eligible and false proposals must sum to proposal_count")
        for value in (
            self.redundant_proposal_count,
            self.missed_eligible_window_count,
            self.capacity_pressure_count,
        ):
            if value < 0:
                raise ValueError("strategy metrics must not be negative")
        if not 0.0 <= self.proposal_precision <= 1.0:
            raise ValueError("proposal_precision must be within [0, 1]")
        if any(record.strategy is not self.strategy for record in self.proposal_records):
            raise ValueError("proposal records must match the strategy result")

    def snapshot(self) -> dict[str, object]:
        return {
            "strategy": self.strategy.value,
            "proposal_count": self.proposal_count,
            "eligible_proposal_count": self.eligible_proposal_count,
            "false_proposal_count": self.false_proposal_count,
            "redundant_proposal_count": self.redundant_proposal_count,
            "missed_eligible_window_count": self.missed_eligible_window_count,
            "capacity_pressure_count": self.capacity_pressure_count,
            "proposal_precision": self.proposal_precision,
            "proposal_records": [record.snapshot() for record in self.proposal_records],
        }


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingExperimentResult:
    """Complete deterministic comparison with no consolidation execution."""

    config: ConsolidationSchedulingExperimentConfig
    eligibility_onsets: tuple[tuple[str, int], ...]
    strategy_results: tuple[ConsolidationSchedulingStrategyResult, ...]
    ledger_unchanged_by_scheduling: bool
    applied_candidate_count: int = 0
    action_authority_violations: int = 0
    sqlite_cognitive_dependency: bool = False

    def __post_init__(self) -> None:
        strategies = tuple(result.strategy for result in self.strategy_results)
        if strategies != tuple(ConsolidationSchedulingStrategy):
            raise ValueError("strategy results must use complete stable enum ordering")
        if tuple(sorted(self.eligibility_onsets)) != self.eligibility_onsets:
            raise ValueError("eligibility onsets must use stable lesson ordering")
        if self.applied_candidate_count != 0:
            raise ValueError("the scheduling experiment cannot apply candidates")
        if self.action_authority_violations != 0:
            raise ValueError("the scheduling experiment cannot have action authority")
        if self.sqlite_cognitive_dependency:
            raise ValueError("SQLite cannot participate in scheduling cognition")

    @property
    def evidence_aware_is_best(self) -> bool:
        """Return whether bounded evidence-aware scheduling dominates key errors."""
        fixed, eligibility_only, evidence_aware = self.strategy_results
        return bool(
            evidence_aware.proposal_precision == 1.0
            and evidence_aware.false_proposal_count < fixed.false_proposal_count
            and evidence_aware.redundant_proposal_count < eligibility_only.redundant_proposal_count
            and evidence_aware.missed_eligible_window_count <= fixed.missed_eligible_window_count
            and evidence_aware.capacity_pressure_count < eligibility_only.capacity_pressure_count
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "config": {
                "final_episode": self.config.final_episode,
                "fixed_first_episode": self.config.fixed_first_episode,
                "fixed_interval_episodes": self.config.fixed_interval_episodes,
                "proposal_capacity_per_episode": self.config.proposal_capacity_per_episode,
            },
            "eligibility_onsets": [
                {"lesson_key": key, "episode_index": episode}
                for key, episode in self.eligibility_onsets
            ],
            "strategy_results": [result.snapshot() for result in self.strategy_results],
            "ledger_unchanged_by_scheduling": self.ledger_unchanged_by_scheduling,
            "applied_candidate_count": self.applied_candidate_count,
            "action_authority_violations": self.action_authority_violations,
            "sqlite_cognitive_dependency": self.sqlite_cognitive_dependency,
            "evidence_aware_is_best": self.evidence_aware_is_best,
        }


def run_consolidation_scheduling_experiment(
    config: ConsolidationSchedulingExperimentConfig | None = None,
) -> ConsolidationSchedulingExperimentResult:
    """Compare three proposal strategies under identical evidence arrival."""
    resolved = config or ConsolidationSchedulingExperimentConfig()
    ledger = ContextualExperienceLedger()
    requests = _requests()
    arrivals = _evidence_arrivals()
    eligibility_policy = ConsolidationEligibilityPolicy()
    records: dict[
        ConsolidationSchedulingStrategy,
        list[ConsolidationSchedulingProposalRecord],
    ] = {strategy: [] for strategy in ConsolidationSchedulingStrategy}
    eligibility_onsets: dict[str, int] = {}
    active_candidate_ids: set[str] = set()
    scheduling_snapshot_consistent = True

    portfolio_policy = ConsolidationPortfolioPolicy(
        scheduling_policy=ConsolidationSchedulingPolicy(
            first_eligible_episode=0,
            minimum_interval_episodes=1,
            maximum_active_candidates=len(requests),
        ),
        maximum_proposals_per_evaluation=resolved.proposal_capacity_per_episode,
    )

    for episode in range(resolved.final_episode + 1):
        for trace in arrivals.get(episode, ()):
            ledger.record(trace)

        eligibility = {
            key: _candidate_for(
                ledger=ledger,
                request=request,
                policy=eligibility_policy,
            )
            for key, request in requests.items()
        }
        for key, candidate in eligibility.items():
            if candidate is not None and key not in eligibility_onsets:
                eligibility_onsets[key] = episode

        before_scheduling = ledger.snapshot()
        if _is_fixed_window(episode, resolved):
            for key in sorted(requests):
                candidate = eligibility[key]
                records[ConsolidationSchedulingStrategy.FIXED_INTERVAL].append(
                    ConsolidationSchedulingProposalRecord(
                        strategy=ConsolidationSchedulingStrategy.FIXED_INTERVAL,
                        episode_index=episode,
                        lesson_key=key,
                        eligible=candidate is not None,
                        candidate_id=(candidate.candidate_id if candidate is not None else None),
                    )
                )

        for key in sorted(requests):
            candidate = eligibility[key]
            if candidate is not None:
                records[ConsolidationSchedulingStrategy.ELIGIBILITY_ONLY].append(
                    ConsolidationSchedulingProposalRecord(
                        strategy=ConsolidationSchedulingStrategy.ELIGIBILITY_ONLY,
                        episode_index=episode,
                        lesson_key=key,
                        eligible=True,
                        candidate_id=candidate.candidate_id,
                    )
                )

        active_ids = tuple(sorted(active_candidate_ids))
        portfolio = portfolio_policy.evaluate(
            ledger=ledger,
            items=tuple(
                ConsolidationPortfolioItem(
                    request=request,
                    context=ConsolidationSchedulingContext(
                        episode_index=episode,
                        active_candidate_ids=active_ids,
                    ),
                )
                for _, request in sorted(requests.items())
            ),
        )
        for proposal in portfolio.selected_proposals:
            key = _lesson_key(proposal.candidate.lesson_identity)
            records[ConsolidationSchedulingStrategy.EVIDENCE_AWARE_BOUNDED].append(
                ConsolidationSchedulingProposalRecord(
                    strategy=ConsolidationSchedulingStrategy.EVIDENCE_AWARE_BOUNDED,
                    episode_index=episode,
                    lesson_key=key,
                    eligible=True,
                    candidate_id=proposal.candidate.candidate_id,
                )
            )
            active_candidate_ids.add(proposal.candidate.candidate_id)

        scheduling_snapshot_consistent = bool(
            scheduling_snapshot_consistent and ledger.snapshot() == before_scheduling
        )

    ordered_onsets = tuple(sorted(eligibility_onsets.items()))
    results = tuple(
        _strategy_result(
            strategy=strategy,
            records=tuple(records[strategy]),
            eligibility_onsets=eligibility_onsets,
            final_episode=resolved.final_episode,
            proposal_capacity=resolved.proposal_capacity_per_episode,
        )
        for strategy in ConsolidationSchedulingStrategy
    )
    return ConsolidationSchedulingExperimentResult(
        config=resolved,
        eligibility_onsets=ordered_onsets,
        strategy_results=results,
        ledger_unchanged_by_scheduling=scheduling_snapshot_consistent,
    )


def export_consolidation_scheduling_experiment(
    result: ConsolidationSchedulingExperimentResult,
    path: Path,
) -> None:
    """Write ASCII JSON evidence for inspection."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(result.snapshot(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )


def _strategy_result(
    *,
    strategy: ConsolidationSchedulingStrategy,
    records: tuple[ConsolidationSchedulingProposalRecord, ...],
    eligibility_onsets: dict[str, int],
    final_episode: int,
    proposal_capacity: int,
) -> ConsolidationSchedulingStrategyResult:
    eligible_records = tuple(record for record in records if record.eligible)
    per_lesson = Counter(record.lesson_key for record in eligible_records)
    redundant = sum(max(0, count - 1) for count in per_lesson.values())
    first_valid: dict[str, int] = {}
    for record in eligible_records:
        first_valid.setdefault(record.lesson_key, record.episode_index)
    missed = sum(
        (first_valid[key] - onset if key in first_valid else final_episode - onset + 1)
        for key, onset in eligibility_onsets.items()
    )
    per_episode = Counter(record.episode_index for record in records)
    pressure = sum(max(0, count - proposal_capacity) for count in per_episode.values())
    eligible_count = len(eligible_records)
    proposal_count = len(records)
    return ConsolidationSchedulingStrategyResult(
        strategy=strategy,
        proposal_records=records,
        proposal_count=proposal_count,
        eligible_proposal_count=eligible_count,
        false_proposal_count=proposal_count - eligible_count,
        redundant_proposal_count=redundant,
        missed_eligible_window_count=missed,
        capacity_pressure_count=pressure,
        proposal_precision=(eligible_count / proposal_count if proposal_count else 0.0),
    )


def _candidate_for(
    *,
    ledger: ContextualExperienceLedger,
    request: ConsolidationScheduleRequest,
    policy: ConsolidationEligibilityPolicy,
) -> ConsolidationCandidate | None:
    profile = ledger.mastery_profile(request.lesson)
    result = policy.evaluate(
        ledger=ledger,
        lesson=request.lesson,
        mastery_profile=profile,
        requested_stability_increment=request.requested_stability_increment,
        requested_plasticity_reduction=request.requested_plasticity_reduction,
        available_assembly_ids=request.available_assembly_ids,
        available_route_ids=request.available_route_ids,
    )
    return result.candidate


def _is_fixed_window(
    episode: int,
    config: ConsolidationSchedulingExperimentConfig,
) -> bool:
    return bool(
        episode >= config.fixed_first_episode
        and (episode - config.fixed_first_episode) % config.fixed_interval_episodes == 0
    )


def _lesson_key(lesson: LessonIdentity) -> str:
    direction = "positive" if lesson.desired_direction > 0.0 else "negative"
    return f"{lesson.need_code}|{lesson.effect_code}|{direction}"


def _requests() -> dict[str, ConsolidationScheduleRequest]:
    lessons = (
        (LessonIdentity("reduce_heat", "cooling", 1.0), "heat"),
        (LessonIdentity("remove_dirt", "cleanliness", 1.0), "clean"),
        (LessonIdentity("reduce_noise", "quiet", 1.0), "quiet"),
    )
    return {
        _lesson_key(lesson): ConsolidationScheduleRequest(
            lesson=lesson,
            available_assembly_ids=(f"assembly:{prefix}:a", f"assembly:{prefix}:b"),
            available_route_ids=(f"route:{prefix}:a", f"route:{prefix}:b"),
        )
        for lesson, prefix in lessons
    }


def _evidence_arrivals() -> dict[int, tuple[ContextualExperienceTrace, ...]]:
    heat = LessonIdentity("reduce_heat", "cooling", 1.0)
    clean = LessonIdentity("remove_dirt", "cleanliness", 1.0)
    quiet = LessonIdentity("reduce_noise", "quiet", 1.0)
    arrivals: defaultdict[int, list[ContextualExperienceTrace]] = defaultdict(list)
    for episode, trace in (
        (1, _trace(heat, "heat", 1, 0, "a", True)),
        (2, _trace(heat, "heat", 2, 1, "b", True)),
        (3, _trace(heat, "heat", 3, 2, "a", False)),
        (4, _trace(clean, "clean", 4, 0, "a", True)),
        (5, _trace(clean, "clean", 5, 1, "b", True)),
        (6, _trace(clean, "clean", 6, 2, "a", False)),
        (2, _trace(quiet, "quiet", 20, 0, "a", True)),
    ):
        arrivals[episode].append(trace)
    return {episode: tuple(traces) for episode, traces in arrivals.items()}


def _trace(
    lesson: LessonIdentity,
    prefix: str,
    identity_index: int,
    context_index: int,
    route_suffix: str,
    transfer_succeeded: bool,
) -> ContextualExperienceTrace:
    return ContextualExperienceTrace(
        identity=EventIdentity("scheduling_experiment", f"episode:{prefix}:{identity_index}", 0),
        correlation_group_id=f"group:{prefix}:{identity_index}",
        assembly_id=f"assembly:{prefix}:{route_suffix}",
        route_id=f"route:{prefix}:{route_suffix}",
        action_code=f"action:{prefix}",
        context=ContextSignature.from_values(
            active_need_code=lesson.need_code,
            sensor_values=(float(context_index),),
            available_action_codes=(f"action:{prefix}", "wait"),
        ),
        observed_effects=(
            EffectObservation(
                effect_code=lesson.effect_code,
                value=lesson.desired_direction,
                confidence=1.0,
            ),
        ),
        transfer_attempted=True,
        transfer_succeeded=transfer_succeeded,
    )
