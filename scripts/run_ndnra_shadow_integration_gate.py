"""Run the NDNRA non-authoritative shadow-integration acceptance gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.integration import (
    export_shadow_comparison_evidence,
    run_shadow_comparison,
)


def parse_args() -> argparse.Namespace:
    """Parse deterministic shadow comparison settings."""
    parser = argparse.ArgumentParser(
        description=(
            "Compare the production curiosity loop with an identical run observed "
            "by non-authoritative NDNRA shadow mode."
        ),
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--budget", type=int, default=12)
    parser.add_argument("--ambition-relevance", type=float, default=0.75)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ndnra_shadow_integration"),
    )
    return parser.parse_args()


def main() -> int:
    """Run the comparison, export evidence, and print acceptance metrics."""
    args = parse_args()
    result, shadow = run_shadow_comparison(
        seed=args.seed,
        play_budget=args.budget,
        ambition_relevance=args.ambition_relevance,
    )
    report_path, timeline_path, graph_path = export_shadow_comparison_evidence(
        result,
        shadow,
        args.output_dir,
    )

    print(f"scenario_id={result.scenario_id}")
    print(f"play_budget={result.play_budget}")
    print(f"baseline_selection_count={result.baseline_selection_count}")
    print(f"shadow_selection_count={result.shadow_selection_count}")
    print(f"action_sequence_unchanged={str(result.action_sequence_unchanged).lower()}")
    print(
        "prediction_error_sequence_unchanged="
        f"{str(result.prediction_error_sequence_unchanged).lower()}"
    )
    print(f"observed_transition_count={result.observed_transition_count}")
    print(f"suggestion_count={result.suggestion_count}")
    print(f"valid_suggestion_count={result.valid_suggestion_count}")
    print(f"suggestion_match_count={result.suggestion_match_count}")
    print(f"suggestion_match_rate={result.suggestion_match_rate:.8f}")
    print(f"authority_violation_count={result.authority_violation_count}")
    print(f"learned_assembly_count={result.learned_assembly_count}")
    print(f"effect_dimension_count={result.effect_dimension_count}")
    print(
        "expected_effect_dimensions_present="
        f"{str(result.expected_effect_dimensions_present).lower()}"
    )
    print(f"first_suggestion_step={result.first_suggestion_step}")
    print(
        f"sqlite_used_for_shadow_decisions={str(result.sqlite_used_for_shadow_decisions).lower()}"
    )
    print(f"integration_percentage_before={result.integration_percentage_before}")
    print(f"integration_percentage_after={result.integration_percentage_after}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"shadow_comparison_report_json={report_path}")
    print(f"shadow_timeline_csv={timeline_path}")
    print(f"shadow_graph_json={graph_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
