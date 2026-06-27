# SeedMind Restart-Safe Proposal Memory Stage Handover

Date: 28 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Status: complete
Authority: persistence-only, review-only, research-only, shadow-only
Heuristic theory-to-integration readiness: 96%

## 1. What this stage achieved

SeedMind can now preserve the complete consolidation proposal lifecycle across process restart without turning persistence into cognition, execution authority, or an autonomous queue.

```text
immutable proposal lifecycle registry
+ versioned lifecycle checkpoint
+ checksum-protected schema-4 brain envelope
+ restart-time evidence revalidation
        -> exact lifecycle reconstruction
        -> current, stale, superseded, or invalid-for-review evidence
        -> complete fallback on corrupt state
        -> no consolidation execution
```

The persisted state records what was proposed, reviewed, and decided. It does not decide what to remember, select actions, apply consolidation, trigger replay, restore checkpoints, influence advice, or discharge growth pressure.

## 2. Completed batches

1. `555efe7` — exact versioned proposal-lifecycle checkpoint codec.
2. `2b0fb0a` — schema-4 atomic brain persistence and migrations from schemas 1–3.
3. `b1ec4a3` — pure restart-time proposal revalidation.
4. `7280954` — complete restart, corruption, stale-proposal, and live-shadow acceptance.
5. Documentation and closure — the commit containing this handover.

## 3. Main implementation files

### Lifecycle checkpoint codec

- `src/seedmind/research/ndnra/consolidation_proposal_persistence.py`

The codec reconstructs and validates:

- Scheduling proposals.
- Consolidation candidates.
- Mastery snapshots.
- Source-event identities.
- Review decisions and deterministic decision identities.
- Ordered lifecycle history.
- Expiry and replacement decisions.
- Active and archived records.
- Active-capacity limits.
- Exact replacement links.

Malformed, internally inconsistent, or authority-bearing snapshots fail reconstruction.

### Schema-4 brain persistence

- `src/seedmind/research/ndnra/persistence.py`

Brain schema version 4 atomically stores:

- Learned graph state.
- Growth state.
- Consolidation checkpoint state.
- Proposal-lifecycle checkpoint state.

The existing temporary-file, flush, file-sync, atomic-replace, deterministic encoding, and outer checksum protections remain in force.

Migration behaviour is explicit:

| Stored brain schema | Consolidation checkpoint | Proposal lifecycle checkpoint |
|---|---|---|
| 1 | Empty migration target | Empty migration target |
| 2 | Empty migration target | Empty migration target |
| 3 | Preserved | Empty migration target |
| 4 | Preserved | Preserved and validated |

No lifecycle state is inferred from unrelated graph or memory evidence during migration.

### Restart-time revalidation

- `src/seedmind/research/ndnra/consolidation_proposal_revalidation.py`

The pure revalidation policy evaluates active restored proposals against present evidence and classifies them as:

- `current` — all required evidence remains valid and the reconstructed candidate is exactly unchanged.
- `stale` — evidence remains valid but additional evidence changes the current candidate identity.
- `superseded` — a supplied newer same-lesson proposal exactly contains the current candidate.
- `invalid_for_review` — source evidence, broad mastery, contradiction state, assemblies, routes, or other eligibility conditions no longer pass.

Revalidation does not mutate the registry, contextual ledger, lifecycle status, or stored review history.

### Restart and live-shadow acceptance

- `src/seedmind/integration/restart_safe_proposal_memory_acceptance.py`

The acceptance gate combines:

- Exact clean restart.
- Legacy migration from schemas 1–3.
- Outer-checksum corruption.
- Relational lifecycle corruption.
- Clean current-proposal revalidation.
- Stale accepted-proposal detection after new independent evidence.
- Eight-step live-shadow comparison against an identical control.
- ASCII report, decision, and timeline exports.

## 4. Exact restart evidence

One accepted proposal lifecycle was saved with the learned graph and growth state, then loaded from schema 4.

The restart preserved exactly:

- Graph snapshot.
- Growth state.
- Proposal identity.
- Candidate identity.
- Lesson identity.
- Reviewer identity.
- Review reason.
- Deterministic review-decision identity.
- Ordered review history.
- Lifecycle status.
- Registry capacity and active-record relationships.

The clean restart passed checksum verification, used no fallback, and left no temporary file behind.

## 5. Migration and corruption evidence

Schemas 1, 2, and 3 loaded successfully with an explicit empty lifecycle checkpoint. Schema 3 also preserved its existing consolidation checkpoint.

Two schema-4 corruption paths were tested:

1. Invalid outer checksum.
2. Internally inconsistent lifecycle relationships with a recomputed valid outer checksum.

Both produced a complete fresh-state fallback containing:

- Empty graph.
- Default growth state.
- Empty consolidation checkpoint.
- Empty proposal-lifecycle checkpoint.

No partial graph, consolidation, lifecycle, or review state survived either failure.

## 6. Current and stale proposal evidence

Immediately after clean restart, the accepted proposal revalidated as `current` because:

- Every original source event remained available.
- Broad mastery remained valid.
- Contradictions remained absent.
- Required assemblies and routes remained available.
- Reconstructing eligibility produced the exact persisted candidate.

After one additional independent supporting experience was added, the proposal revalidated as `stale` because the current candidate identity changed.

The stale result did not:

- Remove the persisted proposal.
- Change its accepted lifecycle status.
- Rewrite its review history.
- Replace it automatically.
- Reject or expire it automatically.
- Apply consolidation.

## 7. Live-shadow evidence

The acceptance gate compared two identical schema-4 restarts over eight ordinary learning transitions:

- Control: identical graph and growth state with an empty lifecycle checkpoint.
- Observed: identical graph and growth state with one persisted accepted lifecycle and post-transition revalidation.

Both sessions had exactly equal:

- Production actions.
- Prediction errors.
- NDNRA suggestions.
- Live developmental signals.
- Final learned graph state.
- Final growth state.

All eight observed revalidations classified the proposal as current and caused:

```text
0 registry mutations
0 revalidation-caused ledger mutations
0 consolidation applications
0 replay triggers
0 restoration triggers
0 SQLite cognitive operations
0 action-authority violations
```

## 8. Tests

Main restart-safe proposal memory tests:

- `tests/unit/test_ndnra_consolidation_proposal_persistence.py`
- `tests/unit/test_ndnra_proposal_lifecycle_brain_persistence.py`
- `tests/unit/test_ndnra_consolidation_proposal_revalidation.py`
- `tests/unit/test_ndnra_restart_safe_proposal_memory_acceptance.py`

Closure validation before the documentation commit:

```text
Ruff format: 166 files already formatted
Ruff lint: all checks passed
Mypy strict: no issues in 166 source files
Pytest: 525 passed
Pip check: no broken requirements
Git diff check: passed
```

## 9. Mandatory boundaries

The following remain true:

- Production curiosity remains the sole production action authority.
- Accepted means approved only for possible future consideration.
- Persistence stores evidence; it does not perform cognitive lookup or selection.
- Restart revalidation produces evidence only.
- Persistence and revalidation cannot create review decisions.
- Persistence and revalidation cannot expire or replace proposals automatically.
- Persistence and revalidation cannot execute consolidation.
- Persistence and revalidation cannot trigger retention replay.
- Persistence and revalidation cannot restore or roll back consolidation checkpoints.
- Persistence and revalidation cannot affect route ranking.
- Persistence and revalidation cannot affect live suggestions or bounded advice.
- Persistence and revalidation cannot affect growth selection or pressure discharge.
- SQLite remains outside persistence reconstruction and revalidation cognition.
- There is no timer, background worker, autonomous reviewer, or persistent execution queue.
- No permanent pruning or source-evidence deletion is permitted.

## 10. Readiness reassessment

The heuristic theory-to-integration readiness indicator increases from 95% to 96% because SeedMind now has validated restart-safe proposal memory, exact schema migration, complete corruption fallback, stale accepted-proposal detection, and live-shadow invariance.

This indicator is an engineering progress measure. It is not:

- A probability of success.
- A safety certification.
- A commercial or production-readiness score.
- Approval for consolidation execution.
- Evidence that automatic replay or restoration is safe.
- Evidence that SeedMind is generally intelligent.

## 11. Explicitly deferred work

A separate future stage is required for:

- Explicit human-approved consolidation execution.
- Final proposal revalidation immediately before execution.
- Atomic application with cancellation and failure-safe fallback.
- Retention replay after an approved application.
- Exact restart semantics during interrupted execution.
- Exact rollback and restoration after failed execution.
- Advice, route-ranking, growth, or production-action influence.
- Autonomous review or execution.

Do not connect persisted accepted proposals to consolidation application by assumption.

## 12. Recommended next stage

The next bounded NDNRA stage may evaluate **human-approved consolidation execution**, but only as a separately gated, non-autonomous capability.

It should require:

- An explicit human approval token tied to one exact current proposal.
- Immediate revalidation before application.
- Single-use execution identity.
- Atomic state transition.
- Cancellation before commit.
- Complete failure fallback.
- Exact audit evidence.
- No automatic replay, advice, growth, or action influence.

SeedMind main-project delivery remains the priority. The execution stage should stay narrowly scoped to making NDNRA safe and usable by the main system rather than expanding into open-ended research.

## 13. Repository workflow

Never push automatically.

After the closure commit, push manually with:

```powershell
Set-Location "D:\Github\SeedMind"
git push
```
