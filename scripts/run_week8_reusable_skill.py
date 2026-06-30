"""Run the SeedMind Week 8 reusable skill gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.skills import run_week8_reusable_skill_evaluation


def parse_args() -> argparse.Namespace:
    """Parse deterministic Week 8 runner settings."""
    parser = argparse.ArgumentParser(
        description="Compile and evaluate the main SeedMind approach_and_push skill.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/week8_reusable_skill"),
    )
    return parser.parse_args()


def main() -> int:
    """Run Week 8, export evidence, and print core metrics."""
    args = parse_args()
    result = run_week8_reusable_skill_evaluation(output_dir=args.output_dir)
    report = result.report

    print(f"training_seeds={','.join(str(seed) for seed in report.training_seeds)}")
    print(f"evaluation_seeds={','.join(str(seed) for seed in report.evaluation_seeds)}")
    print(f"success_rate={report.success_rate:.4f}")
    print(f"baseline_success_rate={report.baseline_success_rate:.4f}")
    print(f"compilation_evidence_count={report.compilation_evidence_count}")
    print(f"skill_invocation_count={report.skill_invocation_count}")
    print(f"reuse_count={report.reuse_count}")
    print(f"discovery_count={report.discovery_count}")
    print(f"authority_violations={report.authority_violations}")
    print(f"ndnra_shadow_observation_count={report.ndnra_shadow_observation_count}")
    print(f"ndnra_authority_violations={report.ndnra_authority_violations}")
    print(f"ndnra_automatic_promotions={report.ndnra_automatic_promotions}")
    print(f"pass_gate={str(report.pass_gate).lower()}")
    print(f"skill_record={args.output_dir / 'approach_and_push_skill_record.json'}")
    print(f"generalisation_report={args.output_dir / 'week8_generalisation_report.json'}")
    return 0 if report.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
