"""Tests for pure multi-lesson consolidation proposal prioritisation."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    ConsolidationPortfolioItem,
    ConsolidationPortfolioPolicy,
    ConsolidationScheduleRequest,
    ConsolidationScheduleStatus,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
)

_HEAT = LessonIdentity("reduce_heat", "cooling", 1.0)
_CLEAN = LessonIdentity("remove_dirt", "cleanliness", 1.0)
_WEAK = LessonIdentity("reduce_noise", "quiet", 1.0)


def _record_mastery(
    ledger: ContextualExperienceLedger,
    lesson: LessonIdentity,
    *,
    prefix: str,
    start_index: int,
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    assemblies = (f"assembly:{prefix}:a", f"assembly:{prefix}:b")
    routes = (f"route:{prefix}:a", f"route:{prefix}:b")
    for offset, route_id, transfer_succeeded in (
        (0, routes[0], True),
        (1, routes[1], True),
        (2, routes[0], False),
    ):
        index = start_index + offset
        assembly_id = assemblies[0] if route_id == routes[0] else assemblies[1]
        ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity("portfolio_test", f"episode:{prefix}:{index}", index),
                correlation_group_id=f"group:{prefix}:{index}",
                assembly_id=assembly_id,
                route_id=route_id,
                action_code=f"action:{prefix}",
                context=ContextSignature.from_values(
                    active_need_code=lesson.need_code,
                    sensor_values=(float(offset),),
                    available_action_codes=(f"action:{prefix}", "wait"),
                ),
                observed_effects=(
                    EffectObservation(lesson.effect_code, lesson.desired_direction, 1.0),
                ),
                transfer_attempted=True,
                transfer_succeeded=transfer_succeeded,
            )
        )
    return assemblies, routes


def _request(
    lesson: LessonIdentity,
    assemblies: tuple[str, ...],
    routes: tuple[str, ...],
) -> ConsolidationScheduleRequest:
    return ConsolidationScheduleRequest(
        lesson=lesson,
        available_assembly_ids=assemblies,
        available_route_ids=routes,
    )


def _portfolio_fixture() -> tuple[
    ContextualExperienceLedger,
    ConsolidationPortfolioItem,
    ConsolidationPortfolioItem,
    ConsolidationPortfolioItem,
]:
    ledger = ContextualExperienceLedger()
    heat_assemblies, heat_routes = _record_mastery(
        ledger,
        _HEAT,
        prefix="heat",
        start_index=0,
    )
    clean_assemblies, clean_routes = _record_mastery(
        ledger,
        _CLEAN,
        prefix="clean",
        start_index=10,
    )
    weak_assemblies = ("assembly:weak:a", "assembly:weak:b")
    weak_routes = ("route:weak:a", "route:weak:b")
    ledger.record(
        ContextualExperienceTrace(
            identity=EventIdentity("portfolio_test", "episode:weak:20", 20),
            correlation_group_id="group:weak:20",
            assembly_id=weak_assemblies[0],
            route_id=weak_routes[0],
            action_code="action:weak",
            context=ContextSignature.from_values(
                active_need_code=_WEAK.need_code,
                sensor_values=(20.0,),
                available_action_codes=("action:weak", "wait"),
            ),
            observed_effects=(EffectObservation(_WEAK.effect_code, 1.0, 1.0),),
            transfer_attempted=True,
            transfer_succeeded=True,
        )
    )
    heat = ConsolidationPortfolioItem(
        request=_request(_HEAT, heat_assemblies, heat_routes),
        context=ConsolidationSchedulingContext(
            episode_index=200,
            last_completed_episode=0,
        ),
    )
    clean = ConsolidationPortfolioItem(
        request=_request(_CLEAN, clean_assemblies, clean_routes),
        context=ConsolidationSchedulingContext(
            episode_index=200,
            last_completed_episode=80,
        ),
    )
    weak = ConsolidationPortfolioItem(
        request=_request(_WEAK, weak_assemblies, weak_routes),
        context=ConsolidationSchedulingContext(episode_index=200),
    )
    return ledger, heat, clean, weak


def test_portfolio_selects_most_overdue_ready_lesson() -> None:
    ledger, heat, clean, _ = _portfolio_fixture()
    policy = ConsolidationPortfolioPolicy(
        scheduling_policy=ConsolidationSchedulingPolicy(maximum_active_candidates=3),
        maximum_proposals_per_evaluation=1,
    )

    result = policy.evaluate(ledger=ledger, items=(clean, heat))

    assert result.proposal_ready_count == 2
    assert result.selection_limit == 1
    assert len(result.selected_proposals) == 1
    assert result.selected_proposals[0].candidate.lesson_identity == _HEAT
    heat_result = next(item for item in result.item_decisions if item.item.request.lesson == _HEAT)
    clean_result = next(
        item for item in result.item_decisions if item.item.request.lesson == _CLEAN
    )
    assert heat_result.proposal_rank == 1
    assert heat_result.selected
    assert clean_result.proposal_rank == 2
    assert not clean_result.selected
    assert clean_result.schedule_decision.proposal is not None


def test_portfolio_preserves_ineligible_lesson_decision() -> None:
    ledger, heat, _, weak = _portfolio_fixture()

    result = ConsolidationPortfolioPolicy(
        scheduling_policy=ConsolidationSchedulingPolicy(maximum_active_candidates=3),
        maximum_proposals_per_evaluation=2,
    ).evaluate(ledger=ledger, items=(weak, heat))

    weak_result = next(item for item in result.item_decisions if item.item.request.lesson == _WEAK)
    assert weak_result.schedule_decision.status is ConsolidationScheduleStatus.NOT_ELIGIBLE
    assert weak_result.schedule_decision.eligibility.reasons
    assert weak_result.proposal_rank is None
    assert not weak_result.selected
    assert len(result.item_decisions) == 2


def test_equivalent_input_order_produces_identical_portfolio() -> None:
    ledger, heat, clean, weak = _portfolio_fixture()
    policy = ConsolidationPortfolioPolicy(
        scheduling_policy=ConsolidationSchedulingPolicy(maximum_active_candidates=3),
        maximum_proposals_per_evaluation=2,
    )

    first = policy.evaluate(ledger=ledger, items=(heat, clean, weak))
    second = policy.evaluate(ledger=ledger, items=(weak, clean, heat))

    assert first == second


def test_proposal_limit_keeps_unselected_candidates_visible() -> None:
    ledger, heat, clean, _ = _portfolio_fixture()

    result = ConsolidationPortfolioPolicy(
        scheduling_policy=ConsolidationSchedulingPolicy(maximum_active_candidates=3),
        maximum_proposals_per_evaluation=1,
    ).evaluate(ledger=ledger, items=(heat, clean))

    assert result.proposal_ready_count == 2
    assert len(result.selected_proposals) == 1
    assert sum(item.schedule_decision.proposal is not None for item in result.item_decisions) == 2
    assert sum(item.selected for item in result.item_decisions) == 1


def test_remaining_active_capacity_bounds_portfolio_selection() -> None:
    ledger, heat, clean, _ = _portfolio_fixture()
    active_ids = ("consolidation:already-active",)
    heat = ConsolidationPortfolioItem(
        request=heat.request,
        context=ConsolidationSchedulingContext(
            episode_index=200,
            last_completed_episode=0,
            active_candidate_ids=active_ids,
        ),
    )
    clean = ConsolidationPortfolioItem(
        request=clean.request,
        context=ConsolidationSchedulingContext(
            episode_index=200,
            last_completed_episode=80,
            active_candidate_ids=active_ids,
        ),
    )

    result = ConsolidationPortfolioPolicy(
        scheduling_policy=ConsolidationSchedulingPolicy(maximum_active_candidates=2),
        maximum_proposals_per_evaluation=2,
    ).evaluate(ledger=ledger, items=(heat, clean))

    assert result.proposal_ready_count == 2
    assert result.selection_limit == 1
    assert len(result.selected_proposals) == 1


def test_portfolio_does_not_mutate_contextual_evidence() -> None:
    ledger, heat, clean, weak = _portfolio_fixture()
    before = ledger.snapshot()

    ConsolidationPortfolioPolicy(
        scheduling_policy=ConsolidationSchedulingPolicy(maximum_active_candidates=3),
        maximum_proposals_per_evaluation=2,
    ).evaluate(ledger=ledger, items=(heat, clean, weak))

    assert ledger.snapshot() == before


def test_duplicate_lesson_requests_are_rejected() -> None:
    ledger, heat, _, _ = _portfolio_fixture()

    with pytest.raises(ValueError, match="lesson identities must be unique"):
        ConsolidationPortfolioPolicy().evaluate(ledger=ledger, items=(heat, heat))


def test_portfolio_requires_shared_evaluation_episode_and_active_candidates() -> None:
    ledger, heat, clean, _ = _portfolio_fixture()
    different_episode = ConsolidationPortfolioItem(
        request=clean.request,
        context=ConsolidationSchedulingContext(
            episode_index=201,
            last_completed_episode=80,
        ),
    )
    with pytest.raises(ValueError, match="share one evaluation episode"):
        ConsolidationPortfolioPolicy().evaluate(
            ledger=ledger,
            items=(heat, different_episode),
        )

    different_active = ConsolidationPortfolioItem(
        request=clean.request,
        context=ConsolidationSchedulingContext(
            episode_index=200,
            last_completed_episode=80,
            active_candidate_ids=("consolidation:other",),
        ),
    )
    with pytest.raises(ValueError, match="share active candidate identities"):
        ConsolidationPortfolioPolicy().evaluate(
            ledger=ledger,
            items=(heat, different_active),
        )


def test_portfolio_module_has_no_execution_or_integration_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/consolidation_portfolio.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "consolidation_application" not in source
    assert "rollback_consolidation" not in source
    assert "seedmind.integration" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert ".apply(" not in source
