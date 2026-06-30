"""Stage 3 specialised concurrent regions and multiple-need evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class DevelopmentalRegionKind(StrEnum):
    """Specialised Stage 3 software-only region kinds."""

    TASK = "task"
    RESOURCE = "resource"
    SAFETY_PERMISSION = "safety_permission"
    CLARITY = "clarity"
    PRESERVATION = "preservation"
    CURIOSITY = "curiosity"


class CrossRegionMessageKind(StrEnum):
    """Typed cross-region communication, not executable action."""

    COMPATIBILITY_SUPPORT = "compatibility_support"
    CONFLICT_INHIBITION = "conflict_inhibition"
    PERMISSION_CONSTRAINT = "permission_constraint"
    RESOURCE_CONSTRAINT = "resource_constraint"
    PRESERVATION_CONSTRAINT = "preservation_constraint"
    STOP_SIGNAL = "stop_signal"


@dataclass(frozen=True, slots=True)
class DevelopmentalRegionConfig:
    """Finite Stage 3 regional concurrency bounds."""

    seed: int = 43
    neurons_per_region: int = 6
    maximum_simultaneous_needs: int = 5
    activation_threshold: float = 0.2
    compatibility_threshold: float = 0.15
    conflict_inhibition_threshold: float = 0.25

    def __post_init__(self) -> None:
        _validate_non_negative_int("seed", self.seed)
        _validate_positive_int("neurons_per_region", self.neurons_per_region)
        _validate_positive_int("maximum_simultaneous_needs", self.maximum_simultaneous_needs)
        _validate_unit("activation_threshold", self.activation_threshold)
        _validate_unit("compatibility_threshold", self.compatibility_threshold)
        _validate_unit("conflict_inhibition_threshold", self.conflict_inhibition_threshold)

    def snapshot(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "neurons_per_region": self.neurons_per_region,
            "maximum_simultaneous_needs": self.maximum_simultaneous_needs,
            "activation_threshold": self.activation_threshold,
            "compatibility_threshold": self.compatibility_threshold,
            "conflict_inhibition_threshold": self.conflict_inhibition_threshold,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalRegionState:
    """Region-local pool and plasticity controls."""

    region_code: str
    kind: DevelopmentalRegionKind
    local_neuron_ids: tuple[str, ...]
    plasticity: float
    activation_threshold: float
    protected_control_plane: bool = False
    has_external_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("region_code", self.region_code)
        _validate_sorted_unique_ascii_codes("local_neuron_ids", self.local_neuron_ids)
        _validate_unit("plasticity", self.plasticity)
        _validate_unit("activation_threshold", self.activation_threshold)
        if not self.local_neuron_ids:
            raise ValueError("region-local pool must not be empty")
        if (
            self.kind is DevelopmentalRegionKind.SAFETY_PERMISSION
            and not self.protected_control_plane
        ):
            raise ValueError("safety and permission region must be protected")
        if self.has_external_action_authority:
            raise ValueError("developmental regions cannot hold external action authority")

    @property
    def region_id(self) -> str:
        return _identity("developmental-region", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"region_id": self.region_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "region_code": self.region_code,
            "kind": self.kind.value,
            "local_neuron_ids": list(self.local_neuron_ids),
            "plasticity": self.plasticity,
            "activation_threshold": self.activation_threshold,
            "protected_control_plane": self.protected_control_plane,
            "has_external_action_authority": self.has_external_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ConcurrentNeedPulse:
    """One simultaneous need routed to a specialised region."""

    need_code: str
    region_code: str
    intensity: float
    compatible_need_codes: tuple[str, ...] = ()
    conflicting_need_codes: tuple[str, ...] = ()
    dormant: bool = False
    protected: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("need_code", self.need_code)
        _validate_ascii_code("region_code", self.region_code)
        _validate_unit("intensity", self.intensity)
        _validate_sorted_unique_ascii_codes("compatible_need_codes", self.compatible_need_codes)
        _validate_sorted_unique_ascii_codes("conflicting_need_codes", self.conflicting_need_codes)
        if set(self.compatible_need_codes) & set(self.conflicting_need_codes):
            raise ValueError("a need cannot be both compatible and conflicting")
        if self.protected and not self.conflicting_need_codes:
            raise ValueError("protected needs must declare the conflict they can inhibit")

    @property
    def need_id(self) -> str:
        return _identity("concurrent-need-pulse", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"need_id": self.need_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "need_code": self.need_code,
            "region_code": self.region_code,
            "intensity": self.intensity,
            "compatible_need_codes": list(self.compatible_need_codes),
            "conflicting_need_codes": list(self.conflicting_need_codes),
            "dormant": self.dormant,
            "protected": self.protected,
        }


@dataclass(frozen=True, slots=True)
class CrossRegionMessage:
    """Inspectable message between specialised regions."""

    message_code: str
    kind: CrossRegionMessageKind
    source_region_code: str
    target_region_code: str
    source_need_code: str
    target_need_code: str
    strength: float
    provenance_need_codes: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("message_code", self.message_code),
            ("source_region_code", self.source_region_code),
            ("target_region_code", self.target_region_code),
            ("source_need_code", self.source_need_code),
            ("target_need_code", self.target_need_code),
        ):
            _validate_ascii_code(name, value)
        if self.source_region_code == self.target_region_code:
            raise ValueError("cross-region messages require distinct regions")
        _validate_unit("strength", self.strength)
        _validate_sorted_unique_ascii_codes("provenance_need_codes", self.provenance_need_codes)
        if not {self.source_need_code, self.target_need_code}.issubset(
            set(self.provenance_need_codes)
        ):
            raise ValueError("message provenance must include source and target needs")

    @property
    def message_id(self) -> str:
        return _identity("cross-region-message", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"message_id": self.message_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "message_code": self.message_code,
            "kind": self.kind.value,
            "source_region_code": self.source_region_code,
            "target_region_code": self.target_region_code,
            "source_need_code": self.source_need_code,
            "target_need_code": self.target_need_code,
            "strength": self.strength,
            "provenance_need_codes": list(self.provenance_need_codes),
        }


@dataclass(frozen=True, slots=True)
class RegionalProposal:
    """Typed internal proposal formed locally by a region."""

    proposal_code: str
    region_code: str
    need_code: str
    activation: float
    supported_by_need_codes: tuple[str, ...] = ()
    inhibited_by_need_codes: tuple[str, ...] = ()
    protected_requirement_codes: tuple[str, ...] = ()
    typed_internal_only: bool = True
    has_external_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("proposal_code", self.proposal_code)
        _validate_ascii_code("region_code", self.region_code)
        _validate_ascii_code("need_code", self.need_code)
        _validate_unit("activation", self.activation)
        _validate_sorted_unique_ascii_codes("supported_by_need_codes", self.supported_by_need_codes)
        _validate_sorted_unique_ascii_codes("inhibited_by_need_codes", self.inhibited_by_need_codes)
        _validate_sorted_unique_ascii_codes(
            "protected_requirement_codes", self.protected_requirement_codes
        )
        if not self.typed_internal_only:
            raise ValueError("Stage 3 regional proposals must remain typed internal proposals")
        if self.has_external_action_authority:
            raise ValueError("regional proposals cannot hold external action authority")

    @property
    def proposal_id(self) -> str:
        return _identity("regional-proposal", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"proposal_id": self.proposal_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "proposal_code": self.proposal_code,
            "region_code": self.region_code,
            "need_code": self.need_code,
            "activation": self.activation,
            "supported_by_need_codes": list(self.supported_by_need_codes),
            "inhibited_by_need_codes": list(self.inhibited_by_need_codes),
            "protected_requirement_codes": list(self.protected_requirement_codes),
            "typed_internal_only": self.typed_internal_only,
            "has_external_action_authority": self.has_external_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ConcurrentNeedActivationResult:
    """One deterministic Stage 3 concurrent-need scenario result."""

    scenario_code: str
    region_states: tuple[DevelopmentalRegionState, ...]
    need_pulses: tuple[ConcurrentNeedPulse, ...]
    messages: tuple[CrossRegionMessage, ...]
    proposals: tuple[RegionalProposal, ...]
    represented_need_codes: tuple[str, ...]
    active_proposal_codes: tuple[str, ...]
    dormant_need_codes: tuple[str, ...] = ()
    reemerged_need_codes: tuple[str, ...] = ()
    region_local_interference: float = 0.0
    uniform_network_interference: float = 0.0
    permanent_global_scalar_used: bool = False
    sqlite_cognition_operation_count: int = 0
    external_side_effect_count: int = 0
    production_action_authority_violations: int = 0

    def __post_init__(self) -> None:
        _validate_ascii_code("scenario_code", self.scenario_code)
        _validate_non_empty_sequence("region_states", self.region_states)
        _validate_non_empty_sequence("need_pulses", self.need_pulses)
        _validate_non_empty_sequence("proposals", self.proposals)
        _validate_sorted_unique_ascii_codes("represented_need_codes", self.represented_need_codes)
        _validate_sorted_unique_ascii_codes("active_proposal_codes", self.active_proposal_codes)
        _validate_sorted_unique_ascii_codes("dormant_need_codes", self.dormant_need_codes)
        _validate_sorted_unique_ascii_codes("reemerged_need_codes", self.reemerged_need_codes)
        region_codes = tuple(region.region_code for region in self.region_states)
        if len(region_codes) != len(set(region_codes)):
            raise ValueError("region codes must be unique")
        region_code_set = set(region_codes)
        need_codes = tuple(need.need_code for need in self.need_pulses)
        if len(need_codes) != len(set(need_codes)):
            raise ValueError("need codes must be unique")
        need_code_set = set(need_codes)
        proposal_codes = tuple(proposal.proposal_code for proposal in self.proposals)
        if proposal_codes != tuple(sorted(proposal_codes)):
            raise ValueError("regional proposals must be sorted by proposal code")
        if len(proposal_codes) != len(set(proposal_codes)):
            raise ValueError("regional proposal codes must be unique")
        for need in self.need_pulses:
            if need.region_code not in region_code_set:
                raise ValueError("need pulse must reference a known region")
        for message in self.messages:
            if message.source_region_code not in region_code_set:
                raise ValueError("message source region must be known")
            if message.target_region_code not in region_code_set:
                raise ValueError("message target region must be known")
            if message.source_need_code not in need_code_set:
                raise ValueError("message source need must be known")
            if message.target_need_code not in need_code_set:
                raise ValueError("message target need must be known")
        for proposal in self.proposals:
            if proposal.region_code not in region_code_set:
                raise ValueError("proposal region must be known")
            if proposal.need_code not in need_code_set:
                raise ValueError("proposal need must be known")
        if not set(self.represented_need_codes).issubset(need_code_set):
            raise ValueError("represented needs must come from active need pulses")
        if not set(self.active_proposal_codes).issubset(set(proposal_codes)):
            raise ValueError("active proposals must reference known proposals")
        _validate_unit("region_local_interference", self.region_local_interference)
        _validate_unit("uniform_network_interference", self.uniform_network_interference)
        if self.permanent_global_scalar_used:
            raise ValueError("Stage 3 cannot use a permanent global scalar collapse")
        _validate_zero_int(
            "sqlite_cognition_operation_count", self.sqlite_cognition_operation_count
        )
        _validate_zero_int("external_side_effect_count", self.external_side_effect_count)
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )

    @property
    def result_id(self) -> str:
        return _identity("concurrent-need-activation-result", self._identity_payload())

    def proposal_by_code(self, proposal_code: str) -> RegionalProposal:
        matches = tuple(
            proposal for proposal in self.proposals if proposal.proposal_code == proposal_code
        )
        if len(matches) != 1:
            raise ValueError("proposal_code must match exactly one proposal")
        return matches[0]

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "scenario_code": self.scenario_code,
            "region_states": [region.snapshot() for region in self.region_states],
            "need_pulses": [need.snapshot() for need in self.need_pulses],
            "messages": [message.snapshot() for message in self.messages],
            "proposals": [proposal.snapshot() for proposal in self.proposals],
            "represented_need_codes": list(self.represented_need_codes),
            "active_proposal_codes": list(self.active_proposal_codes),
            "dormant_need_codes": list(self.dormant_need_codes),
            "reemerged_need_codes": list(self.reemerged_need_codes),
            "region_local_interference": self.region_local_interference,
            "uniform_network_interference": self.uniform_network_interference,
            "permanent_global_scalar_used": self.permanent_global_scalar_used,
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
            "external_side_effect_count": self.external_side_effect_count,
            "production_action_authority_violations": (self.production_action_authority_violations),
        }


@dataclass(frozen=True, slots=True)
class StageThreeRegionalConcurrencyEvidence:
    """Integrated Stage 3 regional concurrency acceptance evidence."""

    config: DevelopmentalRegionConfig
    compatible_result: ConcurrentNeedActivationResult
    protected_inhibition_result: ConcurrentNeedActivationResult
    dormant_reemergence_result: ConcurrentNeedActivationResult

    def __post_init__(self) -> None:
        for result in (
            self.compatible_result,
            self.protected_inhibition_result,
            self.dormant_reemergence_result,
        ):
            if len(result.need_pulses) > self.config.maximum_simultaneous_needs:
                raise ValueError("scenario exceeds maximum simultaneous need bound")
            if any(
                len(region.local_neuron_ids) != self.config.neurons_per_region
                for region in result.region_states
            ):
                raise ValueError("region local pool size must match configured bound")
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage 3 pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-three-regional-concurrency-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        compatible_messages = {message.kind for message in self.compatible_result.messages}
        protected_messages = {message.kind for message in self.protected_inhibition_result.messages}
        safe_proposal = self.protected_inhibition_result.proposal_by_code(
            "proposal:read_only_diagnosis"
        )
        risky_proposal = self.protected_inhibition_result.proposal_by_code(
            "proposal:direct_destructive_fix"
        )
        region_kinds = (
            {region.kind for region in self.compatible_result.region_states}
            | {region.kind for region in self.protected_inhibition_result.region_states}
            | {region.kind for region in self.dormant_reemergence_result.region_states}
        )
        all_results = (
            self.compatible_result,
            self.protected_inhibition_result,
            self.dormant_reemergence_result,
        )
        return {
            "independent_compatible_needs_remain_simultaneous": (
                {"need:complete_task", "need:conserve_resources"}.issubset(
                    set(self.compatible_result.represented_need_codes)
                )
                and len(self.compatible_result.active_proposal_codes) >= 2
            ),
            "compatible_regions_cooperate_without_erasure": (
                CrossRegionMessageKind.COMPATIBILITY_SUPPORT in compatible_messages
                and self.compatible_result.region_local_interference
                < self.compatible_result.uniform_network_interference
            ),
            "protected_need_inhibits_incompatible_task": (
                CrossRegionMessageKind.PERMISSION_CONSTRAINT in protected_messages
                and CrossRegionMessageKind.CONFLICT_INHIBITION in protected_messages
                and "proposal:direct_destructive_fix"
                not in self.protected_inhibition_result.active_proposal_codes
                and "need:preserve_user_data" in risky_proposal.inhibited_by_need_codes
                and "authority:human_permission_required"
                in risky_proposal.protected_requirement_codes
                and safe_proposal.activation > risky_proposal.activation
            ),
            "dormant_need_reemerges_after_blocking_need_resolves": (
                "need:curiosity_followup" in self.dormant_reemergence_result.dormant_need_codes
                and "need:curiosity_followup"
                in self.dormant_reemergence_result.reemerged_need_codes
                and "proposal:inspect_after_stop_resolved"
                in self.dormant_reemergence_result.active_proposal_codes
            ),
            "region_local_learning_reduces_interference": all(
                result.region_local_interference < result.uniform_network_interference
                for result in all_results
            ),
            "cross_region_messages_are_typed_and_inspectable": (
                all(result.messages for result in all_results)
                and all(message.message_id for result in all_results for message in result.messages)
                and len(region_kinds) >= 5
            ),
            "no_region_gains_external_action_authority": all(
                not region.has_external_action_authority
                for result in all_results
                for region in result.region_states
            )
            and all(
                not proposal.has_external_action_authority
                for result in all_results
                for proposal in result.proposals
            )
            and all(
                result.sqlite_cognition_operation_count == 0
                and result.external_side_effect_count == 0
                and result.production_action_authority_violations == 0
                for result in all_results
            ),
            "no_permanent_global_scalar_collapse": all(
                not result.permanent_global_scalar_used for result in all_results
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
            "compatible_result": self.compatible_result.snapshot(),
            "protected_inhibition_result": self.protected_inhibition_result.snapshot(),
            "dormant_reemergence_result": self.dormant_reemergence_result.snapshot(),
        }


def run_stage_three_regional_concurrency_acceptance(
    config: DevelopmentalRegionConfig | None = None,
) -> StageThreeRegionalConcurrencyEvidence:
    """Build deterministic integrated Stage 3 regional concurrency evidence."""

    resolved = DevelopmentalRegionConfig() if config is None else config
    regions = build_stage_three_region_states(resolved)
    return StageThreeRegionalConcurrencyEvidence(
        config=resolved,
        compatible_result=_compatible_task_resource_result(regions),
        protected_inhibition_result=_protected_preservation_result(regions),
        dormant_reemergence_result=_dormant_curiosity_reemergence_result(regions),
    )


def build_stage_three_region_states(
    config: DevelopmentalRegionConfig | None = None,
) -> tuple[DevelopmentalRegionState, ...]:
    """Create deterministic region-local pools without global scalar collapse."""

    resolved = DevelopmentalRegionConfig() if config is None else config
    region_specs = (
        ("region:task", DevelopmentalRegionKind.TASK, 0.48, False),
        ("region:resource", DevelopmentalRegionKind.RESOURCE, 0.36, False),
        ("region:safety_permission", DevelopmentalRegionKind.SAFETY_PERMISSION, 0.22, True),
        ("region:clarity", DevelopmentalRegionKind.CLARITY, 0.4, False),
        ("region:preservation", DevelopmentalRegionKind.PRESERVATION, 0.28, False),
        ("region:curiosity", DevelopmentalRegionKind.CURIOSITY, 0.52, False),
    )
    return tuple(
        DevelopmentalRegionState(
            region_code=region_code,
            kind=kind,
            local_neuron_ids=tuple(
                f"v0_2:{region_code.split(':')[1]}:neuron:{index:03d}"
                for index in range(resolved.neurons_per_region)
            ),
            plasticity=plasticity,
            activation_threshold=resolved.activation_threshold,
            protected_control_plane=protected,
        )
        for region_code, kind, plasticity, protected in region_specs
    )


def _compatible_task_resource_result(
    regions: tuple[DevelopmentalRegionState, ...],
) -> ConcurrentNeedActivationResult:
    needs = (
        ConcurrentNeedPulse(
            "need:complete_task",
            "region:task",
            0.78,
            compatible_need_codes=("need:clarify_request", "need:conserve_resources"),
        ),
        ConcurrentNeedPulse(
            "need:conserve_resources",
            "region:resource",
            0.52,
            compatible_need_codes=("need:complete_task",),
        ),
        ConcurrentNeedPulse(
            "need:clarify_request",
            "region:clarity",
            0.44,
            compatible_need_codes=("need:complete_task",),
        ),
    )
    messages = (
        CrossRegionMessage(
            "message:resource_bounds_task",
            CrossRegionMessageKind.RESOURCE_CONSTRAINT,
            "region:resource",
            "region:task",
            "need:conserve_resources",
            "need:complete_task",
            0.34,
            ("need:complete_task", "need:conserve_resources"),
        ),
        CrossRegionMessage(
            "message:clarity_supports_task",
            CrossRegionMessageKind.COMPATIBILITY_SUPPORT,
            "region:clarity",
            "region:task",
            "need:clarify_request",
            "need:complete_task",
            0.27,
            ("need:clarify_request", "need:complete_task"),
        ),
    )
    proposals = (
        RegionalProposal(
            "proposal:ask_clarifying_question",
            "region:clarity",
            "need:clarify_request",
            0.43,
            supported_by_need_codes=("need:complete_task",),
        ),
        RegionalProposal(
            "proposal:bounded_task_plan",
            "region:task",
            "need:complete_task",
            0.71,
            supported_by_need_codes=("need:clarify_request", "need:conserve_resources"),
        ),
        RegionalProposal(
            "proposal:reuse_low_cost_path",
            "region:resource",
            "need:conserve_resources",
            0.49,
            supported_by_need_codes=("need:complete_task",),
        ),
    )
    return ConcurrentNeedActivationResult(
        scenario_code="scenario:task_resource_clarity",
        region_states=regions,
        need_pulses=needs,
        messages=messages,
        proposals=tuple(sorted(proposals, key=lambda proposal: proposal.proposal_code)),
        represented_need_codes=(
            "need:clarify_request",
            "need:complete_task",
            "need:conserve_resources",
        ),
        active_proposal_codes=(
            "proposal:ask_clarifying_question",
            "proposal:bounded_task_plan",
            "proposal:reuse_low_cost_path",
        ),
        region_local_interference=0.18,
        uniform_network_interference=0.46,
    )


def _protected_preservation_result(
    regions: tuple[DevelopmentalRegionState, ...],
) -> ConcurrentNeedActivationResult:
    needs = (
        ConcurrentNeedPulse(
            "need:repair_code",
            "region:task",
            0.82,
            conflicting_need_codes=("need:preserve_user_data",),
        ),
        ConcurrentNeedPulse(
            "need:preserve_user_data",
            "region:preservation",
            0.9,
            conflicting_need_codes=("need:repair_code",),
            protected=True,
        ),
        ConcurrentNeedPulse(
            "need:permission_check",
            "region:safety_permission",
            0.86,
            conflicting_need_codes=("need:repair_code",),
            protected=True,
        ),
    )
    messages = (
        CrossRegionMessage(
            "message:permission_blocks_destructive_fix",
            CrossRegionMessageKind.PERMISSION_CONSTRAINT,
            "region:safety_permission",
            "region:task",
            "need:permission_check",
            "need:repair_code",
            0.78,
            ("need:permission_check", "need:repair_code"),
        ),
        CrossRegionMessage(
            "message:preservation_inhibits_destructive_fix",
            CrossRegionMessageKind.CONFLICT_INHIBITION,
            "region:preservation",
            "region:task",
            "need:preserve_user_data",
            "need:repair_code",
            0.81,
            ("need:preserve_user_data", "need:repair_code"),
        ),
        CrossRegionMessage(
            "message:preservation_constraint",
            CrossRegionMessageKind.PRESERVATION_CONSTRAINT,
            "region:preservation",
            "region:task",
            "need:preserve_user_data",
            "need:repair_code",
            0.72,
            ("need:preserve_user_data", "need:repair_code"),
        ),
    )
    proposals = (
        RegionalProposal(
            "proposal:direct_destructive_fix",
            "region:task",
            "need:repair_code",
            0.21,
            inhibited_by_need_codes=("need:permission_check", "need:preserve_user_data"),
            protected_requirement_codes=("authority:human_permission_required",),
        ),
        RegionalProposal(
            "proposal:read_only_diagnosis",
            "region:task",
            "need:repair_code",
            0.68,
            supported_by_need_codes=("need:permission_check", "need:preserve_user_data"),
            protected_requirement_codes=("authority:read_only_allowed",),
        ),
        RegionalProposal(
            "proposal:request_permission",
            "region:safety_permission",
            "need:permission_check",
            0.74,
            supported_by_need_codes=("need:preserve_user_data",),
        ),
    )
    return ConcurrentNeedActivationResult(
        scenario_code="scenario:repair_permission_preservation",
        region_states=regions,
        need_pulses=needs,
        messages=messages,
        proposals=tuple(sorted(proposals, key=lambda proposal: proposal.proposal_code)),
        represented_need_codes=(
            "need:permission_check",
            "need:preserve_user_data",
            "need:repair_code",
        ),
        active_proposal_codes=("proposal:read_only_diagnosis", "proposal:request_permission"),
        region_local_interference=0.16,
        uniform_network_interference=0.58,
    )


def _dormant_curiosity_reemergence_result(
    regions: tuple[DevelopmentalRegionState, ...],
) -> ConcurrentNeedActivationResult:
    needs = (
        ConcurrentNeedPulse(
            "need:obey_stop",
            "region:safety_permission",
            0.95,
            conflicting_need_codes=("need:curiosity_followup",),
            protected=True,
        ),
        ConcurrentNeedPulse(
            "need:curiosity_followup",
            "region:curiosity",
            0.31,
            conflicting_need_codes=("need:obey_stop",),
            dormant=True,
        ),
    )
    messages = (
        CrossRegionMessage(
            "message:stop_pauses_curiosity",
            CrossRegionMessageKind.STOP_SIGNAL,
            "region:safety_permission",
            "region:curiosity",
            "need:obey_stop",
            "need:curiosity_followup",
            0.92,
            ("need:curiosity_followup", "need:obey_stop"),
        ),
        CrossRegionMessage(
            "message:curiosity_reemerges_after_stop",
            CrossRegionMessageKind.COMPATIBILITY_SUPPORT,
            "region:safety_permission",
            "region:curiosity",
            "need:obey_stop",
            "need:curiosity_followup",
            0.33,
            ("need:curiosity_followup", "need:obey_stop"),
        ),
    )
    proposals = (
        RegionalProposal(
            "proposal:inspect_after_stop_resolved",
            "region:curiosity",
            "need:curiosity_followup",
            0.42,
            supported_by_need_codes=("need:obey_stop",),
            protected_requirement_codes=("authority:stop_resolved",),
        ),
        RegionalProposal(
            "proposal:pause_for_stop",
            "region:safety_permission",
            "need:obey_stop",
            0.93,
            inhibited_by_need_codes=("need:curiosity_followup",),
        ),
    )
    return ConcurrentNeedActivationResult(
        scenario_code="scenario:stop_then_curiosity_reemerges",
        region_states=regions,
        need_pulses=needs,
        messages=messages,
        proposals=tuple(sorted(proposals, key=lambda proposal: proposal.proposal_code)),
        represented_need_codes=("need:curiosity_followup", "need:obey_stop"),
        active_proposal_codes=("proposal:inspect_after_stop_resolved", "proposal:pause_for_stop"),
        dormant_need_codes=("need:curiosity_followup",),
        reemerged_need_codes=("need:curiosity_followup",),
        region_local_interference=0.14,
        uniform_network_interference=0.51,
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
