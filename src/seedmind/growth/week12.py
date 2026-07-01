"""Original SeedMind Week 12 consolidation runner and evidence exporter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from seedmind.growth.week12_gate import Week12Evidence, run_week12_gate

DEFAULT_WEEK12_OUTPUT_DIR = Path("artifacts/week12_consolidation")


@dataclass(frozen=True, slots=True)
class Week12RunResult:
    """Executed Week 12 evidence and deterministic artifact paths."""

    evidence: Week12Evidence
    artifact_paths: tuple[Path, ...]


def run_week12_consolidation(
    *,
    output_dir: Path | None = None,
) -> Week12RunResult:
    """Execute the Week 12 gate and optionally export all evidence."""
    evidence = run_week12_gate()
    paths = () if output_dir is None else export_week12_evidence(evidence, output_dir)
    return Week12RunResult(evidence=evidence, artifact_paths=paths)


def export_week12_evidence(
    evidence: Week12Evidence,
    output_dir: Path,
) -> tuple[Path, ...]:
    """Write human-readable evaluation evidence and stable checkpoint files."""
    payloads = {
        "consolidation_schedule.json": evidence.consolidation_schedule,
        "scenario_catalogue.json": evidence.scenario_catalogue,
        "replay_report.json": evidence.replay_report,
        "retention_report.json": evidence.retention_report,
        "navigation_regression.json": evidence.navigation_report,
        "help_seeking_regression.json": evidence.help_report,
        "character_safety_report.json": evidence.character_safety_report,
        "growth_audit.json": evidence.growth_audit,
        "stable_mvp_checkpoint.json": evidence.stable_checkpoint,
        "week12_acceptance_report.json": evidence.acceptance_report,
        "checkpoints/final_registry.json": evidence.final_registry,
        "checkpoints/rollback_checkpoint.json": evidence.rollback_checkpoint,
    }
    paths: list[Path] = []
    for name, payload in payloads.items():
        path = output_dir / name
        _write_json(path, payload)
        paths.append(path)
    return tuple(paths)


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(
        json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n",
        encoding="ascii",
        newline="\n",
    )
    temporary.replace(path)
