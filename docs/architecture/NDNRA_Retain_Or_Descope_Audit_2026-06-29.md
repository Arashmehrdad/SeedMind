# NDNRA Retain-or-Descope Audit

Date: 29 June 2026
Scope: standalone NDNRA research architecture only
Status: accepted planning audit

## Decision boundary

This audit resolves the seven expanded research questions left open after Standalone NDNRA Acceptance and Restart Proof Batch 2.

It does not compare NDNRA with the original SeedMind roadmap, authorize integration, add production action authority, or claim that deferred research has been solved.

Classification terms:

- `retain for standalone closure`: must be implemented and independently evidenced before NDNRA v0.1 can close;
- `already sufficiently represented`: the current bounded implementation and evidence satisfy the v0.1 claim, while broader variants remain future research;
- `defer post-v0.1`: explicitly outside the v0.1 closure claim and retained as a later research question.

The expanded developmental architecture marker remains 82%. An audit changes scope clarity, not implemented capability.

## Audit result

| Research area | Repository evidence | Decision | Reason |
| --- | --- | --- | --- |
| Learned context-similarity weights | `contextual_consequence_transfer.py` exposes fixed validated component weights and thresholds; `test_ndnra_contextual_consequence_transfer.py` proves exact-first bounded transfer, attenuation, contradiction handling, and zero action authority. Architecture Section 17.21 explicitly states that the weights are fixed configuration rather than learned semantics. | Defer post-v0.1 | Exact evidence remains primary and fixed bounded transfer is sufficient for the present consequence-model claim. Learning similarity weights is a separate generalisation problem requiring its own provenance, calibration, and overgeneralisation controls. |
| Semantic abstraction above grounded context signatures | No semantic-abstraction implementation or dedicated experiment exists. Current consequence evidence uses exact grounded `ContextSignature` values and bounded structural transfer. | Defer post-v0.1 | Semantic abstraction is not required by the Section 20 prototype gate. Adding it would materially widen the architecture from grounded transfer to learned representation and requires a separate falsifiable stage. |
| Coordination of multiple simultaneous needs | The first prototype intentionally uses one `NeedPulse`; the heat-fan experiment proves persistent single-need recruitment until environmental resolution. Architecture Section 19 specifies one need pulse and Section 21 retains simultaneous-need coordination as an open question. | Defer post-v0.1 | NDNRA v0.1 is explicitly a single-active-need architecture. Multi-need competition or cooperation is important future work but is not needed to validate the local-learning, recall, dormancy, and growth hypothesis. |
| Spreading-activation normalization under competing recruitment | `LocalNeuralGraph.recall_action()` bounds depth and thresholds but sums incoming activation without an explicit normalization rule. Existing recall tests cover one bounded graph and do not test fan-in duplication or competing recruited assemblies. | Retain for standalone closure | Finite depth prevents infinite execution but does not prove stable recruitment as graph fan-in grows. A local normalization mechanism and adversarial competing-recruitment experiment are required before claiming bounded developmental growth remains stable. |
| Locally derived representational saturation | `GrowthPressure`, `EvidenceDrivenGrowthController.observe_unresolved_interaction()`, `NDNRARuntimeAdaptiveState.observe()`, and all current growth experiments accept `capacity_saturation` from the caller. Experiments normally supply `1.0`; no graph-local saturation estimator exists. | Retain for standalone closure | The architecture claims that insufficient local capacity creates growth pressure. That claim is incomplete while saturation is externally asserted rather than derived from inspectable local graph state. |
| Bounded initial-connection policy for newly created neurons | `EvidenceDrivenGrowthController.grow_targeted_specialist()` ranks local eligibility, selects at most two positive-trace members from the last active set, obeys `maximum_specialists`, and blocks duplicate membership. Structural-growth and multi-growth evidence show targeted membership, equal-capacity control, bounded repeated growth, and preservation of old assemblies. | Already sufficiently represented | For the v0.1 specialist-growth mechanism, new structural nodes already receive deterministic, evidence-scoped, bounded initial membership. A generic policy for arbitrary neuron types is deferred because v0.1 does not claim unrestricted neuron creation. |
| Long-horizon interference and adaptability across mixed tasks | `consolidation_interference_experiment.py` proves a deterministic 12-step three-condition interference result: no consolidation, naive consolidation, and retention-gated replay. Tests prove bounded replay, unchanged source mastery, continued new learning, zero action-authority violations, and no SQLite cognition. | Retain for standalone closure | Current evidence is a short bounded proxy. Full standalone closure still needs a longer mixed-task sequence with repeated task switching, retained old-task performance, continued novel-task learning, bounded replay, and no progressive structural or authority drift. |

## Explicit v0.1 closure scope

NDNRA v0.1 may close with these declared boundaries:

- one active need pulse at a time;
- grounded exact context signatures;
- fixed, bounded, inspectable contextual-transfer weights;
- specialist interaction growth rather than unrestricted generic neuron creation;
- no claim of learned semantic abstraction or general multi-need arbitration.

These are scope boundaries, not hidden assumptions. They must appear in the final NDNRA closure record.

## Retained work required before final closure

Three capabilities remain mandatory:

1. local spreading-activation normalization;
2. locally derived representational saturation;
3. long-horizon mixed-task interference and adaptability evidence.

The bounded initial-connection question is closed for the v0.1 specialist mechanism. Learned similarity, semantic abstraction, and simultaneous needs remain explicit post-v0.1 research.

## Next standalone stage

# Normalized Recruitment and Local Saturation

This is the smallest next stage because local saturation should be measured over stable normalized recruitment rather than over an activation process whose fan-in behaviour is still unproven.

### Batch 1: normalized competing recruitment

Required evidence:

1. Activation remains finite and bounded under duplicated incoming support and competing assemblies.
2. Normalization is computed from local or directly inspectable neighbourhood state, not a global planner or opaque utility.
3. The existing heat-fan chain still passes with the same deterministic action sequence.
4. Shallow recall still fails and deeper effort-based recall still succeeds after dormancy.
5. Duplicating irrelevant fan-in cannot win solely through connection count.
6. Tie handling and candidate ordering remain deterministic.
7. No SQLite cognition, worker, timer, scheduler, recommendation, or production action authority is introduced.

### Batch 2: locally derived saturation and growth gating

Required evidence:

1. Saturation is derived from graph-local recruitment and representational state rather than supplied as an unrestricted caller scalar.
2. An unsaturated graph with remaining useful representational capacity does not create growth pressure solely from one unresolved event.
3. Repeated unresolved error under high locally measured saturation creates bounded growth pressure.
4. Low local saturation blocks growth even when curiosity and ambition relevance are high.
5. High saturation without unresolved error does not trigger growth.
6. Targeted growth still beats equal random capacity and preserves old assemblies.
7. The derived saturation report is deterministic, inspectable, and restart-safe if persisted later.
8. No new action-selection, recommendation, scheduling, execution, integration, or production authority is created.

## Later retained stage

After normalization and local saturation pass, implement:

# Long-Horizon Mixed-Task Interference and Adaptability

Minimum acceptance requirements:

- multiple alternating old and new task families over a substantially longer deterministic horizon than the current 12-step experiment;
- explicit no-consolidation, naive-protection, and bounded retention-triggered replay controls;
- retained old-task score above a declared floor;
- novel-task learning above a declared floor;
- no unbounded replay accumulation;
- no progressive specialist duplication or uncontrolled structure growth;
- unchanged source evidence and mastery counts from replay alone;
- zero action-authority violations and zero SQLite cognition;
- exact deterministic rerun and restart equivalence for the accepted evidence boundary.

## Sequence to standalone NDNRA closure

1. Complete Normalized Recruitment and Local Saturation.
2. Complete Long-Horizon Mixed-Task Interference and Adaptability.
3. Run the final cross-capability authority, persistence, and closure audit.
4. Only after standalone NDNRA closure, compare it with the original SeedMind plan.
5. Decide explicitly whether, where, and how integration should occur.
