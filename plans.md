# SeedMind Current Plan

This is the single live continuation file for ongoing SeedMind work.

Update this file in place as work progresses. Do not create or update session handover files unless Arash explicitly asks to move to a new session.

## Repository

- Alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Latest completed milestone: Normalized Recruitment and Local Saturation Batch 1
- Inspect Git history for the current commit hash.
- Push policy: never push automatically

## Current stage

- Program: NDNRA
- Last closed stage: Bounded Imagination at Batch 8
- Current stage: Normalized Recruitment and Local Saturation
- Current status: Batch 1 complete; Batch 2 graph-locally derived saturation next
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

After Normalized Recruitment Batch 1:

```text
ruff format --check .: 232 files already formatted
ruff check .: passed
mypy: no issues in 232 source files
pytest -q: 935 passed
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

## Next planning target

Finish and prove NDNRA as a standalone research architecture before comparing it with, or integrating it into, the original SeedMind roadmap.

The gap audit is complete. It confirms that the Section 20 prototype criteria are evidenced in isolation, while complete NDNRA proof remains fragmented across experiments and checkpoint boundaries.

The next stage is `Standalone NDNRA Acceptance and Restart Proof`. Batch 1 is complete as a deterministic in-memory acceptance aggregator over the existing heat-fan recall, multi-effect composition, and structural-growth experiment gates. It preserves complete component evidence, derives one canonical ASCII snapshot and SHA-256 identity, records explicit zero-authority and zero-delta invariants, and does not add restart persistence, execution, recommendation, scheduling, promotion, or live integration authority.

Batch 2 is complete as a separate standalone acceptance persistence store and restart-proof evidence boundary. It keeps the main brain schema unchanged, persists exactly one validated Batch 1 `StandaloneAcceptanceResult` as versioned canonical ASCII JSON with SHA-256 payload checksum and atomic temp-file replacement, restores only exact validated nested data, reports explicit loaded, missing-fallback, corrupt-fallback, and incompatible-fallback statuses, proves exact reload and deterministic rerun equivalence through a separate zero-authority result, and never synthesizes passing or partial evidence from missing or damaged storage.

The retain-or-descope audit is complete.

Retained as mandatory before standalone v0.1 closure:

- local spreading-activation normalization under competing recruitment;
- locally derived representational saturation;
- long-horizon mixed-task interference and adaptability evidence.

Already sufficiently represented for v0.1:

- bounded initial connections for specialist growth through deterministic local eligibility, bounded membership, configured specialist limits, and duplicate blocking.

Deferred post-v0.1 research:

- learned context-similarity weights;
- semantic abstraction above grounded context signatures;
- coordination of multiple simultaneous needs.

The next stage is `Normalized Recruitment and Local Saturation`:

1. Batch 1 — normalized competing recruitment while preserving deterministic heat-fan recall and dormancy behaviour. Complete: local incoming support now uses deterministic positive-only contributor averaging with separate immutable evidence and no persistence-schema or standalone-payload change.
2. Batch 2 — graph-locally derived saturation and saturation-gated growth pressure.
3. Then complete long-horizon mixed-task interference and adaptability.
4. Run the final standalone NDNRA closure audit.
5. Compare the completed NDNRA architecture with the original SeedMind plan.
6. Decide explicitly whether, where, and how integration should occur.

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
