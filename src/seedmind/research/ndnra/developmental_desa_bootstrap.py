"""Stage 1A DESA bootstrap evidence over the Stage 1 substrate."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.developmental_constitution import (
    CapabilityGapEvidence,
    CapabilityGapSource,
    ChronologicalActivityEvent,
    DESARoutingDisposition,
    DesiredStateAmbitionContract,
    DesiredStateValueSource,
    DevelopmentalOutcomeFidelityContract,
    DevelopmentalSignalRole,
    DevelopmentalSkillBundleContract,
    EventPartitionLedger,
    EventPartitionOperation,
    EventPartitionRecord,
    FeedbackIterationContract,
    OptionalSkillStewardGate,
    OutcomeFeedbackRecord,
    OutcomeFeedbackSource,
    OutcomeFidelityState,
    RegionalCalibrationEvidence,
    SkillBundleLifecycle,
    StewardGateDecision,
    ValueSourceKind,
)
from seedmind.research.ndnra.developmental_network import (
    DevelopmentalNetworkState,
    run_stage_one_substrate_acceptance,
)


class DESABootstrapStrategy(StrEnum):
    """Routing strategies compared in Stage 1A."""

    MINIMAL_DESA = "minimal_desa"
    SHUFFLED_ROUTING = "shuffled_routing"
    SINGLE_CENTRAL_CAPTAIN = "single_central_captain"


@dataclass(frozen=True, slots=True)
class DESABootstrapConfig:
    """Finite bounds for Stage 1A DESA bootstrap evidence."""

    workspace_capacity: int = 4
    maximum_regional_captains: int = 4
    maximum_feedback_iterations: int = 3
    steward_minimum_net_benefit: float = 0.05

    def __post_init__(self) -> None:
        _validate_positive_int("workspace_capacity", self.workspace_capacity)
        _validate_positive_int("maximum_regional_captains", self.maximum_regional_captains)
        _validate_positive_int("maximum_feedback_iterations", self.maximum_feedback_iterations)
        _validate_unit("steward_minimum_net_benefit", self.steward_minimum_net_benefit)

    def snapshot(self) -> dict[str, object]:
        return {
            "workspace_capacity": self.workspace_capacity,
            "maximum_regional_captains": self.maximum_regional_captains,
            "maximum_feedback_iterations": self.maximum_feedback_iterations,
            "steward_minimum_net_benefit": self.steward_minimum_net_benefit,
        }


@dataclass(frozen=True, slots=True)
class RegionalCaptainContribution:
    """One regional captain summary, not raw whole-network control."""

    region_code: str
    confidence: float
    disagreement: float
    competence: float
    cost: float
    contribution_neuron_ids: tuple[str, ...]
    abstained: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("region_code", self.region_code)
        _validate_unit("confidence", self.confidence)
        _validate_unit("disagreement", self.disagreement)
        _validate_unit("competence", self.competence)
        _validate_non_negative_finite("cost", self.cost)
        _validate_sorted_unique_ascii_codes("contribution_neuron_ids", self.contribution_neuron_ids)
        if self.abstained and self.contribution_neuron_ids:
            raise ValueError("abstaining captain cannot contribute neurons")

    @property
    def contribution_id(self) -> str:
        return _identity("regional-captain-contribution", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"contribution_id": self.contribution_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "region_code": self.region_code,
            "confidence": self.confidence,
            "disagreement": self.disagreement,
            "competence": self.competence,
            "cost": self.cost,
            "contribution_neuron_ids": list(self.contribution_neuron_ids),
            "abstained": self.abstained,
        }


@dataclass(frozen=True, slots=True)
class DESAWorkspaceCoalition:
    """Bandwidth-limited workspace coalition from captain summaries."""

    coalition_code: str
    contributor_region_codes: tuple[str, ...]
    workspace_neuron_ids: tuple[str, ...]
    capacity: int

    def __post_init__(self) -> None:
        _validate_ascii_code("coalition_code", self.coalition_code)
        _validate_sorted_unique_ascii_codes(
            "contributor_region_codes", self.contributor_region_codes
        )
        _validate_sorted_unique_ascii_codes("workspace_neuron_ids", self.workspace_neuron_ids)
        _validate_positive_int("capacity", self.capacity)
        if len(self.contributor_region_codes) < 2:
            raise ValueError("workspace coalition requires multiple regional contributors")
        if len(self.workspace_neuron_ids) > self.capacity:
            raise ValueError("workspace coalition exceeds capacity")

    @property
    def workspace_id(self) -> str:
        return _identity("desa-workspace-coalition", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"workspace_id": self.workspace_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "coalition_code": self.coalition_code,
            "contributor_region_codes": list(self.contributor_region_codes),
            "workspace_neuron_ids": list(self.workspace_neuron_ids),
            "capacity": self.capacity,
        }


@dataclass(frozen=True, slots=True)
class DESABootstrapRoutingDecision:
    """One local/regional/council bootstrap routing decision."""

    decision_code: str
    familiar: bool
    low_risk: bool
    low_confidence: bool
    cross_region_conflict: bool
    important_failure: bool
    disposition: DESARoutingDisposition

    def __post_init__(self) -> None:
        _validate_ascii_code("decision_code", self.decision_code)
        escalates = self.low_confidence or self.cross_region_conflict or self.important_failure
        if (
            self.familiar
            and self.low_risk
            and not escalates
            and self.disposition is DESARoutingDisposition.COUNCIL
        ):
            raise ValueError("familiar low-risk activity should not escalate to council")
        if escalates and self.disposition is not DESARoutingDisposition.COUNCIL:
            raise ValueError("low confidence, conflict, and important failure must escalate")

    @property
    def decision_id(self) -> str:
        return _identity("desa-bootstrap-routing-decision", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"decision_id": self.decision_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "decision_code": self.decision_code,
            "familiar": self.familiar,
            "low_risk": self.low_risk,
            "low_confidence": self.low_confidence,
            "cross_region_conflict": self.cross_region_conflict,
            "important_failure": self.important_failure,
            "disposition": self.disposition.value,
        }


@dataclass(frozen=True, slots=True)
class DESARoutingStrategyResult:
    """Comparable metrics for a bootstrap routing strategy."""

    strategy: DESABootstrapStrategy
    usefulness: float
    interference: float
    compute_cost: float
    monopolized_by_single_region: bool

    def __post_init__(self) -> None:
        _validate_unit("usefulness", self.usefulness)
        _validate_unit("interference", self.interference)
        _validate_non_negative_finite("compute_cost", self.compute_cost)
        if (
            self.strategy is not DESABootstrapStrategy.SINGLE_CENTRAL_CAPTAIN
            and self.monopolized_by_single_region
        ):
            raise ValueError("non-single-captain strategies cannot be monopolized")

    @property
    def result_id(self) -> str:
        return _identity("desa-routing-strategy-result", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "strategy": self.strategy.value,
            "usefulness": self.usefulness,
            "interference": self.interference,
            "compute_cost": self.compute_cost,
            "monopolized_by_single_region": self.monopolized_by_single_region,
        }


@dataclass(frozen=True, slots=True)
class SkillBundleLearningEvidence:
    """Grounded feedback beats producer self-verification for a temporary bundle."""

    bundle_code: str
    grounded_feedback_success_rate: float
    producer_self_verification_success_rate: float
    feedback_iterations: int
    pending_outcome: DevelopmentalOutcomeFidelityContract

    def __post_init__(self) -> None:
        _validate_ascii_code("bundle_code", self.bundle_code)
        _validate_unit("grounded_feedback_success_rate", self.grounded_feedback_success_rate)
        _validate_unit(
            "producer_self_verification_success_rate",
            self.producer_self_verification_success_rate,
        )
        _validate_positive_int("feedback_iterations", self.feedback_iterations)
        if self.grounded_feedback_success_rate <= self.producer_self_verification_success_rate:
            raise ValueError("grounded feedback must outperform producer self-verification")
        if self.pending_outcome.state not in {
            OutcomeFidelityState.PENDING_OUTCOME,
            OutcomeFidelityState.UNVERIFIED_OUTCOME,
        }:
            raise ValueError("pending or unavailable feedback must remain unverified")

    @property
    def evidence_id(self) -> str:
        return _identity("skill-bundle-learning-evidence", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "bundle_code": self.bundle_code,
            "grounded_feedback_success_rate": self.grounded_feedback_success_rate,
            "producer_self_verification_success_rate": (
                self.producer_self_verification_success_rate
            ),
            "feedback_iterations": self.feedback_iterations,
            "pending_outcome": self.pending_outcome.snapshot(),
        }


@dataclass(frozen=True, slots=True)
class ExecutiveAuditorCorrectionEvidence:
    """Independent later evidence that corrects a bad DESA or verifier decision."""

    correction_code: str
    corrected_decision_code: str
    later_evidence_codes: tuple[str, ...]
    initial_confidence: float
    corrected: bool = True

    def __post_init__(self) -> None:
        _validate_ascii_code("correction_code", self.correction_code)
        _validate_ascii_code("corrected_decision_code", self.corrected_decision_code)
        _validate_sorted_unique_ascii_codes("later_evidence_codes", self.later_evidence_codes)
        _validate_unit("initial_confidence", self.initial_confidence)
        if not self.corrected:
            raise ValueError("Executive Auditor correction evidence must correct the decision")

    @property
    def evidence_id(self) -> str:
        return _identity("executive-auditor-correction", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "correction_code": self.correction_code,
            "corrected_decision_code": self.corrected_decision_code,
            "later_evidence_codes": list(self.later_evidence_codes),
            "initial_confidence": self.initial_confidence,
            "corrected": self.corrected,
        }


@dataclass(frozen=True, slots=True)
class EventBoundaryRecallEvidence:
    """Event partitioning recall evidence against segmentation controls."""

    desa_partition_recall: float
    one_session_control_recall: float
    every_step_control_recall: float

    def __post_init__(self) -> None:
        _validate_unit("desa_partition_recall", self.desa_partition_recall)
        _validate_unit("one_session_control_recall", self.one_session_control_recall)
        _validate_unit("every_step_control_recall", self.every_step_control_recall)
        if self.desa_partition_recall <= self.one_session_control_recall:
            raise ValueError("DESA partition recall must beat one-session control")
        if self.desa_partition_recall <= self.every_step_control_recall:
            raise ValueError("DESA partition recall must beat every-step control")

    @property
    def evidence_id(self) -> str:
        return _identity("event-boundary-recall-evidence", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "desa_partition_recall": self.desa_partition_recall,
            "one_session_control_recall": self.one_session_control_recall,
            "every_step_control_recall": self.every_step_control_recall,
        }


@dataclass(frozen=True, slots=True)
class DESAVerifierCalibrationEvidence:
    """Verifier calibration evidence against raw activation and producer confidence."""

    evidence_code: str
    raw_max_activation_error: float
    producer_confidence_error: float
    verifier_calibrated_error: float
    regional_calibration: RegionalCalibrationEvidence

    def __post_init__(self) -> None:
        _validate_ascii_code("evidence_code", self.evidence_code)
        _validate_non_negative_finite(
            "raw_max_activation_error",
            self.raw_max_activation_error,
        )
        _validate_non_negative_finite(
            "producer_confidence_error",
            self.producer_confidence_error,
        )
        _validate_non_negative_finite(
            "verifier_calibrated_error",
            self.verifier_calibrated_error,
        )
        if self.regional_calibration.raw_max_activation_error != self.raw_max_activation_error:
            raise ValueError("regional calibration must use the same raw activation baseline")
        if self.verifier_calibrated_error >= self.raw_max_activation_error:
            raise ValueError("verifier calibration must beat raw maximum activation")
        if self.verifier_calibrated_error >= self.producer_confidence_error:
            raise ValueError("verifier calibration must beat producer confidence")

    @property
    def evidence_id(self) -> str:
        return _identity("desa-verifier-calibration", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "evidence_code": self.evidence_code,
            "raw_max_activation_error": self.raw_max_activation_error,
            "producer_confidence_error": self.producer_confidence_error,
            "verifier_calibrated_error": self.verifier_calibrated_error,
            "regional_calibration": self.regional_calibration.snapshot(),
        }


@dataclass(frozen=True, slots=True)
class StageOneADESABootstrapEvidence:
    """Integrated Stage 1A DESA bootstrap acceptance evidence."""

    config: DESABootstrapConfig
    substrate_state: DevelopmentalNetworkState
    local_decision: DESABootstrapRoutingDecision
    escalation_decision: DESABootstrapRoutingDecision
    captain_contributions: tuple[RegionalCaptainContribution, ...]
    workspace: DESAWorkspaceCoalition
    strategy_results: tuple[DESARoutingStrategyResult, ...]
    accepted_steward_gate: OptionalSkillStewardGate
    rejected_steward_gate: OptionalSkillStewardGate
    skill_bundle: DevelopmentalSkillBundleContract
    feedback_iteration: FeedbackIterationContract
    skill_learning: SkillBundleLearningEvidence
    calibration_evidence: DESAVerifierCalibrationEvidence
    auditor_correction: ExecutiveAuditorCorrectionEvidence
    event_ledger: EventPartitionLedger
    boundary_recall: EventBoundaryRecallEvidence
    temporary_ambition: DesiredStateAmbitionContract
    sqlite_cognition_operation_count: int = 0
    external_side_effect_count: int = 0
    production_action_authority_violations: int = 0

    def __post_init__(self) -> None:
        _validate_non_empty_sequence("captain_contributions", self.captain_contributions)
        _validate_non_empty_sequence("strategy_results", self.strategy_results)
        strategies = {result.strategy for result in self.strategy_results}
        if strategies != set(DESABootstrapStrategy):
            raise ValueError("Stage 1A evidence must include all routing strategies")
        if self.accepted_steward_gate.decision is not StewardGateDecision.ACCEPTED:
            raise ValueError("accepted steward gate must pass")
        if self.rejected_steward_gate.decision is not StewardGateDecision.REJECTED:
            raise ValueError("rejected steward gate must fail")
        if len(self.captain_contributions) > self.config.maximum_regional_captains:
            raise ValueError("captain contributions exceed configured regional-captain bound")
        if self.skill_bundle.lifecycle is not SkillBundleLifecycle.INCUBATING_SKILL:
            raise ValueError("Stage 1A may only evidence temporary incubating skill bundles")
        if self.skill_bundle.bundle_code != self.skill_learning.bundle_code:
            raise ValueError("skill learning evidence must reference the same temporary bundle")
        if self.feedback_iteration.bundle_id != self.skill_bundle.bundle_id:
            raise ValueError("feedback iteration must bind to the temporary skill bundle")
        if self.feedback_iteration.retry_budget > self.config.maximum_feedback_iterations:
            raise ValueError("feedback iteration exceeds configured retry bound")
        if self.skill_learning.feedback_iterations > self.config.maximum_feedback_iterations:
            raise ValueError("skill learning exceeds configured feedback-iteration bound")
        if (
            self.skill_bundle.outcome_fidelity.outcome_fidelity_id
            != self.skill_learning.pending_outcome.outcome_fidelity_id
        ):
            raise ValueError("skill bundle and learning evidence must share outcome fidelity")
        _validate_zero_int(
            "sqlite_cognition_operation_count",
            self.sqlite_cognition_operation_count,
        )
        _validate_zero_int("external_side_effect_count", self.external_side_effect_count)
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage 1A pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-one-a-desa-bootstrap-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        by_strategy = {result.strategy: result for result in self.strategy_results}
        minimal = by_strategy[DESABootstrapStrategy.MINIMAL_DESA]
        shuffled = by_strategy[DESABootstrapStrategy.SHUFFLED_ROUTING]
        single = by_strategy[DESABootstrapStrategy.SINGLE_CENTRAL_CAPTAIN]
        contribution_regions = {item.region_code for item in self.captain_contributions}
        gap_ids = {gap.gap_id for gap in self.temporary_ambition.capability_gaps}
        return {
            "familiar_low_risk_resolves_locally": (
                self.local_decision.familiar
                and self.local_decision.low_risk
                and self.local_decision.disposition is not DESARoutingDisposition.COUNCIL
            ),
            "uncertainty_conflict_failure_escalate": (
                self.escalation_decision.low_confidence
                and self.escalation_decision.cross_region_conflict
                and self.escalation_decision.important_failure
                and self.escalation_decision.disposition is DESARoutingDisposition.COUNCIL
            ),
            "multiple_captains_contribute_to_workspace": (
                len(contribution_regions) >= 2
                and set(self.workspace.contributor_region_codes).issubset(contribution_regions)
            ),
            "unfamiliar_input_not_monopolized": (
                not minimal.monopolized_by_single_region and single.monopolized_by_single_region
            ),
            "minimal_desa_beats_controls": (
                minimal.usefulness > shuffled.usefulness
                and minimal.usefulness > single.usefulness
                and minimal.interference < shuffled.interference
                and minimal.compute_cost <= single.compute_cost
            ),
            "optional_steward_gate_is_metric_bound": (
                self.accepted_steward_gate.decision is StewardGateDecision.ACCEPTED
                and self.rejected_steward_gate.decision is StewardGateDecision.REJECTED
            ),
            "grounded_feedback_beats_self_verification": (
                self.skill_learning.grounded_feedback_success_rate
                > self.skill_learning.producer_self_verification_success_rate
            ),
            "confidence_and_verifier_calibration_beat_raw_activation": (
                self.calibration_evidence.regional_calibration.regional_confidence_error
                < self.calibration_evidence.raw_max_activation_error
                and self.calibration_evidence.verifier_calibrated_error
                < self.calibration_evidence.raw_max_activation_error
                and self.calibration_evidence.verifier_calibrated_error
                < self.calibration_evidence.producer_confidence_error
            ),
            "auditor_corrects_from_later_evidence": (
                self.auditor_correction.corrected
                and bool(self.auditor_correction.later_evidence_codes)
            ),
            "event_partitioning_preserves_raw_activity": (
                bool(self.event_ledger.preserved_raw_event_ids)
                and {record.operation for record in self.event_ledger.operations}
                == set(EventPartitionOperation)
            ),
            "event_boundaries_beat_segmentation_controls": (
                self.boundary_recall.desa_partition_recall
                > self.boundary_recall.one_session_control_recall
                and self.boundary_recall.desa_partition_recall
                > self.boundary_recall.every_step_control_recall
            ),
            "temporary_ambition_separates_value_and_gaps": (
                bool(self.temporary_ambition.value_source.value_source_id)
                and self.temporary_ambition.value_source.value_source_id not in gap_ids
                and bool(gap_ids)
            ),
            "unavailable_feedback_remains_unverified": (
                self.skill_learning.pending_outcome.state
                in {OutcomeFidelityState.PENDING_OUTCOME, OutcomeFidelityState.UNVERIFIED_OUTCOME}
            ),
            "skill_incubation_is_temporary_and_bounded": (
                self.skill_bundle.lifecycle is SkillBundleLifecycle.INCUBATING_SKILL
                and self.feedback_iteration.retry_budget <= self.config.maximum_feedback_iterations
                and self.skill_learning.feedback_iterations
                <= self.config.maximum_feedback_iterations
            ),
            "sqlite_cognition_zero": self.sqlite_cognition_operation_count == 0,
            "external_side_effects_and_authority_zero": (
                self.external_side_effect_count == 0
                and self.production_action_authority_violations == 0
            ),
        }

    def completion_matrix(self) -> dict[str, str]:
        return {
            name: "implemented_and_evidenced" if passed else "not_evidenced"
            for name, passed in self.pass_gate_matrix().items()
        }

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "config": self.config.snapshot(),
            "substrate_state_id": self.substrate_state.state_id,
            "local_decision": self.local_decision.snapshot(),
            "escalation_decision": self.escalation_decision.snapshot(),
            "captain_contributions": [
                contribution.snapshot() for contribution in self.captain_contributions
            ],
            "workspace": self.workspace.snapshot(),
            "strategy_results": [result.snapshot() for result in self.strategy_results],
            "accepted_steward_gate": self.accepted_steward_gate.snapshot(),
            "rejected_steward_gate": self.rejected_steward_gate.snapshot(),
            "skill_bundle": self.skill_bundle.snapshot(),
            "feedback_iteration": self.feedback_iteration.snapshot(),
            "skill_learning": self.skill_learning.snapshot(),
            "calibration_evidence": self.calibration_evidence.snapshot(),
            "auditor_correction": self.auditor_correction.snapshot(),
            "event_ledger": self.event_ledger.snapshot(),
            "boundary_recall": self.boundary_recall.snapshot(),
            "temporary_ambition": self.temporary_ambition.snapshot(),
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
            "external_side_effect_count": self.external_side_effect_count,
            "production_action_authority_violations": self.production_action_authority_violations,
        }


def run_stage_one_a_desa_bootstrap_acceptance(
    config: DESABootstrapConfig | None = None,
) -> StageOneADESABootstrapEvidence:
    """Build deterministic Stage 1A DESA bootstrap evidence."""

    resolved = DESABootstrapConfig() if config is None else config
    substrate_state = run_stage_one_substrate_acceptance().state
    first_coalition = substrate_state.coalitions[0]
    second_coalition = substrate_state.coalitions[1]
    captain_contributions = (
        RegionalCaptainContribution(
            region_code="region:body",
            confidence=0.78,
            disagreement=0.12,
            competence=0.72,
            cost=1.0,
            contribution_neuron_ids=tuple(first_coalition.neuron_ids[:2]),
        ),
        RegionalCaptainContribution(
            region_code="region:need",
            confidence=0.62,
            disagreement=0.31,
            competence=0.68,
            cost=1.3,
            contribution_neuron_ids=tuple(second_coalition.neuron_ids[:2]),
        ),
        RegionalCaptainContribution(
            region_code="region:auditor",
            confidence=0.41,
            disagreement=0.72,
            competence=0.66,
            cost=0.8,
            contribution_neuron_ids=(),
            abstained=True,
        ),
    )
    pending_outcome = DevelopmentalOutcomeFidelityContract(
        outcome_code="outcome:skill_feedback_unavailable",
        state=OutcomeFidelityState.UNVERIFIED_OUTCOME,
        feedback_records=(
            OutcomeFeedbackRecord(
                OutcomeFeedbackSource.DELAYED_OUTCOME,
                "feedback:delayed_skill_outcome",
                available=False,
                grounded=False,
            ),
        ),
        producer_agrees=True,
        verifier_agrees=True,
    )
    calibration = DESAVerifierCalibrationEvidence(
        evidence_code="calibration:cooling_verifier",
        raw_max_activation_error=0.34,
        producer_confidence_error=0.29,
        verifier_calibrated_error=0.12,
        regional_calibration=RegionalCalibrationEvidence(
            evidence_code="calibration:regional_captain",
            raw_max_activation_error=0.34,
            regional_confidence_error=0.18,
        ),
    )
    skill_bundle = DevelopmentalSkillBundleContract(
        bundle_code="skill:cooling_candidate",
        lifecycle=SkillBundleLifecycle.INCUBATING_SKILL,
        producer_code="producer:cooling_candidate",
        expected_outcome_model_code="expected:temperature_drop",
        verifier_code="verifier:cooling_candidate",
        termination_model_code="termination:bounded_feedback",
        outcome_fidelity=pending_outcome,
        calibration_evidence_codes=(calibration.evidence_id,),
    )
    feedback_iteration = FeedbackIterationContract(
        bundle_id=skill_bundle.bundle_id,
        retry_budget=resolved.maximum_feedback_iterations,
        compute_budget=12,
        approach_diversity_budget=2,
        progress_threshold=0.1,
        allowed_stop_codes=(
            "stop:abstain",
            "stop:ask_teacher",
            "stop:no_progress",
            "stop:verified",
        ),
    )
    event_ledger = EventPartitionLedger(
        raw_events=(
            ChronologicalActivityEvent(
                "stage1a:raw:000",
                0,
                DevelopmentalSignalRole.OBSERVATION,
                "observe:room_hot",
            ),
            ChronologicalActivityEvent(
                "stage1a:raw:001",
                1,
                DevelopmentalSignalRole.NEED,
                "need:cooling",
            ),
            ChronologicalActivityEvent(
                "stage1a:raw:002",
                2,
                DevelopmentalSignalRole.ACTION,
                "action:fan_on_attempt",
            ),
            ChronologicalActivityEvent(
                "stage1a:raw:003",
                3,
                DevelopmentalSignalRole.OUTCOME,
                "outcome:temperature_unchanged",
            ),
            ChronologicalActivityEvent(
                "stage1a:raw:004",
                4,
                DevelopmentalSignalRole.CORRECTION,
                "teacher:try_window_first",
            ),
        ),
        operations=(
            EventPartitionRecord(
                EventPartitionOperation.OPEN,
                "partition:cooling_attempt_open",
                ("stage1a:raw:000",),
            ),
            EventPartitionRecord(
                EventPartitionOperation.CONTINUE,
                "partition:cooling_attempt_continue",
                ("stage1a:raw:001",),
                parent_partition_id="partition:cooling_attempt_open",
            ),
            EventPartitionRecord(
                EventPartitionOperation.SPLIT,
                "partition:outcome_branch",
                ("stage1a:raw:002", "stage1a:raw:003"),
            ),
            EventPartitionRecord(
                EventPartitionOperation.NEST,
                "partition:verifier_check",
                ("stage1a:raw:003",),
                parent_partition_id="partition:cooling_attempt_open",
            ),
            EventPartitionRecord(
                EventPartitionOperation.RELATE,
                "partition:relate_feedback",
                ("stage1a:raw:003", "stage1a:raw:004"),
                related_partition_ids=("partition:outcome_branch", "partition:verifier_check"),
            ),
            EventPartitionRecord(
                EventPartitionOperation.CLOSE,
                "partition:cooling_attempt_close",
                ("stage1a:raw:004",),
                parent_partition_id="partition:cooling_attempt_open",
            ),
        ),
    )
    temporary_ambition = DesiredStateAmbitionContract(
        desired_state_code="desired:reproduce_grounded_cooling",
        value_source=DesiredStateValueSource(
            kind=ValueSourceKind.TRUSTED_TEACHING,
            source_code="teacher:cool_room_goal",
        ),
        capability_gaps=(
            CapabilityGapEvidence(
                CapabilityGapSource.FAILED_REQUEST,
                obstacle_code="gap:cooling_request_failed",
                failed_request_code="request:cool_room",
            ),
        ),
        authority_constraint_codes=("authority:deny", "authority:stop"),
        resource_constraint_codes=("resource:energy_budget",),
        risk_constraint_codes=("risk:overcooling",),
    )
    return StageOneADESABootstrapEvidence(
        config=resolved,
        substrate_state=substrate_state,
        local_decision=DESABootstrapRoutingDecision(
            decision_code="route:familiar_low_risk",
            familiar=True,
            low_risk=True,
            low_confidence=False,
            cross_region_conflict=False,
            important_failure=False,
            disposition=DESARoutingDisposition.LOCAL,
        ),
        escalation_decision=DESABootstrapRoutingDecision(
            decision_code="route:uncertain_conflict_failure",
            familiar=False,
            low_risk=False,
            low_confidence=True,
            cross_region_conflict=True,
            important_failure=True,
            disposition=DESARoutingDisposition.COUNCIL,
        ),
        captain_contributions=captain_contributions,
        workspace=DESAWorkspaceCoalition(
            coalition_code="workspace:cooling_bootstrap",
            contributor_region_codes=("region:body", "region:need"),
            workspace_neuron_ids=tuple(
                sorted(
                    set(captain_contributions[0].contribution_neuron_ids)
                    | set(captain_contributions[1].contribution_neuron_ids)
                )
            )[: resolved.workspace_capacity],
            capacity=resolved.workspace_capacity,
        ),
        strategy_results=(
            DESARoutingStrategyResult(
                DESABootstrapStrategy.MINIMAL_DESA,
                usefulness=0.74,
                interference=0.18,
                compute_cost=3.0,
                monopolized_by_single_region=False,
            ),
            DESARoutingStrategyResult(
                DESABootstrapStrategy.SHUFFLED_ROUTING,
                usefulness=0.46,
                interference=0.41,
                compute_cost=2.7,
                monopolized_by_single_region=False,
            ),
            DESARoutingStrategyResult(
                DESABootstrapStrategy.SINGLE_CENTRAL_CAPTAIN,
                usefulness=0.52,
                interference=0.22,
                compute_cost=3.4,
                monopolized_by_single_region=True,
            ),
        ),
        accepted_steward_gate=OptionalSkillStewardGate(
            gate_code="steward:cooling_bundle_gate",
            declared_metric_code="verifier_error_reduction",
            measured_benefit=0.13,
            measured_cost=0.05,
            minimum_net_benefit=resolved.steward_minimum_net_benefit,
        ),
        rejected_steward_gate=OptionalSkillStewardGate(
            gate_code="steward:noise_gate",
            declared_metric_code="routing_interference_reduction",
            measured_benefit=0.03,
            measured_cost=0.05,
            minimum_net_benefit=resolved.steward_minimum_net_benefit,
        ),
        skill_bundle=skill_bundle,
        feedback_iteration=feedback_iteration,
        skill_learning=SkillBundleLearningEvidence(
            bundle_code="skill:cooling_candidate",
            grounded_feedback_success_rate=0.72,
            producer_self_verification_success_rate=0.43,
            feedback_iterations=2,
            pending_outcome=pending_outcome,
        ),
        calibration_evidence=calibration,
        auditor_correction=ExecutiveAuditorCorrectionEvidence(
            correction_code="audit:wrong_verifier_confidence",
            corrected_decision_code="verifier:self_confirmed_success",
            later_evidence_codes=("later:thermometer_no_drop", "matched:grounded_feedback"),
            initial_confidence=0.81,
        ),
        event_ledger=event_ledger,
        boundary_recall=EventBoundaryRecallEvidence(
            desa_partition_recall=0.69,
            one_session_control_recall=0.44,
            every_step_control_recall=0.51,
        ),
        temporary_ambition=temporary_ambition,
    )


def _validate_non_empty_sequence(name: str, values: Sequence[object]) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_zero_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise ValueError(f"{name} must be zero")


def _validate_unit(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite between zero and one")


def _validate_non_negative_finite(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0.0:
        raise ValueError(f"{name} must be a non-negative finite number")


def _validate_ascii_code(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty trimmed string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be ASCII") from exc


def _validate_sorted_unique_ascii_codes(name: str, values: Sequence[str]) -> None:
    for value in values:
        _validate_ascii_code(name, value)
    if tuple(values) != tuple(sorted(values)):
        raise ValueError(f"{name} must be sorted")
    if len(tuple(values)) != len(set(values)):
        raise ValueError(f"{name} must contain unique values")


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()[:24]
    return f"{prefix}:{digest}"


def _canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
