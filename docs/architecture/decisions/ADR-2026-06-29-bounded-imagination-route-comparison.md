# ADR: Bounded Imagination Route Comparison Is Pairwise And Non-Authoritative

Date: 29 June 2026
Status: accepted
Scope: SeedMind repository documentation

## Context

Bounded imagination now has caller-driven traces, exact-record candidate enumeration,
and pure need-alignment annotation. The next useful step is to compare already-evaluated
imagined routes without creating a hidden utility function or action authority.

## Decision

Batch 4 route comparison consumes exactly one complete `ImaginedRouteEvaluationResult`.
It compares routes only as unordered caller-index pairs and reports local alignment
relations for each step/effect dimension.

Dominance is allowed only when one route is no worse on every comparable local
dimension and strictly better on at least one. Unknown alignments, low confidence, and
route-depth mismatch block dominance. Conflicting trade-offs remain incomparable.
Alignment-equivalent routes remain distinct and preserve separate source provenance
through the embedded Batch 3 result. Public comparison results must revalidate caller
order, source IDs, dimension source shape, and pair relations against that embedded
result rather than trust copied identifiers.

The comparison layer does not compute a route score, utility, rank, winner, selected
candidate, recommendation, optimisation, schedule, promotion, execution decision,
persistence authority, live integration, or production-action authority.

## Consequences

- Comparison output is inspectable pairwise semantics only.
- Caller order remains ordering of presentation, not quality.
- Incompatible need or evaluation semantics fail atomically instead of being compared.
- Safe-experiment promotion, persistence, live integration, and production action
  influence remain deferred to later explicit boundaries.
- The expanded developmental architecture marker remains 82%.
