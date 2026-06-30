# SeedMind Current Plan

This is the single live continuation file for ongoing SeedMind work.

Update this file in place as work progresses. Do not create or update session handover files unless Arash explicitly asks to move to a new session.

## Repository

- Alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Latest completed milestone: NDNRA Developmental Network Implementation and Test Plan v0.2
- Inspect Git history for the current commit hash.
- Push policy: never push automatically

## Current stage

- Program: NDNRA
- Last closed stage: Original Plan and NDNRA v0.1 Comparison Decision
- Current stage: Developmental Network v0.2 — Stage 0 contracts and lifecycle identities
- Current status: The post-v0.1 implementation and test plan is accepted; isolated Stage 0 and Stage 1 research work is authorised, but production integration and action authority remain prohibited
- Expanded developmental architecture marker: 82%
- Marker interpretation: unchanged because the new document is an implementation and falsification plan, not evidence that a new cognitive capability has passed

Completed bounded increments:

1. Batch 1 — caller-supplied exact-source imagined consequence traces.
2. Batch 2 — deterministic exact-record imagined candidate enumeration.
3. Batch 3 — pure per-step, per-dimension need-alignment annotation.
4. Batch 4 — deterministic caller-order pairwise route comparison.
5. Batch 5 — deterministic unresolved-comparison uncertainty audit.
6. Batch 6 — deterministic caller-nominated safe-experiment proposal contracts.
7. Batch 7 — deterministic explicit human approve, reject, or defer review.
8. Batch 8 — deterministic training-review or explicit configured non-training bypass resolution.

## Current accepted boundary

Standalone NDNRA v0.1 remains closed under its accepted bounded evidence boundary. Its proof stores, persistence schemas, bounded imagination rules, and authority restrictions must not be mutated merely to implement v0.2 research.

The accepted post-v0.1 theory is:

- specialised concurrent regions rather than one uniform mind;
- separate experiences connected through learned need, context, action, outcome, excitation, and inhibition;
- ordinary recruitment of a reusable existing neuron pool rather than one new neuron per experience;
- homeostatic control of connectivity, activation, repeated recruitment, and rare evidence-gated structural expansion;
- regional child-to-adult plasticity with bounded local reopening;
- reversible dormancy and hibernation rather than deletion of memory-bearing structures;
- caller-invoked dream maintenance that cannot create factual evidence or actions;
- exact restoration of the same developmental network after restart;
- protected prohibitions plus directly taught and experience-refined responsibility;
- typed internal action proposals separated from an external protected action gateway.

The v0.2 research programme must remain:

- inside `src/seedmind/research/ndnra` until a later integration ADR;
- deterministic and seeded;
- software-only and symbolic, with physical robotics deferred;
- non-authoritative;
- non-SQLite for cognition;
- provenance-preserving;
- bounded by explicit pass and falsification conditions;
- matched against controls and ablations;
- unable to modify the closed v0.1 proof stores.

The programme must not:

- create factual evidence from dreams or imagination;
- permanently delete memory-bearing neurons or synapses;
- create a neuron automatically for each experience;
- merge separate experiences merely to obtain generalisation;
- grant any region, conscience system, dream process, proposal, or NDNRA component production action authority;
- weaken protected prohibitions through ordinary learning;
- introduce autonomous background workers, queues, or timers;
- persist bounded imagination as real experience;
- merge proof stores;
- connect to physical robotic actuators.

Production curiosity remains the sole production action authority. The protected external safety supervisor and human permission channels remain authoritative.

## Current validation baseline

After NDNRA Developmental Network Implementation and Test Plan v0.2:

```text
ruff format --check .: 237 files already formatted
ruff check .: passed
mypy: no issues in 237 source files
pytest -q: 986 passed
pip check: no broken requirements
git diff --check: passed
```

The planning documents passed the full repository validation baseline without changing the closed v0.1 implementation or test count.

## Current technical sources

Use these for architecture and implementation detail:

- `docs/archive/SeedMind_Bounded_Imagination_Stage_Plan_2026-06-29.md`
- `docs/archive/SeedMind_Consequence_Imagination_Stage_Plan_2026-06-28.md`
- `docs/archive/SeedMind_Master_Implementation_Plan_v0.1.md`
- `docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md`
- `docs/architecture/decisions/ADR-2026-06-29-bounded-imagination-route-comparison.md`
- `docs/architecture/decisions/ADR-2026-06-29-human-permission-review-for-imagined-safe-experiments.md`
- `docs/architecture/decisions/ADR-2026-06-29-explicit-training-review-gate-policy.md`
- `docs/architecture/decisions/ADR-2026-06-29-bounded-imagination-stage-closure.md`
- `docs/architecture/NDNRA_Standalone_Completion_Gap_Audit_2026-06-29.md`
- `docs/architecture/decisions/ADR-2026-06-29-standalone-ndnra-acceptance-and-restart-proof.md`
- `docs/architecture/NDNRA_Retain_Or_Descope_Audit_2026-06-29.md`
- `docs/architecture/decisions/ADR-2026-06-29-ndnra-v0.1-retain-or-descope.md`
- `docs/architecture/decisions/ADR-2026-06-29-normalized-competing-recruitment.md`
- `docs/architecture/decisions/ADR-2026-06-29-locally-derived-representational-saturation.md`
- `docs/architecture/decisions/ADR-2026-06-29-long-horizon-mixed-task-interference.md`
- `docs/architecture/NDNRA_Final_Standalone_Closure_Audit_2026-06-29.md`
- `docs/architecture/decisions/ADR-2026-06-29-standalone-ndnra-v0.1-closure.md`
- `docs/architecture/SeedMind_Original_Plan_NDNRA_Comparison_2026-06-30.md`
- `docs/architecture/decisions/ADR-2026-06-30-original-plan-ndnra-integration-decision.md`
- `docs/architecture/NDNRA_Developmental_Network_Implementation_and_Test_Plan_v0.2.md`
- `docs/architecture/decisions/ADR-2026-06-30-ndnra-developmental-network-implementation-plan.md`

## Next implementation target

The governing post-v0.1 plan is `docs/architecture/NDNRA_Developmental_Network_Implementation_and_Test_Plan_v0.2.md`.

The first authorised implementation boundary is Stage 0 followed by Stage 1 only:

```text
v0.2 typed contracts and lifecycle identities
    +
reusable sparse recurrent neuron pool
    +
excitatory and inhibitory connections
    +
distributed experience coalitions
    +
deterministic bounded recurrent settling
```

Stage 0 must prove:

1. v0.2 identities and schemas cannot be confused with the closed v0.1 persistence boundary.
2. Neuron, connection, region, experience, coalition, need, context, proposal, and outcome identities serialise deterministically.
3. Active, resting, dormant, dream-active, protected, and relearning lifecycle transitions are explicit and invalid transitions fail.
4. Existing v0.1 tests remain unchanged and pass.
5. No runtime adapter or action gateway connection is introduced.

Stage 1 must prove:

1. Experiences are distributed coalitions in an existing reusable neuron pool.
2. Experiences may overlap while retaining separate identity, provenance, and outcomes.
3. Recurrent activity settles within a fixed compute budget.
4. Contradictory episodes remain inspectable.
5. No coalition recruits the complete network.
6. Structural neuron creation remains disabled.
7. SQLite cognition and action-authority violations remain zero.

Do not begin simultaneous multiple-need work, developmental maturity, dream maintenance, conscience, or action proposals until the Stage 1 substrate passes its gate.

The original SeedMind master plan remains the product and MVP spine. The original Week 8 reusable-skill objective remains mandatory and cannot be marked complete from NDNRA research evidence alone.

## Working rules

- Inspect repository status and this file before starting a new batch.
- Implement small bounded tasks directly through CodexBridge when practical.
- Use Codex CLI only when its overhead is justified.
- Run focused checks during implementation and full repository gates before closure.
- Refresh repository wiki and repository-scoped decision memory at completed batch boundaries.
- Create one bounded local commit per completed batch.
- Do not push automatically.
- Do not create a session handover unless Arash explicitly requests one because the session is ending or becoming too heavy.
