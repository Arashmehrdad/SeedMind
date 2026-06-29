# SeedMind Current Plan

This is the single live continuation file for ongoing SeedMind work.

Update this file in place as work progresses. Do not create or update session handover files unless Arash explicitly asks to move to a new session.

## Repository

- Alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Latest completed batch: Batch 5 — comparison uncertainty audit
- Inspect Git history for the current commit hash.
- Push policy: never push automatically

## Current stage

- Stage: Bounded Imagination
- Stage status: active
- Expanded developmental architecture marker: 82%

Completed bounded increments:

1. Batch 1 — caller-supplied exact-source imagined consequence traces.
2. Batch 2 — deterministic exact-record imagined candidate enumeration.
3. Batch 3 — pure per-step, per-dimension need-alignment annotation.
4. Batch 4 — deterministic caller-order pairwise route comparison.
5. Batch 5 — deterministic unresolved-comparison uncertainty audit.

## Current accepted boundary

All bounded imagination outputs remain:

- explicitly `ExperienceOrigin.IMAGINED`;
- in memory only;
- deterministic and finite;
- provenance-preserving;
- non-evidentiary;
- non-authoritative.

The subsystem may represent exact imagined traces, enumerate exact supported candidates, annotate need alignment, describe pairwise route relations, and expose unresolved comparison reasons without proposing what to do.

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

After Batch 5:

```text
ruff format --check .: 219 files already formatted
ruff check .: passed
mypy: no issues in 219 source files
pytest -q: 850 passed
pip check: no broken requirements
git diff --check: passed
```

## Current technical sources

Use these for architecture and implementation detail:

- `docs/SeedMind_Bounded_Imagination_Stage_Plan_2026-06-29.md`
- `docs/SeedMind_Consequence_Imagination_Stage_Plan_2026-06-28.md`
- `docs/SeedMind_Master_Implementation_Plan_v0.1.md`
- `docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md`
- `docs/architecture/decisions/ADR-2026-06-29-bounded-imagination-route-comparison.md`

## Next planning target

Plan the first bounded safe-experiment proposal contracts using explicit caller nomination of one exact imagined source. The proposal layer may describe a hypothesis, predicted benefit, uncertainty, possible harm, reversibility, stop conditions, and required permission, but it must not autonomously select a candidate, schedule, execute, promote, persist, or influence production actions.

The next increment must remain non-authoritative and in memory unless Arash explicitly approves a stronger boundary. Persistence, live integration, autonomous promotion, recommendation, and production action authority remain deferred.

## Working rules

- Inspect repository status and this file before starting a new batch.
- Implement small bounded tasks directly through CodexBridge when practical.
- Use Codex CLI only when its overhead is justified.
- Run focused checks during implementation and full repository gates before closure.
- Refresh repository wiki and repository-scoped decision memory at completed batch boundaries.
- Create one bounded local commit per completed batch.
- Do not push automatically.
- Do not create a session handover unless Arash explicitly requests one because the session is ending or becoming too heavy.
