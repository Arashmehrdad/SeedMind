"""Stage 2 associative need-and-context recall over distinct experiences."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, replace
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.developmental_network import (
    DevelopmentalExperienceEpisode,
    DevelopmentalNetworkConfig,
    DevelopmentalNetworkState,
    create_developmental_network_state,
    encode_developmental_episode,
)


class AssociativeRecallLinkKind(StrEnum):
    """Typed Stage 2 associative links."""

    NEED_TO_EXPERIENCE = "need_to_experience"
    CONTEXT_TO_EXPERIENCE = "context_to_experience"
    EXPERIENCE_TO_EXPERIENCE = "experience_to_experience"
    ACTION_TO_EXPERIENCE = "action_to_experience"
    OUTCOME_TO_EXPERIENCE = "outcome_to_experience"
    INHIBITION = "inhibition"


class AssociativeRecallControl(StrEnum):
    """Matched Stage 2 recall controls and ablations."""

    FULL_ASSOCIATIVE = "full_associative"
    NEED_REMOVED = "need_removed"
    CONTEXT_REMOVED = "context_removed"
    INHIBITION_REMOVED = "inhibition_removed"
    SHUFFLED_LINKS = "shuffled_links"
    ONE_WINNER_ONLY = "one_winner_only"
    EXACT_CONTEXT_ONLY = "exact_context_only"


@dataclass(frozen=True, slots=True)
class AssociativeRecallConfig:
    """Finite deterministic Stage 2 associative-recall bounds."""

    seed: int = 31
    maximum_recall_depth: int = 3
    compatible_coalition_limit: int = 2
    false_coactivation_threshold: float = 0.2
    recurrent_support_gain: float = 0.45
    dormancy_cost_weight: float = 1.2
    depth_cost_weight: float = 0.55

    def __post_init__(self) -> None:
        _validate_non_negative_int("seed", self.seed)
        _validate_positive_int("maximum_recall_depth", self.maximum_recall_depth)
        _validate_positive_int("compatible_coalition_limit", self.compatible_coalition_limit)
        _validate_unit("false_coactivation_threshold", self.false_coactivation_threshold)
        _validate_unit_open("recurrent_support_gain", self.recurrent_support_gain)
        _validate_non_negative_finite("dormancy_cost_weight", self.dormancy_cost_weight)
        _validate_non_negative_finite("depth_cost_weight", self.depth_cost_weight)

    def snapshot(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "maximum_recall_depth": self.maximum_recall_depth,
            "compatible_coalition_limit": self.compatible_coalition_limit,
            "false_coactivation_threshold": self.false_coactivation_threshold,
            "recurrent_support_gain": self.recurrent_support_gain,
            "dormancy_cost_weight": self.dormancy_cost_weight,
            "depth_cost_weight": self.depth_cost_weight,
        }


@dataclass(frozen=True, slots=True)
class AssociativeRecallCue:
    """A partial need-and-context cue for Stage 2 recall."""

    cue_code: str
    need_code: str
    current_context_code: str
    partial_context_codes: tuple[str, ...]
    action_codes: tuple[str, ...] = ()
    outcome_codes: tuple[str, ...] = ()
    maximum_depth: int = 3

    def __post_init__(self) -> None:
        _validate_ascii_code("cue_code", self.cue_code)
        _validate_ascii_code("need_code", self.need_code)
        _validate_ascii_code("current_context_code", self.current_context_code)
        _validate_sorted_unique_ascii_codes("partial_context_codes", self.partial_context_codes)
        _validate_sorted_unique_ascii_codes("action_codes", self.action_codes)
        _validate_sorted_unique_ascii_codes("outcome_codes", self.outcome_codes)
        _validate_positive_int("maximum_depth", self.maximum_depth)
        if not self.partial_context_codes:
            raise ValueError("Stage 2 recall requires at least one partial context cue")
        if self.current_context_code in self.partial_context_codes:
            raise ValueError("current context must stay distinct from partial context cues")

    @property
    def cue_id(self) -> str:
        return _identity("associative-recall-cue", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"cue_id": self.cue_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "cue_code": self.cue_code,
            "need_code": self.need_code,
            "current_context_code": self.current_context_code,
            "partial_context_codes": list(self.partial_context_codes),
            "action_codes": list(self.action_codes),
            "outcome_codes": list(self.outcome_codes),
            "maximum_depth": self.maximum_depth,
        }


@dataclass(frozen=True, slots=True)
class AssociativeRecallLink:
    """One learned association without merging the source experience."""

    kind: AssociativeRecallLinkKind
    source_code: str
    target_episode_id: str
    weight: float
    provenance_episode_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_ascii_code("source_code", self.source_code)
        _validate_ascii_code("target_episode_id", self.target_episode_id)
        _validate_signed_unit_nonzero("weight", self.weight)
        _validate_sorted_unique_ascii_codes("provenance_episode_ids", self.provenance_episode_ids)
        if self.kind is AssociativeRecallLinkKind.INHIBITION and self.weight >= 0.0:
            raise ValueError("inhibition links must have negative weight")
        if self.kind is not AssociativeRecallLinkKind.INHIBITION and self.weight <= 0.0:
            raise ValueError("non-inhibitory associative links must have positive weight")
        if self.target_episode_id not in self.provenance_episode_ids:
            raise ValueError("target episode must be included in link provenance")

    @property
    def link_id(self) -> str:
        return _identity("associative-recall-link", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"link_id": self.link_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "source_code": self.source_code,
            "target_episode_id": self.target_episode_id,
            "weight": self.weight,
            "provenance_episode_ids": list(self.provenance_episode_ids),
        }


@dataclass(frozen=True, slots=True)
class AssociativeRecallActivation:
    """One episode's inspectable activation under a partial cue."""

    episode_id: str
    episode_code: str
    need_codes: tuple[str, ...]
    context_code: str
    action_code: str
    outcome_code: str
    depth_scores: tuple[tuple[int, float], ...]
    direct_support: float
    pattern_completion_support: float
    inhibition: float
    final_score: float
    compatible_episode_ids: tuple[str, ...] = ()
    inhibited_by_episode_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in (
            ("episode_id", self.episode_id),
            ("episode_code", self.episode_code),
            ("context_code", self.context_code),
            ("action_code", self.action_code),
            ("outcome_code", self.outcome_code),
        ):
            _validate_ascii_code(name, value)
        _validate_sorted_unique_ascii_codes("need_codes", self.need_codes)
        _validate_score_rows("depth_scores", self.depth_scores)
        _validate_unit("direct_support", self.direct_support)
        _validate_unit("pattern_completion_support", self.pattern_completion_support)
        _validate_unit("inhibition", self.inhibition)
        _validate_unit("final_score", self.final_score)
        _validate_sorted_unique_ascii_codes("compatible_episode_ids", self.compatible_episode_ids)
        _validate_sorted_unique_ascii_codes(
            "inhibited_by_episode_ids", self.inhibited_by_episode_ids
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "episode_id": self.episode_id,
            "episode_code": self.episode_code,
            "need_codes": list(self.need_codes),
            "context_code": self.context_code,
            "action_code": self.action_code,
            "outcome_code": self.outcome_code,
            "depth_scores": [
                {"depth": depth, "score": score} for depth, score in self.depth_scores
            ],
            "direct_support": self.direct_support,
            "pattern_completion_support": self.pattern_completion_support,
            "inhibition": self.inhibition,
            "final_score": self.final_score,
            "compatible_episode_ids": list(self.compatible_episode_ids),
            "inhibited_by_episode_ids": list(self.inhibited_by_episode_ids),
        }


@dataclass(frozen=True, slots=True)
class AssociativeRecallResult:
    """Finite, non-authoritative Stage 2 recall result."""

    cue: AssociativeRecallCue
    control: AssociativeRecallControl
    activations: tuple[AssociativeRecallActivation, ...]
    dominant_episode_ids: tuple[str, ...]
    recall_depth: int
    effort_cost: float
    sqlite_cognition_operation_count: int = 0
    external_side_effect_count: int = 0
    production_action_authority_violations: int = 0

    def __post_init__(self) -> None:
        _validate_non_empty_sequence("activations", self.activations)
        episode_ids = tuple(activation.episode_id for activation in self.activations)
        if episode_ids != tuple(sorted(episode_ids)):
            raise ValueError("recall activations must be sorted by episode identity")
        if len(episode_ids) != len(set(episode_ids)):
            raise ValueError("recall activations must contain unique episodes")
        _validate_unique_ascii_codes("dominant_episode_ids", self.dominant_episode_ids)
        if not set(self.dominant_episode_ids).issubset(set(episode_ids)):
            raise ValueError("dominant episodes must be present in activations")
        _validate_positive_int("recall_depth", self.recall_depth)
        if self.recall_depth > self.cue.maximum_depth:
            raise ValueError("recall depth cannot exceed cue maximum depth")
        _validate_non_negative_finite("effort_cost", self.effort_cost)
        _validate_zero_int(
            "sqlite_cognition_operation_count",
            self.sqlite_cognition_operation_count,
        )
        _validate_zero_int("external_side_effect_count", self.external_side_effect_count)
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )

    @property
    def result_id(self) -> str:
        return _identity("associative-recall-result", self._identity_payload())

    @property
    def activation_order(self) -> tuple[str, ...]:
        ordered = sorted(
            self.activations,
            key=lambda activation: (-activation.final_score, activation.episode_id),
        )
        return tuple(activation.episode_code for activation in ordered)

    @property
    def false_coactivation_rate(self) -> float:
        unrelated_scores = tuple(
            activation.final_score
            for activation in self.activations
            if self.cue.need_code not in activation.need_codes
        )
        if not unrelated_scores:
            return 0.0
        return round(max(unrelated_scores), 8)

    @property
    def dominant_score(self) -> float:
        score_by_id = {
            activation.episode_id: activation.final_score for activation in self.activations
        }
        return round(sum(score_by_id[episode_id] for episode_id in self.dominant_episode_ids), 8)

    def activation_for_episode_code(self, episode_code: str) -> AssociativeRecallActivation:
        matches = tuple(
            activation for activation in self.activations if activation.episode_code == episode_code
        )
        if len(matches) != 1:
            raise ValueError("episode_code must match exactly one activation")
        return matches[0]

    def score_for_episode_code(self, episode_code: str) -> float:
        return self.activation_for_episode_code(episode_code).final_score

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "cue": self.cue.snapshot(),
            "control": self.control.value,
            "activations": [activation.snapshot() for activation in self.activations],
            "dominant_episode_ids": list(self.dominant_episode_ids),
            "recall_depth": self.recall_depth,
            "effort_cost": self.effort_cost,
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
            "external_side_effect_count": self.external_side_effect_count,
            "production_action_authority_violations": self.production_action_authority_violations,
        }


@dataclass(frozen=True, slots=True)
class RecallCostMeasurement:
    """Effort evidence for bounded depth and dormancy."""

    measurement_code: str
    recall_depth: int
    dormancy: float
    effort_cost: float

    def __post_init__(self) -> None:
        _validate_ascii_code("measurement_code", self.measurement_code)
        _validate_positive_int("recall_depth", self.recall_depth)
        _validate_unit("dormancy", self.dormancy)
        _validate_non_negative_finite("effort_cost", self.effort_cost)

    def snapshot(self) -> dict[str, object]:
        return {
            "measurement_code": self.measurement_code,
            "recall_depth": self.recall_depth,
            "dormancy": self.dormancy,
            "effort_cost": self.effort_cost,
        }


@dataclass(frozen=True, slots=True)
class StageTwoAssociativeRecallEvidence:
    """Integrated Stage 2 associative recall acceptance evidence."""

    config: AssociativeRecallConfig
    state: DevelopmentalNetworkState
    links: tuple[AssociativeRecallLink, ...]
    warm_sunny_recall: AssociativeRecallResult
    humid_recall: AssociativeRecallResult
    controls: tuple[AssociativeRecallResult, ...]
    cost_measurements: tuple[RecallCostMeasurement, ...]
    relevant_episode_codes: tuple[str, ...]
    unrelated_episode_code: str

    def __post_init__(self) -> None:
        _validate_non_empty_sequence("links", self.links)
        link_ids = tuple(link.link_id for link in self.links)
        if link_ids != tuple(sorted(link_ids)):
            raise ValueError("associative links must be sorted by identity")
        if len(link_ids) != len(set(link_ids)):
            raise ValueError("associative links must be unique")
        _validate_non_empty_sequence("controls", self.controls)
        _validate_non_empty_sequence("cost_measurements", self.cost_measurements)
        _validate_sorted_unique_ascii_codes("relevant_episode_codes", self.relevant_episode_codes)
        _validate_ascii_code("unrelated_episode_code", self.unrelated_episode_code)
        if self.unrelated_episode_code in self.relevant_episode_codes:
            raise ValueError("unrelated episode cannot be need relevant")
        controls = {result.control for result in self.controls}
        expected_controls = set(AssociativeRecallControl) - {
            AssociativeRecallControl.FULL_ASSOCIATIVE
        }
        if controls != expected_controls:
            raise ValueError("Stage 2 evidence must include every recall control")
        required_link_kinds = set(AssociativeRecallLinkKind)
        if {link.kind for link in self.links} != required_link_kinds:
            raise ValueError("Stage 2 links must include every associative link kind")
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage 2 pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-two-associative-recall-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        unrelated_score = self.warm_sunny_recall.score_for_episode_code(self.unrelated_episode_code)
        relevant_scores = tuple(
            self.warm_sunny_recall.score_for_episode_code(code)
            for code in self.relevant_episode_codes
        )
        control_by_kind = {result.control: result for result in self.controls}
        shuffled = control_by_kind[AssociativeRecallControl.SHUFFLED_LINKS]
        one_winner = control_by_kind[AssociativeRecallControl.ONE_WINNER_ONLY]
        context_removed = control_by_kind[AssociativeRecallControl.CONTEXT_REMOVED]
        inhibition_removed = control_by_kind[AssociativeRecallControl.INHIBITION_REMOVED]
        contradictory = self.warm_sunny_recall.activation_for_episode_code("episode:cool_warm_wait")
        contradiction_without_inhibition = inhibition_removed.activation_for_episode_code(
            "episode:cool_warm_wait"
        )
        first_cost = self.cost_measurements[0]
        deeper_cost = self.cost_measurements[1]
        dormant_cost = self.cost_measurements[2]
        state_episode_ids = tuple(episode.episode_id for episode in self.state.episodes)
        return {
            "need_relevant_experiences_exceed_unrelated": min(relevant_scores) > unrelated_score,
            "present_context_changes_response_ordering": (
                self.warm_sunny_recall.activation_order[0] != self.humid_recall.activation_order[0]
                and self.humid_recall.activation_order[0] == "episode:cool_humid_vent"
                and context_removed.activation_order[0]
                != self.warm_sunny_recall.activation_order[0]
            ),
            "compatible_context_coalition_dominates": (
                {
                    activation.episode_code
                    for activation in self.warm_sunny_recall.activations
                    if activation.episode_id in self.warm_sunny_recall.dominant_episode_ids
                }
                == {"episode:cool_sunny_blinds", "episode:cool_warm_fan"}
                and self.warm_sunny_recall.dominant_score > one_winner.dominant_score
            ),
            "original_experience_identities_remain_inspectable": (
                len(self.state.episodes) == 5
                and len(state_episode_ids) == len(set(state_episode_ids))
                and len(
                    {
                        self.state.episode_by_code(code).episode_id
                        for code in self.relevant_episode_codes
                    }
                )
                == len(self.relevant_episode_codes)
            ),
            "contradictory_experience_available_but_inhibited": (
                contradictory.final_score > unrelated_score
                and contradictory.inhibition > 0.0
                and contradictory.final_score
                < self.warm_sunny_recall.score_for_episode_code("episode:cool_warm_fan")
                and contradiction_without_inhibition.final_score > contradictory.final_score
            ),
            "partial_cue_beats_shuffled_control": (
                self.warm_sunny_recall.dominant_score > shuffled.dominant_score
                and self.warm_sunny_recall.activation_order[0] != shuffled.activation_order[0]
            ),
            "false_coactivation_below_threshold": (
                self.warm_sunny_recall.false_coactivation_rate
                <= self.config.false_coactivation_threshold
            ),
            "recall_cost_rises_with_depth_and_dormancy": (
                first_cost.recall_depth < deeper_cost.recall_depth
                and first_cost.dormancy == deeper_cost.dormancy
                and first_cost.effort_cost < deeper_cost.effort_cost
                and deeper_cost.recall_depth == dormant_cost.recall_depth
                and deeper_cost.dormancy < dormant_cost.dormancy
                and deeper_cost.effort_cost < dormant_cost.effort_cost
            ),
            "sqlite_and_authority_counts_zero": (
                self.state.sqlite_cognition_operation_count == 0
                and self.warm_sunny_recall.sqlite_cognition_operation_count == 0
                and self.humid_recall.sqlite_cognition_operation_count == 0
                and all(result.sqlite_cognition_operation_count == 0 for result in self.controls)
                and self.state.production_action_authority_violations == 0
                and self.warm_sunny_recall.production_action_authority_violations == 0
                and self.humid_recall.production_action_authority_violations == 0
                and all(
                    result.production_action_authority_violations == 0 for result in self.controls
                )
                and self.warm_sunny_recall.external_side_effect_count == 0
                and self.humid_recall.external_side_effect_count == 0
                and all(result.external_side_effect_count == 0 for result in self.controls)
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
            "config": self.config.snapshot(),
            "state_id": self.state.state_id,
            "links": [link.snapshot() for link in self.links],
            "warm_sunny_recall": self.warm_sunny_recall.snapshot(),
            "humid_recall": self.humid_recall.snapshot(),
            "controls": [result.snapshot() for result in self.controls],
            "cost_measurements": [measurement.snapshot() for measurement in self.cost_measurements],
            "relevant_episode_codes": list(self.relevant_episode_codes),
            "unrelated_episode_code": self.unrelated_episode_code,
        }


def run_associative_recall(
    state: DevelopmentalNetworkState,
    links: Sequence[AssociativeRecallLink],
    cue: AssociativeRecallCue,
    config: AssociativeRecallConfig | None = None,
    control: AssociativeRecallControl = AssociativeRecallControl.FULL_ASSOCIATIVE,
) -> AssociativeRecallResult:
    """Run deterministic bounded associative recall without action authority."""

    resolved = AssociativeRecallConfig() if config is None else config
    if cue.maximum_depth > resolved.maximum_recall_depth:
        raise ValueError("cue maximum depth exceeds recall configuration")
    episode_by_id = {episode.episode_id: episode for episode in state.episodes}
    if set(link.target_episode_id for link in links) - set(episode_by_id):
        raise ValueError("associative links must target encoded episodes")
    active_links = _control_links(tuple(links), tuple(sorted(episode_by_id)), control)
    depth_scores, direct_supports, pattern_supports, inhibitions, compatible, inhibited_by = (
        _settle_associative_scores(state, active_links, cue, resolved, control)
    )
    activations = tuple(
        AssociativeRecallActivation(
            episode_id=episode.episode_id,
            episode_code=episode.episode_code,
            need_codes=_episode_need_codes(episode),
            context_code=episode.context_code,
            action_code=episode.action_code,
            outcome_code=episode.outcome_code,
            depth_scores=depth_scores[episode.episode_id],
            direct_support=direct_supports[episode.episode_id],
            pattern_completion_support=pattern_supports[episode.episode_id],
            inhibition=inhibitions[episode.episode_id],
            final_score=depth_scores[episode.episode_id][-1][1],
            compatible_episode_ids=tuple(sorted(compatible[episode.episode_id])),
            inhibited_by_episode_ids=tuple(sorted(inhibited_by[episode.episode_id])),
        )
        for episode in sorted(state.episodes, key=lambda item: item.episode_id)
    )
    dominant_episode_ids = _dominant_episode_ids(cue, activations, resolved, control)
    return AssociativeRecallResult(
        cue=cue,
        control=control,
        activations=activations,
        dominant_episode_ids=dominant_episode_ids,
        recall_depth=cue.maximum_depth,
        effort_cost=_estimated_effort_cost(resolved, cue.maximum_depth, dormancy=0.1),
    )


def run_stage_two_associative_recall_acceptance(
    config: AssociativeRecallConfig | None = None,
) -> StageTwoAssociativeRecallEvidence:
    """Build deterministic integrated Stage 2 associative-recall evidence."""

    resolved = AssociativeRecallConfig() if config is None else config
    state = build_stage_two_associative_state(resolved)
    links = build_stage_two_associative_links(state)
    warm_sunny_cue = AssociativeRecallCue(
        cue_code="cue:warm_sunny_cooling",
        need_code="need:cool",
        current_context_code="context:warm_sunny_room",
        partial_context_codes=("context:sunny_room", "context:warm_room"),
        maximum_depth=resolved.maximum_recall_depth,
    )
    humid_cue = AssociativeRecallCue(
        cue_code="cue:humid_cooling",
        need_code="need:cool",
        current_context_code="context:humid_shadow_room",
        partial_context_codes=("context:humid_room",),
        maximum_depth=resolved.maximum_recall_depth,
    )
    warm_sunny_recall = run_associative_recall(state, links, warm_sunny_cue, resolved)
    humid_recall = run_associative_recall(state, links, humid_cue, resolved)
    controls = tuple(
        run_associative_recall(state, links, warm_sunny_cue, resolved, control)
        for control in AssociativeRecallControl
        if control is not AssociativeRecallControl.FULL_ASSOCIATIVE
    )
    return StageTwoAssociativeRecallEvidence(
        config=resolved,
        state=state,
        links=links,
        warm_sunny_recall=warm_sunny_recall,
        humid_recall=humid_recall,
        controls=controls,
        cost_measurements=(
            RecallCostMeasurement(
                measurement_code="cost:depth1_low_dormancy",
                recall_depth=1,
                dormancy=0.1,
                effort_cost=_estimated_effort_cost(resolved, 1, dormancy=0.1),
            ),
            RecallCostMeasurement(
                measurement_code="cost:depth3_low_dormancy",
                recall_depth=resolved.maximum_recall_depth,
                dormancy=0.1,
                effort_cost=_estimated_effort_cost(
                    resolved,
                    resolved.maximum_recall_depth,
                    dormancy=0.1,
                ),
            ),
            RecallCostMeasurement(
                measurement_code="cost:depth3_high_dormancy",
                recall_depth=resolved.maximum_recall_depth,
                dormancy=0.7,
                effort_cost=_estimated_effort_cost(
                    resolved,
                    resolved.maximum_recall_depth,
                    dormancy=0.7,
                ),
            ),
        ),
        relevant_episode_codes=(
            "episode:cool_humid_vent",
            "episode:cool_sunny_blinds",
            "episode:cool_warm_fan",
            "episode:cool_warm_wait",
        ),
        unrelated_episode_code="episode:clean_dirty_wipe",
    )


def build_stage_two_associative_state(
    config: AssociativeRecallConfig | None = None,
) -> DevelopmentalNetworkState:
    """Encode the canonical Stage 2 experience family in a Stage 1 substrate."""

    resolved = AssociativeRecallConfig() if config is None else config
    state = create_developmental_network_state(
        DevelopmentalNetworkConfig(
            seed=resolved.seed,
            neuron_count=40,
            coalition_size=6,
            maximum_settling_cycles=12,
        )
    )
    for episode in _stage_two_episodes():
        state = encode_developmental_episode(state, episode)
    return state


def build_stage_two_associative_links(
    state: DevelopmentalNetworkState,
) -> tuple[AssociativeRecallLink, ...]:
    """Build deterministic Stage 2 typed associative links from encoded episodes."""

    links: list[AssociativeRecallLink] = []
    for episode in state.episodes:
        for need_code in _episode_need_codes(episode):
            links.append(
                AssociativeRecallLink(
                    AssociativeRecallLinkKind.NEED_TO_EXPERIENCE,
                    need_code,
                    episode.episode_id,
                    0.42,
                    (episode.episode_id,),
                )
            )
        for context_code in _episode_context_feature_codes(episode):
            links.append(
                AssociativeRecallLink(
                    AssociativeRecallLinkKind.CONTEXT_TO_EXPERIENCE,
                    context_code,
                    episode.episode_id,
                    0.35,
                    (episode.episode_id,),
                )
            )
        links.append(
            AssociativeRecallLink(
                AssociativeRecallLinkKind.ACTION_TO_EXPERIENCE,
                episode.action_code,
                episode.episode_id,
                0.18,
                (episode.episode_id,),
            )
        )
        links.append(
            AssociativeRecallLink(
                AssociativeRecallLinkKind.OUTCOME_TO_EXPERIENCE,
                episode.outcome_code,
                episode.episode_id,
                0.15,
                (episode.episode_id,),
            )
        )
    episode_by_id = {episode.episode_id: episode for episode in state.episodes}
    for source in state.episodes:
        for target in state.episodes:
            if source.episode_id == target.episode_id:
                continue
            shared_need = set(_episode_need_codes(source)) & set(_episode_need_codes(target))
            if not shared_need:
                continue
            provenance = tuple(sorted((source.episode_id, target.episode_id)))
            if source.outcome_code == "outcome:cooler" and target.outcome_code == "outcome:cooler":
                links.append(
                    AssociativeRecallLink(
                        AssociativeRecallLinkKind.EXPERIENCE_TO_EXPERIENCE,
                        source.episode_id,
                        target.episode_id,
                        0.12,
                        provenance,
                    )
                )
            if (
                source.context_code == target.context_code
                and source.outcome_code == "outcome:cooler"
                and target.outcome_code != "outcome:cooler"
            ):
                links.append(
                    AssociativeRecallLink(
                        AssociativeRecallLinkKind.INHIBITION,
                        source.episode_id,
                        target.episode_id,
                        -0.34,
                        provenance,
                    )
                )
            if (
                source.context_code == target.context_code
                and source.outcome_code != "outcome:cooler"
                and episode_by_id[target.episode_id].outcome_code == "outcome:cooler"
            ):
                links.append(
                    AssociativeRecallLink(
                        AssociativeRecallLinkKind.INHIBITION,
                        source.episode_id,
                        target.episode_id,
                        -0.05,
                        provenance,
                    )
                )
    return tuple(sorted(links, key=lambda item: item.link_id))


def _settle_associative_scores(
    state: DevelopmentalNetworkState,
    links: Sequence[AssociativeRecallLink],
    cue: AssociativeRecallCue,
    config: AssociativeRecallConfig,
    control: AssociativeRecallControl,
) -> tuple[
    dict[str, tuple[tuple[int, float], ...]],
    dict[str, float],
    dict[str, float],
    dict[str, float],
    dict[str, set[str]],
    dict[str, set[str]],
]:
    episode_ids = tuple(episode.episode_id for episode in state.episodes)
    direct_scores = {episode_id: 0.0 for episode_id in episode_ids}
    source_codes = _cue_source_codes(cue, control)
    for link in links:
        if (
            link.kind
            in {
                AssociativeRecallLinkKind.NEED_TO_EXPERIENCE,
                AssociativeRecallLinkKind.CONTEXT_TO_EXPERIENCE,
                AssociativeRecallLinkKind.ACTION_TO_EXPERIENCE,
                AssociativeRecallLinkKind.OUTCOME_TO_EXPERIENCE,
            }
            and _link_kind_enabled(link.kind, control)
            and link.source_code in source_codes
        ):
            direct_scores[link.target_episode_id] += link.weight
    scores = {episode_id: _clamp_unit(value) for episode_id, value in direct_scores.items()}
    depth_rows: dict[str, list[tuple[int, float]]] = {
        episode_id: [(1, round(score, 8))] for episode_id, score in scores.items()
    }
    total_pattern = {episode_id: 0.0 for episode_id in episode_ids}
    total_inhibition = {episode_id: 0.0 for episode_id in episode_ids}
    compatible = {episode_id: set[str]() for episode_id in episode_ids}
    inhibited_by = {episode_id: set[str]() for episode_id in episode_ids}
    for depth in range(2, cue.maximum_depth + 1):
        previous = dict(scores)
        next_scores: dict[str, float] = {}
        for episode_id in episode_ids:
            pattern_support = 0.0
            inhibition = 0.0
            for link in links:
                if link.target_episode_id != episode_id:
                    continue
                source_score = previous.get(link.source_code, 0.0)
                if (
                    link.kind is AssociativeRecallLinkKind.EXPERIENCE_TO_EXPERIENCE
                    and _link_kind_enabled(link.kind, control)
                ):
                    support = source_score * link.weight * config.recurrent_support_gain
                    pattern_support += support
                    if support > 0.0:
                        compatible[episode_id].add(link.source_code)
                elif link.kind is AssociativeRecallLinkKind.INHIBITION and _link_kind_enabled(
                    link.kind, control
                ):
                    penalty = source_score * abs(link.weight) * config.recurrent_support_gain
                    inhibition += penalty
                    if penalty > 0.0:
                        inhibited_by[episode_id].add(link.source_code)
            total_pattern[episode_id] += pattern_support
            total_inhibition[episode_id] += inhibition
            retained = previous[episode_id] * 0.82
            direct = direct_scores[episode_id] * 0.18
            next_scores[episode_id] = _clamp_unit(retained + direct + pattern_support - inhibition)
        scores = next_scores
        for episode_id in episode_ids:
            depth_rows[episode_id].append((depth, round(scores[episode_id], 8)))
    return (
        {episode_id: tuple(rows) for episode_id, rows in depth_rows.items()},
        {episode_id: round(_clamp_unit(value), 8) for episode_id, value in direct_scores.items()},
        {episode_id: round(_clamp_unit(value), 8) for episode_id, value in total_pattern.items()},
        {
            episode_id: round(_clamp_unit(value), 8)
            for episode_id, value in total_inhibition.items()
        },
        compatible,
        inhibited_by,
    )


def _dominant_episode_ids(
    cue: AssociativeRecallCue,
    activations: Sequence[AssociativeRecallActivation],
    config: AssociativeRecallConfig,
    control: AssociativeRecallControl,
) -> tuple[str, ...]:
    limit = (
        1
        if control is AssociativeRecallControl.ONE_WINNER_ONLY
        else config.compatible_coalition_limit
    )
    candidates = tuple(
        activation
        for activation in activations
        if cue.need_code in activation.need_codes
        and activation.outcome_code == "outcome:cooler"
        and activation.final_score > 0.0
    )
    if not candidates:
        candidates = tuple(activation for activation in activations if activation.final_score > 0.0)
    ordered = sorted(candidates, key=lambda item: (-item.final_score, item.episode_id))
    return tuple(item.episode_id for item in ordered[:limit])


def _control_links(
    links: tuple[AssociativeRecallLink, ...],
    episode_ids: tuple[str, ...],
    control: AssociativeRecallControl,
) -> tuple[AssociativeRecallLink, ...]:
    if control is not AssociativeRecallControl.SHUFFLED_LINKS:
        return links
    rotated = {
        episode_id: episode_ids[(index + 1) % len(episode_ids)]
        for index, episode_id in enumerate(episode_ids)
    }
    return tuple(
        sorted(
            (
                replace(
                    link,
                    target_episode_id=rotated[link.target_episode_id],
                    provenance_episode_ids=tuple(
                        sorted({*link.provenance_episode_ids, rotated[link.target_episode_id]})
                    ),
                )
                for link in links
            ),
            key=lambda item: item.link_id,
        )
    )


def _cue_source_codes(
    cue: AssociativeRecallCue,
    control: AssociativeRecallControl,
) -> set[str]:
    if control is AssociativeRecallControl.EXACT_CONTEXT_ONLY:
        context_codes: tuple[str, ...] = (cue.current_context_code,)
    else:
        context_codes = cue.partial_context_codes
    return {
        cue.need_code,
        *context_codes,
        *cue.action_codes,
        *cue.outcome_codes,
    }


def _link_kind_enabled(
    kind: AssociativeRecallLinkKind,
    control: AssociativeRecallControl,
) -> bool:
    if control is AssociativeRecallControl.NEED_REMOVED:
        return kind is not AssociativeRecallLinkKind.NEED_TO_EXPERIENCE
    if control in {
        AssociativeRecallControl.CONTEXT_REMOVED,
        AssociativeRecallControl.EXACT_CONTEXT_ONLY,
    }:
        return kind is not AssociativeRecallLinkKind.CONTEXT_TO_EXPERIENCE
    if control is AssociativeRecallControl.INHIBITION_REMOVED:
        return kind is not AssociativeRecallLinkKind.INHIBITION
    return True


def _stage_two_episodes() -> tuple[DevelopmentalExperienceEpisode, ...]:
    return (
        DevelopmentalExperienceEpisode(
            episode_code="episode:cool_warm_fan",
            context_code="context:warm_room",
            action_code="action:fan",
            outcome_code="outcome:cooler",
            feature_codes=("action:fan", "context:warm_room", "need:cool", "outcome:cooler"),
            provenance_event_id="real:stage2:000",
        ),
        DevelopmentalExperienceEpisode(
            episode_code="episode:cool_sunny_blinds",
            context_code="context:sunny_room",
            action_code="action:close_blinds",
            outcome_code="outcome:cooler",
            feature_codes=(
                "action:close_blinds",
                "context:sunny_room",
                "need:cool",
                "outcome:cooler",
            ),
            provenance_event_id="real:stage2:001",
        ),
        DevelopmentalExperienceEpisode(
            episode_code="episode:cool_humid_vent",
            context_code="context:humid_room",
            action_code="action:vent",
            outcome_code="outcome:cooler",
            feature_codes=("action:vent", "context:humid_room", "need:cool", "outcome:cooler"),
            provenance_event_id="real:stage2:002",
        ),
        DevelopmentalExperienceEpisode(
            episode_code="episode:cool_warm_wait",
            context_code="context:warm_room",
            action_code="action:wait",
            outcome_code="outcome:warmer",
            feature_codes=("action:wait", "context:warm_room", "need:cool", "outcome:warmer"),
            provenance_event_id="real:stage2:003",
        ),
        DevelopmentalExperienceEpisode(
            episode_code="episode:clean_dirty_wipe",
            context_code="context:dirty_tile",
            action_code="action:wipe",
            outcome_code="outcome:cleaner",
            feature_codes=("action:wipe", "context:dirty_tile", "need:clean", "outcome:cleaner"),
            provenance_event_id="real:stage2:004",
        ),
    )


def _episode_need_codes(episode: DevelopmentalExperienceEpisode) -> tuple[str, ...]:
    return tuple(sorted(code for code in episode.feature_codes if code.startswith("need:")))


def _episode_context_feature_codes(episode: DevelopmentalExperienceEpisode) -> tuple[str, ...]:
    return tuple(sorted(code for code in episode.feature_codes if code.startswith("context:")))


def _estimated_effort_cost(
    config: AssociativeRecallConfig,
    depth: int,
    *,
    dormancy: float,
) -> float:
    _validate_positive_int("depth", depth)
    _validate_unit("dormancy", dormancy)
    return round(1.0 + depth * config.depth_cost_weight + dormancy * config.dormancy_cost_weight, 8)


def _validate_score_rows(name: str, rows: Sequence[tuple[int, float]]) -> None:
    _validate_non_empty_sequence(name, rows)
    depths = tuple(depth for depth, _ in rows)
    if depths != tuple(sorted(depths)):
        raise ValueError(f"{name} must be sorted by depth")
    if len(depths) != len(set(depths)):
        raise ValueError(f"{name} depths must be unique")
    for depth, value in rows:
        _validate_positive_int(name, depth)
        _validate_unit(name, value)


def _validate_non_empty_sequence(name: str, values: Sequence[object]) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")


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


def _validate_non_negative_finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be a non-negative finite number")


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


def _validate_unique_ascii_codes(name: str, values: Sequence[str]) -> None:
    for value in values:
        _validate_ascii_code(name, value)
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
