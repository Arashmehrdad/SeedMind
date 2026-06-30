# SeedMind Week 9 Contribution Evidence

Date: 30 June 2026
Status: Passed after Default-vs-NDNRA comparison correction
Scope: original SeedMind Master Implementation Plan Week 9 only

## Objective

Complete the original main-roadmap Week 9 milestone: accept a typed human request,
check whether the familiar capability is available and appropriate, execute the
frozen Week 8 `approach_and_push` skill, verify the result from grounded runtime
evidence, report failure honestly, reduce or restore human support only from
predeclared competence evidence, and collect actual Default-vs-NDNRA comparative
data from the same contribution scenarios.

This work does not reopen or recompile Week 8, does not begin original Week 10,
and does not implement NDNRA Stage 9.

## Main Implementation

Week 9 is owned by the main `seedmind.contribution` package:

- `contracts.py` defines typed requests, capability states, grounded verification,
  contribution and failure records, support policy and state, shadow audit, and
  strict persistence envelopes.
- `engine.py` performs capability inspection, frozen skill execution, grounded
  verification, honest failure construction, and evidence-gated support changes.
- `persistence.py` saves and loads checksum-protected ASCII JSON, with a complete
  conservative Level 4 fallback for missing, corrupt, or incompatible state.
- `parallel_comparison.py` gives both systems the same typed contribution goal,
  relational pre-action state context, primitive action set, budgets, and safety
  constraints; trains NDNRA only from NDNRA-executed sandbox transitions; then
  runs frozen held-out counterfactual comparisons plus separate frozen and
  adaptive NDNRA-only rollouts.
- `week9.py` runs the deterministic contribution, degradation, recovery, and
  corrected parallel-comparison sequence and exports the required deliverables.
- `scripts/run_week9_contribution.py` executes the complete contribution and
  comparison acceptance gate.

## Human Request Flow

Each contribution request is typed and inspectable. It binds:

```text
request identity and intent
permission level and verification rule
target capability
expected outcome
target object and target identities
learned context
requested support level
```

The runtime flow is:

```text
human request
-> capability classification
-> authoritative interruption check
-> frozen Week 8 skill controller
-> production curiosity retains each primitive action
-> grounded runtime and actual-transition verification
-> contribution or honest-failure record
-> support-policy evaluation
-> checksum-protected history and support persistence
```

Human stop, denial, correction, clarification, and permission events interrupt
execution before any primitive action and remain authoritative.

## Capability Classification

The Week 9 capability check distinguishes exactly:

```text
unavailable
unproven
degraded
context_mismatched
verified
```

A capability is `verified` only when the frozen Week 8 skill identity, validation
status, expected outcome, target object, target, and learned context all match.
An unfamiliar request, absent skill, unvalidated skill, failed validation, or
context mismatch cannot claim capability.

## Grounded Contribution Verification

Contribution success requires both:

```text
runtime target occupancy confirms the requested object-target relation
and
an actual grounded push transition confirms the causal execution path
```

The verifier rejects:

- self-report;
- producer-verifier agreement alone;
- NDNRA agreement;
- imagination;
- unavailable evidence;
- target occupancy without the required actual transition;
- actual execution that does not produce the requested state.

The two intentionally blocked familiar episodes therefore remain failed
contributions and preserve complete honest-failure records rather than being
hidden or converted into success.

## Support Policy

Thresholds were defined before final evaluation:

```text
minimum verified independent familiar successes: 5
minimum independent familiar success rate: 0.80
minimum distinct familiar scenario contexts: 3
recent evidence window: 12
consecutive grounded familiar failures restoring Level 4: 2
```

One success cannot reduce support. Stale, contradictory, degraded, unsafe,
context-mismatched, or unverified evidence blocks reduction.

Support state uses a post-regression evidence epoch. When competence degradation
restores Level 4, evidence collected before that rollback cannot be recycled to
obtain Level 3 again. Five new verified independent successes across the required
contexts are necessary after the rollback. Degraded or unsafe competence can
restore Level 4 immediately.

## Deterministic Evaluation

The runner performs:

```text
5 familiar verified successes
2 familiar grounded failures caused by blocked preconditions
5 fresh familiar verified recovery successes
```

Observed contribution metrics:

```text
total_attempts=12
total_successes=10
independent_success_rate=0.8333333333333334
executed_step_count=172
production_curiosity_retained_count=172
```

Observed support transitions:

```text
first success: Level 4 remains Level 4
fifth initial success: Level 4 -> Level 3
second consecutive grounded failure: Level 3 -> Level 4
first four recovery successes: Level 4 remains Level 4
fifth fresh recovery success: Level 4 -> Level 3
final support level: Level 3
promotion evidence start index after degradation: 7
```

This proves both required pass gates:

- SeedMind completes a familiar typed human request with grounded verification.
- Support drops only when repeated competence is proven and rises again after
  demonstrated degradation.

## Frozen Week 8 Reuse

The evaluation loads:

```text
artifacts/week8_reusable_skill/approach_and_push_skill_record.json
```

Observed frozen-state metrics:

```text
skill_discovery_delta=0
compile_count=0
training_count=0
component_promotion_count=0
```

No evaluation episode trains, compiles, promotes, mutates the frozen skill
record, or increases its discovery count.

## Default-vs-NDNRA Parallel Comparison

The original corrected comparison in commit `cfb8f3c` is preserved in Git history
but is invalid for NDNRA competence assessment. It gave Default a task-specific
object/target/geometry policy while NDNRA lacked an equivalent typed objective
and relational state context, trained NDNRA from Default evaluation actions,
counted generic-score-only differences as NDNRA task wins, mixed blocked tasks
into ordinary task-success percentages, and exposed one ambiguous `pass_gate`.

The fair replacement evaluates both systems while preserving the authority
boundary. For each of the 172 executed Default steps:

```text
recreate the exact contribution scenario and Default action trace
capture the same immutable pre-action state
give NDNRA the same object, target, outcome, completion condition, context,
  available actions, budgets, and relational geometry available to Default
obtain a goal-conditioned NDNRA proposal from that cloned state
compare the fixed Default action and NDNRA proposal by task progress first
execute only the Default action in the production replay
do not update either controller during frozen held-out comparison
```

NDNRA training is separated from held-out evaluation:

```text
training seeds: 6, 7, 8, 11
held-out evaluation seeds: 206, 207, 208, 211, 212, 213, 206, 207, 208, 211, 212, 213
blocked evaluation seeds: 321, 322
training/evaluation seed overlap: 0
NDNRA training source: NDNRA-executed sandbox transitions only
frozen evaluation updates: 0
adaptive diagnostic updates: 64
```

Generic developmental scores are retained for diagnostics but are separated from
task-progress competence categories. They cannot count as NDNRA task wins.

Observed fair comparison summary:

```text
experiment_integrity_pass=true
default_competence_pass=true
ndnra_competence_pass=false
blocked_scenario_handling_pass=true
authority_containment_pass=true
week9_main_milestone_pass=true
default_solvable_successes=10/10
ndnra_frozen_solvable_successes=0/10
ndnra_adaptive_solvable_successes=0/10
blocked_default_honest_failures=2/2
blocked_ndnra_honest_failures=2/2
task_progress_default_better=23
task_progress_ndnra_better=0
task_equivalent=85
generic_score_only_difference=64
not_comparable=0
```

The result is unambiguous: the current Default skill controller reliably performs
the solvable Week 9 contribution task, while the current goal-conditioned NDNRA
adapter does not yet compose a successful full task policy. No NDNRA competence
claim is made. The generic-score-only differences remain diagnostic evidence,
not task-progress wins or grounds for promotion.

Observed authority metrics:

```text
production_action_replacements=0
authority_violations=0
verification_authority_violations=0
support_authority_violations=0
ndnra_automatic_promotions=0
```

NDNRA cannot replace production actions, certify contribution, change support, or
promote itself. No NDNRA Stage 9 implementation was added.

## Persistence

The contribution history and support state use:

- schema identity;
- deterministic ASCII JSON;
- SHA-256 payload checksums;
- atomic sibling staging and replacement;
- strict payload-type checks;
- complete conservative fallback rather than partial recovery.

Missing, corrupted, checksum-mismatched, or incompatible data restores a fresh
Level 4 state and an empty contribution history.

## Artifacts

- `artifacts/week9_contribution/human_contribution_demo.json`
- `artifacts/week9_contribution/support_level_report.json`
- `artifacts/week9_contribution/contribution_history.json`
- `artifacts/week9_contribution/week9_acceptance_report.json`
- `artifacts/week9_contribution/fair_comparison_protocol.json`
- `artifacts/week9_contribution/default_vs_ndnra_fair_comparison.json`
- `artifacts/week9_contribution/default_vs_ndnra_comparison.json`
  (`valid_for_competence_comparison=false`, superseded marker only)

## Validation

```text
real Week 9 artifact regeneration gate: passed
focused Week 9 contribution tests: 29 passed
complete pytest total: 1162 passed
ruff format --check .: 280 files already formatted
ruff check .: passed
mypy .: no issues in 280 source files
pip check: no broken requirements
git diff --check: passed with line-ending normalization warnings for README.md
  and .codexbridge/wiki/manifest.json only
```
