"""Exact durable restoration of one checksum-verified complete brain envelope."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from seedmind.research.ndnra.controlled_replay_restoration_approval import (
    ControlledReplayRestorationEvidence,
    ControlledReplayRestorationOperation,
    ControlledReplayRestorationTarget,
)
from seedmind.research.ndnra.controlled_replay_restoration_permit_lifecycle import (
    ControlledReplayRestorationPermitLifecycleAction,
    ControlledReplayRestorationPermitLifecycleStatus,
    ControlledReplayRestorationPermitTransitionRequest,
)
from seedmind.research.ndnra.controlled_replay_restoration_persistence import (
    ControlledCheckpointRestorationReceipt,
    NDNRAReplayRestorationCheckpoint,
)
from seedmind.research.ndnra.persistence import (
    BRAIN_SCHEMA_VERSION,
    BrainLoadResult,
    BrainLoadStatus,
    BrainSaveResult,
    NDNRABrainStore,
)


@dataclass(frozen=True, slots=True)
class ControlledCheckpointRestorationRequest:
    """Exact caller request bound to one restoration permit and fresh evidence."""

    target_permit_id: str
    expected_target_id: str
    expected_source_checkpoint_id: str
    expected_source_checkpoint_checksum: str
    expected_current_checkpoint_id: str
    expected_current_checkpoint_checksum: str
    expected_fresh_evidence_state_id: str
    operation_episode: int
    actor_code: str
    reason_code: str

    def __post_init__(self) -> None:
        for name, value in (
            ("target_permit_id", self.target_permit_id),
            ("expected_target_id", self.expected_target_id),
            ("expected_source_checkpoint_id", self.expected_source_checkpoint_id),
            ("expected_current_checkpoint_id", self.expected_current_checkpoint_id),
            ("expected_fresh_evidence_state_id", self.expected_fresh_evidence_state_id),
            ("actor_code", self.actor_code),
            ("reason_code", self.reason_code),
        ):
            _validate_code(name, value)
        _validate_checksum(
            "expected_source_checkpoint_checksum",
            self.expected_source_checkpoint_checksum,
        )
        _validate_checksum(
            "expected_current_checkpoint_checksum",
            self.expected_current_checkpoint_checksum,
        )
        _validate_nonnegative_int("operation_episode", self.operation_episode)
        if self.actor_code != "operation:checkpoint_restoration":
            raise ValueError(
                "checkpoint restoration requires operation:checkpoint_restoration actor"
            )


@dataclass(frozen=True, slots=True)
class ControlledCheckpointRestorationDurableResult:
    """Complete restored state and restart-safe audit evidence."""

    receipt: ControlledCheckpointRestorationReceipt
    replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint
    loaded_state: BrainLoadResult
    save_result: BrainSaveResult | None
    recovered_after_interruption: bool = False

    def __post_init__(self) -> None:
        if self.loaded_state.status is not BrainLoadStatus.LOADED:
            raise ValueError("durable restoration result requires a loaded brain state")
        if not self.loaded_state.checksum_verified or self.loaded_state.used_fallback:
            raise ValueError("durable restoration result requires verified non-fallback state")
        if self.loaded_state.replay_restoration_checkpoint != (
            self.replay_restoration_checkpoint
        ):
            raise ValueError("restored state must retain exact operation audit checkpoint")
        record = self.replay_restoration_checkpoint.permit_registry.record_for(
            self.receipt.permit_id
        )
        if record.status is not ControlledReplayRestorationPermitLifecycleStatus.CONSUMED:
            raise ValueError("durable restoration result requires a consumed permit")
        if record.decisions[0].consumption_reference_code != self.receipt.receipt_id:
            raise ValueError("restoration permit must reference the exact receipt")
        if self.recovered_after_interruption and self.save_result is not None:
            raise ValueError("recovered restoration cannot claim direct save evidence")
        if not self.recovered_after_interruption and self.save_result is None:
            raise ValueError("ordinary restoration requires completed save evidence")


@dataclass(frozen=True, slots=True)
class ControlledCheckpointRestorationPolicy:
    """Restore one complete envelope and resolve interruption to old or new."""

    def restore_and_save(
        self,
        *,
        request: ControlledCheckpointRestorationRequest,
        fresh_evidence: ControlledReplayRestorationEvidence,
        current_store: NDNRABrainStore,
        source_store: NDNRABrainStore,
        durable_interruption_hook: Callable[[str], None] | None = None,
        persistence_interruption_hook: Callable[[str], None] | None = None,
    ) -> ControlledCheckpointRestorationDurableResult:
        """Atomically replace current brain contents with one exact archived state."""
        if current_store.path.resolve() == source_store.path.resolve():
            raise ValueError("restoration source and current store must differ")
        baseline = current_store.load()
        source = source_store.load()
        _validate_complete_loaded("current", baseline)
        _validate_complete_loaded("source", source)
        assert baseline.checksum is not None
        assert baseline.state_checksum is not None
        assert source.checksum is not None
        assert source.state_checksum is not None
        assert source.schema_version is not None

        checkpoint = baseline.replay_restoration_checkpoint
        record = checkpoint.permit_registry.record_for(request.target_permit_id)
        if record.status is not ControlledReplayRestorationPermitLifecycleStatus.ISSUED:
            raise ValueError("checkpoint restoration requires an issued unused permit")
        permit = record.permit
        target = permit.target
        if target.operation is not ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION:
            raise ValueError("checkpoint restoration cannot use a replay permit")
        _validate_request_against_target(request, permit.permit_id, target)
        _validate_fresh_evidence(
            request=request,
            fresh_evidence=fresh_evidence,
            permit_evidence=permit.evidence,
        )
        if not permit.valid_at(request.operation_episode):
            raise ValueError("checkpoint restoration requires an unexpired permit")
        if baseline.state_checksum != request.expected_current_checkpoint_checksum:
            raise ValueError("persisted current state checksum drifted")
        if source.state_checksum != request.expected_source_checkpoint_checksum:
            raise ValueError("persisted source state checksum drifted")
        if not checkpoint.audit_contains(source.replay_restoration_checkpoint):
            raise ValueError("current operation audit does not contain source audit history")

        receipt = ControlledCheckpointRestorationReceipt.create(
            permit_id=permit.permit_id,
            target_id=target.target_id,
            source_checkpoint_id=target.source_checkpoint_id,
            source_checkpoint_checksum=source.state_checksum,
            previous_checkpoint_id=target.expected_current_checkpoint_id,
            previous_checkpoint_checksum=baseline.state_checksum,
            restoration_episode=request.operation_episode,
            actor_code=request.actor_code,
            reason_code=request.reason_code,
            source_schema_version=source.schema_version,
        )
        consumed_registry = checkpoint.permit_registry.transition(
            ControlledReplayRestorationPermitTransitionRequest(
                target_permit_id=permit.permit_id,
                expected_operation=target.operation,
                expected_target_id=target.target_id,
                expected_source_checkpoint_id=target.source_checkpoint_id,
                expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
                expected_current_checkpoint_id=target.expected_current_checkpoint_id,
                expected_current_checkpoint_checksum=(
                    target.expected_current_checkpoint_checksum
                ),
                expected_evidence_state_id=permit.evidence.evidence_state_id,
                action=ControlledReplayRestorationPermitLifecycleAction.CONSUME,
                decision_episode=request.operation_episode,
                actor_code=request.actor_code,
                reason_code="complete_checkpoint_restoration_succeeded",
                consumption_reference_code=receipt.receipt_id,
            )
        )
        new_checkpoint = checkpoint.record_restoration(
            consumed_registry=consumed_registry,
            receipt=receipt,
            restored_activity_ledger=source.replay_restoration_checkpoint.activity_ledger,
        )

        try:
            _interrupt(durable_interruption_hook, "after_restoration_preparation_before_save")
            _interrupt(durable_interruption_hook, "before_save")
            saved = current_store.save(
                source.graph,
                growth_state=source.growth_state,
                consolidation_checkpoint=source.consolidation_checkpoint,
                proposal_lifecycle_checkpoint=source.proposal_lifecycle_checkpoint,
                execution_checkpoint=source.execution_checkpoint,
                replay_restoration_checkpoint=new_checkpoint,
                interruption_hook=persistence_interruption_hook,
            )
        except Exception as error:
            loaded = current_store.load()
            if _matches_restored_state(
                loaded,
                source=source,
                replay_restoration_checkpoint=new_checkpoint,
            ):
                return ControlledCheckpointRestorationDurableResult(
                    receipt=receipt,
                    replay_restoration_checkpoint=new_checkpoint,
                    loaded_state=loaded,
                    save_result=None,
                    recovered_after_interruption=True,
                )
            if not _same_complete_state(loaded, baseline):
                raise RuntimeError(
                    "interrupted checkpoint restoration resolved to neither old nor new state"
                ) from error
            raise

        loaded = current_store.load()
        if not _matches_restored_state(
            loaded,
            source=source,
            replay_restoration_checkpoint=new_checkpoint,
        ):
            raise RuntimeError("completed checkpoint restoration did not persist exact new state")
        return ControlledCheckpointRestorationDurableResult(
            receipt=receipt,
            replay_restoration_checkpoint=new_checkpoint,
            loaded_state=loaded,
            save_result=saved,
        )


def _validate_complete_loaded(name: str, loaded: BrainLoadResult) -> None:
    if loaded.status is not BrainLoadStatus.LOADED:
        raise ValueError(f"{name} checkpoint is not loadable")
    if not loaded.checksum_verified or loaded.used_fallback:
        raise ValueError(f"{name} checkpoint must be checksum-verified and non-fallback")
    if loaded.checksum is None:
        raise ValueError(f"{name} checkpoint checksum is unavailable")
    if loaded.state_checksum is None:
        raise ValueError(f"{name} active-state checksum is unavailable")
    if loaded.schema_version != BRAIN_SCHEMA_VERSION:
        raise ValueError(f"{name} checkpoint must use the complete current brain schema")
    if loaded.migrated_from_version is not None:
        raise ValueError(f"{name} checkpoint cannot be a migrated partial envelope")


def _validate_request_against_target(
    request: ControlledCheckpointRestorationRequest,
    permit_id: str,
    target: ControlledReplayRestorationTarget,
) -> None:
    if request.target_permit_id != permit_id:
        raise ValueError("restoration request targets a different permit")
    if request.expected_target_id != target.target_id:
        raise ValueError("restoration request targets a different restoration target")
    if request.expected_source_checkpoint_id != target.source_checkpoint_id:
        raise ValueError("restoration request targets a different source checkpoint")
    if request.expected_source_checkpoint_checksum != target.source_checkpoint_checksum:
        raise ValueError("restoration request targets a different source checkpoint checksum")
    if request.expected_current_checkpoint_id != target.expected_current_checkpoint_id:
        raise ValueError("restoration request targets a different current checkpoint")
    if request.expected_current_checkpoint_checksum != (
        target.expected_current_checkpoint_checksum
    ):
        raise ValueError("restoration request targets a different current checkpoint checksum")


def _validate_fresh_evidence(
    *,
    request: ControlledCheckpointRestorationRequest,
    fresh_evidence: ControlledReplayRestorationEvidence,
    permit_evidence: ControlledReplayRestorationEvidence,
) -> None:
    if request.operation_episode != fresh_evidence.captured_episode:
        raise ValueError("restoration requires evidence captured in the operation episode")
    if request.expected_fresh_evidence_state_id != fresh_evidence.evidence_state_id:
        raise ValueError("restoration request targets different fresh evidence")
    if not fresh_evidence.checksum_verified:
        raise ValueError("restoration requires checksum-verified fresh evidence")
    if fresh_evidence.used_fallback:
        raise ValueError("restoration cannot use fallback fresh evidence")
    if fresh_evidence.current_checkpoint_id != request.expected_current_checkpoint_id:
        raise ValueError("fresh evidence current checkpoint drifted")
    if fresh_evidence.current_checkpoint_checksum != (
        request.expected_current_checkpoint_checksum
    ):
        raise ValueError("fresh evidence current checkpoint checksum drifted")
    if (
        fresh_evidence.checkpoint_checksum(request.expected_source_checkpoint_id)
        != request.expected_source_checkpoint_checksum
    ):
        raise ValueError("fresh evidence source checkpoint checksum drifted")
    if fresh_evidence.available_checkpoint_checksums != (
        permit_evidence.available_checkpoint_checksums
    ):
        raise ValueError("fresh available checkpoint evidence drifted")
    if fresh_evidence.available_evidence_ids != permit_evidence.available_evidence_ids:
        raise ValueError("fresh restoration evidence identities drifted")


def _matches_restored_state(
    loaded: BrainLoadResult,
    *,
    source: BrainLoadResult,
    replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint,
) -> bool:
    return bool(
        loaded.status is BrainLoadStatus.LOADED
        and loaded.checksum_verified
        and not loaded.used_fallback
        and loaded.schema_version == BRAIN_SCHEMA_VERSION
        and loaded.state_checksum == source.state_checksum
        and loaded.graph.snapshot() == source.graph.snapshot()
        and loaded.growth_state == source.growth_state
        and loaded.consolidation_checkpoint == source.consolidation_checkpoint
        and loaded.proposal_lifecycle_checkpoint == source.proposal_lifecycle_checkpoint
        and loaded.execution_checkpoint == source.execution_checkpoint
        and loaded.replay_restoration_checkpoint == replay_restoration_checkpoint
    )


def _same_complete_state(first: BrainLoadResult, second: BrainLoadResult) -> bool:
    return bool(
        first.status is second.status is BrainLoadStatus.LOADED
        and first.checksum_verified == second.checksum_verified
        and first.used_fallback == second.used_fallback
        and first.checksum == second.checksum
        and first.state_checksum == second.state_checksum
        and first.schema_version == second.schema_version
        and first.graph.snapshot() == second.graph.snapshot()
        and first.growth_state == second.growth_state
        and first.consolidation_checkpoint == second.consolidation_checkpoint
        and first.proposal_lifecycle_checkpoint == second.proposal_lifecycle_checkpoint
        and first.execution_checkpoint == second.execution_checkpoint
        and first.replay_restoration_checkpoint == second.replay_restoration_checkpoint
    )


def _interrupt(hook: Callable[[str], None] | None, point: str) -> None:
    if hook is not None:
        hook(point)


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_checksum(name: str, value: str) -> None:
    if len(value) != 64 or any(character not in "0123456789abcdef" for character in value):
        raise ValueError(f"{name} must be a lowercase SHA-256 checksum")


def _validate_nonnegative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


__all__ = [
    "ControlledCheckpointRestorationDurableResult",
    "ControlledCheckpointRestorationPolicy",
    "ControlledCheckpointRestorationRequest",
]
