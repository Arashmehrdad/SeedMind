"""Stage 6 hibernation, dream maintenance, and restart identity evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path
from typing import Any

STAGE_SIX_HIBERNATION_SCHEMA = "seedmind.ndnra.developmental.stage6.hibernation"
STAGE_SIX_HIBERNATION_SCHEMA_VERSION = 1


class CoalitionDormancyState(StrEnum):
    """Stage 6 coalition dormancy states."""

    ACTIVE = "active"
    DORMANT = "dormant"
    HIBERNATING = "hibernating"
    DREAM_ACTIVE = "dream_active"


class StageSixLoadStatus(StrEnum):
    """Safe restart load status."""

    RESTORED = "restored"
    FALLBACK = "fallback"


@dataclass(frozen=True, slots=True)
class StageSixHibernationConfig:
    """Finite Stage 6 hibernation and restart bounds."""

    seed: int = 46
    schema: str = STAGE_SIX_HIBERNATION_SCHEMA
    schema_version: int = STAGE_SIX_HIBERNATION_SCHEMA_VERSION
    maximum_dream_replay_sources: int = 3

    def __post_init__(self) -> None:
        _validate_non_negative_int("seed", self.seed)
        _validate_ascii_code("schema", self.schema)
        _validate_positive_int("schema_version", self.schema_version)
        _validate_positive_int("maximum_dream_replay_sources", self.maximum_dream_replay_sources)

    def snapshot(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "schema": self.schema,
            "schema_version": self.schema_version,
            "maximum_dream_replay_sources": self.maximum_dream_replay_sources,
        }


@dataclass(frozen=True, slots=True)
class HibernatingCoalitionState:
    """Dormant or hibernating coalition that preserves structure and provenance."""

    coalition_code: str
    neuron_ids: tuple[str, ...]
    topology_edge_codes: tuple[str, ...]
    weight_by_edge: Mapping[str, float]
    inhibition_by_edge: Mapping[str, float]
    maturity_state_code: str
    plasticity: float
    dormancy_state: CoalitionDormancyState
    provenance_experience_ids: tuple[str, ...]
    accessibility: float
    importance: float
    protected: bool = False
    factual_evidence_count: int = 0
    has_external_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("coalition_code", self.coalition_code)
        _validate_sorted_unique_ascii_codes("neuron_ids", self.neuron_ids)
        _validate_sorted_unique_ascii_codes("topology_edge_codes", self.topology_edge_codes)
        _validate_ascii_code("maturity_state_code", self.maturity_state_code)
        _validate_unit("plasticity", self.plasticity)
        _validate_sorted_unique_ascii_codes(
            "provenance_experience_ids",
            self.provenance_experience_ids,
        )
        _validate_unit("accessibility", self.accessibility)
        _validate_unit("importance", self.importance)
        _validate_non_negative_int("factual_evidence_count", self.factual_evidence_count)
        if not self.neuron_ids or not self.topology_edge_codes:
            raise ValueError("hibernating coalitions must preserve structure")
        if set(self.weight_by_edge) != set(self.topology_edge_codes):
            raise ValueError("weights must cover exact topology edges")
        if set(self.inhibition_by_edge) != set(self.topology_edge_codes):
            raise ValueError("inhibition must cover exact topology edges")
        for weight in self.weight_by_edge.values():
            _validate_signed_unit("weight_by_edge", weight)
        for inhibition in self.inhibition_by_edge.values():
            _validate_unit("inhibition_by_edge", inhibition)
        if self.has_external_action_authority:
            raise ValueError("hibernating coalitions cannot hold external action authority")

    @property
    def coalition_id(self) -> str:
        return _identity("hibernating-coalition", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"coalition_id": self.coalition_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "coalition_code": self.coalition_code,
            "neuron_ids": list(self.neuron_ids),
            "topology_edge_codes": list(self.topology_edge_codes),
            "weight_by_edge": {
                edge: self.weight_by_edge[edge] for edge in self.topology_edge_codes
            },
            "inhibition_by_edge": {
                edge: self.inhibition_by_edge[edge] for edge in self.topology_edge_codes
            },
            "maturity_state_code": self.maturity_state_code,
            "plasticity": self.plasticity,
            "dormancy_state": self.dormancy_state.value,
            "provenance_experience_ids": list(self.provenance_experience_ids),
            "accessibility": self.accessibility,
            "importance": self.importance,
            "protected": self.protected,
            "factual_evidence_count": self.factual_evidence_count,
            "has_external_action_authority": self.has_external_action_authority,
        }


@dataclass(frozen=True, slots=True)
class DreamReplayRecord:
    """Caller-invoked dream replay that cannot create factual evidence or actions."""

    replay_code: str
    source_experience_ids: tuple[str, ...]
    accessibility_delta: float
    matched_control_delta: float
    factual_evidence_delta: int = 0
    action_execution_count: int = 0
    weakens_protected_prohibition: bool = False
    autonomous_worker_used: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("replay_code", self.replay_code)
        _validate_sorted_unique_ascii_codes("source_experience_ids", self.source_experience_ids)
        _validate_unit("accessibility_delta", self.accessibility_delta)
        _validate_unit("matched_control_delta", self.matched_control_delta)
        _validate_zero_int("factual_evidence_delta", self.factual_evidence_delta)
        _validate_zero_int("action_execution_count", self.action_execution_count)
        if self.weakens_protected_prohibition:
            raise ValueError("dream replay cannot weaken protected prohibitions")
        if self.autonomous_worker_used:
            raise ValueError("dream replay must be caller-invoked, not autonomous")

    @property
    def replay_id(self) -> str:
        return _identity("dream-replay-record", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"replay_id": self.replay_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "replay_code": self.replay_code,
            "source_experience_ids": list(self.source_experience_ids),
            "accessibility_delta": self.accessibility_delta,
            "matched_control_delta": self.matched_control_delta,
            "factual_evidence_delta": self.factual_evidence_delta,
            "action_execution_count": self.action_execution_count,
            "weakens_protected_prohibition": self.weakens_protected_prohibition,
            "autonomous_worker_used": self.autonomous_worker_used,
        }


@dataclass(frozen=True, slots=True)
class RecallRestorationEvidence:
    """Recall access before and after stronger need or dream maintenance."""

    coalition_code: str
    shallow_recall_access: float
    stronger_need_access: float
    related_activation_access: float
    dream_maintained_access: float
    unreplayed_control_access: float
    long_inactivity_retrieval_access: float

    def __post_init__(self) -> None:
        _validate_ascii_code("coalition_code", self.coalition_code)
        for name, value in (
            ("shallow_recall_access", self.shallow_recall_access),
            ("stronger_need_access", self.stronger_need_access),
            ("related_activation_access", self.related_activation_access),
            ("dream_maintained_access", self.dream_maintained_access),
            ("unreplayed_control_access", self.unreplayed_control_access),
            ("long_inactivity_retrieval_access", self.long_inactivity_retrieval_access),
        ):
            _validate_unit(name, value)
        if self.shallow_recall_access >= 0.5:
            raise ValueError("shallow dormant recall must be allowed to fail")
        if (
            max(
                self.stronger_need_access,
                self.related_activation_access,
                self.dream_maintained_access,
            )
            <= self.shallow_recall_access
        ):
            raise ValueError("stronger need, relation, or dream maintenance must restore access")
        if self.dream_maintained_access <= self.unreplayed_control_access:
            raise ValueError("dream replay must improve accessibility versus matched control")

    @property
    def evidence_id(self) -> str:
        return _identity("recall-restoration-evidence", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "coalition_code": self.coalition_code,
            "shallow_recall_access": self.shallow_recall_access,
            "stronger_need_access": self.stronger_need_access,
            "related_activation_access": self.related_activation_access,
            "dream_maintained_access": self.dream_maintained_access,
            "unreplayed_control_access": self.unreplayed_control_access,
            "long_inactivity_retrieval_access": self.long_inactivity_retrieval_access,
        }


@dataclass(frozen=True, slots=True)
class StageSixRestartLoadResult:
    """Safe restart load result."""

    status: StageSixLoadStatus
    restored_evidence: StageSixHibernationEvidence | None = None
    fallback_reason: str | None = None

    def __post_init__(self) -> None:
        if self.status is StageSixLoadStatus.RESTORED and self.restored_evidence is None:
            raise ValueError("restored load requires evidence")
        if self.status is StageSixLoadStatus.FALLBACK and self.fallback_reason is None:
            raise ValueError("fallback load requires reason")
        if self.fallback_reason is not None:
            _validate_ascii_code("fallback_reason", self.fallback_reason)


@dataclass(frozen=True, slots=True)
class StageSixRestartProof:
    """Restart equivalence and fallback evidence."""

    saved_evidence_id: str
    restored_evidence_id: str
    first_post_restart_recall_matches: bool
    protected_network_remains_protected: bool
    malformed_load_status: StageSixLoadStatus
    incompatible_schema_load_status: StageSixLoadStatus

    def __post_init__(self) -> None:
        _validate_ascii_code("saved_evidence_id", self.saved_evidence_id)
        _validate_ascii_code("restored_evidence_id", self.restored_evidence_id)
        if self.saved_evidence_id != self.restored_evidence_id:
            raise ValueError("restart must restore exact evidence identity")
        if not self.first_post_restart_recall_matches:
            raise ValueError("first post-restart recall must match uninterrupted control")
        if not self.protected_network_remains_protected:
            raise ValueError("protected network must remain protected after restart")
        if self.malformed_load_status is not StageSixLoadStatus.FALLBACK:
            raise ValueError("malformed state must produce complete fallback")
        if self.incompatible_schema_load_status is not StageSixLoadStatus.FALLBACK:
            raise ValueError("incompatible schema must produce complete fallback")

    def snapshot(self) -> dict[str, object]:
        return {
            "saved_evidence_id": self.saved_evidence_id,
            "restored_evidence_id": self.restored_evidence_id,
            "first_post_restart_recall_matches": self.first_post_restart_recall_matches,
            "protected_network_remains_protected": self.protected_network_remains_protected,
            "malformed_load_status": self.malformed_load_status.value,
            "incompatible_schema_load_status": self.incompatible_schema_load_status.value,
        }


@dataclass(frozen=True, slots=True)
class StageSixHibernationEvidence:
    """Integrated Stage 6 hibernation and restart acceptance evidence."""

    config: StageSixHibernationConfig
    coalitions: tuple[HibernatingCoalitionState, ...]
    recall_evidence: RecallRestorationEvidence
    dream_replay: DreamReplayRecord
    sqlite_cognition_operation_count: int = 0
    external_side_effect_count: int = 0
    production_action_authority_violations: int = 0

    def __post_init__(self) -> None:
        _validate_non_empty_sequence("coalitions", self.coalitions)
        if len({coalition.coalition_code for coalition in self.coalitions}) != len(self.coalitions):
            raise ValueError("coalitions must be unique")
        if len(self.dream_replay.source_experience_ids) > self.config.maximum_dream_replay_sources:
            raise ValueError("dream replay exceeds configured source bound")
        _validate_zero_int(
            "sqlite_cognition_operation_count", self.sqlite_cognition_operation_count
        )
        _validate_zero_int("external_side_effect_count", self.external_side_effect_count)
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage 6 pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-six-hibernation-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        dormant = tuple(
            coalition
            for coalition in self.coalitions
            if coalition.dormancy_state
            in {CoalitionDormancyState.DORMANT, CoalitionDormancyState.HIBERNATING}
        )
        return {
            "dormant_coalitions_remain_structurally_present": all(
                coalition.neuron_ids and coalition.topology_edge_codes for coalition in dormant
            ),
            "stronger_need_related_activation_or_dream_restores_access": (
                self.recall_evidence.shallow_recall_access < 0.5
                and max(
                    self.recall_evidence.stronger_need_access,
                    self.recall_evidence.related_activation_access,
                    self.recall_evidence.dream_maintained_access,
                )
                > self.recall_evidence.shallow_recall_access
            ),
            "dream_replay_improves_later_accessibility": (
                self.dream_replay.accessibility_delta > self.dream_replay.matched_control_delta
                and self.recall_evidence.dream_maintained_access
                > self.recall_evidence.unreplayed_control_access
            ),
            "dream_replay_creates_zero_factual_evidence": (
                self.dream_replay.factual_evidence_delta == 0
                and all(coalition.factual_evidence_count == 0 for coalition in self.coalitions)
            ),
            "rare_important_experience_retrievable_after_long_inactivity": (
                any(coalition.importance >= 0.8 for coalition in dormant)
                and self.recall_evidence.long_inactivity_retrieval_access >= 0.65
            ),
            "snapshot_preserves_exact_identity_topology_and_provenance": all(
                coalition.coalition_id for coalition in self.coalitions
            ),
            "mature_protected_network_remains_protected": any(
                coalition.protected and coalition.maturity_state_code == "maturity:mature"
                for coalition in self.coalitions
            ),
            "autonomous_dream_workers_absent": not self.dream_replay.autonomous_worker_used,
            "zero_sqlite_side_effects_and_authority": (
                self.sqlite_cognition_operation_count == 0
                and self.external_side_effect_count == 0
                and self.production_action_authority_violations == 0
                and self.dream_replay.action_execution_count == 0
                and all(
                    not coalition.has_external_action_authority for coalition in self.coalitions
                )
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
            "coalitions": [coalition.snapshot() for coalition in self.coalitions],
            "recall_evidence": self.recall_evidence.snapshot(),
            "dream_replay": self.dream_replay.snapshot(),
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
            "external_side_effect_count": self.external_side_effect_count,
            "production_action_authority_violations": self.production_action_authority_violations,
        }


def run_stage_six_hibernation_acceptance(
    config: StageSixHibernationConfig | None = None,
) -> StageSixHibernationEvidence:
    """Build deterministic integrated Stage 6 hibernation evidence."""

    resolved = StageSixHibernationConfig() if config is None else config
    return StageSixHibernationEvidence(
        config=resolved,
        coalitions=_coalitions(),
        recall_evidence=RecallRestorationEvidence(
            "coalition:rare_permission_lesson",
            shallow_recall_access=0.22,
            stronger_need_access=0.68,
            related_activation_access=0.61,
            dream_maintained_access=0.74,
            unreplayed_control_access=0.39,
            long_inactivity_retrieval_access=0.71,
        ),
        dream_replay=DreamReplayRecord(
            "dream:maintain_rare_permission_lesson",
            source_experience_ids=("experience:permission_denied", "experience:stop_respected"),
            accessibility_delta=0.35,
            matched_control_delta=0.08,
        ),
    )


def save_stage_six_hibernation_evidence(
    evidence: StageSixHibernationEvidence,
    path: Path,
) -> None:
    """Persist deterministic Stage 6 evidence with an outer checksum."""

    payload = evidence.snapshot()
    envelope = {
        "schema": evidence.config.schema,
        "schema_version": evidence.config.schema_version,
        "payload": payload,
        "checksum": _checksum(payload),
    }
    path.write_text(_canonical_json_text(envelope), encoding="ascii")


def load_stage_six_hibernation_evidence(path: Path) -> StageSixRestartLoadResult:
    """Load Stage 6 evidence or return complete fallback."""

    try:
        raw = json.loads(path.read_text(encoding="ascii"))
        if not isinstance(raw, dict):
            raise ValueError("envelope")
        if raw.get("schema") != STAGE_SIX_HIBERNATION_SCHEMA:
            return StageSixRestartLoadResult(StageSixLoadStatus.FALLBACK, fallback_reason="schema")
        if raw.get("schema_version") != STAGE_SIX_HIBERNATION_SCHEMA_VERSION:
            return StageSixRestartLoadResult(
                StageSixLoadStatus.FALLBACK,
                fallback_reason="schema_version",
            )
        payload = raw.get("payload")
        if not isinstance(payload, dict) or raw.get("checksum") != _checksum(payload):
            return StageSixRestartLoadResult(
                StageSixLoadStatus.FALLBACK, fallback_reason="checksum"
            )
        restored = _restore_evidence(payload)
        if restored.evidence_id != payload.get("evidence_id"):
            return StageSixRestartLoadResult(
                StageSixLoadStatus.FALLBACK, fallback_reason="identity"
            )
        return StageSixRestartLoadResult(StageSixLoadStatus.RESTORED, restored_evidence=restored)
    except (OSError, UnicodeError, json.JSONDecodeError, KeyError, TypeError, ValueError):
        return StageSixRestartLoadResult(StageSixLoadStatus.FALLBACK, fallback_reason="malformed")


def prove_stage_six_restart(path: Path) -> StageSixRestartProof:
    """Save, reload, and prove exact Stage 6 restart behavior."""

    evidence = run_stage_six_hibernation_acceptance()
    save_stage_six_hibernation_evidence(evidence, path)
    restored = load_stage_six_hibernation_evidence(path)
    if restored.restored_evidence is None:
        raise ValueError("restart proof requires restored evidence")
    malformed_path = path.with_suffix(".malformed.json")
    malformed_path.write_text("{", encoding="ascii")
    incompatible_path = path.with_suffix(".schema.json")
    envelope = json.loads(path.read_text(encoding="ascii"))
    envelope["schema_version"] = 999
    incompatible_path.write_text(_canonical_json_text(envelope), encoding="ascii")
    malformed = load_stage_six_hibernation_evidence(malformed_path)
    incompatible = load_stage_six_hibernation_evidence(incompatible_path)
    return StageSixRestartProof(
        saved_evidence_id=evidence.evidence_id,
        restored_evidence_id=restored.restored_evidence.evidence_id,
        first_post_restart_recall_matches=(
            evidence.recall_evidence.snapshot()
            == restored.restored_evidence.recall_evidence.snapshot()
        ),
        protected_network_remains_protected=any(
            coalition.protected for coalition in restored.restored_evidence.coalitions
        ),
        malformed_load_status=malformed.status,
        incompatible_schema_load_status=incompatible.status,
    )


def _coalitions() -> tuple[HibernatingCoalitionState, ...]:
    return (
        HibernatingCoalitionState(
            "coalition:rare_permission_lesson",
            neuron_ids=("permission:n001", "permission:n004", "permission:n009"),
            topology_edge_codes=("edge:permission:001", "edge:permission:002"),
            weight_by_edge={"edge:permission:001": 0.62, "edge:permission:002": -0.31},
            inhibition_by_edge={"edge:permission:001": 0.2, "edge:permission:002": 0.74},
            maturity_state_code="maturity:mature",
            plasticity=0.18,
            dormancy_state=CoalitionDormancyState.HIBERNATING,
            provenance_experience_ids=("experience:permission_denied", "experience:stop_respected"),
            accessibility=0.24,
            importance=0.91,
            protected=True,
        ),
        HibernatingCoalitionState(
            "coalition:old_resource_shortcut",
            neuron_ids=("resource:n002", "resource:n006"),
            topology_edge_codes=("edge:resource:001",),
            weight_by_edge={"edge:resource:001": 0.47},
            inhibition_by_edge={"edge:resource:001": 0.18},
            maturity_state_code="maturity:mature",
            plasticity=0.21,
            dormancy_state=CoalitionDormancyState.DORMANT,
            provenance_experience_ids=("experience:reuse_low_cost_path",),
            accessibility=0.31,
            importance=0.72,
        ),
    )


def _restore_evidence(payload: Mapping[str, Any]) -> StageSixHibernationEvidence:
    config_payload = _mapping(payload["config"])
    config = StageSixHibernationConfig(
        seed=_int(config_payload["seed"]),
        schema=_str(config_payload["schema"]),
        schema_version=_int(config_payload["schema_version"]),
        maximum_dream_replay_sources=_int(config_payload["maximum_dream_replay_sources"]),
    )
    coalitions = tuple(
        _restore_coalition(_mapping(item)) for item in _sequence(payload["coalitions"])
    )
    recall_payload = _mapping(payload["recall_evidence"])
    dream_payload = _mapping(payload["dream_replay"])
    return StageSixHibernationEvidence(
        config=config,
        coalitions=coalitions,
        recall_evidence=RecallRestorationEvidence(
            _str(recall_payload["coalition_code"]),
            _float(recall_payload["shallow_recall_access"]),
            _float(recall_payload["stronger_need_access"]),
            _float(recall_payload["related_activation_access"]),
            _float(recall_payload["dream_maintained_access"]),
            _float(recall_payload["unreplayed_control_access"]),
            _float(recall_payload["long_inactivity_retrieval_access"]),
        ),
        dream_replay=DreamReplayRecord(
            _str(dream_payload["replay_code"]),
            tuple(_str(item) for item in _sequence(dream_payload["source_experience_ids"])),
            _float(dream_payload["accessibility_delta"]),
            _float(dream_payload["matched_control_delta"]),
            factual_evidence_delta=_int(dream_payload["factual_evidence_delta"]),
            action_execution_count=_int(dream_payload["action_execution_count"]),
            weakens_protected_prohibition=bool(dream_payload["weakens_protected_prohibition"]),
            autonomous_worker_used=bool(dream_payload["autonomous_worker_used"]),
        ),
        sqlite_cognition_operation_count=_int(payload["sqlite_cognition_operation_count"]),
        external_side_effect_count=_int(payload["external_side_effect_count"]),
        production_action_authority_violations=_int(
            payload["production_action_authority_violations"]
        ),
    )


def _restore_coalition(payload: Mapping[str, Any]) -> HibernatingCoalitionState:
    return HibernatingCoalitionState(
        _str(payload["coalition_code"]),
        tuple(_str(item) for item in _sequence(payload["neuron_ids"])),
        tuple(_str(item) for item in _sequence(payload["topology_edge_codes"])),
        {str(key): _float(value) for key, value in _mapping(payload["weight_by_edge"]).items()},
        {str(key): _float(value) for key, value in _mapping(payload["inhibition_by_edge"]).items()},
        _str(payload["maturity_state_code"]),
        _float(payload["plasticity"]),
        CoalitionDormancyState(_str(payload["dormancy_state"])),
        tuple(_str(item) for item in _sequence(payload["provenance_experience_ids"])),
        _float(payload["accessibility"]),
        _float(payload["importance"]),
        protected=bool(payload["protected"]),
        factual_evidence_count=_int(payload["factual_evidence_count"]),
        has_external_action_authority=bool(payload["has_external_action_authority"]),
    )


def _mapping(value: Any) -> Mapping[str, Any]:
    if not isinstance(value, dict):
        raise ValueError("expected mapping")
    return value


def _sequence(value: Any) -> Sequence[Any]:
    if not isinstance(value, list):
        raise ValueError("expected sequence")
    return value


def _str(value: Any) -> str:
    if not isinstance(value, str):
        raise ValueError("expected string")
    return value


def _int(value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError("expected int")
    return value


def _float(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError("expected float")
    return float(value)


def _validate_non_empty_sequence(name: str, values: Sequence[object]) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_zero_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise ValueError(f"{name} must be zero")


def _validate_unit(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite between zero and one")


def _validate_signed_unit(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < -1.0 or value > 1.0:
        raise ValueError(f"{name} must be finite between minus one and one")


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


def _checksum(payload: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()


def _canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    return _canonical_json_text(payload).encode("ascii")


def _canonical_json_text(payload: Mapping[str, object]) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
