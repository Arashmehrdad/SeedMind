"""Goal-gated multi-step structural growth and pressure discharge."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from seedmind.research.ndnra.adaptive import (
    NDNRARuntimeAdaptiveState,
    PressureDischarge,
)


@dataclass(frozen=True, slots=True)
class GrowthCycleConfig:
    """Bounds for repeated growth before safe escalation or discharge."""

    maximum_growth_steps: int = 4
    continuation_pressure_threshold: float = 0.50
    minimum_causal_improvement: float = 0.05
    discharge_amount: float = 0.60

    def __post_init__(self) -> None:
        if self.maximum_growth_steps <= 0:
            raise ValueError("maximum_growth_steps must be positive")
        for name, value in (
            ("continuation_pressure_threshold", self.continuation_pressure_threshold),
            ("minimum_causal_improvement", self.minimum_causal_improvement),
            ("discharge_amount", self.discharge_amount),
        ):
            _validate_unit(name, value)


@dataclass(frozen=True, slots=True)
class GrowthResolution:
    """Decision after checking whether one growth step resolved the active goal."""

    growth_step_index: int
    maximum_growth_steps: int
    goal_satisfaction: float
    satisfaction_threshold: float
    causal_improvement: float
    minimum_causal_improvement: float
    goal_achieved: bool
    causal_improvement_verified: bool
    continue_growth: bool
    growth_budget_exhausted: bool
    pressure_before: float
    pressure_after: float
    discharge: PressureDischarge | None
    reason_code: str

    def __post_init__(self) -> None:
        if self.growth_step_index <= 0:
            raise ValueError("growth_step_index must be positive")
        if self.maximum_growth_steps <= 0:
            raise ValueError("maximum_growth_steps must be positive")
        if self.growth_step_index > self.maximum_growth_steps:
            raise ValueError("growth_step_index exceeds maximum_growth_steps")
        for name, value in (
            ("goal_satisfaction", self.goal_satisfaction),
            ("satisfaction_threshold", self.satisfaction_threshold),
            ("causal_improvement", self.causal_improvement),
            ("minimum_causal_improvement", self.minimum_causal_improvement),
            ("pressure_before", self.pressure_before),
            ("pressure_after", self.pressure_after),
        ):
            _validate_unit(name, value)
        if self.goal_achieved != (self.goal_satisfaction >= self.satisfaction_threshold):
            raise ValueError("goal_achieved is inconsistent")
        if self.causal_improvement_verified != (
            self.causal_improvement >= self.minimum_causal_improvement
        ):
            raise ValueError("causal improvement flag is inconsistent")
        if self.continue_growth and (self.goal_achieved or self.growth_budget_exhausted):
            raise ValueError("resolved or exhausted growth cannot continue")
        if self.discharge is None and self.pressure_after != self.pressure_before:
            raise ValueError("pressure changed without verified discharge")
        if self.discharge is not None:
            if not self.goal_achieved or not self.causal_improvement_verified:
                raise ValueError("discharge requires verified goal achievement")
            if self.discharge.pressure_before != self.pressure_before:
                raise ValueError("discharge pressure_before mismatch")
            if self.discharge.pressure_after != self.pressure_after:
                raise ValueError("discharge pressure_after mismatch")
        if not self.reason_code.strip() or not self.reason_code.isascii():
            raise ValueError("reason_code must be non-empty ASCII")


class GoalGatedGrowthCycle:
    """Retain pressure until growth causally resolves the active goal."""

    def __init__(
        self,
        adaptive_state: NDNRARuntimeAdaptiveState,
        config: GrowthCycleConfig | None = None,
    ) -> None:
        self.adaptive_state = adaptive_state
        self.config = GrowthCycleConfig() if config is None else config

    def evaluate_growth_step(
        self,
        *,
        growth_step_index: int,
        goal_satisfaction: float,
        satisfaction_threshold: float,
        causal_improvement: float,
    ) -> GrowthResolution:
        """Discharge only after verified resolution; otherwise continue if bounded."""
        if not 1 <= growth_step_index <= self.config.maximum_growth_steps:
            raise ValueError("growth_step_index is outside the configured budget")
        for name, value in (
            ("goal_satisfaction", goal_satisfaction),
            ("satisfaction_threshold", satisfaction_threshold),
            ("causal_improvement", causal_improvement),
        ):
            _validate_unit(name, value)

        goal_achieved = goal_satisfaction >= satisfaction_threshold
        causal_verified = causal_improvement >= self.config.minimum_causal_improvement
        pressure_before = self.adaptive_state.pressure.value
        exhausted = growth_step_index >= self.config.maximum_growth_steps
        discharge: PressureDischarge | None = None

        if goal_achieved and causal_verified:
            pressure_after = max(
                0.0,
                pressure_before - self.config.discharge_amount,
            )
            self.adaptive_state.pressure.value = pressure_after
            discharge = PressureDischarge(
                requested_amount=self.config.discharge_amount,
                pressure_before=pressure_before,
                pressure_after=pressure_after,
                reason_code="growth_goal_verified",
            )
            continue_growth = False
            reason_code = "goal_verified_discharge"
        else:
            pressure_after = pressure_before
            continue_growth = bool(
                not exhausted and pressure_before >= self.config.continuation_pressure_threshold
            )
            if goal_achieved and not causal_verified:
                reason_code = (
                    "goal_unattributed_continue_growth"
                    if continue_growth
                    else "goal_unattributed_hold"
                )
            elif exhausted:
                reason_code = "goal_unresolved_growth_budget_exhausted"
            elif continue_growth:
                reason_code = "goal_unresolved_continue_growth"
            else:
                reason_code = "goal_unresolved_collect_more_evidence"

        return GrowthResolution(
            growth_step_index=growth_step_index,
            maximum_growth_steps=self.config.maximum_growth_steps,
            goal_satisfaction=goal_satisfaction,
            satisfaction_threshold=satisfaction_threshold,
            causal_improvement=causal_improvement,
            minimum_causal_improvement=self.config.minimum_causal_improvement,
            goal_achieved=goal_achieved,
            causal_improvement_verified=causal_verified,
            continue_growth=continue_growth,
            growth_budget_exhausted=exhausted and not goal_achieved,
            pressure_before=pressure_before,
            pressure_after=pressure_after,
            discharge=discharge,
            reason_code=reason_code,
        )


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
