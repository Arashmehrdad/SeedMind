# SeedMind Consolidation Proposal Lifecycle Stage Plan

Date: 27 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Stage status: complete
Authority: review-only, research-only, shadow-only
Accepted heuristic theory-to-integration readiness: 95%

## 1. Stage objective

This stage evaluates whether SeedMind can manage the review state of consolidation proposals without executing consolidation or changing cognitive, advisory, growth, replay, restoration, or production state.

```text
immutable scheduling proposal
+ explicit caller-supplied review action
+ review episode and reason
        -> pure lifecycle decision
        -> accepted, rejected, deferred, expired, or replaced review state
        -> no consolidation execution
```

A proposal marked accepted is approved for possible future consideration only. Acceptance does not apply the candidate, trigger replay, change stability or plasticity, restore a checkpoint, or grant action authority.

## 2. Mandatory invariants

- Production curiosity remains the sole action authority.
- Lifecycle decisions never execute consolidation.
- Accepted proposals remain non-executable evidence.
- Lifecycle decisions never trigger replay or restoration.
- Lifecycle state never affects live suggestion ranking.
- Lifecycle state never affects bounded advice.
- Lifecycle state never affects growth selection or pressure discharge.
- SQLite remains outside lifecycle cognition.
- Brain persistence remains schema version 3 during this stage.
- No timer, background worker, autonomous queue, or automatic reviewer is permitted.
- Review actions, episode indices, reviewer identities, and reasons are caller-supplied.
- Proposal and candidate evidence remain immutable and inspectable.
- Every state change is deterministic and retains its prior history.
- Rejection, deferral, expiry, and replacement never delete source evidence.

## 3. Planned batches

### Batch 1 — single-proposal review contract

Implement a pure deterministic review over one immutable proposal:

- Accept.
- Reject.
- Defer.
- Explicit reviewer identity.
- Explicit reason code.
- Explicit decision episode.
- Future review episode for deferral.
- Immutable deterministic decision identity.
- Explicitly absent execution authority.

Acceptance requires no evidence mutation, no application path, and exact deterministic output.

### Batch 2 — immutable lifecycle history

Add an in-memory lifecycle record that:

- Starts pending.
- Preserves every review decision.
- Enforces valid transitions.
- Rejects duplicate or conflicting decisions.
- Preserves the original scheduling proposal unchanged.
- Exposes a complete inspectable history.

No persistence change is permitted.

### Batch 3 — deferral, expiry, and replacement

Add caller-driven lifecycle operations for:

- Re-review after a deferral window.
- Explicit expiry.
- Replacement by a newer proposal for the same lesson.
- Stale-proposal and candidate-mismatch rejection.
- Bounded active lifecycle capacity.

Replacement must preserve both old and new proposal identities and may not execute either proposal.

### Batch 4 — synthetic and live-shadow acceptance

Compare lifecycle strategies under controlled evidence change, including:

1. Automatic acceptance.
2. Permanent deferral or no review.
3. Evidence-aware explicit lifecycle management.

Measure stale acceptance, unnecessary rejection, review delay, duplicate decisions, retained history, and determinism.

Run identical live-shadow sessions with lifecycle observation enabled and disabled. Passing requires identical:

- Production actions.
- Prediction errors.
- NDNRA suggestions.
- Live developmental signals.
- Learned graph state.
- Growth state.

No proposal may execute.

### Batch 5 — documentation and closure

- Update architecture and master plan.
- Record all commits and evidence.
- Refresh repository wiki.
- Run final quality gates.
- Produce the proposal-lifecycle handover.
- Reassess whether the stage justifies increasing heuristic readiness from 94% to 95%.

## 4. Batch 1 public contract

The initial implementation should provide:

- `ConsolidationProposalReviewAction`
- `ConsolidationProposalLifecycleStatus`
- `ConsolidationProposalReviewRequest`
- `ConsolidationProposalReviewDecision`
- `ConsolidationProposalReviewPolicy`

Initial statuses:

```text
pending
accepted
rejected
deferred
```

Expiry and replacement are reserved for Batch 3.

## 5. Explicitly out of scope

- Consolidation application.
- Retention replay.
- Checkpoint restoration or rollback.
- Persistent lifecycle queues.
- Schema version 4.
- Automatic review decisions.
- Timers or background jobs.
- Advice or growth influence.
- Route-ranking influence.
- Production action authority.
- Permanent pruning or deletion.

## 6. Stage completion rule

The stage is complete only when proposal review, history, deferral, expiry, and replacement have deterministic synthetic and live-shadow acceptance evidence while preserving all authority and cognition boundaries.

Completing the lifecycle stage justifies 95% heuristic theory-to-integration readiness because all five batches, including synthetic and live-shadow acceptance, passed while preserving every authority boundary. It does not authorize proposal execution and is not a production-readiness claim.

## 7. Closure record

Completed implementation commits:

1. `00ac54c` — single-proposal review contract.
2. `ab5167e` — immutable lifecycle history.
3. `2d5f3c8` — expiry, replacement, stale-input protection, and bounded capacity.
4. `a46b662` — synthetic comparison and live-shadow acceptance.
5. Documentation and closure — the commit containing the stage handover.

Accepted evidence:

- Automatic acceptance produced one stale accepted candidate and blocked the newer proposal.
- Permanent deferral avoided stale acceptance but blocked the newer proposal with four episodes of delay.
- Evidence-aware management deferred the old proposal, replaced it with a newer same-lesson proposal, accepted the current proposal after one episode, preserved two records and three lifecycle events, and produced no stale acceptance, unnecessary rejection, or duplicate decision.
- Live-shadow observation scheduled one proposal, recorded one defer and one accept decision, and preserved two review decisions.
- Production actions, prediction errors, suggestions, developmental signals, graph state, and growth state remained exactly equal to the control.
- Contextual-ledger mutations, consolidation applications, SQLite cognition, and authority violations remained zero.

The next stage requires a new plan and must not connect accepted proposals to execution by assumption.
