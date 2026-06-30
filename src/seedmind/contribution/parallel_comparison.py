"""Default SeedMind versus NDNRA comparison for Week 9 contribution."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from math import isfinite
from statistics import fmean

from seedmind.contracts import PrimitiveAction
from seedmind.contribution.contracts import ContributionRecord
from seedmind.curiosity import CuriosityCandidate, CuriositySelection
from seedmind.environment import (
    NurseryRuntime,
    NurseryScenario,
    NurseryState,
    NurseryTransitionEngine,
    WorldProcessPipeline,
)
from seedmind.integration.comparison_oracle import CandidateOutcome, NurseryOutcomeOracle
from seedmind.integration.developmental_signals import LiveDevelopmentalSignals
from seedmind.integration.ndnra_shadow import NDNRAShadowAdapter
from seedmind.training import ExperienceTransition, OnlineTrainingMetrics, collect_experience


@dataclass(frozen=True, slots=True)
class Week9ComparisonStep:
    """One same-state Default and NDNRA candidate comparison."""

    contribution_id: str
    scenario_id: str
    scenario_context: str
    step_index: int
    scenario_step_index: int
    default_action: PrimitiveAction
    ndnra_action: PrimitiveAction | None
    ndnra_abstained: bool
    agreement: bool
    disagreement: bool
    compared: bool
    default_executed: bool
    ndnra_executed: bool
    default_oracle_score: float | None
    ndnra_oracle_score: float | None
    default_goal_progress: float | None
    ndnra_goal_progress: float | None
    default_combined_score: float | None
    ndnra_combined_score: float | None
    ndnra_advantage: float | None
    winner: str
    default_resource_cost: float | None
    ndnra_resource_cost: float | None
    target_achieved_after_default: bool
    ndnra_suggestion_score: float
    ndnra_candidate_count: int
    learned_assembly_count: int
    effect_dimension_count: int
    authority_violation: bool = False

    def __post_init__(self) -> None:
        if self.step_index < 0 or self.scenario_step_index < 0:
            raise ValueError("comparison step indices must not be negative")
        if self.default_executed is not True or self.ndnra_executed:
            raise ValueError("only the Default action may execute in the parallel comparison")
        if self.ndnra_abstained != (self.ndnra_action is None):
            raise ValueError("NDNRA abstention flag is inconsistent")
        if self.agreement != (
            self.ndnra_action is not None and self.ndnra_action is self.default_action
        ):
            raise ValueError("agreement flag is inconsistent")
        if self.disagreement != (
            self.ndnra_action is not None and self.ndnra_action is not self.default_action
        ):
            raise ValueError("disagreement flag is inconsistent")
        if self.compared != (self.ndnra_action is not None):
            raise ValueError("every NDNRA proposal must be scored")
        if self.authority_violation:
            raise ValueError("NDNRA comparison cannot carry production authority")
        if self.learned_assembly_count < 0 or self.effect_dimension_count < 0:
            raise ValueError("NDNRA graph counts must not be negative")
        if self.ndnra_candidate_count < 0 or not isfinite(self.ndnra_suggestion_score):
            raise ValueError("NDNRA suggestion evidence is invalid")
        if self.compared:
            values = (
                self.default_oracle_score,
                self.ndnra_oracle_score,
                self.default_goal_progress,
                self.ndnra_goal_progress,
                self.default_combined_score,
                self.ndnra_combined_score,
                self.ndnra_advantage,
                self.default_resource_cost,
                self.ndnra_resource_cost,
            )
            if any(value is None or not isfinite(value) for value in values):
                raise ValueError("scored comparisons require complete finite values")
            if self.winner not in {"default", "ndnra", "tie"}:
                raise ValueError("scored comparison winner is invalid")
        elif self.winner != "not_compared":
            raise ValueError("abstentions must be marked not_compared")

    def to_json(self) -> dict[str, object]:
        return {
            "agreement": self.agreement,
            "authority_violation": self.authority_violation,
            "compared": self.compared,
            "contribution_id": self.contribution_id,
            "default_action": self.default_action.value,
            "default_combined_score": self.default_combined_score,
            "default_executed": self.default_executed,
            "default_goal_progress": self.default_goal_progress,
            "default_oracle_score": self.default_oracle_score,
            "default_resource_cost": self.default_resource_cost,
            "disagreement": self.disagreement,
            "effect_dimension_count": self.effect_dimension_count,
            "learned_assembly_count": self.learned_assembly_count,
            "ndnra_abstained": self.ndnra_abstained,
            "ndnra_action": None if self.ndnra_action is None else self.ndnra_action.value,
            "ndnra_advantage": self.ndnra_advantage,
            "ndnra_candidate_count": self.ndnra_candidate_count,
            "ndnra_combined_score": self.ndnra_combined_score,
            "ndnra_executed": self.ndnra_executed,
            "ndnra_goal_progress": self.ndnra_goal_progress,
            "ndnra_oracle_score": self.ndnra_oracle_score,
            "ndnra_resource_cost": self.ndnra_resource_cost,
            "ndnra_suggestion_score": self.ndnra_suggestion_score,
            "scenario_context": self.scenario_context,
            "scenario_id": self.scenario_id,
            "scenario_step_index": self.scenario_step_index,
            "step_index": self.step_index,
            "target_achieved_after_default": self.target_achieved_after_default,
            "winner": self.winner,
        }


@dataclass(frozen=True, slots=True)
class Week9ScenarioComparison:
    """Aggregate candidate evidence for one contribution scenario."""

    contribution_id: str
    scenario_id: str
    default_task_success: bool
    production_steps: int
    ndnra_proposals: int
    ndnra_abstentions: int
    agreements: int
    disagreements: int
    default_better: int
    ndnra_better: int
    ties: int

    def to_json(self) -> dict[str, object]:
        return {
            "agreements": self.agreements,
            "contribution_id": self.contribution_id,
            "default_better": self.default_better,
            "default_task_success": self.default_task_success,
            "disagreements": self.disagreements,
            "ndnra_abstentions": self.ndnra_abstentions,
            "ndnra_better": self.ndnra_better,
            "ndnra_proposals": self.ndnra_proposals,
            "production_steps": self.production_steps,
            "scenario_id": self.scenario_id,
            "ties": self.ties,
        }


@dataclass(frozen=True, slots=True)
class Week9NDNRARollout:
    """One isolated NDNRA-only task rollout after shadow learning."""

    contribution_id: str
    scenario_id: str
    success: bool
    executed_steps: int
    abstained: bool
    terminated: bool

    def to_json(self) -> dict[str, object]:
        return {
            "abstained": self.abstained,
            "contribution_id": self.contribution_id,
            "executed_steps": self.executed_steps,
            "scenario_id": self.scenario_id,
            "success": self.success,
            "terminated": self.terminated,
        }


@dataclass(frozen=True, slots=True)
class Week9ParallelComparisonReport:
    """Aggregate Default-vs-NDNRA evidence for Week 9."""

    total_scenarios: int
    total_production_steps: int
    default_proposal_count: int
    ndnra_observation_count: int
    ndnra_proposal_count: int
    ndnra_abstention_count: int
    agreement_count: int
    disagreement_count: int
    comparison_count: int
    disagreement_comparison_count: int
    disagreement_comparison_coverage: float
    default_better_count: int
    ndnra_better_count: int
    tied_count: int
    mean_default_combined_score: float
    mean_ndnra_combined_score: float
    mean_ndnra_advantage: float
    mean_default_resource_cost: float
    mean_ndnra_resource_cost: float
    default_task_successes: int
    default_task_success_rate: float
    ndnra_rollout_attempts: int
    ndnra_rollout_successes: int
    ndnra_rollout_success_rate: float
    ndnra_rollout_abstentions: int
    learned_assembly_count: int
    effect_dimension_count: int
    production_action_replacements: int
    authority_violations: int
    automatic_promotions: int

    def __post_init__(self) -> None:
        integer_values = (
            self.total_scenarios,
            self.total_production_steps,
            self.default_proposal_count,
            self.ndnra_observation_count,
            self.ndnra_proposal_count,
            self.ndnra_abstention_count,
            self.agreement_count,
            self.disagreement_count,
            self.comparison_count,
            self.disagreement_comparison_count,
            self.default_better_count,
            self.ndnra_better_count,
            self.tied_count,
            self.default_task_successes,
            self.ndnra_rollout_attempts,
            self.ndnra_rollout_successes,
            self.ndnra_rollout_abstentions,
            self.learned_assembly_count,
            self.effect_dimension_count,
            self.production_action_replacements,
            self.authority_violations,
            self.automatic_promotions,
        )
        if any(value < 0 for value in integer_values):
            raise ValueError("parallel comparison counts must not be negative")
        if self.default_proposal_count != self.total_production_steps:
            raise ValueError("Default must propose every production step")
        if self.ndnra_observation_count != self.total_production_steps:
            raise ValueError("NDNRA must observe every production step")
        if self.ndnra_proposal_count + self.ndnra_abstention_count != self.total_production_steps:
            raise ValueError("NDNRA proposals and abstentions must cover every step")
        if self.agreement_count + self.disagreement_count != self.ndnra_proposal_count:
            raise ValueError("NDNRA proposals must be agreements or disagreements")
        if self.comparison_count != self.ndnra_proposal_count:
            raise ValueError("every NDNRA proposal must have comparative scores")
        if self.disagreement_comparison_count != self.disagreement_count:
            raise ValueError("every disagreement must be compared")
        if (
            self.default_better_count + self.ndnra_better_count + self.tied_count
            != self.comparison_count
        ):
            raise ValueError("comparison winners must cover all scored proposals")
        if self.ndnra_rollout_attempts != self.total_scenarios:
            raise ValueError("NDNRA isolated rollouts must cover every scenario")
        if (
            self.production_action_replacements
            or self.authority_violations
            or self.automatic_promotions
        ):
            raise ValueError("parallel comparison must remain non-authoritative")
        for value in (
            self.disagreement_comparison_coverage,
            self.default_task_success_rate,
            self.ndnra_rollout_success_rate,
        ):
            if not 0.0 <= value <= 1.0:
                raise ValueError("comparison rates must be between zero and one")
        for value in (
            self.mean_default_combined_score,
            self.mean_ndnra_combined_score,
            self.mean_ndnra_advantage,
            self.mean_default_resource_cost,
            self.mean_ndnra_resource_cost,
        ):
            if not isfinite(value):
                raise ValueError("comparison means must be finite")

    @property
    def pass_gate(self) -> bool:
        return (
            self.total_production_steps > 0
            and self.ndnra_proposal_count > 0
            and self.ndnra_rollout_attempts == self.total_scenarios
            and self.default_proposal_count == self.total_production_steps
            and self.ndnra_observation_count == self.total_production_steps
            and self.disagreement_comparison_coverage == 1.0
            and self.production_action_replacements == 0
            and self.authority_violations == 0
            and self.automatic_promotions == 0
        )

    def to_json(self) -> dict[str, object]:
        return {
            "agreement_count": self.agreement_count,
            "authority_violations": self.authority_violations,
            "automatic_promotions": self.automatic_promotions,
            "comparison_count": self.comparison_count,
            "default_better_count": self.default_better_count,
            "default_proposal_count": self.default_proposal_count,
            "default_task_success_rate": self.default_task_success_rate,
            "default_task_successes": self.default_task_successes,
            "disagreement_comparison_count": self.disagreement_comparison_count,
            "disagreement_comparison_coverage": self.disagreement_comparison_coverage,
            "disagreement_count": self.disagreement_count,
            "effect_dimension_count": self.effect_dimension_count,
            "learned_assembly_count": self.learned_assembly_count,
            "mean_default_combined_score": self.mean_default_combined_score,
            "mean_default_resource_cost": self.mean_default_resource_cost,
            "mean_ndnra_advantage": self.mean_ndnra_advantage,
            "mean_ndnra_combined_score": self.mean_ndnra_combined_score,
            "mean_ndnra_resource_cost": self.mean_ndnra_resource_cost,
            "ndnra_abstention_count": self.ndnra_abstention_count,
            "ndnra_better_count": self.ndnra_better_count,
            "ndnra_observation_count": self.ndnra_observation_count,
            "ndnra_proposal_count": self.ndnra_proposal_count,
            "ndnra_rollout_abstentions": self.ndnra_rollout_abstentions,
            "ndnra_rollout_attempts": self.ndnra_rollout_attempts,
            "ndnra_rollout_success_rate": self.ndnra_rollout_success_rate,
            "ndnra_rollout_successes": self.ndnra_rollout_successes,
            "pass_gate": self.pass_gate,
            "production_action_replacements": self.production_action_replacements,
            "tied_count": self.tied_count,
            "total_production_steps": self.total_production_steps,
            "total_scenarios": self.total_scenarios,
        }


@dataclass(frozen=True, slots=True)
class Week9ParallelComparisonResult:
    """Complete same-state and isolated-rollout comparison evidence."""

    steps: tuple[Week9ComparisonStep, ...]
    scenarios: tuple[Week9ScenarioComparison, ...]
    ndnra_rollouts: tuple[Week9NDNRARollout, ...]
    report: Week9ParallelComparisonReport

    def to_json(self) -> dict[str, object]:
        return {
            "method": {
                "comparison_execution": "deterministic replay of the exact Default action trace",
                "default_production_authority": True,
                "ndnra_production_authority": False,
                "ndnra_rollout_isolated": True,
                "same_pre_action_state": True,
                "scoring": "0.70 target progress + 0.30 existing nursery outcome oracle score",
            },
            "ndnra_rollouts": [rollout.to_json() for rollout in self.ndnra_rollouts],
            "scenario_summaries": [scenario.to_json() for scenario in self.scenarios],
            "steps": [step.to_json() for step in self.steps],
            "summary": self.report.to_json(),
        }


def run_week9_parallel_comparison(
    *,
    records: tuple[ContributionRecord, ...],
    scenarios: tuple[NurseryScenario, ...],
    shadow: NDNRAShadowAdapter | None = None,
) -> Week9ParallelComparisonResult:
    """Replay exact Default traces with same-state NDNRA proposals and scoring."""
    if len(records) != len(scenarios):
        raise ValueError("records and scenarios must have equal lengths")
    resolved_shadow = NDNRAShadowAdapter() if shadow is None else shadow
    steps: list[Week9ComparisonStep] = []
    scenario_summaries: list[Week9ScenarioComparison] = []
    global_step = 0

    for record, scenario in zip(records, scenarios, strict=True):
        if record.scenario_id != scenario.scenario_id:
            raise ValueError("record and comparison scenario identities differ")
        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=f"{record.contribution_id}-parallel-comparison",
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )
        oracle = NurseryOutcomeOracle(scenario)
        scenario_steps: list[Week9ComparisonStep] = []
        for scenario_step, action_code in enumerate(record.action_trace):
            default_action = PrimitiveAction(action_code)
            state_before = runtime.state
            observation = runtime.observe()
            if default_action not in observation.available_actions:
                raise ValueError(
                    "recorded Default action is unavailable during deterministic replay"
                )
            suggestion = resolved_shadow.suggest(observation, step_index=global_step)
            ndnra_action = suggestion.suggested_action
            signals = _comparison_signals(global_step, observation.resource_state)
            scored = None
            if ndnra_action is not None:
                scored = _score_candidates(
                    scenario=scenario,
                    state=state_before,
                    default_action=default_action,
                    ndnra_action=ndnra_action,
                    signals=signals,
                    oracle=oracle,
                    target_object_id=record.request.target_object_id,
                    target_id=record.request.target_id,
                )
            experience = collect_experience(runtime, default_action)
            selection = _selection_for_action(
                step_index=global_step,
                action=default_action,
                remaining_budget=max(0, len(record.action_trace) - scenario_step - 1),
                experience=experience,
            )
            resolved_shadow.observe_transition(
                experience,
                _metrics_for_experience(experience),
                selection,
                ambition_relevance=1.0,
            )
            target_achieved = _target_achieved(
                runtime.state,
                record.request.target_object_id,
                record.request.target_id,
            )
            step = _build_step(
                record=record,
                scenario_step=scenario_step,
                global_step=global_step,
                default_action=default_action,
                ndnra_action=ndnra_action,
                suggestion_score=suggestion.score,
                candidate_count=suggestion.candidate_count,
                learned_assembly_count=resolved_shadow.graph.assembly_count,
                effect_dimension_count=len(resolved_shadow.graph.effect_dimension_codes),
                scored=scored,
                target_achieved=target_achieved,
            )
            steps.append(step)
            scenario_steps.append(step)
            global_step += 1
        scenario_summaries.append(_scenario_summary(record, tuple(scenario_steps)))

    rollouts = _run_isolated_ndnra_rollouts(records, scenarios, resolved_shadow)
    report = _build_report(
        records=records,
        steps=tuple(steps),
        rollouts=rollouts,
        learned_assembly_count=resolved_shadow.graph.assembly_count,
        effect_dimension_count=len(resolved_shadow.graph.effect_dimension_codes),
    )
    return Week9ParallelComparisonResult(
        steps=tuple(steps),
        scenarios=tuple(scenario_summaries),
        ndnra_rollouts=rollouts,
        report=report,
    )


@dataclass(frozen=True, slots=True)
class _ScoredCandidates:
    default: CandidateOutcome
    ndnra: CandidateOutcome
    default_goal_progress: float
    ndnra_goal_progress: float
    default_combined_score: float
    ndnra_combined_score: float
    advantage: float
    winner: str


def _score_candidates(
    *,
    scenario: NurseryScenario,
    state: NurseryState,
    default_action: PrimitiveAction,
    ndnra_action: PrimitiveAction,
    signals: LiveDevelopmentalSignals,
    oracle: NurseryOutcomeOracle,
    target_object_id: str,
    target_id: str,
) -> _ScoredCandidates:
    default = oracle.evaluate(state, default_action, signals)
    ndnra = oracle.evaluate(state, ndnra_action, signals)
    default_progress = _goal_progress(scenario, state, default_action, target_object_id, target_id)
    ndnra_progress = _goal_progress(scenario, state, ndnra_action, target_object_id, target_id)
    default_score = _clamp_signed(0.70 * default_progress + 0.30 * default.score)
    ndnra_score = _clamp_signed(0.70 * ndnra_progress + 0.30 * ndnra.score)
    advantage = ndnra_score - default_score
    if advantage > 1e-12:
        winner = "ndnra"
    elif advantage < -1e-12:
        winner = "default"
    else:
        winner = "tie"
    return _ScoredCandidates(
        default=default,
        ndnra=ndnra,
        default_goal_progress=default_progress,
        ndnra_goal_progress=ndnra_progress,
        default_combined_score=default_score,
        ndnra_combined_score=ndnra_score,
        advantage=advantage,
        winner=winner,
    )


def _goal_progress(
    scenario: NurseryScenario,
    state: NurseryState,
    action: PrimitiveAction,
    target_object_id: str,
    target_id: str,
) -> float:
    before = _distance(state, target_object_id, target_id)
    transition = NurseryTransitionEngine().apply(state, action)
    after_state = transition.state
    if not after_state.terminated:
        after_state = WorldProcessPipeline(scenario.world_processes).advance(after_state).state
    after = _distance(after_state, target_object_id, target_id)
    if before == 0:
        return 0.0
    return _clamp_signed((before - after) / before)


def _distance(state: NurseryState, object_id: str, target_id: str) -> int:
    object_state = next(entity for entity in state.entities if entity.entity_id == object_id)
    target_state = next(entity for entity in state.entities if entity.entity_id == target_id)
    return abs(object_state.position.x - target_state.position.x) + abs(
        object_state.position.y - target_state.position.y
    )


def _target_achieved(state: NurseryState, object_id: str, target_id: str) -> bool:
    return (object_id, target_id) in state_target_pairs(state)


def state_target_pairs(state: NurseryState) -> tuple[tuple[str, str], ...]:
    objects = tuple(entity for entity in state.entities if entity.role.value == "object")
    targets = tuple(entity for entity in state.entities if entity.role.value == "target")
    return tuple(
        (object_state.entity_id, target_state.entity_id)
        for object_state in objects
        for target_state in targets
        if object_state.position == target_state.position
    )


def _selection_for_action(
    *,
    step_index: int,
    action: PrimitiveAction,
    remaining_budget: int,
    experience: ExperienceTransition,
) -> CuriositySelection:
    controllable = _mean_absolute(experience.controllable_sensor_change)
    external = _mean_absolute(experience.external_sensor_change)
    information_gain = min(1.0, 0.50 + 0.30 * controllable + 0.20 * external)
    candidate = CuriosityCandidate(
        action=action,
        sample_count=step_index,
        learning_progress=controllable,
        novelty=1.0 / (step_index + 1),
        uncertainty=max(0.0, 1.0 - controllable),
        information_gain=information_gain,
        repetition_penalty=0.0,
        stagnation_penalty=0.0,
        score=information_gain,
    )
    return CuriositySelection(
        step_index=step_index,
        selected_action=action,
        remaining_budget=remaining_budget,
        candidates=(candidate,),
    )


def _metrics_for_experience(experience: ExperienceTransition) -> OnlineTrainingMetrics:
    error = _mean_absolute(experience.sensor_change)
    return OnlineTrainingMetrics(
        episode_id=experience.observation.episode_id,
        source_step_id=experience.observation.step_id,
        total_loss=error,
        sensor_prediction_loss=error,
        controllable_change_loss=_mean_absolute(experience.controllable_sensor_change),
        confidence_calibration_loss=0.0,
        mean_absolute_error=error,
        external_change_mean_absolute=_mean_absolute(experience.external_sensor_change),
        mean_confidence=max(0.0, 1.0 - error),
        gradient_norm=0.0,
        terminated=experience.terminated,
    )


def _comparison_signals(
    step_index: int, resource_state: tuple[float, ...]
) -> LiveDevelopmentalSignals:
    resource_pressure = 0.0 if not resource_state else max(0.0, 1.0 - fmean(resource_state))
    return LiveDevelopmentalSignals(
        step_index=step_index,
        ambition_relevance=1.0,
        ambition_commitment=1.0,
        ambition_learning_progress=0.5,
        curiosity_value=0.5,
        curiosity_learning_progress=0.25,
        curiosity_uncertainty=0.5,
        self_controllability=0.5,
        body_confidence=0.5,
        help_requested=0.0,
        human_approval=0.0,
        human_correction=0.0,
        human_demonstration=0.0,
        human_clarification=0.0,
        human_signal_magnitude=0.0,
        prediction_error=0.5,
        resource_pressure=resource_pressure,
        need_resolution=0.0,
    )


def _build_step(
    *,
    record: ContributionRecord,
    scenario_step: int,
    global_step: int,
    default_action: PrimitiveAction,
    ndnra_action: PrimitiveAction | None,
    suggestion_score: float,
    candidate_count: int,
    learned_assembly_count: int,
    effect_dimension_count: int,
    scored: _ScoredCandidates | None,
    target_achieved: bool,
) -> Week9ComparisonStep:
    return Week9ComparisonStep(
        contribution_id=record.contribution_id,
        scenario_id=record.scenario_id,
        scenario_context=record.scenario_context,
        step_index=global_step,
        scenario_step_index=scenario_step,
        default_action=default_action,
        ndnra_action=ndnra_action,
        ndnra_abstained=ndnra_action is None,
        agreement=ndnra_action is default_action,
        disagreement=ndnra_action is not None and ndnra_action is not default_action,
        compared=scored is not None,
        default_executed=True,
        ndnra_executed=False,
        default_oracle_score=None if scored is None else scored.default.score,
        ndnra_oracle_score=None if scored is None else scored.ndnra.score,
        default_goal_progress=None if scored is None else scored.default_goal_progress,
        ndnra_goal_progress=None if scored is None else scored.ndnra_goal_progress,
        default_combined_score=None if scored is None else scored.default_combined_score,
        ndnra_combined_score=None if scored is None else scored.ndnra_combined_score,
        ndnra_advantage=None if scored is None else scored.advantage,
        winner="not_compared" if scored is None else scored.winner,
        default_resource_cost=None if scored is None else scored.default.resource_cost,
        ndnra_resource_cost=None if scored is None else scored.ndnra.resource_cost,
        target_achieved_after_default=target_achieved,
        ndnra_suggestion_score=suggestion_score,
        ndnra_candidate_count=candidate_count,
        learned_assembly_count=learned_assembly_count,
        effect_dimension_count=effect_dimension_count,
    )


def _scenario_summary(
    record: ContributionRecord, steps: tuple[Week9ComparisonStep, ...]
) -> Week9ScenarioComparison:
    return Week9ScenarioComparison(
        contribution_id=record.contribution_id,
        scenario_id=record.scenario_id,
        default_task_success=record.success,
        production_steps=len(steps),
        ndnra_proposals=sum(step.ndnra_action is not None for step in steps),
        ndnra_abstentions=sum(step.ndnra_abstained for step in steps),
        agreements=sum(step.agreement for step in steps),
        disagreements=sum(step.disagreement for step in steps),
        default_better=sum(step.winner == "default" for step in steps),
        ndnra_better=sum(step.winner == "ndnra" for step in steps),
        ties=sum(step.winner == "tie" for step in steps),
    )


def _run_isolated_ndnra_rollouts(
    records: tuple[ContributionRecord, ...],
    scenarios: tuple[NurseryScenario, ...],
    shadow: NDNRAShadowAdapter,
) -> tuple[Week9NDNRARollout, ...]:
    rollouts: list[Week9NDNRARollout] = []
    rollout_step = 0
    for record, scenario in zip(records, scenarios, strict=True):
        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=f"{record.contribution_id}-ndnra-isolated-rollout",
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )
        executed = 0
        abstained = False
        while scenario.remaining_steps(runtime.state) > 0:
            if _target_achieved(
                runtime.state,
                record.request.target_object_id,
                record.request.target_id,
            ):
                break
            suggestion = shadow.suggest(runtime.observe(), step_index=rollout_step)
            rollout_step += 1
            if suggestion.suggested_action is None:
                abstained = True
                break
            collect_experience(runtime, suggestion.suggested_action)
            executed += 1
            if runtime.state.terminated:
                break
        rollouts.append(
            Week9NDNRARollout(
                contribution_id=record.contribution_id,
                scenario_id=record.scenario_id,
                success=_target_achieved(
                    runtime.state,
                    record.request.target_object_id,
                    record.request.target_id,
                ),
                executed_steps=executed,
                abstained=abstained,
                terminated=runtime.state.terminated,
            )
        )
    return tuple(rollouts)


def _build_report(
    *,
    records: tuple[ContributionRecord, ...],
    steps: tuple[Week9ComparisonStep, ...],
    rollouts: tuple[Week9NDNRARollout, ...],
    learned_assembly_count: int,
    effect_dimension_count: int,
) -> Week9ParallelComparisonReport:
    compared = tuple(step for step in steps if step.compared)
    disagreements = tuple(step for step in steps if step.disagreement)
    disagreement_comparisons = tuple(step for step in disagreements if step.compared)
    coverage = 1.0 if not disagreements else len(disagreement_comparisons) / len(disagreements)
    return Week9ParallelComparisonReport(
        total_scenarios=len(records),
        total_production_steps=len(steps),
        default_proposal_count=len(steps),
        ndnra_observation_count=len(steps),
        ndnra_proposal_count=len(compared),
        ndnra_abstention_count=sum(step.ndnra_abstained for step in steps),
        agreement_count=sum(step.agreement for step in steps),
        disagreement_count=len(disagreements),
        comparison_count=len(compared),
        disagreement_comparison_count=len(disagreement_comparisons),
        disagreement_comparison_coverage=coverage,
        default_better_count=sum(step.winner == "default" for step in compared),
        ndnra_better_count=sum(step.winner == "ndnra" for step in compared),
        tied_count=sum(step.winner == "tie" for step in compared),
        mean_default_combined_score=_mean_optional(
            step.default_combined_score for step in compared
        ),
        mean_ndnra_combined_score=_mean_optional(step.ndnra_combined_score for step in compared),
        mean_ndnra_advantage=_mean_optional(step.ndnra_advantage for step in compared),
        mean_default_resource_cost=_mean_optional(step.default_resource_cost for step in compared),
        mean_ndnra_resource_cost=_mean_optional(step.ndnra_resource_cost for step in compared),
        default_task_successes=sum(record.success for record in records),
        default_task_success_rate=(
            sum(record.success for record in records) / len(records) if records else 0.0
        ),
        ndnra_rollout_attempts=len(rollouts),
        ndnra_rollout_successes=sum(rollout.success for rollout in rollouts),
        ndnra_rollout_success_rate=(
            sum(rollout.success for rollout in rollouts) / len(rollouts) if rollouts else 0.0
        ),
        ndnra_rollout_abstentions=sum(rollout.abstained for rollout in rollouts),
        learned_assembly_count=learned_assembly_count,
        effect_dimension_count=effect_dimension_count,
        production_action_replacements=0,
        authority_violations=0,
        automatic_promotions=0,
    )


def _mean_optional(values: Iterable[float | None]) -> float:
    resolved = tuple(value for value in values if value is not None)
    return fmean(resolved) if resolved else 0.0


def _mean_absolute(values: tuple[float, ...]) -> float:
    return min(1.0, fmean(abs(value) for value in values)) if values else 0.0


def _clamp_signed(value: float) -> float:
    if not isfinite(value):
        raise ValueError("comparison score must be finite")
    return max(-1.0, min(1.0, value))
