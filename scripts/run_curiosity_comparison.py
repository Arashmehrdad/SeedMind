"""Run the Week 4 curiosity-versus-random discovery comparison."""

from __future__ import annotations

import argparse
from pathlib import Path

import torch

from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.curiosity import (
    CuriosityComparisonConfig,
    CuriosityConfig,
    CuriosityRandomComparisonExperiment,
    export_curiosity_comparison_csv,
    export_curiosity_comparison_json,
)
from seedmind.environment import (
    DynamicNurseryScenarioFactory,
    NurseryRuntime,
    NurseryScenario,
)
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
    """Parse deterministic matched-comparison settings."""
    parser = argparse.ArgumentParser(
        description=("Compare curiosity-guided and random controllable-effect discovery."),
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--model-seed", type=int, default=41)
    parser.add_argument("--random-seed", type=int, default=97)
    parser.add_argument("--trials", type=int, default=8)
    parser.add_argument("--budget", type=int, default=24)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/curiosity_comparison"),
    )
    return parser.parse_args()


def build_trainer(
    model_seed: int,
    scenario: NurseryScenario,
) -> OnlinePredictiveTrainer:
    """Create a fresh deterministic neural learner for one matched trial."""
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-interface-{model_seed}",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    observation = runtime.observe()
    input_spec = SymbolicInputSpec(
        sensor_size=len(observation.sensor_values),
        human_signal_size=len(observation.human_signal),
        resource_state_size=len(observation.resource_state),
    )
    torch.manual_seed(model_seed)
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
    """Run paired trials, export evidence, and return the Week 4 verdict."""
    args = parse_args()
    config = CuriosityComparisonConfig(
        scenario_seed=args.seed,
        model_seed=args.model_seed,
        random_seed=args.random_seed,
        trial_count=args.trials,
        curiosity=CuriosityConfig(
            play_budget=args.budget,
            experiment_actions=_EXPERIMENT_ACTIONS,
        ),
    )
    result = CuriosityRandomComparisonExperiment(
        DynamicNurseryScenarioFactory(),
        build_trainer,
        config,
    ).run()
    json_path = args.output_dir / "comparison_report.json"
    csv_path = args.output_dir / "comparison_timeline.csv"
    export_curiosity_comparison_json(result, json_path)
    export_curiosity_comparison_csv(result, csv_path)

    oracle_actions = ",".join(action.value for action in result.oracle_effect_actions)
    oracle_sensors = ",".join(str(index) for index in result.oracle_body_sensor_indices)
    print(f"scenario_id={result.scenario_id}")
    print(f"trial_count={config.trial_count}")
    print(f"transition_budget={config.curiosity.play_budget}")
    print(f"oracle_effect_actions={oracle_actions}")
    print(f"oracle_body_sensor_indices={oracle_sensors}")
    print(f"curiosity_mean_discovery_auc={result.curiosity_mean_discovery_auc:.8f}")
    print(f"random_mean_discovery_auc={result.random_mean_discovery_auc:.8f}")
    print(f"curiosity_mean_final_effect_recall={result.curiosity_mean_final_effect_recall:.8f}")
    print(f"random_mean_final_effect_recall={result.random_mean_final_effect_recall:.8f}")
    print(f"curiosity_mean_full_discovery_step={result.curiosity_mean_full_discovery_step:.8f}")
    print(f"random_mean_full_discovery_step={result.random_mean_full_discovery_step:.8f}")
    print(f"curiosity_mean_final_body_f1={result.curiosity_mean_final_body_f1:.8f}")
    print(f"random_mean_final_body_f1={result.random_mean_final_body_f1:.8f}")
    print(f"curiosity_mean_noise_share={result.curiosity_mean_noise_share:.8f}")
    print(f"random_mean_noise_share={result.random_mean_noise_share:.8f}")
    print(f"curiosity_maximum_noise_streak={result.curiosity_maximum_noise_streak}")
    print(f"noise_loop_avoided={str(result.noise_loop_avoided).lower()}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"comparison_report_json={json_path}")
    print(f"comparison_timeline_csv={csv_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
