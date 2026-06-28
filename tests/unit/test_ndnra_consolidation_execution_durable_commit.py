"""Tests for durable single-use NDNRA consolidation execution."""

# ruff: noqa: I001 -- pytest exposes the adjacent support module as top-level.

from __future__ import annotations

from pathlib import Path

import pytest

from ndnra_execution_test_support import (
    ASSEMBLIES,
    ROUTES,
    build_setup,
    commit_request,
    execute_loaded,
    raise_at,
    record_trace,
    save_initial,
)

from seedmind.research.ndnra import (
    ConsolidationExecutionDurableCommitPolicy,
    ConsolidationExecutionPermitLifecycleAction,
    ConsolidationExecutionPermitLifecycleStatus,
    ConsolidationExecutionPermitTransitionRequest,
    NDNRABrainStore,
    NDNRAExecutionCheckpoint,
    NDNRAProposalLifecycleCheckpoint,
)


def test_successful_restart_blocks_replay_and_duplicate_reissued_permit(
    tmp_path: Path,
) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / "brain.json")
    execute_loaded(store)
    restarted = store.load()
    state = restarted.consolidation_checkpoint.application_state()
    assert state is not None
    before = state.snapshot()

    with pytest.raises(ValueError, match="requires an issued permit"):
        ConsolidationExecutionDurableCommitPolicy().execute_and_save(
            request=commit_request(setup.permit),
            proposal_record=restarted.proposal_lifecycle_checkpoint.registry.active_records[0],
            execution_checkpoint=restarted.execution_checkpoint,
            ledger=restarted.graph.contextual_memory,
            application_state=state,
            available_assembly_ids=ASSEMBLIES,
            available_route_ids=ROUTES,
            store=store,
            graph=restarted.graph,
            growth_state=restarted.growth_state,
            consolidation_checkpoint=restarted.consolidation_checkpoint,
            proposal_lifecycle_checkpoint=restarted.proposal_lifecycle_checkpoint,
        )
    with pytest.raises(ValueError, match="already exists"):
        NDNRAExecutionCheckpoint.with_issued_permit(
            setup.permit,
            previous=restarted.execution_checkpoint,
        )

    assert state.snapshot() == before
    assert before.applied_candidate_ids == (setup.permit.proposal.candidate.candidate_id,)
    assert len(restarted.execution_checkpoint.receipts) == 1


@pytest.mark.parametrize(
    "point",
    [
        "before_revalidation",
        "after_revalidation",
        "after_consumed_registry_preparation",
        "after_application",
    ],
)
def test_commit_interruption_restores_exact_old_state(
    tmp_path: Path,
    point: str,
) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / f"{point}.json")
    before_file = store.path.read_bytes()
    loaded = store.load()
    state = loaded.consolidation_checkpoint.application_state()
    assert state is not None
    before_state = state.snapshot()

    with pytest.raises(RuntimeError, match=f"interrupted:{point}"):
        ConsolidationExecutionDurableCommitPolicy().execute_and_save(
            request=commit_request(setup.permit),
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
            commit_interruption_hook=raise_at(point),
        )

    restarted = store.load()
    assert store.path.read_bytes() == before_file
    assert state.snapshot() == before_state
    assert restarted.execution_checkpoint.permit_registry.records[0].status is (
        ConsolidationExecutionPermitLifecycleStatus.ISSUED
    )
    assert restarted.execution_checkpoint.receipts == ()


def test_after_application_before_save_restores_old_state(tmp_path: Path) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / "before_save.json")
    before_file = store.path.read_bytes()
    loaded = store.load()
    state = loaded.consolidation_checkpoint.application_state()
    assert state is not None
    before_state = state.snapshot()

    with pytest.raises(RuntimeError, match="after_application_before_save"):
        ConsolidationExecutionDurableCommitPolicy().execute_and_save(
            request=commit_request(setup.permit),
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
            durable_interruption_hook=raise_at("after_application_before_save"),
        )

    assert store.path.read_bytes() == before_file
    assert state.snapshot() == before_state
    assert not store.temporary_path.exists()


@pytest.mark.parametrize(
    "point",
    [
        "before_temporary_write",
        "during_temporary_write",
        "after_temporary_write",
        "before_atomic_replace",
    ],
)
def test_pre_replace_persistence_interruption_resolves_to_complete_old_state(
    tmp_path: Path,
    point: str,
) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / f"{point}.json")
    before_file = store.path.read_bytes()
    loaded = store.load()
    state = loaded.consolidation_checkpoint.application_state()
    assert state is not None
    before_state = state.snapshot()

    with pytest.raises(RuntimeError, match=f"interrupted:{point}"):
        ConsolidationExecutionDurableCommitPolicy().execute_and_save(
            request=commit_request(setup.permit),
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
            persistence_interruption_hook=raise_at(point),
        )

    restarted = store.load()
    assert store.path.read_bytes() == before_file
    assert state.snapshot() == before_state
    assert not store.temporary_path.exists()
    assert restarted.execution_checkpoint.receipts == ()
    assert restarted.execution_checkpoint.permit_registry.records[0].status is (
        ConsolidationExecutionPermitLifecycleStatus.ISSUED
    )


def test_after_replace_interruption_recovers_complete_new_state(tmp_path: Path) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / "after_replace.json")

    durable, state = execute_loaded(
        store,
        persistence_hook=raise_at("after_atomic_replace"),
    )
    restarted = store.load()

    assert durable.recovered_after_interruption
    assert durable.save_result is None
    assert restarted.execution_checkpoint == durable.execution_checkpoint
    assert restarted.consolidation_checkpoint == durable.consolidation_checkpoint
    assert restarted.consolidation_checkpoint.state == state.snapshot()
    assert restarted.execution_checkpoint.permit_registry.records[0].status is (
        ConsolidationExecutionPermitLifecycleStatus.CONSUMED
    )
    assert not store.temporary_path.exists()


def test_new_evidence_after_restart_blocks_stale_permit_without_mutation(
    tmp_path: Path,
) -> None:
    setup = build_setup()
    store = save_initial(setup, tmp_path / "stale.json")
    loaded = store.load()
    state = loaded.consolidation_checkpoint.application_state()
    assert state is not None
    state_before = state.snapshot()
    file_before = store.path.read_bytes()
    record_trace(
        loaded.graph,
        3,
        source_code="execution_persistence_post_restart_evidence",
    )

    with pytest.raises(ValueError, match="received stale"):
        ConsolidationExecutionDurableCommitPolicy().execute_and_save(
            request=commit_request(setup.permit),
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
        )

    restarted = store.load()
    assert state.snapshot() == state_before
    assert store.path.read_bytes() == file_before
    assert restarted.execution_checkpoint.permit_registry.records[0].status is (
        ConsolidationExecutionPermitLifecycleStatus.ISSUED
    )
    assert restarted.proposal_lifecycle_checkpoint == loaded.proposal_lifecycle_checkpoint


@pytest.mark.parametrize(
    ("action", "episode", "actor", "expected_status"),
    [
        (
            ConsolidationExecutionPermitLifecycleAction.CANCEL,
            103,
            "human:operator",
            ConsolidationExecutionPermitLifecycleStatus.CANCELLED,
        ),
        (
            ConsolidationExecutionPermitLifecycleAction.EXPIRE,
            104,
            "caller:episode_boundary",
            ConsolidationExecutionPermitLifecycleStatus.EXPIRED,
        ),
    ],
)
def test_terminal_permit_status_blocks_execution_after_restart(
    tmp_path: Path,
    action: ConsolidationExecutionPermitLifecycleAction,
    episode: int,
    actor: str,
    expected_status: ConsolidationExecutionPermitLifecycleStatus,
) -> None:
    setup = build_setup()
    registry = setup.execution_checkpoint.permit_registry.transition(
        ConsolidationExecutionPermitTransitionRequest(
            target_permit_id=setup.permit.permit_id,
            expected_proposal_id=setup.permit.proposal.proposal_id,
            expected_candidate_id=setup.permit.proposal.candidate.candidate_id,
            action=action,
            decision_episode=episode,
            actor_code=actor,
            reason_code=f"persist_{action.value}_permit",
        )
    )
    execution = NDNRAExecutionCheckpoint(permit_registry=registry)
    store = NDNRABrainStore(tmp_path / f"{action.value}.json")
    store.save(
        setup.graph,
        growth_state=setup.growth_state,
        consolidation_checkpoint=setup.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=NDNRAProposalLifecycleCheckpoint(
            registry=setup.proposal_registry
        ),
        execution_checkpoint=execution,
    )
    loaded = store.load()
    state = loaded.consolidation_checkpoint.application_state()
    assert state is not None
    before = state.snapshot()

    with pytest.raises(ValueError, match="requires an issued permit"):
        ConsolidationExecutionDurableCommitPolicy().execute_and_save(
            request=commit_request(setup.permit),
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
        )

    assert state.snapshot() == before
    assert store.load().execution_checkpoint.permit_registry.records[0].status is expected_status
