"""Atomic human-approved application of one current NDNRA consolidation permit."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from typing import Protocol

from seedmind.research.ndnra.consolidation import ConsolidationEligibility
from seedmind.research.ndnra.consolidation_application import (
    ConsolidationApplicationResult,
    ConsolidationStateSnapshot,
)
from seedmind.research.ndnra.consolidation_execution_approval import (
    ConsolidationExecutionPermit,
)
from seedmind.research.ndnra.consolidation_execution_permit_lifecycle import (
    ConsolidationExecutionPermitLifecycleAction,
    ConsolidationExecutionPermitLifecycleRegistry,
    ConsolidationExecutionPermitLifecycleStatus,
    ConsolidationExecutionPermitTransitionDecision,
    ConsolidationExecutionPermitTransitionRequest,
)
from seedmind.research.ndnra.consolidation_proposal_lifecycle import (
    ConsolidationProposalLifecycleStatus,
    ConsolidationProposalReviewAction,
)
from seedmind.research.ndnra.consolidation_proposal_management import (
    ConsolidationProposalManagedRecord,
)
from seedmind.research.ndnra.consolidation_proposal_revalidation import (
    ConsolidationProposalRevalidationDecision,
    ConsolidationProposalRevalidationPolicy,
    ConsolidationProposalRevalidationStatus,
)
from seedmind.research.ndnra.contextual_memory import ContextualExperienceLedger


class ConsolidationApplicationTarget(Protocol):
    """Minimal atomic state interface required by the execution commit gate."""

    def snapshot(self) -> ConsolidationStateSnapshot:
        """Return the complete current consolidation state."""

    def apply(
        self,
        eligibility: ConsolidationEligibility,
    ) -> ConsolidationApplicationResult:
        """Apply one eligible candidate or raise without retaining partial state."""

    def restore_snapshot(
        self,
        *,
        expected_current: ConsolidationStateSnapshot,
        replacement: ConsolidationStateSnapshot,
    ) -> None:
        """Restore a complete prior state after a failed commit."""


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionCommitRequest:
    """One explicit request to commit one exact issued execution permit."""

    target_permit_id: str
    expected_proposal_id: str
    expected_candidate_id: str
    execution_episode: int
    executor_code: str
    reason_code: str

    def __post_init__(self) -> None:
        _validate_code("target_permit_id", self.target_permit_id)
        _validate_code("expected_proposal_id", self.expected_proposal_id)
        _validate_code("expected_candidate_id", self.expected_candidate_id)
        _validate_nonnegative_int("execution_episode", self.execution_episode)
        _validate_code("executor_code", self.executor_code)
        if not self.executor_code.startswith("execution:"):
            raise ValueError("executor_code must identify the bounded execution gate")
        _validate_code("reason_code", self.reason_code)


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionCommitReceipt:
    """Immutable evidence for one successfully committed human-approved application."""

    execution_id: str
    permit: ConsolidationExecutionPermit
    revalidation: ConsolidationProposalRevalidationDecision
    application: ConsolidationApplicationResult
    permit_transition: ConsolidationExecutionPermitTransitionDecision
    execution_episode: int
    executor_code: str
    reason_code: str
    application_count: int = 1
    replay_trigger_count: int = 0
    restoration_trigger_count: int = 0
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("execution_id", self.execution_id)
        _validate_nonnegative_int("execution_episode", self.execution_episode)
        _validate_code("executor_code", self.executor_code)
        _validate_code("reason_code", self.reason_code)
        if self.revalidation.status is not ConsolidationProposalRevalidationStatus.CURRENT:
            raise ValueError("execution receipt requires current pre-commit revalidation")
        if self.revalidation.proposal != self.permit.proposal:
            raise ValueError("execution receipt revalidation targets a different proposal")
        if self.application.candidate != self.permit.proposal.candidate:
            raise ValueError("execution receipt application targets a different candidate")
        if self.permit_transition.permit != self.permit:
            raise ValueError("execution receipt transition targets a different permit")
        if (
            self.permit_transition.status
            is not ConsolidationExecutionPermitLifecycleStatus.CONSUMED
        ):
            raise ValueError("successful execution receipt requires consumed permit state")
        if self.permit_transition.consumption_reference_code != self.execution_id:
            raise ValueError("permit consumption reference must equal execution identity")
        if self.application_count != 1:
            raise ValueError("successful execution receipt must contain one application")
        if self.replay_trigger_count != 0:
            raise ValueError("human-approved execution cannot trigger replay in this stage")
        if self.restoration_trigger_count != 0:
            raise ValueError("successful execution cannot report restoration")
        if self.has_production_action_authority:
            raise ValueError("consolidation execution cannot select production actions")
        expected_id = _execution_id(
            permit=self.permit,
            revalidation=self.revalidation,
            before=self.application.before,
            execution_episode=self.execution_episode,
            executor_code=self.executor_code,
            reason_code=self.reason_code,
        )
        if self.execution_id != expected_id:
            raise ValueError("execution receipt identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic ASCII-safe execution evidence."""
        return {
            "execution_id": self.execution_id,
            "permit": self.permit.snapshot(),
            "revalidation": self.revalidation.snapshot(),
            "application": {
                "candidate": self.application.candidate.snapshot(),
                "before": self.application.before.snapshot(),
                "after": self.application.after.snapshot(),
            },
            "permit_transition": self.permit_transition.snapshot(),
            "execution_episode": self.execution_episode,
            "executor_code": self.executor_code,
            "reason_code": self.reason_code,
            "application_count": self.application_count,
            "replay_trigger_count": self.replay_trigger_count,
            "restoration_trigger_count": self.restoration_trigger_count,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionCommitResult:
    """Successful atomic state and permit-lifecycle commit result."""

    receipt: ConsolidationExecutionCommitReceipt
    permit_registry: ConsolidationExecutionPermitLifecycleRegistry

    def __post_init__(self) -> None:
        record = self.permit_registry.record_for(self.receipt.permit.permit_id)
        if record.status is not ConsolidationExecutionPermitLifecycleStatus.CONSUMED:
            raise ValueError("commit result registry must contain consumed permit")
        if record.consumption_count != 1:
            raise ValueError("commit result registry must consume permit exactly once")
        if record.decisions != (self.receipt.permit_transition,):
            raise ValueError("commit result registry transition must match receipt")
        if self.permit_registry.has_application_authority:
            raise ValueError("permit registry cannot gain application authority")

    def snapshot(self) -> dict[str, object]:
        """Return complete deterministic commit evidence."""
        return {
            "receipt": self.receipt.snapshot(),
            "permit_registry": self.permit_registry.snapshot(),
        }


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionCommitPolicy:
    """Commit one current issued permit and restore state on any failed application."""

    revalidation_policy: ConsolidationProposalRevalidationPolicy = field(
        default_factory=ConsolidationProposalRevalidationPolicy
    )

    def execute(
        self,
        *,
        request: ConsolidationExecutionCommitRequest,
        proposal_record: ConsolidationProposalManagedRecord,
        permit_registry: ConsolidationExecutionPermitLifecycleRegistry,
        ledger: ContextualExperienceLedger,
        application_state: ConsolidationApplicationTarget,
        available_assembly_ids: Iterable[str],
        available_route_ids: Iterable[str],
        interruption_hook: Callable[[str], None] | None = None,
    ) -> ConsolidationExecutionCommitResult:
        """Atomically apply and consume one permit after immediate revalidation."""
        assemblies = _normalized_codes("available_assembly_ids", available_assembly_ids)
        routes = _normalized_codes("available_route_ids", available_route_ids)
        permit_record = permit_registry.record_for(request.target_permit_id)
        if permit_record.status is not ConsolidationExecutionPermitLifecycleStatus.ISSUED:
            raise ValueError("execution requires an issued permit lifecycle")
        if permit_record.decisions:
            raise ValueError("issued execution permit must not contain terminal decisions")
        permit = permit_record.permit
        proposal = permit.proposal
        if request.expected_proposal_id != proposal.proposal_id:
            raise ValueError("execution request targets a different proposal")
        if request.expected_candidate_id != proposal.candidate.candidate_id:
            raise ValueError("execution request targets a different candidate")
        if request.execution_episode <= permit.issued_episode:
            raise ValueError("execution must follow permit issuance")
        if not permit.valid_at(request.execution_episode):
            raise ValueError("execution permit is outside its validity window")

        if not proposal_record.is_active:
            raise ValueError("execution requires an active proposal lifecycle")
        lifecycle = proposal_record.lifecycle
        if lifecycle.status is not ConsolidationProposalLifecycleStatus.ACCEPTED:
            raise ValueError("execution requires accepted proposal lifecycle status")
        if proposal_record.proposal != proposal:
            raise ValueError("permit proposal differs from active lifecycle proposal")
        if not lifecycle.decisions:
            raise ValueError("accepted proposal lifecycle requires review evidence")
        accepted_review = lifecycle.decisions[-1]
        if (
            accepted_review.action is not ConsolidationProposalReviewAction.ACCEPT
            or accepted_review.status is not ConsolidationProposalLifecycleStatus.ACCEPTED
        ):
            raise ValueError("latest proposal review must remain accepted")
        if accepted_review.decision_id != permit.accepted_review_decision_id:
            raise ValueError("permit targets a different accepted review decision")

        ledger_before = ledger.snapshot()
        proposal_before = lifecycle.snapshot()
        permit_registry_before = permit_registry.snapshot()
        state_before = application_state.snapshot()
        _interrupt(interruption_hook, "before_revalidation")

        revalidation = self.revalidation_policy.evaluate(
            record=proposal_record,
            ledger=ledger,
            available_assembly_ids=assemblies,
            available_route_ids=routes,
        )
        if revalidation.status is not ConsolidationProposalRevalidationStatus.CURRENT:
            raise ValueError(
                "execution requires a current proposal immediately before commit; "
                f"received {revalidation.status.value}"
            )
        if revalidation.proposal != proposal:
            raise ValueError("pre-commit revalidation returned a different proposal")
        if revalidation.current_candidate != proposal.candidate:
            raise ValueError("pre-commit revalidation returned a different candidate")
        _interrupt(interruption_hook, "after_revalidation")

        eligibility = self.revalidation_policy.eligibility_policy.evaluate(
            ledger=ledger,
            lesson=proposal.candidate.lesson_identity,
            mastery_profile=revalidation.current_mastery,
            requested_stability_increment=(proposal.candidate.requested_stability_increment),
            requested_plasticity_reduction=(proposal.candidate.requested_plasticity_reduction),
            available_assembly_ids=assemblies,
            available_route_ids=routes,
        )
        if not eligibility.eligible or eligibility.candidate != proposal.candidate:
            raise ValueError("pre-commit eligibility does not match permitted candidate")

        execution_id = _execution_id(
            permit=permit,
            revalidation=revalidation,
            before=state_before,
            execution_episode=request.execution_episode,
            executor_code=request.executor_code,
            reason_code=request.reason_code,
        )
        consumed_registry = permit_registry.transition(
            ConsolidationExecutionPermitTransitionRequest(
                target_permit_id=permit.permit_id,
                expected_proposal_id=proposal.proposal_id,
                expected_candidate_id=proposal.candidate.candidate_id,
                action=ConsolidationExecutionPermitLifecycleAction.CONSUME,
                decision_episode=request.execution_episode,
                actor_code=request.executor_code,
                reason_code=request.reason_code,
                consumption_reference_code=execution_id,
            )
        )
        consumed_record = consumed_registry.record_for(permit.permit_id)
        permit_transition = consumed_record.decisions[0]
        _interrupt(interruption_hook, "after_consumed_registry_preparation")

        try:
            application = application_state.apply(eligibility)
            _interrupt(interruption_hook, "after_application")
            if application.before != state_before:
                raise RuntimeError("application before-state differs from commit snapshot")
            if application.after != application_state.snapshot():
                raise RuntimeError("application after-state differs from committed state")
            if application.candidate != proposal.candidate:
                raise RuntimeError("application committed a different candidate")
            if ledger.snapshot() != ledger_before:
                raise RuntimeError("execution mutated contextual evidence")
            if lifecycle.snapshot() != proposal_before:
                raise RuntimeError("execution mutated proposal lifecycle history")
            if permit_registry.snapshot() != permit_registry_before:
                raise RuntimeError("execution mutated the original permit registry")

            receipt = ConsolidationExecutionCommitReceipt(
                execution_id=execution_id,
                permit=permit,
                revalidation=revalidation,
                application=application,
                permit_transition=permit_transition,
                execution_episode=request.execution_episode,
                executor_code=request.executor_code,
                reason_code=request.reason_code,
            )
            return ConsolidationExecutionCommitResult(
                receipt=receipt,
                permit_registry=consumed_registry,
            )
        except Exception as error:
            _restore_failed_application(
                application_state=application_state,
                before=state_before,
            )
            if application_state.snapshot() != state_before:
                raise RuntimeError("failed execution could not restore prior state") from error
            raise


def _interrupt(
    hook: Callable[[str], None] | None,
    point: str,
) -> None:
    if hook is not None:
        hook(point)


def _restore_failed_application(
    *,
    application_state: ConsolidationApplicationTarget,
    before: ConsolidationStateSnapshot,
) -> None:
    current = application_state.snapshot()
    if current == before:
        return
    application_state.restore_snapshot(
        expected_current=current,
        replacement=before,
    )


def _execution_id(
    *,
    permit: ConsolidationExecutionPermit,
    revalidation: ConsolidationProposalRevalidationDecision,
    before: ConsolidationStateSnapshot,
    execution_episode: int,
    executor_code: str,
    reason_code: str,
) -> str:
    payload = {
        "permit": permit.snapshot(),
        "revalidation": revalidation.snapshot(),
        "before": before.snapshot(),
        "execution_episode": execution_episode,
        "executor_code": executor_code,
        "reason_code": reason_code,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"consolidation-execution:{hashlib.sha256(canonical).hexdigest()}"


def _normalized_codes(name: str, values: Iterable[str]) -> tuple[str, ...]:
    supplied = tuple(values)
    if not supplied:
        raise ValueError(f"{name} must not be empty")
    if len(supplied) != len(set(supplied)):
        raise ValueError(f"{name} must contain unique identities")
    for value in supplied:
        _validate_code(name, value)
    return tuple(sorted(supplied))


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


__all__ = [
    "ConsolidationApplicationTarget",
    "ConsolidationExecutionCommitPolicy",
    "ConsolidationExecutionCommitReceipt",
    "ConsolidationExecutionCommitRequest",
    "ConsolidationExecutionCommitResult",
]
