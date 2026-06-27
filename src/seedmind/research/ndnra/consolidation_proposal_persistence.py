"""Versioned checkpoint codec for restart-safe NDNRA proposal lifecycles."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite

from seedmind.research.ndnra.consolidation import ConsolidationCandidate
from seedmind.research.ndnra.consolidation_proposal_history import (
    ConsolidationProposalLifecycleRecord,
)
from seedmind.research.ndnra.consolidation_proposal_lifecycle import (
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewDecision,
    ConsolidationProposalReviewPolicy,
    ConsolidationProposalReviewRequest,
)
from seedmind.research.ndnra.consolidation_proposal_management import (
    ConsolidationProposalDisposition,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalManagedRecord,
    ConsolidationProposalManagementAction,
    ConsolidationProposalManagementDecision,
)
from seedmind.research.ndnra.consolidation_scheduling import (
    ConsolidationScheduleProposal,
)
from seedmind.research.ndnra.contextual_memory import LessonIdentity, MasteryProfile

PROPOSAL_LIFECYCLE_SCHEMA = "seedmind.ndnra.proposal_lifecycle"
PROPOSAL_LIFECYCLE_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class NDNRAProposalLifecycleCheckpoint:
    """Versioned non-executable checkpoint for one complete lifecycle registry."""

    registry: ConsolidationProposalLifecycleRegistry = field(
        default_factory=ConsolidationProposalLifecycleRegistry
    )
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_execution_authority:
            raise ValueError("proposal lifecycle checkpoints never have execution authority")
        _validate_replacement_links(self.registry)

    @classmethod
    def empty(cls) -> NDNRAProposalLifecycleCheckpoint:
        """Return the explicit migration target for schemas without lifecycle state."""
        return cls()

    def snapshot(self) -> dict[str, object]:
        """Return deterministic JSON-safe checkpoint evidence."""
        return {
            "schema": PROPOSAL_LIFECYCLE_SCHEMA,
            "schema_version": PROPOSAL_LIFECYCLE_SCHEMA_VERSION,
            "registry": _json_ready(self.registry.snapshot()),
            "has_execution_authority": self.has_execution_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> NDNRAProposalLifecycleCheckpoint:
        """Reconstruct exact lifecycle evidence without invoking cognition."""
        values = _require_mapping("proposal lifecycle checkpoint", snapshot)
        if _require_string(values, "schema") != PROPOSAL_LIFECYCLE_SCHEMA:
            raise ValueError("proposal lifecycle checkpoint schema is incompatible")
        if _require_int(values, "schema_version") != PROPOSAL_LIFECYCLE_SCHEMA_VERSION:
            raise ValueError("proposal lifecycle checkpoint version is incompatible")
        checkpoint = cls(
            registry=_restore_registry(values.get("registry")),
            has_execution_authority=_require_bool(
                values,
                "has_execution_authority",
            ),
        )
        if checkpoint.snapshot() != dict(values):
            raise ValueError("proposal lifecycle checkpoint did not round-trip exactly")
        return checkpoint


def _restore_registry(snapshot: object) -> ConsolidationProposalLifecycleRegistry:
    values = _require_mapping("proposal lifecycle registry", snapshot)
    registry = ConsolidationProposalLifecycleRegistry(
        records=tuple(_restore_managed_record(item) for item in _require_list(values, "records")),
        maximum_active_records=_require_positive_int(
            values,
            "maximum_active_records",
        ),
        has_execution_authority=_require_bool(
            values,
            "has_execution_authority",
        ),
    )
    _validate_replacement_links(registry)
    if _require_nonnegative_int(values, "active_record_count") != len(registry.active_records):
        raise ValueError("persisted active lifecycle count does not match contents")
    if _json_ready(registry.snapshot()) != dict(values):
        raise ValueError("proposal lifecycle registry did not round-trip exactly")
    return registry


def _restore_managed_record(snapshot: object) -> ConsolidationProposalManagedRecord:
    values = _require_mapping("managed proposal lifecycle record", snapshot)
    lifecycle = _restore_lifecycle_record(values.get("lifecycle"))
    raw_management = values.get("management_decision")
    management = (
        None
        if raw_management is None
        else _restore_management_decision(raw_management, lifecycle=lifecycle)
    )
    record = ConsolidationProposalManagedRecord(
        lifecycle=lifecycle,
        disposition=ConsolidationProposalDisposition(_require_string(values, "disposition")),
        management_decision=management,
        has_execution_authority=_require_bool(
            values,
            "has_execution_authority",
        ),
    )
    if _require_bool(values, "is_active") is not record.is_active:
        raise ValueError("persisted managed-record active state does not match contents")
    if _json_ready(record.snapshot()) != dict(values):
        raise ValueError("managed proposal lifecycle record did not round-trip exactly")
    return record


def _restore_lifecycle_record(snapshot: object) -> ConsolidationProposalLifecycleRecord:
    values = _require_mapping("proposal lifecycle record", snapshot)
    proposal = _restore_proposal(values.get("proposal"))
    decisions = tuple(_restore_review_decision(item) for item in _require_list(values, "decisions"))
    record = ConsolidationProposalLifecycleRecord(
        proposal=proposal,
        status=ConsolidationProposalLifecycleStatus(_require_string(values, "status")),
        decisions=decisions,
        has_execution_authority=_require_bool(
            values,
            "has_execution_authority",
        ),
    )
    raw_defer = values.get("current_defer_until_episode")
    stored_defer = (
        None
        if raw_defer is None
        else _require_nonnegative_int(values, "current_defer_until_episode")
    )
    if stored_defer != record.current_defer_until_episode:
        raise ValueError("persisted deferral boundary does not match lifecycle history")
    if _json_ready(record.snapshot()) != dict(values):
        raise ValueError("proposal lifecycle record did not round-trip exactly")
    return record


def _restore_review_decision(snapshot: object) -> ConsolidationProposalReviewDecision:
    values = _require_mapping("proposal review decision", snapshot)
    proposal = _restore_proposal(values.get("proposal"))
    raw_defer = values.get("defer_until_episode")
    request = ConsolidationProposalReviewRequest(
        proposal=proposal,
        action=ConsolidationProposalReviewAction(_require_string(values, "action")),
        decision_episode=_require_nonnegative_int(values, "decision_episode"),
        reviewer_code=_require_string(values, "reviewer_code"),
        reason_code=_require_string(values, "reason_code"),
        defer_until_episode=(
            None if raw_defer is None else _require_nonnegative_int(values, "defer_until_episode")
        ),
    )
    decision = ConsolidationProposalReviewPolicy().evaluate(request)
    if _require_string(values, "decision_id") != decision.decision_id:
        raise ValueError("persisted proposal review decision identity is invalid")
    if _require_string(values, "status") != decision.status.value:
        raise ValueError("persisted proposal review status is inconsistent")
    if _require_bool(values, "has_execution_authority"):
        raise ValueError("persisted proposal review decision cannot have execution authority")
    if _json_ready(decision.snapshot()) != dict(values):
        raise ValueError("proposal review decision did not round-trip exactly")
    return decision


def _restore_management_decision(
    snapshot: object,
    *,
    lifecycle: ConsolidationProposalLifecycleRecord,
) -> ConsolidationProposalManagementDecision:
    values = _require_mapping("proposal management decision", snapshot)
    action = ConsolidationProposalManagementAction(_require_string(values, "action"))
    raw_replacement = values.get("replacement_proposal")
    replacement = None if raw_replacement is None else _restore_proposal(raw_replacement)
    decision = ConsolidationProposalManagementDecision(
        decision_id=_require_string(values, "decision_id"),
        target_proposal_id=_require_string(values, "target_proposal_id"),
        target_candidate_id=_require_string(values, "target_candidate_id"),
        action=action,
        disposition=ConsolidationProposalDisposition(_require_string(values, "disposition")),
        decision_episode=_require_nonnegative_int(values, "decision_episode"),
        reviewer_code=_require_string(values, "reviewer_code"),
        reason_code=_require_string(values, "reason_code"),
        replacement_proposal=replacement,
        has_execution_authority=_require_bool(
            values,
            "has_execution_authority",
        ),
    )
    if decision.decision_id != _management_decision_id(
        lifecycle=lifecycle,
        decision=decision,
    ):
        raise ValueError("persisted proposal management decision identity is invalid")
    if _json_ready(decision.snapshot()) != dict(values):
        raise ValueError("proposal management decision did not round-trip exactly")
    return decision


def _restore_proposal(snapshot: object) -> ConsolidationScheduleProposal:
    values = _require_mapping("consolidation schedule proposal", snapshot)
    proposal = ConsolidationScheduleProposal(
        proposal_id=_require_string(values, "proposal_id"),
        candidate=_restore_candidate(values.get("candidate")),
        proposed_episode=_require_nonnegative_int(values, "proposed_episode"),
        due_episode=_require_nonnegative_int(values, "due_episode"),
        has_execution_authority=_require_bool(
            values,
            "has_execution_authority",
        ),
    )
    if proposal.snapshot() != dict(values):
        raise ValueError("consolidation schedule proposal did not round-trip exactly")
    return proposal


def _restore_candidate(snapshot: object) -> ConsolidationCandidate:
    values = _require_mapping("consolidation candidate", snapshot)
    lesson_values = _require_mapping(
        "lesson identity",
        values.get("lesson_identity"),
    )
    candidate = ConsolidationCandidate(
        candidate_id=_require_string(values, "candidate_id"),
        lesson_identity=LessonIdentity(
            need_code=_require_string(lesson_values, "need_code"),
            effect_code=_require_string(lesson_values, "effect_code"),
            desired_direction=_require_float(
                lesson_values,
                "desired_direction",
            ),
        ),
        source_event_ids=tuple(_require_string_list(values, "source_event_ids")),
        assembly_ids=tuple(_require_string_list(values, "assembly_ids")),
        route_ids=tuple(_require_string_list(values, "route_ids")),
        mastery_snapshot=_restore_mastery_profile(values.get("mastery_snapshot")),
        requested_stability_increment=_require_float(
            values,
            "requested_stability_increment",
        ),
        requested_plasticity_reduction=_require_float(
            values,
            "requested_plasticity_reduction",
        ),
    )
    if candidate.mastery_snapshot.source_event_ids != candidate.source_event_ids:
        raise ValueError("candidate mastery sources must match candidate sources")
    if not candidate.mastery_snapshot.broad_mastery:
        raise ValueError("persisted proposal candidate must preserve broad mastery")
    if candidate.mastery_snapshot.contradiction_count != 0:
        raise ValueError("persisted proposal candidate must start contradiction-free")
    if candidate.snapshot() != dict(values):
        raise ValueError("consolidation candidate did not round-trip exactly")
    return candidate


def _restore_mastery_profile(snapshot: object) -> MasteryProfile:
    values = _require_mapping("mastery profile", snapshot)
    profile = MasteryProfile(
        raw_repetition_count=_require_nonnegative_int(
            values,
            "raw_repetition_count",
        ),
        effective_support=_require_nonnegative_float(
            values,
            "effective_support",
        ),
        unique_context_count=_require_nonnegative_int(
            values,
            "unique_context_count",
        ),
        unique_route_count=_require_nonnegative_int(
            values,
            "unique_route_count",
        ),
        contradiction_count=_require_nonnegative_int(
            values,
            "contradiction_count",
        ),
        repetition_strength=_require_unit(values, "repetition_strength"),
        context_diversity=_require_unit(values, "context_diversity"),
        route_diversity=_require_unit(values, "route_diversity"),
        causal_consistency=_require_unit(values, "causal_consistency"),
        transfer_success=_require_unit(values, "transfer_success"),
        protective_strength=_require_unit(values, "protective_strength"),
        mastery_score=_require_unit(values, "mastery_score"),
        broad_mastery=_require_bool(values, "broad_mastery"),
        source_event_ids=tuple(_require_string_list(values, "source_event_ids")),
    )
    _validate_sorted_unique_codes(
        "mastery source_event_ids",
        profile.source_event_ids,
    )
    if profile.snapshot() != dict(values):
        raise ValueError("mastery profile did not round-trip exactly")
    return profile


def _management_decision_id(
    *,
    lifecycle: ConsolidationProposalLifecycleRecord,
    decision: ConsolidationProposalManagementDecision,
) -> str:
    payload = {
        "target_proposal_id": decision.target_proposal_id,
        "expected_candidate_id": decision.target_candidate_id,
        "action": decision.action.value,
        "decision_episode": decision.decision_episode,
        "reviewer_code": decision.reviewer_code,
        "reason_code": decision.reason_code,
        "replacement_proposal": (
            None
            if decision.replacement_proposal is None
            else decision.replacement_proposal.snapshot()
        ),
        "lifecycle": lifecycle.snapshot(),
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"consolidation-management:{hashlib.sha256(canonical).hexdigest()}"


def _validate_replacement_links(
    registry: ConsolidationProposalLifecycleRegistry,
) -> None:
    by_proposal = {record.proposal.proposal_id: record for record in registry.records}
    for record in registry.records:
        if record.disposition is not ConsolidationProposalDisposition.REPLACED:
            continue
        decision = record.management_decision
        if decision is None or decision.replacement_proposal is None:
            raise ValueError("replaced lifecycle record requires replacement evidence")
        replacement = decision.replacement_proposal
        retained = by_proposal.get(replacement.proposal_id)
        if retained is None or retained.proposal != replacement:
            raise ValueError("replacement proposal must exist as an exact retained record")
        if replacement.candidate.lesson_identity != record.proposal.candidate.lesson_identity:
            raise ValueError("replacement proposal must preserve lesson identity")
        if replacement.proposed_episode <= record.proposal.proposed_episode:
            raise ValueError("replacement proposal must be newer than replaced proposal")
        if replacement.proposed_episode > decision.decision_episode:
            raise ValueError("replacement proposal cannot postdate management decision")


def _json_ready(value: object) -> object:
    if isinstance(value, dict):
        return {str(key): _json_ready(item) for key, item in value.items()}
    if isinstance(value, tuple | list):
        return [_json_ready(item) for item in value]
    return value


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_list(values: Mapping[str, object], key: str) -> list[object]:
    value = values.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str) or not value.strip() or not value.isascii():
        raise ValueError(f"{key} must be non-empty ASCII text")
    return value


def _require_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_nonnegative_int(values: Mapping[str, object], key: str) -> int:
    value = _require_int(values, key)
    if value < 0:
        raise ValueError(f"{key} must not be negative")
    return value


def _require_positive_int(values: Mapping[str, object], key: str) -> int:
    value = _require_int(values, key)
    if value <= 0:
        raise ValueError(f"{key} must be positive")
    return value


def _require_float(values: Mapping[str, object], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    result = float(value)
    if not isfinite(result):
        raise ValueError(f"{key} must be finite")
    return result


def _require_nonnegative_float(
    values: Mapping[str, object],
    key: str,
) -> float:
    value = _require_float(values, key)
    if value < 0.0:
        raise ValueError(f"{key} must not be negative")
    return value


def _require_unit(values: Mapping[str, object], key: str) -> float:
    value = _require_float(values, key)
    if not 0.0 <= value <= 1.0:
        raise ValueError(f"{key} must be between zero and one")
    return value


def _require_string_list(values: Mapping[str, object], key: str) -> list[str]:
    result: list[str] = []
    for item in _require_list(values, key):
        if not isinstance(item, str) or not item.strip() or not item.isascii():
            raise ValueError(f"{key} must contain non-empty ASCII strings")
        result.append(item)
    return result


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
