"""Grounded candidate, general-controller, and routed Week 11 rollouts."""

from dataclasses import dataclass

from seedmind.contracts import PrimitiveAction
from seedmind.environment import NurseryRuntime, NurseryState
from seedmind.growth.router import SpecialistRouter
from seedmind.growth.specialist import (
    CandidateSkillExpert,
    ExpertModuleInput,
    ExpertModuleOutput,
    SpecialistLatentState,
)
from seedmind.growth.week10 import capacity_target_satisfied as _target_satisfied
from seedmind.growth.week11_inputs import STEP_BUDGET
from seedmind.skills import (
    ApproachAndPushSkillController,
    SkillExecutionStatus,
    SkillStepDecision,
    retain_skill_candidate_through_curiosity,
)


@dataclass(frozen=True, slots=True)
class RolloutRecord:
    episode_id: str
    seed: int
    success: bool
    actions: tuple[str, ...]
    outcomes: tuple[str, ...]
    selected_modules: tuple[str, ...] = ()
    fallback_count: int = 0
    abstention_count: int = 0
    authority_violations: int = 0

    @property
    def steps(self) -> int:
        return len(self.actions)

    def to_json(self) -> dict[str, object]:
        return {
            "abstention_count": self.abstention_count,
            "actions": list(self.actions),
            "authority_violations": self.authority_violations,
            "episode_id": self.episode_id,
            "fallback_count": self.fallback_count,
            "outcomes": list(self.outcomes),
            "seed": self.seed,
            "selected_modules": list(self.selected_modules),
            "steps": self.steps,
            "success": self.success,
        }


def run_general(
    state: NurseryState,
    seed: int,
    episode_id: str,
    controller: ApproachAndPushSkillController,
) -> RolloutRecord:
    runtime = NurseryRuntime(state, episode_id)
    actions: list[str] = []
    outcomes: list[str] = []
    for _ in range(STEP_BUDGET):
        if _target_satisfied(runtime.state):
            break
        decision = controller.decide(runtime.state, runtime.observe().available_actions)
        if decision.status is not SkillExecutionStatus.ACTION or decision.action is None:
            break
        action = retain_skill_candidate_through_curiosity(decision).retained_action
        if action is None:
            break
        result = runtime.step(action)
        actions.append(action.value)
        outcomes.append(result.transition.outcome.value)
    return RolloutRecord(
        episode_id,
        seed,
        _target_satisfied(runtime.state),
        tuple(actions),
        tuple(outcomes),
    )


def run_specialist(
    state: NurseryState,
    seed: int,
    episode_id: str,
    candidate: CandidateSkillExpert,
) -> RolloutRecord:
    runtime = NurseryRuntime(state, episode_id)
    actions: list[str] = []
    outcomes: list[str] = []
    abstentions = 0
    for _ in range(STEP_BUDGET):
        if _target_satisfied(runtime.state):
            break
        proposal = candidate.propose(build_module_input(runtime, "control_angular_object_position"))
        if proposal.abstain or proposal.action_proposal is None:
            abstentions += 1
            break
        action = _retain(proposal.action_proposal)
        result = runtime.step(action)
        actions.append(action.value)
        outcomes.append(result.transition.outcome.value)
    return RolloutRecord(
        episode_id,
        seed,
        _target_satisfied(runtime.state),
        tuple(actions),
        tuple(outcomes),
        abstention_count=abstentions,
    )


def run_routed(
    state: NurseryState,
    seed: int,
    episode_id: str,
    goal: str,
    controller: ApproachAndPushSkillController,
    candidate: CandidateSkillExpert,
    router: SpecialistRouter,
) -> RolloutRecord:
    runtime = NurseryRuntime(state, episode_id)
    actions: list[str] = []
    outcomes: list[str] = []
    modules: list[str] = []
    fallbacks = abstentions = violations = 0
    for _ in range(STEP_BUDGET):
        if _target_satisfied(runtime.state):
            break
        routing = router.route(
            general_proposal=_general_proposal(controller, runtime),
            specialist_proposal=candidate.propose(build_module_input(runtime, goal)),
            specialist_registered=True,
            specialist_active=True,
        )
        fallbacks += int(routing.fallback_used)
        violations += int(routing.action_authority_violation)
        if routing.abstained or routing.action_proposal is None:
            abstentions += 1
            break
        action = _retain(routing.action_proposal)
        result = runtime.step(action)
        actions.append(action.value)
        outcomes.append(result.transition.outcome.value)
        modules.append(routing.selected_module)
    return RolloutRecord(
        episode_id,
        seed,
        _target_satisfied(runtime.state),
        tuple(actions),
        tuple(outcomes),
        tuple(modules),
        fallbacks,
        abstentions,
        violations,
    )


def abstaining_output(reason: str) -> ExpertModuleOutput:
    return ExpertModuleOutput(None, 0.0, "no_action", 0.0, True, reason)


def _general_proposal(
    controller: ApproachAndPushSkillController,
    runtime: NurseryRuntime,
) -> ExpertModuleOutput:
    decision = controller.decide(runtime.state, runtime.observe().available_actions)
    if decision.status is not SkillExecutionStatus.ACTION or decision.action is None:
        return abstaining_output(decision.reason_code)
    return ExpertModuleOutput(
        decision.action,
        0.75,
        "general_approach_and_push_step",
        0.10,
        False,
        decision.reason_code,
    )


def build_module_input(runtime: NurseryRuntime, goal: str) -> ExpertModuleInput:
    return ExpertModuleInput(
        SpecialistLatentState.from_nursery(runtime.state),
        goal,
        (
            "week10:sustained_cube_blockage",
            "week10:grounded_replay",
            "week10:teacher_demonstration",
        ),
        runtime.observe().available_actions,
    )


def _retain(action: PrimitiveAction) -> PrimitiveAction:
    decision = SkillStepDecision(
        SkillExecutionStatus.ACTION,
        action,
        "week11_routed_candidate",
        True,
    )
    retained = retain_skill_candidate_through_curiosity(decision).retained_action
    if retained is None:
        raise AssertionError("production curiosity rejected a valid proposal")
    return retained
