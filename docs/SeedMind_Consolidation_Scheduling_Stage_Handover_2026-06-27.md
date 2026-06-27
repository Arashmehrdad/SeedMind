# SeedMind Consolidation Scheduling Stage Handover

Date: 27 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Status: complete
Authority: proposal-only, research-only, shadow-only

## 1. What this stage achieved

SeedMind can now identify when a mastered lesson is worth presenting as a consolidation candidate and can rank several candidates for review.

It cannot accept or execute those proposals.

```text
contextual mastery evidence
+ caller-supplied episode timing
+ explicit lesson requests
+ active proposal capacity
        -> pure per-lesson decisions
        -> deterministic ranking
        -> bounded non-authoritative review proposals
```

There is no internal clock, timer, background process, persistent queue, replay trigger, or consolidation executor.

## 2. Completed batches

1. `1c2b3e9` — single-lesson scheduling proposal contract.
2. `3940dc9` — multi-lesson prioritisation and bounded proposal selection.
3. `0b52a82` — synthetic comparison of three scheduling strategies.
4. `e7a5570` — live-shadow proposal-only acceptance.
5. Documentation and closure — the commit containing this handover.

## 3. Main implementation files

### Single-lesson scheduling

- `src/seedmind/research/ndnra/consolidation_scheduling.py`

This policy checks whether a lesson is ready to be proposed. It supports:

- A first eligible review point.
- A minimum interval after a previously completed consolidation.
- Duplicate-active-candidate suppression.
- A maximum number of active candidates.
- Immutable deterministic proposal identities.
- Explicitly absent execution authority.

All timing values are supplied by the caller as episode numbers.

### Multi-lesson prioritisation

- `src/seedmind/research/ndnra/consolidation_portfolio.py`

This policy evaluates several explicit lesson requests, preserves every result, ranks proposal-ready candidates, and selects only a bounded number for review.

Priority uses:

1. How long the proposal has been due.
2. Mastery score.
3. Effective independent support.
4. Stable candidate identity.

Unselected candidates remain visible. They are not deleted, merged, or treated as failed learning.

### Synthetic experiment

- `src/seedmind/research/ndnra/consolidation_scheduling_experiment.py`

The experiment compares fixed-interval, eligibility-only, and evidence-aware bounded scheduling under identical evidence arrival.

### Live-shadow acceptance

- `src/seedmind/integration/consolidation_scheduling_acceptance.py`

The live acceptance gate runs two identical SeedMind sessions. One session has no scheduler. The other runs scheduling observation after each normal learning step.

The observer may produce review proposals, but it cannot change the transition, graph, growth state, or production action.

## 4. Synthetic evidence

The default controlled experiment produced:

| Strategy | Proposals | False | Redundant | Missed eligible episodes | Capacity pressure | Precision |
|---|---:|---:|---:|---:|---:|---:|
| Fixed interval | 12 | 7 | 3 | 4 | 8 | 0.4167 |
| Eligibility only | 15 | 0 | 13 | 0 | 6 | 1.0000 |
| Evidence-aware bounded | 2 | 0 | 0 | 0 | 0 | 1.0000 |

The evidence-aware bounded method:

- Proposed both genuinely mastered lessons once each.
- Never proposed the weak lesson.
- Introduced no delay.
- Produced no duplicates.
- Stayed within proposal capacity.

This is proposal-quality evidence only. It does not prove that automatically executing the proposals would be safe or useful.

## 5. Live-shadow evidence

The live acceptance test performed eight scheduling evaluations.

The scheduled and unscheduled sessions had exactly equal:

- Production actions.
- Prediction errors.
- NDNRA suggestions.
- Live developmental signals.
- Learned graph state.
- Growth state.

The observer produced one proposal for one eligible candidate. Every later evaluation recognised that the same candidate was already active and produced no duplicate proposal.

Acceptance evidence also confirmed:

- Zero contextual-ledger mutations caused by scheduling.
- Zero consolidation applications.
- Zero action-authority violations.
- Zero SQLite cognitive dependency.
- ASCII-inspectable reports and timelines.

## 6. Tests

Main scheduling tests:

- `tests/unit/test_ndnra_consolidation_scheduling.py`
- `tests/unit/test_ndnra_consolidation_portfolio.py`
- `tests/unit/test_ndnra_consolidation_scheduling_experiment.py`
- `tests/unit/test_ndnra_consolidation_scheduling_acceptance.py`

Verified closure gates:

```text
Ruff format: 149 files already formatted
Ruff lint: all checks passed
Mypy strict: no issues in 149 source files
Pytest: 440 passed
Pip check: no broken requirements
Git diff check: passed after removing one documentation trailing-space issue
```

## 7. Mandatory boundaries

The following remain true:

- Production curiosity is the sole action authority.
- Scheduling proposals cannot execute consolidation.
- Scheduling proposals cannot trigger retention replay.
- Scheduling proposals cannot restore or roll back checkpoints.
- Scheduling cannot affect live suggestion ranking.
- Scheduling cannot affect bounded advice.
- Scheduling cannot affect growth selection or pressure discharge.
- SQLite remains outside scheduling cognition.
- Brain persistence remains schema version 3.
- There is no autonomous or persistent scheduling queue.
- Non-selected candidates and rejection reasons remain inspectable.
- No permanent pruning or deletion is permitted.
- The heuristic readiness indicator remains 94%.

## 8. Explicitly deferred work

A future stage would be required for any of the following:

- Human or policy acceptance of a scheduling proposal.
- Automatic consolidation application.
- Automatic retention replay.
- Persistent proposal queues across restart.
- Autonomous proposal rejection, expiry, or replacement.
- Advice or growth influence.
- Production action influence.
- Automatic rollback or restoration.

Do not connect proposal generation to application by assumption.

## 9. Documentation updated in closure

- `README.md`
- `docs/SeedMind_Master_Implementation_Plan_v0.1.md`
- `docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md`
- `docs/SeedMind_Consolidation_Scheduling_Stage_Plan_2026-06-27.md`
- `docs/SeedMind_Consolidation_Stage_Handover_2026-06-27.md`
- Repository-local CodexBridge wiki.

## 10. Recommended next decision

The next stage should not automatically connect proposals to consolidation execution.

The safest next research direction is a **proposal lifecycle experiment** that remains non-authoritative. It could test explicit human or policy responses such as accept, reject, defer, expire, or replace while still applying nothing.

Before any accepted proposal can execute consolidation, SeedMind needs separate evidence for persistence across restart, stale-proposal detection, contradiction checks before execution, failure fallback, cancellation, and exact rollback.

## 11. Repository workflow

Never push automatically.

After the closure commit, push manually with:

```powershell
Set-Location "D:\Github\SeedMind"
git push
```
