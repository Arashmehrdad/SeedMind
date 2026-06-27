"""Need-driven composition over local multidimensional experience assemblies."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from seedmind.research.ndnra.effects import (
    EffectNeed,
    EffectObservation,
    LocalEffectLink,
    SparseEffectMemory,
    combine_projected_effects,
)


@dataclass(slots=True)
class ExperienceAssembly:
    """One neuron-like local experience fragment containing one action only."""

    assembly_id: str
    action_code: str
    origin_need_code: str
    required_facts: frozenset[str]
    produced_facts: frozenset[str]
    effect_memory: SparseEffectMemory = field(default_factory=SparseEffectMemory)
    evidence_count: int = 0

    def __post_init__(self) -> None:
        for name, value in (
            ("assembly_id", self.assembly_id),
            ("action_code", self.action_code),
            ("origin_need_code", self.origin_need_code),
        ):
            _validate_code(name, value)
        _validate_facts("required_facts", self.required_facts)
        _validate_facts("produced_facts", self.produced_facts)
        if self.evidence_count < 0:
            raise ValueError("evidence_count must not be negative")

    def observe_effects(self, observations: Iterable[EffectObservation]) -> int:
        """Expand this assembly only with consequences it actually observed."""
        self.evidence_count += 1
        return self.effect_memory.observe_many(observations)

    def is_applicable(self, facts: frozenset[str]) -> bool:
        return self.required_facts.issubset(facts)

    def snapshot(self) -> dict[str, object]:
        return {
            "assembly_id": self.assembly_id,
            "action_code": self.action_code,
            "origin_need_code": self.origin_need_code,
            "required_facts": sorted(self.required_facts),
            "produced_facts": sorted(self.produced_facts),
            "evidence_count": self.evidence_count,
            "effect_memory": self.effect_memory.snapshot(),
        }


@dataclass(slots=True)
class SpecialistInteraction:
    """A grown neuron-like unit for a non-additive multi-memory effect."""

    specialist_id: str
    member_assembly_ids: tuple[str, ...]
    origin_code: str
    effect_memory: SparseEffectMemory = field(default_factory=SparseEffectMemory)
    evidence_count: int = 0

    def __post_init__(self) -> None:
        _validate_code("specialist_id", self.specialist_id)
        _validate_code("origin_code", self.origin_code)
        if len(self.member_assembly_ids) < 2:
            raise ValueError("a specialist interaction requires at least two members")
        if len(self.member_assembly_ids) != len(set(self.member_assembly_ids)):
            raise ValueError("specialist members must be unique")
        for assembly_id in self.member_assembly_ids:
            _validate_code("member_assembly_ids", assembly_id)
        if self.evidence_count < 0:
            raise ValueError("evidence_count must not be negative")

    def observe_effects(self, observations: Iterable[EffectObservation]) -> int:
        """Store only effects supported by this interaction's evidence."""
        effects = tuple(observations)
        if effects:
            self.evidence_count += 1
        return self.effect_memory.observe_many(effects)

    def applies_to(self, assembly_ids: tuple[str, ...]) -> bool:
        return set(self.member_assembly_ids).issubset(assembly_ids)

    def snapshot(self) -> dict[str, object]:
        return {
            "specialist_id": self.specialist_id,
            "member_assembly_ids": list(self.member_assembly_ids),
            "origin_code": self.origin_code,
            "evidence_count": self.evidence_count,
            "effect_memory": self.effect_memory.snapshot(),
        }


class MultidimensionalExperienceGraph:
    """Sparse graph of local actions, links, and grown interaction specialists."""

    def __init__(self) -> None:
        self._assemblies: dict[str, ExperienceAssembly] = {}
        self._links: dict[tuple[str, str], LocalEffectLink] = {}
        self._specialists: dict[str, SpecialistInteraction] = {}

    @classmethod
    def from_components(
        cls,
        *,
        assemblies: Iterable[ExperienceAssembly],
        links: Iterable[LocalEffectLink],
        specialists: Iterable[SpecialistInteraction],
    ) -> MultidimensionalExperienceGraph:
        """Restore validated local structures without replaying experience."""
        graph = cls()
        for assembly in assemblies:
            if assembly.assembly_id in graph._assemblies:
                raise ValueError(f"duplicate assembly: {assembly.assembly_id}")
            graph._assemblies[assembly.assembly_id] = assembly
        for link in links:
            if link.source_id not in graph._assemblies:
                raise ValueError(f"link source is not an assembly: {link.source_id}")
            if not link.target_id.startswith("fact:") or len(link.target_id) <= 5:
                raise ValueError("restored link target must identify a produced fact")
            fact = link.target_id.removeprefix("fact:")
            key = (link.source_id, fact)
            if key in graph._links:
                raise ValueError(f"duplicate link: {link.link_id}")
            graph._links[key] = link
        for specialist in specialists:
            if specialist.specialist_id in graph._specialists:
                raise ValueError(f"duplicate specialist: {specialist.specialist_id}")
            missing = set(specialist.member_assembly_ids) - set(graph._assemblies)
            if missing:
                raise ValueError("specialist contains unknown parent assemblies")
            graph._specialists[specialist.specialist_id] = specialist
        return graph

    @property
    def assemblies(self) -> tuple[ExperienceAssembly, ...]:
        return tuple(self._assemblies[key] for key in sorted(self._assemblies))

    @property
    def links(self) -> tuple[LocalEffectLink, ...]:
        return tuple(self._links[key] for key in sorted(self._links))

    @property
    def assembly_count(self) -> int:
        return len(self._assemblies)

    @property
    def link_count(self) -> int:
        return len(self._links)

    @property
    def specialists(self) -> tuple[SpecialistInteraction, ...]:
        return tuple(self._specialists[key] for key in sorted(self._specialists))

    @property
    def specialist_count(self) -> int:
        return len(self._specialists)

    @property
    def structural_node_count(self) -> int:
        return self.assembly_count + self.specialist_count

    @property
    def effect_dimension_codes(self) -> tuple[str, ...]:
        dimensions: set[str] = set()
        for assembly in self._assemblies.values():
            dimensions.update(assembly.effect_memory.effect_codes)
        for link in self._links.values():
            dimensions.update(link.effect_memory.effect_codes)
        for specialist in self._specialists.values():
            dimensions.update(specialist.effect_memory.effect_codes)
        return tuple(sorted(dimensions))

    def assembly(self, assembly_id: str) -> ExperienceAssembly:
        try:
            return self._assemblies[assembly_id]
        except KeyError as error:
            raise ValueError(f"unknown assembly_id: {assembly_id}") from error

    def learn_experience(
        self,
        *,
        assembly_id: str,
        action_code: str,
        origin_need_code: str,
        required_facts: Iterable[str],
        produced_facts: Iterable[str],
        observed_effects: Iterable[EffectObservation],
    ) -> ExperienceAssembly:
        """Learn all observed consequences without storing a complete plan."""
        required = frozenset(required_facts)
        produced = frozenset(produced_facts)
        effects = tuple(observed_effects)
        if not effects:
            raise ValueError("observed_effects must not be empty")

        assembly = self._assemblies.get(assembly_id)
        if assembly is None:
            assembly = ExperienceAssembly(
                assembly_id=assembly_id,
                action_code=action_code,
                origin_need_code=origin_need_code,
                required_facts=required,
                produced_facts=produced,
            )
            self._assemblies[assembly_id] = assembly
        else:
            expected = (
                assembly.action_code,
                assembly.origin_need_code,
                assembly.required_facts,
                assembly.produced_facts,
            )
            supplied = (action_code, origin_need_code, required, produced)
            if expected != supplied:
                raise ValueError("an existing assembly cannot change its identity")

        assembly.observe_effects(effects)
        for fact in produced:
            key = (assembly_id, fact)
            link = self._links.get(key)
            if link is None:
                link = LocalEffectLink(source_id=assembly_id, target_id=f"fact:{fact}")
                self._links[key] = link
            link.observe_effects(effects)
        return assembly

    def grow_specialist_interaction(
        self,
        *,
        specialist_id: str,
        member_assembly_ids: Iterable[str],
        origin_code: str,
        observed_effects: Iterable[EffectObservation] = (),
    ) -> SpecialistInteraction:
        """Add one evidence-scoped structural node without changing old memories."""
        if specialist_id in self._specialists:
            raise ValueError(f"specialist already exists: {specialist_id}")
        members = tuple(member_assembly_ids)
        for assembly_id in members:
            if assembly_id not in self._assemblies:
                raise ValueError(f"unknown specialist member: {assembly_id}")
        specialist = SpecialistInteraction(
            specialist_id=specialist_id,
            member_assembly_ids=members,
            origin_code=origin_code,
        )
        specialist.observe_effects(observed_effects)
        self._specialists[specialist_id] = specialist
        return specialist

    def project_effects(self, assembly_ids: tuple[str, ...]) -> dict[str, float]:
        """Project action effects plus each applicable specialist exactly once."""
        effects: dict[str, float] = {}
        for assembly_id in assembly_ids:
            effects = combine_projected_effects(
                effects,
                self.assembly(assembly_id).effect_memory.projected_values(),
            )
        for specialist in self.specialists:
            if specialist.applies_to(assembly_ids):
                effects = combine_projected_effects(
                    effects,
                    specialist.effect_memory.projected_values(),
                )
        return effects

    def has_stored_action_sequence(self, actions: tuple[str, ...]) -> bool:
        """Return true only for a directly stored single-action memory."""
        if len(actions) != 1:
            return False
        return any(assembly.action_code == actions[0] for assembly in self.assemblies)

    def snapshot(self) -> dict[str, object]:
        return {
            "assembly_count": self.assembly_count,
            "link_count": self.link_count,
            "specialist_count": self.specialist_count,
            "structural_node_count": self.structural_node_count,
            "effect_dimension_count": len(self.effect_dimension_codes),
            "effect_dimensions": list(self.effect_dimension_codes),
            "assemblies": [assembly.snapshot() for assembly in self.assemblies],
            "links": [
                {
                    "link_id": link.link_id,
                    "source_id": link.source_id,
                    "target_id": link.target_id,
                    "usage_count": link.usage_count,
                    "effect_memory": link.effect_memory.snapshot(),
                }
                for link in self.links
            ],
            "specialists": [specialist.snapshot() for specialist in self.specialists],
        }


@dataclass(frozen=True, slots=True)
class CompositionCandidate:
    """One temporary solution assembled from separate local memories."""

    assembly_ids: tuple[str, ...]
    actions: tuple[str, ...]
    resulting_facts: frozenset[str]
    projected_effects: tuple[tuple[str, float], ...]
    score: float
    primary_satisfaction: float

    @property
    def depth(self) -> int:
        return len(self.actions)

    def effect_value(self, effect_code: str) -> float:
        return dict(self.projected_effects).get(effect_code, 0.0)


@dataclass(frozen=True, slots=True)
class CompositionResult:
    """Result of bounded need-driven temporary assembly composition."""

    selected: CompositionCandidate | None
    candidates: tuple[CompositionCandidate, ...]
    explored_state_count: int
    maximum_depth: int

    @property
    def success(self) -> bool:
        return self.selected is not None


@dataclass(frozen=True, slots=True)
class _SearchState:
    assembly_ids: tuple[str, ...]
    actions: tuple[str, ...]
    facts: frozenset[str]
    effects: tuple[tuple[str, float], ...]


class NeedDrivenComposer:
    """Compose novel action chains without retrieving a stored full solution."""

    def __init__(
        self,
        graph: MultidimensionalExperienceGraph,
        *,
        maximum_depth: int = 3,
        step_cost: float = 0.01,
    ) -> None:
        if maximum_depth <= 0:
            raise ValueError("maximum_depth must be positive")
        if not 0.0 <= step_cost <= 1.0:
            raise ValueError("step_cost must be between zero and one")
        self.graph = graph
        self.maximum_depth = maximum_depth
        self.step_cost = step_cost

    def compose(
        self,
        *,
        need: EffectNeed,
        current_facts: Iterable[str],
    ) -> CompositionResult:
        """Explore applicable local assemblies and rank need-resolving chains."""
        initial_facts = frozenset(current_facts)
        _validate_facts("current_facts", initial_facts)
        frontier: tuple[_SearchState, ...] = (
            _SearchState(
                assembly_ids=(),
                actions=(),
                facts=initial_facts,
                effects=(),
            ),
        )
        candidates: list[CompositionCandidate] = []
        explored = 0

        for _ in range(self.maximum_depth):
            next_frontier: list[_SearchState] = []
            for state in frontier:
                used = set(state.assembly_ids)
                for assembly in self.graph.assemblies:
                    if assembly.assembly_id in used or not assembly.is_applicable(state.facts):
                        continue
                    explored += 1
                    facts = state.facts | assembly.produced_facts
                    assembly_ids = (*state.assembly_ids, assembly.assembly_id)
                    actions = (*state.actions, assembly.action_code)
                    effects = self.graph.project_effects(assembly_ids)
                    search_state = _SearchState(
                        assembly_ids=assembly_ids,
                        actions=actions,
                        facts=facts,
                        effects=tuple(sorted(effects.items())),
                    )
                    primary = need.primary_satisfaction(effects)
                    if primary >= need.satisfaction_threshold:
                        candidates.append(
                            CompositionCandidate(
                                assembly_ids=assembly_ids,
                                actions=actions,
                                resulting_facts=facts,
                                projected_effects=tuple(sorted(effects.items())),
                                score=need.score_projected_effects(effects)
                                - self.step_cost * len(actions),
                                primary_satisfaction=primary,
                            )
                        )
                    else:
                        next_frontier.append(search_state)
            frontier = tuple(next_frontier)
            if not frontier:
                break

        ranked = tuple(
            sorted(
                candidates,
                key=lambda candidate: (
                    -candidate.score,
                    candidate.depth,
                    candidate.actions,
                ),
            )
        )
        return CompositionResult(
            selected=ranked[0] if ranked else None,
            candidates=ranked,
            explored_state_count=explored,
            maximum_depth=self.maximum_depth,
        )


def _validate_code(name: str, value: str) -> None:
    if not value.strip():
        raise ValueError(f"{name} must not be empty")
    if not value.isascii():
        raise ValueError(f"{name} must be ASCII")


def _validate_facts(name: str, facts: frozenset[str]) -> None:
    for fact in facts:
        _validate_code(name, fact)
