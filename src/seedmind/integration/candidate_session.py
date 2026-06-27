"""Live non-authoritative candidate comparison session."""

from __future__ import annotations

from dataclasses import dataclass

from seedmind.contracts import PrimitiveAction
from seedmind.curiosity import CuriosityConfig, CuriositySubsystem
from seedmind.environment import DynamicNurseryScenarioFactory, NurseryRuntime
from seedmind.integration.bounded_advice import AdviceConfig, AdviceDecision, BoundedAdvicePolicy
from seedmind.integration.comparison_oracle import CandidateComparison, NurseryOutcomeOracle
from seedmind.integration.developmental_signals import LiveDevelopmentalSignalProvider
from seedmind.integration.unified_shadow import NDNRALiveShadowAdapter
from seedmind.training import OnlinePredictiveTrainer, collect_experience


@dataclass(frozen=True, slots=True)
class CandidateStep:
    step_index: int
    production_action: PrimitiveAction
    ndnra_action: PrimitiveAction | None
    decision: AdviceDecision
    comparison: CandidateComparison | None
    prediction_error: float


@dataclass(frozen=True, slots=True)
class CandidateSessionResult:
    steps: tuple[CandidateStep, ...]
    policy: BoundedAdvicePolicy

    @property
    def actions(self) -> tuple[PrimitiveAction, ...]:
        return tuple(step.production_action for step in self.steps)

    @property
    def prediction_errors(self) -> tuple[float, ...]:
        return tuple(step.prediction_error for step in self.steps)

    @property
    def decisions(self) -> tuple[AdviceDecision, ...]:
        return tuple(step.decision for step in self.steps)

    @property
    def comparisons(self) -> tuple[CandidateComparison, ...]:
        return tuple(step.comparison for step in self.steps if step.comparison is not None)


def run_candidate_session(
    *,
    scenario_factory: DynamicNurseryScenarioFactory,
    seed: int,
    curiosity_config: CuriosityConfig,
    shadow: NDNRALiveShadowAdapter,
    signal_provider: LiveDevelopmentalSignalProvider,
    trainer: OnlinePredictiveTrainer,
) -> CandidateSessionResult:
    scenario = scenario_factory.create(seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-candidate-comparison",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    signal_provider.begin_episode(runtime.episode_id)
    trainer.reset_episode()
    curiosity = CuriositySubsystem(curiosity_config)
    policy = BoundedAdvicePolicy(
        AdviceConfig(
            minimum_evidence=2,
            minimum_confidence=0.10,
            minimum_accessibility=0.10,
            maximum_risk=0.55,
            maximum_resource_cost=0.60,
            human_threshold=0.90,
        )
    )
    oracle = NurseryOutcomeOracle(scenario)
    steps: list[CandidateStep] = []

    while not curiosity.budget_exhausted:
        state_before = runtime.state
        observation = runtime.observe()
        pre_signals = signal_provider.current
        suggestion = shadow.suggest(observation, pre_signals, step_index=len(steps))
        selection = curiosity.select(observation.available_actions)
        decision = policy.evaluate(
            production_action=selection.selected_action,
            ndnra_action=suggestion.suggested_action,
            available_actions=observation.available_actions,
            signals=pre_signals,
            shadow=shadow,
        )
        comparison = None
        if (
            suggestion.suggested_action is not None
            and suggestion.suggested_action is not selection.selected_action
        ):
            comparison = oracle.compare(
                state=state_before,
                production_action=selection.selected_action,
                ndnra_action=suggestion.suggested_action,
                signals=pre_signals,
            )
            policy.observe_comparison(decision, ndnra_better=comparison.ndnra_better)
        experience = collect_experience(runtime, selection.selected_action)
        metrics = trainer.train_transition(experience)
        curiosity.observe(selection.selected_action, metrics.mean_absolute_error)
        signals = signal_provider.observe(experience, metrics, selection)
        shadow.observe_transition(experience, selection, signals)
        steps.append(
            CandidateStep(
                step_index=selection.step_index,
                production_action=selection.selected_action,
                ndnra_action=suggestion.suggested_action,
                decision=decision,
                comparison=comparison,
                prediction_error=metrics.mean_absolute_error,
            )
        )
        if experience.terminated:
            raise RuntimeError("candidate session terminated before budget exhaustion")

    trainer.reset_episode()
    return CandidateSessionResult(steps=tuple(steps), policy=policy)
