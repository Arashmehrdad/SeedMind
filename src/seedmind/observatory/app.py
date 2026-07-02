"""Week 14 observatory app, exports, and claim verification."""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from importlib import resources
from pathlib import Path
from typing import Any, cast

from .data_sources import (
    AUTHORITATIVE_ROLLBACK_CHECKPOINT,
    REJECTED_SPECIALIST_CHECKPOINT,
    ObservatoryEvidence,
    canonical_json_sha256,
    dataclass_to_json_dict,
    load_observatory_evidence,
    repository_root,
    write_ascii_json_atomic,
)
from .view_model import (
    DemoManifest,
    ObservatorySnapshot,
    build_snapshot,
)
from .view_model import (
    build_demo_manifest as build_demo_manifest_view_model,
)

STATIC_PACKAGE = "seedmind.observatory"


@dataclass(frozen=True)
class Week14Paths:
    observatory_snapshot: Path
    observatory_snapshot_tmp: Path
    demo_manifest: Path
    demo_manifest_tmp: Path
    claim_report: Path
    claim_report_tmp: Path


@dataclass(frozen=True)
class VerificationCheck:
    check_id: str
    passed: bool
    summary: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class VerificationReport:
    authoritative_checkpoint_sha256: str
    packaging_status: str
    all_passed: bool
    failure_count: int
    checks: tuple[VerificationCheck, ...]
    deterministic_digest: str


def build_observatory_snapshot(root: Path | None = None) -> dict[str, Any]:
    evidence = load_observatory_evidence(root)
    snapshot = build_snapshot(evidence)
    return _snapshot_payload(snapshot, evidence)


def build_demo_manifest(root: Path | None = None) -> dict[str, Any]:
    evidence = load_observatory_evidence(root)
    manifest = build_demo_manifest_view(evidence)
    return _demo_manifest_payload(manifest)


def build_demo_manifest_view(evidence: ObservatoryEvidence) -> DemoManifest:
    return build_demo_manifest_view_model(evidence)


def verify_week14_claims(root: Path | None = None) -> dict[str, Any]:
    evidence = load_observatory_evidence(root)
    report = _verify(evidence)
    payload = _verification_payload(report)
    payload["deterministic_digest"] = canonical_json_sha256(payload)
    return payload


def write_observatory_snapshot(
    root: Path | None = None, paths: Week14Paths | None = None
) -> dict[str, Any]:
    evidence_root, output_root = _resolve_evidence_and_output_roots(root)
    target_paths = paths or week14_paths(output_root)
    payload = build_observatory_snapshot(evidence_root)
    write_ascii_json_atomic(
        target_paths.observatory_snapshot, target_paths.observatory_snapshot_tmp, payload
    )
    return payload


def write_demo_manifest(
    root: Path | None = None, paths: Week14Paths | None = None
) -> dict[str, Any]:
    evidence_root, output_root = _resolve_evidence_and_output_roots(root)
    target_paths = paths or week14_paths(output_root)
    payload = build_demo_manifest(evidence_root)
    write_ascii_json_atomic(target_paths.demo_manifest, target_paths.demo_manifest_tmp, payload)
    return payload


def write_week14_claim_report(
    root: Path | None = None, paths: Week14Paths | None = None
) -> dict[str, Any]:
    evidence_root, output_root = _resolve_evidence_and_output_roots(root)
    target_paths = paths or week14_paths(output_root)
    payload = verify_week14_claims(evidence_root)
    write_ascii_json_atomic(target_paths.claim_report, target_paths.claim_report_tmp, payload)
    return payload


def week14_paths(root: Path | None = None) -> Week14Paths:
    output_root = (root or repository_root()).resolve()
    base = output_root / "artifacts/week14_packaging"
    return Week14Paths(
        observatory_snapshot=base / "observatory_snapshot.json",
        observatory_snapshot_tmp=base / "observatory_snapshot.json.tmp",
        demo_manifest=base / "demo_manifest.json",
        demo_manifest_tmp=base / "demo_manifest.json.tmp",
        claim_report=base / "claim_verification_report.json",
        claim_report_tmp=base / "claim_verification_report.json.tmp",
    )


def _resolve_evidence_and_output_roots(root: Path | None) -> tuple[Path, Path]:
    if root is None:
        repo_root = repository_root()
        return repo_root, repo_root

    output_root = root.resolve()
    if (output_root / "pyproject.toml").is_file() and (output_root / "src").is_dir():
        return output_root, output_root
    return repository_root(), output_root


def create_observatory_server(
    snapshot_payload: dict[str, Any], host: str = "127.0.0.1", port: int = 8000
) -> ThreadingHTTPServer:
    snapshot_bytes = json.dumps(
        snapshot_payload, ensure_ascii=True, indent=2, sort_keys=True
    ).encode("ascii")
    assets = {
        "/": ("text/html; charset=utf-8", _read_static_text("index.html").encode("utf-8")),
        "/index.html": (
            "text/html; charset=utf-8",
            _read_static_text("index.html").encode("utf-8"),
        ),
        "/app.js": (
            "application/javascript; charset=utf-8",
            _read_static_text("app.js").encode("utf-8"),
        ),
        "/styles.css": ("text/css; charset=utf-8", _read_static_text("styles.css").encode("utf-8")),
        "/api/snapshot": ("application/json; charset=ascii", snapshot_bytes),
    }

    class ObservatoryHandler(BaseHTTPRequestHandler):
        def do_GET(self) -> None:
            asset = assets.get(self.path)
            if asset is None:
                self.send_error(HTTPStatus.NOT_FOUND, "Not Found")
                return
            content_type, body = asset
            self.send_response(HTTPStatus.OK)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)

        def log_message(self, format: str, *args: object) -> None:
            return

    return ThreadingHTTPServer((host, port), ObservatoryHandler)


def run_demo(manifest_payload: dict[str, Any], no_wait: bool = False) -> None:
    print(manifest_payload["title"])
    print(f"Declared total duration: {manifest_payload['declared_total_duration_seconds']} seconds")
    for scene in cast(list[dict[str, Any]], manifest_payload["scenes"]):
        print()
        print(f"[{scene['scene_id']}] {scene['title']} ({scene['duration_seconds']}s)")
        print(scene["narration"])
        print("Evidence:", ", ".join(cast(list[str], scene["evidence_refs"])))
        if not no_wait:
            time.sleep(cast(int, scene["duration_seconds"]))


def _snapshot_payload(
    snapshot: ObservatorySnapshot, evidence: ObservatoryEvidence
) -> dict[str, Any]:
    payload = dataclass_to_json_dict(snapshot)
    payload["evidence_summary"] = {
        "week8": dataclass_to_json_dict(evidence.week8),
        "week9": dataclass_to_json_dict(evidence.week9),
        "week11": dataclass_to_json_dict(evidence.week11),
        "week12": dataclass_to_json_dict(evidence.week12),
        "week13": dataclass_to_json_dict(evidence.week13),
    }
    payload["snapshot_label"] = "Committed snapshot evidence only"
    payload["week14_capability_boundary"] = (
        "Week 14 is packaging rather than new cognitive capability."
    )
    return payload


def _demo_manifest_payload(manifest: DemoManifest) -> dict[str, Any]:
    payload = dataclass_to_json_dict(manifest)
    payload["manifest_label"] = "Committed Week 14 scripted demo manifest"
    payload["week14_capability_boundary"] = (
        "This demo narrates existing evidence; it does not demonstrate new cognition."
    )
    return payload


def _verify(evidence: ObservatoryEvidence) -> VerificationReport:
    week11 = evidence.week11
    week12 = evidence.week12
    week13 = evidence.week13
    checks = (
        VerificationCheck(
            check_id="authoritative_checkpoint",
            passed=week12.stable_checkpoint_sha256 == AUTHORITATIVE_ROLLBACK_CHECKPOINT
            and week13.authoritative_checkpoint_sha256 == AUTHORITATIVE_ROLLBACK_CHECKPOINT,
            summary="Week 12 and Week 13 both anchor the same authoritative rollback checkpoint.",
            evidence_refs=(
                week12.week12_acceptance_reference.path,
                week12.stable_checkpoint_reference.path,
                week13.acceptance_reference.path,
            ),
        ),
        VerificationCheck(
            check_id="evidence_payload_hashes",
            passed=week13.reproducibility_pass
            and week13.checkpoint_checks_all_pass
            and week13.aggregate_reference.sha256 == week13.aggregate_expected_sha256
            and week13.claim_matrix_reference.sha256 == week13.claim_matrix_expected_sha256
            and week12.stable_checkpoint_reference.sha256
            == week13.week12_checkpoint_expected_file_sha256,
            summary="Week 12 checkpoint and Week 13 aggregate and claim bytes match the committed reproducibility manifest.",
            evidence_refs=(
                week12.stable_checkpoint_reference.path,
                week13.aggregate_reference.path,
                week13.claim_matrix_reference.path,
                week13.reproducibility_reference.path,
            ),
        ),
        VerificationCheck(
            check_id="rollback_authority_state",
            passed=week12.rollback_pass
            and week12.production_action_authority == "production_curiosity"
            and week12.general_controller_only
            and not week12.router_registered,
            summary="Rollback checkpoint keeps general controller only and preserves production curiosity authority.",
            evidence_refs=(
                week12.week12_acceptance_reference.path,
                week12.stable_checkpoint_reference.path,
            ),
        ),
        VerificationCheck(
            check_id="specialist_inactive",
            passed=not week12.candidate_active
            and week12.candidate_status == "rejected_after_week12"
            and week12.candidate_checkpoint_sha256 == REJECTED_SPECIALIST_CHECKPOINT
            and not week12.production_activation_authorised
            and not week11.production_activation_authorised,
            summary="Rejected specialist remains experimental and inactive.",
            evidence_refs=(
                week11.reference.path,
                week12.week12_acceptance_reference.path,
                week12.stable_checkpoint_reference.path,
            ),
        ),
        VerificationCheck(
            check_id="paired_narrow_and_broad_results",
            passed=week11.narrow_successes == 52
            and week11.narrow_total == 52
            and week12.broad_successes == 0
            and week12.broad_total == 32
            and week12.candidate_decision == "reject_and_rollback",
            summary="Week 11 narrow 52/52 is paired with Week 12 broad 0/32 and reject_and_rollback.",
            evidence_refs=(
                week11.reference.path,
                week12.week12_acceptance_reference.path,
                week12.retention_reference.path,
            ),
        ),
        VerificationCheck(
            check_id="week13_claim_status",
            passed=_claim_statuses_pass(week13),
            summary="Week 13 claim statuses remain C1-C4 supported and C5 unsupported.",
            evidence_refs=(week13.claim_matrix_reference.path, week13.acceptance_reference.path),
        ),
        VerificationCheck(
            check_id="week13_claim_boundaries",
            passed=week13.supported_core_claim_count == 4
            and not week13.complete_seedmind_task_advantage_over_rollback_claimed
            and not week13.rejected_specialist_production_active
            and week13.decision == "week13_evidence_pass",
            summary="Week 13 preserves bounded claim counts, no task-advantage claim, and inactive rejected specialist.",
            evidence_refs=(week13.acceptance_reference.path, week13.aggregate_reference.path),
        ),
        VerificationCheck(
            check_id="limitation_visibility",
            passed=_limitations_text_pass(week13.limitations_text),
            summary="Week 13 limitations still expose the symbolic boundary and the 36/100, 15/40, 52/52, and 0/32 results.",
            evidence_refs=(week13.limitations_reference.path,),
        ),
    )
    base_payload = {
        "authoritative_checkpoint_sha256": AUTHORITATIVE_ROLLBACK_CHECKPOINT,
        "packaging_status": "Week 14 Batch 1 packaging over committed evidence",
        "all_passed": all(item.passed for item in checks),
        "failure_count": sum(0 if item.passed else 1 for item in checks),
        "checks": [
            {
                "check_id": item.check_id,
                "passed": item.passed,
                "summary": item.summary,
                "evidence_refs": list(item.evidence_refs),
            }
            for item in checks
        ],
    }
    return VerificationReport(
        authoritative_checkpoint_sha256=AUTHORITATIVE_ROLLBACK_CHECKPOINT,
        packaging_status="Week 14 Batch 1 packaging over committed evidence",
        all_passed=cast(bool, base_payload["all_passed"]),
        failure_count=cast(int, base_payload["failure_count"]),
        checks=checks,
        deterministic_digest=canonical_json_sha256(base_payload),
    )


def _verification_payload(report: VerificationReport) -> dict[str, Any]:
    payload = dataclass_to_json_dict(report)
    payload["checks"] = [
        {
            "check_id": check.check_id,
            "passed": check.passed,
            "summary": check.summary,
            "evidence_refs": list(check.evidence_refs),
        }
        for check in report.checks
    ]
    return payload


def _claim_statuses_pass(week13: Any) -> bool:
    expected = {
        "C1": "supported",
        "C2": "supported",
        "C3": "supported",
        "C4": "supported",
        "C5": "unsupported",
    }
    actual = {claim.claim_id: claim.status for claim in week13.claims}
    return actual == expected


def _limitations_text_pass(text: str) -> bool:
    required_fragments = (
        "small, symbolic, deterministic Nursery",
        "36/100",
        "15/40",
        "52/52",
        "0/32",
        "Week 14 may show that, in the deterministic symbolic Nursery:",
    )
    return all(fragment in text for fragment in required_fragments)


def _read_static_text(name: str) -> str:
    return resources.files(STATIC_PACKAGE).joinpath("static", name).read_text(encoding="utf-8")
