"""Run a reproducible SeedMind familiar-sequence training session."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.environment import NurseryRuntime, NurseryScenarioFactory
from seedmind.perception import SymbolicInputSpec
from seedmind.training import (
    FamiliarSequenceConfig,
    FamiliarSequenceTrainingSession,
    OnlinePredictiveTrainer,
    OnlineTrainerConfig,
    export_prediction_error_svg,
    export_training_history_csv,
)


def parse_args() -> argparse.Namespace:
    """Parse command-line settings for one familiar-sequence run."""
    parser = argparse.ArgumentParser(
        description="Train SeedMind on one repeatable nursery action sequence.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--episodes", type=int, default=20)
    parser.add_argument("--max-episodes", type=int)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/familiar_training"),
    )
    parser.add_argument("--resume", action="store_true")
    return parser.parse_args()


def build_trainer(seed: int) -> tuple[OnlinePredictiveTrainer, NurseryScenarioFactory]:
    """Build a deterministic predictive core matching the nursery channels."""
    scenario_factory = NurseryScenarioFactory()
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
    trainer = OnlinePredictiveTrainer(
        core,
        input_spec,
        config=OnlineTrainerConfig(),
    )
    return trainer, scenario_factory


def main() -> int:
    """Run training, save evidence, and report the familiar-sequence gate."""
    args = parse_args()
    trainer, scenario_factory = build_trainer(args.seed)
    config = FamiliarSequenceConfig(
        seed=args.seed,
        episode_count=args.episodes,
    )
    session = FamiliarSequenceTrainingSession(
        trainer,
        scenario_factory,
        config,
    )
    checkpoint_path = args.output_dir / "checkpoint.pt"
    result = session.run(
        checkpoint_path=checkpoint_path,
        resume=args.resume,
        max_episodes=args.max_episodes,
    )
    csv_path = args.output_dir / "training_history.csv"
    chart_path = args.output_dir / "prediction_error.svg"
    export_training_history_csv(result, csv_path)
    export_prediction_error_svg(result, chart_path)

    print(f"completed_episodes={result.completed_episodes}")
    print(f"initial_mean_absolute_error={result.initial_mean_absolute_error:.8f}")
    print(f"final_mean_absolute_error={result.final_mean_absolute_error:.8f}")
    print(f"prediction_error_improved={str(result.prediction_error_improved).lower()}")
    print(f"checkpoint={checkpoint_path}")
    print(f"history_csv={csv_path}")
    print(f"prediction_error_chart={chart_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
