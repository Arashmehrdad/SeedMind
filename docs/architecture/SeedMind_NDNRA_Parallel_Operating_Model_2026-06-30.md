# SeedMind and NDNRA Parallel Operating Model

Date: 30 June 2026
Status: Active main-project operating model
Scope: bounded side-by-side operation of production SeedMind and non-authoritative NDNRA

## 1. Purpose

SeedMind continues along the original product and MVP roadmap while NDNRA runs beside it as a developmental shadow system.

The purpose is to collect real comparative evidence without replacing the trusted production path or granting NDNRA action authority.

## 2. Canonical Flow

```text
Observation and current state
        |
        +---- Production SeedMind curiosity
        |        |
        |        +---- selects the only action executed by the runtime
        |
        +---- NDNRA shadow
                 |
                 +---- observes the same pre-action state
                 +---- activates needs and learned experience
                 +---- emits an optional internal suggestion
                 +---- never executes or replaces the production action

Executed production transition
        |
        +---- trains the existing predictive and curiosity systems
        +---- becomes grounded observed evidence for NDNRA
        +---- supports comparison when production and NDNRA disagree
```

## 3. Authority Boundary

The default policy is `production_with_ndnra_shadow`.

- Production curiosity remains the sole production action selector.
- The retained action must always equal the production action.
- NDNRA suggestions have no action authority.
- NDNRA cannot schedule, execute, promote, or replace an action.
- Automatic component promotion is disabled.
- Human permission, stop, denial, correction, and safety controls remain authoritative.
- Stage 9 remains unauthorised.

The policy fails closed if any session reports a replaced production action, an NDNRA authority grant, or an uncovered disagreement where comparison evidence is required.

## 4. Learning and Comparison

For every production step, NDNRA receives the same observation and the grounded result of the action that was actually executed.

When NDNRA proposes the same action as production, the agreement is recorded. When it proposes a different valid action, the candidates are compared after both candidates are fixed. The comparison is evidence only and does not alter the current production action.

The audit records:

- total production steps;
- retained production actions;
- NDNRA shadow observations;
- suggestions and disagreements;
- comparison coverage;
- cases where the NDNRA candidate would have scored better;
- authority violations;
- automatic promotions.

## 5. Component Promotion Rule

A complete NDNRA replacement is not permitted. A specific component may be considered later only through a separate bounded integration decision.

The required sequence is:

1. run the component in shadow across varied tasks and seeds;
2. collect grounded comparisons against the existing component;
3. demonstrate repeatable benefit without unacceptable interference, cost, or safety regression;
4. define one narrow advisory integration boundary;
5. add explicit tests, rollback, kill switch, and human approval where required;
6. create and accept a separate ADR;
7. integrate only that component, initially without action authority.

A component is not promoted merely because it wins one comparison or performs well on a scenario used to design it.

## 6. Current Implementation

The canonical policy and audit contracts are implemented in:

- `src/seedmind/integration/parallel_operation.py`

The production and shadow execution path reuses:

- `src/seedmind/integration/candidate_session.py`;
- `src/seedmind/integration/unified_shadow.py`;
- `src/seedmind/integration/developmental_signals.py`;
- `src/seedmind/integration/bounded_advice.py`;
- `src/seedmind/integration/comparison_oracle.py`.

The existing advice acceptance path runs its candidate session through the canonical parallel-operation policy before using the result.

Corrected original SeedMind Week 9 also applies this operating intent to human
contribution evaluation through:

- `src/seedmind/contribution/parallel_comparison.py`;
- exact deterministic replay of the frozen Default action traces;
- same-state NDNRA proposals and complete proposal scoring;
- isolated NDNRA-only rollouts across the same scenario set;
- `artifacts/week9_contribution/default_vs_ndnra_comparison.json`.

The corrected Week 9 evidence found Default task success of `10/12` and isolated
NDNRA task success of `0/12`. Across 171 scored NDNRA proposals, Default was better
133 times, NDNRA was better four times, and 34 comparisons tied.

## 7. Persistence Boundary

The main SeedMind stores and NDNRA research proof stores remain distinct.

- Main episodic SQLite memory remains a product subsystem, not NDNRA cognition.
- NDNRA shadow learning may use its accepted local graph and explicit research persistence boundaries.
- Proof stores are not merged merely because both systems observe the same transition.
- Bounded imagination is not converted into factual experience.
- Only actual production transitions and accepted grounded feedback may become observed evidence.

## 8. Immediate Next Work

The original reusable-skill and contribution objectives are now closed with
parallel evidence. Original Week 10 may proceed while comparison remains mandatory.

Near-term batches should:

1. preserve same-state Default-vs-NDNRA proposals in subsequent roadmap stages;
2. keep task outcomes separate from one-step candidate scores;
3. expand comparison across new tasks, contexts, and random seeds;
4. measure NDNRA usefulness, calibration, interference, latency, CPU, and memory;
5. investigate why current NDNRA local proposals do not compose into successful
   full contribution policies;
6. keep promotion disabled until a component-specific ADR is accepted.
