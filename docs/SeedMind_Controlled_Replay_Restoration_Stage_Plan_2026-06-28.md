# SeedMind Controlled Replay and Restoration Stage Plan

Date: 28 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Stage status: active
Authority: explicit-human-approval only, research-only, bounded replay and restoration
Legacy narrow-scope theory-to-integration marker: 97%
Expanded developmental architecture progress after durable replay and restoration: 78%
Legacy target after complete stage acceptance: 98%

## 1. Stage objective

This stage will test whether SeedMind can perform controlled retention replay and exact checkpoint restoration without converting NDNRA, consolidation, persistence, SQLite, or stored evidence into autonomous cognition or production-action authority.

The intended authority chain is:

```text
exact current checkpoint evidence
+ exact replay or restoration target
+ explicit human approval
+ immediate authorization-time validation
+ bounded single-use permit
+ immediate preoperation revalidation
        -> one bounded controlled operation
        -> exact receipt and consumed permit
        -> complete durable envelope or exact prior envelope
        -> no autonomous trigger
```

Human approval is necessary but not sufficient. Every later operation must revalidate the exact target, current checkpoint, source checkpoint, evidence identities, permit lifecycle, and bounded operation contract immediately before any replay or restoration begins.

## 2. Mandatory invariants

- Production curiosity remains the sole production action authority.
- NDNRA, consolidation, replay, restoration, persistence, and SQLite cannot select production actions.
- Persistence stores and reconstructs validated evidence; it is not cognition.
- SQLite remains scientific recording, audit, debugging, and comparison infrastructure only.
- Replay inputs and outputs must be exact, bounded, inspectable, and non-autonomous.
- Restoration must target one exact checksum-verified complete checkpoint envelope.
- Partial authority-bearing restoration is forbidden.
- A fallback or checksum-unverified checkpoint cannot receive authorization.
- Explicit human approval must name the exact target and immediate current evidence.
- Authorization and execution remain separate.
- Permits are immutable, deterministic, bounded, and single-use.
- Permit evidence cannot execute replay, restore checkpoints, perform cognition, or select production actions.
- No autonomous workers, timers, queues, approval, permit issuance, replay, restoration, advice, route ranking, growth influence, pressure discharge, or production-action influence is permitted.
- Failed operations must preserve the exact prior state or produce complete safe fallback.
- Failure-safe rollback for atomicity must not be described as general restoration authority.

## 3. Stage batches

### Batch 1 - explicit replay/restoration authorization contracts

Status: implemented in the commit containing this plan.

Deliverables:

- Exact operation type: retention replay or checkpoint restoration.
- Exact source checkpoint identity and SHA-256 checksum.
- Exact expected current checkpoint identity and checksum.
- Exact source evidence identities.
- Operation-specific bounded target.
- Complete-envelope requirement.
- Explicit prohibition of partial restoration.
- Immediate evidence-state binding.
- Explicit human approver identity and reason.
- Bounded permit validity.
- Deterministic immutable single-use permit evidence.
- Explicit no-replay, no-restoration, no-cognition, and no-production-action authority flags.

Batch 1 performs no replay, restoration, persistence mutation, lifecycle transition, scheduling, or integration action.

### Batch 2 - immutable permit lifecycle

Status: implemented in the commit containing this update.

Deliverables:

- Issued, cancelled, expired, and consumed states.
- One terminal transition per permit identity.
- Exact operation, target, source checkpoint, current checkpoint, checksum, and approval-evidence identity matching.
- Consumption restricted to an explicit `operation:` actor.
- Consumption reference reserved for one future operation receipt.
- Cancellation and consumption restricted to the unexpired validity window.
- Expiry recorded only after the validity window.
- Deterministic immutable transition identities.
- Duplicate permit, duplicate consumption, and conflicting terminal transition rejection.
- Separate replay and restoration consumption counts for audit evidence.
- Explicit no-replay, no-restoration, no-cognition, and no-production-action authority flags on decisions, records, and registries.

Batch 2 performs no replay, restoration, receipt creation, persistence mutation, scheduling, or integration action.

### Batch 3 - bounded retention replay

Status: implemented in the commit containing this update.

Deliverables:

- Immediate preoperation revalidation in the same operation episode.
- Exact current and source checkpoint identity and checksum checks.
- Exact approval-time and operation-time checkpoint/evidence-set comparison.
- Rejection of checksum-unverified and fallback evidence.
- Explicit caller-supplied work items only; no autonomous replay selection.
- Stable unique work-item and source-evidence identities.
- Replay only from named real activity already present in the activity ledger.
- Exact source-structure reconstruction for every work item.
- Strict approved work-item bound.
- Replay quality copied from real evidence rather than caller-supplied inflation.
- Dormancy/accessibility maintenance only, with zero confidence and mastery change.
- No production action, advice, route ranking, growth, pressure discharge, or learning update.
- Copy-first all-or-nothing execution; any failure leaves the original permit, activity ledger, graph, and adaptive state unchanged.
- Deterministic receipt containing exact achieved dormancy changes.
- Permit consumption only after all replay items succeed.
- One receipt tied to one consumed replay permit.
- Cancelled, expired, consumed, stale, drifted, restoration-scoped, and oversized operations rejected.

Batch 3 execution remains isolated from production action and learning authority. Its permit, receipt, activity history, and resulting active state are now persisted atomically by Batch 4.

Any learning-update authority must be separately explicit and bounded. It is not inferred from replay evidence, activity maintenance, a replay permit, or a replay receipt.

### Batch 4 - durable replay persistence

Status: implemented in the commit containing this update.

Deliverables:

- Brain schema 6 stores controlled-operation permits, active activity history, and replay receipts inside the checksum-protected envelope.
- Older schema-5 files migrate to an explicit empty replay/restoration checkpoint.
- Separate outer-envelope and active-state SHA-256 checksums.
- Audit-only permit persistence changes the envelope checksum without invalidating the approved active-state identity.
- Exact activity-ledger reconstruction preserves event order, source distinctions, cycle budgets, and deterministic maintenance decisions.
- Durable replay atomically persists the consumed permit, exact receipt, replay activity history, reduced dormancy, and all unrelated brain components.
- Restarted replay retains single-use enforcement and cannot reuse a consumed permit.
- Interruption before persistence preserves the complete old envelope.
- Interruption after atomic replacement is accepted only when the complete new envelope is present.
- Active-state checksum tampering produces safe corruption fallback.
- Unrelated durable consolidation saves preserve the replay checkpoint instead of erasing its audit history.
- Persistence evidence grants no replay, restoration, cognition, learning, route-ranking, growth, pressure, or production-action authority.

Explicit exclusion: Batch 4 does not implement checkpoint restoration. Restoration-scoped approval and audit contracts may remain representable, but they cannot execute or replace a brain envelope.

### Batch 5 - exact checkpoint restoration

Status: implemented in the commit containing this update.

Deliverables:

- Restore only one checksum-verified native schema-6 active-state checkpoint from a separate source store.
- Revalidate the current state, source state, target, permit, validity window, and fresh evidence immediately before replacement.
- Replace graph, growth, consolidation, proposal lifecycle, execution state, and active activity history together in one atomic save.
- Preserve the current monotonic permit and receipt audit history instead of copying an older audit backward.
- Require the current audit to contain all source audit history before restoration.
- Consume the exact single-use restoration permit only with its deterministic receipt.
- Retain restart-safe restoration evidence and reject permit reuse after restart.
- Resolve interruption to either the complete old envelope or complete restored envelope.
- Reject same-path, corrupt, fallback, migrated, expired, stale, mismatched, or audit-divergent sources without mutating the current store.
- Keep persistence, permits, receipts, and the restoration policy free of cognition, learning, replay selection, growth, advice, and production-action authority.
- Prove full component replacement and failure behavior in the repository-wide test suite.

### Batch 6 - live acceptance, documentation, and closure

Planned:

- Controlled and approved comparison paths.
- Restart, stale-evidence, duplicate, replayed-permit, cancellation, expiry, interruption, and corruption evidence.
- Production-action and cognition invariance.
- Observatory-compatible audit exports if justified.
- Full quality gates.
- Stage handover and wiki refresh.
- Readiness reassessment from 97% to 98% only if every gate passes.

## 4. Batch 1 public contracts

Implementation:

- `src/seedmind/research/ndnra/controlled_replay_restoration_approval.py`

Contracts:

- `ControlledReplayRestorationOperation`
- `ControlledReplayRestorationTarget`
- `ControlledReplayRestorationEvidence`
- `ControlledReplayRestorationApprovalRequest`
- `ControlledReplayRestorationPermit`
- `ControlledReplayRestorationApprovalPolicy`

Tests:

- `tests/unit/test_ndnra_controlled_replay_restoration_approval.py`

## 5. Batch 1 operation boundary

A retention replay target contains:

- A `replay-target:` identity.
- One exact source checkpoint identity and checksum.
- One exact expected current checkpoint identity and checksum.
- A stable non-empty set of source evidence identities.
- A positive maximum work-item count.
- A complete-envelope requirement.

A checkpoint restoration target contains:

- A `restoration-target:` identity.
- One exact source checkpoint identity and checksum.
- One exact expected current checkpoint identity and checksum.
- A stable non-empty set of validation evidence identities.
- Zero replay work items.
- A complete-envelope requirement.
- An explicit prohibition on partial restoration.
- A source target that differs from the current checkpoint.

The target is descriptive evidence only. It has no replay, restoration, cognitive, or production-action authority.

## 6. Immediate approval evidence

Authorization requires one current evidence snapshot containing:

- Capture episode.
- Exact current checkpoint identity and checksum.
- Stable available checkpoint identities and checksums.
- Stable available evidence identities.
- Checksum-verification result.
- Fallback status.
- Explicit absence of replay/restoration authority.

The approval episode must equal the evidence capture episode. A request that names a different evidence-state identity, stale episode, missing checkpoint, changed checksum, missing evidence, checksum-unverified state, or fallback state is rejected.

## 7. Batch 1 exclusions

Batch 1 does not provide:

- A replay executor.
- A restoration function.
- Replay selection.
- Replay learning updates.
- Checkpoint loading or writing.
- Permit lifecycle persistence.
- Permit consumption.
- Operation receipts.
- Automatic triggers.
- Timers, queues, or workers.
- Advice or route-ranking influence.
- Growth or pressure-discharge influence.
- Production-action influence.

## 8. Readiness rule

The legacy narrow-scope marker remains 97% until final live acceptance and stage closure. The expanded developmental architecture marker is 78% after restart-safe durable replay and exact complete-state restoration.

The legacy stage marker may increase to 98% only after live invariance evidence, final documentation, stage handover, and all repository quality gates pass together.

These markers are internal engineering progress measures. They are not production readiness, commercial readiness, safety certification, AGI progress, or approval for autonomous replay or restoration.

## 9. Repository workflow

- Inspect repository status before every batch.
- Commit only files belonging to one bounded batch.
- Run targeted tests during implementation and the complete repository quality gates before committing.
- Never push automatically.
