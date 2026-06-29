"""Bounded observed consequence chains from exact real transition evidence."""

from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite, sqrt
from statistics import fmean

from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.learned_consequence_model import ConsequenceModelObservation


@dataclass(frozen=True, slots=True)
class ObservedConsequenceChainConfig:
    """Finite limits for exact observed action-order evidence."""

    evidence_target: int = 4
    maximum_chain_depth: int = 3
    maximum_chains: int = 256
    maximum_effect_dimensions: int = 16
    maximum_candidates_per_request: int = 16
    neutral_effect_tolerance: float = 0.05

    def __post_init__(self) -> None:
        for name, value in (
            ("evidence_target", self.evidence_target),
            ("maximum_chain_depth", self.maximum_chain_depth),
            ("maximum_chains", self.maximum_chains),
            ("maximum_effect_dimensions", self.maximum_effect_dimensions),
            ("maximum_candidates_per_request", self.maximum_candidates_per_request),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        _validate_unit("neutral_effect_tolerance", self.neutral_effect_tolerance)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable chain limits."""
        return {
            "evidence_target": self.evidence_target,
            "maximum_chain_depth": self.maximum_chain_depth,
            "maximum_chains": self.maximum_chains,
            "maximum_effect_dimensions": self.maximum_effect_dimensions,
            "maximum_candidates_per_request": self.maximum_candidates_per_request,
            "neutral_effect_tolerance": self.neutral_effect_tolerance,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ObservedConsequenceChainConfig:
        """Restore validated chain limits from inspectable state."""
        values = _require_mapping("observed consequence chain config", snapshot)
        config = cls(
            evidence_target=_require_int(values, "evidence_target"),
            maximum_chain_depth=_require_int(values, "maximum_chain_depth"),
            maximum_chains=_require_int(values, "maximum_chains"),
            maximum_effect_dimensions=_require_int(values, "maximum_effect_dimensions"),
            maximum_candidates_per_request=_require_int(
                values,
                "maximum_candidates_per_request",
            ),
            neutral_effect_tolerance=_require_float(values, "neutral_effect_tolerance"),
        )
        if config.snapshot() != dict(values):
            raise ValueError("observed consequence chain config snapshot is not canonical")
        return config


@dataclass(frozen=True, slots=True)
class ObservedConsequenceChainStep:
    """One exact real transition inside an observed action chain."""

    event_id: str
    origin: ExperienceOrigin
    context: ContextSignature
    action_code: str
    next_context: ContextSignature
    observed_effects: tuple[EffectObservation, ...]
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("event_id", self.event_id)
        _validate_code("action_code", self.action_code)
        _validate_effects("observed_effects", self.observed_effects, allow_empty=False)
        if self.origin is not ExperienceOrigin.REAL:
            raise ValueError("observed consequence chain steps require real origin")
        if self.has_action_selection_authority:
            raise ValueError("observed chain steps cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("observed chain steps cannot control production actions")

    @classmethod
    def from_observation(
        cls,
        observation: ConsequenceModelObservation,
    ) -> ObservedConsequenceChainStep:
        """Convert an exact single-step consequence observation into a chain step."""
        return cls(
            event_id=observation.event_id,
            origin=observation.origin,
            context=observation.context,
            action_code=observation.action_code,
            next_context=observation.next_context,
            observed_effects=observation.observed_effects,
            has_action_selection_authority=observation.has_action_selection_authority,
            has_production_action_authority=observation.has_production_action_authority,
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic source transition evidence."""
        return {
            "event_id": self.event_id,
            "origin": self.origin.value,
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "next_context": self.next_context.snapshot(),
            "observed_effects": [_effect_snapshot(item) for item in self.observed_effects],
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ObservedConsequenceChainStep:
        """Restore one exact real chain step."""
        values = _require_mapping("observed consequence chain step", snapshot)
        step = cls(
            event_id=_require_string(values, "event_id"),
            origin=ExperienceOrigin(_require_string(values, "origin")),
            context=ContextSignature.from_snapshot(values.get("context")),
            action_code=_require_string(values, "action_code"),
            next_context=ContextSignature.from_snapshot(values.get("next_context")),
            observed_effects=tuple(
                _effect_from_snapshot(item) for item in _require_list(values, "observed_effects")
            ),
            has_action_selection_authority=_require_bool(
                values,
                "has_action_selection_authority",
            ),
            has_production_action_authority=_require_bool(
                values,
                "has_production_action_authority",
            ),
        )
        if step.snapshot() != dict(values):
            raise ValueError("observed consequence chain step snapshot is not canonical")
        return step


@dataclass(frozen=True, slots=True)
class ObservedConsequenceChain:
    """One complete exact observed ordered chain."""

    steps: tuple[ObservedConsequenceChainStep, ...]
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if not self.steps:
            raise ValueError("observed consequence chains require at least one step")
        event_ids = tuple(step.event_id for step in self.steps)
        if len(event_ids) != len(set(event_ids)):
            raise ValueError("one event cannot appear more than once in a chain")
        for index, step in enumerate(self.steps[:-1]):
            if step.next_context != self.steps[index + 1].context:
                raise ValueError("observed consequence chain continuity is disconnected")
        if self.has_action_selection_authority:
            raise ValueError("observed consequence chains cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("observed consequence chains cannot control production actions")
        if self.chain_id != _chain_id(self._identity_payload()):
            raise ValueError("observed consequence chain identity is inconsistent")

    @classmethod
    def from_observations(
        cls,
        observations: tuple[ConsequenceModelObservation, ...],
    ) -> ObservedConsequenceChain:
        """Build one observed chain from exact single-step observations."""
        return cls(
            steps=tuple(
                ObservedConsequenceChainStep.from_observation(observation)
                for observation in observations
            )
        )

    @property
    def chain_id(self) -> str:
        """Return stable identity for exact ordered source transitions."""
        return _chain_id(self._identity_payload())

    @property
    def start_context(self) -> ContextSignature:
        return self.steps[0].context

    @property
    def final_context(self) -> ContextSignature:
        return self.steps[-1].next_context

    @property
    def action_codes(self) -> tuple[str, ...]:
        return tuple(step.action_code for step in self.steps)

    @property
    def source_event_ids(self) -> tuple[str, ...]:
        return tuple(step.event_id for step in self.steps)

    @property
    def effect_codes(self) -> tuple[str, ...]:
        return tuple(
            sorted({effect.effect_code for step in self.steps for effect in step.observed_effects})
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable chain evidence."""
        return {
            "chain_id": self.chain_id,
            **self._identity_payload(),
            "steps": [step.snapshot() for step in self.steps],
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ObservedConsequenceChain:
        """Restore one complete exact observed ordered chain."""
        values = _require_mapping("observed consequence chain", snapshot)
        chain = cls(
            steps=tuple(
                ObservedConsequenceChainStep.from_snapshot(item)
                for item in _require_list(values, "steps")
            ),
            has_action_selection_authority=_require_bool(
                values,
                "has_action_selection_authority",
            ),
            has_production_action_authority=_require_bool(
                values,
                "has_production_action_authority",
            ),
        )
        if _require_string(values, "chain_id") != chain.chain_id:
            raise ValueError("observed consequence chain identity is inconsistent")
        if chain.snapshot() != dict(values):
            raise ValueError("observed consequence chain snapshot is not canonical")
        return chain

    def _identity_payload(self) -> dict[str, object]:
        return {
            "start_context": self.start_context.snapshot(),
            "action_codes": list(self.action_codes),
            "source_event_ids": list(self.source_event_ids),
            "final_context": self.final_context.snapshot(),
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsequenceChainPredictionRequest:
    """Explicit request for one exact start context and ordered action sequence."""

    start_context: ContextSignature
    action_codes: tuple[str, ...]
    relevant_effect_codes: tuple[str, ...]
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code_sequence("action_codes", self.action_codes, allow_empty=False)
        _validate_sorted_unique_codes("relevant_effect_codes", self.relevant_effect_codes)
        if not self.relevant_effect_codes:
            raise ValueError("relevant_effect_codes must not be empty")
        if self.has_action_selection_authority:
            raise ValueError("chain prediction requests cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("chain prediction requests cannot control production actions")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic non-authoritative prediction input."""
        return {
            "start_context": self.start_context.snapshot(),
            "action_codes": list(self.action_codes),
            "relevant_effect_codes": list(self.relevant_effect_codes),
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ConsequenceChainStepPrediction:
    """Predicted effects for one observed position in an ordered chain."""

    step_index: int
    action_code: str
    predicted_effects: tuple[EffectObservation, ...]
    effect_coverage: float
    confidence: float
    contradiction_score: float
    supporting_chain_ids: tuple[str, ...]
    supporting_real_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        if isinstance(self.step_index, bool) or self.step_index < 0:
            raise ValueError("step_index must be a non-negative integer")
        _validate_code("action_code", self.action_code)
        _validate_effects("predicted_effects", self.predicted_effects, allow_empty=True)
        for name, value in (
            ("effect_coverage", self.effect_coverage),
            ("confidence", self.confidence),
            ("contradiction_score", self.contradiction_score),
        ):
            _validate_unit(name, value)
        _validate_sorted_unique_codes("supporting_chain_ids", self.supporting_chain_ids)
        _validate_sorted_unique_codes("supporting_real_event_ids", self.supporting_real_event_ids)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic per-position prediction evidence."""
        return {
            "step_index": self.step_index,
            "action_code": self.action_code,
            "predicted_effects": [_effect_snapshot(item) for item in self.predicted_effects],
            "effect_coverage": self.effect_coverage,
            "confidence": self.confidence,
            "contradiction_score": self.contradiction_score,
            "supporting_chain_ids": list(self.supporting_chain_ids),
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
        }


@dataclass(frozen=True, slots=True)
class ConsequenceChainCorrelationGroup:
    """Chains connected by overlapping source events."""

    group_id: str
    chain_ids: tuple[str, ...]
    source_event_ids: tuple[str, ...]

    def __post_init__(self) -> None:
        _validate_code("group_id", self.group_id)
        _validate_sorted_unique_codes("chain_ids", self.chain_ids)
        _validate_sorted_unique_codes("source_event_ids", self.source_event_ids)
        if not self.chain_ids:
            raise ValueError("correlation groups require at least one chain")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic correlated-support evidence."""
        return {
            "group_id": self.group_id,
            "chain_ids": list(self.chain_ids),
            "source_event_ids": list(self.source_event_ids),
        }


@dataclass(frozen=True, slots=True)
class ConsequenceChainPrediction:
    """Prediction for an exact observed ordered chain request."""

    prediction_id: str
    request: ConsequenceChainPredictionRequest
    predicted_final_context: ContextSignature | None
    step_predictions: tuple[ConsequenceChainStepPrediction, ...]
    effect_coverage: float
    evidence_coverage: float
    final_context_confidence: float
    confidence: float
    uncertainty: float
    contradiction_score: float
    supporting_chain_ids: tuple[str, ...]
    supporting_real_event_ids: tuple[str, ...]
    independent_chain_group_count: int
    correlated_chain_groups: tuple[ConsequenceChainCorrelationGroup, ...]
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("prediction_id", self.prediction_id)
        for name, value in (
            ("effect_coverage", self.effect_coverage),
            ("evidence_coverage", self.evidence_coverage),
            ("final_context_confidence", self.final_context_confidence),
            ("confidence", self.confidence),
            ("uncertainty", self.uncertainty),
            ("contradiction_score", self.contradiction_score),
        ):
            _validate_unit(name, value)
        _validate_sorted_unique_codes("supporting_chain_ids", self.supporting_chain_ids)
        _validate_sorted_unique_codes("supporting_real_event_ids", self.supporting_real_event_ids)
        if isinstance(self.independent_chain_group_count, bool) or (
            self.independent_chain_group_count < 0
        ):
            raise ValueError("independent_chain_group_count must be non-negative")
        if self.uncertainty != 1.0 - self.confidence:
            raise ValueError("uncertainty must equal one minus confidence")
        if not self.supporting_chain_ids:
            if self.predicted_final_context is not None or self.step_predictions:
                raise ValueError("unsupported chain predictions cannot contain outcomes")
            if any(
                value != 0.0
                for value in (
                    self.effect_coverage,
                    self.evidence_coverage,
                    self.final_context_confidence,
                    self.confidence,
                    self.contradiction_score,
                )
            ):
                raise ValueError("unsupported chain prediction metrics must be zero")
        if self.has_action_selection_authority:
            raise ValueError("chain predictions cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("chain predictions cannot control production actions")
        if self.prediction_id != _prediction_id(self._identity_payload()):
            raise ValueError("chain prediction identity is inconsistent")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable prediction evidence."""
        return {"prediction_id": self.prediction_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "request": self.request.snapshot(),
            "predicted_final_context": (
                None
                if self.predicted_final_context is None
                else self.predicted_final_context.snapshot()
            ),
            "step_predictions": [item.snapshot() for item in self.step_predictions],
            "effect_coverage": self.effect_coverage,
            "evidence_coverage": self.evidence_coverage,
            "final_context_confidence": self.final_context_confidence,
            "confidence": self.confidence,
            "uncertainty": self.uncertainty,
            "contradiction_score": self.contradiction_score,
            "supporting_chain_ids": list(self.supporting_chain_ids),
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
            "independent_chain_group_count": self.independent_chain_group_count,
            "correlated_chain_groups": [item.snapshot() for item in self.correlated_chain_groups],
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ObservedConsequenceChainUpdate:
    """Before-and-after evidence from one observed chain registration."""

    chain_id: str
    evidence_applied: bool
    chain_count_before: int
    chain_count_after: int
    record_chain_count_before: int
    record_chain_count_after: int

    def __post_init__(self) -> None:
        _validate_code("chain_id", self.chain_id)
        for name, value in (
            ("chain_count_before", self.chain_count_before),
            ("chain_count_after", self.chain_count_after),
            ("record_chain_count_before", self.record_chain_count_before),
            ("record_chain_count_after", self.record_chain_count_after),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                raise ValueError(f"{name} must be a non-negative integer")
        if self.chain_count_after != self.chain_count_before + int(self.evidence_applied):
            raise ValueError("chain count change is inconsistent")
        expected_record_after = self.record_chain_count_before + int(self.evidence_applied)
        if self.record_chain_count_after != expected_record_after:
            raise ValueError("record chain count change is inconsistent")


@dataclass(slots=True)
class ObservedConsequenceChainModel:
    """In-memory exact observed chain model with no action authority."""

    config: ObservedConsequenceChainConfig = field(default_factory=ObservedConsequenceChainConfig)
    _chains: dict[str, ObservedConsequenceChain] = field(default_factory=dict)
    _records: dict[str, list[str]] = field(default_factory=dict)
    _steps_by_event_id: dict[str, ObservedConsequenceChainStep] = field(default_factory=dict)
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_action_selection_authority:
            raise ValueError("observed consequence chain model cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("observed consequence chain model cannot control production actions")

    @property
    def chain_count(self) -> int:
        return len(self._chains)

    @property
    def record_count(self) -> int:
        return len(self._records)

    @property
    def chains(self) -> tuple[ObservedConsequenceChain, ...]:
        """Return deterministic read-only access to observed chains."""
        return tuple(self._chains[key] for key in sorted(self._chains))

    def observe(self, chain: ObservedConsequenceChain) -> ObservedConsequenceChainUpdate:
        """Register one complete real observed ordered chain."""
        self._validate_chain(chain)
        chain_id = chain.chain_id
        record_id = _record_id(chain.start_context, chain.action_codes)
        existing = self._chains.get(chain_id)
        record_before = len(self._records.get(record_id, ()))
        if existing is not None:
            if existing != chain:
                raise ValueError("observed consequence chain identity conflict")
            return ObservedConsequenceChainUpdate(
                chain_id=chain_id,
                evidence_applied=False,
                chain_count_before=self.chain_count,
                chain_count_after=self.chain_count,
                record_chain_count_before=record_before,
                record_chain_count_after=record_before,
            )
        for step in chain.steps:
            existing_step = self._steps_by_event_id.get(step.event_id)
            if existing_step is not None and existing_step != step:
                raise ValueError("observed chain source event identity conflict")
        if self.chain_count >= self.config.maximum_chains:
            raise ValueError("observed consequence chain bound exceeded")

        count_before = self.chain_count
        self._chains[chain_id] = chain
        self._records.setdefault(record_id, []).append(chain_id)
        self._records[record_id].sort()
        for step in chain.steps:
            self._steps_by_event_id.setdefault(step.event_id, step)
        return ObservedConsequenceChainUpdate(
            chain_id=chain_id,
            evidence_applied=True,
            chain_count_before=count_before,
            chain_count_after=self.chain_count,
            record_chain_count_before=record_before,
            record_chain_count_after=len(self._records[record_id]),
        )

    def predict(self, request: ConsequenceChainPredictionRequest) -> ConsequenceChainPrediction:
        """Predict only from exact stored observed chains matching the request."""
        self._validate_prediction_request(request)
        chain_ids = tuple(
            self._records.get(_record_id(request.start_context, request.action_codes), ())
        )
        if not chain_ids:
            return self._unknown_prediction(request)
        if len(chain_ids) > self.config.maximum_candidates_per_request:
            raise ValueError("observed consequence chain candidate bound exceeded")
        chains = tuple(self._chains[chain_id] for chain_id in chain_ids)
        groups = _correlation_groups(chains)
        group_support = min(1.0, len(groups) / self.config.evidence_target)
        step_predictions = tuple(
            self._step_prediction(
                chains=chains,
                groups=groups,
                step_index=step_index,
                action_code=request.action_codes[step_index],
                relevant_effect_codes=request.relevant_effect_codes,
                group_support=group_support,
            )
            for step_index in range(len(request.action_codes))
        )
        final_context, final_context_confidence, final_context_contradiction = (
            self._final_context_prediction(chains, group_support)
        )
        effect_slots = len(request.action_codes) * len(request.relevant_effect_codes)
        known_slots = sum(
            len(step_prediction.predicted_effects) for step_prediction in step_predictions
        )
        effect_coverage = known_slots / effect_slots
        mean_step_confidence = (
            fmean(step.confidence for step in step_predictions) if step_predictions else 0.0
        )
        contradiction_score = max(
            final_context_contradiction,
            max((step.contradiction_score for step in step_predictions), default=0.0),
        )
        evidence_coverage = (effect_coverage + group_support) / 2.0
        confidence = min(
            evidence_coverage,
            fmean((mean_step_confidence, final_context_confidence)) * (1.0 - contradiction_score),
        )
        supporting_real_event_ids = tuple(
            sorted({event_id for chain in chains for event_id in chain.source_event_ids})
        )
        payload = self._prediction_payload(
            request=request,
            predicted_final_context=final_context,
            step_predictions=step_predictions,
            effect_coverage=effect_coverage,
            evidence_coverage=evidence_coverage,
            final_context_confidence=final_context_confidence,
            confidence=confidence,
            contradiction_score=contradiction_score,
            supporting_chain_ids=chain_ids,
            supporting_real_event_ids=supporting_real_event_ids,
            correlated_chain_groups=groups,
        )
        return ConsequenceChainPrediction(
            prediction_id=_prediction_id(payload),
            request=request,
            predicted_final_context=final_context,
            step_predictions=step_predictions,
            effect_coverage=effect_coverage,
            evidence_coverage=evidence_coverage,
            final_context_confidence=final_context_confidence,
            confidence=confidence,
            uncertainty=1.0 - confidence,
            contradiction_score=contradiction_score,
            supporting_chain_ids=chain_ids,
            supporting_real_event_ids=supporting_real_event_ids,
            independent_chain_group_count=len(groups),
            correlated_chain_groups=groups,
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic observed chain evidence without action authority."""
        return {
            "config": self.config.snapshot(),
            "chain_count": self.chain_count,
            "record_count": self.record_count,
            "source_event_ids": sorted(self._steps_by_event_id),
            "chains": [self._chains[key].snapshot() for key in sorted(self._chains)],
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ObservedConsequenceChainModel:
        """Restore exact observed chain state and derived indexes."""
        values = _require_mapping("observed consequence chain model", snapshot)
        config = ObservedConsequenceChainConfig.from_snapshot(values.get("config"))
        model = cls(
            config=config,
            has_action_selection_authority=_require_bool(
                values,
                "has_action_selection_authority",
            ),
            has_production_action_authority=_require_bool(
                values,
                "has_production_action_authority",
            ),
        )
        for raw_chain in _require_list(values, "chains"):
            model.observe(ObservedConsequenceChain.from_snapshot(raw_chain))
        if _require_int(values, "chain_count") != model.chain_count:
            raise ValueError("observed chain count does not match contents")
        if _require_int(values, "record_count") != model.record_count:
            raise ValueError("observed chain record count does not match contents")
        if _require_string_list(values, "source_event_ids") != sorted(model._steps_by_event_id):
            raise ValueError("observed chain source event identities do not match contents")
        if model.snapshot() != dict(values):
            raise ValueError("observed consequence chain model snapshot is not canonical")
        return model

    def _validate_chain(self, chain: ObservedConsequenceChain) -> None:
        if len(chain.steps) > self.config.maximum_chain_depth:
            raise ValueError("observed consequence chain depth bound exceeded")
        if len(chain.effect_codes) > self.config.maximum_effect_dimensions:
            raise ValueError("observed consequence chain effect-dimension bound exceeded")

    def _validate_prediction_request(self, request: ConsequenceChainPredictionRequest) -> None:
        if len(request.action_codes) > self.config.maximum_chain_depth:
            raise ValueError("chain prediction request depth bound exceeded")
        if len(request.relevant_effect_codes) > self.config.maximum_effect_dimensions:
            raise ValueError("chain prediction request effect-dimension bound exceeded")

    def _unknown_prediction(
        self,
        request: ConsequenceChainPredictionRequest,
    ) -> ConsequenceChainPrediction:
        payload = self._prediction_payload(
            request=request,
            predicted_final_context=None,
            step_predictions=(),
            effect_coverage=0.0,
            evidence_coverage=0.0,
            final_context_confidence=0.0,
            confidence=0.0,
            contradiction_score=0.0,
            supporting_chain_ids=(),
            supporting_real_event_ids=(),
            correlated_chain_groups=(),
        )
        return ConsequenceChainPrediction(
            prediction_id=_prediction_id(payload),
            request=request,
            predicted_final_context=None,
            step_predictions=(),
            effect_coverage=0.0,
            evidence_coverage=0.0,
            final_context_confidence=0.0,
            confidence=0.0,
            uncertainty=1.0,
            contradiction_score=0.0,
            supporting_chain_ids=(),
            supporting_real_event_ids=(),
            independent_chain_group_count=0,
            correlated_chain_groups=(),
        )

    def _step_prediction(
        self,
        *,
        chains: tuple[ObservedConsequenceChain, ...],
        groups: tuple[ConsequenceChainCorrelationGroup, ...],
        step_index: int,
        action_code: str,
        relevant_effect_codes: tuple[str, ...],
        group_support: float,
    ) -> ConsequenceChainStepPrediction:
        predicted: list[EffectObservation] = []
        confidences: list[float] = []
        contradictions: list[float] = []
        supporting_chain_ids: set[str] = set()
        supporting_event_ids: set[str] = set()
        for effect_code in relevant_effect_codes:
            observations: list[tuple[ObservedConsequenceChain, EffectObservation]] = []
            for chain in chains:
                effect = next(
                    (
                        item
                        for item in chain.steps[step_index].observed_effects
                        if item.effect_code == effect_code
                    ),
                    None,
                )
                if effect is not None:
                    observations.append((chain, effect))
            if not observations:
                continue
            value, confidence, contradiction = _effect_prediction(
                observations,
                groups=groups,
                group_support=group_support,
                neutral_effect_tolerance=self.config.neutral_effect_tolerance,
            )
            predicted.append(
                EffectObservation(
                    effect_code=effect_code,
                    value=value,
                    confidence=confidence,
                )
            )
            confidences.append(confidence)
            contradictions.append(contradiction)
            for chain, _ in observations:
                supporting_chain_ids.add(chain.chain_id)
                supporting_event_ids.add(chain.steps[step_index].event_id)
        return ConsequenceChainStepPrediction(
            step_index=step_index,
            action_code=action_code,
            predicted_effects=tuple(predicted),
            effect_coverage=len(predicted) / len(relevant_effect_codes),
            confidence=fmean(confidences) if confidences else 0.0,
            contradiction_score=max(contradictions, default=0.0),
            supporting_chain_ids=tuple(sorted(supporting_chain_ids)),
            supporting_real_event_ids=tuple(sorted(supporting_event_ids)),
        )

    def _final_context_prediction(
        self,
        chains: tuple[ObservedConsequenceChain, ...],
        group_support: float,
    ) -> tuple[ContextSignature, float, float]:
        by_context: dict[str, list[ObservedConsequenceChain]] = defaultdict(list)
        for chain in chains:
            by_context[_context_id(chain.final_context)].append(chain)
        top_key = min(by_context, key=lambda key: (-len(by_context[key]), key))
        top_count = len(by_context[top_key])
        confidence = group_support * top_count / len(chains)
        contradiction = 1.0 - top_count / len(chains)
        return by_context[top_key][0].final_context, confidence, contradiction

    @staticmethod
    def _prediction_payload(
        *,
        request: ConsequenceChainPredictionRequest,
        predicted_final_context: ContextSignature | None,
        step_predictions: tuple[ConsequenceChainStepPrediction, ...],
        effect_coverage: float,
        evidence_coverage: float,
        final_context_confidence: float,
        confidence: float,
        contradiction_score: float,
        supporting_chain_ids: tuple[str, ...],
        supporting_real_event_ids: tuple[str, ...],
        correlated_chain_groups: tuple[ConsequenceChainCorrelationGroup, ...],
    ) -> dict[str, object]:
        return {
            "request": request.snapshot(),
            "predicted_final_context": (
                None if predicted_final_context is None else predicted_final_context.snapshot()
            ),
            "step_predictions": [item.snapshot() for item in step_predictions],
            "effect_coverage": effect_coverage,
            "evidence_coverage": evidence_coverage,
            "final_context_confidence": final_context_confidence,
            "confidence": confidence,
            "uncertainty": 1.0 - confidence,
            "contradiction_score": contradiction_score,
            "supporting_chain_ids": list(supporting_chain_ids),
            "supporting_real_event_ids": list(supporting_real_event_ids),
            "independent_chain_group_count": len(correlated_chain_groups),
            "correlated_chain_groups": [item.snapshot() for item in correlated_chain_groups],
            "has_action_selection_authority": False,
            "has_production_action_authority": False,
        }


def _effect_prediction(
    observations: list[tuple[ObservedConsequenceChain, EffectObservation]],
    *,
    groups: tuple[ConsequenceChainCorrelationGroup, ...],
    group_support: float,
    neutral_effect_tolerance: float,
) -> tuple[float, float, float]:
    group_by_chain_id = {
        chain_id: group.group_id for group in groups for chain_id in group.chain_ids
    }
    grouped: dict[str, list[EffectObservation]] = defaultdict(list)
    for chain, effect in observations:
        grouped[group_by_chain_id[chain.chain_id]].append(effect)
    group_estimates: list[tuple[float, float]] = []
    for group_id in sorted(grouped):
        effects = grouped[group_id]
        weight_sum = sum(effect.confidence for effect in effects)
        value = (
            sum(effect.value * effect.confidence for effect in effects) / weight_sum
            if weight_sum
            else 0.0
        )
        confidence = fmean(effect.confidence for effect in effects)
        group_estimates.append((value, confidence))
    total_weight = sum(confidence for _, confidence in group_estimates)
    mean = (
        sum(value * confidence for value, confidence in group_estimates) / total_weight
        if total_weight
        else 0.0
    )
    second_moment = (
        sum(value * value * confidence for value, confidence in group_estimates) / total_weight
        if total_weight
        else 1.0
    )
    variance = max(0.0, min(1.0, second_moment - mean * mean))
    consistency = max(0.0, min(1.0, 1.0 - sqrt(variance)))
    positive_weight = sum(
        confidence for value, confidence in group_estimates if value > neutral_effect_tolerance
    )
    negative_weight = sum(
        confidence for value, confidence in group_estimates if value < -neutral_effect_tolerance
    )
    directional_weight = positive_weight + negative_weight
    contradiction = (
        0.0
        if directional_weight == 0.0
        else 2.0 * min(positive_weight, negative_weight) / directional_weight
    )
    confidence = group_support * consistency * (1.0 - contradiction)
    return max(-1.0, min(1.0, mean)), confidence, contradiction


def _correlation_groups(
    chains: tuple[ObservedConsequenceChain, ...],
) -> tuple[ConsequenceChainCorrelationGroup, ...]:
    remaining = {chain.chain_id: chain for chain in chains}
    groups: list[ConsequenceChainCorrelationGroup] = []
    while remaining:
        seed_id = min(remaining)
        stack = [seed_id]
        chain_ids: set[str] = set()
        event_ids: set[str] = set()
        while stack:
            current_id = stack.pop()
            current = remaining.pop(current_id, None)
            if current is None:
                continue
            chain_ids.add(current_id)
            current_events = set(current.source_event_ids)
            event_ids.update(current_events)
            overlapping = [
                candidate_id
                for candidate_id, candidate in remaining.items()
                if current_events & set(candidate.source_event_ids)
            ]
            stack.extend(sorted(overlapping, reverse=True))
        ordered_chain_ids = tuple(sorted(chain_ids))
        ordered_event_ids = tuple(sorted(event_ids))
        groups.append(
            ConsequenceChainCorrelationGroup(
                group_id=_identity(
                    "consequence-chain-correlation-group",
                    {
                        "chain_ids": list(ordered_chain_ids),
                        "source_event_ids": list(ordered_event_ids),
                    },
                ),
                chain_ids=ordered_chain_ids,
                source_event_ids=ordered_event_ids,
            )
        )
    return tuple(sorted(groups, key=lambda group: group.group_id))


def _record_id(context: ContextSignature, action_codes: tuple[str, ...]) -> str:
    return _identity(
        "observed-consequence-chain-record",
        {"start_context": context.snapshot(), "action_codes": list(action_codes)},
    )


def _chain_id(payload: Mapping[str, object]) -> str:
    return _identity("observed-consequence-chain", payload)


def _context_id(context: ContextSignature) -> str:
    return _identity("observed-chain-context", context.snapshot())


def _prediction_id(payload: Mapping[str, object]) -> str:
    return _identity("observed-consequence-chain-prediction", payload)


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"{prefix}:{hashlib.sha256(canonical).hexdigest()}"


def _effect_snapshot(effect: EffectObservation) -> dict[str, object]:
    return {
        "effect_code": effect.effect_code,
        "value": effect.value,
        "confidence": effect.confidence,
    }


def _effect_from_snapshot(snapshot: object) -> EffectObservation:
    values = _require_mapping("effect observation", snapshot)
    effect = EffectObservation(
        effect_code=_require_string(values, "effect_code"),
        value=_require_float(values, "value"),
        confidence=_require_float(values, "confidence"),
    )
    if _effect_snapshot(effect) != dict(values):
        raise ValueError("effect observation snapshot is not canonical")
    return effect


def _validate_effects(
    name: str,
    effects: tuple[EffectObservation, ...],
    *,
    allow_empty: bool,
) -> None:
    if not effects and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    _validate_sorted_unique_codes(name, tuple(effect.effect_code for effect in effects))


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    for value in values:
        _validate_code(name, value)
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique values")
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")


def _validate_code_sequence(
    name: str,
    values: tuple[str, ...],
    *,
    allow_empty: bool,
) -> None:
    if not values and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    for value in values:
        _validate_code(name, value)


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_list(values: Mapping[str, object], key: str) -> list[object]:
    value = values.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_float(values: Mapping[str, object], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _require_string_list(values: Mapping[str, object], key: str) -> list[str]:
    result: list[str] = []
    for item in _require_list(values, key):
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain strings")
        result.append(item)
    return result


__all__ = [
    "ConsequenceChainCorrelationGroup",
    "ConsequenceChainPrediction",
    "ConsequenceChainPredictionRequest",
    "ConsequenceChainStepPrediction",
    "ObservedConsequenceChain",
    "ObservedConsequenceChainConfig",
    "ObservedConsequenceChainModel",
    "ObservedConsequenceChainStep",
    "ObservedConsequenceChainUpdate",
]
