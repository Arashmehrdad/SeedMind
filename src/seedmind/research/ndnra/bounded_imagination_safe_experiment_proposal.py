"""Caller-nominated safe-experiment proposal contracts over Batch 5 uncertainty."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from math import isfinite

from seedmind.research.ndnra.bounded_imagination_uncertainty import (
    ImaginedComparisonUncertaintyIssue,
    ImaginedComparisonUncertaintyResult,
)
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin


@dataclass(frozen=True, slots=True)
class ImaginedSafeExperimentProposalRequest:
    """One explicit Batch 5 issue plus caller-supplied proposal semantics."""

    source_result: ImaginedComparisonUncertaintyResult
    issue_id: str
    hypothesis: str
    predicted_benefit: str
    uncertainty: str
    possible_harm: str
    reversibility: str
    stop_conditions: str
    stop_condition_codes: tuple[str, ...]
    required_permission: str
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
        _validate_ascii_code("issue_id", self.issue_id)
        if self.nominated_issue.issue_id != self.issue_id:
            raise ValueError("nominated issue lookup is inconsistent")
        for name, value in (
            ("hypothesis", self.hypothesis),
            ("predicted_benefit", self.predicted_benefit),
            ("uncertainty", self.uncertainty),
            ("possible_harm", self.possible_harm),
            ("reversibility", self.reversibility),
            ("stop_conditions", self.stop_conditions),
            ("required_permission", self.required_permission),
        ):
            _validate_ascii_code(name, value)
        _validate_sorted_unique_ascii_codes(
            "stop_condition_codes",
            self.stop_condition_codes,
        )
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("safe experiment proposal requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("safe experiment proposal requests cannot control production actions")

    @property
    def nominated_issue(self) -> ImaginedComparisonUncertaintyIssue:
        matches = tuple(
            issue for issue in self.source_result.issues if issue.issue_id == self.issue_id
        )
        if len(matches) != 1:
            raise ValueError("issue_id must match exactly one source uncertainty issue")
        return matches[0]

    @property
    def request_id(self) -> str:
        return _identity(
            "imagined-safe-experiment-proposal-request",
            self._identity_payload(),
        )

    def snapshot(self) -> dict[str, object]:
        return {"request_id": self.request_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "source_result": self.source_result.snapshot(),
            "issue_id": self.issue_id,
            "hypothesis": self.hypothesis,
            "predicted_benefit": self.predicted_benefit,
            "uncertainty": self.uncertainty,
            "possible_harm": self.possible_harm,
            "reversibility": self.reversibility,
            "stop_conditions": self.stop_conditions,
            "stop_condition_codes": list(self.stop_condition_codes),
            "required_permission": self.required_permission,
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
class ImaginedSafeExperimentProposal:
    """One caller-defined proposal tied exactly to one audited uncertainty issue."""

    proposal_id: str
    origin: ExperienceOrigin
    source_result_id: str
    source_request_id: str
    source_issue: ImaginedComparisonUncertaintyIssue
    hypothesis: str
    predicted_benefit: str
    uncertainty: str
    possible_harm: str
    reversibility: str
    stop_conditions: str
    stop_condition_codes: tuple[str, ...]
    required_permission: str
    factual_confidence_change: float = 0.0
    mastery_change: float = 0.0
    competence_change: float = 0.0
    growth_pressure_change: float = 0.0
    replay_evidence_change: float = 0.0
    real_observation_change: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("proposal_id", self.proposal_id)
        _validate_ascii_code("source_result_id", self.source_result_id)
        _validate_ascii_code("source_request_id", self.source_request_id)
        if self.origin is not ExperienceOrigin.IMAGINED:
            raise ValueError("safe experiment proposals require imagined origin")
        for name, value in (
            ("hypothesis", self.hypothesis),
            ("predicted_benefit", self.predicted_benefit),
            ("uncertainty", self.uncertainty),
            ("possible_harm", self.possible_harm),
            ("reversibility", self.reversibility),
            ("stop_conditions", self.stop_conditions),
            ("required_permission", self.required_permission),
        ):
            _validate_ascii_code(name, value)
        _validate_sorted_unique_ascii_codes(
            "stop_condition_codes",
            self.stop_condition_codes,
        )
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("safe experiment proposals cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("safe experiment proposals cannot control production actions")
        if self.proposal_id != _identity(
            "imagined-safe-experiment-proposal",
            self._identity_payload(),
        ):
            raise ValueError("safe experiment proposal identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"proposal_id": self.proposal_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "origin": self.origin.value,
            "source_result_id": self.source_result_id,
            "source_request_id": self.source_request_id,
            "source_issue": self.source_issue.snapshot(),
            "hypothesis": self.hypothesis,
            "predicted_benefit": self.predicted_benefit,
            "uncertainty": self.uncertainty,
            "possible_harm": self.possible_harm,
            "reversibility": self.reversibility,
            "stop_conditions": self.stop_conditions,
            "stop_condition_codes": list(self.stop_condition_codes),
            "required_permission": self.required_permission,
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
class ImaginedSafeExperimentProposalResult:
    """One in-memory proposal result with no scheduling, execution, or persistence."""

    result_id: str
    request: ImaginedSafeExperimentProposalRequest
    proposal: ImaginedSafeExperimentProposal
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
        expected_proposal = BoundedImaginedSafeExperimentProposer()._proposal_for(self.request)
        if self.proposal != expected_proposal:
            raise ValueError("safe experiment proposal is inconsistent with request")
        _validate_zero_delta("factual_confidence_change", self.factual_confidence_change)
        _validate_zero_delta("mastery_change", self.mastery_change)
        _validate_zero_delta("competence_change", self.competence_change)
        _validate_zero_delta("growth_pressure_change", self.growth_pressure_change)
        _validate_zero_delta("replay_evidence_change", self.replay_evidence_change)
        _validate_zero_delta("real_observation_change", self.real_observation_change)
        if self.has_action_selection_authority:
            raise ValueError("safe experiment proposal results cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("safe experiment proposal results cannot control production actions")
        if self.result_id != _identity(
            "imagined-safe-experiment-proposal-result",
            self._identity_payload(),
        ):
            raise ValueError("safe experiment proposal result identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def snapshot_json_ascii(self) -> bytes:
        return _canonical_json_bytes(self.snapshot())

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "proposal": self.proposal.snapshot(),
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
class BoundedImaginedSafeExperimentProposer:
    """Construct caller-specified proposal contracts without inference or authority."""

    def propose(
        self,
        request: ImaginedSafeExperimentProposalRequest,
    ) -> ImaginedSafeExperimentProposalResult:
        proposal = self._proposal_for(request)
        payload = {
            "request": request.snapshot(),
            "proposal": proposal.snapshot(),
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedSafeExperimentProposalResult(
            result_id=_identity("imagined-safe-experiment-proposal-result", payload),
            request=request,
            proposal=proposal,
        )

    def _proposal_for(
        self,
        request: ImaginedSafeExperimentProposalRequest,
    ) -> ImaginedSafeExperimentProposal:
        issue = request.nominated_issue
        payload = {
            "origin": ExperienceOrigin.IMAGINED.value,
            "source_result_id": request.source_result.result_id,
            "source_request_id": request.source_result.request.request_id,
            "source_issue": issue.snapshot(),
            "hypothesis": request.hypothesis,
            "predicted_benefit": request.predicted_benefit,
            "uncertainty": request.uncertainty,
            "possible_harm": request.possible_harm,
            "reversibility": request.reversibility,
            "stop_conditions": request.stop_conditions,
            "stop_condition_codes": list(request.stop_condition_codes),
            "required_permission": request.required_permission,
            "factual_confidence_change": 0.0,
            "mastery_change": 0.0,
            "competence_change": 0.0,
            "growth_pressure_change": 0.0,
            "replay_evidence_change": 0.0,
            "real_observation_change": 0.0,
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }
        return ImaginedSafeExperimentProposal(
            proposal_id=_identity("imagined-safe-experiment-proposal", payload),
            origin=ExperienceOrigin.IMAGINED,
            source_result_id=request.source_result.result_id,
            source_request_id=request.source_result.request.request_id,
            source_issue=issue,
            hypothesis=request.hypothesis,
            predicted_benefit=request.predicted_benefit,
            uncertainty=request.uncertainty,
            possible_harm=request.possible_harm,
            reversibility=request.reversibility,
            stop_conditions=request.stop_conditions,
            stop_condition_codes=request.stop_condition_codes,
            required_permission=request.required_permission,
        )


def _revalidate_source_result(source: ImaginedComparisonUncertaintyResult) -> None:
    ImaginedComparisonUncertaintyResult(
        result_id=source.result_id,
        request=source.request,
        issues=source.issues,
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


def _validate_sorted_unique_ascii_codes(name: str, values: Sequence[str]) -> None:
    if any(not isinstance(value, str) or not value or not value.isascii() for value in values):
        raise ValueError(f"{name} must contain non-empty ASCII strings")
    if tuple(values) != tuple(sorted(values)):
        raise ValueError(f"{name} must be sorted")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must be unique")


def _validate_zero_delta(name: str, value: float) -> None:
    if not isinstance(value, float) or not isfinite(value) or value != 0.0:
        raise ValueError(f"{name} must remain exactly zero")


__all__ = [
    "BoundedImaginedSafeExperimentProposer",
    "ImaginedSafeExperimentProposal",
    "ImaginedSafeExperimentProposalRequest",
    "ImaginedSafeExperimentProposalResult",
]
