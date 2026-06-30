"""Main SeedMind Week 8 approach-and-push skill implementation."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from enum import StrEnum

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import EntityRole, EntityState, NurseryState
from seedmind.skills.records import (
    SKILL_SCHEMA_VERSION,
    SkillAttemptSource,
    SkillCompileFailure,
    SkillCompileResult,
    SkillEpisodeEvidence,
    SkillRecord,
    SkillValidationStatus,
)

APPROACH_AND_PUSH_VERSION = "1.0.0"
APPROACH_AND_PUSH_POLICY = "axis_aligned_object_target_push_policy_v1"


class SkillExecutionStatus(StrEnum):
    """Step-level state for reusable skill execution."""

    ACTION = "action"
    TERMINATED = "terminated"
    FAILED = "failed"
    INTERRUPTED = "interrupted"


@dataclass(frozen=True, slots=True)
class SkillStepDecision:
    """One inspectable skill decision before production curiosity retention."""

    status: SkillExecutionStatus
    action: PrimitiveAction | None
    reason_code: str
    skill_invoked: bool
    production_authority: str = "production_curiosity"
    action_authority_violation: bool = False

    def __post_init__(self) -> None:
        if not self.reason_code.strip() or not self.reason_code.isascii():
            raise ValueError("reason_code must be non-empty ASCII")
        if self.status is SkillExecutionStatus.ACTION and self.action is None:
            raise ValueError("action status requires an action")
        if self.status is not SkillExecutionStatus.ACTION and self.action is not None:
            raise ValueError("non-action status cannot carry an action")
        if self.production_authority != "production_curiosity":
            raise ValueError("production curiosity must remain the action authority")
        if self.action_authority_violation:
            raise ValueError("skill decision cannot claim action authority")


@dataclass(frozen=True, slots=True)
class ProductionSkillAction:
    """Primitive action retained by the production curiosity boundary."""

    decision: SkillStepDecision
    retained_action: PrimitiveAction | None
    retained_by: str = "production_curiosity"

    def __post_init__(self) -> None:
        if self.retained_by != "production_curiosity":
            raise ValueError("compiled skills cannot bypass production curiosity")
        if self.decision.action is not self.retained_action:
            raise ValueError("retained action must match the skill candidate exactly")


def retain_skill_candidate_through_curiosity(decision: SkillStepDecision) -> ProductionSkillAction:
    """Retain one reusable-skill candidate through the production boundary."""
    return ProductionSkillAction(decision=decision, retained_action=decision.action)


def compile_approach_and_push_skill(
    evidence: tuple[SkillEpisodeEvidence, ...],
    *,
    compilation_threshold: int = 3,
) -> SkillCompileResult:
    """Compile the Week 8 main skill from repeated grounded success episodes."""
    if compilation_threshold <= 1:
        raise ValueError("compilation threshold must require repeated evidence")
    if not evidence:
        return SkillCompileResult(None, SkillCompileFailure.INSUFFICIENT_EVIDENCE)

    target_pairs = {(episode.target_object_id, episode.target_id) for episode in evidence}
    if len(target_pairs) != 1:
        return SkillCompileResult(None, SkillCompileFailure.CONTRADICTORY_SEQUENCE)

    if any(
        episode.source is not SkillAttemptSource.GROUNDED_PRODUCTION or episode.used_for_evaluation
        for episode in evidence
    ):
        return SkillCompileResult(None, SkillCompileFailure.NON_GROUNDED_SOURCE)

    if any(
        not step.action_available or step.action is PrimitiveAction.STOP
        for episode in evidence
        for step in episode.steps
    ):
        return SkillCompileResult(None, SkillCompileFailure.UNSAFE_OR_UNAVAILABLE_ACTION)

    successful = tuple(episode for episode in evidence if episode.success)
    if len(successful) < compilation_threshold:
        return SkillCompileResult(None, SkillCompileFailure.INSUFFICIENT_EVIDENCE)

    if any(not episode.has_approach_contact_push_sequence for episode in successful):
        return SkillCompileResult(None, SkillCompileFailure.INCOMPLETE_SEQUENCE)

    target_object_id, target_id = next(iter(target_pairs))
    action_vocabulary = [
        action.value
        for action in (
            PrimitiveAction.TURN_LEFT,
            PrimitiveAction.TURN_RIGHT,
            PrimitiveAction.MOVE_FORWARD,
            PrimitiveAction.PUSH,
        )
    ]
    record = SkillRecord(
        skill_id="skill.main.approach_and_push.v1",
        name="approach_and_push",
        version=APPROACH_AND_PUSH_VERSION,
        schema_version=SKILL_SCHEMA_VERSION,
        provenance_episode_ids=tuple(episode.episode_id for episode in successful),
        provenance_seeds=tuple(episode.seed for episode in successful),
        preconditions=(
            "target_object_id exists",
            "target_id exists",
            "target_object_id is movable",
            "target object is not already incompatible with target task",
            "production curiosity remains action authority",
        ),
        primitive_policy=APPROACH_AND_PUSH_POLICY,
        expected_outcome="target_object_id occupies target_id position",
        termination_conditions=(
            "target object position equals target position",
            "scenario step budget remains non-negative",
        ),
        failure_conditions=(
            "preconditions break",
            "required primitive action is unavailable",
            "target object or target changes incompatibly",
            "no path to a legal pushing contact cell exists",
            "push would move the object outside the nursery or into a blocker",
            "environment changes unexpectedly during active reuse",
            "human or safety interruption is present",
        ),
        success_evidence_count=len(successful),
        attempt_evidence_count=len(evidence),
        compilation_threshold=compilation_threshold,
        reuse_count=0,
        discovery_count=len(evidence),
        last_validation_status=SkillValidationStatus.UNVALIDATED,
        deterministic_snapshot={
            "action_vocabulary": action_vocabulary,
            "compiler": "repeated_grounded_episode_compiler_v1",
            "policy": APPROACH_AND_PUSH_POLICY,
            "target_id": target_id,
            "target_object_id": target_object_id,
        },
    )
    return SkillCompileResult(record, None)


@dataclass(frozen=True, slots=True)
class ApproachAndPushSkillController:
    """Reusable policy compiled from Week 8 grounded evidence."""

    record: SkillRecord
    target_object_id: str = "object_0"
    target_id: str = "target_0"

    def __post_init__(self) -> None:
        if self.record.name != "approach_and_push":
            raise ValueError("controller requires an approach_and_push skill record")
        if self.record.primitive_policy != APPROACH_AND_PUSH_POLICY:
            raise ValueError("unsupported approach_and_push primitive policy")

    def decide(
        self,
        state: NurseryState,
        available_actions: tuple[PrimitiveAction, ...],
        *,
        human_interrupt: bool = False,
        external_world_changed: bool = False,
    ) -> SkillStepDecision:
        """Return the next primitive action candidate for production curiosity."""
        if human_interrupt:
            return _no_action(SkillExecutionStatus.INTERRUPTED, "human_or_safety_interrupt")
        if external_world_changed:
            return _no_action(SkillExecutionStatus.FAILED, "unexpected_environment_change")

        precondition_failure = self._precondition_failure(state)
        if precondition_failure is not None:
            return _no_action(SkillExecutionStatus.FAILED, precondition_failure)

        target_object = _require_entity(state, self.target_object_id)
        target = _require_entity(state, self.target_id)
        if target_object.position == target.position:
            return _no_action(SkillExecutionStatus.TERMINATED, "target_occupied")

        action = self._next_action(state, target_object, target)
        if action is None:
            return _no_action(SkillExecutionStatus.FAILED, "no_legal_approach_path")
        if action not in available_actions:
            return _no_action(SkillExecutionStatus.FAILED, "required_action_unavailable")
        return SkillStepDecision(
            status=SkillExecutionStatus.ACTION,
            action=action,
            reason_code="skill_candidate",
            skill_invoked=True,
        )

    def _precondition_failure(self, state: NurseryState) -> str | None:
        entity_ids = {entity.entity_id for entity in state.entities}
        if self.target_object_id not in entity_ids:
            return "target_object_missing"
        if self.target_id not in entity_ids:
            return "target_missing"

        target_object = _require_entity(state, self.target_object_id)
        target = _require_entity(state, self.target_id)
        snapshot = self.record.deterministic_snapshot
        if snapshot.get("target_object_id") != self.target_object_id:
            return "incompatible_target_object"
        if snapshot.get("target_id") != self.target_id:
            return "incompatible_target"
        if target_object.role is not EntityRole.OBJECT or not target_object.movable:
            return "target_object_not_movable"
        if target.role is not EntityRole.TARGET:
            return "target_role_incompatible"
        return None

    def _next_action(
        self,
        state: NurseryState,
        target_object: EntityState,
        target: EntityState,
    ) -> PrimitiveAction | None:
        desired_direction = _desired_push_direction(target_object.position, target.position)
        contact_position = _contact_position(target_object.position, desired_direction)
        push_destination = target_object.position.moved(desired_direction)
        if not state.is_in_bounds(contact_position) or not state.is_in_bounds(push_destination):
            return None
        blocker = state.blocking_entity_at(push_destination)
        if blocker is not None and blocker.entity_id != self.target_object_id:
            return None

        if state.agent.position == contact_position:
            return _turn_or_push(state.agent.orientation, desired_direction)

        route = _shortest_route(
            state,
            source=state.agent.position,
            destination=contact_position,
            blocked_entity_ids={self.target_object_id},
        )
        if route is None:
            return None
        next_position = route[0]
        direction = _direction_between(state.agent.position, next_position)
        return _turn_or_move(state.agent.orientation, direction)


def _no_action(status: SkillExecutionStatus, reason: str) -> SkillStepDecision:
    return SkillStepDecision(
        status=status,
        action=None,
        reason_code=reason,
        skill_invoked=status is not SkillExecutionStatus.FAILED,
    )


def _require_entity(state: NurseryState, entity_id: str) -> EntityState:
    for entity in state.entities:
        if entity.entity_id == entity_id:
            return entity
    raise KeyError(entity_id)


def _desired_push_direction(
    object_position: GridPosition, target_position: GridPosition
) -> Direction:
    if object_position.x < target_position.x:
        return Direction.EAST
    if object_position.x > target_position.x:
        return Direction.WEST
    if object_position.y < target_position.y:
        return Direction.SOUTH
    return Direction.NORTH


def _contact_position(object_position: GridPosition, direction: Direction) -> GridPosition:
    opposite = Direction((int(direction) + 2) % 4)
    return object_position.moved(opposite)


def _turn_or_push(current: Direction, desired: Direction) -> PrimitiveAction:
    if current is desired:
        return PrimitiveAction.PUSH
    return _turn_toward(current, desired)


def _turn_or_move(current: Direction, desired: Direction) -> PrimitiveAction:
    if current is desired:
        return PrimitiveAction.MOVE_FORWARD
    return _turn_toward(current, desired)


def _turn_toward(current: Direction, desired: Direction) -> PrimitiveAction:
    clockwise = (int(desired) - int(current)) % 4
    if clockwise == 1:
        return PrimitiveAction.TURN_RIGHT
    if clockwise == 3:
        return PrimitiveAction.TURN_LEFT
    return PrimitiveAction.TURN_RIGHT


def _direction_between(source: GridPosition, destination: GridPosition) -> Direction:
    dx = destination.x - source.x
    dy = destination.y - source.y
    for direction in Direction:
        if direction.delta == (dx, dy):
            return direction
    raise ValueError("positions are not adjacent")


def _shortest_route(
    state: NurseryState,
    *,
    source: GridPosition,
    destination: GridPosition,
    blocked_entity_ids: set[str],
) -> tuple[GridPosition, ...] | None:
    if source == destination:
        return ()
    blocked = {
        entity.position
        for entity in state.entities
        if entity.blocks_movement and entity.entity_id in blocked_entity_ids
    }
    blocked.update(
        entity.position
        for entity in state.entities
        if entity.blocks_movement
        and entity.entity_id not in blocked_entity_ids
        and entity.position != destination
    )
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
