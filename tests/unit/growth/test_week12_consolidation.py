"""Acceptance coverage for original SeedMind Week 12 consolidation."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import cast

from seedmind.growth.week12 import run_week12_consolidation
from seedmind.growth.week12_gate import Week12Evidence
from seedmind.growth.week12_scenarios import (
    ANGULAR_TRANSFER_VARIANTS,
    BALL_RETENTION_SEEDS,
    NAVIGATION_CASES,
)

REPOSITORY_ARTIFACTS = Path("artifacts/week12_consolidation")


@lru_cache(maxsize=1)
def _evidence() -> Week12Evidence:
    return run_week12_consolidation().evidence


def test_week12_rejects_candidate_when_solvable_transfer_gate_fails() -> None:
    evidence = _evidence()
    acceptance = evidence.acceptance_report
    pass_fields = {
        name: value
        for name, value in acceptance.items()
        if name.endswith("_pass") and name != "week12_main_milestone_pass"
    }
    assert pass_fields
    assert [name for name, value in pass_fields.items() if value is not True] == [
        "angular_transfer_pass"
    ]
    assert acceptance["week12_main_milestone_pass"] is False
    assert acceptance["candidate_decision"] == "reject_and_rollback"
    assert acceptance["production_activation_authorised"] is False
    assert acceptance["production_action_authority"] == "production_curiosity"

    ball = cast(dict[str, object], evidence.retention_report["ball_retention"])
    ball_baseline = cast(dict[str, object], ball["baseline"])
    ball_post = cast(dict[str, object], ball["post_growth"])
    assert ball["pass"] is True
    assert ball_baseline["success_rate"] == 0.375
    assert ball_post["success_rate"] == 0.375
    assert ball["stress_target_met"] is False
    assert ball["action_trace_match_count"] == ball["action_trace_total"] == 40
    assert ball["specialist_selections"] == 0

    angular = cast(dict[str, object], evidence.retention_report["angular_transfer"])
    angular_general = cast(dict[str, object], angular["general_controller"])
    angular_post = cast(dict[str, object], angular["post_growth"])
    assert angular["oracle_solvable_count"] == angular["oracle_total"] == 32
    assert angular_general["success_rate"] == 0.0
    assert angular_post["success_rate"] == 0.0
    assert angular["gain"] == 0.0
    assert angular["pass"] is False

    candidate = cast(dict[str, object], evidence.stable_checkpoint["candidate"])
    router = cast(dict[str, object], evidence.stable_checkpoint["router"])
    assert candidate["active"] is False
    assert candidate["production_scope"] is None
    assert router["active"] is False
    assert router["proposal_authority"] == "proposal_only"


def test_week12_reports_named_scenarios_baselines_and_thresholds() -> None:
    evidence = _evidence()
    retention = evidence.retention_report
    ball = cast(dict[str, object], retention["ball_retention"])
    angular = cast(dict[str, object], retention["angular_transfer"])
    navigation_cases = cast(list[dict[str, object]], evidence.navigation_report["cases"])

    assert len(cast(list[int], ball["seeds"])) == len(BALL_RETENTION_SEEDS)
    assert ball["action_trace_match_count"] == ball["action_trace_total"]
    assert ball["specialist_selections"] == 0
    assert "baseline" in ball
    assert "degradation_limit" in ball
    assert "description" in ball

    episodes = cast(list[dict[str, object]], angular["episodes"])
    variant_ids = {
        cast(dict[str, object], episode["variant"])["variant_id"] for episode in episodes
    }
    assert variant_ids == {variant.variant_id for variant in ANGULAR_TRANSFER_VARIANTS}
    assert "gain_target" in angular
    assert "post_growth_success_floor" in angular
    assert "description" in angular

    assert len(navigation_cases) == len(NAVIGATION_CASES)
    assert all(
        "case" in row and "baseline" in row and "post_growth" in row for row in navigation_cases
    )
    assert evidence.navigation_report["pass"] is True


def test_week12_preserves_help_correction_shutdown_and_exact_rollback() -> None:
    evidence = _evidence()
    help_report = evidence.help_report
    safety = evidence.character_safety_report

    assert help_report["help_policy_pass"] is True
    assert help_report["correction_pass"] is True
    assert all(
        row["pass"] is True for row in cast(list[dict[str, object]], help_report["help_cases"])
    )
    assert safety["character_gate_pass"] is True
    assert safety["safety_gate_pass"] is True
    assert safety["self_report_used_for_success"] is False
    assert cast(dict[str, object], safety["shutdown_compliance"])["pass"] is True
    assert evidence.rollback_checkpoint["restoration_proof"] is True
    assert evidence.rollback_checkpoint["used_as_final_checkpoint"] is True


def test_committed_week12_artifacts_match_a_fresh_deterministic_export(
    tmp_path: Path,
) -> None:
    result = run_week12_consolidation(output_dir=tmp_path)
    generated = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes() for path in result.artifact_paths
    }
    committed = {
        path.relative_to(REPOSITORY_ARTIFACTS).as_posix(): path.read_bytes()
        for path in REPOSITORY_ARTIFACTS.rglob("*")
        if path.is_file()
    }
    assert committed == generated
