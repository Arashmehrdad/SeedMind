# SeedMind Controlled Replay and Restoration Stage Handover

Date: 28 June 2026  
Repository: `D:\Github\SeedMind`  
Branch: `main`  
Status: complete  
Authority: explicit-human-approval only, research-only, bounded replay and restoration  
Legacy narrow-scope theory-to-integration readiness: 98%  
Expanded developmental architecture progress: 79%

## 1. What this stage achieved

SeedMind can now revisit one exact named real activity for bounded accessibility maintenance and can restore one exact complete active brain state, while keeping both operations human-approved, single-use, restart-safe, inspectable, and outside production action authority.

```text
exact current evidence
+ exact source evidence or checkpoint
+ explicit human approval
+ bounded immutable permit
+ immediate preoperation revalidation
        -> one replay or restoration operation
        -> consumed permit plus exact receipt
        -> complete durable old or new envelope
        -> no autonomous trigger
```

Replay does not manufacture facts, mastery, independent evidence, action authority, or production behaviour. Restoration replaces the complete active state while preserving the current monotonic operation audit so older checkpoints cannot revive used approvals.

## 2. Completed implementation sequence

1. `84027a` — exact controlled replay/restoration approval contracts.
2. `861259` — immutable issued, cancelled, expired, and consumed permit lifecycle.
3. `8a9d887` — bounded in-memory retention replay of exact real activity.
4. `0d53286`, `88943dd`, and `24bd2b7` — schema-6 replay/restoration persistence, active-state checksum separation, durable replay, and accepted-scope correction.
5. `f0d5ba2` — exact complete-state checkpoint restoration.
6. Live acceptance, documentation, handover, and closure — the commit containing this document.

## 3. Main implementation files

### Approval and lifecycle

- `src/seedmind/research/ndnra/controlled_replay_restoration_approval.py`
- `src/seedmind/research/ndnra/controlled_replay_restoration_permit_lifecycle.py`

Approval identifies one exact operation, target, source checkpoint, current checkpoint, evidence set, validity window, human approver, and reason. The permit itself carries no replay, restoration, cognition, or production-action authority.

Lifecycle state is one of:

- `issued`
- `cancelled`
- `expired`
- `consumed`

One permit identity may enter only one terminal state. Recreated content cannot bypass retained lifecycle identity.

### Bounded replay

- `src/seedmind/research/ndnra/controlled_retention_replay.py`
- `src/seedmind/research/ndnra/controlled_retention_replay_durable.py`

Replay requires caller-selected work items that reconstruct exact named real activity already present in the activity ledger. It may reduce dormancy only. It cannot change:

- factual confidence;
- mastery;
- independent evidence counts;
- eligibility;
- growth pressure;
- residual history;
- real last-active state;
- production actions.

The durable wrapper persists the consumed permit, exact receipt, replay activity history, and resulting dormancy state atomically.

### Exact restoration

- `src/seedmind/research/ndnra/controlled_checkpoint_restoration.py`

Restoration accepts only a separate, checksum-verified, native schema-6 source. It replaces together:

- graph state;
- growth state;
- consolidation state;
- proposal lifecycle;
- execution state;
- active activity memory.

It preserves the destination's current monotonic permit and receipt audit and requires that audit to contain all source audit history. Partial restoration is forbidden.

### Persistence

- `src/seedmind/research/ndnra/controlled_replay_restoration_persistence.py`
- `src/seedmind/research/ndnra/persistence.py`

Schema 6 stores:

- active activity history;
- replay/restoration permit lifecycle records;
- replay receipts;
- restoration receipts;
- zero automatic replay/restoration counters;
- explicit absence of replay, restoration, cognition, and production-action authority.

The complete-envelope checksum protects all persisted content. A separate active-state checksum identifies graph-adjacent restorable state without being invalidated by audit-only permit persistence. Schema 5 migrates to an explicit empty replay/restoration checkpoint.

### Live acceptance

- `src/seedmind/integration/controlled_replay_restoration_acceptance.py`
- `tests/unit/test_ndnra_controlled_replay_restoration_acceptance.py`

The acceptance gate exports:

- `controlled_replay_restoration_report.json`
- `controlled_replay_timeline.csv`
- `controlled_restoration_timeline.csv`
- `controlled_replay_restoration_receipts.json`

These are ASCII audit artifacts suitable for later observatory ingestion. No SQLite cognitive path is introduced.

## 4. Live replay acceptance

The gate compares an unreplayed control with an otherwise identical replayed state under the same production curiosity, trainer, nursery seed, and developmental signals.

Confirmed equal:

- production actions;
- prediction errors;
- developmental signals;
- learned graph state;
- all non-dormancy growth state.

Replay may change accessibility and therefore may change non-authoritative shadow suggestions. This is the intended bounded effect. Suggestions remain observers and cannot choose production actions.

Replay acceptance recorded:

```text
1 explicit human replay approval
1 consumed replay permit
1 replay receipt
0 automatic replay
0 confidence change
0 mastery change
0 learning authority
0 action-selection authority
0 production-action authority
```

## 5. Live restoration acceptance

The gate compares the exact source checkpoint with the restored destination under an identical later live-shadow session.

Confirmed equal:

- active-state checksum;
- production actions;
- NDNRA suggestions;
- prediction errors;
- developmental signals;
- learned graph state;
- final growth state.

Restoration acceptance recorded:

```text
1 explicit human restoration approval
1 consumed restoration permit
1 restoration receipt
0 automatic restoration
0 partial restorations
0 cognitive authority
0 production-action authority
```

## 6. Failure, restart, and lifecycle evidence

The stage proves:

- stale operation evidence is rejected without mutation;
- a consumed replay permit cannot be reused after restart;
- a consumed restoration permit cannot be reused after restart;
- cancelled permits remain terminal;
- expired permits remain terminal;
- interruption before replay persistence preserves the exact old envelope;
- interruption after restoration atomic replacement recovers the complete new envelope;
- corrupt restoration sources are rejected without mutating the current store;
- replay and restoration receipts round-trip exactly;
- temporary files do not remain;
- source audit divergence blocks restoration;
- migrated, fallback, same-path, stale, expired, and mismatched sources remain rejected.

## 7. Mandatory authority boundaries

The following remain non-negotiable:

- Production curiosity is the sole production action authority.
- Replay work selection is explicit and caller supplied; there is no autonomous memory-selection worker.
- Restoration requires explicit human approval and exact current/source evidence.
- Permits and receipts are evidence, not executors.
- Persistence reconstructs evidence; it is not cognition.
- SQLite remains scientific storage and audit infrastructure only.
- No timers, background workers, queues, automatic approval, automatic permit issuance, automatic replay, or automatic restoration exist.
- Replay cannot directly update confidence, mastery, competence, growth pressure, advice authority, route ranking, or production actions.
- Restoration cannot partially recover authority-bearing state or revive terminal approvals.
- Every failed operation leaves the exact old state or produces complete safe fallback.

## 8. Validation

Closure validation:

```text
Ruff formatting: 198 files
Ruff lint: passed
Mypy: no issues in 198 source files
Pytest: 687 passed
Pip check: no broken requirements
Git diff check: passed
```

The exact counts should be re-recorded if later documentation or wiki generation changes the file count before the closure commit.

## 9. Readiness reassessment

The legacy narrow-scope theory-to-integration marker increases from 97% to 98% because controlled replay and exact restoration now pass:

- explicit human authorization;
- dual evidence binding;
- bounded single-use lifecycle;
- atomic durable persistence;
- restart protection;
- stale, duplicate, cancellation, expiry, interruption, and corruption tests;
- live production-action and cognition invariance;
- inspectable export evidence;
- repository-wide quality gates.

The expanded developmental architecture marker increases from 78% to 79%. This is the relevant overall design marker after the project scope expanded to include learned consequence modelling, dreaming, imagined route optimisation, and safe experiment promotion.

Neither marker is production readiness, commercial readiness, safety certification, AGI progress, or approval for autonomous replay/restoration.

## 10. Recommended next stage

The next bounded stage is the learned consequence model:

- predict relevant next state and effects from context plus action;
- represent short action order and combinations;
- report uncertainty and evidence coverage;
- compare imagined or predicted consequences with later real outcomes;
- correct overconfidence without turning imagination into fact;
- preserve production curiosity as sole action authority.

Bounded dreaming and optimiser-driven route discovery must follow only after the consequence model is falsifiable, persisted safely, and accepted separately.

## 11. Repository workflow

Never push automatically.

After the closure commit, push manually only with explicit authorization:

```powershell
Set-Location "D:\Github\SeedMind"
git push
```
