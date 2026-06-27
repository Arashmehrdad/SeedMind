"""Run the unified live-signal and restored-adaptive-state acceptance gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.integration import (
    export_unified_signal_evidence,
    run_unified_signal_experiment,
)


def parse_args() -> argparse.Namespace:
    """Parse deterministic integrated developmental-session settings."""
    parser = argparse.ArgumentParser(
        description=(
            "Connect live ambition, curiosity, self-model, apprenticeship, "
            "prediction, resources, restored dormancy, eligibility, and growth "
            "pressure while preserving non-authoritative production behavior."
        ),
    )
    parser.add_argument("--first-seed", type=int, default=7)
    parser.add_argument("--second-seed", type=int, default=11)
    parser.add_argument("--budget", type=int, default=12)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ndnra_unified_signals"),
    )
    return parser.parse_args()


def main() -> int:
    """Run the gate, export evidence, and print acceptance metrics."""
    args = parse_args()
    evidence = run_unified_signal_experiment(
        args.output_dir,
        first_seed=args.first_seed,
        second_seed=args.second_seed,
        play_budget=args.budget,
    )
    report_path, timeline_path, adaptive_path = export_unified_signal_evidence(
        evidence,
        args.output_dir,
    )
    result = evidence.result

    print(f"pretraining_selection_count={result.pretraining_selection_count}")
    print(f"persisted_assembly_count={result.persisted_assembly_count}")
    print(f"persisted_effect_dimension_count={result.persisted_effect_dimension_count}")
    print(f"restored_pressure_before={result.restored_pressure_before:.8f}")
    print(f"restored_pressure_after={result.restored_pressure_after:.8f}")
    print(f"restored_attempt_count_before={result.restored_attempt_count_before}")
    print(f"restored_attempt_count_after={result.restored_attempt_count_after}")
    print(f"restored_first_eligibility_before={result.restored_first_eligibility_before:.8f}")
    print(f"restored_first_eligibility_after={result.restored_first_eligibility_after:.8f}")
    print(f"restored_eligibility_continued={str(result.restored_eligibility_continued).lower()}")
    print(f"most_dormant_assembly_id={result.most_dormant_assembly_id}")
    print(f"restored_dormancy_level={result.restored_dormancy_level:.8f}")
    print(f"restored_accessibility={result.restored_accessibility:.8f}")
    print(f"reset_accessibility={result.reset_accessibility:.8f}")
    print(f"restored_action_score={result.restored_action_score:.8f}")
    print(f"reset_action_score={result.reset_action_score:.8f}")
    print(f"dormancy_changed_accessibility={str(result.dormancy_changed_accessibility).lower()}")
    print(f"dormancy_changed_action_score={str(result.dormancy_changed_action_score).lower()}")
    print(f"ambition_relevance_min={result.ambition_relevance_min:.8f}")
    print(f"ambition_relevance_max={result.ambition_relevance_max:.8f}")
    print(f"ambition_relevance_varied={str(result.ambition_relevance_varied).lower()}")
    print(f"maximum_self_controllability={result.maximum_self_controllability:.8f}")
    print(f"maximum_body_confidence={result.maximum_body_confidence:.8f}")
    print(f"help_request_count={result.help_request_count}")
    print(f"approval_count={result.approval_count}")
    print(f"correction_count={result.correction_count}")
    print(f"demonstration_count={result.demonstration_count}")
    print(f"clarification_count={result.clarification_count}")
    print(f"human_response_count={result.human_response_count}")
    print(f"live_signal_dimension_count={result.live_signal_dimension_count}")
    print(f"baseline_selection_count={result.baseline_selection_count}")
    print(f"unified_selection_count={result.unified_selection_count}")
    print(f"production_actions_unchanged={str(result.production_actions_unchanged).lower()}")
    print(f"prediction_errors_unchanged={str(result.prediction_errors_unchanged).lower()}")
    print(f"authority_violation_count={result.authority_violation_count}")
    print(f"valid_suggestion_count={result.valid_suggestion_count}")
    print(
        "sqlite_used_for_signals_or_adaptation="
        f"{str(result.sqlite_used_for_signals_or_adaptation).lower()}"
    )
    print(f"theory_readiness_before={result.theory_readiness_before}")
    print(f"theory_readiness_after={result.theory_readiness_after}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"initial_brain_state_json={evidence.initial_brain_path}")
    print(f"final_brain_state_json={evidence.final_brain_path}")
    print(f"unified_signal_report_json={report_path}")
    print(f"unified_signal_timeline_csv={timeline_path}")
    print(f"unified_adaptive_state_json={adaptive_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
