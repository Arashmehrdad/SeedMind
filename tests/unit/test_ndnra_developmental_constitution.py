"""Tests for NDNRA v0.2 Stage -1 developmental constitution contracts."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    AuthorityInterruptionOutcome,
    CapabilityGapEvidence,
    CapabilityGapSource,
    CausalResponsibilityCandidate,
    CausalResponsibilityEvidenceKind,
    CausalResponsibilityStatus,
    ChronologicalActivityEvent,
    DESAHierarchyContract,
    DESARoutingDisposition,
    DESARoutingScenario,
    DesiredStateAmbitionContract,
    DesiredStateValueSource,
    DevelopmentalOutcomeFidelityContract,
    DevelopmentalSignalRole,
    DevelopmentalSkillBundleContract,
    EventPartitionLedger,
    EventPartitionOperation,
    EventPartitionRecord,
    FeedbackIterationContract,
    IntegrityManipulationAttempt,
    IntegrityManipulationKind,
    IntegrityProtectionDecision,
    IntegritySurface,
    MetacognitiveSummary,
    MetacognitiveSummaryScope,
    NurseryCurriculumKind,
    OptionalSkillStewardGate,
    OutcomeFeedbackRecord,
    OutcomeFeedbackSource,
    OutcomeFidelityState,
    ProtectedAuthorityAction,
    ProtectedAuthoritySignal,
    SkillBundleLifecycle,
    StewardGateDecision,
    ValueSourceKind,
    evaluate_integrity_attempt,
    run_stage_minus_one_acceptance,
    stage_minus_one_nursery_curriculum,
    stage_minus_one_signal_contracts,
)


def _hierarchy(**overrides: Any) -> DESAHierarchyContract:
    values: dict[str, Any] = {
        "skill_bundle_monitor_codes": ("monitor:a", "monitor:b"),
        "regional_captain_codes": ("region:a", "region:b"),
        "council_code": "desa:council",
        "executive_auditor_code": "desa:auditor",
        "constitutional_authority_code": "desa:constitution",
        "optional_steward_gate": OptionalSkillStewardGate(
            gate_code="gate:reject",
            declared_metric_code="metric:interference",
            measured_benefit=0.01,
            measured_cost=0.03,
            minimum_net_benefit=0.01,
        ),
        "shared_workspace_capacity": 3,
    }
    values.update(overrides)
    return DESAHierarchyContract(**values)


def _raw_events() -> tuple[ChronologicalActivityEvent, ...]:
    return (
        ChronologicalActivityEvent("raw:0", 0, DevelopmentalSignalRole.OBSERVATION, "observe"),
        ChronologicalActivityEvent("raw:1", 1, DevelopmentalSignalRole.ACTION, "act"),
        ChronologicalActivityEvent("raw:2", 2, DevelopmentalSignalRole.OUTCOME, "outcome"),
        ChronologicalActivityEvent("raw:3", 3, DevelopmentalSignalRole.CORRECTION, "stop"),
    )


def _operations() -> tuple[EventPartitionRecord, ...]:
    return (
        EventPartitionRecord(EventPartitionOperation.OPEN, "partition:open", ("raw:0",)),
        EventPartitionRecord(
            EventPartitionOperation.CONTINUE,
            "partition:continue",
            ("raw:1",),
            parent_partition_id="partition:open",
        ),
        EventPartitionRecord(EventPartitionOperation.SPLIT, "partition:split", ("raw:1", "raw:2")),
        EventPartitionRecord(
            EventPartitionOperation.NEST,
            "partition:nest",
            ("raw:2",),
            parent_partition_id="partition:open",
        ),
        EventPartitionRecord(
            EventPartitionOperation.RELATE,
            "partition:relate",
            ("raw:1", "raw:2"),
            related_partition_ids=("partition:nest", "partition:split"),
        ),
        EventPartitionRecord(
            EventPartitionOperation.CLOSE,
            "partition:close",
            ("raw:3",),
            parent_partition_id="partition:open",
        ),
    )


def _value_source() -> DesiredStateValueSource:
    return DesiredStateValueSource(
        kind=ValueSourceKind.NURSERY_PURPOSE,
        source_code="nursery:purpose",
    )


def _gap() -> CapabilityGapEvidence:
    return CapabilityGapEvidence(
        CapabilityGapSource.FAILED_REQUEST,
        obstacle_code="gap:request_failed",
        failed_request_code="request:cool_room",
    )


def _pending_outcome() -> DevelopmentalOutcomeFidelityContract:
    return DevelopmentalOutcomeFidelityContract(
        outcome_code="outcome:pending",
        state=OutcomeFidelityState.UNVERIFIED_OUTCOME,
        feedback_records=(
            OutcomeFeedbackRecord(
                OutcomeFeedbackSource.DELAYED_OUTCOME,
                "feedback:missing",
                available=False,
                grounded=False,
            ),
        ),
        producer_agrees=True,
        verifier_agrees=True,
    )


def _verified_outcome() -> DevelopmentalOutcomeFidelityContract:
    return DevelopmentalOutcomeFidelityContract(
        outcome_code="outcome:verified",
        state=OutcomeFidelityState.VERIFIED_OUTCOME,
        feedback_records=(
            OutcomeFeedbackRecord(
                OutcomeFeedbackSource.ENVIRONMENT_CONSEQUENCE,
                "feedback:thermometer_drop",
                available=True,
                grounded=True,
                supports_success=True,
            ),
        ),
    )


def test_stage_minus_one_acceptance_matrix_is_complete_and_non_authoritative() -> None:
    evidence = run_stage_minus_one_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.production_action_authority_violations == 0
    assert evidence.sqlite_cognition_operation_count == 0
    assert evidence.external_side_effect_count == 0
    assert evidence.snapshot_json_ascii() == evidence.snapshot_json_ascii()
    assert evidence.snapshot_json_ascii().decode("ascii")


def test_public_exports_cover_stage_minus_one_contracts() -> None:
    exported = set(ndnra.__all__)

    assert "run_stage_minus_one_acceptance" in exported
    assert "DevelopmentalSignalRole" in exported
    assert "DESAHierarchyContract" in exported
    assert "StageMinusOneAcceptanceEvidence" in exported
    assert len(stage_minus_one_signal_contracts()) == len(set(DevelopmentalSignalRole))


def test_event_partitioning_preserves_raw_chronology_and_rejects_rewrites() -> None:
    ledger = EventPartitionLedger(raw_events=_raw_events(), operations=_operations())

    assert ledger.preserved_raw_event_ids == ("raw:0", "raw:1", "raw:2", "raw:3")
    assert ledger.snapshot() == ledger.snapshot()

    rewritten = replace(_operations()[2], raw_event_ids=("raw:2", "raw:1"))
    with pytest.raises(ValueError, match="cannot reorder raw events"):
        EventPartitionLedger(
            raw_events=_raw_events(),
            operations=(_operations()[0], _operations()[1], rewritten, *_operations()[3:]),
        )

    missing_operation = tuple(
        operation
        for operation in _operations()
        if operation.operation is not EventPartitionOperation.RELATE
    )
    with pytest.raises(ValueError, match="open, continue, split, nest, relate, and close"):
        EventPartitionLedger(raw_events=_raw_events(), operations=missing_operation)


def test_desa_hierarchy_rejects_hidden_solver_fixed_bureaucracy_and_authority() -> None:
    assert _hierarchy().optional_steward_gate is not None

    invalid_flags = (
        "single_all_knowing_captain",
        "fixed_extra_steward_layer",
        "has_task_solution",
        "has_pretrained_language_model",
        "has_imported_task_knowledge",
        "has_external_action_authority",
        "uses_sqlite_cognition",
    )
    for flag in invalid_flags:
        with pytest.raises(ValueError, match=r"cannot|must"):
            _hierarchy(**{flag: True})

    with pytest.raises(ValueError, match="plural regional captains"):
        _hierarchy(regional_captain_codes=("region:a",))


def test_optional_steward_gate_is_measured_and_rejects_unjustified_layer() -> None:
    rejected = OptionalSkillStewardGate(
        "gate:reject",
        "metric:calibration",
        measured_benefit=0.02,
        measured_cost=0.05,
        minimum_net_benefit=0.01,
    )
    accepted = OptionalSkillStewardGate(
        "gate:accept",
        "metric:calibration",
        measured_benefit=0.08,
        measured_cost=0.03,
        minimum_net_benefit=0.04,
    )

    assert rejected.decision is StewardGateDecision.REJECTED
    assert accepted.decision is StewardGateDecision.ACCEPTED


def test_routing_scenarios_keep_plural_routing_and_escalation_explicit() -> None:
    DESARoutingScenario(
        "route:known",
        ("region:body",),
        DESARoutingDisposition.LOCAL,
        familiar=True,
        low_risk=True,
    )
    DESARoutingScenario(
        "route:new",
        ("region:body", "region:need"),
        DESARoutingDisposition.REGIONAL,
        familiar=False,
        low_risk=True,
    )

    with pytest.raises(ValueError, match="multiple plausible regions"):
        DESARoutingScenario(
            "route:new_bad",
            ("region:body",),
            DESARoutingDisposition.REGIONAL,
            familiar=False,
            low_risk=True,
        )
    with pytest.raises(ValueError, match="escalate"):
        DESARoutingScenario(
            "route:conflict_bad",
            ("region:body", "region:need"),
            DESARoutingDisposition.REGIONAL,
            familiar=False,
            low_risk=False,
            cross_region_conflict=True,
        )
    with pytest.raises(ValueError, match="below council"):
        DESARoutingScenario(
            "route:known_bad",
            ("region:body",),
            DESARoutingDisposition.COUNCIL,
            familiar=True,
            low_risk=True,
        )


def test_metacognitive_summaries_are_bounded_and_do_not_control_the_network() -> None:
    local = MetacognitiveSummary(
        summary_code="summary:local",
        scope=MetacognitiveSummaryScope.LOCAL,
        confidence=0.8,
        disagreement=0.1,
        competence=0.7,
        cost=1.0,
        verifier_competence=0.6,
        help_requested=False,
        abstained=False,
    )
    regional = MetacognitiveSummary(
        summary_code="summary:regional",
        scope=MetacognitiveSummaryScope.REGIONAL,
        confidence=0.3,
        disagreement=0.8,
        competence=0.4,
        cost=2.0,
        verifier_competence=0.5,
        help_requested=True,
        abstained=False,
    )

    assert local.snapshot() == local.snapshot()
    assert regional.help_requested
    with pytest.raises(ValueError, match="low confidence or high disagreement"):
        replace(regional, confidence=0.9, disagreement=0.1)
    with pytest.raises(ValueError, match="distinct summary states"):
        replace(regional, abstained=True)


def test_ambition_requires_grounded_value_source_and_separate_capability_gaps() -> None:
    ambition = DesiredStateAmbitionContract(
        desired_state_code="desired:cool_room",
        value_source=_value_source(),
        capability_gaps=(_gap(),),
        authority_constraint_codes=("authority:stop",),
        resource_constraint_codes=("resource:energy",),
        risk_constraint_codes=("risk:overcool",),
    )

    assert ambition.value_source.value_source_id != ambition.capability_gaps[0].gap_id
    assert ambition.snapshot() == ambition.snapshot()

    with pytest.raises(ValueError, match="trusted"):
        DesiredStateValueSource(
            kind=ValueSourceKind.TRUSTED_TEACHING,
            source_code="teacher:unsafe",
            trusted=False,
        )
    with pytest.raises(ValueError, match="failed_request_code"):
        CapabilityGapEvidence(
            CapabilityGapSource.FAILED_REQUEST,
            obstacle_code="gap:missing_request",
        )
    with pytest.raises(ValueError, match="production action authority"):
        DesiredStateAmbitionContract(
            desired_state_code="desired:bad",
            value_source=_value_source(),
            capability_gaps=(_gap(),),
            has_production_action_authority=True,
        )


def test_outcome_fidelity_requires_grounded_feedback_not_self_confirmation() -> None:
    pending = _pending_outcome()

    assert pending.state is OutcomeFidelityState.UNVERIFIED_OUTCOME
    assert pending.producer_agrees
    assert pending.verifier_agrees

    with pytest.raises(ValueError, match="grounded success feedback"):
        DevelopmentalOutcomeFidelityContract(
            outcome_code="outcome:self_certified",
            state=OutcomeFidelityState.VERIFIED_OUTCOME,
            feedback_records=(
                OutcomeFeedbackRecord(
                    OutcomeFeedbackSource.INDEPENDENT_VERIFIER,
                    "feedback:unavailable",
                    available=False,
                    grounded=False,
                ),
            ),
            producer_agrees=True,
            verifier_agrees=True,
        )
    with pytest.raises(ValueError, match="unavailable feedback"):
        DevelopmentalOutcomeFidelityContract(
            outcome_code="outcome:partial_without_feedback",
            state=OutcomeFidelityState.PARTIALLY_VERIFIED_OUTCOME,
            feedback_records=(
                OutcomeFeedbackRecord(
                    OutcomeFeedbackSource.DELAYED_OUTCOME,
                    "feedback:missing",
                    available=False,
                    grounded=False,
                ),
            ),
        )


def test_skill_bundle_and_iteration_boundaries_are_explicit() -> None:
    bundle = DevelopmentalSkillBundleContract(
        bundle_code="skill:fan",
        lifecycle=SkillBundleLifecycle.INCUBATING_SKILL,
        producer_code="producer:fan",
        expected_outcome_model_code="model:cooling",
        verifier_code="verifier:thermometer",
        termination_model_code="termination:cool_or_stop",
        outcome_fidelity=_verified_outcome(),
        calibration_evidence_codes=("calibration:thermometer",),
    )
    iteration = FeedbackIterationContract(
        bundle_id=bundle.bundle_id,
        retry_budget=2,
        compute_budget=4,
        approach_diversity_budget=2,
        progress_threshold=0.1,
        allowed_stop_codes=("abstain", "ask_help", "stop"),
    )

    assert iteration.bundle_id == bundle.bundle_id

    with pytest.raises(ValueError, match="producer and verifier"):
        DevelopmentalSkillBundleContract(
            bundle_code="skill:bad",
            lifecycle=SkillBundleLifecycle.INCUBATING_SKILL,
            producer_code="same",
            expected_outcome_model_code="model:bad",
            verifier_code="same",
            termination_model_code="termination:bad",
            outcome_fidelity=_verified_outcome(),
            calibration_evidence_codes=("calibration:x",),
        )
    with pytest.raises(ValueError, match="predefined domain knowledge"):
        replace(bundle, has_predefined_domain_knowledge=True)
    with pytest.raises(ValueError, match="help, teaching, and abstention"):
        replace(iteration, may_ask_for_help=False)


def test_protected_authority_is_reward_independent_and_non_mutating() -> None:
    signal = ProtectedAuthoritySignal(
        ProtectedAuthorityAction.STOP,
        authority_code="authority:stop",
    )
    outcome = AuthorityInterruptionOutcome(signal=signal)

    assert outcome.ordinary_reward_delta == 0.0
    assert not outcome.permission_reinterpreted_as_obstacle

    with pytest.raises(ValueError, match="ordinary reward"):
        ProtectedAuthoritySignal(
            ProtectedAuthorityAction.DENY,
            authority_code="authority:deny",
            reward_coupled=True,
        )
    with pytest.raises(ValueError, match="weakened"):
        replace(signal, can_be_weakened_by_learning=True)
    with pytest.raises(ValueError, match=r"anti-human|obstacle"):
        replace(outcome, permission_reinterpreted_as_obstacle=True)


def test_integrity_tampering_is_blocked_preserved_and_non_evidentiary() -> None:
    attempt = IntegrityManipulationAttempt(
        IntegrityManipulationKind.DELETE_NEGATIVE_EVIDENCE,
        IntegritySurface.EVIDENCE,
        "attempt:delete_failure",
    )
    decision = evaluate_integrity_attempt(attempt)

    assert decision.blocked
    assert decision.preserved_in_audit
    assert decision.factual_evidence_change == 0.0
    assert decision.snapshot() == decision.snapshot()

    with pytest.raises(ValueError, match="blocked"):
        IntegrityProtectionDecision(attempt, "bad:allow", blocked=False)
    with pytest.raises(ValueError, match="audit"):
        IntegrityProtectionDecision(attempt, "bad:erase", preserved_in_audit=False)


def test_causal_responsibility_cannot_promote_from_coactivation_alone() -> None:
    candidate = CausalResponsibilityCandidate(
        candidate_code="cause:candidate",
        coactivation_event_ids=("raw:1", "raw:2"),
        evidence_kinds=(CausalResponsibilityEvidenceKind.COACTIVATION,),
    )

    assert candidate.status is CausalResponsibilityStatus.CANDIDATE
    with pytest.raises(ValueError, match="co-activation alone"):
        CausalResponsibilityCandidate(
            candidate_code="cause:bad",
            coactivation_event_ids=("raw:1", "raw:2"),
            evidence_kinds=(CausalResponsibilityEvidenceKind.COACTIVATION,),
            status=CausalResponsibilityStatus.ACCEPTED,
        )

    accepted = CausalResponsibilityCandidate(
        candidate_code="cause:accepted_with_intervention",
        coactivation_event_ids=("raw:1", "raw:2"),
        evidence_kinds=(
            CausalResponsibilityEvidenceKind.COACTIVATION,
            CausalResponsibilityEvidenceKind.INTERVENTION,
        ),
        status=CausalResponsibilityStatus.ACCEPTED,
    )
    assert accepted.status is CausalResponsibilityStatus.ACCEPTED


def test_curricula_are_grounded_bounded_and_non_authoritative() -> None:
    ordinary, executive = stage_minus_one_nursery_curriculum()

    assert tuple(item.step_index for item in ordinary) == tuple(range(1, 11))
    assert tuple(item.step_index for item in executive) == tuple(range(1, 15))
    assert {item.curriculum for item in ordinary} == {NurseryCurriculumKind.ORDINARY}
    assert {item.curriculum for item in executive} == {NurseryCurriculumKind.EXECUTIVE}
    assert not any(item.has_external_action_authority for item in (*ordinary, *executive))
    assert not any(item.has_predefined_task_solution for item in (*ordinary, *executive))


def test_developmental_constitution_has_no_forbidden_runtime_dependencies() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_constitution.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))
    forbidden = {"asyncio", "concurrent", "queue", "sqlite3", "threading", "time"}
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module.split(".")[0])

    assert imports.isdisjoint(forbidden)
    assert "persistence" not in module_path.read_text(encoding="utf-8")
