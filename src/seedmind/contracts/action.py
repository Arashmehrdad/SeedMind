"""Primitive actions exposed by a SeedMind body adapter."""

from enum import StrEnum


class PrimitiveAction(StrEnum):
    """Actions available to the seed without task-specific knowledge."""

    TURN_LEFT = "turn_left"
    TURN_RIGHT = "turn_right"
    MOVE_FORWARD = "move_forward"
    INSPECT = "inspect"
    PUSH = "push"
    WAIT = "wait"
    REQUEST_HELP = "request_help"
    ACKNOWLEDGE = "acknowledge"
    STOP = "stop"
