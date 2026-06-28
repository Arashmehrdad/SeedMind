"""Real consequence comparison and context-specific action competence."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectNeed, EffectObservation


class ExperienceOrigin(StrEnum):
    """Source of an activity record, kept explicit across all later stages."""

    REAL = "real"
    REPLAY = "replay"
    IMAGINED = "imagined"


class ConsequenceDirection(StrEnum):
    """Whether an observed action changed the active need in the right direction."""

    IMPROVED = "improved"
    UNCHANGED = "unchanged"
    WORSENED = "worsened"


@dataclass(frozen=True, slots=True)
class ActionConsequenceAssessment:
    """Expected and observed effects for one exact action occurrence."""

    event_id: str
    origin: ExperienceOrigin
    context: ContextSignature
    action_code: str
    need: EffectNeed
    predicted_effects: tuple[EffectObservation, ...]
    observed_effects: tuple[EffectObservation, ...]
    neutral_tolerance: float = 0.05
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("event_id", self.event_id)
        _validate_code("action_code", self.action_code)
        _validate_effects("predicted_effects", self.predicted_effects, allow_empty=True)
        _validate_effects("observed_effects", self.observed_effects, allow_empty=False)
        if not isfinite(self.neutral_tolerance) or not 0.0 <= self.neutral_tolerance <= 1.0:
            raise ValueError("neutral_tolerance must be between zero and one")
        if self.has_action_selection_authority:
            raise ValueError("consequence assessments cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("consequence assessments cannot control production actions")

    @property
    def predicted_need_alignment(self) -> float:
        """Return normalized expected progress toward the active need."""
        return _need_alignment(self.need, self.predicted_effects)

    @property
    def observed_need_alignment(self) -> float:
        """Return normalized real progress toward or away from the active need."""
        return _need_alignment(self.need, self.observed_effects)

    @property
    def prediction_accuracy(self) -> float:
        """Return bounded agreement between predicted and observed effect values."""
        if not self.predicted_effects:
            return 0.0
        predicted = {effect.effect_code: effect for effect in self.predicted_effects}
        observed = {effect.effect_code: effect for effect in self.observed_effects}
        effect_codes = tuple(sorted(set(predicted) | set(observed)))
        weighted_error = 0.0
        total_weight = 0.0
        for effect_code in effect_codes:
            predicted_effect = predicted.get(effect_code)
            observed_effect = observed.get(effect_code)
            predicted_value = 0.0 if predicted_effect is None else predicted_effect.value
            observed_value = 0.0 if observed_effect is None else observed_effect.value
            weight = max(
                0.01,
                0.0 if predicted_effect is None else predicted_effect.confidence,
                0.0 if observed_effect is None else observed_effect.confidence,
            )
            weighted_error += (abs(predicted_value - observed_value) / 2.0) * weight
            total_weight += weight
        return max(0.0, min(1.0, 1.0 - weighted_error / total_weight))

    @property
    def prediction_surprise(self) -> float:
        """Return the complement of prediction accuracy."""
        return 1.0 - self.prediction_accuracy

    @property
    def direction(self) -> ConsequenceDirection:
        """Classify the observed need-aligned consequence."""
        if self.observed_need_alignment > self.neutral_tolerance:
            return ConsequenceDirection.IMPROVED
        if self.observed_need_alignment < -self.neutral_tolerance:
            return ConsequenceDirection.WORSENED
        return ConsequenceDirection.UNCHANGED

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable consequence evidence."""
        return {
            "event_id": self.event_id,
            "origin": self.origin.value,
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "need": {
                "need_code": self.need.need_code,
                "primary_effect_code": self.need.primary_effect_code,
                "dimensions": [
                    {
                        "effect_code": dimension.effect_code,
                        "desired_direction": dimension.desired_direction,
                        "intensity": dimension.intensity,
                    }
                    for dimension in self.need.dimensions
                ],
                "satisfaction_threshold": self.need.satisfaction_threshold,
            },
            "predicted_effects": [_effect_snapshot(item) for item in self.predicted_effects],
            "observed_effects": [_effect_snapshot(item) for item in self.observed_effects],
            "predicted_need_alignment": self.predicted_need_alignment,
            "observed_need_alignment": self.observed_need_alignment,
            "prediction_accuracy": self.prediction_accuracy,
            "prediction_surprise": self.prediction_surprise,
            "direction": self.direction.value,
            "neutral_tolerance": self.neutral_tolerance,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(frozen=True, slots=True)
class ActionCompetenceUpdate:
    """Inspectable before-and-after result of one competence-ledger observation."""

    event_id: str
    record_id: str
    direction: ConsequenceDirection
    evidence_applied: bool
    competence_before: float
    competence_after: float
    helpfulness_before: float
    helpfulness_after: float
    prediction_accuracy_before: float
    prediction_accuracy_after: float

    def __post_init__(self) -> None:
        _validate_code("event_id", self.event_id)
        _validate_code("record_id", self.record_id)
        for name, value in (
            ("competence_before", self.competence_before),
            ("competence_after", self.competence_after),
            ("helpfulness_before", self.helpfulness_before),
            ("helpfulness_after", self.helpfulness_after),
            ("prediction_accuracy_before", self.prediction_accuracy_before),
            ("prediction_accuracy_after", self.prediction_accuracy_after),
        ):
            _validate_unit(name, value)


@dataclass(slots=True)
class ContextualActionCompetenceRecord:
    """Real outcome evidence for one action in one exact context."""

    context: ContextSignature
    action_code: str
    real_attempt_count: int = 0
    improved_count: int = 0
    unchanged_count: int = 0
    worsened_count: int = 0
    cumulative_need_alignment: float = 0.0
    cumulative_prediction_accuracy: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("action_code", self.action_code)
        counts = (
            self.real_attempt_count,
            self.improved_count,
            self.unchanged_count,
            self.worsened_count,
        )
        if any(
            isinstance(value, bool) or not isinstance(value, int) or value < 0 for value in counts
        ):
            raise ValueError("competence record counts must be non-negative integers")
        if (
            self.improved_count + self.unchanged_count + self.worsened_count
            != self.real_attempt_count
        ):
            raise ValueError("outcome counts must equal real_attempt_count")
        if not isfinite(self.cumulative_need_alignment):
            raise ValueError("cumulative_need_alignment must be finite")
        if (
            not isfinite(self.cumulative_prediction_accuracy)
            or self.cumulative_prediction_accuracy < 0.0
        ):
            raise ValueError("cumulative_prediction_accuracy must be finite and non-negative")
        if self.has_action_selection_authority:
            raise ValueError("competence records cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("competence records cannot control production actions")

    @property
    def record_id(self) -> str:
        """Return stable identity for this context and action pair."""
        payload: dict[str, object] = {
            "context": self.context.snapshot(),
            "action_code": self.action_code,
        }
        return _identity("contextual-action-competence", payload)

    @property
    def mean_need_alignment(self) -> float:
        """Return average real movement toward or away from the active need."""
        if self.real_attempt_count == 0:
            return 0.0
        return self.cumulative_need_alignment / self.real_attempt_count

    @property
    def helpfulness(self) -> float:
        """Return bounded need-helpfulness with a conservative neutral prior."""
        useful_equivalent = self.improved_count + 0.5 * self.unchanged_count
        return (1.0 + useful_equivalent) / (2.0 + self.real_attempt_count)

    @property
    def prediction_accuracy(self) -> float:
        """Return average prediction accuracy for real attempts."""
        if self.real_attempt_count == 0:
            return 0.0
        return self.cumulative_prediction_accuracy / self.real_attempt_count

    @property
    def evidence_strength(self) -> float:
        """Limit confidence until several independent real attempts exist."""
        return min(1.0, self.real_attempt_count / 4.0)

    @property
    def competence(self) -> float:
        """Return local competence from helpfulness, prediction, and support."""
        return self.helpfulness * self.prediction_accuracy * self.evidence_strength

    def observe(self, assessment: ActionConsequenceAssessment) -> ActionCompetenceUpdate:
        """Apply one real assessment to this exact context-action record."""
        if assessment.origin is not ExperienceOrigin.REAL:
            raise ValueError("only real experience may update action competence")
        if assessment.context != self.context:
            raise ValueError("assessment context does not match competence record")
        if assessment.action_code != self.action_code:
            raise ValueError("assessment action does not match competence record")

        competence_before = self.competence
        helpfulness_before = self.helpfulness
        accuracy_before = self.prediction_accuracy
        self.real_attempt_count += 1
        if assessment.direction is ConsequenceDirection.IMPROVED:
            self.improved_count += 1
        elif assessment.direction is ConsequenceDirection.WORSENED:
            self.worsened_count += 1
        else:
            self.unchanged_count += 1
        self.cumulative_need_alignment += assessment.observed_need_alignment
        self.cumulative_prediction_accuracy += assessment.prediction_accuracy
        return ActionCompetenceUpdate(
            event_id=assessment.event_id,
            record_id=self.record_id,
            direction=assessment.direction,
            evidence_applied=True,
            competence_before=competence_before,
            competence_after=self.competence,
            helpfulness_before=helpfulness_before,
            helpfulness_after=self.helpfulness,
            prediction_accuracy_before=accuracy_before,
            prediction_accuracy_after=self.prediction_accuracy,
        )

    def snapshot(self) -> dict[str, object]:
        """Return deterministic local competence evidence."""
        return {
            "record_id": self.record_id,
            "context": self.context.snapshot(),
            "action_code": self.action_code,
            "real_attempt_count": self.real_attempt_count,
            "improved_count": self.improved_count,
            "unchanged_count": self.unchanged_count,
            "worsened_count": self.worsened_count,
            "mean_need_alignment": self.mean_need_alignment,
            "helpfulness": self.helpfulness,
            "prediction_accuracy": self.prediction_accuracy,
            "evidence_strength": self.evidence_strength,
            "competence": self.competence,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


@dataclass(slots=True)
class ContextualActionCompetenceLedger:
    """Deduplicate real events and keep competence local to context and action."""

    _assessments: dict[str, ActionConsequenceAssessment] = field(default_factory=dict)
    _records: dict[str, ContextualActionCompetenceRecord] = field(default_factory=dict)
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_action_selection_authority:
            raise ValueError("competence ledger cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("competence ledger cannot control production actions")

    @property
    def assessment_count(self) -> int:
        return len(self._assessments)

    @property
    def record_count(self) -> int:
        return len(self._records)

    def observe(self, assessment: ActionConsequenceAssessment) -> ActionCompetenceUpdate:
        """Apply one unique real event without accepting replay or imagination."""
        if assessment.origin is not ExperienceOrigin.REAL:
            raise ValueError("only real experience may become competence evidence")
        existing = self._assessments.get(assessment.event_id)
        if existing is not None:
            if existing != assessment:
                raise ValueError("consequence event identity conflict")
            duplicate_record = self.record_for(
                assessment.context,
                assessment.action_code,
            )
            return ActionCompetenceUpdate(
                event_id=assessment.event_id,
                record_id=duplicate_record.record_id,
                direction=assessment.direction,
                evidence_applied=False,
                competence_before=duplicate_record.competence,
                competence_after=duplicate_record.competence,
                helpfulness_before=duplicate_record.helpfulness,
                helpfulness_after=duplicate_record.helpfulness,
                prediction_accuracy_before=duplicate_record.prediction_accuracy,
                prediction_accuracy_after=duplicate_record.prediction_accuracy,
            )

        record_id = _record_id(assessment.context, assessment.action_code)
        record = self._records.get(record_id)
        if record is None:
            record = ContextualActionCompetenceRecord(
                context=assessment.context,
                action_code=assessment.action_code,
            )
            self._records[record_id] = record
        update = record.observe(assessment)
        self._assessments[assessment.event_id] = assessment
        return update

    def record_for(
        self,
        context: ContextSignature,
        action_code: str,
    ) -> ContextualActionCompetenceRecord:
        """Return one exact context-action competence record."""
        _validate_code("action_code", action_code)
        record_id = _record_id(context, action_code)
        try:
            return self._records[record_id]
        except KeyError as error:
            raise ValueError("no competence record exists for this context and action") from error

    def snapshot(self) -> dict[str, object]:
        """Return deterministic evidence with real source identities preserved."""
        return {
            "assessment_count": self.assessment_count,
            "record_count": self.record_count,
            "real_event_ids": sorted(self._assessments),
            "records": [self._records[key].snapshot() for key in sorted(self._records)],
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }


def _need_alignment(
    need: EffectNeed,
    effects: tuple[EffectObservation, ...],
) -> float:
    effect_map = {effect.effect_code: effect for effect in effects}
    total_intensity = sum(dimension.intensity for dimension in need.dimensions)
    aligned = 0.0
    for dimension in need.dimensions:
        effect = effect_map.get(dimension.effect_code)
        if effect is None:
            continue
        aligned += (
            effect.value * effect.confidence * dimension.desired_direction * dimension.intensity
        )
    return max(-1.0, min(1.0, aligned / total_intensity))


def _record_id(context: ContextSignature, action_code: str) -> str:
    return _identity(
        "contextual-action-competence",
        {"context": context.snapshot(), "action_code": action_code},
    )


def _identity(prefix: str, payload: dict[str, object]) -> str:
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


def _validate_effects(
    name: str,
    effects: tuple[EffectObservation, ...],
    *,
    allow_empty: bool,
) -> None:
    if not effects and not allow_empty:
        raise ValueError(f"{name} must not be empty")
    effect_codes = tuple(effect.effect_code for effect in effects)
    if len(effect_codes) != len(set(effect_codes)):
        raise ValueError(f"{name} must contain unique effect dimensions")
    if effect_codes != tuple(sorted(effect_codes)):
        raise ValueError(f"{name} must use stable sorted effect ordering")


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
