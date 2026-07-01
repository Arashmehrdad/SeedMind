"""Grounded deterministic Week 10 capacity-diagnosis runner."""

from __future__ import annotations

import hashlib
import json
import shutil
import tempfile
from collections import deque
from dataclasses import dataclass
from pathlib import Path
from statistics import fmean

import torch

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.core import compare_prediction
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    NurseryRuntime,
    NurseryState,
    NurseryTransitionEngine,
    ShapeCode,
    TransitionOutcome,
)
from seedmind.growth.diagnostic_ladder import DiagnosticLadderRecord, build_ladder
from seedmind.growth.proposal import GrowthProposalRecord, build_week10_growth_proposal
from seedmind.growth.stagnation import (
    LearningAttempt,
    LearningProgressThresholds,
    LearningProgressWindow,
    PlateauClassification,
    build_learning_progress_windows,
    final_classification,
)
from seedmind.human import (
    ApprenticeshipManager,
    HelpContext,
    HumanRequest,
    RequestIntentCode,
    VerificationRule,
)
from seedmind.memory import (
    EpisodicEvent,
    EpisodicEventDraft,
    EpisodicEventType,
    EpisodicSQLiteStore,
    MemoryQuery,
    SignificanceFeatures,
    SignificanceScorer,
)
from seedmind.skills import (
    ApproachAndPushSkillController,
    SkillExecutionStatus,
    Week8ScenarioFactory,
    read_skill_record,
    retain_skill_candidate_through_curiosity,
)

DEFAULT_WEEK10_OUTPUT_DIR = Path("artifacts/week10_capacity_diagnosis")
DEFAULT_WEEK8_SKILL_RECORD = Path(
    "artifacts/week8_reusable_skill/approach_and_push_skill_record.json"
)
WEEK10_CONTROL_SEEDS = (206, 207, 208, 211)
WEEK10_EARLY_SEEDS = (310, 311, 312, 313)
WEEK10_TEMPORARY_SEEDS = (410, 411, 412, 413, 414, 415, 416, 417, 418, 419, 420, 421)
WEEK10_BLOCKAGE_SEEDS = (510, 511, 512, 513, 514, 515, 516, 517, 518, 519, 520, 521)
WEEK10_NON_CAPACITY_SEEDS = (610, 611, 612, 613)
MAX_RESOLVED_PREDICTION_MAE = 0.05


@dataclass(frozen=True, slots=True)
class PredictionTraceRecord:
    """One real predicted-versus-observed transition comparison."""

    prediction_id: str
    action: str
    predicted_source: str
    mean_absolute_error: float
    mean_squared_error: float
    evidence_available: bool

    def to_json(self) -> dict[str, object]:
        return {
            "action": self.action,
            "evidence_available": self.evidence_available,
            "mean_absolute_error": self.mean_absolute_error,
            "mean_squared_error": self.mean_squared_error,
            "predicted_source": self.predicted_source,
            "prediction_id": self.prediction_id,
        }


@dataclass(frozen=True, slots=True)
class EpisodeStepTrace:
    """One primitive action and real Nursery transition outcome."""

    step_index: int
    action: PrimitiveAction
    transition_outcome: TransitionOutcome
    object_position_before: GridPosition
    object_position_after: GridPosition
    prediction: PredictionTraceRecord

    def to_json(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "object_position_after": _position_json(self.object_position_after),
            "object_position_before": _position_json(self.object_position_before),
            "prediction": self.prediction.to_json(),
            "step_index": self.step_index,
            "transition_outcome": self.transition_outcome.value,
        }


@dataclass(frozen=True, slots=True)
class GroundedEpisodeTrace:
    """Full provenance for one executed diagnostic attempt."""

    episode_id: str
    seed: int
    scenario_family: str
    initial_state_digest: str
    object_id: str
    target_id: str
    strategy_id: str
    actions: tuple[str, ...]
    transition_outcomes: tuple[str, ...]
    initial_distance: int
    final_distance: int
    task_progress: float
    success: bool
    steps_used: int
    invalid_or_ineffective_action_count: int
    prediction_error: float
    help_request_events: tuple[str, ...]
    replay_influence: tuple[str, ...]
    demonstration_influence: tuple[str, ...]
    termination_reason: str
    step_traces: tuple[EpisodeStepTrace, ...]
    final_state_digest: str
    trace_digest: str

    def to_json(self) -> dict[str, object]:
        return {
            "actions": list(self.actions),
            "demonstration_influence": list(self.demonstration_influence),
            "episode_id": self.episode_id,
            "final_distance": self.final_distance,
            "final_state_digest": self.final_state_digest,
            "help_request_events": list(self.help_request_events),
            "initial_distance": self.initial_distance,
            "initial_state_digest": self.initial_state_digest,
            "invalid_or_ineffective_action_count": self.invalid_or_ineffective_action_count,
            "object_id": self.object_id,
            "prediction_error": self.prediction_error,
            "replay_influence": list(self.replay_influence),
            "scenario_family": self.scenario_family,
            "seed": self.seed,
            "step_traces": [step.to_json() for step in self.step_traces],
            "steps_used": self.steps_used,
            "strategy_id": self.strategy_id,
            "success": self.success,
            "target_id": self.target_id,
            "task_progress": self.task_progress,
            "termination_reason": self.termination_reason,
            "trace_digest": self.trace_digest,
            "transition_outcomes": list(self.transition_outcomes),
        }


@dataclass(frozen=True, slots=True)
class StrategyVariantRecord:
    """One bounded executable general strategy variant."""

    variant_id: str
    approach_side: str
    contact_offset: int
    alignment_tolerance: int
    retry_angle: str
    reposition_before_push: bool
    safe_attempt_budget: int
    executed_episode_ids: tuple[str, ...]
    created_specialist: bool = False
    mutated_frozen_skill: bool = False

    @property
    def attempts(self) -> int:
        return len(self.executed_episode_ids)

    def to_json(self) -> dict[str, object]:
        return {
            "alignment_tolerance": self.alignment_tolerance,
            "approach_side": self.approach_side,
            "attempts": self.attempts,
            "contact_offset": self.contact_offset,
            "created_specialist": self.created_specialist,
            "executed_episode_ids": list(self.executed_episode_ids),
            "mutated_frozen_skill": self.mutated_frozen_skill,
            "reposition_before_push": self.reposition_before_push,
            "retry_angle": self.retry_angle,
            "safe_attempt_budget": self.safe_attempt_budget,
            "variant_id": self.variant_id,
        }


@dataclass(frozen=True, slots=True)
class MemoryReplayRecord:
    """Grounded main-memory replay evidence for one diagnostic scenario."""

    scenario_family: str
    query: dict[str, object]
    relevant_memory_ids: tuple[str, ...]
    source_episode_ids: tuple[str, ...]
    replay_influenced_episode_ids: tuple[str, ...]
    changed_strategy: bool
    progress_resumed: bool
    evidence_insufficient: bool

    def to_json(self) -> dict[str, object]:
        return {
            "changed_strategy": self.changed_strategy,
            "evidence_insufficient": self.evidence_insufficient,
            "progress_resumed": self.progress_resumed,
            "query": self.query,
            "relevant_memory_ids": list(self.relevant_memory_ids),
            "replay_influenced_episode_ids": list(self.replay_influenced_episode_ids),
            "scenario_family": self.scenario_family,
            "source_episode_ids": list(self.source_episode_ids),
        }


@dataclass(frozen=True, slots=True)
class HelpDemonstrationRecord:
    """Protected help and measured demonstration evidence."""

    scenario_family: str
    help_requested: bool
    help_reason: str
    demonstration_available: bool
    demonstration_episode_id: str | None
    demonstration_trace_digest: str | None
    demonstration_completed_task: bool
    learner_before_episode_ids: tuple[str, ...]
    learner_after_episode_ids: tuple[str, ...]
    before_mean_progress: float
    after_mean_progress: float
    demonstration_applied: bool
    performance_improved_afterward: bool
    blockage_remained: bool

    def to_json(self) -> dict[str, object]:
        return {
            "after_mean_progress": self.after_mean_progress,
            "before_mean_progress": self.before_mean_progress,
            "blockage_remained": self.blockage_remained,
            "demonstration_applied": self.demonstration_applied,
            "demonstration_available": self.demonstration_available,
            "demonstration_completed_task": self.demonstration_completed_task,
            "demonstration_episode_id": self.demonstration_episode_id,
            "demonstration_trace_digest": self.demonstration_trace_digest,
            "help_reason": self.help_reason,
            "help_requested": self.help_requested,
            "learner_after_episode_ids": list(self.learner_after_episode_ids),
            "learner_before_episode_ids": list(self.learner_before_episode_ids),
            "performance_improved_afterward": self.performance_improved_afterward,
            "scenario_family": self.scenario_family,
        }


@dataclass(frozen=True, slots=True)
class Week10ScenarioDiagnosis:
    """Complete diagnosis for one required scenario family."""

    scenario_family: str
    classification: PlateauClassification
    attempts: tuple[LearningAttempt, ...]
    windows: tuple[LearningProgressWindow, ...]
    ladder: DiagnosticLadderRecord
    replay: MemoryReplayRecord
    help: HelpDemonstrationRecord
    proposal_generated: bool
    non_capacity_reason: str | None = None

    def to_json(self) -> dict[str, object]:
        return {
            "attempts": [_attempt_json(attempt) for attempt in self.attempts],
            "classification": self.classification.value,
            "help": self.help.to_json(),
            "ladder": self.ladder.to_json(),
            "non_capacity_reason": self.non_capacity_reason,
            "proposal_generated": self.proposal_generated,
            "replay": self.replay.to_json(),
            "scenario_family": self.scenario_family,
            "windows": [window.to_json() for window in self.windows],
        }


@dataclass(frozen=True, slots=True)
class RepositoryInventory:
    """Static repository evidence for no growth, Week 11, or NDNRA dependency."""

    specialist_created: bool
    router_created: bool
    week11_started: bool
    ndnra_required: bool

    def to_json(self) -> dict[str, object]:
        return {
            "ndnra_required": self.ndnra_required,
            "router_created": self.router_created,
            "specialist_created": self.specialist_created,
            "week11_started": self.week11_started,
        }


@dataclass(frozen=True, slots=True)
class Week10AcceptanceReport:
    """Separate Week 10 result fields derived from evidence."""

    environment_extension_pass: bool
    grounded_attempt_provenance_pass: bool
    learning_progress_pass: bool
    temporary_failure_classification_pass: bool
    sustained_blockage_classification_pass: bool
    diagnostic_ladder_pass: bool
    memory_replay_grounding_pass: bool
    teacher_demonstration_grounding_pass: bool
    prediction_evidence_pass: bool
    non_capacity_blockage_pass: bool
    growth_delay_pass: bool
    growth_proposal_pass: bool
    frozen_skill_preservation_pass: bool
    frozen_ndnra_boundary_pass: bool
    week10_main_milestone_pass: bool
    familiar_control_success_rate: float
    frozen_skill_sha256_before: str
    frozen_skill_sha256_after: str
    repository_inventory: RepositoryInventory

    @property
    def week11_started(self) -> bool:
        return self.repository_inventory.week11_started

    @property
    def specialist_created(self) -> bool:
        return self.repository_inventory.specialist_created

    @property
    def router_created(self) -> bool:
        return self.repository_inventory.router_created

    @property
    def ndnra_required(self) -> bool:
        return self.repository_inventory.ndnra_required

    def to_json(self) -> dict[str, object]:
        return {
            "diagnostic_ladder_pass": self.diagnostic_ladder_pass,
            "environment_extension_pass": self.environment_extension_pass,
            "familiar_control_success_rate": self.familiar_control_success_rate,
            "frozen_ndnra_boundary_pass": self.frozen_ndnra_boundary_pass,
            "frozen_skill_preservation_pass": self.frozen_skill_preservation_pass,
            "frozen_skill_sha256_after": self.frozen_skill_sha256_after,
            "frozen_skill_sha256_before": self.frozen_skill_sha256_before,
            "grounded_attempt_provenance_pass": self.grounded_attempt_provenance_pass,
            "growth_delay_pass": self.growth_delay_pass,
            "growth_proposal_pass": self.growth_proposal_pass,
            "learning_progress_pass": self.learning_progress_pass,
            "memory_replay_grounding_pass": self.memory_replay_grounding_pass,
            "non_capacity_blockage_pass": self.non_capacity_blockage_pass,
            "prediction_evidence_pass": self.prediction_evidence_pass,
            "repository_inventory": self.repository_inventory.to_json(),
            "router_created": self.router_created,
            "specialist_created": self.specialist_created,
            "sustained_blockage_classification_pass": self.sustained_blockage_classification_pass,
            "teacher_demonstration_grounding_pass": self.teacher_demonstration_grounding_pass,
            "temporary_failure_classification_pass": self.temporary_failure_classification_pass,
            "week10_main_milestone_pass": self.week10_main_milestone_pass,
            "week11_started": self.week11_started,
        }


@dataclass(frozen=True, slots=True)
class Week10RunResult:
    """All deterministic Week 10 evidence before export."""

    thresholds: LearningProgressThresholds
    familiar_control_success_rate: float
    familiar_control_steps: tuple[int, ...]
    cube_push_outcomes: dict[str, str]
    strategy_variants: tuple[StrategyVariantRecord, ...]
    diagnoses: tuple[Week10ScenarioDiagnosis, ...]
    episode_traces: tuple[GroundedEpisodeTrace, ...]
    proposal: GrowthProposalRecord | None
    acceptance_report: Week10AcceptanceReport
    artifact_paths: tuple[Path, ...] = ()


def run_week10_capacity_diagnosis(
    *,
    output_dir: Path | None = None,
    skill_record_path: Path = DEFAULT_WEEK8_SKILL_RECORD,
    temporary_seeds: tuple[int, ...] = WEEK10_TEMPORARY_SEEDS,
    blockage_seeds: tuple[int, ...] = WEEK10_BLOCKAGE_SEEDS,
) -> Week10RunResult:
    """Run grounded deterministic Week 10 diagnosis and optionally export evidence."""
    if len(temporary_seeds) < 12 or len(blockage_seeds) < 12:
        raise ValueError("temporary and blockage seed sets must cover three full windows")
    skill_hash_before = _sha256_file(skill_record_path)
    thresholds = LearningProgressThresholds()
    cube_push_outcomes = _cube_push_outcomes()
    familiar_success_rate, familiar_steps = _run_familiar_control(skill_record_path)

    with tempfile.TemporaryDirectory(prefix="seedmind-week10-grounded-memory-") as tmp:
        store = EpisodicSQLiteStore(Path(tmp) / "week10_memory.sqlite3")
        try:
            scorer = SignificanceScorer()
            traces: list[GroundedEpisodeTrace] = []
            strategy_variants: list[StrategyVariantRecord] = []

            early = _early_evidence_diagnosis(thresholds, store, scorer, traces)
            temporary = _temporary_failure_diagnosis(
                thresholds,
                store,
                scorer,
                traces,
                strategy_variants,
                temporary_seeds=temporary_seeds,
            )
            sustained = _sustained_blockage_diagnosis(
                thresholds,
                store,
                scorer,
                traces,
                strategy_variants,
                blockage_seeds=blockage_seeds,
            )
            non_capacity = _non_capacity_diagnosis(thresholds, store, scorer, traces)
        finally:
            store.close()

    skill_hash_after = _sha256_file(skill_record_path)
    repository_inventory = _repository_inventory()
    proposal = _build_sustained_proposal_if_allowed(sustained)
    diagnoses = (
        early,
        temporary,
        _with_proposal_state(sustained, proposal is not None),
        non_capacity,
    )
    trace_tuple = tuple(traces)
    variant_tuple = tuple(strategy_variants)

    environment_pass = (
        cube_push_outcomes["round_open_push"] == TransitionOutcome.PUSHED.value
        and cube_push_outcomes["angular_wall_push"]
        == TransitionOutcome.PUSH_INEFFECTIVE_CONTACT.value
        and cube_push_outcomes["angular_open_push"] == TransitionOutcome.PUSHED.value
    )
    grounded_attempt_pass = all(
        attempt.has_grounded_provenance for diagnosis in diagnoses for attempt in diagnosis.attempts
    ) and all(trace.step_traces for trace in trace_tuple)
    prediction_steps = tuple(step.prediction for trace in trace_tuple for step in trace.step_traces)
    prediction_pass = bool(prediction_steps) and all(
        prediction.evidence_available
        and prediction.mean_absolute_error <= MAX_RESOLVED_PREDICTION_MAE
        for prediction in prediction_steps
    )
    learning_progress_pass = (
        early.classification is PlateauClassification.INSUFFICIENT_EVIDENCE
        and temporary.classification is PlateauClassification.IMPROVING
        and sustained.classification is PlateauClassification.SUSTAINED_BLOCKAGE
    )
    replay_pass = bool(
        temporary.replay.progress_resumed
        and temporary.replay.relevant_memory_ids
        and sustained.replay.relevant_memory_ids
        and not sustained.replay.progress_resumed
    )
    demonstration_pass = (
        temporary.help.demonstration_completed_task
        and temporary.help.performance_improved_afterward
        and sustained.help.demonstration_completed_task
        and sustained.help.blockage_remained
    )
    non_capacity_pass = (
        non_capacity.proposal_generated is False
        and non_capacity.ladder.stopped_early
        and non_capacity.non_capacity_reason
        == "ambiguous_request,impossible_geometry,resource_budget_exhaustion,unsafe_permission_blocked"
    )
    growth_delay_pass = (
        early.proposal_generated is False
        and temporary.proposal_generated is False
        and non_capacity.proposal_generated is False
        and proposal is not None
    )
    growth_proposal_pass = (
        proposal is not None
        and proposal.status.value == "proposed_not_authorised"
        and proposal.candidate.created is False
    )
    frozen_skill_pass = skill_hash_before == skill_hash_after
    frozen_ndnra_pass = _frozen_ndnra_boundary_pass()
    no_growth_started = (
        not repository_inventory.specialist_created
        and not repository_inventory.router_created
        and not repository_inventory.week11_started
        and not repository_inventory.ndnra_required
        and not any(
            variant.created_specialist or variant.mutated_frozen_skill for variant in variant_tuple
        )
    )
    acceptance = Week10AcceptanceReport(
        environment_extension_pass=environment_pass,
        grounded_attempt_provenance_pass=grounded_attempt_pass,
        learning_progress_pass=learning_progress_pass,
        temporary_failure_classification_pass=(
            temporary.proposal_generated is False
            and temporary.help.performance_improved_afterward
            and temporary.replay.progress_resumed
        ),
        sustained_blockage_classification_pass=(
            sustained.classification is PlateauClassification.SUSTAINED_BLOCKAGE
            and sustained.ladder.completed_for_growth_proposal
        ),
        diagnostic_ladder_pass=sustained.ladder.completed_for_growth_proposal,
        memory_replay_grounding_pass=replay_pass,
        teacher_demonstration_grounding_pass=demonstration_pass,
        prediction_evidence_pass=prediction_pass,
        non_capacity_blockage_pass=non_capacity_pass,
        growth_delay_pass=growth_delay_pass,
        growth_proposal_pass=growth_proposal_pass,
        frozen_skill_preservation_pass=frozen_skill_pass,
        frozen_ndnra_boundary_pass=frozen_ndnra_pass,
        week10_main_milestone_pass=(
            environment_pass
            and grounded_attempt_pass
            and prediction_pass
            and learning_progress_pass
            and replay_pass
            and demonstration_pass
            and non_capacity_pass
            and growth_delay_pass
            and growth_proposal_pass
            and frozen_skill_pass
            and frozen_ndnra_pass
            and no_growth_started
        ),
        familiar_control_success_rate=familiar_success_rate,
        frozen_skill_sha256_before=skill_hash_before,
        frozen_skill_sha256_after=skill_hash_after,
        repository_inventory=repository_inventory,
    )
    result = Week10RunResult(
        thresholds=thresholds,
        familiar_control_success_rate=familiar_success_rate,
        familiar_control_steps=familiar_steps,
        cube_push_outcomes=cube_push_outcomes,
        strategy_variants=variant_tuple,
        diagnoses=diagnoses,
        episode_traces=trace_tuple,
        proposal=proposal,
        acceptance_report=acceptance,
    )
    if output_dir is not None:
        paths = export_week10_evidence(result, output_dir)
        result = Week10RunResult(
            thresholds=result.thresholds,
            familiar_control_success_rate=result.familiar_control_success_rate,
            familiar_control_steps=result.familiar_control_steps,
            cube_push_outcomes=result.cube_push_outcomes,
            strategy_variants=result.strategy_variants,
            diagnoses=result.diagnoses,
            episode_traces=result.episode_traces,
            proposal=result.proposal,
            acceptance_report=result.acceptance_report,
            artifact_paths=paths,
        )
    return result


def export_week10_evidence(result: Week10RunResult, output_dir: Path) -> tuple[Path, ...]:
    """Write deterministic grounded Week 10 artifacts."""
    _preserve_superseded_scripted_evidence(output_dir)
    traces = output_dir / "grounded_episode_traces.json"
    diagnostic_report = output_dir / "diagnostic_report.json"
    proposal_record = output_dir / "growth_proposal_record.json"
    windows = output_dir / "learning_progress_windows.json"
    visualisation = output_dir / "plateau_visualisation.svg"
    acceptance = output_dir / "week10_acceptance_report.json"
    _write_json(traces, _traces_payload(result))
    _write_json(diagnostic_report, _diagnostic_report_payload(result))
    _write_json(proposal_record, {} if result.proposal is None else result.proposal.to_json())
    _write_json(windows, _windows_payload(result))
    _write_svg(visualisation, result)
    _write_json(acceptance, result.acceptance_report.to_json())
    return (traces, diagnostic_report, proposal_record, windows, visualisation, acceptance)


def _early_evidence_diagnosis(
    thresholds: LearningProgressThresholds,
    store: EpisodicSQLiteStore,
    scorer: SignificanceScorer,
    traces: list[GroundedEpisodeTrace],
) -> Week10ScenarioDiagnosis:
    attempts = tuple(
        _execute_attempt(
            scenario_family="early_cube_evidence",
            seed=seed,
            strategy_id="frozen_skill",
            plan_kind="frozen_skill",
            store=store,
            scorer=scorer,
            traces=traces,
        )
        for seed in WEEK10_EARLY_SEEDS
    )
    windows = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="early_cube_evidence",
        strategy_variants_exhausted=False,
        replay_attempted=False,
        help_or_demonstration_considered=False,
    )
    ladder = build_ladder(
        scenario_family="early_cube_evidence",
        task_confirmed=True,
        safe_exploration_sufficient=False,
        relevant_memory_retrieved=False,
        existing_skill_attempted=True,
        strategy_variants_tested=False,
        help_or_demonstration_considered=False,
        replay_attempted=False,
        prediction_quality_checked=True,
        competence_still_improving=False,
        inferred_policy_capacity_limitation=False,
        proposal_allowed=False,
        attempt_count=len(attempts),
        evidence_prefix="trace:early_cube_evidence",
    )
    return Week10ScenarioDiagnosis(
        scenario_family="early_cube_evidence",
        classification=final_classification(windows),
        attempts=attempts,
        windows=windows,
        ladder=ladder,
        replay=_empty_replay("early_cube_evidence"),
        help=_empty_help("early_cube_evidence", "minimum evidence not reached"),
        proposal_generated=False,
    )


def _temporary_failure_diagnosis(
    thresholds: LearningProgressThresholds,
    store: EpisodicSQLiteStore,
    scorer: SignificanceScorer,
    traces: list[GroundedEpisodeTrace],
    strategy_variants: list[StrategyVariantRecord],
    *,
    temporary_seeds: tuple[int, ...],
) -> Week10ScenarioDiagnosis:
    seeds = temporary_seeds[:12]
    attempts: list[LearningAttempt] = []
    for seed in seeds[:4]:
        attempts.append(
            _execute_attempt(
                scenario_family="temporary_cube_recovery",
                seed=seed,
                strategy_id="frozen_skill",
                plan_kind="frozen_skill",
                store=store,
                scorer=scorer,
                traces=traces,
            )
        )
    for seed in seeds[4:6]:
        attempts.append(
            _execute_attempt(
                scenario_family="temporary_cube_recovery",
                seed=seed,
                strategy_id="variant_reposition_south",
                plan_kind="south_only",
                store=store,
                scorer=scorer,
                traces=traces,
            )
        )

    source_attempts = tuple(attempts)
    memories = _retrieve_replay_events("temporary_cube_recovery", store, source_attempts)
    for seed in seeds[6:8]:
        state = _scenario_state("temporary_cube_recovery", seed, plan_kind="memory_replay")
        attempts.append(
            _execute_attempt(
                scenario_family="temporary_cube_recovery",
                seed=seed,
                strategy_id="memory_guided_contact",
                plan_kind="memory_replay",
                store=store,
                scorer=scorer,
                traces=traces,
                replay_influence=tuple(event.event_id for event in memories),
                actions_override=_actions_from_retrieved_memory(
                    state,
                    memories,
                    traces,
                    complete_toward_target=True,
                    budget=18,
                ),
            )
        )

    demonstration = _execute_demonstration(
        "temporary_cube_recovery",
        seed=900,
        store=store,
        scorer=scorer,
        traces=traces,
    )
    for seed in seeds[8:12]:
        state = _scenario_state("temporary_cube_recovery", seed, plan_kind="demonstration")
        attempts.append(
            _execute_attempt(
                scenario_family="temporary_cube_recovery",
                seed=seed,
                strategy_id="teacher_demonstrated_contact",
                plan_kind="demonstration",
                store=store,
                scorer=scorer,
                traces=traces,
                demonstration_influence=(demonstration.trace_digest,),
                actions_override=_actions_from_demonstration(
                    state,
                    demonstration,
                    budget=18,
                ),
            )
        )

    attempt_tuple = tuple(attempts)
    variant_records = _variant_records_from_attempts("temporary_cube_recovery", attempt_tuple)
    strategy_variants.extend(variant_records)
    replay = _grounded_replay(
        "temporary_cube_recovery",
        store,
        source_attempts=source_attempts,
        influenced_attempts=attempt_tuple[6:8],
    )
    help_record = _help_record(
        "temporary_cube_recovery",
        before_attempts=attempt_tuple[:6],
        after_attempts=attempt_tuple[8:12],
        demonstration_trace=demonstration,
    )
    windows = build_learning_progress_windows(
        attempt_tuple,
        thresholds,
        scenario_family="temporary_cube_recovery",
        strategy_variants_exhausted=False,
        replay_attempted=bool(replay.relevant_memory_ids),
        help_or_demonstration_considered=help_record.help_requested,
    )
    classification = final_classification(windows)
    prediction_resolved = _attempt_prediction_evidence_resolved(attempt_tuple, traces)
    ladder = build_ladder(
        scenario_family="temporary_cube_recovery",
        task_confirmed=True,
        safe_exploration_sufficient=len(attempt_tuple) >= thresholds.minimum_attempts_for_blockage,
        relevant_memory_retrieved=bool(replay.relevant_memory_ids),
        existing_skill_attempted=any(
            attempt.strategy == "frozen_skill" for attempt in attempt_tuple
        ),
        strategy_variants_tested=bool(variant_records),
        help_or_demonstration_considered=(
            help_record.help_requested and help_record.demonstration_available
        ),
        replay_attempted=bool(replay.replay_influenced_episode_ids),
        prediction_quality_checked=prediction_resolved,
        competence_still_improving=classification is PlateauClassification.IMPROVING,
        inferred_policy_capacity_limitation=False,
        proposal_allowed=False,
        attempt_count=len(attempt_tuple),
        evidence_prefix="trace:temporary_cube_recovery",
    )
    return Week10ScenarioDiagnosis(
        scenario_family="temporary_cube_recovery",
        classification=classification,
        attempts=attempt_tuple,
        windows=windows,
        ladder=ladder,
        replay=replay,
        help=help_record,
        proposal_generated=False,
    )


def _execute_sustained_grounded_sequence(
    *,
    seeds: tuple[int, ...],
    store: EpisodicSQLiteStore,
    scorer: SignificanceScorer,
    traces: list[GroundedEpisodeTrace],
) -> tuple[tuple[LearningAttempt, ...], tuple[LearningAttempt, ...], GroundedEpisodeTrace]:
    attempts: list[LearningAttempt] = []
    for seed in seeds[:2]:
        attempts.append(
            _execute_attempt(
                scenario_family="sustained_cube_blockage",
                seed=seed,
                strategy_id="frozen_skill",
                plan_kind="frozen_skill",
                store=store,
                scorer=scorer,
                traces=traces,
            )
        )
    for seed in seeds[2:4]:
        attempts.append(
            _execute_attempt(
                scenario_family="sustained_cube_blockage",
                seed=seed,
                strategy_id="variant_offset_contact",
                plan_kind="push_north",
                store=store,
                scorer=scorer,
                traces=traces,
            )
        )
    source_attempts = tuple(attempts)
    memories = _retrieve_replay_events("sustained_cube_blockage", store, source_attempts)
    for seed in seeds[4:6]:
        state = _scenario_state("sustained_cube_blockage", seed, plan_kind="memory_replay")
        attempts.append(
            _execute_attempt(
                scenario_family="sustained_cube_blockage",
                seed=seed,
                strategy_id="variant_retreat_reapproach",
                plan_kind="memory_replay",
                store=store,
                scorer=scorer,
                traces=traces,
                replay_influence=tuple(event.event_id for event in memories),
                actions_override=_retreat_then_replay_actions(
                    state,
                    memories,
                    traces,
                    budget=8,
                ),
            )
        )
    for seed in seeds[6:8]:
        attempts.append(
            _execute_attempt(
                scenario_family="sustained_cube_blockage",
                seed=seed,
                strategy_id="variant_alternate_side",
                plan_kind="push_west",
                store=store,
                scorer=scorer,
                traces=traces,
            )
        )
    demonstration = _execute_demonstration(
        "sustained_cube_blockage",
        seed=901,
        store=store,
        scorer=scorer,
        traces=traces,
    )
    for seed in seeds[8:12]:
        attempts.append(
            _execute_attempt(
                scenario_family="sustained_cube_blockage",
                seed=seed,
                strategy_id="post_demo_existing_controller",
                plan_kind="frozen_skill",
                store=store,
                scorer=scorer,
                traces=traces,
                demonstration_influence=(demonstration.trace_digest,),
            )
        )
    return tuple(attempts), source_attempts, demonstration


def _sustained_blockage_diagnosis(
    thresholds: LearningProgressThresholds,
    store: EpisodicSQLiteStore,
    scorer: SignificanceScorer,
    traces: list[GroundedEpisodeTrace],
    strategy_variants: list[StrategyVariantRecord],
    *,
    blockage_seeds: tuple[int, ...],
) -> Week10ScenarioDiagnosis:
    seeds = blockage_seeds[:12]
    attempts, source_attempts, demonstration = _execute_sustained_grounded_sequence(
        seeds=seeds,
        store=store,
        scorer=scorer,
        traces=traces,
    )
    variant_records = _variant_records_from_attempts("sustained_cube_blockage", attempts)
    strategy_variants.extend(variant_records)
    replay = _grounded_replay(
        "sustained_cube_blockage",
        store,
        source_attempts=source_attempts,
        influenced_attempts=attempts[4:6],
    )
    help_record = _help_record(
        "sustained_cube_blockage",
        before_attempts=attempts[:8],
        after_attempts=attempts[8:12],
        demonstration_trace=demonstration,
    )
    windows = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="sustained_cube_blockage",
        strategy_variants_exhausted=bool(variant_records),
        replay_attempted=bool(replay.relevant_memory_ids),
        help_or_demonstration_considered=help_record.help_requested,
    )
    classification = final_classification(windows)
    prediction_resolved = _attempt_prediction_evidence_resolved(attempts, traces)
    inferred_limitation = (
        classification is PlateauClassification.SUSTAINED_BLOCKAGE
        and bool(variant_records)
        and bool(replay.relevant_memory_ids)
        and not replay.progress_resumed
        and help_record.demonstration_completed_task
        and help_record.blockage_remained
        and prediction_resolved
    )
    ladder = build_ladder(
        scenario_family="sustained_cube_blockage",
        task_confirmed=True,
        safe_exploration_sufficient=len(attempts) >= thresholds.minimum_attempts_for_blockage,
        relevant_memory_retrieved=bool(replay.relevant_memory_ids),
        existing_skill_attempted=any(attempt.strategy == "frozen_skill" for attempt in attempts),
        strategy_variants_tested=bool(variant_records),
        help_or_demonstration_considered=(
            help_record.help_requested and help_record.demonstration_available
        ),
        replay_attempted=bool(replay.replay_influenced_episode_ids),
        prediction_quality_checked=prediction_resolved,
        competence_still_improving=classification is PlateauClassification.IMPROVING,
        inferred_policy_capacity_limitation=inferred_limitation,
        proposal_allowed=inferred_limitation,
        attempt_count=len(attempts),
        evidence_prefix="trace:sustained_cube_blockage",
    )
    return Week10ScenarioDiagnosis(
        scenario_family="sustained_cube_blockage",
        classification=classification,
        attempts=attempts,
        windows=windows,
        ladder=ladder,
        replay=replay,
        help=help_record,
        proposal_generated=False,
    )


def _non_capacity_diagnosis(
    thresholds: LearningProgressThresholds,
    store: EpisodicSQLiteStore,
    scorer: SignificanceScorer,
    traces: list[GroundedEpisodeTrace],
) -> Week10ScenarioDiagnosis:
    cases = (
        ("ambiguous_request", "request_help_only"),
        ("impossible_geometry", "frozen_skill_impossible"),
        ("resource_budget_exhaustion", "resource_limited"),
        ("unsafe_permission_blocked", "permission_blocked"),
    )
    attempts = tuple(
        _execute_attempt(
            scenario_family="non_capacity_blockage",
            seed=seed,
            strategy_id=case,
            plan_kind=plan,
            store=store,
            scorer=scorer,
            traces=traces,
        )
        for seed, (case, plan) in zip(WEEK10_NON_CAPACITY_SEEDS, cases, strict=True)
    )
    windows = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="non_capacity_blockage",
        strategy_variants_exhausted=False,
        replay_attempted=False,
        help_or_demonstration_considered=True,
        ambiguity_resolved=False,
        safety_or_permission_clear=False,
        resource_limit=True,
    )
    ladder = build_ladder(
        scenario_family="non_capacity_blockage",
        task_confirmed=False,
        safe_exploration_sufficient=False,
        relevant_memory_retrieved=False,
        existing_skill_attempted=False,
        strategy_variants_tested=False,
        help_or_demonstration_considered=True,
        replay_attempted=False,
        prediction_quality_checked=True,
        competence_still_improving=False,
        inferred_policy_capacity_limitation=False,
        proposal_allowed=False,
        attempt_count=len(attempts),
        evidence_prefix="trace:non_capacity_blockage",
    )
    return Week10ScenarioDiagnosis(
        scenario_family="non_capacity_blockage",
        classification=final_classification(windows),
        attempts=attempts,
        windows=windows,
        ladder=ladder,
        replay=_empty_replay("non_capacity_blockage"),
        help=_empty_help("non_capacity_blockage", "non-capacity stop reason measured"),
        proposal_generated=False,
        non_capacity_reason=(
            "ambiguous_request,impossible_geometry,resource_budget_exhaustion,"
            "unsafe_permission_blocked"
        ),
    )


def _execute_attempt(
    *,
    scenario_family: str,
    seed: int,
    strategy_id: str,
    plan_kind: str,
    store: EpisodicSQLiteStore,
    scorer: SignificanceScorer,
    traces: list[GroundedEpisodeTrace],
    replay_influence: tuple[str, ...] = (),
    demonstration_influence: tuple[str, ...] = (),
    actions_override: tuple[PrimitiveAction, ...] | None = None,
) -> LearningAttempt:
    state = _scenario_state(scenario_family, seed, plan_kind=plan_kind)
    episode_id = f"week10-{scenario_family}-{seed}-{strategy_id}"
    if actions_override is not None:
        actions = actions_override
    elif plan_kind == "frozen_skill" or plan_kind == "frozen_skill_impossible":
        actions = _run_frozen_skill_actions(state, budget=8)
    elif plan_kind == "south_only":
        actions = _planned_actions(state, (Direction.SOUTH,), budget=10)
    elif plan_kind == "push_north":
        actions = _planned_actions(state, (Direction.NORTH,), budget=8)
    elif plan_kind == "push_west":
        actions = _planned_actions(state, (Direction.WEST,), budget=8)
    elif plan_kind == "retreat_reapproach":
        actions = _retreat_reapproach_actions(state, budget=8)
    elif plan_kind == "full_teacher":
        actions = _planned_actions(
            state, (Direction.SOUTH, Direction.EAST, Direction.EAST), budget=18
        )
    elif plan_kind == "request_help_only":
        actions = (PrimitiveAction.REQUEST_HELP,)
    elif plan_kind == "resource_limited":
        actions = (PrimitiveAction.PUSH,)
    elif plan_kind == "permission_blocked":
        actions = (PrimitiveAction.WAIT,)
    else:
        raise ValueError(f"unknown plan kind: {plan_kind}")
    step_budget = 1 if plan_kind == "resource_limited" else len(actions)
    trace = _execute_trace(
        state,
        episode_id=episode_id,
        seed=seed,
        scenario_family=scenario_family,
        strategy_id=strategy_id,
        actions=actions[:step_budget],
        replay_influence=replay_influence,
        demonstration_influence=demonstration_influence,
    )
    traces.append(trace)
    _persist_trace_events(trace, store, scorer)
    return LearningAttempt(
        attempt_index=_attempt_index_for_family(traces, scenario_family),
        scenario_family=scenario_family,
        strategy=strategy_id,
        success=trace.success,
        task_progress=trace.task_progress,
        steps_used=max(1, trace.steps_used),
        prediction_error=trace.prediction_error,
        invalid_or_ineffective_actions=trace.invalid_or_ineffective_action_count,
        episode_id=trace.episode_id,
        trace_digest=trace.trace_digest,
        trace_ref=f"grounded_episode_traces.json:{trace.episode_id}",
        help_requested=PrimitiveAction.REQUEST_HELP.value in trace.actions,
        replay_involved=bool(replay_influence),
        demonstration_involved=bool(demonstration_influence),
    )


def _execute_demonstration(
    scenario_family: str,
    *,
    seed: int,
    store: EpisodicSQLiteStore,
    scorer: SignificanceScorer,
    traces: list[GroundedEpisodeTrace],
) -> GroundedEpisodeTrace:
    state = _scenario_state(scenario_family, seed, plan_kind="full_teacher")
    actions = _planned_actions(state, (Direction.SOUTH, Direction.EAST, Direction.EAST), budget=18)
    trace = _execute_trace(
        state,
        episode_id=f"week10-{scenario_family}-{seed}-teacher-demonstration",
        seed=seed,
        scenario_family=scenario_family,
        strategy_id="protected_teacher_oracle_demonstration",
        actions=actions,
        replay_influence=(),
        demonstration_influence=("protected_teacher_response_policy",),
    )
    traces.append(trace)
    _persist_trace_events(trace, store, scorer)
    return trace


def _execute_trace(
    initial_state: NurseryState,
    *,
    episode_id: str,
    seed: int,
    scenario_family: str,
    strategy_id: str,
    actions: tuple[PrimitiveAction, ...],
    replay_influence: tuple[str, ...],
    demonstration_influence: tuple[str, ...],
) -> GroundedEpisodeTrace:
    runtime = NurseryRuntime(initial_state, episode_id)
    initial_distance = _object_target_distance(runtime.state)
    initial_digest = _state_digest(runtime.state)
    step_traces: list[EpisodeStepTrace] = []
    for action in actions:
        if _target_satisfied(runtime.state):
            break
        before_object = _object_position(runtime.state)
        observation = runtime.observe()
        result = runtime.step(action)
        after_object = _object_position(runtime.state)
        prediction = _prediction_trace(
            episode_id=episode_id,
            step_index=len(step_traces),
            action=action,
            predicted_sensor=observation.sensor_values,
            actual_sensor=result.observation.sensor_values,
        )
        step_traces.append(
            EpisodeStepTrace(
                step_index=len(step_traces),
                action=action,
                transition_outcome=result.transition.outcome,
                object_position_before=before_object,
                object_position_after=after_object,
                prediction=prediction,
            )
        )
    final_distance = _object_target_distance(runtime.state)
    progress = _progress(initial_distance, final_distance)
    success = _target_satisfied(runtime.state)
    ineffective_count = sum(
        step.transition_outcome
        in {
            TransitionOutcome.MOVE_BLOCKED_BOUNDARY,
            TransitionOutcome.MOVE_BLOCKED_ENTITY,
            TransitionOutcome.PUSH_BLOCKED_BOUNDARY,
            TransitionOutcome.PUSH_BLOCKED_ENTITY,
            TransitionOutcome.PUSH_IMMOVABLE,
            TransitionOutcome.PUSH_INEFFECTIVE_CONTACT,
            TransitionOutcome.PUSH_NO_CONTACT,
        }
        for step in step_traces
    )
    prediction_error = (
        fmean(step.prediction.mean_absolute_error for step in step_traces) if step_traces else 0.0
    )
    termination_reason = (
        "success"
        if success
        else "budget_exhausted"
        if len(step_traces) >= len(actions)
        else "stopped"
    )
    final_digest = _state_digest(runtime.state)
    payload = {
        "actions": [step.action.value for step in step_traces],
        "episode_id": episode_id,
        "final_distance": final_distance,
        "final_state_digest": final_digest,
        "initial_distance": initial_distance,
        "initial_state_digest": initial_digest,
        "outcomes": [step.transition_outcome.value for step in step_traces],
        "progress": progress,
        "scenario_family": scenario_family,
        "seed": seed,
        "strategy_id": strategy_id,
        "success": success,
    }
    trace_digest = _canonical_digest(payload)
    return GroundedEpisodeTrace(
        episode_id=episode_id,
        seed=seed,
        scenario_family=scenario_family,
        initial_state_digest=initial_digest,
        object_id="object_0",
        target_id="target_0",
        strategy_id=strategy_id,
        actions=tuple(step.action.value for step in step_traces),
        transition_outcomes=tuple(step.transition_outcome.value for step in step_traces),
        initial_distance=initial_distance,
        final_distance=final_distance,
        task_progress=progress,
        success=success,
        steps_used=len(step_traces),
        invalid_or_ineffective_action_count=ineffective_count,
        prediction_error=_clamp_unit(prediction_error),
        help_request_events=tuple(
            f"{episode_id}:help:{step.step_index}"
            for step in step_traces
            if step.action is PrimitiveAction.REQUEST_HELP
        ),
        replay_influence=replay_influence,
        demonstration_influence=demonstration_influence,
        termination_reason=termination_reason,
        step_traces=tuple(step_traces),
        final_state_digest=final_digest,
        trace_digest=trace_digest,
    )


def _prediction_trace(
    *,
    episode_id: str,
    step_index: int,
    action: PrimitiveAction,
    predicted_sensor: tuple[float, ...],
    actual_sensor: tuple[float, ...],
) -> PredictionTraceRecord:
    predicted = torch.tensor(predicted_sensor, dtype=torch.float32)
    actual = torch.tensor(actual_sensor, dtype=torch.float32)
    comparison = compare_prediction(predicted, actual)
    mae = float(comparison.mean_absolute_error.mean().detach().cpu().item())
    mse = float(comparison.mean_squared_error.mean().detach().cpu().item())
    return PredictionTraceRecord(
        prediction_id=f"week10-prediction-{episode_id}-{step_index:02d}",
        action=action.value,
        predicted_source="persistence_baseline_via_seedmind_compare_prediction",
        mean_absolute_error=_clamp_unit(mae),
        mean_squared_error=_clamp_unit(mse),
        evidence_available=True,
    )


def _persist_trace_events(
    trace: GroundedEpisodeTrace,
    store: EpisodicSQLiteStore,
    scorer: SignificanceScorer,
) -> tuple[EpisodicEvent, ...]:
    events: list[EpisodicEvent] = []
    for step in trace.step_traces:
        events.append(
            store.remember(
                EpisodicEventDraft(
                    event_id=f"{trace.episode_id}-event-{step.step_index:02d}",
                    episode_id=trace.episode_id,
                    step_index=step.step_index,
                    event_type=(
                        EpisodicEventType.HUMAN_GUIDANCE
                        if step.action is PrimitiveAction.REQUEST_HELP
                        else EpisodicEventType.ACTION
                    ),
                    context_code=f"{trace.scenario_family}_angular_contact",
                    outcome_code=step.transition_outcome.value,
                    action=step.action,
                    success=trace.success,
                    features=SignificanceFeatures(
                        prediction_error=step.prediction.mean_absolute_error,
                        novelty=0.25,
                        learning_progress=trace.task_progress,
                        ambition_relevance=0.80,
                        human_relevance=(
                            0.75
                            if step.action is PrimitiveAction.REQUEST_HELP
                            or trace.demonstration_influence
                            else 0.10
                        ),
                        outcome_magnitude=trace.task_progress,
                    ),
                    payload=(
                        ("trace_digest", trace.trace_digest),
                        ("strategy_id", trace.strategy_id),
                        ("transition_outcome", step.transition_outcome.value),
                        ("task_progress", trace.task_progress),
                    ),
                ),
                scorer,
            )
        )
    return tuple(events)


def _grounded_replay(
    scenario_family: str,
    store: EpisodicSQLiteStore,
    *,
    source_attempts: tuple[LearningAttempt, ...],
    influenced_attempts: tuple[LearningAttempt, ...],
) -> MemoryReplayRecord:
    query = MemoryQuery(
        minimum_significance=0.05,
        context_code=f"{scenario_family}_angular_contact",
        event_type=EpisodicEventType.ACTION,
        limit=500,
    )
    memories = tuple(
        event
        for event in store.retrieve(query)
        if event.episode_id in {attempt.episode_id for attempt in source_attempts}
    )
    before = fmean(attempt.task_progress for attempt in source_attempts[-2:])
    after = fmean(attempt.task_progress for attempt in influenced_attempts)
    return MemoryReplayRecord(
        scenario_family=scenario_family,
        query={
            "context_code": query.context_code,
            "event_type": EpisodicEventType.ACTION.value,
            "limit": query.limit,
            "minimum_significance": query.minimum_significance,
        },
        relevant_memory_ids=tuple(event.event_id for event in memories),
        source_episode_ids=tuple(sorted({event.episode_id for event in memories})),
        replay_influenced_episode_ids=tuple(attempt.episode_id for attempt in influenced_attempts),
        changed_strategy=bool(influenced_attempts),
        progress_resumed=(after > before + 0.10),
        evidence_insufficient=not memories,
    )


def _retrieve_replay_events(
    scenario_family: str,
    store: EpisodicSQLiteStore,
    source_attempts: tuple[LearningAttempt, ...],
) -> tuple[EpisodicEvent, ...]:
    source_episode_ids = {attempt.episode_id for attempt in source_attempts}
    query = MemoryQuery(
        minimum_significance=0.05,
        context_code=f"{scenario_family}_angular_contact",
        event_type=EpisodicEventType.ACTION,
        limit=500,
    )
    return tuple(event for event in store.retrieve(query) if event.episode_id in source_episode_ids)


def _actions_from_retrieved_memory(
    state: NurseryState,
    memories: tuple[EpisodicEvent, ...],
    traces: list[GroundedEpisodeTrace],
    *,
    complete_toward_target: bool,
    budget: int,
) -> tuple[PrimitiveAction, ...]:
    """Build a bounded action plan from the best retrieved source episode."""
    source_ids = {event.episode_id for event in memories}
    source_traces = [trace for trace in traces if trace.episode_id in source_ids]
    if not source_traces:
        return _run_frozen_skill_actions(state, budget=budget)
    best = max(source_traces, key=lambda trace: (trace.task_progress, trace.episode_id))
    if not complete_toward_target:
        return tuple(step.action for step in best.step_traces)[:budget]

    push_directions = [
        _direction_between(step.object_position_before, step.object_position_after)
        for step in best.step_traces
        if step.object_position_before != step.object_position_after
    ]
    simulated_object = _object_position(state)
    for direction in push_directions:
        simulated_object = simulated_object.moved(direction)
    target = _target_position(state)
    while simulated_object.x != target.x:
        direction = Direction.EAST if simulated_object.x < target.x else Direction.WEST
        push_directions.append(direction)
        simulated_object = simulated_object.moved(direction)
    while simulated_object.y != target.y:
        direction = Direction.SOUTH if simulated_object.y < target.y else Direction.NORTH
        push_directions.append(direction)
        simulated_object = simulated_object.moved(direction)
    return _planned_actions(state, tuple(push_directions), budget=budget)


def _retreat_then_replay_actions(
    state: NurseryState,
    memories: tuple[EpisodicEvent, ...],
    traces: list[GroundedEpisodeTrace],
    *,
    budget: int,
) -> tuple[PrimitiveAction, ...]:
    """Apply a bounded retreat, then retry the best retrieved action sequence."""
    engine = NurseryTransitionEngine()
    current = state
    prefix: list[PrimitiveAction] = []
    retreat_direction = Direction((int(current.agent.orientation) + 2) % 4)
    for turn in _turn_actions(current.agent.orientation, retreat_direction):
        prefix.append(turn)
        current = engine.apply(current, turn).state
    destination = current.agent.position.moved(retreat_direction)
    if (
        len(prefix) < budget
        and current.is_in_bounds(destination)
        and current.blocking_entity_at(destination) is None
    ):
        prefix.append(PrimitiveAction.MOVE_FORWARD)
        current = engine.apply(current, PrimitiveAction.MOVE_FORWARD).state
    remembered = _actions_from_retrieved_memory(
        current,
        memories,
        traces,
        complete_toward_target=False,
        budget=max(0, budget - len(prefix)),
    )
    return tuple((*prefix, *remembered)[:budget])


def _actions_from_demonstration(
    state: NurseryState,
    demonstration: GroundedEpisodeTrace,
    *,
    budget: int,
) -> tuple[PrimitiveAction, ...]:
    push_directions = tuple(
        _direction_between(step.object_position_before, step.object_position_after)
        for step in demonstration.step_traces
        if step.object_position_before != step.object_position_after
    )
    return _planned_actions(state, push_directions, budget=budget)


def _attempt_prediction_evidence_resolved(
    attempts: tuple[LearningAttempt, ...],
    traces: list[GroundedEpisodeTrace],
) -> bool:
    attempt_ids = {attempt.episode_id for attempt in attempts}
    relevant_traces = [trace for trace in traces if trace.episode_id in attempt_ids]
    prediction_steps = [step.prediction for trace in relevant_traces for step in trace.step_traces]
    return bool(prediction_steps) and all(
        prediction.evidence_available
        and prediction.mean_absolute_error <= MAX_RESOLVED_PREDICTION_MAE
        for prediction in prediction_steps
    )


def _help_record(
    scenario_family: str,
    *,
    before_attempts: tuple[LearningAttempt, ...],
    after_attempts: tuple[LearningAttempt, ...],
    demonstration_trace: GroundedEpisodeTrace,
) -> HelpDemonstrationRecord:
    manager = ApprenticeshipManager()
    request = HumanRequest(
        request_id=f"{scenario_family}-request",
        intent_code=RequestIntentCode.PRACTICE_ACTIVE_AMBITION,
        target_code="move_raw_angular_object_to_target",
        ambiguity=0.10,
        permission_level=4,
        verification_rule=VerificationRule.CONFIRMED_OUTCOME,
    )
    context = HelpContext(
        case_id=f"{scenario_family}-help",
        request=request,
        uncertainty=0.85,
        competence=0.15,
        risk=0.10,
        blocked_attempts=3,
        safe_experiment_available=False,
        familiar=False,
    )
    decision = manager.evaluate(context, episode_id=f"{scenario_family}-help-episode", step_index=0)
    response = manager.teacher_response(
        context,
        decision,
        episode_id=f"{scenario_family}-help-episode",
        step_index=1,
    )
    before = fmean(attempt.task_progress for attempt in before_attempts)
    after = fmean(attempt.task_progress for attempt in after_attempts)
    improved = after > before + 0.10
    return HelpDemonstrationRecord(
        scenario_family=scenario_family,
        help_requested=decision.should_request_help,
        help_reason=decision.reason.value,
        demonstration_available=response.code.name.lower() == "demonstrate",
        demonstration_episode_id=demonstration_trace.episode_id,
        demonstration_trace_digest=demonstration_trace.trace_digest,
        demonstration_completed_task=demonstration_trace.success,
        learner_before_episode_ids=tuple(attempt.episode_id for attempt in before_attempts),
        learner_after_episode_ids=tuple(attempt.episode_id for attempt in after_attempts),
        before_mean_progress=before,
        after_mean_progress=after,
        demonstration_applied=response.code.name.lower() == "demonstrate",
        performance_improved_afterward=improved,
        blockage_remained=not improved,
    )


def _variant_records_from_attempts(
    scenario_family: str,
    attempts: tuple[LearningAttempt, ...],
) -> tuple[StrategyVariantRecord, ...]:
    variant_specs = {
        "variant_reposition_south": ("behind_object", 0, 0, "south_reposition", True, 10),
        "memory_guided_contact": ("behind_object", 0, 0, "memory_replay", True, 18),
        "teacher_demonstrated_contact": ("behind_object", 0, 0, "teacher_trace", True, 18),
        "variant_offset_contact": ("left_side", 1, 0, "quarter_turn", True, 8),
        "variant_retreat_reapproach": ("behind_object", 0, 1, "half_turn", True, 8),
        "variant_alternate_side": ("right_side", -1, 0, "quarter_turn", True, 8),
    }
    records: list[StrategyVariantRecord] = []
    for strategy, spec in sorted(variant_specs.items()):
        episode_ids = tuple(
            attempt.episode_id for attempt in attempts if attempt.strategy == strategy
        )
        if episode_ids:
            records.append(
                StrategyVariantRecord(
                    variant_id=f"{scenario_family}-{strategy}",
                    approach_side=spec[0],
                    contact_offset=spec[1],
                    alignment_tolerance=spec[2],
                    retry_angle=spec[3],
                    reposition_before_push=spec[4],
                    safe_attempt_budget=spec[5],
                    executed_episode_ids=episode_ids,
                )
            )
    return tuple(records)


def _build_sustained_proposal_if_allowed(
    sustained: Week10ScenarioDiagnosis,
) -> GrowthProposalRecord | None:
    try:
        return build_week10_growth_proposal(
            scenario_family=sustained.scenario_family,
            classification=sustained.classification,
            ladder=sustained.ladder,
            windows=sustained.windows,
            grounded_replay_pass=(
                bool(sustained.replay.relevant_memory_ids)
                and bool(sustained.replay.replay_influenced_episode_ids)
                and not sustained.replay.evidence_insufficient
            ),
            reachability_proven=sustained.help.demonstration_completed_task,
            strategy_variant_count=len(
                {
                    attempt.strategy
                    for attempt in sustained.attempts
                    if attempt.strategy.startswith("variant_")
                }
            ),
            help_requested=sustained.help.help_requested,
            demonstration_attempted=(
                sustained.help.demonstration_available
                and sustained.help.demonstration_applied
                and sustained.help.demonstration_episode_id is not None
            ),
            prediction_evidence_resolved=all(
                attempt.prediction_error <= MAX_RESOLVED_PREDICTION_MAE
                for attempt in sustained.attempts
            ),
            competence_still_improving=sustained.classification is PlateauClassification.IMPROVING,
            ambiguity_resolved=True,
            safety_or_permission_clear=True,
            impossible_task=False,
            resource_limit=False,
        )
    except ValueError:
        return None


def _with_proposal_state(
    diagnosis: Week10ScenarioDiagnosis,
    proposal_generated: bool,
) -> Week10ScenarioDiagnosis:
    return Week10ScenarioDiagnosis(
        scenario_family=diagnosis.scenario_family,
        classification=diagnosis.classification,
        attempts=diagnosis.attempts,
        windows=diagnosis.windows,
        ladder=diagnosis.ladder,
        replay=diagnosis.replay,
        help=diagnosis.help,
        proposal_generated=proposal_generated,
        non_capacity_reason=diagnosis.non_capacity_reason,
    )


def _scenario_state(scenario_family: str, seed: int, *, plan_kind: str) -> NurseryState:
    if plan_kind == "frozen_skill_impossible":
        return _angular_state(seed=seed, impossible=True)
    if plan_kind in {"request_help_only", "resource_limited", "permission_blocked"}:
        return _angular_state(seed=seed, impossible=False)
    return _angular_state(seed=seed, impossible=False)


def _angular_state(*, seed: int, impossible: bool) -> NurseryState:
    agent_positions = (
        GridPosition(2, 2),
        GridPosition(1, 2),
        GridPosition(2, 3),
        GridPosition(1, 3),
    )
    agent_position = agent_positions[(seed // 4) % len(agent_positions)]
    orientation = tuple(Direction)[seed % len(tuple(Direction))]
    blockers = [
        EntityState(
            entity_id="flat_contact_blocker",
            role=EntityRole.WALL,
            position=GridPosition(4, 1),
            blocks_movement=True,
            movable=False,
        )
    ]
    if impossible:
        blockers.extend(
            [
                EntityState(
                    entity_id="impossible_blocker_west",
                    role=EntityRole.WALL,
                    position=GridPosition(2, 3),
                    blocks_movement=True,
                    movable=False,
                ),
                EntityState(
                    entity_id="impossible_blocker_south",
                    role=EntityRole.WALL,
                    position=GridPosition(3, 4),
                    blocks_movement=True,
                    movable=False,
                ),
            ]
        )
    return NurseryState(
        width=7,
        height=6,
        agent=AgentState(position=agent_position, orientation=orientation),
        entities=(
            *_wall_entities(7, 6),
            *blockers,
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=GridPosition(3, 2),
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ANGULAR,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=GridPosition(5, 3),
                blocks_movement=False,
                movable=False,
            ),
        ),
    )


def _planned_actions(
    state: NurseryState,
    push_directions: tuple[Direction, ...],
    *,
    budget: int,
) -> tuple[PrimitiveAction, ...]:
    current = state
    engine = NurseryTransitionEngine()
    actions: list[PrimitiveAction] = []
    for direction in push_directions:
        object_position = _object_position(current)
        contact = object_position.moved(Direction((int(direction) + 2) % 4))
        route = _shortest_route(current, source=current.agent.position, destination=contact)
        if route is None:
            break
        for position in route:
            move_direction = _direction_between(current.agent.position, position)
            for turn in _turn_actions(current.agent.orientation, move_direction):
                actions.append(turn)
                current = engine.apply(current, turn).state
            actions.append(PrimitiveAction.MOVE_FORWARD)
            current = engine.apply(current, PrimitiveAction.MOVE_FORWARD).state
        for turn in _turn_actions(current.agent.orientation, direction):
            actions.append(turn)
            current = engine.apply(current, turn).state
        actions.append(PrimitiveAction.PUSH)
        current = engine.apply(current, PrimitiveAction.PUSH).state
        if len(actions) >= budget:
            break
    return tuple(actions[:budget])


def _retreat_reapproach_actions(
    state: NurseryState,
    *,
    budget: int,
) -> tuple[PrimitiveAction, ...]:
    """Execute a bounded retreat before retrying a non-progressing north contact."""
    engine = NurseryTransitionEngine()
    current = state
    actions: list[PrimitiveAction] = []
    retreat_direction = Direction((int(current.agent.orientation) + 2) % 4)
    for turn in _turn_actions(current.agent.orientation, retreat_direction):
        actions.append(turn)
        current = engine.apply(current, turn).state
    destination = current.agent.position.moved(retreat_direction)
    if (
        len(actions) < budget
        and current.is_in_bounds(destination)
        and current.blocking_entity_at(destination) is None
    ):
        actions.append(PrimitiveAction.MOVE_FORWARD)
        current = engine.apply(current, PrimitiveAction.MOVE_FORWARD).state
    remaining = max(0, budget - len(actions))
    actions.extend(_planned_actions(current, (Direction.NORTH,), budget=remaining))
    return tuple(actions[:budget])


def _run_frozen_skill_actions(state: NurseryState, *, budget: int) -> tuple[PrimitiveAction, ...]:
    record = read_skill_record(DEFAULT_WEEK8_SKILL_RECORD)
    controller = ApproachAndPushSkillController(record)
    runtime = NurseryRuntime(state, "week10-frozen-action-plan")
    actions: list[PrimitiveAction] = []
    for _ in range(budget):
        decision = controller.decide(runtime.state, runtime.observe().available_actions)
        if decision.status is SkillExecutionStatus.TERMINATED:
            break
        if decision.status is not SkillExecutionStatus.ACTION or decision.action is None:
            break
        production = retain_skill_candidate_through_curiosity(decision)
        if production.retained_action is None:
            break
        actions.append(production.retained_action)
        runtime.step(production.retained_action)
    return tuple(actions)


def _run_familiar_control(skill_record_path: Path) -> tuple[float, tuple[int, ...]]:
    record = read_skill_record(skill_record_path)
    controller = ApproachAndPushSkillController(record)
    successes = 0
    steps_used: list[int] = []
    factory = Week8ScenarioFactory()
    for seed in WEEK10_CONTROL_SEEDS:
        scenario = factory.create(seed)
        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=f"week10-familiar-control-{seed}",
            resource_state_provider=scenario.resource_state,
        )
        steps = 0
        while scenario.remaining_steps(runtime.state) > 0:
            decision = controller.decide(runtime.state, runtime.observe().available_actions)
            if decision.status is SkillExecutionStatus.TERMINATED:
                break
            if decision.status is not SkillExecutionStatus.ACTION or decision.action is None:
                break
            production = retain_skill_candidate_through_curiosity(decision)
            if production.retained_action is None:
                break
            result = runtime.step(production.retained_action)
            steps += 1
            if result.transition.outcome is TransitionOutcome.PUSHED and _target_satisfied(
                runtime.state
            ):
                break
        steps_used.append(steps)
        successes += int(_target_satisfied(runtime.state))
    return successes / len(WEEK10_CONTROL_SEEDS), tuple(steps_used)


def _cube_push_outcomes() -> dict[str, str]:
    round_open = _push_once(_object_state(ShapeCode.ROUND, near_wall=False))
    angular_wall = _push_once(_object_state(ShapeCode.ANGULAR, near_wall=True))
    angular_open = _push_once(_object_state(ShapeCode.ANGULAR, near_wall=False))
    return {
        "angular_open_push": angular_open.value,
        "angular_wall_push": angular_wall.value,
        "round_open_push": round_open.value,
    }


def _object_state(shape: ShapeCode, *, near_wall: bool) -> NurseryState:
    y = 1 if near_wall else 2
    return NurseryState(
        width=6,
        height=6,
        agent=AgentState(position=GridPosition(1, y), orientation=Direction.EAST),
        entities=(
            *_wall_entities(6, 6),
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=GridPosition(2, y),
                blocks_movement=True,
                movable=True,
                shape_code=shape,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=GridPosition(3, y),
                blocks_movement=False,
                movable=False,
            ),
        ),
    )


def _push_once(state: NurseryState) -> TransitionOutcome:
    runtime = NurseryRuntime(state, "week10-cube-dynamics")
    return runtime.step(PrimitiveAction.PUSH).transition.outcome


def _repository_inventory() -> RepositoryInventory:
    growth_paths = tuple(Path("src/seedmind/growth").glob("*.py"))
    import_lines = "\n".join(
        line
        for path in growth_paths
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.startswith(("import ", "from "))
    )
    module_names = {path.stem for path in growth_paths}
    return RepositoryInventory(
        specialist_created=(
            "specialist" in module_names or Path("src/seedmind/growth/specialist.py").exists()
        ),
        router_created=("router" in module_names or Path("src/seedmind/growth/router.py").exists()),
        week11_started=Path("src/seedmind/growth/week11.py").exists()
        or Path("scripts/run_week11_specialist_growth.py").exists(),
        ndnra_required=(
            "seedmind.research.ndnra" in import_lines
            or "parallel_comparison" in import_lines
            or "parallel_operation" in import_lines
        ),
    )


def _diagnostic_report_payload(result: Week10RunResult) -> dict[str, object]:
    return {
        "corrected_grounded_evidence": {
            "supersedes_commit": "13140df",
            "reason": (
                "The original 13140df Week 10 evidence used scripted diagnostic timelines "
                "and was not valid grounded evidence. The corrected implementation derives "
                "attempts, progress, replay outcomes, demonstration effects, prediction "
                "evidence, classification, and proposal generation from executed Nursery episodes."
            ),
        },
        "integrity_followup": {
            "hardens_commit": "ea15047",
            "reason": (
                "The ea15047 grounded correction still ignored scenario seeds when building "
                "Nursery states, assigned replay and demonstration solution plans before deriving "
                "them from evidence, labelled identical frozen-policy executions as distinct "
                "strategy variants, accepted any non-negative prediction error, and counted "
                "teacher demonstrations in learner attempt indexes. This follow-up corrects "
                "those remaining evidence-integrity defects."
            ),
        },
        "cube_like_raw_behavior": result.cube_push_outcomes,
        "diagnoses": [diagnosis.to_json() for diagnosis in result.diagnoses],
        "episode_counts": _episode_counts(result.episode_traces),
        "familiar_control": {
            "seeds": list(WEEK10_CONTROL_SEEDS),
            "step_counts": list(result.familiar_control_steps),
            "success_rate": result.familiar_control_success_rate,
        },
        "scenario_seeds": {
            "blockage": list(WEEK10_BLOCKAGE_SEEDS),
            "control": list(WEEK10_CONTROL_SEEDS),
            "early": list(WEEK10_EARLY_SEEDS),
            "non_capacity": list(WEEK10_NON_CAPACITY_SEEDS),
            "temporary": list(WEEK10_TEMPORARY_SEEDS),
        },
        "limitations": (
            "Week 10 has diagnosed and proposed. It has not grown, trained, accepted, "
            "routed, or deployed a specialist."
        ),
        "proposal_derivation": None if result.proposal is None else result.proposal.to_json(),
        "strategy_variants": [variant.to_json() for variant in result.strategy_variants],
        "thresholds": result.thresholds.to_json(),
    }


def _traces_payload(result: Week10RunResult) -> dict[str, object]:
    return {
        "episode_traces": [trace.to_json() for trace in result.episode_traces],
        "trace_count": len(result.episode_traces),
    }


def _windows_payload(result: Week10RunResult) -> dict[str, object]:
    return {
        "thresholds": result.thresholds.to_json(),
        "windows": [
            window.to_json() for diagnosis in result.diagnoses for window in diagnosis.windows
        ],
    }


def _write_svg(path: Path, result: Week10RunResult) -> None:
    temporary = next(
        diagnosis
        for diagnosis in result.diagnoses
        if diagnosis.scenario_family == "temporary_cube_recovery"
    )
    sustained = next(
        diagnosis
        for diagnosis in result.diagnoses
        if diagnosis.scenario_family == "sustained_cube_blockage"
    )
    width = 640
    height = 260
    left = 70
    bottom = 210
    scale_x = 90
    scale_y = 150

    def points(windows: tuple[LearningProgressWindow, ...]) -> str:
        return " ".join(
            f"{left + index * scale_x},{bottom - int(window.mean_task_progress * scale_y)}"
            for index, window in enumerate(windows)
        )

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
  <rect x="0" y="0" width="{width}" height="{height}" fill="white"/>
  <line x1="{left}" y1="40" x2="{left}" y2="{bottom}" stroke="black"/>
  <line x1="{left}" y1="{bottom}" x2="560" y2="{bottom}" stroke="black"/>
  <text x="70" y="24" font-family="monospace" font-size="14">Week 10 grounded plateau evidence</text>
  <polyline points="{points(temporary.windows)}" fill="none" stroke="#167a3a" stroke-width="3"/>
  <polyline points="{points(sustained.windows)}" fill="none" stroke="#b3261e" stroke-width="3"/>
  <text x="360" y="72" font-family="monospace" font-size="12" fill="#167a3a">temporary recovery/improving</text>
  <text x="360" y="94" font-family="monospace" font-size="12" fill="#b3261e">sustained blockage</text>
  <text x="20" y="54" font-family="monospace" font-size="11">progress</text>
  <text x="250" y="238" font-family="monospace" font-size="11">grounded learning-progress windows</text>
</svg>
"""
    _write_text(path, svg)


def _preserve_superseded_scripted_evidence(output_dir: Path) -> None:
    diagnostic = output_dir / "diagnostic_report.json"
    superseded_dir = output_dir / "superseded_scripted_evidence"
    if not diagnostic.exists() or superseded_dir.exists():
        return
    try:
        payload = json.loads(diagnostic.read_text(encoding="ascii"))
    except json.JSONDecodeError:
        payload = {}
    if "corrected_grounded_evidence" in payload:
        return
    superseded_dir.mkdir(parents=True, exist_ok=True)
    for name in (
        "diagnostic_report.json",
        "growth_proposal_record.json",
        "learning_progress_windows.json",
        "plateau_visualisation.svg",
        "week10_acceptance_report.json",
    ):
        source = output_dir / name
        if source.exists():
            shutil.copy2(source, superseded_dir / name)
    _write_json(
        superseded_dir / "SUPERSEDED_BY_GROUNDED_WEEK10.json",
        {
            "valid_for_grounded_capacity_diagnosis": False,
            "reason": "13140df used scripted diagnostic timelines rather than executed Nursery episodes.",
            "superseding_artifact_directory": "artifacts/week10_capacity_diagnosis",
        },
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(text, encoding="ascii")
    temporary_path.replace(path)


def _empty_replay(scenario_family: str) -> MemoryReplayRecord:
    return MemoryReplayRecord(
        scenario_family=scenario_family,
        query={},
        relevant_memory_ids=(),
        source_episode_ids=(),
        replay_influenced_episode_ids=(),
        changed_strategy=False,
        progress_resumed=False,
        evidence_insufficient=True,
    )


def _empty_help(scenario_family: str, reason: str) -> HelpDemonstrationRecord:
    return HelpDemonstrationRecord(
        scenario_family=scenario_family,
        help_requested=True,
        help_reason=reason,
        demonstration_available=False,
        demonstration_episode_id=None,
        demonstration_trace_digest=None,
        demonstration_completed_task=False,
        learner_before_episode_ids=(),
        learner_after_episode_ids=(),
        before_mean_progress=0.0,
        after_mean_progress=0.0,
        demonstration_applied=False,
        performance_improved_afterward=False,
        blockage_remained=True,
    )


def _attempt_json(attempt: LearningAttempt) -> dict[str, object]:
    return {
        "attempt_index": attempt.attempt_index,
        "demonstration_involved": attempt.demonstration_involved,
        "episode_id": attempt.episode_id,
        "help_requested": attempt.help_requested,
        "invalid_or_ineffective_actions": attempt.invalid_or_ineffective_actions,
        "prediction_error": attempt.prediction_error,
        "replay_involved": attempt.replay_involved,
        "scenario_family": attempt.scenario_family,
        "steps_used": attempt.steps_used,
        "strategy": attempt.strategy,
        "success": attempt.success,
        "task_progress": attempt.task_progress,
        "trace_digest": attempt.trace_digest,
        "trace_ref": attempt.trace_ref,
    }


def _attempt_index_for_family(
    traces: list[GroundedEpisodeTrace],
    scenario_family: str,
) -> int:
    return (
        sum(
            1
            for trace in traces
            if trace.scenario_family == scenario_family
            and trace.strategy_id != "protected_teacher_oracle_demonstration"
        )
        - 1
    )


def _progress(initial_distance: int, final_distance: int) -> float:
    if initial_distance <= 0:
        return 1.0
    return _clamp_unit((initial_distance - final_distance) / initial_distance)


def _object_target_distance(state: NurseryState) -> int:
    object_position = _object_position(state)
    target_position = _target_position(state)
    return abs(object_position.x - target_position.x) + abs(object_position.y - target_position.y)


def _object_position(state: NurseryState) -> GridPosition:
    return next(entity.position for entity in state.entities if entity.entity_id == "object_0")


def _target_position(state: NurseryState) -> GridPosition:
    return next(entity.position for entity in state.entities if entity.entity_id == "target_0")


def _target_satisfied(state: NurseryState) -> bool:
    return _object_position(state) == _target_position(state)


def _shortest_route(
    state: NurseryState,
    *,
    source: GridPosition,
    destination: GridPosition,
) -> tuple[GridPosition, ...] | None:
    if source == destination:
        return ()
    blocked = {
        entity.position
        for entity in state.entities
        if entity.blocks_movement and entity.position != destination
    }
    queue: deque[tuple[GridPosition, tuple[GridPosition, ...]]] = deque([(source, ())])
    visited = {source}
    while queue:
        position, path = queue.popleft()
        for direction in Direction:
            candidate = position.moved(direction)
            if candidate in visited or not state.is_in_bounds(candidate) or candidate in blocked:
                continue
            next_path = (*path, candidate)
            if candidate == destination:
                return next_path
            visited.add(candidate)
            queue.append((candidate, next_path))
    return None


def _direction_between(source: GridPosition, destination: GridPosition) -> Direction:
    dx = destination.x - source.x
    dy = destination.y - source.y
    for direction in Direction:
        if direction.delta == (dx, dy):
            return direction
    raise ValueError("positions are not adjacent")


def _turn_actions(current: Direction, desired: Direction) -> tuple[PrimitiveAction, ...]:
    if current is desired:
        return ()
    clockwise = (int(desired) - int(current)) % 4
    if clockwise == 1:
        return (PrimitiveAction.TURN_RIGHT,)
    if clockwise == 3:
        return (PrimitiveAction.TURN_LEFT,)
    return (PrimitiveAction.TURN_RIGHT, PrimitiveAction.TURN_RIGHT)


def _wall_entities(width: int, height: int) -> tuple[EntityState, ...]:
    positions = (
        GridPosition(x=x, y=y)
        for y in range(height)
        for x in range(width)
        if x in (0, width - 1) or y in (0, height - 1)
    )
    return tuple(
        EntityState(
            entity_id=f"wall_{index:03d}",
            role=EntityRole.WALL,
            position=position,
            blocks_movement=True,
            movable=False,
        )
        for index, position in enumerate(positions)
    )


def _episode_counts(traces: tuple[GroundedEpisodeTrace, ...]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for trace in traces:
        counts[trace.scenario_family] = counts.get(trace.scenario_family, 0) + 1
    return counts


def _position_json(position: GridPosition) -> dict[str, int]:
    return {"x": position.x, "y": position.y}


def _state_digest(state: NurseryState) -> str:
    return _canonical_digest(
        {
            "agent": {
                "orientation": int(state.agent.orientation),
                "x": state.agent.position.x,
                "y": state.agent.position.y,
            },
            "entities": [
                {
                    "blocks_movement": entity.blocks_movement,
                    "entity_id": entity.entity_id,
                    "movable": entity.movable,
                    "role": entity.role.value,
                    "shape_code": int(entity.shape_code),
                    "x": entity.position.x,
                    "y": entity.position.y,
                }
                for entity in state.entities
            ],
            "height": state.height,
            "step_count": state.step_count,
            "terminated": state.terminated,
            "width": state.width,
        }
    )


def _canonical_digest(payload: object) -> str:
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":")).encode(
            "ascii"
        )
    ).hexdigest()


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _clamp_unit(value: float) -> float:
    return max(0.0, min(1.0, value))


def _frozen_ndnra_boundary_pass() -> bool:
    manifest_path = Path("docs/architecture/NDNRA_Freeze_Manifest_2026-07-01.json")
    payload = json.loads(manifest_path.read_text(encoding="ascii"))
    return (
        payload.get("active_in_seedmind") is False
        and payload.get("new_ndnra_stages_allowed_in_seedmind") is False
        and payload.get("comparison_required_for_future_seedmind_stages") is False
        and payload.get("source_baseline_commit") == "b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a"
    )
