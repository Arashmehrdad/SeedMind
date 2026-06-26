"""Human apprenticeship, help seeking, caregiver memory, and metrics."""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.human.contracts import (
    HumanRequest,
    HumanSignalCode,
    HumanSignalCodec,
    HumanSignalFrame,
    SupportLevel,
)


class HelpReason(StrEnum):
    """Auditable reason for requesting or avoiding caregiver help."""

    AMBIGUOUS_REQUEST = "ambiguous_request"
    BLOCKED_HIGH_UNCERTAINTY = "blocked_high_uncertainty"
    HIGH_RISK_UNCERTAINTY = "high_risk_uncertainty"
    LOW_COMPETENCE_UNCERTAINTY = "low_competence_uncertainty"
    SAFE_EXPERIMENT_AVAILABLE = "safe_experiment_available"
    FAMILIAR_LOW_RISK = "familiar_low_risk"
    SUFFICIENT_EVIDENCE = "sufficient_evidence"


class CaregiverEventType(StrEnum):
    """Append-only developmental events in the caregiver relationship."""

    REQUEST_RECEIVED = "request_received"
    HELP_REQUESTED = "help_requested"
    INDEPENDENT_ATTEMPT = "independent_attempt"
    DEMONSTRATION = "demonstration"
    CLARIFICATION = "clarification"
    CORRECTION = "correction"
    APPROVAL = "approval"
    SUPPORT_PROMOTED = "support_promoted"


@dataclass(frozen=True, slots=True)
class HelpSeekingConfig:
    """Support-sensitive thresholds and Week 6 acceptance targets."""

    level4_uncertainty_threshold: float = 0.55
    level3_uncertainty_threshold: float = 0.72
    ambiguity_threshold: float = 0.50
    blocked_attempt_threshold: int = 2
    high_risk_threshold: float = 0.50
    low_competence_threshold: float = 0.30
    familiar_competence_threshold: float = 0.75
    safe_experiment_risk_ceiling: float = 0.25
    safe_experiment_uncertainty_ceiling: float = 0.90
    promotion_success_threshold: int = 3
    pass_help_recall_threshold: float = 0.70
    pass_help_avoidance_threshold: float = 0.70

    def __post_init__(self) -> None:
        for threshold_name, threshold_value in (
            ("level4_uncertainty_threshold", self.level4_uncertainty_threshold),
            ("level3_uncertainty_threshold", self.level3_uncertainty_threshold),
            ("ambiguity_threshold", self.ambiguity_threshold),
            ("high_risk_threshold", self.high_risk_threshold),
            ("low_competence_threshold", self.low_competence_threshold),
            ("familiar_competence_threshold", self.familiar_competence_threshold),
            ("safe_experiment_risk_ceiling", self.safe_experiment_risk_ceiling),
            ("safe_experiment_uncertainty_ceiling", self.safe_experiment_uncertainty_ceiling),
            ("pass_help_recall_threshold", self.pass_help_recall_threshold),
            ("pass_help_avoidance_threshold", self.pass_help_avoidance_threshold),
        ):
            _validate_unit_interval(threshold_name, threshold_value)
        if self.blocked_attempt_threshold <= 0:
            raise ValueError("blocked_attempt_threshold must be positive")
        if self.promotion_success_threshold <= 0:
            raise ValueError("promotion_success_threshold must be positive")
        if self.level3_uncertainty_threshold < self.level4_uncertainty_threshold:
            raise ValueError("Level 3 must require at least as much uncertainty as Level 4")


@dataclass(frozen=True, slots=True)
class HelpContext:
    """Evidence available when deciding whether human support is necessary."""

    case_id: str
    request: HumanRequest
    uncertainty: float
    competence: float
    risk: float
    blocked_attempts: int
    safe_experiment_available: bool
    familiar: bool

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        for score_name, score_value in (
            ("uncertainty", self.uncertainty),
            ("competence", self.competence),
            ("risk", self.risk),
        ):
            _validate_unit_interval(score_name, score_value)
        if self.blocked_attempts < 0:
            raise ValueError("blocked_attempts must not be negative")


@dataclass(frozen=True, slots=True)
class HelpDecision:
    """One auditable action decision from the help-seeking policy."""

    case_id: str
    should_request_help: bool
    selected_action: PrimitiveAction | None
    reason: HelpReason
    support_level: SupportLevel
    decision_score: float

    def __post_init__(self) -> None:
        if not self.case_id.strip():
            raise ValueError("case_id must not be empty")
        _validate_unit_interval("decision_score", self.decision_score)
        expected_action = PrimitiveAction.REQUEST_HELP if self.should_request_help else None
        if self.selected_action is not expected_action:
            raise ValueError("selected_action does not match should_request_help")


@dataclass(frozen=True, slots=True)
class TeacherResponse:
    """Deterministic caregiver response to one justified help request."""

    code: HumanSignalCode
    confidence: float

    def __post_init__(self) -> None:
        if self.code not in (
            HumanSignalCode.DEMONSTRATE,
            HumanSignalCode.CORRECT,
            HumanSignalCode.CLARIFY,
        ):
            raise ValueError("teacher response must teach, correct, or clarify")
        _validate_unit_interval("confidence", self.confidence)


@dataclass(frozen=True, slots=True)
class CaregiverEvent:
    """One append-only request, decision, teaching, correction, or approval."""

    event_id: str
    episode_id: str
    step_index: int
    request_id: str
    event_type: CaregiverEventType
    support_level: SupportLevel
    uncertainty: float
    competence: float
    signal_code: HumanSignalCode | None = None
    help_reason: HelpReason | None = None
    verified: bool | None = None

    def __post_init__(self) -> None:
        for identifier_name, identifier_value in (
            ("event_id", self.event_id),
            ("episode_id", self.episode_id),
            ("request_id", self.request_id),
        ):
            if not identifier_value.strip():
                raise ValueError(f"{identifier_name} must not be empty")
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        _validate_unit_interval("uncertainty", self.uncertainty)
        _validate_unit_interval("competence", self.competence)


class CaregiverMemory:
    """Append-only in-memory caregiver history with stable event identities."""

    def __init__(self) -> None:
        self._events: list[CaregiverEvent] = []
        self._event_ids: set[str] = set()

    @property
    def events(self) -> tuple[CaregiverEvent, ...]:
        """Return immutable caregiver history in insertion order."""
        return tuple(self._events)

    def append(self, event: CaregiverEvent) -> None:
        """Append one unique event without rewriting earlier history."""
        if event.event_id in self._event_ids:
            raise ValueError("caregiver event_id must be unique")
        self._event_ids.add(event.event_id)
        self._events.append(event)


@dataclass(frozen=True, slots=True)
class ApprenticeshipMetrics:
    """Help calibration, teaching events, and current support level."""

    blocked_high_uncertainty_cases: int
    help_requests_in_blocked_cases: int
    familiar_low_risk_cases: int
    help_requests_in_familiar_cases: int
    teacher_demonstrations: int
    teacher_clarifications: int
    corrections: int
    approvals: int
    support_level: SupportLevel
    help_recall_threshold: float
    help_avoidance_threshold: float

    def __post_init__(self) -> None:
        counts = (
            self.blocked_high_uncertainty_cases,
            self.help_requests_in_blocked_cases,
            self.familiar_low_risk_cases,
            self.help_requests_in_familiar_cases,
            self.teacher_demonstrations,
            self.teacher_clarifications,
            self.corrections,
            self.approvals,
        )
        if any(count < 0 for count in counts):
            raise ValueError("apprenticeship metric counts must not be negative")
        if self.help_requests_in_blocked_cases > self.blocked_high_uncertainty_cases:
            raise ValueError("blocked-case help count exceeds blocked cases")
        if self.help_requests_in_familiar_cases > self.familiar_low_risk_cases:
            raise ValueError("familiar-case help count exceeds familiar cases")
        _validate_unit_interval("help_recall_threshold", self.help_recall_threshold)
        _validate_unit_interval("help_avoidance_threshold", self.help_avoidance_threshold)

    @property
    def help_recall(self) -> float:
        """Return help frequency on blocked high-uncertainty cases."""
        if self.blocked_high_uncertainty_cases == 0:
            return 0.0
        return self.help_requests_in_blocked_cases / self.blocked_high_uncertainty_cases

    @property
    def help_avoidance_rate(self) -> float:
        """Return independent-action frequency on familiar low-risk cases."""
        if self.familiar_low_risk_cases == 0:
            return 0.0
        unnecessary_help = self.help_requests_in_familiar_cases
        return 1.0 - (unnecessary_help / self.familiar_low_risk_cases)

    @property
    def pass_gate(self) -> bool:
        """Return whether both Week 6 help calibration targets pass."""
        return (
            self.help_recall >= self.help_recall_threshold
            and self.help_avoidance_rate >= self.help_avoidance_threshold
        )


class HelpSeekingPolicy:
    """Choose human help only when evidence justifies escalation."""

    def __init__(self, config: HelpSeekingConfig | None = None) -> None:
        self.config = HelpSeekingConfig() if config is None else config

    def decide(
        self,
        context: HelpContext,
        *,
        support_level: SupportLevel,
    ) -> HelpDecision:
        """Evaluate ambiguity, blockage, risk, competence, and safe alternatives."""
        uncertainty_threshold = (
            self.config.level4_uncertainty_threshold
            if support_level is SupportLevel.DEPENDENT
            else self.config.level3_uncertainty_threshold
        )
        if context.request.ambiguity >= self.config.ambiguity_threshold:
            return self._help(
                context,
                support_level,
                HelpReason.AMBIGUOUS_REQUEST,
                context.request.ambiguity,
            )
        if self._is_familiar_low_risk(context):
            return self._independent(
                context,
                support_level,
                HelpReason.FAMILIAR_LOW_RISK,
                1.0 - context.uncertainty,
            )
        if (
            context.safe_experiment_available
            and context.risk <= self.config.safe_experiment_risk_ceiling
            and context.uncertainty < self.config.safe_experiment_uncertainty_ceiling
            and context.blocked_attempts < self.config.blocked_attempt_threshold
        ):
            return self._independent(
                context,
                support_level,
                HelpReason.SAFE_EXPERIMENT_AVAILABLE,
                1.0 - context.risk,
            )
        if (
            context.blocked_attempts >= self.config.blocked_attempt_threshold
            and context.uncertainty >= uncertainty_threshold
        ):
            return self._help(
                context,
                support_level,
                HelpReason.BLOCKED_HIGH_UNCERTAINTY,
                context.uncertainty,
            )
        if (
            context.risk >= self.config.high_risk_threshold
            and context.uncertainty >= uncertainty_threshold
        ):
            return self._help(
                context,
                support_level,
                HelpReason.HIGH_RISK_UNCERTAINTY,
                max(context.risk, context.uncertainty),
            )
        if (
            context.competence <= self.config.low_competence_threshold
            and context.uncertainty >= uncertainty_threshold
            and not context.safe_experiment_available
        ):
            return self._help(
                context,
                support_level,
                HelpReason.LOW_COMPETENCE_UNCERTAINTY,
                context.uncertainty,
            )
        return self._independent(
            context,
            support_level,
            HelpReason.SUFFICIENT_EVIDENCE,
            max(context.competence, 1.0 - context.uncertainty),
        )

    def _is_familiar_low_risk(self, context: HelpContext) -> bool:
        return (
            context.familiar
            and context.competence >= self.config.familiar_competence_threshold
            and context.risk <= self.config.safe_experiment_risk_ceiling
        )

    @staticmethod
    def _help(
        context: HelpContext,
        support_level: SupportLevel,
        reason: HelpReason,
        score: float,
    ) -> HelpDecision:
        return HelpDecision(
            case_id=context.case_id,
            should_request_help=True,
            selected_action=PrimitiveAction.REQUEST_HELP,
            reason=reason,
            support_level=support_level,
            decision_score=min(max(score, 0.0), 1.0),
        )

    @staticmethod
    def _independent(
        context: HelpContext,
        support_level: SupportLevel,
        reason: HelpReason,
        score: float,
    ) -> HelpDecision:
        return HelpDecision(
            case_id=context.case_id,
            should_request_help=False,
            selected_action=None,
            reason=reason,
            support_level=support_level,
            decision_score=min(max(score, 0.0), 1.0),
        )


class TeacherResponsePolicy:
    """Return deterministic symbolic teaching after a justified escalation."""

    def __init__(self, config: HelpSeekingConfig | None = None) -> None:
        self.config = HelpSeekingConfig() if config is None else config

    def respond(
        self,
        context: HelpContext,
        decision: HelpDecision,
    ) -> TeacherResponse:
        """Clarify ambiguity, demonstrate blockage, or correct risky uncertainty."""
        if not decision.should_request_help:
            raise ValueError("teacher response requires a help request")
        if context.request.ambiguity >= self.config.ambiguity_threshold:
            return TeacherResponse(HumanSignalCode.CLARIFY, confidence=1.0)
        if context.blocked_attempts >= self.config.blocked_attempt_threshold:
            return TeacherResponse(HumanSignalCode.DEMONSTRATE, confidence=0.95)
        return TeacherResponse(HumanSignalCode.CORRECT, confidence=0.90)


class ApprenticeshipManager:
    """Coordinate requests, help decisions, teaching, support, and memory."""

    def __init__(
        self,
        config: HelpSeekingConfig | None = None,
        *,
        support_level: SupportLevel = SupportLevel.DEPENDENT,
    ) -> None:
        self.config = HelpSeekingConfig() if config is None else config
        self.support_level = support_level
        self.codec = HumanSignalCodec()
        self.policy = HelpSeekingPolicy(self.config)
        self.teacher_policy = TeacherResponsePolicy(self.config)
        self.memory = CaregiverMemory()
        self._event_index = 0
        self._verified_familiar_successes = 0
        self._blocked_cases = 0
        self._blocked_help = 0
        self._familiar_cases = 0
        self._familiar_help = 0
        self._demonstrations = 0
        self._clarifications = 0
        self._corrections = 0
        self._approvals = 0

    def receive_request(
        self,
        request: HumanRequest,
        *,
        episode_id: str,
        step_index: int,
    ) -> HumanSignalFrame:
        """Record and return the symbolic request frame for the runtime."""
        frame = self.codec.request_frame(request, support_level=self.support_level)
        self._append_event(
            episode_id=episode_id,
            step_index=step_index,
            request=request,
            event_type=CaregiverEventType.REQUEST_RECEIVED,
            uncertainty=request.ambiguity,
            competence=0.0,
            signal_code=frame.code,
        )
        return frame

    def evaluate(
        self,
        context: HelpContext,
        *,
        episode_id: str,
        step_index: int,
    ) -> HelpDecision:
        """Make and record one support-sensitive help decision."""
        decision = self.policy.decide(context, support_level=self.support_level)
        blocked_case = self._is_blocked_high_uncertainty(context)
        familiar_case = self.policy._is_familiar_low_risk(context)
        self._blocked_cases += int(blocked_case)
        self._blocked_help += int(blocked_case and decision.should_request_help)
        self._familiar_cases += int(familiar_case)
        self._familiar_help += int(familiar_case and decision.should_request_help)
        self._append_event(
            episode_id=episode_id,
            step_index=step_index,
            request=context.request,
            event_type=(
                CaregiverEventType.HELP_REQUESTED
                if decision.should_request_help
                else CaregiverEventType.INDEPENDENT_ATTEMPT
            ),
            uncertainty=context.uncertainty,
            competence=context.competence,
            help_reason=decision.reason,
        )
        return decision

    def teacher_response(
        self,
        context: HelpContext,
        decision: HelpDecision,
        *,
        episode_id: str,
        step_index: int,
    ) -> HumanSignalFrame:
        """Record and return a deterministic response to a help request."""
        response = self.teacher_policy.respond(context, decision)
        event_type = {
            HumanSignalCode.DEMONSTRATE: CaregiverEventType.DEMONSTRATION,
            HumanSignalCode.CLARIFY: CaregiverEventType.CLARIFICATION,
            HumanSignalCode.CORRECT: CaregiverEventType.CORRECTION,
        }[response.code]
        self._demonstrations += int(response.code is HumanSignalCode.DEMONSTRATE)
        self._clarifications += int(response.code is HumanSignalCode.CLARIFY)
        self._corrections += int(response.code is HumanSignalCode.CORRECT)
        frame = self.codec.caregiver_frame(
            response.code,
            request=context.request,
            support_level=self.support_level,
            confidence=response.confidence,
        )
        self._append_event(
            episode_id=episode_id,
            step_index=step_index,
            request=context.request,
            event_type=event_type,
            uncertainty=context.uncertainty,
            competence=context.competence,
            signal_code=response.code,
            help_reason=decision.reason,
        )
        return frame

    def record_correction(
        self,
        request: HumanRequest,
        *,
        episode_id: str,
        step_index: int,
        uncertainty: float,
        competence: float,
    ) -> HumanSignalFrame:
        """Store a caregiver correction independently from punishment."""
        self._corrections += 1
        frame = self.codec.caregiver_frame(
            HumanSignalCode.CORRECT,
            request=request,
            support_level=self.support_level,
            confidence=1.0,
        )
        self._append_event(
            episode_id=episode_id,
            step_index=step_index,
            request=request,
            event_type=CaregiverEventType.CORRECTION,
            uncertainty=uncertainty,
            competence=competence,
            signal_code=HumanSignalCode.CORRECT,
        )
        return frame

    def record_approval(
        self,
        request: HumanRequest,
        *,
        episode_id: str,
        step_index: int,
        uncertainty: float,
        competence: float,
        verified: bool,
        familiar: bool,
    ) -> HumanSignalFrame:
        """Store verified approval and promote support after repeated competence."""
        self._approvals += 1
        frame = self.codec.caregiver_frame(
            HumanSignalCode.APPROVE,
            request=request,
            support_level=self.support_level,
            confidence=1.0 if verified else 0.0,
        )
        self._append_event(
            episode_id=episode_id,
            step_index=step_index,
            request=request,
            event_type=CaregiverEventType.APPROVAL,
            uncertainty=uncertainty,
            competence=competence,
            signal_code=HumanSignalCode.APPROVE,
            verified=verified,
        )
        if verified and familiar:
            self._verified_familiar_successes += 1
            if (
                self.support_level is SupportLevel.DEPENDENT
                and self._verified_familiar_successes >= self.config.promotion_success_threshold
            ):
                self.support_level = SupportLevel.GUIDED_LEARNER
                self._append_event(
                    episode_id=episode_id,
                    step_index=step_index,
                    request=request,
                    event_type=CaregiverEventType.SUPPORT_PROMOTED,
                    uncertainty=uncertainty,
                    competence=competence,
                    verified=True,
                )
        return frame

    def metrics(self) -> ApprenticeshipMetrics:
        """Return current help calibration and teaching counts."""
        return ApprenticeshipMetrics(
            blocked_high_uncertainty_cases=self._blocked_cases,
            help_requests_in_blocked_cases=self._blocked_help,
            familiar_low_risk_cases=self._familiar_cases,
            help_requests_in_familiar_cases=self._familiar_help,
            teacher_demonstrations=self._demonstrations,
            teacher_clarifications=self._clarifications,
            corrections=self._corrections,
            approvals=self._approvals,
            support_level=self.support_level,
            help_recall_threshold=self.config.pass_help_recall_threshold,
            help_avoidance_threshold=self.config.pass_help_avoidance_threshold,
        )

    def _is_blocked_high_uncertainty(self, context: HelpContext) -> bool:
        threshold = (
            self.config.level4_uncertainty_threshold
            if self.support_level is SupportLevel.DEPENDENT
            else self.config.level3_uncertainty_threshold
        )
        return (
            context.blocked_attempts >= self.config.blocked_attempt_threshold
            and context.uncertainty >= threshold
        )

    def _append_event(
        self,
        *,
        episode_id: str,
        step_index: int,
        request: HumanRequest,
        event_type: CaregiverEventType,
        uncertainty: float,
        competence: float,
        signal_code: HumanSignalCode | None = None,
        help_reason: HelpReason | None = None,
        verified: bool | None = None,
    ) -> None:
        self._event_index += 1
        self.memory.append(
            CaregiverEvent(
                event_id=f"caregiver-{self._event_index:06d}",
                episode_id=episode_id,
                step_index=step_index,
                request_id=request.request_id,
                event_type=event_type,
                support_level=self.support_level,
                uncertainty=uncertainty,
                competence=competence,
                signal_code=signal_code,
                help_reason=help_reason,
                verified=verified,
            )
        )


def export_apprenticeship_report_json(
    manager: ApprenticeshipManager,
    path: Path,
) -> None:
    """Write metrics and complete caregiver memory as ASCII JSON."""
    metrics = manager.metrics()
    payload = {
        "metrics": {
            "blocked_high_uncertainty_cases": metrics.blocked_high_uncertainty_cases,
            "help_requests_in_blocked_cases": metrics.help_requests_in_blocked_cases,
            "familiar_low_risk_cases": metrics.familiar_low_risk_cases,
            "help_requests_in_familiar_cases": metrics.help_requests_in_familiar_cases,
            "help_recall": metrics.help_recall,
            "help_avoidance_rate": metrics.help_avoidance_rate,
            "teacher_demonstrations": metrics.teacher_demonstrations,
            "teacher_clarifications": metrics.teacher_clarifications,
            "corrections": metrics.corrections,
            "approvals": metrics.approvals,
            "support_level": int(metrics.support_level),
            "pass_gate": metrics.pass_gate,
        },
        "caregiver_events": [_event_payload(event) for event in manager.memory.events],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def export_apprenticeship_timeline_csv(
    manager: ApprenticeshipManager,
    path: Path,
) -> None:
    """Write one ASCII row per caregiver event."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    with temporary_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "event_id",
                "episode_id",
                "step_index",
                "request_id",
                "event_type",
                "support_level",
                "uncertainty",
                "competence",
                "signal_code",
                "help_reason",
                "verified",
            )
        )
        for event in manager.memory.events:
            writer.writerow(
                (
                    event.event_id,
                    event.episode_id,
                    event.step_index,
                    event.request_id,
                    event.event_type.value,
                    int(event.support_level),
                    event.uncertainty,
                    event.competence,
                    event.signal_code.name.lower() if event.signal_code is not None else "",
                    event.help_reason.value if event.help_reason is not None else "",
                    "" if event.verified is None else str(event.verified).lower(),
                )
            )
    temporary_path.replace(path)


def _event_payload(event: CaregiverEvent) -> dict[str, object]:
    return {
        "event_id": event.event_id,
        "episode_id": event.episode_id,
        "step_index": event.step_index,
        "request_id": event.request_id,
        "event_type": event.event_type.value,
        "support_level": int(event.support_level),
        "uncertainty": event.uncertainty,
        "competence": event.competence,
        "signal_code": event.signal_code.name.lower() if event.signal_code is not None else None,
        "help_reason": event.help_reason.value if event.help_reason is not None else None,
        "verified": event.verified,
    }


def _validate_unit_interval(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
