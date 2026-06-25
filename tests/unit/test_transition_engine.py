"""Tests for deterministic Nursery v0 primitive-action transitions."""

from dataclasses import replace

import pytest

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.environment import (
    AgentState,
    EntityRole,
    EntityState,
    NurseryState,
    NurseryTransitionEngine,
    ShapeCode,
    TransitionOutcome,
)


def make_entity(
    *,
    entity_id: str,
    position: GridPosition,
    movable: bool,
    blocks_movement: bool = True,
    role: EntityRole = EntityRole.OBJECT,
) -> EntityState:
    return EntityState(
        entity_id=entity_id,
        role=role,
        position=position,
        blocks_movement=blocks_movement,
        movable=movable,
        shape_code=ShapeCode.ROUND,
    )


def make_state(
    *,
    position: GridPosition | None = None,
    orientation: Direction = Direction.EAST,
    entities: tuple[EntityState, ...] = (),
    terminated: bool = False,
) -> NurseryState:
    body_position = GridPosition(1, 1) if position is None else position
    return NurseryState(
        width=4,
        height=4,
        agent=AgentState(position=body_position, orientation=orientation),
        entities=entities,
        step_count=2,
        terminated=terminated,
    )


def test_turn_changes_orientation_and_advances_one_step() -> None:
    engine = NurseryTransitionEngine()
    state = make_state(orientation=Direction.NORTH)

    transition = engine.apply(state, PrimitiveAction.TURN_LEFT)

    assert transition.outcome is TransitionOutcome.TURNED_LEFT
    assert transition.state.agent.orientation is Direction.WEST
    assert transition.state.agent.position == state.agent.position
    assert transition.state.step_count == 3
    assert transition.world_changed is True
    assert state.step_count == 2


def test_move_forward_changes_position() -> None:
    engine = NurseryTransitionEngine()
    state = make_state()

    transition = engine.apply(state, PrimitiveAction.MOVE_FORWARD)

    assert transition.outcome is TransitionOutcome.MOVED
    assert transition.state.agent.position == GridPosition(2, 1)
    assert transition.state.step_count == 3
    assert transition.world_changed is True


def test_move_is_blocked_by_boundary() -> None:
    engine = NurseryTransitionEngine()
    state = make_state(
        position=GridPosition(0, 1),
        orientation=Direction.WEST,
    )

    transition = engine.apply(state, PrimitiveAction.MOVE_FORWARD)

    assert transition.outcome is TransitionOutcome.MOVE_BLOCKED_BOUNDARY
    assert transition.state.agent == state.agent
    assert transition.state.step_count == 3
    assert transition.world_changed is False


def test_move_is_blocked_by_entity() -> None:
    engine = NurseryTransitionEngine()
    blocker = make_entity(
        entity_id="blocker",
        position=GridPosition(2, 1),
        movable=True,
    )
    state = make_state(entities=(blocker,))

    transition = engine.apply(state, PrimitiveAction.MOVE_FORWARD)

    assert transition.outcome is TransitionOutcome.MOVE_BLOCKED_ENTITY
    assert transition.state.agent == state.agent
    assert transition.world_changed is False


def test_push_moves_adjacent_movable_entity_without_moving_agent() -> None:
    engine = NurseryTransitionEngine()
    pushed = make_entity(
        entity_id="movable",
        position=GridPosition(2, 1),
        movable=True,
    )
    state = make_state(entities=(pushed,))

    transition = engine.apply(state, PrimitiveAction.PUSH)

    assert transition.outcome is TransitionOutcome.PUSHED
    assert transition.state.entities[0].position == GridPosition(3, 1)
    assert transition.state.agent == state.agent
    assert transition.state.step_count == 3
    assert transition.world_changed is True
    assert state.entities[0].position == GridPosition(2, 1)


def test_push_can_move_object_onto_non_blocking_target_cell() -> None:
    engine = NurseryTransitionEngine()
    pushed = make_entity(
        entity_id="movable",
        position=GridPosition(2, 1),
        movable=True,
    )
    target = make_entity(
        entity_id="target",
        position=GridPosition(3, 1),
        movable=False,
        blocks_movement=False,
        role=EntityRole.TARGET,
    )
    state = make_state(entities=(pushed, target))

    transition = engine.apply(state, PrimitiveAction.PUSH)

    assert transition.outcome is TransitionOutcome.PUSHED
    assert len(transition.state.entities_at(GridPosition(3, 1))) == 2


@pytest.mark.parametrize(
    ("state", "expected"),
    [
        (make_state(), TransitionOutcome.PUSH_NO_CONTACT),
        (
            make_state(
                entities=(
                    make_entity(
                        entity_id="wall",
                        position=GridPosition(2, 1),
                        movable=False,
                        role=EntityRole.WALL,
                    ),
                )
            ),
            TransitionOutcome.PUSH_IMMOVABLE,
        ),
        (
            make_state(
                position=GridPosition(2, 1),
                entities=(
                    make_entity(
                        entity_id="edge-object",
                        position=GridPosition(3, 1),
                        movable=True,
                    ),
                ),
            ),
            TransitionOutcome.PUSH_BLOCKED_BOUNDARY,
        ),
        (
            make_state(
                entities=(
                    make_entity(
                        entity_id="movable",
                        position=GridPosition(2, 1),
                        movable=True,
                    ),
                    make_entity(
                        entity_id="blocker",
                        position=GridPosition(3, 1),
                        movable=False,
                    ),
                )
            ),
            TransitionOutcome.PUSH_BLOCKED_ENTITY,
        ),
    ],
)
def test_push_failure_outcomes(
    state: NurseryState,
    expected: TransitionOutcome,
) -> None:
    engine = NurseryTransitionEngine()

    transition = engine.apply(state, PrimitiveAction.PUSH)

    assert transition.outcome is expected
    assert transition.state.agent == state.agent
    assert transition.state.entities == state.entities
    assert transition.state.step_count == 3
    assert transition.world_changed is False


@pytest.mark.parametrize(
    ("action", "expected"),
    [
        (PrimitiveAction.INSPECT, TransitionOutcome.INSPECTED),
        (PrimitiveAction.WAIT, TransitionOutcome.WAITED),
        (PrimitiveAction.REQUEST_HELP, TransitionOutcome.HELP_REQUESTED),
        (PrimitiveAction.ACKNOWLEDGE, TransitionOutcome.ACKNOWLEDGED),
    ],
)
def test_non_physical_actions_advance_without_world_change(
    action: PrimitiveAction,
    expected: TransitionOutcome,
) -> None:
    engine = NurseryTransitionEngine()
    state = make_state()

    transition = engine.apply(state, action)

    assert transition.outcome is expected
    assert transition.state.agent == state.agent
    assert transition.state.entities == state.entities
    assert transition.state.step_count == 3
    assert transition.world_changed is False


def test_stop_terminates_episode() -> None:
    engine = NurseryTransitionEngine()
    state = make_state()

    transition = engine.apply(state, PrimitiveAction.STOP)

    assert transition.outcome is TransitionOutcome.STOPPED
    assert transition.state.terminated is True
    assert transition.state.step_count == 3
    assert transition.world_changed is True


def test_terminated_state_is_stable() -> None:
    engine = NurseryTransitionEngine()
    state = make_state(terminated=True)

    transition = engine.apply(state, PrimitiveAction.MOVE_FORWARD)

    assert transition.outcome is TransitionOutcome.ALREADY_TERMINATED
    assert transition.state is state
    assert transition.state.step_count == 2
    assert transition.world_changed is False


def test_same_state_and_action_produce_identical_transition() -> None:
    engine = NurseryTransitionEngine()
    state = make_state(
        entities=(
            make_entity(
                entity_id="movable",
                position=GridPosition(2, 1),
                movable=True,
            ),
        )
    )

    first = engine.apply(state, PrimitiveAction.PUSH)
    second = engine.apply(replace(state), PrimitiveAction.PUSH)

    assert first == second
