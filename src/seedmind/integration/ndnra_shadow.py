"""Non-authoritative NDNRA observation of the live SeedMind nursery loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from math import isfinite
from statistics import fmean
from typing import Protocol

from seedmind.contracts import ObservationPacket, PrimitiveAction
from seedmind.curiosity import (
    CuriosityConfig,
    CuriositySelection,
    CuriositySubsystem,
)
from seedmind.environment import NurseryRuntime, NurseryScenario
from seedmind.research.ndnra import (
    EffectNeed,
    EffectObservation,
    MultidimensionalExperienceGraph,
    NeedDimension,
    NeedDrivenComposer,
)
from seedmind.training import (
    ExperienceTransition,
    OnlinePredictiveTrainer,
    OnlineTrainingMetrics,
    collect_experience,
)


class ShadowScenarioFactory(Protocol):
    """Create a deterministic scenario for one shadow-mode session."""

    def create(self, seed: int) -> NurseryScenario:
        """Return one scenario for the supplied seed."""
        ...


@dataclass(frozen=True, slots=True)
class NDNRAShadowConfig:
    """Weights and bounds for non-authoritative developmental suggestions."""

    satisfaction_threshold: float = 0.01
    maximum_depth: int = 1
    prediction_error_scale: float = 1.0
    curiosity_value_weight: float = 1.0
    controllable_change_weight: float = 0.25
    ambition_relevance_weight: float = 0.20
    prediction_error_weight: float = 0.15
    resource_cost_weight: float = 0.20
    termination_risk_weight: float = 1.0

    def __post_init__(self) -> None:
        for name, value in (
            ("satisfaction_threshold", self.satisfaction_threshold),
            ("curiosity_value_weight", self.curiosity_value_weight),
            ("controllable_change_weight", self.controllable_change_weight),
            ("ambition_relevance_weight", self.ambition_relevance_weight),
            ("prediction_error_weight", self.prediction_error_weight),
            ("resource_cost_weight", self.resource_cost_weight),
            ("termination_risk_weight", self.termination_risk_weight),
        ):
            _validate_unit(name, value)
        if self.maximum_depth != 1:
            raise ValueError("shadow mode must suggest exactly one primitive action")
        if not isfinite(self.prediction_error_scale) or self.prediction_error_scale <= 0.0:
            raise ValueError("prediction_error_scale must be finite and positive")


@dataclass(frozen=True, slots=True)
class ShadowSuggestion:
    """One optional NDNRA action suggestion with no execution authority."""

    step_index: int
    suggested_action: PrimitiveAction | None
    score: float
    primary_satisfaction: float
    candidate_count: int
    learned_assembly_count: int
    effect_dimension_count: int
    has_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        if not isfinite(self.score):
            raise ValueError("score must be finite")
        if not isfinite(self.primary_satisfaction) or self.primary_satisfaction < 0.0:
            raise ValueError("primary_satisfaction must be finite and non-negative")
        if self.candidate_count < 0:
            raise ValueError("candidate_count must not be negative")
        if self.learned_assembly_count < 0 or self.effect_dimension_count < 0:
            raise ValueError("shadow graph counts must not be negative")
        if self.has_action_authority:
            raise ValueError("shadow suggestions must never have action authority")


@dataclass(frozen=True, slots=True)
class ShadowStepRecord:
    """One production action and its pre-action NDNRA shadow suggestion."""

    step_index: int
    actual_action: PrimitiveAction
    suggested_action: PrimitiveAction | None
    suggestion_matches_actual: bool
    suggestion_was_available: bool
    suggestion_was_valid: bool
    shadow_had_action_authority: bool
    prediction_error: float
    curiosity_value: float
    controllable_change: float
    external_change: float
    resource_cost: float
    human_signal_magnitude: float
    ambition_relevance: float
    learned_assembly_count: int
    effect_dimension_count: int

    def __post_init__(self) -> None:
        if self.step_index < 0:
            raise ValueError("step_index must not be negative")
        for name, value in (
            ("prediction_error", self.prediction_error),
            ("curiosity_value", self.curiosity_value),
            ("controllable_change", self.controllable_change),
            ("external_change", self.external_change),
            ("resource_cost", self.resource_cost),
            ("human_signal_magnitude", self.human_signal_magnitude),
            ("ambition_relevance", self.ambition_relevance),
        ):
            _validate_unit(name, value)
        if self.shadow_had_action_authority:
            raise ValueError("shadow mode must not have action authority")
        if self.suggestion_was_available != (self.suggested_action is not None):
            raise ValueError("suggestion availability does not match suggested_action")
        if self.suggestion_matches_actual != (
            self.suggested_action is not None and self.suggested_action is self.actual_action
        ):
            raise ValueError("suggestion match flag is inconsistent")
        if self.learned_assembly_count < 0 or self.effect_dimension_count < 0:
            raise ValueError("shadow graph counts must not be negative")


@dataclass(frozen=True, slots=True)
class NDNRAShadowSessionConfig:
    """Production curiosity settings plus one fixed ambition relevance signal."""

    seed: int = 7
    curiosity: CuriosityConfig = field(default_factory=CuriosityConfig)
    ambition_relevance: float = 0.0

    def __post_init__(self) -> None:
        if self.seed < 0:
            raise ValueError("seed must not be negative")
        _validate_unit("ambition_relevance", self.ambition_relevance)


@dataclass(frozen=True, slots=True)
class NDNRAShadowSessionResult:
    """Complete production timeline and non-authoritative shadow evidence."""

    scenario_id: str
    config: NDNRAShadowSessionConfig
    selections: tuple[CuriositySelection, ...]
    metrics: tuple[OnlineTrainingMetrics, ...]
    suggestions: tuple[ShadowSuggestion, ...]
    records: tuple[ShadowStepRecord, ...]
    learned_assembly_count: int
    effect_dimensions: tuple[str, ...]
    graph_snapshot: dict[str, object]

    def __post_init__(self) -> None:
        if not self.scenario_id.strip():
            raise ValueError("scenario_id must not be empty")
        expected = self.config.curiosity.play_budget
        lengths = {
            len(self.selections),
            len(self.metrics),
            len(self.suggestions),
            len(self.records),
        }
        if lengths != {expected}:
            raise ValueError("shadow result does not cover the complete play budget")
        if tuple(record.step_index for record in self.records) != tuple(range(expected)):
            raise ValueError("shadow record indices must be contiguous")
        if self.learned_assembly_count < 0:
            raise ValueError("learned_assembly_count must not be negative")
        if len(self.effect_dimensions) != len(set(self.effect_dimensions)):
            raise ValueError("effect_dimensions must be unique")

    @property
    def actual_actions(self) -> tuple[PrimitiveAction, ...]:
        return tuple(record.actual_action for record in self.records)

    @property
    def suggestion_count(self) -> int:
        return sum(record.suggestion_was_available for record in self.records)

    @property
    def suggestion_match_count(self) -> int:
        return sum(record.suggestion_matches_actual for record in self.records)

    @property
    def valid_suggestion_count(self) -> int:
        return sum(record.suggestion_was_valid for record in self.records)

    @property
    def authority_violation_count(self) -> int:
        return sum(record.shadow_had_action_authority for record in self.records)

    @property
    def effect_dimension_count(self) -> int:
        return len(self.effect_dimensions)


class NDNRAShadowAdapter:
    """Learn local action effects and suggest without controlling execution."""

    def __init__(
        self,
        config: NDNRAShadowConfig | None = None,
        *,
        graph: MultidimensionalExperienceGraph | None = None,
    ) -> None:
        self.config = NDNRAShadowConfig() if config is None else config
        self.graph = MultidimensionalExperienceGraph() if graph is None else graph

    def suggest(
        self,
        observation: ObservationPacket,
        *,
        step_index: int,
    ) -> ShadowSuggestion:
        """Return one optional suggestion using only previously learned effects."""
        if step_index < 0:
            raise ValueError("step_index must not be negative")
        available = tuple(
            action for action in observation.available_actions if action is not PrimitiveAction.STOP
        )
        current_facts = tuple(_availability_fact(action) for action in available)
        result = NeedDrivenComposer(
            self.graph,
            maximum_depth=self.config.maximum_depth,
        ).compose(
            need=self._developmental_need(),
            current_facts=current_facts,
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
            raise RuntimeError("NDNRA suggested an unavailable action")
        return ShadowSuggestion(
            step_index=step_index,
            suggested_action=action,
            score=selected.score,
            primary_satisfaction=selected.primary_satisfaction,
            candidate_count=len(result.candidates),
            learned_assembly_count=self.graph.assembly_count,
            effect_dimension_count=len(self.graph.effect_dimension_codes),
        )

    def observe_transition(
        self,
        experience: ExperienceTransition,
        metrics: OnlineTrainingMetrics,
        selection: CuriositySelection,
        *,
        ambition_relevance: float,
    ) -> dict[str, float]:
        """Convert one real transition into all locally observed effect dimensions."""
        _validate_unit("ambition_relevance", ambition_relevance)
        if selection.selected_action is not experience.action:
            raise ValueError("curiosity selection does not match executed action")
        effects = self._effect_values(
            experience,
            metrics,
            selection,
            ambition_relevance=ambition_relevance,
        )
        action = experience.action
        self.graph.learn_experience(
            assembly_id=_assembly_id(action),
            action_code=action.value,
            origin_need_code="nursery_shadow_observation",
            required_facts=(_availability_fact(action),),
            produced_facts=(f"experienced:{action.value}",),
            observed_effects=tuple(
                EffectObservation(effect_code, value, 1.0) for effect_code, value in effects.items()
            ),
        )
        return effects

    def _developmental_need(self) -> EffectNeed:
        dimensions = (
            NeedDimension(
                effect_code="curiosity_value",
                desired_direction=1.0,
                intensity=self.config.curiosity_value_weight,
            ),
            NeedDimension(
                effect_code="controllable_change",
                desired_direction=1.0,
                intensity=self.config.controllable_change_weight,
            ),
            NeedDimension(
                effect_code="ambition_relevance",
                desired_direction=1.0,
                intensity=self.config.ambition_relevance_weight,
            ),
            NeedDimension(
                effect_code="prediction_error",
                desired_direction=1.0,
                intensity=self.config.prediction_error_weight,
            ),
            NeedDimension(
                effect_code="resource_cost",
                desired_direction=-1.0,
                intensity=self.config.resource_cost_weight,
            ),
            NeedDimension(
                effect_code="termination_risk",
                desired_direction=-1.0,
                intensity=self.config.termination_risk_weight,
            ),
        )
        return EffectNeed(
            need_code="increase_developmental_information",
            primary_effect_code="curiosity_value",
            dimensions=dimensions,
            satisfaction_threshold=self.config.satisfaction_threshold,
        )

    def _effect_values(
        self,
        experience: ExperienceTransition,
        metrics: OnlineTrainingMetrics,
        selection: CuriositySelection,
        *,
        ambition_relevance: float,
    ) -> dict[str, float]:
        return {
            "curiosity_value": _clamp_unit(selection.selected_candidate.information_gain),
            "prediction_error": _clamp_unit(
                metrics.mean_absolute_error / self.config.prediction_error_scale
            ),
            "controllable_change": _mean_absolute(experience.controllable_sensor_change),
            "external_change": _mean_absolute(experience.external_sensor_change),
            "resource_cost": _resource_cost(experience),
            "human_signal_magnitude": _mean_absolute(experience.next_observation.human_signal),
            "ambition_relevance": ambition_relevance,
            "termination_risk": float(experience.terminated),
        }


class NDNRAShadowSession:
    """Run production curiosity while NDNRA observes and suggests in shadow."""

    def __init__(
        self,
        trainer: OnlinePredictiveTrainer,
        scenario_factory: ShadowScenarioFactory,
        config: NDNRAShadowSessionConfig,
        *,
        shadow: NDNRAShadowAdapter | None = None,
    ) -> None:
        self.trainer = trainer
        self.scenario_factory = scenario_factory
        self.config = config
        self.shadow = NDNRAShadowAdapter() if shadow is None else shadow
        self.scenario = scenario_factory.create(config.seed)
        if config.curiosity.play_budget > self.scenario.step_budget:
            raise ValueError("shadow play budget exceeds scenario step budget")

    def run(self) -> NDNRAShadowSessionResult:
        """Execute only production choices and record NDNRA comparisons."""
        curiosity = CuriositySubsystem(self.config.curiosity)
        runtime = NurseryRuntime(
            initial_state=self.scenario.initial_state,
            episode_id=f"{self.scenario.scenario_id}-ndnra-shadow",
            resource_state_provider=self.scenario.resource_state,
            world_processes=self.scenario.world_processes,
        )
        selections: list[CuriositySelection] = []
        metrics_history: list[OnlineTrainingMetrics] = []
        suggestions: list[ShadowSuggestion] = []
        records: list[ShadowStepRecord] = []
        self.trainer.reset_episode()

        while not curiosity.budget_exhausted:
            observation = runtime.observe()
            step_index = len(records)
            suggestion = self.shadow.suggest(observation, step_index=step_index)
            selection = curiosity.select(observation.available_actions)
            experience = collect_experience(runtime, selection.selected_action)
            metrics = self.trainer.train_transition(experience)
            curiosity.observe(selection.selected_action, metrics.mean_absolute_error)
            effects = self.shadow.observe_transition(
                experience,
                metrics,
                selection,
                ambition_relevance=self.config.ambition_relevance,
            )
            suggested_action = suggestion.suggested_action
            records.append(
                ShadowStepRecord(
                    step_index=step_index,
                    actual_action=selection.selected_action,
                    suggested_action=suggested_action,
                    suggestion_matches_actual=(
                        suggested_action is not None
                        and suggested_action is selection.selected_action
                    ),
                    suggestion_was_available=suggested_action is not None,
                    suggestion_was_valid=(
                        suggested_action is not None
                        and suggested_action in observation.available_actions
                    ),
                    shadow_had_action_authority=suggestion.has_action_authority,
                    prediction_error=effects["prediction_error"],
                    curiosity_value=effects["curiosity_value"],
                    controllable_change=effects["controllable_change"],
                    external_change=effects["external_change"],
                    resource_cost=effects["resource_cost"],
                    human_signal_magnitude=effects["human_signal_magnitude"],
                    ambition_relevance=effects["ambition_relevance"],
                    learned_assembly_count=self.shadow.graph.assembly_count,
                    effect_dimension_count=len(self.shadow.graph.effect_dimension_codes),
                )
            )
            selections.append(selection)
            metrics_history.append(metrics)
            suggestions.append(suggestion)
            if experience.terminated:
                raise RuntimeError("shadow session terminated before budget exhaustion")

        self.trainer.reset_episode()
        return NDNRAShadowSessionResult(
            scenario_id=self.scenario.scenario_id,
            config=self.config,
            selections=tuple(selections),
            metrics=tuple(metrics_history),
            suggestions=tuple(suggestions),
            records=tuple(records),
            learned_assembly_count=self.shadow.graph.assembly_count,
            effect_dimensions=self.shadow.graph.effect_dimension_codes,
            graph_snapshot=self.shadow.graph.snapshot(),
        )


def _availability_fact(action: PrimitiveAction) -> str:
    return f"available:{action.value}"


def _assembly_id(action: PrimitiveAction) -> str:
    return f"assembly:shadow:{action.value}"


def _mean_absolute(values: tuple[float, ...]) -> float:
    if not values:
        return 0.0
    return _clamp_unit(fmean(abs(value) for value in values))


def _resource_cost(experience: ExperienceTransition) -> float:
    source = experience.observation.resource_state
    destination = experience.next_observation.resource_state
    if not source:
        return 0.0
    return _clamp_unit(
        fmean(
            max(0.0, source_value - destination_value)
            for source_value, destination_value in zip(
                source,
                destination,
                strict=True,
            )
        )
    )


def _clamp_unit(value: float) -> float:
    if not isfinite(value):
        raise ValueError("effect value must be finite")
    return max(0.0, min(1.0, value))


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
