"""Tests for raw symbolic observation encoding."""

import pytest
import torch

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.perception import SymbolicInputSpec, SymbolicObservationEncoder


def create_packet(
    *,
    sensor_values: tuple[float, ...] = (0.1, 0.2, 0.3),
    human_signal: tuple[float, ...] = (0.4,),
    resource_state: tuple[float, ...] = (0.5,),
) -> ObservationPacket:
    return ObservationPacket(
        timestamp=0,
        episode_id="episode-1",
        step_id=0,
        sensor_values=sensor_values,
        available_actions=tuple(PrimitiveAction),
        human_signal=human_signal,
        resource_state=resource_state,
    )


def test_input_spec_vectorizes_raw_channels_in_contract_order() -> None:
    spec = SymbolicInputSpec(
        sensor_size=3,
        human_signal_size=1,
        resource_state_size=1,
    )

    vector = spec.vectorize(create_packet())

    assert spec.input_size == 5
    assert vector.dtype is torch.float32
    torch.testing.assert_close(
        vector,
        torch.tensor((0.1, 0.2, 0.3, 0.4, 0.5)),
    )


@pytest.mark.parametrize(
    ("packet", "message"),
    [
        (create_packet(sensor_values=(0.1,)), "sensor_values"),
        (create_packet(human_signal=()), "human_signal"),
        (create_packet(resource_state=()), "resource_state"),
    ],
)
def test_input_spec_rejects_channel_size_mismatch(
    packet: ObservationPacket,
    message: str,
) -> None:
    spec = SymbolicInputSpec(
        sensor_size=3,
        human_signal_size=1,
        resource_state_size=1,
    )

    with pytest.raises(ValueError, match=message):
        spec.vectorize(packet)


@pytest.mark.parametrize(
    ("sensor_size", "human_size", "resource_size", "message"),
    [
        (0, 0, 0, "sensor_size"),
        (1, -1, 0, "human_signal_size"),
        (1, 0, -1, "resource_state_size"),
    ],
)
def test_input_spec_rejects_invalid_dimensions(
    sensor_size: int,
    human_size: int,
    resource_size: int,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        SymbolicInputSpec(
            sensor_size=sensor_size,
            human_signal_size=human_size,
            resource_state_size=resource_size,
        )


def test_encoder_accepts_single_vector_and_batch() -> None:
    encoder = SymbolicObservationEncoder(input_size=5, embedding_size=7)
    vector = torch.ones(5)
    batch = torch.ones((3, 5))

    single_embedding = encoder(vector)
    batch_embedding = encoder(batch)

    assert single_embedding.shape == (1, 7)
    assert batch_embedding.shape == (3, 7)
    assert torch.isfinite(single_embedding).all()
    assert torch.isfinite(batch_embedding).all()


def test_encoder_parameters_receive_gradients() -> None:
    encoder = SymbolicObservationEncoder(input_size=5, embedding_size=7)

    embedding = encoder(torch.ones((2, 5)))
    embedding.square().mean().backward()

    assert all(parameter.grad is not None for parameter in encoder.parameters())


def test_encoder_rejects_invalid_observation_shape() -> None:
    encoder = SymbolicObservationEncoder(input_size=5, embedding_size=7)

    with pytest.raises(ValueError, match="width"):
        encoder(torch.ones((2, 4)))

    with pytest.raises(ValueError, match="vector"):
        encoder(torch.ones((1, 2, 5)))
