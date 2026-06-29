"""Explicit training review or configured non-training bypass resolution."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.bounded_imagination_safe_experiment_permission import (
    ImaginedSafeExperimentPermissionAction,
    ImaginedSafeExperimentPermissionResult,
)
from seedmind.research.ndnra.bounded_imagination_safe_experiment_proposal import (
    ImaginedSafeExperimentProposal,
    ImaginedSafeExperimentProposalResult,
)
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin


class ImaginedSafeExperimentReviewMode(StrEnum):
    """Whether the proposal is being considered during training or later runtime."""

    TRAINING = "training"
    NON_TRAINING = "non_training"


class ImaginedSafeExperimentReviewGateStatus(StrEnum):
    """Exact non-executing result of the review-gate resolution."""

    REVIEW_REQUIRED = "review_required"
    REVIEW_APPROVED = "review_approved"
    REVIEW_REJECTED = "review_rejected"
    REVIEW_DEFERRED = "review_deferred"
    EXPLICIT_NON_TRAINING_BYPASS = "explicit_non_training_bypass"


@dataclass(frozen=True, slots=True)
class BoundedSafeExperimentReviewGateConfig:
    """Finite policy limits for optional non-training review bypass."""

    allow_non_training_bypass: bool = False
    maximum_source_snapshot_bytes: int = 1_000_000
    maximum_bypass_policy_code_characters: int = 128

    def __post_init__(self) -> None:
        if not isinstance(self.allow_non_training_bypass, bool):
            raise ValueError("allow_non_training_bypass must be boolean")
        _validate_positive_int(
            "maximum_source_snapshot_bytes",
            self.maximum_source_snapshot_bytes,
        )
        _validate_positive_int(
            "maximum_bypass_policy_code_characters",
            self.maximum_bypass_policy_code_characters,
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "allow_non_training_bypass": self.allow_non_training_bypass,
            "maximum_source_snapshot_bytes": self.maximum_source_snapshot_bytes,
            "maximum_bypass_policy_code_characters": (self.maximum_bypass_policy_code_characters),
        }


@dataclass(frozen=True, slots=True)
class ImaginedSafeExperimentReviewGateRequest:
    """Resolve review requirements without scheduling or executing an experiment."""

    source_result: ImaginedSafeExperimentProposalResult
    mode: ImaginedSafeExperimentReviewMode
    permission_result: ImaginedSafeExperimentPermissionResult | None = None
    bypass_requested: bool = False
    bypass_policy_code: str | None = None
    config: BoundedSafeExperimentReviewGateConfig = field(
        default_factory=BoundedSafeExperimentReviewGateConfig
    )
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _revalidate_proposal_result(self.source_result)
        if not isinstance(self.mode, ImaginedSafeExperimentReviewMode):
            raise ValueError("mode must be an imagined safe-experiment review mode")
        if not isinstance(self.bypass_requested, bool):
            raise ValueError("bypass_requested must be boolean")
        if (
            len(self.source_result.snapshot_json_ascii())
            > self.config.maximum_source_snapshot_bytes
        ):
            raise ValueError("source proposal result exceeds review-gate byte bound")
        if self.permission_result is not None:
            _revalidate_permission_result(self.permission_result)
            if self.permission_result.request.source_result != self.source_result:
                raise ValueError("permission result targets a different proposal result")
        if self.bypass_requested:
            if self.mode is not ImaginedSafeExperimentReviewMode.NON_TRAINING:
                raise ValueError("review bypass is forbidden in training mode")
            if not self.config.allow_non_training_bypass:
                raise ValueError("non-training review bypass is disabled by policy")
            if self.permission_result is not None:
                raise ValueError("review bypass cannot be combined with permission evidence")
            if self.bypass_policy_code is None:
                raise ValueError("explicit review bypass requires a policy code")
            _validate_bounded_ascii_code(
                "bypass_policy_code",
                self.bypass_policy_code,
                self.config.maximum_bypass_policy_code_characters,
            )
            if not self.bypass_policy_code.startswith("runtime-policy:"):
                raise ValueError("bypass_policy_code must identify an explicit runtime policy")
        elif self.bypass_policy_code is not None:
            raise ValueError("bypass_policy_code requires an explicit bypass request")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("review-gate requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("review-gate requests cannot control production actions")

    @property
    def request_id(self) -> str:
        return _identity("imagined-safe-experiment-review-gate-request", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"request_id": self.request_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "source_result": self.source_result.snapshot(),
            "mode": self.mode.value,
            "permission_result": (
                None if self.permission_result is None else self.permission_result.snapshot()
            ),
            "bypass_requested": self.bypass_requested,
            "bypass_policy_code": self.bypass_policy_code,
            "config": self.config.snapshot(),
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ImaginedSafeExperimentReviewGateDecision:
    """Review or bypass evidence that grants no execution capability."""

    decision_id: str
    proposal_origin: ExperienceOrigin
    source_result_id: str
    source_request_id: str
    source_proposal: ImaginedSafeExperimentProposal
    mode: ImaginedSafeExperimentReviewMode
    status: ImaginedSafeExperimentReviewGateStatus
    permission_result_id: str | None
    permission_decision_id: str | None
    bypass_policy_code: str | None
    review_required: bool
    review_satisfied: bool
    bypass_applied: bool
    authorizes_execution: bool = False
    authorizes_scheduling: bool = False
    authorizes_persistence: bool = False
    authorizes_live_integration: bool = False
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("decision_id", self.decision_id)
        _validate_ascii_code("source_result_id", self.source_result_id)
        _validate_ascii_code("source_request_id", self.source_request_id)
        if self.proposal_origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("review-gate decisions require imagined proposal origin")
        if not isinstance(self.mode, ImaginedSafeExperimentReviewMode):
            raise ValueError("mode must be an imagined safe-experiment review mode")
        if not isinstance(self.status, ImaginedSafeExperimentReviewGateStatus):
            raise ValueError("status must be an imagined safe-experiment review-gate status")
        for name, value in (
            ("review_required", self.review_required),
            ("review_satisfied", self.review_satisfied),
            ("bypass_applied", self.bypass_applied),
        ):
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be boolean")
        _validate_status_shape(self)
        if self.authorizes_execution:
            raise ValueError("review-gate decisions cannot execute experiments")
        if self.authorizes_scheduling:
            raise ValueError("review-gate decisions cannot schedule experiments")
        if self.authorizes_persistence:
            raise ValueError("review-gate decisions cannot persist experiments")
        if self.authorizes_live_integration:
            raise ValueError("review-gate decisions cannot integrate experiments live")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("review-gate decisions cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("review-gate decisions cannot control production actions")
        if self.decision_id != _identity(
            "imagined-safe-experiment-review-gate-decision",
            self._identity_payload(),
        ):
            raise ValueError("review-gate decision identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"decision_id": self.decision_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "proposal_origin": self.proposal_origin.value,
            "source_result_id": self.source_result_id,
            "source_request_id": self.source_request_id,
            "source_proposal": self.source_proposal.snapshot(),
            "mode": self.mode.value,
            "status": self.status.value,
            "permission_result_id": self.permission_result_id,
            "permission_decision_id": self.permission_decision_id,
            "bypass_policy_code": self.bypass_policy_code,
            "review_required": self.review_required,
            "review_satisfied": self.review_satisfied,
            "bypass_applied": self.bypass_applied,
            "authorizes_execution": self.authorizes_execution,
            "authorizes_scheduling": self.authorizes_scheduling,
            "authorizes_persistence": self.authorizes_persistence,
            "authorizes_live_integration": self.authorizes_live_integration,
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ImaginedSafeExperimentReviewGateResult:
    """One deterministic review-gate result with no experiment authority."""

    result_id: str
    request: ImaginedSafeExperimentReviewGateRequest
    decision: ImaginedSafeExperimentReviewGateDecision
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("result_id", self.result_id)
        expected = BoundedImaginedSafeExperimentReviewGate()._decision_for(self.request)
        if self.decision != expected:
            raise ValueError("review-gate decision is inconsistent with request")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("review-gate results cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("review-gate results cannot control production actions")
        if self.result_id != _identity(
            "imagined-safe-experiment-review-gate-result",
            self._identity_payload(),
        ):
            raise ValueError("review-gate result identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "decision": self.decision.snapshot(),
            "factual_confidence_change": self.factual_confidence_change,
            "mastery_change": self.mastery_change,
            "competence_change": self.competence_change,
            "growth_pressure_change": self.growth_pressure_change,
            "replay_evidence_change": self.replay_evidence_change,
            "real_observation_change": self.real_observation_change,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class BoundedImaginedSafeExperimentReviewGate:
    """Resolve optional training review without creating experiment authority."""

    def resolve(
        self,
        request: ImaginedSafeExperimentReviewGateRequest,
    ) -> ImaginedSafeExperimentReviewGateResult:
        decision = self._decision_for(request)
        payload = {
            "request": request.snapshot(),
            "decision": decision.snapshot(),
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedSafeExperimentReviewGateResult(
            result_id=_identity("imagined-safe-experiment-review-gate-result", payload),
            request=request,
            decision=decision,
        )

    def _decision_for(
        self,
        request: ImaginedSafeExperimentReviewGateRequest,
    ) -> ImaginedSafeExperimentReviewGateDecision:
        status = _status_for(request)
        permission_result_id = (
            None if request.permission_result is None else request.permission_result.result_id
        )
        permission_decision_id = (
            None
            if request.permission_result is None
            else request.permission_result.decision.decision_id
        )
        payload = {
            "proposal_origin": request.source_result.proposal.origin.value,
            "source_result_id": request.source_result.result_id,
            "source_request_id": request.source_result.request.request_id,
            "source_proposal": request.source_result.proposal.snapshot(),
            "mode": request.mode.value,
            "status": status.value,
            "permission_result_id": permission_result_id,
            "permission_decision_id": permission_decision_id,
            "bypass_policy_code": request.bypass_policy_code,
            "review_required": status is ImaginedSafeExperimentReviewGateStatus.REVIEW_REQUIRED,
            "review_satisfied": status is ImaginedSafeExperimentReviewGateStatus.REVIEW_APPROVED,
            "bypass_applied": (
                status is ImaginedSafeExperimentReviewGateStatus.EXPLICIT_NON_TRAINING_BYPASS
            ),
            "authorizes_execution": False,
            "authorizes_scheduling": False,
            "authorizes_persistence": False,
            "authorizes_live_integration": False,
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedSafeExperimentReviewGateDecision(
            decision_id=_identity(
                "imagined-safe-experiment-review-gate-decision",
                payload,
            ),
            proposal_origin=request.source_result.proposal.origin,
            source_result_id=request.source_result.result_id,
            source_request_id=request.source_result.request.request_id,
            source_proposal=request.source_result.proposal,
            mode=request.mode,
            status=status,
            permission_result_id=permission_result_id,
            permission_decision_id=permission_decision_id,
            bypass_policy_code=request.bypass_policy_code,
            review_required=(status is ImaginedSafeExperimentReviewGateStatus.REVIEW_REQUIRED),
            review_satisfied=(status is ImaginedSafeExperimentReviewGateStatus.REVIEW_APPROVED),
            bypass_applied=(
                status is ImaginedSafeExperimentReviewGateStatus.EXPLICIT_NON_TRAINING_BYPASS
            ),
        )


def _status_for(
    request: ImaginedSafeExperimentReviewGateRequest,
) -> ImaginedSafeExperimentReviewGateStatus:
    if request.bypass_requested:
        return ImaginedSafeExperimentReviewGateStatus.EXPLICIT_NON_TRAINING_BYPASS
    if request.permission_result is None:
        return ImaginedSafeExperimentReviewGateStatus.REVIEW_REQUIRED
    action = request.permission_result.decision.action
    if action is ImaginedSafeExperimentPermissionAction.APPROVE:
        return ImaginedSafeExperimentReviewGateStatus.REVIEW_APPROVED
    if action is ImaginedSafeExperimentPermissionAction.REJECT:
        return ImaginedSafeExperimentReviewGateStatus.REVIEW_REJECTED
    if action is ImaginedSafeExperimentPermissionAction.DEFER:
        return ImaginedSafeExperimentReviewGateStatus.REVIEW_DEFERRED
    raise ValueError("unsupported permission review action")


def _validate_status_shape(decision: ImaginedSafeExperimentReviewGateDecision) -> None:
    has_permission_ids = (
        decision.permission_result_id is not None and decision.permission_decision_id is not None
    )
    has_partial_permission_ids = (decision.permission_result_id is None) != (
        decision.permission_decision_id is None
    )
    if has_partial_permission_ids:
        raise ValueError("review-gate permission identities must be complete")
    if decision.status is ImaginedSafeExperimentReviewGateStatus.REVIEW_REQUIRED:
        if has_permission_ids or decision.bypass_policy_code is not None:
            raise ValueError("required review cannot carry permission or bypass evidence")
        if not decision.review_required or decision.review_satisfied or decision.bypass_applied:
            raise ValueError("required review flags are inconsistent")
        return
    if decision.status is ImaginedSafeExperimentReviewGateStatus.REVIEW_APPROVED:
        if not has_permission_ids or decision.bypass_policy_code is not None:
            raise ValueError("approved review requires permission evidence only")
        if decision.review_required or not decision.review_satisfied or decision.bypass_applied:
            raise ValueError("approved review flags are inconsistent")
        return
    if decision.status in (
        ImaginedSafeExperimentReviewGateStatus.REVIEW_REJECTED,
        ImaginedSafeExperimentReviewGateStatus.REVIEW_DEFERRED,
    ):
        if not has_permission_ids or decision.bypass_policy_code is not None:
            raise ValueError("review disposition requires permission evidence only")
        if decision.review_required or decision.review_satisfied or decision.bypass_applied:
            raise ValueError("review disposition flags are inconsistent")
        return
    if decision.status is ImaginedSafeExperimentReviewGateStatus.EXPLICIT_NON_TRAINING_BYPASS:
        if decision.mode is not ImaginedSafeExperimentReviewMode.NON_TRAINING:
            raise ValueError("review bypass requires non-training mode")
        if has_permission_ids or decision.bypass_policy_code is None:
            raise ValueError("review bypass requires policy evidence without permission evidence")
        if decision.review_required or decision.review_satisfied or not decision.bypass_applied:
            raise ValueError("review bypass flags are inconsistent")
        return
    raise ValueError("unsupported review-gate status")


def _revalidate_proposal_result(source: ImaginedSafeExperimentProposalResult) -> None:
    ImaginedSafeExperimentProposalResult(
        result_id=source.result_id,
        request=source.request,
        proposal=source.proposal,
        factual_confidence_change=source.factual_confidence_change,
        mastery_change=source.mastery_change,
        competence_change=source.competence_change,
        growth_pressure_change=source.growth_pressure_change,
        replay_evidence_change=source.replay_evidence_change,
        real_observation_change=source.real_observation_change,
        has_action_selection_authority=source.has_action_selection_authority,
        has_production_action_authority=source.has_production_action_authority,
    )


def _revalidate_permission_result(source: ImaginedSafeExperimentPermissionResult) -> None:
    ImaginedSafeExperimentPermissionResult(
        result_id=source.result_id,
        request=source.request,
        decision=source.decision,
        factual_confidence_change=source.factual_confidence_change,
        mastery_change=source.mastery_change,
        competence_change=source.competence_change,
        growth_pressure_change=source.growth_pressure_change,
        replay_evidence_change=source.replay_evidence_change,
        real_observation_change=source.real_observation_change,
        has_action_selection_authority=source.has_action_selection_authority,
        has_production_action_authority=source.has_production_action_authority,
    )


def _canonical_json_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    return f"{prefix}:{hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()}"


def _validate_ascii_code(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or not value.isascii():
        raise ValueError(f"{name} must be a non-empty ASCII string")


def _validate_bounded_ascii_code(name: str, value: str, maximum: int) -> None:
    _validate_ascii_code(name, value)
    if len(value) > maximum:
        raise ValueError(f"{name} exceeds configured character bound")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_zero_delta(name: str, value: float) -> None:
    if not isinstance(value, float) or not isfinite(value) or value != 0.0:
        raise ValueError(f"{name} must remain exactly zero")


__all__ = [
    "BoundedImaginedSafeExperimentReviewGate",
    "BoundedSafeExperimentReviewGateConfig",
    "ImaginedSafeExperimentReviewGateDecision",
    "ImaginedSafeExperimentReviewGateRequest",
    "ImaginedSafeExperimentReviewGateResult",
    "ImaginedSafeExperimentReviewGateStatus",
    "ImaginedSafeExperimentReviewMode",
]
