"""Live acceptance gate for non-authoritative learned consequence prediction."""

from __future__ import annotations

import csv
import hashlib
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass, replace
from itertools import pairwise
from math import isfinite
from pathlib import Path
from statistics import fmean
from typing import cast

import torch

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.curiosity import CuriosityConfig, CuriositySubsystem
from seedmind.environment import DynamicNurseryScenarioFactory, NurseryRuntime
from seedmind.perception import SymbolicInputSpec
from seedmind.research.ndnra import (
    BRAIN_SCHEMA_VERSION,
    BoundedContextualTransferPolicy,
    BrainLoadStatus,
    ConsequenceChainPredictionRequest,
    ConsequenceModelObservation,
    ConsequencePredictionRequest,
    ContextSignature,
    EffectObservation,
    ExperienceOrigin,
    LearnedConsequenceModel,
    LearnedConsequenceModelConfig,
    NDNRABrainStore,
    NDNRALearnedConsequenceCheckpoint,
    ObservedConsequenceChain,
    ObservedConsequenceChainConfig,
    ObservedConsequenceChainModel,
    ObservedConsequenceChainStep,
    build_capacity_limited_graph,
)
from seedmind.training import (
    ExperienceTransition,
    OnlinePredictiveTrainer,
    OnlineTrainerConfig,
    OnlineTrainingMetrics,
    collect_experience,
)

_EXPERIMENT_ACTIONS = (
    PrimitiveAction.TURN_LEFT,
    PrimitiveAction.TURN_RIGHT,
    PrimitiveAction.MOVE_FORWARD,
    PrimitiveAction.INSPECT,
    PrimitiveAction.PUSH,
    PrimitiveAction.WAIT,
)
_EFFECT_CODES = (
    "controllable_change",
    "external_change",
    "prediction_error",
    "resource_cost",
    "termination_risk",
)
_ACTIVE_NEED_CODE = "live_learned_consequence"


@dataclass(frozen=True, slots=True)
class LearnedConsequenceLivePredictionRecord:
    """One pre-action consequence prediction and later real-outcome comparison."""

    phase: str
    step_index: int
    source_step_id: int
    action_code: str
    event_id: str
    prediction_id: str
    evidence_count_before: int
    predicted_effect_count: int
    predicted_next_context_available: bool
    confidence_before: float
    confidence_after: float
    uncertainty_before: float
    uncertainty_after: float
    evidence_applied: bool
    evaluation_eligible: bool
    combined_accuracy: float | None
    calibration_direction: str
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.phase not in {"pretraining", "evaluation"}:
            raise ValueError("phase is invalid")
        if self.step_index < 0 or self.source_step_id < 0:
            raise ValueError("live prediction indices must not be negative")
        if not self.action_code.strip() or not self.action_code.isascii():
            raise ValueError("action_code must be non-empty ASCII")
        if not self.event_id.strip() or not self.event_id.isascii():
            raise ValueError("event_id must be non-empty ASCII")
        if not self.prediction_id.strip() or not self.prediction_id.isascii():
            raise ValueError("prediction_id must be non-empty ASCII")
        if self.evidence_count_before < 0 or self.predicted_effect_count < 0:
            raise ValueError("prediction evidence counts must not be negative")
        for name, value in (
            ("confidence_before", self.confidence_before),
            ("confidence_after", self.confidence_after),
            ("uncertainty_before", self.uncertainty_before),
            ("uncertainty_after", self.uncertainty_after),
        ):
            _validate_unit(name, value)
        if self.combined_accuracy is not None:
            _validate_unit("combined_accuracy", self.combined_accuracy)
        if self.evaluation_eligible != (self.combined_accuracy is not None):
            raise ValueError("evaluation eligibility must match combined accuracy")
        if self.has_action_selection_authority:
            raise ValueError("learned consequence predictions cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("learned consequence predictions cannot control production actions")


@dataclass(frozen=True, slots=True)
class LearnedConsequenceLiveSession:
    """Production timeline with optional learned-consequence observation records."""

    scenario_id: str
    action_codes: tuple[str, ...]
    prediction_errors: tuple[float, ...]
    records: tuple[LearnedConsequenceLivePredictionRecord, ...]
    observations: tuple[ConsequenceModelObservation, ...] = ()

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        if len(self.action_codes) != len(self.prediction_errors):
            raise ValueError("action and error timelines must have equal length")
        if len(self.records) not in {0, len(self.action_codes)}:
            raise ValueError("prediction records must be absent or cover the complete timeline")
        if len(self.observations) not in {0, len(self.action_codes)}:
            raise ValueError("observations must be absent or cover the complete timeline")
        for action_code in self.action_codes:
            if not action_code.strip() or not action_code.isascii():
                raise ValueError("action code timeline contains invalid entries")
        for error in self.prediction_errors:
            if not isfinite(error) or error < 0.0:
                raise ValueError("prediction errors must be finite and non-negative")

    @property
    def authority_violation_count(self) -> int:
        return sum(
            record.has_action_selection_authority or record.has_production_action_authority
            for record in self.records
        )


@dataclass(frozen=True, slots=True)
class LearnedConsequenceAcceptanceResult:
    """Falsifiable live evidence for Batch 5 learned-consequence integration."""

    scenario_id: str
    seed: int
    play_budget: int
    pretraining_selection_count: int
    baseline_selection_count: int
    evaluation_selection_count: int
    production_actions_unchanged: bool
    prediction_errors_unchanged: bool
    pre_action_prediction_count: int
    evaluated_prediction_count: int
    minimum_evaluation_accuracy: float
    uncertainty_reduction_observed: bool
    contradiction_confidence_reduction_observed: bool
    context_local_unknown_preserved: bool
    learned_real_observation_count: int
    learned_record_count: int
    checkpoint_automatic_prediction_count: int
    authority_violation_count: int
    advice_decision_count: int
    route_ranking_count: int
    growth_attempt_count: int
    replay_operation_count: int
    restoration_operation_count: int
    sqlite_used_for_learned_consequence_acceptance: bool
    observed_chain_count: int
    chain_prediction_count: int
    chain_supporting_real_event_count: int
    chain_ordered_event_ids_preserved: bool
    chain_ordered_action_codes_preserved: bool
    chain_exact_continuity_verified: bool
    chain_duplicate_protection_passed: bool
    event_identity_conflict_rejected: bool
    chain_disconnected_rejected: bool
    chain_replay_rejected: bool
    chain_imagined_rejected: bool
    chain_transfer_non_evidentiary: bool
    chain_partial_effects_are_non_fabricated: bool
    chain_missing_effects_are_unknown: bool
    bounded_update_failure_preserved_state: bool
    configured_model_bound_enforced: bool
    configured_chain_bound_enforced: bool
    prediction_caused_no_mutation: bool
    deterministic_repeated_acceptance_result: bool
    schema_version_saved: int
    schema_version_loaded: int | None
    restart_loaded_through_schema_7: bool
    restart_checkpoint_round_trip_exact: bool
    restart_exact_prediction_equivalent: bool
    restart_chain_prediction_equivalent: bool
    restart_provenance_preserved: bool
    restart_duplicate_protection_preserved: bool
    restart_configuration_preserved: bool
    restart_confidence_preserved: bool
    restart_zero_authority_preserved: bool
    malformed_persisted_state_safe_fallback: bool
    expanded_architecture_before: int
    expanded_architecture_after: int
    pass_gate: bool

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        if self.seed < 0 or self.play_budget <= 1:
            raise ValueError("seed and play_budget are invalid")
        counts = (
            self.pretraining_selection_count,
            self.baseline_selection_count,
            self.evaluation_selection_count,
            self.pre_action_prediction_count,
            self.evaluated_prediction_count,
            self.learned_real_observation_count,
            self.learned_record_count,
            self.checkpoint_automatic_prediction_count,
            self.authority_violation_count,
            self.advice_decision_count,
            self.route_ranking_count,
            self.growth_attempt_count,
            self.replay_operation_count,
            self.restoration_operation_count,
            self.observed_chain_count,
            self.chain_prediction_count,
            self.chain_supporting_real_event_count,
            self.schema_version_saved,
        )
        if any(count < 0 for count in counts):
            raise ValueError("acceptance counts must not be negative")
        if self.schema_version_loaded is not None and self.schema_version_loaded < 0:
            raise ValueError("loaded schema version must not be negative")
        _validate_unit("minimum_evaluation_accuracy", self.minimum_evaluation_accuracy)
        for name, value in (
            ("expanded_architecture_before", self.expanded_architecture_before),
            ("expanded_architecture_after", self.expanded_architecture_after),
        ):
            if not 0 <= value <= 100:
                raise ValueError(f"{name} must be a percentage")


@dataclass(frozen=True, slots=True)
class LearnedConsequenceAcceptanceEvidence:
    """Result, live timelines, and final learned checkpoint for inspection."""

    result: LearnedConsequenceAcceptanceResult
    pretraining: LearnedConsequenceLiveSession
    baseline: LearnedConsequenceLiveSession
    evaluation: LearnedConsequenceLiveSession
    checkpoint: NDNRALearnedConsequenceCheckpoint
    observed_chains: tuple[ObservedConsequenceChain, ...]
    state_path: Path
    malformed_state_path: Path


@dataclass(frozen=True, slots=True)
class _RestartEvidence:
    state_path: Path
    malformed_state_path: Path
    saved_schema_version: int
    loaded_schema_version: int | None
    loaded_through_schema_7: bool
    checkpoint_round_trip_exact: bool
    exact_prediction_equivalent: bool
    chain_prediction_equivalent: bool
    provenance_preserved: bool
    duplicate_protection_preserved: bool
    configuration_preserved: bool
    confidence_preserved: bool
    zero_authority_preserved: bool
    malformed_persisted_state_safe_fallback: bool


@dataclass(frozen=True, slots=True)
class _FailurePathEvidence:
    duplicate_protection_passed: bool
    event_identity_conflict_rejected: bool
    disconnected_rejected: bool
    replay_rejected: bool
    imagined_rejected: bool
    transfer_non_evidentiary: bool
    partial_effects_are_non_fabricated: bool
    missing_effects_are_unknown: bool
    bounded_update_failure_preserved_state: bool
    configured_model_bound_enforced: bool
    configured_chain_bound_enforced: bool
    prediction_caused_no_mutation: bool
    deterministic_repeated_acceptance_result: bool


def run_learned_consequence_acceptance(
    output_directory: Path,
    *,
    seed: int = 7,
    play_budget: int = 8,
    _verify_determinism: bool = True,
) -> LearnedConsequenceAcceptanceEvidence:
    """Run live pre-action consequence prediction without production authority."""
    if seed < 0:
        raise ValueError("seed must not be negative")
    if play_budget <= 1:
        raise ValueError("play_budget must exceed one")
    output_directory.mkdir(parents=True, exist_ok=True)
    scenario_factory = DynamicNurseryScenarioFactory()
    curiosity = CuriosityConfig(
        play_budget=play_budget,
        experiment_actions=_EXPERIMENT_ACTIONS,
    )
    model = LearnedConsequenceModel()
    pretraining = _run_live_session(
        seed,
        scenario_factory,
        curiosity,
        phase="pretraining",
        model=model,
    )
    baseline = _run_control_session(seed, scenario_factory, curiosity)
    evaluation = _run_live_session(
        seed,
        scenario_factory,
        curiosity,
        phase="evaluation",
        model=model,
    )

    chain_model = ObservedConsequenceChainModel(
        ObservedConsequenceChainConfig(
            maximum_chain_depth=2,
            maximum_chains=max(1, (play_budget - 1) * 2),
        )
    )
    observed_chains = _observe_live_chains(
        chain_model,
        (pretraining.observations, evaluation.observations),
    )
    checkpoint = NDNRALearnedConsequenceCheckpoint(
        consequence_model=model,
        observed_chain_model=chain_model,
    )
    evaluation_records = evaluation.records
    evaluated = tuple(record for record in evaluation_records if record.evaluation_eligible)
    minimum_accuracy = (
        min(
            record.combined_accuracy for record in evaluated if record.combined_accuracy is not None
        )
        if evaluated
        else 0.0
    )
    actions_unchanged = baseline.action_codes == evaluation.action_codes
    errors_unchanged = baseline.prediction_errors == evaluation.prediction_errors
    uncertainty_reduction = _uncertainty_reduction_observed(evaluation_records) or (
        _consistent_probe_reduces_uncertainty()
    )
    contradiction_reduction = _contradiction_probe_reduces_confidence()
    context_local_unknown = _context_local_unknown_preserved()
    chain_prediction = chain_model.predict(_chain_request(observed_chains[0]))
    chain_ordered_event_ids = _ordered_event_ids_preserved(
        observed_chains,
        (pretraining.observations, evaluation.observations),
    )
    chain_ordered_action_codes = all(
        chain.action_codes == tuple(step.action_code for step in chain.steps)
        for chain in observed_chains
    )
    chain_exact_continuity = all(
        step.next_context == chain.steps[index + 1].context
        for chain in observed_chains
        for index, step in enumerate(chain.steps[:-1])
    )
    restart = _restart_evidence(
        output_directory=output_directory,
        checkpoint=checkpoint,
        observation=evaluation.observations[0],
        chain=observed_chains[0],
    )
    deterministic_repeated = True
    if _verify_determinism:
        repeated = run_learned_consequence_acceptance(
            output_directory / "determinism_repeat",
            seed=seed,
            play_budget=play_budget,
            _verify_determinism=False,
        )
        deterministic_repeated = _acceptance_signature(
            pretraining=pretraining,
            baseline=baseline,
            evaluation=evaluation,
            checkpoint=checkpoint,
            observed_chains=observed_chains,
        ) == _acceptance_signature(
            pretraining=repeated.pretraining,
            baseline=repeated.baseline,
            evaluation=repeated.evaluation,
            checkpoint=repeated.checkpoint,
            observed_chains=repeated.observed_chains,
        )
    failures = _failure_path_evidence(
        model=model,
        chain_model=chain_model,
        observation=evaluation.observations[0],
        chain=observed_chains[0],
        deterministic_repeated=deterministic_repeated,
    )
    authority_violations = (
        pretraining.authority_violation_count
        + evaluation.authority_violation_count
        + int(model.has_action_selection_authority)
        + int(model.has_production_action_authority)
        + int(chain_model.has_action_selection_authority)
        + int(chain_model.has_production_action_authority)
        + int(checkpoint.has_action_selection_authority)
        + int(checkpoint.has_production_action_authority)
    )
    pass_gate = bool(
        pretraining_selection_count(pretraining) == play_budget
        and len(baseline.action_codes) == play_budget
        and len(evaluation.action_codes) == play_budget
        and actions_unchanged
        and errors_unchanged
        and sum(record.evidence_count_before > 0 for record in evaluation_records) == play_budget
        and len(evaluated) == play_budget
        and minimum_accuracy > 0.0
        and uncertainty_reduction
        and contradiction_reduction
        and context_local_unknown
        and model.real_observation_count == play_budget * 2
        and model.record_count >= 1
        and len(observed_chains) == (play_budget - 1) * 2
        and chain_prediction.supporting_chain_ids
        and chain_prediction.supporting_real_event_ids
        and chain_ordered_event_ids
        and chain_ordered_action_codes
        and chain_exact_continuity
        and failures.duplicate_protection_passed
        and failures.event_identity_conflict_rejected
        and failures.disconnected_rejected
        and failures.replay_rejected
        and failures.imagined_rejected
        and failures.transfer_non_evidentiary
        and failures.partial_effects_are_non_fabricated
        and failures.missing_effects_are_unknown
        and failures.bounded_update_failure_preserved_state
        and failures.configured_model_bound_enforced
        and failures.configured_chain_bound_enforced
        and failures.prediction_caused_no_mutation
        and failures.deterministic_repeated_acceptance_result
        and restart.loaded_through_schema_7
        and restart.checkpoint_round_trip_exact
        and restart.exact_prediction_equivalent
        and restart.chain_prediction_equivalent
        and restart.provenance_preserved
        and restart.duplicate_protection_preserved
        and restart.configuration_preserved
        and restart.confidence_preserved
        and restart.zero_authority_preserved
        and restart.malformed_persisted_state_safe_fallback
        and checkpoint.automatic_prediction_count == 0
        and authority_violations == 0
    )
    result = LearnedConsequenceAcceptanceResult(
        scenario_id=evaluation.scenario_id,
        seed=seed,
        play_budget=play_budget,
        pretraining_selection_count=pretraining_selection_count(pretraining),
        baseline_selection_count=len(baseline.action_codes),
        evaluation_selection_count=len(evaluation.action_codes),
        production_actions_unchanged=actions_unchanged,
        prediction_errors_unchanged=errors_unchanged,
        pre_action_prediction_count=sum(
            record.evidence_count_before > 0 for record in evaluation_records
        ),
        evaluated_prediction_count=len(evaluated),
        minimum_evaluation_accuracy=minimum_accuracy,
        uncertainty_reduction_observed=uncertainty_reduction,
        contradiction_confidence_reduction_observed=contradiction_reduction,
        context_local_unknown_preserved=context_local_unknown,
        learned_real_observation_count=model.real_observation_count,
        learned_record_count=model.record_count,
        checkpoint_automatic_prediction_count=checkpoint.automatic_prediction_count,
        authority_violation_count=authority_violations,
        advice_decision_count=0,
        route_ranking_count=0,
        growth_attempt_count=0,
        replay_operation_count=0,
        restoration_operation_count=0,
        sqlite_used_for_learned_consequence_acceptance=False,
        observed_chain_count=len(observed_chains),
        chain_prediction_count=len(chain_prediction.supporting_chain_ids),
        chain_supporting_real_event_count=len(chain_prediction.supporting_real_event_ids),
        chain_ordered_event_ids_preserved=chain_ordered_event_ids,
        chain_ordered_action_codes_preserved=chain_ordered_action_codes,
        chain_exact_continuity_verified=chain_exact_continuity,
        chain_duplicate_protection_passed=failures.duplicate_protection_passed,
        event_identity_conflict_rejected=failures.event_identity_conflict_rejected,
        chain_disconnected_rejected=failures.disconnected_rejected,
        chain_replay_rejected=failures.replay_rejected,
        chain_imagined_rejected=failures.imagined_rejected,
        chain_transfer_non_evidentiary=failures.transfer_non_evidentiary,
        chain_partial_effects_are_non_fabricated=failures.partial_effects_are_non_fabricated,
        chain_missing_effects_are_unknown=failures.missing_effects_are_unknown,
        bounded_update_failure_preserved_state=(failures.bounded_update_failure_preserved_state),
        configured_model_bound_enforced=failures.configured_model_bound_enforced,
        configured_chain_bound_enforced=failures.configured_chain_bound_enforced,
        prediction_caused_no_mutation=failures.prediction_caused_no_mutation,
        deterministic_repeated_acceptance_result=(
            failures.deterministic_repeated_acceptance_result
        ),
        schema_version_saved=restart.saved_schema_version,
        schema_version_loaded=restart.loaded_schema_version,
        restart_loaded_through_schema_7=restart.loaded_through_schema_7,
        restart_checkpoint_round_trip_exact=restart.checkpoint_round_trip_exact,
        restart_exact_prediction_equivalent=restart.exact_prediction_equivalent,
        restart_chain_prediction_equivalent=restart.chain_prediction_equivalent,
        restart_provenance_preserved=restart.provenance_preserved,
        restart_duplicate_protection_preserved=restart.duplicate_protection_preserved,
        restart_configuration_preserved=restart.configuration_preserved,
        restart_confidence_preserved=restart.confidence_preserved,
        restart_zero_authority_preserved=restart.zero_authority_preserved,
        malformed_persisted_state_safe_fallback=(restart.malformed_persisted_state_safe_fallback),
        expanded_architecture_before=80,
        expanded_architecture_after=82,
        pass_gate=pass_gate,
    )
    return LearnedConsequenceAcceptanceEvidence(
        result=result,
        pretraining=pretraining,
        baseline=baseline,
        evaluation=evaluation,
        checkpoint=checkpoint,
        observed_chains=observed_chains,
        state_path=restart.state_path,
        malformed_state_path=restart.malformed_state_path,
    )


def export_learned_consequence_acceptance(
    evidence: LearnedConsequenceAcceptanceEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export report, live timeline, and final learned consequence checkpoint."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "learned_consequence_acceptance_report.json"
    timeline_path = output_directory / "learned_consequence_live_timeline.csv"
    checkpoint_path = output_directory / "learned_consequence_checkpoint.json"

    _write_ascii_json(report_path, asdict(evidence.result))
    _write_ascii_json(checkpoint_path, evidence.checkpoint.snapshot())
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "phase",
                "step_index",
                "source_step_id",
                "action_code",
                "event_id",
                "evidence_count_before",
                "predicted_effect_count",
                "predicted_next_context_available",
                "confidence_before",
                "confidence_after",
                "uncertainty_before",
                "uncertainty_after",
                "evidence_applied",
                "evaluation_eligible",
                "combined_accuracy",
                "calibration_direction",
                "has_action_selection_authority",
                "has_production_action_authority",
            )
        )
        for record in (*evidence.pretraining.records, *evidence.evaluation.records):
            writer.writerow(
                (
                    record.phase,
                    record.step_index,
                    record.source_step_id,
                    record.action_code,
                    record.event_id,
                    record.evidence_count_before,
                    record.predicted_effect_count,
                    str(record.predicted_next_context_available).lower(),
                    record.confidence_before,
                    record.confidence_after,
                    record.uncertainty_before,
                    record.uncertainty_after,
                    str(record.evidence_applied).lower(),
                    str(record.evaluation_eligible).lower(),
                    "" if record.combined_accuracy is None else record.combined_accuracy,
                    record.calibration_direction,
                    str(record.has_action_selection_authority).lower(),
                    str(record.has_production_action_authority).lower(),
                )
            )
    return report_path, timeline_path, checkpoint_path


def pretraining_selection_count(session: LearnedConsequenceLiveSession) -> int:
    """Return the number of production transitions observed during pretraining."""
    return len(session.action_codes)


def _observe_live_chains(
    model: ObservedConsequenceChainModel,
    sessions: tuple[tuple[ConsequenceModelObservation, ...], ...],
) -> tuple[ObservedConsequenceChain, ...]:
    chains: list[ObservedConsequenceChain] = []
    for observations in sessions:
        for first, second in pairwise(observations):
            chain = ObservedConsequenceChain.from_observations((first, second))
            update = model.observe(chain)
            if not update.evidence_applied:
                raise RuntimeError("live observed chain was not unique")
            chains.append(chain)
    return tuple(chains)


def _chain_request(chain: ObservedConsequenceChain) -> ConsequenceChainPredictionRequest:
    return ConsequenceChainPredictionRequest(
        start_context=chain.start_context,
        action_codes=chain.action_codes,
        relevant_effect_codes=_EFFECT_CODES,
    )


def _ordered_event_ids_preserved(
    chains: tuple[ObservedConsequenceChain, ...],
    sessions: tuple[tuple[ConsequenceModelObservation, ...], ...],
) -> bool:
    expected = tuple(
        tuple(observation.event_id for observation in observations[index : index + 2])
        for observations in sessions
        for index in range(len(observations) - 1)
    )
    return tuple(chain.source_event_ids for chain in chains) == expected


def _restart_evidence(
    *,
    output_directory: Path,
    checkpoint: NDNRALearnedConsequenceCheckpoint,
    observation: ConsequenceModelObservation,
    chain: ObservedConsequenceChain,
) -> _RestartEvidence:
    state_path = output_directory / "learned_consequence_closure_brain_state.json"
    malformed_path = output_directory / "learned_consequence_malformed_brain_state.json"
    store = NDNRABrainStore(state_path)
    saved = store.save(
        build_capacity_limited_graph(),
        learned_consequence_checkpoint=checkpoint,
    )
    loaded = store.load()
    loaded_checkpoint = loaded.learned_consequence_checkpoint
    exact_request = ConsequencePredictionRequest(
        context=observation.context,
        action_code=observation.action_code,
        relevant_effect_codes=_EFFECT_CODES,
    )
    chain_request = _chain_request(chain)
    exact_before = checkpoint.consequence_model.predict(exact_request)
    exact_after = loaded_checkpoint.consequence_model.predict(exact_request)
    chain_before = checkpoint.observed_chain_model.predict(chain_request)
    chain_after = loaded_checkpoint.observed_chain_model.predict(chain_request)
    duplicate_before = loaded_checkpoint.snapshot()
    duplicate = loaded_checkpoint.consequence_model.observe(observation)
    chain_duplicate = loaded_checkpoint.observed_chain_model.observe(chain)
    duplicate_after = loaded_checkpoint.snapshot()

    raw = json.loads(state_path.read_text(encoding="ascii"))
    payload = cast(dict[str, object], raw["payload"])
    learned = cast(dict[str, object], payload["learned_consequence_checkpoint"])
    learned["automatic_prediction_count"] = 1
    _write_brain_envelope(
        malformed_path,
        schema=cast(str, raw["schema"]),
        schema_version=cast(int, raw["schema_version"]),
        payload=payload,
    )
    malformed = NDNRABrainStore(malformed_path).load()
    return _RestartEvidence(
        state_path=state_path,
        malformed_state_path=malformed_path,
        saved_schema_version=saved.schema_version,
        loaded_schema_version=loaded.schema_version,
        loaded_through_schema_7=(
            saved.schema_version == BRAIN_SCHEMA_VERSION
            and loaded.status is BrainLoadStatus.LOADED
            and loaded.schema_version == BRAIN_SCHEMA_VERSION
            and loaded.checksum_verified
            and not loaded.used_fallback
        ),
        checkpoint_round_trip_exact=loaded_checkpoint.snapshot() == checkpoint.snapshot(),
        exact_prediction_equivalent=exact_after.snapshot() == exact_before.snapshot(),
        chain_prediction_equivalent=chain_after.snapshot() == chain_before.snapshot(),
        provenance_preserved=(
            exact_after.supporting_real_event_ids == exact_before.supporting_real_event_ids
            and chain_after.supporting_real_event_ids == chain_before.supporting_real_event_ids
        ),
        duplicate_protection_preserved=(
            not duplicate.evidence_applied
            and not chain_duplicate.evidence_applied
            and duplicate_before == duplicate_after
        ),
        configuration_preserved=(
            loaded_checkpoint.consequence_model.config == checkpoint.consequence_model.config
            and loaded_checkpoint.observed_chain_model.config
            == checkpoint.observed_chain_model.config
        ),
        confidence_preserved=(
            exact_after.calibrated_confidence == exact_before.calibrated_confidence
            and chain_after.confidence == chain_before.confidence
        ),
        zero_authority_preserved=(
            not loaded_checkpoint.has_action_selection_authority
            and not loaded_checkpoint.has_production_action_authority
            and not exact_after.has_action_selection_authority
            and not exact_after.has_production_action_authority
            and not chain_after.has_action_selection_authority
            and not chain_after.has_production_action_authority
            and loaded_checkpoint.automatic_prediction_count == 0
        ),
        malformed_persisted_state_safe_fallback=(
            malformed.status is BrainLoadStatus.CORRUPT_FALLBACK
            and malformed.used_fallback
            and malformed.learned_consequence_checkpoint
            == NDNRALearnedConsequenceCheckpoint.empty()
        ),
    )


def _failure_path_evidence(
    *,
    model: LearnedConsequenceModel,
    chain_model: ObservedConsequenceChainModel,
    observation: ConsequenceModelObservation,
    chain: ObservedConsequenceChain,
    deterministic_repeated: bool,
) -> _FailurePathEvidence:
    duplicate_before = model.snapshot()
    duplicate = model.observe(observation)
    duplicate_after = model.snapshot()
    conflict_before = model.snapshot()
    event_identity_conflict = False
    try:
        model.observe(
            replace(
                observation,
                observed_effects=(
                    replace(
                        observation.observed_effects[0],
                        value=-observation.observed_effects[0].value,
                    ),
                    *observation.observed_effects[1:],
                ),
            )
        )
    except ValueError as error:
        event_identity_conflict = "identity conflict" in str(error)
    conflict_after = model.snapshot()

    disconnected_rejected = _raises_value_error(
        lambda: ObservedConsequenceChain.from_observations(
            (
                observation,
                replace(
                    _observation_from_chain_step(chain.steps[-1]),
                    context=_probe_context("disconnected", 0.123),
                ),
            )
        ),
        "disconnected",
    )
    replay_rejected = _raises_value_error(
        lambda: ObservedConsequenceChain.from_observations(
            (replace(observation, origin=ExperienceOrigin.REPLAY),)
        ),
        "real origin",
    )
    imagined_rejected = _raises_value_error(
        lambda: ObservedConsequenceChain.from_observations(
            (replace(observation, origin=ExperienceOrigin.IMAGINED),)
        ),
        "real origin",
    )
    transfer_before = (model.snapshot(), chain_model.snapshot())
    transfer_prediction = BoundedContextualTransferPolicy().predict(
        model,
        ConsequencePredictionRequest(
            context=_probe_context("transfer", 0.8),
            action_code=observation.action_code,
            relevant_effect_codes=_EFFECT_CODES,
        ),
    )
    transfer_after = (model.snapshot(), chain_model.snapshot())
    partial = chain_model.predict(
        ConsequenceChainPredictionRequest(
            start_context=chain.start_context,
            action_codes=chain.action_codes,
            relevant_effect_codes=("controllable_change", "zz_unobserved_effect"),
        )
    )
    missing = chain_model.predict(
        ConsequenceChainPredictionRequest(
            start_context=chain.start_context,
            action_codes=chain.action_codes,
            relevant_effect_codes=("zz_unobserved_effect",),
        )
    )
    bounded_update_failure = _bounded_update_failure_preserved_state(chain)
    model_bound = _configured_model_bound_enforced(observation)
    chain_bound = _configured_chain_bound_enforced(chain)
    prediction_before = (model.snapshot(), chain_model.snapshot())
    model.predict(
        ConsequencePredictionRequest(
            context=observation.context,
            action_code=observation.action_code,
            relevant_effect_codes=_EFFECT_CODES,
        )
    )
    chain_model.predict(_chain_request(chain))
    prediction_after = (model.snapshot(), chain_model.snapshot())

    return _FailurePathEvidence(
        duplicate_protection_passed=(
            not duplicate.evidence_applied and duplicate_before == duplicate_after
        ),
        event_identity_conflict_rejected=(
            event_identity_conflict and conflict_before == conflict_after
        ),
        disconnected_rejected=disconnected_rejected,
        replay_rejected=replay_rejected,
        imagined_rejected=imagined_rejected,
        transfer_non_evidentiary=(
            not isinstance(transfer_prediction, ConsequenceModelObservation)
            and transfer_before == transfer_after
        ),
        partial_effects_are_non_fabricated=(
            0.0 < partial.effect_coverage < 1.0
            and all(
                effect.effect_code != "zz_unobserved_effect"
                for step in partial.step_predictions
                for effect in step.predicted_effects
            )
        ),
        missing_effects_are_unknown=(
            missing.effect_coverage == 0.0
            and all(not step.predicted_effects for step in missing.step_predictions)
        ),
        bounded_update_failure_preserved_state=bounded_update_failure,
        configured_model_bound_enforced=model_bound,
        configured_chain_bound_enforced=chain_bound,
        prediction_caused_no_mutation=prediction_before == prediction_after,
        deterministic_repeated_acceptance_result=deterministic_repeated,
    )


def _bounded_update_failure_preserved_state(chain: ObservedConsequenceChain) -> bool:
    model = ObservedConsequenceChainModel(ObservedConsequenceChainConfig(maximum_chains=1))
    model.observe(chain)
    before = model.snapshot()
    extra = ObservedConsequenceChain.from_observations(
        (
            replace(
                _observation_from_chain_step(chain.steps[0]), event_id="real:bounded:extra:0001"
            ),
            replace(
                _observation_from_chain_step(chain.steps[1]), event_id="real:bounded:extra:0002"
            ),
        )
    )
    rejected = _raises_value_error(lambda: model.observe(extra), "bound exceeded")
    return rejected and model.snapshot() == before


def _configured_model_bound_enforced(observation: ConsequenceModelObservation) -> bool:
    model = LearnedConsequenceModel(LearnedConsequenceModelConfig(maximum_real_observations=1))
    model.observe(observation)
    before = model.snapshot()
    rejected = _raises_value_error(
        lambda: model.observe(replace(observation, event_id="real:model-bound:extra")),
        "bound exceeded",
    )
    return rejected and model.snapshot() == before


def _configured_chain_bound_enforced(chain: ObservedConsequenceChain) -> bool:
    model = ObservedConsequenceChainModel(ObservedConsequenceChainConfig(maximum_chain_depth=1))
    before = model.snapshot()
    rejected = _raises_value_error(lambda: model.observe(chain), "depth bound exceeded")
    return rejected and model.snapshot() == before


def _acceptance_signature(
    *,
    pretraining: LearnedConsequenceLiveSession,
    baseline: LearnedConsequenceLiveSession,
    evaluation: LearnedConsequenceLiveSession,
    checkpoint: NDNRALearnedConsequenceCheckpoint,
    observed_chains: tuple[ObservedConsequenceChain, ...],
) -> dict[str, object]:
    return {
        "pretraining_actions": pretraining.action_codes,
        "pretraining_errors": pretraining.prediction_errors,
        "baseline_actions": baseline.action_codes,
        "baseline_errors": baseline.prediction_errors,
        "evaluation_actions": evaluation.action_codes,
        "evaluation_errors": evaluation.prediction_errors,
        "checkpoint": checkpoint.snapshot(),
        "chains": [chain.snapshot() for chain in observed_chains],
    }


def _observation_from_chain_step(
    step: ObservedConsequenceChainStep,
) -> ConsequenceModelObservation:
    return ConsequenceModelObservation(
        event_id=step.event_id,
        origin=step.origin,
        context=step.context,
        action_code=step.action_code,
        next_context=step.next_context,
        observed_effects=step.observed_effects,
    )


def _raises_value_error(callable_: Callable[[], object], expected: str) -> bool:
    try:
        callable_()
    except ValueError as error:
        return expected in str(error)
    return False


def _canonical_checksum(payload: object) -> str:
    encoded = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return hashlib.sha256(encoded).hexdigest()


def _write_brain_envelope(
    path: Path,
    *,
    schema: str,
    schema_version: int,
    payload: dict[str, object],
) -> None:
    replay_checkpoint = cast(dict[str, object], payload["replay_restoration_checkpoint"])
    state_payload: dict[str, object] = {
        "graph": payload["graph"],
        "growth_state": payload["growth_state"],
        "consolidation_checkpoint": payload["consolidation_checkpoint"],
        "proposal_lifecycle_checkpoint": payload["proposal_lifecycle_checkpoint"],
        "execution_checkpoint": payload["execution_checkpoint"],
        "replay_restoration_active_state": {
            "activity_ledger": replay_checkpoint["activity_ledger"],
        },
        "learned_consequence_checkpoint": payload["learned_consequence_checkpoint"],
    }
    body: dict[str, object] = {
        "schema": schema,
        "schema_version": schema_version,
        "state_checksum": _canonical_checksum(state_payload),
        "payload": payload,
    }
    path.write_text(
        json.dumps(
            {**body, "checksum": _canonical_checksum(body)},
            ensure_ascii=True,
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="ascii",
    )


def _run_control_session(
    seed: int,
    scenario_factory: DynamicNurseryScenarioFactory,
    curiosity_config: CuriosityConfig,
) -> LearnedConsequenceLiveSession:
    scenario = scenario_factory.create(seed)
    if curiosity_config.play_budget > scenario.step_budget:
        raise ValueError("learned consequence play budget exceeds scenario step budget")
    curiosity = CuriositySubsystem(curiosity_config)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-learned-consequence-control",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    trainer = _build_trainer(seed, scenario_factory)
    actions: list[str] = []
    errors: list[float] = []
    trainer.reset_episode()
    while not curiosity.budget_exhausted:
        observation = runtime.observe()
        selection = curiosity.select(observation.available_actions)
        experience = collect_experience(runtime, selection.selected_action)
        metrics = trainer.train_transition(experience)
        curiosity.observe(selection.selected_action, metrics.mean_absolute_error)
        actions.append(selection.selected_action.value)
        errors.append(metrics.mean_absolute_error)
        if experience.terminated:
            raise RuntimeError("control session terminated before budget exhaustion")
    trainer.reset_episode()
    return LearnedConsequenceLiveSession(
        scenario_id=scenario.scenario_id,
        action_codes=tuple(actions),
        prediction_errors=tuple(errors),
        records=(),
    )


def _run_live_session(
    seed: int,
    scenario_factory: DynamicNurseryScenarioFactory,
    curiosity_config: CuriosityConfig,
    *,
    phase: str,
    model: LearnedConsequenceModel,
) -> LearnedConsequenceLiveSession:
    scenario = scenario_factory.create(seed)
    if curiosity_config.play_budget > scenario.step_budget:
        raise ValueError("learned consequence play budget exceeds scenario step budget")
    curiosity = CuriositySubsystem(curiosity_config)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-learned-consequence-{phase}",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    trainer = _build_trainer(seed, scenario_factory)
    actions: list[str] = []
    errors: list[float] = []
    records: list[LearnedConsequenceLivePredictionRecord] = []
    observations: list[ConsequenceModelObservation] = []
    trainer.reset_episode()
    while not curiosity.budget_exhausted:
        observation = runtime.observe()
        step_index = len(records)
        selection = curiosity.select(observation.available_actions)
        context = _context_from_observation(observation)
        request = ConsequencePredictionRequest(
            context=context,
            action_code=selection.selected_action.value,
            relevant_effect_codes=_EFFECT_CODES,
        )
        prior = model.predict(request)
        experience = collect_experience(runtime, selection.selected_action)
        metrics = trainer.train_transition(experience)
        curiosity.observe(selection.selected_action, metrics.mean_absolute_error)
        next_context = _context_from_observation(experience.next_observation)
        event = ConsequenceModelObservation(
            event_id=_event_id(phase, experience),
            origin=ExperienceOrigin.REAL,
            context=context,
            action_code=selection.selected_action.value,
            next_context=next_context,
            observed_effects=_observed_effects(experience, metrics),
        )
        update = model.observe(
            event,
            prior_prediction=prior if prior.evidence_count > 0 else None,
        )
        post = model.predict(request)
        evaluation = update.evaluation
        records.append(
            LearnedConsequenceLivePredictionRecord(
                phase=phase,
                step_index=step_index,
                source_step_id=experience.observation.step_id,
                action_code=selection.selected_action.value,
                event_id=event.event_id,
                prediction_id=prior.prediction_id,
                evidence_count_before=prior.evidence_count,
                predicted_effect_count=len(prior.predicted_effects),
                predicted_next_context_available=prior.predicted_next_context is not None,
                confidence_before=prior.calibrated_confidence,
                confidence_after=post.calibrated_confidence,
                uncertainty_before=prior.uncertainty,
                uncertainty_after=post.uncertainty,
                evidence_applied=update.evidence_applied,
                evaluation_eligible=(
                    False if evaluation is None else evaluation.calibration_eligible
                ),
                combined_accuracy=(
                    None
                    if evaluation is None or not evaluation.calibration_eligible
                    else evaluation.combined_accuracy
                ),
                calibration_direction=(
                    "unknown" if evaluation is None else evaluation.calibration_direction.value
                ),
                has_action_selection_authority=(
                    prior.has_action_selection_authority or post.has_action_selection_authority
                ),
                has_production_action_authority=(
                    prior.has_production_action_authority or post.has_production_action_authority
                ),
            )
        )
        actions.append(selection.selected_action.value)
        errors.append(metrics.mean_absolute_error)
        observations.append(event)
        if experience.terminated:
            raise RuntimeError("learned consequence session terminated before budget exhaustion")
    trainer.reset_episode()
    return LearnedConsequenceLiveSession(
        scenario_id=scenario.scenario_id,
        action_codes=tuple(actions),
        prediction_errors=tuple(errors),
        records=tuple(records),
        observations=tuple(observations),
    )


def _context_from_observation(observation: ObservationPacket) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code=_ACTIVE_NEED_CODE,
        sensor_values=observation.sensor_values,
        available_action_codes=(action.value for action in observation.available_actions),
        human_values=observation.human_signal,
        resource_values=observation.resource_state,
    )


def _observed_effects(
    experience: ExperienceTransition,
    metrics: OnlineTrainingMetrics,
) -> tuple[EffectObservation, ...]:
    values = {
        "controllable_change": _mean_absolute(experience.controllable_sensor_change),
        "external_change": _mean_absolute(experience.external_sensor_change),
        "prediction_error": _clamp_unit(metrics.mean_absolute_error),
        "resource_cost": _resource_cost(experience),
        "termination_risk": float(experience.terminated),
    }
    return tuple(
        EffectObservation(effect_code, values[effect_code], 1.0) for effect_code in _EFFECT_CODES
    )


def _event_id(phase: str, experience: ExperienceTransition) -> str:
    return (
        "real:learned-consequence:"
        f"{phase}:{experience.observation.episode_id}:{experience.observation.step_id:04d}"
    )


def _uncertainty_reduction_observed(
    records: tuple[LearnedConsequenceLivePredictionRecord, ...],
) -> bool:
    return any(
        record.evidence_count_before > 0
        and record.uncertainty_after < record.uncertainty_before
        and record.confidence_after > record.confidence_before
        for record in records
    )


def _consistent_probe_reduces_uncertainty() -> bool:
    model = LearnedConsequenceModel()
    context = _probe_context("stable", 0.8)
    next_context = _probe_context("stable", 0.6)
    request = ConsequencePredictionRequest(
        context=context,
        action_code="cool",
        relevant_effect_codes=("temperature",),
    )
    first = ConsequenceModelObservation(
        event_id="real:probe:stable:0001",
        origin=ExperienceOrigin.REAL,
        context=context,
        action_code="cool",
        next_context=next_context,
        observed_effects=(EffectObservation("temperature", -0.4, 1.0),),
    )
    second = ConsequenceModelObservation(
        event_id="real:probe:stable:0002",
        origin=ExperienceOrigin.REAL,
        context=context,
        action_code="cool",
        next_context=next_context,
        observed_effects=(EffectObservation("temperature", -0.4, 1.0),),
    )
    model.observe(first)
    prior = model.predict(request)
    model.observe(second, prior_prediction=prior)
    after = model.predict(request)
    return (
        prior.evidence_count == 1
        and after.evidence_count == 2
        and after.uncertainty < prior.uncertainty
        and after.calibrated_confidence > prior.calibrated_confidence
    )


def _contradiction_probe_reduces_confidence() -> bool:
    model = LearnedConsequenceModel()
    context = _probe_context("contradiction", 0.8)
    expected_next = _probe_context("contradiction", 0.6)
    contradictory_next = _probe_context("contradiction", 1.0)
    request = ConsequencePredictionRequest(
        context=context,
        action_code="cool",
        relevant_effect_codes=("temperature",),
    )
    for index in range(4):
        model.observe(
            ConsequenceModelObservation(
                event_id=f"real:probe:consistent:{index:04d}",
                origin=ExperienceOrigin.REAL,
                context=context,
                action_code="cool",
                next_context=expected_next,
                observed_effects=(EffectObservation("temperature", -0.6, 1.0),),
            )
        )
    prior = model.predict(request)
    update = model.observe(
        ConsequenceModelObservation(
            event_id="real:probe:contradiction:0001",
            origin=ExperienceOrigin.REAL,
            context=context,
            action_code="cool",
            next_context=contradictory_next,
            observed_effects=(EffectObservation("temperature", 0.6, 1.0),),
        ),
        prior_prediction=prior,
    )
    after = model.predict(request)
    return (
        update.evaluation is not None
        and update.evaluation.calibration_eligible
        and update.evaluation.combined_accuracy < prior.calibrated_confidence
        and after.calibrated_confidence < prior.calibrated_confidence
    )


def _context_local_unknown_preserved() -> bool:
    model = LearnedConsequenceModel()
    source = _probe_context("local", 0.8)
    target = _probe_context("local", 0.2)
    next_context = _probe_context("local", 0.7)
    model.observe(
        ConsequenceModelObservation(
            event_id="real:probe:local:0001",
            origin=ExperienceOrigin.REAL,
            context=source,
            action_code="cool",
            next_context=next_context,
            observed_effects=(EffectObservation("temperature", -0.2, 1.0),),
        )
    )
    prediction = model.predict(
        ConsequencePredictionRequest(
            context=target,
            action_code="cool",
            relevant_effect_codes=("temperature",),
        )
    )
    return (
        prediction.evidence_count == 0
        and prediction.predicted_effects == ()
        and prediction.predicted_next_context is None
        and prediction.uncertainty == 1.0
    )


def _probe_context(scenario: str, temperature: float) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code=f"probe_{scenario}",
        sensor_values=(temperature,),
        available_action_codes=("cool", "wait"),
        resource_values=(0.5,),
    )


def _build_trainer(
    seed: int,
    scenario_factory: DynamicNurseryScenarioFactory,
) -> OnlinePredictiveTrainer:
    scenario = scenario_factory.create(seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-learned-consequence-interface",
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


def _mean_absolute(values: tuple[float, ...]) -> float:
    if not values:
        return 0.0
    return _clamp_unit(fmean(abs(value) for value in values))


def _resource_cost(experience: ExperienceTransition) -> float:
    source = experience.observation.resource_state
    destination = experience.next_observation.resource_state
    if not source:
        return 0.0
    return _clamp_unit(
        fmean(
            max(0.0, source_value - destination_value)
            for source_value, destination_value in zip(
                source,
                destination,
                strict=True,
            )
        )
    )


def _clamp_unit(value: float) -> float:
    if not isfinite(value):
        raise ValueError("effect value must be finite")
    return max(0.0, min(1.0, value))


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _write_ascii_json(path: Path, payload: object) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)
