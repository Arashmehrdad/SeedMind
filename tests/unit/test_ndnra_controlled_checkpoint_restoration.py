"""Tests for exact restart-safe complete checkpoint restoration."""

# ruff: noqa: I001 -- pytest exposes adjacent support modules as top-level.

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable
from dataclasses import dataclass, replace
from pathlib import Path

import pytest

from ndnra_controlled_replay_test_support import build_replay_scenario
from ndnra_execution_test_support import build_setup

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
from seedmind.research.ndnra.controlled_checkpoint_restoration import (
    ControlledCheckpointRestorationDurableResult,
    ControlledCheckpointRestorationPolicy,
    ControlledCheckpointRestorationRequest,
)
from seedmind.research.ndnra.controlled_replay_restoration_approval import (
    ControlledReplayRestorationApprovalPolicy,
    ControlledReplayRestorationApprovalRequest,
    ControlledReplayRestorationEvidence,
    ControlledReplayRestorationOperation,
    ControlledReplayRestorationPermit,
    ControlledReplayRestorationTarget,
)
from seedmind.research.ndnra.controlled_replay_restoration_permit_lifecycle import (
    ControlledReplayRestorationPermitLifecycleStatus,
)
from seedmind.research.ndnra.controlled_replay_restoration_persistence import (
    NDNRAReplayRestorationCheckpoint,
)
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.persistence import (
    BrainLoadStatus,
    BrainSaveResult,
    NDNRABrainStore,
    NDNRAGrowthState,
)

_WINDOW_EVENT = "real:greenhouse:window"
_FAN_EVENT = "real:greenhouse:fan"
_RESTORATION_EVIDENCE = "evidence:restoration:complete-envelope"
_WINDOW_ASSEMBLY = "assembly:open_window"
_WINDOW_LINK = "assembly:open_window->fact:airflow"
_FAN_ASSEMBLY = "assembly:start_fan"
_FAN_LINK = "assembly:start_fan->fact:forced_airflow"
_WINDOW_STRUCTURES = tuple(sorted((_WINDOW_ASSEMBLY, _WINDOW_LINK)))
_FAN_STRUCTURES = tuple(sorted((_FAN_ASSEMBLY, _FAN_LINK)))


@dataclass(frozen=True, slots=True)
class _Scenario:
    source_store: NDNRABrainStore
    current_store: NDNRABrainStore
    source_graph: MultidimensionalExperienceGraph
    current_graph: MultidimensionalExperienceGraph
    source_growth: NDNRAGrowthState
    current_growth: NDNRAGrowthState
    source_checkpoint: NDNRAReplayRestorationCheckpoint
    issued_checkpoint: NDNRAReplayRestorationCheckpoint
    source_save: BrainSaveResult
    issued_save: BrainSaveResult
    permit: ControlledReplayRestorationPermit
    evidence: ControlledReplayRestorationEvidence
    request: ControlledCheckpointRestorationRequest


def _graph(*, include_fan: bool) -> MultidimensionalExperienceGraph:
    graph = MultidimensionalExperienceGraph()
    graph.learn_experience(
        assembly_id=_WINDOW_ASSEMBLY,
        action_code="open_window",
        origin_need_code="reduce_temperature",
        required_facts=("window_available",),
        produced_facts=("airflow",),
        observed_effects=(EffectObservation("temperature", -0.4, 0.9),),
    )
    if include_fan:
        graph.learn_experience(
            assembly_id=_FAN_ASSEMBLY,
            action_code="start_fan",
            origin_need_code="reduce_temperature",
            required_facts=("fan_available",),
            produced_facts=("forced_airflow",),
            observed_effects=(EffectObservation("temperature", -0.2, 0.9),),
        )
    return graph


def _activity(*, include_fan: bool) -> ActivityMaintenanceLedger:
    ledger = ActivityMaintenanceLedger()
    events = [(_WINDOW_EVENT, _WINDOW_STRUCTURES)]
    if include_fan:
        events.append((_FAN_EVENT, _FAN_STRUCTURES))
    for event_id, structures in events:
        ledger.consider(
            ActivityMaintenanceRequest(
                event_id=event_id,
                cycle=100,
                origin=ExperienceOrigin.REAL,
                structure_ids=structures,
                supporting_real_event_ids=(),
                relevance=1.0,
                helpfulness=1.0,
                prediction_accuracy=1.0,
                real_evidence_strength=1.0,
            )
        )
    return ledger


def _growth(*, include_fan: bool, dormancy: float) -> NDNRAGrowthState:
    dormancy_levels = [
        (_WINDOW_ASSEMBLY, dormancy),
        (_WINDOW_LINK, dormancy),
    ]
    if include_fan:
        dormancy_levels.extend(
            (
                (_FAN_ASSEMBLY, dormancy),
                (_FAN_LINK, dormancy),
            )
        )
    return NDNRAGrowthState(
        pressure=0.4 if include_fan else 0.2,
        eligibility=((_WINDOW_ASSEMBLY, 0.3),),
        residuals=(0.1,),
        attempt_count=5 if include_fan else 2,
        last_active_members=(_WINDOW_ASSEMBLY,),
        dormancy_levels=tuple(sorted(dormancy_levels)),
    )


def _scenario(root: Path) -> _Scenario:
    source_store = NDNRABrainStore(root / "restoration-source.json")
    current_store = NDNRABrainStore(root / "restoration-current.json")
    source_graph = _graph(include_fan=False)
    current_graph = _graph(include_fan=True)
    source_growth = _growth(include_fan=False, dormancy=0.9)
    current_growth = _growth(include_fan=True, dormancy=0.4)
    consolidation = NDNRAConsolidationCheckpoint.empty()
    proposal = NDNRAProposalLifecycleCheckpoint.empty()
    execution = NDNRAExecutionCheckpoint.empty()
    source_checkpoint = NDNRAReplayRestorationCheckpoint(
        activity_ledger=_activity(include_fan=False)
    )
    current_checkpoint = NDNRAReplayRestorationCheckpoint(
        activity_ledger=_activity(include_fan=True)
    )
    source_save = source_store.save(
        source_graph,
        growth_state=source_growth,
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=proposal,
        execution_checkpoint=execution,
        replay_restoration_checkpoint=source_checkpoint,
    )
    current_save = current_store.save(
        current_graph,
        growth_state=current_growth,
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=proposal,
        execution_checkpoint=execution,
        replay_restoration_checkpoint=current_checkpoint,
    )
    checkpoints = tuple(
        sorted(
            (
                ("checkpoint:archive", source_save.state_checksum),
                ("checkpoint:current", current_save.state_checksum),
            )
        )
    )
    approval_evidence = ControlledReplayRestorationEvidence(
        captured_episode=200,
        current_checkpoint_id="checkpoint:current",
        current_checkpoint_checksum=current_save.state_checksum,
        available_checkpoint_checksums=checkpoints,
        available_evidence_ids=(_RESTORATION_EVIDENCE,),
    )
    target = ControlledReplayRestorationTarget(
        operation=ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION,
        target_id="restoration-target:archive-v1",
        source_checkpoint_id="checkpoint:archive",
        source_checkpoint_checksum=source_save.state_checksum,
        expected_current_checkpoint_id="checkpoint:current",
        expected_current_checkpoint_checksum=current_save.state_checksum,
        source_evidence_ids=(_RESTORATION_EVIDENCE,),
        maximum_work_items=0,
    )
    permit = ControlledReplayRestorationApprovalPolicy().evaluate(
        request=ControlledReplayRestorationApprovalRequest(
            target=target,
            expected_evidence_state_id=approval_evidence.evidence_state_id,
            approval_episode=200,
            expires_after_episode=201,
            approver_code="human:operator",
            reason_code="approve_complete_archive_restoration",
        ),
        evidence=approval_evidence,
    )
    issued_checkpoint = NDNRAReplayRestorationCheckpoint.with_issued_permit(
        permit,
        previous=current_checkpoint,
    )
    issued_save = current_store.save(
        current_graph,
        growth_state=current_growth,
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=proposal,
        execution_checkpoint=execution,
        replay_restoration_checkpoint=issued_checkpoint,
    )
    evidence = ControlledReplayRestorationEvidence(
        captured_episode=201,
        current_checkpoint_id="checkpoint:current",
        current_checkpoint_checksum=current_save.state_checksum,
        available_checkpoint_checksums=checkpoints,
        available_evidence_ids=(_RESTORATION_EVIDENCE,),
    )
    request = ControlledCheckpointRestorationRequest(
        target_permit_id=permit.permit_id,
        expected_target_id=target.target_id,
        expected_source_checkpoint_id=target.source_checkpoint_id,
        expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
        expected_current_checkpoint_id=target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=(target.expected_current_checkpoint_checksum),
        expected_fresh_evidence_state_id=evidence.evidence_state_id,
        operation_episode=201,
        actor_code="operation:checkpoint_restoration",
        reason_code="restore_exact_complete_archive",
    )
    return _Scenario(
        source_store=source_store,
        current_store=current_store,
        source_graph=source_graph,
        current_graph=current_graph,
        source_growth=source_growth,
        current_growth=current_growth,
        source_checkpoint=source_checkpoint,
        issued_checkpoint=issued_checkpoint,
        source_save=source_save,
        issued_save=issued_save,
        permit=permit,
        evidence=evidence,
        request=request,
    )


def _raise_at(expected: str) -> Callable[[str], None]:
    def interrupt(point: str) -> None:
        if point == expected:
            raise RuntimeError(f"interrupted at {point}")

    return interrupt


def _restore(
    root: Path,
    *,
    durable_interruption_hook: Callable[[str], None] | None = None,
    persistence_interruption_hook: Callable[[str], None] | None = None,
) -> tuple[_Scenario, ControlledCheckpointRestorationDurableResult]:
    scenario = _scenario(root)
    result = ControlledCheckpointRestorationPolicy().restore_and_save(
        request=scenario.request,
        fresh_evidence=scenario.evidence,
        current_store=scenario.current_store,
        source_store=scenario.source_store,
        durable_interruption_hook=durable_interruption_hook,
        persistence_interruption_hook=persistence_interruption_hook,
    )
    return scenario, result


def test_restoration_replaces_complete_active_brain_and_preserves_audit(
    tmp_path: Path,
) -> None:
    scenario, result = _restore(tmp_path)
    restarted = scenario.current_store.load()
    record = restarted.replay_restoration_checkpoint.permit_registry.record_for(
        scenario.permit.permit_id
    )

    assert restarted.status is BrainLoadStatus.LOADED
    assert restarted.checksum_verified
    assert not restarted.used_fallback
    assert restarted.graph.snapshot() == scenario.source_graph.snapshot()
    assert restarted.graph.snapshot() != scenario.current_graph.snapshot()
    assert restarted.growth_state == scenario.source_growth
    assert restarted.growth_state != scenario.current_growth
    assert restarted.replay_restoration_checkpoint.activity_ledger == (
        scenario.source_checkpoint.activity_ledger
    )
    assert record.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED
    assert record.consumption_count == 1
    assert record.decisions[0].consumption_reference_code == result.receipt.receipt_id
    assert restarted.replay_restoration_checkpoint.restoration_receipts == (result.receipt,)
    assert result.receipt.restored_complete_envelope
    assert result.receipt.partial_restoration_count == 0
    assert not result.receipt.has_restoration_authority
    assert not result.receipt.has_cognitive_authority
    assert not result.receipt.has_production_action_authority
    assert restarted.state_checksum == scenario.source_save.state_checksum
    assert restarted.checksum != scenario.source_save.checksum
    assert restarted.checksum != scenario.issued_save.checksum
    assert result.save_result is not None
    assert not result.recovered_after_interruption
    assert _WINDOW_ASSEMBLY in dict(restarted.growth_state.dormancy_levels)
    assert _FAN_ASSEMBLY not in dict(restarted.growth_state.dormancy_levels)


def test_restoration_audit_survives_restart_and_blocks_permit_reuse(
    tmp_path: Path,
) -> None:
    scenario, result = _restore(tmp_path)
    restarted = scenario.current_store.load()

    with pytest.raises(ValueError, match="issued unused permit"):
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=scenario.request,
            fresh_evidence=scenario.evidence,
            current_store=scenario.current_store,
            source_store=scenario.source_store,
        )

    after = scenario.current_store.load()
    assert after.replay_restoration_checkpoint == (restarted.replay_restoration_checkpoint)
    assert after.replay_restoration_checkpoint.restoration_receipts == (result.receipt,)
    assert after.replay_restoration_checkpoint.permit_registry.restoration_consumption_count == 1


def test_interruption_before_save_preserves_exact_current_envelope(
    tmp_path: Path,
) -> None:
    scenario = _scenario(tmp_path)
    before = scenario.current_store.load()

    with pytest.raises(RuntimeError, match="before_save"):
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=scenario.request,
            fresh_evidence=scenario.evidence,
            current_store=scenario.current_store,
            source_store=scenario.source_store,
            durable_interruption_hook=_raise_at("before_save"),
        )

    after = scenario.current_store.load()
    assert after.checksum == before.checksum
    assert after.state_checksum == before.state_checksum
    assert after.graph.snapshot() == before.graph.snapshot()
    assert after.growth_state == before.growth_state
    assert after.replay_restoration_checkpoint == before.replay_restoration_checkpoint
    assert after.replay_restoration_checkpoint.restoration_receipts == ()
    assert (
        after.replay_restoration_checkpoint.permit_registry.record_for(
            scenario.permit.permit_id
        ).status
        is ControlledReplayRestorationPermitLifecycleStatus.ISSUED
    )


def test_interruption_after_replace_recovers_complete_restored_envelope(
    tmp_path: Path,
) -> None:
    scenario, result = _restore(
        tmp_path,
        persistence_interruption_hook=_raise_at("after_atomic_replace"),
    )

    restarted = scenario.current_store.load()
    record = restarted.replay_restoration_checkpoint.permit_registry.record_for(
        scenario.permit.permit_id
    )
    assert result.recovered_after_interruption
    assert result.save_result is None
    assert restarted.graph.snapshot() == scenario.source_graph.snapshot()
    assert restarted.growth_state == scenario.source_growth
    assert restarted.state_checksum == scenario.source_save.state_checksum
    assert record.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED
    assert restarted.replay_restoration_checkpoint.restoration_receipts == (result.receipt,)
    assert not scenario.current_store.temporary_path.exists()


def test_restoration_rejects_same_path_or_corrupt_source_without_mutation(
    tmp_path: Path,
) -> None:
    scenario = _scenario(tmp_path)

    with pytest.raises(ValueError, match="source and current store must differ"):
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=scenario.request,
            fresh_evidence=scenario.evidence,
            current_store=scenario.current_store,
            source_store=scenario.current_store,
        )

    scenario.source_store.path.write_text("not-json", encoding="ascii")
    with pytest.raises(ValueError, match="source checkpoint is not loadable"):
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=scenario.request,
            fresh_evidence=scenario.evidence,
            current_store=scenario.current_store,
            source_store=scenario.source_store,
        )

    current = scenario.current_store.load()
    assert current.graph.snapshot() == scenario.current_graph.snapshot()
    assert current.growth_state == scenario.current_growth
    assert current.replay_restoration_checkpoint.restoration_receipts == ()


def test_restoration_replaces_every_persisted_active_component(tmp_path: Path) -> None:
    source_setup = build_setup()
    source_store = NDNRABrainStore(tmp_path / "complete-source.json")
    current_store = NDNRABrainStore(tmp_path / "complete-current.json")
    source_proposal = NDNRAProposalLifecycleCheckpoint(registry=source_setup.proposal_registry)
    source_replay = NDNRAReplayRestorationCheckpoint.empty()
    source_save = source_store.save(
        source_setup.graph,
        growth_state=source_setup.growth_state,
        consolidation_checkpoint=source_setup.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=source_proposal,
        execution_checkpoint=source_setup.execution_checkpoint,
        replay_restoration_checkpoint=source_replay,
    )

    current_graph = _graph(include_fan=True)
    current_growth = _growth(include_fan=True, dormancy=0.35)
    current_replay = NDNRAReplayRestorationCheckpoint(activity_ledger=_activity(include_fan=True))
    current_save = current_store.save(
        current_graph,
        growth_state=current_growth,
        consolidation_checkpoint=NDNRAConsolidationCheckpoint.empty(),
        proposal_lifecycle_checkpoint=NDNRAProposalLifecycleCheckpoint.empty(),
        execution_checkpoint=NDNRAExecutionCheckpoint.empty(),
        replay_restoration_checkpoint=current_replay,
    )
    checkpoints = tuple(
        sorted(
            (
                ("checkpoint:archive-complete", source_save.state_checksum),
                ("checkpoint:current-complete", current_save.state_checksum),
            )
        )
    )
    approval = ControlledReplayRestorationEvidence(
        captured_episode=300,
        current_checkpoint_id="checkpoint:current-complete",
        current_checkpoint_checksum=current_save.state_checksum,
        available_checkpoint_checksums=checkpoints,
        available_evidence_ids=(_RESTORATION_EVIDENCE,),
    )
    target = ControlledReplayRestorationTarget(
        operation=ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION,
        target_id="restoration-target:complete-component-set",
        source_checkpoint_id="checkpoint:archive-complete",
        source_checkpoint_checksum=source_save.state_checksum,
        expected_current_checkpoint_id="checkpoint:current-complete",
        expected_current_checkpoint_checksum=current_save.state_checksum,
        source_evidence_ids=(_RESTORATION_EVIDENCE,),
        maximum_work_items=0,
    )
    permit = ControlledReplayRestorationApprovalPolicy().evaluate(
        request=ControlledReplayRestorationApprovalRequest(
            target=target,
            expected_evidence_state_id=approval.evidence_state_id,
            approval_episode=300,
            expires_after_episode=301,
            approver_code="human:operator",
            reason_code="approve_complete_component_restoration",
        ),
        evidence=approval,
    )
    issued = NDNRAReplayRestorationCheckpoint.with_issued_permit(
        permit,
        previous=current_replay,
    )
    current_store.save(
        current_graph,
        growth_state=current_growth,
        consolidation_checkpoint=NDNRAConsolidationCheckpoint.empty(),
        proposal_lifecycle_checkpoint=NDNRAProposalLifecycleCheckpoint.empty(),
        execution_checkpoint=NDNRAExecutionCheckpoint.empty(),
        replay_restoration_checkpoint=issued,
    )
    fresh = ControlledReplayRestorationEvidence(
        captured_episode=301,
        current_checkpoint_id="checkpoint:current-complete",
        current_checkpoint_checksum=current_save.state_checksum,
        available_checkpoint_checksums=checkpoints,
        available_evidence_ids=(_RESTORATION_EVIDENCE,),
    )
    request = ControlledCheckpointRestorationRequest(
        target_permit_id=permit.permit_id,
        expected_target_id=target.target_id,
        expected_source_checkpoint_id=target.source_checkpoint_id,
        expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
        expected_current_checkpoint_id=target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=(target.expected_current_checkpoint_checksum),
        expected_fresh_evidence_state_id=fresh.evidence_state_id,
        operation_episode=301,
        actor_code="operation:checkpoint_restoration",
        reason_code="restore_all_persisted_active_components",
    )

    result = ControlledCheckpointRestorationPolicy().restore_and_save(
        request=request,
        fresh_evidence=fresh,
        current_store=current_store,
        source_store=source_store,
    )
    restored = current_store.load()

    assert restored.graph.snapshot() == source_setup.graph.snapshot()
    assert restored.growth_state == source_setup.growth_state
    assert restored.consolidation_checkpoint == source_setup.consolidation_checkpoint
    assert restored.proposal_lifecycle_checkpoint == source_proposal
    assert restored.execution_checkpoint == source_setup.execution_checkpoint
    assert restored.replay_restoration_checkpoint.activity_ledger == (source_replay.activity_ledger)
    assert restored.state_checksum == source_save.state_checksum
    assert restored.replay_restoration_checkpoint.restoration_receipts == (result.receipt,)
    assert restored.consolidation_checkpoint != NDNRAConsolidationCheckpoint.empty()
    assert restored.proposal_lifecycle_checkpoint != (NDNRAProposalLifecycleCheckpoint.empty())
    assert restored.execution_checkpoint != NDNRAExecutionCheckpoint.empty()


def test_restoration_rejects_migrated_source_without_mutation(tmp_path: Path) -> None:
    scenario = _scenario(tmp_path)
    before = scenario.current_store.load()
    _rewrite_as_schema_5(scenario.source_store.path)

    with pytest.raises(ValueError, match="complete current brain schema"):
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=scenario.request,
            fresh_evidence=scenario.evidence,
            current_store=scenario.current_store,
            source_store=scenario.source_store,
        )

    after = scenario.current_store.load()
    assert after.checksum == before.checksum
    assert after.state_checksum == before.state_checksum
    assert after.replay_restoration_checkpoint == before.replay_restoration_checkpoint


def test_restoration_rejects_fresh_evidence_drift_and_expired_permit(
    tmp_path: Path,
) -> None:
    scenario = _scenario(tmp_path)
    before = scenario.current_store.load()
    drifted_evidence = ControlledReplayRestorationEvidence(
        captured_episode=scenario.evidence.captured_episode,
        current_checkpoint_id=scenario.evidence.current_checkpoint_id,
        current_checkpoint_checksum=scenario.evidence.current_checkpoint_checksum,
        available_checkpoint_checksums=(scenario.evidence.available_checkpoint_checksums),
        available_evidence_ids=tuple(
            sorted((*scenario.evidence.available_evidence_ids, "evidence:unexpected"))
        ),
    )
    drifted_request = replace(
        scenario.request,
        expected_fresh_evidence_state_id=drifted_evidence.evidence_state_id,
    )

    with pytest.raises(ValueError, match="fresh restoration evidence identities drifted"):
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=drifted_request,
            fresh_evidence=drifted_evidence,
            current_store=scenario.current_store,
            source_store=scenario.source_store,
        )

    expired_evidence = replace(scenario.evidence, captured_episode=202)
    expired_request = replace(
        scenario.request,
        expected_fresh_evidence_state_id=expired_evidence.evidence_state_id,
        operation_episode=202,
    )
    with pytest.raises(ValueError, match="unexpired permit"):
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=expired_request,
            fresh_evidence=expired_evidence,
            current_store=scenario.current_store,
            source_store=scenario.source_store,
        )

    after = scenario.current_store.load()
    assert after.checksum == before.checksum
    assert after.replay_restoration_checkpoint == before.replay_restoration_checkpoint


def test_restoration_rejects_source_audit_not_contained_by_current(
    tmp_path: Path,
) -> None:
    scenario = _scenario(tmp_path)
    before = scenario.current_store.load()
    unrelated = build_replay_scenario(tmp_path / "unrelated")
    divergent_source_audit = NDNRAReplayRestorationCheckpoint.with_issued_permit(
        unrelated.permit,
        previous=scenario.source_checkpoint,
    )
    changed = scenario.source_store.save(
        scenario.source_graph,
        growth_state=scenario.source_growth,
        consolidation_checkpoint=NDNRAConsolidationCheckpoint.empty(),
        proposal_lifecycle_checkpoint=NDNRAProposalLifecycleCheckpoint.empty(),
        execution_checkpoint=NDNRAExecutionCheckpoint.empty(),
        replay_restoration_checkpoint=divergent_source_audit,
    )
    assert changed.state_checksum == scenario.source_save.state_checksum

    with pytest.raises(ValueError, match="current operation audit does not contain"):
        ControlledCheckpointRestorationPolicy().restore_and_save(
            request=scenario.request,
            fresh_evidence=scenario.evidence,
            current_store=scenario.current_store,
            source_store=scenario.source_store,
        )

    after = scenario.current_store.load()
    assert after.checksum == before.checksum
    assert after.replay_restoration_checkpoint == before.replay_restoration_checkpoint


def _rewrite_as_schema_5(path: Path) -> None:
    raw_value: object = json.loads(path.read_text(encoding="ascii"))
    assert isinstance(raw_value, dict)
    raw: dict[str, object] = raw_value
    raw.pop("state_checksum", None)
    raw["schema_version"] = 5
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
