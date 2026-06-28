"""Human approval contracts for bounded controlled replay and restoration."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from enum import StrEnum


class ControlledReplayRestorationOperation(StrEnum):
    """The only operation classes recognized by this authorization boundary."""

    RETENTION_REPLAY = "retention_replay"
    CHECKPOINT_RESTORATION = "checkpoint_restoration"


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationTarget:
    """Exact non-executable target for one future bounded operation."""

    operation: ControlledReplayRestorationOperation
    target_id: str
    source_checkpoint_id: str
    source_checkpoint_checksum: str
    expected_current_checkpoint_id: str
    expected_current_checkpoint_checksum: str
    source_evidence_ids: tuple[str, ...]
    maximum_work_items: int
    requires_complete_envelope: bool = True
    allows_partial_restoration: bool = False
    has_replay_authority: bool = False
    has_restoration_authority: bool = False
    has_production_action_authority: bool = False
    has_cognitive_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("target_id", self.target_id)
        _validate_code("source_checkpoint_id", self.source_checkpoint_id)
        _validate_checksum("source_checkpoint_checksum", self.source_checkpoint_checksum)
        _validate_code(
            "expected_current_checkpoint_id",
            self.expected_current_checkpoint_id,
        )
        _validate_checksum(
            "expected_current_checkpoint_checksum",
            self.expected_current_checkpoint_checksum,
        )
        _validate_sorted_unique_codes("source_evidence_ids", self.source_evidence_ids)
        if not self.source_evidence_ids:
            raise ValueError("source_evidence_ids must not be empty")
        _validate_nonnegative_int("maximum_work_items", self.maximum_work_items)
        if self.operation is ControlledReplayRestorationOperation.RETENTION_REPLAY:
            if not self.target_id.startswith("replay-target:"):
                raise ValueError("retention replay target_id must use replay-target prefix")
            if self.maximum_work_items < 1:
                raise ValueError("retention replay requires a positive work-item bound")
        else:
            if not self.target_id.startswith("restoration-target:"):
                raise ValueError(
                    "checkpoint restoration target_id must use restoration-target prefix"
                )
            if self.maximum_work_items != 0:
                raise ValueError("checkpoint restoration cannot contain replay work items")
            if (
                self.source_checkpoint_id == self.expected_current_checkpoint_id
                and self.source_checkpoint_checksum == self.expected_current_checkpoint_checksum
            ):
                raise ValueError("checkpoint restoration target must differ from current state")
        if not self.requires_complete_envelope:
            raise ValueError("controlled operations require a complete checkpoint envelope")
        if self.allows_partial_restoration:
            raise ValueError("partial checkpoint restoration is forbidden")
        if self.has_replay_authority:
            raise ValueError("target evidence cannot execute replay")
        if self.has_restoration_authority:
            raise ValueError("target evidence cannot restore checkpoints")
        if self.has_production_action_authority:
            raise ValueError("target evidence cannot select production actions")
        if self.has_cognitive_authority:
            raise ValueError("target evidence cannot perform cognition")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe target evidence."""
        return {
            "operation": self.operation.value,
            "target_id": self.target_id,
            "source_checkpoint_id": self.source_checkpoint_id,
            "source_checkpoint_checksum": self.source_checkpoint_checksum,
            "expected_current_checkpoint_id": self.expected_current_checkpoint_id,
            "expected_current_checkpoint_checksum": (self.expected_current_checkpoint_checksum),
            "source_evidence_ids": list(self.source_evidence_ids),
            "maximum_work_items": self.maximum_work_items,
            "requires_complete_envelope": self.requires_complete_envelope,
            "allows_partial_restoration": self.allows_partial_restoration,
            "has_replay_authority": self.has_replay_authority,
            "has_restoration_authority": self.has_restoration_authority,
            "has_production_action_authority": self.has_production_action_authority,
            "has_cognitive_authority": self.has_cognitive_authority,
        }


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationEvidence:
    """Current validated identities supplied to the pure approval policy."""

    captured_episode: int
    current_checkpoint_id: str
    current_checkpoint_checksum: str
    available_checkpoint_checksums: tuple[tuple[str, str], ...]
    available_evidence_ids: tuple[str, ...]
    checksum_verified: bool = True
    used_fallback: bool = False
    has_replay_or_restoration_authority: bool = False

    def __post_init__(self) -> None:
        _validate_nonnegative_int("captured_episode", self.captured_episode)
        _validate_code("current_checkpoint_id", self.current_checkpoint_id)
        _validate_checksum("current_checkpoint_checksum", self.current_checkpoint_checksum)
        checkpoint_ids = tuple(item[0] for item in self.available_checkpoint_checksums)
        if checkpoint_ids != tuple(sorted(checkpoint_ids)):
            raise ValueError("available checkpoints must use stable sorted ordering")
        if len(checkpoint_ids) != len(set(checkpoint_ids)):
            raise ValueError("available checkpoint identities must be unique")
        for checkpoint_id, checksum in self.available_checkpoint_checksums:
            _validate_code("available checkpoint_id", checkpoint_id)
            _validate_checksum("available checkpoint checksum", checksum)
        if (
            self.current_checkpoint_id,
            self.current_checkpoint_checksum,
        ) not in self.available_checkpoint_checksums:
            raise ValueError("current checkpoint must exist in available checkpoint evidence")
        _validate_sorted_unique_codes(
            "available_evidence_ids",
            self.available_evidence_ids,
        )
        if self.has_replay_or_restoration_authority:
            raise ValueError("current evidence cannot execute replay or restoration")

    @property
    def evidence_state_id(self) -> str:
        """Return the deterministic identity of this exact evidence snapshot."""
        return _identity("controlled-replay-restoration-evidence", self._identity_payload())

    def checkpoint_checksum(self, checkpoint_id: str) -> str:
        """Return one exact available checkpoint checksum."""
        _validate_code("checkpoint_id", checkpoint_id)
        for available_id, checksum in self.available_checkpoint_checksums:
            if available_id == checkpoint_id:
                return checksum
        raise ValueError("checkpoint identity is not present in current evidence")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic current evidence without granting authority."""
        return {
            "evidence_state_id": self.evidence_state_id,
            **self._identity_payload(),
        }

    def _identity_payload(self) -> dict[str, object]:
        return {
            "captured_episode": self.captured_episode,
            "current_checkpoint_id": self.current_checkpoint_id,
            "current_checkpoint_checksum": self.current_checkpoint_checksum,
            "available_checkpoint_checksums": [
                {"checkpoint_id": checkpoint_id, "checksum": checksum}
                for checkpoint_id, checksum in self.available_checkpoint_checksums
            ],
            "available_evidence_ids": list(self.available_evidence_ids),
            "checksum_verified": self.checksum_verified,
            "used_fallback": self.used_fallback,
            "has_replay_or_restoration_authority": (self.has_replay_or_restoration_authority),
        }


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationApprovalRequest:
    """One explicit human request for one exact future controlled operation."""

    target: ControlledReplayRestorationTarget
    expected_evidence_state_id: str
    approval_episode: int
    expires_after_episode: int
    approver_code: str
    reason_code: str

    def __post_init__(self) -> None:
        _validate_code("expected_evidence_state_id", self.expected_evidence_state_id)
        _validate_nonnegative_int("approval_episode", self.approval_episode)
        _validate_nonnegative_int("expires_after_episode", self.expires_after_episode)
        if self.expires_after_episode <= self.approval_episode:
            raise ValueError("expires_after_episode must follow approval_episode")
        _validate_code("approver_code", self.approver_code)
        if not self.approver_code.startswith("human:"):
            raise ValueError("approver_code must identify an explicit human approver")
        _validate_code("reason_code", self.reason_code)


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationPermit:
    """Single-use authorization evidence that performs no operation itself."""

    permit_id: str
    target: ControlledReplayRestorationTarget
    evidence: ControlledReplayRestorationEvidence
    issued_episode: int
    expires_after_episode: int
    approver_code: str
    reason_code: str
    authorizes_one_operation: bool = True
    single_use: bool = True
    consumed: bool = False
    operation_count: int = 0
    has_direct_replay_authority: bool = False
    has_direct_restoration_authority: bool = False
    has_production_action_authority: bool = False
    has_cognitive_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("permit_id", self.permit_id)
        _validate_nonnegative_int("issued_episode", self.issued_episode)
        _validate_nonnegative_int("expires_after_episode", self.expires_after_episode)
        if self.expires_after_episode <= self.issued_episode:
            raise ValueError("permit expiry must follow its issue episode")
        _validate_code("approver_code", self.approver_code)
        if not self.approver_code.startswith("human:"):
            raise ValueError("controlled operation permit requires a human approver")
        _validate_code("reason_code", self.reason_code)
        if not self.authorizes_one_operation:
            raise ValueError("permit must authorize exactly one bounded operation")
        if not self.single_use:
            raise ValueError("permit must be single-use")
        if self.consumed:
            raise ValueError("new permit cannot already be consumed")
        if self.operation_count != 0:
            raise ValueError("new permit cannot contain completed operations")
        if self.has_direct_replay_authority:
            raise ValueError("permit evidence cannot execute replay directly")
        if self.has_direct_restoration_authority:
            raise ValueError("permit evidence cannot restore checkpoints directly")
        if self.has_production_action_authority:
            raise ValueError("permit evidence cannot select production actions")
        if self.has_cognitive_authority:
            raise ValueError("permit evidence cannot perform cognition")
        _validate_target_against_evidence(self.target, self.evidence)

    def valid_at(self, episode: int) -> bool:
        """Return whether the unused permit remains inside its bounded window."""
        _validate_nonnegative_int("episode", episode)
        return bool(
            not self.consumed and self.issued_episode <= episode <= self.expires_after_episode
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe authorization evidence."""
        return {
            "permit_id": self.permit_id,
            "target": self.target.snapshot(),
            "evidence": self.evidence.snapshot(),
            "issued_episode": self.issued_episode,
            "expires_after_episode": self.expires_after_episode,
            "approver_code": self.approver_code,
            "reason_code": self.reason_code,
            "authorizes_one_operation": self.authorizes_one_operation,
            "single_use": self.single_use,
            "consumed": self.consumed,
            "operation_count": self.operation_count,
            "has_direct_replay_authority": self.has_direct_replay_authority,
            "has_direct_restoration_authority": self.has_direct_restoration_authority,
            "has_production_action_authority": self.has_production_action_authority,
            "has_cognitive_authority": self.has_cognitive_authority,
        }


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationApprovalPolicy:
    """Issue bounded permits only for exact immediately validated evidence."""

    maximum_validity_episodes: int = 1

    def __post_init__(self) -> None:
        if (
            isinstance(self.maximum_validity_episodes, bool)
            or not isinstance(self.maximum_validity_episodes, int)
            or self.maximum_validity_episodes < 1
        ):
            raise ValueError("maximum_validity_episodes must be a positive integer")

    def evaluate(
        self,
        *,
        request: ControlledReplayRestorationApprovalRequest,
        evidence: ControlledReplayRestorationEvidence,
    ) -> ControlledReplayRestorationPermit:
        """Issue immutable authorization evidence without executing anything."""
        before = evidence.snapshot()
        if request.expected_evidence_state_id != evidence.evidence_state_id:
            raise ValueError("approval request targets different current evidence")
        if request.approval_episode != evidence.captured_episode:
            raise ValueError("approval requires immediate current-evidence validation")
        if (
            request.expires_after_episode - request.approval_episode
            > self.maximum_validity_episodes
        ):
            raise ValueError("approval validity exceeds policy limit")
        if not evidence.checksum_verified:
            raise ValueError("approval requires checksum-verified checkpoint evidence")
        if evidence.used_fallback:
            raise ValueError("approval cannot use fallback checkpoint evidence")
        _validate_target_against_evidence(request.target, evidence)
        if evidence.snapshot() != before:
            raise RuntimeError("approval validation mutated current evidence")

        payload = {
            "target": request.target.snapshot(),
            "evidence": evidence.snapshot(),
            "issued_episode": request.approval_episode,
            "expires_after_episode": request.expires_after_episode,
            "approver_code": request.approver_code,
            "reason_code": request.reason_code,
            "authorizes_one_operation": True,
            "single_use": True,
        }
        return ControlledReplayRestorationPermit(
            permit_id=_identity("controlled-replay-restoration-permit", payload),
            target=request.target,
            evidence=evidence,
            issued_episode=request.approval_episode,
            expires_after_episode=request.expires_after_episode,
            approver_code=request.approver_code,
            reason_code=request.reason_code,
        )


def _validate_target_against_evidence(
    target: ControlledReplayRestorationTarget,
    evidence: ControlledReplayRestorationEvidence,
) -> None:
    if target.expected_current_checkpoint_id != evidence.current_checkpoint_id:
        raise ValueError("target expects a different current checkpoint")
    if target.expected_current_checkpoint_checksum != evidence.current_checkpoint_checksum:
        raise ValueError("target expects a different current checkpoint checksum")
    available_source_checksum = evidence.checkpoint_checksum(target.source_checkpoint_id)
    if available_source_checksum != target.source_checkpoint_checksum:
        raise ValueError("target source checkpoint checksum is not current")
    missing_evidence = set(target.source_evidence_ids) - set(evidence.available_evidence_ids)
    if missing_evidence:
        raise ValueError("target source evidence is not currently available")


def _identity(prefix: str, payload: dict[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"{prefix}:{hashlib.sha256(canonical).hexdigest()}"


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_checksum(name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 checksum")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
    for value in values:
        _validate_code(name, value)
