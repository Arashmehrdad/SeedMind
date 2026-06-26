"""Local neural state and experiment records for the NDNRA prototype."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class HeatAction(StrEnum):
    """Primitive actions available in the deterministic heat-and-fan world."""

    STAND = "stand"
    WALK = "walk"
    REACH = "reach"
    ACTIVATE = "activate"
    WAIT = "wait"


class HeatContext(StrEnum):
    """Raw local contexts exposed by the heat-and-fan body adapter."""

    SITTING_AWAY = "sitting_away"
    STANDING_AWAY = "standing_away"
    AT_FAN = "at_fan"
    REACHING_SWITCH = "reaching_switch"
    FAN_ON = "fan_on"
    COOLED = "cooled"


class NeuronKind(StrEnum):
    """Inspectable functional categories in the local neural graph."""

    NEED = "need"
    CONTEXT = "context"
    ACTION = "action"
    OUTCOME = "outcome"
    ASSOCIATIVE = "associative"


@dataclass(slots=True)
class LocalNeuron:
    """One bounded locally adaptive neuron-like unit."""

    neuron_id: str
    kind: NeuronKind
    activation_threshold: float = 0.75
    need_compatibility: float = 0.0
    activation: float = 0.0
    activation_trace: float = 0.0
    utility: float = 0.0
    plasticity: float = 1.0
    stability: float = 0.0
    dormancy_level: float = 0.0
    usage_count: int = 0
    last_activation_cycle: int = -1

    def __post_init__(self) -> None:
        if not self.neuron_id.strip():
            raise ValueError("neuron_id must not be empty")
        for name, value in (
            ("activation_threshold", self.activation_threshold),
            ("need_compatibility", self.need_compatibility),
            ("activation", self.activation),
            ("activation_trace", self.activation_trace),
            ("utility", self.utility),
            ("plasticity", self.plasticity),
            ("stability", self.stability),
            ("dormancy_level", self.dormancy_level),
        ):
            _validate_unit_interval(name, value)
        if self.usage_count < 0:
            raise ValueError("usage_count must not be negative")
        if self.last_activation_cycle < -1:
            raise ValueError("last_activation_cycle must be at least -1")

    def decay_trace(self, decay: float) -> None:
        """Decay recent local participation without changing learned memory."""
        _validate_unit_interval("decay", decay)
        self.activation_trace *= decay

    def mark_active(self, *, amount: float, cycle: int) -> None:
        """Record local participation for later modulatory credit."""
        _validate_unit_interval("amount", amount)
        if cycle < 0:
            raise ValueError("cycle must not be negative")
        self.activation = max(self.activation, amount)
        self.activation_trace = min(1.0, self.activation_trace + amount)
        self.usage_count += 1
        self.last_activation_cycle = cycle

    def apply_modulation(self, *, signal: float, learning_rate: float) -> float:
        """Apply one broadcast signal using only this neuron's local trace."""
        _validate_signed_unit("signal", signal)
        _validate_unit_interval("learning_rate", learning_rate)
        delta = learning_rate * signal * self.activation_trace * self.plasticity
        self.utility = min(1.0, max(0.0, self.utility + delta))
        if delta > 0.0:
            self.stability = min(1.0, self.stability + abs(delta) * 0.25)
        return delta

    def enter_dormancy(self, level: float) -> None:
        """Raise reversible access resistance without deleting local state."""
        _validate_unit_interval("level", level)
        self.dormancy_level = max(self.dormancy_level, level)
        self.activation = 0.0

    def reset_activation(self) -> None:
        """Clear temporary activation while retaining all learned state."""
        self.activation = 0.0


@dataclass(slots=True)
class LocalSynapse:
    """One bounded locally adaptive directed connection."""

    source_id: str
    target_id: str
    weight: float = 0.0
    eligibility_trace: float = 0.0
    trace_decay: float = 0.85
    plasticity: float = 1.0
    stability: float = 0.0
    usage_count: int = 0
    dormancy_level: float = 0.0

    def __post_init__(self) -> None:
        if not self.source_id.strip() or not self.target_id.strip():
            raise ValueError("synapse endpoints must not be empty")
        if self.source_id == self.target_id:
            raise ValueError("self-connections are not used in this prototype")
        for name, value in (
            ("weight", self.weight),
            ("eligibility_trace", self.eligibility_trace),
            ("trace_decay", self.trace_decay),
            ("plasticity", self.plasticity),
            ("stability", self.stability),
            ("dormancy_level", self.dormancy_level),
        ):
            _validate_unit_interval(name, value)
        if self.usage_count < 0:
            raise ValueError("usage_count must not be negative")

    @property
    def synapse_id(self) -> str:
        """Return a deterministic inspectable connection identifier."""
        return f"{self.source_id}->{self.target_id}"

    @property
    def effective_weight(self) -> float:
        """Return weight after reversible dormancy attenuation."""
        return self.weight * (1.0 - 0.35 * self.dormancy_level)

    def decay_eligibility(self) -> None:
        """Decay delayed-credit eligibility locally."""
        self.eligibility_trace *= self.trace_decay

    def mark_participation(self, amount: float = 1.0) -> None:
        """Mark this connection as recently responsible."""
        _validate_unit_interval("amount", amount)
        self.eligibility_trace = min(1.0, self.eligibility_trace + amount)
        self.usage_count += 1

    def apply_modulation(self, *, signal: float, learning_rate: float) -> float:
        """Update this connection from its own trace and a global signal."""
        _validate_signed_unit("signal", signal)
        _validate_unit_interval("learning_rate", learning_rate)
        delta = learning_rate * signal * self.eligibility_trace * self.plasticity
        self.weight = min(1.0, max(0.0, self.weight + delta))
        if delta > 0.0:
            self.stability = min(1.0, self.stability + abs(delta) * 0.25)
        return delta

    def enter_dormancy(self, level: float) -> None:
        """Attenuate access without changing stored weight."""
        _validate_unit_interval("level", level)
        self.dormancy_level = max(self.dormancy_level, level)


@dataclass(frozen=True, slots=True)
class NeedPulse:
    """Compact persistent recruitment signal for one unresolved need."""

    need_code: str
    intensity: float
    urgency: float
    effort_budget: int

    def __post_init__(self) -> None:
        if not self.need_code.strip():
            raise ValueError("need_code must not be empty")
        _validate_unit_interval("intensity", self.intensity)
        _validate_unit_interval("urgency", self.urgency)
        if self.effort_budget <= 0:
            raise ValueError("effort_budget must be positive")


@dataclass(frozen=True, slots=True)
class RecallResult:
    """One bounded spreading-activation recall attempt."""

    selected_action: HeatAction | None
    requested_depth: int
    depth_used: int
    propagation_cycles: int
    neuron_evaluations: int
    selected_score: float
    activated_neuron_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.requested_depth <= 0:
            raise ValueError("requested_depth must be positive")
        if not 0 <= self.depth_used <= self.requested_depth:
            raise ValueError("depth_used must be within requested depth")
        if self.propagation_cycles < 0 or self.neuron_evaluations < 0:
            raise ValueError("recall costs must not be negative")
        if not isfinite(self.selected_score) or self.selected_score < 0.0:
            raise ValueError("selected_score must be finite and non-negative")

    @property
    def computational_cost(self) -> int:
        """Return a simple deterministic recall-cost measure."""
        return self.propagation_cycles + self.neuron_evaluations


@dataclass(frozen=True, slots=True)
class ModulationSummary:
    """Inspectable result of one chemical-like broadcast."""

    signal: float
    updated_neuron_count: int
    updated_synapse_count: int
    total_neuron_delta: float
    total_synapse_delta: float


@dataclass(slots=True)
class GrowthPressure:
    """Accumulate unresolved curiosity and ambition pressure without growth."""

    value: float = 0.0
    update_count: int = 0

    def update(
        self,
        *,
        unresolved_error: float,
        curiosity: float,
        ambition_relevance: float,
        capacity_saturation: float,
        learning_rate: float = 0.25,
    ) -> float:
        """Accumulate bounded pressure from repeated unresolved important need."""
        for name, item in (
            ("unresolved_error", unresolved_error),
            ("curiosity", curiosity),
            ("ambition_relevance", ambition_relevance),
            ("capacity_saturation", capacity_saturation),
            ("learning_rate", learning_rate),
        ):
            _validate_unit_interval(name, item)
        increment = (
            unresolved_error * curiosity * ambition_relevance * capacity_saturation * learning_rate
        )
        self.value = min(1.0, self.value + increment)
        self.update_count += 1
        return self.value


def _validate_unit_interval(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _validate_signed_unit(name: str, value: float) -> None:
    if not isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between negative one and one")
