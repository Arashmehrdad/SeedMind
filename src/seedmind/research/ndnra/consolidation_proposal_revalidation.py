"""Pure restart-time revalidation for persisted NDNRA proposal lifecycles."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum

from seedmind.research.ndnra.consolidation import (
    ConsolidationCandidate,
    ConsolidationEligibilityPolicy,
    ConsolidationRejectionReason,
)
from seedmind.research.ndnra.consolidation_proposal_management import (
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalManagedRecord,
)
from seedmind.research.ndnra.consolidation_scheduling import (
    ConsolidationScheduleProposal,
)
from seedmind.research.ndnra.contextual_memory import (
    ContextualExperienceLedger,
    LessonIdentity,
    MasteryProfile,
)


class ConsolidationProposalRevalidationStatus(StrEnum):
    """Restart-time review classification with no lifecycle mutation authority."""

    CURRENT = "current"
    STALE = "stale"
    SUPERSEDED = "superseded"
    INVALID_FOR_REVIEW = "invalid_for_review"


@dataclass(frozen=True, slots=True)
class ConsolidationProposalRevalidationDecision:
    """Inspect one restored active proposal against current contextual evidence."""

    decision_id: str
    status: ConsolidationProposalRevalidationStatus
    proposal: ConsolidationScheduleProposal
    current_mastery: MasteryProfile
    current_candidate: ConsolidationCandidate | None
    superseding_proposal: ConsolidationScheduleProposal | None
    eligibility_reasons: tuple[ConsolidationRejectionReason, ...]
    source_events_available: bool
    broad_mastery_current: bool
    contradiction_free: bool
    assemblies_available: bool
    routes_available: bool
    candidate_identity_current: bool
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("decision_id", self.decision_id)
        if len(self.eligibility_reasons) != len(set(self.eligibility_reasons)):
            raise ValueError("revalidation eligibility reasons must be unique")
        if self.has_execution_authority:
            raise ValueError("revalidation decisions never have execution authority")
        if self.current_candidate is None and self.candidate_identity_current:
            raise ValueError("missing current candidate cannot match restored identity")
        if self.candidate_identity_current and self.current_candidate != self.proposal.candidate:
            raise ValueError("candidate identity flag requires exact candidate equality")
        if self.superseding_proposal is not None:
            if self.current_candidate is None:
                raise ValueError("superseding proposal requires one current candidate")
            if self.superseding_proposal.candidate != self.current_candidate:
                raise ValueError("superseding proposal must contain the exact current candidate")
            if (
                self.superseding_proposal.candidate.lesson_identity
                != self.proposal.candidate.lesson_identity
            ):
                raise ValueError("superseding proposal must preserve lesson identity")
            if self.superseding_proposal.proposed_episode <= self.proposal.proposed_episode:
                raise ValueError("superseding proposal must be newer")

        valid_evidence = bool(
            self.source_events_available
            and self.broad_mastery_current
            and self.contradiction_free
            and self.assemblies_available
            and self.routes_available
            and self.current_candidate is not None
            and not self.eligibility_reasons
        )
        if self.status is ConsolidationProposalRevalidationStatus.CURRENT:
            if not valid_evidence or not self.candidate_identity_current:
                raise ValueError("current status requires exact valid candidate evidence")
            if self.superseding_proposal is not None:
                raise ValueError("current status cannot contain a superseding proposal")
        elif self.status is ConsolidationProposalRevalidationStatus.STALE:
            if not valid_evidence or self.candidate_identity_current:
                raise ValueError("stale status requires valid changed candidate evidence")
            if self.superseding_proposal is not None:
                raise ValueError("stale status cannot contain a superseding proposal")
        elif self.status is ConsolidationProposalRevalidationStatus.SUPERSEDED:
            if not valid_evidence or self.superseding_proposal is None:
                raise ValueError("superseded status requires valid newer proposal evidence")
        elif valid_evidence:
            raise ValueError("invalid status requires at least one failed review invariant")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe revalidation evidence."""
        return {
            "decision_id": self.decision_id,
            "status": self.status.value,
            "proposal": self.proposal.snapshot(),
            "current_mastery": self.current_mastery.snapshot(),
            "current_candidate": (
                None if self.current_candidate is None else self.current_candidate.snapshot()
            ),
            "superseding_proposal": (
                None if self.superseding_proposal is None else self.superseding_proposal.snapshot()
            ),
            "eligibility_reasons": [reason.value for reason in self.eligibility_reasons],
            "source_events_available": self.source_events_available,
            "broad_mastery_current": self.broad_mastery_current,
            "contradiction_free": self.contradiction_free,
            "assemblies_available": self.assemblies_available,
            "routes_available": self.routes_available,
            "candidate_identity_current": self.candidate_identity_current,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationProposalRevalidationReport:
    """Pure ordered revalidation evidence for all active registry records."""

    decisions: tuple[ConsolidationProposalRevalidationDecision, ...]
    active_record_count: int
    archived_record_count: int
    registry_unchanged: bool
    has_execution_authority: bool = False

    def __post_init__(self) -> None:
        _validate_nonnegative_int("active_record_count", self.active_record_count)
        _validate_nonnegative_int("archived_record_count", self.archived_record_count)
        if len(self.decisions) != self.active_record_count:
            raise ValueError("revalidation decision count must match active record count")
        proposal_ids = tuple(decision.proposal.proposal_id for decision in self.decisions)
        if len(proposal_ids) != len(set(proposal_ids)):
            raise ValueError("revalidation report proposal identities must be unique")
        if not self.registry_unchanged:
            raise ValueError("revalidation must never mutate lifecycle registry state")
        if self.has_execution_authority:
            raise ValueError("revalidation reports never have execution authority")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ordered revalidation evidence."""
        return {
            "decisions": [decision.snapshot() for decision in self.decisions],
            "active_record_count": self.active_record_count,
            "archived_record_count": self.archived_record_count,
            "registry_unchanged": self.registry_unchanged,
            "has_execution_authority": self.has_execution_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationProposalRevalidationPolicy:
    """Revalidate restored proposal evidence without modifying lifecycle state."""

    eligibility_policy: ConsolidationEligibilityPolicy = field(
        default_factory=ConsolidationEligibilityPolicy
    )

    def evaluate(
        self,
        *,
        record: ConsolidationProposalManagedRecord,
        ledger: ContextualExperienceLedger,
        available_assembly_ids: Iterable[str],
        available_route_ids: Iterable[str],
        newer_same_lesson_proposals: Iterable[ConsolidationScheduleProposal] = (),
    ) -> ConsolidationProposalRevalidationDecision:
        """Classify one restored active record against current evidence."""
        if not record.is_active:
            raise ValueError("only active proposal lifecycle records may be revalidated")
        proposal = record.proposal
        candidate = proposal.candidate
        lesson = candidate.lesson_identity
        assemblies = _normalized_codes("available_assembly_ids", available_assembly_ids)
        routes = _normalized_codes("available_route_ids", available_route_ids)
        newer = _validated_newer_proposals(
            proposal=proposal,
            proposals=newer_same_lesson_proposals,
        )

        source_events_available = _source_events_available(
            ledger=ledger,
            lesson=lesson,
            source_event_ids=candidate.source_event_ids,
        )
        current_mastery = ledger.mastery_profile(lesson)
        broad_mastery_current = current_mastery.broad_mastery
        contradiction_free = (
            current_mastery.contradiction_count
            <= self.eligibility_policy.maximum_unresolved_contradictions
        )
        assemblies_available = set(candidate.assembly_ids).issubset(assemblies)
        routes_available = set(candidate.route_ids).issubset(routes)

        current_eligibility = self.eligibility_policy.evaluate(
            ledger=ledger,
            lesson=lesson,
            mastery_profile=current_mastery,
            requested_stability_increment=candidate.requested_stability_increment,
            requested_plasticity_reduction=candidate.requested_plasticity_reduction,
            available_assembly_ids=assemblies,
            available_route_ids=routes,
        )
        current_candidate = current_eligibility.candidate
        reasons = list(current_eligibility.reasons)
        if not source_events_available:
            _add_reason(reasons, ConsolidationRejectionReason.MISSING_SOURCE_EVENTS)
        if not assemblies_available:
            _add_reason(reasons, ConsolidationRejectionReason.MISSING_ASSEMBLIES)
        if not routes_available:
            _add_reason(reasons, ConsolidationRejectionReason.MISSING_ROUTES)
        ordered_reasons = tuple(
            reason for reason in ConsolidationRejectionReason if reason in reasons
        )

        evidence_valid = bool(
            source_events_available
            and broad_mastery_current
            and contradiction_free
            and assemblies_available
            and routes_available
            and current_candidate is not None
            and not ordered_reasons
        )
        candidate_identity_current = bool(
            current_candidate is not None and current_candidate == candidate
        )
        superseding = (
            _select_superseding_proposal(newer, current_candidate) if evidence_valid else None
        )
        if not evidence_valid:
            status = ConsolidationProposalRevalidationStatus.INVALID_FOR_REVIEW
        elif superseding is not None:
            status = ConsolidationProposalRevalidationStatus.SUPERSEDED
        elif candidate_identity_current:
            status = ConsolidationProposalRevalidationStatus.CURRENT
        else:
            status = ConsolidationProposalRevalidationStatus.STALE

        payload = {
            "status": status.value,
            "proposal": proposal.snapshot(),
            "current_mastery": current_mastery.snapshot(),
            "current_candidate": (
                None if current_candidate is None else current_candidate.snapshot()
            ),
            "superseding_proposal": (None if superseding is None else superseding.snapshot()),
            "eligibility_reasons": [reason.value for reason in ordered_reasons],
            "source_events_available": source_events_available,
            "broad_mastery_current": broad_mastery_current,
            "contradiction_free": contradiction_free,
            "assemblies_available": assemblies_available,
            "routes_available": routes_available,
            "candidate_identity_current": candidate_identity_current,
        }
        return ConsolidationProposalRevalidationDecision(
            decision_id=_decision_id(payload),
            status=status,
            proposal=proposal,
            current_mastery=current_mastery,
            current_candidate=current_candidate,
            superseding_proposal=superseding,
            eligibility_reasons=ordered_reasons,
            source_events_available=source_events_available,
            broad_mastery_current=broad_mastery_current,
            contradiction_free=contradiction_free,
            assemblies_available=assemblies_available,
            routes_available=routes_available,
            candidate_identity_current=candidate_identity_current,
        )

    def evaluate_registry(
        self,
        *,
        registry: ConsolidationProposalLifecycleRegistry,
        ledger: ContextualExperienceLedger,
        available_assembly_ids: Iterable[str],
        available_route_ids: Iterable[str],
        newer_proposals: Iterable[ConsolidationScheduleProposal] = (),
    ) -> ConsolidationProposalRevalidationReport:
        """Revalidate every active record while preserving the entire registry."""
        before = registry.snapshot()
        assemblies = _normalized_codes(
            "available_assembly_ids",
            available_assembly_ids,
        )
        routes = _normalized_codes(
            "available_route_ids",
            available_route_ids,
        )
        proposal_candidates = tuple(newer_proposals)
        proposal_ids = tuple(proposal.proposal_id for proposal in proposal_candidates)
        if len(proposal_ids) != len(set(proposal_ids)):
            raise ValueError("newer proposal identities must be unique")
        decisions = tuple(
            self.evaluate(
                record=record,
                ledger=ledger,
                available_assembly_ids=assemblies,
                available_route_ids=routes,
                newer_same_lesson_proposals=tuple(
                    proposal
                    for proposal in proposal_candidates
                    if proposal.candidate.lesson_identity
                    == record.proposal.candidate.lesson_identity
                ),
            )
            for record in registry.active_records
        )
        after = registry.snapshot()
        return ConsolidationProposalRevalidationReport(
            decisions=decisions,
            active_record_count=len(registry.active_records),
            archived_record_count=len(registry.records) - len(registry.active_records),
            registry_unchanged=before == after,
        )


def _source_events_available(
    *,
    ledger: ContextualExperienceLedger,
    lesson: LessonIdentity,
    source_event_ids: tuple[str, ...],
) -> bool:
    for event_id in source_event_ids:
        try:
            trace = ledger.trace(event_id)
        except ValueError:
            return False
        if trace.context.active_need_code != lesson.need_code:
            return False
        if not any(effect.effect_code == lesson.effect_code for effect in trace.observed_effects):
            return False
    return True


def _validated_newer_proposals(
    *,
    proposal: ConsolidationScheduleProposal,
    proposals: Iterable[ConsolidationScheduleProposal],
) -> tuple[ConsolidationScheduleProposal, ...]:
    values = tuple(proposals)
    proposal_ids = tuple(value.proposal_id for value in values)
    if len(proposal_ids) != len(set(proposal_ids)):
        raise ValueError("newer proposal identities must be unique")
    for value in values:
        if value.candidate.lesson_identity != proposal.candidate.lesson_identity:
            raise ValueError("newer proposal must preserve exact lesson identity")
        if value.proposed_episode <= proposal.proposed_episode:
            raise ValueError("newer proposal must have a later proposal episode")
    return tuple(sorted(values, key=lambda value: (value.proposed_episode, value.proposal_id)))


def _select_superseding_proposal(
    proposals: tuple[ConsolidationScheduleProposal, ...],
    current_candidate: ConsolidationCandidate | None,
) -> ConsolidationScheduleProposal | None:
    if current_candidate is None:
        return None
    matches = tuple(proposal for proposal in proposals if proposal.candidate == current_candidate)
    return None if not matches else matches[-1]


def _normalized_codes(name: str, values: Iterable[str]) -> tuple[str, ...]:
    supplied = tuple(values)
    if len(supplied) != len(set(supplied)):
        raise ValueError(f"{name} must contain unique identities")
    for value in supplied:
        _validate_code(name, value)
    return tuple(sorted(supplied))


def _add_reason(
    reasons: list[ConsolidationRejectionReason],
    reason: ConsolidationRejectionReason,
) -> None:
    if reason not in reasons:
        reasons.append(reason)


def _decision_id(payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"consolidation-revalidation:{hashlib.sha256(canonical).hexdigest()}"


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")
