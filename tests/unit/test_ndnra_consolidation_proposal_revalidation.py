"""Tests for pure restart-time proposal lifecycle revalidation."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    BrainLoadStatus,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalRevalidationDecision,
    ConsolidationProposalRevalidationPolicy,
    ConsolidationProposalRevalidationStatus,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewRequest,
    ConsolidationRejectionReason,
    ConsolidationScheduleProposal,
    ConsolidationScheduleRequest,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
    MultidimensionalExperienceGraph,
    NDNRABrainStore,
    NDNRAProposalLifecycleCheckpoint,
)

_HEAT = LessonIdentity("reduce_heat", "cooling", 1.0)
_CLEAN = LessonIdentity("remove_dirt", "cleanliness", 1.0)
_ASSEMBLIES = ("assembly:heat:a", "assembly:heat:b")
_ROUTES = ("route:heat:a", "route:heat:b")


def _trace(
    index: int,
    *,
    lesson: LessonIdentity = _HEAT,
    effect_value: float = 1.0,
    route_id: str | None = None,
    source_code: str = "proposal_revalidation",
) -> ContextualExperienceTrace:
    route = _ROUTES[index % 2] if route_id is None else route_id
    assembly = _ASSEMBLIES[0] if route == _ROUTES[0] else _ASSEMBLIES[1]
    return ContextualExperienceTrace(
        identity=EventIdentity(source_code, "episode:mastery", index),
        correlation_group_id=f"group:revalidation:{source_code}:{index}",
        assembly_id=assembly,
        route_id=route,
        action_code="cool",
        context=ContextSignature.from_values(
            active_need_code=lesson.need_code,
            sensor_values=(float(index), float(index + 1)),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(
            EffectObservation(
                lesson.effect_code,
                effect_value,
                1.0,
            ),
        ),
        transfer_attempted=True,
        transfer_succeeded=effect_value > 0.0,
    )


def _ledger(*, count: int = 3) -> ContextualExperienceLedger:
    ledger = ContextualExperienceLedger()
    for index in range(count):
        ledger.record(_trace(index))
    return ledger


def _proposal(
    ledger: ContextualExperienceLedger,
    *,
    episode: int,
    lesson: LessonIdentity = _HEAT,
    assemblies: tuple[str, ...] = _ASSEMBLIES,
    routes: tuple[str, ...] = _ROUTES,
) -> ConsolidationScheduleProposal:
    decision = ConsolidationSchedulingPolicy(
        first_eligible_episode=episode,
        minimum_interval_episodes=1,
    ).evaluate(
        ledger=ledger,
        request=ConsolidationScheduleRequest(
            lesson=lesson,
            available_assembly_ids=assemblies,
            available_route_ids=routes,
        ),
        context=ConsolidationSchedulingContext(episode_index=episode),
    )
    assert decision.proposal is not None
    return decision.proposal


def _accepted_registry(
    proposal: ConsolidationScheduleProposal,
) -> ConsolidationProposalLifecycleRegistry:
    return (
        ConsolidationProposalLifecycleRegistry()
        .add(proposal)
        .review(
            ConsolidationProposalReviewRequest(
                proposal=proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=proposal.proposed_episode + 1,
                reviewer_code="human:operator",
                reason_code="restart_review_passed",
            )
        )
    )


def _evaluate(
    registry: ConsolidationProposalLifecycleRegistry,
    ledger: ContextualExperienceLedger,
    *,
    assemblies: tuple[str, ...] = _ASSEMBLIES,
    routes: tuple[str, ...] = _ROUTES,
    newer: tuple[ConsolidationScheduleProposal, ...] = (),
) -> ConsolidationProposalRevalidationDecision:
    return ConsolidationProposalRevalidationPolicy().evaluate(
        record=registry.active_records[0],
        ledger=ledger,
        available_assembly_ids=assemblies,
        available_route_ids=routes,
        newer_same_lesson_proposals=newer,
    )


def test_unchanged_restored_proposal_is_current() -> None:
    ledger = _ledger()
    proposal = _proposal(ledger, episode=100)
    registry = _accepted_registry(proposal)
    before_ledger = ledger.snapshot()
    before_registry = registry.snapshot()

    decision = _evaluate(registry, ledger)

    assert decision.status is ConsolidationProposalRevalidationStatus.CURRENT
    assert decision.current_candidate == proposal.candidate
    assert decision.candidate_identity_current
    assert decision.source_events_available
    assert decision.broad_mastery_current
    assert decision.contradiction_free
    assert decision.assemblies_available
    assert decision.routes_available
    assert decision.eligibility_reasons == ()
    assert decision.superseding_proposal is None
    assert not decision.has_execution_authority
    assert ledger.snapshot() == before_ledger
    assert registry.snapshot() == before_registry


def test_additional_valid_evidence_marks_old_candidate_stale() -> None:
    ledger = _ledger()
    proposal = _proposal(ledger, episode=100)
    registry = _accepted_registry(proposal)
    ledger.record(_trace(3))

    decision = _evaluate(registry, ledger)

    assert decision.status is ConsolidationProposalRevalidationStatus.STALE
    assert decision.current_candidate is not None
    assert decision.current_candidate.candidate_id != proposal.candidate.candidate_id
    assert not decision.candidate_identity_current
    assert decision.source_events_available
    assert decision.eligibility_reasons == ()
    assert decision.superseding_proposal is None


def test_matching_newer_same_lesson_proposal_marks_old_one_superseded() -> None:
    ledger = _ledger()
    old = _proposal(ledger, episode=100)
    registry = _accepted_registry(old)
    ledger.record(_trace(3))
    newer = _proposal(ledger, episode=130)
    latest = _proposal(ledger, episode=140)

    decision = _evaluate(registry, ledger, newer=(newer, latest))

    assert decision.status is ConsolidationProposalRevalidationStatus.SUPERSEDED
    assert decision.current_candidate == latest.candidate
    assert decision.superseding_proposal == latest
    assert decision.superseding_proposal.proposed_episode == 140
    assert not decision.candidate_identity_current
    assert decision.eligibility_reasons == ()


def test_contradiction_makes_restored_proposal_invalid_for_review() -> None:
    ledger = _ledger()
    proposal = _proposal(ledger, episode=100)
    registry = _accepted_registry(proposal)
    ledger.record(_trace(3, effect_value=-1.0))

    decision = _evaluate(registry, ledger)

    assert decision.status is ConsolidationProposalRevalidationStatus.INVALID_FOR_REVIEW
    assert not decision.contradiction_free
    assert ConsolidationRejectionReason.UNRESOLVED_CONTRADICTIONS in (decision.eligibility_reasons)
    assert decision.current_candidate is None
    assert decision.superseding_proposal is None


def test_missing_original_source_event_makes_proposal_invalid() -> None:
    full = _ledger()
    proposal = _proposal(full, episode=100)
    registry = _accepted_registry(proposal)
    partial = ContextualExperienceLedger()
    partial.record(_trace(0))
    partial.record(_trace(1))

    decision = _evaluate(registry, partial)

    assert decision.status is ConsolidationProposalRevalidationStatus.INVALID_FOR_REVIEW
    assert not decision.source_events_available
    assert ConsolidationRejectionReason.MISSING_SOURCE_EVENTS in (decision.eligibility_reasons)
    assert decision.current_candidate is None


@pytest.mark.parametrize(
    ("assemblies", "routes", "expected_reason"),
    [
        ((_ASSEMBLIES[0],), _ROUTES, ConsolidationRejectionReason.MISSING_ASSEMBLIES),
        (_ASSEMBLIES, (_ROUTES[0],), ConsolidationRejectionReason.MISSING_ROUTES),
    ],
)
def test_missing_required_structure_makes_proposal_invalid(
    assemblies: tuple[str, ...],
    routes: tuple[str, ...],
    expected_reason: ConsolidationRejectionReason,
) -> None:
    ledger = _ledger()
    proposal = _proposal(ledger, episode=100)
    registry = _accepted_registry(proposal)

    decision = _evaluate(
        registry,
        ledger,
        assemblies=assemblies,
        routes=routes,
    )

    assert decision.status is ConsolidationProposalRevalidationStatus.INVALID_FOR_REVIEW
    assert expected_reason in decision.eligibility_reasons
    assert decision.current_candidate is None


def test_wrong_lesson_or_non_newer_superseding_input_is_rejected() -> None:
    heat_ledger = _ledger()
    heat = _proposal(heat_ledger, episode=100)
    registry = _accepted_registry(heat)

    clean_ledger = ContextualExperienceLedger()
    clean_assemblies = ("assembly:clean:a", "assembly:clean:b")
    clean_routes = ("route:clean:a", "route:clean:b")
    for index in range(3):
        route = clean_routes[index % 2]
        clean_ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity("clean_revalidation", "episode:clean", index),
                correlation_group_id=f"group:clean:{index}",
                assembly_id=(
                    clean_assemblies[0] if route == clean_routes[0] else clean_assemblies[1]
                ),
                route_id=route,
                action_code="clean",
                context=ContextSignature.from_values(
                    active_need_code=_CLEAN.need_code,
                    sensor_values=(float(index),),
                    available_action_codes=("clean", "wait"),
                ),
                observed_effects=(EffectObservation(_CLEAN.effect_code, 1.0, 1.0),),
                transfer_attempted=True,
                transfer_succeeded=True,
            )
        )
    clean = _proposal(
        clean_ledger,
        episode=130,
        lesson=_CLEAN,
        assemblies=clean_assemblies,
        routes=clean_routes,
    )

    with pytest.raises(ValueError, match="exact lesson identity"):
        _evaluate(registry, heat_ledger, newer=(clean,))
    with pytest.raises(ValueError, match="later proposal episode"):
        _evaluate(registry, heat_ledger, newer=(heat,))


def test_closed_records_cannot_be_revalidated() -> None:
    ledger = _ledger()
    proposal = _proposal(ledger, episode=100)
    rejected = (
        ConsolidationProposalLifecycleRegistry()
        .add(proposal)
        .review(
            ConsolidationProposalReviewRequest(
                proposal=proposal,
                action=ConsolidationProposalReviewAction.REJECT,
                decision_episode=101,
                reviewer_code="human:operator",
                reason_code="manual_rejection",
            )
        )
    )

    with pytest.raises(ValueError, match="only active"):
        ConsolidationProposalRevalidationPolicy().evaluate(
            record=rejected.records[0],
            ledger=ledger,
            available_assembly_ids=_ASSEMBLIES,
            available_route_ids=_ROUTES,
        )


def test_registry_report_evaluates_only_active_records_and_preserves_archive() -> None:
    ledger = _ledger()
    heat = _proposal(ledger, episode=100)

    clean_ledger = ContextualExperienceLedger()
    clean_assemblies = ("assembly:clean:a", "assembly:clean:b")
    clean_routes = ("route:clean:a", "route:clean:b")
    for index in range(3):
        route = clean_routes[index % 2]
        clean_ledger.record(
            ContextualExperienceTrace(
                identity=EventIdentity("clean_report", "episode:clean", index),
                correlation_group_id=f"group:clean-report:{index}",
                assembly_id=(
                    clean_assemblies[0] if route == clean_routes[0] else clean_assemblies[1]
                ),
                route_id=route,
                action_code="clean",
                context=ContextSignature.from_values(
                    active_need_code=_CLEAN.need_code,
                    sensor_values=(float(index),),
                    available_action_codes=("clean", "wait"),
                ),
                observed_effects=(EffectObservation(_CLEAN.effect_code, 1.0, 1.0),),
                transfer_attempted=True,
                transfer_succeeded=True,
            )
        )
    clean = _proposal(
        clean_ledger,
        episode=100,
        lesson=_CLEAN,
        assemblies=clean_assemblies,
        routes=clean_routes,
    )
    registry = (
        ConsolidationProposalLifecycleRegistry(maximum_active_records=2)
        .add(heat)
        .add(clean)
        .review(
            ConsolidationProposalReviewRequest(
                proposal=heat,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=101,
                reviewer_code="human:operator",
                reason_code="heat_review_passed",
            )
        )
        .review(
            ConsolidationProposalReviewRequest(
                proposal=clean,
                action=ConsolidationProposalReviewAction.REJECT,
                decision_episode=101,
                reviewer_code="human:operator",
                reason_code="clean_review_rejected",
            )
        )
    )
    before = registry.snapshot()

    report = ConsolidationProposalRevalidationPolicy().evaluate_registry(
        registry=registry,
        ledger=ledger,
        available_assembly_ids=(*_ASSEMBLIES, *clean_assemblies),
        available_route_ids=(*_ROUTES, *clean_routes),
    )

    assert report.active_record_count == 1
    assert report.archived_record_count == 1
    assert len(report.decisions) == 1
    assert report.decisions[0].proposal == heat
    assert report.decisions[0].status is ConsolidationProposalRevalidationStatus.CURRENT
    assert report.registry_unchanged
    assert not report.has_execution_authority
    assert registry.snapshot() == before


def _graph_with_mastery() -> MultidimensionalExperienceGraph:
    graph = MultidimensionalExperienceGraph()
    for index in range(3):
        trace = _trace(index, source_code="restart_graph")
        graph.learn_contextual_experience(
            identity=trace.identity,
            correlation_group_id=trace.correlation_group_id,
            assembly_id=trace.assembly_id,
            route_id=trace.route_id,
            action_code=trace.action_code,
            origin_need_code=_HEAT.need_code,
            required_facts=(),
            produced_facts=(f"cooling:{trace.assembly_id}",),
            context_signature=trace.context,
            observed_effects=trace.observed_effects,
            transfer_attempted=trace.transfer_attempted,
            transfer_succeeded=trace.transfer_succeeded,
        )
    return graph


def test_persisted_accepted_proposal_revalidates_current_after_restart(
    tmp_path: Path,
) -> None:
    graph = _graph_with_mastery()
    proposal = _proposal(graph.contextual_memory, episode=100)
    checkpoint = NDNRAProposalLifecycleCheckpoint(registry=_accepted_registry(proposal))
    path = tmp_path / "brain.json"
    NDNRABrainStore(path).save(
        graph,
        proposal_lifecycle_checkpoint=checkpoint,
    )

    loaded = NDNRABrainStore(path).load()
    report = ConsolidationProposalRevalidationPolicy().evaluate_registry(
        registry=loaded.proposal_lifecycle_checkpoint.registry,
        ledger=loaded.graph.contextual_memory,
        available_assembly_ids=tuple(assembly.assembly_id for assembly in loaded.graph.assemblies),
        available_route_ids=_ROUTES,
    )

    assert loaded.status is BrainLoadStatus.LOADED
    assert loaded.proposal_lifecycle_checkpoint == checkpoint
    assert report.decisions[0].status is ConsolidationProposalRevalidationStatus.CURRENT
    assert report.decisions[0].candidate_identity_current
    assert report.registry_unchanged


def test_revalidation_is_deterministic_and_has_no_execution_or_sqlite_path() -> None:
    ledger = _ledger()
    proposal = _proposal(ledger, episode=100)
    registry = _accepted_registry(proposal)

    first = _evaluate(registry, ledger)
    second = _evaluate(registry, ledger)
    source = (
        Path("src/seedmind/research/ndnra/consolidation_proposal_revalidation.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert first == second
    assert first.snapshot() == second.snapshot()
    assert first.decision_id.startswith("consolidation-revalidation:")
    assert str(first.snapshot()).isascii()
    assert "consolidation_application" not in source
    assert "rollback_consolidation" not in source
    assert ".apply(" not in source
    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "seedmind.integration" not in source
    assert "pathlib" not in source
