# ADR-2026-06-29 Long-Horizon Mixed-Task Interference

## Status

Accepted

## Context

The existing short bounded interference experiment proved the retention pattern in a deterministic 12-step proxy, but standalone NDNRA v0.1 still required a materially longer mixed-task sequence with repeated switching among one mastered old family and two novel families.

The accepted Batch 1 boundary required:

- a separate in-memory deterministic experiment only;
- no edits to the accepted short interference module, main brain persistence, standalone acceptance payloads, live integration, bounded imagination, scheduling, recommendation, execution, promotion, or production authority;
- exactly three controls: no consolidation, naive protection, and bounded retention replay;
- one exact old-family source ledger and one exact consolidation candidate;
- exact finite replay bounds, zero structural drift, zero authority violations, and zero SQLite cognition;
- deterministic rerun-equality plus canonical ASCII JSON snapshot and SHA-256 identity evidence;
- restart-equivalence proof deferred to Batch 2.

## Decision

Implement Batch 1 as `long_horizon_interference_experiment.py` with these invariants:

1. Pretrain family A to mastery across at least two routes and at least three exact source events, then build one exact consolidation candidate from that unchanged source ledger.
2. Run an exact 36-step horizon in stable repeating order `A, B, A, C` for nine cycles.
3. Treat every family A step as a retention probe only. Probe steps must not train, mutate memory, or create source evidence.
4. Train family B and family C as distinct novel tasks through one shared representational bottleneck with separate route-local values so repeated switching produces interference pressure.
5. Compare exactly three independently initialized conditions:
   - no consolidation: unrestricted learning, no replay;
   - naive protection: exact family A consolidation candidate applied, no replay;
   - bounded retention replay: same protection plus at most one exact old source replay after a B or C step drops family A below threshold.
6. Keep replay local and non-authoritative. Replay source identifiers must resolve only to exact members of the consolidation candidate source set and must never be represented as new source evidence.
7. Keep specialist growth count, duplicate specialist membership count, and all structural drift counts exactly zero across every step and condition.
8. Keep action-selection, recommendation, scheduling, execution, live integration, promotion, and production action authority booleans explicitly false, with zero authority violations and `sqlite_used_for_experiment=False`.
9. Keep all public evidence transitively immutable and accept a result identity only after revalidating exact schedule, memory continuity, per-step and final derived scores, replay summaries and bounds, source counts and mastery flags, structural invariants, aggregate pass criteria, canonical snapshot, and SHA-256 digest.

Batch 2 extends the stage with an isolated persistence and restart-proof boundary:

1. Add strict public payload and restore helpers that preserve the existing Batch 1 snapshot shapes exactly, reject unknown fields and semantic tampering, and reconstruct one exact validated `LongHorizonInterferenceResult` with a rederived canonical ASCII snapshot and SHA-256 identity.
2. Store only one validated Batch 1 result in a separate versioned canonical-ASCII JSON envelope with checksum and identity protection. The store must not import or modify main brain persistence, standalone acceptance persistence, bounded imagination, integration, scheduling, recommendation, execution, promotion, production action authority, or SQLite cognition.
3. Loading must expose only four explicit outcomes: loaded, missing fallback, corrupt fallback, and incompatible fallback. Every fallback must return `result=None`, no checksum or identity, no partial proof, no synthesized passing evidence, and no authority.
4. Restart proof must remain separate from the stored Batch 1 result, must preserve `restart_proof_included=False`, must require exact source-to-restored equality and exact restored-to-rerun equality, and must require unchanged source evidence, unchanged mastery, bounded replay, zero structure drift, unchanged bounded-imagination non-persistence, unchanged main brain schema, unchanged standalone-acceptance schema, zero authority, and zero deltas.

## Consequences

- NDNRA now has a materially longer standalone mixed-task interference result without broadening authority or persistence scope.
- The retained old-family source ledger, trace count, and mastery profile remain unchanged despite replay, which keeps replay descriptive rather than evidentiary.
- The experiment yields deterministic complete timelines, transitively immutable bounded replay evidence, canonical ASCII JSON snapshots, and semantically revalidated SHA-256 result identities suitable for strict equality checks.
- The stage now also has an isolated checksum-protected restart-equivalence proof store with explicit safe fallbacks and no new authority.
- Main brain persistence, standalone acceptance persistence, bounded imagination, live integration, scheduling, recommendation, execution, promotion, production action authority, and SQLite cognition remain unchanged by this Batch 2 extension.
