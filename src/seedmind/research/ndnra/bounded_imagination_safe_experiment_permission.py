"""Optional training-time human review for one imagined safe-experiment proposal."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.bounded_imagination_safe_experiment_proposal import (
    ImaginedSafeExperimentProposal,
    ImaginedSafeExperimentProposalResult,
)
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin


class ImaginedSafeExperimentPermissionAction(StrEnum):
    """Explicit human disposition for one exact imagined proposal."""

    APPROVE = "approve"
    REJECT = "reject"
    DEFER = "defer"


@dataclass(frozen=True, slots=True)
class BoundedSafeExperimentPermissionConfig:
    """Finite limits for one in-memory human permission review."""

    maximum_source_snapshot_bytes: int = 1_000_000
    maximum_expected_permission_characters: int = 256
    maximum_reviewer_code_characters: int = 128
    maximum_reason_code_characters: int = 256

    def __post_init__(self) -> None:
        for name, value in (
            ("maximum_source_snapshot_bytes", self.maximum_source_snapshot_bytes),
            (
                "maximum_expected_permission_characters",
                self.maximum_expected_permission_characters,
            ),
            ("maximum_reviewer_code_characters", self.maximum_reviewer_code_characters),
            ("maximum_reason_code_characters", self.maximum_reason_code_characters),
        ):
            _validate_positive_int(name, value)

    def snapshot(self) -> dict[str, object]:
        return {
            "maximum_source_snapshot_bytes": self.maximum_source_snapshot_bytes,
            "maximum_expected_permission_characters": (self.maximum_expected_permission_characters),
            "maximum_reviewer_code_characters": self.maximum_reviewer_code_characters,
            "maximum_reason_code_characters": self.maximum_reason_code_characters,
        }


@dataclass(frozen=True, slots=True)
class ImaginedSafeExperimentPermissionRequest:
    """One explicit human review request over one complete Batch 6 result."""

    source_result: ImaginedSafeExperimentProposalResult
    expected_proposal_id: str
    expected_required_permission: str
    action: ImaginedSafeExperimentPermissionAction
    reviewer_code: str
    reason_code: str
    acknowledges_predicted_benefit: bool
    acknowledges_uncertainty: bool
    acknowledges_possible_harm: bool
    acknowledges_reversibility: bool
    acknowledges_stop_conditions: bool
    config: BoundedSafeExperimentPermissionConfig = field(
        default_factory=BoundedSafeExperimentPermissionConfig
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
        _revalidate_source_result(self.source_result)
        if not isinstance(self.action, ImaginedSafeExperimentPermissionAction):
            raise ValueError("action must be an imagined safe-experiment permission action")
        if (
            len(self.source_result.snapshot_json_ascii())
            > self.config.maximum_source_snapshot_bytes
        ):
            raise ValueError("source proposal result exceeds permission-review byte bound")
        _validate_bounded_ascii_code(
            "expected_proposal_id",
            self.expected_proposal_id,
            self.config.maximum_expected_permission_characters,
        )
        _validate_bounded_ascii_code(
            "expected_required_permission",
            self.expected_required_permission,
            self.config.maximum_expected_permission_characters,
        )
        _validate_bounded_ascii_code(
            "reviewer_code",
            self.reviewer_code,
            self.config.maximum_reviewer_code_characters,
        )
        if not self.reviewer_code.startswith("human:"):
            raise ValueError("reviewer_code must identify an explicit human reviewer")
        _validate_bounded_ascii_code(
            "reason_code",
            self.reason_code,
            self.config.maximum_reason_code_characters,
        )
        if self.expected_proposal_id != self.source_result.proposal.proposal_id:
            raise ValueError("permission request targets a different proposal")
        if self.expected_required_permission != self.source_result.proposal.required_permission:
            raise ValueError("permission request targets a different required permission")
        for name, value in self._acknowledgements().items():
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be boolean")
        if self.action is ImaginedSafeExperimentPermissionAction.APPROVE and not all(
            self._acknowledgements().values()
        ):
            raise ValueError(
                "approval requires explicit acknowledgement of every proposal risk field"
            )
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("permission review requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("permission review requests cannot control production actions")

    @property
    def request_id(self) -> str:
        return _identity(
            "imagined-safe-experiment-permission-request",
            self._identity_payload(),
        )

    def snapshot(self) -> dict[str, object]:
        return {"request_id": self.request_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _acknowledgements(self) -> dict[str, bool]:
        return {
            "acknowledges_predicted_benefit": self.acknowledges_predicted_benefit,
            "acknowledges_uncertainty": self.acknowledges_uncertainty,
            "acknowledges_possible_harm": self.acknowledges_possible_harm,
            "acknowledges_reversibility": self.acknowledges_reversibility,
            "acknowledges_stop_conditions": self.acknowledges_stop_conditions,
        }

    def _identity_payload(self) -> dict[str, object]:
        return {
            "source_result": self.source_result.snapshot(),
            "expected_proposal_id": self.expected_proposal_id,
            "expected_required_permission": self.expected_required_permission,
            "action": self.action.value,
            "reviewer_code": self.reviewer_code,
            "reason_code": self.reason_code,
            **self._acknowledgements(),
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
class ImaginedSafeExperimentPermissionDecision:
    """Human permission evidence that performs no scheduling or execution."""

    decision_id: str
    proposal_origin: ExperienceOrigin
    source_result_id: str
    source_request_id: str
    source_proposal: ImaginedSafeExperimentProposal
    action: ImaginedSafeExperimentPermissionAction
    reviewer_code: str
    reason_code: str
    required_permission: str
    acknowledges_predicted_benefit: bool
    acknowledges_uncertainty: bool
    acknowledges_possible_harm: bool
    acknowledges_reversibility: bool
    acknowledges_stop_conditions: bool
    permission_granted: bool
    review_deferred: bool
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
        _validate_ascii_code("reviewer_code", self.reviewer_code)
        if not self.reviewer_code.startswith("human:"):
            raise ValueError("permission decision requires an explicit human reviewer")
        _validate_ascii_code("reason_code", self.reason_code)
        _validate_ascii_code("required_permission", self.required_permission)
        if not isinstance(self.action, ImaginedSafeExperimentPermissionAction):
            raise ValueError("action must be an imagined safe-experiment permission action")
        if self.proposal_origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("safe-experiment permission decisions require imagined source")
        for name, value in self._acknowledgements().items():
            if not isinstance(value, bool):
                raise ValueError(f"{name} must be boolean")
        expected_granted = self.action is ImaginedSafeExperimentPermissionAction.APPROVE
        expected_deferred = self.action is ImaginedSafeExperimentPermissionAction.DEFER
        if self.permission_granted is not expected_granted:
            raise ValueError("permission_granted is inconsistent with review action")
        if self.review_deferred is not expected_deferred:
            raise ValueError("review_deferred is inconsistent with review action")
        if self.permission_granted and not all(self._acknowledgements().values()):
            raise ValueError("granted permission requires all acknowledgements")
        if self.required_permission != self.source_proposal.required_permission:
            raise ValueError("permission decision required permission mismatch")
        if self.authorizes_execution:
            raise ValueError("permission decisions cannot execute experiments")
        if self.authorizes_scheduling:
            raise ValueError("permission decisions cannot schedule experiments")
        if self.authorizes_persistence:
            raise ValueError("permission decisions cannot persist experiments")
        if self.authorizes_live_integration:
            raise ValueError("permission decisions cannot integrate experiments live")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("permission decisions cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("permission decisions cannot control production actions")
        if self.decision_id != _identity(
            "imagined-safe-experiment-permission-decision",
            self._identity_payload(),
        ):
            raise ValueError("permission decision identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"decision_id": self.decision_id, **self._identity_payload()}

    def _acknowledgements(self) -> dict[str, bool]:
        return {
            "acknowledges_predicted_benefit": self.acknowledges_predicted_benefit,
            "acknowledges_uncertainty": self.acknowledges_uncertainty,
            "acknowledges_possible_harm": self.acknowledges_possible_harm,
            "acknowledges_reversibility": self.acknowledges_reversibility,
            "acknowledges_stop_conditions": self.acknowledges_stop_conditions,
        }

    def _identity_payload(self) -> dict[str, object]:
        return {
            "proposal_origin": self.proposal_origin.value,
            "source_result_id": self.source_result_id,
            "source_request_id": self.source_request_id,
            "source_proposal": self.source_proposal.snapshot(),
            "action": self.action.value,
            "reviewer_code": self.reviewer_code,
            "reason_code": self.reason_code,
            "required_permission": self.required_permission,
            **self._acknowledgements(),
            "permission_granted": self.permission_granted,
            "review_deferred": self.review_deferred,
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
class ImaginedSafeExperimentPermissionResult:
    """One deterministic permission review result with no execution path."""

    result_id: str
    request: ImaginedSafeExperimentPermissionRequest
    decision: ImaginedSafeExperimentPermissionDecision
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
        expected = BoundedImaginedSafeExperimentPermissionReviewer()._decision_for(self.request)
        if self.decision != expected:
            raise ValueError("permission decision is inconsistent with request")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("permission review results cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("permission review results cannot control production actions")
        if self.result_id != _identity(
            "imagined-safe-experiment-permission-result",
            self._identity_payload(),
        ):
            raise ValueError("permission result identity is inconsistent")

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
class BoundedImaginedSafeExperimentPermissionReviewer:
    """Record optional training-time human review without runtime authority."""

    def review(
        self,
        request: ImaginedSafeExperimentPermissionRequest,
    ) -> ImaginedSafeExperimentPermissionResult:
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
        return ImaginedSafeExperimentPermissionResult(
            result_id=_identity("imagined-safe-experiment-permission-result", payload),
            request=request,
            decision=decision,
        )

    def _decision_for(
        self,
        request: ImaginedSafeExperimentPermissionRequest,
    ) -> ImaginedSafeExperimentPermissionDecision:
        proposal = request.source_result.proposal
        payload = {
            "proposal_origin": proposal.origin.value,
            "source_result_id": request.source_result.result_id,
            "source_request_id": request.source_result.request.request_id,
            "source_proposal": proposal.snapshot(),
            "action": request.action.value,
            "reviewer_code": request.reviewer_code,
            "reason_code": request.reason_code,
            "required_permission": request.expected_required_permission,
            **request._acknowledgements(),
            "permission_granted": (
                request.action is ImaginedSafeExperimentPermissionAction.APPROVE
            ),
            "review_deferred": (request.action is ImaginedSafeExperimentPermissionAction.DEFER),
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
        return ImaginedSafeExperimentPermissionDecision(
            decision_id=_identity(
                "imagined-safe-experiment-permission-decision",
                payload,
            ),
            proposal_origin=proposal.origin,
            source_result_id=request.source_result.result_id,
            source_request_id=request.source_result.request.request_id,
            source_proposal=proposal,
            action=request.action,
            reviewer_code=request.reviewer_code,
            reason_code=request.reason_code,
            required_permission=request.expected_required_permission,
            acknowledges_predicted_benefit=request.acknowledges_predicted_benefit,
            acknowledges_uncertainty=request.acknowledges_uncertainty,
            acknowledges_possible_harm=request.acknowledges_possible_harm,
            acknowledges_reversibility=request.acknowledges_reversibility,
            acknowledges_stop_conditions=request.acknowledges_stop_conditions,
            permission_granted=(request.action is ImaginedSafeExperimentPermissionAction.APPROVE),
            review_deferred=(request.action is ImaginedSafeExperimentPermissionAction.DEFER),
        )


def _revalidate_source_result(source: ImaginedSafeExperimentProposalResult) -> None:
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
    "BoundedImaginedSafeExperimentPermissionReviewer",
    "BoundedSafeExperimentPermissionConfig",
    "ImaginedSafeExperimentPermissionAction",
    "ImaginedSafeExperimentPermissionDecision",
    "ImaginedSafeExperimentPermissionRequest",
    "ImaginedSafeExperimentPermissionResult",
]
