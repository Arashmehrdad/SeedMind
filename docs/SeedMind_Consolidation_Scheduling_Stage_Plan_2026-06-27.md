# SeedMind Consolidation Scheduling Stage Plan

Date: 27 June 2026  
Repository: `D:\Github\SeedMind`  
Branch: `main`  
Stage status: active  
Authority: proposal-only, research-only, shadow-only

## 1. Stage objective

This stage evaluates whether SeedMind can decide **when a consolidation candidate is worth proposing** without executing consolidation or changing any cognitive, advisory, growth, replay, restoration, or production state.

The stage begins from the completed retention-gated consolidation subsystem and adds only pure scheduling evidence.

```text
caller-supplied episode context
+ contextual mastery evidence
+ explicit lesson request
+ active-candidate capacity
        -> pure scheduling decision
        -> no proposal, or immutable non-authoritative proposal
```

No internal clock, background task, episode hook, timer, scheduler loop, or automatic executor is permitted.

## 2. Mandatory invariants

- Production curiosity remains the sole action authority.
- Scheduling proposals never execute consolidation.
- Scheduling proposals never trigger replay.
- Scheduling proposals never restore checkpoints.
- Scheduling values never affect live suggestion ranking.
- Scheduling values never affect bounded advice.
- Scheduling values never affect growth selection or pressure discharge.
- SQLite remains outside scheduling decisions.
- The brain persistence schema is not changed during the first scheduling batches.
- All episode indices and completion records are caller-supplied deterministic inputs.
- Every decision retains the underlying consolidation eligibility result and rejection evidence.
- Active-candidate capacity is explicit and bounded.

## 3. Planned batches

### Batch 1 — single-lesson proposal contract

Implement:

- Explicit schedule request.
- Caller-owned episode context.
- First eligible episode.
- Minimum interval after a completed consolidation.
- Active-candidate identity and capacity checks.
- Immutable proposal identifiers.
- Explicitly absent execution authority.

Acceptance requires deterministic decisions, no ledger mutation, no timer or executor dependencies, and full eligibility evidence retention.

### Batch 2 — multi-lesson prioritisation

Add a pure portfolio policy that:

- Evaluates several explicitly supplied lesson requests.
- Preserves every per-lesson decision.
- Ranks only proposal-ready candidates.
- Applies a bounded proposal count.
- Uses stable deterministic tie-breaking.
- Prevents one lesson from silently erasing another.

No proposal may execute.

### Batch 3 — synthetic scheduling experiment

Compare at least:

1. Fixed interval proposal windows.
2. Eligibility-only proposal checks.
3. Evidence-aware bounded proposal scheduling.

Measure proposal precision, redundant proposals, missed eligible windows, active-capacity pressure, and determinism under controlled evidence arrival. The experiment must not apply candidates.

### Batch 4 — live-shadow proposal acceptance

Run identical live-shadow sessions with scheduling observation enabled and disabled. Passing requires identical:

- Production actions.
- Prediction errors.
- NDNRA suggestions.
- Learned graph state.
- Growth state.

Export inspectable proposal-only evidence. No checkpoint application or autonomous scheduling is permitted.

### Batch 5 — documentation and closure

- Update architecture and master plan.
- Record all commits and evidence.
- Refresh repository wiki.
- Run final quality gates.
- Produce the scheduling-stage handover.

## 4. Batch 1 contract

The first implementation uses:

- `ConsolidationScheduleRequest`
- `ConsolidationSchedulingContext`
- `ConsolidationSchedulingPolicy`
- `ConsolidationScheduleDecision`
- `ConsolidationScheduleProposal`
- `ConsolidationScheduleStatus`

Default proposal cadence mirrors the current research plan:

```text
first eligible episode: 100
minimum interval after completion: 100 episodes
maximum simultaneous active candidates: 1
```

These defaults are policy inputs only. They do not create an episode hook or automatic schedule.

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

## 6. Stage completion rule

The stage is complete only when proposal-only scheduling has deterministic synthetic and live-shadow acceptance evidence while preserving all authority and cognition boundaries. A successful scheduling stage still does not authorize automatic consolidation execution.
