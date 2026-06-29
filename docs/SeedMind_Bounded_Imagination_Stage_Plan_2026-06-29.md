# SeedMind Bounded Imagination Stage Plan

Date: 29 June 2026
Repository: `D:\Github\SeedMind`
Stage scope: bounded imagination
Stage status: active
Batch 1 status: complete in memory only
Batch 2 status: complete in memory only

## Scope

Batch 1 implements only caller-driven bounded imagination over exact `LearnedConsequenceModel.predict` outputs.

- The caller supplies unique non-empty ASCII action sequences.
- Caller order is preserved exactly.
- The imagination layer does not generate, rank, select, recommend, optimise, schedule, promote, or execute candidates.
- Every produced step and trace is explicitly `ExperienceOrigin.IMAGINED`.

Batch 2 implements only deterministic exact-record candidate enumeration over exact retained `LearnedConsequenceModel` records plus exact `LearnedConsequenceModel.predict(...)` outputs.

- The caller supplies only one exact starting `ContextSignature` and sorted unique requested effect codes.
- Enumeration is breadth-first over every supported prefix from depth 1 through the configured maximum.
- Within one parent prefix, exact current-context records are considered in stable `(action_code, record_id)` order.
- A step is admitted only when the exact current-context record exists, the action is available, all requested effects are returned in exact requested order, an exact predicted next context exists, and supporting provenance remains in bounds.
- One exact source prediction ID may appear at most once within one generated candidate.
- Generated candidates remain provenance-only imagined hypotheses. They do not rank, score, select, recommend, optimise, schedule, promote, execute, persist, or integrate anything.
- Request, step, candidate, and result identities use deterministic canonical ASCII JSON plus SHA-256.
- Batch 2 does not call Batch 1 implicitly. A caller may explicitly hand generated sequences into Batch 1 later.

## Exact-source-only invariants

- Imagination begins from the exact caller-supplied `ContextSignature`.
- Every step requests the same sorted relevant effect codes.
- A step is supported only when exact requested effects exist and an exact predicted next context exists.
- The exact predicted next context becomes the next step context.
- Missing actions, missing exact evidence, missing exact next context, or supporting-source-event bound exhaustion stop the trace at the first failing step.
- Unsupported traces expose no final context.
- Effects remain per step only. No cumulative effects, route scores, or aggregate ranking fields exist.
- Provenance preserves exact source prediction IDs and exact supporting real event IDs without turning them into new evidence.

Batch 2 adds these exact-source-only invariants:

- The generator enumerates only from exact retained learned consequence records, never from contextual transfer, observed chains, or any other subsystem.
- The exact predicted next context becomes the next prefix context.
- Unsupported contexts return an empty deterministic result rather than an exception.
- Bound exhaustion returns partial deterministic output with result-level truncation reasons only.
- Candidate objects carry no per-candidate truncation flag and no ranking or authority fields.

## Limits

Default request-wide limits:

- `maximum_candidate_sequences=8`
- `maximum_sequence_depth=3`
- `maximum_total_prediction_steps=24`
- `maximum_effect_dimensions=16`
- `maximum_supporting_real_event_ids_per_trace=64`

Default Batch 2 limits:

- `maximum_requested_effect_dimensions=16`
- `maximum_source_records_considered=32`
- `maximum_branch_actions_per_prefix=4`
- `maximum_sequence_depth=3`
- `maximum_generated_candidates=8`
- `maximum_total_expansions=24`
- `maximum_supporting_real_event_ids_per_candidate=64`

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

The Batch 2 test set adds coverage for:

- deterministic one-step and multi-parent BFS candidate order;
- one-step prefixes emitted before longer extensions;
- exact step and candidate provenance preservation;
- reversed action order remaining distinct when exact continuity supports both;
- transfer-like near matches yielding zero candidates;
- missing effects, missing exact next context, unavailable actions, and repeated source prediction cycles blocking admission or extension;
- deterministic runtime truncation for branch, candidate, expansion, source-record, supporting-event, and depth limits;
- repeated identical requests producing identical IDs and ASCII snapshots;
- explicit handoff to Batch 1 without implicit Batch 1 calls;
- static exclusion of contextual transfer, observed chains, persistence, growth, replay, SQLite, timers, threads, and asyncio;
- absence of score, rank, schedule, execution, and promotion fields in snapshots.

## Deferred work

Still pending after Batch 2:

- route optimisation;
- persistence;
- live integration;
- safe-experiment proposal promotion;
- any production-action path.

## Acceptance criteria

Batch 1 and Batch 2 are accepted only when:

- the modules stay in memory only;
- snapshots and IDs are deterministic ASCII SHA-256 contracts;
- focused tests and the complete repository test suite pass;
- `ruff format --check .`, `ruff check .`, full `mypy`, `pip check`, and `git diff --check` pass;
- no file outside the approved boundary changes;
- the repository wiki, repository-scoped decision memory, and final Git metadata are refreshed and verified before commit.
