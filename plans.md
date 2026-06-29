# SeedMind Current Plan

This is the single live continuation file for ongoing SeedMind work.

Update this file in place as work progresses. Do not create or update session handover files unless Arash explicitly asks to move to a new session.

## Repository

- Alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Latest completed batch: Batch 7 — explicit human permission review for safe-experiment proposals
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
6. Batch 6 — deterministic caller-nominated safe-experiment proposal contracts.
7. Batch 7 — deterministic explicit human approve, reject, or defer review.

## Current accepted boundary

All bounded imagination outputs remain:

- explicitly `ExperienceOrigin.IMAGINED`;
- in memory only;
- deterministic and finite;
- provenance-preserving;
- non-evidentiary;
- non-authoritative.

The subsystem may represent exact imagined traces, enumerate exact supported candidates, annotate need alignment, describe pairwise route relations, expose unresolved comparison reasons, preserve caller-supplied safe-experiment proposal semantics, and record an explicit human approve, reject, or defer decision without autonomous recommendation or execution.

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

After Batch 7:

```text
ruff format --check .: 223 files already formatted
ruff check .: passed
mypy: no issues in 223 source files
pytest -q: 875 passed
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

## Next planning target

Audit and close the current bounded-imagination stage with Batch 7 documented as an optional training-time human-review gate, not a permanent runtime dependency. A future runtime may bypass this training gate through an explicit configured policy boundary; bypass must never be inferred silently from missing review evidence.

The current permission decision is review evidence only. Even an approved proposal does not authorize scheduling or execution, and the absence of a Batch 7 decision must not prevent a separately approved future non-training runtime path.

## Working rules

- Inspect repository status and this file before starting a new batch.
- Implement small bounded tasks directly through CodexBridge when practical.
- Use Codex CLI only when its overhead is justified.
- Run focused checks during implementation and full repository gates before closure.
- Refresh repository wiki and repository-scoped decision memory at completed batch boundaries.
- Create one bounded local commit per completed batch.
- Do not push automatically.
- Do not create a session handover unless Arash explicitly requests one because the session is ending or becoming too heavy.
