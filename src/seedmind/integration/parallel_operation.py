"""Canonical side-by-side operation of production SeedMind and NDNRA shadow mode."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from seedmind.curiosity import CuriosityConfig
from seedmind.environment import DynamicNurseryScenarioFactory
from seedmind.integration.candidate_session import (
    CandidateSessionResult,
    run_candidate_session,
)
from seedmind.integration.developmental_signals import LiveDevelopmentalSignalProvider
from seedmind.integration.unified_shadow import NDNRALiveShadowAdapter
from seedmind.training import OnlinePredictiveTrainer


class SeedMindOperatingMode(StrEnum):
    """Authorised main-project operating mode."""

    PRODUCTION_WITH_NDNRA_SHADOW = "production_with_ndnra_shadow"


class ProductionActionAuthority(StrEnum):
    """Component allowed to select the action executed by the runtime."""

    CURIOSITY = "production_curiosity"


@dataclass(frozen=True, slots=True)
class ParallelOperationPolicy:
    """Fail-closed policy for running SeedMind and NDNRA side by side."""

    mode: SeedMindOperatingMode = SeedMindOperatingMode.PRODUCTION_WITH_NDNRA_SHADOW
    production_action_authority: ProductionActionAuthority = ProductionActionAuthority.CURIOSITY
    ndnra_has_action_authority: bool = False
    automatic_component_promotion_enabled: bool = False
    require_comparison_for_disagreement: bool = True

    def __post_init__(self) -> None:
        if self.mode is not SeedMindOperatingMode.PRODUCTION_WITH_NDNRA_SHADOW:
            raise ValueError("only production-with-NDNRA-shadow mode is authorised")
        if self.production_action_authority is not ProductionActionAuthority.CURIOSITY:
            raise ValueError("production curiosity must remain the action authority")
        if self.ndnra_has_action_authority:
            raise ValueError("NDNRA shadow mode cannot have production action authority")
        if self.automatic_component_promotion_enabled:
            raise ValueError("NDNRA components cannot be promoted automatically")


@dataclass(frozen=True, slots=True)
class ParallelOperationAudit:
    """Inspectable evidence that the side-by-side boundary was preserved."""

    step_count: int
    production_action_retained_count: int
    shadow_observation_count: int
    suggestion_count: int
    disagreement_count: int
    comparison_count: int
    ndnra_better_count: int
    authority_violation_count: int
    automatic_promotion_count: int
    pass_gate: bool

    def __post_init__(self) -> None:
        values = (
            self.step_count,
            self.production_action_retained_count,
            self.shadow_observation_count,
            self.suggestion_count,
            self.disagreement_count,
            self.comparison_count,
            self.ndnra_better_count,
            self.authority_violation_count,
            self.automatic_promotion_count,
        )
        if any(value < 0 for value in values):
            raise ValueError("parallel-operation audit counts must not be negative")
        if self.production_action_retained_count > self.step_count:
            raise ValueError("retained production actions cannot exceed step count")
        if self.shadow_observation_count != self.step_count:
            raise ValueError("NDNRA shadow must observe every production step")
        if self.suggestion_count > self.step_count:
            raise ValueError("suggestion count cannot exceed step count")
        if self.disagreement_count > self.suggestion_count:
            raise ValueError("disagreement count cannot exceed suggestion count")
        if self.comparison_count > self.disagreement_count:
            raise ValueError("comparison count cannot exceed disagreement count")
        if self.ndnra_better_count > self.comparison_count:
            raise ValueError("NDNRA-better count cannot exceed comparison count")


@dataclass(frozen=True, slots=True)
class ParallelOperationResult:
    """Candidate session plus the policy and boundary audit applied to it."""

    policy: ParallelOperationPolicy
    session: CandidateSessionResult
    audit: ParallelOperationAudit

    def __post_init__(self) -> None:
        if self.audit.step_count != len(self.session.steps):
            raise ValueError("parallel-operation audit does not match the session")
        if not self.audit.pass_gate:
            raise ValueError("parallel-operation authority boundary failed")


def audit_parallel_candidate_session(
    session: CandidateSessionResult,
    policy: ParallelOperationPolicy | None = None,
) -> ParallelOperationAudit:
    """Verify production retention, comparison coverage, and zero authority."""
    resolved_policy = ParallelOperationPolicy() if policy is None else policy
    steps = session.steps
    retained_count = sum(step.decision.retained_action is step.production_action for step in steps)
    suggestion_count = sum(step.ndnra_action is not None for step in steps)
    disagreement_count = sum(
        step.ndnra_action is not None and step.ndnra_action is not step.production_action
        for step in steps
    )
    comparison_count = len(session.comparisons)
    ndnra_better_count = sum(comparison.ndnra_better for comparison in session.comparisons)
    authority_violation_count = sum(step.decision.has_action_authority for step in steps)
    comparison_coverage_passed = (
        comparison_count == disagreement_count
        if resolved_policy.require_comparison_for_disagreement
        else comparison_count <= disagreement_count
    )
    pass_gate = bool(
        retained_count == len(steps)
        and authority_violation_count == 0
        and comparison_coverage_passed
        and not resolved_policy.ndnra_has_action_authority
        and not resolved_policy.automatic_component_promotion_enabled
    )
    return ParallelOperationAudit(
        step_count=len(steps),
        production_action_retained_count=retained_count,
        shadow_observation_count=len(steps),
        suggestion_count=suggestion_count,
        disagreement_count=disagreement_count,
        comparison_count=comparison_count,
        ndnra_better_count=ndnra_better_count,
        authority_violation_count=authority_violation_count,
        automatic_promotion_count=0,
        pass_gate=pass_gate,
    )


def run_parallel_candidate_session(
    *,
    scenario_factory: DynamicNurseryScenarioFactory,
    seed: int,
    curiosity_config: CuriosityConfig,
    shadow: NDNRALiveShadowAdapter,
    signal_provider: LiveDevelopmentalSignalProvider,
    trainer: OnlinePredictiveTrainer,
    policy: ParallelOperationPolicy | None = None,
) -> ParallelOperationResult:
    """Run the existing candidate session under the canonical safe policy."""
    resolved_policy = ParallelOperationPolicy() if policy is None else policy
    session = run_candidate_session(
        scenario_factory=scenario_factory,
        seed=seed,
        curiosity_config=curiosity_config,
        shadow=shadow,
        signal_provider=signal_provider,
        trainer=trainer,
    )
    audit = audit_parallel_candidate_session(session, resolved_policy)
    return ParallelOperationResult(
        policy=resolved_policy,
        session=session,
        audit=audit,
    )
