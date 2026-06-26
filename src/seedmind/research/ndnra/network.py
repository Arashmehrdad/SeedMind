"""Sparse local neural graph for the isolated NDNRA heat-fan prototype."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite

from seedmind.research.ndnra.models import (
    HeatAction,
    HeatContext,
    LocalNeuron,
    LocalSynapse,
    ModulationSummary,
    NeedPulse,
    NeuronKind,
    RecallResult,
)

_NEED_NEURON_ID = "need:reduce_temperature"
_OUTCOME_NEURON_ID = "outcome:cooling"


@dataclass(frozen=True, slots=True)
class LocalNeuralGraphConfig:
    """Bounded local-learning and recall settings for the prototype."""

    neuron_learning_rate: float = 0.12
    synapse_learning_rate: float = 0.22
    neuron_trace_decay: float = 0.85
    activation_persistence: float = 0.20
    utility_drive_weight: float = 0.25
    dormancy_penalty: float = 0.45
    effort_boost_per_depth: float = 0.18
    action_activation_threshold: float = 0.75
    maximum_recall_depth: int = 5

    def __post_init__(self) -> None:
        for name, value in (
            ("neuron_learning_rate", self.neuron_learning_rate),
            ("synapse_learning_rate", self.synapse_learning_rate),
            ("neuron_trace_decay", self.neuron_trace_decay),
            ("activation_persistence", self.activation_persistence),
            ("utility_drive_weight", self.utility_drive_weight),
            ("dormancy_penalty", self.dormancy_penalty),
            ("effort_boost_per_depth", self.effort_boost_per_depth),
            ("action_activation_threshold", self.action_activation_threshold),
        ):
            if not isfinite(value) or not 0.0 <= value <= 1.0:
                raise ValueError(f"{name} must be between zero and one")
        if self.maximum_recall_depth <= 0:
            raise ValueError("maximum_recall_depth must be positive")


class LocalNeuralGraph:
    """Inspectable graph whose neurons and synapses retain only local state."""

    def __init__(self, config: LocalNeuralGraphConfig | None = None) -> None:
        self.config = LocalNeuralGraphConfig() if config is None else config
        self._neurons = self._create_neurons()
        self._synapses = self._create_synapses()
        self._incoming = self._index_incoming_synapses()
        self._cycle = 0

    @property
    def neurons(self) -> tuple[LocalNeuron, ...]:
        """Return neurons in deterministic identifier order."""
        return tuple(self._neurons[key] for key in sorted(self._neurons))

    @property
    def synapses(self) -> tuple[LocalSynapse, ...]:
        """Return synapses in deterministic endpoint order."""
        return tuple(self._synapses[key] for key in sorted(self._synapses))

    @property
    def neuron_count(self) -> int:
        return len(self._neurons)

    @property
    def synapse_count(self) -> int:
        return len(self._synapses)

    def neuron(self, neuron_id: str) -> LocalNeuron:
        """Return one local neuron by identifier."""
        try:
            return self._neurons[neuron_id]
        except KeyError as error:
            raise ValueError(f"unknown neuron_id: {neuron_id}") from error

    def synapse(self, source_id: str, target_id: str) -> LocalSynapse:
        """Return one local directed connection by endpoints."""
        try:
            return self._synapses[(source_id, target_id)]
        except KeyError as error:
            raise ValueError(f"unknown synapse: {source_id}->{target_id}") from error

    def reset_episode_traces(self) -> None:
        """Clear temporary credit traces while preserving learned local memory."""
        for neuron in self._neurons.values():
            neuron.activation = 0.0
            neuron.activation_trace = 0.0
        for synapse in self._synapses.values():
            synapse.eligibility_trace = 0.0

    def observe_transition(
        self,
        *,
        need_pulse: NeedPulse,
        source_context: HeatContext,
        action: HeatAction,
        target_context: HeatContext,
    ) -> None:
        """Leave decaying traces only on structures participating in one step."""
        self._cycle += 1
        self._decay_traces()
        need_neuron = self._neurons[_NEED_NEURON_ID]
        source_neuron = self._neurons[_context_neuron_id(source_context)]
        action_neuron = self._neurons[_action_neuron_id(action)]
        target_neuron = self._neurons[_context_neuron_id(target_context)]

        need_neuron.mark_active(amount=need_pulse.intensity, cycle=self._cycle)
        source_neuron.mark_active(amount=1.0, cycle=self._cycle)
        action_neuron.mark_active(amount=1.0, cycle=self._cycle)
        target_neuron.mark_active(amount=1.0, cycle=self._cycle)
        self.synapse(source_neuron.neuron_id, action_neuron.neuron_id).mark_participation()
        self.synapse(action_neuron.neuron_id, target_neuron.neuron_id).mark_participation()

    def broadcast_modulatory_signal(self, signal: float) -> ModulationSummary:
        """Broadcast a signal that changes only locally eligible structures."""
        if not isfinite(signal) or not -1.0 <= signal <= 1.0:
            raise ValueError("signal must be between negative one and one")
        updated_neurons = 0
        updated_synapses = 0
        neuron_delta_total = 0.0
        synapse_delta_total = 0.0

        for neuron in self._neurons.values():
            delta = neuron.apply_modulation(
                signal=signal,
                learning_rate=self.config.neuron_learning_rate,
            )
            if abs(delta) > 0.0:
                updated_neurons += 1
                neuron_delta_total += delta
                if neuron.kind is NeuronKind.ACTION and delta > 0.0:
                    neuron.need_compatibility = min(
                        1.0,
                        neuron.need_compatibility + delta,
                    )

        for synapse in self._synapses.values():
            delta = synapse.apply_modulation(
                signal=signal,
                learning_rate=self.config.synapse_learning_rate,
            )
            if abs(delta) > 0.0:
                updated_synapses += 1
                synapse_delta_total += delta

        return ModulationSummary(
            signal=signal,
            updated_neuron_count=updated_neurons,
            updated_synapse_count=updated_synapses,
            total_neuron_delta=neuron_delta_total,
            total_synapse_delta=synapse_delta_total,
        )

    def mark_cooling_outcome(self) -> None:
        """Mark the local cooling outcome before the need-resolution broadcast."""
        self._cycle += 1
        self._neurons[_OUTCOME_NEURON_ID].mark_active(amount=1.0, cycle=self._cycle)

    def enter_dormancy(self, level: float) -> None:
        """Make learned structures harder to access without deleting them."""
        if not isfinite(level) or not 0.0 <= level <= 1.0:
            raise ValueError("level must be between zero and one")
        for neuron in self._neurons.values():
            if neuron.kind in (NeuronKind.ACTION, NeuronKind.OUTCOME) and (
                neuron.utility > 0.0 or neuron.usage_count > 0
            ):
                neuron.enter_dormancy(level)
        for synapse in self._synapses.values():
            if synapse.weight > 0.0:
                synapse.enter_dormancy(level)

    def recall_action(
        self,
        *,
        need_pulse: NeedPulse,
        context: HeatContext,
        maximum_depth: int,
    ) -> RecallResult:
        """Recruit one action through bounded spreading activation."""
        if maximum_depth <= 0:
            raise ValueError("maximum_depth must be positive")
        if maximum_depth > self.config.maximum_recall_depth:
            raise ValueError("maximum_depth exceeds configured recall depth")
        if maximum_depth > need_pulse.effort_budget:
            raise ValueError("maximum_depth exceeds need effort budget")

        self._reset_activations()
        need_id = _NEED_NEURON_ID
        context_id = _context_neuron_id(context)
        self._neurons[need_id].activation = need_pulse.intensity
        self._neurons[context_id].activation = 1.0
        activated_ids: set[str] = {need_id, context_id}
        neuron_evaluations = 0

        for depth in range(1, maximum_depth + 1):
            previous = {neuron_id: neuron.activation for neuron_id, neuron in self._neurons.items()}
            for neuron_id, neuron in self._neurons.items():
                if neuron_id in (need_id, context_id):
                    continue
                neuron_evaluations += 1
                incoming = sum(
                    previous[synapse.source_id] * synapse.effective_weight
                    for synapse in self._incoming[neuron_id]
                )
                need_drive = (
                    need_pulse.intensity
                    * neuron.need_compatibility
                    * self.config.utility_drive_weight
                )
                support = need_pulse.intensity * incoming + need_drive
                effort = (depth - 1) * self.config.effort_boost_per_depth if support > 0.0 else 0.0
                dormancy_resistance = neuron.dormancy_level * self.config.dormancy_penalty
                candidate = max(0.0, support + effort - dormancy_resistance)
                neuron.activation = max(
                    previous[neuron_id] * self.config.activation_persistence,
                    candidate,
                )
                if neuron.activation >= neuron.activation_threshold:
                    activated_ids.add(neuron_id)

            selected_action, selected_score = self._select_action()
            if selected_action is not None:
                return RecallResult(
                    selected_action=selected_action,
                    requested_depth=maximum_depth,
                    depth_used=depth,
                    propagation_cycles=depth,
                    neuron_evaluations=neuron_evaluations,
                    selected_score=selected_score,
                    activated_neuron_ids=tuple(sorted(activated_ids)),
                )

        _, selected_score = self._select_action(require_threshold=False)
        return RecallResult(
            selected_action=None,
            requested_depth=maximum_depth,
            depth_used=maximum_depth,
            propagation_cycles=maximum_depth,
            neuron_evaluations=neuron_evaluations,
            selected_score=selected_score,
            activated_neuron_ids=tuple(sorted(activated_ids)),
        )

    def snapshot(self) -> dict[str, object]:
        """Return an ASCII-serializable view of all local memory state."""
        return {
            "neuron_count": self.neuron_count,
            "synapse_count": self.synapse_count,
            "neurons": [
                {
                    "neuron_id": neuron.neuron_id,
                    "kind": neuron.kind.value,
                    "threshold": neuron.activation_threshold,
                    "need_compatibility": neuron.need_compatibility,
                    "utility": neuron.utility,
                    "plasticity": neuron.plasticity,
                    "stability": neuron.stability,
                    "usage_count": neuron.usage_count,
                    "dormancy_level": neuron.dormancy_level,
                }
                for neuron in self.neurons
            ],
            "synapses": [
                {
                    "synapse_id": synapse.synapse_id,
                    "source_id": synapse.source_id,
                    "target_id": synapse.target_id,
                    "weight": synapse.weight,
                    "eligibility_trace": synapse.eligibility_trace,
                    "stability": synapse.stability,
                    "usage_count": synapse.usage_count,
                    "dormancy_level": synapse.dormancy_level,
                }
                for synapse in self.synapses
            ],
        }

    def _create_neurons(self) -> dict[str, LocalNeuron]:
        neurons = {
            _NEED_NEURON_ID: LocalNeuron(
                neuron_id=_NEED_NEURON_ID,
                kind=NeuronKind.NEED,
                activation_threshold=0.0,
            ),
            _OUTCOME_NEURON_ID: LocalNeuron(
                neuron_id=_OUTCOME_NEURON_ID,
                kind=NeuronKind.OUTCOME,
                activation_threshold=0.75,
            ),
        }
        for context in HeatContext:
            neuron_id = _context_neuron_id(context)
            neurons[neuron_id] = LocalNeuron(
                neuron_id=neuron_id,
                kind=NeuronKind.CONTEXT,
                activation_threshold=0.0,
            )
        for action in HeatAction:
            neuron_id = _action_neuron_id(action)
            neurons[neuron_id] = LocalNeuron(
                neuron_id=neuron_id,
                kind=NeuronKind.ACTION,
                activation_threshold=self.config.action_activation_threshold,
            )
        return neurons

    def _create_synapses(self) -> dict[tuple[str, str], LocalSynapse]:
        synapses: dict[tuple[str, str], LocalSynapse] = {}
        for context in HeatContext:
            source = _context_neuron_id(context)
            for action in HeatAction:
                target = _action_neuron_id(action)
                synapses[(source, target)] = LocalSynapse(
                    source_id=source,
                    target_id=target,
                )
        for action in HeatAction:
            source = _action_neuron_id(action)
            for context in HeatContext:
                target = _context_neuron_id(context)
                synapses[(source, target)] = LocalSynapse(
                    source_id=source,
                    target_id=target,
                )
        return synapses

    def _index_incoming_synapses(self) -> dict[str, tuple[LocalSynapse, ...]]:
        incoming: dict[str, list[LocalSynapse]] = {neuron_id: [] for neuron_id in self._neurons}
        for synapse in self._synapses.values():
            incoming[synapse.target_id].append(synapse)
        return {
            neuron_id: tuple(sorted(items, key=lambda item: (item.source_id, item.target_id)))
            for neuron_id, items in incoming.items()
        }

    def _decay_traces(self) -> None:
        for neuron in self._neurons.values():
            neuron.decay_trace(self.config.neuron_trace_decay)
        for synapse in self._synapses.values():
            synapse.decay_eligibility()

    def _reset_activations(self) -> None:
        for neuron in self._neurons.values():
            neuron.reset_activation()

    def _select_action(
        self,
        *,
        require_threshold: bool = True,
    ) -> tuple[HeatAction | None, float]:
        ranked = sorted(
            (
                (self._neurons[_action_neuron_id(action)].activation, action)
                for action in HeatAction
            ),
            key=lambda item: (-item[0], item[1].value),
        )
        score, action = ranked[0]
        threshold = self._neurons[_action_neuron_id(action)].activation_threshold
        if require_threshold and score < threshold:
            return None, score
        return action, score


def _context_neuron_id(context: HeatContext) -> str:
    return f"context:{context.value}"


def _action_neuron_id(action: HeatAction) -> str:
    return f"action:{action.value}"
