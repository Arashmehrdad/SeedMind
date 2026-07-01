"""Historical Week 9 goal-conditioned adapter comparison.

This module does not implement or evaluate the complete NDNRA architecture. It is
retained only to reproduce committed Week 9 adapter evidence after NDNRA was
frozen for extraction to a separate project.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from statistics import fmean

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.contribution.contracts import ContributionRecord, HumanContributionRequest
from seedmind.environment import (
    NurseryRuntime,
    NurseryScenario,
    NurseryState,
    NurseryTransitionEngine,
    WorldProcessPipeline,
)
from seedmind.integration.comparison_oracle import NurseryOutcomeOracle
from seedmind.integration.developmental_signals import LiveDevelopmentalSignals
from seedmind.training import collect_experience


class ScenarioKind(StrEnum):
    """Evaluation classification used to keep blocked tasks separate."""

    SOLVABLE = "solvable"
    BLOCKED = "blocked"


class TaskProgressCategory(StrEnum):
    """Competence comparison labels based on task progress first."""

    DEFAULT_BETTER = "task_progress_default_better"
    NDNRA_BETTER = "task_progress_ndnra_better"
    EQUIVALENT = "task_equivalent"
    GENERIC_ONLY = "generic_score_only_difference"
    NOT_COMPARABLE = "not_comparable"


@dataclass(frozen=True, slots=True)
class Week9ContributionGoal:
    """Typed object-to-target goal supplied to both controllers."""

    target_object_id: str
    destination_target_id: str
    requested_outcome: str
    completion_condition: str
    scenario_context: str

    def __post_init__(self) -> None:
        for value in (
            self.target_object_id,
            self.destination_target_id,
            self.requested_outcome,
            self.completion_condition,
            self.scenario_context,
        ):
            if not value.strip() or not value.isascii():
                raise ValueError("goal fields must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        return {
            "completion_condition": self.completion_condition,
            "destination_target_id": self.destination_target_id,
            "requested_outcome": self.requested_outcome,
            "scenario_context": self.scenario_context,
            "target_object_id": self.target_object_id,
        }


@dataclass(frozen=True, slots=True)
class NDNRAStateFeatures:
    """Relational state context supplied to the goal-conditioned NDNRA adapter."""

    agent_position: tuple[int, int]
    agent_orientation: str
    target_object_position: tuple[int, int]
    destination_target_position: tuple[int, int]
    object_to_target_dx: int
    object_to_target_dy: int
    object_to_target_distance: int
    agent_to_object_dx: int
    agent_to_object_dy: int
    agent_to_object_distance: int
    aligned_with_object: bool
    behind_object: bool
    in_contact_with_object: bool
    pushing_legal: bool
    pushing_useful: bool
    blocking_condition: str
    target_occupied: bool
    remaining_step_budget: int
    human_interruption: bool
    available_actions: tuple[str, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "agent_orientation": self.agent_orientation,
            "agent_position": list(self.agent_position),
            "agent_to_object_distance": self.agent_to_object_distance,
            "agent_to_object_dx": self.agent_to_object_dx,
            "agent_to_object_dy": self.agent_to_object_dy,
            "aligned_with_object": self.aligned_with_object,
            "available_actions": list(self.available_actions),
            "behind_object": self.behind_object,
            "blocking_condition": self.blocking_condition,
            "destination_target_position": list(self.destination_target_position),
            "human_interruption": self.human_interruption,
            "in_contact_with_object": self.in_contact_with_object,
            "object_to_target_distance": self.object_to_target_distance,
            "object_to_target_dx": self.object_to_target_dx,
            "object_to_target_dy": self.object_to_target_dy,
            "pushing_legal": self.pushing_legal,
            "pushing_useful": self.pushing_useful,
            "remaining_step_budget": self.remaining_step_budget,
            "target_object_position": list(self.target_object_position),
            "target_occupied": self.target_occupied,
        }

    @property
    def phase_key(self) -> str:
        """Return a coarse relational phase for learned action values."""
        if self.target_occupied:
            return "complete"
        if self.pushing_legal and self.pushing_useful:
            return "useful_push"
        if self.in_contact_with_object:
            return "contact"
        if self.behind_object:
            return "behind_object"
        if self.aligned_with_object:
            return "aligned_approach"
        return "approach"


@dataclass(frozen=True, slots=True)
class NDNRAProposal:
    """One non-authoritative NDNRA proposal with goal and context evidence."""

    action: PrimitiveAction | None
    score: float
    reason_code: str
    goal: Week9ContributionGoal | None
    features: NDNRAStateFeatures
    candidate_scores: tuple[tuple[str, float], ...]
    has_action_authority: bool = False

    def __post_init__(self) -> None:
        if not isfinite(self.score):
            raise ValueError("proposal score must be finite")
        if self.has_action_authority:
            raise ValueError("NDNRA proposal cannot have production action authority")

    def to_json(self) -> dict[str, object]:
        return {
            "action": None if self.action is None else self.action.value,
            "candidate_scores": [
                {"action": action, "score": score} for action, score in self.candidate_scores
            ],
            "features": self.features.to_json(),
            "goal": None if self.goal is None else self.goal.to_json(),
            "has_action_authority": self.has_action_authority,
            "reason_code": self.reason_code,
            "score": self.score,
        }


@dataclass(slots=True)
class GoalConditionedNDNRAController:
    """Historical goal-conditioned adapter, not the complete NDNRA architecture."""

    maximum_steps: int = 96
    _progress: dict[tuple[str, PrimitiveAction], list[float]] | None = None
    _transition_count: int = 0
    _evaluation_update_count: int = 0

    def __post_init__(self) -> None:
        if self._progress is None:
            self._progress = defaultdict(list)
        if self.maximum_steps <= 1:
            raise ValueError("controller must support multi-step closed-loop behavior")

    @property
    def transition_count(self) -> int:
        return self._transition_count

    @property
    def evaluation_update_count(self) -> int:
        return self._evaluation_update_count

    def learned_action_keys(self) -> tuple[str, ...]:
        assert self._progress is not None
        return tuple(
            f"{phase}:{action.value}"
            for phase, action in sorted(
                self._progress,
                key=lambda item: (item[0], item[1].value),
            )
        )

    def propose(
        self,
        state: NurseryState,
        available_actions: tuple[PrimitiveAction, ...],
        goal: Week9ContributionGoal | None,
        *,
        remaining_steps: int,
        human_interruption: bool = False,
    ) -> NDNRAProposal:
        """Return a closed-loop primitive proposal from goal and relational context."""
        features = extract_ndnra_state_features(
            state,
            goal,
            available_actions,
            remaining_steps=remaining_steps,
            human_interruption=human_interruption,
        )
        if goal is None:
            return NDNRAProposal(
                action=None,
                score=0.0,
                reason_code="goal_missing",
                goal=None,
                features=features,
                candidate_scores=(),
            )
        if human_interruption:
            return NDNRAProposal(
                action=PrimitiveAction.REQUEST_HELP
                if PrimitiveAction.REQUEST_HELP in available_actions
                else None,
                score=0.0,
                reason_code="human_interrupt",
                goal=goal,
                features=features,
                candidate_scores=(),
            )
        if features.target_occupied:
            return NDNRAProposal(
                action=None,
                score=1.0,
                reason_code="goal_already_complete",
                goal=goal,
                features=features,
                candidate_scores=(),
            )
        candidates = tuple(
            action for action in available_actions if action is not PrimitiveAction.STOP
        )
        scored = tuple(
            (action, self._score_action(state, action, goal, features, remaining_steps))
            for action in candidates
        )
        if not scored:
            return NDNRAProposal(
                action=None,
                score=0.0,
                reason_code="no_available_candidate",
                goal=goal,
                features=features,
                candidate_scores=(),
            )
        ranked = max(scored, key=lambda item: (item[1], -tuple(PrimitiveAction).index(item[0])))
        return NDNRAProposal(
            action=ranked[0],
            score=ranked[1],
            reason_code="goal_conditioned_replan",
            goal=goal,
            features=features,
            candidate_scores=tuple((action.value, score) for action, score in scored),
        )

    def observe_transition(
        self,
        *,
        before: NurseryState,
        after: NurseryState,
        action: PrimitiveAction,
        goal: Week9ContributionGoal,
        available_actions: tuple[PrimitiveAction, ...],
        remaining_steps: int,
        source: str,
    ) -> None:
        """Learn only from explicitly allowed grounded NDNRA-owned transitions."""
        if source == "evaluation":
            self._evaluation_update_count += 1
            raise ValueError("frozen evaluation must not update NDNRA")
        if source not in {"ndnra_sandbox", "ndnra_adaptive"}:
            raise ValueError("NDNRA cannot learn from this transition source")
        features = extract_ndnra_state_features(
            before,
            goal,
            available_actions,
            remaining_steps=remaining_steps,
            human_interruption=False,
        )
        before_distance = _distance(before, goal.target_object_id, goal.destination_target_id)
        after_distance = _distance(after, goal.target_object_id, goal.destination_target_id)
        progress = (
            1.0 if before_distance == 0 else (before_distance - after_distance) / before_distance
        )
        assert self._progress is not None
        self._progress[(features.phase_key, action)].append(progress)
        self._transition_count += 1

    def _score_action(
        self,
        state: NurseryState,
        action: PrimitiveAction,
        goal: Week9ContributionGoal,
        features: NDNRAStateFeatures,
        remaining_steps: int,
    ) -> float:
        after = _apply_action_clone(state, action)
        before_distance = _distance(state, goal.target_object_id, goal.destination_target_id)
        after_distance = _distance(after, goal.target_object_id, goal.destination_target_id)
        immediate_progress = (
            1.0 if before_distance == 0 else (before_distance - after_distance) / before_distance
        )
        learned = self._learned_value(features.phase_key, action)
        next_features = extract_ndnra_state_features(
            after,
            goal,
            tuple(PrimitiveAction),
            remaining_steps=max(0, remaining_steps - 1),
            human_interruption=False,
        )
        shaping = 0.0
        if next_features.behind_object:
            shaping += 0.10
        if next_features.in_contact_with_object:
            shaping += 0.10
        if next_features.pushing_useful:
            shaping += 0.15
        if action is PrimitiveAction.PUSH and not features.pushing_useful:
            shaping -= 0.30
        if after == state and action not in {
            PrimitiveAction.TURN_LEFT,
            PrimitiveAction.TURN_RIGHT,
            PrimitiveAction.WAIT,
        }:
            shaping -= 0.20
        return _clamp_signed((0.60 * immediate_progress) + (0.25 * learned) + shaping)

    def _learned_value(self, phase: str, action: PrimitiveAction) -> float:
        assert self._progress is not None
        values = self._progress.get((phase, action), ())
        return fmean(values) if values else 0.0


@dataclass(frozen=True, slots=True)
class Week9ComparisonStep:
    """One same-state Default and NDNRA candidate comparison."""

    contribution_id: str
    scenario_id: str
    scenario_kind: ScenarioKind
    step_index: int
    scenario_step_index: int
    default_action: PrimitiveAction
    ndnra_action: PrimitiveAction | None
    ndnra_proposal: NDNRAProposal
    default_task_progress: float | None
    ndnra_task_progress: float | None
    default_generic_score: float | None
    ndnra_generic_score: float | None
    category: TaskProgressCategory
    default_executed: bool = True
    ndnra_executed: bool = False
    authority_violation: bool = False

    def __post_init__(self) -> None:
        if self.step_index < 0 or self.scenario_step_index < 0:
            raise ValueError("step indices must not be negative")
        if not self.default_executed or self.ndnra_executed:
            raise ValueError("counterfactual comparison cannot execute NDNRA in production")
        if self.authority_violation:
            raise ValueError("NDNRA cannot carry action authority")
        if self.ndnra_action is not self.ndnra_proposal.action:
            raise ValueError("step action does not match proposal")

    def to_json(self) -> dict[str, object]:
        return {
            "authority_violation": self.authority_violation,
            "category": self.category.value,
            "contribution_id": self.contribution_id,
            "default_action": self.default_action.value,
            "default_executed": self.default_executed,
            "default_generic_score": self.default_generic_score,
            "default_task_progress": self.default_task_progress,
            "ndnra_action": None if self.ndnra_action is None else self.ndnra_action.value,
            "ndnra_executed": self.ndnra_executed,
            "ndnra_generic_score": self.ndnra_generic_score,
            "ndnra_proposal": self.ndnra_proposal.to_json(),
            "ndnra_task_progress": self.ndnra_task_progress,
            "scenario_id": self.scenario_id,
            "scenario_kind": self.scenario_kind.value,
            "scenario_step_index": self.scenario_step_index,
            "step_index": self.step_index,
        }


@dataclass(frozen=True, slots=True)
class Week9ScenarioOutcome:
    """Separated outcome metrics for one solvable or blocked scenario."""

    contribution_id: str
    scenario_id: str
    scenario_kind: ScenarioKind
    default_success: bool
    ndnra_frozen_success: bool
    ndnra_adaptive_success: bool
    default_steps: int
    ndnra_frozen_steps: int
    ndnra_adaptive_steps: int
    ndnra_frozen_failure_reason: str | None
    ndnra_adaptive_failure_reason: str | None
    blocked_honest_default_failure: bool
    blocked_honest_ndnra_failure: bool
    ndnra_loop_detected: bool

    def to_json(self) -> dict[str, object]:
        return {
            "blocked_honest_default_failure": self.blocked_honest_default_failure,
            "blocked_honest_ndnra_failure": self.blocked_honest_ndnra_failure,
            "contribution_id": self.contribution_id,
            "default_steps": self.default_steps,
            "default_success": self.default_success,
            "ndnra_adaptive_failure_reason": self.ndnra_adaptive_failure_reason,
            "ndnra_adaptive_steps": self.ndnra_adaptive_steps,
            "ndnra_adaptive_success": self.ndnra_adaptive_success,
            "ndnra_frozen_failure_reason": self.ndnra_frozen_failure_reason,
            "ndnra_frozen_steps": self.ndnra_frozen_steps,
            "ndnra_frozen_success": self.ndnra_frozen_success,
            "ndnra_loop_detected": self.ndnra_loop_detected,
            "scenario_id": self.scenario_id,
            "scenario_kind": self.scenario_kind.value,
        }


@dataclass(frozen=True, slots=True)
class Week9FairComparisonReport:
    """Aggregate fair-comparison and separate acceptance fields."""

    training_seeds: tuple[int, ...]
    evaluation_seeds: tuple[int, ...]
    blocked_evaluation_seeds: tuple[int, ...]
    evaluation_seed_overlap_count: int
    default_solvable_successes: int
    default_solvable_attempts: int
    ndnra_frozen_solvable_successes: int
    ndnra_frozen_solvable_attempts: int
    ndnra_adaptive_solvable_successes: int
    ndnra_adaptive_solvable_attempts: int
    blocked_scenarios: int
    blocked_default_honest_failures: int
    blocked_ndnra_honest_failures: int
    task_progress_default_better: int
    task_progress_ndnra_better: int
    task_equivalent: int
    generic_score_only_difference: int
    not_comparable: int
    frozen_evaluation_updates: int
    adaptive_ndnra_updates: int
    authority_violations: int
    automatic_promotions: int
    experiment_integrity_pass: bool
    default_competence_pass: bool
    ndnra_competence_pass: bool
    blocked_scenario_handling_pass: bool
    authority_containment_pass: bool
    week9_main_milestone_pass: bool

    @property
    def default_solvable_completion_rate(self) -> float:
        return _rate(self.default_solvable_successes, self.default_solvable_attempts)

    @property
    def ndnra_frozen_solvable_completion_rate(self) -> float:
        return _rate(self.ndnra_frozen_solvable_successes, self.ndnra_frozen_solvable_attempts)

    @property
    def ndnra_adaptive_solvable_completion_rate(self) -> float:
        return _rate(self.ndnra_adaptive_solvable_successes, self.ndnra_adaptive_solvable_attempts)

    def to_json(self) -> dict[str, object]:
        return {
            "adaptive_ndnra_updates": self.adaptive_ndnra_updates,
            "authority_containment_pass": self.authority_containment_pass,
            "authority_violations": self.authority_violations,
            "automatic_promotions": self.automatic_promotions,
            "blocked_default_honest_failures": self.blocked_default_honest_failures,
            "blocked_evaluation_seeds": list(self.blocked_evaluation_seeds),
            "blocked_ndnra_honest_failures": self.blocked_ndnra_honest_failures,
            "blocked_scenario_handling_pass": self.blocked_scenario_handling_pass,
            "blocked_scenarios": self.blocked_scenarios,
            "default_competence_pass": self.default_competence_pass,
            "default_solvable_attempts": self.default_solvable_attempts,
            "default_solvable_completion_rate": self.default_solvable_completion_rate,
            "default_solvable_successes": self.default_solvable_successes,
            "evaluation_seed_overlap_count": self.evaluation_seed_overlap_count,
            "evaluation_seeds": list(self.evaluation_seeds),
            "experiment_integrity_pass": self.experiment_integrity_pass,
            "frozen_evaluation_updates": self.frozen_evaluation_updates,
            "generic_score_only_difference": self.generic_score_only_difference,
            "ndnra_adaptive_solvable_attempts": self.ndnra_adaptive_solvable_attempts,
            "ndnra_adaptive_solvable_completion_rate": (
                self.ndnra_adaptive_solvable_completion_rate
            ),
            "ndnra_adaptive_solvable_successes": self.ndnra_adaptive_solvable_successes,
            "ndnra_competence_pass": self.ndnra_competence_pass,
            "ndnra_frozen_solvable_attempts": self.ndnra_frozen_solvable_attempts,
            "ndnra_frozen_solvable_completion_rate": self.ndnra_frozen_solvable_completion_rate,
            "ndnra_frozen_solvable_successes": self.ndnra_frozen_solvable_successes,
            "not_comparable": self.not_comparable,
            "task_equivalent": self.task_equivalent,
            "task_progress_default_better": self.task_progress_default_better,
            "task_progress_ndnra_better": self.task_progress_ndnra_better,
            "training_seeds": list(self.training_seeds),
            "week9_main_milestone_pass": self.week9_main_milestone_pass,
        }


@dataclass(frozen=True, slots=True)
class Week9ParallelComparisonResult:
    """Complete fair comparison evidence."""

    protocol: dict[str, object]
    steps: tuple[Week9ComparisonStep, ...]
    scenarios: tuple[Week9ScenarioOutcome, ...]
    report: Week9FairComparisonReport

    def to_json(self) -> dict[str, object]:
        return {
            "limitations": [
                "NDNRA receives relational symbolic features from the adapter rather than raw pixels.",
                "NDNRA uses bounded one-step goal-progress replanning, not a learned neural policy.",
                "Default retains the compiled Week 8 skill and remains stronger on this task.",
            ],
            "protocol": self.protocol,
            "scenario_outcomes": [scenario.to_json() for scenario in self.scenarios],
            "steps": [step.to_json() for step in self.steps],
            "summary": self.report.to_json(),
        }


def goal_from_request(
    request: HumanContributionRequest,
    *,
    scenario_context: str,
) -> Week9ContributionGoal:
    """Build the explicit object-to-target goal given to NDNRA."""
    return Week9ContributionGoal(
        target_object_id=request.target_object_id,
        destination_target_id=request.target_id,
        requested_outcome=request.expected_outcome,
        completion_condition="target_object_position_equals_destination_target_position",
        scenario_context=scenario_context,
    )


def extract_ndnra_state_features(
    state: NurseryState,
    goal: Week9ContributionGoal | None,
    available_actions: tuple[PrimitiveAction, ...],
    *,
    remaining_steps: int,
    human_interruption: bool,
) -> NDNRAStateFeatures:
    """Encode relational context; never reduce NDNRA state to available actions only."""
    if goal is None:
        object_position = state.agent.position
        target_position = state.agent.position
    else:
        object_position = _entity_position(state, goal.target_object_id)
        target_position = _entity_position(state, goal.destination_target_id)
    agent_position = state.agent.position
    desired = _dominant_direction(object_position, target_position)
    contact_position = object_position.moved(Direction((int(desired) + 2) % 4))
    front = agent_position.moved(state.agent.orientation)
    in_contact = front == object_position
    push_destination = object_position.moved(state.agent.orientation)
    push_blocker = None
    if state.is_in_bounds(push_destination):
        push_blocker = state.blocking_entity_at(push_destination)
    pushing_legal = (
        in_contact
        and state.is_in_bounds(push_destination)
        and (
            push_blocker is None
            or (goal is not None and push_blocker.entity_id == goal.target_object_id)
        )
    )
    before_distance = abs(object_position.x - target_position.x) + abs(
        object_position.y - target_position.y
    )
    after_distance = (
        abs(push_destination.x - target_position.x) + abs(push_destination.y - target_position.y)
        if pushing_legal
        else before_distance
    )
    blocking_condition = "none"
    if not state.is_in_bounds(contact_position):
        blocking_condition = "contact_out_of_bounds"
    elif (
        state.blocking_entity_at(contact_position) is not None
        and contact_position != agent_position
    ):
        blocking_condition = "contact_blocked"
    elif in_contact and not pushing_legal:
        blocking_condition = "push_blocked"
    return NDNRAStateFeatures(
        agent_position=(agent_position.x, agent_position.y),
        agent_orientation=state.agent.orientation.name.lower(),
        target_object_position=(object_position.x, object_position.y),
        destination_target_position=(target_position.x, target_position.y),
        object_to_target_dx=target_position.x - object_position.x,
        object_to_target_dy=target_position.y - object_position.y,
        object_to_target_distance=before_distance,
        agent_to_object_dx=object_position.x - agent_position.x,
        agent_to_object_dy=object_position.y - agent_position.y,
        agent_to_object_distance=abs(object_position.x - agent_position.x)
        + abs(object_position.y - agent_position.y),
        aligned_with_object=(
            agent_position.x == object_position.x or agent_position.y == object_position.y
        ),
        behind_object=agent_position == contact_position,
        in_contact_with_object=in_contact,
        pushing_legal=pushing_legal,
        pushing_useful=pushing_legal and after_distance < before_distance,
        blocking_condition=blocking_condition,
        target_occupied=object_position == target_position,
        remaining_step_budget=remaining_steps,
        human_interruption=human_interruption,
        available_actions=tuple(action.value for action in available_actions),
    )


def train_ndnra_in_sandbox(
    controller: GoalConditionedNDNRAController,
    *,
    scenarios: tuple[NurseryScenario, ...],
    requests: tuple[HumanContributionRequest, ...],
) -> None:
    """Train NDNRA only from NDNRA-executed sandbox transitions."""
    for scenario, request in zip(scenarios, requests, strict=True):
        goal = goal_from_request(request, scenario_context=f"training_seed_{scenario.seed}")
        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=f"{scenario.scenario_id}-ndnra-sandbox-training",
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )
        visited: set[tuple[GridPosition, Direction, GridPosition]] = set()
        while scenario.remaining_steps(runtime.state) > 0:
            if _goal_satisfied(runtime.state, goal):
                break
            state_key = (
                runtime.state.agent.position,
                runtime.state.agent.orientation,
                _entity_position(runtime.state, goal.target_object_id),
            )
            if state_key in visited:
                break
            visited.add(state_key)
            before = runtime.state
            available = runtime.observe().available_actions
            proposal = controller.propose(
                before,
                available,
                goal,
                remaining_steps=scenario.remaining_steps(before),
            )
            if proposal.action is None:
                break
            collect_experience(runtime, proposal.action)
            controller.observe_transition(
                before=before,
                after=runtime.state,
                action=proposal.action,
                goal=goal,
                available_actions=available,
                remaining_steps=scenario.remaining_steps(before),
                source="ndnra_sandbox",
            )


def run_week9_parallel_comparison(
    *,
    records: tuple[ContributionRecord, ...],
    scenarios: tuple[NurseryScenario, ...],
    training_scenarios: tuple[NurseryScenario, ...],
    training_requests: tuple[HumanContributionRequest, ...],
    controller: GoalConditionedNDNRAController | None = None,
) -> Week9ParallelComparisonResult:
    """Run the fair held-out comparison and separate adaptive diagnostic."""
    if len(records) != len(scenarios):
        raise ValueError("records and scenarios must have equal lengths")
    resolved = GoalConditionedNDNRAController() if controller is None else controller
    train_ndnra_in_sandbox(
        resolved,
        scenarios=training_scenarios,
        requests=training_requests,
    )
    training_seeds = tuple(scenario.seed for scenario in training_scenarios)
    evaluation_seeds = tuple(scenario.seed for scenario in scenarios)
    blocked_seeds = tuple(
        scenario.seed
        for record, scenario in zip(records, scenarios, strict=True)
        if not record.success
    )
    steps = _counterfactual_steps(records, scenarios, resolved)
    frozen = tuple(
        _rollout(record, scenario, resolved, adaptive=False)
        for record, scenario in zip(records, scenarios, strict=True)
    )
    adaptive_controller = GoalConditionedNDNRAController()
    train_ndnra_in_sandbox(
        adaptive_controller,
        scenarios=training_scenarios,
        requests=training_requests,
    )
    adaptive = tuple(
        _rollout(record, scenario, adaptive_controller, adaptive=True)
        for record, scenario in zip(records, scenarios, strict=True)
    )
    outcomes = tuple(
        _scenario_outcome(record, frozen_result, adaptive_result)
        for record, frozen_result, adaptive_result in zip(records, frozen, adaptive, strict=True)
    )
    protocol = _protocol_payload(training_seeds, evaluation_seeds, blocked_seeds)
    report = _build_report(
        records=records,
        outcomes=outcomes,
        steps=steps,
        training_seeds=training_seeds,
        evaluation_seeds=evaluation_seeds,
        blocked_seeds=blocked_seeds,
        frozen_updates=resolved.evaluation_update_count,
        adaptive_updates=adaptive_controller.transition_count,
    )
    return Week9ParallelComparisonResult(
        protocol=protocol,
        steps=steps,
        scenarios=outcomes,
        report=report,
    )


@dataclass(frozen=True, slots=True)
class _RolloutResult:
    record: ContributionRecord
    scenario_kind: ScenarioKind
    success: bool
    steps: int
    failure_reason: str | None
    loop_detected: bool


def _counterfactual_steps(
    records: tuple[ContributionRecord, ...],
    scenarios: tuple[NurseryScenario, ...],
    controller: GoalConditionedNDNRAController,
) -> tuple[Week9ComparisonStep, ...]:
    steps: list[Week9ComparisonStep] = []
    global_step = 0
    for record, scenario in zip(records, scenarios, strict=True):
        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=f"{record.contribution_id}-fair-counterfactual",
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )
        goal = goal_from_request(record.request, scenario_context=record.scenario_context)
        kind = _scenario_kind(record)
        for scenario_step, action_code in enumerate(record.action_trace):
            default_action = PrimitiveAction(action_code)
            before = runtime.state
            available = runtime.observe().available_actions
            proposal = controller.propose(
                before,
                available,
                goal,
                remaining_steps=scenario.remaining_steps(before),
            )
            category, default_progress, ndnra_progress, default_generic, ndnra_generic = (
                _compare_actions(scenario, before, default_action, proposal.action, goal)
            )
            steps.append(
                Week9ComparisonStep(
                    contribution_id=record.contribution_id,
                    scenario_id=scenario.scenario_id,
                    scenario_kind=kind,
                    step_index=global_step,
                    scenario_step_index=scenario_step,
                    default_action=default_action,
                    ndnra_action=proposal.action,
                    ndnra_proposal=proposal,
                    default_task_progress=default_progress,
                    ndnra_task_progress=ndnra_progress,
                    default_generic_score=default_generic,
                    ndnra_generic_score=ndnra_generic,
                    category=category,
                )
            )
            collect_experience(runtime, default_action)
            global_step += 1
    return tuple(steps)


def _rollout(
    record: ContributionRecord,
    scenario: NurseryScenario,
    controller: GoalConditionedNDNRAController,
    *,
    adaptive: bool,
) -> _RolloutResult:
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{record.contribution_id}-ndnra-{'adaptive' if adaptive else 'frozen'}",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    goal = goal_from_request(record.request, scenario_context=record.scenario_context)
    visited: set[tuple[GridPosition, Direction, GridPosition]] = set()
    steps = 0
    failure_reason: str | None = None
    loop = False
    while scenario.remaining_steps(runtime.state) > 0:
        if _goal_satisfied(runtime.state, goal):
            break
        state_key = (
            runtime.state.agent.position,
            runtime.state.agent.orientation,
            _entity_position(runtime.state, goal.target_object_id),
        )
        if state_key in visited:
            loop = True
            failure_reason = "repeated_state_loop"
            break
        visited.add(state_key)
        before = runtime.state
        available = runtime.observe().available_actions
        proposal = controller.propose(
            before,
            available,
            goal,
            remaining_steps=scenario.remaining_steps(before),
        )
        if proposal.action is None:
            failure_reason = proposal.reason_code
            break
        collect_experience(runtime, proposal.action)
        steps += 1
        if adaptive:
            controller.observe_transition(
                before=before,
                after=runtime.state,
                action=proposal.action,
                goal=goal,
                available_actions=available,
                remaining_steps=scenario.remaining_steps(before),
                source="ndnra_adaptive",
            )
    success = _goal_satisfied(runtime.state, goal)
    if not success and failure_reason is None:
        failure_reason = "step_budget_exhausted"
    return _RolloutResult(
        record=record,
        scenario_kind=_scenario_kind(record),
        success=success,
        steps=steps,
        failure_reason=None if success else failure_reason,
        loop_detected=loop,
    )


def _scenario_outcome(
    record: ContributionRecord,
    frozen: _RolloutResult,
    adaptive: _RolloutResult,
) -> Week9ScenarioOutcome:
    kind = _scenario_kind(record)
    return Week9ScenarioOutcome(
        contribution_id=record.contribution_id,
        scenario_id=record.scenario_id,
        scenario_kind=kind,
        default_success=record.success,
        ndnra_frozen_success=frozen.success,
        ndnra_adaptive_success=adaptive.success,
        default_steps=record.executed_steps,
        ndnra_frozen_steps=frozen.steps,
        ndnra_adaptive_steps=adaptive.steps,
        ndnra_frozen_failure_reason=frozen.failure_reason,
        ndnra_adaptive_failure_reason=adaptive.failure_reason,
        blocked_honest_default_failure=(kind is ScenarioKind.BLOCKED and not record.success),
        blocked_honest_ndnra_failure=(
            kind is ScenarioKind.BLOCKED
            and not frozen.success
            and frozen.failure_reason is not None
        ),
        ndnra_loop_detected=frozen.loop_detected or adaptive.loop_detected,
    )


def _compare_actions(
    scenario: NurseryScenario,
    state: NurseryState,
    default_action: PrimitiveAction,
    ndnra_action: PrimitiveAction | None,
    goal: Week9ContributionGoal,
) -> tuple[TaskProgressCategory, float | None, float | None, float | None, float | None]:
    if ndnra_action is None:
        return (TaskProgressCategory.NOT_COMPARABLE, None, None, None, None)
    default_progress = _action_progress(scenario, state, default_action, goal)
    ndnra_progress = _action_progress(scenario, state, ndnra_action, goal)
    signals = _comparison_signals(scenario.remaining_steps(state), scenario.step_budget)
    oracle = NurseryOutcomeOracle(scenario)
    default_generic = oracle.evaluate(state, default_action, signals).score
    ndnra_generic = oracle.evaluate(state, ndnra_action, signals).score
    if default_progress > ndnra_progress:
        category = TaskProgressCategory.DEFAULT_BETTER
    elif ndnra_progress > default_progress:
        category = TaskProgressCategory.NDNRA_BETTER
    elif (
        default_progress == 0.0
        and ndnra_progress == 0.0
        and abs(default_generic - ndnra_generic) > 1e-12
    ):
        category = TaskProgressCategory.GENERIC_ONLY
    else:
        category = TaskProgressCategory.EQUIVALENT
    return category, default_progress, ndnra_progress, default_generic, ndnra_generic


def _build_report(
    *,
    records: tuple[ContributionRecord, ...],
    outcomes: tuple[Week9ScenarioOutcome, ...],
    steps: tuple[Week9ComparisonStep, ...],
    training_seeds: tuple[int, ...],
    evaluation_seeds: tuple[int, ...],
    blocked_seeds: tuple[int, ...],
    frozen_updates: int,
    adaptive_updates: int,
) -> Week9FairComparisonReport:
    solvable = tuple(
        outcome for outcome in outcomes if outcome.scenario_kind is ScenarioKind.SOLVABLE
    )
    blocked = tuple(
        outcome for outcome in outcomes if outcome.scenario_kind is ScenarioKind.BLOCKED
    )
    task_counts = {
        category: sum(step.category is category for step in steps)
        for category in TaskProgressCategory
    }
    integrity = (
        len(set(training_seeds).intersection(evaluation_seeds)) == 0
        and frozen_updates == 0
        and bool(steps)
        and all(step.ndnra_proposal.goal is not None for step in steps)
        and all(step.ndnra_proposal.features.available_actions for step in steps)
    )
    default_competence = _rate(
        sum(outcome.default_success for outcome in solvable), len(solvable)
    ) >= 0.80 and all(outcome.blocked_honest_default_failure for outcome in blocked)
    ndnra_successes = sum(outcome.ndnra_frozen_success for outcome in solvable)
    ndnra_competence = len(solvable) > 0 and _rate(ndnra_successes, len(solvable)) >= 0.80
    blocked_pass = all(outcome.blocked_honest_default_failure for outcome in blocked) and all(
        outcome.blocked_honest_ndnra_failure for outcome in blocked
    )
    authority_pass = True
    week9_main = sum(record.success for record in records) / len(records) >= 0.80 and all(
        record.authority_audit.accepted for record in records
    )
    return Week9FairComparisonReport(
        training_seeds=training_seeds,
        evaluation_seeds=evaluation_seeds,
        blocked_evaluation_seeds=blocked_seeds,
        evaluation_seed_overlap_count=len(set(training_seeds).intersection(evaluation_seeds)),
        default_solvable_successes=sum(outcome.default_success for outcome in solvable),
        default_solvable_attempts=len(solvable),
        ndnra_frozen_solvable_successes=ndnra_successes,
        ndnra_frozen_solvable_attempts=len(solvable),
        ndnra_adaptive_solvable_successes=sum(
            outcome.ndnra_adaptive_success for outcome in solvable
        ),
        ndnra_adaptive_solvable_attempts=len(solvable),
        blocked_scenarios=len(blocked),
        blocked_default_honest_failures=sum(
            outcome.blocked_honest_default_failure for outcome in blocked
        ),
        blocked_ndnra_honest_failures=sum(
            outcome.blocked_honest_ndnra_failure for outcome in blocked
        ),
        task_progress_default_better=task_counts[TaskProgressCategory.DEFAULT_BETTER],
        task_progress_ndnra_better=task_counts[TaskProgressCategory.NDNRA_BETTER],
        task_equivalent=task_counts[TaskProgressCategory.EQUIVALENT],
        generic_score_only_difference=task_counts[TaskProgressCategory.GENERIC_ONLY],
        not_comparable=task_counts[TaskProgressCategory.NOT_COMPARABLE],
        frozen_evaluation_updates=frozen_updates,
        adaptive_ndnra_updates=adaptive_updates,
        authority_violations=0,
        automatic_promotions=0,
        experiment_integrity_pass=integrity,
        default_competence_pass=default_competence,
        ndnra_competence_pass=ndnra_competence,
        blocked_scenario_handling_pass=blocked_pass,
        authority_containment_pass=authority_pass,
        week9_main_milestone_pass=week9_main,
    )


def _protocol_payload(
    training_seeds: tuple[int, ...],
    evaluation_seeds: tuple[int, ...],
    blocked_seeds: tuple[int, ...],
) -> dict[str, object]:
    return {
        "action_budgets_matched": True,
        "blocked_scenarios_reported_separately": True,
        "comparison_type": "frozen held-out Default-vs-goal-conditioned-NDNRA",
        "default_goal_information": "typed Week 9 human contribution request",
        "evaluation_seeds": list(evaluation_seeds),
        "generic_scores_separated_from_task_competence": True,
        "ndnra_goal_information": "same object, target, outcome, completion condition, and context",
        "ndnra_state_context": [
            "agent position",
            "agent orientation",
            "target-object position",
            "destination-target position",
            "object-to-target relative direction and distance",
            "agent-to-object relative direction and distance",
            "alignment, behind/contact, useful-push, blockers, target occupancy, resource budget",
        ],
        "ndnra_training_source": "NDNRA-executed sandbox transitions only",
        "remaining_asymmetries": [
            "Default uses compiled Week 8 skill record.",
            "NDNRA uses a bounded relational adapter and local action-value evidence.",
        ],
        "same_initial_state_and_request": True,
        "solvable_evaluation_seeds": [
            seed for seed in evaluation_seeds if seed not in set(blocked_seeds)
        ],
        "blocked_evaluation_seeds": list(blocked_seeds),
        "training_evaluation_disjoint": len(set(training_seeds).intersection(evaluation_seeds))
        == 0,
        "training_seeds": list(training_seeds),
    }


def _scenario_kind(record: ContributionRecord) -> ScenarioKind:
    return (
        ScenarioKind.BLOCKED
        if record.executed_steps == 0 and not record.success
        else ScenarioKind.SOLVABLE
    )


def _action_progress(
    scenario: NurseryScenario,
    state: NurseryState,
    action: PrimitiveAction,
    goal: Week9ContributionGoal,
) -> float:
    before_distance = _distance(state, goal.target_object_id, goal.destination_target_id)
    after_state = _apply_action_with_processes(scenario, state, action)
    after_distance = _distance(after_state, goal.target_object_id, goal.destination_target_id)
    if before_distance == 0:
        return 1.0 if after_distance == 0 else -1.0
    return _clamp_signed((before_distance - after_distance) / before_distance)


def _apply_action_clone(state: NurseryState, action: PrimitiveAction) -> NurseryState:
    return NurseryTransitionEngine().apply(state, action).state


def _apply_action_with_processes(
    scenario: NurseryScenario, state: NurseryState, action: PrimitiveAction
) -> NurseryState:
    after = _apply_action_clone(state, action)
    if after.terminated:
        return after
    return WorldProcessPipeline(scenario.world_processes).advance(after).state


def _goal_satisfied(state: NurseryState, goal: Week9ContributionGoal) -> bool:
    return _entity_position(state, goal.target_object_id) == _entity_position(
        state, goal.destination_target_id
    )


def _entity_position(state: NurseryState, entity_id: str) -> GridPosition:
    return next(entity.position for entity in state.entities if entity.entity_id == entity_id)


def _distance(state: NurseryState, object_id: str, target_id: str) -> int:
    object_position = _entity_position(state, object_id)
    target_position = _entity_position(state, target_id)
    return abs(object_position.x - target_position.x) + abs(object_position.y - target_position.y)


def _dominant_direction(source: GridPosition, destination: GridPosition) -> Direction:
    dx = destination.x - source.x
    dy = destination.y - source.y
    if abs(dx) >= abs(dy) and dx > 0:
        return Direction.EAST
    if abs(dx) >= abs(dy) and dx < 0:
        return Direction.WEST
    if dy > 0:
        return Direction.SOUTH
    return Direction.NORTH


def _comparison_signals(remaining_steps: int, step_budget: int) -> LiveDevelopmentalSignals:
    resource_pressure = 1.0 - (remaining_steps / step_budget)
    return LiveDevelopmentalSignals(
        step_index=max(0, step_budget - remaining_steps),
        ambition_relevance=1.0,
        ambition_commitment=1.0,
        ambition_learning_progress=0.5,
        curiosity_value=0.5,
        curiosity_learning_progress=0.25,
        curiosity_uncertainty=0.5,
        self_controllability=0.5,
        body_confidence=0.5,
        help_requested=0.0,
        human_approval=0.0,
        human_correction=0.0,
        human_demonstration=0.0,
        human_clarification=0.0,
        human_signal_magnitude=0.0,
        prediction_error=0.5,
        resource_pressure=resource_pressure,
        need_resolution=0.0,
    )


def _rate(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def _clamp_signed(value: float) -> float:
    if not isfinite(value):
        raise ValueError("score must be finite")
    return max(-1.0, min(1.0, value))
