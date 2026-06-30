"""Run the SeedMind Week 9 human contribution gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.contribution import run_week9_contribution_evaluation
from seedmind.human import SupportLevel


def parse_args() -> argparse.Namespace:
    """Parse deterministic Week 9 runner settings."""
    parser = argparse.ArgumentParser(
        description="Evaluate Week 9 human contribution against the frozen Week 8 skill.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/week9_contribution"),
    )
    parser.add_argument(
        "--skill-record",
        type=Path,
        default=Path("artifacts/week8_reusable_skill/approach_and_push_skill_record.json"),
    )
    return parser.parse_args()


def main() -> int:
    """Run Week 9, export evidence, and print core acceptance metrics."""
    args = parse_args()
    result = run_week9_contribution_evaluation(
        skill_record_path=args.skill_record,
        output_dir=args.output_dir,
    )
    report = result.acceptance_report
    comparison = result.parallel_comparison.report
    print(f"attempts={report.total_attempts}")
    print(f"successes={report.total_successes}")
    print(f"independent_success_rate={report.independent_success_rate:.4f}")
    print(f"first_success_kept_dependent={str(report.first_success_kept_dependent).lower()}")
    print(
        f"reduced_after_repeated_competence={str(report.reduced_after_repeated_competence).lower()}"
    )
    print(
        f"restored_to_dependent_after_failures={str(report.restored_to_dependent_after_failures).lower()}"
    )
    print(
        f"reduced_again_after_repeated_competence={str(report.reduced_again_after_repeated_competence).lower()}"
    )
    print(f"final_support_level={report.final_support_level}")
    print(f"skill_discovery_delta={report.skill_discovery_delta}")
    print(f"compile_count={report.compile_count}")
    print(f"training_count={report.training_count}")
    print(f"promotion_count={report.promotion_count}")
    print(f"production_curiosity_retained_count={report.production_curiosity_retained_count}")
    print(f"executed_step_count={report.executed_step_count}")
    print(f"authority_violations={report.authority_violations}")
    print(f"verification_authority_violations={report.verification_authority_violations}")
    print(f"support_authority_violations={report.support_authority_violations}")
    print(f"ndnra_automatic_promotions={report.ndnra_automatic_promotions}")
    print(f"comparison_total_steps={comparison.total_production_steps}")
    print(f"ndnra_proposal_count={comparison.ndnra_proposal_count}")
    print(f"ndnra_abstention_count={comparison.ndnra_abstention_count}")
    print(f"agreement_count={comparison.agreement_count}")
    print(f"disagreement_count={comparison.disagreement_count}")
    print(f"comparison_count={comparison.comparison_count}")
    print(f"disagreement_comparison_coverage={comparison.disagreement_comparison_coverage:.4f}")
    print(f"default_better_count={comparison.default_better_count}")
    print(f"ndnra_better_count={comparison.ndnra_better_count}")
    print(f"tied_count={comparison.tied_count}")
    print(f"mean_default_combined_score={comparison.mean_default_combined_score:.6f}")
    print(f"mean_ndnra_combined_score={comparison.mean_ndnra_combined_score:.6f}")
    print(f"mean_ndnra_advantage={comparison.mean_ndnra_advantage:.6f}")
    print(f"default_task_success_rate={comparison.default_task_success_rate:.4f}")
    print(f"ndnra_rollout_success_rate={comparison.ndnra_rollout_success_rate:.4f}")
    print(f"ndnra_rollout_successes={comparison.ndnra_rollout_successes}")
    print(f"learned_assembly_count={comparison.learned_assembly_count}")
    print(f"effect_dimension_count={comparison.effect_dimension_count}")
    print(f"human_contribution_demo={args.output_dir / 'human_contribution_demo.json'}")
    print(f"support_level_report={args.output_dir / 'support_level_report.json'}")
    print(f"contribution_history={args.output_dir / 'contribution_history.json'}")
    print(f"week9_acceptance_report={args.output_dir / 'week9_acceptance_report.json'}")
    print(f"default_vs_ndnra_comparison={args.output_dir / 'default_vs_ndnra_comparison.json'}")
    passed = (
        report.independent_success_rate >= 0.80
        and report.first_success_kept_dependent
        and report.reduced_after_repeated_competence
        and report.restored_to_dependent_after_failures
        and report.reduced_again_after_repeated_competence
        and report.final_support_level == int(SupportLevel.GUIDED_LEARNER)
        and report.skill_discovery_delta == 0
        and report.compile_count == 0
        and report.training_count == 0
        and report.promotion_count == 0
        and report.production_curiosity_retained_count == report.executed_step_count
        and report.authority_violations == 0
        and report.verification_authority_violations == 0
        and report.support_authority_violations == 0
        and report.ndnra_automatic_promotions == 0
        and comparison.pass_gate
        and comparison.default_task_success_rate == report.independent_success_rate
        and comparison.production_action_replacements == 0
        and comparison.authority_violations == 0
        and comparison.automatic_promotions == 0
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
