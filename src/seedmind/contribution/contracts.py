"""Typed contracts for the main-project Week 9 human contribution slice."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from enum import StrEnum

from seedmind.human.contracts import HumanRequest, SupportLevel

CONTRIBUTION_SCHEMA_VERSION = 1
PERSISTENCE_SCHEMA_VERSION = 1


class CapabilityStatus(StrEnum):
    """Inspectable availability state for a requested capability."""

    UNAVAILABLE = "unavailable"
    UNPROVEN = "unproven"
    DEGRADED = "degraded"
    CONTEXT_MISMATCHED = "context_mismatched"
    VERIFIED = "verified"


class VerificationEvidenceSource(StrEnum):
    """Evidence classes considered during grounded outcome verification."""

    RUNTIME_STATE = "runtime_state"
    ACTUAL_TRANSITION = "actual_transition"
    SELF_REPORT = "self_report"
    PRODUCER_VERIFIER_AGREEMENT = "producer_verifier_agreement"
    NDNRA_AGREEMENT = "ndnra_agreement"
    IMAGINATION = "imagination"
    UNAVAILABLE = "unavailable"


class VerificationStatus(StrEnum):
    """Outcome-verification result for one contribution attempt."""

    VERIFIED = "verified"
    REJECTED = "rejected"
    UNAVAILABLE = "unavailable"


class HumanAuthorityInterruption(StrEnum):
    """Authoritative human interruptions that stop contribution immediately."""

    STOP = "stop"
    DENIAL = "denial"
    CORRECTION = "correction"
    CLARIFICATION = "clarification"
    PERMISSION = "permission"


@dataclass(frozen=True, slots=True)
class HumanContributionRequest:
    """Typed Week 9 human request bound to one frozen skill target."""

    human_request: HumanRequest
    target_capability: str
    expected_outcome: str
    target_object_id: str
    target_id: str
    learned_context: tuple[str, ...]
    requested_support_level: SupportLevel

    def __post_init__(self) -> None:
        for name, value in (
            ("target_capability", self.target_capability),
            ("expected_outcome", self.expected_outcome),
            ("target_object_id", self.target_object_id),
            ("target_id", self.target_id),
        ):
            if not value.strip() or not value.isascii():
                raise ValueError(f"{name} must be non-empty ASCII")
        if not self.learned_context:
            raise ValueError("learned_context must not be empty")
        if any(not item.strip() or not item.isascii() for item in self.learned_context):
            raise ValueError("learned_context entries must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        request = self.human_request
        return {
            "expected_outcome": self.expected_outcome,
            "human_request": {
                "ambiguity": request.ambiguity,
                "intent_code": request.intent_code.value,
                "permission_level": request.permission_level,
                "request_id": request.request_id,
                "target_code": request.target_code,
                "verification_rule": request.verification_rule.value,
            },
            "learned_context": list(self.learned_context),
            "requested_support_level": int(self.requested_support_level),
            "target_capability": self.target_capability,
            "target_id": self.target_id,
            "target_object_id": self.target_object_id,
        }


@dataclass(frozen=True, slots=True)
class CapabilityCheck:
    """Frozen-skill capability inspection before any contribution attempt."""

    status: CapabilityStatus
    target_capability: str
    checked_skill_id: str | None
    expected_outcome_matched: bool
    target_object_matched: bool
    target_matched: bool
    learned_context_matched: bool
    reason_codes: tuple[str, ...]
    failed_preconditions: tuple[str, ...]

    def __post_init__(self) -> None:
        if not self.target_capability.strip() or not self.target_capability.isascii():
            raise ValueError("target_capability must be non-empty ASCII")
        if self.checked_skill_id is not None and (
            not self.checked_skill_id.strip() or not self.checked_skill_id.isascii()
        ):
            raise ValueError("checked_skill_id must be ASCII when provided")
        if not self.reason_codes:
            raise ValueError("reason_codes must not be empty")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "checked_skill_id": self.checked_skill_id,
            "expected_outcome_matched": self.expected_outcome_matched,
            "failed_preconditions": list(self.failed_preconditions),
            "learned_context_matched": self.learned_context_matched,
            "reason_codes": list(self.reason_codes),
            "status": self.status.value,
            "target_capability": self.target_capability,
            "target_matched": self.target_matched,
            "target_object_matched": self.target_object_matched,
        }


@dataclass(frozen=True, slots=True)
class CapabilityEvidence:
    """One inspectable support-evaluation evidence record."""

    contribution_id: str
    familiar_context: bool
    independent_execution: bool
    success: bool
    verification_status: VerificationStatus
    evidence_fresh: bool
    contradictory: bool
    degraded: bool
    unsafe: bool
    context_mismatched: bool
    scenario_context: str

    def __post_init__(self) -> None:
        for name, value in (
            ("contribution_id", self.contribution_id),
            ("scenario_context", self.scenario_context),
        ):
            if not value.strip() or not value.isascii():
                raise ValueError(f"{name} must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "context_mismatched": self.context_mismatched,
            "contradictory": self.contradictory,
            "contribution_id": self.contribution_id,
            "degraded": self.degraded,
            "evidence_fresh": self.evidence_fresh,
            "familiar_context": self.familiar_context,
            "independent_execution": self.independent_execution,
            "scenario_context": self.scenario_context,
            "success": self.success,
            "unsafe": self.unsafe,
            "verification_status": self.verification_status.value,
        }

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> CapabilityEvidence:
        """Load one evidence record from a strict JSON payload."""
        return cls(
            contribution_id=_require_str(payload, "contribution_id"),
            familiar_context=_require_bool(payload, "familiar_context"),
            independent_execution=_require_bool(payload, "independent_execution"),
            success=_require_bool(payload, "success"),
            verification_status=VerificationStatus(_require_str(payload, "verification_status")),
            evidence_fresh=_require_bool(payload, "evidence_fresh"),
            contradictory=_require_bool(payload, "contradictory"),
            degraded=_require_bool(payload, "degraded"),
            unsafe=_require_bool(payload, "unsafe"),
            context_mismatched=_require_bool(payload, "context_mismatched"),
            scenario_context=_require_str(payload, "scenario_context"),
        )


@dataclass(frozen=True, slots=True)
class GroundedOutcomeVerification:
    """Inspectably grounded contribution outcome verification."""

    status: VerificationStatus
    evidence_sources: tuple[VerificationEvidenceSource, ...]
    reason_code: str
    target_achieved: bool

    def __post_init__(self) -> None:
        if not self.evidence_sources:
            raise ValueError("evidence_sources must not be empty")
        if not self.reason_code.strip() or not self.reason_code.isascii():
            raise ValueError("reason_code must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "evidence_sources": [source.value for source in self.evidence_sources],
            "reason_code": self.reason_code,
            "status": self.status.value,
            "target_achieved": self.target_achieved,
        }


@dataclass(frozen=True, slots=True)
class ContributionShadowAudit:
    """Inspectable shadow audit for Week 9 contribution authority boundaries."""

    observations: int = 0
    suggestions: int = 0
    disagreements: int = 0
    comparisons: int = 0
    production_actions_retained: int = 0
    production_action_replacements: int = 0
    authority_violations: int = 0
    verification_authority_violations: int = 0
    support_authority_violations: int = 0
    automatic_promotions: int = 0

    def __post_init__(self) -> None:
        if any(value < 0 for value in asdict(self).values()):
            raise ValueError("audit counters must not be negative")

    @property
    def accepted(self) -> bool:
        """Return whether the audit satisfies the Week 9 authority boundary."""
        return (
            self.production_action_replacements == 0
            and self.authority_violations == 0
            and self.verification_authority_violations == 0
            and self.support_authority_violations == 0
            and self.automatic_promotions == 0
        )

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return asdict(self)


@dataclass(frozen=True, slots=True)
class HonestFailureReport:
    """Explicit honest failure payload for rejected or unsuccessful attempts."""

    reason: str
    attempted_capability: str
    failed_preconditions: tuple[str, ...]
    interruption: HumanAuthorityInterruption | None
    uncertainty: str
    requested_support: SupportLevel
    verification_status: VerificationStatus
    authority_audit: ContributionShadowAudit

    def __post_init__(self) -> None:
        for name, value in (
            ("reason", self.reason),
            ("attempted_capability", self.attempted_capability),
            ("uncertainty", self.uncertainty),
        ):
            if not value.strip() or not value.isascii():
                raise ValueError(f"{name} must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "attempted_capability": self.attempted_capability,
            "authority_audit": self.authority_audit.to_json(),
            "failed_preconditions": list(self.failed_preconditions),
            "interruption": None if self.interruption is None else self.interruption.value,
            "reason": self.reason,
            "requested_support": int(self.requested_support),
            "uncertainty": self.uncertainty,
            "verification_status": self.verification_status.value,
        }


@dataclass(frozen=True, slots=True)
class ContributionRecord:
    """Complete inspectable Week 9 contribution attempt record."""

    contribution_id: str
    request: HumanContributionRequest
    scenario_id: str
    scenario_context: str
    seed: int
    attempted_capability: str
    support_level_before: SupportLevel
    support_level_after: SupportLevel
    requested_support: SupportLevel
    capability_check: CapabilityCheck
    verification: GroundedOutcomeVerification
    success: bool
    independent_execution: bool
    familiar_context: bool
    executed_steps: int
    retained_steps: int
    interruption: HumanAuthorityInterruption | None
    authority_audit: ContributionShadowAudit
    failure_report: HonestFailureReport | None
    evidence: CapabilityEvidence
    action_trace: tuple[str, ...]
    outcome_trace: tuple[str, ...]

    def __post_init__(self) -> None:
        for name, value in (
            ("contribution_id", self.contribution_id),
            ("scenario_id", self.scenario_id),
            ("scenario_context", self.scenario_context),
            ("attempted_capability", self.attempted_capability),
        ):
            if not value.strip() or not value.isascii():
                raise ValueError(f"{name} must be non-empty ASCII")
        if self.seed < 0 or self.executed_steps < 0 or self.retained_steps < 0:
            raise ValueError("seed and step counters must not be negative")
        if self.retained_steps > self.executed_steps:
            raise ValueError("retained_steps cannot exceed executed_steps")
        if len(self.action_trace) != len(self.outcome_trace):
            raise ValueError("action and outcome traces must have equal length")
        if self.success and self.failure_report is not None:
            raise ValueError("successful records cannot carry a failure report")
        if not self.success and self.failure_report is None:
            raise ValueError("unsuccessful records require a failure report")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "action_trace": list(self.action_trace),
            "attempted_capability": self.attempted_capability,
            "authority_audit": self.authority_audit.to_json(),
            "capability_check": self.capability_check.to_json(),
            "contribution_id": self.contribution_id,
            "evidence": self.evidence.to_json(),
            "executed_steps": self.executed_steps,
            "failure_report": None
            if self.failure_report is None
            else self.failure_report.to_json(),
            "familiar_context": self.familiar_context,
            "independent_execution": self.independent_execution,
            "interruption": None if self.interruption is None else self.interruption.value,
            "outcome_trace": list(self.outcome_trace),
            "request": self.request.to_json(),
            "requested_support": int(self.requested_support),
            "retained_steps": self.retained_steps,
            "scenario_context": self.scenario_context,
            "scenario_id": self.scenario_id,
            "seed": self.seed,
            "success": self.success,
            "support_level_after": int(self.support_level_after),
            "support_level_before": int(self.support_level_before),
            "verification": self.verification.to_json(),
        }


@dataclass(frozen=True, slots=True)
class SupportPolicy:
    """Declared Week 9 support-reduction policy defaults."""

    minimum_verified_independent_familiar_successes: int = 5
    minimum_success_rate: float = 0.80
    minimum_distinct_scenario_contexts: int = 3
    recent_evidence_window: int = 12
    grounded_failures_to_restore_dependent: int = 2

    def __post_init__(self) -> None:
        if self.minimum_verified_independent_familiar_successes < 5:
            raise ValueError("minimum successes must be at least five")
        if self.minimum_success_rate < 0.80 or self.minimum_success_rate > 1.0:
            raise ValueError("minimum_success_rate must be between 0.80 and 1.0")
        if self.minimum_distinct_scenario_contexts < 3:
            raise ValueError("minimum distinct scenario contexts must be at least three")
        if self.recent_evidence_window <= 0:
            raise ValueError("recent_evidence_window must be positive")
        if self.grounded_failures_to_restore_dependent != 2:
            raise ValueError("grounded_failures_to_restore_dependent must equal two")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "grounded_failures_to_restore_dependent": (self.grounded_failures_to_restore_dependent),
            "minimum_distinct_scenario_contexts": self.minimum_distinct_scenario_contexts,
            "minimum_success_rate": self.minimum_success_rate,
            "minimum_verified_independent_familiar_successes": (
                self.minimum_verified_independent_familiar_successes
            ),
            "recent_evidence_window": self.recent_evidence_window,
        }


@dataclass(frozen=True, slots=True)
class SupportEvaluation:
    """Inspectable result of evaluating support-state transitions."""

    previous_level: SupportLevel
    next_level: SupportLevel
    blocker_codes: tuple[str, ...]
    recent_verified_independent_familiar_successes: int
    recent_success_rate: float
    distinct_scenario_contexts: int
    recent_grounded_familiar_failures: int

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "blocker_codes": list(self.blocker_codes),
            "distinct_scenario_contexts": self.distinct_scenario_contexts,
            "next_level": int(self.next_level),
            "previous_level": int(self.previous_level),
            "recent_grounded_familiar_failures": self.recent_grounded_familiar_failures,
            "recent_success_rate": self.recent_success_rate,
            "recent_verified_independent_familiar_successes": (
                self.recent_verified_independent_familiar_successes
            ),
        }


@dataclass(frozen=True, slots=True)
class SupportState:
    """Persisted Week 9 support state."""

    current_level: SupportLevel
    policy: SupportPolicy
    history: tuple[CapabilityEvidence, ...]
    promotion_evidence_start_index: int
    last_evaluation: SupportEvaluation

    def __post_init__(self) -> None:
        if not 0 <= self.promotion_evidence_start_index <= len(self.history):
            raise ValueError("promotion_evidence_start_index must reference support history")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "current_level": int(self.current_level),
            "history": [item.to_json() for item in self.history],
            "last_evaluation": self.last_evaluation.to_json(),
            "policy": self.policy.to_json(),
            "promotion_evidence_start_index": self.promotion_evidence_start_index,
        }

    @classmethod
    def fresh(cls, policy: SupportPolicy | None = None) -> SupportState:
        """Return the conservative default support state."""
        resolved_policy = policy or SupportPolicy()
        evaluation = SupportEvaluation(
            previous_level=SupportLevel.DEPENDENT,
            next_level=SupportLevel.DEPENDENT,
            blocker_codes=("fresh_dependent_fallback",),
            recent_verified_independent_familiar_successes=0,
            recent_success_rate=0.0,
            distinct_scenario_contexts=0,
            recent_grounded_familiar_failures=0,
        )
        return cls(
            current_level=SupportLevel.DEPENDENT,
            policy=resolved_policy,
            history=(),
            promotion_evidence_start_index=0,
            last_evaluation=evaluation,
        )


@dataclass(frozen=True, slots=True)
class PersistedEnvelope:
    """Strict checksum-protected ASCII JSON envelope."""

    schema_version: int
    payload_type: str
    payload: dict[str, object]
    checksum: str

    def __post_init__(self) -> None:
        if self.schema_version != PERSISTENCE_SCHEMA_VERSION:
            raise ValueError("unsupported persistence schema version")
        if not self.payload_type.strip() or not self.payload_type.isascii():
            raise ValueError("payload_type must be non-empty ASCII")
        if self.checksum != calculate_checksum(self.payload):
            raise ValueError("checksum does not match payload")

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "checksum": self.checksum,
            "payload": self.payload,
            "payload_type": self.payload_type,
            "schema_version": self.schema_version,
        }

    @classmethod
    def build(cls, *, payload_type: str, payload: dict[str, object]) -> PersistedEnvelope:
        """Build a checksum-protected persistence envelope."""
        return cls(
            schema_version=PERSISTENCE_SCHEMA_VERSION,
            payload_type=payload_type,
            payload=payload,
            checksum=calculate_checksum(payload),
        )

    @classmethod
    def from_json(cls, payload: dict[str, object]) -> PersistedEnvelope:
        """Load one strict persistence envelope."""
        return cls(
            schema_version=_require_int(payload, "schema_version"),
            payload_type=_require_str(payload, "payload_type"),
            payload=_require_object(payload, "payload"),
            checksum=_require_str(payload, "checksum"),
        )


def calculate_checksum(payload: dict[str, object]) -> str:
    """Return a deterministic checksum for one ASCII JSON payload."""
    serialized = json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(serialized.encode("ascii")).hexdigest()


def _require_bool(payload: dict[str, object], key: str) -> bool:
    value = payload[key]
    if not isinstance(value, bool):
        raise TypeError(f"{key} must be a bool")
    return value


def _require_int(payload: dict[str, object], key: str) -> int:
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} must be an int")
    return value


def _require_object(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload[key]
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be an object")
    if any(not isinstance(item_key, str) for item_key in value):
        raise TypeError(f"{key} must have string keys")
    return value


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value
