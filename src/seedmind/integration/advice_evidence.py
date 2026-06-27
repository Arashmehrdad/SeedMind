"""Local evidence extraction for bounded NDNRA advice."""

from __future__ import annotations

from math import isfinite
from statistics import fmean

from seedmind.contracts import PrimitiveAction
from seedmind.integration.bounded_advice import AdviceEvidence, ConfidenceCalibration
from seedmind.integration.developmental_signals import LiveDevelopmentalSignals
from seedmind.integration.unified_shadow import NDNRALiveShadowAdapter


def collect_local_evidence(
    action: PrimitiveAction,
    signals: LiveDevelopmentalSignals,
    shadow: NDNRALiveShadowAdapter,
    calibration: ConfidenceCalibration,
) -> AdviceEvidence | None:
    assembly_id = f"assembly:shadow:{action.value}"
    try:
        shadow.graph.assembly(assembly_id)
    except ValueError:
        return None
    accessibility, score = shadow.evaluate_action(action, signals)
    return _assemble_evidence(
        action=action,
        assembly_id=assembly_id,
        accessibility=accessibility,
        score=score,
        signals=signals,
        shadow=shadow,
        calibration=calibration,
    )


def _assemble_evidence(
    *,
    action: PrimitiveAction,
    assembly_id: str,
    accessibility: float,
    score: float,
    signals: LiveDevelopmentalSignals,
    shadow: NDNRALiveShadowAdapter,
    calibration: ConfidenceCalibration,
) -> AdviceEvidence:
    assembly = shadow.graph.assembly(assembly_id)
    confidences: list[float] = []
    for code in (
        "need_resolution",
        "curiosity_value",
        "ambition_relevance",
        "resource_pressure",
        "prediction_error",
        "human_approval",
        "human_correction",
    ):
        estimate = assembly.effect_memory.estimate(code)
        if estimate is not None:
            confidences.append(estimate.confidence)
    mean_confidence = fmean(confidences) if confidences else 0.0
    raw = mean_confidence * min(1.0, assembly.evidence_count / 4.0) * accessibility
    projected = shadow.graph.project_effects(
        (assembly_id,),
        accessibility=shadow.adaptive.accessibility_map(),
    )
    resource = _positive(projected.get("resource_pressure", 0.0))
    risk = max(
        _positive(projected.get("termination_risk", 0.0)),
        0.50 * resource,
        0.25 * _positive(projected.get("prediction_error", 0.0)),
        signals.human_correction,
    )
    return AdviceEvidence(
        action=action,
        assembly_id=assembly_id,
        evidence_count=assembly.evidence_count,
        accessibility=accessibility,
        predicted_score=score,
        raw_confidence=raw,
        calibrated_confidence=calibration.calibrate(raw),
        predicted_risk=min(1.0, risk),
        predicted_resource_cost=resource,
        human_constraint=signals.human_correction,
    )


def _positive(value: float) -> float:
    if not isfinite(value):
        raise ValueError("value must be finite")
    return max(0.0, min(1.0, value))
