# SeedMind Human-Approved Consolidation Execution Stage Plan

Date: 28 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Stage status: active
Authority: explicit-human-approval only, research-only, bounded execution
Target heuristic theory-to-integration readiness after full acceptance: 97%

## 1. Stage objective

This stage evaluates whether one exact, current consolidation proposal can be applied only after explicit human approval, immediate evidence revalidation, and bounded single-use authorization.

```text
accepted lifecycle proposal
+ explicit human approval
+ immediate current-evidence revalidation
+ single-use execution identity
        -> bounded execution permit
        -> later atomic application gate
        -> no autonomous execution
```

Human approval is necessary but not sufficient. The proposal must still be current at the approval boundary and again immediately before any future application.

## 2. Mandatory invariants

- Production curiosity remains the sole production action authority.
- Only an active lifecycle record with accepted review status may be considered.
- Human approval must name one exact proposal and candidate.
- Approval must identify the exact accepted review decision.
- Approval must include an explicit approver identity and reason.
- Immediate revalidation must classify the proposal as `current`.
- Stale, superseded, or invalid-for-review proposals cannot receive an execution permit.
- Every permit must have a deterministic identity, bounded validity window, and single-use semantics.
- Permit issuance must not apply consolidation or mutate neural state.
- Permit issuance must not mutate lifecycle history, contextual evidence, graph state, growth state, or persistence.
- No autonomous approval, timer, background worker, or execution queue is permitted.
- No replay, restoration, advice, route-ranking, growth, or production-action influence is permitted without separate gates.
- SQLite remains outside approval, revalidation, execution selection, and authority.
- Failure at any validation boundary must leave all state unchanged.

## 3. Planned batches

### Batch 1 — explicit approval and execution-permit contract

Implement a pure approval policy that:

- Accepts one explicit human approval request.
- Requires one active accepted lifecycle record.
- Verifies the exact proposal, candidate, and accepted review decision.
- Performs immediate revalidation against current contextual evidence and available structures.
- Issues a deterministic, bounded, single-use execution permit only when the proposal is current.
- Rejects stale, superseded, invalid, unaccepted, expired, mismatched, or malformed requests.
- Does not consume the permit or apply consolidation.

### Batch 2 — cancellation and single-use permit state

Implement immutable permit lifecycle state:

- Issued.
- Cancelled.
- Consumed.
- Expired.

Prove:

- One permit identity can be consumed at most once.
- Cancellation before commit blocks application.
- Expiry blocks application.
- Conflicting state transitions fail without mutation.
- Permit state is separate from proposal lifecycle state.

### Batch 3 — atomic human-approved application

Connect one current, issued, unexpired, unconsumed permit to bounded consolidation application:

- Immediate revalidation immediately before commit.
- Exact candidate and structure identity checks.
- Atomic before/after state capture.
- Single-use permit consumption tied to successful commit.
- Cancellation before commit.
- Complete restoration of pre-application state on failure.
- No replay, advice, growth, route-ranking, or action influence.

### Batch 4 — persistence, interruption, and live acceptance

Prove:

- Approval and permit state survive restart exactly.
- Interrupted pre-commit execution performs no application.
- Failed application restores exact prior state.
- Duplicate or replayed permits cannot apply twice.
- Stale evidence between approval and commit blocks application.
- Live-shadow execution tests preserve production action authority and unrelated learning.
- No SQLite cognition or autonomous execution occurs.

### Batch 5 — documentation and closure

- Update README, master plan, and NDNRA architecture.
- Produce the human-approved execution handover.
- Refresh the repository wiki.
- Run final quality gates.
- Reassess whether the complete stage justifies increasing heuristic readiness from 96% to 97%.

## 4. Batch 1 public contract

The first implementation should provide:

- `ConsolidationExecutionApprovalRequest`
- `ConsolidationExecutionPermit`
- `ConsolidationExecutionApprovalPolicy`

The approval policy must receive the current ledger and structure identities directly so that permit issuance includes immediate revalidation rather than trusting a prior classification.

## 5. Batch 1 non-authority rule

A permit is authorization evidence for one possible future application. It is not an executor.

The permit may state that it authorizes one bounded application, while still having:

```text
has_direct_execution_authority = false
application_count = 0
state_mutation_count = 0
```

Consumption and application belong to later batches.

## 6. Explicitly out of scope for Batch 1

- Consolidation application.
- Permit consumption.
- Permit cancellation state.
- Permit persistence.
- Retention replay.
- Consolidation rollback or restoration.
- Advice or growth influence.
- Route-ranking influence.
- Production action authority.
- Autonomous review or approval.
- Background execution.

## 7. Stage completion rule

The stage is complete only when explicit approval, single-use permit state, atomic application, cancellation, failure fallback, restart safety, and live acceptance all pass while preserving every authority boundary.

Completing Batch 1 alone does not raise readiness above 96%.
