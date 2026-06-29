"""Live acceptance for restart-safe human-approved NDNRA consolidation execution."""

from __future__ import annotations

import csv
import json
from dataclasses import asdict, dataclass
from pathlib import Path

from seedmind.curiosity import CuriosityConfig
from seedmind.environment import DynamicNurseryScenarioFactory
from seedmind.integration.consolidation_proposal_lifecycle_acceptance import (
    _build_live_lifecycle_request,
)
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
    BrainLoadStatus,
    ConsolidationApplicationState,
    ConsolidationExecutionApprovalPolicy,
    ConsolidationExecutionApprovalRequest,
    ConsolidationExecutionCommitReceipt,
    ConsolidationExecutionCommitRequest,
    ConsolidationExecutionDurableCommitPolicy,
    ConsolidationExecutionPermitLifecycleStatus,
    ConsolidationProposalLifecycleRegistry,
    ConsolidationProposalRevalidationStatus,
    ConsolidationProposalReviewAction,
    ConsolidationProposalReviewRequest,
    ConsolidationSchedulingContext,
    ConsolidationSchedulingPolicy,
    NDNRABrainStore,
    NDNRAConsolidationCheckpoint,
    NDNRAExecutionCheckpoint,
    NDNRAProposalLifecycleCheckpoint,
)


@dataclass(frozen=True, slots=True)
class HumanApprovedConsolidationExecutionAcceptanceResult:
    """Bounded execution, durability, and live-invariance acceptance metrics."""

    brain_schema_version: int
    explicit_human_approval_count: int
    current_precommit_revalidation_count: int
    control_application_count: int
    approved_application_count: int
    consumed_permit_count: int
    execution_receipt_count: int
    automatic_execution_count: int
    replay_trigger_count: int
    restoration_trigger_count: int
    action_authority_violation_count: int
    proposal_history_unchanged: bool
    graph_unchanged_by_execution: bool
    growth_state_unchanged_by_execution: bool
    production_actions_unchanged: bool
    prediction_errors_unchanged: bool
    developmental_signals_unchanged: bool
    advice_unchanged: bool
    route_ranking_unchanged: bool
    unrelated_graph_learning_unchanged: bool
    growth_states_equal: bool
    human_dependence_accounting_unchanged: bool
    temporary_file_remaining: bool
    sqlite_used_for_execution_acceptance: bool
    pass_gate: bool

    def __post_init__(self) -> None:
        if self.brain_schema_version < 1:
            raise ValueError("brain_schema_version must be positive")
        for name, value in (
            ("explicit_human_approval_count", self.explicit_human_approval_count),
            (
                "current_precommit_revalidation_count",
                self.current_precommit_revalidation_count,
            ),
            ("control_application_count", self.control_application_count),
            ("approved_application_count", self.approved_application_count),
            ("consumed_permit_count", self.consumed_permit_count),
            ("execution_receipt_count", self.execution_receipt_count),
            ("automatic_execution_count", self.automatic_execution_count),
            ("replay_trigger_count", self.replay_trigger_count),
            ("restoration_trigger_count", self.restoration_trigger_count),
            ("action_authority_violation_count", self.action_authority_violation_count),
        ):
            if value < 0:
                raise ValueError(f"{name} must not be negative")


@dataclass(frozen=True, slots=True)
class HumanApprovedConsolidationExecutionAcceptanceEvidence:
    """Acceptance metrics plus complete control, approved, and receipt evidence."""

    result: HumanApprovedConsolidationExecutionAcceptanceResult
    pretraining: UnifiedShadowResult
    control: UnifiedShadowResult
    approved: UnifiedShadowResult
    receipt: ConsolidationExecutionCommitReceipt
    control_brain_path: Path
    approved_brain_path: Path


def run_human_approved_consolidation_execution_acceptance(
    output_directory: Path,
    *,
    first_seed: int = 7,
    second_seed: int = 11,
    play_budget: int = 8,
) -> HumanApprovedConsolidationExecutionAcceptanceEvidence:
    """Prove one approval causes one durable application and no cognitive influence."""
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
    eligibility, request = _build_live_lifecycle_request(pretraining_shadow.graph)
    schedule = ConsolidationSchedulingPolicy(
        first_eligible_episode=100,
        minimum_interval_episodes=1,
    ).evaluate(
        ledger=pretraining_shadow.graph.contextual_memory,
        request=request,
        context=ConsolidationSchedulingContext(episode_index=100),
    )
    if schedule.proposal is None or eligibility.candidate is None:
        raise RuntimeError("execution acceptance could not create a proposal")
    proposal = schedule.proposal
    registry = (
        ConsolidationProposalLifecycleRegistry()
        .add(proposal)
        .review(
            ConsolidationProposalReviewRequest(
                proposal=proposal,
                action=ConsolidationProposalReviewAction.ACCEPT,
                decision_episode=101,
                reviewer_code="human:execution_acceptance_reviewer",
                reason_code="bounded_proposal_review_passed",
            )
        )
    )
    lifecycle = NDNRAProposalLifecycleCheckpoint(registry=registry)
    record = registry.active_records[0]
    permit = ConsolidationExecutionApprovalPolicy().evaluate(
        request=ConsolidationExecutionApprovalRequest(
            target_proposal_id=proposal.proposal_id,
            expected_candidate_id=proposal.candidate.candidate_id,
            expected_review_decision_id=record.lifecycle.decisions[-1].decision_id,
            approval_episode=102,
            expires_after_episode=103,
            approver_code="human:execution_acceptance_operator",
            reason_code="explicit_bounded_live_acceptance",
        ),
        record=record,
        ledger=pretraining_shadow.graph.contextual_memory,
        available_assembly_ids=proposal.candidate.assembly_ids,
        available_route_ids=proposal.candidate.route_ids,
    )
    issued = NDNRAExecutionCheckpoint.with_issued_permit(permit)
    state = ConsolidationApplicationState.from_identifiers(
        assembly_ids=(*proposal.candidate.assembly_ids, "assembly:execution:untouched"),
        route_ids=(*proposal.candidate.route_ids, "route:execution:untouched"),
        initial_stability=0.20,
        initial_plasticity=0.80,
    )
    consolidation = NDNRAConsolidationCheckpoint(state=state.snapshot())

    control_brain_path = output_directory / "execution_acceptance_control_brain.json"
    approved_brain_path = output_directory / "execution_acceptance_approved_brain.json"
    control_store = NDNRABrainStore(control_brain_path)
    approved_store = NDNRABrainStore(approved_brain_path)
    control_store.save(
        pretraining_shadow.graph,
        growth_state=pretraining.final_growth_state,
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=lifecycle,
    )
    approved_store.save(
        pretraining_shadow.graph,
        growth_state=pretraining.final_growth_state,
        consolidation_checkpoint=consolidation,
        proposal_lifecycle_checkpoint=lifecycle,
        execution_checkpoint=issued,
    )
    pre_execution = approved_store.load()
    application_state = pre_execution.consolidation_checkpoint.application_state()
    if application_state is None:
        raise RuntimeError("execution acceptance did not restore application state")
    graph_before_execution = pre_execution.graph.snapshot()
    growth_before_execution = pre_execution.growth_state
    durable = ConsolidationExecutionDurableCommitPolicy().execute_and_save(
        request=ConsolidationExecutionCommitRequest(
            target_permit_id=permit.permit_id,
            expected_proposal_id=proposal.proposal_id,
            expected_candidate_id=proposal.candidate.candidate_id,
            execution_episode=103,
            executor_code="execution:live_acceptance",
            reason_code="commit_explicit_human_approval",
        ),
        proposal_record=pre_execution.proposal_lifecycle_checkpoint.registry.active_records[0],
        execution_checkpoint=pre_execution.execution_checkpoint,
        ledger=pre_execution.graph.contextual_memory,
        application_state=application_state,
        available_assembly_ids=proposal.candidate.assembly_ids,
        available_route_ids=proposal.candidate.route_ids,
        store=approved_store,
        graph=pre_execution.graph,
        growth_state=pre_execution.growth_state,
        consolidation_checkpoint=pre_execution.consolidation_checkpoint,
        proposal_lifecycle_checkpoint=pre_execution.proposal_lifecycle_checkpoint,
    )
    control_load = control_store.load()
    approved_load = approved_store.load()
    proposal_history_unchanged = approved_load.proposal_lifecycle_checkpoint == lifecycle
    graph_unchanged_by_execution = approved_load.graph.snapshot() == graph_before_execution
    growth_unchanged_by_execution = approved_load.growth_state == growth_before_execution

    control_shadow = NDNRALiveShadowAdapter(
        graph=control_load.graph,
        growth_state=control_load.growth_state,
    )
    approved_shadow = NDNRALiveShadowAdapter(
        graph=approved_load.graph,
        growth_state=approved_load.growth_state,
    )
    control = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, factory),
        factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, factory),
        shadow=control_shadow,
    ).run()
    approved = UnifiedDevelopmentalShadowSession(
        _build_trainer(second_seed, factory),
        factory,
        UnifiedShadowConfig(seed=second_seed, curiosity=curiosity),
        signal_provider=_build_signal_provider(second_seed, factory),
        shadow=approved_shadow,
    ).run()

    receipt = durable.commit_result.receipt
    permit_records = approved_load.execution_checkpoint.permit_registry.records
    consumed_count = sum(
        item.status is ConsolidationExecutionPermitLifecycleStatus.CONSUMED
        for item in permit_records
    )
    current_revalidations = int(
        receipt.revalidation.status is ConsolidationProposalRevalidationStatus.CURRENT
    )
    control_errors = tuple(metric.mean_absolute_error for metric in control.metrics)
    approved_errors = tuple(metric.mean_absolute_error for metric in approved.metrics)
    advice_unchanged = tuple(
        suggestion.suggested_action for suggestion in control.suggestions
    ) == tuple(suggestion.suggested_action for suggestion in approved.suggestions)
    route_ranking_unchanged = control.suggestions == approved.suggestions
    human_dependence_unchanged = tuple(
        (
            item.help_requested,
            item.human_approval,
            item.human_correction,
            item.human_demonstration,
        )
        for item in control.records
    ) == tuple(
        (
            item.help_requested,
            item.human_approval,
            item.human_correction,
            item.human_demonstration,
        )
        for item in approved.records
    )
    authority_violations = (
        control.authority_violation_count
        + approved.authority_violation_count
        + int(receipt.has_production_action_authority)
        + int(permit.has_direct_execution_authority)
        + int(approved_load.execution_checkpoint.has_execution_authority)
        + int(approved_load.execution_checkpoint.permit_registry.has_application_authority)
    )
    actions_unchanged = control.actual_actions == approved.actual_actions
    errors_unchanged = control_errors == approved_errors
    signals_unchanged = control.signals == approved.signals
    graphs_equal = control.graph_snapshot == approved.graph_snapshot
    growth_equal = control.final_growth_state == approved.final_growth_state
    control_application_count = len(control_load.consolidation_checkpoint.active_applications)
    approved_application_count = len(approved_load.consolidation_checkpoint.active_applications)
    receipt_count = len(approved_load.execution_checkpoint.receipts)
    automatic_count = approved_load.execution_checkpoint.automatic_execution_count
    replay_count = sum(
        item.replay_trigger_count for item in approved_load.execution_checkpoint.receipts
    )
    restoration_count = sum(
        item.restoration_trigger_count for item in approved_load.execution_checkpoint.receipts
    )
    temporary_remaining = bool(
        (durable.save_result is not None and durable.save_result.temporary_file_remaining)
        or approved_store.temporary_path.exists()
    )
    pass_gate = bool(
        BRAIN_SCHEMA_VERSION == 7
        and control_load.status is BrainLoadStatus.LOADED
        and approved_load.status is BrainLoadStatus.LOADED
        and permit.approver_code.startswith("human:")
        and current_revalidations == 1
        and control_application_count == 0
        and approved_application_count == 1
        and consumed_count == 1
        and receipt_count == 1
        and automatic_count == 0
        and replay_count == 0
        and restoration_count == 0
        and authority_violations == 0
        and proposal_history_unchanged
        and graph_unchanged_by_execution
        and growth_unchanged_by_execution
        and actions_unchanged
        and errors_unchanged
        and signals_unchanged
        and advice_unchanged
        and route_ranking_unchanged
        and graphs_equal
        and growth_equal
        and human_dependence_unchanged
        and not temporary_remaining
    )
    result = HumanApprovedConsolidationExecutionAcceptanceResult(
        brain_schema_version=BRAIN_SCHEMA_VERSION,
        explicit_human_approval_count=1,
        current_precommit_revalidation_count=current_revalidations,
        control_application_count=control_application_count,
        approved_application_count=approved_application_count,
        consumed_permit_count=consumed_count,
        execution_receipt_count=receipt_count,
        automatic_execution_count=automatic_count,
        replay_trigger_count=replay_count,
        restoration_trigger_count=restoration_count,
        action_authority_violation_count=authority_violations,
        proposal_history_unchanged=proposal_history_unchanged,
        graph_unchanged_by_execution=graph_unchanged_by_execution,
        growth_state_unchanged_by_execution=growth_unchanged_by_execution,
        production_actions_unchanged=actions_unchanged,
        prediction_errors_unchanged=errors_unchanged,
        developmental_signals_unchanged=signals_unchanged,
        advice_unchanged=advice_unchanged,
        route_ranking_unchanged=route_ranking_unchanged,
        unrelated_graph_learning_unchanged=graphs_equal,
        growth_states_equal=growth_equal,
        human_dependence_accounting_unchanged=human_dependence_unchanged,
        temporary_file_remaining=temporary_remaining,
        sqlite_used_for_execution_acceptance=False,
        pass_gate=pass_gate,
    )
    return HumanApprovedConsolidationExecutionAcceptanceEvidence(
        result=result,
        pretraining=pretraining,
        control=control,
        approved=approved,
        receipt=receipt,
        control_brain_path=control_brain_path,
        approved_brain_path=approved_brain_path,
    )


def export_human_approved_consolidation_execution_acceptance(
    evidence: HumanApprovedConsolidationExecutionAcceptanceEvidence,
    output_directory: Path,
) -> tuple[Path, Path, Path]:
    """Export ASCII result, live comparison, and durable receipt evidence."""
    output_directory.mkdir(parents=True, exist_ok=True)
    report_path = output_directory / "human_approved_execution_report.json"
    timeline_path = output_directory / "human_approved_execution_timeline.csv"
    receipt_path = output_directory / "human_approved_execution_receipt.json"
    _write_ascii_json(report_path, asdict(evidence.result))
    _write_ascii_json(receipt_path, evidence.receipt.snapshot())
    with timeline_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "step_index",
                "control_action",
                "approved_action",
                "control_suggestion",
                "approved_suggestion",
                "control_prediction_error",
                "approved_prediction_error",
            )
        )
        for control_record, approved_record in zip(
            evidence.control.records,
            evidence.approved.records,
            strict=True,
        ):
            writer.writerow(
                (
                    control_record.step_index,
                    control_record.actual_action.value,
                    approved_record.actual_action.value,
                    ""
                    if control_record.suggested_action is None
                    else control_record.suggested_action.value,
                    ""
                    if approved_record.suggested_action is None
                    else approved_record.suggested_action.value,
                    control_record.prediction_error,
                    approved_record.prediction_error,
                )
            )
    return report_path, timeline_path, receipt_path


def _write_ascii_json(path: Path, payload: object) -> None:
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)
