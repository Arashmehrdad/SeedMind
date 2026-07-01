"""Original SeedMind Week 11 specialist-growth runner and evidence exporter."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from seedmind.growth.week11_gate import Week11Evidence, run_week11_gate

DEFAULT_WEEK11_OUTPUT_DIR = Path("artifacts/week11_specialist_growth")


@dataclass(frozen=True, slots=True)
class Week11RunResult:
    """Executed Week 11 evidence and deterministic artifact paths."""

    evidence: Week11Evidence
    artifact_paths: tuple[Path, ...]


def run_week11_specialist_growth(
    *,
    output_dir: Path | None = None,
) -> Week11RunResult:
    """Execute the bounded growth gate and optionally export its evidence."""
    evidence = run_week11_gate()
    paths = () if output_dir is None else export_week11_evidence(evidence, output_dir)
    return Week11RunResult(evidence=evidence, artifact_paths=paths)


def export_week11_evidence(
    evidence: Week11Evidence,
    output_dir: Path,
) -> tuple[Path, ...]:
    """Write all requested Week 11 evidence and checkpoint manifests."""
    payloads = {
        "candidate_specialist_manifest.json": evidence.candidate_manifest,
        "incubation_report.json": evidence.incubation_report,
        "candidate_evaluation.json": evidence.candidate_evaluation,
        "router_evaluation.json": evidence.router_evaluation,
        "parameter_budget_report.json": evidence.parameter_budget_report,
        "rollback_report.json": evidence.rollback_report,
        "brain_graph.json": evidence.brain_graph,
        "grown_architecture_manifest.json": evidence.architecture_manifest,
        "week11_acceptance_report.json": evidence.acceptance_report,
    }
    paths: list[Path] = []
    for name, payload in payloads.items():
        path = output_dir / name
        _write_json(path, payload)
        paths.append(path)

    graph = output_dir / "brain_graph.svg"
    _write_text(graph, _brain_graph_svg(evidence))
    paths.append(graph)

    checkpoints = output_dir / "checkpoints"
    checkpoint_payloads: dict[str, dict[str, object]] = {
        "pre_growth_registry.json": evidence.pre_growth_registry,
        "accepted_candidate_registry.json": evidence.grown_registry,
        "accepted_specialist_checkpoint.json": {
            "candidate_id": evidence.candidate.candidate_id,
            "checkpoint_sha256": evidence.candidate.checkpoint_sha256,
            "profile": evidence.candidate.profile.to_json(),
            "status": evidence.candidate.status.value,
        },
    }
    for name, payload in checkpoint_payloads.items():
        path = checkpoints / name
        _write_json(path, payload)
        paths.append(path)
    return tuple(paths)


def _brain_graph_svg(evidence: Week11Evidence) -> str:
    accepted = bool(evidence.acceptance_report["week11_main_milestone_pass"])
    status = "accepted for Week 12" if accepted else "rejected"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="900" height="320" viewBox="0 0 900 320">
  <rect width="900" height="320" fill="white"/>
  <text x="28" y="34" font-family="monospace" font-size="18">SeedMind Week 11 grown architecture - {status}</text>
  <rect x="40" y="90" width="180" height="70" rx="8" fill="#f4f4f4" stroke="black"/>
  <text x="62" y="130" font-family="monospace" font-size="14">Predictive seed core</text>
  <rect x="350" y="90" width="180" height="70" rx="8" fill="#f4f4f4" stroke="black"/>
  <text x="397" y="130" font-family="monospace" font-size="14">Router</text>
  <rect x="650" y="45" width="210" height="70" rx="8" fill="#f4f4f4" stroke="black"/>
  <text x="676" y="85" font-family="monospace" font-size="14">General controller</text>
  <rect x="650" y="185" width="210" height="70" rx="8" fill="#f4f4f4" stroke="black"/>
  <text x="672" y="225" font-family="monospace" font-size="14">Angular push specialist</text>
  <line x1="220" y1="125" x2="350" y2="125" stroke="black" stroke-width="2"/>
  <line x1="530" y1="115" x2="650" y2="80" stroke="black" stroke-width="2"/>
  <line x1="530" y1="135" x2="650" y2="220" stroke="black" stroke-width="2"/>
  <text x="42" y="286" font-family="monospace" font-size="13">Production authority remains production_curiosity; router and specialist are sandbox-only.</text>
</svg>
"""


def _write_json(path: Path, payload: dict[str, object]) -> None:
    _write_text(path, json.dumps(payload, indent=2, sort_keys=True, ensure_ascii=True) + "\n")


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(content, encoding="ascii", newline="\n")
    temporary.replace(path)
