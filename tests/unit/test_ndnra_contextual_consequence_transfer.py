"""Tests for bounded contextual transfer over exact consequence records."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.contextual_consequence_transfer import (
    BoundedContextualTransferPolicy,
    ConsequencePredictionMode,
    ContextualTransferConfig,
)
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.learned_consequence_model import (
    ConsequenceModelObservation,
    ConsequencePredictionRequest,
    LearnedConsequenceModel,
)


def _context(
    *,
    inside_heat: float,
    outside_heat: float,
    need_code: str = "reduce_temperature",
    actions: tuple[str, ...] = ("open_window", "start_fan"),
    human_values: tuple[float, ...] = (),
    resource_values: tuple[float, ...] = (0.8,),
    extra_sensor: float | None = None,
) -> ContextSignature:
    sensors = (
        (inside_heat, outside_heat)
        if extra_sensor is None
        else (inside_heat, outside_heat, extra_sensor)
    )
    return ContextSignature.from_values(
        active_need_code=need_code,
        sensor_values=sensors,
        available_action_codes=actions,
        human_values=human_values,
        resource_values=resource_values,
    )


def _request(
    context: ContextSignature,
    *,
    action_code: str = "open_window",
    effect_codes: tuple[str, ...] = ("energy_cost", "temperature"),
) -> ConsequencePredictionRequest:
    return ConsequencePredictionRequest(
        context=context,
        action_code=action_code,
        relevant_effect_codes=effect_codes,
    )


def _observe(
    model: LearnedConsequenceModel,
    *,
    event_id: str,
    context: ContextSignature,
    next_context: ContextSignature,
    temperature_effect: float,
    energy_effect: float = 0.0,
    action_code: str = "open_window",
    temperature_confidence: float = 1.0,
    include_energy: bool = True,
) -> None:
    effects = [
        EffectObservation(
            "temperature",
            temperature_effect,
            temperature_confidence,
        )
    ]
    if include_energy:
        effects.append(EffectObservation("energy_cost", energy_effect, 1.0))
    effects.sort(key=lambda item: item.effect_code)
    model.observe(
        ConsequenceModelObservation(
            event_id=event_id,
            origin=ExperienceOrigin.REAL,
            context=context,
            action_code=action_code,
            next_context=next_context,
            observed_effects=tuple(effects),
        )
    )


def test_exact_context_evidence_always_wins_over_transfer() -> None:
    exact_context = _context(inside_heat=0.8, outside_heat=0.4)
    similar_context = _context(inside_heat=0.8, outside_heat=0.3)
    exact_after = _context(inside_heat=0.5, outside_heat=0.4)
    similar_after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:exact",
        context=exact_context,
        next_context=exact_after,
        temperature_effect=-0.3,
    )
    _observe(
        model,
        event_id="real:transfer:similar",
        context=similar_context,
        next_context=similar_after,
        temperature_effect=-0.7,
    )
    policy = BoundedContextualTransferPolicy()

    result = policy.predict(model, _request(exact_context))

    assert result.mode is ConsequencePredictionMode.EXACT
    assert result.predicted_next_context == exact_after
    assert result.supporting_real_event_ids == ("real:transfer:exact",)
    assert result.considered_similarities == ()
    assert result.transfer_sources == ()
    assert result.transferred_effects == ()
    assert result.transfer_coverage == 0.0
    assert result.contradiction_score == 0.0


def test_similar_context_produces_explicit_attenuated_transfer() -> None:
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    target_context = _context(inside_heat=0.8, outside_heat=0.4)
    source_after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:source",
        context=source_context,
        next_context=source_after,
        temperature_effect=-0.5,
        energy_effect=-0.1,
    )
    policy = BoundedContextualTransferPolicy()
    source_exact = model.predict(_request(source_context))

    result = policy.predict(model, _request(target_context))

    assert result.mode is ConsequencePredictionMode.TRANSFERRED
    assert result.predicted_next_context is None
    assert result.effect_coverage == 1.0
    assert result.source_coverage == 1.0
    assert 0.0 < result.transfer_coverage < 1.0
    assert 0.0 < result.confidence < source_exact.calibrated_confidence
    assert result.confidence <= policy.config.maximum_transferred_confidence
    assert result.supporting_real_event_ids == ("real:transfer:source",)
    assert len(result.considered_similarities) == 1
    similarity = result.considered_similarities[0]
    assert similarity.active_need_match
    assert similarity.action_available_in_target
    assert similarity.action_available_in_source
    assert similarity.shape_compatible
    assert similarity.sensor_similarity == pytest.approx(0.95)
    assert similarity.action_similarity == 1.0
    assert similarity.resource_similarity == 1.0
    assert similarity.eligible
    assert len(result.transfer_sources) == 1
    source = result.transfer_sources[0]
    assert source.attenuation < 1.0
    assert source.effective_confidence < source.source_confidence
    assert not result.has_action_selection_authority
    assert not result.has_production_action_authority


def test_exact_partial_record_is_not_silently_filled_from_transfer() -> None:
    target_context = _context(inside_heat=0.8, outside_heat=0.4)
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    target_after = _context(inside_heat=0.5, outside_heat=0.4)
    source_after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:partial-exact",
        context=target_context,
        next_context=target_after,
        temperature_effect=-0.3,
        include_energy=False,
    )
    _observe(
        model,
        event_id="real:transfer:complete-source",
        context=source_context,
        next_context=source_after,
        temperature_effect=-0.5,
        energy_effect=-0.2,
    )

    result = BoundedContextualTransferPolicy().predict(
        model,
        _request(target_context),
    )

    assert result.mode is ConsequencePredictionMode.EXACT
    assert tuple(item.effect_code for item in result.predicted_effects) == ("temperature",)
    assert result.effect_coverage == pytest.approx(0.5)
    assert result.supporting_real_event_ids == ("real:transfer:partial-exact",)
    assert result.transfer_sources == ()


def test_need_action_and_shape_mismatches_remain_unknown() -> None:
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    source_after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:structural-source",
        context=source_context,
        next_context=source_after,
        temperature_effect=-0.5,
    )
    policy = BoundedContextualTransferPolicy()

    different_need = policy.predict(
        model,
        _request(
            _context(
                inside_heat=0.8,
                outside_heat=0.4,
                need_code="increase_temperature",
            )
        ),
    )
    unavailable_action = policy.predict(
        model,
        _request(
            _context(
                inside_heat=0.8,
                outside_heat=0.4,
                actions=("start_fan",),
            )
        ),
    )
    incompatible_shape = policy.predict(
        model,
        _request(
            _context(
                inside_heat=0.8,
                outside_heat=0.4,
                extra_sensor=0.2,
            )
        ),
    )

    for result in (different_need, unavailable_action, incompatible_shape):
        assert result.mode is ConsequencePredictionMode.UNKNOWN
        assert result.predicted_effects == ()
        assert result.confidence == 0.0
        assert result.uncertainty == 1.0
        assert len(result.considered_similarities) == 1
        assert not result.considered_similarities[0].eligible
    assert not different_need.considered_similarities[0].active_need_match
    assert not unavailable_action.considered_similarities[0].action_available_in_target
    assert not incompatible_shape.considered_similarities[0].shape_compatible


def test_different_action_never_borrows_source_evidence() -> None:
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    target_context = _context(inside_heat=0.8, outside_heat=0.4)
    source_after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:window-only",
        context=source_context,
        next_context=source_after,
        temperature_effect=-0.5,
        action_code="open_window",
    )

    result = BoundedContextualTransferPolicy().predict(
        model,
        _request(target_context, action_code="start_fan"),
    )

    assert result.mode is ConsequencePredictionMode.UNKNOWN
    assert result.considered_similarities == ()
    assert result.supporting_real_event_ids == ()


def test_one_source_cannot_create_broad_certainty() -> None:
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    target_context = _context(inside_heat=0.8, outside_heat=0.4)
    source_after = _context(inside_heat=0.4, outside_heat=0.3)
    model = LearnedConsequenceModel()
    for index in range(8):
        _observe(
            model,
            event_id=f"real:transfer:repeated:{index}",
            context=source_context,
            next_context=source_after,
            temperature_effect=-0.5,
        )

    result = BoundedContextualTransferPolicy().predict(
        model,
        _request(target_context),
    )

    assert result.mode is ConsequencePredictionMode.TRANSFERRED
    assert len(result.transfer_sources) == 1
    assert result.confidence <= 0.5
    assert result.confidence <= result.transfer_coverage
    assert result.uncertainty >= 0.5


def test_consistent_sources_raise_support_but_respect_transfer_cap() -> None:
    target_context = _context(inside_heat=0.8, outside_heat=0.5)
    source_contexts = (
        _context(inside_heat=0.8, outside_heat=0.3),
        _context(inside_heat=0.8, outside_heat=0.4),
        _context(inside_heat=0.8, outside_heat=0.6),
    )
    model = LearnedConsequenceModel()
    for index, source_context in enumerate(source_contexts):
        _observe(
            model,
            event_id=f"real:transfer:consistent-source:{index}",
            context=source_context,
            next_context=_context(inside_heat=0.4, outside_heat=0.5),
            temperature_effect=-0.5,
        )
    one_source_policy = BoundedContextualTransferPolicy(
        ContextualTransferConfig(maximum_transfer_sources=1)
    )
    three_source_policy = BoundedContextualTransferPolicy(
        ContextualTransferConfig(maximum_transfer_sources=3)
    )

    one_source = one_source_policy.predict(model, _request(target_context))
    three_sources = three_source_policy.predict(model, _request(target_context))

    assert one_source.mode is ConsequencePredictionMode.TRANSFERRED
    assert three_sources.mode is ConsequencePredictionMode.TRANSFERRED
    assert len(one_source.transfer_sources) == 1
    assert len(three_sources.transfer_sources) == 3
    assert three_sources.confidence > one_source.confidence
    assert three_sources.confidence <= three_source_policy.config.maximum_transferred_confidence
    assert three_sources.contradiction_score == 0.0


def test_opposing_sources_surface_contradiction_and_remove_confidence() -> None:
    target_context = _context(inside_heat=0.8, outside_heat=0.5)
    cooler_source = _context(inside_heat=0.8, outside_heat=0.4)
    hotter_source = _context(inside_heat=0.8, outside_heat=0.6)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:cooling-source",
        context=cooler_source,
        next_context=_context(inside_heat=0.4, outside_heat=0.4),
        temperature_effect=-0.5,
        include_energy=False,
    )
    _observe(
        model,
        event_id="real:transfer:warming-source",
        context=hotter_source,
        next_context=_context(inside_heat=0.9, outside_heat=0.6),
        temperature_effect=0.5,
        include_energy=False,
    )

    result = BoundedContextualTransferPolicy().predict(
        model,
        _request(target_context, effect_codes=("temperature",)),
    )

    assert result.mode is ConsequencePredictionMode.TRANSFERRED
    assert len(result.transfer_sources) == 2
    assert result.predicted_effects[0].value == pytest.approx(0.0)
    assert result.transferred_effects[0].contradiction_score == pytest.approx(1.0)
    assert result.contradiction_score == pytest.approx(1.0)
    assert result.predicted_effects[0].confidence == 0.0
    assert result.confidence == 0.0
    assert result.uncertainty == 1.0


def test_missing_source_effect_dimension_remains_unknown() -> None:
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    target_context = _context(inside_heat=0.8, outside_heat=0.4)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:temperature-only",
        context=source_context,
        next_context=_context(inside_heat=0.4, outside_heat=0.3),
        temperature_effect=-0.5,
        include_energy=False,
    )

    result = BoundedContextualTransferPolicy().predict(
        model,
        _request(target_context),
    )

    assert result.mode is ConsequencePredictionMode.TRANSFERRED
    assert tuple(item.effect_code for item in result.predicted_effects) == ("temperature",)
    assert result.effect_coverage == pytest.approx(0.5)
    assert result.transfer_coverage < 0.5


def test_zero_confidence_source_cannot_support_transfer() -> None:
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    target_context = _context(inside_heat=0.8, outside_heat=0.4)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:zero-confidence",
        context=source_context,
        next_context=_context(inside_heat=0.4, outside_heat=0.3),
        temperature_effect=-0.5,
        temperature_confidence=0.0,
        include_energy=False,
    )

    result = BoundedContextualTransferPolicy().predict(
        model,
        _request(target_context, effect_codes=("temperature",)),
    )

    assert result.mode is ConsequencePredictionMode.UNKNOWN
    assert len(result.considered_similarities) == 1
    assert result.considered_similarities[0].eligible
    assert result.transfer_sources == ()


def test_transfer_prediction_is_pure_and_does_not_mutate_exact_model() -> None:
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    target_context = _context(inside_heat=0.8, outside_heat=0.4)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:pure",
        context=source_context,
        next_context=_context(inside_heat=0.4, outside_heat=0.3),
        temperature_effect=-0.5,
    )
    before = model.snapshot()
    policy = BoundedContextualTransferPolicy()

    first = policy.predict(model, _request(target_context))
    second = policy.predict(model, _request(target_context))

    assert first == second
    assert model.snapshot() == before
    with pytest.raises(ValueError, match="no consequence record"):
        model.record_for(target_context, "open_window")


def test_candidate_and_source_limits_are_enforced_deterministically() -> None:
    target_context = _context(inside_heat=0.8, outside_heat=0.5)
    model = LearnedConsequenceModel()
    for index, outside_heat in enumerate((0.3, 0.4, 0.6)):
        source_context = _context(inside_heat=0.8, outside_heat=outside_heat)
        _observe(
            model,
            event_id=f"real:transfer:bounded-source:{index}",
            context=source_context,
            next_context=_context(inside_heat=0.4, outside_heat=outside_heat),
            temperature_effect=-0.5,
        )

    with pytest.raises(ValueError, match="candidate bound"):
        BoundedContextualTransferPolicy(
            ContextualTransferConfig(maximum_contexts_considered=2)
        ).predict(model, _request(target_context))

    limited = BoundedContextualTransferPolicy(
        ContextualTransferConfig(maximum_transfer_sources=2)
    ).predict(model, _request(target_context))

    assert limited.mode is ConsequencePredictionMode.TRANSFERRED
    assert len(limited.considered_similarities) == 3
    assert len(limited.transfer_sources) == 2
    assert tuple(source.source_record_id for source in limited.transfer_sources) == tuple(
        source.source_record_id
        for source in sorted(
            limited.transfer_sources,
            key=lambda item: (
                -item.similarity.combined_similarity,
                -item.effective_confidence,
                item.source_record_id,
            ),
        )
    )


def test_transfer_snapshots_are_ascii_deterministic_and_inspectable() -> None:
    source_context = _context(inside_heat=0.8, outside_heat=0.3)
    target_context = _context(inside_heat=0.8, outside_heat=0.4)
    model = LearnedConsequenceModel()
    _observe(
        model,
        event_id="real:transfer:snapshot",
        context=source_context,
        next_context=_context(inside_heat=0.4, outside_heat=0.3),
        temperature_effect=-0.5,
    )
    policy = BoundedContextualTransferPolicy()

    first = policy.predict(model, _request(target_context)).snapshot()
    second = policy.predict(model, _request(target_context)).snapshot()

    assert first == second
    assert str(first).isascii()
    assert first["mode"] == "transferred"
    assert first["predicted_next_context"] is None
    assert first["has_action_selection_authority"] is False
    assert first["has_production_action_authority"] is False


def test_transfer_configuration_and_authority_contracts_are_enforced() -> None:
    with pytest.raises(ValueError, match="positive integer"):
        ContextualTransferConfig(maximum_transfer_sources=0)
    with pytest.raises(ValueError, match="finite and positive"):
        ContextualTransferConfig(context_bin_distance_scale=0.0)
    with pytest.raises(ValueError, match="at least one"):
        ContextualTransferConfig(
            sensor_weight=0.0,
            action_weight=0.0,
            human_weight=0.0,
            resource_weight=0.0,
        )
    with pytest.raises(ValueError, match="cannot select actions"):
        BoundedContextualTransferPolicy(has_action_selection_authority=True)
    with pytest.raises(ValueError, match="cannot control production actions"):
        BoundedContextualTransferPolicy(has_production_action_authority=True)

    policy = BoundedContextualTransferPolicy()
    with pytest.raises(ValueError, match="cannot select actions"):
        replace(policy, has_action_selection_authority=True)


def test_transfer_module_has_no_execution_persistence_or_background_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/contextual_consequence_transfer.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert ".step(" not in source
    assert ".compose(" not in source
    assert ".apply(" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "optimizer" not in source
    assert "rollout" not in source
    assert "seedmind.integration" not in source
