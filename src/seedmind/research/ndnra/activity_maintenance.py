"""Bounded memory accessibility maintenance from real, replayed, or imagined activity."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping
from dataclasses import dataclass, field
from math import isfinite

from seedmind.research.ndnra.contextual_consequence import ExperienceOrigin


@dataclass(frozen=True, slots=True)
class ActivityMaintenanceConfig:
    """Strengths and budgets for non-evidentiary accessibility maintenance."""

    real_strength: float = 0.60
    replay_strength: float = 0.30
    imagined_strength: float = 0.10
    safety_critical_floor: float = 0.20
    rare_use_floor: float = 0.15
    minimum_replay_real_evidence: float = 0.25
    minimum_imagined_real_evidence: float = 0.50
    maximum_structures_per_event: int = 8
    maximum_events_per_cycle: int = 8
    maximum_total_reactivation_per_cycle: float = 2.0

    def __post_init__(self) -> None:
        for name, value in (
            ("real_strength", self.real_strength),
            ("replay_strength", self.replay_strength),
            ("imagined_strength", self.imagined_strength),
            ("safety_critical_floor", self.safety_critical_floor),
            ("rare_use_floor", self.rare_use_floor),
            ("minimum_replay_real_evidence", self.minimum_replay_real_evidence),
            ("minimum_imagined_real_evidence", self.minimum_imagined_real_evidence),
        ):
            _validate_unit(name, value)
        if not self.real_strength > self.replay_strength > self.imagined_strength:
            raise ValueError("activity strengths must satisfy real > replay > imagined")
        for name, value in (
            ("maximum_structures_per_event", self.maximum_structures_per_event),
            ("maximum_events_per_cycle", self.maximum_events_per_cycle),
        ):
            if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if (
            not isfinite(self.maximum_total_reactivation_per_cycle)
            or self.maximum_total_reactivation_per_cycle <= 0.0
        ):
            raise ValueError("maximum_total_reactivation_per_cycle must be finite and positive")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic maintenance policy evidence."""
        return {
            "real_strength": self.real_strength,
            "replay_strength": self.replay_strength,
            "imagined_strength": self.imagined_strength,
            "safety_critical_floor": self.safety_critical_floor,
            "rare_use_floor": self.rare_use_floor,
            "minimum_replay_real_evidence": self.minimum_replay_real_evidence,
            "minimum_imagined_real_evidence": self.minimum_imagined_real_evidence,
            "maximum_structures_per_event": self.maximum_structures_per_event,
            "maximum_events_per_cycle": self.maximum_events_per_cycle,
            "maximum_total_reactivation_per_cycle": (self.maximum_total_reactivation_per_cycle),
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ActivityMaintenanceConfig:
        """Restore exact policy values without applying maintenance."""
        values = _require_mapping("activity maintenance config", snapshot)
        config = cls(
            real_strength=_require_float(values, "real_strength"),
            replay_strength=_require_float(values, "replay_strength"),
            imagined_strength=_require_float(values, "imagined_strength"),
            safety_critical_floor=_require_float(values, "safety_critical_floor"),
            rare_use_floor=_require_float(values, "rare_use_floor"),
            minimum_replay_real_evidence=_require_float(values, "minimum_replay_real_evidence"),
            minimum_imagined_real_evidence=_require_float(values, "minimum_imagined_real_evidence"),
            maximum_structures_per_event=_require_int(values, "maximum_structures_per_event"),
            maximum_events_per_cycle=_require_int(values, "maximum_events_per_cycle"),
            maximum_total_reactivation_per_cycle=_require_float(
                values, "maximum_total_reactivation_per_cycle"
            ),
        )
        if config.snapshot() != dict(values):
            raise ValueError("activity maintenance config did not round-trip exactly")
        return config


@dataclass(frozen=True, slots=True)
class ActivityMaintenanceRequest:
    """One activity occurrence requesting accessibility maintenance only."""

    event_id: str
    cycle: int
    origin: ExperienceOrigin
    structure_ids: tuple[str, ...]
    supporting_real_event_ids: tuple[str, ...]
    relevance: float
    helpfulness: float
    prediction_accuracy: float
    real_evidence_strength: float
    safety_critical: bool = False
    rare_use: bool = False
    harmful: bool = False
    redundant: bool = False
    factual_confidence_delta: float = 0.0
    mastery_delta: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("event_id", self.event_id)
        if isinstance(self.cycle, bool) or not isinstance(self.cycle, int) or self.cycle < 0:
            raise ValueError("cycle must be a non-negative integer")
        _validate_sorted_unique_codes("structure_ids", self.structure_ids)
        if not self.structure_ids:
            raise ValueError("structure_ids must not be empty")
        _validate_sorted_unique_codes(
            "supporting_real_event_ids",
            self.supporting_real_event_ids,
        )
        for name, value in (
            ("relevance", self.relevance),
            ("helpfulness", self.helpfulness),
            ("prediction_accuracy", self.prediction_accuracy),
            ("real_evidence_strength", self.real_evidence_strength),
        ):
            _validate_unit(name, value)
        if self.origin is ExperienceOrigin.REAL:
            if self.supporting_real_event_ids:
                raise ValueError("real activity cannot cite separate supporting real events")
            if self.real_evidence_strength == 0.0:
                raise ValueError("real activity requires non-zero real evidence strength")
        elif not self.supporting_real_event_ids:
            raise ValueError("replay and imagined activity require supporting real events")
        if self.factual_confidence_delta != 0.0:
            raise ValueError("activity maintenance cannot change factual confidence")
        if self.mastery_delta != 0.0:
            raise ValueError("activity maintenance cannot change mastery")
        if self.has_action_selection_authority:
            raise ValueError("activity maintenance cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("activity maintenance cannot control production actions")

    def snapshot(self) -> dict[str, object]:
        """Return deterministic request evidence."""
        return {
            "event_id": self.event_id,
            "cycle": self.cycle,
            "origin": self.origin.value,
            "structure_ids": list(self.structure_ids),
            "supporting_real_event_ids": list(self.supporting_real_event_ids),
            "relevance": self.relevance,
            "helpfulness": self.helpfulness,
            "prediction_accuracy": self.prediction_accuracy,
            "real_evidence_strength": self.real_evidence_strength,
            "safety_critical": self.safety_critical,
            "rare_use": self.rare_use,
            "harmful": self.harmful,
            "redundant": self.redundant,
            "factual_confidence_delta": self.factual_confidence_delta,
            "mastery_delta": self.mastery_delta,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ActivityMaintenanceRequest:
        """Restore one exact source-labelled activity occurrence."""
        values = _require_mapping("activity maintenance request", snapshot)
        request = cls(
            event_id=_require_string(values, "event_id"),
            cycle=_require_int(values, "cycle"),
            origin=ExperienceOrigin(_require_string(values, "origin")),
            structure_ids=tuple(_require_string_list(values, "structure_ids")),
            supporting_real_event_ids=tuple(
                _require_string_list(values, "supporting_real_event_ids")
            ),
            relevance=_require_float(values, "relevance"),
            helpfulness=_require_float(values, "helpfulness"),
            prediction_accuracy=_require_float(values, "prediction_accuracy"),
            real_evidence_strength=_require_float(values, "real_evidence_strength"),
            safety_critical=_require_bool(values, "safety_critical"),
            rare_use=_require_bool(values, "rare_use"),
            harmful=_require_bool(values, "harmful"),
            redundant=_require_bool(values, "redundant"),
            factual_confidence_delta=_require_float(values, "factual_confidence_delta"),
            mastery_delta=_require_float(values, "mastery_delta"),
            has_action_selection_authority=_require_bool(values, "has_action_selection_authority"),
            has_production_action_authority=_require_bool(
                values, "has_production_action_authority"
            ),
        )
        if request.snapshot() != dict(values):
            raise ValueError("activity maintenance request did not round-trip exactly")
        return request


@dataclass(frozen=True, slots=True)
class ActivityMaintenanceDecision:
    """One bounded decision that may only reduce dormancy."""

    decision_id: str
    request: ActivityMaintenanceRequest
    requested_strength: float
    granted_strength: float
    per_structure_reactivation: float
    reason_code: str
    evidence_applied: bool
    factual_confidence_delta: float = 0.0
    mastery_delta: float = 0.0
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_code("decision_id", self.decision_id)
        _validate_unit("requested_strength", self.requested_strength)
        _validate_unit("granted_strength", self.granted_strength)
        _validate_unit("per_structure_reactivation", self.per_structure_reactivation)
        _validate_code("reason_code", self.reason_code)
        if self.granted_strength > self.requested_strength:
            raise ValueError("granted strength cannot exceed requested strength")
        if self.per_structure_reactivation != self.granted_strength:
            raise ValueError("per-structure reactivation must equal granted strength")
        if self.factual_confidence_delta != 0.0:
            raise ValueError("maintenance decisions cannot change factual confidence")
        if self.mastery_delta != 0.0:
            raise ValueError("maintenance decisions cannot change mastery")
        if self.has_action_selection_authority:
            raise ValueError("maintenance decisions cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("maintenance decisions cannot control production actions")
        expected_id = _decision_id(
            request=self.request,
            requested_strength=self.requested_strength,
            granted_strength=self.granted_strength,
            reason_code=self.reason_code,
        )
        if self.decision_id != expected_id:
            raise ValueError("maintenance decision identity is inconsistent")

    @property
    def maintenance_applied(self) -> bool:
        """Return whether this decision grants any dormancy reduction."""
        return self.granted_strength > 0.0 and self.evidence_applied

    @property
    def total_reactivation(self) -> float:
        """Return total granted reactivation across all named structures."""
        return self.per_structure_reactivation * len(self.request.structure_ids)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic non-evidentiary maintenance evidence."""
        return {
            "decision_id": self.decision_id,
            "request": self.request.snapshot(),
            "requested_strength": self.requested_strength,
            "granted_strength": self.granted_strength,
            "per_structure_reactivation": self.per_structure_reactivation,
            "total_reactivation": self.total_reactivation,
            "reason_code": self.reason_code,
            "evidence_applied": self.evidence_applied,
            "maintenance_applied": self.maintenance_applied,
            "factual_confidence_delta": self.factual_confidence_delta,
            "mastery_delta": self.mastery_delta,
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ActivityMaintenanceDecision:
        """Restore exact non-authoritative maintenance evidence."""
        values = _require_mapping("activity maintenance decision", snapshot)
        decision = cls(
            decision_id=_require_string(values, "decision_id"),
            request=ActivityMaintenanceRequest.from_snapshot(values.get("request")),
            requested_strength=_require_float(values, "requested_strength"),
            granted_strength=_require_float(values, "granted_strength"),
            per_structure_reactivation=_require_float(values, "per_structure_reactivation"),
            reason_code=_require_string(values, "reason_code"),
            evidence_applied=_require_bool(values, "evidence_applied"),
            factual_confidence_delta=_require_float(values, "factual_confidence_delta"),
            mastery_delta=_require_float(values, "mastery_delta"),
            has_action_selection_authority=_require_bool(values, "has_action_selection_authority"),
            has_production_action_authority=_require_bool(
                values, "has_production_action_authority"
            ),
        )
        if _require_float(values, "total_reactivation") != decision.total_reactivation:
            raise ValueError("persisted total reactivation is inconsistent")
        if _require_bool(values, "maintenance_applied") is not decision.maintenance_applied:
            raise ValueError("persisted maintenance-applied state is inconsistent")
        if decision.snapshot() != dict(values):
            raise ValueError("activity maintenance decision did not round-trip exactly")
        return decision


@dataclass(slots=True)
class ActivityMaintenanceLedger:
    """Deduplicate activity and enforce per-cycle maintenance budgets."""

    config: ActivityMaintenanceConfig = field(default_factory=ActivityMaintenanceConfig)
    _requests: dict[str, ActivityMaintenanceRequest] = field(default_factory=dict)
    _decisions: dict[str, ActivityMaintenanceDecision] = field(default_factory=dict)
    _events_by_cycle: dict[int, int] = field(default_factory=dict)
    _reactivation_by_cycle: dict[int, float] = field(default_factory=dict)
    has_action_selection_authority: bool = False
    has_production_action_authority: bool = False

    def __post_init__(self) -> None:
        if self.has_action_selection_authority:
            raise ValueError("activity ledger cannot select actions")
        if self.has_production_action_authority:
            raise ValueError("activity ledger cannot control production actions")

    @property
    def event_count(self) -> int:
        return len(self._requests)

    @property
    def real_activity_count(self) -> int:
        return self._count_origin(ExperienceOrigin.REAL)

    @property
    def replay_activity_count(self) -> int:
        return self._count_origin(ExperienceOrigin.REPLAY)

    @property
    def imagined_activity_count(self) -> int:
        return self._count_origin(ExperienceOrigin.IMAGINED)

    def consider(self, request: ActivityMaintenanceRequest) -> ActivityMaintenanceDecision:
        """Return one budgeted decision without creating learning evidence."""
        existing = self._requests.get(request.event_id)
        if existing is not None:
            if existing != request:
                raise ValueError("activity event identity conflict")
            original = self._decisions[request.event_id]
            return ActivityMaintenanceDecision(
                decision_id=_decision_id(
                    request=request,
                    requested_strength=original.requested_strength,
                    granted_strength=0.0,
                    reason_code="exact_duplicate_ignored",
                ),
                request=request,
                requested_strength=original.requested_strength,
                granted_strength=0.0,
                per_structure_reactivation=0.0,
                reason_code="exact_duplicate_ignored",
                evidence_applied=False,
            )

        requested_strength, reason_code = self._requested_strength(request)
        granted_strength = self._budgeted_strength(request, requested_strength)
        if requested_strength > 0.0 and granted_strength == 0.0:
            reason_code = "cycle_budget_exhausted"
        elif 0.0 < granted_strength < requested_strength:
            reason_code = "cycle_budget_limited"
        decision = ActivityMaintenanceDecision(
            decision_id=_decision_id(
                request=request,
                requested_strength=requested_strength,
                granted_strength=granted_strength,
                reason_code=reason_code,
            ),
            request=request,
            requested_strength=requested_strength,
            granted_strength=granted_strength,
            per_structure_reactivation=granted_strength,
            reason_code=reason_code,
            evidence_applied=True,
        )
        self._requests[request.event_id] = request
        self._decisions[request.event_id] = decision
        self._events_by_cycle[request.cycle] = self._events_by_cycle.get(request.cycle, 0) + 1
        self._reactivation_by_cycle[request.cycle] = (
            self._reactivation_by_cycle.get(request.cycle, 0.0) + decision.total_reactivation
        )
        return decision

    def request_for(self, event_id: str) -> ActivityMaintenanceRequest:
        """Return one exact recorded activity request by stable event identity."""
        _validate_code("event_id", event_id)
        try:
            return self._requests[event_id]
        except KeyError as error:
            raise ValueError("unknown activity event identity") from error

    def decision_for(self, event_id: str) -> ActivityMaintenanceDecision:
        """Return the original decision for one unique activity event."""
        _validate_code("event_id", event_id)
        try:
            return self._decisions[event_id]
        except KeyError as error:
            raise ValueError("unknown activity event identity") from error

    def snapshot(self) -> dict[str, object]:
        """Return deterministic source-separated activity evidence."""
        return {
            "config": self.config.snapshot(),
            "event_order": list(self._requests),
            "event_count": self.event_count,
            "real_activity_count": self.real_activity_count,
            "replay_activity_count": self.replay_activity_count,
            "imagined_activity_count": self.imagined_activity_count,
            "events_by_cycle": [
                {"cycle": cycle, "count": self._events_by_cycle[cycle]}
                for cycle in sorted(self._events_by_cycle)
            ],
            "reactivation_by_cycle": [
                {"cycle": cycle, "amount": self._reactivation_by_cycle[cycle]}
                for cycle in sorted(self._reactivation_by_cycle)
            ],
            "decisions": [self._decisions[key].snapshot() for key in sorted(self._decisions)],
            "has_action_selection_authority": self.has_action_selection_authority,
            "has_production_action_authority": self.has_production_action_authority,
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> ActivityMaintenanceLedger:
        """Restore exact activity history by replaying persisted event order."""
        values = _require_mapping("activity maintenance ledger", snapshot)
        config = ActivityMaintenanceConfig.from_snapshot(values.get("config"))
        event_order = tuple(_require_string_list(values, "event_order"))
        if len(event_order) != len(set(event_order)):
            raise ValueError("persisted activity event order must be unique")
        stored_decisions = tuple(
            ActivityMaintenanceDecision.from_snapshot(item)
            for item in _require_list(values, "decisions")
        )
        decision_by_event = {decision.request.event_id: decision for decision in stored_decisions}
        if len(decision_by_event) != len(stored_decisions):
            raise ValueError("persisted activity decisions must have unique events")
        if set(event_order) != set(decision_by_event):
            raise ValueError("persisted event order and decisions must match")

        ledger = cls(config=config)
        for event_id in event_order:
            stored = decision_by_event[event_id]
            restored = ledger.consider(stored.request)
            if restored != stored:
                raise ValueError("persisted activity decision is not reproducible")
        if _require_int(values, "event_count") != ledger.event_count:
            raise ValueError("persisted activity event count is inconsistent")
        if _require_int(values, "real_activity_count") != ledger.real_activity_count:
            raise ValueError("persisted real activity count is inconsistent")
        if _require_int(values, "replay_activity_count") != ledger.replay_activity_count:
            raise ValueError("persisted replay activity count is inconsistent")
        if _require_int(values, "imagined_activity_count") != ledger.imagined_activity_count:
            raise ValueError("persisted imagined activity count is inconsistent")
        if ledger.snapshot() != dict(values):
            raise ValueError("activity maintenance ledger did not round-trip exactly")
        return ledger

    def _requested_strength(
        self,
        request: ActivityMaintenanceRequest,
    ) -> tuple[float, str]:
        if len(request.structure_ids) > self.config.maximum_structures_per_event:
            return 0.0, "structure_budget_exceeded"
        if request.harmful:
            return 0.0, "harmful_pathway_not_maintained"
        if request.redundant:
            return 0.0, "redundant_pathway_not_maintained"
        if request.relevance == 0.0:
            return 0.0, "irrelevant_pathway_not_maintained"
        support_reason = self._support_reason(request)
        if support_reason is not None:
            return 0.0, support_reason
        if (
            request.origin is ExperienceOrigin.REPLAY
            and request.real_evidence_strength < self.config.minimum_replay_real_evidence
        ):
            return 0.0, "insufficient_real_evidence_for_replay"
        if (
            request.origin is ExperienceOrigin.IMAGINED
            and request.real_evidence_strength < self.config.minimum_imagined_real_evidence
        ):
            return 0.0, "insufficient_real_evidence_for_imagination"

        quality = min(
            request.relevance,
            request.helpfulness,
            request.prediction_accuracy,
            request.real_evidence_strength,
        )
        if request.safety_critical:
            quality = max(quality, self.config.safety_critical_floor)
        if request.rare_use:
            quality = max(quality, self.config.rare_use_floor)
        base = {
            ExperienceOrigin.REAL: self.config.real_strength,
            ExperienceOrigin.REPLAY: self.config.replay_strength,
            ExperienceOrigin.IMAGINED: self.config.imagined_strength,
        }[request.origin]
        return base * quality, "maintenance_granted"

    def _support_reason(
        self,
        request: ActivityMaintenanceRequest,
    ) -> str | None:
        if request.origin is ExperienceOrigin.REAL:
            return None
        supported_structures: set[str] = set()
        for event_id in request.supporting_real_event_ids:
            supporting = self._requests.get(event_id)
            if supporting is None or supporting.origin is not ExperienceOrigin.REAL:
                return "supporting_real_activity_missing"
            supported_structures.update(supporting.structure_ids)
        if set(request.structure_ids) - supported_structures:
            return "supporting_real_activity_structure_mismatch"
        return None

    def _budgeted_strength(
        self,
        request: ActivityMaintenanceRequest,
        requested_strength: float,
    ) -> float:
        if requested_strength == 0.0:
            return 0.0
        if self._events_by_cycle.get(request.cycle, 0) >= self.config.maximum_events_per_cycle:
            return 0.0
        used = self._reactivation_by_cycle.get(request.cycle, 0.0)
        remaining = max(0.0, self.config.maximum_total_reactivation_per_cycle - used)
        return min(requested_strength, remaining / len(request.structure_ids))

    def _count_origin(self, origin: ExperienceOrigin) -> int:
        return sum(request.origin is origin for request in self._requests.values())


def _decision_id(
    *,
    request: ActivityMaintenanceRequest,
    requested_strength: float,
    granted_strength: float,
    reason_code: str,
) -> str:
    payload = {
        "request": request.snapshot(),
        "requested_strength": requested_strength,
        "granted_strength": granted_strength,
        "reason_code": reason_code,
    }
    canonical = json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("ascii")
    return f"activity-maintenance-decision:{hashlib.sha256(canonical).hexdigest()}"


def _require_mapping(name: str, value: object) -> Mapping[str, object]:
    if not isinstance(value, dict) or not all(isinstance(key, str) for key in value):
        raise ValueError(f"{name} must be a string-keyed object")
    return value


def _require_list(values: Mapping[str, object], key: str) -> list[object]:
    value = values.get(key)
    if not isinstance(value, list):
        raise ValueError(f"{key} must be a list")
    return value


def _require_string(values: Mapping[str, object], key: str) -> str:
    value = values.get(key)
    if not isinstance(value, str):
        raise ValueError(f"{key} must be a string")
    return value


def _require_int(values: Mapping[str, object], key: str) -> int:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"{key} must be an integer")
    return value


def _require_float(values: Mapping[str, object], key: str) -> float:
    value = values.get(key)
    if isinstance(value, bool) or not isinstance(value, int | float):
        raise ValueError(f"{key} must be numeric")
    return float(value)


def _require_bool(values: Mapping[str, object], key: str) -> bool:
    value = values.get(key)
    if not isinstance(value, bool):
        raise ValueError(f"{key} must be boolean")
    return value


def _require_string_list(values: Mapping[str, object], key: str) -> list[str]:
    result: list[str] = []
    for item in _require_list(values, key):
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain strings")
        result.append(item)
    return result


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
    for value in values:
        _validate_code(name, value)


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")
