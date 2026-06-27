"""Live-shadow acceptance for non-authoritative NDNRA proposal lifecycles."""

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
    ConsolidationProposalLifecycleExperimentResult,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewRequest,
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
    run_consolidation_proposal_lifecycle_experiment,
)
from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.training import ExperienceTransition

_LIFECYCLE_LESSON = LessonIdentity(
    need_code="retain_live_lifecycle_skill",
    effect_code="lifecycle_probe",
    desired_direction=1.0,
)
_ROUTE_IDS = (
    "route:lifecycle:primary",
    "route:lifecycle:transfer",
)


@dataclass(frozen=True, slots=True)
class ConsolidationProposalLifecycleShadowObservation:
    """One read-only lifecycle observation after a live shadow transition."""

    step_index: int
    schedule_status: ConsolidationScheduleStatus
    scheduled_proposal_id: str | None
    active_proposal_id: str | None
    candidate_id: str | None
    review_action: ConsolidationProposalReviewAction | None
    lifecycle_status: ConsolidationProposalLifecycleStatus | None
    registry_record_count: int
    lifecycle_decision_count: int
    ledger_unchanged: bool
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        for name, value in (
            ("registry_record_count", self.registry_record_count),
            ("lifecycle_decision_count", self.lifecycle_decision_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must not be negative")
        if self.scheduled_proposal_id is not None:
            if self.schedule_status is not ConsolidationScheduleStatus.PROPOSED:
                raise ValueError("scheduled proposal identity requires proposed status")
            _validate_code("scheduled_proposal_id", self.scheduled_proposal_id)
        if self.active_proposal_id is not None:
            _validate_code("active_proposal_id", self.active_proposal_id)
        if self.candidate_id is not None:
            _validate_code("candidate_id", self.candidate_id)
        if (
            self.review_action is ConsolidationProposalReviewAction.DEFER
            and self.lifecycle_status is not ConsolidationProposalLifecycleStatus.DEFERRED
        ):
            raise ValueError("defer action must produce deferred lifecycle status")
        if (
            self.review_action is ConsolidationProposalReviewAction.ACCEPT
            and self.lifecycle_status is not ConsolidationProposalLifecycleStatus.ACCEPTED
        ):
            raise ValueError("accept action must produce accepted lifecycle status")
        if self.registry_record_count == 0 and (
            self.active_proposal_id is not None or self.lifecycle_status is not None
        ):
            raise ValueError("empty registry cannot expose active lifecycle state")
        if self.has_execution_authority:
            raise ValueError("lifecycle observations cannot have execution authority")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe lifecycle observation evidence."""
        return {
            "step_index": self.step_index,
            "schedule_status": self.schedule_status.value,
            "scheduled_proposal_id": self.scheduled_proposal_id,
            "active_proposal_id": self.active_proposal_id,
            "candidate_id": self.candidate_id,
            "review_action": (None if self.review_action is None else self.review_action.value),
            "lifecycle_status": (
                None if self.lifecycle_status is None else self.lifecycle_status.value
            ),
            "registry_record_count": self.registry_record_count,
            "lifecycle_decision_count": self.lifecycle_decision_count,
            "ledger_unchanged": self.ledger_unchanged,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationProposalLifecycleAcceptanceResult:
    """Synthetic and live-shadow evidence for proposal lifecycle management."""

    synthetic_lifecycle_gate_passed: bool
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
    lifecycle_evaluation_count: int
    scheduled_proposal_count: int
    review_decision_count: int
    defer_decision_count: int
    accept_decision_count: int
    retained_registry_record_count: int
    retained_lifecycle_history_count: int
    final_proposal_accepted: bool
    lifecycle_ledger_mutation_count: int
    consolidation_application_count: int
    sqlite_used_for_lifecycle_acceptance: bool
    pass_gate: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("live_mastery_source_count", self.live_mastery_source_count),
            ("live_mastery_route_count", self.live_mastery_route_count),
            ("authority_violation_count", self.authority_violation_count),
            ("lifecycle_evaluation_count", self.lifecycle_evaluation_count),
            ("scheduled_proposal_count", self.scheduled_proposal_count),
            ("review_decision_count", self.review_decision_count),
            ("defer_decision_count", self.defer_decision_count),
            ("accept_decision_count", self.accept_decision_count),
            ("retained_registry_record_count", self.retained_registry_record_count),
            ("retained_lifecycle_history_count", self.retained_lifecycle_history_count),
            ("lifecycle_ledger_mutation_count", self.lifecycle_ledger_mutation_count),
            ("consolidation_application_count", self.consolidation_application_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must not be negative")


@dataclass(frozen=True, slots=True)
class ConsolidationProposalLifecycleAcceptanceEvidence:
    """Acceptance result and complete live lifecycle comparison evidence."""

    result: ConsolidationProposalLifecycleAcceptanceResult
    synthetic: ConsolidationProposalLifecycleExperimentResult
    pretraining: UnifiedShadowResult
    baseline: UnifiedShadowResult
    lifecycle_observed: UnifiedShadowResult
    observations: tuple[ConsolidationProposalLifecycleShadowObservation, ...]
    registry: ConsolidationProposalLifecycleRegistry
    source_brain_path: Path


class _LifecycleObservedShadowAdapter(NDNRALiveShadowAdapter):
    """Run pure lifecycle review after learning without altering live cognition."""

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
        self._registry = ConsolidationProposalLifecycleRegistry(maximum_active_records=1)
        self._observations: list[ConsolidationProposalLifecycleShadowObservation] = []

    @property
    def observations(
        self,
    ) -> tuple[ConsolidationProposalLifecycleShadowObservation, ...]:
        return tuple(self._observations)

    @property
    def registry(self) -> ConsolidationProposalLifecycleRegistry:
        return self._registry

    def observe_transition(
        self,
        experience: ExperienceTransition,
        selection: CuriositySelection,
        signals: LiveDevelopmentalSignals,
    ) -> AdaptiveUpdate:
        update = super().observe_transition(experience, selection, signals)
        before = self.graph.contextual_memory.snapshot()
        step = experience.observation.step_id
        portfolio = self._portfolio.evaluate(
            ledger=self.graph.contextual_memory,
            items=(
                ConsolidationPortfolioItem(
                    request=self._request,
                    context=ConsolidationSchedulingContext(
                        episode_index=step,
                        active_candidate_ids=tuple(sorted(self._active_candidate_ids)),
                    ),
                ),
            ),
        )
        item = portfolio.item_decisions[0]
        proposal = portfolio.selected_proposals[0] if portfolio.selected_proposals else None
        review_action: ConsolidationProposalReviewAction | None = None
        if proposal is not None:
            self._active_candidate_ids.add(proposal.candidate.candidate_id)
            self._registry = self._registry.add(proposal)
            review_action = ConsolidationProposalReviewAction.DEFER
            self._registry = self._registry.review(
                ConsolidationProposalReviewRequest(
                    proposal=proposal,
                    action=review_action,
                    decision_episode=step,
                    reviewer_code="policy:live_lifecycle_shadow",
                    reason_code="bounded_observation_window",
                    defer_until_episode=step + 2,
                )
            )
        elif self._registry.active_records:
            active = self._registry.active_records[0]
            due = active.lifecycle.current_defer_until_episode
            if (
                active.lifecycle.status is ConsolidationProposalLifecycleStatus.DEFERRED
                and due is not None
                and step >= due
            ):
                review_action = ConsolidationProposalReviewAction.ACCEPT
                self._registry = self._registry.review(
                    ConsolidationProposalReviewRequest(
                        proposal=active.proposal,
                        action=review_action,
                        decision_episode=step,
                        reviewer_code="policy:live_lifecycle_shadow",
                        reason_code="bounded_review_window_complete",
                    )
                )

        active_record = self._registry.active_records[0] if self._registry.active_records else None
        after = self.graph.contextual_memory.snapshot()
        candidate = item.schedule_decision.eligibility.candidate
        self._observations.append(
            ConsolidationProposalLifecycleShadowObservation(
                step_index=step,
                schedule_status=item.schedule_decision.status,
                scheduled_proposal_id=(None if proposal is None else proposal.proposal_id),
                active_proposal_id=(
                    None if active_record is None else active_record.proposal.proposal_id
                ),
                candidate_id=(None if candidate is None else candidate.candidate_id),
                review_action=review_action,
                lifecycle_status=(
                    None if active_record is None else active_record.lifecycle.status
                ),
                registry_record_count=len(self._registry.records),
                lifecycle_decision_count=sum(
                    len(record.lifecycle.decisions) for record in self._registry.records
                ),
                ledger_unchanged=before == after,
            )
        )
        return update


def run_consolidation_proposal_lifecycle_acceptance(
    output_directory: Path,
    *,
    first_seed: int = 7,
    second_seed: int = 11,
    play_budget: int = 8,
) -> ConsolidationProposalLifecycleAcceptanceEvidence:
    """Prove lifecycle observation cannot alter SeedMind behavior or learning."""
    if play_budget <= 2:
        raise ValueError("play_budget must exceed two")
    output_directory.mkdir(parents=True, exist_ok=True)
    synthetic = run_consolidation_proposal_lifecycle_experiment()
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
    eligibility, request = _build_live_lifecycle_request(pretraining_shadow.graph)

    source_brain_path = output_directory / "proposal_lifecycle_acceptance_source_brain.json"
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
    observed_shadow = _LifecycleObservedShadowAdapter(
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
    lifecycle_observed = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, factory),
        factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, factory),
        shadow=observed_shadow,
    ).run()

    baseline_errors = tuple(metric.mean_absolute_error for metric in baseline.metrics)
    observed_errors = tuple(metric.mean_absolute_error for metric in lifecycle_observed.metrics)
    baseline_suggestions = tuple(suggestion.suggested_action for suggestion in baseline.suggestions)
    observed_suggestions = tuple(
        suggestion.suggested_action for suggestion in lifecycle_observed.suggestions
    )
    observations = observed_shadow.observations
    registry = observed_shadow.registry
    actions_unchanged = baseline.actual_actions == lifecycle_observed.actual_actions
    errors_unchanged = baseline_errors == observed_errors
    suggestions_unchanged = baseline_suggestions == observed_suggestions
    signals_unchanged = baseline.signals == lifecycle_observed.signals
    graphs_equal = baseline.graph_snapshot == lifecycle_observed.graph_snapshot
    growth_equal = baseline.final_growth_state == lifecycle_observed.final_growth_state
    scheduled_count = sum(
        observation.scheduled_proposal_id is not None for observation in observations
    )
    defer_count = sum(
        observation.review_action is ConsolidationProposalReviewAction.DEFER
        for observation in observations
    )
    accept_count = sum(
        observation.review_action is ConsolidationProposalReviewAction.ACCEPT
        for observation in observations
    )
    review_count = defer_count + accept_count
    history_count = sum(len(record.lifecycle.decisions) for record in registry.records)
    final_accepted = bool(
        len(registry.active_records) == 1
        and registry.active_records[0].lifecycle.status
        is ConsolidationProposalLifecycleStatus.ACCEPTED
    )
    authority_violations = (
        baseline.authority_violation_count
        + lifecycle_observed.authority_violation_count
        + sum(observation.has_execution_authority for observation in observations)
        + int(registry.has_execution_authority)
    )
    ledger_mutations = sum(not observation.ledger_unchanged for observation in observations)
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
        and scheduled_count == 1
        and review_count == 2
        and defer_count == 1
        and accept_count == 1
        and len(registry.records) == 1
        and history_count == 2
        and final_accepted
        and ledger_mutations == 0
    )
    result = ConsolidationProposalLifecycleAcceptanceResult(
        synthetic_lifecycle_gate_passed=synthetic.evidence_aware_is_best,
        live_mastery_eligible=eligibility.eligible,
        live_mastery_source_count=len(eligibility.mastery_snapshot.source_event_ids),
        live_mastery_route_count=(eligibility.mastery_snapshot.unique_route_count),
        production_actions_unchanged=actions_unchanged,
        prediction_errors_unchanged=errors_unchanged,
        suggestion_sequence_unchanged=suggestions_unchanged,
        live_signals_unchanged=signals_unchanged,
        learned_graphs_equal=graphs_equal,
        growth_states_equal=growth_equal,
        authority_violation_count=authority_violations,
        lifecycle_evaluation_count=len(observations),
        scheduled_proposal_count=scheduled_count,
        review_decision_count=review_count,
        defer_decision_count=defer_count,
        accept_decision_count=accept_count,
        retained_registry_record_count=len(registry.records),
        retained_lifecycle_history_count=history_count,
        final_proposal_accepted=final_accepted,
        lifecycle_ledger_mutation_count=ledger_mutations,
        consolidation_application_count=0,
        sqlite_used_for_lifecycle_acceptance=False,
        pass_gate=pass_gate,
    )
    return ConsolidationProposalLifecycleAcceptanceEvidence(
        result=result,
        synthetic=synthetic,
        pretraining=pretraining,
        baseline=baseline,
        lifecycle_observed=lifecycle_observed,
        observations=observations,
        registry=registry,
        source_brain_path=source_brain_path,
    )


def export_consolidation_proposal_lifecycle_acceptance(
    evidence: ConsolidationProposalLifecycleAcceptanceEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export ASCII acceptance, comparison, and registry evidence."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "proposal_lifecycle_acceptance_report.json"
    timeline_path = output_directory / "proposal_lifecycle_shadow_timeline.csv"
    registry_path = output_directory / "proposal_lifecycle_registry.json"
    _write_ascii_json(report_path, asdict(evidence.result))
    _write_ascii_json(
        registry_path,
        {
            "registry": evidence.registry.snapshot(),
            "observations": [observation.snapshot() for observation in evidence.observations],
        },
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
                "scheduled_proposal_id",
                "review_action",
                "lifecycle_status",
                "lifecycle_decision_count",
                "ledger_unchanged",
            )
        )
        for baseline_record, observed_record, lifecycle in zip(
            evidence.baseline.records,
            evidence.lifecycle_observed.records,
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
                    lifecycle.schedule_status.value,
                    lifecycle.scheduled_proposal_id or "",
                    ("" if lifecycle.review_action is None else lifecycle.review_action.value),
                    (
                        ""
                        if lifecycle.lifecycle_status is None
                        else lifecycle.lifecycle_status.value
                    ),
                    lifecycle.lifecycle_decision_count,
                    str(lifecycle.ledger_unchanged).lower(),
                )
            )
    return report_path, timeline_path, registry_path


def _build_live_lifecycle_request(
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
                source_code="proposal_lifecycle_acceptance",
                episode_id="live_mastery",
                step_id=step_id,
            ),
            correlation_group_id=f"group:lifecycle_mastery:{step_id}",
            assembly_id=assembly_id,
            route_id=route_id,
            action_code=assembly.action_code,
            origin_need_code=assembly.origin_need_code,
            required_facts=assembly.required_facts,
            produced_facts=assembly.produced_facts,
            context_signature=ContextSignature.from_values(
                active_need_code=_LIFECYCLE_LESSON.need_code,
                sensor_values=sensors,
                available_action_codes=(graph.assembly(item).action_code for item in assembly_ids),
            ),
            observed_effects=(
                EffectObservation(
                    effect_code=_LIFECYCLE_LESSON.effect_code,
                    value=1.0,
                    confidence=1.0,
                ),
            ),
            transfer_attempted=True,
            transfer_succeeded=transfer_succeeded,
        )
    request = ConsolidationScheduleRequest(
        lesson=_LIFECYCLE_LESSON,
        available_assembly_ids=assembly_ids,
        available_route_ids=_ROUTE_IDS,
    )
    profile = graph.contextual_memory.mastery_profile(_LIFECYCLE_LESSON)
    eligibility = ConsolidationEligibilityPolicy().evaluate(
        ledger=graph.contextual_memory,
        lesson=_LIFECYCLE_LESSON,
        mastery_profile=profile,
        available_assembly_ids=assembly_ids,
        available_route_ids=_ROUTE_IDS,
    )
    return eligibility, request


def _action_value(action: PrimitiveAction | None) -> str:
    return "" if action is None else action.value


def _write_ascii_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(
            payload,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="ascii",
    )


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")
