"""Tests for real consequences and context-specific action competence."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra.contextual_consequence import (
    ActionConsequenceAssessment,
    ConsequenceDirection,
    ContextualActionCompetenceLedger,
    ContextualActionCompetenceRecord,
    ExperienceOrigin,
)
from seedmind.research.ndnra.contextual_memory import ContextSignature
from seedmind.research.ndnra.effects import (
    EffectNeed,
    EffectObservation,
    NeedDimension,
)


def _cooling_need() -> EffectNeed:
    return EffectNeed(
        need_code="reduce_temperature",
        primary_effect_code="temperature",
        dimensions=(
            NeedDimension(
                effect_code="temperature",
                desired_direction=-1.0,
                intensity=1.0,
            ),
        ),
        satisfaction_threshold=0.2,
    )


def _context(*, outside_hotter: bool) -> ContextSignature:
    return ContextSignature.from_values(
        active_need_code="reduce_temperature",
        sensor_values=(0.6, 0.9 if outside_hotter else 0.3),
        available_action_codes=("open_window", "start_fan"),
    )


def _assessment(
    *,
    event_id: str,
    context: ContextSignature,
    predicted_temperature_effect: float,
    observed_temperature_effect: float,
    origin: ExperienceOrigin = ExperienceOrigin.REAL,
) -> ActionConsequenceAssessment:
    return ActionConsequenceAssessment(
        event_id=event_id,
        origin=origin,
        context=context,
        action_code="open_window",
        need=_cooling_need(),
        predicted_effects=(
            EffectObservation(
                "temperature",
                predicted_temperature_effect,
                1.0,
            ),
        ),
        observed_effects=(
            EffectObservation(
                "temperature",
                observed_temperature_effect,
                1.0,
            ),
        ),
    )


def test_opening_window_into_hotter_air_is_a_real_worsened_consequence() -> None:
    assessment = _assessment(
        event_id="real:greenhouse:001",
        context=_context(outside_hotter=True),
        predicted_temperature_effect=-0.4,
        observed_temperature_effect=0.2,
    )

    assert assessment.predicted_need_alignment == pytest.approx(0.4)
    assert assessment.observed_need_alignment == pytest.approx(-0.2)
    assert assessment.direction is ConsequenceDirection.WORSENED
    assert assessment.prediction_accuracy == pytest.approx(0.7)
    assert assessment.prediction_surprise == pytest.approx(0.3)
    assert not assessment.has_action_selection_authority
    assert not assessment.has_production_action_authority


def test_wrong_action_creates_a_low_local_competence_record() -> None:
    context = _context(outside_hotter=True)
    assessment = _assessment(
        event_id="real:greenhouse:002",
        context=context,
        predicted_temperature_effect=-0.4,
        observed_temperature_effect=0.2,
    )
    ledger = ContextualActionCompetenceLedger()

    update = ledger.observe(assessment)
    record = ledger.record_for(context, "open_window")

    assert update.evidence_applied
    assert update.direction is ConsequenceDirection.WORSENED
    assert record.real_attempt_count == 1
    assert record.improved_count == 0
    assert record.worsened_count == 1
    assert record.mean_need_alignment == pytest.approx(-0.2)
    assert record.helpfulness == pytest.approx(1.0 / 3.0)
    assert record.prediction_accuracy == pytest.approx(0.7)
    assert record.evidence_strength == pytest.approx(0.25)
    assert record.competence == pytest.approx((1.0 / 3.0) * 0.7 * 0.25)


def test_same_action_remains_separate_across_different_contexts() -> None:
    hot_context = _context(outside_hotter=True)
    cool_context = _context(outside_hotter=False)
    ledger = ContextualActionCompetenceLedger()

    ledger.observe(
        _assessment(
            event_id="real:greenhouse:hot",
            context=hot_context,
            predicted_temperature_effect=-0.4,
            observed_temperature_effect=0.2,
        )
    )
    ledger.observe(
        _assessment(
            event_id="real:greenhouse:cool",
            context=cool_context,
            predicted_temperature_effect=-0.4,
            observed_temperature_effect=-0.5,
        )
    )

    hot_record = ledger.record_for(hot_context, "open_window")
    cool_record = ledger.record_for(cool_context, "open_window")
    assert ledger.record_count == 2
    assert hot_record.record_id != cool_record.record_id
    assert hot_record.worsened_count == 1
    assert cool_record.improved_count == 1
    assert cool_record.helpfulness > hot_record.helpfulness
    assert cool_record.competence > hot_record.competence


def test_later_failure_reduces_helpfulness_after_successes() -> None:
    context = _context(outside_hotter=False)
    ledger = ContextualActionCompetenceLedger()

    for index in range(3):
        ledger.observe(
            _assessment(
                event_id=f"real:greenhouse:success:{index}",
                context=context,
                predicted_temperature_effect=-0.4,
                observed_temperature_effect=-0.4,
            )
        )
    record = ledger.record_for(context, "open_window")
    helpfulness_before = record.helpfulness
    competence_before = record.competence

    update = ledger.observe(
        _assessment(
            event_id="real:greenhouse:later-failure",
            context=context,
            predicted_temperature_effect=-0.4,
            observed_temperature_effect=0.4,
        )
    )

    assert update.helpfulness_before == pytest.approx(helpfulness_before)
    assert update.helpfulness_after < update.helpfulness_before
    assert update.competence_before == pytest.approx(competence_before)
    assert update.competence_after < update.competence_before
    assert record.worsened_count == 1


def test_prediction_accuracy_does_not_make_a_harmful_action_helpful() -> None:
    context = _context(outside_hotter=True)
    assessment = _assessment(
        event_id="real:greenhouse:accurate-harm",
        context=context,
        predicted_temperature_effect=0.4,
        observed_temperature_effect=0.4,
    )
    ledger = ContextualActionCompetenceLedger()

    ledger.observe(assessment)
    record = ledger.record_for(context, "open_window")

    assert assessment.prediction_accuracy == 1.0
    assert assessment.direction is ConsequenceDirection.WORSENED
    assert record.prediction_accuracy == 1.0
    assert record.helpfulness == pytest.approx(1.0 / 3.0)
    assert record.competence == pytest.approx(1.0 / 12.0)


def test_replay_and_imagination_cannot_become_new_competence_evidence() -> None:
    context = _context(outside_hotter=False)
    ledger = ContextualActionCompetenceLedger()

    for origin in (ExperienceOrigin.REPLAY, ExperienceOrigin.IMAGINED):
        assessment = _assessment(
            event_id=f"{origin.value}:greenhouse:001",
            context=context,
            predicted_temperature_effect=-0.4,
            observed_temperature_effect=-0.4,
            origin=origin,
        )
        with pytest.raises(ValueError, match="only real experience"):
            ledger.observe(assessment)

    assert ledger.assessment_count == 0
    assert ledger.record_count == 0


def test_exact_duplicate_is_ignored_but_identity_conflict_is_rejected() -> None:
    context = _context(outside_hotter=False)
    assessment = _assessment(
        event_id="real:greenhouse:duplicate",
        context=context,
        predicted_temperature_effect=-0.4,
        observed_temperature_effect=-0.4,
    )
    ledger = ContextualActionCompetenceLedger()

    first = ledger.observe(assessment)
    duplicate = ledger.observe(assessment)

    assert first.evidence_applied
    assert not duplicate.evidence_applied
    assert ledger.assessment_count == 1
    assert ledger.record_for(context, "open_window").real_attempt_count == 1

    conflicting = replace(
        assessment,
        observed_effects=(EffectObservation("temperature", 0.4, 1.0),),
    )
    with pytest.raises(ValueError, match="identity conflict"):
        ledger.observe(conflicting)


def test_missing_prediction_is_unknown_not_false_accuracy() -> None:
    assessment = ActionConsequenceAssessment(
        event_id="real:greenhouse:unknown-prediction",
        origin=ExperienceOrigin.REAL,
        context=_context(outside_hotter=False),
        action_code="open_window",
        need=_cooling_need(),
        predicted_effects=(),
        observed_effects=(EffectObservation("temperature", -0.4, 1.0),),
    )

    assert assessment.direction is ConsequenceDirection.IMPROVED
    assert assessment.prediction_accuracy == 0.0
    assert assessment.prediction_surprise == 1.0


def test_effect_order_and_authority_contracts_are_enforced() -> None:
    context = _context(outside_hotter=False)
    need = EffectNeed(
        need_code="cool_safely",
        primary_effect_code="temperature",
        dimensions=(
            NeedDimension("temperature", -1.0, 1.0),
            NeedDimension("energy_cost", -1.0, 0.5),
        ),
        satisfaction_threshold=0.2,
    )

    with pytest.raises(ValueError, match="stable sorted"):
        ActionConsequenceAssessment(
            event_id="real:unordered",
            origin=ExperienceOrigin.REAL,
            context=context,
            action_code="open_window",
            need=need,
            predicted_effects=(
                EffectObservation("temperature", -0.4, 1.0),
                EffectObservation("energy_cost", 0.0, 1.0),
            ),
            observed_effects=(EffectObservation("temperature", -0.4, 1.0),),
        )

    assessment = _assessment(
        event_id="real:authority",
        context=context,
        predicted_temperature_effect=-0.4,
        observed_temperature_effect=-0.4,
    )
    with pytest.raises(ValueError, match="cannot select actions"):
        replace(assessment, has_action_selection_authority=True)
    with pytest.raises(ValueError, match="cannot control production actions"):
        replace(assessment, has_production_action_authority=True)

    record = ContextualActionCompetenceRecord(context=context, action_code="open_window")
    with pytest.raises(ValueError, match="cannot select actions"):
        replace(record, has_action_selection_authority=True)


def test_snapshots_are_deterministic_ascii_and_non_executing() -> None:
    context = _context(outside_hotter=False)
    assessment = _assessment(
        event_id="real:greenhouse:snapshot",
        context=context,
        predicted_temperature_effect=-0.4,
        observed_temperature_effect=-0.5,
    )
    ledger = ContextualActionCompetenceLedger()
    ledger.observe(assessment)

    first = ledger.snapshot()
    second = ledger.snapshot()

    assert first == second
    assert str(first).isascii()
    assert first["real_event_ids"] == ["real:greenhouse:snapshot"]
    assert first["has_action_selection_authority"] is False
    assert first["has_production_action_authority"] is False


def test_consequence_module_has_no_action_execution_persistence_or_timer_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/contextual_consequence.py")
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
    assert "seedmind.integration" not in source
