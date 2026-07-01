"""Authoritative Week 11 scenario and evidence inputs."""

from pathlib import Path

from seedmind.environment import NurseryState
from seedmind.growth.week10 import _angular_state

WEEK10_DIR = Path("artifacts/week10_capacity_diagnosis")
WEEK8_SKILL = Path("artifacts/week8_reusable_skill/approach_and_push_skill_record.json")
TRAINING_SEEDS = (710, 711, 712, 713, 714, 715, 716, 717)
EVALUATION_SEEDS = tuple(range(810, 830))
ROUTER_SEEDS = tuple(range(910, 920))
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
    return _angular_state(seed=seed, impossible=False)
