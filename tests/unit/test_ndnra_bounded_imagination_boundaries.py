"""Additional boundary tests for non-factual bounded imagination."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

import pytest

from seedmind.research.ndnra import (
    BoundedConsequenceImagination,
    ConsequenceModelObservation,
    ContextSignature,
    EffectObservation,
    ExperienceOrigin,
    ImaginedActionSequence,
    ImaginedConsequenceRequest,
    LearnedConsequenceModel,
)


def _model_and_context() -> tuple[LearnedConsequenceModel, ContextSignature]:
    start = ContextSignature.from_values(
        active_need_code="cooling",
        sensor_values=(0.8,),
        available_action_codes=("cool",),
    )
    final = ContextSignature.from_values(
        active_need_code="cooling",
        sensor_values=(0.3,),
        available_action_codes=("wait",),
    )
    model = LearnedConsequenceModel()
    model.observe(
        ConsequenceModelObservation(
            event_id="real:bounded-imagination:boundary:0001",
            origin=ExperienceOrigin.REAL,
            context=start,
            action_code="cool",
            next_context=final,
            observed_effects=(EffectObservation("heat_delta", -0.5, 1.0),),
        )
    )
    return model, start


def _trace() -> tuple[LearnedConsequenceModel, object]:
    model, start = _model_and_context()
    result = BoundedConsequenceImagination(model).imagine(
        ImaginedConsequenceRequest(
            context=start,
            relevant_effect_codes=("heat_delta",),
            candidate_sequences=(ImaginedActionSequence(("cool",)),),
        )
    )
    return model, result.traces[0]


def test_trace_is_explicitly_imagined_and_non_authoritative() -> None:
    _, raw_trace = _trace()
    trace = cast(Any, raw_trace)

    assert trace.origin is ExperienceOrigin.IMAGINED
    assert all(step.origin is ExperienceOrigin.IMAGINED for step in trace.steps)
    assert trace.snapshot()["origin"] == "imagined"
    assert trace.factual_confidence_change == 0.0
    assert trace.mastery_change == 0.0
    assert trace.competence_change == 0.0
    assert trace.growth_pressure_change == 0.0
    assert trace.replay_evidence_change == 0.0
    assert trace.real_observation_change == 0.0
    assert not trace.has_action_selection_authority
    assert not trace.has_production_action_authority


def test_actual_imagined_trace_cannot_update_real_consequence_evidence() -> None:
    model, trace = _trace()
    before = model.snapshot()

    with pytest.raises(ValueError, match="only real observations"):
        model.observe(cast(Any, trace))

    assert model.snapshot() == before


def test_module_imports_no_forbidden_cognitive_or_execution_subsystems() -> None:
    source = Path("src/seedmind/research/ndnra/bounded_imagination.py").read_text(encoding="ascii")
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_prefixes = (
        "sqlite3",
        "asyncio",
        "threading",
        "time",
        "seedmind.integration",
        "seedmind.environment",
        "seedmind.curiosity",
        "seedmind.research.ndnra.contextual_consequence_transfer",
        "seedmind.research.ndnra.composition",
        "seedmind.research.ndnra.persistence",
        "seedmind.research.ndnra.growth",
        "seedmind.research.ndnra.controlled_retention_replay",
    )
    for forbidden in forbidden_prefixes:
        assert not any(
            module == forbidden or module.startswith(f"{forbidden}.") for module in imported_modules
        )

    lowered = source.lower()
    assert "optimise(" not in lowered
    assert "optimize(" not in lowered
    assert "experiment_promotion" not in lowered
