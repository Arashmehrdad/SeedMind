"""Bounded comparison of production and NDNRA candidates."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite
from statistics import fmean

from seedmind.contracts import PrimitiveAction
from seedmind.integration.developmental_signals import LiveDevelopmentalSignals
from seedmind.integration.unified_shadow import NDNRALiveShadowAdapter


class AdviceCode(StrEnum):
    DISABLED = "disabled"
    FALLBACK = "fallback"
    ABSTAIN = "abstain"
    HUMAN_HOLD = "human_hold"
    HUMAN_VETO = "human_veto"
    RISK_VETO = "risk_veto"
    RESOURCE_VETO = "resource_veto"
    AGREE = "agree"
    ADVISE = "advise"


@dataclass(frozen=True, slots=True)
class AdviceConfig:
    enabled: bool = True
    minimum_evidence: int = 2
    minimum_confidence: float = 0.20
    minimum_accessibility: float = 0.20
    maximum_risk: float = 0.45
    maximum_resource_cost: float = 0.50
    human_threshold: float = 0.50
    history_limit: int = 64

    def __post_init__(self) -> None:
        if self.minimum_evidence <= 0 or self.history_limit <= 0:
            raise ValueError("integer bounds must be positive")
        for value in (
            self.minimum_confidence,
            self.minimum_accessibility,
            self.maximum_risk,
            self.maximum_resource_cost,
            self.human_threshold,
        ):
            _unit(value)


@dataclass(frozen=True, slots=True)
class AdviceEvidence:
    action: PrimitiveAction
    assembly_id: str
    evidence_count: int
    accessibility: float
    predicted_score: float
    raw_confidence: float
    calibrated_confidence: float
    predicted_risk: float
    predicted_resource_cost: float
    human_constraint: float

    def __post_init__(self) -> None:
        if not self.assembly_id.strip() or self.evidence_count <= 0:
            raise ValueError("advice evidence identity and count are invalid")
        if not isfinite(self.predicted_score):
            raise ValueError("predicted_score must be finite")
        for value in (
            self.accessibility,
            self.raw_confidence,
            self.calibrated_confidence,
            self.predicted_risk,
            self.predicted_resource_cost,
            self.human_constraint,
        ):
            _unit(value)


@dataclass(frozen=True, slots=True)
class AdviceDecision:
    code: AdviceCode
    production_action: PrimitiveAction
    ndnra_action: PrimitiveAction | None
    advice_action: PrimitiveAction | None
    retained_action: PrimitiveAction
    reason_code: str
    evidence: AdviceEvidence | None
    has_action_authority: bool = False
    kill_switch_active: bool = False

    def __post_init__(self) -> None:
        if self.retained_action is not self.production_action:
            raise ValueError("production action must be retained")
        if self.has_action_authority:
            raise ValueError("advice must remain non-authoritative")
        if not self.reason_code.strip() or not self.reason_code.isascii():
            raise ValueError("reason_code must be non-empty ASCII")


@dataclass(slots=True)
class ConfidenceCalibration:
    history_limit: int = 64
    _history: list[tuple[float, float]] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self._history)

    @property
    def error(self) -> float:
        if not self._history:
            return 0.0
        return fmean(abs(predicted - actual) for predicted, actual in self._history)

    @property
    def reliability(self) -> float:
        return 0.50 if not self._history else max(0.10, 1.0 - self.error)

    def calibrate(self, raw: float) -> float:
        _unit(raw)
        return raw * self.reliability

    def observe(self, predicted: float, success: bool) -> None:
        _unit(predicted)
        self._history.append((predicted, float(success)))
        if len(self._history) > self.history_limit:
            del self._history[: -self.history_limit]


class BoundedAdvicePolicy:
    def __init__(self, config: AdviceConfig | None = None) -> None:
        self.config = AdviceConfig() if config is None else config
        self.calibration = ConfidenceCalibration(self.config.history_limit)
        self._kill_switch = False

    @property
    def kill_switch_active(self) -> bool:
        return self._kill_switch

    def set_kill_switch(self, active: bool) -> None:
        self._kill_switch = active

    def evaluate(
        self,
        *,
        production_action: PrimitiveAction,
        ndnra_action: PrimitiveAction | None,
        available_actions: tuple[PrimitiveAction, ...],
        signals: LiveDevelopmentalSignals,
        shadow: NDNRALiveShadowAdapter,
    ) -> AdviceDecision:
        if production_action not in available_actions:
            raise ValueError("production action is unavailable")
        if self._kill_switch or not self.config.enabled:
            return self._result(
                AdviceCode.DISABLED,
                production_action,
                ndnra_action,
                None,
                "disabled",
                None,
            )
        if ndnra_action is None:
            return self._result(
                AdviceCode.ABSTAIN,
                production_action,
                None,
                None,
                "no_candidate",
                None,
            )
        if ndnra_action not in available_actions:
            return self._result(
                AdviceCode.FALLBACK,
                production_action,
                ndnra_action,
                None,
                "unavailable",
                None,
            )
        return self._evaluate_evidence(
            production_action,
            ndnra_action,
            signals,
            shadow,
        )

    def _evaluate_evidence(
        self,
        production: PrimitiveAction,
        ndnra: PrimitiveAction,
        signals: LiveDevelopmentalSignals,
        shadow: NDNRALiveShadowAdapter,
    ) -> AdviceDecision:
        evidence = self._evidence(ndnra, signals, shadow)
        if evidence is None:
            return self._result(
                AdviceCode.ABSTAIN,
                production,
                ndnra,
                None,
                "no_memory",
                None,
            )
        if evidence.human_constraint >= self.config.human_threshold:
            return self._result(
                AdviceCode.HUMAN_VETO,
                production,
                ndnra,
                None,
                "human_veto",
                evidence,
            )
        if evidence.predicted_risk > self.config.maximum_risk:
            return self._result(
                AdviceCode.RISK_VETO,
                production,
                ndnra,
                None,
                "risk_veto",
                evidence,
            )
        if evidence.predicted_resource_cost > self.config.maximum_resource_cost:
            return self._result(
                AdviceCode.RESOURCE_VETO,
                production,
                ndnra,
                None,
                "resource_veto",
                evidence,
            )
        if max(signals.help_requested, signals.human_clarification) >= self.config.human_threshold:
            return self._result(
                AdviceCode.HUMAN_HOLD,
                production,
                ndnra,
                None,
                "human_hold",
                evidence,
            )
        if (
            evidence.evidence_count < self.config.minimum_evidence
            or evidence.calibrated_confidence < self.config.minimum_confidence
            or evidence.accessibility < self.config.minimum_accessibility
        ):
            return self._result(
                AdviceCode.ABSTAIN,
                production,
                ndnra,
                None,
                "weak_evidence",
                evidence,
            )
        code = AdviceCode.AGREE if ndnra is production else AdviceCode.ADVISE
        return self._result(
            code,
            production,
            ndnra,
            ndnra,
            code.value,
            evidence,
        )

    def observe_comparison(
        self,
        decision: AdviceDecision,
        *,
        ndnra_better: bool,
    ) -> None:
        if decision.evidence is None or decision.ndnra_action is decision.production_action:
            return
        self.calibration.observe(
            decision.evidence.calibrated_confidence,
            ndnra_better,
        )

    def _evidence(
        self,
        action: PrimitiveAction,
        signals: LiveDevelopmentalSignals,
        shadow: NDNRALiveShadowAdapter,
    ) -> AdviceEvidence | None:
        from seedmind.integration.advice_evidence import collect_local_evidence

        return collect_local_evidence(action, signals, shadow, self.calibration)

    def _result(
        self,
        code: AdviceCode,
        production: PrimitiveAction,
        ndnra: PrimitiveAction | None,
        advice: PrimitiveAction | None,
        reason: str,
        evidence: AdviceEvidence | None,
    ) -> AdviceDecision:
        return AdviceDecision(
            code=code,
            production_action=production,
            ndnra_action=ndnra,
            advice_action=advice,
            retained_action=production,
            reason_code=reason,
            evidence=evidence,
            kill_switch_active=self._kill_switch,
        )


def _unit(value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("value must be between zero and one")
