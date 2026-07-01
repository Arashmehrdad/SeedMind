"""Non-authoritative Week 10 growth proposal records."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum


class GrowthProposalStatus(StrEnum):
    """Authority state for a Week 10 proposal."""

    PROPOSED_NOT_AUTHORISED = "proposed_not_authorised"


@dataclass(frozen=True, slots=True)
class GrowthDiagnosisSummary:
    """Prerequisite evidence included in a capacity-growth proposal."""

    task_confirmed: bool
    safe_exploration_sufficient: bool
    relevant_memory_replayed: bool
    existing_skill_attempted: bool
    strategy_variants_tested: int
    help_requested: bool
    demonstration_attempted: bool
    progress_plateau: bool
    prediction_quality: str
    inferred_limitation: str
    rejected_alternative_causes: tuple[str, ...]

    def __post_init__(self) -> None:
        if self.strategy_variants_tested <= 0:
            raise ValueError("strategy_variants_tested must be positive")
        for value in (
            self.prediction_quality,
            self.inferred_limitation,
            *self.rejected_alternative_causes,
        ):
            if not value.strip() or not value.isascii():
                raise ValueError("diagnosis text must be non-empty ASCII")

    def to_json(self) -> dict[str, object]:
        return {
            "demonstration_attempted": self.demonstration_attempted,
            "existing_skill_attempted": self.existing_skill_attempted,
            "help_requested": self.help_requested,
            "inferred_limitation": self.inferred_limitation,
            "prediction_quality": self.prediction_quality,
            "progress_plateau": self.progress_plateau,
            "rejected_alternative_causes": list(self.rejected_alternative_causes),
            "relevant_memory_replayed": self.relevant_memory_replayed,
            "safe_exploration_sufficient": self.safe_exploration_sufficient,
            "strategy_variants_tested": self.strategy_variants_tested,
            "task_confirmed": self.task_confirmed,
        }


@dataclass(frozen=True, slots=True)
class GrowthCandidateSummary:
    """Candidate description without creating capacity."""

    type: str
    parent_module: str
    created: bool

    def __post_init__(self) -> None:
        if self.type != "skill_expert":
            raise ValueError("Week 10 may only propose a future skill_expert candidate")
        if self.parent_module != "general_push_controller":
            raise ValueError("Week 10 proposal must point at the general push controller")
        if self.created:
            raise ValueError("Week 10 must not create a specialist")

    def to_json(self) -> dict[str, object]:
        return {
            "created": self.created,
            "parent_module": self.parent_module,
            "type": self.type,
        }


@dataclass(frozen=True, slots=True)
class GrowthProposalRecord:
    """One request for Week 11 investigation, not approval to grow."""

    proposal_id: str
    trigger_ambition: str
    diagnosis: GrowthDiagnosisSummary
    candidate: GrowthCandidateSummary
    expected_benefit: dict[str, object]
    resource_cost: dict[str, object]
    validation_plan: tuple[str, ...]
    retention_limits: tuple[str, ...]
    safety_constraints: tuple[str, ...]
    status: GrowthProposalStatus

    def __post_init__(self) -> None:
        for value in (
            self.proposal_id,
            self.trigger_ambition,
            *self.validation_plan,
            *self.retention_limits,
            *self.safety_constraints,
        ):
            if not value.strip() or not value.isascii():
                raise ValueError("proposal text must be non-empty ASCII")
        if self.status is not GrowthProposalStatus.PROPOSED_NOT_AUTHORISED:
            raise ValueError("Week 10 proposals must remain non-authoritative")

    def to_json(self) -> dict[str, object]:
        return {
            "candidate": self.candidate.to_json(),
            "diagnosis": self.diagnosis.to_json(),
            "expected_benefit": self.expected_benefit,
            "proposal_id": self.proposal_id,
            "resource_cost": self.resource_cost,
            "retention_limits": list(self.retention_limits),
            "safety_constraints": list(self.safety_constraints),
            "status": self.status.value,
            "trigger_ambition": self.trigger_ambition,
            "validation_plan": list(self.validation_plan),
        }


def build_week10_growth_proposal() -> GrowthProposalRecord:
    """Return the single non-authoritative sustained-blockage proposal."""
    return GrowthProposalRecord(
        proposal_id="growth-week10-cube-policy-0001",
        trigger_ambition="control_angular_object_position",
        diagnosis=GrowthDiagnosisSummary(
            task_confirmed=True,
            safe_exploration_sufficient=True,
            relevant_memory_replayed=True,
            existing_skill_attempted=True,
            strategy_variants_tested=4,
            help_requested=True,
            demonstration_attempted=True,
            progress_plateau=True,
            prediction_quality="predictable_contact_effects_but_policy_limited",
            inferred_limitation="general_push_controller_lacks_flat_contact_policy_capacity",
            rejected_alternative_causes=(
                "insufficient_exploration_rejected_by_three_full_windows",
                "missing_experience_rejected_by_grounded_memory_replay",
                "incorrect_prediction_rejected_by_stable_contact_prediction_evidence",
                "poor_strategy_rejected_by_bounded_variant_exhaustion",
                "ambiguous_goal_rejected_by_confirmed_success_condition",
                "inadequate_teaching_rejected_by_completed_demonstration_attempt",
                "optimisation_failure_not_proven_but_less_likely_after_no_progress",
                "impossible_task_rejected_by_demonstration_proven_reachability",
                "resource_limitation_rejected_by_remaining_budget",
            ),
        ),
        candidate=GrowthCandidateSummary(
            type="skill_expert",
            parent_module="general_push_controller",
            created=False,
        ),
        expected_benefit={
            "cube_like_success_gain_target": 0.20,
            "familiar_ball_retention_floor": 0.90,
        },
        resource_cost={
            "new_parameters_created_now": 0,
            "week11_investigation_budget": "bounded_candidate_evaluation_only",
        },
        validation_plan=(
            "week11_train_temporary_skill_expert_candidate",
            "compare_against_general_push_controller",
            "measure_ball_retention_before_any_acceptance",
            "reject_candidate_if_interference_or_authority_violations_appear",
        ),
        retention_limits=(
            "no_specialist_created_in_week10",
            "no_router_created_in_week10",
            "future_candidate_must_not_reduce_ball_success_below_0.90",
        ),
        safety_constraints=(
            "production_curiosity_remains_action_authority",
            "human_stop_denial_permission_remain_protected",
            "no_self_modification_or_shell_or_internet_access",
        ),
        status=GrowthProposalStatus.PROPOSED_NOT_AUTHORISED,
    )
