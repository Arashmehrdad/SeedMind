"""Restart and live-shadow acceptance for persisted NDNRA proposal memory."""

from __future__ import annotations

import csv
import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from seedmind.curiosity import CuriosityConfig, CuriositySelection
from seedmind.environment import DynamicNurseryScenarioFactory
from seedmind.integration.consolidation_proposal_lifecycle_acceptance import (
    _build_live_lifecycle_request,
)
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
    BRAIN_SCHEMA_VERSION,
    AdaptiveUpdate,
    BrainLoadResult,
    BrainLoadStatus,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalRevalidationPolicy,
    ConsolidationProposalRevalidationReport,
    ConsolidationProposalRevalidationStatus,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewRequest,
    ConsolidationScheduleProposal,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
    ContextSignature,
    EffectObservation,
    EventIdentity,
    NDNRABrainStore,
    NDNRAConsolidationCheckpoint,
    NDNRAExecutionCheckpoint,
    NDNRAGrowthState,
    NDNRAProposalLifecycleCheckpoint,
)
from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.training import ExperienceTransition


@dataclass(frozen=True, slots=True)
class RestartSafeProposalMemoryObservation:
    """One post-transition revalidation observation with no authority."""

    step_index: int
    status: ConsolidationProposalRevalidationStatus
    proposal_id: str
    candidate_id: str
    registry_unchanged: bool
    ledger_unchanged_by_revalidation: bool
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        for name, value in (
            ("proposal_id", self.proposal_id),
            ("candidate_id", self.candidate_id),
        ):
            if not value.strip() or not value.isascii():
                raise ValueError(f"{name} must be non-empty ASCII")
        if not self.registry_unchanged:
            raise ValueError("restart revalidation must preserve registry state")
        if not self.ledger_unchanged_by_revalidation:
            raise ValueError("restart revalidation must preserve contextual evidence")
        if self.has_execution_authority:
            raise ValueError("restart revalidation observations have no authority")

    def snapshot(self) -> dict[str, object]:
        return {
            "step_index": self.step_index,
            "status": self.status.value,
            "proposal_id": self.proposal_id,
            "candidate_id": self.candidate_id,
            "registry_unchanged": self.registry_unchanged,
            "ledger_unchanged_by_revalidation": self.ledger_unchanged_by_revalidation,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class RestartSafeProposalMemoryAcceptanceResult:
    """Falsifiable restart, corruption, staleness, and live invariance evidence."""

    brain_schema_version: int
    exact_graph_round_trip: bool
    exact_growth_round_trip: bool
    exact_lifecycle_round_trip: bool
    exact_review_history_round_trip: bool
    checksum_verified: bool
    temporary_file_remaining: bool
    legacy_v1_migrated_empty: bool
    legacy_v2_migrated_empty: bool
    legacy_v3_migrated_empty: bool
    legacy_v4_migrated_empty: bool
    checksum_corruption_fallback_complete: bool
    relational_corruption_fallback_complete: bool
    current_after_clean_restart: bool
    stale_after_additional_evidence: bool
    stale_registry_unchanged: bool
    production_actions_unchanged: bool
    prediction_errors_unchanged: bool
    suggestion_sequence_unchanged: bool
    live_signals_unchanged: bool
    learned_graphs_equal: bool
    growth_states_equal: bool
    revalidation_evaluation_count: int
    current_revalidation_count: int
    revalidation_registry_mutation_count: int
    revalidation_ledger_mutation_count: int
    authority_violation_count: int
    consolidation_application_count: int
    replay_trigger_count: int
    restoration_trigger_count: int
    sqlite_used_for_restart_acceptance: bool
    pass_gate: bool

    def __post_init__(self) -> None:
        if self.brain_schema_version < 1:
            raise ValueError("brain_schema_version must be positive")
        for name, value in (
            ("revalidation_evaluation_count", self.revalidation_evaluation_count),
            ("current_revalidation_count", self.current_revalidation_count),
            ("revalidation_registry_mutation_count", self.revalidation_registry_mutation_count),
            ("revalidation_ledger_mutation_count", self.revalidation_ledger_mutation_count),
            ("authority_violation_count", self.authority_violation_count),
            ("consolidation_application_count", self.consolidation_application_count),
            ("replay_trigger_count", self.replay_trigger_count),
            ("restoration_trigger_count", self.restoration_trigger_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must not be negative")


@dataclass(frozen=True, slots=True)
class RestartSafeProposalMemoryAcceptanceEvidence:
    """Acceptance result plus complete live and restart evidence."""

    result: RestartSafeProposalMemoryAcceptanceResult
    baseline: UnifiedShadowResult
    persisted: UnifiedShadowResult
    observations: tuple[RestartSafeProposalMemoryObservation, ...]
    clean_restart_report: ConsolidationProposalRevalidationReport
    stale_restart_report: ConsolidationProposalRevalidationReport
    accepted_checkpoint: NDNRAProposalLifecycleCheckpoint
    brain_path: Path


class _RestartRevalidatingShadowAdapter(NDNRALiveShadowAdapter):
    """Observe live learning and revalidate restored proposals afterward."""

    def __init__(
        self,
        *,
        graph: MultidimensionalExperienceGraph,
        growth_state: NDNRAGrowthState,
        registry: ConsolidationProposalLifecycleRegistry,
    ) -> None:
        super().__init__(graph=graph, growth_state=growth_state)
        self._registry = registry
        self._policy = ConsolidationProposalRevalidationPolicy()
        self._observations: list[RestartSafeProposalMemoryObservation] = []

    @property
    def observations(self) -> tuple[RestartSafeProposalMemoryObservation, ...]:
        return tuple(self._observations)

    def observe_transition(
        self,
        experience: ExperienceTransition,
        selection: CuriositySelection,
        signals: LiveDevelopmentalSignals,
    ) -> AdaptiveUpdate:
        update = super().observe_transition(experience, selection, signals)
        ledger_before = self.graph.contextual_memory.snapshot()
        registry_before = self._registry.snapshot()
        report = self._policy.evaluate_registry(
            registry=self._registry,
            ledger=self.graph.contextual_memory,
            available_assembly_ids=tuple(
                assembly.assembly_id for assembly in self.graph.assemblies
            ),
            available_route_ids=tuple(
                sorted({trace.route_id for trace in self.graph.contextual_memory.traces})
            ),
        )
        if len(report.decisions) != 1:
            raise RuntimeError("restart acceptance requires one active proposal")
        decision = report.decisions[0]
        self._observations.append(
            RestartSafeProposalMemoryObservation(
                step_index=experience.observation.step_id,
                status=decision.status,
                proposal_id=decision.proposal.proposal_id,
                candidate_id=decision.proposal.candidate.candidate_id,
                registry_unchanged=registry_before == self._registry.snapshot(),
                ledger_unchanged_by_revalidation=(
                    ledger_before == self.graph.contextual_memory.snapshot()
                ),
            )
        )
        return update


def run_restart_safe_proposal_memory_acceptance(
    output_directory: Path,
    *,
    first_seed: int = 7,
    second_seed: int = 11,
    play_budget: int = 8,
) -> RestartSafeProposalMemoryAcceptanceEvidence:
    """Run the complete restart-safe proposal memory acceptance gate."""
    if play_budget <= 2:
        raise ValueError("play_budget must exceed two")
    output_directory.mkdir(parents=True, exist_ok=True)
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
    schedule = ConsolidationSchedulingPolicy(
        first_eligible_episode=100,
        minimum_interval_episodes=1,
    ).evaluate(
        ledger=pretraining_shadow.graph.contextual_memory,
        request=request,
        context=ConsolidationSchedulingContext(episode_index=100),
    )
    if schedule.proposal is None or eligibility.candidate is None:
        raise RuntimeError("restart acceptance could not create a lifecycle proposal")
    proposal = schedule.proposal
    registry = (
        ConsolidationProposalLifecycleRegistry()
        .add(proposal)
        .review(
            ConsolidationProposalReviewRequest(
                proposal=proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=101,
                reviewer_code="human:restart_acceptance",
                reason_code="pre_restart_review_passed",
            )
        )
    )
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=registry)

    brain_path = output_directory / "restart_safe_proposal_memory_brain.json"
    store = NDNRABrainStore(brain_path)
    saved = store.save(
        pretraining_shadow.graph,
        growth_state=pretraining.final_growth_state,
        proposal_lifecycle_checkpoint=checkpoint,
    )
    clean_load = store.load()
    baseline_path = output_directory / "restart_safe_proposal_memory_baseline.json"
    NDNRABrainStore(baseline_path).save(
        pretraining_shadow.graph,
        growth_state=pretraining.final_growth_state,
    )
    baseline_load = NDNRABrainStore(baseline_path).load()
    exact_graph_round_trip = clean_load.graph.snapshot() == pretraining_shadow.graph.snapshot()
    exact_growth_round_trip = clean_load.growth_state == pretraining.final_growth_state
    exact_lifecycle_round_trip = clean_load.proposal_lifecycle_checkpoint == checkpoint
    exact_review_history = bool(
        clean_load.proposal_lifecycle_checkpoint.registry.records[0].lifecycle.decisions
        == checkpoint.registry.records[0].lifecycle.decisions
    )

    clean_report = ConsolidationProposalRevalidationPolicy().evaluate_registry(
        registry=clean_load.proposal_lifecycle_checkpoint.registry,
        ledger=clean_load.graph.contextual_memory,
        available_assembly_ids=tuple(
            assembly.assembly_id for assembly in clean_load.graph.assemblies
        ),
        available_route_ids=tuple(
            sorted({trace.route_id for trace in clean_load.graph.contextual_memory.traces})
        ),
    )

    stale_load = store.load()
    _add_independent_lifecycle_evidence(stale_load.graph, proposal)
    stale_registry_before = stale_load.proposal_lifecycle_checkpoint.registry.snapshot()
    stale_report = ConsolidationProposalRevalidationPolicy().evaluate_registry(
        registry=stale_load.proposal_lifecycle_checkpoint.registry,
        ledger=stale_load.graph.contextual_memory,
        available_assembly_ids=tuple(
            assembly.assembly_id for assembly in stale_load.graph.assemblies
        ),
        available_route_ids=tuple(
            sorted({trace.route_id for trace in stale_load.graph.contextual_memory.traces})
        ),
    )
    stale_registry_unchanged = (
        stale_registry_before == stale_load.proposal_lifecycle_checkpoint.registry.snapshot()
    )

    migration_results = tuple(
        _legacy_migration_is_empty(brain_path, output_directory, version)
        for version in (1, 2, 3, 4)
    )
    checksum_fallback = _checksum_corruption_falls_back(
        brain_path,
        output_directory / "restart_safe_checksum_corrupt.json",
    )
    relational_fallback = _relational_corruption_falls_back(
        brain_path,
        output_directory / "restart_safe_relational_corrupt.json",
    )

    baseline_shadow = NDNRALiveShadowAdapter(
        graph=baseline_load.graph,
        growth_state=baseline_load.growth_state,
    )
    persisted_shadow = _RestartRevalidatingShadowAdapter(
        graph=clean_load.graph,
        growth_state=clean_load.growth_state,
        registry=clean_load.proposal_lifecycle_checkpoint.registry,
    )
    baseline = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, factory),
        factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, factory),
        shadow=baseline_shadow,
    ).run()
    persisted = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, factory),
        factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, factory),
        shadow=persisted_shadow,
    ).run()

    observations = persisted_shadow.observations
    baseline_errors = tuple(metric.mean_absolute_error for metric in baseline.metrics)
    persisted_errors = tuple(metric.mean_absolute_error for metric in persisted.metrics)
    baseline_suggestions = tuple(suggestion.suggested_action for suggestion in baseline.suggestions)
    persisted_suggestions = tuple(
        suggestion.suggested_action for suggestion in persisted.suggestions
    )
    actions_equal = baseline.actual_actions == persisted.actual_actions
    errors_equal = baseline_errors == persisted_errors
    suggestions_equal = baseline_suggestions == persisted_suggestions
    signals_equal = baseline.signals == persisted.signals
    graphs_equal = baseline.graph_snapshot == persisted.graph_snapshot
    growth_equal = baseline.final_growth_state == persisted.final_growth_state
    current_count = sum(
        observation.status is ConsolidationProposalRevalidationStatus.CURRENT
        for observation in observations
    )
    registry_mutations = sum(not observation.registry_unchanged for observation in observations)
    ledger_mutations = sum(
        not observation.ledger_unchanged_by_revalidation for observation in observations
    )
    authority_violations = (
        baseline.authority_violation_count
        + persisted.authority_violation_count
        + sum(observation.has_execution_authority for observation in observations)
        + int(clean_report.has_execution_authority)
        + int(stale_report.has_execution_authority)
    )
    clean_current = bool(
        len(clean_report.decisions) == 1
        and clean_report.decisions[0].status is ConsolidationProposalRevalidationStatus.CURRENT
    )
    stale_detected = bool(
        len(stale_report.decisions) == 1
        and stale_report.decisions[0].status is ConsolidationProposalRevalidationStatus.STALE
    )
    pass_gate = bool(
        BRAIN_SCHEMA_VERSION == 6
        and saved.schema_version == BRAIN_SCHEMA_VERSION
        and not saved.temporary_file_remaining
        and clean_load.status is BrainLoadStatus.LOADED
        and clean_load.checksum_verified
        and not clean_load.used_fallback
        and exact_graph_round_trip
        and exact_growth_round_trip
        and exact_lifecycle_round_trip
        and exact_review_history
        and all(migration_results)
        and checksum_fallback
        and relational_fallback
        and clean_current
        and stale_detected
        and stale_registry_unchanged
        and actions_equal
        and errors_equal
        and suggestions_equal
        and signals_equal
        and graphs_equal
        and growth_equal
        and len(observations) == play_budget
        and current_count == play_budget
        and registry_mutations == 0
        and ledger_mutations == 0
        and authority_violations == 0
    )
    result = RestartSafeProposalMemoryAcceptanceResult(
        brain_schema_version=BRAIN_SCHEMA_VERSION,
        exact_graph_round_trip=exact_graph_round_trip,
        exact_growth_round_trip=exact_growth_round_trip,
        exact_lifecycle_round_trip=exact_lifecycle_round_trip,
        exact_review_history_round_trip=exact_review_history,
        checksum_verified=clean_load.checksum_verified,
        temporary_file_remaining=saved.temporary_file_remaining,
        legacy_v1_migrated_empty=migration_results[0],
        legacy_v2_migrated_empty=migration_results[1],
        legacy_v3_migrated_empty=migration_results[2],
        legacy_v4_migrated_empty=migration_results[3],
        checksum_corruption_fallback_complete=checksum_fallback,
        relational_corruption_fallback_complete=relational_fallback,
        current_after_clean_restart=clean_current,
        stale_after_additional_evidence=stale_detected,
        stale_registry_unchanged=stale_registry_unchanged,
        production_actions_unchanged=actions_equal,
        prediction_errors_unchanged=errors_equal,
        suggestion_sequence_unchanged=suggestions_equal,
        live_signals_unchanged=signals_equal,
        learned_graphs_equal=graphs_equal,
        growth_states_equal=growth_equal,
        revalidation_evaluation_count=len(observations),
        current_revalidation_count=current_count,
        revalidation_registry_mutation_count=registry_mutations,
        revalidation_ledger_mutation_count=ledger_mutations,
        authority_violation_count=authority_violations,
        consolidation_application_count=0,
        replay_trigger_count=0,
        restoration_trigger_count=0,
        sqlite_used_for_restart_acceptance=False,
        pass_gate=pass_gate,
    )
    return RestartSafeProposalMemoryAcceptanceEvidence(
        result=result,
        baseline=baseline,
        persisted=persisted,
        observations=observations,
        clean_restart_report=clean_report,
        stale_restart_report=stale_report,
        accepted_checkpoint=checkpoint,
        brain_path=brain_path,
    )


def export_restart_safe_proposal_memory_acceptance(
    evidence: RestartSafeProposalMemoryAcceptanceEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export ASCII acceptance report, live timeline, and restart decisions."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "restart_safe_proposal_memory_report.json"
    timeline_path = output_directory / "restart_safe_proposal_memory_timeline.csv"
    decisions_path = output_directory / "restart_safe_proposal_memory_decisions.json"
    _write_ascii_json(report_path, asdict(evidence.result))
    _write_ascii_json(
        decisions_path,
        {
            "clean_restart": evidence.clean_restart_report.snapshot(),
            "stale_restart": evidence.stale_restart_report.snapshot(),
            "persisted_checkpoint": evidence.accepted_checkpoint.snapshot(),
        },
    )
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "baseline_action",
                "persisted_action",
                "baseline_prediction_error",
                "persisted_prediction_error",
                "revalidation_status",
                "proposal_id",
                "registry_unchanged",
                "ledger_unchanged_by_revalidation",
            )
        )
        for baseline_record, persisted_record, observation in zip(
            evidence.baseline.records,
            evidence.persisted.records,
            evidence.observations,
            strict=True,
        ):
            writer.writerow(
                (
                    baseline_record.step_index,
                    baseline_record.actual_action.value,
                    persisted_record.actual_action.value,
                    baseline_record.prediction_error,
                    persisted_record.prediction_error,
                    observation.status.value,
                    observation.proposal_id,
                    str(observation.registry_unchanged).lower(),
                    str(observation.ledger_unchanged_by_revalidation).lower(),
                )
            )
    return report_path, timeline_path, decisions_path


def _add_independent_lifecycle_evidence(
    graph: MultidimensionalExperienceGraph,
    proposal: ConsolidationScheduleProposal,
) -> None:
    candidate = proposal.candidate
    assembly_id = candidate.assembly_ids[0]
    route_id = candidate.route_ids[0]
    assembly = graph.assembly(assembly_id)
    graph.learn_contextual_experience(
        identity=EventIdentity(
            source_code="restart_safe_proposal_memory_acceptance",
            episode_id="post_restart_evidence",
            step_id=1000,
        ),
        correlation_group_id="group:restart_safe_post_restart:1000",
        assembly_id=assembly_id,
        route_id=route_id,
        action_code=assembly.action_code,
        origin_need_code=assembly.origin_need_code,
        required_facts=assembly.required_facts,
        produced_facts=assembly.produced_facts,
        context_signature=ContextSignature.from_values(
            active_need_code=candidate.lesson_identity.need_code,
            sensor_values=(0.33, 0.77),
            available_action_codes=(
                graph.assembly(item).action_code for item in candidate.assembly_ids
            ),
        ),
        observed_effects=(
            EffectObservation(
                effect_code=candidate.lesson_identity.effect_code,
                value=candidate.lesson_identity.desired_direction,
                confidence=1.0,
            ),
        ),
        transfer_attempted=True,
        transfer_succeeded=True,
    )


def _legacy_migration_is_empty(
    source_path: Path,
    output_directory: Path,
    version: int,
) -> bool:
    target = output_directory / f"restart_safe_legacy_v{version}.json"
    raw = _read_json_object(source_path)
    payload = _require_object(raw, "payload")
    payload.pop("execution_checkpoint", None)
    if version < 4:
        payload.pop("proposal_lifecycle_checkpoint", None)
    if version < 3:
        payload.pop("consolidation_checkpoint", None)
    if version == 1:
        graph = _require_object(payload, "graph")
        graph.pop("contextual_memory", None)
    raw["schema_version"] = version
    _write_envelope(target, raw)
    loaded = NDNRABrainStore(target).load()
    proposal_migration_valid = (
        loaded.proposal_lifecycle_checkpoint == NDNRAProposalLifecycleCheckpoint.empty()
        if version < 4
        else bool(loaded.proposal_lifecycle_checkpoint.registry.records)
    )
    return bool(
        loaded.status is BrainLoadStatus.LOADED
        and loaded.migrated_from_version == version
        and loaded.checksum_verified
        and not loaded.used_fallback
        and proposal_migration_valid
        and loaded.execution_checkpoint == NDNRAExecutionCheckpoint.empty()
    )


def _checksum_corruption_falls_back(source_path: Path, target: Path) -> bool:
    raw = _read_json_object(source_path)
    raw["checksum"] = "0" * 64
    target.write_text(
        json.dumps(raw, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    return _complete_fallback(NDNRABrainStore(target).load())


def _relational_corruption_falls_back(source_path: Path, target: Path) -> bool:
    raw = _read_json_object(source_path)
    payload = _require_object(raw, "payload")
    lifecycle = _require_object(payload, "proposal_lifecycle_checkpoint")
    registry = _require_object(lifecycle, "registry")
    registry["active_record_count"] = 0
    _write_envelope(target, raw)
    return _complete_fallback(NDNRABrainStore(target).load())


def _complete_fallback(loaded: BrainLoadResult) -> bool:
    return bool(
        loaded.status is BrainLoadStatus.CORRUPT_FALLBACK
        and loaded.used_fallback
        and not loaded.checksum_verified
        and loaded.graph.assembly_count == 0
        and loaded.growth_state == NDNRAGrowthState()
        and loaded.consolidation_checkpoint == NDNRAConsolidationCheckpoint.empty()
        and loaded.proposal_lifecycle_checkpoint == NDNRAProposalLifecycleCheckpoint.empty()
        and loaded.execution_checkpoint == NDNRAExecutionCheckpoint.empty()
    )


def _read_json_object(path: Path) -> dict[str, object]:
    raw: object = json.loads(path.read_text(encoding="ascii"))
    if not isinstance(raw, dict) or not all(isinstance(key, str) for key in raw):
        raise ValueError("brain envelope must be a string-keyed object")
    return raw


def _require_object(values: dict[str, object], key: str) -> dict[str, object]:
    value = values.get(key)
    if not isinstance(value, dict) or not all(isinstance(item, str) for item in value):
        raise ValueError(f"{key} must be a string-keyed object")
    return value


def _write_envelope(path: Path, envelope: dict[str, object]) -> None:
    body: dict[str, object] = {
        "schema": envelope["schema"],
        "schema_version": envelope["schema_version"],
        "payload": envelope["payload"],
    }
    envelope["checksum"] = hashlib.sha256(
        json.dumps(
            body,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()
    path.write_text(
        json.dumps(envelope, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )


def _write_ascii_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
