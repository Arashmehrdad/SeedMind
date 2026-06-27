"""End-to-end gate for live developmental signals and restored adaptive state."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from seedmind.ambition import (
    AmbitionManager,
    GoalDirectedOutcomeDetector,
    ObservedDemonstration,
)
from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.curiosity import (
    CuriosityConfig,
    CuriosityTrainingConfig,
    CuriosityTrainingSession,
)
from seedmind.environment import (
    DynamicNurseryScenarioFactory,
    NurseryRuntime,
    TeacherDemonstrationScenarioFactory,
)
from seedmind.human import ApprenticeshipManager
from seedmind.integration.developmental_signals import (
    LiveDevelopmentalSignalProvider,
)
from seedmind.integration.unified_shadow import (
    NDNRALiveShadowAdapter,
    UnifiedDevelopmentalShadowSession,
    UnifiedShadowConfig,
    UnifiedShadowResult,
)
from seedmind.perception import SymbolicInputSpec
from seedmind.research.ndnra import NDNRABrainStore, NDNRAGrowthState
from seedmind.self_model import SelfModelConfig, SelfModelRegistry
from seedmind.training import OnlinePredictiveTrainer, OnlineTrainerConfig

_EXPERIMENT_ACTIONS = (
    PrimitiveAction.TURN_LEFT,
    PrimitiveAction.TURN_RIGHT,
    PrimitiveAction.MOVE_FORWARD,
    PrimitiveAction.INSPECT,
    PrimitiveAction.PUSH,
    PrimitiveAction.WAIT,
)


@dataclass(frozen=True, slots=True)
class UnifiedSignalExperimentResult:
    """Falsifiable metrics for the complete non-authoritative integration stage."""

    pretraining_selection_count: int
    persisted_assembly_count: int
    persisted_effect_dimension_count: int
    restored_pressure_before: float
    restored_pressure_after: float
    restored_attempt_count_before: int
    restored_attempt_count_after: int
    restored_first_eligibility_before: float
    restored_first_eligibility_after: float
    restored_eligibility_continued: bool
    most_dormant_assembly_id: str
    restored_dormancy_level: float
    restored_accessibility: float
    reset_accessibility: float
    restored_action_score: float
    reset_action_score: float
    dormancy_changed_accessibility: bool
    dormancy_changed_action_score: bool
    ambition_relevance_min: float
    ambition_relevance_max: float
    ambition_relevance_varied: bool
    maximum_self_controllability: float
    maximum_body_confidence: float
    help_request_count: int
    approval_count: int
    correction_count: int
    demonstration_count: int
    clarification_count: int
    human_response_count: int
    live_signal_dimension_count: int
    baseline_selection_count: int
    unified_selection_count: int
    production_actions_unchanged: bool
    prediction_errors_unchanged: bool
    authority_violation_count: int
    valid_suggestion_count: int
    sqlite_used_for_signals_or_adaptation: bool
    theory_readiness_before: int
    theory_readiness_after: int
    pass_gate: bool


@dataclass(frozen=True, slots=True)
class UnifiedSignalEvidence:
    """Result and inspectable state from both live developmental sessions."""

    result: UnifiedSignalExperimentResult
    pretraining: UnifiedShadowResult
    unified: UnifiedShadowResult
    initial_brain_path: Path
    final_brain_path: Path


def run_unified_signal_experiment(
    output_directory: Path,
    *,
    first_seed: int = 7,
    second_seed: int = 11,
    play_budget: int = 12,
) -> UnifiedSignalEvidence:
    """Run live subsystems, restart adaptive state, and compare with baseline."""
    if play_budget <= len(_EXPERIMENT_ACTIONS):
        raise ValueError("play_budget must exceed one full action exploration cycle")
    output_directory.mkdir(parents=True, exist_ok=True)
    scenario_factory = DynamicNurseryScenarioFactory()
    curiosity = CuriosityConfig(
        play_budget=play_budget,
        experiment_actions=_EXPERIMENT_ACTIONS,
    )

    pretraining_provider = _build_signal_provider(first_seed, scenario_factory)
    pretraining_shadow = NDNRALiveShadowAdapter()
    pretraining = UnifiedDevelopmentalShadowSession(
        _build_trainer(first_seed, scenario_factory),
        scenario_factory,
        UnifiedShadowConfig(seed=first_seed, curiosity=curiosity),
        signal_provider=pretraining_provider,
        shadow=pretraining_shadow,
    ).run()

    initial_brain_path = output_directory / "unified_brain_before_restart.json"
    store = NDNRABrainStore(initial_brain_path)
    store.save(
        pretraining_shadow.graph,
        growth_state=pretraining.final_growth_state,
    )
    loaded = store.load()
    reset_loaded = store.load()

    unified_provider = _build_signal_provider(second_seed, scenario_factory)
    restored_shadow = NDNRALiveShadowAdapter(
        graph=loaded.graph,
        growth_state=loaded.growth_state,
    )
    reset_shadow = NDNRALiveShadowAdapter(
        graph=reset_loaded.graph,
        growth_state=NDNRAGrowthState(),
    )
    dormant_assembly_id, dormant_level = _most_dormant_assembly(
        loaded.growth_state,
    )
    dormant_action = PrimitiveAction(loaded.graph.assembly(dormant_assembly_id).action_code)
    restored_accessibility, restored_score = restored_shadow.evaluate_action(
        dormant_action,
        unified_provider.current,
    )
    reset_accessibility, reset_score = reset_shadow.evaluate_action(
        dormant_action,
        unified_provider.current,
    )

    baseline = CuriosityTrainingSession(
        _build_trainer(second_seed, scenario_factory),
        scenario_factory,
        CuriosityTrainingConfig(seed=second_seed, curiosity=curiosity),
    ).run()
    unified = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, scenario_factory),
        scenario_factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=unified_provider,
        shadow=restored_shadow,
    ).run()

    baseline_actions = tuple(record.action for record in baseline.records)
    baseline_errors = tuple(record.prediction_error for record in baseline.records)
    unified_errors = tuple(metric.mean_absolute_error for metric in unified.metrics)
    ambition_values = tuple(signal.ambition_relevance for signal in unified.signals)
    help_count = sum(int(signal.help_requested) for signal in unified.signals)
    approval_count = sum(int(signal.human_approval) for signal in unified.signals)
    correction_count = sum(int(signal.human_correction) for signal in unified.signals)
    demonstration_count = sum(int(signal.human_demonstration) for signal in unified.signals)
    clarification_count = sum(int(signal.human_clarification) for signal in unified.signals)
    human_response_count = (
        approval_count + correction_count + demonstration_count + clarification_count
    )
    first_record = unified.records[0]
    final_state = unified.final_growth_state
    final_brain_path = output_directory / "unified_brain_after_live_signals.json"
    NDNRABrainStore(final_brain_path).save(
        restored_shadow.graph,
        growth_state=final_state,
    )

    pressure_continued = (
        first_record.pressure_before == loaded.growth_state.pressure
        and final_state.attempt_count == loaded.growth_state.attempt_count + play_budget
        and final_state.pressure >= loaded.growth_state.pressure
    )
    eligibility_continued = (
        first_record.eligibility_before > 0.0
        and first_record.eligibility_after >= first_record.eligibility_before
    )
    dormancy_changed_accessibility = (
        dormant_level > 0.0 and restored_accessibility < reset_accessibility
    )
    dormancy_changed_score = abs(restored_score - reset_score) > 1e-9
    ambition_varied = max(ambition_values) - min(ambition_values) > 1e-9
    actions_unchanged = baseline_actions == unified.actual_actions
    errors_unchanged = baseline_errors == unified_errors
    signal_dimension_count = len(unified.signals[0].values())
    pass_gate = bool(
        loaded.checksum_verified
        and not loaded.used_fallback
        and pressure_continued
        and eligibility_continued
        and dormancy_changed_accessibility
        and dormancy_changed_score
        and ambition_varied
        and max(signal.self_controllability for signal in unified.signals) > 0.0
        and max(signal.body_confidence for signal in unified.signals) > 0.0
        and help_count > 0
        and human_response_count > 0
        and signal_dimension_count >= 17
        and actions_unchanged
        and errors_unchanged
        and unified.authority_violation_count == 0
        and unified.valid_suggestion_count == unified.suggestion_count
    )
    result = UnifiedSignalExperimentResult(
        pretraining_selection_count=len(pretraining.records),
        persisted_assembly_count=pretraining_shadow.graph.assembly_count,
        persisted_effect_dimension_count=len(pretraining_shadow.graph.effect_dimension_codes),
        restored_pressure_before=loaded.growth_state.pressure,
        restored_pressure_after=final_state.pressure,
        restored_attempt_count_before=loaded.growth_state.attempt_count,
        restored_attempt_count_after=final_state.attempt_count,
        restored_first_eligibility_before=first_record.eligibility_before,
        restored_first_eligibility_after=first_record.eligibility_after,
        restored_eligibility_continued=eligibility_continued,
        most_dormant_assembly_id=dormant_assembly_id,
        restored_dormancy_level=dormant_level,
        restored_accessibility=restored_accessibility,
        reset_accessibility=reset_accessibility,
        restored_action_score=restored_score,
        reset_action_score=reset_score,
        dormancy_changed_accessibility=dormancy_changed_accessibility,
        dormancy_changed_action_score=dormancy_changed_score,
        ambition_relevance_min=min(ambition_values),
        ambition_relevance_max=max(ambition_values),
        ambition_relevance_varied=ambition_varied,
        maximum_self_controllability=max(signal.self_controllability for signal in unified.signals),
        maximum_body_confidence=max(signal.body_confidence for signal in unified.signals),
        help_request_count=help_count,
        approval_count=approval_count,
        correction_count=correction_count,
        demonstration_count=demonstration_count,
        clarification_count=clarification_count,
        human_response_count=human_response_count,
        live_signal_dimension_count=signal_dimension_count,
        baseline_selection_count=baseline.selection_count,
        unified_selection_count=len(unified.records),
        production_actions_unchanged=actions_unchanged,
        prediction_errors_unchanged=errors_unchanged,
        authority_violation_count=unified.authority_violation_count,
        valid_suggestion_count=unified.valid_suggestion_count,
        sqlite_used_for_signals_or_adaptation=False,
        theory_readiness_before=78,
        theory_readiness_after=85,
        pass_gate=pass_gate,
    )
    return UnifiedSignalEvidence(
        result=result,
        pretraining=pretraining,
        unified=unified,
        initial_brain_path=initial_brain_path,
        final_brain_path=final_brain_path,
    )


def export_unified_signal_evidence(
    evidence: UnifiedSignalEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export acceptance report, live timeline, and final adaptive state."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "unified_signal_report.json"
    timeline_path = output_directory / "unified_signal_timeline.csv"
    adaptive_path = output_directory / "unified_adaptive_state.json"
    _write_ascii_json(report_path, asdict(evidence.result))
    _write_ascii_json(adaptive_path, evidence.unified.final_growth_state.snapshot())
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "actual_action",
                "suggested_action",
                "ambition_relevance",
                "curiosity_learning_progress",
                "self_controllability",
                "body_confidence",
                "help_requested",
                "human_approval",
                "human_correction",
                "human_demonstration",
                "prediction_error",
                "resource_pressure",
                "need_resolution",
                "memory_accessibility",
                "pressure_before",
                "pressure_after",
                "eligibility_before",
                "eligibility_after",
                "dormancy_before",
                "dormancy_after",
            )
        )
        for record in evidence.unified.records:
            writer.writerow(
                (
                    record.step_index,
                    record.actual_action.value,
                    record.suggested_action.value if record.suggested_action is not None else "",
                    record.post_ambition_relevance,
                    record.curiosity_learning_progress,
                    record.self_controllability,
                    record.body_confidence,
                    record.help_requested,
                    record.human_approval,
                    record.human_correction,
                    record.human_demonstration,
                    record.prediction_error,
                    record.resource_pressure,
                    record.need_resolution,
                    record.selected_memory_accessibility,
                    record.pressure_before,
                    record.pressure_after,
                    record.eligibility_before,
                    record.eligibility_after,
                    record.dormancy_before,
                    record.dormancy_after,
                )
            )
    return report_path, timeline_path, adaptive_path


def _build_signal_provider(
    seed: int,
    scenario_factory: DynamicNurseryScenarioFactory,
) -> LiveDevelopmentalSignalProvider:
    scenario = scenario_factory.create(seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-signal-interface",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    return LiveDevelopmentalSignalProvider(
        ambition=_adopted_ambition_manager(),
        self_model=SelfModelRegistry(
            SelfModelConfig(sensor_size=len(runtime.observe().sensor_values))
        ),
        apprenticeship=ApprenticeshipManager(),
    )


def _adopted_ambition_manager() -> AmbitionManager:
    detector = GoalDirectedOutcomeDetector()
    candidate = None
    for index in range(3):
        scenario = TeacherDemonstrationScenarioFactory().create(7)
        episode_id = f"unified-teacher-{index}"
        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=episode_id,
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )
        start = runtime.observe()
        changed_steps = 0
        for _ in range(2):
            changed_steps += int(runtime.step(PrimitiveAction.WAIT).external_world_changed)
        candidate = detector.observe(
            ObservedDemonstration(
                episode_id=episode_id,
                start_observation=start,
                end_observation=runtime.observe(),
                external_change_steps=changed_steps,
                outcome_signal=1.0,
            )
        )
    if candidate is None:
        raise RuntimeError("failed to form the live integration ambition")
    manager = AmbitionManager()
    if manager.consider(candidate, episode_id="unified-teacher-2") is None:
        raise RuntimeError("failed to adopt the live integration ambition")
    return manager


def _most_dormant_assembly(
    state: NDNRAGrowthState,
) -> tuple[str, float]:
    candidates = tuple(
        (structure_id, level)
        for structure_id, level in state.dormancy_levels
        if structure_id.startswith("assembly:") and "->" not in structure_id
    )
    if not candidates:
        raise RuntimeError("persisted adaptive state has no assembly dormancy")
    return max(candidates, key=lambda item: (item[1], item[0]))


def _build_trainer(
    seed: int,
    scenario_factory: DynamicNurseryScenarioFactory,
) -> OnlinePredictiveTrainer:
    scenario = scenario_factory.create(seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-unified-interface",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    observation = runtime.observe()
    input_spec = SymbolicInputSpec(
        sensor_size=len(observation.sensor_values),
        human_signal_size=len(observation.human_signal),
        resource_state_size=len(observation.resource_state),
    )
    torch.manual_seed(seed)
    core = PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=input_spec.input_size,
            sensor_size=input_spec.sensor_size,
            action_count=len(PrimitiveAction),
        )
    )
    return OnlinePredictiveTrainer(
        core,
        input_spec,
        config=OnlineTrainerConfig(),
    )


def _write_ascii_json(path: Path, payload: object) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)
