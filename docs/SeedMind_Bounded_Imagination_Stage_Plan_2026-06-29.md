# SeedMind Bounded Imagination Stage Plan

Date: 29 June 2026
Repository: `D:\Github\SeedMind`
Stage scope: bounded imagination
Stage status: active
Batch 1 status: complete in memory only

## Scope

Batch 1 implements only caller-driven bounded imagination over exact `LearnedConsequenceModel.predict` outputs.

- The caller supplies unique non-empty ASCII action sequences.
- Caller order is preserved exactly.
- The imagination layer does not generate, rank, select, recommend, optimise, schedule, promote, or execute candidates.
- Every produced step and trace is explicitly `ExperienceOrigin.IMAGINED`.

## Exact-source-only invariants

- Imagination begins from the exact caller-supplied `ContextSignature`.
- Every step requests the same sorted relevant effect codes.
- A step is supported only when exact requested effects exist and an exact predicted next context exists.
- The exact predicted next context becomes the next step context.
- Missing actions, missing exact evidence, missing exact next context, or supporting-source-event bound exhaustion stop the trace at the first failing step.
- Unsupported traces expose no final context.
- Effects remain per step only. No cumulative effects, route scores, or aggregate ranking fields exist.
- Provenance preserves exact source prediction IDs and exact supporting real event IDs without turning them into new evidence.

## Limits

Default request-wide limits:

- `maximum_candidate_sequences=8`
- `maximum_sequence_depth=3`
- `maximum_total_prediction_steps=24`
- `maximum_effect_dimensions=16`
- `maximum_supporting_real_event_ids_per_trace=64`

All bounds are validated before prediction where possible. Any rejection or failure leaves the learned model snapshot unchanged.

## Immutable zero-authority contract

Every public request, step, trace, and result contract fixes these fields at zero or false and validates them explicitly:

- factual confidence change
- mastery change
- competence change
- growth pressure change
- replay evidence change
- real observation change
- action-selection authority
- production-action authority

## Adversarial tests

The Batch 1 test set covers:

- valid two-step exact continuity with provenance preservation;
- reversed caller order as a distinct candidate without ranking fields;
- unavailable action, missing exact evidence, and missing exact next context failure paths;
- partial per-step effects without cumulative aggregation;
- transfer-like contexts remaining unsupported;
- finite bound rejections without model mutation;
- duplicate candidate rejection;
- stable IDs and ASCII snapshots;
- unchanged learned evidence, confidence, competence, mastery, growth, replay, and authority state;
- static exclusion of SQLite, timers, threads, asyncio, persistence, integration, and optimisation surfaces;
- rejection of imagined activity as real consequence evidence.

## Deferred work

Still pending after Batch 1:

- candidate generation;
- route optimisation;
- persistence;
- live integration;
- safe-experiment proposal promotion;
- any production-action path.

## Acceptance criteria

Batch 1 is accepted only when:

- the new module stays in memory only;
- snapshots and IDs are deterministic ASCII SHA-256 contracts;
- all supplied unit tests pass;
- `mypy`, `ruff check .`, and `git diff --check` pass;
- no file outside the approved allowlist changes.
