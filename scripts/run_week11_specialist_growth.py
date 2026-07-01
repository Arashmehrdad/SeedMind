"""Generate SeedMind Week 11 specialist-growth evidence."""

from seedmind.growth.week11 import DEFAULT_WEEK11_OUTPUT_DIR, run_week11_specialist_growth


def main() -> None:
    result = run_week11_specialist_growth(output_dir=DEFAULT_WEEK11_OUTPUT_DIR)
    report = result.evidence.acceptance_report
    print(f"week11_main_milestone_pass={report['week11_main_milestone_pass']}")


if __name__ == "__main__":
    main()
