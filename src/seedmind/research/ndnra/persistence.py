"""Versioned non-SQL persistence for reconstructing an NDNRA brain graph."""

from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Callable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite
from pathlib import Path

from seedmind.research.ndnra.composition import (
    ExperienceAssembly,
    MultidimensionalExperienceGraph,
    SpecialistInteraction,
)
from seedmind.research.ndnra.consolidation_execution_persistence import (
    NDNRAExecutionCheckpoint,
)
from seedmind.research.ndnra.consolidation_persistence import (
    ConsolidationRollbackAuditRecord,
    NDNRAConsolidationCheckpoint,
)
from seedmind.research.ndnra.consolidation_proposal_persistence import (
    NDNRAProposalLifecycleCheckpoint,
)
from seedmind.research.ndnra.contextual_memory import ContextualExperienceLedger
from seedmind.research.ndnra.controlled_replay_restoration_persistence import (
    NDNRAReplayRestorationCheckpoint,
)
from seedmind.research.ndnra.effects import LocalEffectLink, SparseEffectMemory

BRAIN_SCHEMA = "seedmind.ndnra.brain"
BRAIN_SCHEMA_VERSION = 6
_SUPPORTED_SCHEMA_VERSIONS = frozenset({1, 2, 3, 4, 5, BRAIN_SCHEMA_VERSION})

__all__ = [
    "BRAIN_SCHEMA",
    "BRAIN_SCHEMA_VERSION",
    "BrainLoadResult",
    "BrainLoadStatus",
    "BrainSaveResult",
    "ConsolidationRollbackAuditRecord",
    "NDNRABrainStore",
    "NDNRAConsolidationCheckpoint",
    "NDNRAExecutionCheckpoint",
    "NDNRAGrowthState",
    "NDNRAProposalLifecycleCheckpoint",
    "NDNRAReplayRestorationCheckpoint",
]


class BrainLoadStatus(StrEnum):
    """Outcome of loading persistent local graph state."""

    LOADED = "loaded"
    MISSING_FALLBACK = "missing_fallback"
    CORRUPT_FALLBACK = "corrupt_fallback"
    INCOMPATIBLE_FALLBACK = "incompatible_fallback"


@dataclass(frozen=True, slots=True)
class NDNRAGrowthState:
    """Optional bounded structural-growth metadata preserved across restarts."""

    pressure: float = 0.0
    eligibility: tuple[tuple[str, float], ...] = ()
    residuals: tuple[float, ...] = ()
    attempt_count: int = 0
    last_active_members: tuple[str, ...] = ()
    dormancy_levels: tuple[tuple[str, float], ...] = ()

    def __post_init__(self) -> None:
        _validate_unit("pressure", self.pressure)
        if self.attempt_count < 0:
            raise ValueError("attempt_count must not be negative")
        eligibility_ids = tuple(assembly_id for assembly_id, _ in self.eligibility)
        if len(eligibility_ids) != len(set(eligibility_ids)):
            raise ValueError("eligibility assembly identifiers must be unique")
        for assembly_id, trace in self.eligibility:
            _validate_code("eligibility assembly_id", assembly_id)
            _validate_unit("eligibility trace", trace)
        for residual in self.residuals:
            _validate_signed("residual", residual)
        if len(self.last_active_members) != len(set(self.last_active_members)):
            raise ValueError("last_active_members must be unique")
        for assembly_id in self.last_active_members:
            _validate_code("last_active_members", assembly_id)
        dormancy_ids = tuple(structure_id for structure_id, _ in self.dormancy_levels)
        if len(dormancy_ids) != len(set(dormancy_ids)):
            raise ValueError("dormancy structure identifiers must be unique")
        for structure_id, dormancy in self.dormancy_levels:
            _validate_code("dormancy structure_id", structure_id)
            _validate_unit("dormancy level", dormancy)

    def snapshot(self) -> dict[str, object]:
        """Return deterministic inspectable growth metadata."""
        return {
            "pressure": self.pressure,
            "eligibility": [
                {"assembly_id": assembly_id, "trace": trace}
                for assembly_id, trace in self.eligibility
            ],
            "residuals": list(self.residuals),
            "attempt_count": self.attempt_count,
            "last_active_members": list(self.last_active_members),
            "dormancy_levels": [
                {"structure_id": structure_id, "level": level}
                for structure_id, level in self.dormancy_levels
            ],
        }

    @classmethod
    def from_snapshot(cls, snapshot: object) -> NDNRAGrowthState:
        """Restore validated growth metadata without triggering growth."""
        values = _require_mapping("growth state", snapshot)
        raw_eligibility = _require_list(values, "eligibility")
        eligibility: list[tuple[str, float]] = []
        for raw_item in raw_eligibility:
            item = _require_mapping("eligibility item", raw_item)
            eligibility.append(
                (
                    _require_string(item, "assembly_id"),
                    _require_float(item, "trace"),
                )
            )
        raw_dormancy = _require_list(values, "dormancy_levels")
        dormancy_levels: list[tuple[str, float]] = []
        for raw_item in raw_dormancy:
            item = _require_mapping("dormancy item", raw_item)
            dormancy_levels.append(
                (
                    _require_string(item, "structure_id"),
                    _require_float(item, "level"),
                )
            )
        return cls(
            pressure=_require_float(values, "pressure"),
            eligibility=tuple(eligibility),
            residuals=tuple(_require_numeric_list(values, "residuals")),
            attempt_count=_require_int(values, "attempt_count"),
            last_active_members=tuple(_require_string_list(values, "last_active_members")),
            dormancy_levels=tuple(dormancy_levels),
        )


@dataclass(frozen=True, slots=True)
class BrainSaveResult:
    """Evidence from one completed atomic brain-state write."""

    path: Path
    checksum: str
    state_checksum: str
    schema: str
    schema_version: int
    byte_count: int
    temporary_file_remaining: bool


@dataclass(frozen=True, slots=True)
class BrainLoadResult:
    """Loaded brain state or a safe fresh-graph fallback."""

    status: BrainLoadStatus
    graph: MultidimensionalExperienceGraph
    growth_state: NDNRAGrowthState
    consolidation_checkpoint: NDNRAConsolidationCheckpoint
    proposal_lifecycle_checkpoint: NDNRAProposalLifecycleCheckpoint
    execution_checkpoint: NDNRAExecutionCheckpoint
    replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint
    checksum_verified: bool
    used_fallback: bool
    checksum: str | None = None
    state_checksum: str | None = None
    schema_version: int | None = None
    migrated_from_version: int | None = None
    error: str | None = None


class NDNRABrainStore:
    """Persist and restore local graph state without cognitive database lookup."""

    def __init__(self, path: Path) -> None:
        if not path.name:
            raise ValueError("brain-state path must identify a file")
        self.path = path

    @property
    def temporary_path(self) -> Path:
        return self.path.with_name(f"{self.path.name}.tmp")

    def save(
        self,
        graph: MultidimensionalExperienceGraph,
        *,
        growth_state: NDNRAGrowthState | None = None,
        consolidation_checkpoint: NDNRAConsolidationCheckpoint | None = None,
        proposal_lifecycle_checkpoint: NDNRAProposalLifecycleCheckpoint | None = None,
        execution_checkpoint: NDNRAExecutionCheckpoint | None = None,
        replay_restoration_checkpoint: NDNRAReplayRestorationCheckpoint | None = None,
        interruption_hook: Callable[[str], None] | None = None,
    ) -> BrainSaveResult:
        """Atomically save a checksum-protected reconstruction snapshot."""
        growth = NDNRAGrowthState() if growth_state is None else growth_state
        consolidation = (
            NDNRAConsolidationCheckpoint.empty()
            if consolidation_checkpoint is None
            else consolidation_checkpoint
        )
        proposal_lifecycle = (
            NDNRAProposalLifecycleCheckpoint.empty()
            if proposal_lifecycle_checkpoint is None
            else proposal_lifecycle_checkpoint
        )
        execution = (
            NDNRAExecutionCheckpoint.empty()
            if execution_checkpoint is None
            else execution_checkpoint
        )
        replay_restoration = (
            NDNRAReplayRestorationCheckpoint.empty()
            if replay_restoration_checkpoint is None
            else replay_restoration_checkpoint
        )
        execution.validate_consolidation_checkpoint(consolidation)
        state_payload: dict[str, object] = {
            "graph": graph.snapshot(),
            "growth_state": growth.snapshot(),
            "consolidation_checkpoint": consolidation.snapshot(),
            "proposal_lifecycle_checkpoint": proposal_lifecycle.snapshot(),
            "execution_checkpoint": execution.snapshot(),
            "replay_restoration_active_state": (replay_restoration.active_state_snapshot()),
        }
        state_checksum = _checksum(state_payload)
        payload: dict[str, object] = {
            "graph": state_payload["graph"],
            "growth_state": state_payload["growth_state"],
            "consolidation_checkpoint": state_payload["consolidation_checkpoint"],
            "proposal_lifecycle_checkpoint": state_payload["proposal_lifecycle_checkpoint"],
            "execution_checkpoint": state_payload["execution_checkpoint"],
            "replay_restoration_checkpoint": replay_restoration.snapshot(),
        }
        body: dict[str, object] = {
            "schema": BRAIN_SCHEMA,
            "schema_version": BRAIN_SCHEMA_VERSION,
            "state_checksum": state_checksum,
            "payload": payload,
        }
        checksum = _checksum(body)
        envelope = {**body, "checksum": checksum}
        encoded = (
            json.dumps(
                envelope,
                ensure_ascii=True,
                indent=2,
                sort_keys=True,
            )
            + "\n"
        ).encode("ascii")

        self.path.parent.mkdir(parents=True, exist_ok=True)
        try:
            _interrupt(interruption_hook, "before_temporary_write")
            with self.temporary_path.open("wb") as handle:
                midpoint = len(encoded) // 2
                handle.write(encoded[:midpoint])
                _interrupt(interruption_hook, "during_temporary_write")
                handle.write(encoded[midpoint:])
                handle.flush()
                os.fsync(handle.fileno())
            _interrupt(interruption_hook, "after_temporary_write")
            _interrupt(interruption_hook, "before_atomic_replace")
            self.temporary_path.replace(self.path)
            _interrupt(interruption_hook, "after_atomic_replace")
        finally:
            if self.temporary_path.exists():
                self.temporary_path.unlink()

        return BrainSaveResult(
            path=self.path,
            checksum=checksum,
            state_checksum=state_checksum,
            schema=BRAIN_SCHEMA,
            schema_version=BRAIN_SCHEMA_VERSION,
            byte_count=len(encoded),
            temporary_file_remaining=self.temporary_path.exists(),
        )

    def load(self) -> BrainLoadResult:
        """Reconstruct local state or safely return a fresh graph fallback."""
        if not self.path.exists():
            return self._fallback(BrainLoadStatus.MISSING_FALLBACK, "state file is missing")
        try:
            raw = json.loads(self.path.read_text(encoding="ascii"))
            envelope = _require_mapping("brain envelope", raw)
            schema = _require_string(envelope, "schema")
            version = _require_int(envelope, "schema_version")
            if schema != BRAIN_SCHEMA or version not in _SUPPORTED_SCHEMA_VERSIONS:
                return self._fallback(
                    BrainLoadStatus.INCOMPATIBLE_FALLBACK,
                    "brain-state schema is incompatible",
                )
            stored_checksum = _require_string(envelope, "checksum")
            stored_state_checksum = (
                None if version < 6 else _require_string(envelope, "state_checksum")
            )
            body: dict[str, object] = {
                "schema": schema,
                "schema_version": version,
                "payload": envelope.get("payload"),
            }
            if stored_state_checksum is not None:
                body["state_checksum"] = stored_state_checksum
            if not hashlib.sha256(_canonical_bytes(body)).hexdigest() == stored_checksum:
                raise ValueError("brain-state checksum does not match")
            payload = _require_mapping("brain payload", envelope.get("payload"))
            graph = _restore_graph(payload.get("graph"), schema_version=version)
            growth_state = NDNRAGrowthState.from_snapshot(payload.get("growth_state"))
            consolidation_checkpoint = (
                NDNRAConsolidationCheckpoint.empty()
                if version < 3
                else NDNRAConsolidationCheckpoint.from_snapshot(
                    payload.get("consolidation_checkpoint")
                )
            )
            proposal_lifecycle_checkpoint = (
                NDNRAProposalLifecycleCheckpoint.empty()
                if version < 4
                else NDNRAProposalLifecycleCheckpoint.from_snapshot(
                    payload.get("proposal_lifecycle_checkpoint")
                )
            )
            execution_checkpoint = (
                NDNRAExecutionCheckpoint.empty()
                if version < 5
                else NDNRAExecutionCheckpoint.from_snapshot(payload.get("execution_checkpoint"))
            )
            replay_restoration_checkpoint = (
                NDNRAReplayRestorationCheckpoint.empty()
                if version < 6
                else NDNRAReplayRestorationCheckpoint.from_snapshot(
                    payload.get("replay_restoration_checkpoint")
                )
            )
            execution_checkpoint.validate_consolidation_checkpoint(consolidation_checkpoint)
            if stored_state_checksum is not None:
                restored_state_checksum = _checksum(
                    {
                        "graph": graph.snapshot(),
                        "growth_state": growth_state.snapshot(),
                        "consolidation_checkpoint": consolidation_checkpoint.snapshot(),
                        "proposal_lifecycle_checkpoint": (proposal_lifecycle_checkpoint.snapshot()),
                        "execution_checkpoint": execution_checkpoint.snapshot(),
                        "replay_restoration_active_state": (
                            replay_restoration_checkpoint.active_state_snapshot()
                        ),
                    }
                )
                if restored_state_checksum != stored_state_checksum:
                    raise ValueError("brain active-state checksum does not match")
            return BrainLoadResult(
                status=BrainLoadStatus.LOADED,
                graph=graph,
                growth_state=growth_state,
                consolidation_checkpoint=consolidation_checkpoint,
                proposal_lifecycle_checkpoint=proposal_lifecycle_checkpoint,
                execution_checkpoint=execution_checkpoint,
                replay_restoration_checkpoint=replay_restoration_checkpoint,
                checksum_verified=True,
                used_fallback=False,
                checksum=stored_checksum,
                state_checksum=stored_state_checksum,
                schema_version=version,
                migrated_from_version=(version if version < BRAIN_SCHEMA_VERSION else None),
            )
        except (OSError, UnicodeError, json.JSONDecodeError, ValueError) as error:
            return self._fallback(BrainLoadStatus.CORRUPT_FALLBACK, str(error))

    @staticmethod
    def _fallback(status: BrainLoadStatus, error: str) -> BrainLoadResult:
        return BrainLoadResult(
            status=status,
            graph=MultidimensionalExperienceGraph(),
            growth_state=NDNRAGrowthState(),
            consolidation_checkpoint=NDNRAConsolidationCheckpoint.empty(),
            proposal_lifecycle_checkpoint=NDNRAProposalLifecycleCheckpoint.empty(),
            execution_checkpoint=NDNRAExecutionCheckpoint.empty(),
            replay_restoration_checkpoint=NDNRAReplayRestorationCheckpoint.empty(),
            checksum_verified=False,
            used_fallback=True,
            checksum=None,
            state_checksum=None,
            schema_version=None,
            migrated_from_version=None,
            error=error,
        )


def _interrupt(
    hook: Callable[[str], None] | None,
    point: str,
) -> None:
    if hook is not None:
        hook(point)


def _restore_graph(
    snapshot: object,
    *,
    schema_version: int,
) -> MultidimensionalExperienceGraph:
    values = _require_mapping("graph snapshot", snapshot)
    assemblies = tuple(_restore_assembly(item) for item in _require_list(values, "assemblies"))
    links = tuple(LocalEffectLink.from_snapshot(item) for item in _require_list(values, "links"))
    specialists = tuple(_restore_specialist(item) for item in _require_list(values, "specialists"))
    contextual_memory = (
        ContextualExperienceLedger()
        if schema_version == 1
        else ContextualExperienceLedger.from_snapshot(values.get("contextual_memory"))
    )
    graph = MultidimensionalExperienceGraph.from_components(
        assemblies=assemblies,
        links=links,
        specialists=specialists,
        contextual_memory=contextual_memory,
    )
    restored = graph.snapshot()
    if schema_version == 1:
        restored.pop("contextual_memory")
    if restored != dict(values):
        raise ValueError("restored graph does not exactly match persisted state")
    return graph


def _restore_assembly(snapshot: object) -> ExperienceAssembly:
    values = _require_mapping("experience assembly", snapshot)
    return ExperienceAssembly(
        assembly_id=_require_string(values, "assembly_id"),
        action_code=_require_string(values, "action_code"),
        origin_need_code=_require_string(values, "origin_need_code"),
        required_facts=frozenset(_require_string_list(values, "required_facts")),
        produced_facts=frozenset(_require_string_list(values, "produced_facts")),
        effect_memory=SparseEffectMemory.from_snapshot(values.get("effect_memory")),
        evidence_count=_require_int(values, "evidence_count"),
    )


def _restore_specialist(snapshot: object) -> SpecialistInteraction:
    values = _require_mapping("specialist interaction", snapshot)
    return SpecialistInteraction(
        specialist_id=_require_string(values, "specialist_id"),
        member_assembly_ids=tuple(_require_string_list(values, "member_assembly_ids")),
        origin_code=_require_string(values, "origin_code"),
        effect_memory=SparseEffectMemory.from_snapshot(values.get("effect_memory")),
        evidence_count=_require_int(values, "evidence_count"),
    )


def _checksum(body: Mapping[str, object]) -> str:
    return hashlib.sha256(_canonical_bytes(body)).hexdigest()


def _canonical_bytes(body: Mapping[str, object]) -> bytes:
    return json.dumps(
        body,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("ascii")


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


def _require_string_list(values: Mapping[str, object], key: str) -> list[str]:
    result: list[str] = []
    for item in _require_list(values, key):
        if not isinstance(item, str):
            raise ValueError(f"{key} must contain strings")
        result.append(item)
    return result


def _require_numeric_list(values: Mapping[str, object], key: str) -> list[float]:
    result: list[float] = []
    for item in _require_list(values, key):
        if isinstance(item, bool) or not isinstance(item, int | float):
            raise ValueError(f"{key} must contain numbers")
        result.append(float(item))
    return result


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between zero and one")


def _validate_signed(name: str, value: float) -> None:
    if not isfinite(value) or not -1.0 <= value <= 1.0:
        raise ValueError(f"{name} must be between negative one and one")
