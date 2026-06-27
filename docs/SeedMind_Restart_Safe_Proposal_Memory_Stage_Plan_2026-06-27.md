# SeedMind Restart-Safe Proposal Memory Stage Plan

Date: 27 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Stage status: active
Authority: persistence-only, review-only, research-only, shadow-only
Target heuristic theory-to-integration readiness after full acceptance: 96%

## 1. Stage objective

This stage evaluates whether the complete consolidation proposal lifecycle can survive process restart without becoming cognition, execution authority, or an autonomous queue.

```text
immutable proposal lifecycle registry
+ versioned non-SQL checkpoint
+ checksum-protected brain envelope
+ restart-time evidence revalidation
        -> exact lifecycle reconstruction
        -> stale or corrupt state rejected safely
        -> no consolidation execution
```

Persistence stores and reconstructs review evidence only. It must never search for relevant memories, rank routes, create proposals, decide reviews, apply consolidation, trigger replay, restore consolidation checkpoints, influence advice or growth, or select production actions.

## 2. Mandatory invariants

- Production curiosity remains the sole production action authority.
- Accepted means approved only for possible future consideration.
- Persisted lifecycle state cannot execute consolidation.
- Persistence cannot trigger retention replay or checkpoint restoration.
- Persistence cannot create, accept, reject, defer, expire, or replace proposals automatically.
- Restart revalidation may mark evidence as current or stale but may not execute or silently delete it.
- Proposal, candidate, reviewer, reason, decision, and management identities must round-trip exactly.
- Corrupt, incompatible, or relationally inconsistent state must produce a complete safe fallback.
- Older brain schemas must migrate to an explicit empty proposal-lifecycle checkpoint.
- SQLite remains outside proposal persistence, reconstruction, revalidation, and cognition.
- No timer, background worker, autonomous reviewer, or persistent execution queue is permitted.
- No permanent pruning or source-evidence deletion is permitted.

## 3. Planned batches

### Batch 1 — exact lifecycle checkpoint codec

Implement a pure versioned checkpoint contract for one complete lifecycle registry:

- Explicit lifecycle checkpoint schema and version.
- Empty migration target.
- Exact reconstruction of proposals, candidates, mastery snapshots, review decisions, lifecycle histories, management decisions, archived records, active records, and capacity.
- Structural and relational validation during reconstruction.
- Deterministic ASCII-safe snapshots.
- Explicitly absent execution authority.

This batch does not write files and does not change brain schema version 3.

### Batch 2 — brain schema version 4 integration

Embed the lifecycle checkpoint into the existing checksum-protected atomic brain envelope:

- Advance brain schema version from 3 to 4.
- Save and load lifecycle checkpoints atomically with graph, growth, and consolidation state.
- Migrate versions 1, 2, and 3 to an explicit empty lifecycle checkpoint.
- Preserve complete fallback behavior for corruption and incompatible schemas.
- Keep persistence outside the cognitive path.

### Batch 3 — restart-time proposal revalidation

Add a pure revalidation policy that compares restored active proposals with current contextual evidence:

- Exact lesson identity.
- Exact candidate identity when evidence is unchanged.
- Source-event availability.
- Current broad mastery.
- Contradiction state.
- Assembly and route availability.
- Newer same-lesson proposal evidence.

The policy may classify restored proposals as current, stale, superseded, or invalid for review. It may not execute, delete, or automatically replace them.

### Batch 4 — restart and live-shadow acceptance

Run deterministic corruption, migration, restart, and live-shadow acceptance:

- Exact round-trip across restart.
- Safe empty migration from schemas 1–3.
- Checksum tampering fallback.
- Relational mismatch fallback.
- Stale accepted proposal detection after evidence changes.
- Identical production actions, predictions, suggestions, signals, learned graph state, and growth state with lifecycle persistence enabled or disabled.
- Zero consolidation applications, replay triggers, SQLite cognition, or authority violations.

### Batch 5 — documentation and closure

- Update README, master plan, and NDNRA architecture.
- Produce the restart-safe proposal memory handover.
- Refresh the repository wiki.
- Run final quality gates.
- Reassess whether the complete stage justifies increasing heuristic readiness from 95% to 96%.

## 4. Batch 1 public contract

The first implementation should provide:

- `PROPOSAL_LIFECYCLE_SCHEMA`
- `PROPOSAL_LIFECYCLE_SCHEMA_VERSION`
- `NDNRAProposalLifecycleCheckpoint`

The checkpoint must support:

```text
empty checkpoint
complete bounded lifecycle registry
exact snapshot
exact reconstruction
complete validation failure on malformed state
```

## 5. Explicitly out of scope

- Consolidation execution.
- Retention replay.
- Consolidation rollback or restoration.
- Human-approved execution.
- Autonomous review decisions.
- Background scheduling.
- Advice or growth influence.
- Route-ranking influence.
- Production action authority.
- SQLite cognitive lookup.

## 6. Stage completion rule

The stage is complete only when lifecycle persistence, migration, restart revalidation, corruption fallback, and live-shadow invariance all pass while preserving every authority and cognition boundary.

Completing Batch 1 alone does not raise readiness above 95%.
