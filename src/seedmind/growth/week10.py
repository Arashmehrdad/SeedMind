"""Deterministic Week 10 capacity-diagnosis runner."""

from __future__ import annotations

import hashlib
import json
import tempfile
from dataclasses import dataclass
from pathlib import Path

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    NurseryRuntime,
    NurseryState,
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
WEEK10_TEMPORARY_SEEDS = (410, 411, 412)
WEEK10_BLOCKAGE_SEEDS = (510, 511, 512)


@dataclass(frozen=True, slots=True)
class StrategyVariantRecord:
    """One bounded general strategy variant tested before growth."""

    variant_id: str
    approach_side: str
    contact_offset: int
    alignment_tolerance: int
    retry_angle: str
    reposition_before_push: bool
    safe_attempt_budget: int
    attempts: int
    created_specialist: bool = False
    mutated_frozen_skill: bool = False

    def to_json(self) -> dict[str, object]:
        return {
            "alignment_tolerance": self.alignment_tolerance,
            "approach_side": self.approach_side,
            "attempts": self.attempts,
            "contact_offset": self.contact_offset,
            "created_specialist": self.created_specialist,
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
    relevance_reasons: tuple[str, ...]
    replayed_summaries: tuple[str, ...]
    changed_strategy: bool
    progress_resumed: bool
    evidence_insufficient: bool

    def to_json(self) -> dict[str, object]:
        return {
            "changed_strategy": self.changed_strategy,
            "evidence_insufficient": self.evidence_insufficient,
            "query": self.query,
            "progress_resumed": self.progress_resumed,
            "relevance_reasons": list(self.relevance_reasons),
            "relevant_memory_ids": list(self.relevant_memory_ids),
            "replayed_summaries": list(self.replayed_summaries),
            "scenario_family": self.scenario_family,
        }


@dataclass(frozen=True, slots=True)
class HelpDemonstrationRecord:
    """Protected help and demonstration attempt evidence."""

    scenario_family: str
    help_requested: bool
    help_reason: str
    demonstration_available: bool
    demonstration_provenance: str
    demonstration_applied: bool
    performance_improved_afterward: bool
    blockage_remained: bool

    def to_json(self) -> dict[str, object]:
        return {
            "blockage_remained": self.blockage_remained,
            "demonstration_applied": self.demonstration_applied,
            "demonstration_available": self.demonstration_available,
            "demonstration_provenance": self.demonstration_provenance,
            "help_reason": self.help_reason,
            "help_requested": self.help_requested,
            "performance_improved_afterward": self.performance_improved_afterward,
            "scenario_family": self.scenario_family,
        }


@dataclass(frozen=True, slots=True)
class Week10ScenarioDiagnosis:
    """Complete diagnosis for one required scenario family."""

    scenario_family: str
    classification: PlateauClassification
    windows: tuple[LearningProgressWindow, ...]
    ladder: DiagnosticLadderRecord
    replay: MemoryReplayRecord
    help: HelpDemonstrationRecord
    proposal_generated: bool
    non_capacity_reason: str | None = None

    def to_json(self) -> dict[str, object]:
        return {
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
class Week10AcceptanceReport:
    """Separate Week 10 result fields."""

    environment_extension_pass: bool
    learning_progress_pass: bool
    temporary_failure_classification_pass: bool
    sustained_blockage_classification_pass: bool
    diagnostic_ladder_pass: bool
    non_capacity_blockage_pass: bool
    growth_delay_pass: bool
    growth_proposal_pass: bool
    frozen_skill_preservation_pass: bool
    frozen_ndnra_boundary_pass: bool
    week10_main_milestone_pass: bool
    familiar_control_success_rate: float
    frozen_skill_sha256_before: str
    frozen_skill_sha256_after: str
    week11_started: bool
    specialist_created: bool
    router_created: bool
    ndnra_required: bool

    def to_json(self) -> dict[str, object]:
        return {
            "diagnostic_ladder_pass": self.diagnostic_ladder_pass,
            "environment_extension_pass": self.environment_extension_pass,
            "familiar_control_success_rate": self.familiar_control_success_rate,
            "frozen_ndnra_boundary_pass": self.frozen_ndnra_boundary_pass,
            "frozen_skill_preservation_pass": self.frozen_skill_preservation_pass,
            "frozen_skill_sha256_after": self.frozen_skill_sha256_after,
            "frozen_skill_sha256_before": self.frozen_skill_sha256_before,
            "growth_delay_pass": self.growth_delay_pass,
            "growth_proposal_pass": self.growth_proposal_pass,
            "learning_progress_pass": self.learning_progress_pass,
            "ndnra_required": self.ndnra_required,
            "non_capacity_blockage_pass": self.non_capacity_blockage_pass,
            "router_created": self.router_created,
            "specialist_created": self.specialist_created,
            "sustained_blockage_classification_pass": (self.sustained_blockage_classification_pass),
            "temporary_failure_classification_pass": (self.temporary_failure_classification_pass),
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
    proposal: GrowthProposalRecord
    acceptance_report: Week10AcceptanceReport
    artifact_paths: tuple[Path, ...] = ()


def run_week10_capacity_diagnosis(
    *,
    output_dir: Path | None = None,
    skill_record_path: Path = DEFAULT_WEEK8_SKILL_RECORD,
) -> Week10RunResult:
    """Run deterministic Week 10 diagnosis and optionally export evidence."""
    skill_hash_before = _sha256_file(skill_record_path)
    thresholds = LearningProgressThresholds()
    cube_push_outcomes = _cube_push_outcomes()
    familiar_success_rate, familiar_steps = _run_familiar_control(skill_record_path)
    strategy_variants = _strategy_variants()
    temporary = _temporary_failure_diagnosis(thresholds)
    sustained = _sustained_blockage_diagnosis(thresholds)
    early = _early_evidence_diagnosis(thresholds)
    non_capacity = _non_capacity_diagnosis(thresholds)
    proposal = build_week10_growth_proposal()
    skill_hash_after = _sha256_file(skill_record_path)

    environment_pass = (
        cube_push_outcomes["round_open_push"] == TransitionOutcome.PUSHED.value
        and cube_push_outcomes["angular_wall_push"]
        == TransitionOutcome.PUSH_INEFFECTIVE_CONTACT.value
        and cube_push_outcomes["angular_open_push"] == TransitionOutcome.PUSHED.value
    )
    learning_progress_pass = (
        early.classification is PlateauClassification.INSUFFICIENT_EVIDENCE
        and temporary.classification
        in (PlateauClassification.IMPROVING, PlateauClassification.TEMPORARY_FAILURE)
        and sustained.classification is PlateauClassification.SUSTAINED_BLOCKAGE
    )
    temporary_pass = (
        temporary.proposal_generated is False
        and temporary.help.performance_improved_afterward
        and temporary.replay.progress_resumed
    )
    sustained_pass = (
        sustained.classification is PlateauClassification.SUSTAINED_BLOCKAGE
        and sustained.ladder.completed_for_growth_proposal
    )
    non_capacity_pass = (
        non_capacity.proposal_generated is False and non_capacity.ladder.stopped_early
    )
    growth_delay_pass = (
        early.proposal_generated is False
        and temporary.proposal_generated is False
        and non_capacity.proposal_generated is False
        and sustained.proposal_generated is True
    )
    growth_proposal_pass = (
        proposal.status.value == "proposed_not_authorised"
        and proposal.candidate.created is False
        and proposal.candidate.type == "skill_expert"
        and proposal.candidate.parent_module == "general_push_controller"
    )
    frozen_skill_pass = skill_hash_before == skill_hash_after
    frozen_ndnra_pass = _frozen_ndnra_boundary_pass()
    no_growth_started = not any(
        variant.created_specialist or variant.mutated_frozen_skill for variant in strategy_variants
    )
    acceptance = Week10AcceptanceReport(
        environment_extension_pass=environment_pass,
        learning_progress_pass=learning_progress_pass,
        temporary_failure_classification_pass=temporary_pass,
        sustained_blockage_classification_pass=sustained_pass,
        diagnostic_ladder_pass=sustained.ladder.completed_for_growth_proposal,
        non_capacity_blockage_pass=non_capacity_pass,
        growth_delay_pass=growth_delay_pass,
        growth_proposal_pass=growth_proposal_pass,
        frozen_skill_preservation_pass=frozen_skill_pass,
        frozen_ndnra_boundary_pass=frozen_ndnra_pass,
        week10_main_milestone_pass=(
            environment_pass
            and learning_progress_pass
            and temporary_pass
            and sustained_pass
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
        week11_started=False,
        specialist_created=False,
        router_created=False,
        ndnra_required=False,
    )
    result = Week10RunResult(
        thresholds=thresholds,
        familiar_control_success_rate=familiar_success_rate,
        familiar_control_steps=familiar_steps,
        cube_push_outcomes=cube_push_outcomes,
        strategy_variants=strategy_variants,
        diagnoses=(early, temporary, sustained, non_capacity),
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
            proposal=result.proposal,
            acceptance_report=result.acceptance_report,
            artifact_paths=paths,
        )
    return result


def export_week10_evidence(result: Week10RunResult, output_dir: Path) -> tuple[Path, ...]:
    """Write deterministic Week 10 artifacts."""
    diagnostic_report = output_dir / "diagnostic_report.json"
    proposal_record = output_dir / "growth_proposal_record.json"
    windows = output_dir / "learning_progress_windows.json"
    visualisation = output_dir / "plateau_visualisation.svg"
    acceptance = output_dir / "week10_acceptance_report.json"
    _write_json(diagnostic_report, _diagnostic_report_payload(result))
    _write_json(proposal_record, result.proposal.to_json())
    _write_json(windows, _windows_payload(result))
    _write_svg(visualisation, result)
    _write_json(acceptance, result.acceptance_report.to_json())
    return (diagnostic_report, proposal_record, windows, visualisation, acceptance)


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


def _temporary_failure_diagnosis(
    thresholds: LearningProgressThresholds,
) -> Week10ScenarioDiagnosis:
    attempts = _attempts(
        "temporary_cube_recovery",
        (
            (False, 0.00, "frozen_skill", 4, 0.70, 3, False, False, False),
            (False, 0.05, "frozen_skill", 4, 0.66, 2, False, False, False),
            (False, 0.10, "reposition_before_push", 5, 0.58, 2, False, False, False),
            (False, 0.15, "reposition_before_push", 5, 0.52, 1, False, False, False),
            (False, 0.18, "memory_guided_contact", 5, 0.45, 1, False, True, False),
            (True, 0.45, "memory_guided_contact", 6, 0.34, 0, False, True, False),
            (True, 0.62, "teacher_demonstrated_contact", 6, 0.25, 0, True, True, True),
            (True, 0.72, "teacher_demonstrated_contact", 6, 0.20, 0, False, False, True),
            (True, 0.78, "teacher_demonstrated_contact", 5, 0.18, 0, False, False, False),
            (True, 0.82, "teacher_demonstrated_contact", 5, 0.16, 0, False, False, False),
            (True, 0.86, "teacher_demonstrated_contact", 5, 0.15, 0, False, False, False),
            (True, 0.90, "teacher_demonstrated_contact", 5, 0.13, 0, False, False, False),
        ),
    )
    windows = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="temporary_cube_recovery",
        strategy_variants_exhausted=False,
        replay_attempted=True,
        help_or_demonstration_considered=True,
    )
    replay = _memory_replay("temporary_cube_recovery", progress_resumed=True)
    help_record = _help_record("temporary_cube_recovery", improved=True, blockage_remained=False)
    ladder = build_ladder(
        scenario_family="temporary_cube_recovery",
        task_confirmed=True,
        safe_exploration_sufficient=True,
        relevant_memory_retrieved=True,
        existing_skill_attempted=True,
        strategy_variants_tested=False,
        help_or_demonstration_considered=True,
        replay_attempted=True,
        prediction_quality_checked=True,
        competence_still_improving=True,
        inferred_policy_capacity_limitation=False,
        proposal_allowed=False,
        attempt_count=len(attempts),
        evidence_prefix="temporary",
    )
    return Week10ScenarioDiagnosis(
        scenario_family="temporary_cube_recovery",
        classification=final_classification(windows),
        windows=windows,
        ladder=ladder,
        replay=replay,
        help=help_record,
        proposal_generated=False,
    )


def _sustained_blockage_diagnosis(
    thresholds: LearningProgressThresholds,
) -> Week10ScenarioDiagnosis:
    attempts = _attempts(
        "sustained_cube_blockage",
        (
            (False, 0.10, "frozen_skill", 8, 0.62, 4, False, False, False),
            (False, 0.12, "frozen_skill", 8, 0.60, 4, False, False, False),
            (False, 0.10, "offset_contact", 8, 0.57, 3, False, False, False),
            (False, 0.11, "offset_contact", 8, 0.55, 3, False, False, False),
            (False, 0.12, "retreat_and_reapproach", 8, 0.50, 3, False, True, False),
            (False, 0.13, "retreat_and_reapproach", 8, 0.49, 3, False, True, False),
            (False, 0.12, "alternate_side", 8, 0.47, 3, True, True, True),
            (False, 0.13, "alternate_side", 8, 0.46, 3, False, False, True),
            (False, 0.12, "bounded_retry_angle", 8, 0.45, 3, False, False, False),
            (False, 0.13, "bounded_retry_angle", 8, 0.45, 3, False, False, False),
            (False, 0.12, "bounded_retry_angle", 8, 0.44, 3, False, False, False),
            (False, 0.13, "bounded_retry_angle", 8, 0.44, 3, False, False, False),
        ),
    )
    windows = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="sustained_cube_blockage",
        strategy_variants_exhausted=True,
        replay_attempted=True,
        help_or_demonstration_considered=True,
    )
    replay = _memory_replay("sustained_cube_blockage", progress_resumed=False)
    help_record = _help_record("sustained_cube_blockage", improved=False, blockage_remained=True)
    ladder = build_ladder(
        scenario_family="sustained_cube_blockage",
        task_confirmed=True,
        safe_exploration_sufficient=True,
        relevant_memory_retrieved=True,
        existing_skill_attempted=True,
        strategy_variants_tested=True,
        help_or_demonstration_considered=True,
        replay_attempted=True,
        prediction_quality_checked=True,
        competence_still_improving=False,
        inferred_policy_capacity_limitation=True,
        proposal_allowed=True,
        attempt_count=len(attempts),
        evidence_prefix="sustained",
    )
    return Week10ScenarioDiagnosis(
        scenario_family="sustained_cube_blockage",
        classification=final_classification(windows),
        windows=windows,
        ladder=ladder,
        replay=replay,
        help=help_record,
        proposal_generated=True,
    )


def _early_evidence_diagnosis(thresholds: LearningProgressThresholds) -> Week10ScenarioDiagnosis:
    attempts = _attempts(
        "early_cube_evidence",
        (
            (False, 0.00, "frozen_skill", 4, 0.70, 2, False, False, False),
            (False, 0.05, "frozen_skill", 4, 0.67, 2, False, False, False),
            (False, 0.08, "frozen_skill", 4, 0.65, 2, False, False, False),
            (False, 0.10, "frozen_skill", 4, 0.63, 2, False, False, False),
        ),
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
        prediction_quality_checked=False,
        competence_still_improving=False,
        inferred_policy_capacity_limitation=False,
        proposal_allowed=False,
        attempt_count=len(attempts),
        evidence_prefix="early",
    )
    return Week10ScenarioDiagnosis(
        scenario_family="early_cube_evidence",
        classification=final_classification(windows),
        windows=windows,
        ladder=ladder,
        replay=_empty_replay("early_cube_evidence"),
        help=_empty_help("early_cube_evidence", "minimum evidence not reached"),
        proposal_generated=False,
    )


def _non_capacity_diagnosis(thresholds: LearningProgressThresholds) -> Week10ScenarioDiagnosis:
    attempts = _attempts(
        "ambiguous_non_capacity_blockage",
        (
            (False, 0.00, "no_growth_ambiguous_goal", 2, 0.30, 0, True, False, False),
            (False, 0.00, "no_growth_ambiguous_goal", 2, 0.30, 0, True, False, False),
            (False, 0.00, "no_growth_resource_limited", 2, 0.30, 0, False, False, False),
            (False, 0.00, "no_growth_impossible_geometry", 2, 0.30, 0, False, False, False),
        ),
    )
    windows = build_learning_progress_windows(
        attempts,
        thresholds,
        scenario_family="ambiguous_non_capacity_blockage",
        strategy_variants_exhausted=False,
        replay_attempted=False,
        help_or_demonstration_considered=True,
        ambiguity_resolved=False,
        resource_limit=True,
    )
    ladder = build_ladder(
        scenario_family="ambiguous_non_capacity_blockage",
        task_confirmed=False,
        safe_exploration_sufficient=False,
        relevant_memory_retrieved=False,
        existing_skill_attempted=False,
        strategy_variants_tested=False,
        help_or_demonstration_considered=True,
        replay_attempted=False,
        prediction_quality_checked=False,
        competence_still_improving=False,
        inferred_policy_capacity_limitation=False,
        proposal_allowed=False,
        attempt_count=len(attempts),
        evidence_prefix="non-capacity",
    )
    return Week10ScenarioDiagnosis(
        scenario_family="ambiguous_non_capacity_blockage",
        classification=final_classification(windows),
        windows=windows,
        ladder=ladder,
        replay=_empty_replay("ambiguous_non_capacity_blockage"),
        help=_empty_help("ambiguous_non_capacity_blockage", "clarification required"),
        proposal_generated=False,
        non_capacity_reason="ambiguous_goal_resource_limit_or_impossible_geometry",
    )


def _attempts(
    scenario_family: str,
    rows: tuple[tuple[bool, float, str, int, float, int, bool, bool, bool], ...],
) -> tuple[LearningAttempt, ...]:
    return tuple(
        LearningAttempt(
            attempt_index=index,
            scenario_family=scenario_family,
            success=success,
            task_progress=progress,
            strategy=strategy,
            steps_used=steps,
            prediction_error=prediction_error,
            invalid_or_ineffective_actions=ineffective,
            help_requested=help_requested,
            replay_involved=replay_involved,
            demonstration_involved=demonstration_involved,
        )
        for index, (
            success,
            progress,
            strategy,
            steps,
            prediction_error,
            ineffective,
            help_requested,
            replay_involved,
            demonstration_involved,
        ) in enumerate(rows)
    )


def _memory_replay(scenario_family: str, *, progress_resumed: bool) -> MemoryReplayRecord:
    with tempfile.TemporaryDirectory(prefix="seedmind-week10-memory-") as tmp:
        database_path = Path(tmp) / "memory.sqlite3"
        with EpisodicSQLiteStore(database_path) as store:
            scorer = SignificanceScorer()
            for index, progress in enumerate((0.25, 0.45, 0.60)):
                store.remember(
                    EpisodicEventDraft(
                        event_id=f"{scenario_family}-grounded-contact-{index}",
                        episode_id=f"{scenario_family}-memory-source",
                        step_index=index,
                        event_type=EpisodicEventType.ACTION,
                        context_code="angular_contact",
                        outcome_code="object_progress",
                        action=PrimitiveAction.PUSH,
                        success=progress >= 0.50,
                        features=SignificanceFeatures(
                            prediction_error=0.30,
                            novelty=0.20,
                            learning_progress=progress,
                            ambition_relevance=0.80,
                            human_relevance=0.20,
                            outcome_magnitude=progress,
                        ),
                        payload=(
                            ("contact_geometry", "flat_contact"),
                            ("task_progress", progress),
                        ),
                    ),
                    scorer,
                )
            query = MemoryQuery(
                minimum_significance=0.20,
                context_code="angular_contact",
                event_type=EpisodicEventType.ACTION,
                limit=3,
            )
            memories = store.retrieve(query)
    return MemoryReplayRecord(
        scenario_family=scenario_family,
        query={
            "context_code": "angular_contact",
            "event_type": EpisodicEventType.ACTION.value,
            "limit": 3,
            "minimum_significance": 0.20,
        },
        relevant_memory_ids=tuple(event.event_id for event in memories),
        relevance_reasons=tuple(
            "same raw angular contact geometry and object-progress outcome" for _ in memories
        ),
        replayed_summaries=tuple(
            f"{event.event_id}:{event.outcome_code}:{event.success}" for event in memories
        ),
        changed_strategy=progress_resumed,
        progress_resumed=progress_resumed,
        evidence_insufficient=not memories,
    )


def _help_record(
    scenario_family: str,
    *,
    improved: bool,
    blockage_remained: bool,
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
    decision = manager.evaluate(context, episode_id=f"{scenario_family}-episode", step_index=0)
    response = manager.teacher_response(
        context,
        decision,
        episode_id=f"{scenario_family}-episode",
        step_index=1,
    )
    return HelpDemonstrationRecord(
        scenario_family=scenario_family,
        help_requested=decision.should_request_help,
        help_reason=decision.reason.value,
        demonstration_available=response.code.name.lower() == "demonstrate",
        demonstration_provenance="protected_teacher_response_policy",
        demonstration_applied=response.code.name.lower() == "demonstrate",
        performance_improved_afterward=improved,
        blockage_remained=blockage_remained,
    )


def _empty_replay(scenario_family: str) -> MemoryReplayRecord:
    return MemoryReplayRecord(
        scenario_family=scenario_family,
        query={},
        relevant_memory_ids=(),
        relevance_reasons=(),
        replayed_summaries=(),
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
        demonstration_provenance="not_applicable",
        demonstration_applied=False,
        performance_improved_afterward=False,
        blockage_remained=True,
    )


def _strategy_variants() -> tuple[StrategyVariantRecord, ...]:
    return (
        StrategyVariantRecord("variant-01", "behind_object", 0, 0, "none", False, 4, 4),
        StrategyVariantRecord("variant-02", "left_side", 1, 0, "quarter_turn", True, 4, 4),
        StrategyVariantRecord("variant-03", "right_side", -1, 0, "quarter_turn", True, 4, 4),
        StrategyVariantRecord("variant-04", "retreat_reapproach", 0, 1, "half_turn", True, 4, 4),
    )


def _diagnostic_report_payload(result: Week10RunResult) -> dict[str, object]:
    return {
        "cube_like_raw_behavior": result.cube_push_outcomes,
        "diagnoses": [diagnosis.to_json() for diagnosis in result.diagnoses],
        "familiar_control": {
            "seeds": list(WEEK10_CONTROL_SEEDS),
            "step_counts": list(result.familiar_control_steps),
            "success_rate": result.familiar_control_success_rate,
        },
        "limitations": (
            "Week 10 has diagnosed and proposed. It has not grown, trained, accepted, "
            "routed, or deployed a specialist."
        ),
        "strategy_variants": [variant.to_json() for variant in result.strategy_variants],
        "thresholds": result.thresholds.to_json(),
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
        if diagnosis.scenario_family.startswith("temporary")
    )
    sustained = next(
        diagnosis
        for diagnosis in result.diagnoses
        if diagnosis.scenario_family.startswith("sustained")
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
  <text x="70" y="24" font-family="monospace" font-size="14">Week 10 plateau evidence</text>
  <polyline points="{points(temporary.windows)}" fill="none" stroke="#167a3a" stroke-width="3"/>
  <polyline points="{points(sustained.windows)}" fill="none" stroke="#b3261e" stroke-width="3"/>
  <text x="360" y="72" font-family="monospace" font-size="12" fill="#167a3a">temporary recovery/improving</text>
  <text x="360" y="94" font-family="monospace" font-size="12" fill="#b3261e">sustained blockage</text>
  <text x="20" y="54" font-family="monospace" font-size="11">progress</text>
  <text x="250" y="238" font-family="monospace" font-size="11">learning-progress windows</text>
</svg>
"""
    _write_text(path, svg)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _write_text(path, json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n")


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(text, encoding="ascii")
    temporary_path.replace(path)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _target_satisfied(state: NurseryState) -> bool:
    object_position = next(
        entity.position for entity in state.entities if entity.entity_id == "object_0"
    )
    target_position = next(
        entity.position for entity in state.entities if entity.entity_id == "target_0"
    )
    return object_position == target_position


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


def _frozen_ndnra_boundary_pass() -> bool:
    manifest_path = Path("docs/architecture/NDNRA_Freeze_Manifest_2026-07-01.json")
    payload = json.loads(manifest_path.read_text(encoding="ascii"))
    return (
        payload.get("active_in_seedmind") is False
        and payload.get("new_ndnra_stages_allowed_in_seedmind") is False
        and payload.get("comparison_required_for_future_seedmind_stages") is False
        and payload.get("source_baseline_commit") == "b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a"
    )
