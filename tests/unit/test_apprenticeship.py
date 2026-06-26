"""Tests for calibrated help seeking and caregiver apprenticeship memory."""

from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.human import (
    ApprenticeshipManager,
    CaregiverEventType,
    HelpContext,
    HelpReason,
    HelpSeekingPolicy,
    HumanRequest,
    HumanSignalCode,
    RequestIntentCode,
    SupportLevel,
    VerificationRule,
    export_apprenticeship_report_json,
    export_apprenticeship_timeline_csv,
)


def make_request(*, ambiguity: float = 0.1) -> HumanRequest:
    return HumanRequest(
        request_id="request-001",
        intent_code=RequestIntentCode.REPRODUCE_OBSERVED_OUTCOME,
        target_code="outcome-signature-001",
        ambiguity=ambiguity,
        permission_level=2,
        verification_rule=VerificationRule.CONFIRMED_OUTCOME,
    )


def make_context(
    case_id: str,
    *,
    request: HumanRequest | None = None,
    uncertainty: float,
    competence: float,
    risk: float,
    blocked_attempts: int,
    safe_experiment_available: bool,
    familiar: bool,
) -> HelpContext:
    return HelpContext(
        case_id=case_id,
        request=make_request() if request is None else request,
        uncertainty=uncertainty,
        competence=competence,
        risk=risk,
        blocked_attempts=blocked_attempts,
        safe_experiment_available=safe_experiment_available,
        familiar=familiar,
    )


def blocked_context(case_id: str = "blocked-001") -> HelpContext:
    return make_context(
        case_id,
        uncertainty=0.9,
        competence=0.2,
        risk=0.4,
        blocked_attempts=3,
        safe_experiment_available=False,
        familiar=False,
    )


def familiar_context(case_id: str = "familiar-001") -> HelpContext:
    return make_context(
        case_id,
        uncertainty=0.1,
        competence=0.9,
        risk=0.1,
        blocked_attempts=0,
        safe_experiment_available=True,
        familiar=True,
    )


def test_blocked_high_uncertainty_requests_help() -> None:
    decision = HelpSeekingPolicy().decide(
        blocked_context(),
        support_level=SupportLevel.DEPENDENT,
    )
    assert decision.should_request_help
    assert decision.selected_action is PrimitiveAction.REQUEST_HELP
    assert decision.reason is HelpReason.BLOCKED_HIGH_UNCERTAINTY


def test_familiar_low_risk_avoids_unnecessary_help() -> None:
    decision = HelpSeekingPolicy().decide(
        familiar_context(),
        support_level=SupportLevel.GUIDED_LEARNER,
    )
    assert not decision.should_request_help
    assert decision.selected_action is None
    assert decision.reason is HelpReason.FAMILIAR_LOW_RISK


def test_safe_low_cost_experiment_is_preferred_over_help() -> None:
    context = make_context(
        "safe-experiment",
        uncertainty=0.7,
        competence=0.2,
        risk=0.1,
        blocked_attempts=0,
        safe_experiment_available=True,
        familiar=False,
    )
    decision = HelpSeekingPolicy().decide(
        context,
        support_level=SupportLevel.DEPENDENT,
    )
    assert not decision.should_request_help
    assert decision.reason is HelpReason.SAFE_EXPERIMENT_AVAILABLE


def test_guided_learner_requires_more_uncertainty_than_dependent_level() -> None:
    context = make_context(
        "support-sensitive",
        uncertainty=0.65,
        competence=0.2,
        risk=0.3,
        blocked_attempts=2,
        safe_experiment_available=False,
        familiar=False,
    )
    policy = HelpSeekingPolicy()
    dependent = policy.decide(context, support_level=SupportLevel.DEPENDENT)
    guided = policy.decide(context, support_level=SupportLevel.GUIDED_LEARNER)
    assert dependent.should_request_help
    assert not guided.should_request_help


def test_teacher_demonstrates_blockage_and_clarifies_ambiguity() -> None:
    manager = ApprenticeshipManager()
    blocked = blocked_context()
    blocked_decision = manager.evaluate(blocked, episode_id="episode-1", step_index=1)
    demonstration = manager.teacher_response(
        blocked,
        blocked_decision,
        episode_id="episode-1",
        step_index=2,
    )
    ambiguous_request = make_request(ambiguity=0.9)
    ambiguous = make_context(
        "ambiguous",
        request=ambiguous_request,
        uncertainty=0.8,
        competence=0.4,
        risk=0.2,
        blocked_attempts=0,
        safe_experiment_available=True,
        familiar=False,
    )
    ambiguous_decision = manager.evaluate(
        ambiguous,
        episode_id="episode-2",
        step_index=1,
    )
    clarification = manager.teacher_response(
        ambiguous,
        ambiguous_decision,
        episode_id="episode-2",
        step_index=2,
    )
    assert demonstration.code is HumanSignalCode.DEMONSTRATE
    assert clarification.code is HumanSignalCode.CLARIFY


def test_verified_familiar_approvals_promote_support_level() -> None:
    manager = ApprenticeshipManager()
    request = make_request()
    for index in range(3):
        manager.record_approval(
            request,
            episode_id=f"approval-{index}",
            step_index=1,
            uncertainty=0.1,
            competence=0.9,
            verified=True,
            familiar=True,
        )
    assert manager.support_level is SupportLevel.GUIDED_LEARNER
    assert manager.memory.events[-1].event_type is CaregiverEventType.SUPPORT_PROMOTED


def test_metrics_and_timeline_exports_pass_gate(tmp_path: Path) -> None:
    manager = ApprenticeshipManager()
    request = make_request()
    manager.receive_request(request, episode_id="request-episode", step_index=0)
    for index in range(4):
        context = blocked_context(f"blocked-{index}")
        decision = manager.evaluate(
            context,
            episode_id=f"blocked-episode-{index}",
            step_index=1,
        )
        manager.teacher_response(
            context,
            decision,
            episode_id=f"blocked-episode-{index}",
            step_index=2,
        )
    for index in range(4):
        context = familiar_context(f"familiar-{index}")
        decision = manager.evaluate(
            context,
            episode_id=f"familiar-episode-{index}",
            step_index=1,
        )
        assert not decision.should_request_help
        manager.record_approval(
            request,
            episode_id=f"familiar-episode-{index}",
            step_index=2,
            uncertainty=context.uncertainty,
            competence=context.competence,
            verified=True,
            familiar=True,
        )
    metrics = manager.metrics()
    report_path = tmp_path / "report.json"
    timeline_path = tmp_path / "timeline.csv"
    export_apprenticeship_report_json(manager, report_path)
    export_apprenticeship_timeline_csv(manager, timeline_path)
    assert metrics.help_recall == 1.0
    assert metrics.help_avoidance_rate == 1.0
    assert metrics.pass_gate
    assert metrics.support_level is SupportLevel.GUIDED_LEARNER
    report = report_path.read_text(encoding="ascii")
    timeline = timeline_path.read_text(encoding="ascii")
    assert '"pass_gate": true' in report
    assert '"help_recall": 1.0' in report
    assert timeline.startswith("event_id,episode_id,step_index")
    assert "support_promoted" in timeline
