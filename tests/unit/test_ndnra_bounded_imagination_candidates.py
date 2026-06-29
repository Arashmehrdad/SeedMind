"""Tests for deterministic exact-record bounded imagination candidate generation."""

from __future__ import annotations

import ast
from pathlib import Path
from typing import Any, cast

import pytest

from seedmind.research.ndnra import (
    BoundedCandidateGenerationConfig,
    BoundedConsequenceImagination,
    BoundedExactCandidateGenerator,
    CandidateGenerationTruncationReason,
    ConsequenceModelObservation,
    ContextSignature,
    EffectObservation,
    ExperienceOrigin,
    ImaginedCandidateGenerationRequest,
    ImaginedConsequenceRequest,
    LearnedConsequenceModel,
)


def _context(
    *,
    heat: float,
    actions: tuple[str, ...],
    need: str = "cooling",
) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code=need,
        sensor_values=(heat, 0.0),
        available_action_codes=actions,
    )


def _observation(
    *,
    event_id: str,
    context: ContextSignature,
    action_code: str,
    next_context: ContextSignature,
    effects: tuple[EffectObservation, ...],
) -> ConsequenceModelObservation:
    return ConsequenceModelObservation(
        event_id=event_id,
        origin=ExperienceOrigin.REAL,
        context=context,
        action_code=action_code,
        next_context=next_context,
        observed_effects=effects,
    )


def _generator(model: LearnedConsequenceModel) -> BoundedExactCandidateGenerator:
    return BoundedExactCandidateGenerator(model)


def _request(
    context: ContextSignature,
    *,
    effect_codes: tuple[str, ...] = ("energy_delta", "heat_delta"),
    config: BoundedCandidateGenerationConfig | None = None,
) -> ImaginedCandidateGenerationRequest:
    return ImaginedCandidateGenerationRequest(
        context=context,
        requested_effect_codes=effect_codes,
        config=(BoundedCandidateGenerationConfig() if config is None else config),
    )


def _predictable_model() -> tuple[
    LearnedConsequenceModel,
    ContextSignature,
    ContextSignature,
    ContextSignature,
]:
    start = _context(heat=0.9, actions=("cool", "wait"))
    middle = _context(heat=0.5, actions=("fan", "rest"))
    final = _context(heat=0.1, actions=("rest",))
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:cool:1",
            context=start,
            action_code="cool",
            next_context=middle,
            effects=(
                EffectObservation("energy_delta", -0.3, 1.0),
                EffectObservation("heat_delta", -0.4, 1.0),
            ),
        )
    )
    model.observe(
        _observation(
            event_id="real:wait:1",
            context=start,
            action_code="wait",
            next_context=final,
            effects=(
                EffectObservation("energy_delta", -0.1, 1.0),
                EffectObservation("heat_delta", -0.8, 1.0),
            ),
        )
    )
    model.observe(
        _observation(
            event_id="real:fan:1",
            context=middle,
            action_code="fan",
            next_context=final,
            effects=(
                EffectObservation("energy_delta", -0.1, 1.0),
                EffectObservation("heat_delta", -0.4, 1.0),
            ),
        )
    )
    return model, start, middle, final


def test_exact_one_step_records_generate_candidates_in_deterministic_action_order() -> None:
    model, start, _, _ = _predictable_model()

    result = _generator(model).generate(_request(start))

    assert [candidate.sequence.action_codes for candidate in result.candidates[:2]] == [
        ("cool",),
        ("wait",),
    ]
    assert result.truncated is False
    assert result.truncation_reasons == ()


def test_exact_bounds_do_not_report_false_truncation_when_enumeration_is_complete() -> None:
    model, start, _, _ = _predictable_model()

    result = _generator(model).generate(
        _request(
            start,
            config=BoundedCandidateGenerationConfig(
                maximum_generated_candidates=2,
                maximum_sequence_depth=1,
                maximum_total_expansions=1,
            ),
        )
    )

    assert [candidate.sequence.action_codes for candidate in result.candidates] == [
        ("cool",),
        ("wait",),
    ]
    assert result.truncated is False
    assert result.truncation_reasons == ()


def test_exact_two_step_continuity_emits_prefix_before_extension_in_bfs_order() -> None:
    model, start, _, _ = _predictable_model()

    result = _generator(model).generate(_request(start))

    assert [candidate.sequence.action_codes for candidate in result.candidates] == [
        ("cool",),
        ("wait",),
        ("cool", "fan"),
    ]


def test_multiple_parents_preserve_deterministic_bfs_order() -> None:
    start = _context(heat=0.9, actions=("alpha", "beta"))
    alpha_ctx = _context(heat=0.7, actions=("alpha_child",))
    beta_ctx = _context(heat=0.6, actions=("beta_child",))
    alpha_final = _context(heat=0.3, actions=("rest",))
    beta_final = _context(heat=0.2, actions=("rest",))
    model = LearnedConsequenceModel()
    for event_id, context, action_code, next_context, heat_delta in (
        ("real:alpha:1", start, "alpha", alpha_ctx, -0.2),
        ("real:beta:1", start, "beta", beta_ctx, -0.3),
        ("real:alpha-child:1", alpha_ctx, "alpha_child", alpha_final, -0.4),
        ("real:beta-child:1", beta_ctx, "beta_child", beta_final, -0.4),
    ):
        model.observe(
            _observation(
                event_id=event_id,
                context=context,
                action_code=action_code,
                next_context=next_context,
                effects=(
                    EffectObservation("energy_delta", -0.1, 1.0),
                    EffectObservation("heat_delta", heat_delta, 1.0),
                ),
            )
        )

    result = _generator(model).generate(_request(start))

    assert [candidate.sequence.action_codes for candidate in result.candidates] == [
        ("alpha",),
        ("beta",),
        ("alpha", "alpha_child"),
        ("beta", "beta_child"),
    ]


def test_every_step_and_candidate_is_imagined_and_preserves_exact_provenance() -> None:
    model, start, middle, final = _predictable_model()

    result = _generator(model).generate(_request(start))
    candidate = result.candidates[2]

    assert candidate.origin is ExperienceOrigin.IMAGINED
    assert all(step.origin is ExperienceOrigin.IMAGINED for step in candidate.steps)
    assert all(
        step.step_id.startswith("imagined-candidate-generation-step:") for step in candidate.steps
    )
    assert len({step.step_id for step in candidate.steps}) == len(candidate.steps)
    assert candidate.steps[0].context == start
    assert candidate.steps[0].predicted_next_context == middle
    assert candidate.steps[1].context == middle
    assert candidate.steps[1].predicted_next_context == final
    assert candidate.source_record_ids == tuple(sorted(candidate.source_record_ids))
    assert candidate.source_prediction_ids == tuple(sorted(candidate.source_prediction_ids))
    assert candidate.supporting_real_event_ids == ("real:cool:1", "real:fan:1")
    assert candidate.steps[0].supporting_real_event_ids == ("real:cool:1",)
    assert candidate.steps[1].supporting_real_event_ids == ("real:fan:1",)


def test_reversed_action_order_remains_distinct_when_exact_continuity_supports_both() -> None:
    start = _context(heat=0.9, actions=("cool", "wait"))
    cool_ctx = _context(heat=0.7, actions=("wait",))
    wait_ctx = _context(heat=0.8, actions=("cool",))
    final = _context(heat=0.4, actions=("rest",))
    model = LearnedConsequenceModel()
    for event_id, context, action_code, next_context in (
        ("real:cool:1", start, "cool", cool_ctx),
        ("real:wait:1", start, "wait", wait_ctx),
        ("real:wait:2", cool_ctx, "wait", final),
        ("real:cool:2", wait_ctx, "cool", final),
    ):
        model.observe(
            _observation(
                event_id=event_id,
                context=context,
                action_code=action_code,
                next_context=next_context,
                effects=(
                    EffectObservation("energy_delta", -0.1, 1.0),
                    EffectObservation("heat_delta", -0.2, 1.0),
                ),
            )
        )

    result = _generator(model).generate(_request(start))
    sequences = [candidate.sequence.action_codes for candidate in result.candidates]

    assert ("cool", "wait") in sequences
    assert ("wait", "cool") in sequences
    assert len({candidate.candidate_id for candidate in result.candidates}) == len(
        result.candidates
    )


def test_near_match_context_that_would_require_transfer_yields_zero_candidates() -> None:
    model, _, _, _ = _predictable_model()
    shifted = _context(heat=0.8, actions=("cool", "wait"))

    result = _generator(model).generate(_request(shifted))

    assert result.candidates == ()
    assert result.truncated is False


def test_observed_chain_only_or_transferred_evidence_cannot_become_generation_source() -> None:
    source = Path("src/seedmind/research/ndnra/bounded_imagination_candidates.py").read_text(
        encoding="ascii"
    )

    forbidden = (
        "observed_consequence_chains",
        "contextual_consequence_transfer",
        "NeedDrivenComposer",
        "sqlite3",
        "asyncio",
        "threading",
    )
    for token in forbidden:
        assert token not in source


def test_missing_requested_effects_and_missing_exact_next_context_block_admission() -> None:
    start = _context(heat=0.9, actions=("cool",))
    final = _context(heat=0.4, actions=("rest",))
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:cool:partial",
            context=start,
            action_code="cool",
            next_context=final,
            effects=(EffectObservation("heat_delta", -0.5, 1.0),),
        )
    )

    partial = _generator(model).generate(_request(start))

    class MissingNextContextModel:
        def __init__(self, base: LearnedConsequenceModel) -> None:
            self._base = base

        @property
        def records(self) -> tuple[object, ...]:
            return self._base.records

        def snapshot(self) -> dict[str, object]:
            return self._base.snapshot()

        def predict(self, request: Any) -> Any:
            prediction = self._base.predict(request)
            return type(
                "PredictionWithoutNextContext",
                (),
                {
                    "prediction_id": prediction.prediction_id,
                    "predicted_effects": prediction.predicted_effects,
                    "predicted_next_context": None,
                    "supporting_real_event_ids": prediction.supporting_real_event_ids,
                },
            )()

    nextless = _generator(cast(Any, MissingNextContextModel(model))).generate(_request(start))

    assert partial.candidates == ()
    assert nextless.candidates == ()


def test_unavailable_actions_block_admission() -> None:
    start = _context(heat=0.9, actions=("wait",))
    record_context = _context(heat=0.9, actions=("cool",))
    final = _context(heat=0.4, actions=("rest",))
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:cool:1",
            context=record_context,
            action_code="cool",
            next_context=final,
            effects=(
                EffectObservation("energy_delta", -0.1, 1.0),
                EffectObservation("heat_delta", -0.5, 1.0),
            ),
        )
    )

    result = _generator(model).generate(_request(start))

    assert result.candidates == ()


def test_repeated_source_prediction_ids_stop_cycle_extension() -> None:
    start = _context(heat=0.9, actions=("wait",))
    model = LearnedConsequenceModel()
    model.observe(
        _observation(
            event_id="real:wait:1",
            context=start,
            action_code="wait",
            next_context=start,
            effects=(
                EffectObservation("energy_delta", 0.0, 1.0),
                EffectObservation("heat_delta", 0.0, 1.0),
            ),
        )
    )

    result = _generator(model).generate(
        _request(
            start,
            config=BoundedCandidateGenerationConfig(maximum_sequence_depth=3),
        )
    )

    assert [candidate.sequence.action_codes for candidate in result.candidates] == [("wait",)]


def test_runtime_bounds_are_deterministic_and_non_mutating() -> None:
    model, start, _, _ = _predictable_model()
    before = model.snapshot()

    branch_result = _generator(model).generate(
        _request(
            start,
            config=BoundedCandidateGenerationConfig(maximum_branch_actions_per_prefix=1),
        )
    )
    candidate_result = _generator(model).generate(
        _request(
            start,
            config=BoundedCandidateGenerationConfig(maximum_generated_candidates=2),
        )
    )
    expansion_result = _generator(model).generate(
        _request(
            start,
            config=BoundedCandidateGenerationConfig(maximum_total_expansions=1),
        )
    )
    source_record_result = _generator(model).generate(
        _request(
            start,
            config=BoundedCandidateGenerationConfig(maximum_source_records_considered=1),
        )
    )
    support_bound_model = LearnedConsequenceModel()
    duplicated_end = _context(heat=0.3, actions=("rest",))
    support_bound_model.observe(
        _observation(
            event_id="real:support:a",
            context=start,
            action_code="cool",
            next_context=duplicated_end,
            effects=(
                EffectObservation("energy_delta", -0.1, 1.0),
                EffectObservation("heat_delta", -0.2, 1.0),
            ),
        )
    )
    support_bound_model.observe(
        _observation(
            event_id="real:support:b",
            context=start,
            action_code="cool",
            next_context=duplicated_end,
            effects=(
                EffectObservation("energy_delta", -0.1, 1.0),
                EffectObservation("heat_delta", -0.2, 1.0),
            ),
        )
    )
    support_bound_result = _generator(support_bound_model).generate(
        _request(
            start,
            config=BoundedCandidateGenerationConfig(
                maximum_supporting_real_event_ids_per_candidate=1
            ),
        )
    )
    depth_result = _generator(model).generate(
        _request(
            start,
            config=BoundedCandidateGenerationConfig(maximum_sequence_depth=1),
        )
    )

    assert branch_result.truncation_reasons == (
        CandidateGenerationTruncationReason.BRANCH_BOUND_REACHED,
    )
    assert candidate_result.truncation_reasons == (
        CandidateGenerationTruncationReason.CANDIDATE_BOUND_REACHED,
    )
    assert expansion_result.truncation_reasons == (
        CandidateGenerationTruncationReason.EXPANSION_BOUND_REACHED,
    )
    assert source_record_result.truncation_reasons == (
        CandidateGenerationTruncationReason.SOURCE_RECORD_BOUND_REACHED,
    )
    assert support_bound_result.truncation_reasons == (
        CandidateGenerationTruncationReason.SUPPORTING_SOURCE_EVENT_BOUND_REACHED,
    )
    assert all(len(candidate.steps) == 1 for candidate in depth_result.candidates)
    assert before == model.snapshot()


def test_request_bounds_fail_before_prediction_where_possible_and_leave_model_unchanged() -> None:
    model, start, _, _ = _predictable_model()
    before = model.snapshot()

    with pytest.raises(ValueError, match="effect-dimension bound exceeded"):
        ImaginedCandidateGenerationRequest(
            context=start,
            requested_effect_codes=tuple(f"effect_{index:02d}" for index in range(17)),
        )

    assert before == model.snapshot()


def test_repeated_identical_generation_requests_produce_identical_ids_and_ascii_snapshots() -> None:
    model, start, _, _ = _predictable_model()
    generator = _generator(model)
    request_a = _request(start)
    request_b = _request(start)

    result_a = generator.generate(request_a)
    result_b = generator.generate(request_b)

    assert request_a.request_id == request_b.request_id
    assert result_a.result_id == result_b.result_id
    assert [step.step_id for item in result_a.candidates for step in item.steps] == [
        step.step_id for item in result_b.candidates for step in item.steps
    ]
    assert result_a.snapshot_json_ascii() == result_b.snapshot_json_ascii()
    assert request_a.snapshot_json_ascii().decode("ascii")
    assert result_a.snapshot_json_ascii().decode("ascii")


def test_ordinary_unsupported_context_returns_empty_non_truncated_result() -> None:
    model, _, _, _ = _predictable_model()
    unsupported = _context(heat=0.0, actions=("rest",))

    result = _generator(model).generate(_request(unsupported))

    assert result.candidates == ()
    assert result.truncated is False
    assert result.truncation_reasons == ()


def test_generated_sequences_can_be_explicitly_handed_to_batch1_without_implicit_call(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    model, start, _, _ = _predictable_model()
    called = False

    def _forbidden_imagine(*_: object, **__: object) -> object:
        nonlocal called
        called = True
        raise AssertionError("generation must not call Batch 1 imagination")

    with monkeypatch.context() as patch:
        patch.setattr(BoundedConsequenceImagination, "imagine", _forbidden_imagine)
        generation_result = _generator(model).generate(_request(start))
    assert called is False

    request = ImaginedConsequenceRequest(
        context=start,
        relevant_effect_codes=("energy_delta", "heat_delta"),
        candidate_sequences=tuple(candidate.sequence for candidate in generation_result.candidates),
    )
    traces = BoundedConsequenceImagination(model).imagine(request).traces

    assert len(traces) == len(generation_result.candidates)


def test_generated_candidate_types_cannot_update_real_consequence_evidence() -> None:
    model, start, _, _ = _predictable_model()
    candidate = _generator(model).generate(_request(start)).candidates[0]
    before = model.snapshot()

    with pytest.raises(ValueError, match="only real observations"):
        model.observe(cast(Any, candidate))

    assert before == model.snapshot()


def test_static_ast_import_checks_prove_no_forbidden_subsystem_dependencies() -> None:
    source = Path("src/seedmind/research/ndnra/bounded_imagination_candidates.py").read_text(
        encoding="ascii"
    )
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
        "seedmind.research.ndnra.contextual_consequence_transfer",
        "seedmind.research.ndnra.observed_consequence_chains",
        "seedmind.research.ndnra.composition",
        "seedmind.research.ndnra.persistence",
        "seedmind.research.ndnra.growth",
        "seedmind.research.ndnra.controlled_retention_replay",
    )
    for forbidden in forbidden_prefixes:
        assert not any(
            module == forbidden or module.startswith(f"{forbidden}.") for module in imported_modules
        )
    assert ".imagine(" not in source


def test_snapshots_exclude_scoring_selection_schedule_execution_and_promotion_fields() -> None:
    model, start, _, _ = _predictable_model()
    snapshot = _generator(model).generate(_request(start)).snapshot()

    for forbidden_key in (
        "score",
        "rank",
        "selected_candidate",
        "recommended_candidate",
        "schedule",
        "execution",
        "promotion",
    ):
        assert forbidden_key not in snapshot_json(snapshot)


def snapshot_json(snapshot: dict[str, object]) -> str:
    return str(snapshot)
