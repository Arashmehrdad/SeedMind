# ADR: SeedMind Week 9 Contribution Closure

Date: 30 June 2026
Status: Accepted after comparative-evidence correction
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
export actual NDNRA proposals, candidate comparisons, or NDNRA task outcomes. The
closure was therefore reopened and corrected before continuing to Week 10.

## Decision

Accept the main `seedmind.contribution` implementation as the original SeedMind
Week 9 closure.

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
11. Corrected shadow operation must collect a Default and NDNRA proposal from the
    same pre-action state, score every NDNRA proposal, and compare every
    disagreement.
12. A separate isolated NDNRA-only rollout must cover every Week 9 scenario so
    task-completion rates can be compared without granting production authority.

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

Observed corrected parallel comparison:

```text
total_production_steps=172
ndnra_proposal_count=171
ndnra_abstention_count=1
agreement_count=34
disagreement_count=137
disagreement_comparison_coverage=1.0
default_better_count=133
ndnra_better_count=4
tied_count=34
mean_default_combined_score=0.1091104458581823
mean_ndnra_combined_score=0.0773852996593519
default_task_successes=10/12
ndnra_isolated_task_successes=0/12
production_action_replacements=0
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
- `artifacts/week9_contribution/default_vs_ndnra_comparison.json`
- `docs/architecture/SeedMind_Week9_Contribution_Evidence_2026-06-30.md`

## Consequences

- Original SeedMind Week 9 is closed.
- Main SeedMind owns contribution, grounded verification, failure reporting, and
  support-level state.
- The frozen Week 8 skill is reused without rediscovery or recompilation.
- Competence degradation can restore higher support, and recovery requires a new
  full evidence threshold.
- NDNRA remains non-authoritative but now produces measurable proposals and
  isolated task outcomes for direct comparison.
- The observed NDNRA result is currently weaker than Default: `0/12` isolated
  task successes and only four better one-step candidates versus 133 for Default.
- Original SeedMind Week 10 was not started.
- NDNRA Stage 9 was not started or authorised.
