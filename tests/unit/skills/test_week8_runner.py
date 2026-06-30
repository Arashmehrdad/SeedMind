"""Acceptance tests for the deterministic Week 8 reusable-skill runner."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.skills import (
    DEFAULT_EVALUATION_SEEDS,
    DEFAULT_TRAINING_SEEDS,
    WEEK8_SUCCESS_TARGET,
    read_skill_record,
    run_week8_reusable_skill_evaluation,
)


def test_week8_runner_compiles_reuses_and_exports_evidence(tmp_path: Path) -> None:
    result = run_week8_reusable_skill_evaluation(output_dir=tmp_path)
    report = result.report

    assert report.pass_gate is True
    assert report.training_seeds == DEFAULT_TRAINING_SEEDS
    assert report.evaluation_seeds == DEFAULT_EVALUATION_SEEDS
    assert report.seed_overlap_count == 0
    assert report.success_rate >= WEEK8_SUCCESS_TARGET
    assert report.success_rate >= report.baseline_success_rate
    assert report.compilation_evidence_count >= 3
    assert report.skill_invocation_count >= len(DEFAULT_EVALUATION_SEEDS)
    assert report.reuse_count == len(DEFAULT_EVALUATION_SEEDS)
    assert report.discovery_count == 0
    assert report.evaluation_learning_attempts == 0
    assert report.authority_violations == 0
    assert report.ndnra_authority_violations == 0
    assert report.ndnra_automatic_promotions == 0
    assert all(episode.discovery_count == 0 for episode in result.evaluation_episodes)
    assert all(episode.reuse_count == 1 for episode in result.evaluation_episodes)
    assert (tmp_path / "approach_and_push_skill_record.json").exists()
    assert (tmp_path / "week8_generalisation_report.json").exists()


def test_week8_runner_rejects_training_evaluation_seed_overlap() -> None:
    with pytest.raises(ValueError, match="must not overlap"):
        run_week8_reusable_skill_evaluation(
            training_seeds=(1, 2, 3),
            evaluation_seeds=(3, *range(20, 39)),
        )


def test_week8_runner_requires_twenty_evaluation_episodes() -> None:
    with pytest.raises(ValueError, match="at least 20"):
        run_week8_reusable_skill_evaluation(
            training_seeds=(1, 2, 3),
            evaluation_seeds=tuple(range(10, 20)),
        )


def test_exported_skill_record_is_inspectable_and_loadable(tmp_path: Path) -> None:
    result = run_week8_reusable_skill_evaluation(output_dir=tmp_path)

    loaded = read_skill_record(tmp_path / "approach_and_push_skill_record.json")

    assert loaded == result.skill_record
    assert loaded.name == "approach_and_push"
    assert loaded.reuse_count == len(DEFAULT_EVALUATION_SEEDS)
    assert "target_object_id exists" in loaded.preconditions
