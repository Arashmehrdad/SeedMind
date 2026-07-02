"""Verify Week 14 public claims against committed evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.observatory import write_week14_claim_report


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()

    report = write_week14_claim_report(args.root)
    print(
        f"Week 14 claim verification: {'pass' if report['all_passed'] else 'fail'} "
        f"({report['failure_count']} failing checks)"
    )
    return 0 if report["all_passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
