"""Run the NDNRA dynamic-effects and novel-composition acceptance gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.research.ndnra.multieffect_experiment import (
    export_multieffect_evidence,
    run_ndnra_multieffect_experiment,
)


def parse_args() -> argparse.Namespace:
    """Parse deterministic evidence output settings."""
    parser = argparse.ArgumentParser(
        description=(
            "Test dynamically expanding local effect memory and compose an "
            "undemonstrated cooling solution."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ndnra_multieffect"),
    )
    return parser.parse_args()


def main() -> int:
    """Run the second isolated NDNRA experiment and print evidence."""
    args = parse_args()
    result, graph, shower_result, shared_result = run_ndnra_multieffect_experiment()
    report_path, candidates_path, graph_path = export_multieffect_evidence(
        result,
        graph,
        shower_result,
        shared_result,
        args.output_dir,
    )

    print(f"effect_dimension_count={result.effect_dimension_count}")
    print(f"shower_effect_dimension_count={result.shower_effect_dimension_count}")
    print(f"shower_link_dimension_count={result.shower_link_dimension_count}")
    print(f"shower_origin_need_code={result.shower_origin_need_code}")
    print(f"shower_cooling_compatibility={result.shower_cooling_compatibility:.8f}")
    print(f"shower_cleaning_success={str(result.shower_cleaning_success).lower()}")
    print(f"shower_reused_for_cooling={str(result.shower_reused_for_cooling).lower()}")
    print(f"direct_window_solution_success={str(result.direct_window_solution_success).lower()}")
    print(
        f"composed_window_solution_success={str(result.composed_window_solution_success).lower()}"
    )
    print("selected_window_actions=" + ",".join(result.selected_window_actions))
    print(
        "complete_window_sequence_was_stored="
        f"{str(result.complete_window_sequence_was_stored).lower()}"
    )
    print(
        "window_beats_shower_in_shared_context="
        f"{str(result.window_beats_shower_in_shared_context).lower()}"
    )
    print(
        "baseline_without_incidental_effect_success="
        f"{str(result.baseline_without_incidental_effect_success).lower()}"
    )
    print(f"selected_window_score={result.selected_window_score:.8f}")
    print(f"selected_shower_score={result.selected_shower_score:.8f}")
    print(f"explored_state_count={result.explored_state_count}")
    print(f"sqlite_used_for_composition={str(result.sqlite_used_for_composition).lower()}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"multieffect_report_json={report_path}")
    print(f"candidate_solutions_csv={candidates_path}")
    print(f"multidimensional_graph_json={graph_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
