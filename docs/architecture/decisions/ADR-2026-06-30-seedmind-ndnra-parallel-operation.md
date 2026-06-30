# ADR: SeedMind and NDNRA Parallel Operation

Date: 30 June 2026
Status: Accepted
Scope: main SeedMind development after NDNRA v0.2 Stage 8 closure

## Context

The authorised NDNRA v0.2 research programme is closed through Stage 8. The completed evidence supports continued experimentation but does not justify replacing the original SeedMind product roadmap or granting NDNRA production action authority.

The project needs a practical way to continue the main system while testing whether NDNRA contributes useful learning, recall, verification, skill, and coordination behavior on the same grounded tasks.

## Decision

Adopt `production_with_ndnra_shadow` as the canonical side-by-side operating model.

- Production SeedMind curiosity remains the sole production action selector.
- NDNRA observes the same pre-action state and actual grounded transition.
- NDNRA may emit an optional internal suggestion.
- The production action is always retained for the current step.
- Every valid disagreement must have comparison evidence when the policy requires it.
- NDNRA has no scheduling, execution, replacement, promotion, or production action authority.
- Automatic component promotion is disabled.
- A policy audit must fail closed on action replacement, authority grant, or missing required comparison evidence.
- Existing main SeedMind persistence and NDNRA proof stores remain separate.
- Stage 9 remains unauthorised.

The policy is implemented by `src/seedmind/integration/parallel_operation.py`. The existing live advice acceptance path is routed through this policy.

## Promotion Boundary

Only a specific NDNRA component may be considered for later integration. Consideration requires repeated grounded advantage across varied tasks and seeds, acceptable resource and interference results, explicit rollback and kill-switch behavior, focused tests, and a separate accepted ADR.

No whole-architecture promotion is authorised by this decision.

## Consequences

- The original SeedMind master plan remains the product and MVP spine.
- Main development resumes, including the mandatory reusable-skill objective.
- NDNRA can accumulate grounded side-by-side evidence without controlling current behavior.
- Production-versus-shadow comparisons become a normal evaluation artifact.
- One comparison win is insufficient for promotion.
- Human and external safety controls remain authoritative.
- The expanded developmental architecture marker remains 82%; this policy is an integration boundary, not new cognitive capability evidence.
- No automatic push is authorised.
