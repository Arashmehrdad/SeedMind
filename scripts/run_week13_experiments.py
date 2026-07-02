"""Generate SeedMind Week 13 baseline, ablation, and evidence artifacts."""

from seedmind.evaluation import DEFAULT_WEEK13_OUTPUT_DIR, run_week13_experiments


def main() -> None:
    result = run_week13_experiments(output_dir=DEFAULT_WEEK13_OUTPUT_DIR)
    report = result.evidence.acceptance_report
    print(f"week13_main_milestone_pass={report['week13_main_milestone_pass']}")
    print(f"decision={report['decision']}")
    print(f"supported_core_claim_count={report['supported_core_claim_count']}")
    print(f"authoritative_checkpoint_sha256={report['authoritative_checkpoint_sha256']}")


if __name__ == "__main__":
    main()
