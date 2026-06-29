"""Tests for standalone NDNRA acceptance Batch 1 aggregation."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from pathlib import Path
from typing import Any, cast

import pytest

from seedmind.research.ndnra import (
    LearnedConsequenceModel,
    StandaloneAcceptanceAuthority,
    StandaloneAcceptanceDeltaReport,
    StandaloneAcceptanceResult,
    run_standalone_acceptance,
    validate_standalone_acceptance_result,
)
from seedmind.research.ndnra.experiment import run_ndnra_heat_fan_experiment
from seedmind.research.ndnra.growth_experiment import run_ndnra_structural_growth_experiment
from seedmind.research.ndnra.multieffect_experiment import run_ndnra_multieffect_experiment


def test_standalone_acceptance_preserves_complete_component_results() -> None:
    heat_fan_result, _ = run_ndnra_heat_fan_experiment()
    multieffect_result, _, _, _ = run_ndnra_multieffect_experiment()
    structural_growth_result, _, _, _ = run_ndnra_structural_growth_experiment()

    result = run_standalone_acceptance()

    assert result.heat_fan_result == heat_fan_result
    assert result.multieffect_result == multieffect_result
    assert result.structural_growth_result == structural_growth_result
    assert result.heat_fan_passed
    assert result.multieffect_passed
    assert result.structural_growth_passed
    assert result.sqlite_cognition_unused
    assert not result.observable_as_factual_consequence_evidence
    assert not result.checkpoint_restart_proof_included
    assert result.pass_gate


def test_standalone_acceptance_is_deterministic_across_repeated_runs() -> None:
    first = run_standalone_acceptance()
    second = run_standalone_acceptance()

    assert second == first
    assert second.canonical_ascii_snapshot == first.canonical_ascii_snapshot
    assert second.result_identity == first.result_identity


@pytest.mark.parametrize(
    ("mutator", "message"),
    [
        (
            lambda result: replace(result, heat_fan_passed=False),
            "heat-fan pass flag does not match component result",
        ),
        (
            lambda result: replace(
                result,
                deltas=StandaloneAcceptanceDeltaReport(
                    factual_confidence_delta=0.1,
                    mastery_delta=0.0,
                    competence_delta=0.0,
                    growth_delta=0.0,
                    replay_delta=0.0,
                    real_observation_delta=0.0,
                ),
            ),
            "standalone acceptance deltas must remain zero",
        ),
        (
            lambda result: replace(
                result,
                authority=StandaloneAcceptanceAuthority(
                    action_selection_authority=True,
                    production_action_authority=False,
                    recommendation_authority=False,
                    scheduling_authority=False,
                    execution_authority=False,
                    persistence_authority=False,
                    live_integration_authority=False,
                    promotion_authority=False,
                ),
            ),
            "standalone acceptance cannot grant authority",
        ),
        (
            lambda result: replace(result, observable_as_factual_consequence_evidence=True),
            "standalone acceptance cannot become factual consequence evidence",
        ),
        (
            lambda result: replace(result, result_identity="0" * 64),
            "result identity does not match canonical snapshot",
        ),
    ],
)
def test_standalone_acceptance_rejects_tampering(
    mutator: Callable[[StandaloneAcceptanceResult], StandaloneAcceptanceResult],
    message: str,
) -> None:
    result = run_standalone_acceptance()

    with pytest.raises(ValueError, match=message):
        validate_standalone_acceptance_result(mutator(result))


def test_standalone_acceptance_has_no_forbidden_authority_or_runtime_dependencies() -> None:
    source = Path("src/seedmind/research/ndnra/standalone_acceptance.py").read_text(
        encoding="utf-8"
    )
    lowered = source.lower()

    assert "sqlite3" not in lowered
    assert "asyncio" not in lowered
    assert "threading" not in lowered
    assert "timer" not in lowered
    assert "worker" not in lowered
    assert "subprocess" not in lowered
    assert "seedmind.integration" not in source


def test_standalone_acceptance_cannot_be_observed_as_factual_consequence_evidence() -> None:
    result = run_standalone_acceptance()
    model = LearnedConsequenceModel()
    before = model.snapshot()

    with pytest.raises((AttributeError, ValueError)):
        model.observe(cast(Any, result))

    assert model.snapshot() == before
    assert result.deltas == StandaloneAcceptanceDeltaReport(
        factual_confidence_delta=0.0,
        mastery_delta=0.0,
        competence_delta=0.0,
        growth_delta=0.0,
        replay_delta=0.0,
        real_observation_delta=0.0,
    )
    assert not result.observable_as_factual_consequence_evidence
    validate_standalone_acceptance_result(result)
