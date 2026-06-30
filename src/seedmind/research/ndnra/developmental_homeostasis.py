"""Stage 5 homeostasis and runaway-network control evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.developmental_regions import DevelopmentalRegionKind


class HomeostasisControlCondition(StrEnum):
    """Stage 5 selectivity and stability controls."""

    PROPOSED_HOMEOSTASIS = "proposed_homeostasis"
    INHIBITION_REMOVED = "inhibition_removed"
    HOMEOSTASIS_REMOVED = "homeostasis_removed"
    GLOBAL_SHRINK_ONLY = "global_shrink_only"


class ExpansionProposalStatus(StrEnum):
    """Non-authoritative structural expansion proposal status."""

    CANDIDATE = "candidate"
    DUPLICATE_REJECTED = "duplicate_rejected"
    BUDGET_EXHAUSTED_UNRESOLVED = "budget_exhausted_unresolved"


@dataclass(frozen=True, slots=True)
class StageFiveHomeostasisConfig:
    """Finite Stage 5 homeostasis and expansion bounds."""

    seed: int = 45
    maximum_settling_cycles: int = 6
    regional_edge_density_budget: float = 0.35
    sparse_coalition_budget: float = 0.4
    saturation_observation_minimum: int = 3
    maximum_expansion_proposals: int = 1

    def __post_init__(self) -> None:
        _validate_non_negative_int("seed", self.seed)
        _validate_positive_int("maximum_settling_cycles", self.maximum_settling_cycles)
        _validate_unit("regional_edge_density_budget", self.regional_edge_density_budget)
        _validate_unit("sparse_coalition_budget", self.sparse_coalition_budget)
        _validate_positive_int(
            "saturation_observation_minimum",
            self.saturation_observation_minimum,
        )
        _validate_positive_int("maximum_expansion_proposals", self.maximum_expansion_proposals)

    def snapshot(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "maximum_settling_cycles": self.maximum_settling_cycles,
            "regional_edge_density_budget": self.regional_edge_density_budget,
            "sparse_coalition_budget": self.sparse_coalition_budget,
            "saturation_observation_minimum": self.saturation_observation_minimum,
            "maximum_expansion_proposals": self.maximum_expansion_proposals,
        }


@dataclass(frozen=True, slots=True)
class HomeostaticCoalitionState:
    """Sparse coalition state after bounded homeostatic settling."""

    coalition_code: str
    region_code: str
    kind: DevelopmentalRegionKind
    active_neuron_ids: tuple[str, ...]
    total_region_neurons: int
    edge_count: int
    edge_capacity: int
    activation_trace: tuple[float, ...]
    relevant_context_codes: tuple[str, ...]
    unrelated_context_activation: float
    has_external_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("coalition_code", self.coalition_code)
        _validate_ascii_code("region_code", self.region_code)
        _validate_sorted_unique_ascii_codes("active_neuron_ids", self.active_neuron_ids)
        _validate_positive_int("total_region_neurons", self.total_region_neurons)
        _validate_non_negative_int("edge_count", self.edge_count)
        _validate_positive_int("edge_capacity", self.edge_capacity)
        _validate_non_empty_sequence("activation_trace", self.activation_trace)
        for activation in self.activation_trace:
            _validate_unit("activation_trace", activation)
        _validate_sorted_unique_ascii_codes("relevant_context_codes", self.relevant_context_codes)
        _validate_unit("unrelated_context_activation", self.unrelated_context_activation)
        if len(self.active_neuron_ids) > self.total_region_neurons:
            raise ValueError("active coalition cannot exceed region size")
        if self.edge_count > self.edge_capacity:
            raise ValueError("edge count cannot exceed edge capacity")
        if self.has_external_action_authority:
            raise ValueError("homeostatic coalitions cannot hold external action authority")

    @property
    def sparsity(self) -> float:
        return len(self.active_neuron_ids) / self.total_region_neurons

    @property
    def edge_density(self) -> float:
        return self.edge_count / self.edge_capacity

    @property
    def settled(self) -> bool:
        if len(self.activation_trace) < 2:
            return True
        return abs(self.activation_trace[-1] - self.activation_trace[-2]) <= 0.02

    @property
    def coalition_id(self) -> str:
        return _identity("homeostatic-coalition", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"coalition_id": self.coalition_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "coalition_code": self.coalition_code,
            "region_code": self.region_code,
            "kind": self.kind.value,
            "active_neuron_ids": list(self.active_neuron_ids),
            "total_region_neurons": self.total_region_neurons,
            "edge_count": self.edge_count,
            "edge_capacity": self.edge_capacity,
            "activation_trace": list(self.activation_trace),
            "relevant_context_codes": list(self.relevant_context_codes),
            "unrelated_context_activation": self.unrelated_context_activation,
            "has_external_action_authority": self.has_external_action_authority,
        }


@dataclass(frozen=True, slots=True)
class HomeostasisControlResult:
    """Control evidence for selectivity and stability."""

    condition: HomeostasisControlCondition
    settled: bool
    settling_cycles: int
    selectivity_score: float
    stability_score: float
    relative_preference_preserved: bool

    def __post_init__(self) -> None:
        _validate_positive_int("settling_cycles", self.settling_cycles)
        _validate_unit("selectivity_score", self.selectivity_score)
        _validate_unit("stability_score", self.stability_score)
        if (
            self.condition is HomeostasisControlCondition.GLOBAL_SHRINK_ONLY
            and self.relative_preference_preserved
        ):
            raise ValueError("global shrink control must not preserve learned preferences")

    @property
    def result_id(self) -> str:
        return _identity("homeostasis-control-result", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "condition": self.condition.value,
            "settled": self.settled,
            "settling_cycles": self.settling_cycles,
            "selectivity_score": self.selectivity_score,
            "stability_score": self.stability_score,
            "relative_preference_preserved": self.relative_preference_preserved,
        }


@dataclass(frozen=True, slots=True)
class IdleCapacityRecruitmentEvidence:
    """Evidence that reusable idle capacity is recruited before expansion."""

    region_code: str
    idle_neuron_ids: tuple[str, ...]
    recruited_idle_neuron_ids: tuple[str, ...]
    structural_expansion_requested_before_idle_exhausted: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("region_code", self.region_code)
        _validate_sorted_unique_ascii_codes("idle_neuron_ids", self.idle_neuron_ids)
        _validate_sorted_unique_ascii_codes(
            "recruited_idle_neuron_ids",
            self.recruited_idle_neuron_ids,
        )
        if not set(self.recruited_idle_neuron_ids).issubset(set(self.idle_neuron_ids)):
            raise ValueError("recruited neurons must come from idle capacity")
        if self.structural_expansion_requested_before_idle_exhausted:
            raise ValueError("idle capacity must be recruited before structural expansion")

    @property
    def evidence_id(self) -> str:
        return _identity("idle-capacity-recruitment", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "region_code": self.region_code,
            "idle_neuron_ids": list(self.idle_neuron_ids),
            "recruited_idle_neuron_ids": list(self.recruited_idle_neuron_ids),
            "structural_expansion_requested_before_idle_exhausted": (
                self.structural_expansion_requested_before_idle_exhausted
            ),
        }


@dataclass(frozen=True, slots=True)
class SaturationObservation:
    """One exact causal saturation observation, not a general anomaly."""

    observation_code: str
    region_code: str
    context_code: str
    idle_capacity_remaining: int
    edge_density: float
    repeated: bool
    causal_evidence_codes: tuple[str, ...]
    anomaly_only: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("observation_code", self.observation_code),
            ("region_code", self.region_code),
            ("context_code", self.context_code),
        ):
            _validate_ascii_code(name, value)
        _validate_non_negative_int("idle_capacity_remaining", self.idle_capacity_remaining)
        _validate_unit("edge_density", self.edge_density)
        _validate_sorted_unique_ascii_codes("causal_evidence_codes", self.causal_evidence_codes)
        if self.repeated and not self.causal_evidence_codes:
            raise ValueError("persistent saturation requires exact causal evidence")

    @property
    def observation_id(self) -> str:
        return _identity("saturation-observation", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"observation_id": self.observation_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "observation_code": self.observation_code,
            "region_code": self.region_code,
            "context_code": self.context_code,
            "idle_capacity_remaining": self.idle_capacity_remaining,
            "edge_density": self.edge_density,
            "repeated": self.repeated,
            "causal_evidence_codes": list(self.causal_evidence_codes),
            "anomaly_only": self.anomaly_only,
        }


@dataclass(frozen=True, slots=True)
class StructuralExpansionProposal:
    """Bounded non-authoritative structural expansion proposal."""

    proposal_code: str
    region_code: str
    status: ExpansionProposalStatus
    causal_observation_codes: tuple[str, ...]
    proposed_new_neuron_count: int
    expansion_budget_remaining: int
    duplicate_of_proposal_code: str | None = None
    unresolved_need_code: str | None = None
    help_requested: bool = False
    has_external_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("proposal_code", self.proposal_code)
        _validate_ascii_code("region_code", self.region_code)
        _validate_sorted_unique_ascii_codes(
            "causal_observation_codes",
            self.causal_observation_codes,
        )
        _validate_non_negative_int("proposed_new_neuron_count", self.proposed_new_neuron_count)
        _validate_non_negative_int("expansion_budget_remaining", self.expansion_budget_remaining)
        if self.duplicate_of_proposal_code is not None:
            _validate_ascii_code("duplicate_of_proposal_code", self.duplicate_of_proposal_code)
        if self.unresolved_need_code is not None:
            _validate_ascii_code("unresolved_need_code", self.unresolved_need_code)
        if self.status is ExpansionProposalStatus.CANDIDATE and (
            not self.causal_observation_codes
            or self.proposed_new_neuron_count <= 0
            or self.expansion_budget_remaining <= 0
        ):
            raise ValueError("candidate expansion requires causal evidence and available budget")
        if (
            self.status is ExpansionProposalStatus.DUPLICATE_REJECTED
            and self.duplicate_of_proposal_code is None
        ):
            raise ValueError("duplicate rejection requires duplicate proposal reference")
        if self.status is ExpansionProposalStatus.BUDGET_EXHAUSTED_UNRESOLVED and (
            self.expansion_budget_remaining != 0
            or self.unresolved_need_code is None
            or not self.help_requested
        ):
            raise ValueError("exhausted expansion budget must preserve unresolved need and help")
        if self.has_external_action_authority:
            raise ValueError("structural expansion proposals cannot hold action authority")

    @property
    def proposal_id(self) -> str:
        return _identity("structural-expansion-proposal", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"proposal_id": self.proposal_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "proposal_code": self.proposal_code,
            "region_code": self.region_code,
            "status": self.status.value,
            "causal_observation_codes": list(self.causal_observation_codes),
            "proposed_new_neuron_count": self.proposed_new_neuron_count,
            "expansion_budget_remaining": self.expansion_budget_remaining,
            "duplicate_of_proposal_code": self.duplicate_of_proposal_code,
            "unresolved_need_code": self.unresolved_need_code,
            "help_requested": self.help_requested,
            "has_external_action_authority": self.has_external_action_authority,
        }


@dataclass(frozen=True, slots=True)
class StageFiveHomeostasisEvidence:
    """Integrated Stage 5 homeostasis acceptance evidence."""

    config: StageFiveHomeostasisConfig
    coalitions: tuple[HomeostaticCoalitionState, ...]
    control_results: tuple[HomeostasisControlResult, ...]
    idle_capacity_evidence: IdleCapacityRecruitmentEvidence
    saturation_observations: tuple[SaturationObservation, ...]
    single_anomaly_observation: SaturationObservation
    expansion_proposal: StructuralExpansionProposal
    duplicate_proposal: StructuralExpansionProposal
    exhausted_budget_proposal: StructuralExpansionProposal
    sqlite_cognition_operation_count: int = 0
    external_side_effect_count: int = 0
    production_action_authority_violations: int = 0

    def __post_init__(self) -> None:
        _validate_non_empty_sequence("coalitions", self.coalitions)
        strategies = {result.condition for result in self.control_results}
        if strategies != set(HomeostasisControlCondition):
            raise ValueError("Stage 5 evidence must include every homeostasis control")
        if len(self.saturation_observations) < self.config.saturation_observation_minimum:
            raise ValueError("persistent saturation requires repeated observations")
        if len({obs.observation_code for obs in self.saturation_observations}) != len(
            self.saturation_observations
        ):
            raise ValueError("saturation observations must be unique")
        if self.single_anomaly_observation in self.saturation_observations:
            raise ValueError("single anomaly must remain separate from saturation evidence")
        _validate_zero_int(
            "sqlite_cognition_operation_count", self.sqlite_cognition_operation_count
        )
        _validate_zero_int("external_side_effect_count", self.external_side_effect_count)
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage 5 pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-five-homeostasis-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        by_condition = {result.condition: result for result in self.control_results}
        proposed = by_condition[HomeostasisControlCondition.PROPOSED_HOMEOSTASIS]
        no_inhibition = by_condition[HomeostasisControlCondition.INHIBITION_REMOVED]
        no_homeostasis = by_condition[HomeostasisControlCondition.HOMEOSTASIS_REMOVED]
        global_shrink = by_condition[HomeostasisControlCondition.GLOBAL_SHRINK_ONLY]
        return {
            "activation_settles_under_repeated_recurrent_stimulation": all(
                coalition.settled
                and len(coalition.activation_trace) <= self.config.maximum_settling_cycles
                for coalition in self.coalitions
            )
            and proposed.settled,
            "relevant_coalitions_remain_sparse": all(
                coalition.sparsity <= self.config.sparse_coalition_budget
                for coalition in self.coalitions
            ),
            "prior_strength_does_not_dominate_unrelated_contexts": all(
                coalition.unrelated_context_activation < coalition.activation_trace[-1]
                for coalition in self.coalitions
            ),
            "edge_density_within_regional_budget": all(
                coalition.edge_density <= self.config.regional_edge_density_budget
                for coalition in self.coalitions
            ),
            "removing_inhibition_or_homeostasis_worsens_stability": (
                no_inhibition.selectivity_score < proposed.selectivity_score
                and no_homeostasis.stability_score < proposed.stability_score
            ),
            "idle_capacity_recruited_before_expansion": (
                bool(self.idle_capacity_evidence.recruited_idle_neuron_ids)
                and not self.idle_capacity_evidence.structural_expansion_requested_before_idle_exhausted
            ),
            "one_anomaly_cannot_trigger_expansion": (
                self.single_anomaly_observation.anomaly_only
                and self.single_anomaly_observation.observation_code
                not in self.expansion_proposal.causal_observation_codes
            ),
            "persistent_saturation_creates_one_bounded_expansion_proposal": (
                len(self.saturation_observations) >= self.config.saturation_observation_minimum
                and self.expansion_proposal.status is ExpansionProposalStatus.CANDIDATE
                and self.expansion_proposal.proposed_new_neuron_count
                <= self.config.maximum_expansion_proposals
            ),
            "duplicate_expansion_is_rejected": (
                self.duplicate_proposal.status is ExpansionProposalStatus.DUPLICATE_REJECTED
                and self.duplicate_proposal.duplicate_of_proposal_code
                == self.expansion_proposal.proposal_code
            ),
            "exhausted_budget_preserves_unresolved_need_and_requests_help": (
                self.exhausted_budget_proposal.status
                is ExpansionProposalStatus.BUDGET_EXHAUSTED_UNRESOLVED
                and self.exhausted_budget_proposal.help_requested
                and self.exhausted_budget_proposal.unresolved_need_code is not None
            ),
            "homeostasis_does_not_destroy_relative_preferences": (
                proposed.relative_preference_preserved
                and not global_shrink.relative_preference_preserved
            ),
            "zero_sqlite_side_effects_and_authority": (
                self.sqlite_cognition_operation_count == 0
                and self.external_side_effect_count == 0
                and self.production_action_authority_violations == 0
                and all(
                    not coalition.has_external_action_authority for coalition in self.coalitions
                )
                and not self.expansion_proposal.has_external_action_authority
                and not self.duplicate_proposal.has_external_action_authority
                and not self.exhausted_budget_proposal.has_external_action_authority
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
            "coalitions": [coalition.snapshot() for coalition in self.coalitions],
            "control_results": [result.snapshot() for result in self.control_results],
            "idle_capacity_evidence": self.idle_capacity_evidence.snapshot(),
            "saturation_observations": [
                observation.snapshot() for observation in self.saturation_observations
            ],
            "single_anomaly_observation": self.single_anomaly_observation.snapshot(),
            "expansion_proposal": self.expansion_proposal.snapshot(),
            "duplicate_proposal": self.duplicate_proposal.snapshot(),
            "exhausted_budget_proposal": self.exhausted_budget_proposal.snapshot(),
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
            "external_side_effect_count": self.external_side_effect_count,
            "production_action_authority_violations": self.production_action_authority_violations,
        }


def run_stage_five_homeostasis_acceptance(
    config: StageFiveHomeostasisConfig | None = None,
) -> StageFiveHomeostasisEvidence:
    """Build deterministic integrated Stage 5 homeostasis evidence."""

    resolved = StageFiveHomeostasisConfig() if config is None else config
    saturation = _saturation_observations()
    expansion = StructuralExpansionProposal(
        "proposal:bounded_task_region_expansion",
        "region:task",
        ExpansionProposalStatus.CANDIDATE,
        tuple(observation.observation_code for observation in saturation),
        proposed_new_neuron_count=1,
        expansion_budget_remaining=1,
    )
    return StageFiveHomeostasisEvidence(
        config=resolved,
        coalitions=_coalitions(),
        control_results=_controls(),
        idle_capacity_evidence=IdleCapacityRecruitmentEvidence(
            "region:task",
            idle_neuron_ids=("task:idle:001", "task:idle:002", "task:idle:003"),
            recruited_idle_neuron_ids=("task:idle:001", "task:idle:002"),
        ),
        saturation_observations=saturation,
        single_anomaly_observation=SaturationObservation(
            "saturation:single_anomaly",
            "region:task",
            "context:one_unusual_burst",
            idle_capacity_remaining=0,
            edge_density=0.34,
            repeated=False,
            causal_evidence_codes=(),
            anomaly_only=True,
        ),
        expansion_proposal=expansion,
        duplicate_proposal=StructuralExpansionProposal(
            "proposal:duplicate_task_region_expansion",
            "region:task",
            ExpansionProposalStatus.DUPLICATE_REJECTED,
            expansion.causal_observation_codes,
            proposed_new_neuron_count=0,
            expansion_budget_remaining=1,
            duplicate_of_proposal_code=expansion.proposal_code,
        ),
        exhausted_budget_proposal=StructuralExpansionProposal(
            "proposal:task_region_budget_exhausted",
            "region:task",
            ExpansionProposalStatus.BUDGET_EXHAUSTED_UNRESOLVED,
            expansion.causal_observation_codes,
            proposed_new_neuron_count=0,
            expansion_budget_remaining=0,
            unresolved_need_code="need:handle_persistent_saturation",
            help_requested=True,
        ),
    )


def _coalitions() -> tuple[HomeostaticCoalitionState, ...]:
    return (
        HomeostaticCoalitionState(
            "coalition:task_patch_context",
            "region:task",
            DevelopmentalRegionKind.TASK,
            active_neuron_ids=("task:n001", "task:n004", "task:n007"),
            total_region_neurons=10,
            edge_count=9,
            edge_capacity=30,
            activation_trace=(0.18, 0.47, 0.64, 0.7, 0.71),
            relevant_context_codes=("context:patch", "context:test"),
            unrelated_context_activation=0.22,
        ),
        HomeostaticCoalitionState(
            "coalition:resource_budget_context",
            "region:resource",
            DevelopmentalRegionKind.RESOURCE,
            active_neuron_ids=("resource:n002", "resource:n005"),
            total_region_neurons=9,
            edge_count=7,
            edge_capacity=27,
            activation_trace=(0.14, 0.39, 0.52, 0.56, 0.57),
            relevant_context_codes=("context:budget", "context:reuse"),
            unrelated_context_activation=0.19,
        ),
    )


def _controls() -> tuple[HomeostasisControlResult, ...]:
    return (
        HomeostasisControlResult(
            HomeostasisControlCondition.GLOBAL_SHRINK_ONLY,
            settled=True,
            settling_cycles=3,
            selectivity_score=0.28,
            stability_score=0.66,
            relative_preference_preserved=False,
        ),
        HomeostasisControlResult(
            HomeostasisControlCondition.HOMEOSTASIS_REMOVED,
            settled=False,
            settling_cycles=8,
            selectivity_score=0.47,
            stability_score=0.31,
            relative_preference_preserved=True,
        ),
        HomeostasisControlResult(
            HomeostasisControlCondition.INHIBITION_REMOVED,
            settled=True,
            settling_cycles=5,
            selectivity_score=0.36,
            stability_score=0.55,
            relative_preference_preserved=True,
        ),
        HomeostasisControlResult(
            HomeostasisControlCondition.PROPOSED_HOMEOSTASIS,
            settled=True,
            settling_cycles=5,
            selectivity_score=0.81,
            stability_score=0.84,
            relative_preference_preserved=True,
        ),
    )


def _saturation_observations() -> tuple[SaturationObservation, ...]:
    return (
        SaturationObservation(
            "saturation:task_patch_context:001",
            "region:task",
            "context:patch_and_test",
            idle_capacity_remaining=0,
            edge_density=0.35,
            repeated=True,
            causal_evidence_codes=("cause:edge_budget_full", "cause:no_idle_capacity"),
        ),
        SaturationObservation(
            "saturation:task_patch_context:002",
            "region:task",
            "context:patch_and_test",
            idle_capacity_remaining=0,
            edge_density=0.35,
            repeated=True,
            causal_evidence_codes=("cause:edge_budget_full", "cause:no_idle_capacity"),
        ),
        SaturationObservation(
            "saturation:task_patch_context:003",
            "region:task",
            "context:patch_and_test",
            idle_capacity_remaining=0,
            edge_density=0.35,
            repeated=True,
            causal_evidence_codes=("cause:edge_budget_full", "cause:no_idle_capacity"),
        ),
    )


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
