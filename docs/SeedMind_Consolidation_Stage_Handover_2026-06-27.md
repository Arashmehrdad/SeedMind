# SeedMind Retention-Gated Consolidation Stage Handover

Date: 27 June 2026  
Repository: `D:\Github\SeedMind`  
Branch: `main`  
Status: bounded consolidation research stage complete; research-only and shadow-only

## 1. Scope completed

This stage implemented a complete falsifiable path from contextual mastery to reversible persisted consolidation without granting cognitive or production authority.

```text
contextual mastery
-> pure consolidation eligibility
-> bounded isolated application
-> overlapping-learning interference experiment
-> retention-gated exact-source replay
-> contradiction-driven reopening
-> candidate-scoped atomic restoration
-> schema-v3 checkpoint and audit persistence
-> live-shadow invariance acceptance
```

The production curiosity controller remains the sole action authority.

## 2. Batch and commit sequence

1. `15e02be` — add NDNRA consolidation eligibility.
2. `2ca0efe` — apply bounded NDNRA consolidation.
3. `a404b32` — add NDNRA consolidation interference experiment.
4. `af539ca` — add NDNRA contradiction reopening.
5. `d1fbafb` — persist NDNRA consolidation checkpoints.
6. `8ec6637` — add NDNRA consolidation shadow acceptance.
7. Documentation and acceptance closure — the commit containing this handover.

## 3. Core implementation files

### Eligibility and application

- `src/seedmind/research/ndnra/consolidation.py`
- `src/seedmind/research/ndnra/consolidation_application.py`

Eligibility is pure and deterministic. Application is bounded, atomic, identity-preserving, and isolated from contextual graph cognition.

### Interference and replay experiment

- `src/seedmind/research/ndnra/consolidation_interference_experiment.py`

The experiment compares no consolidation, naive consolidation, and retention-gated replay under overlapping old/new learning. Replay uses exact candidate source event IDs only, is triggered below a retention threshold, is bounded to one replay per new-learning step, and does not create contextual traces or inflate mastery.

### Reopening and restoration

- `src/seedmind/research/ndnra/consolidation_reopening.py`

Reopening requires a new independent contradiction plus measurable degradation. Restoration is candidate-scoped and atomic. It rejects stale, mismatched, ineligible, and repeated attempts while preserving all source and contradiction evidence.

### Persistence

- `src/seedmind/research/ndnra/consolidation_persistence.py`
- `src/seedmind/research/ndnra/persistence.py`

Brain schema version is 3. `NDNRAConsolidationCheckpoint` stores current bounded state, active application records required for later restoration, and compact completed-restoration audit records. Schema versions 1 and 2 migrate to an explicit empty checkpoint. Invalid relationships cause complete safe fallback.

### Live-shadow acceptance

- `src/seedmind/integration/consolidation_acceptance.py`

The acceptance gate builds qualifying mastery on assemblies that exist in the live graph, persists an active checkpoint, restarts identical sessions with and without checkpoint carriage, and proves that production actions, prediction errors, NDNRA suggestions, learned graph state, and action authority are unchanged. A later contradiction then reopens and restores the loaded candidate, and the completed audit is persisted again.

## 4. Main tests

- `tests/unit/test_ndnra_consolidation.py`
- `tests/unit/test_ndnra_consolidation_application.py`
- `tests/unit/test_ndnra_consolidation_interference.py`
- `tests/unit/test_ndnra_consolidation_reopening.py`
- `tests/unit/test_ndnra_consolidation_persistence.py`
- `tests/unit/test_ndnra_consolidation_acceptance.py`

The last behavioral validation before documentation closure reported:

```text
Ruff format: 141 files formatted
Ruff lint: all checks passed
Mypy strict: no issues in 141 source files
Pytest: 408 passed
Pip check: no broken requirements
Git diff check: passed
```

Run the full gates again after any future change.

## 5. Deterministic interference evidence

The default interference experiment produces these representative outcomes:

| Condition | Old lesson after | New lesson after | Interpretation |
|---|---:|---:|---|
| No consolidation | approximately 0.4928 | approximately 0.9163 | strong new learning, substantial forgetting |
| Naive consolidation | approximately 0.5526 | approximately 0.8564 | better retention, slower new learning |
| Retention-gated replay | approximately 0.7329 | approximately 0.7343 | strongest minimum joint score |

The retention-gated condition performs seven bounded replays in the default deterministic configuration. All replay triggers occur below the configured old-retention threshold, and replay sources are a subset of the candidate's exact source event IDs.

## 6. Architectural invariants

The following constraints are mandatory:

- NDNRA remains research-only, shadow-only, and non-authoritative.
- Production curiosity retains action authority.
- SQLite is audit/debug infrastructure only and is never cognition, replay selection, eligibility, route ranking, retention evaluation, reopening, restoration, or action selection.
- Only exact event identity is deduplicated.
- Legitimate repetitions, correlated copies, contradictions, routes, and source references remain preserved.
- Correlated copies cannot multiply independent support.
- Severe one-shot evidence may create protection but not broad mastery.
- Multiple valid routes remain available.
- No permanent pruning or deletion of memory-bearing structures.
- Dormancy remains reversible.
- Consolidation values do not affect live suggestion ranking, bounded advice, growth selection, pressure discharge, or production actions.
- The heuristic readiness indicator remains 94%; it is not a probability, safety certification, or production-readiness claim.

## 7. Explicitly deferred work

At the time of this handover, proposal-only scheduling had not yet been implemented. It was later completed in the separate consolidation scheduling stage recorded in `docs/SeedMind_Consolidation_Scheduling_Stage_Handover_2026-06-27.md`.

The following still require separate architecture and acceptance gates:

- Automatic acceptance or execution of consolidation proposals.
- Production replay scheduling.
- Persistent or autonomous scheduling queues.
- Consolidation-aware live suggestion ranking.
- Consolidation-aware bounded advice.
- Consolidation-aware growth selection or pressure discharge.
- Advisory or production action authority.
- Autonomous checkpoint restoration.
- Permanent pruning, merging, or deletion.

Do not infer execution authority from schema-v3 checkpoints or proposal-only scheduling.

## 8. Documentation updated in closure

- `README.md` identifies the research phase.
- `docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md` uses ordered sections:
  - `17.12` goal-gated multi-step growth
  - `17.13` contextual experiential redundancy and mastery
  - `17.14` retention-gated consolidation and reversible checkpoints
- `docs/SeedMind_Master_Implementation_Plan_v0.1.md` records the completed stage, evidence, commits, and deferred work.
- Repository wiki was refreshed during closure.

## 9. Repository workflow

Use CodexBridge for repository inspection, patching, validation, and commits. Commit only explicitly selected files. Never push automatically.

After a closure commit, the user pushes manually with:

```powershell
Set-Location "D:\Github\SeedMind"
git push
```

## 10. Historical next decision

This handover recommended a pure scheduling-policy experiment that could produce consolidation proposals without executing them. That bounded stage was subsequently implemented and accepted. Automatic execution, replay, ranking influence, advice, growth influence, restoration automation, and action authority remain separate future decisions.
