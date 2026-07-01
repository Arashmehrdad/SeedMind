"""Named, disjoint evaluation scenarios for original SeedMind Week 12."""

from __future__ import annotations

from dataclasses import dataclass

from seedmind.contracts import Direction, GridPosition
from seedmind.environment import AgentState, EntityRole, EntityState, NurseryState, ShapeCode

BALL_RETENTION_SEEDS = tuple(range(1200, 1240))
ANGULAR_TRANSFER_SEEDS = tuple(range(1300, 1332))
WEEK12_STEP_BUDGET = 64


@dataclass(frozen=True, slots=True)
class AngularTransferVariant:
    """One inspectable angular-object transfer geometry."""

    variant_id: str
    description: str
    object_position: GridPosition
    target_position: GridPosition
    blocker_positions: tuple[GridPosition, ...]

    def to_json(self) -> dict[str, object]:
        return {
            "blocker_positions": [_position_json(position) for position in self.blocker_positions],
            "description": self.description,
            "object_position": _position_json(self.object_position),
            "target_position": _position_json(self.target_position),
            "variant_id": self.variant_id,
        }


ANGULAR_TRANSFER_VARIANTS = (
    AngularTransferVariant(
        "east_north_contact_block",
        "Target is east; a north-side blocker invalidates the direct east contact.",
        GridPosition(3, 3),
        GridPosition(6, 3),
        (GridPosition(4, 2),),
    ),
    AngularTransferVariant(
        "east_south_contact_block",
        "Target is east; a south-side blocker invalidates the direct east contact.",
        GridPosition(3, 3),
        GridPosition(6, 3),
        (GridPosition(4, 4),),
    ),
    AngularTransferVariant(
        "west_north_contact_block",
        "Target is west; a north-side blocker invalidates the direct west contact.",
        GridPosition(4, 3),
        GridPosition(1, 3),
        (GridPosition(3, 2),),
    ),
    AngularTransferVariant(
        "west_south_contact_block",
        "Target is west; a south-side blocker invalidates the direct west contact.",
        GridPosition(4, 3),
        GridPosition(1, 3),
        (GridPosition(3, 4),),
    ),
    AngularTransferVariant(
        "south_west_contact_block",
        "Target is south; a west-side blocker invalidates the direct south contact.",
        GridPosition(3, 2),
        GridPosition(3, 5),
        (GridPosition(2, 3),),
    ),
    AngularTransferVariant(
        "south_east_contact_block",
        "Target is south; an east-side blocker invalidates the direct south contact.",
        GridPosition(3, 2),
        GridPosition(3, 5),
        (GridPosition(4, 3),),
    ),
    AngularTransferVariant(
        "north_west_contact_block",
        "Target is north; a west-side blocker invalidates the direct north contact.",
        GridPosition(3, 4),
        GridPosition(3, 1),
        (GridPosition(2, 3),),
    ),
    AngularTransferVariant(
        "north_east_contact_block",
        "Target is north; an east-side blocker invalidates the direct north contact.",
        GridPosition(3, 4),
        GridPosition(3, 1),
        (GridPosition(4, 3),),
    ),
)


@dataclass(frozen=True, slots=True)
class NavigationCase:
    """One non-object-control regression scenario."""

    case_id: str
    description: str
    width: int
    height: int
    start: GridPosition
    orientation: Direction
    destination: GridPosition
    blocker_positions: tuple[GridPosition, ...]
    expected_solvable: bool

    def to_json(self) -> dict[str, object]:
        return {
            "blocker_positions": [_position_json(position) for position in self.blocker_positions],
            "case_id": self.case_id,
            "description": self.description,
            "destination": _position_json(self.destination),
            "expected_solvable": self.expected_solvable,
            "height": self.height,
            "orientation": self.orientation.name.lower(),
            "start": _position_json(self.start),
            "width": self.width,
        }


NAVIGATION_CASES = (
    NavigationCase(
        "empty_straight_east",
        "Straight route across an empty interior row.",
        7,
        7,
        GridPosition(1, 1),
        Direction.EAST,
        GridPosition(5, 1),
        (),
        True,
    ),
    NavigationCase(
        "empty_turn_south",
        "The agent must rotate from north and then travel south.",
        7,
        7,
        GridPosition(2, 1),
        Direction.NORTH,
        GridPosition(2, 5),
        (),
        True,
    ),
    NavigationCase(
        "single_wall_detour",
        "A three-cell vertical wall requires a deterministic detour through the upper opening.",
        7,
        7,
        GridPosition(1, 3),
        Direction.EAST,
        GridPosition(5, 3),
        (GridPosition(3, 2), GridPosition(3, 3), GridPosition(3, 4)),
        True,
    ),
    NavigationCase(
        "double_turn_corridor",
        "Two offset wall segments require more than one route-direction change.",
        8,
        7,
        GridPosition(1, 1),
        Direction.SOUTH,
        GridPosition(6, 5),
        (
            GridPosition(3, 1),
            GridPosition(3, 2),
            GridPosition(3, 3),
            GridPosition(5, 3),
            GridPosition(5, 4),
            GridPosition(5, 5),
        ),
        True,
    ),
    NavigationCase(
        "enclosed_destination",
        "The destination is enclosed; the correct result is an honest unreachable outcome.",
        7,
        7,
        GridPosition(1, 1),
        Direction.EAST,
        GridPosition(4, 4),
        (
            GridPosition(4, 3),
            GridPosition(5, 4),
            GridPosition(4, 5),
            GridPosition(3, 4),
        ),
        False,
    ),
)


def angular_transfer_state(seed: int) -> tuple[AngularTransferVariant, NurseryState]:
    """Build one deterministic transfer scenario from a named geometry family."""
    variant = ANGULAR_TRANSFER_VARIANTS[seed % len(ANGULAR_TRANSFER_VARIANTS)]
    occupied = {
        variant.object_position,
        variant.target_position,
        *variant.blocker_positions,
    }
    starts = (
        GridPosition(1, 1),
        GridPosition(6, 1),
        GridPosition(1, 5),
        GridPosition(6, 5),
        GridPosition(2, 4),
        GridPosition(5, 2),
    )
    available_starts = tuple(position for position in starts if position not in occupied)
    start = available_starts[(seed // len(ANGULAR_TRANSFER_VARIANTS)) % len(available_starts)]
    entities = (
        *_boundary_walls(8, 7, "week12_transfer_wall"),
        *(
            EntityState(
                entity_id=f"transfer_blocker_{index:02d}",
                role=EntityRole.WALL,
                position=position,
                blocks_movement=True,
                movable=False,
            )
            for index, position in enumerate(variant.blocker_positions)
        ),
        EntityState(
            entity_id="object_0",
            role=EntityRole.OBJECT,
            position=variant.object_position,
            blocks_movement=True,
            movable=True,
            shape_code=ShapeCode.ANGULAR,
        ),
        EntityState(
            entity_id="target_0",
            role=EntityRole.TARGET,
            position=variant.target_position,
            blocks_movement=False,
            movable=False,
        ),
    )
    state = NurseryState(
        width=8,
        height=7,
        agent=AgentState(
            position=start,
            orientation=tuple(Direction)[seed % len(tuple(Direction))],
        ),
        entities=entities,
    )
    return variant, state


def navigation_state(case: NavigationCase) -> NurseryState:
    """Build a navigation-only state with a harmless round object outside the route goal."""
    reserved = {case.start, case.destination, *case.blocker_positions}
    object_position = next(
        GridPosition(x, y)
        for y in range(1, case.height - 1)
        for x in range(1, case.width - 1)
        if GridPosition(x, y) not in reserved
    )
    entities = (
        *_boundary_walls(case.width, case.height, f"{case.case_id}_wall"),
        *(
            EntityState(
                entity_id=f"{case.case_id}_blocker_{index:02d}",
                role=EntityRole.WALL,
                position=position,
                blocks_movement=True,
                movable=False,
            )
            for index, position in enumerate(case.blocker_positions)
        ),
        EntityState(
            entity_id="object_0",
            role=EntityRole.OBJECT,
            position=object_position,
            blocks_movement=True,
            movable=False,
            shape_code=ShapeCode.ROUND,
        ),
        EntityState(
            entity_id="target_0",
            role=EntityRole.TARGET,
            position=case.destination,
            blocks_movement=False,
            movable=False,
        ),
    )
    return NurseryState(
        width=case.width,
        height=case.height,
        agent=AgentState(position=case.start, orientation=case.orientation),
        entities=entities,
    )


def scenario_catalogue() -> dict[str, object]:
    """Describe every Week 12 evaluation family in human-readable form."""
    return {
        "angular_transfer": {
            "baseline": "frozen_general_push_controller",
            "decision_use": "bounded transfer and post-consolidation capability gate",
            "seed_count": len(ANGULAR_TRANSFER_SEEDS),
            "seeds": list(ANGULAR_TRANSFER_SEEDS),
            "variants": [variant.to_json() for variant in ANGULAR_TRANSFER_VARIANTS],
        },
        "ball_retention": {
            "baseline": "frozen general controller without specialist routing",
            "decision_use": "old-skill retention and routing non-interference gate",
            "generator": "Week8ScenarioFactory random-start round-object task",
            "seed_count": len(BALL_RETENTION_SEEDS),
            "seeds": list(BALL_RETENTION_SEEDS),
        },
        "navigation_regression": {
            "baseline": "deterministic shortest-route navigation without growth routing",
            "decision_use": "out-of-scope action-trace equivalence and honest failure gate",
            "cases": [case.to_json() for case in NAVIGATION_CASES],
        },
    }


def _boundary_walls(width: int, height: int, prefix: str) -> tuple[EntityState, ...]:
    positions = (
        GridPosition(x, y)
        for y in range(height)
        for x in range(width)
        if x in (0, width - 1) or y in (0, height - 1)
    )
    return tuple(
        EntityState(
            entity_id=f"{prefix}_{index:03d}",
            role=EntityRole.WALL,
            position=position,
            blocks_movement=True,
            movable=False,
        )
        for index, position in enumerate(positions)
    )


def _position_json(position: GridPosition) -> dict[str, int]:
    return {"x": position.x, "y": position.y}
