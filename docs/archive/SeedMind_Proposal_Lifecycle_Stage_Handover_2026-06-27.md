# SeedMind Consolidation Proposal Lifecycle Stage Handover

Date: 27 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Status: complete
Authority: review-only, research-only, shadow-only
Heuristic theory-to-integration readiness: 95%

## 1. What this stage achieved

SeedMind can now manage the review lifecycle of immutable consolidation proposals without executing consolidation.

```text
immutable scheduling proposal
+ explicit caller review action
+ bounded active lifecycle capacity
+ newer evidence when available
        -> pending, accepted, rejected, or deferred review state
        -> explicit expiry or same-lesson replacement
        -> complete immutable history
        -> no consolidation execution
```

An accepted proposal is approved only for possible future consideration. It does not change stability, plasticity, contextual evidence, replay state, checkpoint state, advice, growth, or production actions.

## 2. Completed batches

1. `00ac54c` — deterministic single-proposal review with accept, reject, and defer decisions.
2. `ab5167e` — immutable lifecycle history and valid transition enforcement.
3. `2d5f3c8` — bounded lifecycle registry with expiry, replacement, stale-input protection, and capacity limits.
4. `a46b662` — deterministic strategy comparison and live-shadow lifecycle acceptance.
5. Documentation and closure — the commit containing this handover.

## 3. Main implementation files

### Review contract

- `src/seedmind/research/ndnra/consolidation_proposal_lifecycle.py`

Provides explicit caller-supplied accept, reject, and defer actions. Every result records reviewer identity, reason, decision episode, optional future review episode, deterministic decision identity, and explicitly absent execution authority.

### Immutable history

- `src/seedmind/research/ndnra/consolidation_proposal_history.py`

Each lifecycle record:

- Starts pending.
- Preserves every decision.
- Requires strictly increasing decision episodes.
- Prevents early review of deferred proposals.
- Treats accepted and rejected states as terminal during this stage.
- Rejects proposal substitution, duplicate decisions, and invalid reconstructed histories.

### Bounded management registry

- `src/seedmind/research/ndnra/consolidation_proposal_management.py`

The immutable in-memory registry supports:

- Bounded active lifecycle capacity.
- At most one active proposal per lesson.
- Explicit expiry.
- Replacement by a different newer proposal for the same lesson.
- Expected-candidate checks that reject stale controller or user-interface state.
- Permanent retention of rejected, expired, and replaced records.

Pending, deferred, and accepted records consume active capacity. Rejected, expired, and replaced records remain archived and release capacity.

### Synthetic lifecycle experiment

- `src/seedmind/research/ndnra/consolidation_proposal_lifecycle_experiment.py`

Compares three strategies under identical proposal evolution:

1. Automatic acceptance.
2. Permanent deferral.
3. Evidence-aware explicit management.

### Live-shadow acceptance

- `src/seedmind/integration/consolidation_proposal_lifecycle_acceptance.py`

Runs two identical SeedMind sessions. The observed session attaches proposal scheduling and lifecycle review after ordinary learning. The control session does not.

The observer creates one proposal, defers it for a bounded review interval, and later marks it accepted for future consideration. It cannot execute the proposal or alter live cognition.

## 4. Synthetic evidence

Additional independent evidence changes the consolidation candidate identity, creating an older proposal and a current proposal for the same lesson.

| Strategy | Stale acceptances | Current proposal blocked | Current review delay | Retained records | Retained history events | Current accepted |
|---|---:|---:|---:|---:|---:|---:|
| Automatic acceptance | 1 | 1 | 4 episodes | 1 | 1 | No |
| Permanent deferral | 0 | 1 | 4 episodes | 1 | 1 | No |
| Evidence-aware explicit | 0 | 0 | 1 episode | 2 | 3 | Yes |

The evidence-aware strategy:

- Deferred the older proposal while evidence was incomplete.
- Replaced it when a newer same-lesson candidate appeared.
- Preserved both proposal identities.
- Accepted only the current proposal.
- Produced no unnecessary rejection.
- Produced no duplicate decision.
- Applied no consolidation.
- Used no SQLite cognition.
- Had no action authority.

This proves bounded lifecycle management under the controlled scenario. It does not prove that executing an accepted proposal is safe.

## 5. Live-shadow evidence

The live acceptance gate evaluated lifecycle observation over eight ordinary learning steps.

It produced:

- One scheduled proposal.
- One defer decision.
- One later accept decision.
- One retained registry record.
- Two retained lifecycle review decisions.

The lifecycle-observed and control sessions had exactly equal:

- Production actions.
- Prediction errors.
- NDNRA suggestions.
- Live developmental signals.
- Learned graph state.
- Growth state.

Acceptance evidence also confirmed:

- Zero contextual-ledger mutations caused by lifecycle management.
- Zero consolidation applications.
- Zero action-authority violations.
- Zero SQLite cognitive dependency.
- ASCII-inspectable reports, registry evidence, and timelines.

## 6. Tests

Main lifecycle tests:

- `tests/unit/test_ndnra_consolidation_proposal_lifecycle.py`
- `tests/unit/test_ndnra_consolidation_proposal_history.py`
- `tests/unit/test_ndnra_consolidation_proposal_management.py`
- `tests/unit/test_ndnra_consolidation_proposal_lifecycle_experiment.py`
- `tests/unit/test_ndnra_consolidation_proposal_lifecycle_acceptance.py`

Closure validation before the documentation commit:

```text
Ruff format: 159 files already formatted
Ruff lint: all checks passed
Mypy strict: no issues in 159 source files
Pytest: 485 passed
Pip check: no broken requirements
Git diff check: passed
```

## 7. Mandatory boundaries

The following remain true:

- Production curiosity is the sole action authority.
- Accepted means approved for possible future consideration only.
- Lifecycle decisions cannot execute consolidation.
- Lifecycle decisions cannot trigger retention replay.
- Lifecycle decisions cannot restore or roll back checkpoints.
- Lifecycle decisions cannot affect route ranking.
- Lifecycle decisions cannot affect live suggestions.
- Lifecycle decisions cannot affect bounded advice.
- Lifecycle decisions cannot affect growth selection or pressure discharge.
- Lifecycle state is in-memory only during this stage.
- Brain persistence remains schema version 3.
- There is no timer, background worker, autonomous reviewer, or persistent lifecycle queue.
- SQLite remains outside lifecycle cognition.
- No permanent pruning or evidence deletion is permitted.

## 8. Readiness reassessment

The heuristic theory-to-integration readiness indicator increases from 94% to 95% because SeedMind now has validated, deterministic, bounded proposal lifecycle management with synthetic and live-shadow evidence.

This indicator is an engineering progress measure. It is not:

- A probability of success.
- A safety certification.
- A production-readiness score.
- Evidence that automatic consolidation execution is safe.
- Evidence that SeedMind is generally intelligent.

## 9. Explicitly deferred work

A separate future stage is required for:

- Restart-safe lifecycle persistence.
- Revalidation of accepted proposals immediately before execution.
- Human-approved consolidation application.
- Cancellation during an attempted application.
- Failure-safe atomic execution.
- Retention replay triggered by an approved application.
- Exact restart and rollback behavior around execution.
- Advice, growth, or production influence.
- Autonomous review or execution.

Do not connect accepted proposals to application by assumption.

## 10. Recommended next stage

The next bounded NDNRA stage should be **restart-safe proposal memory**, not execution.

It should prove that lifecycle records can survive restart while:

- Preserving exact proposal, candidate, decision, reviewer, and reason identities.
- Rejecting corrupt, stale, or mismatched state.
- Rechecking whether accepted proposals remain current after restart.
- Keeping persisted state outside cognition and action selection.
- Maintaining schema migration and complete safe fallback.

Only after restart-safe lifecycle memory passes should human-approved execution be considered.

## 11. Repository workflow

Never push automatically.

The local branch may contain several unpushed lifecycle commits. When back on the development computer, push manually with:

```powershell
Set-Location "D:\Github\SeedMind"
git push
```
