# SeedMind Current Plan

This is the single live continuation file for ongoing SeedMind work.

Update this file in place as work progresses. Do not create or update session handover files unless Arash explicitly asks to move to a new session.

## Repository

- Alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Latest completed milestone: NDNRA standalone completion gap audit
- Inspect Git history for the current commit hash.
- Push policy: never push automatically

## Current stage

- Program: NDNRA
- Last closed stage: Bounded Imagination at Batch 8
- Current stage: Standalone NDNRA Acceptance and Restart Proof
- Current status: planned; implementation not yet started
- Expanded developmental architecture marker: 82%

Completed bounded increments:

1. Batch 1 — caller-supplied exact-source imagined consequence traces.
2. Batch 2 — deterministic exact-record imagined candidate enumeration.
3. Batch 3 — pure per-step, per-dimension need-alignment annotation.
4. Batch 4 — deterministic caller-order pairwise route comparison.
5. Batch 5 — deterministic unresolved-comparison uncertainty audit.
6. Batch 6 — deterministic caller-nominated safe-experiment proposal contracts.
7. Batch 7 — deterministic explicit human approve, reject, or defer review.
8. Batch 8 — deterministic training-review or explicit configured non-training bypass resolution.

## Current accepted boundary

All bounded imagination outputs remain:

- explicitly `ExperienceOrigin.IMAGINED`;
- in memory only;
- deterministic and finite;
- provenance-preserving;
- non-evidentiary;
- non-authoritative.

The subsystem may represent exact imagined traces, enumerate exact supported candidates, annotate need alignment, describe pairwise route relations, expose unresolved comparison reasons, preserve caller-supplied safe-experiment proposal semantics, record optional training-time human review, and resolve an explicit configured non-training review bypass without autonomous recommendation or execution.

It must not:

- create factual evidence;
- change confidence, mastery, competence, growth pressure, replay evidence, or real-observation state;
- create a hidden route utility or arbitrary cross-effect total;
- globally rank candidates;
- select a winner;
- recommend, optimise, schedule, promote, or execute an action;
- persist imagination state;
- integrate with the live Nursery loop;
- influence production curiosity or production actions.

Unknown evidence, low-confidence evidence, route-depth mismatch, and explicit trade-offs block unsupported dominance claims.

## Current validation baseline

At stage closure:

```text
ruff format --check .: 226 files already formatted
ruff check .: passed
mypy: no issues in 226 source files
pytest -q: 896 passed
pip check: no broken requirements
git diff --check: passed
```

## Current technical sources

Use these for architecture and implementation detail:

- `docs/archive/SeedMind_Bounded_Imagination_Stage_Plan_2026-06-29.md`
- `docs/archive/SeedMind_Consequence_Imagination_Stage_Plan_2026-06-28.md`
- `docs/archive/SeedMind_Master_Implementation_Plan_v0.1.md`
- `docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md`
- `docs/architecture/decisions/ADR-2026-06-29-bounded-imagination-route-comparison.md`
- `docs/architecture/decisions/ADR-2026-06-29-human-permission-review-for-imagined-safe-experiments.md`
- `docs/architecture/decisions/ADR-2026-06-29-explicit-training-review-gate-policy.md`
- `docs/architecture/decisions/ADR-2026-06-29-bounded-imagination-stage-closure.md`
- `docs/architecture/NDNRA_Standalone_Completion_Gap_Audit_2026-06-29.md`
- `docs/architecture/decisions/ADR-2026-06-29-standalone-ndnra-acceptance-and-restart-proof.md`

## Next planning target

Finish and prove NDNRA as a standalone research architecture before comparing it with, or integrating it into, the original SeedMind roadmap.

The gap audit is complete. It confirms that the Section 20 prototype criteria are evidenced in isolation, while complete NDNRA proof remains fragmented across experiments and checkpoint boundaries.

The next stage is `Standalone NDNRA Acceptance and Restart Proof`. It must aggregate existing heat-fan recall, multi-effect composition, structural growth, restart, corruption-fallback, and authority evidence into one deterministic standalone acceptance boundary without adding new cognitive authority.

Required sequence:

1. Complete the remaining NDNRA stages in isolation.
2. Run end-to-end NDNRA proof and acceptance experiments.
3. Compare the completed NDNRA architecture with the original SeedMind plan.
4. Decide explicitly whether, where, and how integration should occur.

The gap audit also identifies later retain-or-descope questions for learned similarity, semantic abstraction, simultaneous-need coordination, recruitment normalization, locally derived saturation, growth initialization, and long-horizon interference. Passing the next acceptance stage will not silently declare those questions solved.

Original-roadmap milestones, including Week 8 skill compilation, are not active implementation targets unless a later NDNRA-only audit independently requires an equivalent capability.

Experiment permits, schedulers, executors, bounded-imagination persistence, live Nursery integration, autonomous promotion, recommendation, and production action authority remain separate boundaries requiring explicit approval.

## Working rules

- Inspect repository status and this file before starting a new batch.
- Implement small bounded tasks directly through CodexBridge when practical.
- Use Codex CLI only when its overhead is justified.
- Run focused checks during implementation and full repository gates before closure.
- Refresh repository wiki and repository-scoped decision memory at completed batch boundaries.
- Create one bounded local commit per completed batch.
- Do not push automatically.
- Do not create a session handover unless Arash explicitly requests one because the session is ending or becoming too heavy.
