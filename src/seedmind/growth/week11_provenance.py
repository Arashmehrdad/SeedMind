"""Authoritative Week 11 input and freeze-boundary checks."""

from pathlib import Path

from seedmind.growth.week11_inputs import WEEK8_SKILL, WEEK10_DIR
from seedmind.growth.week11_io import read_json, sha256_file
from seedmind.growth.week11_profiles import PARENT_MODULE

WEEK11_IMPLEMENTATION_PATHS = (
    Path("src/seedmind/growth/specialist.py"),
    Path("src/seedmind/growth/router.py"),
    Path("src/seedmind/growth/rollback.py"),
    Path("src/seedmind/growth/week11.py"),
    Path("src/seedmind/growth/week11_evaluation.py"),
    Path("src/seedmind/growth/week11_gate.py"),
    Path("src/seedmind/growth/week11_inputs.py"),
    Path("src/seedmind/growth/week11_profile_comparison.py"),
    Path("src/seedmind/growth/week11_rollout.py"),
    Path("src/seedmind/growth/week11_selection.py"),
)
FORBIDDEN_NDNRA_REFERENCES = (
    "seedmind.research.ndnra",
    "parallel_comparison",
    "parallel_operation",
)


def validate_week10_proposal() -> dict[str, object]:
    proposal = read_json(WEEK10_DIR / "growth_proposal_record.json")
    candidate = proposal.get("candidate")
    valid = isinstance(candidate, dict) and (
        proposal.get("status") == "proposed_not_authorised"
        and candidate.get("created") is False
        and candidate.get("type") == "skill_expert"
        and candidate.get("parent_module") == PARENT_MODULE
    )
    if not valid:
        raise ValueError("Week 10 proposal is not the authoritative Week 11 input")
    return proposal


def authoritative_hashes() -> dict[str, str]:
    paths = (
        WEEK10_DIR / "growth_proposal_record.json",
        WEEK10_DIR / "grounded_episode_traces.json",
        WEEK10_DIR / "diagnostic_report.json",
        WEEK10_DIR / "learning_progress_windows.json",
        WEEK10_DIR / "week10_acceptance_report.json",
        WEEK8_SKILL,
        Path("artifacts/week9_contribution/week9_acceptance_report.json"),
        Path("docs/architecture/NDNRA_Freeze_Manifest_2026-07-01.json"),
    )
    return {path.as_posix(): sha256_file(path) for path in paths}


def implementation_hashes() -> dict[str, str]:
    """Hash the executable Week 11 implementation tied to candidate evidence."""
    return {path.as_posix(): sha256_file(path) for path in WEEK11_IMPLEMENTATION_PATHS}


def frozen_ndnra_boundary_pass() -> bool:
    manifest = read_json(Path("docs/architecture/NDNRA_Freeze_Manifest_2026-07-01.json"))
    implementation_text = "\n".join(
        path.read_text(encoding="utf-8") for path in WEEK11_IMPLEMENTATION_PATHS
    )
    return bool(
        manifest.get("active_in_seedmind") is False
        and manifest.get("new_ndnra_stages_allowed_in_seedmind") is False
        and manifest.get("production_integration_allowed") is False
        and not any(reference in implementation_text for reference in FORBIDDEN_NDNRA_REFERENCES)
    )
