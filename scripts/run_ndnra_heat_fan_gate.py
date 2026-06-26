"""Run the first NDNRA local-memory and need-recruitment acceptance gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.research.ndnra import (
    export_ndnra_evidence,
    run_ndnra_heat_fan_experiment,
)


def parse_args() -> argparse.Namespace:
    """Parse deterministic prototype settings."""
    parser = argparse.ArgumentParser(
        description="Test local neural memory, dormancy, and need-driven recall.",
    )
    parser.add_argument("--demonstrations", type=int, default=6)
    parser.add_argument("--dormancy", type=float, default=0.80)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ndnra_heat_fan"),
    )
    return parser.parse_args()


def main() -> int:
    """Run the isolated NDNRA experiment and print falsifiable evidence."""
    args = parse_args()
    result, graph = run_ndnra_heat_fan_experiment(
        demonstration_count=args.demonstrations,
        dormancy_level=args.dormancy,
    )
    report_path, timeline_path, graph_path = export_ndnra_evidence(
        result,
        graph,
        args.output_dir,
    )

    deep_first_cost = (
        result.deep_recall.records[0].computational_cost if result.deep_recall.records else 0
    )
    print(f"demonstrations={result.training.demonstration_count}")
    print(f"earliest_action_weight={result.training.earliest_action_weight:.8f}")
    print(f"latest_action_weight={result.training.latest_action_weight:.8f}")
    print(f"irrelevant_action_weight={result.training.irrelevant_action_weight:.8f}")
    print(f"baseline_success={str(result.baseline_recall.success).lower()}")
    print(f"shallow_recall_success={str(result.shallow_recall.success).lower()}")
    print(f"deep_recall_success={str(result.deep_recall.success).lower()}")
    print(
        "deep_recalled_actions=" + ",".join(action.value for action in result.deep_recall.actions)
    )
    print(f"deep_maximum_depth_used={result.deep_recall.maximum_depth_used}")
    print(f"deep_first_action_cost={deep_first_cost}")
    print(f"deep_total_cost={result.deep_recall.total_computational_cost}")
    print(f"neuron_count_before_dormancy={result.neuron_count_before_dormancy}")
    print(f"neuron_count_after_dormancy={result.neuron_count_after_dormancy}")
    print(f"synapse_count_before_dormancy={result.synapse_count_before_dormancy}")
    print(f"synapse_count_after_dormancy={result.synapse_count_after_dormancy}")
    print(f"growth_pressure={result.growth_pressure:.8f}")
    print(f"sqlite_used_for_recall={str(result.sqlite_used_for_recall).lower()}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"ndnra_report_json={report_path}")
    print(f"recall_timeline_csv={timeline_path}")
    print(f"local_graph_state_json={graph_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
