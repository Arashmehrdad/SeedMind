"""Run the Week 5 teacher-demonstration ambition formation gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.ambition import (
    AmbitionManager,
    AmbitionStatus,
    GoalDirectedOutcomeDetector,
    ObservedDemonstration,
    export_ambition_dashboard,
    export_demonstration_evidence,
    load_ambition_manager,
    save_ambition_manager,
)
from seedmind.contracts import PrimitiveAction
from seedmind.environment import NurseryRuntime, TeacherDemonstrationScenarioFactory


def parse_args() -> argparse.Namespace:
    """Parse deterministic ambition-formation evidence settings."""
    parser = argparse.ArgumentParser(
        description="Form and persist an ambition from repeated teacher outcomes.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--demonstrations", type=int, default=3)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ambition_formation"),
    )
    return parser.parse_args()


def main() -> int:
    """Observe demonstrations, adopt an ambition, and verify persistence."""
    args = parse_args()
    if args.demonstrations <= 0:
        raise ValueError("demonstrations must be positive")

    scenario_factory = TeacherDemonstrationScenarioFactory()
    detector = GoalDirectedOutcomeDetector()
    manager = AmbitionManager()
    candidate = None

    for demonstration_index in range(args.demonstrations):
        scenario = scenario_factory.create(args.seed)
        episode_id = f"{scenario.scenario_id}-demonstration-{demonstration_index:04d}"
        runtime = NurseryRuntime(
            initial_state=scenario.initial_state,
            episode_id=episode_id,
            resource_state_provider=scenario.resource_state,
            world_processes=scenario.world_processes,
        )
        start_observation = runtime.observe()
        external_change_steps = 0
        for _ in range(2):
            step = runtime.step(PrimitiveAction.WAIT)
            external_change_steps += int(step.external_world_changed)
        outcome_signal = float(scenario.target_occupancy(runtime.state).all_targets_occupied)
        candidate = detector.observe(
            ObservedDemonstration(
                episode_id=episode_id,
                start_observation=start_observation,
                end_observation=runtime.observe(),
                external_change_steps=external_change_steps,
                outcome_signal=outcome_signal,
            )
        )
        if candidate is not None:
            manager.consider(candidate, episode_id=episode_id)

    active = manager.active_ambition
    if active is not None:
        manager.begin_episode("ambition-practice-episode-0001")

    evidence_path = args.output_dir / "demonstration_evidence.json"
    state_path = args.output_dir / "ambition_state.json"
    dashboard_path = args.output_dir / "ambition_dashboard.json"
    export_demonstration_evidence(detector, evidence_path)
    save_ambition_manager(manager, state_path)
    restored = load_ambition_manager(state_path)
    export_ambition_dashboard(restored, dashboard_path)

    restored_active = restored.active_ambition
    persistence_verified = (
        active is not None
        and restored_active is not None
        and restored_active.ambition_id == active.ambition_id
        and restored_active.last_episode_id == "ambition-practice-episode-0001"
        and restored_active.status is AmbitionStatus.ACTIVE
    )
    pass_gate = active is not None and persistence_verified
    evidence = detector.evidence()
    repeated_outcome_count = evidence[0].repetition_count if evidence else 0

    print(f"demonstrations_observed={detector.observed_episode_count}")
    print(f"repeated_outcome_count={repeated_outcome_count}")
    print(f"candidate_generated={str(candidate is not None).lower()}")
    print(f"ambition_adopted={str(active is not None).lower()}")
    if restored_active is not None:
        print(f"active_ambition_id={restored_active.ambition_id}")
        print(f"target_capability={restored_active.target_capability}")
        print(f"ambition_status={restored_active.status.value}")
        print(f"commitment={restored_active.commitment:.8f}")
        print(f"current_milestone={restored_active.current_milestone.code.value}")
        print(f"practice_budget={restored_active.practice_budget}")
        print(f"remaining_practice_budget={restored_active.remaining_practice_budget}")
        print(f"play_budget={restored_active.play_budget}")
        print(f"observed_episode_count={restored_active.observed_episode_count}")
    print(f"persisted_across_reload={str(persistence_verified).lower()}")
    print(f"pass_gate={str(pass_gate).lower()}")
    print(f"demonstration_evidence_json={evidence_path}")
    print(f"ambition_state_json={state_path}")
    print(f"ambition_dashboard_json={dashboard_path}")
    return 0 if pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
