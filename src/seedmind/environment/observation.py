"""Deterministic raw observation adapter for SeedMind Nursery v0."""

from collections.abc import Sequence
from dataclasses import dataclass
from typing import ClassVar

from seedmind.contracts import GridPosition, ObservationPacket, PrimitiveAction
from seedmind.environment.entities import EntityState, ShapeCode
from seedmind.environment.state import NurseryState

_ACTIVE_ACTIONS = tuple(PrimitiveAction)
_TERMINATED_ACTIONS = (PrimitiveAction.STOP,)
_MAX_SHAPE_CODE = max(int(shape_code) for shape_code in ShapeCode)


@dataclass(frozen=True, slots=True)
class NurseryObservationAdapter:
    """Convert nursery state into fixed raw numeric channels.

    Layout: normalized body x/y, orientation one-hot channels in cardinal
    order, then occupied/blocking/movable/shape channels for every grid cell
    in row-major order.
    """

    width: int
    height: int

    BODY_CHANNEL_COUNT: ClassVar[int] = 6
    CELL_CHANNEL_COUNT: ClassVar[int] = 4

    def __post_init__(self) -> None:
        """Validate the fixed observation dimensions."""
        if self.width < 3 or self.height < 3:
            raise ValueError("Observation dimensions must be at least 3 by 3")

    @property
    def sensor_size(self) -> int:
        """Return the fixed number of numeric sensor channels."""
        return self.BODY_CHANNEL_COUNT + (
            self.width * self.height * self.CELL_CHANNEL_COUNT
        )

    def observe(
        self,
        state: NurseryState,
        *,
        episode_id: str,
        timestamp: int | None = None,
        human_signal: Sequence[float] = (),
        resource_state: Sequence[float] = (),
    ) -> ObservationPacket:
        """Return a deterministic observation without semantic entity labels."""
        self._validate_state_dimensions(state)

        sensor_values = self._encode_body(state)
        sensor_values.extend(self._encode_grid(state))

        available_actions = (
            _TERMINATED_ACTIONS if state.terminated else _ACTIVE_ACTIONS
        )

        return ObservationPacket(
            timestamp=state.step_count if timestamp is None else timestamp,
            episode_id=episode_id,
            step_id=state.step_count,
            sensor_values=tuple(sensor_values),
            available_actions=available_actions,
            human_signal=tuple(human_signal),
            resource_state=tuple(resource_state),
        )

    def _validate_state_dimensions(self, state: NurseryState) -> None:
        """Reject states that do not match the fixed adapter shape."""
        if state.width != self.width or state.height != self.height:
            raise ValueError(
                "Nursery state dimensions do not match observation adapter"
            )

    def _encode_body(self, state: NurseryState) -> list[float]:
        """Encode normalized body position and orientation one-hot channels."""
        orientation = int(state.agent.orientation)
        orientation_channels = [
            1.0 if index == orientation else 0.0
            for index in range(4)
        ]

        return [
            state.agent.position.x / (self.width - 1),
            state.agent.position.y / (self.height - 1),
            *orientation_channels,
        ]

    def _encode_grid(self, state: NurseryState) -> list[float]:
        """Encode raw cell properties in row-major order."""
        channels: list[float] = []

        for y in range(self.height):
            for x in range(self.width):
                entities = state.entities_at(GridPosition(x=x, y=y))
                channels.extend(
                    (
                        float(bool(entities)),
                        float(any(entity.blocks_movement for entity in entities)),
                        float(any(entity.movable for entity in entities)),
                        self._normalized_shape_code(entities),
                    )
                )

        return channels

    @staticmethod
    def _normalized_shape_code(entities: Sequence[EntityState]) -> float:
        """Return the strongest raw shape channel for one occupied cell."""
        maximum = max(
            (int(entity.shape_code) for entity in entities),
            default=0,
        )
        return maximum / _MAX_SHAPE_CODE
