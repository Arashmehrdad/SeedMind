"""Cross-session NDNRA shadow-memory persistence acceptance experiment."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from statistics import fmean

import torch

from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.curiosity import CuriosityConfig
from seedmind.environment import DynamicNurseryScenarioFactory, NurseryRuntime
from seedmind.integration.ndnra_shadow import (
    NDNRAShadowAdapter,
    NDNRAShadowSession,
    NDNRAShadowSessionConfig,
    NDNRAShadowSessionResult,
)
from seedmind.perception import SymbolicInputSpec
from seedmind.research.ndnra.persistence import (
    BRAIN_SCHEMA_VERSION,
    BrainLoadStatus,
    NDNRABrainStore,
    NDNRAGrowthState,
)
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
class PersistentShadowResult:
    """Evidence that local NDNRA state survives a process-equivalent restart."""

    first_session_selection_count: int
    first_session_assembly_count: int
    first_session_effect_dimension_count: int
    saved_schema_version: int
    saved_byte_count: int
    temporary_file_remaining: bool
    load_status: str
    checksum_verified: bool
    graph_round_trip_exact: bool
    growth_state_round_trip_exact: bool
    loaded_step_zero_suggestion_available: bool
    fresh_step_zero_suggestion_available: bool
    loaded_step_zero_suggestion_valid: bool
    second_session_action_sequence_unchanged: bool
    second_session_prediction_errors_unchanged: bool
    loaded_evidence_count_after: int
    fresh_evidence_count_after: int
    cross_session_evidence_advantage: bool
    corruption_fallback_status: str
    corruption_fallback_fresh: bool
    incompatible_fallback_status: str
    incompatible_fallback_fresh: bool
    sqlite_used_for_persistence_or_recall: bool
    theory_readiness_before: int
    theory_readiness_after: int
    pass_gate: bool


@dataclass(frozen=True, slots=True)
class PersistentShadowEvidence:
    """Result plus timelines and persisted state paths for inspection."""

    result: PersistentShadowResult
    first_session: NDNRAShadowSessionResult
    loaded_second_session: NDNRAShadowSessionResult
    fresh_second_session: NDNRAShadowSessionResult
    state_path: Path
    corrupt_state_path: Path
    incompatible_state_path: Path


def run_persistent_shadow_experiment(
    output_directory: Path,
    *,
    first_seed: int = 7,
    second_seed: int = 11,
    play_budget: int = 6,
    ambition_relevance: float = 0.75,
) -> PersistentShadowEvidence:
    """Learn, save, restart, reload, and compare against a fresh shadow graph."""
    if play_budget <= 1:
        raise ValueError("play_budget must exceed one")
    output_directory.mkdir(parents=True, exist_ok=True)
    scenario_factory = DynamicNurseryScenarioFactory()
    curiosity = CuriosityConfig(
        play_budget=play_budget,
        experiment_actions=_EXPERIMENT_ACTIONS,
    )

    first_config = NDNRAShadowSessionConfig(
        seed=first_seed,
        curiosity=curiosity,
        ambition_relevance=ambition_relevance,
    )
    first_shadow = NDNRAShadowAdapter()
    first_session = NDNRAShadowSession(
        _build_trainer(first_seed, scenario_factory),
        scenario_factory,
        first_config,
        shadow=first_shadow,
    ).run()
    first_snapshot = first_shadow.graph.snapshot()
    growth_state = _derive_growth_state(first_session, first_shadow)

    state_path = output_directory / "ndnra_brain_state.json"
    store = NDNRABrainStore(state_path)
    save_result = store.save(first_shadow.graph, growth_state=growth_state)
    load_result = store.load()
    graph_round_trip = load_result.graph.snapshot() == first_snapshot
    growth_round_trip = load_result.growth_state == growth_state

    second_config = NDNRAShadowSessionConfig(
        seed=second_seed,
        curiosity=curiosity,
        ambition_relevance=ambition_relevance,
    )
    loaded_shadow = NDNRAShadowAdapter(graph=load_result.graph)
    fresh_shadow = NDNRAShadowAdapter()
    loaded_second = NDNRAShadowSession(
        _build_trainer(second_seed, scenario_factory),
        scenario_factory,
        second_config,
        shadow=loaded_shadow,
    ).run()
    fresh_second = NDNRAShadowSession(
        _build_trainer(second_seed, scenario_factory),
        scenario_factory,
        second_config,
        shadow=fresh_shadow,
    ).run()

    corrupt_path = output_directory / "ndnra_brain_state_corrupt.json"
    corrupt_path.write_text("not-json\n", encoding="ascii")
    corrupt_load = NDNRABrainStore(corrupt_path).load()

    incompatible_path = output_directory / "ndnra_brain_state_incompatible.json"
    incompatible_payload: object = json.loads(state_path.read_text(encoding="ascii"))
    if not isinstance(incompatible_payload, dict):
        raise RuntimeError("saved brain envelope is not an object")
    incompatible_payload["schema_version"] = BRAIN_SCHEMA_VERSION + 1
    incompatible_path.write_text(
        json.dumps(
            incompatible_payload,
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="ascii",
    )
    incompatible_load = NDNRABrainStore(incompatible_path).load()

    loaded_initial = loaded_second.suggestions[0]
    fresh_initial = fresh_second.suggestions[0]
    loaded_evidence = _total_assembly_evidence(loaded_shadow)
    fresh_evidence = _total_assembly_evidence(fresh_shadow)
    actions_unchanged = loaded_second.actual_actions == fresh_second.actual_actions
    loaded_errors = tuple(metric.mean_absolute_error for metric in loaded_second.metrics)
    fresh_errors = tuple(metric.mean_absolute_error for metric in fresh_second.metrics)
    errors_unchanged = loaded_errors == fresh_errors
    loaded_initial_valid = loaded_second.records[0].suggestion_was_valid
    evidence_advantage = loaded_evidence > fresh_evidence
    corruption_fresh = (
        corrupt_load.used_fallback
        and corrupt_load.graph.assembly_count == 0
        and corrupt_load.graph.specialist_count == 0
    )
    incompatible_fresh = (
        incompatible_load.used_fallback
        and incompatible_load.graph.assembly_count == 0
        and incompatible_load.graph.specialist_count == 0
    )
    pass_gate = bool(
        load_result.status is BrainLoadStatus.LOADED
        and load_result.checksum_verified
        and not load_result.used_fallback
        and graph_round_trip
        and growth_round_trip
        and not save_result.temporary_file_remaining
        and loaded_initial.suggested_action is not None
        and fresh_initial.suggested_action is None
        and loaded_initial_valid
        and actions_unchanged
        and errors_unchanged
        and evidence_advantage
        and corrupt_load.status is BrainLoadStatus.CORRUPT_FALLBACK
        and corruption_fresh
        and incompatible_load.status is BrainLoadStatus.INCOMPATIBLE_FALLBACK
        and incompatible_fresh
    )
    result = PersistentShadowResult(
        first_session_selection_count=len(first_session.records),
        first_session_assembly_count=first_session.learned_assembly_count,
        first_session_effect_dimension_count=first_session.effect_dimension_count,
        saved_schema_version=save_result.schema_version,
        saved_byte_count=save_result.byte_count,
        temporary_file_remaining=save_result.temporary_file_remaining,
        load_status=load_result.status.value,
        checksum_verified=load_result.checksum_verified,
        graph_round_trip_exact=graph_round_trip,
        growth_state_round_trip_exact=growth_round_trip,
        loaded_step_zero_suggestion_available=loaded_initial.suggested_action is not None,
        fresh_step_zero_suggestion_available=fresh_initial.suggested_action is not None,
        loaded_step_zero_suggestion_valid=loaded_initial_valid,
        second_session_action_sequence_unchanged=actions_unchanged,
        second_session_prediction_errors_unchanged=errors_unchanged,
        loaded_evidence_count_after=loaded_evidence,
        fresh_evidence_count_after=fresh_evidence,
        cross_session_evidence_advantage=evidence_advantage,
        corruption_fallback_status=corrupt_load.status.value,
        corruption_fallback_fresh=corruption_fresh,
        incompatible_fallback_status=incompatible_load.status.value,
        incompatible_fallback_fresh=incompatible_fresh,
        sqlite_used_for_persistence_or_recall=False,
        theory_readiness_before=70,
        theory_readiness_after=78,
        pass_gate=pass_gate,
    )
    return PersistentShadowEvidence(
        result=result,
        first_session=first_session,
        loaded_second_session=loaded_second,
        fresh_second_session=fresh_second,
        state_path=state_path,
        corrupt_state_path=corrupt_path,
        incompatible_state_path=incompatible_path,
    )


def export_persistent_shadow_evidence(
    evidence: PersistentShadowEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export report, second-session comparison, and loaded graph evidence."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "persistent_shadow_report.json"
    timeline_path = output_directory / "persistent_shadow_timeline.csv"
    graph_path = output_directory / "reloaded_shadow_graph.json"

    _write_ascii_json(report_path, asdict(evidence.result))
    _write_ascii_json(graph_path, evidence.loaded_second_session.graph_snapshot)
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "loaded_actual_action",
                "fresh_actual_action",
                "loaded_suggested_action",
                "fresh_suggested_action",
                "loaded_prediction_error",
                "fresh_prediction_error",
            )
        )
        for loaded_record, fresh_record in zip(
            evidence.loaded_second_session.records,
            evidence.fresh_second_session.records,
            strict=True,
        ):
            writer.writerow(
                (
                    loaded_record.step_index,
                    loaded_record.actual_action.value,
                    fresh_record.actual_action.value,
                    (
                        loaded_record.suggested_action.value
                        if loaded_record.suggested_action is not None
                        else ""
                    ),
                    (
                        fresh_record.suggested_action.value
                        if fresh_record.suggested_action is not None
                        else ""
                    ),
                    loaded_record.prediction_error,
                    fresh_record.prediction_error,
                )
            )
    return report_path, timeline_path, graph_path


def _derive_growth_state(
    session: NDNRAShadowSessionResult,
    shadow: NDNRAShadowAdapter,
) -> NDNRAGrowthState:
    pressure = fmean(record.prediction_error for record in session.records)
    eligibility = tuple(
        (
            assembly.assembly_id,
            min(1.0, assembly.evidence_count / len(session.records)),
        )
        for assembly in shadow.graph.assemblies
    )
    residuals = tuple(
        max(-1.0, min(1.0, record.controllable_change - record.external_change))
        for record in session.records
    )
    last_members = tuple(
        dict.fromkeys(
            f"assembly:shadow:{record.actual_action.value}" for record in session.records[-2:]
        )
    )
    recent = set(last_members)
    dormancy_levels = tuple(
        (
            assembly.assembly_id,
            0.0
            if assembly.assembly_id in recent
            else max(0.0, 1.0 - assembly.evidence_count / len(session.records)),
        )
        for assembly in shadow.graph.assemblies
    ) + tuple(
        (
            link.link_id,
            0.0
            if link.source_id in recent
            else max(0.0, 1.0 - link.usage_count / len(session.records)),
        )
        for link in shadow.graph.links
    )
    return NDNRAGrowthState(
        pressure=pressure,
        eligibility=eligibility,
        residuals=residuals,
        attempt_count=len(session.records),
        last_active_members=last_members,
        dormancy_levels=dormancy_levels,
    )


def _total_assembly_evidence(shadow: NDNRAShadowAdapter) -> int:
    return sum(assembly.evidence_count for assembly in shadow.graph.assemblies)


def _build_trainer(
    seed: int,
    scenario_factory: DynamicNurseryScenarioFactory,
) -> OnlinePredictiveTrainer:
    scenario = scenario_factory.create(seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-persistent-interface",
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
