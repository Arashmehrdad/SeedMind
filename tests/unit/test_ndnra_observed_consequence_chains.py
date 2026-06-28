"""Tests for bounded observed consequence chains."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.contextual_consequence_transfer import (
    BoundedContextualTransferPolicy,
)
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.learned_consequence_model import (
    ConsequenceModelObservation,
    ConsequencePredictionRequest,
    LearnedConsequenceModel,
)
from seedmind.research.ndnra.observed_consequence_chains import (
    ConsequenceChainPredictionRequest,
    ObservedConsequenceChain,
    ObservedConsequenceChainConfig,
    ObservedConsequenceChainModel,
)


def _context(*, inside_heat: float, outside_heat: float = 0.3) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code="reduce_temperature",
        sensor_values=(inside_heat, outside_heat),
        available_action_codes=("open_window", "start_fan", "wait"),
        resource_values=(0.8,),
    )


def _observation(
    *,
    event_id: str,
    context: ContextSignature,
    action_code: str,
    next_context: ContextSignature,
    temperature_effect: float,
    energy_effect: float | None = 0.0,
    origin: ExperienceOrigin = ExperienceOrigin.REAL,
) -> ConsequenceModelObservation:
    effects = [EffectObservation("temperature", temperature_effect, 1.0)]
    if energy_effect is not None:
        effects.append(EffectObservation("energy_cost", energy_effect, 1.0))
    effects.sort(key=lambda item: item.effect_code)
    return ConsequenceModelObservation(
        event_id=event_id,
        origin=origin,
        context=context,
        action_code=action_code,
        next_context=next_context,
        observed_effects=tuple(effects),
    )


def _chain(
    *,
    first_event_id: str = "real:chain:001",
    second_event_id: str = "real:chain:002",
    first_action: str = "open_window",
    second_action: str = "start_fan",
    start_heat: float = 0.9,
    middle_heat: float = 0.7,
    final_heat: float = 0.4,
    first_temperature_effect: float = -0.2,
    second_temperature_effect: float = -0.3,
    second_final: ContextSignature | None = None,
) -> ObservedConsequenceChain:
    start = _context(inside_heat=start_heat)
    middle = _context(inside_heat=middle_heat)
    final = _context(inside_heat=final_heat) if second_final is None else second_final
    return ObservedConsequenceChain.from_observations(
        (
            _observation(
                event_id=first_event_id,
                context=start,
                action_code=first_action,
                next_context=middle,
                temperature_effect=first_temperature_effect,
            ),
            _observation(
                event_id=second_event_id,
                context=middle,
                action_code=second_action,
                next_context=final,
                temperature_effect=second_temperature_effect,
                energy_effect=-0.1,
            ),
        )
    )


def _request(
    start_context: ContextSignature,
    *,
    action_codes: tuple[str, ...] = ("open_window", "start_fan"),
    effect_codes: tuple[str, ...] = ("energy_cost", "temperature"),
) -> ConsequenceChainPredictionRequest:
    return ConsequenceChainPredictionRequest(
        start_context=start_context,
        action_codes=action_codes,
        relevant_effect_codes=effect_codes,
    )


def test_valid_two_step_real_chain_preserves_order_and_provenance() -> None:
    chain = _chain()
    model = ObservedConsequenceChainModel()

    update = model.observe(chain)
    prediction = model.predict(_request(chain.start_context))

    assert update.evidence_applied
    assert update.chain_count_before == 0
    assert update.chain_count_after == 1
    assert chain.action_codes == ("open_window", "start_fan")
    assert chain.source_event_ids == ("real:chain:001", "real:chain:002")
    assert prediction.predicted_final_context == chain.final_context
    assert prediction.supporting_chain_ids == (chain.chain_id,)
    assert prediction.supporting_real_event_ids == chain.source_event_ids
    assert prediction.independent_chain_group_count == 1
    assert len(prediction.step_predictions) == 2
    assert prediction.step_predictions[0].action_code == "open_window"
    assert prediction.step_predictions[1].action_code == "start_fan"
    assert not prediction.has_action_selection_authority
    assert not prediction.has_production_action_authority


def test_reversed_action_order_is_distinct_and_does_not_share_support() -> None:
    forward = _chain()
    reversed_order = _chain(
        first_event_id="real:chain:reverse:001",
        second_event_id="real:chain:reverse:002",
        first_action="start_fan",
        second_action="open_window",
    )
    model = ObservedConsequenceChainModel()

    model.observe(forward)
    model.observe(reversed_order)
    forward_prediction = model.predict(_request(forward.start_context))
    reverse_prediction = model.predict(
        _request(
            reversed_order.start_context,
            action_codes=("start_fan", "open_window"),
        )
    )

    assert forward.chain_id != reversed_order.chain_id
    assert forward_prediction.supporting_chain_ids == (forward.chain_id,)
    assert reverse_prediction.supporting_chain_ids == (reversed_order.chain_id,)
    assert forward_prediction.request.action_codes != reverse_prediction.request.action_codes


def test_disconnected_contexts_are_rejected_atomically() -> None:
    start = _context(inside_heat=0.9)
    middle = _context(inside_heat=0.7)
    disconnected = _context(inside_heat=0.2)
    final = _context(inside_heat=0.4)
    model = ObservedConsequenceChainModel()
    snapshot_before = model.snapshot()

    with pytest.raises(ValueError, match="continuity is disconnected"):
        model.observe(
            ObservedConsequenceChain.from_observations(
                (
                    _observation(
                        event_id="real:chain:broken:001",
                        context=start,
                        action_code="open_window",
                        next_context=middle,
                        temperature_effect=-0.2,
                    ),
                    _observation(
                        event_id="real:chain:broken:002",
                        context=disconnected,
                        action_code="start_fan",
                        next_context=final,
                        temperature_effect=-0.3,
                    ),
                )
            )
        )
    assert model.snapshot() == snapshot_before


def test_one_event_cannot_appear_twice_in_one_chain() -> None:
    start = _context(inside_heat=0.9)
    middle = _context(inside_heat=0.7)

    with pytest.raises(ValueError, match="more than once"):
        ObservedConsequenceChain.from_observations(
            (
                _observation(
                    event_id="real:chain:repeat",
                    context=start,
                    action_code="wait",
                    next_context=middle,
                    temperature_effect=0.0,
                ),
                _observation(
                    event_id="real:chain:repeat",
                    context=middle,
                    action_code="wait",
                    next_context=start,
                    temperature_effect=0.0,
                ),
            )
        )


def test_exact_duplicate_chain_is_ignored_without_multiplying_support() -> None:
    chain = _chain()
    model = ObservedConsequenceChainModel()

    first = model.observe(chain)
    duplicate = model.observe(chain)
    prediction = model.predict(_request(chain.start_context))

    assert first.evidence_applied
    assert not duplicate.evidence_applied
    assert model.chain_count == 1
    assert prediction.independent_chain_group_count == 1
    assert prediction.supporting_chain_ids == (chain.chain_id,)


def test_conflicting_reuse_of_chain_identity_is_rejected() -> None:
    chain = _chain()
    conflicting = _chain(
        first_temperature_effect=0.4,
        second_temperature_effect=-0.3,
    )
    model = ObservedConsequenceChainModel()
    model.observe(chain)
    snapshot_before = model.snapshot()

    assert conflicting.chain_id == chain.chain_id
    with pytest.raises(ValueError, match="chain identity conflict"):
        model.observe(conflicting)
    assert model.snapshot() == snapshot_before


def test_source_event_identity_conflict_is_rejected_across_overlapping_chains() -> None:
    chain = _chain()
    conflicting_reuse = _chain(
        second_event_id="real:chain:other:002",
        middle_heat=0.6,
        final_heat=0.3,
    )
    model = ObservedConsequenceChainModel()
    model.observe(chain)

    with pytest.raises(ValueError, match="source event identity conflict"):
        model.observe(conflicting_reuse)


def test_replay_and_imagined_steps_cannot_become_chain_evidence() -> None:
    start = _context(inside_heat=0.9)
    final = _context(inside_heat=0.7)

    for origin in (ExperienceOrigin.REPLAY, ExperienceOrigin.IMAGINED):
        with pytest.raises(ValueError, match="real origin"):
            ObservedConsequenceChain.from_observations(
                (
                    _observation(
                        event_id=f"{origin.value}:chain:001",
                        origin=origin,
                        context=start,
                        action_code="open_window",
                        next_context=final,
                        temperature_effect=-0.2,
                    ),
                )
            )


def test_depth_effect_dimension_and_total_chain_bounds_are_atomic() -> None:
    model = ObservedConsequenceChainModel(
        ObservedConsequenceChainConfig(
            maximum_chain_depth=1,
            maximum_chains=1,
            maximum_effect_dimensions=1,
        )
    )
    accepted = ObservedConsequenceChain.from_observations(
        (
            _observation(
                event_id="real:chain:bounded:001",
                context=_context(inside_heat=0.9),
                action_code="wait",
                next_context=_context(inside_heat=0.8),
                temperature_effect=-0.1,
                energy_effect=None,
            ),
        )
    )
    model.observe(accepted)
    snapshot_before = model.snapshot()

    with pytest.raises(ValueError, match="depth bound"):
        model.observe(
            _chain(
                first_event_id="real:chain:depth:001",
                second_event_id="real:chain:depth:002",
            )
        )
    assert model.snapshot() == snapshot_before

    with pytest.raises(ValueError, match="chain bound"):
        model.observe(
            ObservedConsequenceChain.from_observations(
                (
                    _observation(
                        event_id="real:chain:total:001",
                        context=_context(inside_heat=0.6),
                        action_code="wait",
                        next_context=_context(inside_heat=0.5),
                        temperature_effect=-0.1,
                        energy_effect=None,
                    ),
                )
            )
        )
    assert model.snapshot() == snapshot_before

    dimension_bounded = ObservedConsequenceChainModel(
        ObservedConsequenceChainConfig(maximum_effect_dimensions=1)
    )
    with pytest.raises(ValueError, match="effect-dimension bound"):
        dimension_bounded.observe(_chain())
    assert dimension_bounded.chain_count == 0


def test_missing_effect_dimensions_remain_unknown() -> None:
    start = _context(inside_heat=0.9)
    final = _context(inside_heat=0.7)
    chain = ObservedConsequenceChain.from_observations(
        (
            _observation(
                event_id="real:chain:partial",
                context=start,
                action_code="open_window",
                next_context=final,
                temperature_effect=-0.2,
                energy_effect=None,
            ),
        )
    )
    model = ObservedConsequenceChainModel()
    model.observe(chain)

    prediction = model.predict(
        _request(
            chain.start_context,
            action_codes=("open_window",),
        )
    )

    assert prediction.effect_coverage == pytest.approx(0.5)
    assert tuple(
        effect.effect_code for effect in prediction.step_predictions[0].predicted_effects
    ) == ("temperature",)


def test_contradictory_chains_lower_confidence_and_remain_inspectable() -> None:
    start = _context(inside_heat=0.9)
    final = _context(inside_heat=0.7)
    cooling = ObservedConsequenceChain.from_observations(
        (
            _observation(
                event_id="real:chain:cooling",
                context=start,
                action_code="open_window",
                next_context=final,
                temperature_effect=-0.5,
                energy_effect=None,
            ),
        )
    )
    warming = ObservedConsequenceChain.from_observations(
        (
            _observation(
                event_id="real:chain:warming",
                context=start,
                action_code="open_window",
                next_context=final,
                temperature_effect=0.5,
                energy_effect=None,
            ),
        )
    )
    model = ObservedConsequenceChainModel()
    model.observe(cooling)
    model.observe(warming)

    prediction = model.predict(
        _request(
            start,
            action_codes=("open_window",),
            effect_codes=("temperature",),
        )
    )

    assert prediction.independent_chain_group_count == 2
    assert prediction.contradiction_score == pytest.approx(1.0)
    assert prediction.step_predictions[0].contradiction_score == pytest.approx(1.0)
    assert prediction.step_predictions[0].predicted_effects[0].confidence == 0.0
    assert prediction.confidence == 0.0
    assert prediction.uncertainty == 1.0


def test_overlapping_chains_do_not_count_as_fully_independent_support() -> None:
    shared_start = _context(inside_heat=0.9)
    shared_middle = _context(inside_heat=0.7)
    first_chain = _chain()
    overlapping = ObservedConsequenceChain.from_observations(
        (
            _observation(
                event_id="real:chain:001",
                context=shared_start,
                action_code="open_window",
                next_context=shared_middle,
                temperature_effect=-0.2,
            ),
            _observation(
                event_id="real:chain:overlap:002",
                context=shared_middle,
                action_code="start_fan",
                next_context=_context(inside_heat=0.3),
                temperature_effect=-0.4,
                energy_effect=-0.1,
            ),
        )
    )
    model = ObservedConsequenceChainModel()
    model.observe(first_chain)
    model.observe(overlapping)

    prediction = model.predict(_request(first_chain.start_context))

    assert prediction.independent_chain_group_count == 1
    assert len(prediction.correlated_chain_groups) == 1
    assert len(prediction.correlated_chain_groups[0].chain_ids) == 2
    assert prediction.supporting_real_event_ids == (
        "real:chain:001",
        "real:chain:002",
        "real:chain:overlap:002",
    )
    assert prediction.final_context_confidence < 0.5


def test_unknown_action_sequence_returns_complete_uncertainty() -> None:
    model = ObservedConsequenceChainModel()
    prediction = model.predict(
        _request(
            _context(inside_heat=0.9),
            action_codes=("start_fan", "open_window"),
        )
    )

    assert prediction.predicted_final_context is None
    assert prediction.step_predictions == ()
    assert prediction.effect_coverage == 0.0
    assert prediction.evidence_coverage == 0.0
    assert prediction.final_context_confidence == 0.0
    assert prediction.confidence == 0.0
    assert prediction.uncertainty == 1.0
    assert prediction.supporting_chain_ids == ()
    assert prediction.supporting_real_event_ids == ()


def test_exact_observed_order_may_predict_final_context_but_bridge_may_not() -> None:
    chain = _chain()
    bridged_start = _context(inside_heat=0.6)
    model = ObservedConsequenceChainModel()
    model.observe(chain)

    exact = model.predict(_request(chain.start_context))
    bridged = model.predict(_request(bridged_start))

    assert exact.predicted_final_context == chain.final_context
    assert exact.supporting_real_event_ids == chain.source_event_ids
    assert bridged.predicted_final_context is None
    assert bridged.uncertainty == 1.0


def test_chain_prediction_does_not_mutate_exact_model_or_transfer_policy() -> None:
    chain = _chain()
    exact_model = LearnedConsequenceModel()
    exact_model.observe(
        _observation(
            event_id="real:single:001",
            context=chain.start_context,
            action_code="open_window",
            next_context=chain.steps[0].next_context,
            temperature_effect=-0.2,
        )
    )
    transfer_policy = BoundedContextualTransferPolicy()
    exact_snapshot = exact_model.snapshot()
    transfer_snapshot = transfer_policy.config.snapshot()
    chain_model = ObservedConsequenceChainModel()
    chain_model.observe(chain)

    first = chain_model.predict(_request(chain.start_context))
    second = chain_model.predict(_request(chain.start_context))

    assert first == second
    assert exact_model.snapshot() == exact_snapshot
    assert transfer_policy.config.snapshot() == transfer_snapshot


def test_candidate_limit_is_enforced_during_prediction_without_mutation() -> None:
    start = _context(inside_heat=0.9)
    model = ObservedConsequenceChainModel(
        ObservedConsequenceChainConfig(maximum_candidates_per_request=1)
    )
    for index, final_heat in enumerate((0.4, 0.5)):
        model.observe(
            ObservedConsequenceChain.from_observations(
                (
                    _observation(
                        event_id=f"real:chain:candidate:{index}",
                        context=start,
                        action_code="open_window",
                        next_context=_context(inside_heat=final_heat),
                        temperature_effect=-0.2,
                        energy_effect=None,
                    ),
                )
            )
        )
    snapshot_before = model.snapshot()

    with pytest.raises(ValueError, match="candidate bound"):
        model.predict(
            _request(
                start,
                action_codes=("open_window",),
                effect_codes=("temperature",),
            )
        )
    assert model.snapshot() == snapshot_before


def test_authority_configuration_and_request_contracts_are_enforced() -> None:
    context = _context(inside_heat=0.9)
    chain = _chain()

    with pytest.raises(ValueError, match="cannot select actions"):
        ObservedConsequenceChainModel(has_action_selection_authority=True)
    with pytest.raises(ValueError, match="cannot control production actions"):
        replace(chain, has_production_action_authority=True)
    with pytest.raises(ValueError, match="stable sorted"):
        _request(context, effect_codes=("temperature", "energy_cost"))
    with pytest.raises(ValueError, match="must not be empty"):
        ConsequenceChainPredictionRequest(
            start_context=context,
            action_codes=(),
            relevant_effect_codes=("temperature",),
        )


def test_chain_snapshots_are_deterministic_ascii_and_non_authoritative() -> None:
    chain = _chain()
    model = ObservedConsequenceChainModel()
    model.observe(chain)

    first = model.snapshot()
    second = model.snapshot()
    prediction = model.predict(_request(chain.start_context)).snapshot()

    assert first == second
    assert str(first).isascii()
    assert str(prediction).isascii()
    assert first["source_event_ids"] == ["real:chain:001", "real:chain:002"]
    assert first["has_action_selection_authority"] is False
    assert first["has_production_action_authority"] is False


def test_chain_module_has_no_execution_storage_timer_or_transfer_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/observed_consequence_chains.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert ".step(" not in source
    assert ".compose(" not in source
    assert ".apply(" not in source
    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "optimizer" not in source
    assert "rollout" not in source
    assert "contextual_consequence_transfer" not in source
    assert "seedmind.integration" not in source


def test_transfer_predictions_cannot_be_inserted_as_chain_evidence() -> None:
    source_context = _context(inside_heat=0.9)
    target_context = _context(inside_heat=0.8)
    exact_model = LearnedConsequenceModel()
    exact_model.observe(
        _observation(
            event_id="real:transfer-source",
            context=source_context,
            action_code="open_window",
            next_context=_context(inside_heat=0.7),
            temperature_effect=-0.2,
        )
    )
    transferred = BoundedContextualTransferPolicy().predict(
        exact_model,
        ConsequencePredictionRequest(
            context=target_context,
            action_code="open_window",
            relevant_effect_codes=("energy_cost", "temperature"),
        ),
    )

    assert not isinstance(transferred, ConsequenceModelObservation)
    with pytest.raises(AttributeError):
        ObservedConsequenceChain.from_observations((transferred,))  # type: ignore[arg-type]
