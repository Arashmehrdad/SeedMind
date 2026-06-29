"""Tests for deterministic long-horizon mixed-task interference Batch 1."""

from __future__ import annotations

import hashlib
import json
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from seedmind.research.ndnra import (
    LongHorizonInterferenceConfig,
    LongHorizonTaskFamily,
    run_long_horizon_interference_experiment,
    validate_long_horizon_interference_result,
)


def test_old_family_is_mastered_and_eligible_before_horizon() -> None:
    evidence = run_long_horizon_interference_experiment()
    result = evidence.result

    assert evidence.eligibility.eligible
    assert evidence.eligibility.candidate is not None
    assert result.old_family_mastery_profile.broad_mastery
    assert result.old_family_mastery_profile.effective_support >= 3.0
    assert result.old_family_mastery_profile.unique_context_count >= 3
    assert result.old_family_mastery_profile.unique_route_count >= 2
    assert result.source_trace_count_before == 3
    assert result.source_trace_count_after == 3
    assert evidence.old_family_source_event_ids == result.consolidation_candidate.source_event_ids


def test_all_conditions_use_exact_36_step_abac_schedule_with_contiguous_indices() -> None:
    evidence = run_long_horizon_interference_experiment()
    expected_pattern = (
        LongHorizonTaskFamily.FAMILY_A,
        LongHorizonTaskFamily.FAMILY_B,
        LongHorizonTaskFamily.FAMILY_A,
        LongHorizonTaskFamily.FAMILY_C,
    )

    for condition in (
        evidence.result.no_consolidation,
        evidence.result.naive_protection,
        evidence.result.bounded_retention_replay,
    ):
        assert tuple(step.step_index for step in condition.timeline) == tuple(range(36))
        assert tuple(step.task_family for step in condition.timeline) == expected_pattern * 9


def test_family_a_probe_steps_do_not_mutate_memory() -> None:
    evidence = run_long_horizon_interference_experiment()

    for condition in (
        evidence.result.no_consolidation,
        evidence.result.naive_protection,
        evidence.result.bounded_retention_replay,
    ):
        for step in condition.timeline:
            if step.task_family is not LongHorizonTaskFamily.FAMILY_A:
                continue
            assert step.probe_only
            assert not step.learning_applied
            assert step.memory_state_before == step.memory_state_after
            assert not step.replay_applied


def test_public_snapshots_are_transitively_immutable() -> None:
    evidence = run_long_horizon_interference_experiment()
    step = evidence.result.bounded_retention_replay.timeline[0]

    assert isinstance(step.memory_state_before, tuple)
    assert isinstance(step.memory_state_before[1], tuple)
    assert isinstance(evidence.source_ledger_snapshot, str)
    with pytest.raises(TypeError):
        step.memory_state_before[1][0][0] = "tampered"  # type: ignore[index]


def test_no_consolidation_learns_b_and_c_while_degrading_old_family() -> None:
    result = run_long_horizon_interference_experiment().result.no_consolidation

    assert result.final_b_family_score >= 0.68
    assert result.final_c_family_score >= 0.68
    assert result.b_family_learning_gain > 0.40
    assert result.c_family_learning_gain > 0.40
    assert result.old_family_interference >= 0.25
    assert result.final_old_family_score < result.initial_old_family_score
    assert result.replay_count == 0


def test_naive_protection_retains_old_family_better_while_slowing_novel_learning() -> None:
    result = run_long_horizon_interference_experiment().result
    naive = result.naive_protection
    baseline = result.no_consolidation

    assert naive.final_old_family_score > baseline.final_old_family_score
    assert naive.old_family_interference < baseline.old_family_interference
    assert (
        naive.final_b_family_score < baseline.final_b_family_score
        or naive.final_c_family_score < baseline.final_c_family_score
    )
    assert naive.replay_count == 0


def test_bounded_replay_uses_only_exact_candidate_sources_and_only_below_threshold() -> None:
    evidence = run_long_horizon_interference_experiment()
    result = evidence.result
    replay = result.bounded_retention_replay
    candidate_source_ids = set(result.consolidation_candidate.source_event_ids)

    assert replay.replay_count > 0
    assert set(replay.replay_source_event_ids).issubset(candidate_source_ids)
    assert all(score < result.config.retention_threshold for score in replay.replay_trigger_scores)
    assert result.replay_sources_resolved


def test_replay_bounds_floors_and_joint_advantage_hold() -> None:
    result = run_long_horizon_interference_experiment().result
    replay = result.bounded_retention_replay
    baseline_joint = max(result.no_consolidation.joint_score, result.naive_protection.joint_score)
    replay_steps = [step for step in replay.timeline if step.replay_applied]

    assert replay.replay_count == len(replay_steps)
    assert replay.replay_count <= result.config.maximum_total_replays
    assert all(step.task_family is not LongHorizonTaskFamily.FAMILY_A for step in replay_steps)
    assert replay.final_old_family_score >= result.config.minimum_old_family_retention_floor
    assert replay.final_b_family_score >= result.config.minimum_b_family_novel_learning_floor
    assert replay.final_c_family_score >= result.config.minimum_c_family_novel_learning_floor
    assert replay.joint_score >= baseline_joint + result.config.minimum_joint_score_advantage
    assert result.replay_bounded


def test_source_ledger_snapshot_trace_count_and_mastery_profile_remain_unchanged() -> None:
    evidence = run_long_horizon_interference_experiment()
    result = evidence.result

    assert evidence.source_ledger_snapshot == evidence.source_ledger_snapshot_after
    assert result.source_evidence_unchanged
    assert result.source_mastery_unchanged
    assert result.old_family_mastery_profile == result.source_mastery_profile_after
    assert '"trace_count":3' in evidence.source_ledger_snapshot


def test_zero_structural_drift_zero_authority_and_no_sqlite_hold() -> None:
    result = run_long_horizon_interference_experiment().result

    assert result.structure_unchanged
    assert result.action_authority_violation_count == 0
    assert not result.sqlite_used_for_experiment
    assert not result.action_selection_authority_used
    assert not result.recommendation_authority_used
    assert not result.scheduling_authority_used
    assert not result.execution_authority_used
    assert not result.live_integration_used
    assert not result.promotion_authority_used
    assert not result.production_action_authority_used
    for condition in (
        result.no_consolidation,
        result.naive_protection,
        result.bounded_retention_replay,
    ):
        assert condition.specialist_count_before == 0
        assert condition.specialist_count_after == 0
        assert condition.structural_growth_operation_count == 0
        assert condition.duplicate_specialist_membership_count == 0
        for step in condition.timeline:
            assert step.specialist_count_before == 0
            assert step.specialist_count_after == 0
            assert step.structural_growth_operation_count == 0
            assert step.duplicate_specialist_membership_count == 0


def test_exact_rerun_equality_ascii_snapshot_and_sha256_identity_are_stable() -> None:
    first = run_long_horizon_interference_experiment()
    second = run_long_horizon_interference_experiment()

    assert first == second
    assert first.result.pass_gate
    assert first.result.canonical_snapshot == second.result.canonical_snapshot
    assert first.result.canonical_snapshot.isascii()
    assert first.result.sha256_identity == second.result.sha256_identity


@pytest.mark.parametrize(
    ("field_name", "value"),
    [
        ("learning_rate", -0.01),
        ("stability_protection_weight", 1.01),
        ("old_training_passes", 0),
        ("horizon_steps", 32),
        ("maximum_replays_per_learning_step", 2),
        ("maximum_total_replays", 19),
    ],
)
def test_config_rejects_invalid_bounds_and_horizon(field_name: str, value: object) -> None:
    with pytest.raises(ValueError, match="must"):
        _build_invalid_config(field_name, value)


def test_nested_contract_validation_rejects_tampering() -> None:
    evidence = run_long_horizon_interference_experiment()
    result = evidence.result
    replay = result.bounded_retention_replay
    first_step = replay.timeline[0]
    replay_step = next(step for step in replay.timeline if step.replay_applied)

    with pytest.raises(ValueError, match="canonical snapshot"):
        validate_long_horizon_interference_result(
            replace(
                result,
                canonical_snapshot=result.canonical_snapshot + "x",
            )
        )
    with pytest.raises(ValueError, match="sha256 identity"):
        validate_long_horizon_interference_result(
            replace(
                result,
                sha256_identity="f" * 64,
            )
        )
    with pytest.raises(ValueError, match="action_selection_authority_used"):
        validate_long_horizon_interference_result(
            replace(
                result,
                action_selection_authority_used=True,
            )
        )
    with pytest.raises(ValueError, match="stable sorted ordering"):
        replace(
            result.consolidation_candidate,
            source_event_ids=tuple(reversed(result.consolidation_candidate.source_event_ids)),
        )
    with pytest.raises(ValueError, match="unique"):
        replace(
            result.consolidation_candidate,
            source_event_ids=(
                result.consolidation_candidate.source_event_ids[0],
                result.consolidation_candidate.source_event_ids[0],
                result.consolidation_candidate.source_event_ids[1],
            ),
        )
    tampered_replay = replace(
        replay,
        replay_source_event_ids=(
            "invalid:source",
            *replay.replay_source_event_ids[1:],
        ),
        timeline=tuple(
            replace(
                step,
                replay_source_event_id="invalid:source",
            )
            if step.step_index == replay_step.step_index
            else step
            for step in replay.timeline
        ),
    )
    with pytest.raises(
        ValueError,
        match="replay source ids must resolve to exact candidate source events",
    ):
        validate_long_horizon_interference_result(
            replace(
                result,
                bounded_retention_replay=tampered_replay,
            )
        )
    with pytest.raises(ValueError, match="exactly 36"):
        replace(replay, timeline=replay.timeline[1:])
    with pytest.raises(ValueError, match="contiguous"):
        validate_long_horizon_interference_result(
            replace(
                result,
                bounded_retention_replay=replace(
                    replay,
                    timeline=(
                        replace(first_step, step_index=1),
                        *replay.timeline[1:],
                    ),
                ),
            )
        )
    with pytest.raises(ValueError, match="replay steps require exact source id"):
        validate_long_horizon_interference_result(
            replace(
                result,
                bounded_retention_replay=replace(
                    replay,
                    timeline=(
                        replay.timeline[0],
                        replace(
                            replay.timeline[1], replay_applied=True, replay_source_event_id=None
                        ),
                        *replay.timeline[2:],
                    ),
                ),
            )
        )
    with pytest.raises(ValueError, match="zero structural counts"):
        validate_long_horizon_interference_result(
            replace(
                result,
                no_consolidation=replace(
                    result.no_consolidation,
                    specialist_count_after=1,
                ),
            )
        )
    with pytest.raises(ValueError, match="initial_old_family_score"):
        validate_long_horizon_interference_result(
            replace(
                result,
                bounded_retention_replay=replace(
                    replay,
                    initial_old_family_score=replay.initial_old_family_score - 0.01,
                ),
                canonical_snapshot=_rehashed_snapshot(
                    replace(
                        result,
                        bounded_retention_replay=replace(
                            replay,
                            initial_old_family_score=replay.initial_old_family_score - 0.01,
                        ),
                    )
                )[0],
                sha256_identity=_rehashed_snapshot(
                    replace(
                        result,
                        bounded_retention_replay=replace(
                            replay,
                            initial_old_family_score=replay.initial_old_family_score - 0.01,
                        ),
                    )
                )[1],
            )
        )
    with pytest.raises(ValueError, match="condition_pass_evidence"):
        replace(replay, condition_pass_evidence=not replay.condition_pass_evidence)
    with pytest.raises(ValueError, match="step old-family score"):
        replace(
            replay,
            timeline=(
                replace(
                    replay.timeline[0],
                    old_family_score_after=replay.timeline[0].old_family_score_after - 0.01,
                ),
                *replay.timeline[1:],
            ),
        )
    with pytest.raises(ValueError, match="timeline memory states must be contiguous"):
        replace(
            replay,
            timeline=(
                replay.timeline[0],
                replace(
                    replay.timeline[1],
                    memory_state_before=replay.timeline[1].memory_state_after,
                ),
                *replay.timeline[2:],
            ),
        )
    with pytest.raises(ValueError, match="probe and learning flags"):
        replace(
            replay,
            timeline=(
                replay.timeline[0],
                replace(
                    replay.timeline[1],
                    probe_only=True,
                    learning_applied=False,
                    memory_state_after=replay.timeline[1].memory_state_before,
                ),
                *replay.timeline[2:],
            ),
        )
    with pytest.raises(ValueError, match="baseline conditions must not contain replay"):
        replace(
            result.no_consolidation,
            replay_count=1,
            replay_source_event_ids=(result.consolidation_candidate.source_event_ids[0],),
            replay_trigger_scores=(0.5,),
            replay_step_indices=(1,),
            replay_bound_held=False,
            condition_pass_evidence=False,
        )
    with pytest.raises(ValueError, match="replay_bound_held"):
        replace(
            replay,
            replay_step_indices=(replay.replay_step_indices[0],) * replay.replay_count,
        )
    with pytest.raises(ValueError, match="bounded retention replay must contain"):
        replace(
            replay,
            replay_count=0,
            replay_source_event_ids=(),
            replay_trigger_scores=(),
            replay_step_indices=(),
            replay_bound_held=False,
            condition_pass_evidence=False,
        )
    tampered_result = replace(result, source_trace_count_before=2)
    snapshot, digest = _rehashed_snapshot(tampered_result)
    with pytest.raises(ValueError, match="source_trace_count_before"):
        validate_long_horizon_interference_result(
            replace(tampered_result, canonical_snapshot=snapshot, sha256_identity=digest)
        )
    tampered_result = replace(result, source_mastery_unchanged=False)
    snapshot, digest = _rehashed_snapshot(tampered_result)
    with pytest.raises(ValueError, match="source_mastery_unchanged"):
        validate_long_horizon_interference_result(
            replace(tampered_result, canonical_snapshot=snapshot, sha256_identity=digest)
        )
    tampered_result = replace(result, structure_unchanged=False)
    snapshot, digest = _rehashed_snapshot(tampered_result)
    with pytest.raises(ValueError, match="structure_unchanged"):
        validate_long_horizon_interference_result(
            replace(tampered_result, canonical_snapshot=snapshot, sha256_identity=digest)
        )
    tampered_result = replace(result, pass_gate=False)
    snapshot, digest = _rehashed_snapshot(tampered_result)
    with pytest.raises(ValueError, match="pass_gate"):
        validate_long_horizon_interference_result(
            replace(tampered_result, canonical_snapshot=snapshot, sha256_identity=digest)
        )


def test_evidence_validation_rejects_source_snapshot_mismatch() -> None:
    evidence = run_long_horizon_interference_experiment()
    altered_payload = json.loads(evidence.source_ledger_snapshot_after)
    altered_payload["trace_count"] = 4
    altered_snapshot = json.dumps(
        altered_payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    )

    with pytest.raises(ValueError, match="source snapshots"):
        replace(
            evidence,
            source_ledger_snapshot_after=altered_snapshot,
        )
    with pytest.raises(ValueError, match="canonical JSON"):
        replace(
            evidence,
            source_ledger_snapshot=evidence.source_ledger_snapshot + " ",
            source_ledger_snapshot_after=evidence.source_ledger_snapshot_after + " ",
        )
    with pytest.raises(ValueError, match="source snapshot before count"):
        replace(
            evidence,
            result=replace(
                evidence.result,
                source_trace_count_before=evidence.result.source_trace_count_before + 1,
            ),
        )


def test_static_dependency_exclusions_hold() -> None:
    source = (
        Path("src/seedmind/research/ndnra/long_horizon_interference_experiment.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    for forbidden in (
        "import sqlite3",
        "asyncio",
        "threading",
        "subprocess",
        "import sched",
        "import time",
        "from time import",
        "bounded_imagination",
        "seedmind.integration",
        "persistence",
        "import recommendation",
        "from recommendation",
        "executor import",
        "scheduler import",
        "production_action_control",
        "promotion import",
    ):
        assert forbidden not in source


def _build_invalid_config(
    field_name: str,
    value: object,
) -> LongHorizonInterferenceConfig:
    if field_name == "learning_rate":
        return LongHorizonInterferenceConfig(learning_rate=cast(float, value))
    if field_name == "stability_protection_weight":
        return LongHorizonInterferenceConfig(stability_protection_weight=cast(float, value))
    if field_name == "old_training_passes":
        return LongHorizonInterferenceConfig(old_training_passes=cast(int, value))
    if field_name == "horizon_steps":
        return LongHorizonInterferenceConfig(horizon_steps=cast(int, value))
    if field_name == "maximum_replays_per_learning_step":
        return LongHorizonInterferenceConfig(maximum_replays_per_learning_step=cast(int, value))
    return LongHorizonInterferenceConfig(maximum_total_replays=cast(int, value))


def _rehashed_snapshot(result: object) -> tuple[str, str]:
    snapshot = cast(Any, result).snapshot_payload()
    canonical = json.dumps(snapshot, ensure_ascii=True, sort_keys=True, separators=(",", ":"))
    digest = hashlib.sha256(canonical.encode("ascii")).hexdigest()
    return canonical, digest
