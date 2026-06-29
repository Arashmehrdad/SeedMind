"""Deterministic standalone acceptance aggregation for Batch 1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from typing import Any

from seedmind.research.ndnra.experiment import (
    NDNRAExperimentResult,
    run_ndnra_heat_fan_experiment,
)
from seedmind.research.ndnra.growth_experiment import (
    StructuralGrowthExperimentResult,
    run_ndnra_structural_growth_experiment,
)
from seedmind.research.ndnra.multieffect_experiment import (
    MultieffectExperimentResult,
    run_ndnra_multieffect_experiment,
)

__all__ = [
    "StandaloneAcceptanceAuthority",
    "StandaloneAcceptanceDeltaReport",
    "StandaloneAcceptanceResult",
    "run_standalone_acceptance",
    "validate_standalone_acceptance_result",
]


@dataclass(frozen=True, slots=True)
class StandaloneAcceptanceAuthority:
    """Explicitly records absent authority for the standalone aggregate."""

    action_selection_authority: bool
    production_action_authority: bool
    recommendation_authority: bool
    scheduling_authority: bool
    execution_authority: bool
    persistence_authority: bool
    live_integration_authority: bool
    promotion_authority: bool


@dataclass(frozen=True, slots=True)
class StandaloneAcceptanceDeltaReport:
    """Records that this boundary adds no new evidence or authority deltas."""

    factual_confidence_delta: float
    mastery_delta: float
    competence_delta: float
    growth_delta: float
    replay_delta: float
    real_observation_delta: float


@dataclass(frozen=True, slots=True)
class StandaloneAcceptanceResult:
    """In-memory aggregate of the existing standalone NDNRA experiment gates."""

    heat_fan_result: NDNRAExperimentResult
    multieffect_result: MultieffectExperimentResult
    structural_growth_result: StructuralGrowthExperimentResult
    heat_fan_passed: bool
    multieffect_passed: bool
    structural_growth_passed: bool
    sqlite_cognition_unused: bool
    observable_as_factual_consequence_evidence: bool
    checkpoint_restart_proof_included: bool
    authority: StandaloneAcceptanceAuthority
    deltas: StandaloneAcceptanceDeltaReport
    canonical_ascii_snapshot: str
    result_identity: str
    pass_gate: bool


def run_standalone_acceptance() -> StandaloneAcceptanceResult:
    """Run the existing standalone gates and aggregate them without new authority."""

    heat_fan_result, _ = run_ndnra_heat_fan_experiment()
    multieffect_result, _, _, _ = run_ndnra_multieffect_experiment()
    structural_growth_result, _, _, _ = run_ndnra_structural_growth_experiment()

    authority = StandaloneAcceptanceAuthority(
        action_selection_authority=False,
        production_action_authority=False,
        recommendation_authority=False,
        scheduling_authority=False,
        execution_authority=False,
        persistence_authority=False,
        live_integration_authority=False,
        promotion_authority=False,
    )
    deltas = StandaloneAcceptanceDeltaReport(
        factual_confidence_delta=0.0,
        mastery_delta=0.0,
        competence_delta=0.0,
        growth_delta=0.0,
        replay_delta=0.0,
        real_observation_delta=0.0,
    )

    sqlite_cognition_unused = (
        not heat_fan_result.sqlite_used_for_recall
        and not multieffect_result.sqlite_used_for_composition
        and not structural_growth_result.sqlite_used_for_growth
    )
    pass_gate = bool(
        heat_fan_result.pass_gate
        and multieffect_result.pass_gate
        and structural_growth_result.pass_gate
        and sqlite_cognition_unused
        and _authority_is_zero(authority)
        and _deltas_are_zero(deltas)
    )
    seed = StandaloneAcceptanceResult(
        heat_fan_result=heat_fan_result,
        multieffect_result=multieffect_result,
        structural_growth_result=structural_growth_result,
        heat_fan_passed=heat_fan_result.pass_gate,
        multieffect_passed=multieffect_result.pass_gate,
        structural_growth_passed=structural_growth_result.pass_gate,
        sqlite_cognition_unused=sqlite_cognition_unused,
        observable_as_factual_consequence_evidence=False,
        checkpoint_restart_proof_included=False,
        authority=authority,
        deltas=deltas,
        canonical_ascii_snapshot="",
        result_identity="",
        pass_gate=pass_gate,
    )
    snapshot = _canonical_snapshot(seed)
    identity = hashlib.sha256(snapshot.encode("ascii")).hexdigest()
    result = StandaloneAcceptanceResult(
        heat_fan_result=heat_fan_result,
        multieffect_result=multieffect_result,
        structural_growth_result=structural_growth_result,
        heat_fan_passed=heat_fan_result.pass_gate,
        multieffect_passed=multieffect_result.pass_gate,
        structural_growth_passed=structural_growth_result.pass_gate,
        sqlite_cognition_unused=sqlite_cognition_unused,
        observable_as_factual_consequence_evidence=False,
        checkpoint_restart_proof_included=False,
        authority=authority,
        deltas=deltas,
        canonical_ascii_snapshot=snapshot,
        result_identity=identity,
        pass_gate=pass_gate,
    )
    validate_standalone_acceptance_result(result)
    return result


def validate_standalone_acceptance_result(result: StandaloneAcceptanceResult) -> None:
    """Reject tampered or internally inconsistent acceptance aggregates."""

    if result.heat_fan_passed is not result.heat_fan_result.pass_gate:
        raise ValueError("heat-fan pass flag does not match component result")
    if result.multieffect_passed is not result.multieffect_result.pass_gate:
        raise ValueError("multieffect pass flag does not match component result")
    if result.structural_growth_passed is not result.structural_growth_result.pass_gate:
        raise ValueError("structural-growth pass flag does not match component result")

    sqlite_unused = (
        not result.heat_fan_result.sqlite_used_for_recall
        and not result.multieffect_result.sqlite_used_for_composition
        and not result.structural_growth_result.sqlite_used_for_growth
    )
    if result.sqlite_cognition_unused is not sqlite_unused:
        raise ValueError("sqlite cognition flag does not match component results")
    if result.observable_as_factual_consequence_evidence:
        raise ValueError("standalone acceptance cannot become factual consequence evidence")
    if result.checkpoint_restart_proof_included:
        raise ValueError("checkpoint restart proof is deferred to Batch 2")
    if not _authority_is_zero(result.authority):
        raise ValueError("standalone acceptance cannot grant authority")
    if not _deltas_are_zero(result.deltas):
        raise ValueError("standalone acceptance deltas must remain zero")

    expected_snapshot = _canonical_snapshot(result)
    if result.canonical_ascii_snapshot != expected_snapshot:
        raise ValueError("canonical snapshot does not match aggregate content")
    expected_identity = hashlib.sha256(expected_snapshot.encode("ascii")).hexdigest()
    if result.result_identity != expected_identity:
        raise ValueError("result identity does not match canonical snapshot")

    expected_pass_gate = bool(
        result.heat_fan_result.pass_gate
        and result.multieffect_result.pass_gate
        and result.structural_growth_result.pass_gate
        and sqlite_unused
        and not result.observable_as_factual_consequence_evidence
        and not result.checkpoint_restart_proof_included
        and _authority_is_zero(result.authority)
        and _deltas_are_zero(result.deltas)
    )
    if result.pass_gate is not expected_pass_gate:
        raise ValueError("aggregate pass gate does not match component evidence")


def _canonical_snapshot(result: StandaloneAcceptanceResult) -> str:
    payload = {
        field.name: _normalize(getattr(result, field.name))
        for field in fields(result)
        if field.name not in {"canonical_ascii_snapshot", "result_identity"}
    }
    return json.dumps(payload, ensure_ascii=True, sort_keys=True, separators=(",", ":"))


def _normalize(value: Any) -> Any:
    if is_dataclass(value):
        return {field.name: _normalize(getattr(value, field.name)) for field in fields(value)}
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, tuple):
        return [_normalize(item) for item in value]
    if isinstance(value, list):
        return [_normalize(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _normalize(item) for key, item in value.items()}
    return value


def _authority_is_zero(authority: StandaloneAcceptanceAuthority) -> bool:
    return not any(getattr(authority, field.name) for field in fields(authority))


def _deltas_are_zero(deltas: StandaloneAcceptanceDeltaReport) -> bool:
    return all(getattr(deltas, field.name) == 0.0 for field in fields(deltas))
