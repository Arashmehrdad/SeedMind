"""Deterministic primitive-action transitions for SeedMind Nursery v0."""

from dataclasses import dataclass, replace
from enum import StrEnum

from seedmind.contracts import PrimitiveAction
from seedmind.environment.state import NurseryState


class TransitionOutcome(StrEnum):
    """Internal diagnostic outcome for one primitive action.

    These values are not part of the observation delivered to SeedMind.
    """

    TURNED_LEFT = "turned_left"
    TURNED_RIGHT = "turned_right"
    MOVED = "moved"
    MOVE_BLOCKED_BOUNDARY = "move_blocked_boundary"
    MOVE_BLOCKED_ENTITY = "move_blocked_entity"
    INSPECTED = "inspected"
    PUSHED = "pushed"
    PUSH_NO_CONTACT = "push_no_contact"
    PUSH_IMMOVABLE = "push_immovable"
    PUSH_BLOCKED_BOUNDARY = "push_blocked_boundary"
    PUSH_BLOCKED_ENTITY = "push_blocked_entity"
    WAITED = "waited"
    HELP_REQUESTED = "help_requested"
    ACKNOWLEDGED = "acknowledged"
    STOPPED = "stopped"
    ALREADY_TERMINATED = "already_terminated"


@dataclass(frozen=True, slots=True)
class NurseryTransition:
    """Result of applying one primitive action to a nursery state."""

    action: PrimitiveAction
    outcome: TransitionOutcome
    state: NurseryState
    world_changed: bool


@dataclass(frozen=True, slots=True)
class NurseryTransitionEngine:
    """Apply deterministic primitive actions without reward or task logic."""

    def apply(
        self,
        state: NurseryState,
        action: PrimitiveAction,
    ) -> NurseryTransition:
        """Return the deterministic transition for one primitive action."""
        if state.terminated:
            return NurseryTransition(
                action=action,
                outcome=TransitionOutcome.ALREADY_TERMINATED,
                state=state,
                world_changed=False,
            )

        if action is PrimitiveAction.TURN_LEFT:
            return self._complete(
                state=state.with_agent(state.agent.turned_left()),
                action=action,
                outcome=TransitionOutcome.TURNED_LEFT,
                world_changed=True,
            )

        if action is PrimitiveAction.TURN_RIGHT:
            return self._complete(
                state=state.with_agent(state.agent.turned_right()),
                action=action,
                outcome=TransitionOutcome.TURNED_RIGHT,
                world_changed=True,
            )

        if action is PrimitiveAction.MOVE_FORWARD:
            return self._move_forward(state)

        if action is PrimitiveAction.PUSH:
            return self._push(state)

        if action is PrimitiveAction.INSPECT:
            return self._complete(
                state=state,
                action=action,
                outcome=TransitionOutcome.INSPECTED,
                world_changed=False,
            )

        if action is PrimitiveAction.WAIT:
            return self._complete(
                state=state,
                action=action,
                outcome=TransitionOutcome.WAITED,
                world_changed=False,
            )

        if action is PrimitiveAction.REQUEST_HELP:
            return self._complete(
                state=state,
                action=action,
                outcome=TransitionOutcome.HELP_REQUESTED,
                world_changed=False,
            )

        if action is PrimitiveAction.ACKNOWLEDGE:
            return self._complete(
                state=state,
                action=action,
                outcome=TransitionOutcome.ACKNOWLEDGED,
                world_changed=False,
            )

        if action is PrimitiveAction.STOP:
            return self._complete(
                state=replace(state, terminated=True),
                action=action,
                outcome=TransitionOutcome.STOPPED,
                world_changed=True,
            )

        raise AssertionError(f"Unhandled primitive action: {action!r}")

    def _move_forward(self, state: NurseryState) -> NurseryTransition:
        destination = state.agent.position.moved(state.agent.orientation)

        if not state.is_in_bounds(destination):
            return self._complete(
                state=state,
                action=PrimitiveAction.MOVE_FORWARD,
                outcome=TransitionOutcome.MOVE_BLOCKED_BOUNDARY,
                world_changed=False,
            )

        if state.blocking_entity_at(destination) is not None:
            return self._complete(
                state=state,
                action=PrimitiveAction.MOVE_FORWARD,
                outcome=TransitionOutcome.MOVE_BLOCKED_ENTITY,
                world_changed=False,
            )

        return self._complete(
            state=state.with_agent(state.agent.moved_forward()),
            action=PrimitiveAction.MOVE_FORWARD,
            outcome=TransitionOutcome.MOVED,
            world_changed=True,
        )

    def _push(self, state: NurseryState) -> NurseryTransition:
        contact_position = state.agent.position.moved(state.agent.orientation)

        if not state.is_in_bounds(contact_position):
            return self._complete(
                state=state,
                action=PrimitiveAction.PUSH,
                outcome=TransitionOutcome.PUSH_NO_CONTACT,
                world_changed=False,
            )

        contacted = state.blocking_entity_at(contact_position)

        if contacted is None:
            return self._complete(
                state=state,
                action=PrimitiveAction.PUSH,
                outcome=TransitionOutcome.PUSH_NO_CONTACT,
                world_changed=False,
            )

        if not contacted.movable:
            return self._complete(
                state=state,
                action=PrimitiveAction.PUSH,
                outcome=TransitionOutcome.PUSH_IMMOVABLE,
                world_changed=False,
            )

        destination = contact_position.moved(state.agent.orientation)

        if not state.is_in_bounds(destination):
            return self._complete(
                state=state,
                action=PrimitiveAction.PUSH,
                outcome=TransitionOutcome.PUSH_BLOCKED_BOUNDARY,
                world_changed=False,
            )

        if state.blocking_entity_at(destination) is not None:
            return self._complete(
                state=state,
                action=PrimitiveAction.PUSH,
                outcome=TransitionOutcome.PUSH_BLOCKED_ENTITY,
                world_changed=False,
            )

        updated = state.replace_entity(
            entity_id=contacted.entity_id,
            replacement=contacted.moved_to(destination),
        )
        return self._complete(
            state=updated,
            action=PrimitiveAction.PUSH,
            outcome=TransitionOutcome.PUSHED,
            world_changed=True,
        )

    @staticmethod
    def _complete(
        *,
        state: NurseryState,
        action: PrimitiveAction,
        outcome: TransitionOutcome,
        world_changed: bool,
    ) -> NurseryTransition:
        """Advance one active-state timestep and package its outcome."""
        return NurseryTransition(
            action=action,
            outcome=outcome,
            state=state.advanced(),
            world_changed=world_changed,
        )
