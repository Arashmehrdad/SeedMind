"""Run contextual NDNRA redundancy and mastery acceptance."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.integration import (
    export_contextual_mastery_acceptance,
    run_contextual_mastery_acceptance,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Verify exact-event deduplication, contextual trace preservation, "
            "correlation discounting, route diversity, transfer, contradiction, "
            "persistence migration, and unchanged shadow production actions."
        )
    )
    parser.add_argument("--seed", type=int, default=13)
    parser.add_argument("--budget", type=int, default=12)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/ndnra_contextual_mastery"),
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    evidence = run_contextual_mastery_acceptance(
        args.output_dir,
        seed=args.seed,
        play_budget=args.budget,
    )
    report_path, timeline_path, profiles_path, shadow_path = export_contextual_mastery_acceptance(
        evidence, args.output_dir
    )
    result = evidence.result
    synthetic = evidence.experiment.result

    print(f"exact_duplicate_ignored={str(synthetic.exact_duplicate_ignored).lower()}")
    print(f"exact_duplicate_evidence_count={synthetic.exact_duplicate_evidence_count}")
    print(f"identity_conflict_blocked={str(synthetic.identity_conflict_blocked).lower()}")
    print(f"legitimate_context_preserved={str(synthetic.legitimate_context_preserved).lower()}")
    print(f"replay_trace_count={synthetic.replay_trace_count}")
    print(f"replay_effective_support={synthetic.replay_effective_support:.8f}")
    print(f"replay_unique_context_count={synthetic.replay_unique_context_count}")
    print(f"replay_aggregate_evidence_count={synthetic.replay_aggregate_evidence_count}")
    print(f"independent_trace_count={synthetic.independent_trace_count}")
    print(f"independent_effective_support={synthetic.independent_effective_support:.8f}")
    print(f"independent_unique_context_count={synthetic.independent_unique_context_count}")
    print(f"independent_unique_route_count={synthetic.independent_unique_route_count}")
    print(f"mastery_score_gain={synthetic.mastery_score_gain:.8f}")
    print(f"one_shot_protective_strength={synthetic.one_shot_protective_strength:.8f}")
    print(f"one_shot_broad_mastery={str(synthetic.one_shot_broad_mastery).lower()}")
    print(f"varied_heat_mastery_score={synthetic.varied_heat_mastery_score:.8f}")
    print(f"varied_heat_broad_mastery={str(synthetic.varied_heat_broad_mastery).lower()}")
    print(f"contradiction_count_before={synthetic.contradiction_count_before}")
    print(f"contradiction_count_after={synthetic.contradiction_count_after}")
    print(f"causal_consistency_before={synthetic.causal_consistency_before:.8f}")
    print(f"causal_consistency_after={synthetic.causal_consistency_after:.8f}")
    print(f"mastery_before_contradiction={synthetic.mastery_before_contradiction:.8f}")
    print(f"mastery_after_contradiction={synthetic.mastery_after_contradiction:.8f}")
    print(f"source_traces_preserved={str(synthetic.source_traces_preserved).lower()}")
    print(f"route_switches_with_context={str(synthetic.route_switches_with_context).lower()}")
    print(f"production_actions_unchanged={str(result.production_actions_unchanged).lower()}")
    print(f"prediction_errors_unchanged={str(result.prediction_errors_unchanged).lower()}")
    print(f"authority_violation_count={result.authority_violation_count}")
    print(f"tracked_trace_count={result.tracked_trace_count}")
    print(f"expected_trace_count={result.expected_trace_count}")
    print(f"graph_round_trip_exact={str(result.graph_round_trip_exact).lower()}")
    print(f"contextual_round_trip_exact={str(result.contextual_round_trip_exact).lower()}")
    print(f"legacy_v1_migration_passed={str(result.legacy_v1_migration_passed).lower()}")
    print(
        "sqlite_used_for_contextual_mastery="
        f"{str(result.sqlite_used_for_contextual_mastery).lower()}"
    )
    print(f"theory_readiness_before={result.theory_readiness_before}")
    print(f"theory_readiness_after={result.theory_readiness_after}")
    print(f"pass_gate={str(result.pass_gate).lower()}")
    print(f"contextual_mastery_report_json={report_path}")
    print(f"contextual_trace_timeline_csv={timeline_path}")
    print(f"mastery_profiles_json={profiles_path}")
    print(f"shadow_invariance_report_json={shadow_path}")
    return 0 if result.pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
