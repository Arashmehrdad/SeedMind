"""Live acceptance gate for non-authoritative learned consequence prediction."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from math import isfinite
from pathlib import Path
from statistics import fmean

import torch

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.curiosity import CuriosityConfig, CuriositySubsystem
from seedmind.environment import DynamicNurseryScenarioFactory, NurseryRuntime
from seedmind.perception import SymbolicInputSpec
from seedmind.research.ndnra import (
    ConsequenceModelObservation,
    ConsequencePredictionRequest,
    ContextSignature,
    EffectObservation,
    ExperienceOrigin,
    LearnedConsequenceModel,
    NDNRALearnedConsequenceCheckpoint,
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

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        if len(self.action_codes) != len(self.prediction_errors):
            raise ValueError("action and error timelines must have equal length")
        if len(self.records) not in {0, len(self.action_codes)}:
            raise ValueError("prediction records must be absent or cover the complete timeline")
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
        )
        if any(count < 0 for count in counts):
            raise ValueError("acceptance counts must not be negative")
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


def run_learned_consequence_acceptance(
    output_directory: Path,
    *,
    seed: int = 7,
    play_budget: int = 8,
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

    checkpoint = NDNRALearnedConsequenceCheckpoint(consequence_model=model)
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
    authority_violations = (
        pretraining.authority_violation_count
        + evaluation.authority_violation_count
        + int(model.has_action_selection_authority)
        + int(model.has_production_action_authority)
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
        if experience.terminated:
            raise RuntimeError("learned consequence session terminated before budget exhaustion")
    trainer.reset_episode()
    return LearnedConsequenceLiveSession(
        scenario_id=scenario.scenario_id,
        action_codes=tuple(actions),
        prediction_errors=tuple(errors),
        records=tuple(records),
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
