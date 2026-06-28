"""Tests for restart-safe durable controlled retention replay."""

# ruff: noqa: I001 -- pytest exposes the adjacent support module as top-level.

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from ndnra_replay_restoration_test_support import (
    WINDOW_ASSEMBLY,
    ReplayScenario,
    build_replay_scenario,
    raise_at,
)

from seedmind.research.ndnra.adaptive import NDNRARuntimeAdaptiveState
from seedmind.research.ndnra.controlled_replay_restoration_permit_lifecycle import (
    ControlledReplayRestorationPermitLifecycleStatus,
)
from seedmind.research.ndnra.controlled_retention_replay import (
    ControlledRetentionReplayOperation,
)
from seedmind.research.ndnra.controlled_retention_replay_durable import (
    ControlledRetentionReplayDurablePolicy,
    ControlledRetentionReplayDurableResult,
)
from seedmind.research.ndnra.persistence import BrainLoadStatus


def _execute(
    tmp_path: Path,
    *,
    durable_interruption_hook: Callable[[str], None] | None = None,
    persistence_interruption_hook: Callable[[str], None] | None = None,
) -> tuple[ReplayScenario, ControlledRetentionReplayDurableResult]:
    scenario = build_replay_scenario(tmp_path)
    result = ControlledRetentionReplayDurablePolicy().execute_and_save(
        request=scenario.request,
        fresh_evidence=scenario.fresh_evidence,
        replay_restoration_checkpoint=scenario.issued_checkpoint,
        store=scenario.store,
        graph=scenario.graph,
        growth_state=scenario.growth_state,
        consolidation_checkpoint=scenario.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=scenario.proposal_checkpoint,
        execution_checkpoint=scenario.execution_checkpoint,
        durable_interruption_hook=durable_interruption_hook,
        persistence_interruption_hook=persistence_interruption_hook,
    )
    return scenario, result


def test_durable_replay_round_trips_consumed_permit_receipt_and_activity(
    tmp_path: Path,
) -> None:
    scenario, result = _execute(tmp_path)

    restarted = scenario.store.load()
    record = restarted.replay_restoration_checkpoint.permit_registry.record_for(
        scenario.permit.permit_id
    )

    assert restarted.status is BrainLoadStatus.LOADED
    assert restarted.checksum_verified
    assert not restarted.used_fallback
    assert record.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED
    assert record.consumption_count == 1
    assert record.decisions[0].consumption_reference_code == result.replay_result.receipt.receipt_id
    assert restarted.replay_restoration_checkpoint.replay_receipts == (
        result.replay_result.receipt,
    )
    assert restarted.replay_restoration_checkpoint.activity_ledger.real_activity_count == 1
    assert restarted.replay_restoration_checkpoint.activity_ledger.replay_activity_count == 1
    assert restarted.growth_state == result.growth_state
    assert dict(restarted.growth_state.dormancy_levels)[WINDOW_ASSEMBLY] == pytest.approx(0.5)
    assert restarted.state_checksum != scenario.issued_save.state_checksum
    assert restarted.checksum != scenario.issued_save.checksum
    assert result.save_result is not None
    assert not result.recovered_after_interruption


def test_restart_retains_single_use_and_blocks_replay_again(tmp_path: Path) -> None:
    scenario, result = _execute(tmp_path)
    restarted = scenario.store.load()
    adaptive = NDNRARuntimeAdaptiveState.from_growth_state(
        restarted.graph,
        restarted.growth_state,
    )

    with pytest.raises(ValueError, match="issued unused permit"):
        ControlledRetentionReplayOperation().execute(
            request=scenario.request,
            fresh_evidence=scenario.fresh_evidence,
            lifecycle_registry=(restarted.replay_restoration_checkpoint.permit_registry),
            activity_ledger=restarted.replay_restoration_checkpoint.activity_ledger,
            adaptive_state=adaptive,
        )

    assert len(restarted.replay_restoration_checkpoint.replay_receipts) == 1
    assert restarted.replay_restoration_checkpoint.replay_receipts[0] == (
        result.replay_result.receipt
    )


def test_interruption_before_save_preserves_exact_old_envelope(tmp_path: Path) -> None:
    scenario = build_replay_scenario(tmp_path)
    before = scenario.store.load()

    with pytest.raises(RuntimeError, match="before_save"):
        ControlledRetentionReplayDurablePolicy().execute_and_save(
            request=scenario.request,
            fresh_evidence=scenario.fresh_evidence,
            replay_restoration_checkpoint=scenario.issued_checkpoint,
            store=scenario.store,
            graph=scenario.graph,
            growth_state=scenario.growth_state,
            consolidation_checkpoint=scenario.consolidation_checkpoint,
            proposal_lifecycle_checkpoint=scenario.proposal_checkpoint,
            execution_checkpoint=scenario.execution_checkpoint,
            durable_interruption_hook=raise_at("before_save"),
        )

    after = scenario.store.load()
    assert after.checksum == before.checksum
    assert after.state_checksum == before.state_checksum
    assert after.growth_state == before.growth_state
    assert after.replay_restoration_checkpoint == before.replay_restoration_checkpoint
    assert after.replay_restoration_checkpoint.replay_receipts == ()
    assert (
        after.replay_restoration_checkpoint.permit_registry.record_for(
            scenario.permit.permit_id
        ).status
        is ControlledReplayRestorationPermitLifecycleStatus.ISSUED
    )


def test_interruption_after_atomic_replace_recovers_complete_new_envelope(
    tmp_path: Path,
) -> None:
    scenario, result = _execute(
        tmp_path,
        persistence_interruption_hook=raise_at("after_atomic_replace"),
    )

    restarted = scenario.store.load()
    record = restarted.replay_restoration_checkpoint.permit_registry.record_for(
        scenario.permit.permit_id
    )
    assert result.recovered_after_interruption
    assert result.save_result is None
    assert record.status is ControlledReplayRestorationPermitLifecycleStatus.CONSUMED
    assert restarted.replay_restoration_checkpoint.replay_receipts == (
        result.replay_result.receipt,
    )
    assert restarted.growth_state == result.growth_state
    assert not scenario.store.temporary_path.exists()


def test_durable_replay_rejects_state_or_caller_boundary_drift(tmp_path: Path) -> None:
    scenario = build_replay_scenario(tmp_path)
    changed_growth = scenario.growth_state.__class__(
        pressure=0.9,
        eligibility=scenario.growth_state.eligibility,
        residuals=scenario.growth_state.residuals,
        attempt_count=scenario.growth_state.attempt_count,
        last_active_members=scenario.growth_state.last_active_members,
        dormancy_levels=scenario.growth_state.dormancy_levels,
    )

    with pytest.raises(ValueError, match="exact persisted brain boundaries"):
        ControlledRetentionReplayDurablePolicy().execute_and_save(
            request=scenario.request,
            fresh_evidence=scenario.fresh_evidence,
            replay_restoration_checkpoint=scenario.issued_checkpoint,
            store=scenario.store,
            graph=scenario.graph,
            growth_state=changed_growth,
            consolidation_checkpoint=scenario.consolidation_checkpoint,
            proposal_lifecycle_checkpoint=scenario.proposal_checkpoint,
            execution_checkpoint=scenario.execution_checkpoint,
        )

    restarted = scenario.store.load()
    assert restarted.checksum == scenario.issued_save.checksum
    assert restarted.replay_restoration_checkpoint.replay_receipts == ()
