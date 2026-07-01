"""Run the original SeedMind Week 10 capacity-diagnosis gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.growth import DEFAULT_WEEK10_OUTPUT_DIR, run_week10_capacity_diagnosis


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Diagnose temporary failure versus sustained blockage without growth.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=DEFAULT_WEEK10_OUTPUT_DIR,
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    result = run_week10_capacity_diagnosis(output_dir=args.output_dir)
    report = result.acceptance_report
    print(f"environment_extension_pass={str(report.environment_extension_pass).lower()}")
    print(
        f"grounded_attempt_provenance_pass={str(report.grounded_attempt_provenance_pass).lower()}"
    )
    print(f"learning_progress_pass={str(report.learning_progress_pass).lower()}")
    print(
        "temporary_failure_classification_pass="
        f"{str(report.temporary_failure_classification_pass).lower()}"
    )
    print(
        "sustained_blockage_classification_pass="
        f"{str(report.sustained_blockage_classification_pass).lower()}"
    )
    print(f"diagnostic_ladder_pass={str(report.diagnostic_ladder_pass).lower()}")
    print(f"memory_replay_grounding_pass={str(report.memory_replay_grounding_pass).lower()}")
    print(
        "teacher_demonstration_grounding_pass="
        f"{str(report.teacher_demonstration_grounding_pass).lower()}"
    )
    print(f"prediction_evidence_pass={str(report.prediction_evidence_pass).lower()}")
    print(f"non_capacity_blockage_pass={str(report.non_capacity_blockage_pass).lower()}")
    print(f"growth_delay_pass={str(report.growth_delay_pass).lower()}")
    print(f"growth_proposal_pass={str(report.growth_proposal_pass).lower()}")
    print(f"frozen_skill_preservation_pass={str(report.frozen_skill_preservation_pass).lower()}")
    print(f"frozen_ndnra_boundary_pass={str(report.frozen_ndnra_boundary_pass).lower()}")
    print(f"week10_main_milestone_pass={str(report.week10_main_milestone_pass).lower()}")
    print(f"familiar_control_success_rate={report.familiar_control_success_rate:.4f}")
    print(f"specialist_created={str(report.specialist_created).lower()}")
    print(f"router_created={str(report.router_created).lower()}")
    print(f"week11_started={str(report.week11_started).lower()}")
    print(f"ndnra_required={str(report.ndnra_required).lower()}")
    for path in result.artifact_paths:
        print(f"artifact={path}")
    return 0 if report.week10_main_milestone_pass else 1


if __name__ == "__main__":
    raise SystemExit(main())
