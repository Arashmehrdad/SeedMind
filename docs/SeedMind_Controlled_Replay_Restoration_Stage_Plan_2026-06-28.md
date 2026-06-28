# SeedMind Controlled Replay and Restoration Stage Plan

Date: 28 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Stage status: active
Authority: explicit-human-approval only, research-only, bounded replay and restoration
Current heuristic theory-to-integration readiness: 97%
Target after complete stage acceptance: 98%

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

Planned:

- Immediate preoperation revalidation.
- Exact replay target and source evidence reconstruction.
- Strict work-item bound.
- Explicit output contract.
- No production action, advice, route-ranking, growth, or pressure-discharge influence.
- Exact in-memory rollback on failure.
- One receipt tied to one consumed replay permit.

Any learning-update authority must be separately explicit and bounded. It must not be inferred from the existence of replay evidence or a replay permit.

### Batch 4 - exact checkpoint restoration and durable persistence

Planned:

- Restore only one exact checksum-verified complete brain envelope.
- Immediate current-state and target revalidation.
- Atomic replacement with exact old-or-new resolution.
- Schema migration for permit, operation, and receipt evidence if required.
- Restart-safe single-use enforcement.
- Interruption handling before and after durable replacement.
- Complete corruption fallback.
- No partial graph, growth, consolidation, proposal, execution, replay, or restoration recovery.

### Batch 5 - live acceptance, documentation, and closure

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

Readiness remains 97% during Batches 1 through 4.

The stage may increase the heuristic marker to 98% only after controlled replay, exact restoration, permit lifecycle, durable persistence, restart safety, corruption fallback, live invariance, documentation, and all repository quality gates pass together.

The marker is an internal engineering progress measure. It is not production readiness, commercial readiness, safety certification, AGI progress, or approval for autonomous replay or restoration.

## 9. Repository workflow

- Inspect repository status before every batch.
- Commit only files belonging to one bounded batch.
- Run targeted tests during implementation and the complete repository quality gates before committing.
- Never push automatically.
