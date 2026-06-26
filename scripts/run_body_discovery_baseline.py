"""Run the Week 3 targeted body-discovery comparison gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.environment import DynamicNurseryScenarioFactory
from seedmind.self_model import (
    BodyDiscoveryBaselineConfig,
    BodyDiscoveryBaselineExperiment,
    export_body_discovery_baseline_csv,
    export_body_discovery_baseline_json,
)


def parse_args() -> argparse.Namespace:
    """Parse deterministic matched-budget comparison settings."""
    parser = argparse.ArgumentParser(
        description=("Compare targeted primitive body probes with random safe actions."),
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--random-seed", type=int, default=29)
    parser.add_argument("--budget", type=int, default=12)
    parser.add_argument("--random-trials", type=int, default=16)
    parser.add_argument("--minimum-samples", type=int, default=4)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/body_discovery_baseline"),
    )
    return parser.parse_args()


def main() -> int:
    """Run the comparison, export evidence, and return its gate verdict."""
    args = parse_args()
    config = BodyDiscoveryBaselineConfig(
        scenario_seed=args.seed,
        random_seed=args.random_seed,
        transition_budget=args.budget,
        random_trials=args.random_trials,
        minimum_samples=args.minimum_samples,
    )
    result = BodyDiscoveryBaselineExperiment(
        DynamicNurseryScenarioFactory(),
        config,
    ).run()
    json_path = args.output_dir / "baseline_report.json"
    csv_path = args.output_dir / "baseline_trials.csv"
    export_body_discovery_baseline_json(result, json_path)
    export_body_discovery_baseline_csv(result, csv_path)

    oracle_indices = ",".join(str(index) for index in result.oracle_body_sensor_indices)
    print(f"transition_budget={config.transition_budget}")
    print(f"random_trials={config.random_trials}")
    print(f"oracle_body_sensor_indices={oracle_indices}")
    print(f"active_effect_count={result.active_effect_count}")
    print(f"targeted_body_effect_mae={result.targeted.body_effect_mean_absolute_error:.8f}")
    print(f"random_mean_body_effect_mae={result.random_mean_body_effect_error:.8f}")
    print(f"targeted_body_effect_recall={result.targeted.body_effect_recall:.8f}")
    print(f"random_mean_body_effect_recall={result.random_mean_body_effect_recall:.8f}")
    print(f"targeted_body_f1={result.targeted.body_f1:.8f}")
    print(f"random_mean_body_f1={result.random_mean_body_f1:.8f}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"baseline_report_json={json_path}")
    print(f"baseline_trials_csv={csv_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
