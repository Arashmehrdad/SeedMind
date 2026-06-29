# SeedMind Bounded Imagination Stage Plan

Date: 29 June 2026
Repository: `D:\Github\SeedMind`
Stage scope: bounded imagination
Stage status: active
Batch 1 status: complete in memory only
Batch 2 status: complete in memory only
Batch 3 status: complete in memory only
Batch 4 status: complete in memory only
Batch 5 status: complete in memory only
Batch 6 status: complete in memory only

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

Batch 3 implements only pure need-alignment annotation for caller-ordered imagined candidates.

- The caller supplies an explicit `EffectNeed` and already-generated imagined candidates.
- Every candidate step is annotated independently for each need dimension as improving, worsening, neutral, or unknown.
- Signed alignment uses predicted effect direction and learned prediction confidence; need intensity remains explicit metadata and is not hidden inside a route total.
- Missing predicted dimensions remain unknown rather than neutral.
- Exact source step, record, prediction, context, next-context, and supporting-real-event provenance remain inspectable.
- Candidate order is preserved exactly. No route total, winner, rank, recommendation, selection, optimisation, schedule, promotion, execution, persistence, or live integration is created.
- All step contexts must retain the same active need identity as the evaluation request.

Batch 4 implements only pairwise alignment comparison over one complete Batch 3 `ImaginedRouteEvaluationResult`.

- The comparison request embeds the complete source result and derives source request and result identity from it.
- Pair comparisons preserve caller-index order and never sort by quality.
- A route may dominate another only when every comparable local step/effect relation is no worse and at least one is better.
- Unknown alignments, low confidence, and route-depth mismatch block dominance.
- Conflicting trade-offs remain incomparable rather than being collapsed into a utility value.
- Alignment-equivalent routes remain distinct and preserve separate provenance through the embedded source result.
- No global route score, utility, rank, winner, selected candidate, recommendation, optimisation, schedule, promotion, execution, persistence, or live integration is created.

Batch 5 implements only deterministic uncertainty auditing over one complete Batch 4 `ImaginedRouteComparisonResult`.

- Comparable pairs emit no uncertainty issue.
- Unknown alignments, low confidence, and route-depth mismatch emit dimension-scoped issues tied to the exact source dimension comparison.
- Conflicting trade-offs emit one pair-scoped issue tied to the exact opposing dimension comparisons.
- Issue order preserves source pair order and source dimension order.
- The audit proposes no experiment, route, action, schedule, permission decision, promotion, or execution.
- The complete Batch 4 result remains canonical provenance and is revalidated before auditing.

Batch 6 implements only caller-nominated safe-experiment proposal contracts over one complete Batch 5 `ImaginedComparisonUncertaintyResult`.

- The caller supplies exactly one explicit `issue_id` from the embedded Batch 5 result plus all proposal semantics.
- The request revalidates the complete Batch 5 result before any proposal is constructed.
- The proposal may describe only hypothesis, predicted benefit, uncertainty, possible harm, reversibility, stop conditions, and required permission.
- The layer does not infer, rank, recommend, optimise, schedule, execute, persist, promote, or integrate anything.
- The nominated Batch 5 issue and complete source result remain exact provenance.

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

Batch 3 adds these need-alignment invariants:

- Evaluation accepts imagined generated candidates only and never invokes generation or Batch 1 imagination internally.
- Every candidate step context must preserve the request need identity.
- Each need dimension remains a separate alignment record; arbitrary cross-effect and cross-step summation is prohibited.
- Unknown dimensions retain zero prediction confidence, no signed alignment, and no borrowed provenance.
- Known alignment provenance exactly matches the originating imagined step and its real supporting events.
- Evaluation order is caller order and carries no quality semantics.

Batch 4 adds these comparison invariants:

- Comparison consumes exactly one `ImaginedRouteEvaluationResult`; unrelated free evaluation tuples are not accepted.
- Every source evaluation must share the Batch 3 request's need definition and evaluation semantics.
- Per-dimension comparison uses local direction ordering only: worsening < neutral < improving.
- Neutral alignments are equivalent inside the neutral band even when signed values differ.
- Same non-neutral categories compare signed alignment using an explicit epsilon.
- Prediction confidence is not weighted again because Batch 3 already folded it into signed alignment.
- Need intensity remains inspectable metadata and is not multiplied into a hidden route score.
- Source evaluation order must still match the embedded Batch 3 request candidate order.
- Missing-step comparison records cannot expose orphaned alignment identity or evidence.
- Pair relation and incomparability reasons must be derivable exactly from their dimension relations.
- Final results recompute expected caller-order pairs and reject altered source references or relations.

Batch 5 adds these uncertainty-audit invariants:

- Auditing consumes exactly one complete Batch 4 result and never invokes earlier generation, evaluation, or comparison stages.
- Every issue retains exact source pair, evaluation, candidate, and optional dimension identities.
- Dimension issues may report only unknown-alignment, low-confidence, or route-depth reasons.
- Pair issues may report only explicit conflicting trade-offs and must retain the opposing dimension-comparison IDs.
- Comparable pairs cannot carry uncertainty issues.
- Issue identity and final result identity use canonical ASCII JSON plus SHA-256.
- Audit output contains no proposed experiment, score, utility, rank, winner, recommendation, selection, scheduling, promotion, execution, persistence, or production authority.

Batch 6 adds these safe-experiment proposal invariants:

- Proposal construction consumes exactly one complete uncertainty result and one explicit caller-nominated issue ID.
- The nominated issue must exist exactly once in the source result and remains attached as exact provenance.
- Proposal semantics remain caller supplied only; no hidden experiment inference or recommendation path exists.
- Stop-condition codes remain sorted unique ASCII codes when provided.
- Request, proposal, and result identities use canonical ASCII JSON plus SHA-256.
- Request, proposal, and result carry zero deltas and zero action or production authority.

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

Default Batch 3 limits:

- `maximum_candidates=8`
- `maximum_steps_per_candidate=3`
- `maximum_need_dimensions=16`
- `maximum_total_alignments=384`
- `neutral_tolerance=0.05`

Default Batch 4 limits:

- `maximum_evaluations=8`
- `maximum_pairs=28`
- `maximum_steps_per_evaluation=3`
- `maximum_dimensions_per_step=16`
- `maximum_total_dimension_comparisons=1344`
- `maximum_unique_supporting_real_event_ids_per_evaluation=64`
- `confidence_floor=0.0`
- `comparison_epsilon=1e-12`

Default Batch 5 limits:

- `maximum_pairs=28`
- `maximum_dimension_issues=1344`
- `maximum_pair_issues=28`
- `maximum_total_issues=1372`
- `maximum_reasons_per_issue=4`

All bounds are validated before evaluation where possible. Batch 1 and Batch 2 leave the learned model snapshot unchanged; Batch 3, Batch 4, and Batch 5 are pure and do not receive a mutable model reference.

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

The Batch 3 test set adds coverage for:

- improving, worsening, neutral, and unknown per-effect alignment classifications;
- learned prediction confidence affecting signed alignment without creating a route total;
- need intensity remaining inspectable without hidden aggregation;
- exact step, record, prediction, context, next-context, and supporting-event provenance;
- caller candidate order preserved without a winner or ranking field;
- first-step and later-step active-need mismatches rejected before evaluation;
- candidate, step, need-dimension, and total-alignment bounds;
- deterministic ASCII identities and empty deterministic evaluation;
- zero evidence, confidence, mastery, competence, growth, replay, and authority changes on every public layer;
- rejection of imagined evaluations as real consequence evidence;
- static exclusion of generation calls, integration, persistence, transfer, observed-chain substitution, timers, workers, SQLite, and optimisation.

The Batch 4 test set adds coverage for:

- left and right pairwise dominance without route scores;
- conflicting trade-offs remaining incomparable;
- unknown, zero-confidence, low-confidence, and route-depth mismatch blocking dominance;
- neutral-band equivalence without raw-value dominance;
- improving and worsening alignments comparing by signed magnitude only;
- equivalent routes with distinct provenance remaining separate;
- duplicate IDs and incompatible Batch 3 semantics rejected atomically;
- empty deterministic comparison results;
- evaluation, pair, step, dimension, total-comparison, and provenance bounds;
- caller-index pair order and stable ASCII identities;
- exact source IDs resolving into the embedded source result;
- zero evidence, confidence, mastery, competence, growth, replay, real-observation, and authority changes on every public layer;
- rejection of comparison results as real consequence evidence;
- static exclusion of generation, imagination, learned-model, transfer, observed-chain, composition, replay, growth, persistence, SQLite, timers, workers, queues, threading, asyncio, integration, curiosity, advice, safe-experiment, optimisation, and execution surfaces.

The Batch 5 test set adds coverage for:

- comparable pairs producing no uncertainty issue;
- exact dimension issues for unknown alignment, low confidence, and route-depth mismatch;
- exact pair issues for conflicting trade-offs with opposing dimension provenance;
- deterministic source pair and dimension issue order;
- empty deterministic audit results;
- pair, dimension-issue, and total-issue bounds;
- tampered source comparison and tampered issue reference rejection;
- stable ASCII identities;
- zero evidence, confidence, mastery, competence, growth, replay, real-observation, and authority changes;
- rejection of uncertainty results as real consequence evidence;
- static exclusion of earlier generation, evaluation, comparison execution, learned-model, transfer, persistence, integration, scheduling, optimisation, and execution surfaces.

The Batch 6 test set adds coverage for:

- valid caller-nominated proposal creation with exact Batch 5 provenance;
- missing nominated issue rejection;
- unstable or tampered source-result rejection before proposal construction;
- duplicate and unsorted stop-condition-code rejection;
- stable ASCII identities and snapshots;
- zero deltas and zero authority on request, proposal, and result;
- snapshots excluding ranking, scheduling, execution, persistence, promotion, and integration fields;
- no earlier-stage calls;
- static exclusion of persistence, integration, timers, threading, asyncio, sqlite, and optimisation surfaces.

## Deferred work

Still pending after Batch 6:

- explicit human permission boundary for safe-experiment proposals;
- optional route optimisation only under a separately accepted non-authoritative semantics contract;
- persistence;
- live integration;
- autonomous proposal promotion;
- any production-action path.

## Acceptance criteria

Batch 1, Batch 2, Batch 3, Batch 4, and Batch 5 are accepted only when:

- the modules stay in memory only;
- snapshots and IDs are deterministic ASCII SHA-256 contracts;
- focused tests and the complete repository test suite pass;
- `ruff format --check .`, `ruff check .`, full `mypy`, `pip check`, and `git diff --check` pass;
- no file outside the approved boundary changes;
- the repository wiki, repository-scoped decision memory, and final Git metadata are refreshed and verified before commit.
