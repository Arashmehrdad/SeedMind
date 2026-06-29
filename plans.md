# SeedMind Current Plan

This is the single live continuation file for ongoing SeedMind work.

Update this file in place as work progresses. Do not create or update session handover files unless Arash explicitly asks to move to a new session.

## Repository

- Alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Latest completed milestone: Original Plan and NDNRA v0.1 Comparison Decision
- Inspect Git history for the current commit hash.
- Push policy: never push automatically

## Current stage

- Program: NDNRA
- Last closed stage: Original Plan and NDNRA v0.1 Comparison Decision
- Current stage: Awaiting explicit integration-boundary approval
- Current status: The original master plan remains the product and MVP spine; selective partial integration of NDNRA is recommended, but no runtime integration is approved
- Expanded developmental architecture marker: 82%
- Marker interpretation: unchanged because the comparison adds no new cognitive architecture capability; it is not a completion percentage for the original SeedMind roadmap

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

After Original Plan and NDNRA v0.1 Comparison Decision:

```text
ruff format --check .: 237 files already formatted
ruff check .: passed
mypy: no issues in 237 source files
pytest -q: 986 passed
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
- `docs/architecture/NDNRA_Retain_Or_Descope_Audit_2026-06-29.md`
- `docs/architecture/decisions/ADR-2026-06-29-ndnra-v0.1-retain-or-descope.md`
- `docs/architecture/decisions/ADR-2026-06-29-normalized-competing-recruitment.md`
- `docs/architecture/decisions/ADR-2026-06-29-locally-derived-representational-saturation.md`
- `docs/architecture/decisions/ADR-2026-06-29-long-horizon-mixed-task-interference.md`
- `docs/architecture/NDNRA_Final_Standalone_Closure_Audit_2026-06-29.md`
- `docs/architecture/decisions/ADR-2026-06-29-standalone-ndnra-v0.1-closure.md`
- `docs/architecture/SeedMind_Original_Plan_NDNRA_Comparison_2026-06-30.md`
- `docs/architecture/decisions/ADR-2026-06-30-original-plan-ndnra-integration-decision.md`

## Next planning target

The documentation-first comparison is accepted. Its decision is:

- retain the original SeedMind master plan as the governing product, MVP, safety, human-apprenticeship, evaluation, and competition roadmap;
- adapt selected memory, persistence, observatory, metric, and roadmap interfaces around NDNRA;
- consider later partial integration for local delayed credit, need-driven recall, consequence memory, recall effort, local saturation evidence, provenance, retention evidence, and bounded consolidation evidence;
- keep NDNRA proof stores, research growth, shadow suggestions, human-approved research operations, and bounded imagination isolated unless a later ADR approves a narrower boundary;
- reject proof-store merging, bounded-imagination persistence, implicit permission, autonomous execution, and NDNRA production action authority.

The original Week 8 reusable-skill objective remains mandatory. NDNRA has not yet proved a Nursery `approach_and_push` skill with explicit preconditions, termination, varied-start generalisation, reuse, known failure boundaries, and retention.

The original roadmap is active as the product sequence, but its dates and implementation order may require re-baselining after an integration boundary is approved. No milestone may be marked complete solely because a related NDNRA research proof exists.

No runtime integration work is approved. The next possible work requires Arash's separate explicit approval and must begin with a bounded integration-boundary design rather than code.

Any later integration proposal must preserve:

- production curiosity as the sole production action authority;
- the protected external safety supervisor and human permission channels;
- separate standalone-acceptance and long-horizon proof stores;
- non-persistent bounded imagination;
- atomic versioned runtime persistence with complete safe fallback;
- matched-control behavioural invariance for unaffected production paths;
- original retention, rollback, hardware, observability, and competition-claim gates.

Deferred post-v0.1 research remains outside the accepted integration recommendation:

- learned context-similarity weights;
- semantic abstraction above grounded context signatures;
- simultaneous multiple-need coordination;
- unrestricted generic neuron creation;
- a unified production cognitive runtime checkpoint.

## Working rules

- Inspect repository status and this file before starting a new batch.
- Implement small bounded tasks directly through CodexBridge when practical.
- Use Codex CLI only when its overhead is justified.
- Run focused checks during implementation and full repository gates before closure.
- Refresh repository wiki and repository-scoped decision memory at completed batch boundaries.
- Create one bounded local commit per completed batch.
- Do not push automatically.
- Do not create a session handover unless Arash explicitly requests one because the session is ending or becoming too heavy.
