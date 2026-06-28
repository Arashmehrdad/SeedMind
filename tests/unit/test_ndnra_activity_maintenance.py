"""Tests for source-separated activity and bounded dormancy maintenance."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra.activity_maintenance import (
    ActivityMaintenanceConfig,
    ActivityMaintenanceLedger,
    ActivityMaintenanceRequest,
)
from seedmind.research.ndnra.adaptive import NDNRARuntimeAdaptiveState
from seedmind.research.ndnra.composition import MultidimensionalExperienceGraph
from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin
from seedmind.research.ndnra.effects import EffectObservation
from seedmind.research.ndnra.persistence import NDNRAGrowthState

_ASSEMBLY_ID = "assembly:open_window"
_LINK_ID = "assembly:open_window->fact:airflow"
_STRUCTURES = (_ASSEMBLY_ID, _LINK_ID)


def _graph() -> MultidimensionalExperienceGraph:
    graph = MultidimensionalExperienceGraph()
    graph.learn_experience(
        assembly_id=_ASSEMBLY_ID,
        action_code="open_window",
        origin_need_code="reduce_temperature",
        required_facts=("window_available",),
        produced_facts=("airflow",),
        observed_effects=(EffectObservation("temperature", -0.4, 0.9),),
    )
    return graph


def _runtime() -> NDNRARuntimeAdaptiveState:
    return NDNRARuntimeAdaptiveState.from_growth_state(
        _graph(),
        NDNRAGrowthState(
            pressure=0.4,
            eligibility=((_ASSEMBLY_ID, 0.3),),
            residuals=(0.1,),
            attempt_count=5,
            last_active_members=(_ASSEMBLY_ID,),
            dormancy_levels=((_ASSEMBLY_ID, 0.8), (_LINK_ID, 0.8)),
        ),
    )


def _request(
    origin: ExperienceOrigin,
    *,
    event_id: str,
    cycle: int = 1,
    structures: tuple[str, ...] = _STRUCTURES,
    relevance: float = 1.0,
    helpfulness: float = 1.0,
    prediction_accuracy: float = 1.0,
    real_evidence_strength: float = 1.0,
    safety_critical: bool = False,
    rare_use: bool = False,
    harmful: bool = False,
    redundant: bool = False,
) -> ActivityMaintenanceRequest:
    return ActivityMaintenanceRequest(
        event_id=event_id,
        cycle=cycle,
        origin=origin,
        structure_ids=structures,
        supporting_real_event_ids=(
            () if origin is ExperienceOrigin.REAL else ("real:greenhouse:001",)
        ),
        relevance=relevance,
        helpfulness=helpfulness,
        prediction_accuracy=prediction_accuracy,
        real_evidence_strength=real_evidence_strength,
        safety_critical=safety_critical,
        rare_use=rare_use,
        harmful=harmful,
        redundant=redundant,
    )


def _ledger_with_real_support(
    config: ActivityMaintenanceConfig | None = None,
    *,
    structures: tuple[str, ...] = _STRUCTURES,
) -> ActivityMaintenanceLedger:
    ledger = ActivityMaintenanceLedger(ActivityMaintenanceConfig() if config is None else config)
    ledger.consider(
        _request(
            ExperienceOrigin.REAL,
            event_id="real:greenhouse:001",
            cycle=0,
            structures=structures,
        )
    )
    return ledger


def test_real_replay_and_imagined_activity_have_ordered_strengths() -> None:
    strengths = {}
    for origin in ExperienceOrigin:
        ledger = (
            ActivityMaintenanceLedger()
            if origin is ExperienceOrigin.REAL
            else _ledger_with_real_support()
        )
        decision = ledger.consider(_request(origin, event_id=f"{origin.value}:greenhouse:001"))
        strengths[origin] = decision.granted_strength
        assert decision.maintenance_applied
        assert decision.factual_confidence_delta == 0.0
        assert decision.mastery_delta == 0.0

    assert strengths[ExperienceOrigin.REAL] == pytest.approx(0.60)
    assert strengths[ExperienceOrigin.REPLAY] == pytest.approx(0.30)
    assert strengths[ExperienceOrigin.IMAGINED] == pytest.approx(0.10)
    assert (
        strengths[ExperienceOrigin.REAL]
        > strengths[ExperienceOrigin.REPLAY]
        > strengths[ExperienceOrigin.IMAGINED]
    )


def test_replay_and_imagination_require_real_support() -> None:
    replay = _request(ExperienceOrigin.REPLAY, event_id="replay:unsupported")
    imagined = _request(ExperienceOrigin.IMAGINED, event_id="imagined:unsupported")

    with pytest.raises(ValueError, match="require supporting real events"):
        replace(replay, supporting_real_event_ids=())
    with pytest.raises(ValueError, match="require supporting real events"):
        replace(imagined, supporting_real_event_ids=())

    missing_replay = ActivityMaintenanceLedger().consider(replay)
    missing_imagined = ActivityMaintenanceLedger().consider(imagined)
    assert missing_replay.reason_code == "supporting_real_activity_missing"
    assert missing_imagined.reason_code == "supporting_real_activity_missing"
    assert not missing_replay.maintenance_applied
    assert not missing_imagined.maintenance_applied

    weak_replay = replace(replay, real_evidence_strength=0.20)
    weak_imagined = replace(imagined, real_evidence_strength=0.40)
    replay_decision = _ledger_with_real_support().consider(weak_replay)
    imagined_decision = _ledger_with_real_support().consider(weak_imagined)

    assert not replay_decision.maintenance_applied
    assert replay_decision.reason_code == "insufficient_real_evidence_for_replay"
    assert not imagined_decision.maintenance_applied
    assert imagined_decision.reason_code == "insufficient_real_evidence_for_imagination"

    mismatch = _ledger_with_real_support(structures=(_ASSEMBLY_ID,)).consider(replay)
    assert mismatch.reason_code == "supporting_real_activity_structure_mismatch"
    assert not mismatch.maintenance_applied


def test_real_activity_requires_real_evidence_and_cannot_cite_other_events() -> None:
    request = _request(ExperienceOrigin.REAL, event_id="real:invalid")

    with pytest.raises(ValueError, match="non-zero real evidence"):
        replace(request, real_evidence_strength=0.0)
    with pytest.raises(ValueError, match="cannot cite separate"):
        replace(request, supporting_real_event_ids=("real:other",))


def test_harmful_redundant_and_irrelevant_pathways_remain_dormant() -> None:
    cases = (
        (
            _request(
                ExperienceOrigin.REAL,
                event_id="real:harmful",
                harmful=True,
                safety_critical=True,
                rare_use=True,
            ),
            "harmful_pathway_not_maintained",
        ),
        (
            _request(
                ExperienceOrigin.REAL,
                event_id="real:redundant",
                redundant=True,
                safety_critical=True,
            ),
            "redundant_pathway_not_maintained",
        ),
        (
            _request(
                ExperienceOrigin.REAL,
                event_id="real:irrelevant",
                relevance=0.0,
                rare_use=True,
            ),
            "irrelevant_pathway_not_maintained",
        ),
    )

    for request, reason in cases:
        decision = ActivityMaintenanceLedger().consider(request)
        assert not decision.maintenance_applied
        assert decision.granted_strength == 0.0
        assert decision.reason_code == reason


def test_safety_critical_and_rare_use_memory_receive_bounded_floors() -> None:
    safety = ActivityMaintenanceLedger().consider(
        _request(
            ExperienceOrigin.REAL,
            event_id="real:safety",
            relevance=0.1,
            helpfulness=0.01,
            prediction_accuracy=0.01,
            real_evidence_strength=0.9,
            safety_critical=True,
        )
    )
    rare = ActivityMaintenanceLedger().consider(
        _request(
            ExperienceOrigin.REAL,
            event_id="real:rare",
            relevance=0.1,
            helpfulness=0.01,
            prediction_accuracy=0.01,
            real_evidence_strength=0.9,
            rare_use=True,
        )
    )

    assert safety.granted_strength == pytest.approx(0.60 * 0.20)
    assert rare.granted_strength == pytest.approx(0.60 * 0.15)
    assert safety.granted_strength > rare.granted_strength


def test_cycle_budget_limits_total_reactivation() -> None:
    ledger = ActivityMaintenanceLedger(
        ActivityMaintenanceConfig(maximum_total_reactivation_per_cycle=0.50)
    )

    first = ledger.consider(_request(ExperienceOrigin.REAL, event_id="real:budget:1", cycle=3))
    second = ledger.consider(_request(ExperienceOrigin.REAL, event_id="real:budget:2", cycle=3))

    assert first.reason_code == "cycle_budget_limited"
    assert first.per_structure_reactivation == pytest.approx(0.25)
    assert first.total_reactivation == pytest.approx(0.50)
    assert second.reason_code == "cycle_budget_exhausted"
    assert not second.maintenance_applied
    assert ledger.snapshot()["reactivation_by_cycle"] == [
        {"cycle": 3, "amount": pytest.approx(0.50)}
    ]


def test_event_budget_and_structure_budget_are_enforced() -> None:
    event_limited = ActivityMaintenanceLedger(ActivityMaintenanceConfig(maximum_events_per_cycle=1))
    event_limited.consider(_request(ExperienceOrigin.REAL, event_id="real:event-budget:1", cycle=5))
    blocked = event_limited.consider(
        _request(ExperienceOrigin.REAL, event_id="real:event-budget:2", cycle=5)
    )
    structure_limited = ActivityMaintenanceLedger(
        ActivityMaintenanceConfig(maximum_structures_per_event=1)
    ).consider(_request(ExperienceOrigin.REAL, event_id="real:structure-budget"))

    assert blocked.reason_code == "cycle_budget_exhausted"
    assert not blocked.maintenance_applied
    assert structure_limited.reason_code == "structure_budget_exceeded"
    assert not structure_limited.maintenance_applied


def test_duplicate_activity_cannot_reduce_dormancy_twice() -> None:
    ledger = _ledger_with_real_support()
    request = _request(ExperienceOrigin.REPLAY, event_id="replay:duplicate")

    original = ledger.consider(request)
    duplicate = ledger.consider(request)

    assert original.maintenance_applied
    assert not duplicate.evidence_applied
    assert not duplicate.maintenance_applied
    assert duplicate.reason_code == "exact_duplicate_ignored"
    assert ledger.event_count == 2
    assert ledger.real_activity_count == 1
    assert ledger.replay_activity_count == 1

    with pytest.raises(ValueError, match="identity conflict"):
        ledger.consider(replace(request, helpfulness=0.5))


def test_source_counters_remain_separate_and_inspectable() -> None:
    ledger = ActivityMaintenanceLedger()
    ledger.consider(_request(ExperienceOrigin.REAL, event_id="real:greenhouse:001"))
    ledger.consider(_request(ExperienceOrigin.REPLAY, event_id="replay:count"))
    ledger.consider(_request(ExperienceOrigin.IMAGINED, event_id="imagined:count"))

    snapshot = ledger.snapshot()
    assert ledger.event_count == 3
    assert ledger.real_activity_count == 1
    assert ledger.replay_activity_count == 1
    assert ledger.imagined_activity_count == 1
    assert snapshot["real_activity_count"] == 1
    assert snapshot["replay_activity_count"] == 1
    assert snapshot["imagined_activity_count"] == 1
    assert str(snapshot).isascii()


def test_runtime_maintenance_only_reduces_dormancy() -> None:
    runtime = _runtime()
    before_graph = runtime.graph.snapshot()
    before_state = runtime.to_growth_state()
    decision = _ledger_with_real_support().consider(
        _request(ExperienceOrigin.REPLAY, event_id="replay:apply")
    )

    application = runtime.apply_activity_maintenance(decision)
    after_state = runtime.to_growth_state()

    assert tuple(item[0] for item in application.changes) == _STRUCTURES
    assert tuple(item[1] for item in application.changes) == pytest.approx((0.8, 0.8))
    assert tuple(item[2] for item in application.changes) == pytest.approx((0.5, 0.5))
    assert application.eligibility_unchanged
    assert application.pressure_unchanged
    assert application.residuals_unchanged
    assert application.last_active_members_unchanged
    assert runtime.graph.snapshot() == before_graph
    assert after_state.pressure == before_state.pressure
    assert after_state.eligibility == before_state.eligibility
    assert after_state.residuals == before_state.residuals
    assert after_state.attempt_count == before_state.attempt_count
    assert after_state.last_active_members == before_state.last_active_members
    assert after_state.dormancy_levels != before_state.dormancy_levels


def test_runtime_applies_real_more_than_replay_more_than_imagination() -> None:
    accessibility = {}
    for origin in ExperienceOrigin:
        runtime = _runtime()
        ledger = (
            ActivityMaintenanceLedger()
            if origin is ExperienceOrigin.REAL
            else _ledger_with_real_support()
        )
        decision = ledger.consider(_request(origin, event_id=f"{origin.value}:runtime"))
        runtime.apply_activity_maintenance(decision)
        accessibility[origin] = runtime.accessibility(_ASSEMBLY_ID)

    assert (
        accessibility[ExperienceOrigin.REAL]
        > accessibility[ExperienceOrigin.REPLAY]
        > accessibility[ExperienceOrigin.IMAGINED]
    )


def test_denied_or_duplicate_decision_does_not_change_runtime() -> None:
    runtime = _runtime()
    before = runtime.to_growth_state()
    ledger = ActivityMaintenanceLedger()
    harmful = ledger.consider(
        _request(
            ExperienceOrigin.REAL,
            event_id="real:no-change",
            harmful=True,
        )
    )
    duplicate = ledger.consider(
        _request(
            ExperienceOrigin.REAL,
            event_id="real:no-change",
            harmful=True,
        )
    )

    harmful_application = runtime.apply_activity_maintenance(harmful)
    duplicate_application = runtime.apply_activity_maintenance(duplicate)

    assert all(
        before_level == after_level for _, before_level, after_level in harmful_application.changes
    )
    assert all(
        before_level == after_level
        for _, before_level, after_level in duplicate_application.changes
    )
    assert runtime.to_growth_state() == before


def test_unknown_structure_is_rejected_before_any_dormancy_change() -> None:
    runtime = _runtime()
    before = runtime.to_growth_state()
    decision = ActivityMaintenanceLedger().consider(
        _request(
            ExperienceOrigin.REAL,
            event_id="real:unknown",
            structures=(_ASSEMBLY_ID, "assembly:unknown"),
        )
    )

    with pytest.raises(ValueError, match="unknown structures"):
        runtime.apply_activity_maintenance(decision)

    assert runtime.to_growth_state() == before


def test_activity_contract_rejects_confidence_mastery_and_authority_changes() -> None:
    request = _request(ExperienceOrigin.REAL, event_id="real:authority")

    with pytest.raises(ValueError, match="factual confidence"):
        replace(request, factual_confidence_delta=0.1)
    with pytest.raises(ValueError, match="change mastery"):
        replace(request, mastery_delta=0.1)
    with pytest.raises(ValueError, match="cannot select actions"):
        replace(request, has_action_selection_authority=True)
    with pytest.raises(ValueError, match="cannot control production actions"):
        replace(request, has_production_action_authority=True)


def test_activity_maintenance_has_no_execution_persistence_timer_or_sql_dependency() -> None:
    source = (
        Path("src/seedmind/research/ndnra/activity_maintenance.py")
        .read_text(encoding="utf-8")
        .lower()
    )

    assert ".step(" not in source
    assert ".compose(" not in source
    assert ".apply(" not in source
    assert "persistence" not in source
    assert "sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "import time" not in source
    assert "datetime" not in source
    assert "threading" not in source
    assert "asyncio" not in source
    assert "seedmind.integration" not in source
