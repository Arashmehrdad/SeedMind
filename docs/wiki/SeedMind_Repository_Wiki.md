# SeedMind Repository Wiki

Last refreshed: 29 June 2026

## Current State

- Branch: `main`
- Push policy: do not push automatically.
- Learned Consequence Model stage: complete.
- Expanded developmental architecture marker: 82%.
- Next planned stage: bounded imagination only.

## Current Learned Consequence Boundary

Learned consequence evidence is restart-safe, live accepted, prediction-only, and
non-authoritative.

Accepted factual evidence:

- unique real one-step Nursery transitions;
- observed consequence chains built only from consecutive unique real Nursery
  transitions with exact context continuity;
- schema-7 persisted learned-consequence checkpoints that reload exactly.

Rejected or non-evidentiary inputs:

- duplicate events;
- conflicting event identity;
- disconnected chains;
- replayed evidence;
- imagined evidence;
- transferred predictions;
- malformed persisted learned state;
- partial, missing, or bound-failing evidence paths.

## Stage Documents

- `docs/SeedMind_Learned_Consequence_Model_Stage_Plan_2026-06-28.md`
- `docs/SeedMind_Learned_Consequence_Model_Stage_Closure_2026-06-29.md`
- `docs/SeedMind_Consequence_Imagination_Stage_Plan_2026-06-28.md`
- `docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md`
- `docs/architecture/decisions/ADR-2026-06-29-learned-consequence-evidence.md`

## Next Stage Boundary

Bounded imagination should begin with non-factual hypotheses only.

Initial scope:

- generate bounded imagined action candidates and short sequences;
- consume learned consequence predictions as non-authoritative estimates;
- keep imagined traces separate from real and replayed evidence;
- enforce depth, candidate, rollout, and computation bounds;
- prove imagined evidence cannot update real consequence, competence, mastery, or
  production authority.

Explicitly not in the first bounded-imagination stage:

- safe-experiment proposals;
- production action authority;
- route recommendation or automatic execution;
- treating imagined outcomes as facts.
