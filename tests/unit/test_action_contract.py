"""Tests for primitive body actions."""

from seedmind.contracts import PrimitiveAction


def test_primitive_action_values_are_stable() -> None:
    assert [action.value for action in PrimitiveAction] == [
        "turn_left",
        "turn_right",
        "move_forward",
        "inspect",
        "push",
        "wait",
        "request_help",
        "acknowledge",
        "stop",
    ]


def test_primitive_action_can_be_created_from_wire_value() -> None:
    assert PrimitiveAction("request_help") is PrimitiveAction.REQUEST_HELP
