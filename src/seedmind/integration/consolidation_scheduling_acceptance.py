"""Live-shadow acceptance for proposal-only NDNRA consolidation scheduling."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.curiosity import CuriosityConfig, CuriositySelection
from seedmind.environment import DynamicNurseryScenarioFactory
from seedmind.integration.developmental_signals import LiveDevelopmentalSignals
from seedmind.integration.unified_shadow import (
    NDNRALiveShadowAdapter,
    UnifiedDevelopmentalShadowSession,
    UnifiedShadowConfig,
    UnifiedShadowResult,
)
from seedmind.integration.unified_signal_experiment import (
    _build_signal_provider,
    _build_trainer,
)
from seedmind.research.ndnra import (
    AdaptiveUpdate,
    ConsolidationEligibility,
    ConsolidationEligibilityPolicy,
    ConsolidationPortfolioItem,
    ConsolidationPortfolioPolicy,
    ConsolidationScheduleRequest,
    ConsolidationScheduleStatus,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
    ContextSignature,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
    NDNRABrainStore,
    NDNRAGrowthState,
    run_consolidation_scheduling_experiment,
)
from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.training import ExperienceTransition

_SCHEDULING_LESSON = LessonIdentity(
    need_code="retain_live_scheduling_skill",
    effect_code="scheduling_probe",
    desired_direction=1.0,
)
_ROUTE_IDS = (
    "route:scheduling:primary",
    "route:scheduling:transfer",
)


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingShadowObservation:
    """One read-only scheduling evaluation after a live shadow transition."""

    step_index: int
    status: ConsolidationScheduleStatus
    proposal_id: str | None
    candidate_id: str | None
    selected: bool
    ledger_unchanged: bool
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        if self.selected != (self.proposal_id is not None):
            raise ValueError("selected observations require one proposal identity")
        if self.selected and self.status is not ConsolidationScheduleStatus.PROPOSED:
            raise ValueError("selected observations must have proposed status")
        if self.has_execution_authority:
            raise ValueError("scheduling observations cannot have execution authority")

    def snapshot(self) -> dict[str, object]:
        return {
            "step_index": self.step_index,
            "status": self.status.value,
            "proposal_id": self.proposal_id,
            "candidate_id": self.candidate_id,
            "selected": self.selected,
            "ledger_unchanged": self.ledger_unchanged,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingAcceptanceResult:
    """Synthetic and live-shadow evidence for proposal-only scheduling."""

    synthetic_scheduling_gate_passed: bool
    live_mastery_eligible: bool
    live_mastery_source_count: int
    live_mastery_route_count: int
    production_actions_unchanged: bool
    prediction_errors_unchanged: bool
    suggestion_sequence_unchanged: bool
    live_signals_unchanged: bool
    learned_graphs_equal: bool
    growth_states_equal: bool
    authority_violation_count: int
    schedule_evaluation_count: int
    proposal_count: int
    unique_candidate_count: int
    redundant_proposal_count: int
    scheduler_ledger_mutation_count: int
    consolidation_application_count: int
    sqlite_used_for_scheduling_acceptance: bool
    pass_gate: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("live_mastery_source_count", self.live_mastery_source_count),
            ("live_mastery_route_count", self.live_mastery_route_count),
            ("authority_violation_count", self.authority_violation_count),
            ("schedule_evaluation_count", self.schedule_evaluation_count),
            ("proposal_count", self.proposal_count),
            ("unique_candidate_count", self.unique_candidate_count),
            ("redundant_proposal_count", self.redundant_proposal_count),
            ("scheduler_ledger_mutation_count", self.scheduler_ledger_mutation_count),
            ("consolidation_application_count", self.consolidation_application_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must not be negative")


@dataclass(frozen=True, slots=True)
class ConsolidationSchedulingAcceptanceEvidence:
    """Acceptance result and complete live comparison evidence."""

    result: ConsolidationSchedulingAcceptanceResult
    pretraining: UnifiedShadowResult
    baseline: UnifiedShadowResult
    scheduling_observed: UnifiedShadowResult
    observations: tuple[ConsolidationSchedulingShadowObservation, ...]
    source_brain_path: Path


class _SchedulingObservedShadowAdapter(NDNRALiveShadowAdapter):
    """Run the pure scheduler after learning without altering the live transition."""

    def __init__(
        self,
        *,
        graph: MultidimensionalExperienceGraph,
        growth_state: NDNRAGrowthState,
        request: ConsolidationScheduleRequest,
    ) -> None:
        super().__init__(graph=graph, growth_state=growth_state)
        self._request = request
        self._portfolio = ConsolidationPortfolioPolicy(
            scheduling_policy=ConsolidationSchedulingPolicy(
                first_eligible_episode=0,
                minimum_interval_episodes=1,
                maximum_active_candidates=1,
            ),
            maximum_proposals_per_evaluation=1,
        )
        self._active_candidate_ids: set[str] = set()
        self._observations: list[ConsolidationSchedulingShadowObservation] = []

    @property
    def observations(self) -> tuple[ConsolidationSchedulingShadowObservation, ...]:
        return tuple(self._observations)

    def observe_transition(
        self,
        experience: ExperienceTransition,
        selection: CuriositySelection,
        signals: LiveDevelopmentalSignals,
    ) -> AdaptiveUpdate:
        update = super().observe_transition(experience, selection, signals)
        before = self.graph.contextual_memory.snapshot()
        portfolio = self._portfolio.evaluate(
            ledger=self.graph.contextual_memory,
            items=(
                ConsolidationPortfolioItem(
                    request=self._request,
                    context=ConsolidationSchedulingContext(
                        episode_index=experience.observation.step_id,
                        active_candidate_ids=tuple(sorted(self._active_candidate_ids)),
                    ),
                ),
            ),
        )
        item = portfolio.item_decisions[0]
        proposal = portfolio.selected_proposals[0] if portfolio.selected_proposals else None
        if proposal is not None:
            self._active_candidate_ids.add(proposal.candidate.candidate_id)
        after = self.graph.contextual_memory.snapshot()
        candidate = item.schedule_decision.eligibility.candidate
        self._observations.append(
            ConsolidationSchedulingShadowObservation(
                step_index=experience.observation.step_id,
                status=item.schedule_decision.status,
                proposal_id=(proposal.proposal_id if proposal is not None else None),
                candidate_id=(candidate.candidate_id if candidate is not None else None),
                selected=item.selected,
                ledger_unchanged=before == after,
            )
        )
        return update


def run_consolidation_scheduling_acceptance(
    output_directory: Path,
    *,
    first_seed: int = 7,
    second_seed: int = 11,
    play_budget: int = 8,
) -> ConsolidationSchedulingAcceptanceEvidence:
    """Prove live scheduling observation cannot alter SeedMind behavior or learning."""
    if play_budget <= 2:
        raise ValueError("play_budget must exceed two")
    output_directory.mkdir(parents=True, exist_ok=True)
    synthetic = run_consolidation_scheduling_experiment()
    factory = DynamicNurseryScenarioFactory()
    curiosity = CuriosityConfig(play_budget=play_budget)

    pretraining_shadow = NDNRALiveShadowAdapter()
    pretraining = UnifiedDevelopmentalShadowSession(
        _build_trainer(first_seed, factory),
        factory,
        UnifiedShadowConfig(seed=first_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(first_seed, factory),
        shadow=pretraining_shadow,
    ).run()
    eligibility, request = _build_live_schedule_request(pretraining_shadow.graph)

    source_brain_path = output_directory / "scheduling_acceptance_source_brain.json"
    store = NDNRABrainStore(source_brain_path)
    store.save(
        pretraining_shadow.graph,
        growth_state=pretraining.final_growth_state,
    )
    baseline_load = store.load()
    observed_load = store.load()

    baseline_shadow = NDNRALiveShadowAdapter(
        graph=baseline_load.graph,
        growth_state=baseline_load.growth_state,
    )
    observed_shadow = _SchedulingObservedShadowAdapter(
        graph=observed_load.graph,
        growth_state=observed_load.growth_state,
        request=request,
    )
    baseline = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, factory),
        factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, factory),
        shadow=baseline_shadow,
    ).run()
    scheduling_observed = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, factory),
        factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, factory),
        shadow=observed_shadow,
    ).run()

    baseline_errors = tuple(metric.mean_absolute_error for metric in baseline.metrics)
    observed_errors = tuple(metric.mean_absolute_error for metric in scheduling_observed.metrics)
    baseline_suggestions = tuple(suggestion.suggested_action for suggestion in baseline.suggestions)
    observed_suggestions = tuple(
        suggestion.suggested_action for suggestion in scheduling_observed.suggestions
    )
    observations = observed_shadow.observations
    proposal_ids = tuple(
        observation.proposal_id
        for observation in observations
        if observation.proposal_id is not None
    )
    candidate_ids = tuple(
        observation.candidate_id
        for observation in observations
        if observation.proposal_id is not None and observation.candidate_id is not None
    )
    redundant_count = len(candidate_ids) - len(set(candidate_ids))
    authority_violations = (
        baseline.authority_violation_count
        + scheduling_observed.authority_violation_count
        + sum(observation.has_execution_authority for observation in observations)
    )
    ledger_mutations = sum(not observation.ledger_unchanged for observation in observations)
    actions_unchanged = baseline.actual_actions == scheduling_observed.actual_actions
    errors_unchanged = baseline_errors == observed_errors
    suggestions_unchanged = baseline_suggestions == observed_suggestions
    signals_unchanged = baseline.signals == scheduling_observed.signals
    graphs_equal = baseline.graph_snapshot == scheduling_observed.graph_snapshot
    growth_equal = baseline.final_growth_state == scheduling_observed.final_growth_state
    pass_gate = bool(
        synthetic.evidence_aware_is_best
        and eligibility.eligible
        and actions_unchanged
        and errors_unchanged
        and suggestions_unchanged
        and signals_unchanged
        and graphs_equal
        and growth_equal
        and authority_violations == 0
        and len(observations) == play_budget
        and len(proposal_ids) == 1
        and len(set(candidate_ids)) == 1
        and redundant_count == 0
        and ledger_mutations == 0
    )
    result = ConsolidationSchedulingAcceptanceResult(
        synthetic_scheduling_gate_passed=synthetic.evidence_aware_is_best,
        live_mastery_eligible=eligibility.eligible,
        live_mastery_source_count=len(eligibility.mastery_snapshot.source_event_ids),
        live_mastery_route_count=eligibility.mastery_snapshot.unique_route_count,
        production_actions_unchanged=actions_unchanged,
        prediction_errors_unchanged=errors_unchanged,
        suggestion_sequence_unchanged=suggestions_unchanged,
        live_signals_unchanged=signals_unchanged,
        learned_graphs_equal=graphs_equal,
        growth_states_equal=growth_equal,
        authority_violation_count=authority_violations,
        schedule_evaluation_count=len(observations),
        proposal_count=len(proposal_ids),
        unique_candidate_count=len(set(candidate_ids)),
        redundant_proposal_count=redundant_count,
        scheduler_ledger_mutation_count=ledger_mutations,
        consolidation_application_count=0,
        sqlite_used_for_scheduling_acceptance=False,
        pass_gate=pass_gate,
    )
    return ConsolidationSchedulingAcceptanceEvidence(
        result=result,
        pretraining=pretraining,
        baseline=baseline,
        scheduling_observed=scheduling_observed,
        observations=observations,
        source_brain_path=source_brain_path,
    )


def export_consolidation_scheduling_acceptance(
    evidence: ConsolidationSchedulingAcceptanceEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export ASCII acceptance, comparison, and proposal evidence."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "scheduling_acceptance_report.json"
    timeline_path = output_directory / "scheduling_shadow_timeline.csv"
    proposals_path = output_directory / "scheduling_proposals.json"
    _write_ascii_json(report_path, asdict(evidence.result))
    _write_ascii_json(
        proposals_path,
        [observation.snapshot() for observation in evidence.observations],
    )
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "baseline_action",
                "observed_action",
                "baseline_suggestion",
                "observed_suggestion",
                "baseline_prediction_error",
                "observed_prediction_error",
                "schedule_status",
                "proposal_id",
                "ledger_unchanged",
            )
        )
        for baseline_record, observed_record, schedule in zip(
            evidence.baseline.records,
            evidence.scheduling_observed.records,
            evidence.observations,
            strict=True,
        ):
            writer.writerow(
                (
                    baseline_record.step_index,
                    baseline_record.actual_action.value,
                    observed_record.actual_action.value,
                    _action_value(baseline_record.suggested_action),
                    _action_value(observed_record.suggested_action),
                    baseline_record.prediction_error,
                    observed_record.prediction_error,
                    schedule.status.value,
                    schedule.proposal_id or "",
                    str(schedule.ledger_unchanged).lower(),
                )
            )
    return report_path, timeline_path, proposals_path


def _build_live_schedule_request(
    graph: MultidimensionalExperienceGraph,
) -> tuple[ConsolidationEligibility, ConsolidationScheduleRequest]:
    assembly_ids = tuple(assembly.assembly_id for assembly in graph.assemblies[:2])
    if len(assembly_ids) < 2:
        raise RuntimeError("live shadow pretraining did not produce two assemblies")
    specifications = (
        (0, assembly_ids[0], _ROUTE_IDS[0], (0.10, 0.20), True),
        (1, assembly_ids[1], _ROUTE_IDS[1], (0.50, 0.60), True),
        (2, assembly_ids[0], _ROUTE_IDS[0], (0.90, 1.00), False),
    )
    for step_id, assembly_id, route_id, sensors, transfer_succeeded in specifications:
        assembly = graph.assembly(assembly_id)
        graph.learn_contextual_experience(
            identity=EventIdentity(
                source_code="scheduling_acceptance",
                episode_id="live_mastery",
                step_id=step_id,
            ),
            correlation_group_id=f"group:scheduling_mastery:{step_id}",
            assembly_id=assembly_id,
            route_id=route_id,
            action_code=assembly.action_code,
            origin_need_code=assembly.origin_need_code,
            required_facts=assembly.required_facts,
            produced_facts=assembly.produced_facts,
            context_signature=ContextSignature.from_values(
                active_need_code=_SCHEDULING_LESSON.need_code,
                sensor_values=sensors,
                available_action_codes=(graph.assembly(item).action_code for item in assembly_ids),
            ),
            observed_effects=(
                EffectObservation(
                    effect_code=_SCHEDULING_LESSON.effect_code,
                    value=1.0,
                    confidence=1.0,
                ),
            ),
            transfer_attempted=True,
            transfer_succeeded=transfer_succeeded,
        )
    request = ConsolidationScheduleRequest(
        lesson=_SCHEDULING_LESSON,
        available_assembly_ids=assembly_ids,
        available_route_ids=_ROUTE_IDS,
    )
    profile = graph.contextual_memory.mastery_profile(_SCHEDULING_LESSON)
    eligibility = ConsolidationEligibilityPolicy().evaluate(
        ledger=graph.contextual_memory,
        lesson=_SCHEDULING_LESSON,
        mastery_profile=profile,
        available_assembly_ids=assembly_ids,
        available_route_ids=_ROUTE_IDS,
    )
    return eligibility, request


def _action_value(action: PrimitiveAction | None) -> str:
    return "" if action is None else action.value


def _write_ascii_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
