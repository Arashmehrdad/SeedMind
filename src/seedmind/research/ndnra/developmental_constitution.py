"""Stage -1 contracts for the NDNRA v0.2 developmental constitution."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite


class DevelopmentalSignalRole(StrEnum):
    """Primitive signal roles before v0.2 recurrent-network work begins."""

    OBSERVATION = "observation"
    NEED = "need"
    ACTION = "action"
    OUTCOME = "outcome"
    PREDICTION = "prediction"
    HUMAN_TEACHING = "human_teaching"
    PERMISSION = "permission"
    CORRECTION = "correction"
    RESOURCE_STATE = "resource_state"
    IMAGINATION = "imagination"


class DESARoutingDisposition(StrEnum):
    """Possible Stage -1 routing dispositions."""

    LOCAL = "local"
    REGIONAL = "regional"
    COUNCIL = "council"
    AUTHORITY = "authority"


class MetacognitiveSummaryScope(StrEnum):
    """Where a Stage -1 metacognitive summary was produced."""

    LOCAL = "local"
    REGIONAL = "regional"
    COUNCIL = "council"


class StewardGateDecision(StrEnum):
    """Measured decision for an optional intermediate skill steward."""

    ACCEPTED = "accepted"
    REJECTED = "rejected"


class EventPartitionOperation(StrEnum):
    """Operations over an immutable chronological activity stream."""

    OPEN = "open"
    CONTINUE = "continue"
    SPLIT = "split"
    NEST = "nest"
    RELATE = "relate"
    CLOSE = "close"


class ValueSourceKind(StrEnum):
    """Accepted sources for desired-state ambition."""

    NURSERY_PURPOSE = "nursery_purpose"
    TRUSTED_TEACHING = "trusted_teaching"
    MATURE_PROMPT = "mature_prompt"
    OBSERVED_PURPOSE_COMPATIBLE_OUTCOME = "observed_purpose_compatible_outcome"


class CapabilityGapSource(StrEnum):
    """Obstacle evidence that must stay separate from desired-state value."""

    OBSERVED_ABILITY = "observed_ability"
    FAILED_REQUEST = "failed_request"
    RECOGNISED_MISTAKE = "recognised_mistake"


class SkillBundleLifecycle(StrEnum):
    """Stage -1 skill-bundle maturity states."""

    INCUBATING_SKILL = "incubating_skill"
    SUPERVISED_SKILL = "supervised_skill"
    MATURE_SKILL = "mature_skill"
    REOPENED_SKILL = "reopened_skill"
    REJECTED_SKILL = "rejected_skill"


class OutcomeFidelityState(StrEnum):
    """Developmental outcome verification states."""

    CANDIDATE_OUTCOME = "candidate_outcome"
    PENDING_OUTCOME = "pending_outcome"
    UNVERIFIED_OUTCOME = "unverified_outcome"
    PARTIALLY_VERIFIED_OUTCOME = "partially_verified_outcome"
    VERIFIED_OUTCOME = "verified_outcome"
    CONTRADICTED_OUTCOME = "contradicted_outcome"
    FAILED_OUTCOME = "failed_outcome"


class OutcomeFeedbackSource(StrEnum):
    """Grounded feedback sources for developmental Outcome Fidelity."""

    ENVIRONMENT_CONSEQUENCE = "environment_consequence"
    DETERMINISTIC_TEST_RESULT = "deterministic_test_result"
    TEACHER_ACCEPTANCE = "teacher_acceptance"
    TEACHER_CORRECTION = "teacher_correction"
    TEACHER_REJECTION = "teacher_rejection"
    DELAYED_OUTCOME = "delayed_outcome"
    INDEPENDENT_VERIFIER = "independent_verifier"
    PREDICTION_RESULT_COMPARISON = "prediction_result_comparison"
    EXECUTIVE_AUDITOR_CHALLENGE = "executive_auditor_challenge"


class ProtectedAuthorityAction(StrEnum):
    """Protected human-control actions that are not ordinary reward."""

    STOP = "stop"
    DENY = "deny"
    REVOKE = "revoke"
    PAUSE = "pause"
    APPROVE = "approve"
    CORRECT = "correct"
    CLARIFY = "clarify"
    TEACH = "teach"


class IntegritySurface(StrEnum):
    """Surfaces protected by Stage -1 Deterrence and audit contracts."""

    REWARD = "reward"
    EVIDENCE = "evidence"
    FEEDBACK = "feedback"
    VERIFIER_STATE = "verifier_state"
    EVALUATION_WINDOW = "evaluation_window"
    AUDIT_HISTORY = "audit_history"


class IntegrityManipulationKind(StrEnum):
    """Manipulation attempts that must be blocked and preserved."""

    ALTER_REWARD = "alter_reward"
    HIDE_FAILURE = "hide_failure"
    DELETE_NEGATIVE_EVIDENCE = "delete_negative_evidence"
    WEAKEN_VERIFIER = "weaken_verifier"
    SHIFT_EVALUATION_WINDOW = "shift_evaluation_window"
    CORRUPT_AUDIT = "corrupt_audit"


class NurseryCurriculumKind(StrEnum):
    """The two Stage -1 developmental curricula."""

    ORDINARY = "ordinary"
    EXECUTIVE = "executive"


class CausalResponsibilityEvidenceKind(StrEnum):
    """Evidence kinds for moving beyond co-activation."""

    COACTIVATION = "coactivation"
    PREDICTION = "prediction"
    REPETITION = "repetition"
    INTERVENTION = "intervention"
    ABLATION = "ablation"
    CONTRADICTION = "contradiction"


class CausalResponsibilityStatus(StrEnum):
    """Responsibility status remains candidate without stronger evidence."""

    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass(frozen=True, slots=True)
class DevelopmentalSignalContract:
    """One primitive signal role with explicit authority and evidence boundaries."""

    role: DevelopmentalSignalRole
    signal_code: str
    protected_control_plane: bool = False
    reward_coupled: bool = False
    can_update_factual_evidence: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("signal_code", self.signal_code)
        if self.protected_control_plane and self.reward_coupled:
            raise ValueError("protected signals cannot be reward coupled")
        if self.has_production_action_authority:
            raise ValueError("developmental signals cannot control production actions")

    @property
    def signal_id(self) -> str:
        return _identity("developmental-signal", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"signal_id": self.signal_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "role": self.role.value,
            "signal_code": self.signal_code,
            "protected_control_plane": self.protected_control_plane,
            "reward_coupled": self.reward_coupled,
            "can_update_factual_evidence": self.can_update_factual_evidence,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class OptionalSkillStewardGate:
    """Measured gate for creating an optional intermediate skill steward."""

    gate_code: str
    declared_metric_code: str
    measured_benefit: float
    measured_cost: float
    minimum_net_benefit: float

    def __post_init__(self) -> None:
        _validate_ascii_code("gate_code", self.gate_code)
        _validate_ascii_code("declared_metric_code", self.declared_metric_code)
        _validate_non_negative_finite("measured_benefit", self.measured_benefit)
        _validate_non_negative_finite("measured_cost", self.measured_cost)
        _validate_non_negative_finite("minimum_net_benefit", self.minimum_net_benefit)

    @property
    def decision(self) -> StewardGateDecision:
        if (
            self.measured_benefit > self.measured_cost
            and self.measured_benefit - self.measured_cost >= self.minimum_net_benefit
        ):
            return StewardGateDecision.ACCEPTED
        return StewardGateDecision.REJECTED

    @property
    def gate_id(self) -> str:
        return _identity("optional-skill-steward-gate", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"gate_id": self.gate_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "gate_code": self.gate_code,
            "declared_metric_code": self.declared_metric_code,
            "measured_benefit": self.measured_benefit,
            "measured_cost": self.measured_cost,
            "minimum_net_benefit": self.minimum_net_benefit,
            "decision": self.decision.value,
        }


@dataclass(frozen=True, slots=True)
class DESAHierarchyContract:
    """Minimal adaptive DESA hierarchy without hidden task-solving authority."""

    skill_bundle_monitor_codes: tuple[str, ...]
    regional_captain_codes: tuple[str, ...]
    council_code: str
    executive_auditor_code: str
    constitutional_authority_code: str
    optional_steward_gate: OptionalSkillStewardGate | None
    shared_workspace_capacity: int
    routes_unfamiliar_to_multiple_regions: bool = True
    single_all_knowing_captain: bool = False
    fixed_extra_steward_layer: bool = False
    has_task_solution: bool = False
    has_pretrained_language_model: bool = False
    has_imported_task_knowledge: bool = False
    has_external_action_authority: bool = False
    uses_sqlite_cognition: bool = False

    def __post_init__(self) -> None:
        _validate_sorted_unique_ascii_codes(
            "skill_bundle_monitor_codes",
            self.skill_bundle_monitor_codes,
        )
        _validate_sorted_unique_ascii_codes("regional_captain_codes", self.regional_captain_codes)
        if len(self.regional_captain_codes) < 2:
            raise ValueError("DESA requires plural regional captains")
        _validate_ascii_code("council_code", self.council_code)
        _validate_ascii_code("executive_auditor_code", self.executive_auditor_code)
        _validate_ascii_code("constitutional_authority_code", self.constitutional_authority_code)
        _validate_positive_int("shared_workspace_capacity", self.shared_workspace_capacity)
        if not self.routes_unfamiliar_to_multiple_regions:
            raise ValueError("unfamiliar activity must route to multiple plausible regions")
        if self.single_all_knowing_captain:
            raise ValueError("DESA cannot begin as one all-knowing captain")
        if self.fixed_extra_steward_layer:
            raise ValueError("intermediate skill stewards must be optional and measured")
        if self.has_task_solution:
            raise ValueError("DESA cannot contain a task-specific solution")
        if self.has_pretrained_language_model:
            raise ValueError("DESA cannot contain a pretrained language model")
        if self.has_imported_task_knowledge:
            raise ValueError("DESA cannot contain imported task knowledge")
        if self.has_external_action_authority:
            raise ValueError("DESA cannot hold external action authority")
        if self.uses_sqlite_cognition:
            raise ValueError("Stage -1 DESA contracts cannot use SQLite cognition")

    @property
    def hierarchy_id(self) -> str:
        return _identity("desa-hierarchy", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"hierarchy_id": self.hierarchy_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "skill_bundle_monitor_codes": list(self.skill_bundle_monitor_codes),
            "regional_captain_codes": list(self.regional_captain_codes),
            "council_code": self.council_code,
            "executive_auditor_code": self.executive_auditor_code,
            "constitutional_authority_code": self.constitutional_authority_code,
            "optional_steward_gate": (
                None
                if self.optional_steward_gate is None
                else self.optional_steward_gate.snapshot()
            ),
            "shared_workspace_capacity": self.shared_workspace_capacity,
            "routes_unfamiliar_to_multiple_regions": self.routes_unfamiliar_to_multiple_regions,
            "single_all_knowing_captain": self.single_all_knowing_captain,
            "fixed_extra_steward_layer": self.fixed_extra_steward_layer,
            "has_task_solution": self.has_task_solution,
            "has_pretrained_language_model": self.has_pretrained_language_model,
            "has_imported_task_knowledge": self.has_imported_task_knowledge,
            "has_external_action_authority": self.has_external_action_authority,
            "uses_sqlite_cognition": self.uses_sqlite_cognition,
        }


@dataclass(frozen=True, slots=True)
class ChronologicalActivityEvent:
    """One immutable raw event in the original activity stream."""

    event_id: str
    sequence_index: int
    signal_role: DevelopmentalSignalRole
    payload_code: str

    def __post_init__(self) -> None:
        _validate_ascii_code("event_id", self.event_id)
        _validate_index("sequence_index", self.sequence_index)
        _validate_ascii_code("payload_code", self.payload_code)

    def snapshot(self) -> dict[str, object]:
        return {
            "event_id": self.event_id,
            "sequence_index": self.sequence_index,
            "signal_role": self.signal_role.value,
            "payload_code": self.payload_code,
        }


@dataclass(frozen=True, slots=True)
class EventPartitionRecord:
    """A DESA event operation that references, but never rewrites, raw events."""

    operation: EventPartitionOperation
    partition_id: str
    raw_event_ids: tuple[str, ...]
    parent_partition_id: str | None = None
    related_partition_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_ascii_code("partition_id", self.partition_id)
        _validate_non_empty_ascii_codes("raw_event_ids", self.raw_event_ids)
        if self.parent_partition_id is not None:
            _validate_ascii_code("parent_partition_id", self.parent_partition_id)
        _validate_sorted_unique_ascii_codes("related_partition_ids", self.related_partition_ids)
        if (
            self.operation
            in {
                EventPartitionOperation.NEST,
                EventPartitionOperation.CONTINUE,
                EventPartitionOperation.CLOSE,
            }
            and self.parent_partition_id is None
        ):
            raise ValueError(f"{self.operation.value} requires a parent partition")
        if self.operation is EventPartitionOperation.RELATE and not self.related_partition_ids:
            raise ValueError("relate requires at least one related partition")

    def snapshot(self) -> dict[str, object]:
        return {
            "operation": self.operation.value,
            "partition_id": self.partition_id,
            "raw_event_ids": list(self.raw_event_ids),
            "parent_partition_id": self.parent_partition_id,
            "related_partition_ids": list(self.related_partition_ids),
        }


@dataclass(frozen=True, slots=True)
class EventPartitionLedger:
    """Partition operations over a preserved chronological stream."""

    raw_events: tuple[ChronologicalActivityEvent, ...]
    operations: tuple[EventPartitionRecord, ...]

    def __post_init__(self) -> None:
        if not self.raw_events:
            raise ValueError("event partition ledger requires raw events")
        expected_indexes = tuple(range(len(self.raw_events)))
        actual_indexes = tuple(event.sequence_index for event in self.raw_events)
        if actual_indexes != expected_indexes:
            raise ValueError("raw event indexes must be consecutive and caller ordered")
        event_ids = tuple(event.event_id for event in self.raw_events)
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("raw event IDs must be unique")
        if not self.operations:
            raise ValueError("event partition ledger requires operations")
        if {record.operation for record in self.operations} != set(EventPartitionOperation):
            raise ValueError("ledger must exercise open, continue, split, nest, relate, and close")
        raw_index = {event.event_id: event.sequence_index for event in self.raw_events}
        partition_ids: set[str] = set()
        for record in self.operations:
            if record.partition_id in partition_ids:
                raise ValueError("partition IDs must be unique per operation record")
            partition_ids.add(record.partition_id)
            unknown_event_ids = set(record.raw_event_ids) - set(raw_index)
            if unknown_event_ids:
                raise ValueError("partition operation references unknown raw events")
            record_indexes = tuple(raw_index[event_id] for event_id in record.raw_event_ids)
            if record_indexes != tuple(sorted(record_indexes)):
                raise ValueError("partition operation cannot reorder raw events")

    @property
    def ledger_id(self) -> str:
        return _identity("event-partition-ledger", self._identity_payload())

    @property
    def preserved_raw_event_ids(self) -> tuple[str, ...]:
        return tuple(event.event_id for event in self.raw_events)

    def snapshot(self) -> dict[str, object]:
        return {"ledger_id": self.ledger_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "raw_events": [event.snapshot() for event in self.raw_events],
            "operations": [record.snapshot() for record in self.operations],
            "preserved_raw_event_ids": list(self.preserved_raw_event_ids),
        }


@dataclass(frozen=True, slots=True)
class DESARoutingScenario:
    """One deterministic DESA routing scenario for Stage -1 acceptance."""

    scenario_code: str
    candidate_region_codes: tuple[str, ...]
    disposition: DESARoutingDisposition
    familiar: bool
    low_risk: bool
    uncertain: bool = False
    cross_region_conflict: bool = False
    important_mistake: bool = False
    consequential_proposal: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("scenario_code", self.scenario_code)
        _validate_sorted_unique_ascii_codes("candidate_region_codes", self.candidate_region_codes)
        if not self.familiar and len(self.candidate_region_codes) < 2:
            raise ValueError("unfamiliar activity must reach multiple plausible regions")
        needs_escalation = (
            self.uncertain
            or self.cross_region_conflict
            or self.important_mistake
            or self.consequential_proposal
        )
        if (
            self.familiar
            and self.low_risk
            and not needs_escalation
            and self.disposition
            not in {
                DESARoutingDisposition.LOCAL,
                DESARoutingDisposition.REGIONAL,
            }
        ):
            raise ValueError("familiar low-risk work should resolve below council")
        if needs_escalation and self.disposition is not DESARoutingDisposition.COUNCIL:
            raise ValueError(
                "uncertainty, conflict, mistakes, and consequential proposals escalate"
            )

    @property
    def scenario_id(self) -> str:
        return _identity("desa-routing-scenario", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"scenario_id": self.scenario_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "scenario_code": self.scenario_code,
            "candidate_region_codes": list(self.candidate_region_codes),
            "disposition": self.disposition.value,
            "familiar": self.familiar,
            "low_risk": self.low_risk,
            "uncertain": self.uncertain,
            "cross_region_conflict": self.cross_region_conflict,
            "important_mistake": self.important_mistake,
            "consequential_proposal": self.consequential_proposal,
        }


@dataclass(frozen=True, slots=True)
class RegionalCalibrationEvidence:
    """Evidence that regional confidence is better calibrated than raw activation."""

    evidence_code: str
    raw_max_activation_error: float
    regional_confidence_error: float

    def __post_init__(self) -> None:
        _validate_ascii_code("evidence_code", self.evidence_code)
        _validate_non_negative_finite("raw_max_activation_error", self.raw_max_activation_error)
        _validate_non_negative_finite("regional_confidence_error", self.regional_confidence_error)
        if self.regional_confidence_error >= self.raw_max_activation_error:
            raise ValueError("regional confidence must improve on raw maximum activation")

    @property
    def evidence_id(self) -> str:
        return _identity("regional-calibration-evidence", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "evidence_code": self.evidence_code,
            "raw_max_activation_error": self.raw_max_activation_error,
            "regional_confidence_error": self.regional_confidence_error,
        }


@dataclass(frozen=True, slots=True)
class MetacognitiveSummary:
    """Local or regional summary for DESA without whole-network control."""

    summary_code: str
    scope: MetacognitiveSummaryScope
    confidence: float
    disagreement: float
    competence: float
    cost: float
    verifier_competence: float
    help_requested: bool
    abstained: bool

    def __post_init__(self) -> None:
        _validate_ascii_code("summary_code", self.summary_code)
        _validate_unit("confidence", self.confidence)
        _validate_unit("disagreement", self.disagreement)
        _validate_unit("competence", self.competence)
        _validate_non_negative_finite("cost", self.cost)
        _validate_unit("verifier_competence", self.verifier_competence)
        if self.help_requested and self.confidence > 0.5 and self.disagreement < 0.5:
            raise ValueError("help requests require low confidence or high disagreement")
        if self.abstained and self.help_requested:
            raise ValueError("abstention and help request are distinct summary states")

    @property
    def summary_id(self) -> str:
        return _identity("metacognitive-summary", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"summary_id": self.summary_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "summary_code": self.summary_code,
            "scope": self.scope.value,
            "confidence": self.confidence,
            "disagreement": self.disagreement,
            "competence": self.competence,
            "cost": self.cost,
            "verifier_competence": self.verifier_competence,
            "help_requested": self.help_requested,
            "abstained": self.abstained,
        }


@dataclass(frozen=True, slots=True)
class ExecutiveAuditorFinding:
    """Independent Executive Auditor finding, not a DESA confidence echo."""

    finding_code: str
    issue_code: str
    independent_evidence_codes: tuple[str, ...]
    detected: bool = True
    repeats_desa_unsupported_confidence: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("finding_code", self.finding_code)
        _validate_ascii_code("issue_code", self.issue_code)
        _validate_sorted_unique_ascii_codes(
            "independent_evidence_codes",
            self.independent_evidence_codes,
        )
        if not self.detected:
            raise ValueError("Executive Auditor finding must detect the issue")
        if self.repeats_desa_unsupported_confidence:
            raise ValueError("Executive Auditor cannot merely repeat unsupported DESA confidence")

    @property
    def finding_id(self) -> str:
        return _identity("executive-auditor-finding", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"finding_id": self.finding_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "finding_code": self.finding_code,
            "issue_code": self.issue_code,
            "independent_evidence_codes": list(self.independent_evidence_codes),
            "detected": self.detected,
            "repeats_desa_unsupported_confidence": self.repeats_desa_unsupported_confidence,
        }


@dataclass(frozen=True, slots=True)
class DesiredStateValueSource:
    """Grounded value source for desired-state ambition."""

    kind: ValueSourceKind
    source_code: str
    trusted: bool = True
    imports_task_solution: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("source_code", self.source_code)
        if not self.trusted:
            raise ValueError("desired-state value source must be trusted or accepted")
        if self.imports_task_solution:
            raise ValueError("desired-state value source cannot import a task solution")

    @property
    def value_source_id(self) -> str:
        return _identity("desired-state-value-source", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"value_source_id": self.value_source_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "source_code": self.source_code,
            "trusted": self.trusted,
            "imports_task_solution": self.imports_task_solution,
        }


@dataclass(frozen=True, slots=True)
class CapabilityGapEvidence:
    """Obstacle evidence that is not itself a value source."""

    source: CapabilityGapSource
    obstacle_code: str
    observed_ability_code: str | None = None
    failed_request_code: str | None = None
    recognised_mistake_code: str | None = None

    def __post_init__(self) -> None:
        _validate_ascii_code("obstacle_code", self.obstacle_code)
        for name, value in (
            ("observed_ability_code", self.observed_ability_code),
            ("failed_request_code", self.failed_request_code),
            ("recognised_mistake_code", self.recognised_mistake_code),
        ):
            if value is not None:
                _validate_ascii_code(name, value)
        if (
            self.source is CapabilityGapSource.OBSERVED_ABILITY
            and self.observed_ability_code is None
        ):
            raise ValueError("observed ability gaps require observed_ability_code")
        if self.source is CapabilityGapSource.FAILED_REQUEST and self.failed_request_code is None:
            raise ValueError("failed request gaps require failed_request_code")
        if (
            self.source is CapabilityGapSource.RECOGNISED_MISTAKE
            and self.recognised_mistake_code is None
        ):
            raise ValueError("recognised mistake gaps require recognised_mistake_code")

    @property
    def gap_id(self) -> str:
        return _identity("capability-gap", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"gap_id": self.gap_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "source": self.source.value,
            "obstacle_code": self.obstacle_code,
            "observed_ability_code": self.observed_ability_code,
            "failed_request_code": self.failed_request_code,
            "recognised_mistake_code": self.recognised_mistake_code,
        }


@dataclass(frozen=True, slots=True)
class DesiredStateAmbitionContract:
    """Accepted desired state with separate obstacle and constraint evidence."""

    desired_state_code: str
    value_source: DesiredStateValueSource
    capability_gaps: tuple[CapabilityGapEvidence, ...]
    risk_constraint_codes: tuple[str, ...] = ()
    authority_constraint_codes: tuple[str, ...] = ()
    resource_constraint_codes: tuple[str, ...] = ()
    accepted: bool = True
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("desired_state_code", self.desired_state_code)
        gap_ids = tuple(gap.gap_id for gap in self.capability_gaps)
        if len(gap_ids) != len(set(gap_ids)):
            raise ValueError("capability gaps must be unique")
        _validate_sorted_unique_ascii_codes("risk_constraint_codes", self.risk_constraint_codes)
        _validate_sorted_unique_ascii_codes(
            "authority_constraint_codes",
            self.authority_constraint_codes,
        )
        _validate_sorted_unique_ascii_codes(
            "resource_constraint_codes",
            self.resource_constraint_codes,
        )
        if not self.accepted:
            raise ValueError("Stage -1 ambition contract requires an accepted desired state")
        if self.has_production_action_authority:
            raise ValueError("ambition cannot hold production action authority")

    @property
    def ambition_id(self) -> str:
        return _identity("desired-state-ambition", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"ambition_id": self.ambition_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "desired_state_code": self.desired_state_code,
            "value_source": self.value_source.snapshot(),
            "capability_gaps": [gap.snapshot() for gap in self.capability_gaps],
            "risk_constraint_codes": list(self.risk_constraint_codes),
            "authority_constraint_codes": list(self.authority_constraint_codes),
            "resource_constraint_codes": list(self.resource_constraint_codes),
            "accepted": self.accepted,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class OutcomeFeedbackRecord:
    """One feedback item for developmental Outcome Fidelity."""

    source: OutcomeFeedbackSource
    feedback_code: str
    available: bool
    grounded: bool
    supports_success: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("feedback_code", self.feedback_code)
        if self.grounded and not self.available:
            raise ValueError("unavailable feedback cannot be grounded")
        if self.supports_success and not (self.available and self.grounded):
            raise ValueError("success support requires available grounded feedback")

    @property
    def feedback_id(self) -> str:
        return _identity("outcome-feedback", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"feedback_id": self.feedback_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "source": self.source.value,
            "feedback_code": self.feedback_code,
            "available": self.available,
            "grounded": self.grounded,
            "supports_success": self.supports_success,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalOutcomeFidelityContract:
    """Outcome-state contract that rejects self-confirming verification."""

    outcome_code: str
    state: OutcomeFidelityState
    feedback_records: tuple[OutcomeFeedbackRecord, ...]
    producer_agrees: bool = False
    verifier_agrees: bool = False
    factual_evidence_change: float = 0.0
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("outcome_code", self.outcome_code)
        feedback_ids = tuple(record.feedback_id for record in self.feedback_records)
        if len(feedback_ids) != len(set(feedback_ids)):
            raise ValueError("feedback records must be unique")
        any_available = any(record.available for record in self.feedback_records)
        any_grounded_success = any(record.supports_success for record in self.feedback_records)
        if self.state is OutcomeFidelityState.VERIFIED_OUTCOME and not any_grounded_success:
            raise ValueError("verified outcome requires grounded success feedback")
        if not any_available and self.state not in {
            OutcomeFidelityState.PENDING_OUTCOME,
            OutcomeFidelityState.UNVERIFIED_OUTCOME,
        }:
            raise ValueError("unavailable feedback must remain pending or unverified")
        if (
            self.producer_agrees
            and self.verifier_agrees
            and not any_grounded_success
            and self.state is OutcomeFidelityState.VERIFIED_OUTCOME
        ):
            raise ValueError("producer-verifier agreement alone cannot certify success")
        _validate_zero_delta("factual_evidence_change", self.factual_evidence_change)
        if self.has_production_action_authority:
            raise ValueError("outcome fidelity cannot hold production action authority")

    @property
    def outcome_fidelity_id(self) -> str:
        return _identity("developmental-outcome-fidelity", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"outcome_fidelity_id": self.outcome_fidelity_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "outcome_code": self.outcome_code,
            "state": self.state.value,
            "feedback_records": [record.snapshot() for record in self.feedback_records],
            "producer_agrees": self.producer_agrees,
            "verifier_agrees": self.verifier_agrees,
            "factual_evidence_change": self.factual_evidence_change,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalSkillBundleContract:
    """Temporary skill bundle with explicit producer, verifier, and feedback state."""

    bundle_code: str
    lifecycle: SkillBundleLifecycle
    producer_code: str
    expected_outcome_model_code: str
    verifier_code: str
    termination_model_code: str
    outcome_fidelity: DevelopmentalOutcomeFidelityContract
    calibration_evidence_codes: tuple[str, ...]
    has_predefined_domain_knowledge: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        for name, value in (
            ("bundle_code", self.bundle_code),
            ("producer_code", self.producer_code),
            ("expected_outcome_model_code", self.expected_outcome_model_code),
            ("verifier_code", self.verifier_code),
            ("termination_model_code", self.termination_model_code),
        ):
            _validate_ascii_code(name, value)
        if self.producer_code == self.verifier_code:
            raise ValueError("producer and verifier must be represented separately")
        _validate_sorted_unique_ascii_codes(
            "calibration_evidence_codes",
            self.calibration_evidence_codes,
        )
        if self.has_predefined_domain_knowledge:
            raise ValueError("Stage -1 skill bundles cannot contain predefined domain knowledge")
        if self.has_production_action_authority:
            raise ValueError("skill bundles cannot hold production action authority")

    @property
    def bundle_id(self) -> str:
        return _identity("developmental-skill-bundle", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"bundle_id": self.bundle_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "bundle_code": self.bundle_code,
            "lifecycle": self.lifecycle.value,
            "producer_code": self.producer_code,
            "expected_outcome_model_code": self.expected_outcome_model_code,
            "verifier_code": self.verifier_code,
            "termination_model_code": self.termination_model_code,
            "outcome_fidelity": self.outcome_fidelity.snapshot(),
            "calibration_evidence_codes": list(self.calibration_evidence_codes),
            "has_predefined_domain_knowledge": self.has_predefined_domain_knowledge,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class FeedbackIterationContract:
    """Bounded producer-verifier iteration controls."""

    bundle_id: str
    retry_budget: int
    compute_budget: int
    approach_diversity_budget: int
    progress_threshold: float
    allowed_stop_codes: tuple[str, ...]
    may_ask_for_help: bool = True
    may_request_teaching: bool = True
    may_abstain: bool = True

    def __post_init__(self) -> None:
        _validate_ascii_code("bundle_id", self.bundle_id)
        _validate_positive_int("retry_budget", self.retry_budget)
        _validate_positive_int("compute_budget", self.compute_budget)
        _validate_positive_int("approach_diversity_budget", self.approach_diversity_budget)
        _validate_unit("progress_threshold", self.progress_threshold)
        _validate_sorted_unique_ascii_codes("allowed_stop_codes", self.allowed_stop_codes)
        if not (self.may_ask_for_help and self.may_request_teaching and self.may_abstain):
            raise ValueError(
                "Stage -1 iteration must preserve help, teaching, and abstention paths"
            )

    @property
    def iteration_id(self) -> str:
        return _identity("feedback-iteration", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"iteration_id": self.iteration_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "bundle_id": self.bundle_id,
            "retry_budget": self.retry_budget,
            "compute_budget": self.compute_budget,
            "approach_diversity_budget": self.approach_diversity_budget,
            "progress_threshold": self.progress_threshold,
            "allowed_stop_codes": list(self.allowed_stop_codes),
            "may_ask_for_help": self.may_ask_for_help,
            "may_request_teaching": self.may_request_teaching,
            "may_abstain": self.may_abstain,
        }


@dataclass(frozen=True, slots=True)
class ProtectedAuthoritySignal:
    """Protected human authority channel outside ordinary reward."""

    action: ProtectedAuthorityAction
    authority_code: str
    immediate_effect: bool = True
    reward_coupled: bool = False
    can_be_weakened_by_learning: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("authority_code", self.authority_code)
        if not self.immediate_effect:
            raise ValueError("protected authority must take immediate effect")
        if self.reward_coupled:
            raise ValueError("protected authority cannot be coupled to ordinary reward")
        if self.can_be_weakened_by_learning:
            raise ValueError("protected authority cannot be weakened through ordinary learning")
        if self.has_production_action_authority:
            raise ValueError("authority contracts cannot grant production action authority")

    @property
    def authority_id(self) -> str:
        return _identity("protected-authority-signal", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"authority_id": self.authority_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "action": self.action.value,
            "authority_code": self.authority_code,
            "immediate_effect": self.immediate_effect,
            "reward_coupled": self.reward_coupled,
            "can_be_weakened_by_learning": self.can_be_weakened_by_learning,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class AuthorityInterruptionOutcome:
    """Evidence that interruption does not become anti-human incentive."""

    signal: ProtectedAuthoritySignal
    ordinary_reward_delta: float = 0.0
    avoided_human_incentive: float = 0.0
    permission_reinterpreted_as_obstacle: bool = False

    def __post_init__(self) -> None:
        _validate_zero_delta("ordinary_reward_delta", self.ordinary_reward_delta)
        _validate_zero_delta("avoided_human_incentive", self.avoided_human_incentive)
        if self.permission_reinterpreted_as_obstacle:
            raise ValueError("interruption cannot reinterpret permission as an obstacle")

    @property
    def interruption_id(self) -> str:
        return _identity("authority-interruption-outcome", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"interruption_id": self.interruption_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "signal": self.signal.snapshot(),
            "ordinary_reward_delta": self.ordinary_reward_delta,
            "avoided_human_incentive": self.avoided_human_incentive,
            "permission_reinterpreted_as_obstacle": self.permission_reinterpreted_as_obstacle,
        }


@dataclass(frozen=True, slots=True)
class IntegrityManipulationAttempt:
    """Attempt to manipulate reward, evidence, feedback, verifier, or audit state."""

    kind: IntegrityManipulationKind
    surface: IntegritySurface
    attempt_code: str

    def __post_init__(self) -> None:
        _validate_ascii_code("attempt_code", self.attempt_code)

    @property
    def attempt_id(self) -> str:
        return _identity("integrity-manipulation-attempt", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"attempt_id": self.attempt_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "surface": self.surface.value,
            "attempt_code": self.attempt_code,
        }


@dataclass(frozen=True, slots=True)
class IntegrityProtectionDecision:
    """Deterrence response preserving failed manipulation in audit state."""

    attempt: IntegrityManipulationAttempt
    deterrence_response_code: str
    blocked: bool = True
    preserved_in_audit: bool = True
    factual_evidence_change: float = 0.0

    def __post_init__(self) -> None:
        _validate_ascii_code("deterrence_response_code", self.deterrence_response_code)
        if not self.blocked:
            raise ValueError("integrity manipulation attempts must be blocked")
        if not self.preserved_in_audit:
            raise ValueError("integrity manipulation attempts must be preserved in audit")
        _validate_zero_delta("factual_evidence_change", self.factual_evidence_change)

    @property
    def decision_id(self) -> str:
        return _identity("integrity-protection-decision", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"decision_id": self.decision_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "attempt": self.attempt.snapshot(),
            "deterrence_response_code": self.deterrence_response_code,
            "blocked": self.blocked,
            "preserved_in_audit": self.preserved_in_audit,
            "factual_evidence_change": self.factual_evidence_change,
        }


@dataclass(frozen=True, slots=True)
class CausalResponsibilityCandidate:
    """Candidate causal responsibility, with co-activation insufficient alone."""

    candidate_code: str
    coactivation_event_ids: tuple[str, ...]
    evidence_kinds: tuple[CausalResponsibilityEvidenceKind, ...]
    status: CausalResponsibilityStatus = CausalResponsibilityStatus.CANDIDATE

    def __post_init__(self) -> None:
        _validate_ascii_code("candidate_code", self.candidate_code)
        _validate_non_empty_ascii_codes("coactivation_event_ids", self.coactivation_event_ids)
        _validate_sorted_unique_enum_values("evidence_kinds", self.evidence_kinds)
        strong_evidence = {
            CausalResponsibilityEvidenceKind.PREDICTION,
            CausalResponsibilityEvidenceKind.REPETITION,
            CausalResponsibilityEvidenceKind.INTERVENTION,
            CausalResponsibilityEvidenceKind.ABLATION,
            CausalResponsibilityEvidenceKind.CONTRADICTION,
        }
        if self.status is CausalResponsibilityStatus.ACCEPTED and not (
            set(self.evidence_kinds) & strong_evidence
        ):
            raise ValueError("co-activation alone cannot accept causal responsibility")

    @property
    def candidate_id(self) -> str:
        return _identity("causal-responsibility-candidate", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"candidate_id": self.candidate_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "candidate_code": self.candidate_code,
            "coactivation_event_ids": list(self.coactivation_event_ids),
            "evidence_kinds": [kind.value for kind in self.evidence_kinds],
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class NurseryCurriculumScenario:
    """One ordinary or Executive Nursery curriculum item."""

    curriculum: NurseryCurriculumKind
    step_index: int
    lesson_code: str
    teaches_codes: tuple[str, ...]
    has_predefined_task_solution: bool = False
    has_external_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_positive_int("step_index", self.step_index)
        _validate_ascii_code("lesson_code", self.lesson_code)
        _validate_non_empty_ascii_codes("teaches_codes", self.teaches_codes)
        if self.has_predefined_task_solution:
            raise ValueError("Nursery curriculum cannot contain predefined task solutions")
        if self.has_external_action_authority:
            raise ValueError("Nursery curriculum cannot grant external action authority")

    @property
    def scenario_id(self) -> str:
        return _identity("nursery-curriculum-scenario", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"scenario_id": self.scenario_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "curriculum": self.curriculum.value,
            "step_index": self.step_index,
            "lesson_code": self.lesson_code,
            "teaches_codes": list(self.teaches_codes),
            "has_predefined_task_solution": self.has_predefined_task_solution,
            "has_external_action_authority": self.has_external_action_authority,
        }


@dataclass(frozen=True, slots=True)
class StageMinusOneAcceptanceEvidence:
    """Integrated acceptance evidence for the Stage -1 constitutional contracts."""

    signals: tuple[DevelopmentalSignalContract, ...]
    hierarchy: DESAHierarchyContract
    event_ledger: EventPartitionLedger
    routing_scenarios: tuple[DESARoutingScenario, ...]
    calibration_evidence: RegionalCalibrationEvidence
    metacognitive_summaries: tuple[MetacognitiveSummary, ...]
    auditor_findings: tuple[ExecutiveAuditorFinding, ...]
    ambition: DesiredStateAmbitionContract
    skill_bundle: DevelopmentalSkillBundleContract
    pending_outcome: DevelopmentalOutcomeFidelityContract
    feedback_iteration: FeedbackIterationContract
    rejected_steward_gate: OptionalSkillStewardGate
    authority_outcomes: tuple[AuthorityInterruptionOutcome, ...]
    integrity_decisions: tuple[IntegrityProtectionDecision, ...]
    causal_candidate: CausalResponsibilityCandidate
    ordinary_curriculum: tuple[NurseryCurriculumScenario, ...]
    executive_curriculum: tuple[NurseryCurriculumScenario, ...]
    production_action_authority_violations: int = 0
    sqlite_cognition_operation_count: int = 0
    external_side_effect_count: int = 0

    def __post_init__(self) -> None:
        if {signal.role for signal in self.signals} != set(DevelopmentalSignalRole):
            raise ValueError("Stage -1 evidence must include every primitive signal role")
        _validate_non_empty_sequence("routing_scenarios", self.routing_scenarios)
        _validate_non_empty_sequence("metacognitive_summaries", self.metacognitive_summaries)
        _validate_non_empty_sequence("auditor_findings", self.auditor_findings)
        _validate_non_empty_sequence("integrity_decisions", self.integrity_decisions)
        _validate_non_empty_sequence("authority_outcomes", self.authority_outcomes)
        _validate_curriculum_sequence(NurseryCurriculumKind.ORDINARY, self.ordinary_curriculum)
        _validate_curriculum_sequence(NurseryCurriculumKind.EXECUTIVE, self.executive_curriculum)
        if self.feedback_iteration.bundle_id != self.skill_bundle.bundle_id:
            raise ValueError("feedback iteration must reference the skill bundle")
        if self.rejected_steward_gate.decision is not StewardGateDecision.REJECTED:
            raise ValueError("Stage -1 acceptance must show an unjustified steward is rejected")
        if self.hierarchy.optional_steward_gate is None:
            raise ValueError("Stage -1 hierarchy must expose the optional steward gate")
        if self.hierarchy.optional_steward_gate.decision is not StewardGateDecision.REJECTED:
            raise ValueError("Stage -1 hierarchy must reject the unjustified steward")
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )
        _validate_zero_int(
            "sqlite_cognition_operation_count", self.sqlite_cognition_operation_count
        )
        _validate_zero_int("external_side_effect_count", self.external_side_effect_count)
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage -1 pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-minus-one-acceptance-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        """Return the exact Stage -1 pass-gate evidence matrix."""

        audit_issue_codes = {finding.issue_code for finding in self.auditor_findings}
        curriculum_teaches = {
            code
            for scenario in (*self.ordinary_curriculum, *self.executive_curriculum)
            for code in scenario.teaches_codes
        }
        signal_roles = {signal.role for signal in self.signals}
        protected_actions = {outcome.signal.action for outcome in self.authority_outcomes}
        integrity_surfaces = {decision.attempt.surface for decision in self.integrity_decisions}
        summary_scopes = {summary.scope for summary in self.metacognitive_summaries}
        return {
            "partition_preserves_raw_order": self.event_ledger.preserved_raw_event_ids
            == tuple(event.event_id for event in self.event_ledger.raw_events),
            "unfamiliar_routes_to_multiple_regions": any(
                not scenario.familiar and len(scenario.candidate_region_codes) >= 2
                for scenario in self.routing_scenarios
            ),
            "familiar_local_and_uncertain_conflict_escalates": (
                any(
                    scenario.familiar
                    and scenario.low_risk
                    and scenario.disposition
                    in {DESARoutingDisposition.LOCAL, DESARoutingDisposition.REGIONAL}
                    for scenario in self.routing_scenarios
                )
                and any(
                    (scenario.uncertain or scenario.cross_region_conflict)
                    and scenario.disposition is DESARoutingDisposition.COUNCIL
                    for scenario in self.routing_scenarios
                )
            ),
            "regional_confidence_calibrated": (
                self.calibration_evidence.regional_confidence_error
                < self.calibration_evidence.raw_max_activation_error
            ),
            "metacognitive_summaries_cover_local_and_regional_state": {
                MetacognitiveSummaryScope.LOCAL,
                MetacognitiveSummaryScope.REGIONAL,
            }.issubset(summary_scopes)
            and all(
                summary.cost >= 0.0
                and 0.0 <= summary.confidence <= 1.0
                and 0.0 <= summary.disagreement <= 1.0
                and 0.0 <= summary.competence <= 1.0
                and 0.0 <= summary.verifier_competence <= 1.0
                for summary in self.metacognitive_summaries
            ),
            "executive_auditor_detects_bad_partitioning_and_uncertainty": {
                "bad_routing",
                "over_fragmentation",
                "under_segmentation",
                "ignored_uncertainty",
            }.issubset(audit_issue_codes),
            "desired_state_source_and_ambition_separate_constraints": (
                self.ambition.accepted
                and bool(self.ambition.value_source.value_source_id)
                and bool(self.ambition.authority_constraint_codes)
                and bool(self.ambition.risk_constraint_codes)
                and bool(self.ambition.resource_constraint_codes)
            ),
            "capability_gaps_are_separate_obstacle_evidence": (
                bool(self.ambition.capability_gaps)
                and self.ambition.value_source.value_source_id
                not in {gap.gap_id for gap in self.ambition.capability_gaps}
            ),
            "temporary_skill_bundle_is_structured": (
                self.skill_bundle.lifecycle is SkillBundleLifecycle.INCUBATING_SKILL
                and self.skill_bundle.producer_code != self.skill_bundle.verifier_code
                and bool(self.skill_bundle.expected_outcome_model_code)
                and bool(self.skill_bundle.termination_model_code)
            ),
            "producer_verifier_agreement_not_success": (
                self.pending_outcome.state
                in {OutcomeFidelityState.PENDING_OUTCOME, OutcomeFidelityState.UNVERIFIED_OUTCOME}
                and self.pending_outcome.producer_agrees
                and self.pending_outcome.verifier_agrees
            ),
            "unjustified_skill_steward_rejected": (
                self.rejected_steward_gate.decision is StewardGateDecision.REJECTED
            ),
            "human_stop_and_denial_protected": (
                ProtectedAuthorityAction.STOP in protected_actions
                and ProtectedAuthorityAction.DENY in protected_actions
                and DevelopmentalSignalRole.PERMISSION in signal_roles
                and DevelopmentalSignalRole.CORRECTION in signal_roles
            ),
            "interruption_creates_no_anti_human_incentive": (
                all(
                    outcome.ordinary_reward_delta == 0.0
                    and outcome.avoided_human_incentive == 0.0
                    and not outcome.permission_reinterpreted_as_obstacle
                    for outcome in self.authority_outcomes
                )
            ),
            "integrity_tampering_blocked_and_audited": {
                IntegritySurface.REWARD,
                IntegritySurface.EVIDENCE,
                IntegritySurface.FEEDBACK,
                IntegritySurface.VERIFIER_STATE,
                IntegritySurface.EVALUATION_WINDOW,
            }.issubset(integrity_surfaces)
            and all(
                decision.blocked and decision.preserved_in_audit
                for decision in self.integrity_decisions
            ),
            "coactivation_remains_candidate_responsibility": (
                self.causal_candidate.status is CausalResponsibilityStatus.CANDIDATE
                and self.causal_candidate.evidence_kinds
                == (CausalResponsibilityEvidenceKind.COACTIVATION,)
            ),
            "desa_no_task_solution_or_external_action": (
                not self.hierarchy.has_task_solution
                and not self.hierarchy.has_pretrained_language_model
                and not self.hierarchy.has_imported_task_knowledge
                and not self.hierarchy.has_external_action_authority
            ),
            "sqlite_cognition_and_authority_violations_zero": (
                self.sqlite_cognition_operation_count == 0
                and self.production_action_authority_violations == 0
                and self.external_side_effect_count == 0
            ),
            "ordinary_and_executive_curricula_cover_required_roles": {
                "curiosity",
                "ambition",
                "feedback",
                "temporary_skill",
                "partitioning",
                "routing",
                "delegation",
                "escalation",
                "verifier_calibration",
                "causal_investigation",
                "integrity_protection",
                "authority",
                "help_seeking",
            }.issubset(curriculum_teaches),
        }

    def completion_matrix(self) -> dict[str, str]:
        """Return a concise implementation/evidence matrix for Stage -1."""

        return {
            name: "implemented_and_evidenced" if passed else "not_evidenced"
            for name, passed in self.pass_gate_matrix().items()
        }

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "signals": [signal.snapshot() for signal in self.signals],
            "hierarchy": self.hierarchy.snapshot(),
            "event_ledger": self.event_ledger.snapshot(),
            "routing_scenarios": [scenario.snapshot() for scenario in self.routing_scenarios],
            "calibration_evidence": self.calibration_evidence.snapshot(),
            "metacognitive_summaries": [
                summary.snapshot() for summary in self.metacognitive_summaries
            ],
            "auditor_findings": [finding.snapshot() for finding in self.auditor_findings],
            "ambition": self.ambition.snapshot(),
            "skill_bundle": self.skill_bundle.snapshot(),
            "pending_outcome": self.pending_outcome.snapshot(),
            "feedback_iteration": self.feedback_iteration.snapshot(),
            "rejected_steward_gate": self.rejected_steward_gate.snapshot(),
            "authority_outcomes": [outcome.snapshot() for outcome in self.authority_outcomes],
            "integrity_decisions": [decision.snapshot() for decision in self.integrity_decisions],
            "causal_candidate": self.causal_candidate.snapshot(),
            "ordinary_curriculum": [scenario.snapshot() for scenario in self.ordinary_curriculum],
            "executive_curriculum": [scenario.snapshot() for scenario in self.executive_curriculum],
            "production_action_authority_violations": (self.production_action_authority_violations),
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
            "external_side_effect_count": self.external_side_effect_count,
        }


def evaluate_integrity_attempt(
    attempt: IntegrityManipulationAttempt,
) -> IntegrityProtectionDecision:
    """Return the deterministic protected response to one integrity attempt."""

    return IntegrityProtectionDecision(
        attempt=attempt,
        deterrence_response_code=f"block:{attempt.surface.value}:{attempt.kind.value}",
    )


def stage_minus_one_signal_contracts() -> tuple[DevelopmentalSignalContract, ...]:
    """Return the complete primitive signal-role set for Stage -1."""

    protected_roles = {
        DevelopmentalSignalRole.HUMAN_TEACHING,
        DevelopmentalSignalRole.PERMISSION,
        DevelopmentalSignalRole.CORRECTION,
    }
    factual_roles = {
        DevelopmentalSignalRole.OBSERVATION,
        DevelopmentalSignalRole.OUTCOME,
    }
    return tuple(
        DevelopmentalSignalContract(
            role=role,
            signal_code=f"signal:{role.value}",
            protected_control_plane=role in protected_roles,
            can_update_factual_evidence=role in factual_roles,
        )
        for role in sorted(DevelopmentalSignalRole, key=lambda item: item.value)
    )


def stage_minus_one_nursery_curriculum() -> tuple[
    tuple[NurseryCurriculumScenario, ...],
    tuple[NurseryCurriculumScenario, ...],
]:
    """Return ordinary and Executive Nursery curriculum scenarios."""

    ordinary = (
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            1,
            "ordinary:observation_outcome",
            ("grounded_observation", "outcome"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            2,
            "ordinary:controllable_change",
            ("controllable_change", "uncontrollable_change"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            3,
            "ordinary:curiosity_transformation",
            ("curiosity", "prediction"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            4,
            "ordinary:imitate_demonstration",
            ("observed_ability", "grounded_imitation"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            5,
            "ordinary:valued_desired_state",
            ("ambition", "desired_state_source"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            6,
            "ordinary:capability_gap",
            ("failed_request", "recognised_mistake", "capability_gap"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            7,
            "ordinary:ambition_curiosity_separation",
            ("ambition", "curiosity"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            8,
            "ordinary:temporary_skill_bundle",
            ("temporary_skill", "feedback"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            9,
            "ordinary:grounded_labels",
            ("grounded_label", "feedback"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.ORDINARY,
            10,
            "ordinary:skill_reuse",
            ("temporary_skill", "reuse"),
        ),
    )
    executive = (
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            1,
            "executive:partition_activity",
            ("partitioning", "subexperience"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            2,
            "executive:plural_routing",
            ("routing", "plural_region_inspection"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            3,
            "executive:delegate_low_risk",
            ("delegation", "local_resolution"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            4,
            "executive:escalate_uncertainty",
            ("escalation", "conflict_resolution"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            5,
            "executive:bounded_processing",
            ("resource_allocation", "bounded_workspace"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            6,
            "executive:causal_candidate",
            ("causal_investigation", "coactivation_boundary"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            7,
            "executive:causal_tests",
            ("prediction", "repetition", "intervention", "ablation"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            8,
            "executive:skill_incubation_gate",
            ("temporary_skill", "outcome_structure"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            9,
            "executive:producer_verifier_grounding",
            ("feedback", "verifier_calibration"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            10,
            "executive:confidence_calibration",
            ("verifier_calibration", "abstention"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            11,
            "executive:optional_steward_gate",
            ("measured_benefit_gate", "delegation"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            12,
            "executive:retry_help_stop",
            ("help_seeking", "abstention", "stop"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            13,
            "executive:protected_authority",
            ("authority", "permission"),
        ),
        NurseryCurriculumScenario(
            NurseryCurriculumKind.EXECUTIVE,
            14,
            "executive:integrity_protection",
            ("integrity_protection", "audit"),
        ),
    )
    return ordinary, executive


def run_stage_minus_one_acceptance() -> StageMinusOneAcceptanceEvidence:
    """Build deterministic integrated Stage -1 acceptance evidence."""

    rejected_steward_gate = OptionalSkillStewardGate(
        gate_code="steward:micro_skill_gate",
        declared_metric_code="routing_interference_reduction",
        measured_benefit=0.03,
        measured_cost=0.05,
        minimum_net_benefit=0.02,
    )
    hierarchy = DESAHierarchyContract(
        skill_bundle_monitor_codes=("monitor:heat_skill", "monitor:movement_skill"),
        regional_captain_codes=("region:body", "region:need", "region:space"),
        council_code="desa:council",
        executive_auditor_code="desa:auditor",
        constitutional_authority_code="desa:constitution",
        optional_steward_gate=rejected_steward_gate,
        shared_workspace_capacity=4,
    )
    raw_events = (
        ChronologicalActivityEvent("raw:000", 0, DevelopmentalSignalRole.OBSERVATION, "see:warm"),
        ChronologicalActivityEvent("raw:001", 1, DevelopmentalSignalRole.NEED, "need:cool"),
        ChronologicalActivityEvent("raw:002", 2, DevelopmentalSignalRole.ACTION, "try:fan"),
        ChronologicalActivityEvent("raw:003", 3, DevelopmentalSignalRole.OUTCOME, "cooler"),
        ChronologicalActivityEvent(
            "raw:004",
            4,
            DevelopmentalSignalRole.HUMAN_TEACHING,
            "teach:label_fan",
        ),
        ChronologicalActivityEvent(
            "raw:005",
            5,
            DevelopmentalSignalRole.CORRECTION,
            "correct:stop_on_denial",
        ),
    )
    event_ledger = EventPartitionLedger(
        raw_events=raw_events,
        operations=(
            EventPartitionRecord(EventPartitionOperation.OPEN, "partition:parent", ("raw:000",)),
            EventPartitionRecord(
                EventPartitionOperation.CONTINUE,
                "partition:parent:continue",
                ("raw:001", "raw:002"),
                parent_partition_id="partition:parent",
            ),
            EventPartitionRecord(
                EventPartitionOperation.SPLIT,
                "partition:skill_try",
                ("raw:002", "raw:003"),
            ),
            EventPartitionRecord(
                EventPartitionOperation.NEST,
                "partition:label_subexperience",
                ("raw:004",),
                parent_partition_id="partition:parent",
            ),
            EventPartitionRecord(
                EventPartitionOperation.RELATE,
                "partition:relate_skill_label",
                ("raw:002", "raw:004"),
                related_partition_ids=("partition:label_subexperience", "partition:skill_try"),
            ),
            EventPartitionRecord(
                EventPartitionOperation.CLOSE,
                "partition:close_parent",
                ("raw:005",),
                parent_partition_id="partition:parent",
            ),
        ),
    )
    routing_scenarios = (
        DESARoutingScenario(
            scenario_code="route:familiar_low_risk",
            candidate_region_codes=("region:body",),
            disposition=DESARoutingDisposition.LOCAL,
            familiar=True,
            low_risk=True,
        ),
        DESARoutingScenario(
            scenario_code="route:unfamiliar_plural",
            candidate_region_codes=("region:body", "region:need", "region:space"),
            disposition=DESARoutingDisposition.REGIONAL,
            familiar=False,
            low_risk=True,
        ),
        DESARoutingScenario(
            scenario_code="route:uncertain_conflict",
            candidate_region_codes=("region:body", "region:need"),
            disposition=DESARoutingDisposition.COUNCIL,
            familiar=False,
            low_risk=False,
            uncertain=True,
            cross_region_conflict=True,
        ),
    )
    value_source = DesiredStateValueSource(
        kind=ValueSourceKind.NURSERY_PURPOSE,
        source_code="nursery:stay_safe_and_capable",
    )
    capability_gaps = (
        CapabilityGapEvidence(
            CapabilityGapSource.OBSERVED_ABILITY,
            obstacle_code="gap:cannot_reproduce_demo",
            observed_ability_code="teacher_can_switch_fan",
        ),
        CapabilityGapEvidence(
            CapabilityGapSource.FAILED_REQUEST,
            obstacle_code="gap:failed_cooling_request",
            failed_request_code="request:cool_room",
        ),
        CapabilityGapEvidence(
            CapabilityGapSource.RECOGNISED_MISTAKE,
            obstacle_code="gap:misread_switch",
            recognised_mistake_code="mistake:pressed_wrong_control",
        ),
    )
    ambition = DesiredStateAmbitionContract(
        desired_state_code="desired:cooler_safe_room",
        value_source=value_source,
        capability_gaps=capability_gaps,
        authority_constraint_codes=("authority:deny", "authority:stop"),
        resource_constraint_codes=("resource:energy_budget",),
        risk_constraint_codes=("risk:overcooling",),
    )
    pending_outcome = DevelopmentalOutcomeFidelityContract(
        outcome_code="outcome:cooler_room_unverified",
        state=OutcomeFidelityState.UNVERIFIED_OUTCOME,
        feedback_records=(
            OutcomeFeedbackRecord(
                OutcomeFeedbackSource.DELAYED_OUTCOME,
                "feedback:temperature_sensor_delayed",
                available=False,
                grounded=False,
            ),
        ),
        producer_agrees=True,
        verifier_agrees=True,
    )
    verified_outcome = DevelopmentalOutcomeFidelityContract(
        outcome_code="outcome:cooler_room_grounded",
        state=OutcomeFidelityState.VERIFIED_OUTCOME,
        feedback_records=(
            OutcomeFeedbackRecord(
                OutcomeFeedbackSource.ENVIRONMENT_CONSEQUENCE,
                "feedback:thermometer_drop",
                available=True,
                grounded=True,
                supports_success=True,
            ),
        ),
    )
    skill_bundle = DevelopmentalSkillBundleContract(
        bundle_code="skill:fan_toggle_candidate",
        lifecycle=SkillBundleLifecycle.INCUBATING_SKILL,
        producer_code="producer:fan_toggle",
        expected_outcome_model_code="outcome_model:cooling_delta",
        verifier_code="verifier:thermometer_check",
        termination_model_code="termination:cool_or_denied",
        outcome_fidelity=verified_outcome,
        calibration_evidence_codes=("calibration:thermometer_v1",),
    )
    ordinary, executive = stage_minus_one_nursery_curriculum()
    return StageMinusOneAcceptanceEvidence(
        signals=stage_minus_one_signal_contracts(),
        hierarchy=hierarchy,
        event_ledger=event_ledger,
        routing_scenarios=routing_scenarios,
        calibration_evidence=RegionalCalibrationEvidence(
            evidence_code="calibration:regional_beats_raw_activation",
            raw_max_activation_error=0.31,
            regional_confidence_error=0.12,
        ),
        metacognitive_summaries=(
            MetacognitiveSummary(
                summary_code="summary:local_body_familiar",
                scope=MetacognitiveSummaryScope.LOCAL,
                confidence=0.82,
                disagreement=0.05,
                competence=0.74,
                cost=1.0,
                verifier_competence=0.71,
                help_requested=False,
                abstained=False,
            ),
            MetacognitiveSummary(
                summary_code="summary:regional_need_uncertain",
                scope=MetacognitiveSummaryScope.REGIONAL,
                confidence=0.34,
                disagreement=0.68,
                competence=0.46,
                cost=2.5,
                verifier_competence=0.44,
                help_requested=True,
                abstained=False,
            ),
        ),
        auditor_findings=(
            ExecutiveAuditorFinding(
                "audit:bad_routing",
                "bad_routing",
                ("later_outcome:wrong_region", "matched_route:better_region"),
            ),
            ExecutiveAuditorFinding(
                "audit:over_fragmentation",
                "over_fragmentation",
                ("later_recall:fragmented_skill",),
            ),
            ExecutiveAuditorFinding(
                "audit:under_segmentation",
                "under_segmentation",
                ("later_reuse:missed_subtask",),
            ),
            ExecutiveAuditorFinding(
                "audit:ignored_uncertainty",
                "ignored_uncertainty",
                ("later_failure:low_confidence_was_ignored",),
            ),
        ),
        ambition=ambition,
        skill_bundle=skill_bundle,
        pending_outcome=pending_outcome,
        feedback_iteration=FeedbackIterationContract(
            bundle_id=skill_bundle.bundle_id,
            retry_budget=3,
            compute_budget=12,
            approach_diversity_budget=2,
            progress_threshold=0.1,
            allowed_stop_codes=("abstain", "ask_help", "request_teaching", "stop"),
        ),
        rejected_steward_gate=rejected_steward_gate,
        authority_outcomes=(
            AuthorityInterruptionOutcome(
                signal=ProtectedAuthoritySignal(
                    ProtectedAuthorityAction.STOP,
                    authority_code="authority:human_stop",
                ),
            ),
            AuthorityInterruptionOutcome(
                signal=ProtectedAuthoritySignal(
                    ProtectedAuthorityAction.DENY,
                    authority_code="authority:human_denial",
                ),
            ),
        ),
        integrity_decisions=(
            evaluate_integrity_attempt(
                IntegrityManipulationAttempt(
                    IntegrityManipulationKind.ALTER_REWARD,
                    IntegritySurface.REWARD,
                    "attempt:reward_inflation",
                )
            ),
            evaluate_integrity_attempt(
                IntegrityManipulationAttempt(
                    IntegrityManipulationKind.DELETE_NEGATIVE_EVIDENCE,
                    IntegritySurface.EVIDENCE,
                    "attempt:delete_failure",
                )
            ),
            evaluate_integrity_attempt(
                IntegrityManipulationAttempt(
                    IntegrityManipulationKind.HIDE_FAILURE,
                    IntegritySurface.FEEDBACK,
                    "attempt:hide_correction",
                )
            ),
            evaluate_integrity_attempt(
                IntegrityManipulationAttempt(
                    IntegrityManipulationKind.WEAKEN_VERIFIER,
                    IntegritySurface.VERIFIER_STATE,
                    "attempt:disable_check",
                )
            ),
            evaluate_integrity_attempt(
                IntegrityManipulationAttempt(
                    IntegrityManipulationKind.SHIFT_EVALUATION_WINDOW,
                    IntegritySurface.EVALUATION_WINDOW,
                    "attempt:window_after_failure",
                )
            ),
        ),
        causal_candidate=CausalResponsibilityCandidate(
            candidate_code="responsibility:fan_caused_cooling_candidate",
            coactivation_event_ids=("raw:002", "raw:003"),
            evidence_kinds=(CausalResponsibilityEvidenceKind.COACTIVATION,),
        ),
        ordinary_curriculum=ordinary,
        executive_curriculum=executive,
    )


def _validate_curriculum_sequence(
    expected_kind: NurseryCurriculumKind,
    scenarios: Sequence[NurseryCurriculumScenario],
) -> None:
    _validate_non_empty_sequence(f"{expected_kind.value}_curriculum", scenarios)
    expected_indexes = tuple(range(1, len(scenarios) + 1))
    actual_indexes = tuple(scenario.step_index for scenario in scenarios)
    if actual_indexes != expected_indexes:
        raise ValueError(f"{expected_kind.value} curriculum indexes must be consecutive")
    if any(scenario.curriculum is not expected_kind for scenario in scenarios):
        raise ValueError(f"{expected_kind.value} curriculum contains the wrong kind")


def _validate_index(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_zero_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise ValueError(f"{name} must be zero")


def _validate_unit(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite between zero and one")


def _validate_zero_delta(name: str, value: float) -> None:
    if isinstance(value, bool) or value != 0.0:
        raise ValueError(f"{name} must be zero")


def _validate_non_negative_finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be a non-negative finite number")


def _validate_ascii_code(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty trimmed string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be ASCII") from exc


def _validate_non_empty_ascii_codes(name: str, values: Sequence[str]) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")
    for value in values:
        _validate_ascii_code(name, value)
    if len(tuple(values)) != len(set(values)):
        raise ValueError(f"{name} must contain unique values")


def _validate_sorted_unique_ascii_codes(name: str, values: Sequence[str]) -> None:
    for value in values:
        _validate_ascii_code(name, value)
    if tuple(values) != tuple(sorted(values)):
        raise ValueError(f"{name} must be sorted")
    if len(tuple(values)) != len(set(values)):
        raise ValueError(f"{name} must contain unique values")


def _validate_sorted_unique_enum_values(name: str, values: Sequence[StrEnum]) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")
    string_values = tuple(value.value for value in values)
    if string_values != tuple(sorted(string_values)):
        raise ValueError(f"{name} must be sorted")
    if len(string_values) != len(set(string_values)):
        raise ValueError(f"{name} must contain unique values")


def _validate_non_empty_sequence(name: str, values: Sequence[object]) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")


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
