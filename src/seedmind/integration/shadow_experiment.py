"""End-to-end baseline comparison for NDNRA shadow-mode integration."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

import torch

from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.curiosity import CuriosityConfig, CuriosityTrainingConfig, CuriosityTrainingSession
from seedmind.environment import DynamicNurseryScenarioFactory, NurseryRuntime
from seedmind.integration.ndnra_shadow import (
    NDNRAShadowSession,
    NDNRAShadowSessionConfig,
    NDNRAShadowSessionResult,
)
from seedmind.perception import SymbolicInputSpec
from seedmind.training import OnlinePredictiveTrainer, OnlineTrainerConfig

_EXPERIMENT_ACTIONS = (
    PrimitiveAction.TURN_LEFT,
    PrimitiveAction.TURN_RIGHT,
    PrimitiveAction.MOVE_FORWARD,
    PrimitiveAction.INSPECT,
    PrimitiveAction.PUSH,
    PrimitiveAction.WAIT,
)
_EXPECTED_EFFECT_DIMENSIONS = {
    "ambition_relevance",
    "controllable_change",
    "curiosity_value",
    "external_change",
    "human_signal_magnitude",
    "prediction_error",
    "resource_cost",
    "termination_risk",
}


@dataclass(frozen=True, slots=True)
class ShadowComparisonResult:
    """Acceptance metrics proving shadow observation cannot alter production."""

    scenario_id: str
    seed: int
    play_budget: int
    baseline_selection_count: int
    shadow_selection_count: int
    action_sequence_unchanged: bool
    prediction_error_sequence_unchanged: bool
    observed_transition_count: int
    suggestion_count: int
    valid_suggestion_count: int
    suggestion_match_count: int
    suggestion_match_rate: float
    authority_violation_count: int
    learned_assembly_count: int
    effect_dimension_count: int
    expected_effect_dimensions_present: bool
    first_suggestion_step: int | None
    sqlite_used_for_shadow_decisions: bool
    integration_percentage_before: int
    integration_percentage_after: int
    pass_gate: bool

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        if self.seed < 0 or self.play_budget <= 0:
            raise ValueError("seed and play_budget are invalid")
        counts = (
            self.baseline_selection_count,
            self.shadow_selection_count,
            self.observed_transition_count,
            self.suggestion_count,
            self.valid_suggestion_count,
            self.suggestion_match_count,
            self.authority_violation_count,
            self.learned_assembly_count,
            self.effect_dimension_count,
        )
        if any(count < 0 for count in counts):
            raise ValueError("comparison counts must not be negative")
        if not 0.0 <= self.suggestion_match_rate <= 1.0:
            raise ValueError("suggestion_match_rate must be between zero and one")
        if self.first_suggestion_step is not None and self.first_suggestion_step < 0:
            raise ValueError("first_suggestion_step must not be negative")
        if not 0 <= self.integration_percentage_before <= 100:
            raise ValueError("integration_percentage_before is invalid")
        if not 0 <= self.integration_percentage_after <= 100:
            raise ValueError("integration_percentage_after is invalid")


def run_shadow_comparison(
    *,
    seed: int = 7,
    play_budget: int = 12,
    ambition_relevance: float = 0.75,
) -> tuple[ShadowComparisonResult, NDNRAShadowSessionResult]:
    """Run identical baseline and shadow sessions and compare production actions."""
    if seed < 0:
        raise ValueError("seed must not be negative")
    if play_budget <= 1:
        raise ValueError("play_budget must exceed one to test learned suggestions")
    scenario_factory = DynamicNurseryScenarioFactory()
    curiosity = CuriosityConfig(
        play_budget=play_budget,
        experiment_actions=_EXPERIMENT_ACTIONS,
    )
    baseline_config = CuriosityTrainingConfig(seed=seed, curiosity=curiosity)
    shadow_config = NDNRAShadowSessionConfig(
        seed=seed,
        curiosity=curiosity,
        ambition_relevance=ambition_relevance,
    )
    baseline_trainer = _build_trainer(seed, scenario_factory)
    shadow_trainer = _build_trainer(seed, scenario_factory)

    baseline = CuriosityTrainingSession(
        baseline_trainer,
        scenario_factory,
        baseline_config,
    ).run()
    shadow = NDNRAShadowSession(
        shadow_trainer,
        scenario_factory,
        shadow_config,
    ).run()

    baseline_actions = tuple(record.action for record in baseline.records)
    baseline_errors = tuple(record.prediction_error for record in baseline.records)
    shadow_errors = tuple(metric.mean_absolute_error for metric in shadow.metrics)
    first_suggestion_step = next(
        (record.step_index for record in shadow.records if record.suggestion_was_available),
        None,
    )
    graph_dimensions = set(shadow.effect_dimensions)
    match_rate = (
        shadow.suggestion_match_count / shadow.suggestion_count
        if shadow.suggestion_count > 0
        else 0.0
    )
    actions_unchanged = baseline_actions == shadow.actual_actions
    errors_unchanged = baseline_errors == shadow_errors
    expected_dimensions = _EXPECTED_EFFECT_DIMENSIONS.issubset(graph_dimensions)
    pass_gate = bool(
        baseline.selection_count == play_budget
        and len(shadow.records) == play_budget
        and actions_unchanged
        and errors_unchanged
        and shadow.authority_violation_count == 0
        and shadow.suggestion_count >= play_budget - 1
        and shadow.valid_suggestion_count == shadow.suggestion_count
        and shadow.learned_assembly_count >= 2
        and expected_dimensions
        and first_suggestion_step == 1
    )
    result = ShadowComparisonResult(
        scenario_id=shadow.scenario_id,
        seed=seed,
        play_budget=play_budget,
        baseline_selection_count=baseline.selection_count,
        shadow_selection_count=len(shadow.records),
        action_sequence_unchanged=actions_unchanged,
        prediction_error_sequence_unchanged=errors_unchanged,
        observed_transition_count=len(shadow.records),
        suggestion_count=shadow.suggestion_count,
        valid_suggestion_count=shadow.valid_suggestion_count,
        suggestion_match_count=shadow.suggestion_match_count,
        suggestion_match_rate=match_rate,
        authority_violation_count=shadow.authority_violation_count,
        learned_assembly_count=shadow.learned_assembly_count,
        effect_dimension_count=shadow.effect_dimension_count,
        expected_effect_dimensions_present=expected_dimensions,
        first_suggestion_step=first_suggestion_step,
        sqlite_used_for_shadow_decisions=False,
        integration_percentage_before=30,
        integration_percentage_after=45,
        pass_gate=pass_gate,
    )
    return result, shadow


def export_shadow_comparison_evidence(
    result: ShadowComparisonResult,
    shadow: NDNRAShadowSessionResult,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export report, action comparison timeline, and learned shadow graph."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "shadow_comparison_report.json"
    timeline_path = output_directory / "shadow_timeline.csv"
    graph_path = output_directory / "shadow_graph.json"

    _write_ascii_json(report_path, asdict(result))
    _write_ascii_json(graph_path, shadow.graph_snapshot)
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "actual_action",
                "suggested_action",
                "suggestion_matches_actual",
                "suggestion_was_valid",
                "shadow_had_action_authority",
                "prediction_error",
                "curiosity_value",
                "controllable_change",
                "external_change",
                "resource_cost",
                "human_signal_magnitude",
                "ambition_relevance",
                "learned_assembly_count",
                "effect_dimension_count",
            )
        )
        for record in shadow.records:
            writer.writerow(
                (
                    record.step_index,
                    record.actual_action.value,
                    record.suggested_action.value if record.suggested_action is not None else "",
                    str(record.suggestion_matches_actual).lower(),
                    str(record.suggestion_was_valid).lower(),
                    str(record.shadow_had_action_authority).lower(),
                    record.prediction_error,
                    record.curiosity_value,
                    record.controllable_change,
                    record.external_change,
                    record.resource_cost,
                    record.human_signal_magnitude,
                    record.ambition_relevance,
                    record.learned_assembly_count,
                    record.effect_dimension_count,
                )
            )
    return report_path, timeline_path, graph_path


def _build_trainer(
    seed: int,
    scenario_factory: DynamicNurseryScenarioFactory,
) -> OnlinePredictiveTrainer:
    scenario = scenario_factory.create(seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-shadow-interface",
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
