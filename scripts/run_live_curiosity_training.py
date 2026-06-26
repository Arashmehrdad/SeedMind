"""Run curiosity-guided predictive training in the dynamic nursery."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.curiosity import (
    CuriosityConfig,
    CuriosityTrainingConfig,
    CuriosityTrainingSession,
    export_curiosity_training_csv,
    export_curiosity_training_json,
)
from seedmind.environment import DynamicNurseryScenarioFactory, NurseryRuntime
from seedmind.perception import SymbolicInputSpec
from seedmind.training import OnlinePredictiveTrainer, OnlineTrainerConfig

_EXPERIMENT_ACTIONS = (
    PrimitiveAction.TURN_LEFT,
    PrimitiveAction.TURN_RIGHT,
    PrimitiveAction.MOVE_FORWARD,
    PrimitiveAction.INSPECT,
    PrimitiveAction.PUSH,
    PrimitiveAction.WAIT,
)


def parse_args() -> argparse.Namespace:
    """Parse one deterministic live-curiosity training run."""
    parser = argparse.ArgumentParser(
        description="Train SeedMind from curiosity-selected dynamic nursery experience.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--budget", type=int, default=24)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/live_curiosity_training"),
    )
    return parser.parse_args()


def build_trainer(
    seed: int,
    scenario_factory: DynamicNurseryScenarioFactory,
) -> OnlinePredictiveTrainer:
    """Build a deterministic learner matching the dynamic nursery interface."""
    scenario = scenario_factory.create(seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-interface",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    observation = runtime.observe()
    input_spec = SymbolicInputSpec(
        sensor_size=len(observation.sensor_values),
        human_signal_size=len(observation.human_signal),
        resource_state_size=len(observation.resource_state),
    )
    torch.manual_seed(seed)
    core = PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=input_spec.input_size,
            sensor_size=input_spec.sensor_size,
            action_count=len(PrimitiveAction),
        )
    )
    return OnlinePredictiveTrainer(
        core,
        input_spec,
        config=OnlineTrainerConfig(),
    )


def main() -> int:
    """Run live curiosity, export evidence, and print summary metrics."""
    args = parse_args()
    scenario_factory = DynamicNurseryScenarioFactory()
    trainer = build_trainer(args.seed, scenario_factory)
    config = CuriosityTrainingConfig(
        seed=args.seed,
        curiosity=CuriosityConfig(
            play_budget=args.budget,
            experiment_actions=_EXPERIMENT_ACTIONS,
        ),
    )
    result = CuriosityTrainingSession(
        trainer,
        scenario_factory,
        config,
    ).run()
    json_path = args.output_dir / "live_experiment_timeline.json"
    csv_path = args.output_dir / "live_experiment_timeline.csv"
    export_curiosity_training_json(result, json_path)
    export_curiosity_training_csv(result, csv_path)

    print(f"scenario_id={result.scenario_id}")
    print(f"selection_count={result.selection_count}")
    print(f"mean_prediction_error={result.mean_prediction_error:.8f}")
    print(f"initial_prediction_error={result.initial_prediction_error:.8f}")
    print(f"final_prediction_error={result.final_prediction_error:.8f}")
    for action, count in result.action_counts:
        print(f"selected_{action.value}={count}")
    print(f"timeline_json={json_path}")
    print(f"timeline_csv={csv_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
