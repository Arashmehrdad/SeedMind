"""Authoritative Week 11 scenario and evidence inputs."""

from pathlib import Path

from seedmind.contracts import Direction, GridPosition
from seedmind.environment import AgentState, EntityRole, EntityState, NurseryState, ShapeCode
from seedmind.growth.week10 import build_angular_capacity_state

WEEK10_DIR = Path("artifacts/week10_capacity_diagnosis")
WEEK8_SKILL = Path("artifacts/week8_reusable_skill/approach_and_push_skill_record.json")
TRAINING_SEEDS = (710, 711, 712, 713, 714, 715, 716, 717)
EVALUATION_SEEDS = tuple(range(810, 830))
ROUTER_SEEDS = tuple(range(910, 920))
HOLDOUT_SEEDS = tuple(range(1010, 1042))
FAMILIAR_SEEDS = (
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
STEP_BUDGET = 32


def cube_like_state(seed: int) -> NurseryState:
    """Reuse the exact grounded Week 10 angular-object state contract."""
    return build_angular_capacity_state(seed=seed)


def cube_like_holdout_state(seed: int) -> NurseryState:
    """Build a deterministic mirrored or rotated cube-like holdout geometry."""
    variants = (
        (GridPosition(3, 2), GridPosition(1, 3), GridPosition(2, 1)),
        (GridPosition(3, 3), GridPosition(5, 2), GridPosition(4, 4)),
        (GridPosition(3, 3), GridPosition(1, 2), GridPosition(2, 4)),
        (GridPosition(2, 2), GridPosition(3, 4), GridPosition(3, 1)),
        (GridPosition(4, 2), GridPosition(3, 4), GridPosition(3, 1)),
        (GridPosition(2, 3), GridPosition(3, 1), GridPosition(3, 4)),
        (GridPosition(4, 3), GridPosition(3, 1), GridPosition(3, 4)),
    )
    object_position, target_position, blocker_position = variants[seed % len(variants)]
    agent_candidates = (
        GridPosition(1, 1),
        GridPosition(5, 1),
        GridPosition(1, 4),
        GridPosition(5, 4),
        GridPosition(2, 4),
        GridPosition(4, 1),
    )
    available_starts = tuple(
        position
        for position in agent_candidates
        if position not in {object_position, target_position, blocker_position}
    )
    agent_position = available_starts[(seed // len(variants)) % len(available_starts)]
    return NurseryState(
        width=7,
        height=6,
        agent=AgentState(
            position=agent_position,
            orientation=tuple(Direction)[seed % len(tuple(Direction))],
        ),
        entities=(
            *_holdout_wall_entities(7, 6),
            EntityState(
                entity_id="flat_contact_blocker",
                role=EntityRole.WALL,
                position=blocker_position,
                blocks_movement=True,
                movable=False,
            ),
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=object_position,
                blocks_movement=True,
                movable=True,
                shape_code=ShapeCode.ANGULAR,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=target_position,
                blocks_movement=False,
                movable=False,
            ),
        ),
    )


def _holdout_wall_entities(width: int, height: int) -> tuple[EntityState, ...]:
    positions = (
        GridPosition(x, y)
        for y in range(height)
        for x in range(width)
        if x in (0, width - 1) or y in (0, height - 1)
    )
    return tuple(
        EntityState(
            entity_id=f"holdout_wall_{index:03d}",
            role=EntityRole.WALL,
            position=position,
            blocks_movement=True,
            movable=False,
        )
        for index, position in enumerate(positions)
    )
