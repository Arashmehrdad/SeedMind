"""Live acceptance for controlled replay and exact checkpoint restoration."""

from __future__ import annotations

import csv
import json
from collections.abc import Callable
from dataclasses import asdict, dataclass
from pathlib import Path

from seedmind.curiosity import CuriosityConfig
from seedmind.environment import DynamicNurseryScenarioFactory
from seedmind.integration.unified_shadow import (
    NDNRALiveShadowAdapter,
    UnifiedDevelopmentalShadowSession,
    UnifiedShadowConfig,
    UnifiedShadowResult,
)
from seedmind.integration.unified_signal_experiment import (
    _build_signal_provider,
    _build_trainer,
)
from seedmind.research.ndnra import (
    BRAIN_SCHEMA_VERSION,
    ActivityMaintenanceLedger,
    ActivityMaintenanceRequest,
    BrainLoadResult,
    BrainLoadStatus,
    ControlledCheckpointRestorationPolicy,
    ControlledCheckpointRestorationRequest,
    ControlledReplayRestorationApprovalPolicy,
    ControlledReplayRestorationApprovalRequest,
    ControlledReplayRestorationEvidence,
    ControlledReplayRestorationOperation,
    ControlledReplayRestorationPermit,
    ControlledReplayRestorationPermitLifecycleAction,
    ControlledReplayRestorationPermitLifecycleRegistry,
    ControlledReplayRestorationPermitLifecycleStatus,
    ControlledReplayRestorationPermitTransitionRequest,
    ControlledReplayRestorationTarget,
    ControlledRetentionReplayDurablePolicy,
    ControlledRetentionReplayOperation,
    ControlledRetentionReplayReceipt,
    ControlledRetentionReplayRequest,
    ControlledRetentionReplayWorkItem,
    ExperienceOrigin,
    MultidimensionalExperienceGraph,
    NDNRABrainStore,
    NDNRAGrowthState,
    NDNRAReplayRestorationCheckpoint,
    NDNRARuntimeAdaptiveState,
)
from seedmind.research.ndnra.controlled_replay_restoration_persistence import (
    ControlledCheckpointRestorationReceipt,
)


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationAcceptanceResult:
    """Falsifiable durability, failure-path, and live-invariance metrics."""

    brain_schema_version: int
    explicit_human_approval_count: int
    replay_consumed_permit_count: int
    restoration_consumed_permit_count: int
    replay_receipt_count: int
    restoration_receipt_count: int
    automatic_replay_count: int
    automatic_restoration_count: int
    cancelled_permit_count: int
    expired_permit_count: int
    stale_evidence_rejected: bool
    duplicate_replay_rejected_after_restart: bool
    restoration_reuse_rejected_after_restart: bool
    cancellation_terminal_enforced: bool
    expiry_terminal_enforced: bool
    replay_interruption_preserved_old_state: bool
    restoration_interruption_recovered_complete_new_state: bool
    corrupt_source_rejected_without_mutation: bool
    replay_restart_round_trip_exact: bool
    restoration_restart_round_trip_exact: bool
    production_actions_unchanged_after_replay: bool
    prediction_errors_unchanged_after_replay: bool
    developmental_signals_unchanged_after_replay: bool
    replay_graph_learning_unchanged: bool
    replay_non_dormancy_growth_unchanged: bool
    replay_suggestion_difference_count: int
    restored_active_state_matches_source: bool
    restoration_actions_unchanged: bool
    restoration_suggestions_unchanged: bool
    restoration_prediction_errors_unchanged: bool
    restoration_signals_unchanged: bool
    restoration_graph_learning_unchanged: bool
    restoration_growth_unchanged: bool
    action_authority_violation_count: int
    temporary_file_remaining: bool
    sqlite_used_for_acceptance: bool
    pass_gate: bool

    def __post_init__(self) -> None:
        if self.brain_schema_version < 1:
            raise ValueError("brain_schema_version must be positive")
        for name, value in (
            ("explicit_human_approval_count", self.explicit_human_approval_count),
            ("replay_consumed_permit_count", self.replay_consumed_permit_count),
            (
                "restoration_consumed_permit_count",
                self.restoration_consumed_permit_count,
            ),
            ("replay_receipt_count", self.replay_receipt_count),
            ("restoration_receipt_count", self.restoration_receipt_count),
            ("automatic_replay_count", self.automatic_replay_count),
            ("automatic_restoration_count", self.automatic_restoration_count),
            ("cancelled_permit_count", self.cancelled_permit_count),
            ("expired_permit_count", self.expired_permit_count),
            ("replay_suggestion_difference_count", self.replay_suggestion_difference_count),
            ("action_authority_violation_count", self.action_authority_violation_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must not be negative")


@dataclass(frozen=True, slots=True)
class ControlledReplayRestorationAcceptanceEvidence:
    """Acceptance result plus live comparisons and durable operation receipts."""

    result: ControlledReplayRestorationAcceptanceResult
    pretraining: UnifiedShadowResult
    replay_control: UnifiedShadowResult
    replay_approved: UnifiedShadowResult
    restoration_source: UnifiedShadowResult
    restoration_restored: UnifiedShadowResult
    replay_receipt: ControlledRetentionReplayReceipt
    restoration_receipt: ControlledCheckpointRestorationReceipt
    replay_control_brain_path: Path
    replay_approved_brain_path: Path
    restoration_source_brain_path: Path
    restoration_current_brain_path: Path


def run_controlled_replay_restoration_acceptance(
    output_directory: Path,
    *,
    first_seed: int = 7,
    replay_seed: int = 11,
    restoration_seed: int = 13,
    play_budget: int = 8,
) -> ControlledReplayRestorationAcceptanceEvidence:
    """Run the complete controlled replay/restoration stage acceptance gate."""
    if play_budget <= 2:
        raise ValueError("play_budget must exceed two")
    output_directory.mkdir(parents=True, exist_ok=True)
    factory = DynamicNurseryScenarioFactory()
    curiosity = CuriosityConfig(play_budget=play_budget)

    pretraining_shadow = NDNRALiveShadowAdapter()
    pretraining = UnifiedDevelopmentalShadowSession(
        _build_trainer(first_seed, factory),
        factory,
        UnifiedShadowConfig(seed=first_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(first_seed, factory),
        shadow=pretraining_shadow,
    ).run()
    graph = pretraining_shadow.graph
    assembly_id = sorted(assembly.assembly_id for assembly in graph.assemblies)[0]
    growth = _with_dormancy(pretraining.final_growth_state, assembly_id, 0.80)
    real_event_id = f"real:controlled-acceptance:{assembly_id}"
    activity = ActivityMaintenanceLedger()
    activity.consider(
        ActivityMaintenanceRequest(
            event_id=real_event_id,
            cycle=100,
            origin=ExperienceOrigin.REAL,
            structure_ids=(assembly_id,),
            supporting_real_event_ids=(),
            relevance=1.0,
            helpfulness=1.0,
            prediction_accuracy=1.0,
            real_evidence_strength=1.0,
        )
    )
    base_checkpoint = NDNRAReplayRestorationCheckpoint(activity_ledger=activity)

    control_path = output_directory / "controlled_replay_control_brain.json"
    approved_path = output_directory / "controlled_replay_approved_brain.json"
    control_store = NDNRABrainStore(control_path)
    approved_store = NDNRABrainStore(approved_path)
    control_save = control_store.save(
        graph,
        growth_state=growth,
        replay_restoration_checkpoint=base_checkpoint,
    )
    approved_store.save(
        graph,
        growth_state=growth,
        replay_restoration_checkpoint=base_checkpoint,
    )
    replay_permit, replay_approval_evidence = _approved_permit(
        operation=ControlledReplayRestorationOperation.RETENTION_REPLAY,
        target_id="replay-target:live-acceptance",
        source_checkpoint_id="checkpoint:replay-control",
        source_checksum=control_save.state_checksum,
        current_checkpoint_id="checkpoint:replay-control",
        current_checksum=control_save.state_checksum,
        source_evidence_ids=(real_event_id,),
        maximum_work_items=1,
        approval_episode=200,
        expires_after_episode=201,
        reason_code="approve_live_replay_acceptance",
    )
    issued_replay_checkpoint = NDNRAReplayRestorationCheckpoint.with_issued_permit(
        replay_permit,
        previous=base_checkpoint,
    )
    approved_store.save(
        graph,
        growth_state=growth,
        replay_restoration_checkpoint=issued_replay_checkpoint,
    )
    replay_fresh = _fresh_evidence(replay_approval_evidence, captured_episode=201)
    replay_request = ControlledRetentionReplayRequest(
        target_permit_id=replay_permit.permit_id,
        expected_target_id=replay_permit.target.target_id,
        expected_source_checkpoint_id=replay_permit.target.source_checkpoint_id,
        expected_source_checkpoint_checksum=(replay_permit.target.source_checkpoint_checksum),
        expected_current_checkpoint_id=(replay_permit.target.expected_current_checkpoint_id),
        expected_current_checkpoint_checksum=(
            replay_permit.target.expected_current_checkpoint_checksum
        ),
        expected_fresh_evidence_state_id=replay_fresh.evidence_state_id,
        operation_episode=201,
        actor_code="operation:retention_replay",
        reason_code="execute_live_replay_acceptance",
        work_items=(
            ControlledRetentionReplayWorkItem(
                work_item_id="replay-work-item:live-acceptance",
                source_evidence_id=real_event_id,
                structure_ids=(assembly_id,),
            ),
        ),
    )
    stale_rejected = _stale_replay_is_rejected(
        store=approved_store,
        request=replay_request,
        approval_evidence=replay_approval_evidence,
    )
    replay_interruption_old = _replay_interruption_preserves_old(
        output_directory=output_directory,
        graph=graph,
        growth=growth,
        base_checkpoint=base_checkpoint,
        event_id=real_event_id,
        assembly_id=assembly_id,
        state_checksum=control_save.state_checksum,
    )

    replay_pre = approved_store.load()
    replay_durable = ControlledRetentionReplayDurablePolicy().execute_and_save(
        request=replay_request,
        fresh_evidence=replay_fresh,
        replay_restoration_checkpoint=replay_pre.replay_restoration_checkpoint,
        store=approved_store,
        graph=replay_pre.graph,
        growth_state=replay_pre.growth_state,
        consolidation_checkpoint=replay_pre.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=replay_pre.proposal_lifecycle_checkpoint,
        execution_checkpoint=replay_pre.execution_checkpoint,
    )
    replay_loaded = approved_store.load()
    replay_restart_exact = bool(
        replay_loaded.status is BrainLoadStatus.LOADED
        and replay_loaded.checksum_verified
        and replay_loaded.growth_state == replay_durable.growth_state
        and replay_loaded.replay_restoration_checkpoint
        == replay_durable.replay_restoration_checkpoint
    )
    duplicate_replay_rejected = _duplicate_replay_is_rejected(
        loaded=replay_loaded,
        request=replay_request,
        fresh_evidence=replay_fresh,
    )

    control_load = control_store.load()
    replay_control = _run_live_shadow(
        load=control_load,
        seed=replay_seed,
        play_budget=play_budget,
        factory=factory,
        curiosity=curiosity,
    )
    replay_approved = _run_live_shadow(
        load=replay_loaded,
        seed=replay_seed,
        play_budget=play_budget,
        factory=factory,
        curiosity=curiosity,
    )
    replay_actions_equal = replay_control.actual_actions == replay_approved.actual_actions
    replay_errors_equal = _prediction_errors(replay_control) == _prediction_errors(replay_approved)
    replay_signals_equal = replay_control.signals == replay_approved.signals
    replay_graphs_equal = replay_control.graph_snapshot == replay_approved.graph_snapshot
    replay_growth_equal = _growth_without_dormancy(
        replay_control.final_growth_state
    ) == _growth_without_dormancy(replay_approved.final_growth_state)
    replay_suggestion_differences = sum(
        control.suggested_action is not approved.suggested_action
        for control, approved in zip(
            replay_control.suggestions,
            replay_approved.suggestions,
            strict=True,
        )
    )

    cancelled_count, expired_count, cancellation_enforced, expiry_enforced = (
        _terminal_lifecycle_evidence(
            state_checksum=control_save.state_checksum,
            evidence_id=real_event_id,
        )
    )

    source_path = output_directory / "controlled_restoration_source_brain.json"
    current_path = output_directory / "controlled_restoration_current_brain.json"
    source_store = NDNRABrainStore(source_path)
    current_store = NDNRABrainStore(current_path)
    source_store.save(
        control_load.graph,
        growth_state=control_load.growth_state,
        consolidation_checkpoint=control_load.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=control_load.proposal_lifecycle_checkpoint,
        execution_checkpoint=control_load.execution_checkpoint,
        replay_restoration_checkpoint=control_load.replay_restoration_checkpoint,
    )
    current_store.save(
        replay_loaded.graph,
        growth_state=replay_loaded.growth_state,
        consolidation_checkpoint=replay_loaded.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=replay_loaded.proposal_lifecycle_checkpoint,
        execution_checkpoint=replay_loaded.execution_checkpoint,
        replay_restoration_checkpoint=replay_loaded.replay_restoration_checkpoint,
    )
    source_load = source_store.load()
    current_load = current_store.load()
    assert source_load.state_checksum is not None
    assert current_load.state_checksum is not None
    restoration_permit, restoration_approval_evidence = _approved_permit(
        operation=ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION,
        target_id="restoration-target:live-acceptance",
        source_checkpoint_id="checkpoint:restoration-source",
        source_checksum=source_load.state_checksum,
        current_checkpoint_id="checkpoint:restoration-current",
        current_checksum=current_load.state_checksum,
        source_evidence_ids=("evidence:restoration:live-acceptance",),
        maximum_work_items=0,
        approval_episode=300,
        expires_after_episode=301,
        reason_code="approve_live_restoration_acceptance",
    )
    issued_restoration = NDNRAReplayRestorationCheckpoint.with_issued_permit(
        restoration_permit,
        previous=current_load.replay_restoration_checkpoint,
    )
    current_store.save(
        current_load.graph,
        growth_state=current_load.growth_state,
        consolidation_checkpoint=current_load.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=current_load.proposal_lifecycle_checkpoint,
        execution_checkpoint=current_load.execution_checkpoint,
        replay_restoration_checkpoint=issued_restoration,
    )
    restoration_fresh = _fresh_evidence(
        restoration_approval_evidence,
        captured_episode=301,
    )
    restoration_request = ControlledCheckpointRestorationRequest(
        target_permit_id=restoration_permit.permit_id,
        expected_target_id=restoration_permit.target.target_id,
        expected_source_checkpoint_id=(restoration_permit.target.source_checkpoint_id),
        expected_source_checkpoint_checksum=(restoration_permit.target.source_checkpoint_checksum),
        expected_current_checkpoint_id=(restoration_permit.target.expected_current_checkpoint_id),
        expected_current_checkpoint_checksum=(
            restoration_permit.target.expected_current_checkpoint_checksum
        ),
        expected_fresh_evidence_state_id=restoration_fresh.evidence_state_id,
        operation_episode=301,
        actor_code="operation:checkpoint_restoration",
        reason_code="execute_live_restoration_acceptance",
    )
    corrupt_rejected = _corrupt_source_is_rejected(
        output_directory=output_directory,
        current_store=current_store,
        request=restoration_request,
        fresh_evidence=restoration_fresh,
    )
    restoration_interruption_new = _restoration_interruption_recovers_new(
        output_directory=output_directory,
        source_store=source_store,
        current_load=current_load,
        current_checkpoint=issued_restoration,
        source_checksum=source_load.state_checksum,
        current_checksum=current_load.state_checksum,
    )
    restoration_durable = ControlledCheckpointRestorationPolicy().restore_and_save(
        request=restoration_request,
        fresh_evidence=restoration_fresh,
        current_store=current_store,
        source_store=source_store,
    )
    restored_load = current_store.load()
    restoration_restart_exact = bool(
        restored_load.status is BrainLoadStatus.LOADED
        and restored_load.checksum_verified
        and restored_load.replay_restoration_checkpoint
        == restoration_durable.replay_restoration_checkpoint
        and restored_load.state_checksum == source_load.state_checksum
    )
    restoration_reuse_rejected = _restoration_reuse_is_rejected(
        current_store=current_store,
        source_store=source_store,
        request=restoration_request,
        fresh_evidence=restoration_fresh,
    )
    restored_matches_source = _active_state_equal(source_load, restored_load)

    restoration_source = _run_live_shadow(
        load=source_load,
        seed=restoration_seed,
        play_budget=play_budget,
        factory=factory,
        curiosity=curiosity,
    )
    restoration_restored = _run_live_shadow(
        load=restored_load,
        seed=restoration_seed,
        play_budget=play_budget,
        factory=factory,
        curiosity=curiosity,
    )
    restoration_actions_equal = (
        restoration_source.actual_actions == restoration_restored.actual_actions
    )
    restoration_suggestions_equal = (
        restoration_source.suggestions == restoration_restored.suggestions
    )
    restoration_errors_equal = _prediction_errors(restoration_source) == _prediction_errors(
        restoration_restored
    )
    restoration_signals_equal = restoration_source.signals == restoration_restored.signals
    restoration_graphs_equal = (
        restoration_source.graph_snapshot == restoration_restored.graph_snapshot
    )
    restoration_growth_equal = (
        restoration_source.final_growth_state == restoration_restored.final_growth_state
    )

    final_checkpoint = restored_load.replay_restoration_checkpoint
    replay_consumed = final_checkpoint.permit_registry.replay_consumption_count
    restoration_consumed = final_checkpoint.permit_registry.restoration_consumption_count
    authority_violations = (
        replay_control.authority_violation_count
        + replay_approved.authority_violation_count
        + restoration_source.authority_violation_count
        + restoration_restored.authority_violation_count
        + int(replay_durable.replay_result.receipt.has_production_action_authority)
        + int(restoration_durable.receipt.has_production_action_authority)
        + int(final_checkpoint.has_replay_authority)
        + int(final_checkpoint.has_restoration_authority)
        + int(final_checkpoint.has_cognitive_authority)
        + int(final_checkpoint.has_production_action_authority)
    )
    temporary_remaining = any(
        store.temporary_path.exists()
        for store in (control_store, approved_store, source_store, current_store)
    )
    pass_gate = bool(
        BRAIN_SCHEMA_VERSION == 6
        and replay_consumed == 1
        and restoration_consumed == 1
        and len(final_checkpoint.replay_receipts) == 1
        and len(final_checkpoint.restoration_receipts) == 1
        and final_checkpoint.automatic_replay_count == 0
        and final_checkpoint.automatic_restoration_count == 0
        and cancelled_count == 1
        and expired_count == 1
        and stale_rejected
        and duplicate_replay_rejected
        and restoration_reuse_rejected
        and cancellation_enforced
        and expiry_enforced
        and replay_interruption_old
        and restoration_interruption_new
        and corrupt_rejected
        and replay_restart_exact
        and restoration_restart_exact
        and replay_actions_equal
        and replay_errors_equal
        and replay_signals_equal
        and replay_graphs_equal
        and replay_growth_equal
        and restored_matches_source
        and restoration_actions_equal
        and restoration_suggestions_equal
        and restoration_errors_equal
        and restoration_signals_equal
        and restoration_graphs_equal
        and restoration_growth_equal
        and authority_violations == 0
        and not temporary_remaining
    )
    result = ControlledReplayRestorationAcceptanceResult(
        brain_schema_version=BRAIN_SCHEMA_VERSION,
        explicit_human_approval_count=2,
        replay_consumed_permit_count=replay_consumed,
        restoration_consumed_permit_count=restoration_consumed,
        replay_receipt_count=len(final_checkpoint.replay_receipts),
        restoration_receipt_count=len(final_checkpoint.restoration_receipts),
        automatic_replay_count=final_checkpoint.automatic_replay_count,
        automatic_restoration_count=final_checkpoint.automatic_restoration_count,
        cancelled_permit_count=cancelled_count,
        expired_permit_count=expired_count,
        stale_evidence_rejected=stale_rejected,
        duplicate_replay_rejected_after_restart=duplicate_replay_rejected,
        restoration_reuse_rejected_after_restart=restoration_reuse_rejected,
        cancellation_terminal_enforced=cancellation_enforced,
        expiry_terminal_enforced=expiry_enforced,
        replay_interruption_preserved_old_state=replay_interruption_old,
        restoration_interruption_recovered_complete_new_state=(restoration_interruption_new),
        corrupt_source_rejected_without_mutation=corrupt_rejected,
        replay_restart_round_trip_exact=replay_restart_exact,
        restoration_restart_round_trip_exact=restoration_restart_exact,
        production_actions_unchanged_after_replay=replay_actions_equal,
        prediction_errors_unchanged_after_replay=replay_errors_equal,
        developmental_signals_unchanged_after_replay=replay_signals_equal,
        replay_graph_learning_unchanged=replay_graphs_equal,
        replay_non_dormancy_growth_unchanged=replay_growth_equal,
        replay_suggestion_difference_count=replay_suggestion_differences,
        restored_active_state_matches_source=restored_matches_source,
        restoration_actions_unchanged=restoration_actions_equal,
        restoration_suggestions_unchanged=restoration_suggestions_equal,
        restoration_prediction_errors_unchanged=restoration_errors_equal,
        restoration_signals_unchanged=restoration_signals_equal,
        restoration_graph_learning_unchanged=restoration_graphs_equal,
        restoration_growth_unchanged=restoration_growth_equal,
        action_authority_violation_count=authority_violations,
        temporary_file_remaining=temporary_remaining,
        sqlite_used_for_acceptance=False,
        pass_gate=pass_gate,
    )
    return ControlledReplayRestorationAcceptanceEvidence(
        result=result,
        pretraining=pretraining,
        replay_control=replay_control,
        replay_approved=replay_approved,
        restoration_source=restoration_source,
        restoration_restored=restoration_restored,
        replay_receipt=replay_durable.replay_result.receipt,
        restoration_receipt=restoration_durable.receipt,
        replay_control_brain_path=control_path,
        replay_approved_brain_path=approved_path,
        restoration_source_brain_path=source_path,
        restoration_current_brain_path=current_path,
    )


def export_controlled_replay_restoration_acceptance(
    evidence: ControlledReplayRestorationAcceptanceEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path, Path]:
    """Export ASCII report, two live timelines, and operation receipts."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "controlled_replay_restoration_report.json"
    replay_path = output_directory / "controlled_replay_timeline.csv"
    restoration_path = output_directory / "controlled_restoration_timeline.csv"
    receipts_path = output_directory / "controlled_replay_restoration_receipts.json"
    _write_ascii_json(report_path, asdict(evidence.result))
    _write_ascii_json(
        receipts_path,
        {
            "replay": evidence.replay_receipt.snapshot(),
            "restoration": evidence.restoration_receipt.snapshot(),
        },
    )
    _write_comparison_csv(replay_path, evidence.replay_control, evidence.replay_approved)
    _write_comparison_csv(
        restoration_path,
        evidence.restoration_source,
        evidence.restoration_restored,
    )
    return report_path, replay_path, restoration_path, receipts_path


def _run_live_shadow(
    *,
    load: BrainLoadResult,
    seed: int,
    play_budget: int,
    factory: DynamicNurseryScenarioFactory,
    curiosity: CuriosityConfig,
) -> UnifiedShadowResult:
    graph = load.graph
    growth_state = load.growth_state
    return UnifiedDevelopmentalShadowSession(
        _build_trainer(seed, factory),
        factory,
        UnifiedShadowConfig(seed=seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(seed, factory),
        shadow=NDNRALiveShadowAdapter(graph=graph, growth_state=growth_state),
    ).run()


def _approved_permit(
    *,
    operation: ControlledReplayRestorationOperation,
    target_id: str,
    source_checkpoint_id: str,
    source_checksum: str,
    current_checkpoint_id: str,
    current_checksum: str,
    source_evidence_ids: tuple[str, ...],
    maximum_work_items: int,
    approval_episode: int,
    expires_after_episode: int,
    reason_code: str,
) -> tuple[ControlledReplayRestorationPermit, ControlledReplayRestorationEvidence]:
    available_checkpoints = tuple(
        sorted(
            {
                (source_checkpoint_id, source_checksum),
                (current_checkpoint_id, current_checksum),
            }
        )
    )
    evidence = ControlledReplayRestorationEvidence(
        captured_episode=approval_episode,
        current_checkpoint_id=current_checkpoint_id,
        current_checkpoint_checksum=current_checksum,
        available_checkpoint_checksums=available_checkpoints,
        available_evidence_ids=tuple(sorted(source_evidence_ids)),
    )
    target = ControlledReplayRestorationTarget(
        operation=operation,
        target_id=target_id,
        source_checkpoint_id=source_checkpoint_id,
        source_checkpoint_checksum=source_checksum,
        expected_current_checkpoint_id=current_checkpoint_id,
        expected_current_checkpoint_checksum=current_checksum,
        source_evidence_ids=tuple(sorted(source_evidence_ids)),
        maximum_work_items=maximum_work_items,
    )
    permit = ControlledReplayRestorationApprovalPolicy().evaluate(
        request=ControlledReplayRestorationApprovalRequest(
            target=target,
            expected_evidence_state_id=evidence.evidence_state_id,
            approval_episode=approval_episode,
            expires_after_episode=expires_after_episode,
            approver_code="human:controlled_acceptance_operator",
            reason_code=reason_code,
        ),
        evidence=evidence,
    )
    return permit, evidence


def _fresh_evidence(
    approval: ControlledReplayRestorationEvidence,
    *,
    captured_episode: int,
) -> ControlledReplayRestorationEvidence:
    return ControlledReplayRestorationEvidence(
        captured_episode=captured_episode,
        current_checkpoint_id=approval.current_checkpoint_id,
        current_checkpoint_checksum=approval.current_checkpoint_checksum,
        available_checkpoint_checksums=approval.available_checkpoint_checksums,
        available_evidence_ids=approval.available_evidence_ids,
    )


def _stale_replay_is_rejected(
    *,
    store: NDNRABrainStore,
    request: ControlledRetentionReplayRequest,
    approval_evidence: ControlledReplayRestorationEvidence,
) -> bool:
    before = store.load()
    drifted = ControlledReplayRestorationEvidence(
        captured_episode=request.operation_episode,
        current_checkpoint_id=approval_evidence.current_checkpoint_id,
        current_checkpoint_checksum=approval_evidence.current_checkpoint_checksum,
        available_checkpoint_checksums=approval_evidence.available_checkpoint_checksums,
        available_evidence_ids=tuple(
            sorted((*approval_evidence.available_evidence_ids, "evidence:unexpected"))
        ),
    )
    drifted_request = ControlledRetentionReplayRequest(
        target_permit_id=request.target_permit_id,
        expected_target_id=request.expected_target_id,
        expected_source_checkpoint_id=request.expected_source_checkpoint_id,
        expected_source_checkpoint_checksum=request.expected_source_checkpoint_checksum,
        expected_current_checkpoint_id=request.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=request.expected_current_checkpoint_checksum,
        expected_fresh_evidence_state_id=drifted.evidence_state_id,
        operation_episode=request.operation_episode,
        actor_code=request.actor_code,
        reason_code=request.reason_code,
        work_items=request.work_items,
    )
    try:
        ControlledRetentionReplayDurablePolicy().execute_and_save(
            request=drifted_request,
            fresh_evidence=drifted,
            replay_restoration_checkpoint=before.replay_restoration_checkpoint,
            store=store,
            graph=before.graph,
            growth_state=before.growth_state,
            consolidation_checkpoint=before.consolidation_checkpoint,
            proposal_lifecycle_checkpoint=before.proposal_lifecycle_checkpoint,
            execution_checkpoint=before.execution_checkpoint,
        )
    except ValueError:
        after = store.load()
        return bool(
            after.checksum == before.checksum
            and after.replay_restoration_checkpoint == before.replay_restoration_checkpoint
        )
    return False


def _duplicate_replay_is_rejected(
    *,
    loaded: BrainLoadResult,
    request: ControlledRetentionReplayRequest,
    fresh_evidence: ControlledReplayRestorationEvidence,
) -> bool:
    adaptive = NDNRARuntimeAdaptiveState.from_growth_state(
        loaded.graph,
        loaded.growth_state,
    )
    try:
        ControlledRetentionReplayOperation().execute(
            request=request,
            fresh_evidence=fresh_evidence,
            lifecycle_registry=loaded.replay_restoration_checkpoint.permit_registry,
            activity_ledger=loaded.replay_restoration_checkpoint.activity_ledger,
            adaptive_state=adaptive,
        )
    except ValueError as error:
        return "issued unused permit" in str(error)
    return False


def _replay_interruption_preserves_old(
    *,
    output_directory: Path,
    graph: MultidimensionalExperienceGraph,
    growth: NDNRAGrowthState,
    base_checkpoint: NDNRAReplayRestorationCheckpoint,
    event_id: str,
    assembly_id: str,
    state_checksum: str,
) -> bool:
    store = NDNRABrainStore(output_directory / "replay_interruption_brain.json")
    store.save(
        graph,
        growth_state=growth,
        replay_restoration_checkpoint=base_checkpoint,
    )
    permit, approval = _approved_permit(
        operation=ControlledReplayRestorationOperation.RETENTION_REPLAY,
        target_id="replay-target:interruption-acceptance",
        source_checkpoint_id="checkpoint:replay-interruption",
        source_checksum=state_checksum,
        current_checkpoint_id="checkpoint:replay-interruption",
        current_checksum=state_checksum,
        source_evidence_ids=(event_id,),
        maximum_work_items=1,
        approval_episode=210,
        expires_after_episode=211,
        reason_code="approve_interrupted_replay_acceptance",
    )
    issued = NDNRAReplayRestorationCheckpoint.with_issued_permit(
        permit,
        previous=base_checkpoint,
    )
    store.save(graph, growth_state=growth, replay_restoration_checkpoint=issued)
    before = store.load()
    fresh = _fresh_evidence(approval, captured_episode=211)
    request = ControlledRetentionReplayRequest(
        target_permit_id=permit.permit_id,
        expected_target_id=permit.target.target_id,
        expected_source_checkpoint_id=permit.target.source_checkpoint_id,
        expected_source_checkpoint_checksum=permit.target.source_checkpoint_checksum,
        expected_current_checkpoint_id=permit.target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=(permit.target.expected_current_checkpoint_checksum),
        expected_fresh_evidence_state_id=fresh.evidence_state_id,
        operation_episode=211,
        actor_code="operation:retention_replay",
        reason_code="interrupt_before_replay_save",
        work_items=(
            ControlledRetentionReplayWorkItem(
                work_item_id="replay-work-item:interruption-acceptance",
                source_evidence_id=event_id,
                structure_ids=(assembly_id,),
            ),
        ),
    )
    try:
        ControlledRetentionReplayDurablePolicy().execute_and_save(
            request=request,
            fresh_evidence=fresh,
            replay_restoration_checkpoint=before.replay_restoration_checkpoint,
            store=store,
            graph=before.graph,
            growth_state=before.growth_state,
            consolidation_checkpoint=before.consolidation_checkpoint,
            proposal_lifecycle_checkpoint=before.proposal_lifecycle_checkpoint,
            execution_checkpoint=before.execution_checkpoint,
            durable_interruption_hook=_raise_at("before_save"),
        )
    except RuntimeError:
        after = store.load()
        return bool(
            after.checksum == before.checksum
            and after.replay_restoration_checkpoint == before.replay_restoration_checkpoint
            and not store.temporary_path.exists()
        )
    return False


def _terminal_lifecycle_evidence(
    *,
    state_checksum: str,
    evidence_id: str,
) -> tuple[int, int, bool, bool]:
    cancelled, _ = _approved_permit(
        operation=ControlledReplayRestorationOperation.RETENTION_REPLAY,
        target_id="replay-target:cancelled-acceptance",
        source_checkpoint_id="checkpoint:lifecycle",
        source_checksum=state_checksum,
        current_checkpoint_id="checkpoint:lifecycle",
        current_checksum=state_checksum,
        source_evidence_ids=(evidence_id,),
        maximum_work_items=1,
        approval_episode=220,
        expires_after_episode=221,
        reason_code="approve_cancellation_acceptance",
    )
    expired, _ = _approved_permit(
        operation=ControlledReplayRestorationOperation.RETENTION_REPLAY,
        target_id="replay-target:expired-acceptance",
        source_checkpoint_id="checkpoint:lifecycle",
        source_checksum=state_checksum,
        current_checkpoint_id="checkpoint:lifecycle",
        current_checksum=state_checksum,
        source_evidence_ids=(evidence_id,),
        maximum_work_items=1,
        approval_episode=220,
        expires_after_episode=221,
        reason_code="approve_expiry_acceptance",
    )
    registry = ControlledReplayRestorationPermitLifecycleRegistry().add(cancelled).add(expired)
    registry = registry.transition(
        _transition_request(
            permit=cancelled,
            action=ControlledReplayRestorationPermitLifecycleAction.CANCEL,
            episode=221,
            actor_code="human:controlled_acceptance_operator",
            reason_code="cancel_unused_acceptance_permit",
        )
    )
    registry = registry.transition(
        _transition_request(
            permit=expired,
            action=ControlledReplayRestorationPermitLifecycleAction.EXPIRE,
            episode=222,
            actor_code="system:controlled_acceptance_clock",
            reason_code="record_expired_acceptance_permit",
        )
    )
    cancellation_enforced = _terminal_reuse_rejected(registry, cancelled, episode=221)
    expiry_enforced = _terminal_reuse_rejected(registry, expired, episode=223)
    cancelled_count = sum(
        record.status is ControlledReplayRestorationPermitLifecycleStatus.CANCELLED
        for record in registry.records
    )
    expired_count = sum(
        record.status is ControlledReplayRestorationPermitLifecycleStatus.EXPIRED
        for record in registry.records
    )
    return cancelled_count, expired_count, cancellation_enforced, expiry_enforced


def _transition_request(
    *,
    permit: ControlledReplayRestorationPermit,
    action: ControlledReplayRestorationPermitLifecycleAction,
    episode: int,
    actor_code: str,
    reason_code: str,
) -> ControlledReplayRestorationPermitTransitionRequest:
    target = permit.target
    return ControlledReplayRestorationPermitTransitionRequest(
        target_permit_id=permit.permit_id,
        expected_operation=target.operation,
        expected_target_id=target.target_id,
        expected_source_checkpoint_id=target.source_checkpoint_id,
        expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
        expected_current_checkpoint_id=target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=(target.expected_current_checkpoint_checksum),
        expected_evidence_state_id=permit.evidence.evidence_state_id,
        action=action,
        decision_episode=episode,
        actor_code=actor_code,
        reason_code=reason_code,
    )


def _terminal_reuse_rejected(
    registry: ControlledReplayRestorationPermitLifecycleRegistry,
    permit: ControlledReplayRestorationPermit,
    *,
    episode: int,
) -> bool:
    try:
        registry.transition(
            _transition_request(
                permit=permit,
                action=ControlledReplayRestorationPermitLifecycleAction.CANCEL,
                episode=episode,
                actor_code="human:controlled_acceptance_operator",
                reason_code="attempt_duplicate_terminal_transition",
            )
        )
    except ValueError as error:
        return "already terminal" in str(error)
    return False


def _corrupt_source_is_rejected(
    *,
    output_directory: Path,
    current_store: NDNRABrainStore,
    request: ControlledCheckpointRestorationRequest,
    fresh_evidence: ControlledReplayRestorationEvidence,
) -> bool:
    corrupt_path = output_directory / "controlled_restoration_corrupt_source.json"
    corrupt_path.write_text("not-json", encoding="ascii")
    before = current_store.load()
    try:
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=request,
            fresh_evidence=fresh_evidence,
            current_store=current_store,
            source_store=NDNRABrainStore(corrupt_path),
        )
    except ValueError:
        after = current_store.load()
        return bool(
            after.checksum == before.checksum
            and after.replay_restoration_checkpoint == before.replay_restoration_checkpoint
        )
    return False


def _restoration_interruption_recovers_new(
    *,
    output_directory: Path,
    source_store: NDNRABrainStore,
    current_load: BrainLoadResult,
    current_checkpoint: NDNRAReplayRestorationCheckpoint,
    source_checksum: str,
    current_checksum: str,
) -> bool:
    store = NDNRABrainStore(output_directory / "restoration_interruption_brain.json")
    store.save(
        current_load.graph,
        growth_state=current_load.growth_state,
        consolidation_checkpoint=current_load.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=current_load.proposal_lifecycle_checkpoint,
        execution_checkpoint=current_load.execution_checkpoint,
        replay_restoration_checkpoint=current_load.replay_restoration_checkpoint,
    )
    permit, approval = _approved_permit(
        operation=ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION,
        target_id="restoration-target:interruption-acceptance",
        source_checkpoint_id="checkpoint:restoration-source",
        source_checksum=source_checksum,
        current_checkpoint_id="checkpoint:restoration-interruption",
        current_checksum=current_checksum,
        source_evidence_ids=("evidence:restoration:interruption",),
        maximum_work_items=0,
        approval_episode=310,
        expires_after_episode=311,
        reason_code="approve_interrupted_restoration_acceptance",
    )
    issued = NDNRAReplayRestorationCheckpoint.with_issued_permit(
        permit,
        previous=current_checkpoint,
    )
    store.save(
        current_load.graph,
        growth_state=current_load.growth_state,
        consolidation_checkpoint=current_load.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=current_load.proposal_lifecycle_checkpoint,
        execution_checkpoint=current_load.execution_checkpoint,
        replay_restoration_checkpoint=issued,
    )
    fresh = _fresh_evidence(approval, captured_episode=311)
    request = ControlledCheckpointRestorationRequest(
        target_permit_id=permit.permit_id,
        expected_target_id=permit.target.target_id,
        expected_source_checkpoint_id=permit.target.source_checkpoint_id,
        expected_source_checkpoint_checksum=permit.target.source_checkpoint_checksum,
        expected_current_checkpoint_id=permit.target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=(permit.target.expected_current_checkpoint_checksum),
        expected_fresh_evidence_state_id=fresh.evidence_state_id,
        operation_episode=311,
        actor_code="operation:checkpoint_restoration",
        reason_code="interrupt_after_atomic_restoration_replace",
    )
    result = ControlledCheckpointRestorationPolicy().restore_and_save(
        request=request,
        fresh_evidence=fresh,
        current_store=store,
        source_store=source_store,
        persistence_interruption_hook=_raise_at("after_atomic_replace"),
    )
    loaded = store.load()
    return bool(
        result.recovered_after_interruption
        and result.save_result is None
        and loaded.state_checksum == source_checksum
        and loaded.replay_restoration_checkpoint.restoration_receipts == (result.receipt,)
        and not store.temporary_path.exists()
    )


def _restoration_reuse_is_rejected(
    *,
    current_store: NDNRABrainStore,
    source_store: NDNRABrainStore,
    request: ControlledCheckpointRestorationRequest,
    fresh_evidence: ControlledReplayRestorationEvidence,
) -> bool:
    try:
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=request,
            fresh_evidence=fresh_evidence,
            current_store=current_store,
            source_store=source_store,
        )
    except ValueError as error:
        return "issued unused permit" in str(error)
    return False


def _active_state_equal(first: BrainLoadResult, second: BrainLoadResult) -> bool:
    return bool(
        first.state_checksum == second.state_checksum
        and first.graph.snapshot() == second.graph.snapshot()
        and first.growth_state == second.growth_state
        and first.consolidation_checkpoint == second.consolidation_checkpoint
        and first.proposal_lifecycle_checkpoint == second.proposal_lifecycle_checkpoint
        and first.execution_checkpoint == second.execution_checkpoint
        and first.replay_restoration_checkpoint.activity_ledger
        == second.replay_restoration_checkpoint.activity_ledger
    )


def _with_dormancy(
    growth: NDNRAGrowthState,
    structure_id: str,
    value: float,
) -> NDNRAGrowthState:
    dormancy = dict(growth.dormancy_levels)
    dormancy[structure_id] = value
    return NDNRAGrowthState(
        pressure=growth.pressure,
        eligibility=growth.eligibility,
        residuals=growth.residuals,
        attempt_count=growth.attempt_count,
        last_active_members=growth.last_active_members,
        dormancy_levels=tuple(sorted(dormancy.items())),
    )


def _growth_without_dormancy(growth: NDNRAGrowthState) -> tuple[object, ...]:
    return (
        growth.pressure,
        growth.eligibility,
        growth.residuals,
        growth.attempt_count,
        growth.last_active_members,
    )


def _prediction_errors(result: UnifiedShadowResult) -> tuple[float, ...]:
    return tuple(metric.mean_absolute_error for metric in result.metrics)


def _write_comparison_csv(
    path: Path,
    first: UnifiedShadowResult,
    second: UnifiedShadowResult,
) -> None:
    with path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "first_action",
                "second_action",
                "first_suggestion",
                "second_suggestion",
                "first_prediction_error",
                "second_prediction_error",
            )
        )
        for first_record, second_record in zip(
            first.records,
            second.records,
            strict=True,
        ):
            writer.writerow(
                (
                    first_record.step_index,
                    first_record.actual_action.value,
                    second_record.actual_action.value,
                    ""
                    if first_record.suggested_action is None
                    else first_record.suggested_action.value,
                    ""
                    if second_record.suggested_action is None
                    else second_record.suggested_action.value,
                    first_record.prediction_error,
                    second_record.prediction_error,
                )
            )


def _write_ascii_json(path: Path, payload: object) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def _raise_at(expected_point: str) -> Callable[[str], None]:
    def interrupt(point: str) -> None:
        if point == expected_point:
            raise RuntimeError(f"interrupted at {point}")

    return interrupt


__all__ = [
    "ControlledReplayRestorationAcceptanceEvidence",
    "ControlledReplayRestorationAcceptanceResult",
    "export_controlled_replay_restoration_acceptance",
    "run_controlled_replay_restoration_acceptance",
]
