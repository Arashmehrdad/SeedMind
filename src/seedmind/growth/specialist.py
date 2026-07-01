"""Bounded policy-specialist contract for original SeedMind Week 11."""

from __future__ import annotations

import hashlib
import json
from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from math import exp

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import EntityRole, NurseryState, ShapeCode

SPECIALIST_PARAMETER_NAMES = (
    "distance_progress_weight",
    "clearance_weight",
    "route_cost_weight",
    "direct_axis_bonus",
    "confidence_bias",
    "abstain_threshold",
)


class CandidateStatus(StrEnum):
    """Lifecycle state for a temporary Week 11 specialist."""

    INCUBATING = "incubating"
    ACCEPTED_FOR_WEEK12 = "accepted_for_week12"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class SpecialistLatentState:
    """Compact raw policy state reconstructed from the symbolic Nursery state."""

    width: int
    height: int
    agent_position: GridPosition
    agent_orientation: Direction
    object_position: GridPosition
    target_position: GridPosition
    blocked_positions: tuple[GridPosition, ...]
    raw_shape_feature: float

    @classmethod
    def from_nursery(cls, state: NurseryState) -> SpecialistLatentState:
        target_object = next(
            entity
            for entity in state.entities
            if entity.entity_id == "object_0" and entity.role is EntityRole.OBJECT
        )
        target = next(
            entity
            for entity in state.entities
            if entity.entity_id == "target_0" and entity.role is EntityRole.TARGET
        )
        blocked = tuple(
            sorted(
                (
                    entity.position
                    for entity in state.entities
                    if entity.blocks_movement and entity.entity_id != target_object.entity_id
                ),
                key=lambda position: (position.y, position.x),
            )
        )
        return cls(
            width=state.width,
            height=state.height,
            agent_position=state.agent.position,
            agent_orientation=state.agent.orientation,
            object_position=target_object.position,
            target_position=target.position,
            blocked_positions=blocked,
            raw_shape_feature=float(target_object.shape_code) / float(ShapeCode.ANGULAR),
        )

    @property
    def target_satisfied(self) -> bool:
        return self.object_position == self.target_position


@dataclass(frozen=True, slots=True)
class ExpertModuleInput:
    """Authoritative specialist input contract from the master plan."""

    latent_state: SpecialistLatentState
    current_goal: str
    relevant_memory_summary: tuple[str, ...]
    available_actions: tuple[PrimitiveAction, ...]


@dataclass(frozen=True, slots=True)
class ExpertModuleOutput:
    """Proposal-only specialist output; production curiosity retains authority."""

    action_proposal: PrimitiveAction | None
    confidence: float
    expected_result: str
    predicted_goal_progress: float
    abstain: bool
    reason_code: str
    proposal_authority: str = "proposal_only"
    action_authority_violation: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("confidence must be in [0, 1]")
        if not 0.0 <= self.predicted_goal_progress <= 1.0:
            raise ValueError("predicted_goal_progress must be in [0, 1]")
        if self.abstain != (self.action_proposal is None):
            raise ValueError("abstention and action proposal disagree")
        if self.proposal_authority != "proposal_only" or self.action_authority_violation:
            raise ValueError("specialist cannot claim production action authority")


@dataclass(frozen=True, slots=True)
class SpecialistProfile:
    """One deterministic policy-parameter profile evaluated in incubation."""

    profile_id: str
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if len(self.values) != len(SPECIALIST_PARAMETER_NAMES):
            raise ValueError("specialist profile has the wrong parameter count")
        if not self.profile_id.strip() or not self.profile_id.isascii():
            raise ValueError("profile_id must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        return {
            "profile_id": self.profile_id,
            "parameters": dict(zip(SPECIALIST_PARAMETER_NAMES, self.values, strict=True)),
        }


@dataclass(frozen=True, slots=True)
class CandidateSkillExpert:
    """Small clearance-aware policy expert selected by grounded comparison."""

    candidate_id: str
    parent_module: str
    profile: SpecialistProfile
    status: CandidateStatus = CandidateStatus.INCUBATING

    def __post_init__(self) -> None:
        if not self.candidate_id.strip() or not self.candidate_id.isascii():
            raise ValueError("candidate_id must be non-empty ASCII")
        if self.parent_module != "general_push_controller":
            raise ValueError("specialist must descend from general_push_controller")

    @property
    def added_parameter_count(self) -> int:
        return len(self.profile.values)

    @property
    def checkpoint_sha256(self) -> str:
        payload = {
            "candidate_id": self.candidate_id,
            "parent_module": self.parent_module,
            "profile": self.profile.to_json(),
            "status": self.status.value,
        }
        encoded = json.dumps(payload, sort_keys=True, separators=(",", ":")).encode("ascii")
        return hashlib.sha256(encoded).hexdigest()

    def with_status(self, status: CandidateStatus) -> CandidateSkillExpert:
        return CandidateSkillExpert(
            candidate_id=self.candidate_id,
            parent_module=self.parent_module,
            profile=self.profile,
            status=status,
        )

    def propose(self, module_input: ExpertModuleInput) -> ExpertModuleOutput:
        """Return one inspectable primitive-action proposal or abstain."""
        if module_input.current_goal != "control_angular_object_position":
            return _abstain("goal_outside_specialist_scope")
        latent = module_input.latent_state
        if latent.target_satisfied:
            return _abstain("goal_already_satisfied")
        selected = self._select_push_direction(latent)
        if selected is None:
            return _abstain("no_safe_effective_push_route")
        direction, score, predicted_progress = selected
        contact = latent.object_position.moved(_opposite(direction))
        route = _shortest_route(latent, latent.agent_position, contact)
        if route is None:
            return _abstain("contact_cell_unreachable")
        if latent.agent_position == contact:
            action = _turn_or_push(latent.agent_orientation, direction)
        else:
            action = _turn_or_move(
                latent.agent_orientation,
                _direction_between(latent.agent_position, route[0]),
            )
        if action not in module_input.available_actions:
            return _abstain("required_action_unavailable")
        if score < self.profile.values[5]:
            return _abstain("candidate_confidence_below_threshold")
        return ExpertModuleOutput(
            action_proposal=action,
            confidence=_sigmoid(score + self.profile.values[4]),
            expected_result=f"effective_push_toward_{direction.name.lower()}",
            predicted_goal_progress=predicted_progress,
            abstain=False,
            reason_code="clearance_aware_specialist_proposal",
        )

    def _select_push_direction(
        self,
        latent: SpecialistLatentState,
    ) -> tuple[Direction, float, float] | None:
        current_distance = _manhattan(latent.object_position, latent.target_position)
        direct_direction = _desired_direction(latent.object_position, latent.target_position)
        distance_weight, clearance_weight, route_weight, direct_bonus, _, _ = self.profile.values
        candidates: list[tuple[float, int, Direction, float]] = []
        for direction in Direction:
            destination = latent.object_position.moved(direction)
            contact = latent.object_position.moved(_opposite(direction))
            if not _in_bounds(latent, destination) or not _in_bounds(latent, contact):
                continue
            if destination in latent.blocked_positions or contact in latent.blocked_positions:
                continue
            route = _shortest_route(latent, latent.agent_position, contact)
            if route is None:
                continue
            effective = _push_contact_effective(latent, direction)
            progress = float(current_distance - _manhattan(destination, latent.target_position))
            score = (
                distance_weight * progress
                + clearance_weight * (1.0 if effective else -1.0)
                - route_weight * float(len(route))
                + (direct_bonus if direction is direct_direction else 0.0)
            )
            normalized = max(0.0, progress) / max(1.0, float(current_distance))
            candidates.append((score, -int(direction), direction, normalized))
        if not candidates:
            return None
        score, _, direction, progress = max(candidates)
        if not _push_contact_effective(latent, direction):
            return None
        return direction, score, progress


def _abstain(reason: str) -> ExpertModuleOutput:
    return ExpertModuleOutput(None, 0.0, "no_specialist_action", 0.0, True, reason)


def _desired_direction(source: GridPosition, target: GridPosition) -> Direction:
    if source.x < target.x:
        return Direction.EAST
    if source.x > target.x:
        return Direction.WEST
    if source.y < target.y:
        return Direction.SOUTH
    return Direction.NORTH


def _push_contact_effective(latent: SpecialistLatentState, direction: Direction) -> bool:
    destination = latent.object_position.moved(direction)
    if destination in latent.blocked_positions or not _in_bounds(latent, destination):
        return False
    if latent.raw_shape_feature < 0.75:
        return True
    positions = _lateral_positions(latent.object_position, direction) + _lateral_positions(
        destination, direction
    )
    return all(
        _in_bounds(latent, position) and position not in latent.blocked_positions
        for position in positions
    )


def _lateral_positions(position: GridPosition, direction: Direction) -> tuple[GridPosition, ...]:
    if direction in (Direction.NORTH, Direction.SOUTH):
        return (position.moved(Direction.EAST), position.moved(Direction.WEST))
    return (position.moved(Direction.NORTH), position.moved(Direction.SOUTH))


def _shortest_route(
    latent: SpecialistLatentState,
    source: GridPosition,
    destination: GridPosition,
) -> tuple[GridPosition, ...] | None:
    if source == destination:
        return ()
    blocked = {*latent.blocked_positions, latent.object_position}
    blocked.discard(destination)
    queue: deque[tuple[GridPosition, tuple[GridPosition, ...]]] = deque([(source, ())])
    visited = {source}
    while queue:
        position, path = queue.popleft()
        for direction in Direction:
            candidate = position.moved(direction)
            if candidate in visited or candidate in blocked or not _in_bounds(latent, candidate):
                continue
            candidate_path = (*path, candidate)
            if candidate == destination:
                return candidate_path
            visited.add(candidate)
            queue.append((candidate, candidate_path))
    return None


def _in_bounds(latent: SpecialistLatentState, position: GridPosition) -> bool:
    return 0 <= position.x < latent.width and 0 <= position.y < latent.height


def _opposite(direction: Direction) -> Direction:
    return Direction((int(direction) + 2) % 4)


def _turn_or_push(current: Direction, desired: Direction) -> PrimitiveAction:
    return PrimitiveAction.PUSH if current is desired else _turn_toward(current, desired)


def _turn_or_move(current: Direction, desired: Direction) -> PrimitiveAction:
    return PrimitiveAction.MOVE_FORWARD if current is desired else _turn_toward(current, desired)


def _turn_toward(current: Direction, desired: Direction) -> PrimitiveAction:
    clockwise = (int(desired) - int(current)) % 4
    if clockwise == 1:
        return PrimitiveAction.TURN_RIGHT
    if clockwise == 3:
        return PrimitiveAction.TURN_LEFT
    return PrimitiveAction.TURN_RIGHT


def _direction_between(source: GridPosition, destination: GridPosition) -> Direction:
    delta = (destination.x - source.x, destination.y - source.y)
    return next(direction for direction in Direction if direction.delta == delta)


def _manhattan(first: GridPosition, second: GridPosition) -> int:
    return abs(first.x - second.x) + abs(first.y - second.y)


def _sigmoid(value: float) -> float:
    if value >= 0.0:
        return 1.0 / (1.0 + exp(-value))
    exponential = exp(value)
    return exponential / (1.0 + exponential)
