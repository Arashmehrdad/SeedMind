"""Tests for fair Week 9 Default-vs-NDNRA comparative evidence."""

from __future__ import annotations

import pytest

from seedmind.contracts import Direction, GridPosition, PrimitiveAction
from seedmind.contribution import (
    GoalConditionedNDNRAController,
    TaskProgressCategory,
    extract_ndnra_state_features,
    goal_from_request,
    run_week9_contribution_evaluation,
)
from seedmind.contribution.parallel_comparison import train_ndnra_in_sandbox
from seedmind.contribution.week9 import _build_request
from seedmind.environment import AgentState, EntityRole, EntityState, NurseryState
from seedmind.skills import DEFAULT_TRAINING_SEEDS, Week8ScenarioFactory


def test_ndnra_receives_explicit_week9_goal_and_goal_omission_blocks_competence() -> None:
    result = run_week9_contribution_evaluation()
    first_step = result.parallel_comparison.steps[0]

    assert first_step.ndnra_proposal.goal is not None
    assert first_step.ndnra_proposal.goal.target_object_id == "object_0"
    assert first_step.ndnra_proposal.goal.destination_target_id == "target_0"

    controller = GoalConditionedNDNRAController()
    scenario = Week8ScenarioFactory().create(206)
    proposal = controller.propose(
        scenario.initial_state,
        tuple(PrimitiveAction),
        None,
        remaining_steps=scenario.step_budget,
    )

    assert proposal.action is None
    assert proposal.reason_code == "goal_missing"


def test_ndnra_receives_relational_context_not_only_available_actions() -> None:
    scenario = Week8ScenarioFactory().create(206)
    goal = goal_from_request(_build_request(request_id="request"), scenario_context="familiar")
    features = extract_ndnra_state_features(
        scenario.initial_state,
        goal,
        tuple(PrimitiveAction),
        remaining_steps=scenario.step_budget,
        human_interruption=False,
    )

    assert features.available_actions
    assert features.target_object_position != features.destination_target_position
    assert features.object_to_target_distance > 0
    assert isinstance(features.agent_to_object_dx, int)


def test_identical_available_actions_with_different_geometry_can_change_proposal() -> None:
    controller = GoalConditionedNDNRAController()
    request = _build_request(request_id="request")
    goal = goal_from_request(request, scenario_context="familiar")
    east = _state(
        agent=GridPosition(1, 3),
        orientation=Direction.EAST,
        ball=GridPosition(2, 3),
        target=GridPosition(4, 3),
    )
    north = _state(
        agent=GridPosition(3, 4),
        orientation=Direction.NORTH,
        ball=GridPosition(3, 3),
        target=GridPosition(3, 1),
    )

    east_proposal = controller.propose(east, tuple(PrimitiveAction), goal, remaining_steps=30)
    north_proposal = controller.propose(north, tuple(PrimitiveAction), goal, remaining_steps=30)

    assert east_proposal.features.available_actions == north_proposal.features.available_actions
    assert east_proposal.features.object_to_target_dx != north_proposal.features.object_to_target_dx
    assert (
        east_proposal.action != north_proposal.action
        or east_proposal.features != north_proposal.features
    )


def test_ndnra_training_uses_ndnra_executed_sandbox_transitions() -> None:
    factory = Week8ScenarioFactory()
    controller = GoalConditionedNDNRAController()
    scenarios = tuple(factory.create(seed) for seed in DEFAULT_TRAINING_SEEDS)
    requests = tuple(_build_request(request_id=f"train-{seed}") for seed in DEFAULT_TRAINING_SEEDS)

    train_ndnra_in_sandbox(controller, scenarios=scenarios, requests=requests)

    assert controller.transition_count > 0
    assert controller.evaluation_update_count == 0
    assert controller.learned_action_keys()


def test_frozen_evaluation_refuses_to_train_ndnra() -> None:
    controller = GoalConditionedNDNRAController()
    scenario = Week8ScenarioFactory().create(206)
    goal = goal_from_request(_build_request(request_id="request"), scenario_context="familiar")

    with pytest.raises(ValueError, match="frozen evaluation"):
        controller.observe_transition(
            before=scenario.initial_state,
            after=scenario.initial_state,
            action=PrimitiveAction.WAIT,
            goal=goal,
            available_actions=tuple(PrimitiveAction),
            remaining_steps=scenario.step_budget,
            source="evaluation",
        )


def test_fair_comparison_separates_integrity_from_ndnra_competence() -> None:
    result = run_week9_contribution_evaluation()
    report = result.parallel_comparison.report

    assert report.experiment_integrity_pass is True
    assert report.default_competence_pass is True
    assert report.blocked_scenario_handling_pass is True
    assert report.authority_containment_pass is True
    assert report.week9_main_milestone_pass is True
    assert report.ndnra_competence_pass == (report.ndnra_frozen_solvable_completion_rate >= 0.80)
    assert not (report.ndnra_competence_pass and report.ndnra_frozen_solvable_successes == 0)


def test_counterfactual_categories_do_not_count_generic_only_as_task_wins() -> None:
    result = run_week9_contribution_evaluation()
    report = result.parallel_comparison.report

    assert (
        report.task_progress_default_better
        + report.task_progress_ndnra_better
        + report.task_equivalent
        + report.generic_score_only_difference
        + report.not_comparable
        == len(result.parallel_comparison.steps)
    )
    generic_only_steps = [
        step
        for step in result.parallel_comparison.steps
        if step.category is TaskProgressCategory.GENERIC_ONLY
    ]
    ndnra_task_wins = [
        step
        for step in result.parallel_comparison.steps
        if step.category is TaskProgressCategory.NDNRA_BETTER
    ]
    assert len(generic_only_steps) == report.generic_score_only_difference
    assert len(ndnra_task_wins) == report.task_progress_ndnra_better


def test_solvable_and_blocked_scenarios_are_reported_separately() -> None:
    result = run_week9_contribution_evaluation()
    report = result.parallel_comparison.report

    assert report.default_solvable_attempts == 10
    assert report.blocked_scenarios == 2
    assert report.blocked_default_honest_failures == 2
    assert report.blocked_ndnra_honest_failures == 2


def test_default_remains_sole_production_controller_and_ndnra_cannot_promote() -> None:
    result = run_week9_contribution_evaluation()

    assert result.parallel_comparison.report.authority_violations == 0
    assert result.parallel_comparison.report.automatic_promotions == 0
    assert all(step.default_executed for step in result.parallel_comparison.steps)
    assert all(not step.ndnra_executed for step in result.parallel_comparison.steps)
    assert all(
        not step.ndnra_proposal.has_action_authority for step in result.parallel_comparison.steps
    )


def test_fair_comparison_is_deterministic() -> None:
    first = run_week9_contribution_evaluation().parallel_comparison.to_json()
    second = run_week9_contribution_evaluation().parallel_comparison.to_json()

    assert first == second


def _state(
    *,
    agent: GridPosition,
    orientation: Direction,
    ball: GridPosition,
    target: GridPosition,
) -> NurseryState:
    return NurseryState(
        width=7,
        height=7,
        agent=AgentState(position=agent, orientation=orientation),
        entities=(
            EntityState(
                entity_id="object_0",
                role=EntityRole.OBJECT,
                position=ball,
                blocks_movement=True,
                movable=True,
            ),
            EntityState(
                entity_id="target_0",
                role=EntityRole.TARGET,
                position=target,
                blocks_movement=False,
                movable=False,
            ),
        ),
    )
