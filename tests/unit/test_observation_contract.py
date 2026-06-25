"""Tests for the body-independent observation packet."""

import pytest

from seedmind.contracts import ObservationPacket, PrimitiveAction


def create_packet(**overrides: object) -> ObservationPacket:
    values: dict[str, object] = {
        "timestamp": 3,
        "episode_id": "episode-1",
        "step_id": 2,
        "sensor_values": (0.0, 1.0),
        "available_actions": (
            PrimitiveAction.WAIT,
            PrimitiveAction.STOP,
        ),
        "human_signal": (0.25,),
        "resource_state": (1.0,),
    }
    values.update(overrides)
    return ObservationPacket(**values)  # type: ignore[arg-type]


def test_packet_preserves_raw_channels() -> None:
    packet = create_packet()

    assert packet.sensor_values == (0.0, 1.0)
    assert packet.human_signal == (0.25,)
    assert packet.resource_state == (1.0,)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("timestamp", -1, "timestamp"),
        ("episode_id", " ", "episode_id"),
        ("step_id", -1, "step_id"),
        ("sensor_values", (), "sensor_values"),
        ("available_actions", (), "available_actions"),
    ],
)
def test_packet_rejects_invalid_required_values(
    field: str,
    value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        create_packet(**{field: value})


def test_packet_rejects_duplicate_actions() -> None:
    with pytest.raises(ValueError, match="unique"):
        create_packet(
            available_actions=(
                PrimitiveAction.WAIT,
                PrimitiveAction.WAIT,
            )
        )


@pytest.mark.parametrize(
    "field",
    ["sensor_values", "human_signal", "resource_state"],
)
def test_packet_rejects_non_finite_channels(field: str) -> None:
    with pytest.raises(ValueError, match="finite"):
        create_packet(**{field: (float("nan"),)})
