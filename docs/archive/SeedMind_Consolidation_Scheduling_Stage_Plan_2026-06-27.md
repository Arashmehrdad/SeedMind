# SeedMind Consolidation Scheduling Stage Plan

Date: 27 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Stage status: complete
Authority: proposal-only, research-only, shadow-only

## 1. Stage objective

This stage evaluated whether SeedMind can decide **when a consolidation candidate is worth proposing** without executing consolidation or changing any cognitive, advisory, growth, replay, restoration, or production state.

The completed flow is:

```text
caller-supplied episode context
+ contextual mastery evidence
+ explicit lesson requests
+ active-candidate capacity
        -> pure scheduling decisions
        -> deterministic portfolio ranking
        -> bounded non-authoritative proposals
```

There is no internal clock, background task, timer, persistent queue, or automatic executor.

## 2. Preserved invariants

- Production curiosity remains the sole action authority.
- Scheduling proposals never execute consolidation.
- Scheduling proposals never trigger replay.
- Scheduling proposals never restore checkpoints.
- Scheduling values never affect live suggestion ranking.
- Scheduling values never affect bounded advice.
- Scheduling values never affect growth selection or pressure discharge.
- SQLite remains outside scheduling decisions.
- The brain persistence schema remains version 3.
- All episode indices and completion records are caller-supplied deterministic inputs.
- Every lesson decision retains its eligibility and rejection evidence.
- Active-candidate and per-evaluation proposal capacity remain explicit and bounded.
- Non-selected candidates remain visible and are not deleted or merged.

## 3. Completed batches

### Batch 1 — single-lesson proposal contract

Commit: `1c2b3e9`

Added deterministic first-window, cooldown, active-candidate, and capacity decisions. Proposals are immutable and explicitly reject execution authority.

### Batch 2 — multi-lesson prioritisation

Commit: `3940dc9`

Added deterministic ranking across several lesson requests. Every per-lesson result remains visible, while only a bounded number of ready proposals are selected for review.

Priority is based on overdue duration, mastery score, effective independent support, and stable candidate identity.

### Batch 3 — synthetic scheduling experiment

Commit: `0b52a82`

Compared fixed-interval, eligibility-only, and evidence-aware bounded scheduling under identical evidence arrival.

| Strategy | Proposals | False | Redundant | Missed eligible episodes | Capacity pressure | Precision |
|---|---:|---:|---:|---:|---:|---:|
| Fixed interval | 12 | 7 | 3 | 4 | 8 | 0.4167 |
| Eligibility only | 15 | 0 | 13 | 0 | 6 | 1.0000 |
| Evidence-aware bounded | 2 | 0 | 0 | 0 | 0 | 1.0000 |

The balanced method proposed both mastered lessons exactly once, never proposed the weak lesson, caused no delay, and stayed within capacity.

### Batch 4 — live-shadow proposal acceptance

Commit: `e7a5570`

Ran identical SeedMind sessions with and without scheduling observation. The sessions produced exactly equal:

- Production actions.
- Prediction errors.
- NDNRA suggestions.
- Live developmental signals.
- Learned graph state.
- Growth state.

Across eight scheduling evaluations, the observer produced one proposal for one eligible candidate, then suppressed repeats while it remained active. It changed no contextual evidence, applied no consolidation, used no SQLite cognition, and had zero authority violations.

### Batch 5 — documentation and closure

Completed in the closure commit containing this updated record.

- Architecture updated with proposal-only scheduling.
- Master implementation plan updated with commits and evidence.
- README current phase updated.
- Final scheduling-stage handover added.
- Repository wiki refreshed.
- Full quality gates rerun.

## 4. Public contracts

The stage added:

- `ConsolidationScheduleRequest`
- `ConsolidationSchedulingContext`
- `ConsolidationSchedulingPolicy`
- `ConsolidationScheduleDecision`
- `ConsolidationScheduleProposal`
- `ConsolidationScheduleStatus`
- `ConsolidationPortfolioItem`
- `ConsolidationPortfolioPolicy`
- `ConsolidationPortfolioDecision`
- Scheduling experiment result and export contracts.
- Live-shadow scheduling acceptance result and export contracts.

Default single-lesson policy values are:

```text
first eligible episode: 100
minimum interval after completion: 100 episodes
maximum simultaneous active candidates: 1
```

These remain policy inputs, not an autonomous schedule.

## 5. Explicitly out of scope

- Automatic consolidation application.
- Automatic replay.
- Automatic rollback or restoration.
- OS or framework timers.
- Background jobs.
- Persistent scheduling queues.
- Schema version 4.
- Live ranking influence.
- Advice or growth influence.
- Production action authority.
- Permanent pruning or deletion.

## 6. Completion decision

The stage passed deterministic synthetic comparison and live-shadow invariance acceptance while preserving all authority and cognition boundaries.

The completed scheduler may identify, rank, and export review proposals. It may not accept or execute them. Moving from proposal generation to automatic action requires a separately approved stage with new fallback, persistence, restart, rejection, and rollback evidence.

The heuristic readiness indicator remains 94%. This stage improves scheduling evidence and inspectability; it is not a production-readiness claim.
