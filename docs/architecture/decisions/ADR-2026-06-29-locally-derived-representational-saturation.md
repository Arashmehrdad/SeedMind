# ADR-2026-06-29: Locally Derived Representational Saturation

## Status

Accepted

## Context

Normalized Recruitment and Local Saturation Batch 2 closes the remaining v0.1 structural-growth
gap around representational saturation. Batch 1 already normalized competing recruitment, but the
structural-growth controller still accepted caller-supplied `capacity_saturation`. That allowed
non-local callers to inject readiness pressure and let old accumulated pressure remain sufficient
even when the current unresolved interaction no longer showed strong local evidence.

The accepted Batch 2 boundary requires saturation to be derived inside the structural-growth
controller without changing persistence schemas, standalone acceptance payloads, adaptive runtime
callers, or live integration code.

## Decision

Structural-growth saturation is now derived deterministically inside
`EvidenceDrivenGrowthController.observe_unresolved_interaction()` before eligibility mutation.

The local saturation report uses only:

- exact active assembly identities;
- active-member eligibility values before the current event;
- current graph assembly and specialist counts;
- configured maximum specialists;
- exact duplicate specialist membership;
- remaining specialist slots.

The report is immutable, bounded, and self-validating. It records stable sorted active identities,
aligned eligibility-before values, remaining capacity, canonical duplicate membership, minimum and mean
active eligibility, a boolean `locally_saturated`, and scalar `saturation`.

`locally_saturated` is true only when:

- at least two unique existing assemblies are active;
- remaining specialist slots are available;
- no exact duplicate specialist membership already exists;
- every active member eligibility already meets the configured minimum threshold.

`saturation` equals the minimum active eligibility when locally saturated, otherwise exactly
`0.0`.

Growth pressure continues to use unresolved error, curiosity, and ambition, but now receives only
the derived local saturation scalar. Controller readiness and per-attempt readiness both require
the current report to be locally saturated so stale accumulated pressure cannot bypass a weak
current interaction.

## Consequences

- One unresolved event on a fresh controller cannot self-certify growth pressure.
- Repeated identical unresolved local interactions can deterministically accumulate enough local
  evidence to cross the structural-growth gate.
- Exact duplicate specialist membership and exhausted specialist capacity force saturation to zero.
- Structural-growth experiments keep deterministic three-attempt readiness and targeted membership.
- Persistence schemas, standalone acceptance formats, bounded imagination, adaptive runtime
  saturation callers, and integration boundaries remain unchanged in this batch.
