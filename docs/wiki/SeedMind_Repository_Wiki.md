# SeedMind Repository Wiki

Last refreshed: 1 July 2026

## Current State

- Branch: `main`
- Push policy: do not push automatically.
- Latest completed main-roadmap milestone: original SeedMind Week 9 contribution, reduced support, and fair Default-vs-NDNRA comparison correction.
- Latest completed NDNRA research stage: Developmental Network v0.2 Stage 8.
- Current operating mode: `production_with_ndnra_shadow`.
- Next main-roadmap target: original Week 10 capacity diagnosis.
- Original Week 10 and NDNRA Stage 9: not started or authorised.

## Week 9 Main Roadmap Boundary

Week 9 is closed by the main `seedmind.contribution` package, not by NDNRA
research contracts.

Implemented main contribution behavior:

- typed human contribution requests;
- five-state capability checks;
- frozen Week 8 `approach_and_push` skill reuse;
- grounded outcome verification from actual runtime transitions;
- complete honest failure records;
- checksum-protected contribution history and support-state persistence;
- five-success, `0.80` success-rate, and three-context support-reduction rule;
- support restoration after two grounded familiar failures;
- post-regression evidence epochs before re-promotion.

Observed main-roadmap metrics:

```text
total_attempts=12
total_successes=10
independent_success_rate=0.8333
executed_step_count=172
production_curiosity_retained_count=172
skill_discovery_delta=0
compile_count=0
training_count=0
component_promotion_count=0
authority_violations=0
verification_authority_violations=0
support_authority_violations=0
ndnra_automatic_promotions=0
week9_main_milestone_pass=true
```

## Fair Default-vs-NDNRA Comparison

Commit `cfb8f3c` is preserved but superseded as invalid evidence for NDNRA
competence. The current comparison gives NDNRA the same typed object-to-target
goal and relational state context as Default, trains NDNRA only from
NDNRA-executed sandbox transitions, keeps training and held-out evaluation seeds
disjoint, freezes evaluation, separates adaptive diagnostics, and reports
blocked scenarios separately.

Observed fair-comparison metrics:

```text
experiment_integrity_pass=true
default_competence_pass=true
ndnra_competence_pass=false
blocked_scenario_handling_pass=true
authority_containment_pass=true
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
frozen_evaluation_updates=0
adaptive_ndnra_updates=64
training_evaluation_seed_overlap=0
```

Evidence files:

- `docs/architecture/SeedMind_Week9_Contribution_Evidence_2026-06-30.md`
- `docs/architecture/decisions/ADR-2026-06-30-seedmind-week9-contribution-closure.md`
- `docs/architecture/SeedMind_NDNRA_Parallel_Operating_Model_2026-06-30.md`
- `artifacts/week9_contribution/week9_acceptance_report.json`
- `artifacts/week9_contribution/fair_comparison_protocol.json`
- `artifacts/week9_contribution/default_vs_ndnra_fair_comparison.json`
- `artifacts/week9_contribution/default_vs_ndnra_comparison.json`
  (`valid_for_competence_comparison=false`, superseded marker only)

## Authority Boundary

- Production curiosity remains the only production action authority.
- Default remains the sole production controller.
- NDNRA observes, suggests, trains in bounded diagnostics, and reports evidence
  only as a non-authoritative shadow.
- NDNRA cannot execute, schedule, replace, promote, verify contribution, or
  change support level.
- Automatic NDNRA component promotion remains disabled.
- Human stop, denial, correction, clarification, teaching, and permission remain
  protected controls separate from reward.

## Next Stage Boundary

Original SeedMind Week 10 may begin after the fair Week 9 closure commit.

Explicitly not authorised by Week 9 closure:

- NDNRA Stage 9;
- production action replacement;
- internet access;
- shell access inside the seed;
- source self-modification;
- autonomous background workers;
- new specialist growth.
