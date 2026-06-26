"""Run initial action-effect and body-channel discovery evidence."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.environment import DynamicNurseryScenarioFactory, NurseryRuntime
from seedmind.self_model import (
    SelfModelConfig,
    SelfModelRegistry,
    export_action_effects_csv,
    export_self_model_json,
)
from seedmind.training import collect_experience


def parse_args() -> argparse.Namespace:
    """Parse deterministic body-discovery experiment settings."""
    parser = argparse.ArgumentParser(
        description="Infer anonymous controllable body channels from repeated actions.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--repetitions", type=int, default=8)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/body_discovery"),
    )
    return parser.parse_args()


def main() -> int:
    """Collect causal transitions and export an inspectable self-model."""
    args = parse_args()
    if args.repetitions <= 0:
        raise ValueError("repetitions must be positive")

    scenario = DynamicNurseryScenarioFactory().create(args.seed)
    interface_runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-interface",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    registry = SelfModelRegistry(
        SelfModelConfig(
            sensor_size=interface_runtime.sensor_size,
            minimum_samples=args.repetitions,
        )
    )
    actions = (
        PrimitiveAction.TURN_LEFT,
        PrimitiveAction.TURN_RIGHT,
        PrimitiveAction.MOVE_FORWARD,
        PrimitiveAction.WAIT,
    )

    for action in actions:
        for repetition in range(args.repetitions):
            runtime = NurseryRuntime(
                initial_state=scenario.initial_state,
                episode_id=(
                    f"{scenario.scenario_id}-{action.value}-{repetition:04d}"
                ),
                resource_state_provider=scenario.resource_state,
                world_processes=scenario.world_processes,
            )
            registry.observe(collect_experience(runtime, action))

    snapshot = registry.snapshot()
    json_path = args.output_dir / "self_model.json"
    csv_path = args.output_dir / "action_effects.csv"
    export_self_model_json(snapshot, json_path)
    export_action_effects_csv(snapshot, csv_path)

    body_indices = ",".join(str(index) for index in snapshot.body_sensor_indices)
    print(f"experience_count={snapshot.experience_count}")
    print(f"action_coverage={snapshot.action_coverage:.8f}")
    print(f"body_sensor_indices={body_indices}")
    print(
        "mean_body_controllability="
        f"{snapshot.mean_body_controllability:.8f}"
    )
    print(
        "mean_external_effect_frequency="
        f"{snapshot.mean_external_effect_frequency:.8f}"
    )
    print(f"self_model_json={json_path}")
    print(f"action_effects_csv={csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
