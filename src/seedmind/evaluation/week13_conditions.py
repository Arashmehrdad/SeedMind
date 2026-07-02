"""Executable Week 13 baseline, ablation, and developmental-condition trials."""

from __future__ import annotations

import random
import tempfile
from dataclasses import dataclass
from pathlib import Path

from seedmind.ambition import (
    AmbitionManager,
    AmbitionStatus,
    GoalDirectedOutcomeDetector,
    ObservedDemonstration,
    load_ambition_manager,
    save_ambition_manager,
)
from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    EntityRole,
    NurseryRuntime,
    NurseryState,
    TeacherDemonstrationScenarioFactory,
)
from seedmind.growth.week12_evaluation import run_general
from seedmind.human import (
    ApprenticeshipManager,
    HelpContext,
    HumanRequest,
    RequestIntentCode,
    SupportLevel,
    VerificationRule,
)
from seedmind.skills import ApproachAndPushSkillController, Week8ScenarioFactory

BALL_REPETITION_SEEDS = tuple(
    tuple(range(2000 + 20 * index, 2020 + 20 * index)) for index in range(5)
)
AMBITION_REPLICATION_SEEDS = (2100, 2101, 2102, 2103, 2104)
APPRENTICESHIP_REPLICATION_SEEDS = (2200, 2201, 2202, 2203, 2204)
RANDOM_ACTIONS = (
    PrimitiveAction.TURN_LEFT,
    PrimitiveAction.TURN_RIGHT,
    PrimitiveAction.MOVE_FORWARD,
    PrimitiveAction.INSPECT,
    PrimitiveAction.PUSH,
    PrimitiveAction.WAIT,
)


@dataclass(frozen=True, slots=True)
class TaskEpisode:
    """One deterministic familiar-task episode."""

    condition: str
    repetition: int
    seed: int
    success: bool
    steps: int
    authority_violations: int = 0


@dataclass(frozen=True, slots=True)
class AmbitionTrial:
    """One repeated demonstration and persistence trial."""

    condition: str
    repetition: int
    seed: int
    candidate_generated: bool
    adopted: bool
    persisted: bool
    reload_identity_match: bool
    active_status_preserved: bool
    later_episode_count: int


@dataclass(frozen=True, slots=True)
class ApprenticeshipTrial:
    """One repeated help, teaching, and support trial."""

    condition: str
    repetition: int
    seed: int
    help_recall: float
    help_avoidance: float
    justified_help_requests: int
    teaching_responses: int
    teaching_resolution_rate: float
    support_promoted: bool
    unresolved_justified_help: int


def run_task_suite(
    condition: str,
    controller: ApproachAndPushSkillController,
) -> tuple[TaskEpisode, ...]:
    """Run one condition across the 100 disjoint Week 13 familiar scenarios."""
    factory = Week8ScenarioFactory()
    episodes: list[TaskEpisode] = []
    for repetition, seeds in enumerate(BALL_REPETITION_SEEDS, start=1):
        for seed in seeds:
            scenario = factory.create(seed)
            if condition == "random_primitive":
                success, steps = _run_random_episode(
                    scenario.initial_state, seed, factory.step_budget
                )
            elif condition == "fixed_reactive":
                success, steps = _run_reactive_episode(scenario.initial_state, factory.step_budget)
            else:
                record = run_general(
                    scenario.initial_state,
                    seed,
                    f"week13-{condition}-{seed}",
                    controller,
                    step_budget=factory.step_budget,
                )
                success, steps = record.success, record.steps
            episodes.append(
                TaskEpisode(
                    condition=condition,
                    repetition=repetition,
                    seed=seed,
                    success=success,
                    steps=steps,
                )
            )
    return tuple(episodes)


def run_ambition_trials(*, enabled: bool) -> tuple[AmbitionTrial, ...]:
    """Run five repeated ambition-formation and persistence trials."""
    condition = "complete_seedmind" if enabled else "no_ambition"
    trials: list[AmbitionTrial] = []
    scenario_factory = TeacherDemonstrationScenarioFactory()
    for repetition, seed in enumerate(AMBITION_REPLICATION_SEEDS, start=1):
        detector = GoalDirectedOutcomeDetector()
        manager = AmbitionManager()
        candidate_generated = False
        for demonstration_index in range(3):
            scenario = scenario_factory.create(seed)
            episode_id = f"week13-demo-{seed}-{demonstration_index:02d}"
            runtime = NurseryRuntime(
                initial_state=scenario.initial_state,
                episode_id=episode_id,
                resource_state_provider=scenario.resource_state,
                world_processes=scenario.world_processes,
            )
            start = runtime.observe()
            external_change_steps = 0
            for _ in range(2):
                step = runtime.step(PrimitiveAction.WAIT)
                external_change_steps += int(step.external_world_changed)
            candidate = detector.observe(
                ObservedDemonstration(
                    episode_id=episode_id,
                    start_observation=start,
                    end_observation=runtime.observe(),
                    external_change_steps=external_change_steps,
                    outcome_signal=float(
                        scenario.target_occupancy(runtime.state).all_targets_occupied
                    ),
                )
            )
            candidate_generated = candidate_generated or candidate is not None
            if enabled and candidate is not None:
                manager.consider(candidate, episode_id=episode_id)

        active = manager.active_ambition
        if active is not None:
            for later_index in range(5):
                manager.begin_episode(f"week13-practice-{seed}-{later_index:02d}")
        with tempfile.TemporaryDirectory(prefix="seedmind-week13-") as temporary_directory:
            state_path = Path(temporary_directory) / "ambition_state.json"
            save_ambition_manager(manager, state_path)
            restored = load_ambition_manager(state_path)
        restored_active = restored.active_ambition
        persisted = active is not None and restored_active is not None
        trials.append(
            AmbitionTrial(
                condition=condition,
                repetition=repetition,
                seed=seed,
                candidate_generated=candidate_generated,
                adopted=active is not None,
                persisted=persisted,
                reload_identity_match=bool(
                    persisted
                    and restored_active is not None
                    and active is not None
                    and restored_active.ambition_id == active.ambition_id
                ),
                active_status_preserved=bool(
                    persisted
                    and restored_active is not None
                    and restored_active.status is AmbitionStatus.ACTIVE
                ),
                later_episode_count=(
                    0 if restored_active is None else restored_active.observed_episode_count - 1
                ),
            )
        )
    return tuple(trials)


def run_apprenticeship_trials(*, teaching_enabled: bool) -> tuple[ApprenticeshipTrial, ...]:
    """Run five matched apprenticeship trials with or without caregiver teaching."""
    condition = "complete_seedmind" if teaching_enabled else "no_human_teaching"
    trials: list[ApprenticeshipTrial] = []
    for repetition, seed in enumerate(APPRENTICESHIP_REPLICATION_SEEDS, start=1):
        manager = ApprenticeshipManager()
        request = HumanRequest(
            request_id=f"week13-request-{seed}",
            intent_code=RequestIntentCode.REPRODUCE_OBSERVED_OUTCOME,
            target_code="active-demonstrated-outcome",
            ambiguity=0.1,
            permission_level=2,
            verification_rule=VerificationRule.CONFIRMED_OUTCOME,
        )
        justified_help_requests = 0
        teaching_responses = 0
        for case_index in range(4):
            context = HelpContext(
                case_id=f"week13-blocked-{seed}-{case_index}",
                request=request,
                uncertainty=0.90,
                competence=0.20,
                risk=0.40,
                blocked_attempts=3,
                safe_experiment_available=False,
                familiar=False,
            )
            decision = manager.evaluate(
                context,
                episode_id=f"week13-blocked-episode-{seed}-{case_index}",
                step_index=1,
            )
            justified_help_requests += int(decision.should_request_help)
            if teaching_enabled and decision.should_request_help:
                manager.teacher_response(
                    context,
                    decision,
                    episode_id=f"week13-blocked-episode-{seed}-{case_index}",
                    step_index=2,
                )
                teaching_responses += 1

        for case_index in range(4):
            context = HelpContext(
                case_id=f"week13-familiar-{seed}-{case_index}",
                request=request,
                uncertainty=0.10,
                competence=0.90,
                risk=0.10,
                blocked_attempts=0,
                safe_experiment_available=True,
                familiar=True,
            )
            decision = manager.evaluate(
                context,
                episode_id=f"week13-familiar-episode-{seed}-{case_index}",
                step_index=1,
            )
            if teaching_enabled and not decision.should_request_help:
                manager.record_approval(
                    request,
                    episode_id=f"week13-familiar-episode-{seed}-{case_index}",
                    step_index=2,
                    uncertainty=context.uncertainty,
                    competence=context.competence,
                    verified=True,
                    familiar=True,
                )

        ambiguous_request = HumanRequest(
            request_id=f"week13-ambiguous-request-{seed}",
            intent_code=RequestIntentCode.PRACTICE_ACTIVE_AMBITION,
            target_code="active-ambition",
            ambiguity=0.90,
            permission_level=1,
            verification_rule=VerificationRule.EXTERNAL_CHANGE,
        )
        ambiguous = HelpContext(
            case_id=f"week13-ambiguous-{seed}",
            request=ambiguous_request,
            uncertainty=0.80,
            competence=0.50,
            risk=0.10,
            blocked_attempts=0,
            safe_experiment_available=True,
            familiar=False,
        )
        ambiguous_decision = manager.evaluate(
            ambiguous,
            episode_id=f"week13-ambiguous-episode-{seed}",
            step_index=1,
        )
        justified_help_requests += int(ambiguous_decision.should_request_help)
        if teaching_enabled and ambiguous_decision.should_request_help:
            manager.teacher_response(
                ambiguous,
                ambiguous_decision,
                episode_id=f"week13-ambiguous-episode-{seed}",
                step_index=2,
            )
            teaching_responses += 1

        metrics = manager.metrics()
        resolution_rate = (
            0.0 if justified_help_requests == 0 else teaching_responses / justified_help_requests
        )
        trials.append(
            ApprenticeshipTrial(
                condition=condition,
                repetition=repetition,
                seed=seed,
                help_recall=metrics.help_recall,
                help_avoidance=metrics.help_avoidance_rate,
                justified_help_requests=justified_help_requests,
                teaching_responses=teaching_responses,
                teaching_resolution_rate=resolution_rate,
                support_promoted=manager.support_level is SupportLevel.GUIDED_LEARNER,
                unresolved_justified_help=justified_help_requests - teaching_responses,
            )
        )
    return tuple(trials)


def _run_random_episode(
    state: NurseryState,
    seed: int,
    step_budget: int,
) -> tuple[bool, int]:
    runtime = NurseryRuntime(state, f"week13-random-{seed}")
    generator = random.Random(7919 * seed + 104729)
    steps = 0
    for _ in range(step_budget):
        if _target_satisfied(runtime.state):
            break
        available = set(runtime.observe().available_actions)
        candidates = tuple(action for action in RANDOM_ACTIONS if action in available)
        if not candidates:
            break
        runtime.step(generator.choice(candidates))
        steps += 1
    return _target_satisfied(runtime.state), steps


def _run_reactive_episode(state: NurseryState, step_budget: int) -> tuple[bool, int]:
    runtime = NurseryRuntime(state, "week13-fixed-reactive")
    steps = 0
    for _ in range(step_budget):
        if _target_satisfied(runtime.state):
            break
        action = _reactive_action(runtime.state)
        if action not in runtime.observe().available_actions:
            action = PrimitiveAction.WAIT
        runtime.step(action)
        steps += 1
    return _target_satisfied(runtime.state), steps


def _reactive_action(state: NurseryState) -> PrimitiveAction:
    object_position = _entity_position(state, "object_0")
    target_position = _entity_position(state, "target_0")
    delta_x = target_position.x - object_position.x
    delta_y = target_position.y - object_position.y
    if abs(delta_x) >= abs(delta_y) and delta_x != 0:
        push_direction = Direction.EAST if delta_x > 0 else Direction.WEST
    else:
        push_direction = Direction.SOUTH if delta_y > 0 else Direction.NORTH
    contact_position = object_position.moved(_opposite(push_direction))
    if state.agent.position == contact_position:
        return _turn_or_act(state.agent.orientation, push_direction, PrimitiveAction.PUSH)
    desired = _greedy_direction(state.agent.position, contact_position)
    if desired is None:
        return PrimitiveAction.WAIT
    return _turn_or_act(state.agent.orientation, desired, PrimitiveAction.MOVE_FORWARD)


def _turn_or_act(
    current: Direction,
    desired: Direction,
    aligned_action: PrimitiveAction,
) -> PrimitiveAction:
    if current is desired:
        return aligned_action
    clockwise = (int(desired) - int(current)) % 4
    return PrimitiveAction.TURN_RIGHT if clockwise in (1, 2) else PrimitiveAction.TURN_LEFT


def _greedy_direction(source: GridPosition, destination: GridPosition) -> Direction | None:
    if source.x < destination.x:
        return Direction.EAST
    if source.x > destination.x:
        return Direction.WEST
    if source.y < destination.y:
        return Direction.SOUTH
    if source.y > destination.y:
        return Direction.NORTH
    return None


def _opposite(direction: Direction) -> Direction:
    return tuple(Direction)[(int(direction) + 2) % len(tuple(Direction))]


def _entity_position(state: NurseryState, entity_id: str) -> GridPosition:
    return next(entity.position for entity in state.entities if entity.entity_id == entity_id)


def _target_satisfied(state: NurseryState) -> bool:
    object_position = next(
        entity.position
        for entity in state.entities
        if entity.entity_id == "object_0" and entity.role is EntityRole.OBJECT
    )
    target_position = next(
        entity.position
        for entity in state.entities
        if entity.entity_id == "target_0" and entity.role is EntityRole.TARGET
    )
    return object_position == target_position
