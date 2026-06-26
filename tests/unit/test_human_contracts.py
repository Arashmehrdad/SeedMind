"""Tests for symbolic human request and signal contracts."""

import pytest

from seedmind.human import (
    HumanRequest,
    HumanSignalCode,
    HumanSignalCodec,
    RequestIntentCode,
    SupportLevel,
    VerificationRule,
)


def make_request(ambiguity: float = 0.2) -> HumanRequest:
    return HumanRequest(
        request_id="request-001",
        intent_code=RequestIntentCode.REPRODUCE_OBSERVED_OUTCOME,
        target_code="outcome-signature-001",
        ambiguity=ambiguity,
        permission_level=2,
        verification_rule=VerificationRule.CONFIRMED_OUTCOME,
    )


def test_request_signal_has_fixed_width_and_one_hot_code() -> None:
    codec = HumanSignalCodec()
    frame = codec.request_frame(make_request(), support_level=SupportLevel.DEPENDENT)
    encoded = codec.encode(frame)
    assert len(encoded) == codec.width
    assert sum(encoded[: codec.signal_count]) == 1.0
    assert encoded[int(HumanSignalCode.REQUEST)] == 1.0
    assert encoded[codec.signal_count] == 1.0
    assert encoded[-2] == 1.0


def test_caregiver_frame_encodes_demonstration() -> None:
    codec = HumanSignalCodec()
    frame = codec.caregiver_frame(
        HumanSignalCode.DEMONSTRATE,
        request=make_request(),
        support_level=SupportLevel.GUIDED_LEARNER,
        confidence=0.9,
    )
    assert frame.code is HumanSignalCode.DEMONSTRATE
    assert codec.encode(frame)[int(HumanSignalCode.DEMONSTRATE)] == 1.0


def test_caregiver_frame_rejects_request_code() -> None:
    codec = HumanSignalCodec()
    with pytest.raises(ValueError, match="caregiver response"):
        codec.caregiver_frame(
            HumanSignalCode.REQUEST,
            request=make_request(),
            support_level=SupportLevel.DEPENDENT,
            confidence=1.0,
        )


def test_request_rejects_invalid_metadata() -> None:
    with pytest.raises(ValueError, match="request_id"):
        HumanRequest(
            request_id="",
            intent_code=RequestIntentCode.PRACTICE_ACTIVE_AMBITION,
            target_code="active-ambition",
            ambiguity=0.0,
            permission_level=1,
            verification_rule=VerificationRule.EXTERNAL_CHANGE,
        )
    with pytest.raises(ValueError, match="ambiguity"):
        make_request(1.1)
