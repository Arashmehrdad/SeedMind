"""Immutable lifecycle state for controlled replay and restoration permits."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum

from seedmind.research.ndnra.controlled_replay_restoration_approval import (
    ControlledReplayRestorationOperation,
    ControlledReplayRestorationPermit,
)


class ControlledReplayRestorationPermitLifecycleAction(StrEnum):
    """Explicit caller-supplied transition for one exact issued permit."""

    CANCEL = "cancel"
    EXPIRE = "expire"
    CONSUME = "consume"


class ControlledReplayRestorationPermitLifecycleStatus(StrEnum):
    """Current immutable state of one controlled-operation permit."""

    ISSUED = "issued"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    CONSUMED = "consumed"


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationPermitTransitionRequest:
    """One explicit lifecycle request bound to all authority-bearing identities."""

    target_permit_id: str
    expected_operation: ControlledReplayRestorationOperation
    expected_target_id: str
    expected_source_checkpoint_id: str
    expected_source_checkpoint_checksum: str
    expected_current_checkpoint_id: str
    expected_current_checkpoint_checksum: str
    expected_evidence_state_id: str
    action: ControlledReplayRestorationPermitLifecycleAction
    decision_episode: int
    actor_code: str
    reason_code: str
    consumption_reference_code: str | None = None

    def __post_init__(self) -> None:
        _validate_code("target_permit_id", self.target_permit_id)
        _validate_code("expected_target_id", self.expected_target_id)
        _validate_code(
            "expected_source_checkpoint_id",
            self.expected_source_checkpoint_id,
        )
        _validate_checksum(
            "expected_source_checkpoint_checksum",
            self.expected_source_checkpoint_checksum,
        )
        _validate_code(
            "expected_current_checkpoint_id",
            self.expected_current_checkpoint_id,
        )
        _validate_checksum(
            "expected_current_checkpoint_checksum",
            self.expected_current_checkpoint_checksum,
        )
        _validate_code("expected_evidence_state_id", self.expected_evidence_state_id)
        _validate_nonnegative_int("decision_episode", self.decision_episode)
        _validate_code("actor_code", self.actor_code)
        _validate_code("reason_code", self.reason_code)
        if self.action is ControlledReplayRestorationPermitLifecycleAction.CONSUME:
            if self.consumption_reference_code is None:
                raise ValueError("consume transition requires consumption_reference_code")
            _validate_code(
                "consumption_reference_code",
                self.consumption_reference_code,
            )
            if not self.actor_code.startswith("operation:"):
                raise ValueError("permit consumption requires an operation actor")
        elif self.consumption_reference_code is not None:
            raise ValueError("only consume transition may include a consumption reference")


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationPermitTransitionDecision:
    """Immutable terminal transition carrying no replay or restoration authority."""

    decision_id: str
    permit: ControlledReplayRestorationPermit
    action: ControlledReplayRestorationPermitLifecycleAction
    status: ControlledReplayRestorationPermitLifecycleStatus
    decision_episode: int
    actor_code: str
    reason_code: str
    consumption_reference_code: str | None = None
    has_replay_authority: bool = False
    has_restoration_authority: bool = False
    has_cognitive_authority: bool = False
    has_production_action_authority: bool = False

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
        if self.action is ControlledReplayRestorationPermitLifecycleAction.CONSUME:
            if self.consumption_reference_code is None:
                raise ValueError("consumed permit requires a consumption reference")
            _validate_code(
                "consumption_reference_code",
                self.consumption_reference_code,
            )
            if not self.actor_code.startswith("operation:"):
                raise ValueError("consumed permit requires an operation actor")
        elif self.consumption_reference_code is not None:
            raise ValueError("only consumed permit may include a consumption reference")
        _reject_authority(
            has_replay_authority=self.has_replay_authority,
            has_restoration_authority=self.has_restoration_authority,
            has_cognitive_authority=self.has_cognitive_authority,
            has_production_action_authority=self.has_production_action_authority,
            owner="permit lifecycle decisions",
        )
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
        """Return deterministic ASCII-safe terminal transition evidence."""
        return {
            "decision_id": self.decision_id,
            "permit": self.permit.snapshot(),
            "action": self.action.value,
            "status": self.status.value,
            "decision_episode": self.decision_episode,
            "actor_code": self.actor_code,
            "reason_code": self.reason_code,
            "consumption_reference_code": self.consumption_reference_code,
            "has_replay_authority": self.has_replay_authority,
            "has_restoration_authority": self.has_restoration_authority,
            "has_cognitive_authority": self.has_cognitive_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationPermitLifecycleRecord:
    """One issued permit plus at most one immutable terminal transition."""

    permit: ControlledReplayRestorationPermit
    status: ControlledReplayRestorationPermitLifecycleStatus = (
        ControlledReplayRestorationPermitLifecycleStatus.ISSUED
    )
    decisions: tuple[ControlledReplayRestorationPermitTransitionDecision, ...] = ()
    has_replay_authority: bool = False
    has_restoration_authority: bool = False
    has_cognitive_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _reject_authority(
            has_replay_authority=self.has_replay_authority,
            has_restoration_authority=self.has_restoration_authority,
            has_cognitive_authority=self.has_cognitive_authority,
            has_production_action_authority=self.has_production_action_authority,
            owner="permit lifecycle records",
        )
        if len(self.decisions) > 1:
            raise ValueError("permit lifecycle permits only one terminal transition")
        decision_ids = tuple(decision.decision_id for decision in self.decisions)
        if len(decision_ids) != len(set(decision_ids)):
            raise ValueError("permit lifecycle decision identities must be unique")
        if not self.decisions:
            if self.status is not ControlledReplayRestorationPermitLifecycleStatus.ISSUED:
                raise ValueError("empty permit history must remain issued")
            return
        decision = self.decisions[0]
        if decision.permit != self.permit:
            raise ValueError("permit lifecycle decision targets a different permit")
        if self.status is not decision.status:
            raise ValueError("permit lifecycle status must match terminal decision")
        if self.status is ControlledReplayRestorationPermitLifecycleStatus.ISSUED:
            raise ValueError("issued status cannot contain terminal decisions")

    @classmethod
    def issued(
        cls,
        permit: ControlledReplayRestorationPermit,
    ) -> ControlledReplayRestorationPermitLifecycleRecord:
        """Create immutable issued lifecycle evidence for one permit."""
        return cls(permit=permit)

    @property
    def is_terminal(self) -> bool:
        """Return whether cancellation, expiry, or consumption has occurred."""
        return self.status is not ControlledReplayRestorationPermitLifecycleStatus.ISSUED

    @property
    def consumption_count(self) -> int:
        """Return one only for a consumed terminal record."""
        return int(self.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED)

    def transition(
        self,
        request: ControlledReplayRestorationPermitTransitionRequest,
    ) -> ControlledReplayRestorationPermitLifecycleRecord:
        """Return a new terminal record while preserving this issued record."""
        if self.is_terminal:
            raise ValueError("permit lifecycle is already terminal")
        _validate_request_matches_permit(request, self.permit)
        _validate_transition_episode(
            permit=self.permit,
            action=request.action,
            decision_episode=request.decision_episode,
        )
        decision = ControlledReplayRestorationPermitTransitionDecision(
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
        return ControlledReplayRestorationPermitLifecycleRecord(
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
            "has_replay_authority": self.has_replay_authority,
            "has_restoration_authority": self.has_restoration_authority,
            "has_cognitive_authority": self.has_cognitive_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationPermitLifecycleRegistry:
    """Immutable collection with one lifecycle record per permit identity."""

    records: tuple[ControlledReplayRestorationPermitLifecycleRecord, ...] = ()
    has_replay_authority: bool = False
    has_restoration_authority: bool = False
    has_cognitive_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _reject_authority(
            has_replay_authority=self.has_replay_authority,
            has_restoration_authority=self.has_restoration_authority,
            has_cognitive_authority=self.has_cognitive_authority,
            has_production_action_authority=self.has_production_action_authority,
            owner="permit lifecycle registry",
        )
        permit_ids = tuple(record.permit.permit_id for record in self.records)
        if len(permit_ids) != len(set(permit_ids)):
            raise ValueError("permit lifecycle registry identities must be unique")

    def add(
        self,
        permit: ControlledReplayRestorationPermit,
    ) -> ControlledReplayRestorationPermitLifecycleRegistry:
        """Add one issued permit without replacing existing history."""
        if any(record.permit.permit_id == permit.permit_id for record in self.records):
            raise ValueError("permit identity already exists in lifecycle registry")
        return ControlledReplayRestorationPermitLifecycleRegistry(
            records=(
                *self.records,
                ControlledReplayRestorationPermitLifecycleRecord.issued(permit),
            )
        )

    def transition(
        self,
        request: ControlledReplayRestorationPermitTransitionRequest,
    ) -> ControlledReplayRestorationPermitLifecycleRegistry:
        """Transition one exact permit and preserve all other records."""
        index, record = self._target(request.target_permit_id)
        updated = record.transition(request)
        return ControlledReplayRestorationPermitLifecycleRegistry(
            records=(*self.records[:index], updated, *self.records[index + 1 :])
        )

    def record_for(
        self,
        permit_id: str,
    ) -> ControlledReplayRestorationPermitLifecycleRecord:
        """Return one exact lifecycle record."""
        return self._target(permit_id)[1]

    @property
    def consumption_count(self) -> int:
        """Return the number of uniquely consumed permits."""
        return sum(record.consumption_count for record in self.records)

    @property
    def replay_consumption_count(self) -> int:
        """Return consumed permits scoped to retention replay targets."""
        return sum(
            record.consumption_count
            for record in self.records
            if record.permit.target.operation
            is ControlledReplayRestorationOperation.RETENTION_REPLAY
        )

    @property
    def restoration_consumption_count(self) -> int:
        """Return consumed permits scoped to checkpoint restoration targets."""
        return sum(
            record.consumption_count
            for record in self.records
            if record.permit.target.operation
            is ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic registry evidence."""
        return {
            "records": [record.snapshot() for record in self.records],
            "consumption_count": self.consumption_count,
            "replay_consumption_count": self.replay_consumption_count,
            "restoration_consumption_count": self.restoration_consumption_count,
            "has_replay_authority": self.has_replay_authority,
            "has_restoration_authority": self.has_restoration_authority,
            "has_cognitive_authority": self.has_cognitive_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    def _target(
        self,
        permit_id: str,
    ) -> tuple[int, ControlledReplayRestorationPermitLifecycleRecord]:
        _validate_code("permit_id", permit_id)
        for index, record in enumerate(self.records):
            if record.permit.permit_id == permit_id:
                return index, record
        raise ValueError("permit identity is not present in lifecycle registry")


def _validate_request_matches_permit(
    request: ControlledReplayRestorationPermitTransitionRequest,
    permit: ControlledReplayRestorationPermit,
) -> None:
    target = permit.target
    if request.target_permit_id != permit.permit_id:
        raise ValueError("transition request targets a different permit")
    if request.expected_operation is not target.operation:
        raise ValueError("transition request targets a different operation")
    if request.expected_target_id != target.target_id:
        raise ValueError("transition request targets a different operation target")
    if request.expected_source_checkpoint_id != target.source_checkpoint_id:
        raise ValueError("transition request targets a different source checkpoint")
    if request.expected_source_checkpoint_checksum != target.source_checkpoint_checksum:
        raise ValueError("transition request targets a different source checkpoint checksum")
    if request.expected_current_checkpoint_id != target.expected_current_checkpoint_id:
        raise ValueError("transition request targets a different current checkpoint")
    if request.expected_current_checkpoint_checksum != target.expected_current_checkpoint_checksum:
        raise ValueError("transition request targets a different current checkpoint checksum")
    if request.expected_evidence_state_id != permit.evidence.evidence_state_id:
        raise ValueError("transition request targets different approval evidence")


def _status_for(
    action: ControlledReplayRestorationPermitLifecycleAction,
) -> ControlledReplayRestorationPermitLifecycleStatus:
    if action is ControlledReplayRestorationPermitLifecycleAction.CANCEL:
        return ControlledReplayRestorationPermitLifecycleStatus.CANCELLED
    if action is ControlledReplayRestorationPermitLifecycleAction.EXPIRE:
        return ControlledReplayRestorationPermitLifecycleStatus.EXPIRED
    return ControlledReplayRestorationPermitLifecycleStatus.CONSUMED


def _validate_transition_episode(
    *,
    permit: ControlledReplayRestorationPermit,
    action: ControlledReplayRestorationPermitLifecycleAction,
    decision_episode: int,
) -> None:
    _validate_nonnegative_int("decision_episode", decision_episode)
    if decision_episode <= permit.issued_episode:
        raise ValueError("permit lifecycle transition must follow permit issuance")
    if action is ControlledReplayRestorationPermitLifecycleAction.EXPIRE:
        if decision_episode <= permit.expires_after_episode:
            raise ValueError("permit may expire only after its validity window")
        return
    if decision_episode > permit.expires_after_episode:
        raise ValueError("cancel or consume transition requires an unexpired permit")


def _transition_decision_id(
    *,
    permit: ControlledReplayRestorationPermit,
    action: ControlledReplayRestorationPermitLifecycleAction,
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
    return f"controlled-operation-permit-transition:{hashlib.sha256(canonical).hexdigest()}"


def _reject_authority(
    *,
    has_replay_authority: bool,
    has_restoration_authority: bool,
    has_cognitive_authority: bool,
    has_production_action_authority: bool,
    owner: str,
) -> None:
    if has_replay_authority:
        raise ValueError(f"{owner} cannot execute replay")
    if has_restoration_authority:
        raise ValueError(f"{owner} cannot restore checkpoints")
    if has_cognitive_authority:
        raise ValueError(f"{owner} cannot perform cognition")
    if has_production_action_authority:
        raise ValueError(f"{owner} cannot select production actions")


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_checksum(name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 checksum")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
