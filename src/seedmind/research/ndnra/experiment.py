"""Training, evaluation, and evidence for the NDNRA heat-fan prototype."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from seedmind.research.ndnra.heat_world import HeatFanWorld
from seedmind.research.ndnra.models import (
    GrowthPressure,
    HeatAction,
    HeatContext,
    ModulationSummary,
)
from seedmind.research.ndnra.network import LocalNeuralGraph

_EXPECTED_CHAIN = (
    HeatAction.STAND,
    HeatAction.WALK,
    HeatAction.REACH,
    HeatAction.ACTIVATE,
    HeatAction.WAIT,
)


@dataclass(frozen=True, slots=True)
class RecallStepRecord:
    """One selected action and its need and recall costs."""

    step_index: int
    source_context: HeatContext
    action: HeatAction
    target_context: HeatContext
    valid: bool
    need_before: float
    need_after: float
    recall_depth: int
    propagation_cycles: int
    neuron_evaluations: int
    selected_score: float

    @property
    def computational_cost(self) -> int:
        return self.propagation_cycles + self.neuron_evaluations


@dataclass(frozen=True, slots=True)
class RecallEpisodeResult:
    """Outcome of one need-driven action reconstruction attempt."""

    success: bool
    maximum_depth: int
    records: tuple[RecallStepRecord, ...]
    failed_context: HeatContext | None

    @property
    def actions(self) -> tuple[HeatAction, ...]:
        return tuple(record.action for record in self.records)

    @property
    def total_computational_cost(self) -> int:
        return sum(record.computational_cost for record in self.records)

    @property
    def maximum_depth_used(self) -> int:
        return max((record.recall_depth for record in self.records), default=0)


@dataclass(frozen=True, slots=True)
class TeacherTrainingResult:
    """Summary of delayed local credit across demonstrations."""

    demonstration_count: int
    modulation_summaries: tuple[ModulationSummary, ...]
    earliest_action_weight: float
    latest_action_weight: float
    irrelevant_action_weight: float


@dataclass(frozen=True, slots=True)
class NDNRAExperimentResult:
    """All falsifiable metrics for the first NDNRA prototype."""

    training: TeacherTrainingResult
    baseline_recall: RecallEpisodeResult
    shallow_recall: RecallEpisodeResult
    deep_recall: RecallEpisodeResult
    neuron_count_before_dormancy: int
    neuron_count_after_dormancy: int
    synapse_count_before_dormancy: int
    synapse_count_after_dormancy: int
    growth_pressure: float
    sqlite_used_for_recall: bool
    pass_gate: bool


def train_teacher_demonstrations(
    graph: LocalNeuralGraph,
    *,
    demonstration_count: int,
) -> TeacherTrainingResult:
    """Teach a cooling chain with no weight update until cooling is observed."""
    if demonstration_count <= 0:
        raise ValueError("demonstration_count must be positive")
    world = HeatFanWorld()
    summaries: list[ModulationSummary] = []

    for _ in range(demonstration_count):
        world.reset()
        graph.reset_episode_traces()
        while not world.state.resolved:
            pulse = world.need_pulse(effort_budget=graph.config.maximum_recall_depth)
            source_context = world.state.context
            action = world.teacher_action()
            transition = world.step(action)
            graph.observe_transition(
                need_pulse=pulse,
                source_context=source_context,
                action=action,
                target_context=transition.state.context,
            )
            if transition.need_reduction > 0.0:
                graph.mark_cooling_outcome()
                summaries.append(graph.broadcast_modulatory_signal(transition.need_reduction))

    return TeacherTrainingResult(
        demonstration_count=demonstration_count,
        modulation_summaries=tuple(summaries),
        earliest_action_weight=graph.synapse(
            "context:sitting_away",
            "action:stand",
        ).weight,
        latest_action_weight=graph.synapse(
            "context:fan_on",
            "action:wait",
        ).weight,
        irrelevant_action_weight=graph.synapse(
            "context:sitting_away",
            "action:activate",
        ).weight,
    )


def evaluate_recall(
    graph: LocalNeuralGraph,
    *,
    maximum_depth: int,
    maximum_steps: int = 8,
) -> RecallEpisodeResult:
    """Resolve heat using only local graph recruitment and current world context."""
    if maximum_steps <= 0:
        raise ValueError("maximum_steps must be positive")
    world = HeatFanWorld()
    records: list[RecallStepRecord] = []

    for step_index in range(1, maximum_steps + 1):
        if world.state.resolved:
            break
        source_context = world.state.context
        need_before = world.state.need_intensity
        recall = graph.recall_action(
            need_pulse=world.need_pulse(effort_budget=maximum_depth),
            context=source_context,
            maximum_depth=maximum_depth,
        )
        if recall.selected_action is None:
            return RecallEpisodeResult(
                success=False,
                maximum_depth=maximum_depth,
                records=tuple(records),
                failed_context=source_context,
            )
        transition = world.step(recall.selected_action)
        records.append(
            RecallStepRecord(
                step_index=step_index,
                source_context=source_context,
                action=recall.selected_action,
                target_context=transition.state.context,
                valid=transition.valid,
                need_before=need_before,
                need_after=transition.state.need_intensity,
                recall_depth=recall.depth_used,
                propagation_cycles=recall.propagation_cycles,
                neuron_evaluations=recall.neuron_evaluations,
                selected_score=recall.selected_score,
            )
        )
        if not transition.valid:
            return RecallEpisodeResult(
                success=False,
                maximum_depth=maximum_depth,
                records=tuple(records),
                failed_context=source_context,
            )

    return RecallEpisodeResult(
        success=world.state.resolved,
        maximum_depth=maximum_depth,
        records=tuple(records),
        failed_context=None if world.state.resolved else world.state.context,
    )


def run_ndnra_heat_fan_experiment(
    *,
    demonstration_count: int = 6,
    dormancy_level: float = 0.80,
) -> tuple[NDNRAExperimentResult, LocalNeuralGraph]:
    """Compare an untrained graph with dormant shallow and deep recall."""
    baseline_graph = LocalNeuralGraph()
    baseline_recall = evaluate_recall(
        baseline_graph,
        maximum_depth=baseline_graph.config.maximum_recall_depth,
    )

    graph = LocalNeuralGraph()
    training = train_teacher_demonstrations(
        graph,
        demonstration_count=demonstration_count,
    )
    neuron_count_before = graph.neuron_count
    synapse_count_before = graph.synapse_count
    graph.enter_dormancy(dormancy_level)
    neuron_count_after = graph.neuron_count
    synapse_count_after = graph.synapse_count

    shallow_recall = evaluate_recall(graph, maximum_depth=1)
    deep_recall = evaluate_recall(
        graph,
        maximum_depth=graph.config.maximum_recall_depth,
    )

    growth = GrowthPressure()
    for _ in range(4):
        growth.update(
            unresolved_error=1.0,
            curiosity=0.9,
            ambition_relevance=1.0,
            capacity_saturation=1.0,
        )

    local_credit_passed = (
        training.earliest_action_weight > 0.0
        and training.latest_action_weight > training.earliest_action_weight
        and training.irrelevant_action_weight == 0.0
    )
    dormant_memory_preserved = (
        neuron_count_before == neuron_count_after and synapse_count_before == synapse_count_after
    )
    exact_chain_recalled = deep_recall.actions == _EXPECTED_CHAIN
    need_persisted = _need_persisted_until_cooling(deep_recall)
    effort_cost_increased = deep_recall.records and deep_recall.records[
        0
    ].computational_cost > _failed_recall_cost(graph, maximum_depth=1)
    pass_gate = bool(
        local_credit_passed
        and not baseline_recall.success
        and not shallow_recall.success
        and deep_recall.success
        and exact_chain_recalled
        and need_persisted
        and effort_cost_increased
        and dormant_memory_preserved
        and growth.value >= 0.80
    )

    return (
        NDNRAExperimentResult(
            training=training,
            baseline_recall=baseline_recall,
            shallow_recall=shallow_recall,
            deep_recall=deep_recall,
            neuron_count_before_dormancy=neuron_count_before,
            neuron_count_after_dormancy=neuron_count_after,
            synapse_count_before_dormancy=synapse_count_before,
            synapse_count_after_dormancy=synapse_count_after,
            growth_pressure=growth.value,
            sqlite_used_for_recall=False,
            pass_gate=pass_gate,
        ),
        graph,
    )


def export_ndnra_evidence(
    result: NDNRAExperimentResult,
    graph: LocalNeuralGraph,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Write the report, recall timeline, and complete local graph state."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "ndnra_report.json"
    timeline_path = output_directory / "recall_timeline.csv"
    graph_path = output_directory / "local_graph_state.json"

    report_payload = {
        "training": {
            "demonstration_count": result.training.demonstration_count,
            "earliest_action_weight": result.training.earliest_action_weight,
            "latest_action_weight": result.training.latest_action_weight,
            "irrelevant_action_weight": result.training.irrelevant_action_weight,
            "modulation_summaries": [
                asdict(summary) for summary in result.training.modulation_summaries
            ],
        },
        "baseline_success": result.baseline_recall.success,
        "shallow_success": result.shallow_recall.success,
        "deep_success": result.deep_recall.success,
        "deep_actions": [action.value for action in result.deep_recall.actions],
        "deep_total_computational_cost": result.deep_recall.total_computational_cost,
        "deep_maximum_depth_used": result.deep_recall.maximum_depth_used,
        "neuron_count_before_dormancy": result.neuron_count_before_dormancy,
        "neuron_count_after_dormancy": result.neuron_count_after_dormancy,
        "synapse_count_before_dormancy": result.synapse_count_before_dormancy,
        "synapse_count_after_dormancy": result.synapse_count_after_dormancy,
        "growth_pressure": result.growth_pressure,
        "sqlite_used_for_recall": result.sqlite_used_for_recall,
        "pass_gate": result.pass_gate,
    }
    _write_ascii_json(report_path, report_payload)
    _write_ascii_json(graph_path, graph.snapshot())

    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "source_context",
                "action",
                "target_context",
                "valid",
                "need_before",
                "need_after",
                "recall_depth",
                "propagation_cycles",
                "neuron_evaluations",
                "computational_cost",
                "selected_score",
            )
        )
        for record in result.deep_recall.records:
            writer.writerow(
                (
                    record.step_index,
                    record.source_context.value,
                    record.action.value,
                    record.target_context.value,
                    str(record.valid).lower(),
                    record.need_before,
                    record.need_after,
                    record.recall_depth,
                    record.propagation_cycles,
                    record.neuron_evaluations,
                    record.computational_cost,
                    record.selected_score,
                )
            )
    return report_path, timeline_path, graph_path


def _need_persisted_until_cooling(result: RecallEpisodeResult) -> bool:
    if not result.success or not result.records:
        return False
    prior_records = result.records[:-1]
    final_record = result.records[-1]
    return all(record.need_after == 1.0 for record in prior_records) and (
        final_record.need_before == 1.0 and final_record.need_after == 0.0
    )


def _failed_recall_cost(graph: LocalNeuralGraph, *, maximum_depth: int) -> int:
    world = HeatFanWorld()
    result = graph.recall_action(
        need_pulse=world.need_pulse(effort_budget=maximum_depth),
        context=world.state.context,
        maximum_depth=maximum_depth,
    )
    return result.computational_cost


def _write_ascii_json(path: Path, payload: object) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)
