"""Typed deterministic loaders for committed Week 8-13 evidence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Final, cast

AUTHORITATIVE_ROLLBACK_CHECKPOINT: Final[str] = (
    "dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093"
)
REJECTED_SPECIALIST_CHECKPOINT: Final[str] = (
    "3d86d365496f16678363f9348280c9c102b1bfa98e3a000e23be775a989188b2"
)


class EvidenceError(ValueError):
    """Raised when committed evidence is missing or malformed."""


@dataclass(frozen=True)
class EvidenceReference:
    path: str
    sha256: str


@dataclass(frozen=True)
class Week8Evidence:
    skill_success_rate: float
    baseline_success_rate: float
    reuse_count: int
    skill_invocation_count: int
    authority_violations: int
    reference: EvidenceReference


@dataclass(frozen=True)
class Week9Evidence:
    total_attempts: int
    total_successes: int
    independent_success_rate: float
    final_support_level: int
    reduced_after_repeated_competence: bool
    reduced_again_after_repeated_competence: bool
    authority_violations: int
    reference: EvidenceReference


@dataclass(frozen=True)
class Week11Evidence:
    candidate_id: str
    policy_version: str
    narrow_successes: int
    narrow_total: int
    holdout_successes: int
    holdout_total: int
    production_activation_authorised: bool
    rollback_pass: bool
    reference: EvidenceReference


@dataclass(frozen=True)
class Week12Evidence:
    candidate_decision: str
    stable_checkpoint_sha256: str
    production_action_authority: str
    production_activation_authorised: bool
    candidate_active: bool
    router_registered: bool
    general_controller_only: bool
    candidate_status: str
    candidate_checkpoint_sha256: str
    broad_successes: int
    broad_total: int
    oracle_solvable_count: int
    familiar_retention_successes: int
    familiar_retention_total: int
    exact_trace_match_count: int
    specialist_selections: int
    rollback_pass: bool
    week12_acceptance_reference: EvidenceReference
    stable_checkpoint_reference: EvidenceReference
    retention_reference: EvidenceReference


@dataclass(frozen=True)
class ClaimRecord:
    claim_id: str
    claim: str
    status: str
    threshold: str
    observed: dict[str, Any]


@dataclass(frozen=True)
class Week13Evidence:
    authoritative_checkpoint_sha256: str
    supported_core_claim_count: int
    complete_and_rollback_action_path_equivalence_pass: bool
    complete_seedmind_task_advantage_over_rollback_claimed: bool
    rejected_specialist_production_active: bool
    decision: str
    familiar_successes: int
    familiar_total: int
    broader_retention_successes: int
    broader_retention_total: int
    no_task_advantage_text: str
    ambition_persistence_rate: float
    no_ambition_persistence_rate: float
    teaching_resolution_rate: float
    no_teaching_resolution_rate: float
    support_promotion_rate: float
    narrow_successes: int
    narrow_total: int
    broad_successes: int
    broad_total: int
    oracle_solvable_count: int
    familiar_degradation: float
    invalid_promotion_count: int
    growth_without_replay_invalid_promotions: int
    claims: tuple[ClaimRecord, ...]
    acceptance_reference: EvidenceReference
    aggregate_reference: EvidenceReference
    claim_matrix_reference: EvidenceReference
    reproducibility_reference: EvidenceReference
    limitations_reference: EvidenceReference
    reproducibility_pass: bool
    checkpoint_checks_all_pass: bool
    aggregate_expected_sha256: str
    claim_matrix_expected_sha256: str
    week12_checkpoint_expected_file_sha256: str
    limitations_text: str


@dataclass(frozen=True)
class ObservatoryEvidence:
    repository_root: Path
    week8: Week8Evidence
    week9: Week9Evidence
    week11: Week11Evidence
    week12: Week12Evidence
    week13: Week13Evidence


def repository_root(start: Path | None = None) -> Path:
    """Resolve the repository root from a working path inside the repo."""

    current = (start or Path.cwd()).resolve()
    for candidate in (current, *current.parents):
        if (candidate / "pyproject.toml").is_file() and (candidate / "src").is_dir():
            return candidate
    raise EvidenceError(f"Could not resolve repository root from {current}")


def load_observatory_evidence(root: Path | None = None) -> ObservatoryEvidence:
    repo_root = repository_root(root)

    week8_path = repo_root / "artifacts/week8_reusable_skill/week8_generalisation_report.json"
    week9_path = repo_root / "artifacts/week9_contribution/week9_acceptance_report.json"
    week11_acceptance_path = (
        repo_root / "artifacts/week11_specialist_growth/week11_acceptance_report.json"
    )
    week11_candidate_path = (
        repo_root / "artifacts/week11_specialist_growth/candidate_specialist_manifest.json"
    )
    week11_eval_path = repo_root / "artifacts/week11_specialist_growth/candidate_evaluation.json"
    week12_acceptance_path = (
        repo_root / "artifacts/week12_consolidation/week12_acceptance_report.json"
    )
    week12_checkpoint_path = repo_root / "artifacts/week12_consolidation/stable_mvp_checkpoint.json"
    week12_retention_path = repo_root / "artifacts/week12_consolidation/retention_report.json"
    week13_acceptance_path = (
        repo_root / "artifacts/week13_experiments/week13_acceptance_report.json"
    )
    week13_aggregate_path = repo_root / "artifacts/week13_experiments/aggregate_metrics.json"
    week13_claims_path = repo_root / "artifacts/week13_experiments/claim_evidence_matrix.json"
    week13_reproducibility_path = (
        repo_root / "artifacts/week13_experiments/reproducibility_report.json"
    )
    week13_limitations_path = (
        repo_root / "docs/architecture/SeedMind_Week13_Limitations_2026-07-01.md"
    )

    week8_json = _load_json_dict(week8_path)
    week9_json = _load_json_dict(week9_path)
    week11_acceptance_json = _load_json_dict(week11_acceptance_path)
    week11_candidate_json = _load_json_dict(week11_candidate_path)
    week11_eval_json = _load_json_dict(week11_eval_path)
    week12_acceptance_json = _load_json_dict(week12_acceptance_path)
    week12_checkpoint_json = _load_json_dict(week12_checkpoint_path)
    _load_json_dict(week12_retention_path)
    week13_acceptance_json = _load_json_dict(week13_acceptance_path)
    week13_aggregate_json = _load_json_dict(week13_aggregate_path)
    week13_claims_json = _load_json_dict(week13_claims_path)
    week13_reproducibility_json = _load_json_dict(week13_reproducibility_path)
    week13_limitations_text = _load_text(week13_limitations_path)

    week8 = Week8Evidence(
        skill_success_rate=_require_float(week8_json, "success_rate"),
        baseline_success_rate=_require_float(week8_json, "baseline_success_rate"),
        reuse_count=_require_int(week8_json, "reuse_count"),
        skill_invocation_count=_require_int(week8_json, "skill_invocation_count"),
        authority_violations=_require_int(week8_json, "authority_violations"),
        reference=_reference(repo_root, week8_path),
    )
    week9_acceptance = _require_dict(week9_json, "week9_acceptance")
    week9 = Week9Evidence(
        total_attempts=_require_int(week9_acceptance, "total_attempts"),
        total_successes=_require_int(week9_acceptance, "total_successes"),
        independent_success_rate=_require_float(week9_acceptance, "independent_success_rate"),
        final_support_level=_require_int(week9_acceptance, "final_support_level"),
        reduced_after_repeated_competence=_require_bool(
            week9_acceptance, "reduced_after_repeated_competence"
        ),
        reduced_again_after_repeated_competence=_require_bool(
            week9_acceptance, "reduced_again_after_repeated_competence"
        ),
        authority_violations=_require_int(week9_acceptance, "authority_violations"),
        reference=_reference(repo_root, week9_path),
    )

    candidate_section = _require_dict(week11_eval_json, "candidate")
    holdout_generalisation = _require_dict(week11_eval_json, "holdout_generalisation")
    holdout_section = _require_dict(holdout_generalisation, "candidate")
    week11 = Week11Evidence(
        candidate_id=_require_str(week11_acceptance_json, "candidate_id"),
        policy_version=_require_str(week11_candidate_json, "policy_version"),
        narrow_successes=_require_int(candidate_section, "successes")
        + _require_int(holdout_section, "successes"),
        narrow_total=_require_int(candidate_section, "total")
        + _require_int(holdout_section, "total"),
        holdout_successes=_require_int(holdout_section, "successes"),
        holdout_total=_require_int(holdout_section, "total"),
        production_activation_authorised=_require_bool(
            week11_acceptance_json, "production_activation_authorised"
        ),
        rollback_pass=_require_bool(week11_acceptance_json, "rollback_pass"),
        reference=_reference(repo_root, week11_acceptance_path),
    )

    checkpoint_candidate = _require_dict(week12_checkpoint_json, "candidate")
    checkpoint_registry = _require_dict(week12_checkpoint_json, "registry")
    growth_and_retention_summary = _require_dict(week13_aggregate_json, "growth_and_retention")
    broad_angular_summary = _require_dict(growth_and_retention_summary, "broad_angular")
    familiar_retention_summary = _require_dict(growth_and_retention_summary, "familiar_retention")
    familiar_total = _require_int(familiar_retention_summary, "action_trace_total")
    familiar_successes = round(
        _require_float(familiar_retention_summary, "post_growth_success_rate") * familiar_total
    )
    modules = _require_list(checkpoint_registry, "modules")
    general_controller_only = (
        len(modules) == 1
        and _require_str(cast(dict[str, Any], modules[0]), "module_type") == "general_controller"
    )
    week12 = Week12Evidence(
        candidate_decision=_require_str(week12_acceptance_json, "candidate_decision"),
        stable_checkpoint_sha256=_require_str(week12_acceptance_json, "stable_checkpoint_sha256"),
        production_action_authority=_require_str(
            week12_acceptance_json, "production_action_authority"
        ),
        production_activation_authorised=_require_bool(
            week12_acceptance_json, "production_activation_authorised"
        ),
        candidate_active=_require_bool(checkpoint_candidate, "active"),
        router_registered=_require_bool(checkpoint_registry, "router_registered"),
        general_controller_only=general_controller_only,
        candidate_status=_require_str(checkpoint_candidate, "status"),
        candidate_checkpoint_sha256=_require_str(checkpoint_candidate, "checkpoint_sha256"),
        broad_successes=_require_int(broad_angular_summary, "candidate_successes"),
        broad_total=_require_int(broad_angular_summary, "total"),
        oracle_solvable_count=_require_int(broad_angular_summary, "oracle_solvable_count"),
        familiar_retention_successes=familiar_successes,
        familiar_retention_total=familiar_total,
        exact_trace_match_count=_require_int(
            familiar_retention_summary, "action_trace_match_count"
        ),
        specialist_selections=_require_int(familiar_retention_summary, "specialist_selections"),
        rollback_pass=_require_bool(week12_acceptance_json, "rollback_pass"),
        week12_acceptance_reference=_reference(repo_root, week12_acceptance_path),
        stable_checkpoint_reference=_reference(repo_root, week12_checkpoint_path),
        retention_reference=_reference(repo_root, week12_retention_path),
    )

    task = _require_dict(week13_aggregate_json, "task")
    growth_and_retention = _require_dict(week13_aggregate_json, "growth_and_retention")
    ambition = _require_dict(week13_aggregate_json, "ambition")
    apprenticeship = _require_dict(week13_aggregate_json, "apprenticeship")
    production_equivalence = _require_dict(week13_aggregate_json, "production_equivalence")
    artifact_payload_hashes = _require_dict(week13_reproducibility_json, "artifact_payload_hashes")
    reproducibility_input_hashes = _require_dict(week13_reproducibility_json, "input_hashes")
    checkpoint_checks = _require_dict(
        week13_reproducibility_json, "authoritative_checkpoint_checks"
    )
    claim_records = []
    for item in _require_list(week13_claims_json, "claims"):
        raw_claim = cast(dict[str, Any], item)
        claim_records.append(
            ClaimRecord(
                claim_id=_require_str(raw_claim, "claim_id"),
                claim=_require_str(raw_claim, "claim"),
                status=_require_str(raw_claim, "status"),
                threshold=_require_str(raw_claim, "threshold"),
                observed=_require_dict(raw_claim, "observed"),
            )
        )

    week13 = Week13Evidence(
        authoritative_checkpoint_sha256=_require_str(
            week13_acceptance_json, "authoritative_checkpoint_sha256"
        ),
        supported_core_claim_count=_require_int(
            week13_acceptance_json, "supported_core_claim_count"
        ),
        complete_and_rollback_action_path_equivalence_pass=_require_bool(
            week13_acceptance_json, "complete_and_rollback_action_path_equivalence_pass"
        ),
        complete_seedmind_task_advantage_over_rollback_claimed=_require_bool(
            week13_acceptance_json, "complete_seedmind_task_advantage_over_rollback_claimed"
        ),
        rejected_specialist_production_active=_require_bool(
            week13_acceptance_json, "rejected_specialist_production_active"
        ),
        decision=_require_str(week13_acceptance_json, "decision"),
        familiar_successes=_require_int(
            _require_dict(task, "rollback_production_reference"), "successes"
        ),
        familiar_total=_require_int(
            _require_dict(task, "rollback_production_reference"), "episodes"
        ),
        broader_retention_successes=int(
            _require_float(
                _require_dict(growth_and_retention, "familiar_retention"),
                "post_growth_success_rate",
            )
            * _require_int(
                _require_dict(growth_and_retention, "familiar_retention"), "action_trace_total"
            )
        ),
        broader_retention_total=_require_int(
            _require_dict(growth_and_retention, "familiar_retention"), "action_trace_total"
        ),
        no_task_advantage_text=_require_str(production_equivalence, "interpretation"),
        ambition_persistence_rate=_require_float(
            _require_dict(ambition, "complete_seedmind"), "persistence_rate"
        ),
        no_ambition_persistence_rate=_require_float(
            _require_dict(ambition, "no_ambition"), "persistence_rate"
        ),
        teaching_resolution_rate=_require_float(
            _require_dict(
                _require_dict(apprenticeship, "complete_seedmind"), "teaching_resolution"
            ),
            "mean",
        ),
        no_teaching_resolution_rate=_require_float(
            _require_dict(
                _require_dict(apprenticeship, "no_human_teaching"), "teaching_resolution"
            ),
            "mean",
        ),
        support_promotion_rate=_require_float(
            _require_dict(apprenticeship, "complete_seedmind"), "support_promotion_rate"
        ),
        narrow_successes=_require_int(
            _require_dict(growth_and_retention, "narrow_angular"), "successes"
        ),
        narrow_total=_require_int(_require_dict(growth_and_retention, "narrow_angular"), "total"),
        broad_successes=_require_int(
            _require_dict(growth_and_retention, "broad_angular"), "candidate_successes"
        ),
        broad_total=_require_int(_require_dict(growth_and_retention, "broad_angular"), "total"),
        oracle_solvable_count=_require_int(
            _require_dict(growth_and_retention, "broad_angular"), "oracle_solvable_count"
        ),
        familiar_degradation=_require_float(
            _require_dict(growth_and_retention, "complete_seedmind"), "familiar_degradation"
        ),
        invalid_promotion_count=_require_int(
            _require_dict(growth_and_retention, "complete_seedmind"), "invalid_promotion_count"
        ),
        growth_without_replay_invalid_promotions=_require_int(
            _require_dict(growth_and_retention, "growth_without_replay"), "invalid_promotion_count"
        ),
        claims=tuple(claim_records),
        acceptance_reference=_reference(repo_root, week13_acceptance_path),
        aggregate_reference=_reference(repo_root, week13_aggregate_path),
        claim_matrix_reference=_reference(repo_root, week13_claims_path),
        reproducibility_reference=_reference(repo_root, week13_reproducibility_path),
        limitations_reference=_reference(repo_root, week13_limitations_path),
        reproducibility_pass=_require_bool(week13_reproducibility_json, "reproducibility_pass"),
        checkpoint_checks_all_pass=_require_bool(checkpoint_checks, "all_pass"),
        aggregate_expected_sha256=_require_str(artifact_payload_hashes, "aggregate_metrics.json"),
        claim_matrix_expected_sha256=_require_str(
            artifact_payload_hashes, "claim_evidence_matrix.json"
        ),
        week12_checkpoint_expected_file_sha256=_require_str(
            reproducibility_input_hashes,
            "artifacts/week12_consolidation/stable_mvp_checkpoint.json",
        ),
        limitations_text=week13_limitations_text,
    )
    return ObservatoryEvidence(
        repository_root=repo_root,
        week8=week8,
        week9=week9,
        week11=week11,
        week12=week12,
        week13=week13,
    )


def write_ascii_json_atomic(path: Path, temporary_path: Path, payload: dict[str, Any]) -> None:
    """Write deterministic ASCII JSON through an explicitly authorised sibling tmp path."""

    path.parent.mkdir(parents=True, exist_ok=True)
    if temporary_path.parent != path.parent:
        raise EvidenceError(
            f"Temporary path {temporary_path} must be a sibling of target path {path}"
        )
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
        newline="\n",
    )
    temporary_path.replace(path)


def canonical_json_sha256(payload: dict[str, Any]) -> str:
    encoded = json.dumps(payload, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()


def dataclass_to_json_dict(value: Any) -> dict[str, Any]:
    data = asdict(value)
    if "repository_root" in data:
        data["repository_root"] = str(data["repository_root"])
    return data


def _reference(root: Path, path: Path) -> EvidenceReference:
    return EvidenceReference(
        path=path.relative_to(root).as_posix(),
        sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
    )


def _load_text(path: Path) -> str:
    if not path.is_file():
        raise EvidenceError(f"Missing evidence file: {path}")
    return path.read_text(encoding="utf-8")


def _load_json_dict(path: Path) -> dict[str, Any]:
    if not path.is_file():
        raise EvidenceError(f"Missing evidence file: {path}")
    try:
        loaded = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise EvidenceError(f"Malformed JSON evidence in {path}: {exc}") from exc
    if not isinstance(loaded, dict):
        raise EvidenceError(f"Expected JSON object in {path}")
    return cast(dict[str, Any], loaded)


def _require_bool(payload: dict[str, Any], key: str) -> bool:
    value = payload.get(key)
    if not isinstance(value, bool):
        raise EvidenceError(f"Expected boolean {key!r}")
    return value


def _require_dict(payload: dict[str, Any], key: str) -> dict[str, Any]:
    value = payload.get(key)
    if not isinstance(value, dict):
        raise EvidenceError(f"Expected object {key!r}")
    return cast(dict[str, Any], value)


def _require_float(payload: dict[str, Any], key: str) -> float:
    value = payload.get(key)
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        raise EvidenceError(f"Expected number {key!r}")
    return float(value)


def _require_int(payload: dict[str, Any], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise EvidenceError(f"Expected integer {key!r}")
    return value


def _require_list(payload: dict[str, Any], key: str) -> list[Any]:
    value = payload.get(key)
    if not isinstance(value, list):
        raise EvidenceError(f"Expected list {key!r}")
    return value


def _require_str(payload: dict[str, Any], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise EvidenceError(f"Expected string {key!r}")
    return value
