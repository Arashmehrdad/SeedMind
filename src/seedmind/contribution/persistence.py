"""Strict persistence for Week 9 contribution history and support state."""

from __future__ import annotations

import json
from pathlib import Path

from seedmind.contribution.contracts import (
    CONTRIBUTION_SCHEMA_VERSION,
    CapabilityCheck,
    CapabilityEvidence,
    CapabilityStatus,
    ContributionRecord,
    ContributionShadowAudit,
    GroundedOutcomeVerification,
    HonestFailureReport,
    HumanAuthorityInterruption,
    HumanContributionRequest,
    PersistedEnvelope,
    SupportEvaluation,
    SupportPolicy,
    SupportState,
    VerificationEvidenceSource,
    VerificationStatus,
    calculate_checksum,
)
from seedmind.human.contracts import (
    HumanRequest,
    RequestIntentCode,
    SupportLevel,
    VerificationRule,
)

ATOMIC_TEMP_SUFFIX = ".tmp"


def save_contribution_history(path: Path, history: tuple[ContributionRecord, ...]) -> None:
    """Atomically write contribution history as checksum-protected ASCII JSON."""
    payload = {
        "contribution_schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "records": [record.to_json() for record in history],
    }
    _save_envelope(path, payload_type="contribution_history", payload=payload)


def save_support_state(path: Path, state: SupportState) -> None:
    """Atomically write support state as checksum-protected ASCII JSON."""
    payload = {
        "contribution_schema_version": CONTRIBUTION_SCHEMA_VERSION,
        "support_state": state.to_json(),
    }
    _save_envelope(path, payload_type="support_state", payload=payload)


def load_support_state(path: Path, policy: SupportPolicy | None = None) -> SupportState:
    """Load support state or return a conservative fresh DEPENDENT fallback."""
    fallback = SupportState.fresh(policy)
    envelope = _load_envelope(path, expected_type="support_state")
    if envelope is None:
        return fallback
    try:
        payload = envelope.payload
        if _require_int(payload, "contribution_schema_version") != CONTRIBUTION_SCHEMA_VERSION:
            return fallback
        data = _require_object(payload, "support_state")
        history = tuple(
            CapabilityEvidence.from_json(item) for item in _require_object_list(data, "history")
        )
        policy_payload = _require_object(data, "policy")
        resolved_policy = SupportPolicy(
            minimum_verified_independent_familiar_successes=_require_int(
                policy_payload, "minimum_verified_independent_familiar_successes"
            ),
            minimum_success_rate=_require_float(policy_payload, "minimum_success_rate"),
            minimum_distinct_scenario_contexts=_require_int(
                policy_payload, "minimum_distinct_scenario_contexts"
            ),
            recent_evidence_window=_require_int(policy_payload, "recent_evidence_window"),
            grounded_failures_to_restore_dependent=_require_int(
                policy_payload, "grounded_failures_to_restore_dependent"
            ),
        )
        evaluation_payload = _require_object(data, "last_evaluation")
        evaluation = SupportEvaluation(
            previous_level=SupportLevel(_require_int(evaluation_payload, "previous_level")),
            next_level=SupportLevel(_require_int(evaluation_payload, "next_level")),
            blocker_codes=tuple(_require_str_list(evaluation_payload, "blocker_codes")),
            recent_verified_independent_familiar_successes=_require_int(
                evaluation_payload, "recent_verified_independent_familiar_successes"
            ),
            recent_success_rate=_require_float(evaluation_payload, "recent_success_rate"),
            distinct_scenario_contexts=_require_int(
                evaluation_payload, "distinct_scenario_contexts"
            ),
            recent_grounded_familiar_failures=_require_int(
                evaluation_payload, "recent_grounded_familiar_failures"
            ),
        )
        return SupportState(
            current_level=SupportLevel(_require_int(data, "current_level")),
            policy=resolved_policy,
            history=history,
            promotion_evidence_start_index=_require_int(data, "promotion_evidence_start_index"),
            last_evaluation=evaluation,
        )
    except (KeyError, TypeError, ValueError):
        return fallback


def load_contribution_history(path: Path) -> tuple[ContributionRecord, ...]:
    """Load contribution history or return a conservative empty fallback."""
    envelope = _load_envelope(path, expected_type="contribution_history")
    if envelope is None:
        return ()
    try:
        payload = envelope.payload
        if _require_int(payload, "contribution_schema_version") != CONTRIBUTION_SCHEMA_VERSION:
            return ()
        return tuple(
            _history_record_from_json(item) for item in _require_object_list(payload, "records")
        )
    except (KeyError, TypeError, ValueError):
        return ()


def _history_record_from_json(payload: dict[str, object]) -> ContributionRecord:
    request_payload = _require_object(payload, "request")
    human_request_payload = _require_object(request_payload, "human_request")

    request = HumanContributionRequest(
        human_request=HumanRequest(
            request_id=_require_str(human_request_payload, "request_id"),
            intent_code=RequestIntentCode(_require_str(human_request_payload, "intent_code")),
            target_code=_require_str(human_request_payload, "target_code"),
            ambiguity=_require_float(human_request_payload, "ambiguity"),
            permission_level=_require_int(human_request_payload, "permission_level"),
            verification_rule=VerificationRule(
                _require_str(human_request_payload, "verification_rule")
            ),
        ),
        target_capability=_require_str(request_payload, "target_capability"),
        expected_outcome=_require_str(request_payload, "expected_outcome"),
        target_object_id=_require_str(request_payload, "target_object_id"),
        target_id=_require_str(request_payload, "target_id"),
        learned_context=tuple(_require_str_list(request_payload, "learned_context")),
        requested_support_level=SupportLevel(
            _require_int(request_payload, "requested_support_level")
        ),
    )
    capability_check_payload = _require_object(payload, "capability_check")
    capability_check = CapabilityCheck(
        status=CapabilityStatus(_require_str(capability_check_payload, "status")),
        target_capability=_require_str(capability_check_payload, "target_capability"),
        checked_skill_id=_require_optional_str(capability_check_payload, "checked_skill_id"),
        expected_outcome_matched=_require_bool(
            capability_check_payload, "expected_outcome_matched"
        ),
        target_object_matched=_require_bool(capability_check_payload, "target_object_matched"),
        target_matched=_require_bool(capability_check_payload, "target_matched"),
        learned_context_matched=_require_bool(capability_check_payload, "learned_context_matched"),
        reason_codes=tuple(_require_str_list(capability_check_payload, "reason_codes")),
        failed_preconditions=tuple(
            _require_str_list(capability_check_payload, "failed_preconditions")
        ),
    )
    verification_payload = _require_object(payload, "verification")
    verification = GroundedOutcomeVerification(
        status=VerificationStatus(_require_str(verification_payload, "status")),
        evidence_sources=tuple(
            VerificationEvidenceSource(item)
            for item in _require_str_list(verification_payload, "evidence_sources")
        ),
        reason_code=_require_str(verification_payload, "reason_code"),
        target_achieved=_require_bool(verification_payload, "target_achieved"),
    )
    audit = _load_shadow_audit(_require_object(payload, "authority_audit"))
    failure_payload = _require_optional_object(payload, "failure_report")
    failure_report = None
    if failure_payload is not None:
        failure = failure_payload
        failure_report = HonestFailureReport(
            reason=_require_str(failure, "reason"),
            attempted_capability=_require_str(failure, "attempted_capability"),
            failed_preconditions=tuple(_require_str_list(failure, "failed_preconditions")),
            interruption=_load_optional_interruption(failure, "interruption"),
            uncertainty=_require_str(failure, "uncertainty"),
            requested_support=SupportLevel(_require_int(failure, "requested_support")),
            verification_status=VerificationStatus(_require_str(failure, "verification_status")),
            authority_audit=_load_shadow_audit(_require_object(failure, "authority_audit")),
        )
    return ContributionRecord(
        contribution_id=_require_str(payload, "contribution_id"),
        request=request,
        scenario_id=_require_str(payload, "scenario_id"),
        scenario_context=_require_str(payload, "scenario_context"),
        seed=_require_int(payload, "seed"),
        attempted_capability=_require_str(payload, "attempted_capability"),
        support_level_before=SupportLevel(_require_int(payload, "support_level_before")),
        support_level_after=SupportLevel(_require_int(payload, "support_level_after")),
        requested_support=SupportLevel(_require_int(payload, "requested_support")),
        capability_check=capability_check,
        verification=verification,
        success=_require_bool(payload, "success"),
        independent_execution=_require_bool(payload, "independent_execution"),
        familiar_context=_require_bool(payload, "familiar_context"),
        executed_steps=_require_int(payload, "executed_steps"),
        retained_steps=_require_int(payload, "retained_steps"),
        interruption=_load_optional_interruption(payload, "interruption"),
        authority_audit=audit,
        failure_report=failure_report,
        evidence=CapabilityEvidence.from_json(_require_object(payload, "evidence")),
        action_trace=tuple(_require_str_list(payload, "action_trace")),
        outcome_trace=tuple(_require_str_list(payload, "outcome_trace")),
    )


def _save_envelope(path: Path, *, payload_type: str, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    envelope = PersistedEnvelope.build(payload_type=payload_type, payload=payload)
    temporary = _stage_path_for(path)
    temporary.write_text(
        json.dumps(envelope.to_json(), ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary.replace(path)


def _load_envelope(path: Path, *, expected_type: str) -> PersistedEnvelope | None:
    if not path.exists():
        return None
    try:
        payload = json.loads(path.read_text(encoding="ascii"))
        if not isinstance(payload, dict):
            return None
        envelope = PersistedEnvelope.from_json(payload)
    except (OSError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return None
    if envelope.payload_type != expected_type:
        return None
    if envelope.checksum != calculate_checksum(envelope.payload):
        return None
    return envelope


def _load_optional_interruption(
    payload: dict[str, object], key: str
) -> HumanAuthorityInterruption | None:
    value = _require_optional_str(payload, key)
    return None if value is None else HumanAuthorityInterruption(value)


def _load_shadow_audit(payload: dict[str, object]) -> ContributionShadowAudit:
    return ContributionShadowAudit(
        observations=_require_int(payload, "observations"),
        suggestions=_require_int(payload, "suggestions"),
        disagreements=_require_int(payload, "disagreements"),
        comparisons=_require_int(payload, "comparisons"),
        production_actions_retained=_require_int(payload, "production_actions_retained"),
        production_action_replacements=_require_int(payload, "production_action_replacements"),
        authority_violations=_require_int(payload, "authority_violations"),
        verification_authority_violations=_require_int(
            payload, "verification_authority_violations"
        ),
        support_authority_violations=_require_int(payload, "support_authority_violations"),
        automatic_promotions=_require_int(payload, "automatic_promotions"),
    )


def _stage_path_for(path: Path) -> Path:
    return path.with_name(f"{path.name}{ATOMIC_TEMP_SUFFIX}")


def _require_bool(payload: dict[str, object], key: str) -> bool:
    value = payload[key]
    if not isinstance(value, bool):
        raise TypeError(f"{key} must be a bool")
    return value


def _require_float(payload: dict[str, object], key: str) -> float:
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise TypeError(f"{key} must be a float")
    return float(value)


def _require_int(payload: dict[str, object], key: str) -> int:
    value = payload[key]
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{key} must be an int")
    return value


def _require_object(payload: dict[str, object], key: str) -> dict[str, object]:
    value = payload[key]
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be an object")
    if any(not isinstance(item_key, str) for item_key in value):
        raise TypeError(f"{key} must have string keys")
    return value


def _require_optional_object(payload: dict[str, object], key: str) -> dict[str, object] | None:
    value = payload[key]
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError(f"{key} must be an object or null")
    if any(not isinstance(item_key, str) for item_key in value):
        raise TypeError(f"{key} must have string keys")
    return value


def _require_object_list(payload: dict[str, object], key: str) -> list[dict[str, object]]:
    value = payload[key]
    if not isinstance(value, list):
        raise TypeError(f"{key} must be a list")
    result: list[dict[str, object]] = []
    for index, item in enumerate(value):
        if not isinstance(item, dict):
            raise TypeError(f"{key}[{index}] must be an object")
        if any(not isinstance(item_key, str) for item_key in item):
            raise TypeError(f"{key}[{index}] must have string keys")
        result.append(item)
    return result


def _require_optional_str(payload: dict[str, object], key: str) -> str | None:
    value = payload[key]
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string or null")
    return value


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload[key]
    if not isinstance(value, str):
        raise TypeError(f"{key} must be a string")
    return value


def _require_str_list(payload: dict[str, object], key: str) -> list[str]:
    value = payload[key]
    if not isinstance(value, list):
        raise TypeError(f"{key} must be a list")
    result: list[str] = []
    for index, item in enumerate(value):
        if not isinstance(item, str):
            raise TypeError(f"{key}[{index}] must be a string")
        result.append(item)
    return result
