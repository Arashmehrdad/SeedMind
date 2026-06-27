"""Typed live developmental signals for non-authoritative NDNRA integration."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import fmean

from seedmind.ambition import AmbitionManager, AmbitionRecord, AmbitionStatus
from seedmind.curiosity import CuriositySelection
from seedmind.human import (
    ApprenticeshipManager,
    HelpContext,
    HumanRequest,
    HumanSignalCode,
    RequestIntentCode,
    VerificationRule,
)
from seedmind.self_model import ActionEffectEstimate, SelfModelRegistry
from seedmind.training import ExperienceTransition, OnlineTrainingMetrics


@dataclass(frozen=True, slots=True)
class LiveDevelopmentalSignals:
    """One bounded frame derived from active SeedMind subsystems."""

    step_index: int
    ambition_relevance: float
    ambition_commitment: float
    ambition_learning_progress: float
    curiosity_value: float
    curiosity_learning_progress: float
    curiosity_uncertainty: float
    self_controllability: float
    body_confidence: float
    help_requested: float
    human_approval: float
    human_correction: float
    human_demonstration: float
    human_clarification: float
    human_signal_magnitude: float
    prediction_error: float
    resource_pressure: float
    need_resolution: float

    def __post_init__(self) -> None:
        if self.step_index < -1:
            raise ValueError("step_index must be at least negative one")
        for name, value in self.values().items():
            _validate_unit(name, value)

    def values(self) -> dict[str, float]:
        """Return every learned effect dimension except the timeline index."""
        return {
            "ambition_relevance": self.ambition_relevance,
            "ambition_commitment": self.ambition_commitment,
            "ambition_learning_progress": self.ambition_learning_progress,
            "curiosity_value": self.curiosity_value,
            "curiosity_learning_progress": self.curiosity_learning_progress,
            "curiosity_uncertainty": self.curiosity_uncertainty,
            "self_controllability": self.self_controllability,
            "body_confidence": self.body_confidence,
            "help_requested": self.help_requested,
            "human_approval": self.human_approval,
            "human_correction": self.human_correction,
            "human_demonstration": self.human_demonstration,
            "human_clarification": self.human_clarification,
            "human_signal_magnitude": self.human_signal_magnitude,
            "prediction_error": self.prediction_error,
            "resource_pressure": self.resource_pressure,
            "need_resolution": self.need_resolution,
        }


class LiveDevelopmentalSignalProvider:
    """Coordinate real ambition, self-model, and apprenticeship evidence."""

    def __init__(
        self,
        *,
        ambition: AmbitionManager,
        self_model: SelfModelRegistry,
        apprenticeship: ApprenticeshipManager,
    ) -> None:
        if ambition.active_ambition is None:
            raise ValueError("live signal integration requires an active ambition")
        self.ambition = ambition
        self.self_model = self_model
        self.apprenticeship = apprenticeship
        self._blocked_attempts = 0
        self._last_signals = self._initial_signals()

    @property
    def current(self) -> LiveDevelopmentalSignals:
        """Return the latest frame for pre-action need recruitment."""
        return self._last_signals

    def begin_episode(self, episode_id: str) -> LiveDevelopmentalSignals:
        """Carry the active ambition into the live episode."""
        self.ambition.begin_episode(episode_id)
        self._last_signals = self._initial_signals()
        return self._last_signals

    def observe(
        self,
        experience: ExperienceTransition,
        metrics: OnlineTrainingMetrics,
        selection: CuriositySelection,
    ) -> LiveDevelopmentalSignals:
        """Update every contributing subsystem from one real transition."""
        if selection.selected_action is not experience.action:
            raise ValueError("selection action does not match the live transition")
        self.self_model.observe(experience)
        snapshot = self.self_model.snapshot()
        candidate = selection.selected_candidate
        controllable = _mean_absolute(experience.controllable_sensor_change)
        external = _mean_absolute(experience.external_sensor_change)
        need_resolution = _clamp_unit(max(0.0, controllable - external))
        resource_pressure = _resource_pressure(experience)
        action_controllability = _action_controllability(
            snapshot.action_effects,
            experience.action.value,
        )
        body_confidence = max(
            (estimate.controllability_score for estimate in snapshot.sensor_estimates),
            default=0.0,
        )
        competence = max(body_confidence, action_controllability)
        progress = min(
            0.79,
            _clamp_unit(
                0.50 * candidate.learning_progress + 0.30 * need_resolution + 0.20 * competence
            ),
        )
        active = self.ambition.active_ambition
        if active is None:
            raise RuntimeError("active ambition disappeared during live integration")
        if active.status is AmbitionStatus.ACTIVE:
            active = self.ambition.record_progress(
                progress,
                competence=competence,
                episode_id=experience.observation.episode_id,
            )

        self._blocked_attempts = self._blocked_attempts + 1 if need_resolution < 0.05 else 0
        request = HumanRequest(
            request_id=(
                f"live-{experience.observation.episode_id}-{experience.observation.step_id:04d}"
            ),
            intent_code=RequestIntentCode.PRACTICE_ACTIVE_AMBITION,
            target_code=active.target_capability,
            ambiguity=candidate.uncertainty,
            permission_level=2,
            verification_rule=VerificationRule.EXTERNAL_CHANGE,
        )
        self.apprenticeship.receive_request(
            request,
            episode_id=experience.observation.episode_id,
            step_index=experience.observation.step_id,
        )
        context = HelpContext(
            case_id=f"case-{request.request_id}",
            request=request,
            uncertainty=candidate.uncertainty,
            competence=competence,
            risk=max(resource_pressure, float(experience.terminated)),
            blocked_attempts=self._blocked_attempts,
            safe_experiment_available=(resource_pressure < 0.25 and candidate.uncertainty < 0.90),
            familiar=candidate.sample_count > 0,
        )
        decision = self.apprenticeship.evaluate(
            context,
            episode_id=experience.observation.episode_id,
            step_index=experience.observation.step_id,
        )
        response_code = HumanSignalCode.NONE
        if decision.should_request_help:
            response_code = self.apprenticeship.teacher_response(
                context,
                decision,
                episode_id=experience.observation.episode_id,
                step_index=experience.observation.step_id,
            ).code
        elif need_resolution > 0.05:
            response_code = self.apprenticeship.record_approval(
                request,
                episode_id=experience.observation.episode_id,
                step_index=experience.observation.step_id,
                uncertainty=candidate.uncertainty,
                competence=competence,
                verified=True,
                familiar=context.familiar,
            ).code
        elif candidate.sample_count > 0 and candidate.uncertainty >= 0.50:
            response_code = self.apprenticeship.record_correction(
                request,
                episode_id=experience.observation.episode_id,
                step_index=experience.observation.step_id,
                uncertainty=candidate.uncertainty,
                competence=competence,
            ).code

        ambition_relevance = _ambition_relevance(active)
        self._last_signals = LiveDevelopmentalSignals(
            step_index=selection.step_index,
            ambition_relevance=ambition_relevance,
            ambition_commitment=active.commitment,
            ambition_learning_progress=active.learning_progress,
            curiosity_value=_clamp_unit(candidate.information_gain),
            curiosity_learning_progress=candidate.learning_progress,
            curiosity_uncertainty=candidate.uncertainty,
            self_controllability=action_controllability,
            body_confidence=body_confidence,
            help_requested=float(decision.should_request_help),
            human_approval=float(response_code is HumanSignalCode.APPROVE),
            human_correction=float(response_code is HumanSignalCode.CORRECT),
            human_demonstration=float(response_code is HumanSignalCode.DEMONSTRATE),
            human_clarification=float(response_code is HumanSignalCode.CLARIFY),
            human_signal_magnitude=_mean_absolute(experience.next_observation.human_signal),
            prediction_error=_clamp_unit(metrics.mean_absolute_error),
            resource_pressure=resource_pressure,
            need_resolution=need_resolution,
        )
        return self._last_signals

    def _initial_signals(self) -> LiveDevelopmentalSignals:
        active = self.ambition.active_ambition
        if active is None:
            raise RuntimeError("active ambition is required")
        return LiveDevelopmentalSignals(
            step_index=-1,
            ambition_relevance=_ambition_relevance(active),
            ambition_commitment=active.commitment,
            ambition_learning_progress=active.learning_progress,
            curiosity_value=0.50,
            curiosity_learning_progress=0.0,
            curiosity_uncertainty=1.0,
            self_controllability=0.0,
            body_confidence=0.0,
            help_requested=0.0,
            human_approval=0.0,
            human_correction=0.0,
            human_demonstration=0.0,
            human_clarification=0.0,
            human_signal_magnitude=0.0,
            prediction_error=1.0,
            resource_pressure=0.0,
            need_resolution=0.0,
        )


def _ambition_relevance(active: AmbitionRecord) -> float:
    base = fmean(
        (
            active.purpose_relevance,
            active.expected_value,
            active.commitment,
        )
    )
    return _clamp_unit(
        base * (0.55 + 0.45 * (1.0 - active.competence)) + 0.10 * active.learning_progress
    )


def _action_controllability(
    action_effects: tuple[ActionEffectEstimate, ...],
    action_code: str,
) -> float:
    for estimate in action_effects:
        if estimate.action.value == action_code:
            scores = estimate.controllability_score
            return _clamp_unit(fmean(scores) if scores else 0.0)
    return 0.0


def _resource_pressure(experience: ExperienceTransition) -> float:
    source = experience.observation.resource_state
    destination = experience.next_observation.resource_state
    if not source:
        return 0.0
    depletion = fmean(
        max(0.0, source_value - destination_value)
        for source_value, destination_value in zip(source, destination, strict=True)
    )
    remaining = fmean(destination)
    return _clamp_unit(0.50 * depletion + 0.50 * max(0.0, 1.0 - remaining))


def _mean_absolute(values: tuple[float, ...]) -> float:
    return _clamp_unit(fmean(abs(value) for value in values)) if values else 0.0


def _clamp_unit(value: float) -> float:
    if not isfinite(value):
        raise ValueError("developmental signal must be finite")
    return max(0.0, min(1.0, value))


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
