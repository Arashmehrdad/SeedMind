"""Shared deterministic fixtures for NDNRA execution persistence tests."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from seedmind.research.ndnra import (
    ConsolidationApplicationState,
    ConsolidationExecutionApprovalPolicy,
    ConsolidationExecutionApprovalRequest,
    ConsolidationExecutionCommitRequest,
    ConsolidationExecutionDurableCommitPolicy,
    ConsolidationExecutionDurableCommitResult,
    ConsolidationExecutionPermit,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewRequest,
    ConsolidationScheduleProposal,
    ConsolidationScheduleRequest,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
    ContextSignature,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
    MultidimensionalExperienceGraph,
    NDNRABrainStore,
    NDNRAConsolidationCheckpoint,
    NDNRAExecutionCheckpoint,
    NDNRAGrowthState,
    NDNRAProposalLifecycleCheckpoint,
)

LESSON = LessonIdentity("reduce_heat", "cooling", 1.0)
ASSEMBLIES = ("assembly:heat:a", "assembly:heat:b")
ROUTES = ("route:heat:a", "route:heat:b")


@dataclass(slots=True)
class ExecutionSetup:
    graph: MultidimensionalExperienceGraph
    proposal_registry: ConsolidationProposalLifecycleRegistry
    permit: ConsolidationExecutionPermit
    execution_checkpoint: NDNRAExecutionCheckpoint
    state: ConsolidationApplicationState
    consolidation_checkpoint: NDNRAConsolidationCheckpoint
    growth_state: NDNRAGrowthState


def record_trace(
    graph: MultidimensionalExperienceGraph,
    index: int,
    *,
    source_code: str = "execution_persistence_test",
) -> None:
    route_id = ROUTES[index % 2]
    assembly_id = ASSEMBLIES[0] if route_id == ROUTES[0] else ASSEMBLIES[1]
    graph.learn_contextual_experience(
        identity=EventIdentity(source_code, "episode:mastery", index),
        correlation_group_id=f"group:execution-persistence:{index}",
        assembly_id=assembly_id,
        route_id=route_id,
        action_code="cool",
        origin_need_code=LESSON.need_code,
        required_facts=(),
        produced_facts=("cooling_available",),
        context_signature=ContextSignature.from_values(
            active_need_code=LESSON.need_code,
            sensor_values=(float(index), float(index + 1)),
            available_action_codes=("cool", "wait"),
        ),
        observed_effects=(EffectObservation(LESSON.effect_code, 1.0, 1.0),),
        transfer_attempted=True,
        transfer_succeeded=index < 2,
    )


def build_proposal(graph: MultidimensionalExperienceGraph) -> ConsolidationScheduleProposal:
    decision = ConsolidationSchedulingPolicy(
        first_eligible_episode=100,
        minimum_interval_episodes=1,
    ).evaluate(
        ledger=graph.contextual_memory,
        request=ConsolidationScheduleRequest(
            lesson=LESSON,
            available_assembly_ids=ASSEMBLIES,
            available_route_ids=ROUTES,
        ),
        context=ConsolidationSchedulingContext(episode_index=100),
    )
    assert decision.proposal is not None
    return decision.proposal


def build_setup() -> ExecutionSetup:
    graph = MultidimensionalExperienceGraph()
    for index in range(3):
        record_trace(graph, index)
    proposal = build_proposal(graph)
    proposal_registry = (
        ConsolidationProposalLifecycleRegistry()
        .add(proposal)
        .review(
            ConsolidationProposalReviewRequest(
                proposal=proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=101,
                reviewer_code="human:reviewer",
                reason_code="proposal_review_passed",
            )
        )
    )
    record = proposal_registry.active_records[0]
    permit = ConsolidationExecutionApprovalPolicy().evaluate(
        request=ConsolidationExecutionApprovalRequest(
            target_proposal_id=proposal.proposal_id,
            expected_candidate_id=proposal.candidate.candidate_id,
            expected_review_decision_id=record.lifecycle.decisions[-1].decision_id,
            approval_episode=102,
            expires_after_episode=103,
            approver_code="human:operator",
            reason_code="approve_bounded_consolidation",
        ),
        record=record,
        ledger=graph.contextual_memory,
        available_assembly_ids=ASSEMBLIES,
        available_route_ids=ROUTES,
    )
    execution = NDNRAExecutionCheckpoint.with_issued_permit(permit)
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=(*ASSEMBLIES, "assembly:untouched"),
        route_ids=(*ROUTES, "route:untouched"),
        initial_stability=0.20,
        initial_plasticity=0.80,
    )
    consolidation = NDNRAConsolidationCheckpoint(state=state.snapshot())
    return ExecutionSetup(
        graph=graph,
        proposal_registry=proposal_registry,
        permit=permit,
        execution_checkpoint=execution,
        state=state,
        consolidation_checkpoint=consolidation,
        growth_state=NDNRAGrowthState(pressure=0.25, attempt_count=1),
    )


def commit_request(permit: ConsolidationExecutionPermit) -> ConsolidationExecutionCommitRequest:
    return ConsolidationExecutionCommitRequest(
        target_permit_id=permit.permit_id,
        expected_proposal_id=permit.proposal.proposal_id,
        expected_candidate_id=permit.proposal.candidate.candidate_id,
        execution_episode=103,
        executor_code="execution:bounded_commit",
        reason_code="commit_human_approved_consolidation",
    )


def save_initial(setup: ExecutionSetup, path: Path) -> NDNRABrainStore:
    store = NDNRABrainStore(path)
    store.save(
        setup.graph,
        growth_state=setup.growth_state,
        consolidation_checkpoint=setup.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=NDNRAProposalLifecycleCheckpoint(
            registry=setup.proposal_registry
        ),
        execution_checkpoint=setup.execution_checkpoint,
    )
    return store


def execute_loaded(
    store: NDNRABrainStore,
    *,
    commit_hook: Callable[[str], None] | None = None,
    durable_hook: Callable[[str], None] | None = None,
    persistence_hook: Callable[[str], None] | None = None,
) -> tuple[ConsolidationExecutionDurableCommitResult, ConsolidationApplicationState]:
    loaded = store.load()
    state = loaded.consolidation_checkpoint.application_state()
    assert state is not None
    result = ConsolidationExecutionDurableCommitPolicy().execute_and_save(
        request=commit_request(loaded.execution_checkpoint.permit_registry.records[0].permit),
        proposal_record=loaded.proposal_lifecycle_checkpoint.registry.active_records[0],
        execution_checkpoint=loaded.execution_checkpoint,
        ledger=loaded.graph.contextual_memory,
        application_state=state,
        available_assembly_ids=ASSEMBLIES,
        available_route_ids=ROUTES,
        store=store,
        graph=loaded.graph,
        growth_state=loaded.growth_state,
        consolidation_checkpoint=loaded.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=loaded.proposal_lifecycle_checkpoint,
        commit_interruption_hook=commit_hook,
        durable_interruption_hook=durable_hook,
        persistence_interruption_hook=persistence_hook,
    )
    return result, state


def raise_at(target: str) -> Callable[[str], None]:
    def hook(point: str) -> None:
        if point == target:
            raise RuntimeError(f"interrupted:{target}")

    return hook


def read_object(path: Path) -> dict[str, object]:
    value: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(value, dict)
    return value


def object_value(values: dict[str, object], key: str) -> dict[str, object]:
    value = values[key]
    assert isinstance(value, dict)
    return value


def list_value(values: dict[str, object], key: str) -> list[object]:
    value = values[key]
    assert isinstance(value, list)
    return value


def rewrite_checksum(path: Path, raw: dict[str, object]) -> None:
    body = {
        "schema": raw["schema"],
        "schema_version": raw["schema_version"],
        "payload": raw["payload"],
    }
    raw["checksum"] = hashlib.sha256(
        json.dumps(
            body,
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("ascii")
    ).hexdigest()
    path.write_text(
        json.dumps(raw, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
