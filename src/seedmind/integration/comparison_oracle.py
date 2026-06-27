"""One-step outcome comparison that does not select production actions."""

from __future__ import annotations

from dataclasses import dataclass
from math import isfinite
from statistics import fmean

from seedmind.contracts import PrimitiveAction
from seedmind.environment import (
    NurseryObservationAdapter,
    NurseryScenario,
    NurseryState,
    NurseryTransitionEngine,
    TransitionOutcome,
    WorldProcessPipeline,
)
from seedmind.integration.developmental_signals import LiveDevelopmentalSignals


@dataclass(frozen=True, slots=True)
class CandidateOutcome:
    action: PrimitiveAction
    controllable_change: float
    external_change: float
    need_resolution: float
    resource_cost: float
    risk: float
    score: float

    def __post_init__(self) -> None:
        for value in (
            self.controllable_change,
            self.external_change,
            self.need_resolution,
            self.resource_cost,
            self.risk,
        ):
            _unit(value)
        if not isfinite(self.score) or not -1.0 <= self.score <= 1.0:
            raise ValueError("score must be between negative one and one")


@dataclass(frozen=True, slots=True)
class CandidateComparison:
    production: CandidateOutcome
    ndnra: CandidateOutcome
    advantage: float
    ndnra_better: bool

    def __post_init__(self) -> None:
        if not isfinite(self.advantage) or not -2.0 <= self.advantage <= 2.0:
            raise ValueError("advantage is outside the valid score difference")
        if self.ndnra_better != (self.advantage > 0.0):
            raise ValueError("ndnra_better is inconsistent")


class NurseryOutcomeOracle:
    """Evaluate cloned outcomes after candidates are fixed."""

    def __init__(self, scenario: NurseryScenario) -> None:
        self.scenario = scenario
        self._transition = NurseryTransitionEngine()
        self._pipeline = WorldProcessPipeline(scenario.world_processes)
        self._adapter = NurseryObservationAdapter(
            width=scenario.initial_state.width,
            height=scenario.initial_state.height,
        )

    def compare(
        self,
        *,
        state: NurseryState,
        production_action: PrimitiveAction,
        ndnra_action: PrimitiveAction,
        signals: LiveDevelopmentalSignals,
    ) -> CandidateComparison:
        production = self.evaluate(state, production_action, signals)
        ndnra = self.evaluate(state, ndnra_action, signals)
        advantage = ndnra.score - production.score
        return CandidateComparison(
            production=production,
            ndnra=ndnra,
            advantage=advantage,
            ndnra_better=advantage > 0.0,
        )

    def evaluate(
        self,
        state: NurseryState,
        action: PrimitiveAction,
        signals: LiveDevelopmentalSignals,
    ) -> CandidateOutcome:
        source = self._adapter.observe(
            state,
            episode_id="comparison-oracle",
            resource_state=self.scenario.resource_state(state),
        )
        transition = self._transition.apply(state, action)
        agent_state = transition.state
        agent = self._adapter.observe(
            agent_state,
            episode_id="comparison-oracle",
            resource_state=self.scenario.resource_state(agent_state),
        )
        final_state = agent_state
        if not final_state.terminated:
            final_state = self._pipeline.advance(agent_state).state
        final = self._adapter.observe(
            final_state,
            episode_id="comparison-oracle",
            resource_state=self.scenario.resource_state(final_state),
        )
        controllable = _mean_change(source.sensor_values, agent.sensor_values)
        external = _mean_change(agent.sensor_values, final.sensor_values)
        need_resolution = max(0.0, min(1.0, controllable - external))
        resource_cost = _resource_cost(source.resource_state, final.resource_state)
        risk = _transition_risk(transition.outcome, final_state.terminated)
        gain = (
            0.45 * need_resolution
            + 0.25 * controllable
            + 0.20 * external * signals.curiosity_value
            + 0.10 * signals.ambition_relevance
        )
        score = max(-1.0, min(1.0, gain - 0.35 * resource_cost - risk))
        return CandidateOutcome(
            action=action,
            controllable_change=controllable,
            external_change=external,
            need_resolution=need_resolution,
            resource_cost=resource_cost,
            risk=risk,
            score=score,
        )


def _mean_change(source: tuple[float, ...], destination: tuple[float, ...]) -> float:
    if not source:
        return 0.0
    return min(
        1.0,
        fmean(
            abs(destination_value - source_value)
            for source_value, destination_value in zip(source, destination, strict=True)
        ),
    )


def _resource_cost(source: tuple[float, ...], destination: tuple[float, ...]) -> float:
    if not source:
        return 0.0
    return min(
        1.0,
        fmean(
            max(0.0, source_value - destination_value)
            for source_value, destination_value in zip(source, destination, strict=True)
        ),
    )


def _transition_risk(outcome: TransitionOutcome, terminated: bool) -> float:
    if terminated:
        return 1.0
    if "blocked" in outcome.value or "immovable" in outcome.value:
        return 0.25
    if "no_contact" in outcome.value:
        return 0.10
    return 0.0


def _unit(value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError("value must be between zero and one")
