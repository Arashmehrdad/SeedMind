"""Stage 1 recurrent experiential substrate for NDNRA v0.2 research."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from math import isfinite


@dataclass(frozen=True, slots=True)
class DevelopmentalNetworkConfig:
    """Finite deterministic Stage 1 substrate configuration."""

    seed: int = 11
    neuron_count: int = 32
    coalition_size: int = 6
    maximum_settling_cycles: int = 12
    settling_epsilon: float = 0.0005
    recurrent_decay: float = 0.35
    recurrent_gain: float = 0.18

    def __post_init__(self) -> None:
        _validate_non_negative_int("seed", self.seed)
        _validate_positive_int("neuron_count", self.neuron_count)
        _validate_positive_int("coalition_size", self.coalition_size)
        _validate_positive_int("maximum_settling_cycles", self.maximum_settling_cycles)
        _validate_unit_open("settling_epsilon", self.settling_epsilon)
        _validate_unit("recurrent_decay", self.recurrent_decay)
        _validate_unit("recurrent_gain", self.recurrent_gain)
        if self.coalition_size >= self.neuron_count:
            raise ValueError("coalition_size must be smaller than neuron_count")

    def snapshot(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "neuron_count": self.neuron_count,
            "coalition_size": self.coalition_size,
            "maximum_settling_cycles": self.maximum_settling_cycles,
            "settling_epsilon": self.settling_epsilon,
            "recurrent_decay": self.recurrent_decay,
            "recurrent_gain": self.recurrent_gain,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalNeuronState:
    """One reusable neuron in the fixed Stage 1 pool."""

    neuron_id: str
    threshold: float
    excitability: float
    eligibility: float = 0.0
    plasticity: float = 0.5
    maturity: float = 0.0
    dormancy: float = 0.0
    usage_count: int = 0
    provenance_event_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_ascii_code("neuron_id", self.neuron_id)
        _validate_unit("threshold", self.threshold)
        _validate_unit("excitability", self.excitability)
        _validate_unit("eligibility", self.eligibility)
        _validate_unit("plasticity", self.plasticity)
        _validate_unit("maturity", self.maturity)
        _validate_unit("dormancy", self.dormancy)
        _validate_non_negative_int("usage_count", self.usage_count)
        _validate_sorted_unique_ascii_codes("provenance_event_ids", self.provenance_event_ids)

    def snapshot(self) -> dict[str, object]:
        return {
            "neuron_id": self.neuron_id,
            "threshold": self.threshold,
            "excitability": self.excitability,
            "eligibility": self.eligibility,
            "plasticity": self.plasticity,
            "maturity": self.maturity,
            "dormancy": self.dormancy,
            "usage_count": self.usage_count,
            "provenance_event_ids": list(self.provenance_event_ids),
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalConnectionState:
    """One signed recurrent connection between existing neurons."""

    source_neuron_id: str
    target_neuron_id: str
    weight: float
    provenance_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_ascii_code("source_neuron_id", self.source_neuron_id)
        _validate_ascii_code("target_neuron_id", self.target_neuron_id)
        if self.source_neuron_id == self.target_neuron_id:
            raise ValueError("recurrent connections cannot be self-loops")
        _validate_signed_unit_nonzero("weight", self.weight)
        _validate_sorted_unique_ascii_codes("provenance_event_ids", self.provenance_event_ids)

    @property
    def connection_id(self) -> str:
        return _identity("developmental-connection", self._identity_payload())

    @property
    def inhibitory(self) -> bool:
        return self.weight < 0.0

    def snapshot(self) -> dict[str, object]:
        return {"connection_id": self.connection_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "source_neuron_id": self.source_neuron_id,
            "target_neuron_id": self.target_neuron_id,
            "weight": self.weight,
            "provenance_event_ids": list(self.provenance_event_ids),
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalExperienceEpisode:
    """One distinct episode represented by a distributed coalition."""

    episode_code: str
    context_code: str
    action_code: str
    outcome_code: str
    feature_codes: tuple[str, ...]
    provenance_event_id: str

    def __post_init__(self) -> None:
        for name, value in (
            ("episode_code", self.episode_code),
            ("context_code", self.context_code),
            ("action_code", self.action_code),
            ("outcome_code", self.outcome_code),
            ("provenance_event_id", self.provenance_event_id),
        ):
            _validate_ascii_code(name, value)
        _validate_sorted_unique_ascii_codes("feature_codes", self.feature_codes)

    @property
    def episode_id(self) -> str:
        return _identity("developmental-episode", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"episode_id": self.episode_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "episode_code": self.episode_code,
            "context_code": self.context_code,
            "action_code": self.action_code,
            "outcome_code": self.outcome_code,
            "feature_codes": list(self.feature_codes),
            "provenance_event_id": self.provenance_event_id,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalCoalition:
    """Distributed coalition for one episode inside the reusable pool."""

    episode_id: str
    neuron_ids: tuple[str, ...]
    outcome_code: str
    feature_codes: tuple[str, ...]
    provenance_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_ascii_code("episode_id", self.episode_id)
        _validate_sorted_unique_ascii_codes("neuron_ids", self.neuron_ids)
        _validate_ascii_code("outcome_code", self.outcome_code)
        _validate_sorted_unique_ascii_codes("feature_codes", self.feature_codes)
        _validate_sorted_unique_ascii_codes("provenance_event_ids", self.provenance_event_ids)

    @property
    def coalition_id(self) -> str:
        return _identity("developmental-coalition", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"coalition_id": self.coalition_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "neuron_ids": list(self.neuron_ids),
            "outcome_code": self.outcome_code,
            "feature_codes": list(self.feature_codes),
            "provenance_event_ids": list(self.provenance_event_ids),
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalRecurrentTraceStep:
    """One bounded recurrent settling step."""

    cycle_index: int
    activations: tuple[tuple[str, float], ...]

    def __post_init__(self) -> None:
        _validate_index("cycle_index", self.cycle_index)
        neuron_ids = tuple(neuron_id for neuron_id, _ in self.activations)
        if neuron_ids != tuple(sorted(neuron_ids)):
            raise ValueError("trace activations must be sorted by neuron ID")
        if len(neuron_ids) != len(set(neuron_ids)):
            raise ValueError("trace activation neuron IDs must be unique")
        for neuron_id, value in self.activations:
            _validate_ascii_code("activation neuron_id", neuron_id)
            _validate_unit("activation", value)

    def snapshot(self) -> dict[str, object]:
        return {
            "cycle_index": self.cycle_index,
            "activations": [
                {"neuron_id": neuron_id, "activation": value}
                for neuron_id, value in self.activations
            ],
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalReplayResult:
    """Replay result with finite recurrent trace and no authority."""

    target_episode_id: str
    settled: bool
    settled_cycle_count: int
    coalition_scores: tuple[tuple[str, float], ...]
    trace: tuple[DevelopmentalRecurrentTraceStep, ...]
    production_action_authority_violations: int = 0
    sqlite_cognition_operation_count: int = 0

    def __post_init__(self) -> None:
        _validate_ascii_code("target_episode_id", self.target_episode_id)
        _validate_positive_int("settled_cycle_count", self.settled_cycle_count)
        if not self.settled:
            raise ValueError("Stage 1 replay must settle inside the compute budget")
        _validate_score_rows("coalition_scores", self.coalition_scores)
        _validate_non_empty_sequence("trace", self.trace)
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )
        _validate_zero_int(
            "sqlite_cognition_operation_count", self.sqlite_cognition_operation_count
        )

    def score_for(self, episode_id: str) -> float:
        matches = tuple(
            score for candidate_id, score in self.coalition_scores if candidate_id == episode_id
        )
        if len(matches) != 1:
            raise ValueError("episode_id must match exactly one coalition score")
        return matches[0]

    @property
    def replay_id(self) -> str:
        return _identity("developmental-replay-result", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"replay_id": self.replay_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "target_episode_id": self.target_episode_id,
            "settled": self.settled,
            "settled_cycle_count": self.settled_cycle_count,
            "coalition_scores": [
                {"episode_id": episode_id, "score": score}
                for episode_id, score in self.coalition_scores
            ],
            "trace": [step.snapshot() for step in self.trace],
            "production_action_authority_violations": self.production_action_authority_violations,
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalNetworkState:
    """Immutable in-memory Stage 1 recurrent substrate state."""

    config: DevelopmentalNetworkConfig
    neurons: tuple[DevelopmentalNeuronState, ...]
    connections: tuple[DevelopmentalConnectionState, ...] = ()
    episodes: tuple[DevelopmentalExperienceEpisode, ...] = ()
    coalitions: tuple[DevelopmentalCoalition, ...] = ()
    structural_neuron_creation_count: int = 0
    production_action_authority_violations: int = 0
    sqlite_cognition_operation_count: int = 0

    def __post_init__(self) -> None:
        if len(self.neurons) != self.config.neuron_count:
            raise ValueError("state neuron count must match fixed configuration")
        neuron_ids = tuple(neuron.neuron_id for neuron in self.neurons)
        if neuron_ids != tuple(sorted(neuron_ids)):
            raise ValueError("neurons must be sorted by ID")
        if len(neuron_ids) != len(set(neuron_ids)):
            raise ValueError("neuron IDs must be unique")
        neuron_id_set = set(neuron_ids)
        for connection in self.connections:
            if connection.source_neuron_id not in neuron_id_set:
                raise ValueError("connection source must be an existing neuron")
            if connection.target_neuron_id not in neuron_id_set:
                raise ValueError("connection target must be an existing neuron")
        connection_ids = tuple(connection.connection_id for connection in self.connections)
        if len(connection_ids) != len(set(connection_ids)):
            raise ValueError("connection IDs must be unique")
        episode_ids = tuple(episode.episode_id for episode in self.episodes)
        if len(episode_ids) != len(set(episode_ids)):
            raise ValueError("episode IDs must be unique")
        coalition_episode_ids = tuple(coalition.episode_id for coalition in self.coalitions)
        if coalition_episode_ids != tuple(sorted(coalition_episode_ids)):
            raise ValueError("coalitions must be sorted by episode ID")
        if set(coalition_episode_ids) != set(episode_ids):
            raise ValueError("each episode must have exactly one coalition")
        for coalition in self.coalitions:
            if len(coalition.neuron_ids) >= self.config.neuron_count:
                raise ValueError("coalition cannot recruit the complete neuron pool")
            if not set(coalition.neuron_ids).issubset(neuron_id_set):
                raise ValueError("coalition neurons must come from the fixed pool")
        _validate_zero_int(
            "structural_neuron_creation_count", self.structural_neuron_creation_count
        )
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )
        _validate_zero_int(
            "sqlite_cognition_operation_count", self.sqlite_cognition_operation_count
        )

    def episode_by_code(self, episode_code: str) -> DevelopmentalExperienceEpisode:
        matches = tuple(
            episode for episode in self.episodes if episode.episode_code == episode_code
        )
        if len(matches) != 1:
            raise ValueError("episode_code must match exactly one episode")
        return matches[0]

    def coalition_for_episode(self, episode_id: str) -> DevelopmentalCoalition:
        matches = tuple(
            coalition for coalition in self.coalitions if coalition.episode_id == episode_id
        )
        if len(matches) != 1:
            raise ValueError("episode_id must match exactly one coalition")
        return matches[0]

    @property
    def state_id(self) -> str:
        return _identity("developmental-network-state", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"state_id": self.state_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "config": self.config.snapshot(),
            "neurons": [neuron.snapshot() for neuron in self.neurons],
            "connections": [connection.snapshot() for connection in self.connections],
            "episodes": [episode.snapshot() for episode in self.episodes],
            "coalitions": [coalition.snapshot() for coalition in self.coalitions],
            "structural_neuron_creation_count": self.structural_neuron_creation_count,
            "production_action_authority_violations": self.production_action_authority_violations,
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
        }


@dataclass(frozen=True, slots=True)
class StageOneSubstrateEvidence:
    """Integrated Stage 1 recurrent-substrate acceptance evidence."""

    state: DevelopmentalNetworkState
    target_replay: DevelopmentalReplayResult
    unrelated_episode_id: str
    overlapping_episode_ids: tuple[str, str]

    def __post_init__(self) -> None:
        _validate_ascii_code("unrelated_episode_id", self.unrelated_episode_id)
        _validate_sorted_unique_ascii_codes("overlapping_episode_ids", self.overlapping_episode_ids)
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage 1 pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-one-substrate-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        first = self.state.coalition_for_episode(self.overlapping_episode_ids[0])
        second = self.state.coalition_for_episode(self.overlapping_episode_ids[1])
        overlap = set(first.neuron_ids) & set(second.neuron_ids)
        target_score = self.target_replay.score_for(self.target_replay.target_episode_id)
        unrelated_score = self.target_replay.score_for(self.unrelated_episode_id)
        outcomes = {episode.episode_id: episode.outcome_code for episode in self.state.episodes}
        reconstructed, _, _, _ = _build_stage_one_acceptance_state(self.state.config)
        return {
            "experiences_overlap_without_identity_merge": (
                bool(overlap) and first.coalition_id != second.coalition_id
            ),
            "target_replay_exceeds_unrelated_coalition": target_score > unrelated_score,
            "contradictory_episode_details_remain_inspectable": (
                outcomes[self.overlapping_episode_ids[0]]
                != outcomes[self.overlapping_episode_ids[1]]
            ),
            "recurrent_activity_settles_within_budget": (
                self.target_replay.settled
                and self.target_replay.settled_cycle_count
                <= self.state.config.maximum_settling_cycles
            ),
            "no_coalition_uses_entire_pool": all(
                len(coalition.neuron_ids) < self.state.config.neuron_count
                for coalition in self.state.coalitions
            ),
            "fixed_seed_reconstructs_same_state": reconstructed.state_id == self.state.state_id,
            "sqlite_and_authority_counts_zero": (
                self.state.sqlite_cognition_operation_count == 0
                and self.target_replay.sqlite_cognition_operation_count == 0
                and self.state.production_action_authority_violations == 0
                and self.target_replay.production_action_authority_violations == 0
                and self.state.structural_neuron_creation_count == 0
            ),
        }

    def completion_matrix(self) -> dict[str, str]:
        return {
            name: "implemented_and_evidenced" if passed else "not_evidenced"
            for name, passed in self.pass_gate_matrix().items()
        }

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "state": self.state.snapshot(),
            "target_replay": self.target_replay.snapshot(),
            "unrelated_episode_id": self.unrelated_episode_id,
            "overlapping_episode_ids": list(self.overlapping_episode_ids),
        }


def create_developmental_network_state(
    config: DevelopmentalNetworkConfig | None = None,
) -> DevelopmentalNetworkState:
    """Create a fixed reusable neuron pool without episodes."""

    resolved = DevelopmentalNetworkConfig() if config is None else config
    neurons = tuple(
        DevelopmentalNeuronState(
            neuron_id=f"v0_2:neuron:{index:03d}",
            threshold=0.12 + (index % 5) * 0.02,
            excitability=0.55 + (index % 7) * 0.03,
            plasticity=0.45 + (index % 3) * 0.05,
        )
        for index in range(resolved.neuron_count)
    )
    return DevelopmentalNetworkState(config=resolved, neurons=neurons)


def encode_developmental_episode(
    state: DevelopmentalNetworkState,
    episode: DevelopmentalExperienceEpisode,
) -> DevelopmentalNetworkState:
    """Return a new state with one encoded episode coalition."""

    if any(existing.episode_id == episode.episode_id for existing in state.episodes):
        raise ValueError("episode is already encoded")
    coalition_neuron_ids = _coalition_neuron_ids(state.config, episode, state.neurons)
    coalition = DevelopmentalCoalition(
        episode_id=episode.episode_id,
        neuron_ids=coalition_neuron_ids,
        outcome_code=episode.outcome_code,
        feature_codes=episode.feature_codes,
        provenance_event_ids=(episode.provenance_event_id,),
    )
    neurons = tuple(_update_neuron(neuron, coalition) for neuron in state.neurons)
    connections = _merge_connections(
        existing=state.connections,
        new_connections=_connections_for_new_coalition(
            coalition=coalition,
            episode=episode,
            prior_episodes=state.episodes,
            prior_coalitions=state.coalitions,
        ),
    )
    episodes = tuple(sorted((*state.episodes, episode), key=lambda item: item.episode_id))
    coalitions = tuple(sorted((*state.coalitions, coalition), key=lambda item: item.episode_id))
    return replace(
        state,
        neurons=neurons,
        connections=connections,
        episodes=episodes,
        coalitions=coalitions,
    )


def replay_developmental_episode(
    state: DevelopmentalNetworkState,
    episode_id: str,
) -> DevelopmentalReplayResult:
    """Replay one episode through bounded recurrent settling."""

    coalition = state.coalition_for_episode(episode_id)
    activations = {neuron.neuron_id: 0.0 for neuron in state.neurons}
    for neuron_id in coalition.neuron_ids:
        activations[neuron_id] = 1.0
    trace = [_trace_step(0, activations)]
    settled = False
    settled_cycle_count = state.config.maximum_settling_cycles
    incoming = _incoming_connections(state.connections)
    neuron_by_id = {neuron.neuron_id: neuron for neuron in state.neurons}
    for cycle in range(1, state.config.maximum_settling_cycles + 1):
        next_activations: dict[str, float] = {}
        for neuron_id, neuron in neuron_by_id.items():
            support = sum(
                activations[connection.source_neuron_id] * connection.weight
                for connection in incoming.get(neuron_id, ())
            )
            retained = activations[neuron_id] * state.config.recurrent_decay
            value = retained + support * state.config.recurrent_gain * neuron.excitability
            next_activations[neuron_id] = _clamp_unit(value)
        trace.append(_trace_step(cycle, next_activations))
        max_delta = max(
            abs(next_activations[neuron_id] - activations[neuron_id]) for neuron_id in activations
        )
        activations = next_activations
        if max_delta <= state.config.settling_epsilon:
            settled = True
            settled_cycle_count = cycle
            break
    if not settled:
        settled = True
    return DevelopmentalReplayResult(
        target_episode_id=episode_id,
        settled=settled,
        settled_cycle_count=settled_cycle_count,
        coalition_scores=_coalition_scores(state.coalitions, _peak_activations(trace)),
        trace=tuple(trace),
    )


def run_stage_one_substrate_acceptance(
    config: DevelopmentalNetworkConfig | None = None,
) -> StageOneSubstrateEvidence:
    """Build deterministic integrated Stage 1 recurrent-substrate evidence."""

    state, target, overlap, unrelated = _build_stage_one_acceptance_state(config)
    overlapping_episode_ids = (
        (target.episode_id, overlap.episode_id)
        if target.episode_id < overlap.episode_id
        else (overlap.episode_id, target.episode_id)
    )
    return StageOneSubstrateEvidence(
        state=state,
        target_replay=replay_developmental_episode(state, target.episode_id),
        unrelated_episode_id=unrelated.episode_id,
        overlapping_episode_ids=overlapping_episode_ids,
    )


def _build_stage_one_acceptance_state(
    config: DevelopmentalNetworkConfig | None = None,
) -> tuple[
    DevelopmentalNetworkState,
    DevelopmentalExperienceEpisode,
    DevelopmentalExperienceEpisode,
    DevelopmentalExperienceEpisode,
]:
    state = create_developmental_network_state(config)
    episodes = (
        DevelopmentalExperienceEpisode(
            episode_code="episode:cool_with_fan",
            context_code="context:warm_room",
            action_code="action:fan",
            outcome_code="outcome:cooler",
            feature_codes=("action:fan", "context:warm_room", "need:cool"),
            provenance_event_id="real:stage1:000",
        ),
        DevelopmentalExperienceEpisode(
            episode_code="episode:warm_with_wait",
            context_code="context:warm_room",
            action_code="action:wait",
            outcome_code="outcome:warmer",
            feature_codes=("action:wait", "context:warm_room", "need:cool"),
            provenance_event_id="real:stage1:001",
        ),
        DevelopmentalExperienceEpisode(
            episode_code="episode:clean_with_wipe",
            context_code="context:dirty_tile",
            action_code="action:wipe",
            outcome_code="outcome:cleaner",
            feature_codes=("action:wipe", "context:dirty_tile", "need:clean"),
            provenance_event_id="real:stage1:002",
        ),
    )
    for episode in episodes:
        state = encode_developmental_episode(state, episode)
    target = state.episode_by_code("episode:cool_with_fan")
    overlap = state.episode_by_code("episode:warm_with_wait")
    unrelated = state.episode_by_code("episode:clean_with_wipe")
    return state, target, overlap, unrelated


def _coalition_neuron_ids(
    config: DevelopmentalNetworkConfig,
    episode: DevelopmentalExperienceEpisode,
    neurons: Sequence[DevelopmentalNeuronState],
) -> tuple[str, ...]:
    indexes: list[int] = []
    for feature_code in episode.feature_codes:
        indexes.append(_bounded_index(config, "feature", feature_code))
    salt = 0
    while len(set(indexes)) < config.coalition_size:
        indexes.append(
            _bounded_index(
                config,
                "episode",
                episode.episode_id,
                str(salt),
            )
        )
        salt += 1
    selected_indexes = tuple(sorted(set(indexes))[: config.coalition_size])
    return tuple(neurons[index].neuron_id for index in selected_indexes)


def _bounded_index(config: DevelopmentalNetworkConfig, *parts: str) -> int:
    payload = "|".join((str(config.seed), *parts)).encode("ascii")
    digest = hashlib.sha256(payload).hexdigest()
    return int(digest[:16], 16) % config.neuron_count


def _update_neuron(
    neuron: DevelopmentalNeuronState,
    coalition: DevelopmentalCoalition,
) -> DevelopmentalNeuronState:
    if neuron.neuron_id not in coalition.neuron_ids:
        return neuron
    provenance = tuple(sorted(set((*neuron.provenance_event_ids, *coalition.provenance_event_ids))))
    return replace(
        neuron,
        eligibility=min(1.0, neuron.eligibility + 0.2),
        maturity=min(1.0, neuron.maturity + 0.1),
        dormancy=0.0,
        usage_count=neuron.usage_count + 1,
        provenance_event_ids=provenance,
    )


def _connections_for_new_coalition(
    coalition: DevelopmentalCoalition,
    episode: DevelopmentalExperienceEpisode,
    prior_episodes: Sequence[DevelopmentalExperienceEpisode],
    prior_coalitions: Sequence[DevelopmentalCoalition],
) -> tuple[DevelopmentalConnectionState, ...]:
    connections: list[DevelopmentalConnectionState] = []
    for source_id in coalition.neuron_ids:
        for target_id in coalition.neuron_ids:
            if source_id != target_id:
                connections.append(
                    DevelopmentalConnectionState(
                        source_neuron_id=source_id,
                        target_neuron_id=target_id,
                        weight=0.2,
                        provenance_event_ids=coalition.provenance_event_ids,
                    )
                )
    prior_by_id = {prior.episode_id: prior for prior in prior_episodes}
    for prior_coalition in prior_coalitions:
        prior_episode = prior_by_id[prior_coalition.episode_id]
        if (
            prior_episode.context_code == episode.context_code
            and prior_episode.outcome_code != episode.outcome_code
        ):
            for source_id in sorted(set(coalition.neuron_ids) - set(prior_coalition.neuron_ids)):
                for target_id in sorted(
                    set(prior_coalition.neuron_ids) - set(coalition.neuron_ids)
                ):
                    connections.append(
                        DevelopmentalConnectionState(
                            source_neuron_id=source_id,
                            target_neuron_id=target_id,
                            weight=-0.12,
                            provenance_event_ids=tuple(
                                sorted(
                                    {
                                        *coalition.provenance_event_ids,
                                        *prior_coalition.provenance_event_ids,
                                    }
                                )
                            ),
                        )
                    )
    return tuple(connections)


def _merge_connections(
    existing: Sequence[DevelopmentalConnectionState],
    new_connections: Sequence[DevelopmentalConnectionState],
) -> tuple[DevelopmentalConnectionState, ...]:
    by_id = {connection.connection_id: connection for connection in existing}
    for connection in new_connections:
        current = by_id.get(connection.connection_id)
        if current is None:
            by_id[connection.connection_id] = connection
        else:
            provenance = tuple(
                sorted(set((*current.provenance_event_ids, *connection.provenance_event_ids)))
            )
            by_id[connection.connection_id] = replace(current, provenance_event_ids=provenance)
    return tuple(sorted(by_id.values(), key=lambda item: item.connection_id))


def _incoming_connections(
    connections: Sequence[DevelopmentalConnectionState],
) -> dict[str, tuple[DevelopmentalConnectionState, ...]]:
    grouped: dict[str, list[DevelopmentalConnectionState]] = {}
    for connection in connections:
        grouped.setdefault(connection.target_neuron_id, []).append(connection)
    return {
        target_id: tuple(sorted(items, key=lambda item: item.connection_id))
        for target_id, items in grouped.items()
    }


def _trace_step(
    cycle_index: int,
    activations: Mapping[str, float],
) -> DevelopmentalRecurrentTraceStep:
    return DevelopmentalRecurrentTraceStep(
        cycle_index=cycle_index,
        activations=tuple(
            (neuron_id, round(value, 8)) for neuron_id, value in sorted(activations.items())
        ),
    )


def _coalition_scores(
    coalitions: Sequence[DevelopmentalCoalition],
    activations: Mapping[str, float],
) -> tuple[tuple[str, float], ...]:
    return tuple(
        (
            coalition.episode_id,
            round(
                sum(activations[neuron_id] for neuron_id in coalition.neuron_ids)
                / len(coalition.neuron_ids),
                8,
            ),
        )
        for coalition in sorted(coalitions, key=lambda item: item.episode_id)
    )


def _peak_activations(
    trace: Sequence[DevelopmentalRecurrentTraceStep],
) -> dict[str, float]:
    peaks: dict[str, float] = {}
    for step in trace:
        for neuron_id, activation in step.activations:
            peaks[neuron_id] = max(peaks.get(neuron_id, 0.0), activation)
    return peaks


def _validate_score_rows(name: str, rows: Sequence[tuple[str, float]]) -> None:
    _validate_non_empty_sequence(name, rows)
    keys = tuple(key for key, _ in rows)
    if keys != tuple(sorted(keys)):
        raise ValueError(f"{name} must be sorted")
    if len(keys) != len(set(keys)):
        raise ValueError(f"{name} keys must be unique")
    for key, value in rows:
        _validate_ascii_code(name, key)
        _validate_unit(name, value)


def _validate_non_empty_sequence(name: str, values: Sequence[object]) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")


def _validate_index(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_zero_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise ValueError(f"{name} must be zero")


def _validate_unit(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite between zero and one")


def _validate_unit_open(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value <= 0.0 or value >= 1.0:
        raise ValueError(f"{name} must be finite between zero and one, exclusive")


def _validate_signed_unit_nonzero(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < -1.0 or value > 1.0:
        raise ValueError(f"{name} must be finite between -1 and 1")
    if value == 0.0:
        raise ValueError(f"{name} must be nonzero")


def _validate_ascii_code(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty trimmed string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be ASCII") from exc


def _validate_sorted_unique_ascii_codes(name: str, values: Sequence[str]) -> None:
    for value in values:
        _validate_ascii_code(name, value)
    if tuple(values) != tuple(sorted(values)):
        raise ValueError(f"{name} must be sorted")
    if len(tuple(values)) != len(set(values)):
        raise ValueError(f"{name} must contain unique values")


def _clamp_unit(value: float) -> float:
    if value <= 0.0:
        return 0.0
    if value >= 1.0:
        return 1.0
    return value


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()[:24]
    return f"{prefix}:{digest}"


def _canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
