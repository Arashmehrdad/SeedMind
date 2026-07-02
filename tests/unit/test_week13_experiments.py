"""Acceptance coverage for original SeedMind Week 13 experiments."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import cast

from seedmind.evaluation import run_week13_experiments
from seedmind.evaluation.week13 import Week13Evidence

REPOSITORY_ARTIFACTS = Path("artifacts/week13_experiments")
AUTHORITATIVE_CHECKPOINT = "dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093"


@lru_cache(maxsize=1)
def _evidence() -> Week13Evidence:
    return run_week13_experiments().evidence


def test_week13_uses_rollback_checkpoint_and_keeps_specialist_rejected() -> None:
    evidence = _evidence()
    acceptance = evidence.acceptance_report
    manifest_checkpoint = cast(
        dict[str, object], evidence.experiment_manifest["authoritative_checkpoint"]
    )
    verification = cast(dict[str, object], manifest_checkpoint["verification"])

    assert acceptance["authoritative_checkpoint_sha256"] == AUTHORITATIVE_CHECKPOINT
    assert acceptance["rejected_specialist_production_active"] is False
    assert acceptance["complete_seedmind_task_advantage_over_rollback_claimed"] is False
    assert verification["all_pass"] is True
    assert evidence.aggregate_metrics["production_equivalence"] == {
        "episode_match_count": 100,
        "episode_total": 100,
        "exact_success_and_step_equivalence": True,
        "interpretation": (
            "Complete SeedMind uses the same rollback production action path; no task-success "
            "advantage over the frozen rollback controller is claimed."
        ),
    }


def test_week13_supports_bounded_claims_and_rejects_broad_transfer_claim() -> None:
    evidence = _evidence()
    claims = cast(list[dict[str, object]], evidence.claim_evidence_matrix["claims"])
    by_id = {cast(str, claim["claim_id"]): claim for claim in claims}

    assert by_id["C2"]["status"] == "supported"
    assert by_id["C3"]["status"] == "supported"
    assert by_id["C4"]["status"] == "supported"
    assert by_id["C5"]["status"] == "unsupported"
    assert cast(int, evidence.acceptance_report["supported_core_claim_count"]) >= 3
    assert evidence.acceptance_report["week13_main_milestone_pass"] is True
    assert evidence.acceptance_report["decision"] == "week13_evidence_pass"


def test_week13_exports_all_required_machine_readable_evidence(tmp_path: Path) -> None:
    result = run_week13_experiments(output_dir=tmp_path)
    relative_paths = {path.relative_to(tmp_path).as_posix() for path in result.artifact_paths}

    assert {
        "experiment_manifest.json",
        "baseline_results.csv",
        "ablation_results.csv",
        "repeated_seed_results.csv",
        "aggregate_metrics.json",
        "reproducibility_report.json",
        "claim_evidence_matrix.json",
        "week13_acceptance_report.json",
        "learning_curves/familiar_task_cumulative_success.svg",
        "learning_curves/ambition_persistence.svg",
        "learning_curves/apprenticeship_resolution.svg",
        "retention_charts/familiar_retention.svg",
        "retention_charts/angular_transfer.svg",
    } == relative_paths
    assert not tuple(tmp_path.rglob("*.tmp"))


def test_committed_week13_artifacts_match_fresh_deterministic_export(tmp_path: Path) -> None:
    result = run_week13_experiments(output_dir=tmp_path)
    generated = {
        path.relative_to(tmp_path).as_posix(): path.read_bytes() for path in result.artifact_paths
    }
    committed = {
        path.relative_to(REPOSITORY_ARTIFACTS).as_posix(): path.read_bytes()
        for path in REPOSITORY_ARTIFACTS.rglob("*")
        if path.is_file()
    }

    assert committed == generated
