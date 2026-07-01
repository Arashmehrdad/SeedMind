"""Proposal-only specialist routing for original SeedMind Week 11."""

from dataclasses import dataclass

from seedmind.contracts import PrimitiveAction
from seedmind.growth.specialist import ExpertModuleOutput


@dataclass(frozen=True, slots=True)
class RoutingDecision:
    """One inspectable module-selection proposal."""

    selected_module: str
    action_proposal: PrimitiveAction | None
    confidence: float
    abstained: bool
    fallback_used: bool
    reason_code: str
    specialist_registered: bool
    specialist_active: bool
    proposal_authority: str = "proposal_only"
    production_authority: str = "production_curiosity"
    action_authority_violation: bool = False

    def __post_init__(self) -> None:
        if not 0.0 <= self.confidence <= 1.0:
            raise ValueError("router confidence must be in [0, 1]")
        if self.abstained != (self.action_proposal is None):
            raise ValueError("router abstention and action proposal disagree")
        if self.proposal_authority != "proposal_only":
            raise ValueError("router must remain proposal-only")
        if self.production_authority != "production_curiosity":
            raise ValueError("production curiosity must remain action authority")
        if self.action_authority_violation:
            raise ValueError("router cannot claim action authority")


@dataclass(frozen=True, slots=True)
class SpecialistRouter:
    """Prefer a registered specialist only when it clears the confidence gate."""

    specialist_module_id: str
    minimum_specialist_confidence: float = 0.70

    def __post_init__(self) -> None:
        if not self.specialist_module_id.strip() or not self.specialist_module_id.isascii():
            raise ValueError("specialist_module_id must be non-empty ASCII")
        if not 0.0 <= self.minimum_specialist_confidence <= 1.0:
            raise ValueError("minimum_specialist_confidence must be in [0, 1]")

    def route(
        self,
        *,
        general_proposal: ExpertModuleOutput,
        specialist_proposal: ExpertModuleOutput,
        specialist_registered: bool,
        specialist_active: bool,
    ) -> RoutingDecision:
        specialist_eligible = (
            specialist_registered
            and specialist_active
            and not specialist_proposal.abstain
            and specialist_proposal.confidence >= self.minimum_specialist_confidence
        )
        if specialist_eligible:
            return RoutingDecision(
                selected_module=self.specialist_module_id,
                action_proposal=specialist_proposal.action_proposal,
                confidence=specialist_proposal.confidence,
                abstained=False,
                fallback_used=False,
                reason_code="specialist_confident_in_registered_scope",
                specialist_registered=True,
                specialist_active=True,
            )
        if not general_proposal.abstain:
            return RoutingDecision(
                selected_module="general_push_controller",
                action_proposal=general_proposal.action_proposal,
                confidence=general_proposal.confidence,
                abstained=False,
                fallback_used=specialist_registered and specialist_active,
                reason_code="general_fallback_or_default",
                specialist_registered=specialist_registered,
                specialist_active=specialist_active,
            )
        return RoutingDecision(
            selected_module="none",
            action_proposal=None,
            confidence=0.0,
            abstained=True,
            fallback_used=False,
            reason_code="all_available_modules_abstained",
            specialist_registered=specialist_registered,
            specialist_active=specialist_active,
        )
