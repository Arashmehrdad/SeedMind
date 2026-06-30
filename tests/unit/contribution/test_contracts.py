"""Focused tests for Week 9 contribution contracts."""

from __future__ import annotations

import pytest

from seedmind.contribution import (
    CapabilityStatus,
    ContributionShadowAudit,
    HumanContributionRequest,
    PersistedEnvelope,
    SupportPolicy,
    VerificationEvidenceSource,
)
from seedmind.human import HumanRequest, RequestIntentCode, SupportLevel, VerificationRule


def _request() -> HumanContributionRequest:
    return HumanContributionRequest(
        human_request=HumanRequest(
            request_id="request-001",
            intent_code=RequestIntentCode.REPRODUCE_OBSERVED_OUTCOME,
            target_code="move_ball_to_target",
            ambiguity=0.0,
            permission_level=2,
            verification_rule=VerificationRule.CONFIRMED_OUTCOME,
        ),
        target_capability="approach_and_push",
        expected_outcome="target_object_id occupies target_id position",
        target_object_id="object_0",
        target_id="target_0",
        learned_context=("familiar_row", "familiar_column", "familiar_diagonal"),
        requested_support_level=SupportLevel.DEPENDENT,
    )


def test_human_contribution_request_binds_week9_fields() -> None:
    request = _request()

    assert request.target_capability == "approach_and_push"
    assert request.target_object_id == "object_0"
    assert request.target_id == "target_0"
    assert request.learned_context == ("familiar_row", "familiar_column", "familiar_diagonal")


def test_support_policy_enforces_declared_defaults() -> None:
    policy = SupportPolicy()

    assert policy.minimum_verified_independent_familiar_successes == 5
    assert policy.minimum_success_rate == 0.80
    assert policy.minimum_distinct_scenario_contexts == 3
    assert policy.grounded_failures_to_restore_dependent == 2


def test_shadow_audit_rejects_any_authority_or_replacement_violation() -> None:
    assert ContributionShadowAudit().accepted is True
    assert ContributionShadowAudit(authority_violations=1).accepted is False
    assert ContributionShadowAudit(production_action_replacements=1).accepted is False
    assert ContributionShadowAudit(verification_authority_violations=1).accepted is False
    assert ContributionShadowAudit(support_authority_violations=1).accepted is False
    assert ContributionShadowAudit(automatic_promotions=1).accepted is False


def test_persisted_envelope_rejects_checksum_tampering() -> None:
    envelope = PersistedEnvelope.build(payload_type="support_state", payload={"state": "ok"})

    with pytest.raises(ValueError, match="checksum"):
        PersistedEnvelope(
            schema_version=envelope.schema_version,
            payload_type=envelope.payload_type,
            payload={"state": "changed"},
            checksum=envelope.checksum,
        )


def test_contract_enums_expose_required_week9_values() -> None:
    assert {status.value for status in CapabilityStatus} == {
        "unavailable",
        "unproven",
        "degraded",
        "context_mismatched",
        "verified",
    }
    assert VerificationEvidenceSource.SELF_REPORT.value == "self_report"
