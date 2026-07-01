"""Typed diagnostic ladder for Week 10 capacity diagnosis."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class DiagnosticStepStatus(StrEnum):
    """Inspectable state for one diagnostic-ladder step."""

    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    PASSED = "passed"
    FAILED = "failed"
    NOT_APPLICABLE = "not_applicable"
    BLOCKED = "blocked"


class DiagnosticStepCode(StrEnum):
    """Week 10 diagnostic-ladder steps before any growth proposal."""

    CONFIRM_TASK = "confirm_task_and_success_condition"
    SAFE_EXPLORATION = "confirm_sufficient_safe_exploration"
    RETRIEVE_MEMORY = "retrieve_relevant_memories"
    ATTEMPT_EXISTING_SKILL = "attempt_existing_frozen_skill"
    TRY_STRATEGIES = "try_bounded_alternative_strategies"
    REQUEST_HELP = "request_help_or_demonstration"
    MEMORY_REPLAY = "attempt_bounded_memory_replay"
    CHECK_PREDICTION = "check_prediction_quality"
    CHECK_IMPROVEMENT = "check_learning_progress"
    INFER_LIMITATION = "infer_policy_capacity_limitation"
    PRODUCE_PROPOSAL = "produce_non_authoritative_growth_proposal"


@dataclass(frozen=True, slots=True)
class DiagnosticStepRecord:
    """One auditable ladder step result."""

    code: DiagnosticStepCode
    status: DiagnosticStepStatus
    evidence_refs: tuple[str, ...]
    attempt_count: int
    result: str
    reason: str
    remaining_uncertainty: str
    next_permitted_step: DiagnosticStepCode | None

    def __post_init__(self) -> None:
        if self.attempt_count < 0:
            raise ValueError("attempt_count must not be negative")
        for value in (
            self.result,
            self.reason,
            self.remaining_uncertainty,
        ):
            if not value.strip() or not value.isascii():
                raise ValueError("diagnostic text must be non-empty ASCII")
        if any(not ref.strip() or not ref.isascii() for ref in self.evidence_refs):
            raise ValueError("evidence references must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        return {
            "attempt_count": self.attempt_count,
            "code": self.code.value,
            "evidence_refs": list(self.evidence_refs),
            "next_permitted_step": (
                None if self.next_permitted_step is None else self.next_permitted_step.value
            ),
            "reason": self.reason,
            "remaining_uncertainty": self.remaining_uncertainty,
            "result": self.result,
            "status": self.status.value,
        }


@dataclass(frozen=True, slots=True)
class DiagnosticLadderRecord:
    """Complete Week 10 diagnostic ladder for one scenario family."""

    scenario_family: str
    steps: tuple[DiagnosticStepRecord, ...]
    stopped_early: bool
    stop_reason: str | None

    def __post_init__(self) -> None:
        if not self.scenario_family.strip() or not self.scenario_family.isascii():
            raise ValueError("scenario_family must be non-empty ASCII")
        if not self.steps:
            raise ValueError("diagnostic ladder must contain steps")
        if self.stopped_early and (self.stop_reason is None or not self.stop_reason.strip()):
            raise ValueError("early stop requires a reason")

    @property
    def completed_for_growth_proposal(self) -> bool:
        """Return whether every prerequisite reached a passing terminal state."""
        return (
            not self.stopped_early
            and self.steps[-1].code is DiagnosticStepCode.PRODUCE_PROPOSAL
            and all(step.status is DiagnosticStepStatus.PASSED for step in self.steps)
        )

    def to_json(self) -> dict[str, object]:
        return {
            "completed_for_growth_proposal": self.completed_for_growth_proposal,
            "scenario_family": self.scenario_family,
            "steps": [step.to_json() for step in self.steps],
            "stop_reason": self.stop_reason,
            "stopped_early": self.stopped_early,
        }


def build_ladder(
    *,
    scenario_family: str,
    task_confirmed: bool,
    safe_exploration_sufficient: bool,
    relevant_memory_retrieved: bool,
    existing_skill_attempted: bool,
    strategy_variants_tested: bool,
    help_or_demonstration_considered: bool,
    replay_attempted: bool,
    prediction_quality_checked: bool,
    competence_still_improving: bool,
    inferred_policy_capacity_limitation: bool,
    proposal_allowed: bool,
    attempt_count: int,
    evidence_prefix: str,
) -> DiagnosticLadderRecord:
    """Build the deterministic ladder and stop early when prerequisites fail."""
    steps: list[DiagnosticStepRecord] = []

    def append(
        code: DiagnosticStepCode,
        passed: bool,
        reason: str,
        next_step: DiagnosticStepCode | None,
        *,
        count: int = attempt_count,
    ) -> bool:
        status = DiagnosticStepStatus.PASSED if passed else DiagnosticStepStatus.BLOCKED
        steps.append(
            DiagnosticStepRecord(
                code=code,
                status=status,
                evidence_refs=(f"{evidence_prefix}:{code.value}",),
                attempt_count=count,
                result="passed" if passed else "blocked",
                reason=reason,
                remaining_uncertainty="none" if passed else reason,
                next_permitted_step=next_step if passed else None,
            )
        )
        return passed

    checks = (
        (
            DiagnosticStepCode.CONFIRM_TASK,
            task_confirmed,
            "task and success condition are confirmed",
            DiagnosticStepCode.SAFE_EXPLORATION,
        ),
        (
            DiagnosticStepCode.SAFE_EXPLORATION,
            safe_exploration_sufficient,
            "safe exploration meets the minimum evidence window",
            DiagnosticStepCode.RETRIEVE_MEMORY,
        ),
        (
            DiagnosticStepCode.RETRIEVE_MEMORY,
            relevant_memory_retrieved,
            "relevant grounded main-memory evidence was retrieved",
            DiagnosticStepCode.ATTEMPT_EXISTING_SKILL,
        ),
        (
            DiagnosticStepCode.ATTEMPT_EXISTING_SKILL,
            existing_skill_attempted,
            "the frozen approach_and_push skill was attempted",
            DiagnosticStepCode.TRY_STRATEGIES,
        ),
        (
            DiagnosticStepCode.TRY_STRATEGIES,
            strategy_variants_tested,
            "bounded general strategy variants were exhausted",
            DiagnosticStepCode.REQUEST_HELP,
        ),
        (
            DiagnosticStepCode.REQUEST_HELP,
            help_or_demonstration_considered,
            "help and demonstration were considered or attempted",
            DiagnosticStepCode.MEMORY_REPLAY,
        ),
        (
            DiagnosticStepCode.MEMORY_REPLAY,
            replay_attempted,
            "bounded replay of grounded main-memory evidence was attempted",
            DiagnosticStepCode.CHECK_PREDICTION,
        ),
        (
            DiagnosticStepCode.CHECK_PREDICTION,
            prediction_quality_checked,
            "prediction-quality evidence was checked",
            DiagnosticStepCode.CHECK_IMPROVEMENT,
        ),
        (
            DiagnosticStepCode.CHECK_IMPROVEMENT,
            not competence_still_improving,
            "competence is not improving above the declared threshold",
            DiagnosticStepCode.INFER_LIMITATION,
        ),
        (
            DiagnosticStepCode.INFER_LIMITATION,
            inferred_policy_capacity_limitation,
            "remaining evidence supports a possible policy-capacity limitation",
            DiagnosticStepCode.PRODUCE_PROPOSAL,
        ),
        (
            DiagnosticStepCode.PRODUCE_PROPOSAL,
            proposal_allowed,
            "a non-authoritative Week 11 investigation proposal is allowed",
            None,
        ),
    )
    for code, passed, reason, next_step in checks:
        if not append(code, passed, reason, next_step):
            return DiagnosticLadderRecord(
                scenario_family=scenario_family,
                steps=tuple(steps),
                stopped_early=True,
                stop_reason=reason,
            )
    return DiagnosticLadderRecord(
        scenario_family=scenario_family,
        steps=tuple(steps),
        stopped_early=False,
        stop_reason=None,
    )
