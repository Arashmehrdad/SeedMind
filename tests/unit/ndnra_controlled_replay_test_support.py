"""Shared deterministic fixtures for durable controlled replay tests."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from seedmind.research.ndnra.activity_maintenance import (
    ActivityMaintenanceLedger,
    ActivityMaintenanceRequest,
)
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
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.controlled_replay_restoration_approval import (
    ControlledReplayRestorationApprovalPolicy,
    ControlledReplayRestorationApprovalRequest,
    ControlledReplayRestorationEvidence,
    ControlledReplayRestorationOperation,
    ControlledReplayRestorationPermit,
    ControlledReplayRestorationTarget,
)
from seedmind.research.ndnra.controlled_replay_restoration_persistence import (
    NDNRAReplayRestorationCheckpoint,
)
from seedmind.research.ndnra.controlled_retention_replay import (
    ControlledRetentionReplayRequest,
    ControlledRetentionReplayWorkItem,
)
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.persistence import (
    BrainSaveResult,
    NDNRABrainStore,
    NDNRAGrowthState,
)

WINDOW_EVENT = "real:greenhouse:window"
WINDOW_ASSEMBLY = "assembly:open_window"
WINDOW_LINK = "assembly:open_window->fact:airflow"
WINDOW_STRUCTURES = tuple(sorted((WINDOW_ASSEMBLY, WINDOW_LINK)))


@dataclass(frozen=True, slots=True)
class ReplayScenario:
    store: NDNRABrainStore
    graph: MultidimensionalExperienceGraph
    growth_state: NDNRAGrowthState
    consolidation_checkpoint: NDNRAConsolidationCheckpoint
    proposal_checkpoint: NDNRAProposalLifecycleCheckpoint
    execution_checkpoint: NDNRAExecutionCheckpoint
    initial_checkpoint: NDNRAReplayRestorationCheckpoint
    issued_checkpoint: NDNRAReplayRestorationCheckpoint
    initial_save: BrainSaveResult
    issued_save: BrainSaveResult
    permit: ControlledReplayRestorationPermit
    fresh_evidence: ControlledReplayRestorationEvidence
    request: ControlledRetentionReplayRequest


def build_replay_scenario(root: Path) -> ReplayScenario:
    store = NDNRABrainStore(root / "replay-current.json")
    graph = MultidimensionalExperienceGraph()
    graph.learn_experience(
        assembly_id=WINDOW_ASSEMBLY,
        action_code="open_window",
        origin_need_code="reduce_temperature",
        required_facts=("window_available",),
        produced_facts=("airflow",),
        observed_effects=(EffectObservation("temperature", -0.4, 0.9),),
    )
    growth = NDNRAGrowthState(
        pressure=0.2,
        eligibility=((WINDOW_ASSEMBLY, 0.3),),
        residuals=(0.1,),
        attempt_count=2,
        last_active_members=(WINDOW_ASSEMBLY,),
        dormancy_levels=((WINDOW_ASSEMBLY, 0.8), (WINDOW_LINK, 0.8)),
    )
    consolidation = NDNRAConsolidationCheckpoint.empty()
    proposal = NDNRAProposalLifecycleCheckpoint.empty()
    execution = NDNRAExecutionCheckpoint.empty()
    ledger = ActivityMaintenanceLedger()
    ledger.consider(
        ActivityMaintenanceRequest(
            event_id=WINDOW_EVENT,
            cycle=100,
            origin=ExperienceOrigin.REAL,
            structure_ids=WINDOW_STRUCTURES,
            supporting_real_event_ids=(),
            relevance=1.0,
            helpfulness=1.0,
            prediction_accuracy=1.0,
            real_evidence_strength=1.0,
        )
    )
    checkpoint = NDNRAReplayRestorationCheckpoint(activity_ledger=ledger)
    initial_save = store.save(
        graph,
        growth_state=growth,
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=proposal,
        execution_checkpoint=execution,
        replay_restoration_checkpoint=checkpoint,
    )
    evidence = ControlledReplayRestorationEvidence(
        captured_episode=200,
        current_checkpoint_id="checkpoint:current",
        current_checkpoint_checksum=initial_save.state_checksum,
        available_checkpoint_checksums=(("checkpoint:current", initial_save.state_checksum),),
        available_evidence_ids=(WINDOW_EVENT,),
    )
    target = ControlledReplayRestorationTarget(
        operation=ControlledReplayRestorationOperation.RETENTION_REPLAY,
        target_id="replay-target:window-retention-v1",
        source_checkpoint_id="checkpoint:current",
        source_checkpoint_checksum=initial_save.state_checksum,
        expected_current_checkpoint_id="checkpoint:current",
        expected_current_checkpoint_checksum=initial_save.state_checksum,
        source_evidence_ids=(WINDOW_EVENT,),
        maximum_work_items=1,
    )
    permit = ControlledReplayRestorationApprovalPolicy().evaluate(
        request=ControlledReplayRestorationApprovalRequest(
            target=target,
            expected_evidence_state_id=evidence.evidence_state_id,
            approval_episode=200,
            expires_after_episode=201,
            approver_code="human:operator",
            reason_code="approve_restart_safe_retention_replay",
        ),
        evidence=evidence,
    )
    issued_checkpoint = NDNRAReplayRestorationCheckpoint.with_issued_permit(
        permit,
        previous=checkpoint,
    )
    issued_save = store.save(
        graph,
        growth_state=growth,
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=proposal,
        execution_checkpoint=execution,
        replay_restoration_checkpoint=issued_checkpoint,
    )
    fresh = ControlledReplayRestorationEvidence(
        captured_episode=201,
        current_checkpoint_id="checkpoint:current",
        current_checkpoint_checksum=initial_save.state_checksum,
        available_checkpoint_checksums=(("checkpoint:current", initial_save.state_checksum),),
        available_evidence_ids=(WINDOW_EVENT,),
    )
    request = ControlledRetentionReplayRequest(
        target_permit_id=permit.permit_id,
        expected_target_id=target.target_id,
        expected_source_checkpoint_id=target.source_checkpoint_id,
        expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
        expected_current_checkpoint_id=target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=(target.expected_current_checkpoint_checksum),
        expected_fresh_evidence_state_id=fresh.evidence_state_id,
        operation_episode=201,
        actor_code="operation:retention_replay",
        reason_code="refresh_exact_window_memory",
        work_items=(
            ControlledRetentionReplayWorkItem(
                work_item_id="replay-work-item:window",
                source_evidence_id=WINDOW_EVENT,
                structure_ids=WINDOW_STRUCTURES,
            ),
        ),
    )
    return ReplayScenario(
        store=store,
        graph=graph,
        growth_state=growth,
        consolidation_checkpoint=consolidation,
        proposal_checkpoint=proposal,
        execution_checkpoint=execution,
        initial_checkpoint=checkpoint,
        issued_checkpoint=issued_checkpoint,
        initial_save=initial_save,
        issued_save=issued_save,
        permit=permit,
        fresh_evidence=fresh,
        request=request,
    )


def raise_at(expected_point: str) -> Callable[[str], None]:
    def interrupt(point: str) -> None:
        if point == expected_point:
            raise RuntimeError(f"interrupted at {point}")

    return interrupt
