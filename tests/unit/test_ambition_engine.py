"""Tests for demonstration-derived persistent ambitions."""

from pathlib import Path

import pytest

from seedmind.ambition import (
    AmbitionManager,
    AmbitionStatus,
    GoalDirectedOutcomeDetector,
    MilestoneCode,
    MilestoneStatus,
    ObservedDemonstration,
    export_ambition_dashboard,
    load_ambition_manager,
    save_ambition_manager,
)
from seedmind.contracts import PrimitiveAction
from seedmind.environment import NurseryRuntime, TeacherDemonstrationScenarioFactory


def observed_demo(index: int, signal: float = 1.0) -> ObservedDemonstration:
    scenario = TeacherDemonstrationScenarioFactory().create(7)
    episode_id = f"teacher-evidence-{index}"
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=episode_id,
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    start = runtime.observe()
    changed_steps = 0
    for _ in range(2):
        changed_steps += int(runtime.step(PrimitiveAction.WAIT).external_world_changed)
    return ObservedDemonstration(
        episode_id=episode_id,
        start_observation=start,
        end_observation=runtime.observe(),
        external_change_steps=changed_steps,
        outcome_signal=signal,
    )


def adopted_manager() -> AmbitionManager:
    detector = GoalDirectedOutcomeDetector()
    candidate = None
    for index in range(3):
        candidate = detector.observe(observed_demo(index))
    assert candidate is not None
    manager = AmbitionManager()
    assert manager.consider(candidate, episode_id="teacher-evidence-2") is not None
    return manager


def test_detector_requires_three_confirmed_repetitions() -> None:
    detector = GoalDirectedOutcomeDetector()
    assert detector.observe(observed_demo(0)) is None
    assert detector.observe(observed_demo(1)) is None
    candidate = detector.observe(observed_demo(2))
    assert candidate is not None
    assert candidate.target_capability == "control_external_change"
    assert candidate.evidence_count == 3
    assert candidate.milestone_codes[0] is MilestoneCode.LOCATE_CAUSAL_SOURCE
    assert detector.evidence()[0].confirmed_episode_count == 3


def test_unconfirmed_repetition_does_not_form_candidate() -> None:
    detector = GoalDirectedOutcomeDetector()
    results = tuple(detector.observe(observed_demo(index, 0.0)) for index in range(3))
    assert results == (None, None, None)


def test_ambition_persists_across_episodes() -> None:
    manager = adopted_manager()
    adopted = manager.active_ambition
    assert adopted is not None
    manager.begin_episode("practice-1")
    carried = manager.begin_episode("practice-2")
    assert carried is not None
    assert carried.ambition_id == adopted.ambition_id
    assert carried.observed_episode_count == 3
    assert carried.current_milestone.status is MilestoneStatus.ACTIVE


def test_budget_and_milestone_progression() -> None:
    manager = adopted_manager()
    active = manager.active_ambition
    assert active is not None
    practiced = manager.allocate_practice(8, episode_id="practice-1")
    progressed = manager.record_progress(0.80, competence=0.25, episode_id="practice-1")
    assert practiced.remaining_practice_budget == active.practice_budget - 8
    assert progressed.milestones[0].status is MilestoneStatus.COMPLETED
    assert progressed.current_milestone_index == 1
    with pytest.raises(ValueError, match="exceeds"):
        manager.allocate_practice(
            progressed.remaining_practice_budget + 1,
            episode_id="practice-2",
        )


def test_state_round_trip_and_dashboard(tmp_path: Path) -> None:
    manager = adopted_manager()
    manager.allocate_practice(5, episode_id="practice-1")
    state_path = tmp_path / "state.json"
    dashboard_path = tmp_path / "dashboard.json"
    save_ambition_manager(manager, state_path)
    restored = load_ambition_manager(state_path)
    export_ambition_dashboard(restored, dashboard_path)
    assert restored.active_ambition == manager.active_ambition
    dashboard = dashboard_path.read_text(encoding="ascii")
    assert '"has_active_ambition": true' in dashboard
    assert '"target_capability": "control_external_change"' in dashboard


def test_final_milestone_completes_ambition() -> None:
    manager = adopted_manager()
    for index in range(4):
        record = manager.record_progress(
            0.80,
            competence=(index + 1) / 4,
            episode_id=f"progress-{index}",
        )
    assert record.status is AmbitionStatus.COMPLETED
    assert all(item.status is MilestoneStatus.COMPLETED for item in record.milestones)
