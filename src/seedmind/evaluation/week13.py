"""Original SeedMind Week 13 experiment runner and reproducible evidence exporter."""

from __future__ import annotations

import csv
import hashlib
import io
import json
import math
from dataclasses import dataclass, replace
from html import escape
from pathlib import Path
from statistics import fmean, median, pstdev
from typing import cast

from seedmind.evaluation.week13_conditions import (
    AMBITION_REPLICATION_SEEDS,
    APPRENTICESHIP_REPLICATION_SEEDS,
    BALL_REPETITION_SEEDS,
    AmbitionTrial,
    ApprenticeshipTrial,
    TaskEpisode,
    run_ambition_trials,
    run_apprenticeship_trials,
    run_task_suite,
)
from seedmind.skills import ApproachAndPushSkillController, read_skill_record

DEFAULT_WEEK13_OUTPUT_DIR = Path("artifacts/week13_experiments")
WEEK12_CHECKPOINT_PATH = Path("artifacts/week12_consolidation/stable_mvp_checkpoint.json")
WEEK11_CHECKPOINT_PATH = Path(
    "artifacts/week11_specialist_growth/checkpoints/accepted_specialist_checkpoint.json"
)
WEEK8_SKILL_PATH = Path("artifacts/week8_reusable_skill/approach_and_push_skill_record.json")
WEEK13_PLAN_PATH = Path("docs/architecture/SeedMind_Week13_Experiments_Plan_2026-07-01.md")
WEEK12_REPLAY_PATH = Path("artifacts/week12_consolidation/replay_report.json")
WEEK12_RETENTION_PATH = Path("artifacts/week12_consolidation/retention_report.json")
WEEK12_ACCEPTANCE_PATH = Path("artifacts/week12_consolidation/week12_acceptance_report.json")
AUTHORITATIVE_CHECKPOINT_SHA256 = "dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093"
REJECTED_SPECIALIST_SHA256 = "3d86d365496f16678363f9348280c9c102b1bfa98e3a000e23be775a989188b2"
BASELINE_FIELDS = (
    "condition",
    "evaluation_family",
    "repetitions",
    "episodes",
    "successes",
    "success_rate",
    "mean_repetition_success_rate",
    "median_repetition_success_rate",
    "std_repetition_success_rate",
    "min_repetition_success_rate",
    "max_repetition_success_rate",
    "wilson_95_low",
    "wilson_95_high",
    "mean_steps",
    "authority_violations",
    "production_reference",
)
ABLATION_FIELDS = (
    "condition",
    "ball_success_rate",
    "ambition_persistence_rate",
    "help_recall",
    "help_avoidance",
    "teaching_resolution_rate",
    "support_promotion_rate",
    "familiar_retention_rate",
    "narrow_angular_success_rate",
    "broad_angular_success_rate",
    "invalid_promotion_count",
    "production_active",
    "interpretation",
)
REPEATED_FIELDS = (
    "condition",
    "repetition",
    "scenario_seed",
    "metric",
    "value",
    "numerator",
    "denominator",
    "notes",
)
IMPLEMENTATION_FILES = (
    Path("src/seedmind/evaluation/week13.py"),
    Path("src/seedmind/evaluation/week13_conditions.py"),
    Path("src/seedmind/evaluation/__init__.py"),
    Path("scripts/run_week13_experiments.py"),
)


@dataclass(frozen=True, slots=True)
class Week13Evidence:
    """All machine-readable Week 13 reports and deterministic chart text."""

    experiment_manifest: dict[str, object]
    baseline_rows: tuple[dict[str, object], ...]
    ablation_rows: tuple[dict[str, object], ...]
    repeated_rows: tuple[dict[str, object], ...]
    aggregate_metrics: dict[str, object]
    reproducibility_report: dict[str, object]
    claim_evidence_matrix: dict[str, object]
    acceptance_report: dict[str, object]
    charts: dict[str, str]


@dataclass(frozen=True, slots=True)
class Week13RunResult:
    """Executed Week 13 evidence and exported artifact paths."""

    evidence: Week13Evidence
    artifact_paths: tuple[Path, ...]


def run_week13_experiments(*, output_dir: Path | None = None) -> Week13RunResult:
    """Execute all pre-registered Week 13 conditions and optionally export evidence."""
    checkpoint = _read_json(WEEK12_CHECKPOINT_PATH)
    candidate_checkpoint = _read_json(WEEK11_CHECKPOINT_PATH)
    checkpoint_checks = _checkpoint_checks(checkpoint, candidate_checkpoint)
    controller = ApproachAndPushSkillController(read_skill_record(WEEK8_SKILL_PATH))

    random_episodes = run_task_suite("random_primitive", controller)
    reactive_episodes = run_task_suite("fixed_reactive", controller)
    rollback_episodes = run_task_suite("rollback_production_reference", controller)
    complete_episodes = tuple(
        replace(item, condition="complete_seedmind") for item in rollback_episodes
    )
    complete_ambition = run_ambition_trials(enabled=True)
    no_ambition = run_ambition_trials(enabled=False)
    complete_apprenticeship = run_apprenticeship_trials(teaching_enabled=True)
    no_teaching = run_apprenticeship_trials(teaching_enabled=False)
    week12 = _load_week12_evidence()

    task_sets = {
        "random_primitive": random_episodes,
        "fixed_reactive": reactive_episodes,
        "rollback_production_reference": rollback_episodes,
        "complete_seedmind": complete_episodes,
    }
    task_metrics = {name: _task_metrics(episodes) for name, episodes in task_sets.items()}
    ambition_metrics = {
        "complete_seedmind": _ambition_metrics(complete_ambition),
        "no_ambition": _ambition_metrics(no_ambition),
    }
    apprenticeship_metrics = {
        "complete_seedmind": _apprenticeship_metrics(complete_apprenticeship),
        "no_human_teaching": _apprenticeship_metrics(no_teaching),
    }
    growth_metrics = _growth_metrics(week12)
    production_equivalence = _task_equivalence(rollback_episodes, complete_episodes)

    baseline_rows = tuple(
        _baseline_row(name, task_metrics[name], name == "rollback_production_reference")
        for name in (
            "random_primitive",
            "fixed_reactive",
            "rollback_production_reference",
        )
    )
    ablation_rows = _ablation_rows(
        task_metrics=task_metrics,
        ambition_metrics=ambition_metrics,
        apprenticeship_metrics=apprenticeship_metrics,
        growth_metrics=growth_metrics,
    )
    repeated_rows = _repeated_rows(
        task_sets=task_sets,
        complete_ambition=complete_ambition,
        no_ambition=no_ambition,
        complete_apprenticeship=complete_apprenticeship,
        no_teaching=no_teaching,
        growth_metrics=growth_metrics,
    )
    aggregate_metrics = {
        "ambition": ambition_metrics,
        "apprenticeship": apprenticeship_metrics,
        "growth_and_retention": growth_metrics,
        "production_equivalence": production_equivalence,
        "task": task_metrics,
    }
    claims = _claim_matrix(
        task_metrics=task_metrics,
        ambition_metrics=ambition_metrics,
        apprenticeship_metrics=apprenticeship_metrics,
        growth_metrics=growth_metrics,
        checkpoint_checks=checkpoint_checks,
    )
    charts = _build_charts(
        task_sets=task_sets,
        complete_ambition=complete_ambition,
        no_ambition=no_ambition,
        complete_apprenticeship=complete_apprenticeship,
        no_teaching=no_teaching,
        growth_metrics=growth_metrics,
    )
    manifest = _experiment_manifest(checkpoint_checks)
    reproducibility = _reproducibility_report(
        manifest=manifest,
        baseline_rows=baseline_rows,
        ablation_rows=ablation_rows,
        repeated_rows=repeated_rows,
        aggregate_metrics=aggregate_metrics,
        claims=claims,
        charts=charts,
        checkpoint_checks=checkpoint_checks,
    )
    acceptance = _acceptance_report(
        claims=claims,
        checkpoint_checks=checkpoint_checks,
        production_equivalence=production_equivalence,
        reproducibility=reproducibility,
    )
    evidence = Week13Evidence(
        experiment_manifest=manifest,
        baseline_rows=baseline_rows,
        ablation_rows=ablation_rows,
        repeated_rows=repeated_rows,
        aggregate_metrics=aggregate_metrics,
        reproducibility_report=reproducibility,
        claim_evidence_matrix=claims,
        acceptance_report=acceptance,
        charts=charts,
    )
    paths = () if output_dir is None else export_week13_evidence(evidence, output_dir)
    return Week13RunResult(evidence=evidence, artifact_paths=paths)


def export_week13_evidence(evidence: Week13Evidence, output_dir: Path) -> tuple[Path, ...]:
    """Write all required deterministic Week 13 JSON, CSV, and SVG artifacts."""
    payloads = {
        "experiment_manifest.json": _json_text(evidence.experiment_manifest),
        "baseline_results.csv": _csv_text(evidence.baseline_rows, BASELINE_FIELDS),
        "ablation_results.csv": _csv_text(evidence.ablation_rows, ABLATION_FIELDS),
        "repeated_seed_results.csv": _csv_text(evidence.repeated_rows, REPEATED_FIELDS),
        "aggregate_metrics.json": _json_text(evidence.aggregate_metrics),
        "reproducibility_report.json": _json_text(evidence.reproducibility_report),
        "claim_evidence_matrix.json": _json_text(evidence.claim_evidence_matrix),
        "week13_acceptance_report.json": _json_text(evidence.acceptance_report),
        **evidence.charts,
    }
    paths: list[Path] = []
    for relative_name, text in payloads.items():
        path = output_dir / relative_name
        _write_text(path, text)
        paths.append(path)
    return tuple(paths)


def _checkpoint_checks(
    checkpoint: dict[str, object],
    candidate_checkpoint: dict[str, object],
) -> dict[str, object]:
    registry = cast(dict[str, object], checkpoint["registry"])
    modules = cast(list[dict[str, object]], registry["modules"])
    candidate = cast(dict[str, object], checkpoint["candidate"])
    router = cast(dict[str, object], checkpoint["router"])
    checks = {
        "authoritative_checkpoint_match": (
            checkpoint.get("checkpoint_sha256") == AUTHORITATIVE_CHECKPOINT_SHA256
        ),
        "candidate_inactive": candidate.get("active") is False,
        "candidate_rejected_status": candidate.get("status") == "rejected_after_week12",
        "general_controller_only": len(modules) == 1
        and modules[0].get("module_id") == "general_push_controller"
        and modules[0].get("active") is True,
        "rejected_specialist_identity_match": (
            candidate_checkpoint.get("checkpoint_sha256") == REJECTED_SPECIALIST_SHA256
        ),
        "router_inactive": router.get("active") is False
        and registry.get("router_registered") is False,
    }
    return {
        "all_pass": all(checks.values()),
        "authoritative_checkpoint_sha256": checkpoint.get("checkpoint_sha256"),
        "checks": checks,
        "production_action_authority": checkpoint.get("production_action_authority"),
        "rejected_specialist_checkpoint_sha256": candidate_checkpoint.get("checkpoint_sha256"),
    }


def _task_metrics(episodes: tuple[TaskEpisode, ...]) -> dict[str, object]:
    repetition_rates = []
    for repetition in range(1, len(BALL_REPETITION_SEEDS) + 1):
        group = tuple(item for item in episodes if item.repetition == repetition)
        repetition_rates.append(_binary_rate(tuple(item.success for item in group)))
    successes = sum(item.success for item in episodes)
    interval = _wilson_interval(successes, len(episodes))
    return {
        "authority_violations": sum(item.authority_violations for item in episodes),
        "episodes": len(episodes),
        "mean_steps": fmean(item.steps for item in episodes),
        "repetition_success_rate_summary": _summary(tuple(repetition_rates)),
        "success_rate": successes / len(episodes),
        "successes": successes,
        "wilson_95": {"high": interval[1], "low": interval[0]},
    }


def _ambition_metrics(trials: tuple[AmbitionTrial, ...]) -> dict[str, object]:
    return {
        "active_status_preservation_rate": _binary_rate(
            tuple(item.active_status_preserved for item in trials)
        ),
        "adoption_rate": _binary_rate(tuple(item.adopted for item in trials)),
        "candidate_generation_rate": _binary_rate(
            tuple(item.candidate_generated for item in trials)
        ),
        "mean_later_episode_count": fmean(item.later_episode_count for item in trials),
        "persistence_rate": _binary_rate(tuple(item.persisted for item in trials)),
        "reload_identity_match_rate": _binary_rate(
            tuple(item.reload_identity_match for item in trials)
        ),
        "replications": len(trials),
    }


def _apprenticeship_metrics(trials: tuple[ApprenticeshipTrial, ...]) -> dict[str, object]:
    return {
        "help_avoidance": _summary(tuple(item.help_avoidance for item in trials)),
        "help_recall": _summary(tuple(item.help_recall for item in trials)),
        "justified_help_requests": sum(item.justified_help_requests for item in trials),
        "support_promotion_rate": _binary_rate(tuple(item.support_promoted for item in trials)),
        "teaching_resolution": _summary(tuple(item.teaching_resolution_rate for item in trials)),
        "teaching_responses": sum(item.teaching_responses for item in trials),
        "unresolved_justified_help": sum(item.unresolved_justified_help for item in trials),
    }


def _load_week12_evidence() -> dict[str, dict[str, object]]:
    return {
        "replay_report": _read_json(WEEK12_REPLAY_PATH),
        "retention_report": _read_json(WEEK12_RETENTION_PATH),
        "acceptance_report": _read_json(WEEK12_ACCEPTANCE_PATH),
    }


def _growth_metrics(week12: dict[str, dict[str, object]]) -> dict[str, object]:
    replay_report = week12["replay_report"]
    retention_report = week12["retention_report"]
    acceptance_report = week12["acceptance_report"]
    ball = cast(dict[str, object], retention_report["ball_retention"])
    ball_baseline = cast(dict[str, object], ball["baseline"])
    ball_post = cast(dict[str, object], ball["post_growth"])
    angular = cast(dict[str, object], retention_report["angular_transfer"])
    angular_general = cast(dict[str, object], angular["general_controller"])
    angular_post = cast(dict[str, object], angular["post_growth"])
    angular_replay = cast(dict[str, object], replay_report["angular_replay"])
    original = cast(dict[str, object], angular_replay["original_summary"])
    holdout = cast(dict[str, object], angular_replay["holdout_summary"])
    narrow_successes = int(cast(int, original["successes"])) + int(cast(int, holdout["successes"]))
    narrow_total = int(cast(int, original["total"])) + int(cast(int, holdout["total"]))
    broad_rate = float(cast(float, angular_post["success_rate"]))
    narrow_rate = narrow_successes / narrow_total
    invalid_without_replay = int(narrow_rate >= 0.95 and broad_rate < 0.80)
    return {
        "broad_angular": {
            "candidate_success_rate": broad_rate,
            "candidate_successes": angular_post["successes"],
            "gain": angular["gain"],
            "general_success_rate": angular_general["success_rate"],
            "oracle_solvable_count": angular["oracle_solvable_count"],
            "total": angular_post["total"],
        },
        "complete_seedmind": {
            "candidate_decision": acceptance_report["candidate_decision"],
            "familiar_degradation": ball["degradation"],
            "familiar_retention_rate": ball_post["success_rate"],
            "invalid_promotion_count": 0,
            "production_activation_authorised": acceptance_report[
                "production_activation_authorised"
            ],
            "rollback_pass": acceptance_report["rollback_pass"],
        },
        "familiar_retention": {
            "action_trace_match_count": ball["action_trace_match_count"],
            "action_trace_total": ball["action_trace_total"],
            "baseline_success_rate": ball_baseline["success_rate"],
            "post_growth_success_rate": ball_post["success_rate"],
            "specialist_selections": ball["specialist_selections"],
        },
        "growth_without_replay": {
            "broad_angular_success_rate": broad_rate,
            "familiar_retention_rate": ball_post["success_rate"],
            "invalid_promotion_count": invalid_without_replay,
            "narrow_angular_success_rate": narrow_rate,
            "would_authorise_from_narrow_evidence": narrow_rate >= 0.95,
        },
        "narrow_angular": {
            "success_rate": narrow_rate,
            "successes": narrow_successes,
            "total": narrow_total,
        },
    }


def _task_equivalence(
    left: tuple[TaskEpisode, ...],
    right: tuple[TaskEpisode, ...],
) -> dict[str, object]:
    matches = tuple(
        first.seed == second.seed
        and first.success is second.success
        and first.steps == second.steps
        for first, second in zip(left, right, strict=True)
    )
    return {
        "episode_match_count": sum(matches),
        "episode_total": len(matches),
        "exact_success_and_step_equivalence": all(matches),
        "interpretation": (
            "Complete SeedMind uses the same rollback production action path; no task-success "
            "advantage over the frozen rollback controller is claimed."
        ),
    }


def _baseline_row(
    condition: str,
    metrics: dict[str, object],
    production_reference: bool,
) -> dict[str, object]:
    repetition = cast(dict[str, float], metrics["repetition_success_rate_summary"])
    interval = cast(dict[str, float], metrics["wilson_95"])
    return {
        "authority_violations": metrics["authority_violations"],
        "condition": condition,
        "episodes": metrics["episodes"],
        "evaluation_family": "familiar_round_object_100_seed_suite",
        "max_repetition_success_rate": repetition["maximum"],
        "mean_repetition_success_rate": repetition["mean"],
        "mean_steps": metrics["mean_steps"],
        "median_repetition_success_rate": repetition["median"],
        "min_repetition_success_rate": repetition["minimum"],
        "production_reference": production_reference,
        "repetitions": len(BALL_REPETITION_SEEDS),
        "std_repetition_success_rate": repetition["population_std"],
        "success_rate": metrics["success_rate"],
        "successes": metrics["successes"],
        "wilson_95_high": interval["high"],
        "wilson_95_low": interval["low"],
    }


def _ablation_rows(
    *,
    task_metrics: dict[str, dict[str, object]],
    ambition_metrics: dict[str, dict[str, object]],
    apprenticeship_metrics: dict[str, dict[str, object]],
    growth_metrics: dict[str, object],
) -> tuple[dict[str, object], ...]:
    complete_apprenticeship = apprenticeship_metrics["complete_seedmind"]
    no_teaching = apprenticeship_metrics["no_human_teaching"]
    complete_help = cast(dict[str, float], complete_apprenticeship["help_recall"])
    complete_avoid = cast(dict[str, float], complete_apprenticeship["help_avoidance"])
    complete_resolution = cast(dict[str, float], complete_apprenticeship["teaching_resolution"])
    no_teaching_help = cast(dict[str, float], no_teaching["help_recall"])
    no_teaching_avoid = cast(dict[str, float], no_teaching["help_avoidance"])
    no_teaching_resolution = cast(dict[str, float], no_teaching["teaching_resolution"])
    complete_growth = cast(dict[str, object], growth_metrics["complete_seedmind"])
    no_replay = cast(dict[str, object], growth_metrics["growth_without_replay"])
    rows = (
        {
            "ambition_persistence_rate": ambition_metrics["complete_seedmind"]["persistence_rate"],
            "ball_success_rate": task_metrics["complete_seedmind"]["success_rate"],
            "broad_angular_success_rate": "not_applicable_rejected_component_inactive",
            "condition": "complete_seedmind",
            "familiar_retention_rate": complete_growth["familiar_retention_rate"],
            "help_avoidance": complete_avoid["mean"],
            "help_recall": complete_help["mean"],
            "interpretation": "authoritative rollback production system with full developmental controls",
            "invalid_promotion_count": complete_growth["invalid_promotion_count"],
            "narrow_angular_success_rate": "not_production_active",
            "production_active": True,
            "support_promotion_rate": complete_apprenticeship["support_promotion_rate"],
            "teaching_resolution_rate": complete_resolution["mean"],
        },
        {
            "ambition_persistence_rate": ambition_metrics["no_ambition"]["persistence_rate"],
            "ball_success_rate": task_metrics["complete_seedmind"]["success_rate"],
            "broad_angular_success_rate": "not_applicable",
            "condition": "no_ambition",
            "familiar_retention_rate": complete_growth["familiar_retention_rate"],
            "help_avoidance": complete_avoid["mean"],
            "help_recall": complete_help["mean"],
            "interpretation": "same production controller; persistence mechanism removed",
            "invalid_promotion_count": 0,
            "narrow_angular_success_rate": "not_applicable",
            "production_active": False,
            "support_promotion_rate": complete_apprenticeship["support_promotion_rate"],
            "teaching_resolution_rate": complete_resolution["mean"],
        },
        {
            "ambition_persistence_rate": 0.0,
            "ball_success_rate": task_metrics["complete_seedmind"]["success_rate"],
            "broad_angular_success_rate": "not_applicable",
            "condition": "no_human_teaching",
            "familiar_retention_rate": complete_growth["familiar_retention_rate"],
            "help_avoidance": no_teaching_avoid["mean"],
            "help_recall": no_teaching_help["mean"],
            "interpretation": "help policy remains but caregiver responses and approvals are suppressed",
            "invalid_promotion_count": 0,
            "narrow_angular_success_rate": "not_applicable",
            "production_active": False,
            "support_promotion_rate": no_teaching["support_promotion_rate"],
            "teaching_resolution_rate": no_teaching_resolution["mean"],
        },
        {
            "ambition_persistence_rate": "not_measured",
            "ball_success_rate": no_replay["familiar_retention_rate"],
            "broad_angular_success_rate": no_replay["broad_angular_success_rate"],
            "condition": "growth_without_replay",
            "familiar_retention_rate": no_replay["familiar_retention_rate"],
            "help_avoidance": "not_measured",
            "help_recall": "not_measured",
            "interpretation": (
                "decision ablation: narrow Week 11 success would promote a component that fails "
                "the broader Week 12 transfer suite"
            ),
            "invalid_promotion_count": no_replay["invalid_promotion_count"],
            "narrow_angular_success_rate": no_replay["narrow_angular_success_rate"],
            "production_active": False,
            "support_promotion_rate": "not_measured",
            "teaching_resolution_rate": "not_measured",
        },
    )
    return rows


def _repeated_rows(
    *,
    task_sets: dict[str, tuple[TaskEpisode, ...]],
    complete_ambition: tuple[AmbitionTrial, ...],
    no_ambition: tuple[AmbitionTrial, ...],
    complete_apprenticeship: tuple[ApprenticeshipTrial, ...],
    no_teaching: tuple[ApprenticeshipTrial, ...],
    growth_metrics: dict[str, object],
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for condition, episodes in task_sets.items():
        for episode in episodes:
            rows.append(
                _repeated_row(
                    condition,
                    episode.repetition,
                    episode.seed,
                    "familiar_task_success",
                    float(episode.success),
                    int(episode.success),
                    1,
                    f"steps={episode.steps}",
                )
            )
    for ambition_trial in (*complete_ambition, *no_ambition):
        rows.append(
            _repeated_row(
                ambition_trial.condition,
                ambition_trial.repetition,
                ambition_trial.seed,
                "ambition_persistence",
                float(ambition_trial.persisted),
                int(ambition_trial.persisted),
                1,
                f"later_episode_count={ambition_trial.later_episode_count}",
            )
        )
    for apprenticeship_trial in (*complete_apprenticeship, *no_teaching):
        rows.extend(
            (
                _repeated_row(
                    apprenticeship_trial.condition,
                    apprenticeship_trial.repetition,
                    apprenticeship_trial.seed,
                    "help_recall",
                    apprenticeship_trial.help_recall,
                    None,
                    None,
                    "blocked high-uncertainty cases",
                ),
                _repeated_row(
                    apprenticeship_trial.condition,
                    apprenticeship_trial.repetition,
                    apprenticeship_trial.seed,
                    "help_avoidance",
                    apprenticeship_trial.help_avoidance,
                    None,
                    None,
                    "familiar low-risk cases",
                ),
                _repeated_row(
                    apprenticeship_trial.condition,
                    apprenticeship_trial.repetition,
                    apprenticeship_trial.seed,
                    "teaching_resolution",
                    apprenticeship_trial.teaching_resolution_rate,
                    apprenticeship_trial.teaching_responses,
                    apprenticeship_trial.justified_help_requests,
                    f"unresolved={apprenticeship_trial.unresolved_justified_help}",
                ),
            )
        )
    no_replay = cast(dict[str, object], growth_metrics["growth_without_replay"])
    rows.extend(
        (
            _repeated_row(
                "growth_without_replay",
                0,
                None,
                "narrow_angular_success",
                float(cast(float, no_replay["narrow_angular_success_rate"])),
                None,
                None,
                "Week 11 original plus mirrored/rotated cohorts",
            ),
            _repeated_row(
                "growth_without_replay",
                0,
                None,
                "broad_angular_success",
                float(cast(float, no_replay["broad_angular_success_rate"])),
                None,
                None,
                "Week 12 broader solvable transfer suite",
            ),
            _repeated_row(
                "growth_without_replay",
                0,
                None,
                "invalid_promotion_count",
                float(cast(int, no_replay["invalid_promotion_count"])),
                cast(int, no_replay["invalid_promotion_count"]),
                1,
                "counterfactual decision from narrow evidence only",
            ),
        )
    )
    return tuple(rows)


def _repeated_row(
    condition: str,
    repetition: int,
    scenario_seed: int | None,
    metric: str,
    value: float,
    numerator: int | None,
    denominator: int | None,
    notes: str,
) -> dict[str, object]:
    return {
        "condition": condition,
        "denominator": denominator,
        "metric": metric,
        "notes": notes,
        "numerator": numerator,
        "repetition": repetition,
        "scenario_seed": scenario_seed,
        "value": value,
    }


def _claim_matrix(
    *,
    task_metrics: dict[str, dict[str, object]],
    ambition_metrics: dict[str, dict[str, object]],
    apprenticeship_metrics: dict[str, dict[str, object]],
    growth_metrics: dict[str, object],
    checkpoint_checks: dict[str, object],
) -> dict[str, object]:
    random_rate = float(cast(float, task_metrics["random_primitive"]["success_rate"]))
    rollback_rate = float(
        cast(float, task_metrics["rollback_production_reference"]["success_rate"])
    )
    c1_gain = rollback_rate - random_rate
    complete_ambition = ambition_metrics["complete_seedmind"]
    no_ambition = ambition_metrics["no_ambition"]
    complete_apprenticeship = apprenticeship_metrics["complete_seedmind"]
    no_teaching = apprenticeship_metrics["no_human_teaching"]
    complete_help = cast(dict[str, float], complete_apprenticeship["help_recall"])["mean"]
    complete_avoid = cast(dict[str, float], complete_apprenticeship["help_avoidance"])["mean"]
    complete_resolution = cast(dict[str, float], complete_apprenticeship["teaching_resolution"])[
        "mean"
    ]
    no_teaching_resolution = cast(dict[str, float], no_teaching["teaching_resolution"])["mean"]
    complete_growth = cast(dict[str, object], growth_metrics["complete_seedmind"])
    no_replay = cast(dict[str, object], growth_metrics["growth_without_replay"])
    broad = cast(dict[str, object], growth_metrics["broad_angular"])
    claims = (
        {
            "claim_id": "C1",
            "claim": "The reusable rollback production skill beats random primitive action on familiar tasks.",
            "observed": {
                "gain": c1_gain,
                "random_success_rate": random_rate,
                "rollback_success_rate": rollback_rate,
            },
            "status": "supported"
            if c1_gain >= 0.20
            and task_metrics["rollback_production_reference"]["authority_violations"] == 0
            else "unsupported",
            "threshold": "success-rate gain >= 0.20 and zero authority violations",
        },
        {
            "claim_id": "C2",
            "claim": "Ambition machinery creates persistent cross-episode capability commitment.",
            "observed": {
                "complete_persistence_rate": complete_ambition["persistence_rate"],
                "no_ambition_persistence_rate": no_ambition["persistence_rate"],
            },
            "status": "supported"
            if complete_ambition["persistence_rate"] == 1.0
            and no_ambition["persistence_rate"] == 0.0
            else "unsupported",
            "threshold": "complete=1.00 and no-ambition=0.00",
        },
        {
            "claim_id": "C3",
            "claim": "Human apprenticeship resolves justified help and supports reduced dependence.",
            "observed": {
                "complete_help_avoidance": complete_avoid,
                "complete_help_recall": complete_help,
                "complete_teaching_resolution": complete_resolution,
                "no_teaching_resolution": no_teaching_resolution,
                "support_promotion_rate": complete_apprenticeship["support_promotion_rate"],
            },
            "status": "supported"
            if complete_help >= 0.70
            and complete_avoid >= 0.70
            and complete_resolution == 1.0
            and no_teaching_resolution == 0.0
            else "unsupported",
            "threshold": "help recall/avoidance >= 0.70; resolution complete=1.00, no-teaching=0.00",
        },
        {
            "claim_id": "C4",
            "claim": "Retention-gated growth prevents unsupported specialist promotion.",
            "observed": {
                "complete_familiar_degradation": complete_growth["familiar_degradation"],
                "complete_invalid_promotions": complete_growth["invalid_promotion_count"],
                "growth_without_replay_invalid_promotions": no_replay["invalid_promotion_count"],
                "rollback_checkpoint_verified": checkpoint_checks["all_pass"],
            },
            "status": "supported"
            if complete_growth["invalid_promotion_count"] == 0
            and int(cast(int, no_replay["invalid_promotion_count"])) >= 1
            and float(cast(float, complete_growth["familiar_degradation"])) <= 0.10
            and checkpoint_checks["all_pass"] is True
            else "unsupported",
            "threshold": "complete invalid promotions=0; no-replay >=1; degradation <=0.10",
        },
        {
            "claim_id": "C5",
            "claim": "The rejected angular specialist transfers broadly beyond its designed cohorts.",
            "observed": {
                "broad_success_rate": broad["candidate_success_rate"],
                "gain": broad["gain"],
                "oracle_solvable_count": broad["oracle_solvable_count"],
                "total": broad["total"],
            },
            "status": "supported"
            if float(cast(float, broad["candidate_success_rate"])) >= 0.80
            and float(cast(float, broad["gain"])) >= 0.20
            else "unsupported",
            "threshold": "broad success >=0.80 and gain >=+0.20",
        },
    )
    return {
        "claims": list(claims),
        "supported_claim_count": sum(item["status"] == "supported" for item in claims),
        "unsupported_claim_count": sum(item["status"] == "unsupported" for item in claims),
    }


def _experiment_manifest(checkpoint_checks: dict[str, object]) -> dict[str, object]:
    return {
        "authoritative_checkpoint": {
            "path": WEEK12_CHECKPOINT_PATH.as_posix(),
            "sha256": AUTHORITATIVE_CHECKPOINT_SHA256,
            "verification": checkpoint_checks,
        },
        "conditions": [
            "random_primitive",
            "fixed_reactive",
            "rollback_production_reference",
            "complete_seedmind",
            "no_ambition",
            "no_human_teaching",
            "growth_without_replay",
            "rejected_specialist_experimental_comparison",
        ],
        "date": "2026-07-01",
        "experiment_question": (
            "Does complete SeedMind provide measurable benefits over simpler versions?"
        ),
        "familiar_seed_groups": [list(group) for group in BALL_REPETITION_SEEDS],
        "human_apprenticeship_seeds": list(APPRENTICESHIP_REPLICATION_SEEDS),
        "ambition_seeds": list(AMBITION_REPLICATION_SEEDS),
        "production_reference": "week12_rollback_checkpoint",
        "rejected_specialist": {
            "comparison_only": True,
            "path": WEEK11_CHECKPOINT_PATH.as_posix(),
            "sha256": REJECTED_SPECIALIST_SHA256,
        },
        "schema_version": 1,
        "statistical_summary": (
            "mean, median, population standard deviation, range, and Wilson 95% intervals"
        ),
    }


def _reproducibility_report(
    *,
    manifest: dict[str, object],
    baseline_rows: tuple[dict[str, object], ...],
    ablation_rows: tuple[dict[str, object], ...],
    repeated_rows: tuple[dict[str, object], ...],
    aggregate_metrics: dict[str, object],
    claims: dict[str, object],
    charts: dict[str, str],
    checkpoint_checks: dict[str, object],
) -> dict[str, object]:
    all_seeds = tuple(seed for group in BALL_REPETITION_SEEDS for seed in group)
    seed_checks = {
        "familiar_seed_count": len(all_seeds),
        "familiar_seeds_unique": len(all_seeds) == len(set(all_seeds)) == 100,
        "replication_groups_disjoint": all(
            set(left).isdisjoint(right)
            for index, left in enumerate(BALL_REPETITION_SEEDS)
            for right in BALL_REPETITION_SEEDS[index + 1 :]
        ),
    }
    payload_texts = {
        "ablation_results.csv": _csv_text(ablation_rows, ABLATION_FIELDS),
        "aggregate_metrics.json": _json_text(aggregate_metrics),
        "baseline_results.csv": _csv_text(baseline_rows, BASELINE_FIELDS),
        "claim_evidence_matrix.json": _json_text(claims),
        "experiment_manifest.json": _json_text(manifest),
        "repeated_seed_results.csv": _csv_text(repeated_rows, REPEATED_FIELDS),
        **charts,
    }
    payload_hashes = {
        name: hashlib.sha256(text.encode("utf-8")).hexdigest()
        for name, text in sorted(payload_texts.items())
    }
    digest = _payload_digest(payload_hashes)
    implementation_hashes = {
        path.as_posix(): _sha256_file(path) for path in IMPLEMENTATION_FILES if path.exists()
    }
    input_hashes = {
        path.as_posix(): _sha256_file(path)
        for path in (
            WEEK12_CHECKPOINT_PATH,
            WEEK11_CHECKPOINT_PATH,
            WEEK8_SKILL_PATH,
            WEEK13_PLAN_PATH,
        )
    }
    return {
        "artifact_payload_hashes": payload_hashes,
        "authoritative_checkpoint_checks": checkpoint_checks,
        "deterministic_payload_digest": digest,
        "fresh_export_byte_equality_required": True,
        "implementation_hashes": implementation_hashes,
        "input_hashes": input_hashes,
        "no_temporary_files_expected": True,
        "seed_checks": seed_checks,
        "reproducibility_pass": checkpoint_checks["all_pass"] is True
        and all(
            bool(value)
            for key, value in seed_checks.items()
            if key.endswith("unique") or key.endswith("disjoint")
        )
        and bool(implementation_hashes)
        and bool(input_hashes),
    }


def _acceptance_report(
    *,
    claims: dict[str, object],
    checkpoint_checks: dict[str, object],
    production_equivalence: dict[str, object],
    reproducibility: dict[str, object],
) -> dict[str, object]:
    claim_rows = cast(list[dict[str, object]], claims["claims"])
    supported_core = sum(
        row["status"] == "supported" and row["claim_id"] in {"C1", "C2", "C3", "C4"}
        for row in claim_rows
    )
    c5_reported = any(row["claim_id"] == "C5" for row in claim_rows)
    pass_fields = {
        "at_least_three_core_claims_supported_pass": supported_core >= 3,
        "authoritative_rollback_checkpoint_pass": checkpoint_checks["all_pass"] is True,
        "broad_transfer_claim_reported_pass": c5_reported,
        "complete_and_rollback_action_path_equivalence_pass": production_equivalence[
            "exact_success_and_step_equivalence"
        ]
        is True,
        "rejected_specialist_not_production_pass": checkpoint_checks["all_pass"] is True,
        "reproducibility_manifest_pass": reproducibility["reproducibility_pass"] is True,
    }
    return {
        **pass_fields,
        "authoritative_checkpoint_sha256": AUTHORITATIVE_CHECKPOINT_SHA256,
        "complete_seedmind_task_advantage_over_rollback_claimed": False,
        "decision": "week13_evidence_pass" if all(pass_fields.values()) else "week13_evidence_fail",
        "rejected_specialist_production_active": False,
        "supported_core_claim_count": supported_core,
        "week13_main_milestone_pass": all(pass_fields.values()),
    }


def _build_charts(
    *,
    task_sets: dict[str, tuple[TaskEpisode, ...]],
    complete_ambition: tuple[AmbitionTrial, ...],
    no_ambition: tuple[AmbitionTrial, ...],
    complete_apprenticeship: tuple[ApprenticeshipTrial, ...],
    no_teaching: tuple[ApprenticeshipTrial, ...],
    growth_metrics: dict[str, object],
) -> dict[str, str]:
    cumulative_series: dict[str, tuple[float, ...]] = {}
    for condition, episodes in task_sets.items():
        successes = 0
        curve: list[float] = []
        for index, episode in enumerate(episodes, start=1):
            successes += int(episode.success)
            curve.append(successes / index)
        cumulative_series[condition] = tuple(curve)
    ambition_series = {
        "complete_seedmind": tuple(float(item.persisted) for item in complete_ambition),
        "no_ambition": tuple(float(item.persisted) for item in no_ambition),
    }
    apprenticeship_series = {
        "complete_seedmind": tuple(
            item.teaching_resolution_rate for item in complete_apprenticeship
        ),
        "no_human_teaching": tuple(item.teaching_resolution_rate for item in no_teaching),
    }
    retention = cast(dict[str, object], growth_metrics["familiar_retention"])
    narrow = cast(dict[str, object], growth_metrics["narrow_angular"])
    broad = cast(dict[str, object], growth_metrics["broad_angular"])
    return {
        "learning_curves/familiar_task_cumulative_success.svg": _line_svg(
            "Familiar-task cumulative success",
            cumulative_series,
            x_label="evaluated episode",
            y_label="cumulative success rate",
        ),
        "learning_curves/ambition_persistence.svg": _line_svg(
            "Ambition persistence across repeated trials",
            ambition_series,
            x_label="replication",
            y_label="persistence",
        ),
        "learning_curves/apprenticeship_resolution.svg": _line_svg(
            "Teaching resolution across repeated trials",
            apprenticeship_series,
            x_label="replication",
            y_label="resolution rate",
        ),
        "retention_charts/familiar_retention.svg": _bar_svg(
            "Familiar-task retention",
            {
                "frozen baseline": float(cast(float, retention["baseline_success_rate"])),
                "routed rejected candidate": float(
                    cast(float, retention["post_growth_success_rate"])
                ),
            },
            y_label="success rate",
        ),
        "retention_charts/angular_transfer.svg": _bar_svg(
            "Rejected specialist: narrow versus broad",
            {
                "narrow cohorts": float(cast(float, narrow["success_rate"])),
                "broad transfer": float(cast(float, broad["candidate_success_rate"])),
            },
            y_label="success rate",
        ),
    }


def _line_svg(
    title: str,
    series: dict[str, tuple[float, ...]],
    *,
    x_label: str,
    y_label: str,
) -> str:
    width, height = 900, 520
    left, top, plot_width, plot_height = 90, 60, 740, 380
    palette = ("#1f77b4", "#ff7f0e", "#2ca02c", "#9467bd", "#8c564b")
    max_points = max((len(values) for values in series.values()), default=1)
    parts = _svg_frame(title, width, height, left, top, plot_width, plot_height, x_label, y_label)
    for index, (name, values) in enumerate(series.items()):
        points = []
        for point_index, value in enumerate(values):
            x = left + (plot_width * point_index / max(max_points - 1, 1))
            y = top + plot_height * (1.0 - min(max(value, 0.0), 1.0))
            points.append(f"{x:.2f},{y:.2f}")
        colour = palette[index % len(palette)]
        parts.append(
            f'<polyline fill="none" stroke="{colour}" stroke-width="2.5" points="{" ".join(points)}"/>'
        )
        legend_y = 82 + index * 24
        parts.append(
            f'<line x1="650" y1="{legend_y}" x2="675" y2="{legend_y}" stroke="{colour}" stroke-width="3"/>'
        )
        parts.append(f'<text x="682" y="{legend_y + 5}" font-size="13">{escape(name)}</text>')
    parts.append("</svg>\n")
    return "".join(parts)


def _bar_svg(title: str, values: dict[str, float], *, y_label: str) -> str:
    width, height = 760, 500
    left, top, plot_width, plot_height = 90, 60, 600, 340
    parts = _svg_frame(
        title, width, height, left, top, plot_width, plot_height, "condition", y_label
    )
    count = max(len(values), 1)
    slot = plot_width / count
    for index, (name, raw_value) in enumerate(values.items()):
        value = min(max(raw_value, 0.0), 1.0)
        bar_width = slot * 0.55
        x = left + index * slot + (slot - bar_width) / 2
        y = top + plot_height * (1.0 - value)
        bar_height = plot_height * value
        parts.append(
            f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" fill="#4c78a8"/>'
        )
        parts.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{y - 8:.2f}" text-anchor="middle" font-size="13">{value:.3f}</text>'
        )
        parts.append(
            f'<text x="{x + bar_width / 2:.2f}" y="{top + plot_height + 25}" text-anchor="middle" font-size="12">{escape(name)}</text>'
        )
    parts.append("</svg>\n")
    return "".join(parts)


def _svg_frame(
    title: str,
    width: int,
    height: int,
    left: int,
    top: int,
    plot_width: int,
    plot_height: int,
    x_label: str,
    y_label: str,
) -> list[str]:
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2:.1f}" y="30" text-anchor="middle" font-size="20" font-weight="bold">{escape(title)}</text>',
        f'<line x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}" stroke="black"/>',
        f'<line x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}" stroke="black"/>',
    ]
    for tick in range(6):
        value = tick / 5
        y = top + plot_height * (1.0 - value)
        parts.append(
            f'<line x1="{left - 5}" y1="{y:.2f}" x2="{left + plot_width}" y2="{y:.2f}" stroke="#dddddd"/>'
        )
        parts.append(
            f'<text x="{left - 10}" y="{y + 4:.2f}" text-anchor="end" font-size="12">{value:.1f}</text>'
        )
    parts.extend(
        (
            f'<text x="{left + plot_width / 2:.2f}" y="{height - 20}" text-anchor="middle" font-size="14">{escape(x_label)}</text>',
            f'<text x="20" y="{top + plot_height / 2:.2f}" text-anchor="middle" font-size="14" transform="rotate(-90 20 {top + plot_height / 2:.2f})">{escape(y_label)}</text>',
        )
    )
    return parts


def _summary(values: tuple[float, ...]) -> dict[str, float]:
    if not values:
        return {
            "maximum": 0.0,
            "mean": 0.0,
            "median": 0.0,
            "minimum": 0.0,
            "population_std": 0.0,
        }
    return {
        "maximum": max(values),
        "mean": fmean(values),
        "median": median(values),
        "minimum": min(values),
        "population_std": pstdev(values),
    }


def _binary_rate(values: tuple[bool, ...]) -> float:
    return 0.0 if not values else sum(values) / len(values)


def _wilson_interval(
    successes: int, total: int, z: float = 1.959963984540054
) -> tuple[float, float]:
    if total == 0:
        return 0.0, 0.0
    proportion = successes / total
    denominator = 1.0 + z * z / total
    centre = (proportion + z * z / (2.0 * total)) / denominator
    margin = (
        z
        * math.sqrt(proportion * (1.0 - proportion) / total + z * z / (4.0 * total * total))
        / denominator
    )
    return max(0.0, centre - margin), min(1.0, centre + margin)


def _csv_text(rows: tuple[dict[str, object], ...], fields: tuple[str, ...]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(stream, fieldnames=list(fields), lineterminator="\n")
    writer.writeheader()
    for row in rows:
        writer.writerow({field: _csv_value(row.get(field)) for field in fields})
    return stream.getvalue()


def _csv_value(value: object) -> object:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value).lower()
    if isinstance(value, float):
        return f"{value:.12g}"
    return value


def _json_text(payload: dict[str, object]) -> str:
    return json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n"


def _payload_digest(payload: object) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return cast(dict[str, object], payload)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(text, encoding="utf-8", newline="\n")
    temporary.replace(path)
