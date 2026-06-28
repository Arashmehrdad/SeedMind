"""Tests for single-use bounded replay of exact real activity."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra.activity_maintenance import (
    ActivityMaintenanceLedger,
    ActivityMaintenanceRequest,
)
from seedmind.research.ndnra.adaptive import NDNRARuntimeAdaptiveState
from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.controlled_replay_restoration_approval import (
    ControlledReplayRestorationApprovalPolicy,
    ControlledReplayRestorationApprovalRequest,
    ControlledReplayRestorationEvidence,
    ControlledReplayRestorationOperation,
    ControlledReplayRestorationPermit,
    ControlledReplayRestorationTarget,
)
from seedmind.research.ndnra.controlled_replay_restoration_permit_lifecycle import (
    ControlledReplayRestorationPermitLifecycleAction,
    ControlledReplayRestorationPermitLifecycleRegistry,
    ControlledReplayRestorationPermitLifecycleStatus,
    ControlledReplayRestorationPermitTransitionRequest,
)
from seedmind.research.ndnra.controlled_retention_replay import (
    ControlledRetentionReplayOperation,
    ControlledRetentionReplayReceipt,
    ControlledRetentionReplayRequest,
    ControlledRetentionReplayResult,
    ControlledRetentionReplayWorkItem,
)
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.persistence import NDNRAGrowthState

_CURRENT_CHECKSUM = "a" * 64
_ARCHIVE_CHECKSUM = "b" * 64
_WINDOW_EVENT = "real:greenhouse:window"
_FAN_EVENT = "real:greenhouse:fan"
_WINDOW_ASSEMBLY = "assembly:open_window"
_WINDOW_LINK = "assembly:open_window->fact:airflow"
_FAN_ASSEMBLY = "assembly:start_fan"
_FAN_LINK = "assembly:start_fan->fact:forced_airflow"
_WINDOW_STRUCTURES = tuple(sorted((_WINDOW_ASSEMBLY, _WINDOW_LINK)))
_FAN_STRUCTURES = tuple(sorted((_FAN_ASSEMBLY, _FAN_LINK)))
_EVIDENCE_IDS = tuple(sorted((_WINDOW_EVENT, _FAN_EVENT)))


def _graph(*, include_fan: bool = True) -> MultidimensionalExperienceGraph:
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


def _activity_ledger(
    *,
    fan_harmful: bool = False,
    fan_structures: tuple[str, ...] = _FAN_STRUCTURES,
) -> ActivityMaintenanceLedger:
    ledger = ActivityMaintenanceLedger()
    for event_id, structures, harmful in (
        (_WINDOW_EVENT, _WINDOW_STRUCTURES, False),
        (_FAN_EVENT, fan_structures, fan_harmful),
    ):
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
                harmful=harmful,
            )
        )
    return ledger


def _runtime(*, include_fan: bool = True) -> NDNRARuntimeAdaptiveState:
    dormancy = [
        (_WINDOW_ASSEMBLY, 0.8),
        (_WINDOW_LINK, 0.8),
    ]
    if include_fan:
        dormancy.extend(((_FAN_ASSEMBLY, 0.8), (_FAN_LINK, 0.8)))
    return NDNRARuntimeAdaptiveState.from_growth_state(
        _graph(include_fan=include_fan),
        NDNRAGrowthState(
            pressure=0.4,
            eligibility=((_WINDOW_ASSEMBLY, 0.3),),
            residuals=(0.1,),
            attempt_count=5,
            last_active_members=(_WINDOW_ASSEMBLY,),
            dormancy_levels=tuple(sorted(dormancy)),
        ),
    )


def _evidence(
    *,
    captured_episode: int,
    current_checksum: str = _CURRENT_CHECKSUM,
    evidence_ids: tuple[str, ...] = _EVIDENCE_IDS,
    checksum_verified: bool = True,
    used_fallback: bool = False,
) -> ControlledReplayRestorationEvidence:
    return ControlledReplayRestorationEvidence(
        captured_episode=captured_episode,
        current_checkpoint_id="checkpoint:current",
        current_checkpoint_checksum=current_checksum,
        available_checkpoint_checksums=(
            ("checkpoint:archive", _ARCHIVE_CHECKSUM),
            ("checkpoint:current", current_checksum),
        ),
        available_evidence_ids=evidence_ids,
        checksum_verified=checksum_verified,
        used_fallback=used_fallback,
    )


def _target(
    operation: ControlledReplayRestorationOperation = (
        ControlledReplayRestorationOperation.RETENTION_REPLAY
    ),
    *,
    maximum_work_items: int = 2,
) -> ControlledReplayRestorationTarget:
    if operation is ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION:
        return ControlledReplayRestorationTarget(
            operation=operation,
            target_id="restoration-target:archive-v1",
            source_checkpoint_id="checkpoint:archive",
            source_checkpoint_checksum=_ARCHIVE_CHECKSUM,
            expected_current_checkpoint_id="checkpoint:current",
            expected_current_checkpoint_checksum=_CURRENT_CHECKSUM,
            source_evidence_ids=_EVIDENCE_IDS,
            maximum_work_items=0,
        )
    return ControlledReplayRestorationTarget(
        operation=operation,
        target_id="replay-target:greenhouse-retention-v1",
        source_checkpoint_id="checkpoint:current",
        source_checkpoint_checksum=_CURRENT_CHECKSUM,
        expected_current_checkpoint_id="checkpoint:current",
        expected_current_checkpoint_checksum=_CURRENT_CHECKSUM,
        source_evidence_ids=_EVIDENCE_IDS,
        maximum_work_items=maximum_work_items,
    )


def _permit(
    operation: ControlledReplayRestorationOperation = (
        ControlledReplayRestorationOperation.RETENTION_REPLAY
    ),
    *,
    maximum_work_items: int = 2,
) -> ControlledReplayRestorationPermit:
    evidence = _evidence(captured_episode=200)
    target = _target(operation, maximum_work_items=maximum_work_items)
    return ControlledReplayRestorationApprovalPolicy().evaluate(
        request=ControlledReplayRestorationApprovalRequest(
            target=target,
            expected_evidence_state_id=evidence.evidence_state_id,
            approval_episode=200,
            expires_after_episode=201,
            approver_code="human:operator",
            reason_code="approve_exact_greenhouse_retention_replay",
        ),
        evidence=evidence,
    )


def _registry(
    operation: ControlledReplayRestorationOperation = (
        ControlledReplayRestorationOperation.RETENTION_REPLAY
    ),
    *,
    maximum_work_items: int = 2,
) -> ControlledReplayRestorationPermitLifecycleRegistry:
    return ControlledReplayRestorationPermitLifecycleRegistry().add(
        _permit(operation, maximum_work_items=maximum_work_items)
    )


def _items() -> tuple[ControlledRetentionReplayWorkItem, ...]:
    return (
        ControlledRetentionReplayWorkItem(
            work_item_id="replay-work-item:fan",
            source_evidence_id=_FAN_EVENT,
            structure_ids=_FAN_STRUCTURES,
        ),
        ControlledRetentionReplayWorkItem(
            work_item_id="replay-work-item:window",
            source_evidence_id=_WINDOW_EVENT,
            structure_ids=_WINDOW_STRUCTURES,
        ),
    )


def _request(
    registry: ControlledReplayRestorationPermitLifecycleRegistry,
    fresh: ControlledReplayRestorationEvidence,
    *,
    work_items: tuple[ControlledRetentionReplayWorkItem, ...] | None = None,
    operation_episode: int = 201,
) -> ControlledRetentionReplayRequest:
    permit = registry.records[0].permit
    target = permit.target
    return ControlledRetentionReplayRequest(
        target_permit_id=permit.permit_id,
        expected_target_id=target.target_id,
        expected_source_checkpoint_id=target.source_checkpoint_id,
        expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
        expected_current_checkpoint_id=target.expected_current_checkpoint_id,
        expected_current_checkpoint_checksum=target.expected_current_checkpoint_checksum,
        expected_fresh_evidence_state_id=fresh.evidence_state_id,
        operation_episode=operation_episode,
        actor_code="operation:retention_replay",
        reason_code="refresh_exact_real_greenhouse_memories",
        work_items=_items() if work_items is None else work_items,
    )


def _execute(
    *,
    registry: ControlledReplayRestorationPermitLifecycleRegistry | None = None,
    fresh: ControlledReplayRestorationEvidence | None = None,
    ledger: ActivityMaintenanceLedger | None = None,
    runtime: NDNRARuntimeAdaptiveState | None = None,
    request: ControlledRetentionReplayRequest | None = None,
) -> ControlledRetentionReplayResult:
    selected_registry = _registry() if registry is None else registry
    selected_fresh = _evidence(captured_episode=201) if fresh is None else fresh
    selected_ledger = _activity_ledger() if ledger is None else ledger
    selected_runtime = _runtime() if runtime is None else runtime
    selected_request = _request(selected_registry, selected_fresh) if request is None else request
    return ControlledRetentionReplayOperation().execute(
        request=selected_request,
        fresh_evidence=selected_fresh,
        lifecycle_registry=selected_registry,
        activity_ledger=selected_ledger,
        adaptive_state=selected_runtime,
    )


def test_success_replays_exact_real_activity_and_consumes_one_permit() -> None:
    registry = _registry()
    ledger = _activity_ledger()
    runtime = _runtime()
    fresh = _evidence(captured_episode=201)
    registry_before = registry.snapshot()
    ledger_before = ledger.snapshot()
    state_before = runtime.to_growth_state()
    graph_before = runtime.graph.snapshot()

    result = _execute(
        registry=registry,
        fresh=fresh,
        ledger=ledger,
        runtime=runtime,
    )

    receipt = result.receipt
    consumed = result.lifecycle_registry.record_for(receipt.permit_id)
    assert receipt.receipt_id.startswith("retention-replay-receipt:")
    assert receipt.work_item_count == 2
    assert receipt.total_reactivation == pytest.approx(1.2)
    assert receipt.factual_confidence_delta == 0.0
    assert receipt.mastery_delta == 0.0
    assert not receipt.has_learning_authority
    assert not receipt.has_action_selection_authority
    assert not receipt.has_production_action_authority
    assert consumed.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED
    assert consumed.decisions[0].consumption_reference_code == receipt.receipt_id
    assert result.lifecycle_registry.replay_consumption_count == 1
    assert result.activity_ledger.real_activity_count == 2
    assert result.activity_ledger.replay_activity_count == 2
    assert result.adaptive_state.accessibility(_WINDOW_ASSEMBLY) == pytest.approx(0.5)
    assert result.adaptive_state.accessibility(_FAN_ASSEMBLY) == pytest.approx(0.5)
    assert result.adaptive_state.graph.snapshot() == graph_before
    assert result.input_state_unchanged

    assert registry.snapshot() == registry_before
    assert ledger.snapshot() == ledger_before
    assert runtime.to_growth_state() == state_before
    assert runtime.graph.snapshot() == graph_before
    assert registry.record_for(receipt.permit_id).status is (
        ControlledReplayRestorationPermitLifecycleStatus.ISSUED
    )


def test_success_is_deterministic_from_identical_inputs() -> None:
    registry = _registry()
    fresh = _evidence(captured_episode=201)
    ledger = _activity_ledger()
    runtime = _runtime()
    request = _request(registry, fresh)

    first = _execute(
        registry=registry,
        fresh=fresh,
        ledger=ledger,
        runtime=runtime,
        request=request,
    )
    second = _execute(
        registry=registry,
        fresh=fresh,
        ledger=ledger,
        runtime=runtime,
        request=request,
    )

    assert first.receipt == second.receipt
    assert first.lifecycle_registry.snapshot() == second.lifecycle_registry.snapshot()
    assert first.activity_ledger.snapshot() == second.activity_ledger.snapshot()
    assert first.adaptive_state.to_growth_state() == second.adaptive_state.to_growth_state()
    assert str(first.receipt.snapshot()).isascii()


def test_restoration_permit_cannot_execute_retention_replay() -> None:
    registry = _registry(ControlledReplayRestorationOperation.CHECKPOINT_RESTORATION)
    fresh = _evidence(captured_episode=201)
    request = _request(registry, fresh, work_items=(_items()[0],))

    with pytest.raises(ValueError, match="cannot use a restoration permit"):
        _execute(registry=registry, fresh=fresh, request=request)


def test_replay_requires_fresh_same_episode_verified_nonfallback_evidence() -> None:
    registry = _registry()
    stale = _evidence(captured_episode=200)
    stale_request = _request(registry, stale, operation_episode=201)
    with pytest.raises(ValueError, match="captured in the operation episode"):
        _execute(registry=registry, fresh=stale, request=stale_request)

    unverified = _evidence(captured_episode=201, checksum_verified=False)
    with pytest.raises(ValueError, match="checksum-verified fresh evidence"):
        _execute(
            registry=registry,
            fresh=unverified,
            request=_request(registry, unverified),
        )

    fallback = _evidence(captured_episode=201, used_fallback=True)
    with pytest.raises(ValueError, match="fallback fresh evidence"):
        _execute(
            registry=registry,
            fresh=fallback,
            request=_request(registry, fallback),
        )


def test_checkpoint_and_source_evidence_drift_are_rejected() -> None:
    registry = _registry()
    changed_checksum = _evidence(captured_episode=201, current_checksum="c" * 64)
    with pytest.raises(ValueError, match="current checkpoint checksum drifted"):
        _execute(
            registry=registry,
            fresh=changed_checksum,
            request=_request(registry, changed_checksum),
        )

    changed_ids = _evidence(
        captured_episode=201,
        evidence_ids=tuple(sorted((*_EVIDENCE_IDS, "real:greenhouse:new"))),
    )
    with pytest.raises(ValueError, match="source evidence identities drifted"):
        _execute(
            registry=registry,
            fresh=changed_ids,
            request=_request(registry, changed_ids),
        )


def test_request_must_match_every_permit_and_fresh_evidence_identity() -> None:
    registry = _registry()
    fresh = _evidence(captured_episode=201)
    request = _request(registry, fresh)
    cases = (
        (
            replace(request, target_permit_id="permit:wrong"),
            "permit identity is not present",
        ),
        (replace(request, expected_target_id="replay-target:wrong"), "replay target"),
        (
            replace(request, expected_source_checkpoint_id="checkpoint:wrong"),
            "source checkpoint",
        ),
        (
            replace(request, expected_source_checkpoint_checksum="c" * 64),
            "source checkpoint checksum",
        ),
        (
            replace(request, expected_current_checkpoint_id="checkpoint:wrong"),
            "current checkpoint",
        ),
        (
            replace(request, expected_current_checkpoint_checksum="c" * 64),
            "current checkpoint checksum",
        ),
        (
            replace(request, expected_fresh_evidence_state_id="evidence:wrong"),
            "different fresh evidence",
        ),
    )
    for changed, message in cases:
        with pytest.raises(ValueError, match=message):
            _execute(registry=registry, fresh=fresh, request=changed)


def test_cancelled_consumed_and_expired_permits_cannot_run() -> None:
    for action, episode, actor, reference in (
        (
            ControlledReplayRestorationPermitLifecycleAction.CANCEL,
            201,
            "human:operator",
            None,
        ),
        (
            ControlledReplayRestorationPermitLifecycleAction.CONSUME,
            201,
            "operation:retention_replay",
            "retention-replay-receipt:already-used",
        ),
        (
            ControlledReplayRestorationPermitLifecycleAction.EXPIRE,
            202,
            "caller:episode-boundary",
            None,
        ),
    ):
        issued = _registry()
        permit = issued.records[0].permit
        target = permit.target
        terminal = issued.transition(
            ControlledReplayRestorationPermitTransitionRequest(
                target_permit_id=permit.permit_id,
                expected_operation=target.operation,
                expected_target_id=target.target_id,
                expected_source_checkpoint_id=target.source_checkpoint_id,
                expected_source_checkpoint_checksum=target.source_checkpoint_checksum,
                expected_current_checkpoint_id=target.expected_current_checkpoint_id,
                expected_current_checkpoint_checksum=target.expected_current_checkpoint_checksum,
                expected_evidence_state_id=permit.evidence.evidence_state_id,
                action=action,
                decision_episode=episode,
                actor_code=actor,
                reason_code="terminal_test",
                consumption_reference_code=reference,
            )
        )
        fresh = _evidence(captured_episode=201)
        with pytest.raises(ValueError, match="issued unused permit"):
            _execute(
                registry=terminal,
                fresh=fresh,
                request=_request(terminal, fresh),
            )


def test_work_items_are_explicit_unique_sorted_and_bounded() -> None:
    fan, window = _items()
    with pytest.raises(ValueError, match="stable sorted ordering"):
        replace(
            _request(_registry(), _evidence(captured_episode=201)),
            work_items=(window, fan),
        )
    with pytest.raises(ValueError, match="identities must be unique"):
        replace(
            _request(_registry(), _evidence(captured_episode=201)),
            work_items=(fan, fan),
        )
    with pytest.raises(ValueError, match="source evidence identities must be unique"):
        replace(
            _request(_registry(), _evidence(captured_episode=201)),
            work_items=(fan, replace(window, source_evidence_id=_FAN_EVENT)),
        )

    registry = _registry(maximum_work_items=1)
    fresh = _evidence(captured_episode=201)
    with pytest.raises(ValueError, match="work-item bound exceeded"):
        _execute(registry=registry, fresh=fresh, request=_request(registry, fresh))


def test_work_items_must_use_approved_exact_real_activity() -> None:
    registry = _registry()
    fresh = _evidence(captured_episode=201)
    fan, window = _items()

    unapproved = replace(fan, source_evidence_id="real:greenhouse:unapproved")
    with pytest.raises(ValueError, match="unapproved source evidence"):
        _execute(
            registry=registry,
            fresh=fresh,
            request=_request(registry, fresh, work_items=(unapproved, window)),
        )

    mismatched = replace(fan, structure_ids=(_FAN_ASSEMBLY,))
    with pytest.raises(ValueError, match="exactly reconstruct source structures"):
        _execute(
            registry=registry,
            fresh=fresh,
            request=_request(registry, fresh, work_items=(mismatched, window)),
        )

    missing_ledger = ActivityMaintenanceLedger()
    with pytest.raises(ValueError, match="unknown activity event identity"):
        _execute(
            registry=registry,
            fresh=fresh,
            ledger=missing_ledger,
            request=_request(registry, fresh, work_items=(fan,)),
        )


def test_midoperation_failure_preserves_exact_original_state() -> None:
    registry = _registry()
    fresh = _evidence(captured_episode=201)
    unknown_structures = tuple(sorted((_FAN_ASSEMBLY, "assembly:missing")))
    ledger = _activity_ledger(fan_structures=unknown_structures)
    runtime = _runtime(include_fan=True)
    fan, window = _items()
    changed_fan = replace(fan, structure_ids=unknown_structures)
    request = _request(registry, fresh, work_items=(changed_fan, window))
    registry_before = registry.snapshot()
    ledger_before = ledger.snapshot()
    state_before = runtime.to_growth_state()
    graph_before = runtime.graph.snapshot()

    with pytest.raises(ValueError, match="unknown structures"):
        _execute(
            registry=registry,
            fresh=fresh,
            ledger=ledger,
            runtime=runtime,
            request=request,
        )

    assert registry.snapshot() == registry_before
    assert ledger.snapshot() == ledger_before
    assert runtime.to_growth_state() == state_before
    assert runtime.graph.snapshot() == graph_before


def test_denied_replay_preserves_exact_original_state() -> None:
    registry = _registry()
    fresh = _evidence(captured_episode=201)
    ledger = _activity_ledger(fan_harmful=True)
    runtime = _runtime()
    request = _request(registry, fresh)
    before = (registry.snapshot(), ledger.snapshot(), runtime.to_growth_state())

    with pytest.raises(ValueError, match="harmful_pathway_not_maintained"):
        _execute(
            registry=registry,
            fresh=fresh,
            ledger=ledger,
            runtime=runtime,
            request=request,
        )

    assert (registry.snapshot(), ledger.snapshot(), runtime.to_growth_state()) == before


def test_receipt_identity_and_authority_contracts_are_enforced() -> None:
    result = _execute()
    receipt = result.receipt
    with pytest.raises(ValueError, match="identity is inconsistent"):
        replace(receipt, receipt_id="retention-replay-receipt:tampered")
    with pytest.raises(ValueError, match="cannot change factual confidence"):
        replace(receipt, factual_confidence_delta=0.1)
    with pytest.raises(ValueError, match="cannot change mastery"):
        replace(receipt, mastery_delta=0.1)
    with pytest.raises(ValueError, match="cannot update learning evidence"):
        replace(receipt, has_learning_authority=True)
    with pytest.raises(ValueError, match="cannot select actions"):
        replace(receipt, has_action_selection_authority=True)
    with pytest.raises(ValueError, match="cannot control production actions"):
        replace(receipt, has_production_action_authority=True)

    item = receipt.items[0]
    with pytest.raises(ValueError, match="cannot update learning evidence"):
        replace(item, has_learning_authority=True)

    rebuilt = ControlledRetentionReplayReceipt(
        receipt_id=receipt.receipt_id,
        permit_id=receipt.permit_id,
        target_id=receipt.target_id,
        fresh_evidence_state_id=receipt.fresh_evidence_state_id,
        operation_episode=receipt.operation_episode,
        actor_code=receipt.actor_code,
        reason_code=receipt.reason_code,
        items=receipt.items,
    )
    assert rebuilt == receipt


def test_replay_module_has_no_persistence_timer_sql_integration_or_action_execution() -> None:
    source = (
        Path("src/seedmind/research/ndnra/controlled_retention_replay.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "seedmind.integration" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert ".step(" not in source
    assert ".compose(" not in source
    assert "pressure.update" not in source
    assert "grow_specialist" not in source
    assert "learn_experience" not in source
    assert "learn_contextual_experience" not in source
