"""Versioned learned-consequence checkpoint contracts for NDNRA."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field

from seedmind.research.ndnra.contextual_consequence_transfer import (
    ContextualTransferConfig,
)
from seedmind.research.ndnra.learned_consequence_model import LearnedConsequenceModel
from seedmind.research.ndnra.observed_consequence_chains import (
    ObservedConsequenceChainModel,
)

LEARNED_CONSEQUENCE_SCHEMA = "seedmind.ndnra.learned_consequence"
LEARNED_CONSEQUENCE_SCHEMA_VERSION = 1


@dataclass(frozen=True, slots=True)
class NDNRALearnedConsequenceCheckpoint:
    """Restart checkpoint for validated learned consequence state only."""

    consequence_model: LearnedConsequenceModel = field(default_factory=LearnedConsequenceModel)
    transfer_config: ContextualTransferConfig = field(default_factory=ContextualTransferConfig)
    observed_chain_model: ObservedConsequenceChainModel = field(
        default_factory=ObservedConsequenceChainModel
    )
    automatic_prediction_count: int = 0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.automatic_prediction_count != 0:
            raise ValueError("learned consequence checkpoint cannot contain automatic predictions")
        if self.has_action_selection_authority:
            raise ValueError("learned consequence checkpoint cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("learned consequence checkpoint cannot control production actions")
        if self.consequence_model.has_action_selection_authority:
            raise ValueError("learned consequence model cannot select actions")
        if self.consequence_model.has_production_action_authority:
            raise ValueError("learned consequence model cannot control production actions")
        if self.observed_chain_model.has_action_selection_authority:
            raise ValueError("observed chain model cannot select actions")
        if self.observed_chain_model.has_production_action_authority:
            raise ValueError("observed chain model cannot control production actions")

    @classmethod
    def empty(cls) -> NDNRALearnedConsequenceCheckpoint:
        """Return an explicit empty checkpoint for older brain schemas."""
        return cls()

    def snapshot(self) -> dict[str, object]:
        """Return deterministic restart state without predictions or action authority."""
        return {
            "schema": LEARNED_CONSEQUENCE_SCHEMA,
            "schema_version": LEARNED_CONSEQUENCE_SCHEMA_VERSION,
            "consequence_model": self.consequence_model.snapshot(),
            "transfer_config": self.transfer_config.snapshot(),
            "observed_chain_model": self.observed_chain_model.snapshot(),
            "automatic_prediction_count": self.automatic_prediction_count,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> NDNRALearnedConsequenceCheckpoint:
        """Restore a validated learned consequence checkpoint."""
        values = _require_mapping("learned consequence checkpoint", snapshot)
        if _require_string(values, "schema") != LEARNED_CONSEQUENCE_SCHEMA:
            raise ValueError("learned consequence checkpoint schema is incompatible")
        if _require_int(values, "schema_version") != LEARNED_CONSEQUENCE_SCHEMA_VERSION:
            raise ValueError("learned consequence checkpoint version is incompatible")
        checkpoint = cls(
            consequence_model=LearnedConsequenceModel.from_snapshot(
                values.get("consequence_model")
            ),
            transfer_config=ContextualTransferConfig.from_snapshot(values.get("transfer_config")),
            observed_chain_model=ObservedConsequenceChainModel.from_snapshot(
                values.get("observed_chain_model")
            ),
            automatic_prediction_count=_require_int(values, "automatic_prediction_count"),
            has_action_selection_authority=_require_bool(
                values,
                "has_action_selection_authority",
            ),
            has_production_action_authority=_require_bool(
                values,
                "has_production_action_authority",
            ),
        )
        if checkpoint.snapshot() != dict(values):
            raise ValueError("learned consequence checkpoint snapshot is not canonical")
        return checkpoint


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be a boolean")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


__all__ = [
    "LEARNED_CONSEQUENCE_SCHEMA",
    "LEARNED_CONSEQUENCE_SCHEMA_VERSION",
    "NDNRALearnedConsequenceCheckpoint",
]
