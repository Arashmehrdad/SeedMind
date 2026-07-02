"""Focused tests for Week 14 claim verification fail-closed behavior."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

import pytest

from seedmind.observatory import verify_week14_claims, write_week14_claim_report

COMMITTED_PATH = Path("artifacts/week14_packaging/claim_verification_report.json")
COPY_PATHS = (
    Path("artifacts/week11_specialist_growth/week11_acceptance_report.json"),
    Path("artifacts/week11_specialist_growth/candidate_specialist_manifest.json"),
    Path("artifacts/week11_specialist_growth/candidate_evaluation.json"),
    Path("artifacts/week12_consolidation/week12_acceptance_report.json"),
    Path("artifacts/week12_consolidation/stable_mvp_checkpoint.json"),
    Path("artifacts/week12_consolidation/retention_report.json"),
    Path("artifacts/week13_experiments/week13_acceptance_report.json"),
    Path("artifacts/week13_experiments/aggregate_metrics.json"),
    Path("artifacts/week13_experiments/claim_evidence_matrix.json"),
    Path("artifacts/week13_experiments/reproducibility_report.json"),
    Path("docs/architecture/SeedMind_Week13_Limitations_2026-07-01.md"),
    Path("artifacts/week8_reusable_skill/week8_generalisation_report.json"),
    Path("artifacts/week9_contribution/week9_acceptance_report.json"),
    Path("pyproject.toml"),
)


def test_claim_verification_passes_on_committed_evidence() -> None:
    report = verify_week14_claims()
    assert report["all_passed"] is True
    assert report["failure_count"] == 0
    assert report["authoritative_checkpoint_sha256"] == (
        "dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093"
    )


def test_claim_verifier_fails_closed_on_contradictory_status(tmp_path: Path) -> None:
    root = _copy_minimal_tree(tmp_path)
    claims_path = root / "artifacts/week13_experiments/claim_evidence_matrix.json"
    payload = json.loads(claims_path.read_text(encoding="utf-8"))
    payload["claims"][-1]["status"] = "supported"
    claims_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n", encoding="ascii"
    )

    report = verify_week14_claims(root)

    assert report["all_passed"] is False
    assert any(
        check["check_id"] == "evidence_payload_hashes" and not check["passed"]
        for check in report["checks"]
    )
    assert any(
        check["check_id"] == "week13_claim_status" and not check["passed"]
        for check in report["checks"]
    )


def test_claim_verifier_fails_closed_on_missing_or_malformed_evidence(tmp_path: Path) -> None:
    root = _copy_minimal_tree(tmp_path)
    (root / "artifacts/week12_consolidation/stable_mvp_checkpoint.json").unlink()
    with pytest.raises(ValueError, match="Missing evidence file"):
        verify_week14_claims(root)

    root = _copy_minimal_tree(tmp_path / "malformed")
    bad = root / "artifacts/week12_consolidation/stable_mvp_checkpoint.json"
    bad.write_text("{bad json\n", encoding="ascii")
    with pytest.raises(ValueError, match="Malformed JSON evidence"):
        verify_week14_claims(root)


def test_committed_claim_report_matches_fresh_export(tmp_path: Path) -> None:
    write_week14_claim_report(tmp_path)
    generated = (
        tmp_path / "artifacts/week14_packaging/claim_verification_report.json"
    ).read_bytes()
    committed = COMMITTED_PATH.read_bytes()
    assert generated == committed
    assert not tuple((tmp_path / "artifacts/week14_packaging").glob("*.tmp"))


def _copy_minimal_tree(destination_root: Path) -> Path:
    destination_root.mkdir(parents=True, exist_ok=True)
    (destination_root / "src").mkdir(parents=True, exist_ok=True)
    for relative in COPY_PATHS:
        target = destination_root / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(relative, target)
    return destination_root
