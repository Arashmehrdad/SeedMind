"""Durable restart-safe commit of one explicitly approved consolidation execution."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from dataclasses import dataclass, field

from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.research.ndnra.consolidation_application import ConsolidationStateSnapshot
from seedmind.research.ndnra.consolidation_execution_commit import (
    ConsolidationApplicationTarget,
    ConsolidationExecutionCommitPolicy,
    ConsolidationExecutionCommitRequest,
    ConsolidationExecutionCommitResult,
)
from seedmind.research.ndnra.consolidation_execution_persistence import (
    NDNRAExecutionCheckpoint,
)
from seedmind.research.ndnra.consolidation_persistence import (
    NDNRAConsolidationCheckpoint,
)
from seedmind.research.ndnra.consolidation_proposal_management import (
    ConsolidationProposalManagedRecord,
)
from seedmind.research.ndnra.consolidation_proposal_persistence import (
    NDNRAProposalLifecycleCheckpoint,
)
from seedmind.research.ndnra.contextual_memory import ContextualExperienceLedger
from seedmind.research.ndnra.controlled_replay_restoration_persistence import (
    NDNRAReplayRestorationCheckpoint,
)
from seedmind.research.ndnra.persistence import (
    BrainLoadResult,
    BrainLoadStatus,
    BrainSaveResult,
    NDNRABrainStore,
    NDNRAGrowthState,
)


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionDurableCommitResult:
    """Complete durable outcome for one bounded human-approved application."""

    commit_result: ConsolidationExecutionCommitResult
    consolidation_checkpoint: NDNRAConsolidationCheckpoint
    execution_checkpoint: NDNRAExecutionCheckpoint
    save_result: BrainSaveResult | None
    recovered_after_interruption: bool = False

    def __post_init__(self) -> None:
        self.execution_checkpoint.validate_consolidation_checkpoint(self.consolidation_checkpoint)
        if self.commit_result.permit_registry != self.execution_checkpoint.permit_registry:
            raise ValueError("durable result must retain the committed permit registry")
        if self.recovered_after_interruption and self.save_result is not None:
            raise ValueError("recovered durable result cannot claim a direct save result")
        if not self.recovered_after_interruption and self.save_result is None:
            raise ValueError("ordinary durable result requires completed save evidence")


@dataclass(frozen=True, slots=True)
class ConsolidationExecutionDurableCommitPolicy:
    """Commit in memory, atomically persist, and resolve interruption to old or new."""

    commit_policy: ConsolidationExecutionCommitPolicy = field(
        default_factory=ConsolidationExecutionCommitPolicy
    )

    def execute_and_save(
        self,
        *,
        request: ConsolidationExecutionCommitRequest,
        proposal_record: ConsolidationProposalManagedRecord,
        execution_checkpoint: NDNRAExecutionCheckpoint,
        ledger: ContextualExperienceLedger,
        application_state: ConsolidationApplicationTarget,
        available_assembly_ids: Iterable[str],
        available_route_ids: Iterable[str],
        store: NDNRABrainStore,
        graph: MultidimensionalExperienceGraph,
        growth_state: NDNRAGrowthState,
        consolidation_checkpoint: NDNRAConsolidationCheckpoint,
        proposal_lifecycle_checkpoint: NDNRAProposalLifecycleCheckpoint,
        replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint | None = None,
        commit_interruption_hook: Callable[[str], None] | None = None,
        durable_interruption_hook: Callable[[str], None] | None = None,
        persistence_interruption_hook: Callable[[str], None] | None = None,
    ) -> ConsolidationExecutionDurableCommitResult:
        """Persist either the exact old envelope or one complete consumed outcome."""
        state_before = application_state.snapshot()
        if consolidation_checkpoint.state != state_before:
            raise ValueError("application state must match the persisted consolidation state")
        replay_restoration = (
            NDNRAReplayRestorationCheckpoint.empty()
            if replay_restoration_checkpoint is None
            else replay_restoration_checkpoint
        )
        baseline = store.load()
        if not _matches_persisted_boundaries(
            baseline,
            consolidation_checkpoint=consolidation_checkpoint,
            proposal_lifecycle_checkpoint=proposal_lifecycle_checkpoint,
            execution_checkpoint=execution_checkpoint,
            replay_restoration_checkpoint=replay_restoration,
        ):
            raise ValueError("durable execution requires exact persisted authority boundaries")

        commit = self.commit_policy.execute(
            request=request,
            proposal_record=proposal_record,
            permit_registry=execution_checkpoint.permit_registry,
            ledger=ledger,
            application_state=application_state,
            available_assembly_ids=available_assembly_ids,
            available_route_ids=available_route_ids,
            interruption_hook=commit_interruption_hook,
        )
        candidate_id = commit.receipt.application.candidate.candidate_id
        if any(
            application.candidate.candidate_id == candidate_id
            for application in consolidation_checkpoint.active_applications
        ):
            _restore_application_state(application_state, state_before)
            raise ValueError("durable execution candidate already exists in application history")
        new_consolidation = NDNRAConsolidationCheckpoint(
            state=commit.receipt.application.after,
            active_applications=tuple(
                sorted(
                    (
                        *consolidation_checkpoint.active_applications,
                        commit.receipt.application,
                    ),
                    key=lambda item: item.candidate.candidate_id,
                )
            ),
            rollback_records=consolidation_checkpoint.rollback_records,
        )
        new_execution = execution_checkpoint.record_commit(commit)
        new_execution.validate_consolidation_checkpoint(new_consolidation)

        try:
            _interrupt(durable_interruption_hook, "after_application_before_save")
            _interrupt(durable_interruption_hook, "before_save")
            saved = store.save(
                graph,
                growth_state=growth_state,
                consolidation_checkpoint=new_consolidation,
                proposal_lifecycle_checkpoint=proposal_lifecycle_checkpoint,
                execution_checkpoint=new_execution,
                replay_restoration_checkpoint=replay_restoration,
                learned_consequence_checkpoint=baseline.learned_consequence_checkpoint,
                interruption_hook=persistence_interruption_hook,
            )
        except Exception as error:
            loaded = store.load()
            if _matches_expected(
                loaded,
                graph=graph,
                growth_state=growth_state,
                consolidation_checkpoint=new_consolidation,
                proposal_lifecycle_checkpoint=proposal_lifecycle_checkpoint,
                execution_checkpoint=new_execution,
                replay_restoration_checkpoint=replay_restoration,
                learned_consequence_checkpoint=baseline.learned_consequence_checkpoint,
            ):
                return ConsolidationExecutionDurableCommitResult(
                    commit_result=commit,
                    consolidation_checkpoint=new_consolidation,
                    execution_checkpoint=new_execution,
                    save_result=None,
                    recovered_after_interruption=True,
                )
            _restore_application_state(application_state, state_before)
            if not _matches_loaded_result(loaded, baseline):
                raise RuntimeError(
                    "interrupted durable execution resolved to neither old nor new state"
                ) from error
            raise

        return ConsolidationExecutionDurableCommitResult(
            commit_result=commit,
            consolidation_checkpoint=new_consolidation,
            execution_checkpoint=new_execution,
            save_result=saved,
        )


def _matches_persisted_boundaries(
    loaded: BrainLoadResult,
    *,
    consolidation_checkpoint: NDNRAConsolidationCheckpoint,
    proposal_lifecycle_checkpoint: NDNRAProposalLifecycleCheckpoint,
    execution_checkpoint: NDNRAExecutionCheckpoint,
    replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint,
) -> bool:
    return bool(
        loaded.status is BrainLoadStatus.LOADED
        and loaded.checksum_verified
        and not loaded.used_fallback
        and loaded.consolidation_checkpoint == consolidation_checkpoint
        and loaded.proposal_lifecycle_checkpoint == proposal_lifecycle_checkpoint
        and loaded.execution_checkpoint == execution_checkpoint
        and loaded.replay_restoration_checkpoint == replay_restoration_checkpoint
    )


def _matches_loaded_result(
    loaded: BrainLoadResult,
    expected: BrainLoadResult,
) -> bool:
    return bool(
        loaded.status is expected.status is BrainLoadStatus.LOADED
        and loaded.checksum_verified == expected.checksum_verified
        and loaded.used_fallback == expected.used_fallback
        and loaded.checksum == expected.checksum
        and loaded.schema_version == expected.schema_version
        and loaded.graph.snapshot() == expected.graph.snapshot()
        and loaded.growth_state == expected.growth_state
        and loaded.consolidation_checkpoint == expected.consolidation_checkpoint
        and loaded.proposal_lifecycle_checkpoint == expected.proposal_lifecycle_checkpoint
        and loaded.execution_checkpoint == expected.execution_checkpoint
        and loaded.replay_restoration_checkpoint == expected.replay_restoration_checkpoint
        and loaded.learned_consequence_checkpoint == expected.learned_consequence_checkpoint
    )


def _matches_expected(
    loaded: BrainLoadResult,
    *,
    graph: MultidimensionalExperienceGraph,
    growth_state: NDNRAGrowthState,
    consolidation_checkpoint: NDNRAConsolidationCheckpoint,
    proposal_lifecycle_checkpoint: NDNRAProposalLifecycleCheckpoint,
    execution_checkpoint: NDNRAExecutionCheckpoint,
    replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint,
    learned_consequence_checkpoint: object,
) -> bool:
    return bool(
        loaded.status is BrainLoadStatus.LOADED
        and loaded.checksum_verified
        and not loaded.used_fallback
        and loaded.graph.snapshot() == graph.snapshot()
        and loaded.growth_state == growth_state
        and loaded.consolidation_checkpoint == consolidation_checkpoint
        and loaded.proposal_lifecycle_checkpoint == proposal_lifecycle_checkpoint
        and loaded.execution_checkpoint == execution_checkpoint
        and loaded.replay_restoration_checkpoint == replay_restoration_checkpoint
        and loaded.learned_consequence_checkpoint == learned_consequence_checkpoint
    )


def _restore_application_state(
    application_state: ConsolidationApplicationTarget,
    before: ConsolidationStateSnapshot,
) -> None:
    current = application_state.snapshot()
    if current == before:
        return
    application_state.restore_snapshot(
        expected_current=current,
        replacement=before,
    )
    if application_state.snapshot() != before:
        raise RuntimeError("durable execution could not restore prior application state")


def _interrupt(
    hook: Callable[[str], None] | None,
    point: str,
) -> None:
    if hook is not None:
        hook(point)


__all__ = [
    "ConsolidationExecutionDurableCommitPolicy",
    "ConsolidationExecutionDurableCommitResult",
]
