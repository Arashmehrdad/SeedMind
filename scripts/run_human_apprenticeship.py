"""Run the Week 6 symbolic human-apprenticeship acceptance gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.environment import NurseryRuntime, TeacherDemonstrationScenarioFactory
from seedmind.human import (
    ApprenticeshipManager,
    HelpContext,
    HumanRequest,
    RequestIntentCode,
    SupportLevel,
    VerificationRule,
    export_apprenticeship_report_json,
    export_apprenticeship_timeline_csv,
)


def parse_args() -> argparse.Namespace:
    """Parse deterministic apprenticeship evidence settings."""
    parser = argparse.ArgumentParser(
        description="Evaluate calibrated help seeking and caregiver apprenticeship.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--blocked-cases", type=int, default=4)
    parser.add_argument("--familiar-cases", type=int, default=4)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/human_apprenticeship"),
    )
    return parser.parse_args()


def main() -> int:
    """Run help calibration, teacher responses, promotion, and exports."""
    args = parse_args()
    if args.blocked_cases <= 0 or args.familiar_cases <= 0:
        raise ValueError("blocked and familiar case counts must be positive")

    manager = ApprenticeshipManager()
    request = HumanRequest(
        request_id="request-reproduce-outcome-001",
        intent_code=RequestIntentCode.REPRODUCE_OBSERVED_OUTCOME,
        target_code="active-demonstrated-outcome",
        ambiguity=0.1,
        permission_level=2,
        verification_rule=VerificationRule.CONFIRMED_OUTCOME,
    )
    scenario = TeacherDemonstrationScenarioFactory().create(args.seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id="apprenticeship-channel-episode",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    request_frame = manager.receive_request(
        request,
        episode_id=runtime.episode_id,
        step_index=0,
    )
    request_signal = manager.codec.encode(request_frame)
    request_observation = runtime.observe(human_signal=request_signal)
    request_help_action_executed = False

    for case_index in range(args.blocked_cases):
        context = HelpContext(
            case_id=f"blocked-{case_index:04d}",
            request=request,
            uncertainty=0.90,
            competence=0.20,
            risk=0.40,
            blocked_attempts=3,
            safe_experiment_available=False,
            familiar=False,
        )
        episode_id = f"blocked-episode-{case_index:04d}"
        decision = manager.evaluate(context, episode_id=episode_id, step_index=1)
        response_frame = manager.teacher_response(
            context,
            decision,
            episode_id=episode_id,
            step_index=2,
        )
        if case_index == 0:
            response_signal = manager.codec.encode(response_frame)
            step = runtime.step(
                PrimitiveAction.REQUEST_HELP,
                human_signal=response_signal,
            )
            request_help_action_executed = (
                step.transition.action is PrimitiveAction.REQUEST_HELP
                and step.observation.human_signal == response_signal
            )
            manager.record_correction(
                request,
                episode_id=episode_id,
                step_index=3,
                uncertainty=0.70,
                competence=0.25,
            )

    for case_index in range(args.familiar_cases):
        context = HelpContext(
            case_id=f"familiar-{case_index:04d}",
            request=request,
            uncertainty=0.10,
            competence=0.90,
            risk=0.10,
            blocked_attempts=0,
            safe_experiment_available=True,
            familiar=True,
        )
        episode_id = f"familiar-episode-{case_index:04d}"
        decision = manager.evaluate(context, episode_id=episode_id, step_index=1)
        if decision.should_request_help:
            raise RuntimeError("familiar low-risk case requested unnecessary help")
        manager.record_approval(
            request,
            episode_id=episode_id,
            step_index=2,
            uncertainty=context.uncertainty,
            competence=context.competence,
            verified=True,
            familiar=True,
        )

    ambiguous_request = HumanRequest(
        request_id="request-ambiguous-001",
        intent_code=RequestIntentCode.PRACTICE_ACTIVE_AMBITION,
        target_code="active-ambition",
        ambiguity=0.90,
        permission_level=1,
        verification_rule=VerificationRule.EXTERNAL_CHANGE,
    )
    ambiguous_context = HelpContext(
        case_id="ambiguous-0000",
        request=ambiguous_request,
        uncertainty=0.80,
        competence=0.50,
        risk=0.10,
        blocked_attempts=0,
        safe_experiment_available=True,
        familiar=False,
    )
    ambiguous_decision = manager.evaluate(
        ambiguous_context,
        episode_id="ambiguous-episode-0000",
        step_index=1,
    )
    manager.teacher_response(
        ambiguous_context,
        ambiguous_decision,
        episode_id="ambiguous-episode-0000",
        step_index=2,
    )

    metrics = manager.metrics()
    report_path = args.output_dir / "apprenticeship_report.json"
    timeline_path = args.output_dir / "apprenticeship_timeline.csv"
    export_apprenticeship_report_json(manager, report_path)
    export_apprenticeship_timeline_csv(manager, timeline_path)
    pass_gate = (
        metrics.pass_gate
        and manager.support_level is SupportLevel.GUIDED_LEARNER
        and request_help_action_executed
        and len(request_observation.human_signal) == manager.codec.width
    )

    print(f"blocked_high_uncertainty_cases={metrics.blocked_high_uncertainty_cases}")
    print(f"help_requests_in_blocked_cases={metrics.help_requests_in_blocked_cases}")
    print(f"help_recall={metrics.help_recall:.8f}")
    print(f"familiar_low_risk_cases={metrics.familiar_low_risk_cases}")
    print(f"help_requests_in_familiar_cases={metrics.help_requests_in_familiar_cases}")
    print(f"help_avoidance_rate={metrics.help_avoidance_rate:.8f}")
    print(f"teacher_demonstrations={metrics.teacher_demonstrations}")
    print(f"teacher_clarifications={metrics.teacher_clarifications}")
    print(f"corrections={metrics.corrections}")
    print(f"approvals={metrics.approvals}")
    print(f"support_level={int(metrics.support_level)}")
    print(f"human_signal_width={manager.codec.width}")
    print(f"request_help_action_executed={str(request_help_action_executed).lower()}")
    print(f"caregiver_event_count={len(manager.memory.events)}")
    print(f"pass_gate={str(pass_gate).lower()}")
    print(f"apprenticeship_report_json={report_path}")
    print(f"apprenticeship_timeline_csv={timeline_path}")
    return 0 if pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
