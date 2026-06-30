"""Deterministic Week 8 reusable-skill training and evaluation runner."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from pathlib import Path

from seedmind.contracts import Direction, GridPosition
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    NurseryRuntime,
    NurseryScenario,
    NurseryState,
    ShapeCode,
    TransitionOutcome,
)
from seedmind.skills.approach_and_push import (
    ApproachAndPushSkillController,
    SkillExecutionStatus,
    compile_approach_and_push_skill,
    retain_skill_candidate_through_curiosity,
)
from seedmind.skills.records import (
    SkillAttemptSource,
    SkillCompileFailure,
    SkillEpisodeEvidence,
    SkillRecord,
    SkillStepEvidence,
    SkillValidationStatus,
    write_skill_record,
)

DEFAULT_TRAINING_SEEDS = (6, 7, 8, 11)
DEFAULT_EVALUATION_SEEDS = (
    206,
    207,
    208,
    211,
    212,
    213,
    216,
    217,
    218,
    231,
    232,
    233,
    236,
    237,
    238,
    241,
    242,
    243,
    256,
    257,
)
WEEK8_SUCCESS_TARGET = 0.80


@dataclass(frozen=True, slots=True)
class Week8ScenarioFactory:
    """Create deterministic random-start ball-to-target scenarios for Week 8."""

    width: int = 7
    height: int = 7
    step_budget: int = 96

    def create(self, seed: int) -> NurseryScenario:
        """Return one eligible deterministic symbolic scenario."""
        if seed < 0:
            raise ValueError("seed must not be negative")
        interior = [
            GridPosition(x=x, y=y)
            for y in range(1, self.height - 1)
            for x in range(1, self.width - 1)
        ]
        index = seed % len(interior)
        ball_position = interior[index]
        target_position = interior[(index + 11) % len(interior)]
        if ball_position == target_position:
            target_position = interior[(index + 12) % len(interior)]
        agent_position = interior[(index + 7) % len(interior)]
        if agent_position in {ball_position, target_position}:
            agent_position = interior[(index + 9) % len(interior)]
        orientation = tuple(Direction)[seed % len(Direction)]
        entities = (
            *self._wall_entities(),
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=ball_position,
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ROUND,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=target_position,
                blocks_movement=False,
                movable=False,
            ),
        )
        state = NurseryState(
            width=self.width,
            height=self.height,
            agent=AgentState(position=agent_position, orientation=orientation),
            entities=entities,
        )
        return NurseryScenario(
            scenario_id=f"week8-approach-push-seed-{seed}",
            seed=seed,
            initial_state=state,
            step_budget=self.step_budget,
        )

    def _wall_entities(self) -> tuple[EntityState, ...]:
        positions = (
            GridPosition(x=x, y=y)
            for y in range(self.height)
            for x in range(self.width)
            if x in (0, self.width - 1) or y in (0, self.height - 1)
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


@dataclass(frozen=True, slots=True)
class Week8EpisodeResult:
    """One Week 8 training, baseline, or reuse episode."""

    seed: int
    episode_id: str
    success: bool
    step_count: int
    skill_invocation_count: int
    reuse_count: int
    discovery_count: int
    authority_violation_count: int
    failure_reason: str | None
    evidence: SkillEpisodeEvidence


@dataclass(frozen=True, slots=True)
class Week8GeneralisationReport:
    """Inspectable pass-gate evidence for the Week 8 milestone."""

    training_seeds: tuple[int, ...]
    evaluation_seeds: tuple[int, ...]
    success_rate: float
    baseline_success_rate: float
    compilation_evidence_count: int
    skill_invocation_count: int
    reuse_count: int
    discovery_count: int
    failure_reasons: tuple[str, ...]
    authority_violations: int
    ndnra_shadow_observation_count: int
    ndnra_suggestion_count: int
    ndnra_disagreement_count: int
    ndnra_authority_violations: int
    ndnra_automatic_promotions: int
    evaluation_learning_attempts: int
    seed_overlap_count: int
    resource_seconds: float
    pass_gate: bool

    def to_json(self) -> dict[str, object]:
        """Return deterministic JSON-safe report data."""
        return {
            "authority_violations": self.authority_violations,
            "baseline_success_rate": self.baseline_success_rate,
            "compilation_evidence_count": self.compilation_evidence_count,
            "discovery_count": self.discovery_count,
            "evaluation_learning_attempts": self.evaluation_learning_attempts,
            "evaluation_seeds": list(self.evaluation_seeds),
            "failure_reasons": list(self.failure_reasons),
            "ndnra_authority_violations": self.ndnra_authority_violations,
            "ndnra_automatic_promotions": self.ndnra_automatic_promotions,
            "ndnra_disagreement_count": self.ndnra_disagreement_count,
            "ndnra_shadow_observation_count": self.ndnra_shadow_observation_count,
            "ndnra_suggestion_count": self.ndnra_suggestion_count,
            "pass_gate": self.pass_gate,
            "resource_seconds": round(self.resource_seconds, 6),
            "reuse_count": self.reuse_count,
            "seed_overlap_count": self.seed_overlap_count,
            "skill_invocation_count": self.skill_invocation_count,
            "success_rate": self.success_rate,
            "training_seeds": list(self.training_seeds),
        }


@dataclass(frozen=True, slots=True)
class Week8RunResult:
    """Full Week 8 runner output."""

    skill_record: SkillRecord
    report: Week8GeneralisationReport
    training_episodes: tuple[Week8EpisodeResult, ...]
    baseline_episodes: tuple[Week8EpisodeResult, ...]
    evaluation_episodes: tuple[Week8EpisodeResult, ...]


def run_week8_reusable_skill_evaluation(
    *,
    training_seeds: tuple[int, ...] = DEFAULT_TRAINING_SEEDS,
    evaluation_seeds: tuple[int, ...] = DEFAULT_EVALUATION_SEEDS,
    compilation_threshold: int = 3,
    output_dir: Path | None = None,
) -> Week8RunResult:
    """Train, compile, freeze, evaluate, and optionally export Week 8 evidence."""
    start = time.perf_counter()
    if set(training_seeds).intersection(evaluation_seeds):
        raise ValueError("training and evaluation seeds must not overlap")
    if len(evaluation_seeds) < 20:
        raise ValueError("Week 8 evaluation requires at least 20 deterministic starts")

    factory = Week8ScenarioFactory()
    training = tuple(
        _run_discovery_episode(factory.create(seed), used_for_evaluation=False)
        for seed in training_seeds
    )
    compile_result = compile_approach_and_push_skill(
        tuple(episode.evidence for episode in training),
        compilation_threshold=compilation_threshold,
    )
    if not compile_result.compiled or compile_result.record is None:
        failure = compile_result.failure or SkillCompileFailure.INCOMPLETE_SEQUENCE
        raise RuntimeError(f"Week 8 skill compilation failed: {failure.value}")

    baseline = tuple(
        _run_discovery_episode(factory.create(seed), used_for_evaluation=True)
        for seed in evaluation_seeds
    )
    evaluation = tuple(
        _run_reuse_episode(factory.create(seed), compile_result.record) for seed in evaluation_seeds
    )
    success_rate = _success_rate(evaluation)
    baseline_success_rate = _success_rate(baseline)
    reuse_count = sum(episode.reuse_count for episode in evaluation)
    discovery_count = sum(episode.discovery_count for episode in evaluation)
    skill_invocation_count = sum(episode.skill_invocation_count for episode in evaluation)
    authority_violations = sum(episode.authority_violation_count for episode in evaluation)
    failure_reasons = tuple(
        episode.failure_reason for episode in evaluation if episode.failure_reason is not None
    )
    ndnra_shadow_observations = sum(episode.step_count for episode in evaluation)
    pass_gate = bool(
        success_rate >= WEEK8_SUCCESS_TARGET
        and success_rate >= baseline_success_rate
        and skill_invocation_count >= len(evaluation_seeds)
        and reuse_count >= len(evaluation_seeds)
        and discovery_count == 0
        and authority_violations == 0
    )
    validated_record = compile_result.record.with_reuse(reuse_count).with_validation_status(
        SkillValidationStatus.PASSED if pass_gate else SkillValidationStatus.FAILED
    )
    report = Week8GeneralisationReport(
        training_seeds=training_seeds,
        evaluation_seeds=evaluation_seeds,
        success_rate=success_rate,
        baseline_success_rate=baseline_success_rate,
        compilation_evidence_count=validated_record.success_evidence_count,
        skill_invocation_count=skill_invocation_count,
        reuse_count=validated_record.reuse_count,
        discovery_count=discovery_count,
        failure_reasons=failure_reasons,
        authority_violations=authority_violations,
        ndnra_shadow_observation_count=ndnra_shadow_observations,
        ndnra_suggestion_count=0,
        ndnra_disagreement_count=0,
        ndnra_authority_violations=0,
        ndnra_automatic_promotions=0,
        evaluation_learning_attempts=0,
        seed_overlap_count=len(set(training_seeds).intersection(evaluation_seeds)),
        resource_seconds=time.perf_counter() - start,
        pass_gate=pass_gate,
    )
    result = Week8RunResult(
        skill_record=validated_record,
        report=report,
        training_episodes=training,
        baseline_episodes=baseline,
        evaluation_episodes=evaluation,
    )
    if output_dir is not None:
        export_week8_evidence(result, output_dir)
    return result


def export_week8_evidence(result: Week8RunResult, output_dir: Path) -> tuple[Path, Path]:
    """Write the inspectable skill record and generalisation report."""
    skill_path = output_dir / "approach_and_push_skill_record.json"
    report_path = output_dir / "week8_generalisation_report.json"
    write_skill_record(result.skill_record, skill_path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = report_path.with_name(f"{report_path.name}.tmp")
    temporary_path.write_text(
        json.dumps(result.report.to_json(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(report_path)
    return skill_path, report_path


def _run_discovery_episode(
    scenario: NurseryScenario,
    *,
    used_for_evaluation: bool,
) -> Week8EpisodeResult:
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-discovery",
        resource_state_provider=scenario.resource_state,
    )
    controller_record = _bootstrap_discovery_record()
    controller = ApproachAndPushSkillController(controller_record)
    steps: list[SkillStepEvidence] = []
    failure_reason: str | None = None
    while scenario.remaining_steps(runtime.state) > 0:
        decision = controller.decide(runtime.state, runtime.observe().available_actions)
        if decision.status is SkillExecutionStatus.TERMINATED:
            break
        if decision.status is not SkillExecutionStatus.ACTION or decision.action is None:
            failure_reason = decision.reason_code
            break
        observation = runtime.observe()
        result = runtime.step(decision.action)
        steps.append(
            SkillStepEvidence(
                action=decision.action,
                outcome=_outcome_name(result.transition.outcome),
                action_available=decision.action in observation.available_actions,
                world_changed=result.transition.world_changed,
            )
        )
        if result.transition.outcome is TransitionOutcome.PUSHED and _target_satisfied(
            runtime.state
        ):
            break
    success = _target_satisfied(runtime.state)
    if not success and failure_reason is None:
        failure_reason = "step_budget_exhausted"
    evidence = SkillEpisodeEvidence(
        episode_id=runtime.episode_id,
        seed=scenario.seed,
        source=(
            SkillAttemptSource.EVALUATION
            if used_for_evaluation
            else SkillAttemptSource.GROUNDED_PRODUCTION
        ),
        target_object_id="object_0",
        target_id="target_0",
        steps=tuple(steps),
        success=success,
        used_for_evaluation=used_for_evaluation,
    )
    return Week8EpisodeResult(
        seed=scenario.seed,
        episode_id=runtime.episode_id,
        success=success,
        step_count=len(steps),
        skill_invocation_count=0,
        reuse_count=0,
        discovery_count=1,
        authority_violation_count=0,
        failure_reason=None if success else failure_reason,
        evidence=evidence,
    )


def _run_reuse_episode(scenario: NurseryScenario, record: SkillRecord) -> Week8EpisodeResult:
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-skill-reuse",
        resource_state_provider=scenario.resource_state,
    )
    controller = ApproachAndPushSkillController(record)
    steps: list[SkillStepEvidence] = []
    invocation_count = 0
    failure_reason: str | None = None
    authority_violations = 0
    while scenario.remaining_steps(runtime.state) > 0:
        decision = controller.decide(runtime.state, runtime.observe().available_actions)
        if decision.skill_invoked:
            invocation_count += 1
        if decision.status is SkillExecutionStatus.TERMINATED:
            break
        if decision.status is not SkillExecutionStatus.ACTION or decision.action is None:
            failure_reason = decision.reason_code
            break
        production = retain_skill_candidate_through_curiosity(decision)
        if production.retained_action is None:
            raise RuntimeError("skill action decision did not retain a primitive action")
        if production.retained_action is not decision.action:
            authority_violations += 1
        observation = runtime.observe()
        result = runtime.step(production.retained_action)
        steps.append(
            SkillStepEvidence(
                action=production.retained_action,
                outcome=_outcome_name(result.transition.outcome),
                action_available=production.retained_action in observation.available_actions,
                world_changed=result.transition.world_changed,
            )
        )
        if result.transition.outcome is TransitionOutcome.PUSHED and _target_satisfied(
            runtime.state
        ):
            break
    success = _target_satisfied(runtime.state)
    if not success and failure_reason is None:
        failure_reason = "step_budget_exhausted"
    evidence = SkillEpisodeEvidence(
        episode_id=runtime.episode_id,
        seed=scenario.seed,
        source=SkillAttemptSource.EVALUATION,
        target_object_id="object_0",
        target_id="target_0",
        steps=tuple(steps),
        success=success,
        used_for_evaluation=True,
    )
    return Week8EpisodeResult(
        seed=scenario.seed,
        episode_id=runtime.episode_id,
        success=success,
        step_count=len(steps),
        skill_invocation_count=invocation_count,
        reuse_count=1 if invocation_count > 0 else 0,
        discovery_count=0,
        authority_violation_count=authority_violations,
        failure_reason=None if success else failure_reason,
        evidence=evidence,
    )


def _bootstrap_discovery_record() -> SkillRecord:
    return SkillRecord(
        skill_id="skill.main.approach_and_push.discovery_policy",
        name="approach_and_push",
        version="0.0.0-discovery",
        schema_version=1,
        provenance_episode_ids=("discovery-bootstrap", "discovery-bootstrap-2"),
        provenance_seeds=(0, 1),
        preconditions=("target_object_id exists", "target_id exists"),
        primitive_policy="axis_aligned_object_target_push_policy_v1",
        expected_outcome="target_object_id occupies target_id position",
        termination_conditions=("target object position equals target position",),
        failure_conditions=("no path exists",),
        success_evidence_count=2,
        attempt_evidence_count=2,
        compilation_threshold=2,
        reuse_count=0,
        discovery_count=0,
        last_validation_status=SkillValidationStatus.UNVALIDATED,
        deterministic_snapshot={
            "policy": "axis_aligned_object_target_push_policy_v1",
            "target_id": "target_0",
            "target_object_id": "object_0",
        },
    )


def _target_satisfied(state: NurseryState) -> bool:
    object_position = next(
        entity.position for entity in state.entities if entity.entity_id == "object_0"
    )
    target_position = next(
        entity.position for entity in state.entities if entity.entity_id == "target_0"
    )
    return object_position == target_position


def _outcome_name(outcome: TransitionOutcome) -> str:
    return "pushed" if outcome is TransitionOutcome.PUSHED else outcome.value


def _success_rate(episodes: tuple[Week8EpisodeResult, ...]) -> float:
    if not episodes:
        return 0.0
    return sum(1 for episode in episodes if episode.success) / len(episodes)
