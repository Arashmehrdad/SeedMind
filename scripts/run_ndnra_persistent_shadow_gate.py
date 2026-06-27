"""Run the NDNRA non-SQL cross-session persistence acceptance gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.integration import (
    export_persistent_shadow_evidence,
    run_persistent_shadow_experiment,
)


def parse_args() -> argparse.Namespace:
    """Parse deterministic persistence experiment settings."""
    parser = argparse.ArgumentParser(
        description=(
            "Learn NDNRA local shadow state, save it atomically, reconstruct it "
            "after a process-equivalent restart, and compare with a fresh graph."
        ),
    )
    parser.add_argument("--first-seed", type=int, default=7)
    parser.add_argument("--second-seed", type=int, default=11)
    parser.add_argument("--budget", type=int, default=6)
    parser.add_argument("--ambition-relevance", type=float, default=0.75)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ndnra_persistent_shadow"),
    )
    return parser.parse_args()


def main() -> int:
    """Run the persistence gate, export evidence, and print core metrics."""
    args = parse_args()
    evidence = run_persistent_shadow_experiment(
        args.output_dir,
        first_seed=args.first_seed,
        second_seed=args.second_seed,
        play_budget=args.budget,
        ambition_relevance=args.ambition_relevance,
    )
    report_path, timeline_path, graph_path = export_persistent_shadow_evidence(
        evidence,
        args.output_dir,
    )
    result = evidence.result

    print(f"first_session_selection_count={result.first_session_selection_count}")
    print(f"first_session_assembly_count={result.first_session_assembly_count}")
    print(f"first_session_effect_dimension_count={result.first_session_effect_dimension_count}")
    print(f"saved_schema_version={result.saved_schema_version}")
    print(f"saved_byte_count={result.saved_byte_count}")
    print(f"temporary_file_remaining={str(result.temporary_file_remaining).lower()}")
    print(f"load_status={result.load_status}")
    print(f"checksum_verified={str(result.checksum_verified).lower()}")
    print(f"graph_round_trip_exact={str(result.graph_round_trip_exact).lower()}")
    print(f"growth_state_round_trip_exact={str(result.growth_state_round_trip_exact).lower()}")
    print(
        "loaded_step_zero_suggestion_available="
        f"{str(result.loaded_step_zero_suggestion_available).lower()}"
    )
    print(
        "fresh_step_zero_suggestion_available="
        f"{str(result.fresh_step_zero_suggestion_available).lower()}"
    )
    print(
        f"loaded_step_zero_suggestion_valid={str(result.loaded_step_zero_suggestion_valid).lower()}"
    )
    print(
        "second_session_action_sequence_unchanged="
        f"{str(result.second_session_action_sequence_unchanged).lower()}"
    )
    print(
        "second_session_prediction_errors_unchanged="
        f"{str(result.second_session_prediction_errors_unchanged).lower()}"
    )
    print(f"loaded_evidence_count_after={result.loaded_evidence_count_after}")
    print(f"fresh_evidence_count_after={result.fresh_evidence_count_after}")
    print(
        f"cross_session_evidence_advantage={str(result.cross_session_evidence_advantage).lower()}"
    )
    print(f"corruption_fallback_status={result.corruption_fallback_status}")
    print(f"corruption_fallback_fresh={str(result.corruption_fallback_fresh).lower()}")
    print(f"incompatible_fallback_status={result.incompatible_fallback_status}")
    print(f"incompatible_fallback_fresh={str(result.incompatible_fallback_fresh).lower()}")
    print(
        "sqlite_used_for_persistence_or_recall="
        f"{str(result.sqlite_used_for_persistence_or_recall).lower()}"
    )
    print(f"theory_readiness_before={result.theory_readiness_before}")
    print(f"theory_readiness_after={result.theory_readiness_after}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"brain_state_json={evidence.state_path}")
    print(f"persistent_shadow_report_json={report_path}")
    print(f"persistent_shadow_timeline_csv={timeline_path}")
    print(f"reloaded_shadow_graph_json={graph_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
