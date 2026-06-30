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
- `parallel_comparison.py` replays the exact Default action traces, obtains NDNRA
  proposals from the same pre-action states, scores every proposal, and runs
  isolated NDNRA-only task rollouts after shadow learning.
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

The original closure was reopened because authority-only shadow counters did not
provide comparative performance evidence. Corrected Week 9 now evaluates both
systems while preserving the authority boundary.

For each of the 172 executed Default steps:

```text
recreate the exact contribution scenario and Default action trace
capture the same immutable pre-action state
obtain an NDNRA proposal from that state
score each NDNRA proposal against the fixed Default proposal
execute only the Default action in the production replay
feed the grounded Default transition to NDNRA for shadow learning
```

Candidate scoring combines task relevance and the existing nursery oracle:

```text
combined score = 0.70 * target progress + 0.30 * nursery outcome score
```

After shadow learning, NDNRA receives one isolated rollout on each of the same 12
scenarios. These cloned evaluations measure NDNRA task completion but do not grant
it production authority.

Observed comparison metrics:

```text
total_scenarios=12
total_production_steps=172
default_proposal_count=172
ndnra_observation_count=172
ndnra_proposal_count=171
ndnra_abstention_count=1
agreement_count=34
disagreement_count=137
comparison_count=171
disagreement_comparison_count=137
disagreement_comparison_coverage=1.0
default_better_count=133
ndnra_better_count=4
tied_count=34
mean_default_combined_score=0.1091104458581823
mean_ndnra_combined_score=0.0773852996593519
mean_ndnra_advantage=-0.031725146198830406
default_task_successes=10
default_task_success_rate=0.8333333333333334
ndnra_rollout_attempts=12
ndnra_rollout_successes=0
ndnra_rollout_success_rate=0.0
learned_assembly_count=4
effect_dimension_count=8
```

The result is unambiguous: the current Default skill controller reliably performs
the Week 9 contribution task, while the current NDNRA shadow does not yet compose
a successful full task policy. NDNRA nevertheless produced four locally better
one-step proposals, which remain useful diagnostic evidence rather than grounds
for promotion.

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
- `artifacts/week9_contribution/default_vs_ndnra_comparison.json`

## Validation

```text
focused corrected Week 9 tests: 21 passed
remaining main-product tests: 312 passed
main-product total: 333 passed
early NDNRA tests: 422 passed
controlled and developmental NDNRA tests: 191 passed
remaining NDNRA tests: 208 passed
complete pytest total: 1154 passed
real Week 9 artifact regeneration gate: passed
ruff format --check .: 280 files already formatted
ruff check .: passed
mypy .: no issues in 280 source files
pip check: no broken requirements
git diff --check: passed with line-ending normalization warnings only
```
