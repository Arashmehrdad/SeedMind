"""Run a deterministic curiosity-scoring demonstration timeline."""

from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.curiosity import (
    CuriosityConfig,
    CuriositySelection,
    CuriositySubsystem,
    export_curiosity_timeline_csv,
    export_curiosity_timeline_json,
)

_EXPERIMENT_ACTIONS = (
    PrimitiveAction.TURN_LEFT,
    PrimitiveAction.WAIT,
    PrimitiveAction.INSPECT,
)


def parse_args() -> argparse.Namespace:
    """Parse bounded synthetic curiosity demonstration settings."""
    parser = argparse.ArgumentParser(
        description=(
            "Demonstrate learning-progress curiosity, novelty decay, and stagnation avoidance."
        ),
    )
    parser.add_argument("--budget", type=int, default=18)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/curiosity_scoring"),
    )
    return parser.parse_args()


def main() -> int:
    """Select bounded experiments and feed deterministic prediction errors."""
    args = parse_args()
    subsystem = CuriositySubsystem(
        CuriosityConfig(
            play_budget=args.budget,
            progress_window=2,
            novelty_decay=4.0,
            repetition_horizon=2,
            stagnation_horizon=3,
            experiment_actions=_EXPERIMENT_ACTIONS,
        )
    )
    selections: list[CuriositySelection] = []
    action_counts: Counter[PrimitiveAction] = Counter()

    while not subsystem.budget_exhausted:
        selection = subsystem.select(_EXPERIMENT_ACTIONS)
        selections.append(selection)
        action = selection.selected_action
        observation_index = len(subsystem.observed_errors(action))
        prediction_error = _prediction_error(action, observation_index)
        subsystem.observe(action, prediction_error)
        action_counts[action] += 1

    timeline_json = args.output_dir / "experiment_timeline.json"
    timeline_csv = args.output_dir / "experiment_timeline.csv"
    export_curiosity_timeline_json(tuple(selections), timeline_json)
    export_curiosity_timeline_csv(tuple(selections), timeline_csv)

    final_candidates = subsystem.generate_candidates(_EXPERIMENT_ACTIONS)
    print(f"selection_count={subsystem.selection_count}")
    print(f"remaining_budget={subsystem.remaining_budget}")
    for action in _EXPERIMENT_ACTIONS:
        print(f"selected_{action.value}={action_counts[action]}")
    for candidate in final_candidates:
        print(f"final_score_{candidate.action.value}={candidate.score:.8f}")
        print(f"final_progress_{candidate.action.value}={candidate.learning_progress:.8f}")
        print(f"final_stagnation_{candidate.action.value}={candidate.stagnation_penalty:.8f}")
    print(f"timeline_json={timeline_json}")
    print(f"timeline_csv={timeline_csv}")
    return 0


def _prediction_error(action: PrimitiveAction, observation_index: int) -> float:
    """Return one learnable, noisy, or already-familiar synthetic error."""
    if action is PrimitiveAction.TURN_LEFT:
        learning_curve = (1.0, 0.82, 0.58, 0.36, 0.21, 0.12, 0.08, 0.05)
        return learning_curve[min(observation_index, len(learning_curve) - 1)]

    if action is PrimitiveAction.WAIT:
        return 1.0

    if action is PrimitiveAction.INSPECT:
        return 0.1

    raise AssertionError(f"Unhandled curiosity demonstration action: {action!r}")


if __name__ == "__main__":
    raise SystemExit(main())
