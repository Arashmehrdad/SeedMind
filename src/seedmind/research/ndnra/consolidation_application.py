"""Atomic bounded application of eligible NDNRA consolidation proposals."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from math import isfinite

from seedmind.research.ndnra.consolidation import (
    ConsolidationCandidate,
    ConsolidationEligibility,
)


@dataclass(frozen=True, slots=True)
class ConsolidationStructureState:
    """Bounded consolidation state for one assembly or route identity."""

    structure_id: str
    stability: float = 0.0
    plasticity: float = 1.0

    def __post_init__(self) -> None:
        _validate_code("structure_id", self.structure_id)
        _validate_unit("stability", self.stability)
        _validate_unit("plasticity", self.plasticity)


@dataclass(frozen=True, slots=True)
class ConsolidationStateSnapshot:
    """Immutable complete state captured before or after one application."""

    assembly_states: tuple[ConsolidationStructureState, ...]
    route_states: tuple[ConsolidationStructureState, ...]
    applied_candidate_ids: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        _validate_state_collection("assembly_states", self.assembly_states)
        _validate_state_collection("route_states", self.route_states)
        assembly_ids = {state.structure_id for state in self.assembly_states}
        route_ids = {state.structure_id for state in self.route_states}
        if assembly_ids & route_ids:
            raise ValueError("assembly and route identities must not overlap")
        _validate_sorted_unique_codes(
            "applied_candidate_ids",
            self.applied_candidate_ids,
        )

    def assembly_state(self, assembly_id: str) -> ConsolidationStructureState:
        """Return one captured assembly state by exact identity."""
        return _find_state("assembly", assembly_id, self.assembly_states)

    def route_state(self, route_id: str) -> ConsolidationStructureState:
        """Return one captured route state by exact identity."""
        return _find_state("route", route_id, self.route_states)


@dataclass(frozen=True, slots=True)
class ConsolidationApplicationResult:
    """Evidence that one eligible proposal was applied atomically."""

    candidate: ConsolidationCandidate
    before: ConsolidationStateSnapshot
    after: ConsolidationStateSnapshot

    def __post_init__(self) -> None:
        candidate_id = self.candidate.candidate_id
        if candidate_id in self.before.applied_candidate_ids:
            raise ValueError("candidate must not be applied in the before snapshot")
        if candidate_id not in self.after.applied_candidate_ids:
            raise ValueError("candidate must be recorded in the after snapshot")
        if _snapshot_ids(self.before.assembly_states) != _snapshot_ids(self.after.assembly_states):
            raise ValueError("consolidation must preserve all assembly identities")
        if _snapshot_ids(self.before.route_states) != _snapshot_ids(self.after.route_states):
            raise ValueError("consolidation must preserve all route identities")
        if not set(self.candidate.assembly_ids).issubset(_snapshot_ids(self.after.assembly_states)):
            raise ValueError("candidate assemblies must remain present after consolidation")
        if not set(self.candidate.route_ids).issubset(_snapshot_ids(self.after.route_states)):
            raise ValueError("candidate routes must remain present after consolidation")


@dataclass(slots=True)
class ConsolidationApplicationState:
    """Apply approved bounded changes without replay or cognitive authority."""

    _assembly_states: dict[str, ConsolidationStructureState] = field(default_factory=dict)
    _route_states: dict[str, ConsolidationStructureState] = field(default_factory=dict)
    _applied_candidate_ids: set[str] = field(default_factory=set)

    def __post_init__(self) -> None:
        _validate_state_mapping("assembly_states", self._assembly_states)
        _validate_state_mapping("route_states", self._route_states)
        if set(self._assembly_states) & set(self._route_states):
            raise ValueError("assembly and route identities must not overlap")
        for candidate_id in self._applied_candidate_ids:
            _validate_code("applied_candidate_id", candidate_id)

    @classmethod
    def from_identifiers(
        cls,
        *,
        assembly_ids: Iterable[str],
        route_ids: Iterable[str],
        initial_stability: float = 0.0,
        initial_plasticity: float = 1.0,
    ) -> ConsolidationApplicationState:
        """Create registered state without silently deduplicating identities."""
        _validate_unit("initial_stability", initial_stability)
        _validate_unit("initial_plasticity", initial_plasticity)
        assemblies = _validated_identifiers("assembly_ids", assembly_ids)
        routes = _validated_identifiers("route_ids", route_ids)
        return cls(
            _assembly_states={
                structure_id: ConsolidationStructureState(
                    structure_id=structure_id,
                    stability=initial_stability,
                    plasticity=initial_plasticity,
                )
                for structure_id in assemblies
            },
            _route_states={
                structure_id: ConsolidationStructureState(
                    structure_id=structure_id,
                    stability=initial_stability,
                    plasticity=initial_plasticity,
                )
                for structure_id in routes
            },
        )

    @classmethod
    def from_states(
        cls,
        *,
        assembly_states: Iterable[ConsolidationStructureState],
        route_states: Iterable[ConsolidationStructureState],
    ) -> ConsolidationApplicationState:
        """Create state from explicit bounded values for controlled experiments."""
        assemblies = _validated_states("assembly_states", assembly_states)
        routes = _validated_states("route_states", route_states)
        return cls(
            _assembly_states={state.structure_id: state for state in assemblies},
            _route_states={state.structure_id: state for state in routes},
        )

    def snapshot(self) -> ConsolidationStateSnapshot:
        """Capture complete deterministic state without exposing mutable mappings."""
        return ConsolidationStateSnapshot(
            assembly_states=tuple(
                self._assembly_states[key] for key in sorted(self._assembly_states)
            ),
            route_states=tuple(self._route_states[key] for key in sorted(self._route_states)),
            applied_candidate_ids=tuple(sorted(self._applied_candidate_ids)),
        )

    def apply(
        self,
        eligibility: ConsolidationEligibility,
    ) -> ConsolidationApplicationResult:
        """Atomically apply one eligible bounded proposal exactly once."""
        candidate = _validated_candidate(eligibility)
        before = self.snapshot()
        if candidate.candidate_id in self._applied_candidate_ids:
            raise RuntimeError("consolidation candidate has already been applied")

        missing_assemblies = set(candidate.assembly_ids) - set(self._assembly_states)
        missing_routes = set(candidate.route_ids) - set(self._route_states)
        if missing_assemblies:
            raise ValueError("consolidation candidate references unknown assemblies")
        if missing_routes:
            raise ValueError("consolidation candidate references unknown routes")

        updated_assemblies = dict(self._assembly_states)
        updated_routes = dict(self._route_states)
        for assembly_id in candidate.assembly_ids:
            updated_assemblies[assembly_id] = _updated_state(
                updated_assemblies[assembly_id],
                candidate,
            )
        for route_id in candidate.route_ids:
            updated_routes[route_id] = _updated_state(
                updated_routes[route_id],
                candidate,
            )

        updated_candidate_ids = set(self._applied_candidate_ids)
        updated_candidate_ids.add(candidate.candidate_id)
        after = ConsolidationStateSnapshot(
            assembly_states=tuple(updated_assemblies[key] for key in sorted(updated_assemblies)),
            route_states=tuple(updated_routes[key] for key in sorted(updated_routes)),
            applied_candidate_ids=tuple(sorted(updated_candidate_ids)),
        )

        result = ConsolidationApplicationResult(
            candidate=candidate,
            before=before,
            after=after,
        )
        self._assembly_states = updated_assemblies
        self._route_states = updated_routes
        self._applied_candidate_ids = updated_candidate_ids
        return result


def _validated_candidate(eligibility: ConsolidationEligibility) -> ConsolidationCandidate:
    if not eligibility.eligible or eligibility.candidate is None:
        raise RuntimeError("only an eligible consolidation proposal may be applied")
    candidate = eligibility.candidate
    if candidate.lesson_identity != eligibility.evaluated_lesson:
        raise ValueError("candidate lesson does not match eligibility result")
    if candidate.mastery_snapshot != eligibility.mastery_snapshot:
        raise ValueError("candidate mastery snapshot does not match eligibility result")
    if candidate.requested_stability_increment > eligibility.policy.maximum_stability_increment:
        raise ValueError("candidate stability request exceeds eligibility policy")
    if candidate.requested_plasticity_reduction > eligibility.policy.maximum_plasticity_reduction:
        raise ValueError("candidate plasticity request exceeds eligibility policy")
    return candidate


def _updated_state(
    state: ConsolidationStructureState,
    candidate: ConsolidationCandidate,
) -> ConsolidationStructureState:
    return ConsolidationStructureState(
        structure_id=state.structure_id,
        stability=min(
            1.0,
            state.stability + candidate.requested_stability_increment,
        ),
        plasticity=max(
            0.0,
            state.plasticity - candidate.requested_plasticity_reduction,
        ),
    )


def _validated_identifiers(name: str, values: Iterable[str]) -> tuple[str, ...]:
    identifiers = tuple(values)
    if not identifiers:
        raise ValueError(f"{name} must not be empty")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{name} must contain unique identities")
    for identifier in identifiers:
        _validate_code(name, identifier)
    return tuple(sorted(identifiers))


def _validated_states(
    name: str,
    values: Iterable[ConsolidationStructureState],
) -> tuple[ConsolidationStructureState, ...]:
    states = tuple(values)
    if not states:
        raise ValueError(f"{name} must not be empty")
    identifiers = tuple(state.structure_id for state in states)
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{name} must contain unique identities")
    return tuple(sorted(states, key=lambda state: state.structure_id))


def _validate_state_collection(
    name: str,
    states: tuple[ConsolidationStructureState, ...],
) -> None:
    if not states:
        raise ValueError(f"{name} must not be empty")
    identifiers = tuple(state.structure_id for state in states)
    if identifiers != tuple(sorted(identifiers)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(identifiers) != len(set(identifiers)):
        raise ValueError(f"{name} must contain unique identities")


def _validate_state_mapping(
    name: str,
    states: dict[str, ConsolidationStructureState],
) -> None:
    if not states:
        raise ValueError(f"{name} must not be empty")
    for structure_id, state in states.items():
        if structure_id != state.structure_id:
            raise ValueError(f"{name} key must match structure identity")


def _validate_sorted_unique_codes(name: str, values: tuple[str, ...]) -> None:
    if values != tuple(sorted(values)):
        raise ValueError(f"{name} must use stable sorted ordering")
    if len(values) != len(set(values)):
        raise ValueError(f"{name} must contain unique identities")
    for value in values:
        _validate_code(name, value)


def _find_state(
    kind: str,
    structure_id: str,
    states: tuple[ConsolidationStructureState, ...],
) -> ConsolidationStructureState:
    _validate_code(f"{kind}_id", structure_id)
    for state in states:
        if state.structure_id == structure_id:
            return state
    raise ValueError(f"unknown {kind} identity: {structure_id}")


def _snapshot_ids(states: tuple[ConsolidationStructureState, ...]) -> set[str]:
    return {state.structure_id for state in states}


def _validate_code(name: str, value: str) -> None:
    if not value.strip() or not value.isascii():
        raise ValueError(f"{name} must be non-empty ASCII")


def _validate_unit(name: str, value: float) -> None:
    if not isfinite(value) or not 0.0 <= value <= 1.0:
        raise ValueError(f"{name} must be finite and between zero and one")
