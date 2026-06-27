"""Live-shadow acceptance gate for persisted reversible NDNRA consolidation."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.curiosity import CuriosityConfig
from seedmind.environment import DynamicNurseryScenarioFactory
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
    BrainLoadStatus,
    ConsolidationApplicationResult,
    ConsolidationApplicationState,
    ConsolidationEligibility,
    ConsolidationEligibilityPolicy,
    ConsolidationReopeningPolicy,
    ConsolidationRollbackAuditRecord,
    ContextSignature,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
    NDNRABrainStore,
    NDNRAConsolidationCheckpoint,
    rollback_consolidation,
    run_consolidation_interference_experiment,
)
from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph

_CONSOLIDATION_LESSON = LessonIdentity(
    need_code="retain_live_shadow_skill",
    effect_code="retention_probe",
    desired_direction=1.0,
)
_ROUTE_IDS = (
    "route:consolidation:primary",
    "route:consolidation:transfer",
)


@dataclass(frozen=True, slots=True)
class ConsolidationAcceptanceResult:
    """Synthetic, restart, shadow-invariance, and restoration acceptance metrics."""

    synthetic_interference_gate_passed: bool
    live_mastery_eligible: bool
    live_mastery_source_count: int
    live_mastery_route_count: int
    saved_schema_version: int
    active_checkpoint_round_trip_exact: bool
    baseline_checkpoint_empty: bool
    loaded_graphs_equal: bool
    loaded_growth_states_equal: bool
    production_actions_unchanged: bool
    prediction_errors_unchanged: bool
    suggestion_sequence_unchanged: bool
    learned_graphs_equal: bool
    authority_violation_count: int
    checkpoint_unchanged_during_shadow: bool
    post_restart_reopening_passed: bool
    post_restart_restoration_exact: bool
    source_events_preserved: bool
    rollback_audit_round_trip_exact: bool
    sqlite_used_for_consolidation_acceptance: bool
    pass_gate: bool

    def __post_init__(self) -> None:
        for name, value in (
            ("live_mastery_source_count", self.live_mastery_source_count),
            ("live_mastery_route_count", self.live_mastery_route_count),
            ("saved_schema_version", self.saved_schema_version),
            ("authority_violation_count", self.authority_violation_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must not be negative")


@dataclass(frozen=True, slots=True)
class ConsolidationAcceptanceEvidence:
    """Acceptance result plus complete live-shadow comparison evidence."""

    result: ConsolidationAcceptanceResult
    pretraining: UnifiedShadowResult
    baseline: UnifiedShadowResult
    checkpoint_tracked: UnifiedShadowResult
    active_state_path: Path
    restored_state_path: Path
    candidate_id: str
    rollback_id: str


def run_consolidation_acceptance(
    output_directory: Path,
    *,
    first_seed: int = 7,
    second_seed: int = 11,
    play_budget: int = 12,
) -> ConsolidationAcceptanceEvidence:
    """Prove checkpoint carriage and reversal cannot alter production behavior."""
    if play_budget <= 2:
        raise ValueError("play_budget must exceed two")
    output_directory.mkdir(parents=True, exist_ok=True)
    synthetic = run_consolidation_interference_experiment()
    scenario_factory = DynamicNurseryScenarioFactory()
    curiosity = CuriosityConfig(play_budget=play_budget)

    pretraining_shadow = NDNRALiveShadowAdapter()
    pretraining = UnifiedDevelopmentalShadowSession(
        _build_trainer(first_seed, scenario_factory),
        scenario_factory,
        UnifiedShadowConfig(seed=first_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(first_seed, scenario_factory),
        shadow=pretraining_shadow,
    ).run()
    eligibility, application, checkpoint = _build_live_checkpoint(pretraining_shadow.graph)

    baseline_path = output_directory / "consolidation_baseline_brain.json"
    active_state_path = output_directory / "consolidation_active_brain.json"
    baseline_store = NDNRABrainStore(baseline_path)
    active_store = NDNRABrainStore(active_state_path)
    baseline_store.save(
        pretraining_shadow.graph,
        growth_state=pretraining.final_growth_state,
    )
    active_save = active_store.save(
        pretraining_shadow.graph,
        growth_state=pretraining.final_growth_state,
        consolidation_checkpoint=checkpoint,
    )
    baseline_load = baseline_store.load()
    active_load = active_store.load()

    loaded_graphs_equal = baseline_load.graph.snapshot() == active_load.graph.snapshot()
    loaded_growth_states_equal = baseline_load.growth_state == active_load.growth_state
    active_checkpoint_exact = active_load.consolidation_checkpoint == checkpoint
    baseline_checkpoint_empty = (
        baseline_load.consolidation_checkpoint == NDNRAConsolidationCheckpoint.empty()
    )
    checkpoint_before_shadow = active_load.consolidation_checkpoint.snapshot()

    baseline_shadow = NDNRALiveShadowAdapter(
        graph=baseline_load.graph,
        growth_state=baseline_load.growth_state,
    )
    tracked_shadow = NDNRALiveShadowAdapter(
        graph=active_load.graph,
        growth_state=active_load.growth_state,
    )
    baseline = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, scenario_factory),
        scenario_factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, scenario_factory),
        shadow=baseline_shadow,
    ).run()
    tracked = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, scenario_factory),
        scenario_factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, scenario_factory),
        shadow=tracked_shadow,
    ).run()

    baseline_errors = tuple(metric.mean_absolute_error for metric in baseline.metrics)
    tracked_errors = tuple(metric.mean_absolute_error for metric in tracked.metrics)
    baseline_suggestions = tuple(item.suggested_action for item in baseline.suggestions)
    tracked_suggestions = tuple(item.suggested_action for item in tracked.suggestions)
    production_actions_unchanged = baseline.actual_actions == tracked.actual_actions
    prediction_errors_unchanged = baseline_errors == tracked_errors
    suggestion_sequence_unchanged = baseline_suggestions == tracked_suggestions
    learned_graphs_equal = baseline.graph_snapshot == tracked.graph_snapshot
    authority_violations = baseline.authority_violation_count + tracked.authority_violation_count
    checkpoint_unchanged = (
        active_load.consolidation_checkpoint.snapshot() == checkpoint_before_shadow
    )

    application_state = active_load.consolidation_checkpoint.application_state()
    if application_state is None:
        raise RuntimeError("active consolidation checkpoint did not restore application state")
    loaded_application = active_load.consolidation_checkpoint.active_applications[0]
    ledger = tracked_shadow.graph.contextual_memory
    original_source_ids = loaded_application.candidate.source_event_ids
    trace_count_before = ledger.trace_count
    _record_later_contradiction(
        tracked_shadow.graph,
        loaded_application,
        step_id=trace_count_before,
    )
    decision = ConsolidationReopeningPolicy().evaluate(
        ledger=ledger,
        candidate=loaded_application.candidate,
    )
    restoration = rollback_consolidation(
        state=application_state,
        application=loaded_application,
        decision=decision,
    )
    source_events_preserved = bool(
        ledger.trace_count == trace_count_before + 1
        and all(ledger.trace(event_id).identity.key == event_id for event_id in original_source_ids)
    )
    restoration_exact = restoration.after == loaded_application.before
    audit_record = ConsolidationRollbackAuditRecord.from_result(restoration)
    restored_checkpoint = NDNRAConsolidationCheckpoint(
        state=application_state.snapshot(),
        rollback_records=(audit_record,),
    )
    restored_state_path = output_directory / "consolidation_restored_brain.json"
    restored_store = NDNRABrainStore(restored_state_path)
    restored_store.save(
        tracked_shadow.graph,
        growth_state=tracked.final_growth_state,
        consolidation_checkpoint=restored_checkpoint,
    )
    restored_load = restored_store.load()
    rollback_audit_exact = restored_load.consolidation_checkpoint == restored_checkpoint

    pass_gate = bool(
        synthetic.result.pass_gate
        and eligibility.eligible
        and active_save.schema_version == 3
        and baseline_load.status is BrainLoadStatus.LOADED
        and active_load.status is BrainLoadStatus.LOADED
        and active_checkpoint_exact
        and baseline_checkpoint_empty
        and loaded_graphs_equal
        and loaded_growth_states_equal
        and production_actions_unchanged
        and prediction_errors_unchanged
        and suggestion_sequence_unchanged
        and learned_graphs_equal
        and authority_violations == 0
        and checkpoint_unchanged
        and decision.reopen
        and restoration_exact
        and source_events_preserved
        and restored_load.status is BrainLoadStatus.LOADED
        and rollback_audit_exact
    )
    result = ConsolidationAcceptanceResult(
        synthetic_interference_gate_passed=synthetic.result.pass_gate,
        live_mastery_eligible=eligibility.eligible,
        live_mastery_source_count=len(application.candidate.source_event_ids),
        live_mastery_route_count=len(application.candidate.route_ids),
        saved_schema_version=active_save.schema_version,
        active_checkpoint_round_trip_exact=active_checkpoint_exact,
        baseline_checkpoint_empty=baseline_checkpoint_empty,
        loaded_graphs_equal=loaded_graphs_equal,
        loaded_growth_states_equal=loaded_growth_states_equal,
        production_actions_unchanged=production_actions_unchanged,
        prediction_errors_unchanged=prediction_errors_unchanged,
        suggestion_sequence_unchanged=suggestion_sequence_unchanged,
        learned_graphs_equal=learned_graphs_equal,
        authority_violation_count=authority_violations,
        checkpoint_unchanged_during_shadow=checkpoint_unchanged,
        post_restart_reopening_passed=decision.reopen,
        post_restart_restoration_exact=restoration_exact,
        source_events_preserved=source_events_preserved,
        rollback_audit_round_trip_exact=rollback_audit_exact,
        sqlite_used_for_consolidation_acceptance=False,
        pass_gate=pass_gate,
    )
    return ConsolidationAcceptanceEvidence(
        result=result,
        pretraining=pretraining,
        baseline=baseline,
        checkpoint_tracked=tracked,
        active_state_path=active_state_path,
        restored_state_path=restored_state_path,
        candidate_id=application.candidate.candidate_id,
        rollback_id=restoration.rollback_id,
    )


def export_consolidation_acceptance(
    evidence: ConsolidationAcceptanceEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export result, live comparison timeline, and final checkpoint evidence."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "consolidation_acceptance_report.json"
    timeline_path = output_directory / "consolidation_shadow_timeline.csv"
    checkpoint_path = output_directory / "consolidation_checkpoint_report.json"
    _write_ascii_json(
        report_path,
        {
            "result": asdict(evidence.result),
            "candidate_id": evidence.candidate_id,
            "rollback_id": evidence.rollback_id,
        },
    )
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "baseline_action",
                "tracked_action",
                "baseline_suggestion",
                "tracked_suggestion",
                "baseline_prediction_error",
                "tracked_prediction_error",
            )
        )
        for baseline_record, tracked_record in zip(
            evidence.baseline.records,
            evidence.checkpoint_tracked.records,
            strict=True,
        ):
            writer.writerow(
                (
                    baseline_record.step_index,
                    baseline_record.actual_action.value,
                    tracked_record.actual_action.value,
                    _action_value(baseline_record.suggested_action),
                    _action_value(tracked_record.suggested_action),
                    baseline_record.prediction_error,
                    tracked_record.prediction_error,
                )
            )
    restored = NDNRABrainStore(evidence.restored_state_path).load()
    _write_ascii_json(
        checkpoint_path,
        restored.consolidation_checkpoint.snapshot(),
    )
    return report_path, timeline_path, checkpoint_path


def _build_live_checkpoint(
    graph: MultidimensionalExperienceGraph,
) -> tuple[
    ConsolidationEligibility,
    ConsolidationApplicationResult,
    NDNRAConsolidationCheckpoint,
]:
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
                source_code="consolidation_acceptance",
                episode_id="live_mastery",
                step_id=step_id,
            ),
            correlation_group_id=f"group:live_mastery:{step_id}",
            assembly_id=assembly_id,
            route_id=route_id,
            action_code=assembly.action_code,
            origin_need_code=assembly.origin_need_code,
            required_facts=assembly.required_facts,
            produced_facts=assembly.produced_facts,
            context_signature=ContextSignature.from_values(
                active_need_code=_CONSOLIDATION_LESSON.need_code,
                sensor_values=sensors,
                available_action_codes=(graph.assembly(item).action_code for item in assembly_ids),
            ),
            observed_effects=(
                EffectObservation(
                    effect_code=_CONSOLIDATION_LESSON.effect_code,
                    value=1.0,
                    confidence=1.0,
                ),
            ),
            transfer_attempted=True,
            transfer_succeeded=transfer_succeeded,
        )
    profile = graph.contextual_memory.mastery_profile(_CONSOLIDATION_LESSON)
    eligibility = ConsolidationEligibilityPolicy().evaluate(
        ledger=graph.contextual_memory,
        lesson=_CONSOLIDATION_LESSON,
        mastery_profile=profile,
        requested_stability_increment=0.20,
        requested_plasticity_reduction=0.20,
        available_assembly_ids=assembly_ids,
        available_route_ids=_ROUTE_IDS,
    )
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=assembly_ids,
        route_ids=_ROUTE_IDS,
    )
    application = state.apply(eligibility)
    checkpoint = NDNRAConsolidationCheckpoint(
        state=state.snapshot(),
        active_applications=(application,),
    )
    return eligibility, application, checkpoint


def _record_later_contradiction(
    graph: MultidimensionalExperienceGraph,
    application: ConsolidationApplicationResult,
    *,
    step_id: int,
) -> None:
    candidate = application.candidate
    assembly = graph.assembly(candidate.assembly_ids[0])
    graph.learn_contextual_experience(
        identity=EventIdentity(
            source_code="consolidation_acceptance",
            episode_id="later_contradiction",
            step_id=step_id,
        ),
        correlation_group_id="group:later_contradiction:0",
        assembly_id=assembly.assembly_id,
        route_id=candidate.route_ids[0],
        action_code=assembly.action_code,
        origin_need_code=assembly.origin_need_code,
        required_facts=assembly.required_facts,
        produced_facts=assembly.produced_facts,
        context_signature=ContextSignature.from_values(
            active_need_code=candidate.lesson_identity.need_code,
            sensor_values=(9.0, 9.5),
            available_action_codes=(assembly.action_code,),
        ),
        observed_effects=(
            EffectObservation(
                effect_code=candidate.lesson_identity.effect_code,
                value=-candidate.lesson_identity.desired_direction,
                confidence=1.0,
            ),
        ),
    )


def _action_value(action: PrimitiveAction | None) -> str:
    return "" if action is None else action.value


def _write_ascii_json(path: Path, payload: object) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)
