# SeedMind Week 11 Specialist Growth Plan

**Date:** 1 July 2026  
**Stage:** Original SeedMind Week 11  
**Status:** Executed

## Objective

Implement the original roadmap's bounded policy-specialist growth stage from the hardened Week 10 proposal. Week 11 may create, incubate, compare, register, reject, or provisionally accept one temporary specialist. It must not activate that specialist in production or perform Week 12 consolidation.

## Authoritative inputs

Week 11 uses `plans.md`, the archived master implementation plan, hardened Week 10 diagnosis artifacts, the frozen Week 8 skill, the Week 9 authority boundary, and only the NDNRA freeze documents. Old NDNRA architecture, stage evidence, comparison artifacts, and parallel-operation documents are excluded.

## Scope

1. Validate the Week 10 `proposed_not_authorised` skill-expert proposal.
2. Implement the master-plan expert interface and proposal-only router.
3. Incubate bounded candidate profiles on the exact Week 10 cube-like Nursery state.
4. Compare candidate and frozen general controller across repeated seeds.
5. Enforce the 25 percent parameter cap.
6. Prove exact failed-candidate disposal and rollback.
7. Export separate acceptance fields and a brain graph.
8. Accept only for Week 12 retention evaluation.

## Non-goals

Week 11 does not modify the predictive core or frozen skill, grant action authority to the router or specialist, run Week 12 consolidation, integrate NDNRA, or promote a candidate to production.

## Expert-module interface

Inputs:

- `latent_state`
- `current_goal`
- `relevant_memory_summary`
- `available_actions`

Outputs:

- `action_proposal`
- `confidence`
- `expected_result`
- `predicted_goal_progress`
- `abstain`

Every output is a proposal. `production_curiosity` retains primitive-action authority.

## Specialist design

The candidate is a clearance-aware policy expert using raw symbolic geometry and a normalized shape feature, never a privileged `cube` label. Six bounded parameters score distance progress, lateral clearance, route cost, direct-axis preference, confidence, and abstention. It searches for a reachable effective contact cell, proposes one primitive action at a time, and abstains outside scope or safety.

## Router contract

The specialist is eligible only when registered, active in the sandbox, non-abstaining, and above the confidence threshold. Otherwise the router selects the general controller when available or abstains. The router cannot execute actions directly.

## Incubation and comparison

Each candidate profile runs across fixed training seeds with action, transition, success, step, abstention, and checkpoint provenance. Selection is by success rate, then mean steps, then stable profile order. General and specialist controllers then run identical evaluation seeds and budgets.

Required cube-like gain is at least `+0.20`. Preliminary familiar retention must be at least `0.90` on the authoritative Week 8 evaluation cohort.

## Parameter budget

Actual added parameters must not exceed 25 percent of the instantiated seed-core parameter count. Evidence records seed count, cap, actual parameters, float32 memory cost, violations, and gain per parameter.

## Checkpoint and rollback

A pre-growth registry contains only the frozen general controller. A rejected candidate is registered, discarded, and compared with the checkpoint by structured equality and SHA-256 digest. The frozen skill hash must remain unchanged, the failed module and router registration must be removed, and no NDNRA dependency may appear.

## Acceptance gates

All fields must pass independently: authoritative input, module contract, incubation provenance, capability gain, repeated seeds, preliminary retention, router scope, fallback, parameter budget, rollback, failed-candidate disposal, frozen-skill preservation, authority containment, and the NDNRA freeze boundary.

A passing candidate is only `accepted_for_week12`. Week 12 must run full consolidation and retention before stable production activation.
