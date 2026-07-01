# ADR: SeedMind Week 9 Contribution Closure

Date: 30 June 2026
Status: Accepted for the main SeedMind Week 9 milestone; NDNRA comparison provisions superseded on 1 July 2026 by the freeze ADR
Scope: original SeedMind Master Implementation Plan Week 9

## Context

The original SeedMind roadmap requires Week 9 to convert the familiar Week 8
`approach_and_push` capability into verified human contribution and to reduce
support only after competence is proven.

Producer-verifier agreement, NDNRA agreement, imagination, or self-report cannot
certify contribution. Evaluation cannot silently train, compile, promote, or
increase discovery. Human authority remains separate from reward and ordinary
learning. NDNRA remains a non-authoritative shadow under the accepted parallel
operating policy.

The initial Week 9 closure recorded only authority counters and did not obtain or
export actual NDNRA proposals, candidate comparisons, or NDNRA task outcomes. A
later commit, `cfb8f3c`, added a comparison but was methodologically invalid for
NDNRA competence assessment because NDNRA lacked the same typed object-to-target
goal and relational state context as Default, learned from Default evaluation
actions, counted generic-score-only differences as task wins, mixed blocked
scenarios into ordinary task-success percentages, and exposed one ambiguous
`pass_gate`. Week 9 was therefore reopened again and corrected before continuing
to Week 10.

## Decision

Accept the main `seedmind.contribution` implementation as the original SeedMind
Week 9 closure.

The main closure rests on human contribution, grounded verification, honest failure, persistence, and support-transition evidence. Items 11-16 below describe a historical adapter comparison and are not requirements for Week 9 closure or future SeedMind work. They are superseded by `ADR-2026-07-01-freeze-ndnra-for-separate-project.md`.

The accepted design is:

1. Human contribution requests are typed and bind capability, outcome, object,
   target, learned context, permission, verification, and requested support.
2. Capability inspection distinguishes unavailable, unproven, degraded,
   context-mismatched, and verified states.
3. Contribution success requires grounded runtime state and actual-transition
   evidence.
4. Failure preserves the reason, attempted capability, failed preconditions,
   interruption, uncertainty, requested support, verification state, and
   authority audit.
5. Support reduction requires at least five verified independent familiar
   successes, an 0.80 success rate, and three distinct familiar contexts within
   the declared evidence window.
6. One success cannot reduce support. Weak, stale, contradictory, degraded,
   unsafe, context-mismatched, or unverified evidence blocks reduction.
7. Two consecutive grounded familiar failures restore Level 4. Degraded or unsafe
   evidence can restore Level 4 immediately.
8. A support rollback starts a new promotion-evidence epoch. Earlier successes
   cannot be reused for re-promotion.
9. Missing, corrupt, or incompatible persisted state fails safely to a complete
   fresh Level 4 state and empty history.
10. Production curiosity retains every executed primitive action. NDNRA has no
    production execution, verification, support, scheduling, replacement, or
    promotion authority, and automatic NDNRA promotion remains disabled.
11. Fair shadow comparison must give both controllers the same initial state,
    human request, object, target, available primitive actions, budgets, safety
    and interruption constraints.
12. NDNRA must receive an explicit typed goal and relational state context rather
    than only available actions.
13. NDNRA training must use NDNRA-executed sandbox transitions, with disjoint
    training and held-out evaluation seeds.
14. Frozen held-out counterfactual comparisons must update neither controller and
    must classify outcomes by task progress before generic developmental score.
15. Separate frozen and adaptive NDNRA-only rollouts must report task-completion
    rates without granting production authority.
16. Solvable and intentionally blocked scenarios must be reported separately.

## Evidence

Deterministic evaluation sequence:

```text
5 verified familiar successes
2 grounded familiar failures
5 fresh verified familiar recovery successes
```

Observed metrics:

```text
total_attempts=12
total_successes=10
independent_success_rate=0.8333333333333334
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
```

Observed historical goal-conditioned adapter comparison:

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
frozen_evaluation_updates=0
adaptive_ndnra_updates=64
training_evaluation_seed_overlap=0
authority_violations=0
```

Observed support behavior:

```text
one success does not reduce support
fifth initial verified success reduces Level 4 to Level 3
two consecutive grounded failures restore Level 4
four fresh recovery successes do not reduce support
fifth fresh recovery success reduces Level 4 to Level 3
final support level is Level 3
```

Artifacts:

- `artifacts/week9_contribution/human_contribution_demo.json`
- `artifacts/week9_contribution/support_level_report.json`
- `artifacts/week9_contribution/contribution_history.json`
- `artifacts/week9_contribution/week9_acceptance_report.json`
- `artifacts/week9_contribution/fair_comparison_protocol.json`
- `artifacts/week9_contribution/default_vs_ndnra_fair_comparison.json`
- `artifacts/week9_contribution/default_vs_ndnra_comparison.json`
  (`valid_for_competence_comparison=false`, superseded marker only)
- `docs/architecture/SeedMind_Week9_Contribution_Evidence_2026-06-30.md`

## Consequences

- Original SeedMind Week 9 is closed.
- Main SeedMind owns contribution, grounded verification, failure reporting, and
  support-level state.
- The frozen Week 8 skill is reused without rediscovery or recompilation.
- Competence degradation can restore higher support, and recovery requires a new
  full evidence threshold.
- The goal-conditioned adapter comparison is retained as historical diagnostic evidence only. It is not a competence claim about the complete NDNRA architecture.
- NDNRA is frozen in SeedMind for later separate-project extraction; no further comparison, promotion, integration, or Stage 9 work is authorised here.
- Original SeedMind Week 10 was not started and is the next authorised main-product stage.
