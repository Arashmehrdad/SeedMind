"""Run bounded NDNRA advice and goal-gated repeated-growth acceptance."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.integration.advice_acceptance import (
    export_advice_acceptance,
    run_advice_acceptance,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Compare NDNRA advice against retained production actions, calibrate "
            "confidence from cloned outcomes, test vetoes and kill switch, and "
            "verify pressure releases only after repeated growth resolves the goal."
        )
    )
    parser.add_argument("--first-seed", type=int, default=7)
    parser.add_argument("--second-seed", type=int, default=11)
    parser.add_argument("--budget", type=int, default=18)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ndnra_advice"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = run_advice_acceptance(
        args.output_dir,
        first_seed=args.first_seed,
        second_seed=args.second_seed,
        play_budget=args.budget,
    )
    report_path, timeline_path, growth_path = export_advice_acceptance(
        evidence,
        args.output_dir,
    )
    result = evidence.result

    print(f"pretraining_selection_count={result.pretraining_selection_count}")
    print(f"pretraining_assembly_count={result.pretraining_assembly_count}")
    print(f"pretraining_effect_dimension_count={result.pretraining_effect_dimension_count}")
    print(f"baseline_selection_count={result.baseline_selection_count}")
    print(f"advice_selection_count={result.advice_selection_count}")
    print(f"production_actions_unchanged={str(result.production_actions_unchanged).lower()}")
    print(f"prediction_errors_unchanged={str(result.prediction_errors_unchanged).lower()}")
    print(f"disagreement_count={result.disagreement_count}")
    print(f"comparison_count={result.comparison_count}")
    print(f"advice_count={result.advice_count}")
    print(f"agreement_count={result.agreement_count}")
    print(f"abstention_count={result.abstention_count}")
    print(f"live_veto_count={result.live_veto_count}")
    print(f"ndnra_better_count={result.ndnra_better_count}")
    print(f"advised_better_count={result.advised_better_count}")
    print(f"advice_precision={result.advice_precision:.8f}")
    print(f"calibration_observation_count={result.calibration_observation_count}")
    print(f"calibration_error={result.calibration_error:.8f}")
    print(f"calibration_reliability={result.calibration_reliability:.8f}")
    print(f"authority_violation_count={result.authority_violation_count}")
    print(f"kill_switch_probe_passed={str(result.kill_switch_probe_passed).lower()}")
    print(f"fallback_probe_passed={str(result.fallback_probe_passed).lower()}")
    print(f"risk_veto_probe_passed={str(result.risk_veto_probe_passed).lower()}")
    print(f"human_veto_probe_passed={str(result.human_veto_probe_passed).lower()}")
    print(f"weak_evidence_probe_passed={str(result.weak_evidence_probe_passed).lower()}")
    print(f"first_growth_goal_achieved={str(result.first_growth_goal_achieved).lower()}")
    print(
        f"first_growth_pressure_discharged={str(result.first_growth_pressure_discharged).lower()}"
    )
    print(f"first_growth_continue_growth={str(result.first_growth_continue_growth).lower()}")
    print(f"second_growth_goal_achieved={str(result.second_growth_goal_achieved).lower()}")
    print(
        f"second_growth_pressure_discharged={str(result.second_growth_pressure_discharged).lower()}"
    )
    print(f"growth_step_count={result.growth_step_count}")
    print(f"duplicate_growth_blocked={str(result.duplicate_growth_blocked).lower()}")
    print(
        "growth_budget_exhaustion_probe_passed="
        f"{str(result.growth_budget_exhaustion_probe_passed).lower()}"
    )
    print(
        f"sqlite_used_for_advice_or_growth={str(result.sqlite_used_for_advice_or_growth).lower()}"
    )
    print(f"theory_readiness_before={result.theory_readiness_before}")
    print(f"theory_readiness_after={result.theory_readiness_after}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"advice_acceptance_report_json={report_path}")
    print(f"advice_timeline_csv={timeline_path}")
    print(f"multi_growth_report_json={growth_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
