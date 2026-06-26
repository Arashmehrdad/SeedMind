"""Run the NDNRA evidence-driven structural-growth acceptance gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.research.ndnra.growth_experiment import (
    export_structural_growth_evidence,
    run_ndnra_structural_growth_experiment,
)


def parse_args() -> argparse.Namespace:
    """Parse deterministic evidence output settings."""
    parser = argparse.ArgumentParser(
        description=(
            "Test curiosity-and-ambition pressure, local eligibility, targeted "
            "specialist growth, and a random-capacity baseline."
        ),
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ndnra_structural_growth"),
    )
    return parser.parse_args()


def main() -> int:
    """Run the third isolated NDNRA experiment and print evidence."""
    args = parse_args()
    result, targeted_graph, random_graph, attempts = run_ndnra_structural_growth_experiment()
    report_path, timeline_path, targeted_path, random_path = export_structural_growth_evidence(
        result,
        targeted_graph,
        random_graph,
        attempts,
        args.output_dir,
    )

    print(f"base_assembly_count={result.base_assembly_count}")
    print(f"base_specialist_count={result.base_specialist_count}")
    print(f"base_structural_node_count={result.base_structural_node_count}")
    print(f"base_predicted_temperature_effect={result.base_predicted_temperature_effect:.8f}")
    print(f"actual_temperature_effect={result.actual_temperature_effect:.8f}")
    print(f"residual_temperature_effect={result.residual_temperature_effect:.8f}")
    print(f"before_growth_success={str(result.before_growth_success).lower()}")
    print(f"growth_attempt_count={result.growth_attempt_count}")
    print(f"first_growth_ready_attempt={result.first_growth_ready_attempt}")
    print(f"premature_growth_blocked={str(result.premature_growth_blocked).lower()}")
    print(f"final_growth_pressure={result.final_growth_pressure:.8f}")
    print(f"targeted_specialist_id={result.targeted_specialist_id}")
    print("targeted_specialist_members=" + ",".join(result.targeted_specialist_members))
    print(f"targeted_specialist_effect={result.targeted_specialist_effect:.8f}")
    print(f"targeted_structural_nodes_after={result.targeted_structural_nodes_after}")
    print(
        f"targeted_old_assemblies_preserved={str(result.targeted_old_assemblies_preserved).lower()}"
    )
    print(f"targeted_solution_success={str(result.targeted_solution_success).lower()}")
    print("targeted_actions=" + ",".join(result.targeted_actions))
    print(f"targeted_primary_satisfaction={result.targeted_primary_satisfaction:.8f}")
    print("random_specialist_members=" + ",".join(result.random_specialist_members))
    print(f"random_structural_nodes_after={result.random_structural_nodes_after}")
    print(f"random_solution_success={str(result.random_solution_success).lower()}")
    print(f"random_primary_satisfaction={result.random_primary_satisfaction:.8f}")
    print(f"targeted_beats_random={str(result.targeted_beats_random).lower()}")
    print(f"duplicate_growth_blocked={str(result.duplicate_growth_blocked).lower()}")
    print(f"sqlite_used_for_growth={str(result.sqlite_used_for_growth).lower()}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"structural_growth_report_json={report_path}")
    print(f"growth_pressure_timeline_csv={timeline_path}")
    print(f"targeted_growth_graph_json={targeted_path}")
    print(f"random_growth_graph_json={random_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
