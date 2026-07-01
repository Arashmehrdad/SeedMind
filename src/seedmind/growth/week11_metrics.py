"""Small deterministic metrics for Week 11 growth evidence."""

from statistics import fmean

from seedmind.growth.week11_rollout import RolloutRecord


def success_rate(records: tuple[RolloutRecord, ...]) -> float:
    return fmean(float(record.success) for record in records)


def rollout_summary(records: tuple[RolloutRecord, ...]) -> dict[str, object]:
    return {
        "episodes": [record.to_json() for record in records],
        "mean_steps": fmean(record.steps for record in records),
        "success_rate": success_rate(records),
        "successes": sum(record.success for record in records),
        "total": len(records),
    }
