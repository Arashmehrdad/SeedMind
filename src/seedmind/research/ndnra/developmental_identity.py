"""Stage 0 identity, lifecycle, and schema-separation contracts for NDNRA v0.2."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum

from seedmind.research.ndnra.long_horizon_interference_persistence import (
    LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA,
    LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION,
)
from seedmind.research.ndnra.persistence import BRAIN_SCHEMA, BRAIN_SCHEMA_VERSION
from seedmind.research.ndnra.standalone_acceptance_persistence import (
    STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA,
    STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION,
)

DEVELOPMENTAL_NETWORK_NAMESPACE = "seedmind.ndnra.developmental_network.v0_2"
DEVELOPMENTAL_NETWORK_SCHEMA = "seedmind.ndnra.developmental_network"
DEVELOPMENTAL_NETWORK_SCHEMA_VERSION = 2
DEVELOPMENTAL_TRACE_SCHEMA = "seedmind.ndnra.developmental_trace"
DEVELOPMENTAL_TRACE_SCHEMA_VERSION = 1


class DevelopmentalIdentityKind(StrEnum):
    """Typed v0.2 identities required before the recurrent substrate exists."""

    NEURON = "neuron"
    CONNECTION = "connection"
    REGION = "region"
    EXPERIENCE = "experience"
    COALITION = "coalition"
    NEED_PULSE = "need_pulse"
    CONTEXT_CUE = "context_cue"
    ACTION_PROPOSAL = "action_proposal"
    OUTCOME = "outcome"
    SKILL_BUNDLE = "skill_bundle"
    OPTIONAL_SKILL_STEWARD = "optional_skill_steward"
    REGIONAL_CAPTAIN = "regional_captain"
    DESA_COUNCIL_STATE = "desa_council_state"
    EXECUTIVE_AUDITOR_FINDING = "executive_auditor_finding"
    VALUE_SOURCE = "value_source"
    DESIRED_STATE_AMBITION = "desired_state_ambition"
    CAPABILITY_GAP = "capability_gap"
    VERIFIER = "verifier"
    AUTHORITY_SIGNAL = "authority_signal"
    CAUSAL_RESPONSIBILITY_CANDIDATE = "causal_responsibility_candidate"


class DevelopmentalLifecycleState(StrEnum):
    """Explicit lifecycle states for v0.2 structures."""

    ACTIVE = "active"
    RESTING = "resting"
    DORMANT = "dormant"
    DREAM_ACTIVE = "dream_active"
    PROTECTED = "protected"
    RELEARNING = "relearning"
    INCUBATING_SKILL = "incubating_skill"
    SUPERVISED_SKILL = "supervised_skill"
    MATURE_SKILL = "mature_skill"
    REOPENED_SKILL = "reopened_skill"
    REJECTED_SKILL = "rejected_skill"
    CANDIDATE_AMBITION = "candidate_ambition"
    ACCEPTED_AMBITION = "accepted_ambition"
    PAUSED_AMBITION = "paused_ambition"
    SATISFIED_AMBITION = "satisfied_ambition"
    RETIRED_AMBITION = "retired_ambition"
    CANDIDATE_OUTCOME = "candidate_outcome"
    PENDING_OUTCOME = "pending_outcome"
    UNVERIFIED_OUTCOME = "unverified_outcome"
    PARTIALLY_VERIFIED_OUTCOME = "partially_verified_outcome"
    VERIFIED_OUTCOME = "verified_outcome"
    CONTRADICTED_OUTCOME = "contradicted_outcome"
    FAILED_OUTCOME = "failed_outcome"


@dataclass(frozen=True, slots=True)
class V01AcceptanceBaselineReference:
    """Immutable reference to the closed v0.1 acceptance boundary."""

    closure_code: str = "standalone_ndnra_v0_1_closed_2026_06_29"
    brain_schema: str = BRAIN_SCHEMA
    brain_schema_version: int = BRAIN_SCHEMA_VERSION
    standalone_acceptance_schema: str = STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA
    standalone_acceptance_schema_version: int = STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA_VERSION
    long_horizon_schema: str = LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA
    long_horizon_schema_version: int = LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA_VERSION
    proof_store_mutation_allowed: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("closure_code", self.closure_code)
        for name, schema_name in (
            ("brain_schema", self.brain_schema),
            ("standalone_acceptance_schema", self.standalone_acceptance_schema),
            ("long_horizon_schema", self.long_horizon_schema),
        ):
            _validate_ascii_code(name, schema_name)
            if schema_name in {DEVELOPMENTAL_NETWORK_SCHEMA, DEVELOPMENTAL_TRACE_SCHEMA}:
                raise ValueError("v0.1 schemas cannot equal v0.2 developmental schemas")
        for name, schema_version in (
            ("brain_schema_version", self.brain_schema_version),
            (
                "standalone_acceptance_schema_version",
                self.standalone_acceptance_schema_version,
            ),
            ("long_horizon_schema_version", self.long_horizon_schema_version),
        ):
            _validate_positive_int(name, schema_version)
        if self.proof_store_mutation_allowed:
            raise ValueError("Stage 0 cannot allow v0.1 proof-store mutation")

    @property
    def baseline_id(self) -> str:
        return _identity("v0-1-acceptance-baseline", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"baseline_id": self.baseline_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "closure_code": self.closure_code,
            "brain_schema": self.brain_schema,
            "brain_schema_version": self.brain_schema_version,
            "standalone_acceptance_schema": self.standalone_acceptance_schema,
            "standalone_acceptance_schema_version": self.standalone_acceptance_schema_version,
            "long_horizon_schema": self.long_horizon_schema,
            "long_horizon_schema_version": self.long_horizon_schema_version,
            "proof_store_mutation_allowed": self.proof_store_mutation_allowed,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalSchemaIdentity:
    """v0.2 configuration namespace and schema identity."""

    namespace: str = DEVELOPMENTAL_NETWORK_NAMESPACE
    schema: str = DEVELOPMENTAL_NETWORK_SCHEMA
    schema_version: int = DEVELOPMENTAL_NETWORK_SCHEMA_VERSION
    trace_schema: str = DEVELOPMENTAL_TRACE_SCHEMA
    trace_schema_version: int = DEVELOPMENTAL_TRACE_SCHEMA_VERSION

    def __post_init__(self) -> None:
        for name, value in (
            ("namespace", self.namespace),
            ("schema", self.schema),
            ("trace_schema", self.trace_schema),
        ):
            _validate_ascii_code(name, value)
        if self.namespace != DEVELOPMENTAL_NETWORK_NAMESPACE:
            raise ValueError("developmental namespace must be the v0.2 namespace")
        if self.schema != DEVELOPMENTAL_NETWORK_SCHEMA:
            raise ValueError("developmental schema must use the v0.2 schema")
        if self.trace_schema != DEVELOPMENTAL_TRACE_SCHEMA:
            raise ValueError("developmental trace schema must use the v0.2 trace schema")
        _validate_positive_int("schema_version", self.schema_version)
        _validate_positive_int("trace_schema_version", self.trace_schema_version)
        v01_schemas = {
            BRAIN_SCHEMA,
            STANDALONE_ACCEPTANCE_PERSISTENCE_SCHEMA,
            LONG_HORIZON_INTERFERENCE_PERSISTENCE_SCHEMA,
        }
        if self.schema in v01_schemas or self.trace_schema in v01_schemas:
            raise ValueError("v0.2 developmental schemas cannot reuse v0.1 schema names")

    @property
    def schema_identity_id(self) -> str:
        return _identity("developmental-schema-identity", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"schema_identity_id": self.schema_identity_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "namespace": self.namespace,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "trace_schema": self.trace_schema,
            "trace_schema_version": self.trace_schema_version,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalIdentity:
    """One deterministic typed identity inside the v0.2 namespace."""

    kind: DevelopmentalIdentityKind
    local_code: str
    namespace: str = DEVELOPMENTAL_NETWORK_NAMESPACE

    def __post_init__(self) -> None:
        _validate_ascii_code("local_code", self.local_code)
        _validate_ascii_code("namespace", self.namespace)
        if self.namespace != DEVELOPMENTAL_NETWORK_NAMESPACE:
            raise ValueError("developmental identities must use the v0.2 namespace")

    @property
    def identity_id(self) -> str:
        return _identity("developmental-identity", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"identity_id": self.identity_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "kind": self.kind.value,
            "local_code": self.local_code,
            "namespace": self.namespace,
        }


@dataclass(frozen=True, slots=True)
class StageZeroIdentityCatalog:
    """Finite catalog proving the required v0.2 identity kinds are typed."""

    identities: tuple[DevelopmentalIdentity, ...]

    def __post_init__(self) -> None:
        if not self.identities:
            raise ValueError("Stage 0 identity catalog cannot be empty")
        identity_ids = tuple(identity.identity_id for identity in self.identities)
        if len(identity_ids) != len(set(identity_ids)):
            raise ValueError("developmental identity IDs must be unique")
        kinds = {identity.kind for identity in self.identities}
        if len(kinds) != len(self.identities):
            raise ValueError("identity catalog must contain exactly one identity per kind")
        missing = set(DevelopmentalIdentityKind) - kinds
        if missing:
            raise ValueError(
                f"identity catalog missing kinds: {sorted(item.value for item in missing)}"
            )
        ordered_keys = tuple(
            (identity.kind.value, identity.local_code) for identity in self.identities
        )
        if ordered_keys != tuple(sorted(ordered_keys)):
            raise ValueError("identity catalog must be canonical sorted order")

    @property
    def catalog_id(self) -> str:
        return _identity("stage-zero-identity-catalog", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"catalog_id": self.catalog_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {"identities": [identity.snapshot() for identity in self.identities]}


@dataclass(frozen=True, slots=True)
class DevelopmentalLifecycleTransition:
    """One explicit lifecycle transition with no authority side effects."""

    structure_identity: DevelopmentalIdentity
    from_state: DevelopmentalLifecycleState
    to_state: DevelopmentalLifecycleState
    reason_code: str
    authority_count_delta: int = 0
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("reason_code", self.reason_code)
        if self.to_state not in _ALLOWED_TRANSITIONS[self.from_state]:
            raise ValueError(
                f"invalid lifecycle transition: {self.from_state.value} -> {self.to_state.value}"
            )
        _validate_zero_int("authority_count_delta", self.authority_count_delta)
        if self.has_production_action_authority:
            raise ValueError("lifecycle transitions cannot grant production action authority")

    @property
    def transition_id(self) -> str:
        return _identity("developmental-lifecycle-transition", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"transition_id": self.transition_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "structure_identity": self.structure_identity.snapshot(),
            "from_state": self.from_state.value,
            "to_state": self.to_state.value,
            "reason_code": self.reason_code,
            "authority_count_delta": self.authority_count_delta,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalTraceEvent:
    """One deterministic v0.2 trace event."""

    sequence_index: int
    event_code: str
    subject_identity: DevelopmentalIdentity
    lifecycle_transition: DevelopmentalLifecycleTransition | None = None

    def __post_init__(self) -> None:
        _validate_index("sequence_index", self.sequence_index)
        _validate_ascii_code("event_code", self.event_code)
        if (
            self.lifecycle_transition is not None
            and self.lifecycle_transition.structure_identity.identity_id
            != self.subject_identity.identity_id
        ):
            raise ValueError("trace transition must reference the subject identity")

    @property
    def trace_event_id(self) -> str:
        return _identity("developmental-trace-event", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"trace_event_id": self.trace_event_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "sequence_index": self.sequence_index,
            "event_code": self.event_code,
            "subject_identity": self.subject_identity.snapshot(),
            "lifecycle_transition": (
                None if self.lifecycle_transition is None else self.lifecycle_transition.snapshot()
            ),
        }


@dataclass(frozen=True, slots=True)
class DevelopmentalEvidenceTrace:
    """Finite deterministic evidence trace with no runtime or gateway link."""

    schema_identity: DevelopmentalSchemaIdentity
    events: tuple[DevelopmentalTraceEvent, ...]
    authority_count: int = 0
    runtime_adapter_connected: bool = False
    action_gateway_connected: bool = False
    sqlite_cognition_operation_count: int = 0

    def __post_init__(self) -> None:
        if not self.events:
            raise ValueError("developmental evidence trace requires events")
        indexes = tuple(event.sequence_index for event in self.events)
        if indexes != tuple(range(len(self.events))):
            raise ValueError("trace event indexes must be consecutive")
        event_ids = tuple(event.trace_event_id for event in self.events)
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("trace event identities must be unique")
        _validate_zero_int("authority_count", self.authority_count)
        _validate_zero_int(
            "sqlite_cognition_operation_count",
            self.sqlite_cognition_operation_count,
        )
        if self.runtime_adapter_connected:
            raise ValueError("Stage 0 cannot connect a runtime adapter")
        if self.action_gateway_connected:
            raise ValueError("Stage 0 cannot connect an action gateway")

    @property
    def trace_id(self) -> str:
        return _identity("developmental-evidence-trace", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"trace_id": self.trace_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "schema_identity": self.schema_identity.snapshot(),
            "events": [event.snapshot() for event in self.events],
            "authority_count": self.authority_count,
            "runtime_adapter_connected": self.runtime_adapter_connected,
            "action_gateway_connected": self.action_gateway_connected,
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
        }


@dataclass(frozen=True, slots=True)
class StageZeroContractEvidence:
    """Integrated Stage 0 pass-gate evidence."""

    baseline: V01AcceptanceBaselineReference
    schema_identity: DevelopmentalSchemaIdentity
    identity_catalog: StageZeroIdentityCatalog
    lifecycle_transitions: tuple[DevelopmentalLifecycleTransition, ...]
    evidence_trace: DevelopmentalEvidenceTrace
    production_action_authority_violations: int = 0

    def __post_init__(self) -> None:
        if not self.lifecycle_transitions:
            raise ValueError("Stage 0 evidence requires lifecycle transitions")
        transition_ids = tuple(
            transition.transition_id for transition in self.lifecycle_transitions
        )
        if len(transition_ids) != len(set(transition_ids)):
            raise ValueError("Stage 0 lifecycle transition IDs must be unique")
        if (
            self.evidence_trace.schema_identity.schema_identity_id
            != self.schema_identity.schema_identity_id
        ):
            raise ValueError("trace schema identity must match Stage 0 schema identity")
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage 0 pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-zero-contract-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        """Return Stage 0 pass-gate results."""

        v01_schemas = {
            self.baseline.brain_schema,
            self.baseline.standalone_acceptance_schema,
            self.baseline.long_horizon_schema,
        }
        return {
            "v0_1_baseline_referenced_without_mutation": (
                self.baseline.closure_code == "standalone_ndnra_v0_1_closed_2026_06_29"
                and not self.baseline.proof_store_mutation_allowed
            ),
            "v0_2_schema_separate_from_v0_1": (
                self.schema_identity.schema not in v01_schemas
                and self.schema_identity.trace_schema not in v01_schemas
                and self.schema_identity.namespace == DEVELOPMENTAL_NETWORK_NAMESPACE
            ),
            "all_required_identity_kinds_present": (
                {identity.kind for identity in self.identity_catalog.identities}
                == set(DevelopmentalIdentityKind)
            ),
            "identities_and_transitions_serialize_deterministically": (
                self.identity_catalog.snapshot_json_ascii()
                == self.identity_catalog.snapshot_json_ascii()
                and all(
                    transition.snapshot_json_ascii() == transition.snapshot_json_ascii()
                    for transition in self.lifecycle_transitions
                )
                and self.evidence_trace.snapshot_json_ascii()
                == self.evidence_trace.snapshot_json_ascii()
            ),
            "runtime_adapter_and_action_gateway_absent": (
                not self.evidence_trace.runtime_adapter_connected
                and not self.evidence_trace.action_gateway_connected
            ),
            "authority_count_zero": (
                self.evidence_trace.authority_count == 0
                and self.production_action_authority_violations == 0
            ),
        }

    def completion_matrix(self) -> dict[str, str]:
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
            "baseline": self.baseline.snapshot(),
            "schema_identity": self.schema_identity.snapshot(),
            "identity_catalog": self.identity_catalog.snapshot(),
            "lifecycle_transitions": [
                transition.snapshot() for transition in self.lifecycle_transitions
            ],
            "evidence_trace": self.evidence_trace.snapshot(),
            "production_action_authority_violations": (self.production_action_authority_violations),
        }


def make_developmental_identity(
    kind: DevelopmentalIdentityKind,
    local_code: str,
) -> DevelopmentalIdentity:
    """Construct one v0.2 developmental identity."""

    return DevelopmentalIdentity(kind=kind, local_code=local_code)


def default_stage_zero_identity_catalog() -> StageZeroIdentityCatalog:
    """Return one canonical identity for every required Stage 0 kind."""

    return StageZeroIdentityCatalog(
        identities=tuple(
            make_developmental_identity(kind, f"stage0:{kind.value}")
            for kind in sorted(DevelopmentalIdentityKind, key=lambda item: item.value)
        )
    )


def run_stage_zero_contract_acceptance() -> StageZeroContractEvidence:
    """Build deterministic Stage 0 contract acceptance evidence."""

    schema_identity = DevelopmentalSchemaIdentity()
    catalog = default_stage_zero_identity_catalog()
    identity_by_kind = {identity.kind: identity for identity in catalog.identities}
    neuron_identity = identity_by_kind[DevelopmentalIdentityKind.NEURON]
    skill_identity = identity_by_kind[DevelopmentalIdentityKind.SKILL_BUNDLE]
    ambition_identity = identity_by_kind[DevelopmentalIdentityKind.DESIRED_STATE_AMBITION]
    outcome_identity = identity_by_kind[DevelopmentalIdentityKind.OUTCOME]
    transitions = (
        DevelopmentalLifecycleTransition(
            structure_identity=neuron_identity,
            from_state=DevelopmentalLifecycleState.ACTIVE,
            to_state=DevelopmentalLifecycleState.RESTING,
            reason_code="stage0:bounded_rest",
        ),
        DevelopmentalLifecycleTransition(
            structure_identity=skill_identity,
            from_state=DevelopmentalLifecycleState.INCUBATING_SKILL,
            to_state=DevelopmentalLifecycleState.SUPERVISED_SKILL,
            reason_code="stage0:grounded_feedback_available",
        ),
        DevelopmentalLifecycleTransition(
            structure_identity=ambition_identity,
            from_state=DevelopmentalLifecycleState.CANDIDATE_AMBITION,
            to_state=DevelopmentalLifecycleState.ACCEPTED_AMBITION,
            reason_code="stage0:accepted_value_source",
        ),
        DevelopmentalLifecycleTransition(
            structure_identity=outcome_identity,
            from_state=DevelopmentalLifecycleState.CANDIDATE_OUTCOME,
            to_state=DevelopmentalLifecycleState.PENDING_OUTCOME,
            reason_code="stage0:awaiting_feedback",
        ),
    )
    trace = DevelopmentalEvidenceTrace(
        schema_identity=schema_identity,
        events=tuple(
            DevelopmentalTraceEvent(
                sequence_index=index,
                event_code=f"stage0:transition:{index}",
                subject_identity=transition.structure_identity,
                lifecycle_transition=transition,
            )
            for index, transition in enumerate(transitions)
        ),
    )
    return StageZeroContractEvidence(
        baseline=V01AcceptanceBaselineReference(),
        schema_identity=schema_identity,
        identity_catalog=catalog,
        lifecycle_transitions=transitions,
        evidence_trace=trace,
    )


_ALLOWED_TRANSITIONS: Mapping[
    DevelopmentalLifecycleState,
    frozenset[DevelopmentalLifecycleState],
] = {
    DevelopmentalLifecycleState.ACTIVE: frozenset(
        {
            DevelopmentalLifecycleState.RESTING,
            DevelopmentalLifecycleState.DORMANT,
            DevelopmentalLifecycleState.PROTECTED,
            DevelopmentalLifecycleState.RELEARNING,
        }
    ),
    DevelopmentalLifecycleState.RESTING: frozenset(
        {DevelopmentalLifecycleState.ACTIVE, DevelopmentalLifecycleState.DORMANT}
    ),
    DevelopmentalLifecycleState.DORMANT: frozenset(
        {
            DevelopmentalLifecycleState.RESTING,
            DevelopmentalLifecycleState.DREAM_ACTIVE,
            DevelopmentalLifecycleState.RELEARNING,
        }
    ),
    DevelopmentalLifecycleState.DREAM_ACTIVE: frozenset(
        {DevelopmentalLifecycleState.DORMANT, DevelopmentalLifecycleState.RESTING}
    ),
    DevelopmentalLifecycleState.PROTECTED: frozenset(
        {DevelopmentalLifecycleState.ACTIVE, DevelopmentalLifecycleState.RESTING}
    ),
    DevelopmentalLifecycleState.RELEARNING: frozenset(
        {DevelopmentalLifecycleState.ACTIVE, DevelopmentalLifecycleState.RESTING}
    ),
    DevelopmentalLifecycleState.INCUBATING_SKILL: frozenset(
        {
            DevelopmentalLifecycleState.SUPERVISED_SKILL,
            DevelopmentalLifecycleState.REJECTED_SKILL,
        }
    ),
    DevelopmentalLifecycleState.SUPERVISED_SKILL: frozenset(
        {
            DevelopmentalLifecycleState.MATURE_SKILL,
            DevelopmentalLifecycleState.REOPENED_SKILL,
            DevelopmentalLifecycleState.REJECTED_SKILL,
        }
    ),
    DevelopmentalLifecycleState.MATURE_SKILL: frozenset(
        {DevelopmentalLifecycleState.REOPENED_SKILL, DevelopmentalLifecycleState.RESTING}
    ),
    DevelopmentalLifecycleState.REOPENED_SKILL: frozenset(
        {
            DevelopmentalLifecycleState.SUPERVISED_SKILL,
            DevelopmentalLifecycleState.REJECTED_SKILL,
        }
    ),
    DevelopmentalLifecycleState.REJECTED_SKILL: frozenset(),
    DevelopmentalLifecycleState.CANDIDATE_AMBITION: frozenset(
        {
            DevelopmentalLifecycleState.ACCEPTED_AMBITION,
            DevelopmentalLifecycleState.RETIRED_AMBITION,
        }
    ),
    DevelopmentalLifecycleState.ACCEPTED_AMBITION: frozenset(
        {
            DevelopmentalLifecycleState.PAUSED_AMBITION,
            DevelopmentalLifecycleState.SATISFIED_AMBITION,
            DevelopmentalLifecycleState.RETIRED_AMBITION,
        }
    ),
    DevelopmentalLifecycleState.PAUSED_AMBITION: frozenset(
        {
            DevelopmentalLifecycleState.ACCEPTED_AMBITION,
            DevelopmentalLifecycleState.RETIRED_AMBITION,
        }
    ),
    DevelopmentalLifecycleState.SATISFIED_AMBITION: frozenset(
        {DevelopmentalLifecycleState.RETIRED_AMBITION}
    ),
    DevelopmentalLifecycleState.RETIRED_AMBITION: frozenset(),
    DevelopmentalLifecycleState.CANDIDATE_OUTCOME: frozenset(
        {
            DevelopmentalLifecycleState.PENDING_OUTCOME,
            DevelopmentalLifecycleState.UNVERIFIED_OUTCOME,
        }
    ),
    DevelopmentalLifecycleState.PENDING_OUTCOME: frozenset(
        {
            DevelopmentalLifecycleState.UNVERIFIED_OUTCOME,
            DevelopmentalLifecycleState.PARTIALLY_VERIFIED_OUTCOME,
            DevelopmentalLifecycleState.VERIFIED_OUTCOME,
            DevelopmentalLifecycleState.FAILED_OUTCOME,
        }
    ),
    DevelopmentalLifecycleState.UNVERIFIED_OUTCOME: frozenset(
        {
            DevelopmentalLifecycleState.PARTIALLY_VERIFIED_OUTCOME,
            DevelopmentalLifecycleState.VERIFIED_OUTCOME,
            DevelopmentalLifecycleState.CONTRADICTED_OUTCOME,
            DevelopmentalLifecycleState.FAILED_OUTCOME,
        }
    ),
    DevelopmentalLifecycleState.PARTIALLY_VERIFIED_OUTCOME: frozenset(
        {
            DevelopmentalLifecycleState.VERIFIED_OUTCOME,
            DevelopmentalLifecycleState.CONTRADICTED_OUTCOME,
            DevelopmentalLifecycleState.FAILED_OUTCOME,
        }
    ),
    DevelopmentalLifecycleState.VERIFIED_OUTCOME: frozenset(),
    DevelopmentalLifecycleState.CONTRADICTED_OUTCOME: frozenset(
        {
            DevelopmentalLifecycleState.UNVERIFIED_OUTCOME,
            DevelopmentalLifecycleState.FAILED_OUTCOME,
        }
    ),
    DevelopmentalLifecycleState.FAILED_OUTCOME: frozenset(),
}


def _validate_index(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_zero_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise ValueError(f"{name} must be zero")


def _validate_ascii_code(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty trimmed string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be ASCII") from exc


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
