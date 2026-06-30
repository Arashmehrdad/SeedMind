"""Tests for canonical SeedMind and NDNRA side-by-side operation."""

from __future__ import annotations

from dataclasses import replace

import pytest

from seedmind.contracts import PrimitiveAction
from seedmind.integration.bounded_advice import (
    AdviceCode,
    AdviceDecision,
    BoundedAdvicePolicy,
)
from seedmind.integration.candidate_session import CandidateSessionResult, CandidateStep
from seedmind.integration.comparison_oracle import CandidateComparison, CandidateOutcome
from seedmind.integration.parallel_operation import (
    ParallelOperationPolicy,
    ParallelOperationResult,
    ProductionActionAuthority,
    SeedMindOperatingMode,
    audit_parallel_candidate_session,
)


def _outcome(action: PrimitiveAction, score: float) -> CandidateOutcome:
    return CandidateOutcome(
        action=action,
        controllable_change=0.2,
        external_change=0.1,
        need_resolution=0.1,
        resource_cost=0.0,
        risk=0.0,
        score=score,
    )


def _session(*, include_comparison: bool = True) -> CandidateSessionResult:
    production = PrimitiveAction.WAIT
    alternative = PrimitiveAction.INSPECT
    agreement = AdviceDecision(
        code=AdviceCode.AGREE,
        production_action=production,
        ndnra_action=production,
        advice_action=production,
        retained_action=production,
        reason_code="agree",
        evidence=None,
    )
    advice = AdviceDecision(
        code=AdviceCode.ADVISE,
        production_action=production,
        ndnra_action=alternative,
        advice_action=alternative,
        retained_action=production,
        reason_code="advise",
        evidence=None,
    )
    comparison = CandidateComparison(
        production=_outcome(production, 0.1),
        ndnra=_outcome(alternative, 0.3),
        advantage=0.2,
        ndnra_better=True,
    )
    return CandidateSessionResult(
        steps=(
            CandidateStep(
                step_index=0,
                production_action=production,
                ndnra_action=production,
                decision=agreement,
                comparison=None,
                prediction_error=0.5,
            ),
            CandidateStep(
                step_index=1,
                production_action=production,
                ndnra_action=alternative,
                decision=advice,
                comparison=comparison if include_comparison else None,
                prediction_error=0.4,
            ),
        ),
        policy=BoundedAdvicePolicy(),
    )


def test_default_policy_keeps_curiosity_authoritative_and_shadow_non_authoritative() -> None:
    policy = ParallelOperationPolicy()

    assert policy.mode is SeedMindOperatingMode.PRODUCTION_WITH_NDNRA_SHADOW
    assert policy.production_action_authority is ProductionActionAuthority.CURIOSITY
    assert not policy.ndnra_has_action_authority
    assert not policy.automatic_component_promotion_enabled
    assert policy.require_comparison_for_disagreement


def test_parallel_audit_records_shadow_comparison_without_replacing_action() -> None:
    session = _session()
    audit = audit_parallel_candidate_session(session)
    result = ParallelOperationResult(
        policy=ParallelOperationPolicy(),
        session=session,
        audit=audit,
    )

    assert result.audit.step_count == 2
    assert result.audit.production_action_retained_count == 2
    assert result.audit.shadow_observation_count == 2
    assert result.audit.suggestion_count == 2
    assert result.audit.disagreement_count == 1
    assert result.audit.comparison_count == 1
    assert result.audit.ndnra_better_count == 1
    assert result.audit.authority_violation_count == 0
    assert result.audit.automatic_promotion_count == 0
    assert result.audit.pass_gate
    assert result.session.actions == (PrimitiveAction.WAIT, PrimitiveAction.WAIT)


def test_missing_disagreement_comparison_fails_the_parallel_boundary() -> None:
    session = _session(include_comparison=False)
    audit = audit_parallel_candidate_session(session)

    assert not audit.pass_gate
    with pytest.raises(ValueError, match="authority boundary failed"):
        ParallelOperationResult(
            policy=ParallelOperationPolicy(),
            session=session,
            audit=audit,
        )


def test_parallel_policy_rejects_action_authority_and_automatic_promotion() -> None:
    with pytest.raises(ValueError, match="cannot have production action authority"):
        ParallelOperationPolicy(ndnra_has_action_authority=True)
    with pytest.raises(ValueError, match="cannot be promoted automatically"):
        ParallelOperationPolicy(automatic_component_promotion_enabled=True)


def test_audit_identity_mismatch_is_rejected() -> None:
    session = _session()
    audit = audit_parallel_candidate_session(session)

    with pytest.raises(ValueError, match="does not match the session"):
        ParallelOperationResult(
            policy=ParallelOperationPolicy(),
            session=session,
            audit=replace(audit, step_count=3, shadow_observation_count=3),
        )
