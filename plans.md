# SeedMind Current Plan

This is the single live continuation file for ongoing SeedMind work.

Update this file in place as work progresses. Do not create or update session handover files unless Arash explicitly asks to move to a new session.

## Repository

- Alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Latest completed milestone: NDNRA Adaptive Skill and Outcome Fidelity Planning Refinement
- Inspect Git history for the current commit hash.
- Push policy: never push automatically

## Current stage

- Program: NDNRA
- Last closed stage: NDNRA Adaptive Skill and Outcome Fidelity Planning Refinement
- Current stage: Developmental Network v0.2 — Stage -1 developmental constitution, desired-state ambition, adaptive DESA, and skill-bundle contracts
- Current status: The latest theory corrections are now reflected in the governing plan; implementation must begin with the updated Stage -1 contracts before recurrent-network work
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
- typed internal action proposals separated from an external protected action gateway;
- a minimal adaptive Developmental Executive Steward Architecture (DESA) with skill-local monitors, regional captains, a cross-region executive council, an independent Executive Auditor, constitutional authority, and optional evidence-gated intermediate stewards;
- DESA-managed event partitioning over a preserved raw chronological stream;
- ambition as persistent pressure toward a valued desired state supplied by Nursery purpose, trusted teaching, mature prompts, or purpose-compatible positive outcomes;
- capability gaps as separate obstacle evidence from observed ability, failed requests, and recognised mistakes;
- automatically incubated skill bundles containing a producer, expected-outcome model, verifier, termination model, feedback, and calibration history;
- developmental Outcome Fidelity that learns domain-specific verification from grounded feedback and preserves pending or unverified states;
- bounded producer-verifier iteration controlled by DESA;
- causal responsibility that requires prediction, repetition, intervention, ablation, or contradiction evidence beyond co-activation;
- learned Deterrence plus protected engineering controls for reward, evidence, feedback, verifier, evaluation-window, and audit integrity;
- an ordinary Nursery and a dedicated Executive Nursery;
- human stop, denial, correction, clarification, teaching, and permission as a protected control plane separate from reward.

The v0.2 research programme must remain:

- inside `src/seedmind/research/ndnra` until a later integration ADR;
- deterministic and seeded;
- software-only and symbolic, with physical robotics deferred;
- grounded in the Nursery without a pretrained language model or imported task knowledge as the initial cognitive foundation;
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
- connect to physical robotic actuators;
- turn DESA into a hidden task-solving model or mandatory bottleneck;
- keep an intermediate management layer that adds no measurable benefit;
- treat capability gaps as the complete definition or value source of ambition;
- let producer-verifier agreement certify success without grounded feedback;
- convert unavailable feedback into success instead of pending or unverified outcome state;
- allow ambition to manipulate reward, evidence, feedback, verifier state, evaluation scope, or audit history;
- promote causal responsibility from co-activation alone;
- couple human authority to ordinary reward;
- create persistent ambition without an accepted desired-state source.

Production curiosity remains the sole production action authority. The protected external safety supervisor and human permission channels remain authoritative.

## Current validation baseline

After NDNRA Adaptive Skill and Outcome Fidelity Planning Refinement:

```text
ruff format --check .: 237 files already formatted
ruff check .: passed
mypy: no issues in 237 source files
pytest -q: 986 passed
pip check: no broken requirements
git diff --check: passed
```

The adaptive-skill planning refinement passed the full repository validation baseline without changing the closed v0.1 implementation or test count.

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
- `docs/architecture/decisions/ADR-2026-06-30-ndnra-desa-executive-foundation.md`
- `docs/architecture/decisions/ADR-2026-06-30-ndnra-adaptive-skill-outcome-fidelity.md`

## Next implementation target

The governing post-v0.1 plan is `docs/architecture/NDNRA_Developmental_Network_Implementation_and_Test_Plan_v0.2.md`.

The first authorised implementation boundary is Stage -1 and Stage 0 contracts, followed by Stage 1 and Stage 1A in separate bounded batches:

```text
developmental constitution and ordinary and Executive Nursery curricula
    +
desired-state value-source, ambition, capability-gap, and integrity contracts
    +
minimal adaptive DESA hierarchy, event partitioning, and metacognition
    +
skill-bundle, developmental Outcome Fidelity, and feedback-iteration contracts
    +
v0.2 lifecycle identities and schema separation
    +
reusable sparse recurrent neuron pool
    +
excitatory and inhibitory connections
    +
distributed experience coalitions
    +
deterministic bounded recurrent settling
    +
DESA bootstrap and hierarchical metacognition
```

Stage -1 must prove at the contract and scenario level:

1. DESA begins with skill bundles, regional captains, and a cross-region council rather than one all-knowing captain or a fixed bureaucracy.
2. An intermediate skill steward is optional and survives only when its measured benefit justifies its cost.
3. Event open, continue, split, nest, relate, and close operations preserve the exact raw chronological stream.
4. The ordinary Nursery teaches grounded cognition, desired-state ambition, curiosity, feedback, and temporary skill formation; the Executive Nursery teaches partitioning, routing, incubation, delegation, escalation, verifier calibration, causal investigation, integrity protection, authority, and help-seeking.
5. Ambition preserves an accepted desired state while capability gaps preserve separate obstacle evidence from observed ability, failed requests, or recognised mistakes.
6. Temporary skill bundles represent producer, expected outcome, verifier, termination, feedback, and calibration without predefined domain knowledge.
7. Producer-verifier agreement alone cannot certify success; unavailable feedback preserves pending or unverified outcome state.
8. Human authority remains separate from reward, and reward/evidence/verifier integrity is protected.
9. DESA contains no task solution, pretrained language model, imported task knowledge, or external action authority.

Stage 0 must prove:

1. v0.2 identities and schemas cannot be confused with the closed v0.1 persistence boundary.
2. Cognitive, DESA, value-source, desired-state ambition, capability-gap, skill-bundle, verifier, outcome-state, authority, integrity, and causal-responsibility identities serialise deterministically.
3. Lifecycle transitions are explicit and invalid transitions fail.
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

Stage 1A must prove:

1. Familiar low-risk work can resolve locally while uncertainty and conflict escalate.
2. Several regional captains can contribute without one region monopolising unfamiliar input.
3. Minimal DESA routing beats shuffled routing and a single-central-captain control on usefulness, interference, or compute cost.
4. An optional intermediate steward survives only when it improves a declared benefit metric without unacceptable cost.
5. A temporary skill bundle learns from grounded feedback more reliably than producer self-verification.
6. Confidence and verifier calibration beat raw maximum activation and producer confidence.
7. The Executive Auditor can identify a wrong DESA or verifier decision from independent later evidence.
8. Event partitioning improves reusable recall over one-session and every-step controls.
9. Temporary ambitions preserve their desired-state source separately from capability-gap evidence.
10. Pending or unavailable feedback remains unverified rather than successful.
11. External side effects and production action-authority violations remain zero.

Do not begin broad associative recall, simultaneous multiple-need work, mature ambition commitment, mature skill promotion, dream maintenance, conscience-guided proposals, internet knowledge acquisition, or action-gateway work until Stage 1A passes.

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
