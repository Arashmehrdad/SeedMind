"""Durable restart-safe commit of one controlled retention replay."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from seedmind.research.ndnra.adaptive import NDNRARuntimeAdaptiveState
from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.research.ndnra.consolidation_execution_persistence import (
    NDNRAExecutionCheckpoint,
)
from seedmind.research.ndnra.consolidation_persistence import (
    NDNRAConsolidationCheckpoint,
)
from seedmind.research.ndnra.consolidation_proposal_persistence import (
    NDNRAProposalLifecycleCheckpoint,
)
from seedmind.research.ndnra.controlled_replay_restoration_approval import (
    ControlledReplayRestorationEvidence,
)
from seedmind.research.ndnra.controlled_replay_restoration_persistence import (
    NDNRAReplayRestorationCheckpoint,
)
from seedmind.research.ndnra.controlled_retention_replay import (
    ControlledRetentionReplayOperation,
    ControlledRetentionReplayRequest,
    ControlledRetentionReplayResult,
)
from seedmind.research.ndnra.persistence import (
    BrainLoadResult,
    BrainLoadStatus,
    BrainSaveResult,
    NDNRABrainStore,
    NDNRAGrowthState,
)


@dataclass(frozen=True, slots=True)
class ControlledRetentionReplayDurableResult:
    """Complete durable outcome for one single-use retention replay."""

    replay_result: ControlledRetentionReplayResult
    replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint
    growth_state: NDNRAGrowthState
    save_result: BrainSaveResult | None
    recovered_after_interruption: bool = False

    def __post_init__(self) -> None:
        if self.replay_result.lifecycle_registry != (
            self.replay_restoration_checkpoint.permit_registry
        ):
            raise ValueError("durable replay must retain the consumed permit registry")
        if self.replay_result.activity_ledger != (
            self.replay_restoration_checkpoint.activity_ledger
        ):
            raise ValueError("durable replay must retain exact activity history")
        if self.growth_state != self.replay_result.adaptive_state.to_growth_state():
            raise ValueError("durable replay growth state must match replay output")
        if self.recovered_after_interruption and self.save_result is not None:
            raise ValueError("recovered durable replay cannot claim direct save evidence")
        if not self.recovered_after_interruption and self.save_result is None:
            raise ValueError("ordinary durable replay requires completed save evidence")


@dataclass(frozen=True, slots=True)
class ControlledRetentionReplayDurablePolicy:
    """Replay on copied state, atomically persist, and resolve to old or new."""

    operation: ControlledRetentionReplayOperation = field(
        default_factory=ControlledRetentionReplayOperation
    )

    def execute_and_save(
        self,
        *,
        request: ControlledRetentionReplayRequest,
        fresh_evidence: ControlledReplayRestorationEvidence,
        replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint,
        store: NDNRABrainStore,
        graph: MultidimensionalExperienceGraph,
        growth_state: NDNRAGrowthState,
        consolidation_checkpoint: NDNRAConsolidationCheckpoint,
        proposal_lifecycle_checkpoint: NDNRAProposalLifecycleCheckpoint,
        execution_checkpoint: NDNRAExecutionCheckpoint,
        durable_interruption_hook: Callable[[str], None] | None = None,
        persistence_interruption_hook: Callable[[str], None] | None = None,
    ) -> ControlledRetentionReplayDurableResult:
        """Persist either the exact old envelope or one complete replay outcome."""
        baseline = store.load()
        if not _matches_persisted_boundaries(
            baseline,
            graph=graph,
            growth_state=growth_state,
            consolidation_checkpoint=consolidation_checkpoint,
            proposal_lifecycle_checkpoint=proposal_lifecycle_checkpoint,
            execution_checkpoint=execution_checkpoint,
            replay_restoration_checkpoint=replay_restoration_checkpoint,
        ):
            raise ValueError("durable replay requires exact persisted brain boundaries")
        if baseline.state_checksum != request.expected_current_checkpoint_checksum:
            raise ValueError("durable replay current state checksum is stale")
        if fresh_evidence.current_checkpoint_checksum != baseline.state_checksum:
            raise ValueError("fresh replay evidence does not match the persisted state")

        adaptive_state = NDNRARuntimeAdaptiveState.from_growth_state(graph, growth_state)
        replay = self.operation.execute(
            request=request,
            fresh_evidence=fresh_evidence,
            lifecycle_registry=replay_restoration_checkpoint.permit_registry,
            activity_ledger=replay_restoration_checkpoint.activity_ledger,
            adaptive_state=adaptive_state,
        )
        new_checkpoint = replay_restoration_checkpoint.record_replay(replay)
        new_growth = replay.adaptive_state.to_growth_state()

        try:
            _interrupt(durable_interruption_hook, "after_replay_before_save")
            _interrupt(durable_interruption_hook, "before_save")
            saved = store.save(
                graph,
                growth_state=new_growth,
                consolidation_checkpoint=consolidation_checkpoint,
                proposal_lifecycle_checkpoint=proposal_lifecycle_checkpoint,
                execution_checkpoint=execution_checkpoint,
                replay_restoration_checkpoint=new_checkpoint,
                learned_consequence_checkpoint=baseline.learned_consequence_checkpoint,
                interruption_hook=persistence_interruption_hook,
            )
        except Exception as error:
            loaded = store.load()
            if _matches_expected(
                loaded,
                graph=graph,
                growth_state=new_growth,
                consolidation_checkpoint=consolidation_checkpoint,
                proposal_lifecycle_checkpoint=proposal_lifecycle_checkpoint,
                execution_checkpoint=execution_checkpoint,
                replay_restoration_checkpoint=new_checkpoint,
                learned_consequence_checkpoint=baseline.learned_consequence_checkpoint,
            ):
                return ControlledRetentionReplayDurableResult(
                    replay_result=replay,
                    replay_restoration_checkpoint=new_checkpoint,
                    growth_state=new_growth,
                    save_result=None,
                    recovered_after_interruption=True,
                )
            if not _matches_loaded_result(loaded, baseline):
                raise RuntimeError(
                    "interrupted durable replay resolved to neither old nor new state"
                ) from error
            raise

        return ControlledRetentionReplayDurableResult(
            replay_result=replay,
            replay_restoration_checkpoint=new_checkpoint,
            growth_state=new_growth,
            save_result=saved,
        )


def _matches_persisted_boundaries(
    loaded: BrainLoadResult,
    *,
    graph: MultidimensionalExperienceGraph,
    growth_state: NDNRAGrowthState,
    consolidation_checkpoint: NDNRAConsolidationCheckpoint,
    proposal_lifecycle_checkpoint: NDNRAProposalLifecycleCheckpoint,
    execution_checkpoint: NDNRAExecutionCheckpoint,
    replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint,
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
        and loaded.state_checksum == expected.state_checksum
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


def _interrupt(hook: Callable[[str], None] | None, point: str) -> None:
    if hook is not None:
        hook(point)


__all__ = [
    "ControlledRetentionReplayDurablePolicy",
    "ControlledRetentionReplayDurableResult",
]
