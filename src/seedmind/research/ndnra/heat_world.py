"""Deterministic heat-and-fan world for the NDNRA research prototype."""

from __future__ import annotations

from dataclasses import dataclass, replace

from seedmind.research.ndnra.models import HeatAction, HeatContext, NeedPulse


@dataclass(frozen=True, slots=True)
class HeatWorldState:
    """Minimal body and environment state for one cooling task."""

    need_intensity: float = 1.0
    sitting: bool = True
    distance_to_fan: int = 1
    reaching_switch: bool = False
    fan_on: bool = False
    step_index: int = 0

    def __post_init__(self) -> None:
        if not 0.0 <= self.need_intensity <= 1.0:
            raise ValueError("need_intensity must be between zero and one")
        if self.distance_to_fan < 0:
            raise ValueError("distance_to_fan must not be negative")
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        if self.sitting and self.distance_to_fan == 0:
            raise ValueError("the seated start must remain away from the fan")
        if self.reaching_switch and self.distance_to_fan != 0:
            raise ValueError("the switch can be reached only at the fan")
        if self.fan_on and not self.reaching_switch:
            raise ValueError("fan activation requires prior switch reach")

    @property
    def context(self) -> HeatContext:
        """Return the local context visible to the neural graph."""
        if self.need_intensity == 0.0:
            return HeatContext.COOLED
        if self.fan_on:
            return HeatContext.FAN_ON
        if self.reaching_switch:
            return HeatContext.REACHING_SWITCH
        if self.distance_to_fan == 0:
            return HeatContext.AT_FAN
        if self.sitting:
            return HeatContext.SITTING_AWAY
        return HeatContext.STANDING_AWAY

    @property
    def resolved(self) -> bool:
        """Return whether the heat need has been fully resolved."""
        return self.need_intensity == 0.0


@dataclass(frozen=True, slots=True)
class HeatTransition:
    """One action result with explicit need reduction."""

    previous_state: HeatWorldState
    action: HeatAction
    state: HeatWorldState
    valid: bool
    need_reduction: float

    def __post_init__(self) -> None:
        if not 0.0 <= self.need_reduction <= 1.0:
            raise ValueError("need_reduction must be between zero and one")
        expected = self.previous_state.need_intensity - self.state.need_intensity
        if abs(expected - self.need_reduction) > 1e-12:
            raise ValueError("need_reduction does not match state change")


class HeatFanWorld:
    """Tiny deterministic world used only to falsify NDNRA prototype claims."""

    def __init__(self, initial_need: float = 1.0) -> None:
        if not 0.0 < initial_need <= 1.0:
            raise ValueError("initial_need must be above zero and at most one")
        self._initial_need = initial_need
        self._state = HeatWorldState(need_intensity=initial_need)

    @property
    def state(self) -> HeatWorldState:
        """Return the current immutable world state."""
        return self._state

    def reset(self) -> HeatWorldState:
        """Restore the deterministic hot seated start."""
        self._state = HeatWorldState(need_intensity=self._initial_need)
        return self._state

    def need_pulse(self, *, effort_budget: int) -> NeedPulse:
        """Expose the unresolved heat need as a compact persistent pulse."""
        return NeedPulse(
            need_code="reduce_temperature",
            intensity=self._state.need_intensity,
            urgency=self._state.need_intensity,
            effort_budget=effort_budget,
        )

    def teacher_action(self) -> HeatAction:
        """Return the deterministic demonstrated action for the current context."""
        return {
            HeatContext.SITTING_AWAY: HeatAction.STAND,
            HeatContext.STANDING_AWAY: HeatAction.WALK,
            HeatContext.AT_FAN: HeatAction.REACH,
            HeatContext.REACHING_SWITCH: HeatAction.ACTIVATE,
            HeatContext.FAN_ON: HeatAction.WAIT,
            HeatContext.COOLED: HeatAction.WAIT,
        }[self._state.context]

    def step(self, action: HeatAction) -> HeatTransition:
        """Apply one primitive action and reduce heat only after fan exposure."""
        previous = self._state
        valid = False
        state = previous

        if action is HeatAction.STAND and previous.sitting:
            state = replace(previous, sitting=False)
            valid = True
        elif action is HeatAction.WALK and not previous.sitting and previous.distance_to_fan > 0:
            state = replace(previous, distance_to_fan=previous.distance_to_fan - 1)
            valid = True
        elif (
            action is HeatAction.REACH
            and not previous.sitting
            and previous.distance_to_fan == 0
            and not previous.reaching_switch
        ):
            state = replace(previous, reaching_switch=True)
            valid = True
        elif action is HeatAction.ACTIVATE and previous.reaching_switch and not previous.fan_on:
            state = replace(previous, fan_on=True)
            valid = True
        elif action is HeatAction.WAIT and previous.fan_on and not previous.resolved:
            state = replace(previous, need_intensity=0.0)
            valid = True
        elif action is HeatAction.WAIT:
            valid = True

        state = replace(state, step_index=previous.step_index + 1)
        self._state = state
        return HeatTransition(
            previous_state=previous,
            action=action,
            state=state,
            valid=valid,
            need_reduction=previous.need_intensity - state.need_intensity,
        )
