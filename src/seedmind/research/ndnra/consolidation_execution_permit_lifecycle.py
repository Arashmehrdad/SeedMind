"""Immutable lifecycle state for human-approved NDNRA execution permits."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from seedmind.research.ndnra.consolidation_execution_approval import (
    ConsolidationExecutionPermit,
)


class ConsolidationExecutionPermitLifecycleAction(StrEnum):
    """Explicit caller-supplied transition for one issued execution permit."""

    CANCEL = "cancel"
    EXPIRE = "expire"
    CONSUME = "consume"


class ConsolidationExecutionPermitLifecycleStatus(StrEnum):
    """Current state of one immutable execution-permit lifecycle."""

    ISSUED = "issued"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    CONSUMED = "consumed"


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionPermitTransitionRequest:
    """One explicit transition request over one exact permit identity."""

    target_permit_id: str
    expected_proposal_id: str
    expected_candidate_id: str
    action: ConsolidationExecutionPermitLifecycleAction
    decision_episode: int
    actor_code: str
    reason_code: str
    consumption_reference_code: str | None = None

    def __post_init__(self) -> None:
        _validate_code("target_permit_id", self.target_permit_id)
        _validate_code("expected_proposal_id", self.expected_proposal_id)
        _validate_code("expected_candidate_id", self.expected_candidate_id)
        _validate_nonnegative_int("decision_episode", self.decision_episode)
        _validate_code("actor_code", self.actor_code)
        _validate_code("reason_code", self.reason_code)
        if self.action is ConsolidationExecutionPermitLifecycleAction.CONSUME:
            if self.consumption_reference_code is None:
                raise ValueError("consume transition requires consumption_reference_code")
            _validate_code(
                "consumption_reference_code",
                self.consumption_reference_code,
            )
        elif self.consumption_reference_code is not None:
            raise ValueError("only consume transition may include a consumption reference")


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionPermitTransitionDecision:
    """Immutable terminal permit transition with no application authority."""

    decision_id: str
    permit: ConsolidationExecutionPermit
    action: ConsolidationExecutionPermitLifecycleAction
    status: ConsolidationExecutionPermitLifecycleStatus
    decision_episode: int
    actor_code: str
    reason_code: str
    consumption_reference_code: str | None = None
    has_application_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("decision_id", self.decision_id)
        _validate_nonnegative_int("decision_episode", self.decision_episode)
        _validate_code("actor_code", self.actor_code)
        _validate_code("reason_code", self.reason_code)
        if self.status is not _status_for(self.action):
            raise ValueError("permit lifecycle action and status are inconsistent")
        _validate_transition_episode(
            permit=self.permit,
            action=self.action,
            decision_episode=self.decision_episode,
        )
        if self.action is ConsolidationExecutionPermitLifecycleAction.CONSUME:
            if self.consumption_reference_code is None:
                raise ValueError("consumed permit requires a consumption reference")
            _validate_code(
                "consumption_reference_code",
                self.consumption_reference_code,
            )
        elif self.consumption_reference_code is not None:
            raise ValueError("only consumed permit may include a consumption reference")
        if self.has_application_authority:
            raise ValueError("permit lifecycle decisions cannot apply consolidation")
        expected_id = _transition_decision_id(
            permit=self.permit,
            action=self.action,
            decision_episode=self.decision_episode,
            actor_code=self.actor_code,
            reason_code=self.reason_code,
            consumption_reference_code=self.consumption_reference_code,
        )
        if self.decision_id != expected_id:
            raise ValueError("permit lifecycle decision identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe transition evidence."""
        return {
            "decision_id": self.decision_id,
            "permit": self.permit.snapshot(),
            "action": self.action.value,
            "status": self.status.value,
            "decision_episode": self.decision_episode,
            "actor_code": self.actor_code,
            "reason_code": self.reason_code,
            "consumption_reference_code": self.consumption_reference_code,
            "has_application_authority": self.has_application_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionPermitLifecycleRecord:
    """One issued permit plus at most one immutable terminal transition."""

    permit: ConsolidationExecutionPermit
    status: ConsolidationExecutionPermitLifecycleStatus = (
        ConsolidationExecutionPermitLifecycleStatus.ISSUED
    )
    decisions: tuple[ConsolidationExecutionPermitTransitionDecision, ...] = ()
    has_application_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_application_authority:
            raise ValueError("permit lifecycle records cannot apply consolidation")
        if len(self.decisions) > 1:
            raise ValueError("permit lifecycle permits only one terminal transition")
        decision_ids = tuple(decision.decision_id for decision in self.decisions)
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("permit lifecycle decision identities must be unique")
        if not self.decisions:
            if self.status is not ConsolidationExecutionPermitLifecycleStatus.ISSUED:
                raise ValueError("empty permit history must remain issued")
            return
        decision = self.decisions[0]
        if decision.permit != self.permit:
            raise ValueError("permit lifecycle decision targets a different permit")
        if self.status is not decision.status:
            raise ValueError("permit lifecycle status must match terminal decision")
        if self.status is ConsolidationExecutionPermitLifecycleStatus.ISSUED:
            raise ValueError("issued status cannot contain terminal decisions")

    @classmethod
    def issued(
        cls,
        permit: ConsolidationExecutionPermit,
    ) -> ConsolidationExecutionPermitLifecycleRecord:
        """Create an immutable issued lifecycle for one permit."""
        return cls(permit=permit)

    @property
    def is_terminal(self) -> bool:
        """Return whether cancellation, expiry, or consumption has occurred."""
        return self.status is not ConsolidationExecutionPermitLifecycleStatus.ISSUED

    @property
    def consumption_count(self) -> int:
        """Return one only for a consumed terminal record."""
        return int(self.status is ConsolidationExecutionPermitLifecycleStatus.CONSUMED)

    def transition(
        self,
        request: ConsolidationExecutionPermitTransitionRequest,
    ) -> ConsolidationExecutionPermitLifecycleRecord:
        """Return a new terminal record while preserving this issued record."""
        if self.is_terminal:
            raise ValueError("permit lifecycle is already terminal")
        proposal = self.permit.proposal
        if request.target_permit_id != self.permit.permit_id:
            raise ValueError("transition request targets a different permit")
        if request.expected_proposal_id != proposal.proposal_id:
            raise ValueError("transition request targets a different proposal")
        if request.expected_candidate_id != proposal.candidate.candidate_id:
            raise ValueError("transition request targets a different candidate")
        _validate_transition_episode(
            permit=self.permit,
            action=request.action,
            decision_episode=request.decision_episode,
        )
        decision = ConsolidationExecutionPermitTransitionDecision(
            decision_id=_transition_decision_id(
                permit=self.permit,
                action=request.action,
                decision_episode=request.decision_episode,
                actor_code=request.actor_code,
                reason_code=request.reason_code,
                consumption_reference_code=request.consumption_reference_code,
            ),
            permit=self.permit,
            action=request.action,
            status=_status_for(request.action),
            decision_episode=request.decision_episode,
            actor_code=request.actor_code,
            reason_code=request.reason_code,
            consumption_reference_code=request.consumption_reference_code,
        )
        return ConsolidationExecutionPermitLifecycleRecord(
            permit=self.permit,
            status=decision.status,
            decisions=(decision,),
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic lifecycle evidence."""
        return {
            "permit": self.permit.snapshot(),
            "status": self.status.value,
            "decisions": [decision.snapshot() for decision in self.decisions],
            "is_terminal": self.is_terminal,
            "consumption_count": self.consumption_count,
            "has_application_authority": self.has_application_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionPermitLifecycleRegistry:
    """Immutable collection with one lifecycle record per permit identity."""

    records: tuple[ConsolidationExecutionPermitLifecycleRecord, ...] = ()
    has_application_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_application_authority:
            raise ValueError("permit lifecycle registry cannot apply consolidation")
        permit_ids = tuple(record.permit.permit_id for record in self.records)
        if len(permit_ids) != len(set(permit_ids)):
            raise ValueError("permit lifecycle registry identities must be unique")

    def add(
        self,
        permit: ConsolidationExecutionPermit,
    ) -> ConsolidationExecutionPermitLifecycleRegistry:
        """Add one issued permit without replacing existing history."""
        if any(record.permit.permit_id == permit.permit_id for record in self.records):
            raise ValueError("permit identity already exists in lifecycle registry")
        return ConsolidationExecutionPermitLifecycleRegistry(
            records=(*self.records, ConsolidationExecutionPermitLifecycleRecord.issued(permit))
        )

    def transition(
        self,
        request: ConsolidationExecutionPermitTransitionRequest,
    ) -> ConsolidationExecutionPermitLifecycleRegistry:
        """Transition one exact permit and preserve all other records."""
        index, record = self._target(request.target_permit_id)
        updated = record.transition(request)
        return ConsolidationExecutionPermitLifecycleRegistry(
            records=(*self.records[:index], updated, *self.records[index + 1 :])
        )

    def record_for(
        self,
        permit_id: str,
    ) -> ConsolidationExecutionPermitLifecycleRecord:
        """Return one exact permit record."""
        return self._target(permit_id)[1]

    @property
    def consumption_count(self) -> int:
        """Return the number of uniquely consumed permits."""
        return sum(record.consumption_count for record in self.records)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic registry evidence."""
        return {
            "records": [record.snapshot() for record in self.records],
            "consumption_count": self.consumption_count,
            "has_application_authority": self.has_application_authority,
        }

    def _target(
        self,
        permit_id: str,
    ) -> tuple[int, ConsolidationExecutionPermitLifecycleRecord]:
        _validate_code("permit_id", permit_id)
        for index, record in enumerate(self.records):
            if record.permit.permit_id == permit_id:
                return index, record
        raise ValueError("permit identity is not present in lifecycle registry")


def _status_for(
    action: ConsolidationExecutionPermitLifecycleAction,
) -> ConsolidationExecutionPermitLifecycleStatus:
    if action is ConsolidationExecutionPermitLifecycleAction.CANCEL:
        return ConsolidationExecutionPermitLifecycleStatus.CANCELLED
    if action is ConsolidationExecutionPermitLifecycleAction.EXPIRE:
        return ConsolidationExecutionPermitLifecycleStatus.EXPIRED
    return ConsolidationExecutionPermitLifecycleStatus.CONSUMED


def _validate_transition_episode(
    *,
    permit: ConsolidationExecutionPermit,
    action: ConsolidationExecutionPermitLifecycleAction,
    decision_episode: int,
) -> None:
    _validate_nonnegative_int("decision_episode", decision_episode)
    if decision_episode <= permit.issued_episode:
        raise ValueError("permit lifecycle transition must follow permit issuance")
    if action is ConsolidationExecutionPermitLifecycleAction.EXPIRE:
        if decision_episode <= permit.expires_after_episode:
            raise ValueError("permit may expire only after its validity window")
        return
    if decision_episode > permit.expires_after_episode:
        raise ValueError("cancel or consume transition requires an unexpired permit")


def _transition_decision_id(
    *,
    permit: ConsolidationExecutionPermit,
    action: ConsolidationExecutionPermitLifecycleAction,
    decision_episode: int,
    actor_code: str,
    reason_code: str,
    consumption_reference_code: str | None,
) -> str:
    payload = {
        "permit": permit.snapshot(),
        "action": action.value,
        "decision_episode": decision_episode,
        "actor_code": actor_code,
        "reason_code": reason_code,
        "consumption_reference_code": consumption_reference_code,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"consolidation-permit-transition:{hashlib.sha256(canonical).hexdigest()}"


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
