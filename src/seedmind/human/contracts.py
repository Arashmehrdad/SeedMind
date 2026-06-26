"""Symbolic human-apprenticeship contracts and numeric signal encoding."""

from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum, StrEnum
from math import isfinite


class SupportLevel(IntEnum):
    """Implemented SeedMind apprenticeship support levels."""

    GUIDED_LEARNER = 3
    DEPENDENT = 4


class HumanSignalCode(IntEnum):
    """Fixed symbolic events exposed through the protected human channel."""

    NONE = 0
    REQUEST = 1
    DEMONSTRATE = 2
    CORRECT = 3
    APPROVE = 4
    CLARIFY = 5


class RequestIntentCode(StrEnum):
    """Small non-language request vocabulary for the Week 6 nursery."""

    REPRODUCE_OBSERVED_OUTCOME = "reproduce_observed_outcome"
    PRACTICE_ACTIVE_AMBITION = "practice_active_ambition"


class VerificationRule(StrEnum):
    """Externally checked success conditions for symbolic requests."""

    EXTERNAL_CHANGE = "external_change"
    CONFIRMED_OUTCOME = "confirmed_outcome"


@dataclass(frozen=True, slots=True)
class HumanRequest:
    """One symbolic human request with permission and ambiguity metadata."""

    request_id: str
    intent_code: RequestIntentCode
    target_code: str
    ambiguity: float
    permission_level: int
    verification_rule: VerificationRule

    def __post_init__(self) -> None:
        for identifier_name, identifier_value in (
            ("request_id", self.request_id),
            ("target_code", self.target_code),
        ):
            if not identifier_value.strip():
                raise ValueError(f"{identifier_name} must not be empty")
        _validate_unit_interval("ambiguity", self.ambiguity)
        if not 0 <= self.permission_level <= 4:
            raise ValueError("permission_level must be between zero and four")


@dataclass(frozen=True, slots=True)
class HumanSignalFrame:
    """One symbolic caregiver event before conversion to numeric channels."""

    code: HumanSignalCode
    request_id: str | None
    request_active: bool
    ambiguity: float
    permission_level: int
    support_level: SupportLevel
    confidence: float

    def __post_init__(self) -> None:
        if self.request_id is not None and not self.request_id.strip():
            raise ValueError("request_id must not be empty when provided")
        if self.request_active and self.request_id is None:
            raise ValueError("active request signals require request_id")
        _validate_unit_interval("ambiguity", self.ambiguity)
        _validate_unit_interval("confidence", self.confidence)
        if not 0 <= self.permission_level <= 4:
            raise ValueError("permission_level must be between zero and four")


@dataclass(frozen=True, slots=True)
class HumanSignalCodec:
    """Encode symbolic caregiver events into a fixed body-independent vector."""

    @property
    def signal_count(self) -> int:
        """Return the number of one-hot symbolic signal channels."""
        return len(HumanSignalCode)

    @property
    def width(self) -> int:
        """Return one-hot width plus request, ambiguity, permission, and support."""
        return self.signal_count + 5

    def encode(self, frame: HumanSignalFrame) -> tuple[float, ...]:
        """Return a deterministic finite numeric representation."""
        signal_channels = tuple(
            1.0 if index == int(frame.code) else 0.0 for index in range(self.signal_count)
        )
        return (
            *signal_channels,
            float(frame.request_active),
            frame.ambiguity,
            frame.permission_level / 4.0,
            int(frame.support_level) / 4.0,
            frame.confidence,
        )

    def request_frame(
        self,
        request: HumanRequest,
        *,
        support_level: SupportLevel,
    ) -> HumanSignalFrame:
        """Create the symbolic frame announcing one active request."""
        return HumanSignalFrame(
            code=HumanSignalCode.REQUEST,
            request_id=request.request_id,
            request_active=True,
            ambiguity=request.ambiguity,
            permission_level=request.permission_level,
            support_level=support_level,
            confidence=1.0 - request.ambiguity,
        )

    def caregiver_frame(
        self,
        code: HumanSignalCode,
        *,
        request: HumanRequest,
        support_level: SupportLevel,
        confidence: float,
    ) -> HumanSignalFrame:
        """Create a teacher response, correction, approval, or clarification."""
        if code not in (
            HumanSignalCode.DEMONSTRATE,
            HumanSignalCode.CORRECT,
            HumanSignalCode.APPROVE,
            HumanSignalCode.CLARIFY,
        ):
            raise ValueError("caregiver_frame requires a caregiver response code")
        return HumanSignalFrame(
            code=code,
            request_id=request.request_id,
            request_active=True,
            ambiguity=request.ambiguity,
            permission_level=request.permission_level,
            support_level=support_level,
            confidence=confidence,
        )


def _validate_unit_interval(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
