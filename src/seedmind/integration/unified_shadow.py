"""Unified non-authoritative NDNRA shadow session with live developmental signals."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.curiosity import CuriosityConfig, CuriositySelection, CuriositySubsystem
from seedmind.environment import NurseryRuntime
from seedmind.integration.developmental_signals import (
    LiveDevelopmentalSignalProvider,
    LiveDevelopmentalSignals,
)
from seedmind.integration.ndnra_shadow import ShadowScenarioFactory, ShadowSuggestion
from seedmind.research.ndnra import (
    AdaptiveUpdate,
    ContextSignature,
    EffectNeed,
    EffectObservation,
    EventIdentity,
    MultidimensionalExperienceGraph,
    NDNRAGrowthState,
    NDNRARuntimeAdaptiveState,
    NeedDimension,
    NeedDrivenComposer,
)
from seedmind.training import (
    ExperienceTransition,
    OnlinePredictiveTrainer,
    OnlineTrainingMetrics,
    collect_experience,
)


@dataclass(frozen=True, slots=True)
class UnifiedShadowConfig:
    """Bounded production curiosity and one-action shadow suggestion settings."""

    seed: int = 7
    curiosity: CuriosityConfig = field(default_factory=CuriosityConfig)
    satisfaction_threshold: float = 0.01
    maximum_depth: int = 1

    def __post_init__(self) -> None:
        if self.seed < 0:
            raise ValueError("seed must not be negative")
        if not 0.0 <= self.satisfaction_threshold <= 1.0:
            raise ValueError("satisfaction_threshold must be between zero and one")
        if self.maximum_depth != 1:
            raise ValueError("unified shadow mode must remain one-action and non-authoritative")


@dataclass(frozen=True, slots=True)
class UnifiedShadowStepRecord:
    """One production transition with live signals and adaptive NDNRA evidence."""

    step_index: int
    actual_action: PrimitiveAction
    suggested_action: PrimitiveAction | None
    suggestion_valid: bool
    suggestion_matches_actual: bool
    shadow_had_action_authority: bool
    pre_ambition_relevance: float
    post_ambition_relevance: float
    curiosity_learning_progress: float
    self_controllability: float
    body_confidence: float
    help_requested: float
    human_approval: float
    human_correction: float
    human_demonstration: float
    prediction_error: float
    resource_pressure: float
    need_resolution: float
    selected_memory_accessibility: float
    pressure_before: float
    pressure_after: float
    attempt_count_before: int
    attempt_count_after: int
    eligibility_before: float
    eligibility_after: float
    dormancy_before: float
    dormancy_after: float

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        for name, value in (
            ("pre_ambition_relevance", self.pre_ambition_relevance),
            ("post_ambition_relevance", self.post_ambition_relevance),
            ("curiosity_learning_progress", self.curiosity_learning_progress),
            ("self_controllability", self.self_controllability),
            ("body_confidence", self.body_confidence),
            ("help_requested", self.help_requested),
            ("human_approval", self.human_approval),
            ("human_correction", self.human_correction),
            ("human_demonstration", self.human_demonstration),
            ("prediction_error", self.prediction_error),
            ("resource_pressure", self.resource_pressure),
            ("need_resolution", self.need_resolution),
            ("selected_memory_accessibility", self.selected_memory_accessibility),
            ("pressure_before", self.pressure_before),
            ("pressure_after", self.pressure_after),
            ("eligibility_before", self.eligibility_before),
            ("eligibility_after", self.eligibility_after),
            ("dormancy_before", self.dormancy_before),
            ("dormancy_after", self.dormancy_after),
        ):
            _validate_unit(name, value)
        if self.shadow_had_action_authority:
            raise ValueError("unified shadow mode must not have action authority")
        if self.suggestion_matches_actual != (
            self.suggested_action is not None and self.suggested_action is self.actual_action
        ):
            raise ValueError("suggestion match flag is inconsistent")
        if self.attempt_count_after != self.attempt_count_before + 1:
            raise ValueError("adaptive attempt count must advance by one")


@dataclass(frozen=True, slots=True)
class UnifiedShadowResult:
    """Complete live-signal timeline and final operational adaptive state."""

    scenario_id: str
    config: UnifiedShadowConfig
    selections: tuple[CuriositySelection, ...]
    metrics: tuple[OnlineTrainingMetrics, ...]
    suggestions: tuple[ShadowSuggestion, ...]
    signals: tuple[LiveDevelopmentalSignals, ...]
    records: tuple[UnifiedShadowStepRecord, ...]
    final_growth_state: NDNRAGrowthState
    graph_snapshot: dict[str, object]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        expected = self.config.curiosity.play_budget
        lengths = {
            len(self.selections),
            len(self.metrics),
            len(self.suggestions),
            len(self.signals),
            len(self.records),
        }
        if lengths != {expected}:
            raise ValueError("unified shadow result must cover the complete play budget")

    @property
    def actual_actions(self) -> tuple[PrimitiveAction, ...]:
        return tuple(record.actual_action for record in self.records)

    @property
    def authority_violation_count(self) -> int:
        return sum(record.shadow_had_action_authority for record in self.records)

    @property
    def valid_suggestion_count(self) -> int:
        return sum(record.suggestion_valid for record in self.records)

    @property
    def suggestion_count(self) -> int:
        return sum(record.suggested_action is not None for record in self.records)


class NDNRALiveShadowAdapter:
    """Use live needs and operational adaptive state without selecting actions."""

    def __init__(
        self,
        *,
        graph: MultidimensionalExperienceGraph | None = None,
        growth_state: NDNRAGrowthState | None = None,
        satisfaction_threshold: float = 0.01,
        record_contextual_memory: bool = True,
    ) -> None:
        if not 0.0 <= satisfaction_threshold <= 1.0:
            raise ValueError("satisfaction_threshold must be between zero and one")
        self.graph = MultidimensionalExperienceGraph() if graph is None else graph
        self.adaptive = NDNRARuntimeAdaptiveState.from_growth_state(
            self.graph,
            growth_state,
        )
        self.satisfaction_threshold = satisfaction_threshold
        self.record_contextual_memory = record_contextual_memory

    @property
    def growth_state(self) -> NDNRAGrowthState:
        return self.adaptive.to_growth_state()

    def suggest(
        self,
        observation: ObservationPacket,
        signals: LiveDevelopmentalSignals,
        *,
        step_index: int,
    ) -> ShadowSuggestion:
        """Recruit accessible local effects under the current live need frame."""
        available = tuple(
            action for action in observation.available_actions if action is not PrimitiveAction.STOP
        )
        result = NeedDrivenComposer(
            self.graph,
            maximum_depth=1,
            accessibility=self.adaptive.accessibility_map(),
        ).compose(
            need=self._developmental_need(signals),
            current_facts=tuple(_availability_fact(action) for action in available),
        )
        selected = result.selected
        if selected is None:
            return ShadowSuggestion(
                step_index=step_index,
                suggested_action=None,
                score=0.0,
                primary_satisfaction=0.0,
                candidate_count=0,
                learned_assembly_count=self.graph.assembly_count,
                effect_dimension_count=len(self.graph.effect_dimension_codes),
            )
        action = PrimitiveAction(selected.actions[0])
        if action not in available:
            raise RuntimeError("live NDNRA suggested an unavailable action")
        return ShadowSuggestion(
            step_index=step_index,
            suggested_action=action,
            score=selected.score,
            primary_satisfaction=selected.primary_satisfaction,
            candidate_count=len(result.candidates),
            learned_assembly_count=self.graph.assembly_count,
            effect_dimension_count=len(self.graph.effect_dimension_codes),
        )

    def evaluate_action(
        self,
        action: PrimitiveAction,
        signals: LiveDevelopmentalSignals,
    ) -> tuple[float, float]:
        """Return one action's accessibility and need-aligned local score."""
        assembly_id = _assembly_id(action)
        try:
            self.graph.assembly(assembly_id)
        except ValueError:
            return 0.0, 0.0
        accessibility = self.adaptive.accessibility(assembly_id)
        effects = self.graph.project_effects(
            (assembly_id,),
            accessibility=self.adaptive.accessibility_map(),
        )
        score = self._developmental_need(signals).score_projected_effects(effects) - 0.01
        return accessibility, score

    def observe_transition(
        self,
        experience: ExperienceTransition,
        selection: CuriositySelection,
        signals: LiveDevelopmentalSignals,
    ) -> AdaptiveUpdate:
        """Learn all live consequences and continue restored adaptive state."""
        if selection.selected_action is not experience.action:
            raise ValueError("selection action does not match executed transition")
        assembly_id = _assembly_id(experience.action)
        predicted_resolution = self._predicted_effect(
            assembly_id,
            "need_resolution",
        )
        observed_effects = tuple(
            EffectObservation(effect_code, value, 1.0)
            for effect_code, value in signals.values().items()
        )
        if self.record_contextual_memory:
            identity = EventIdentity(
                source_code="nursery_runtime",
                episode_id=experience.observation.episode_id,
                step_id=experience.observation.step_id,
            )
            self.graph.learn_contextual_experience(
                identity=identity,
                correlation_group_id=identity.key,
                assembly_id=assembly_id,
                route_id=assembly_id,
                action_code=experience.action.value,
                origin_need_code="live_developmental_shadow",
                required_facts=(_availability_fact(experience.action),),
                produced_facts=(f"experienced:{experience.action.value}",),
                context_signature=ContextSignature.from_values(
                    active_need_code="live_developmental_growth",
                    sensor_values=experience.observation.sensor_values,
                    available_action_codes=(
                        action.value for action in experience.observation.available_actions
                    ),
                    human_values=experience.observation.human_signal,
                    resource_values=experience.observation.resource_state,
                ),
                observed_effects=observed_effects,
            )
        else:
            self.graph.learn_experience(
                assembly_id=assembly_id,
                action_code=experience.action.value,
                origin_need_code="live_developmental_shadow",
                required_facts=(_availability_fact(experience.action),),
                produced_facts=(f"experienced:{experience.action.value}",),
                observed_effects=observed_effects,
            )
        available_count = sum(
            action is not PrimitiveAction.STOP
            for action in experience.observation.available_actions
        )
        capacity_saturation = min(
            1.0,
            self.graph.assembly_count / max(available_count, 1),
        )
        residual = max(-1.0, min(1.0, signals.need_resolution - predicted_resolution))
        return self.adaptive.observe(
            assembly_id=assembly_id,
            unresolved_error=signals.prediction_error,
            curiosity=signals.curiosity_value,
            ambition_relevance=signals.ambition_relevance,
            capacity_saturation=capacity_saturation,
            residual_effect=residual,
        )

    def _predicted_effect(self, assembly_id: str, effect_code: str) -> float:
        try:
            assembly = self.graph.assembly(assembly_id)
        except ValueError:
            return 0.0
        estimate = assembly.effect_memory.estimate(effect_code)
        if estimate is None:
            return 0.0
        return estimate.value * estimate.confidence * self.adaptive.accessibility(assembly_id)

    def _developmental_need(self, signals: LiveDevelopmentalSignals) -> EffectNeed:
        return EffectNeed(
            need_code="live_developmental_growth",
            primary_effect_code="curiosity_value",
            dimensions=(
                NeedDimension(
                    "curiosity_value",
                    1.0,
                    _positive_intensity(signals.curiosity_value),
                ),
                NeedDimension(
                    "curiosity_learning_progress",
                    1.0,
                    _positive_intensity(signals.curiosity_learning_progress),
                ),
                NeedDimension(
                    "self_controllability",
                    1.0,
                    _positive_intensity(1.0 - signals.self_controllability),
                ),
                NeedDimension(
                    "ambition_relevance",
                    1.0,
                    _positive_intensity(signals.ambition_relevance),
                ),
                NeedDimension(
                    "human_approval",
                    1.0,
                    _positive_intensity(0.25 + signals.help_requested),
                ),
                NeedDimension(
                    "need_resolution",
                    1.0,
                    _positive_intensity(1.0 - signals.need_resolution),
                ),
                NeedDimension(
                    "prediction_error",
                    1.0,
                    _positive_intensity(signals.prediction_error),
                ),
                NeedDimension(
                    "resource_pressure",
                    -1.0,
                    _positive_intensity(signals.resource_pressure),
                ),
            ),
            satisfaction_threshold=self.satisfaction_threshold,
        )


class UnifiedDevelopmentalShadowSession:
    """Run production curiosity with unified live NDNRA evidence in shadow."""

    def __init__(
        self,
        trainer: OnlinePredictiveTrainer,
        scenario_factory: ShadowScenarioFactory,
        config: UnifiedShadowConfig,
        *,
        signal_provider: LiveDevelopmentalSignalProvider,
        shadow: NDNRALiveShadowAdapter | None = None,
    ) -> None:
        self.trainer = trainer
        self.config = config
        self.scenario = scenario_factory.create(config.seed)
        self.signal_provider = signal_provider
        self.shadow = (
            NDNRALiveShadowAdapter(satisfaction_threshold=config.satisfaction_threshold)
            if shadow is None
            else shadow
        )
        if config.curiosity.play_budget > self.scenario.step_budget:
            raise ValueError("unified shadow budget exceeds scenario step budget")

    def run(self) -> UnifiedShadowResult:
        """Execute production actions while all integrated systems remain observers."""
        curiosity = CuriositySubsystem(self.config.curiosity)
        runtime = NurseryRuntime(
            initial_state=self.scenario.initial_state,
            episode_id=f"{self.scenario.scenario_id}-unified-shadow",
            resource_state_provider=self.scenario.resource_state,
            world_processes=self.scenario.world_processes,
        )
        self.signal_provider.begin_episode(runtime.episode_id)
        selections: list[CuriositySelection] = []
        metrics_history: list[OnlineTrainingMetrics] = []
        suggestions: list[ShadowSuggestion] = []
        signal_history: list[LiveDevelopmentalSignals] = []
        records: list[UnifiedShadowStepRecord] = []
        self.trainer.reset_episode()

        while not curiosity.budget_exhausted:
            observation = runtime.observe()
            step_index = len(records)
            pre_signals = self.signal_provider.current
            suggestion = self.shadow.suggest(
                observation,
                pre_signals,
                step_index=step_index,
            )
            selection = curiosity.select(observation.available_actions)
            experience = collect_experience(runtime, selection.selected_action)
            metrics = self.trainer.train_transition(experience)
            curiosity.observe(selection.selected_action, metrics.mean_absolute_error)
            signals = self.signal_provider.observe(experience, metrics, selection)
            suggested_action = suggestion.suggested_action
            selected_accessibility = (
                self.shadow.adaptive.accessibility(_assembly_id(suggested_action))
                if suggested_action is not None
                else 0.0
            )
            update = self.shadow.observe_transition(experience, selection, signals)
            records.append(
                UnifiedShadowStepRecord(
                    step_index=step_index,
                    actual_action=selection.selected_action,
                    suggested_action=suggested_action,
                    suggestion_valid=(
                        suggested_action is not None
                        and suggested_action in observation.available_actions
                    ),
                    suggestion_matches_actual=(
                        suggested_action is not None
                        and suggested_action is selection.selected_action
                    ),
                    shadow_had_action_authority=suggestion.has_action_authority,
                    pre_ambition_relevance=pre_signals.ambition_relevance,
                    post_ambition_relevance=signals.ambition_relevance,
                    curiosity_learning_progress=signals.curiosity_learning_progress,
                    self_controllability=signals.self_controllability,
                    body_confidence=signals.body_confidence,
                    help_requested=signals.help_requested,
                    human_approval=signals.human_approval,
                    human_correction=signals.human_correction,
                    human_demonstration=signals.human_demonstration,
                    prediction_error=signals.prediction_error,
                    resource_pressure=signals.resource_pressure,
                    need_resolution=signals.need_resolution,
                    selected_memory_accessibility=selected_accessibility,
                    pressure_before=update.pressure_before,
                    pressure_after=update.pressure_after,
                    attempt_count_before=update.attempt_count_before,
                    attempt_count_after=update.attempt_count_after,
                    eligibility_before=update.eligibility_before,
                    eligibility_after=update.eligibility_after,
                    dormancy_before=update.dormancy_before,
                    dormancy_after=update.dormancy_after,
                )
            )
            selections.append(selection)
            metrics_history.append(metrics)
            suggestions.append(suggestion)
            signal_history.append(signals)
            if experience.terminated:
                raise RuntimeError("unified shadow session terminated before budget exhaustion")

        self.trainer.reset_episode()
        return UnifiedShadowResult(
            scenario_id=self.scenario.scenario_id,
            config=self.config,
            selections=tuple(selections),
            metrics=tuple(metrics_history),
            suggestions=tuple(suggestions),
            signals=tuple(signal_history),
            records=tuple(records),
            final_growth_state=self.shadow.growth_state,
            graph_snapshot=self.shadow.graph.snapshot(),
        )


def _assembly_id(action: PrimitiveAction) -> str:
    return f"assembly:shadow:{action.value}"


def _availability_fact(action: PrimitiveAction) -> str:
    return f"available:{action.value}"


def _positive_intensity(value: float) -> float:
    return max(0.01, min(1.0, value))


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
