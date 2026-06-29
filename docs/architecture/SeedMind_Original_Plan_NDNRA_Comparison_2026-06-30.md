# SeedMind Original Plan and NDNRA v0.1 Comparison Audit

Date: 30 June 2026  
Status: Accepted comparison boundary; integration implementation not approved  
Scope: Original SeedMind master implementation plan versus closed standalone NDNRA v0.1

## 1. Executive decision

The original SeedMind master implementation plan remains the governing product, MVP, Nursery, human-apprenticeship, safety, evaluation, and competition roadmap.

Standalone NDNRA v0.1 is not a replacement for that roadmap. It is a completed bounded research architecture that may later supply selected cognitive mechanisms for local memory, need-driven recall, consequence learning, retention-gated consolidation evidence, and specialist-interaction growth.

The recommended architecture direction is therefore:

```text
retain the original SeedMind product and developmental runtime spine
    +
adapt selected memory, recall, consequence, consolidation, and growth seams around NDNRA
    +
keep NDNRA non-authoritative and isolated until separate integration gates pass
```

This comparison accepts no runtime integration. In particular, it does not:

- merge either isolated NDNRA proof store into a cognitive runtime checkpoint;
- persist bounded imagination;
- grant NDNRA advice, scheduling, execution, growth, route-ranking, or production action authority;
- replace production curiosity as the sole current production action selector;
- reopen any closed NDNRA v0.1 stage;
- claim that NDNRA satisfies the original Week 8 reusable-skill objective;
- change the expanded developmental architecture marker from 82%.

## 2. Evidence and scope

This audit uses:

- `docs/archive/SeedMind_Master_Implementation_Plan_v0.1.md`;
- `docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md`;
- `docs/architecture/NDNRA_Final_Standalone_Closure_Audit_2026-06-29.md`;
- `docs/architecture/decisions/ADR-2026-06-29-standalone-ndnra-v0.1-closure.md`;
- the current production Nursery, predictive, curiosity, ambition, apprenticeship, memory, and shadow-integration modules;
- the accepted NDNRA standalone proof and persistence boundaries.

Standalone NDNRA v0.1 is treated as closed only under its declared scope:

- one active need pulse at a time;
- grounded exact context signatures;
- fixed bounded inspectable contextual-transfer weights;
- bounded specialist-interaction growth;
- no semantic abstraction claim;
- no simultaneous multi-need arbitration claim;
- no production integration or production action authority;
- two separate isolated proof stores;
- bounded imagination remaining in memory, non-evidentiary, and non-authoritative.

## 3. Classification legend

Every disposition in this audit uses one of these exact classifications.

| Classification | Meaning in this decision |
| --- | --- |
| `retain unchanged` | The original component remains required and NDNRA does not alter its role. |
| `adapt around NDNRA` | Keep the original component, but revise its interfaces or responsibilities so NDNRA can coexist without duplicating authority. |
| `replace with NDNRA` | Remove only the named original cognitive mechanism after evidence shows NDNRA safely supplies that same responsibility. |
| `partially integrate` | Combine a bounded NDNRA capability with an original component while preserving the original component's remaining responsibilities. |
| `keep isolated` | Preserve the capability as a research, proof, observer, or shadow subsystem with no production influence. |
| `postpone` | Defer the component until prerequisite evidence exists or the MVP scope permits it. |
| `reject` | Do not implement or approve the named interpretation because it conflicts with accepted architecture or authority boundaries. |

## 4. Section-by-section disposition of the original master plan

This index classifies every top-level original-plan component. Detailed subsystem and week-by-week decisions follow.

| Original section | Primary classification | Decision |
| --- | --- | --- |
| 1. Executive summary and developmental story | `adapt around NDNRA` | Retain the complete developmental story, but describe NDNRA as a candidate substrate rather than proof that the full story is complete. |
| 2. Product definition, packages, and commercial wedge | `retain unchanged` | NDNRA does not replace the body-independent runtime, adapters, observatory, or research-market positioning. |
| 3. Foundational philosophy | `retain unchanged` | Learning machinery, grounded development, corrigibility, usefulness, and bounded truth-seeking remain governing principles. |
| 4. Foundational traits | `retain unchanged` | Humility, patience, bounded courage, consequence care, forgiveness, play, asking why, and wisdom before power remain external behavioural requirements and tests. |
| 5. Motivational architecture | `partially integrate` | Existing drives remain distinct; one selected active need and ambition relevance may modulate NDNRA locally. |
| 6. Purpose and goal hierarchy | `retain unchanged` | Protected principles, purpose, ambition, milestones, micro-goals, and actions remain the controlling hierarchy. |
| 7. Native SeedMind architecture | `adapt around NDNRA` | Preserve the runtime spine and add only typed, bounded seams to an optional NDNRA cognitive substrate. |
| 8. Human apprenticeship | `retain unchanged` | Requests, demonstrations, corrections, approval, clarification, support levels, and help-seeking remain owned by the apprenticeship system. |
| 9. Memory architecture | `adapt around NDNRA` | Keep working, audit, caregiver, developmental, and evidence memory; move future cognitive recall away from unrestricted SQLite lookup. |
| 10. Learning architecture | `partially integrate` | Keep predictive and controller learning; NDNRA may add local eligibility, local consequence memory, dormancy, and effort-based recall. |
| 11. Ambition implementation | `retain unchanged` | Ambition generation, commitment, budgets, milestones, pause, and retirement remain original runtime responsibilities. |
| 12. Capacity diagnosis and structural growth | `partially integrate` | Keep the diagnostic ladder and product growth gate; NDNRA local saturation and specialist interactions may supply bounded evidence. |
| 13. Consolidation and artificial sleep | `partially integrate` | Keep retention, rollback, and stable checkpoint goals; reuse only bounded NDNRA evidence and human-approved operations after later integration approval. |
| 14. Protected safety supervisor | `retain unchanged` | Safety remains external to learning and authoritative over all actions, resources, permissions, and restoration. |
| 15. Competition Nursery | `retain unchanged` | The symbolic 2D Nursery remains the MVP environment; the heat-world prototype remains research evidence only. |
| 16. MVP claims and acceptance criteria | `adapt around NDNRA` | Preserve the full MVP claim and thresholds; do not count standalone NDNRA proofs as completion of unrelated Nursery objectives. |
| 17. Scientific experiment matrix | `adapt around NDNRA` | Retain baselines and ablations and add matched NDNRA shadow and substrate comparisons. |
| 18. Metrics | `adapt around NDNRA` | Retain original product metrics and add recall cost, local interference, dormancy, proof-store integrity, and authority invariance. |
| 19. Technical stack and hardware target | `retain unchanged` | Current Python, PyTorch, Gymnasium, Windows, deterministic, and local-compute constraints remain valid. |
| 20. Repository structure | `adapt around NDNRA` | Keep the current implemented repository layout and the isolated `research/ndnra` and integration-observer boundaries. |
| 21. Core data contracts | `adapt around NDNRA` | Preserve original contracts and add only typed signal, provenance, checkpoint, and shadow evidence contracts through later ADRs. |
| 22. Testing strategy | `adapt around NDNRA` | Retain all original tests and add matched-control, zero-authority, persistence, corruption, and migration gates. |
| 23. Fourteen-week roadmap | `adapt around NDNRA` | Keep the roadmap as the product sequence; adjust Weeks 7, 8, 10, 11, and 12 without treating NDNRA as roadmap completion. |
| 24. MVP demonstration script | `adapt around NDNRA` | Keep the visible developmental story and show NDNRA only where actual integrated evidence later exists. |
| 25. Observatory dashboard | `adapt around NDNRA` | Add local assemblies, recall depth, dormancy, proof provenance, and authority status without removing original panels. |
| 26. Risk register | `adapt around NDNRA` | Add dual-memory divergence, false equivalence, proof-store misuse, hidden authority, and migration risks. |
| 27. Strict MVP non-goals | `retain unchanged` | Preserve all original non-goals and the current NDNRA restrictions. |
| 28. Competition positioning | `adapt around NDNRA` | NDNRA strengthens the developmental-memory narrative but must not be presented as production-ready or as the full MVP. |
| 29. Post-MVP roadmap | `adapt around NDNRA` | Route semantic abstraction, multi-need coordination, and wider neural growth into later evidence-gated versions. |
| 30. First 72 hours | `reject` | Treat this as completed historical startup guidance, not as a current work order. |
| 31. Definition of done | `adapt around NDNRA` | Preserve every original product condition; add NDNRA only where later integration evidence directly satisfies a condition. |
| 32. Founding statement | `retain unchanged` | NDNRA does not alter the project's founding commitments. |
| 33. Immediate decision checklist | `adapt around NDNRA` | Preserve the decisions already made and add explicit no-authority, no-proof-store-merge, and no-imagination-persistence conditions. |
| 34. Final implementation rule | `retain unchanged` | The small seed, grounded learning, human relationship, justified growth, retention, safety, and portability remain final tie-breakers. |

## 5. Detailed product and architecture comparison

### 5.1 Product, philosophy, and developmental governance

| Original component | NDNRA relationship | Classification | Decision |
| --- | --- | --- | --- |
| Body-independent developmental runtime | NDNRA is body-independent but covers only a bounded cognitive research substrate. | `retain unchanged` | Preserve SeedMind core, adapters, and observatory as product packages. |
| Small seed without task knowledge | Local graph state can begin empty and learn from grounded transitions. | `retain unchanged` | Keep the no-task-knowledge birth condition. |
| Protected principles and North Star | NDNRA contains no replacement purpose or safety authority. | `retain unchanged` | Purpose remains external and higher-order. |
| Joint foundational traits | Confidence, contradiction, help, human review, and bounded growth offer partial implementation evidence only. | `retain unchanged` | Continue testing the traits across the whole runtime. |
| Distinct developmental drives | NDNRA can consume a compact active need and modulatory signals but cannot arbitrate all drives. | `partially integrate` | Keep the original need engine and expose one bounded selected pulse to NDNRA. |
| Purpose-to-action hierarchy | NDNRA reconstructs candidate chains but must not bypass milestones, permission, or production control. | `retain unchanged` | Preserve explicit hierarchy and external authority. |
| Product and competition claims | NDNRA proves a bounded local-memory architecture, not the complete MVP. | `adapt around NDNRA` | Use NDNRA as supporting evidence only after scope is stated precisely. |

### 5.2 Nursery, perception, prediction, and self-model

| Original component | NDNRA relationship | Classification | Decision |
| --- | --- | --- | --- |
| Symbolic 2D SeedMind Nursery | The NDNRA heat world is a prototype, not a replacement product environment. | `retain unchanged` | Continue using the Nursery for the product story and acceptance gates. |
| Primitive action and observation contracts | Existing NDNRA shadow code already consumes typed production observations and actions. | `adapt around NDNRA` | Preserve contracts and expose bounded observation copies to shadow adapters only. |
| Symbolic perception encoder | NDNRA assumes grounded context and local effects; it does not replace perception. | `retain unchanged` | Keep the encoder as the body-facing representation layer. |
| GRU predictive seed core | NDNRA learned consequences and local chains complement, but do not replace, recurrent next-state learning. | `retain unchanged` | The predictive core remains the production training baseline. |
| Consequence prediction head | NDNRA has exact-context local consequence records with provenance and uncertainty. | `partially integrate` | Compare predictions side by side; do not create two authoritative consequence selectors. |
| Confidence and calibration | Both systems estimate confidence differently. | `adapt around NDNRA` | Preserve separate confidence semantics and never combine them into an unexplained scalar. |
| Self-model and controllability | The self-model can provide typed controllability evidence to NDNRA. | `partially integrate` | Self-model remains authoritative for body ownership; NDNRA records local effects only. |
| Unified developmental state | NDNRA graph state is too rich and distinct to be collapsed into one opaque field. | `adapt around NDNRA` | Store only handles, summaries, and current pulse information in the explicit developmental state. |

### 5.3 Curiosity, ambition, human apprenticeship, and contribution

| Original component | NDNRA relationship | Classification | Decision |
| --- | --- | --- | --- |
| Production curiosity policy | Current accepted boundaries explicitly keep production curiosity as sole action authority. | `retain unchanged` | Do not allow NDNRA candidate order, advice, or imagination to choose an action. |
| Curiosity learning-progress signals | NDNRA can use novelty and learning-progress modulation. | `partially integrate` | Feed bounded typed measurements after a separate integration ADR. |
| Persistent ambition engine | NDNRA consumes ambition relevance but does not generate or manage the ambition portfolio. | `retain unchanged` | Keep candidate adoption, commitment, budgets, and milestones in the original engine. |
| Teacher demonstration and ambition formation | Human and ambition systems already generate auditable evidence suitable for modulation. | `partially integrate` | Preserve the original event source and let NDNRA learn only local consequences. |
| Request interpretation and help-seeking | NDNRA does not implement the complete ambiguity, competence, risk, and support policy. | `retain unchanged` | Apprenticeship manager remains responsible. |
| Human correction and approval | NDNRA supports local modulatory effects from correction and approval. | `partially integrate` | Corrections and approvals remain protected external signals; local updates cannot reinterpret permission. |
| Support-level progression | NDNRA has no evidence-backed replacement for Levels 4 to 0. | `retain unchanged` | Continue original competence and verified-success promotion rules. |
| Human contribution and verification | NDNRA does not complete requested Nursery work or verify human value. | `retain unchanged` | Week 9 contribution remains a separate product objective. |

### 5.4 Memory, recall, belief, and skill

| Original component | NDNRA relationship | Classification | Decision |
| --- | --- | --- | --- |
| Recurrent working memory | NDNRA does not replace the active recurrent state or explicit context buffer. | `retain unchanged` | Keep current working memory. |
| SQLite episodic store as audit and scientific evidence | NDNRA explicitly permits SQLite for event recording, debugging, and comparison. | `adapt around NDNRA` | Preserve append-only evidence and inspection roles. |
| SQLite retrieval as the mechanism that remembers how to act | This conflicts with NDNRA's local activation and no-SQLite-cognition invariant. | `replace with NDNRA` | Replace only after live Nursery evidence proves equivalent or better recall; until then, the current path remains the baseline. |
| Belief registry and contradiction evidence | NDNRA exact local consequences overlap with causal evidence but do not supply semantic belief abstraction. | `adapt around NDNRA` | Keep symbolic beliefs for explanation; link them to NDNRA provenance rather than duplicating hidden truth claims. |
| Semantic or concept memory | NDNRA v0.1 supports grounded exact contexts, not semantic abstraction. | `postpone` | Preserve as a later original-plan objective. |
| Developmental and caregiver memory | NDNRA does not replace human-readable histories and support progression evidence. | `retain unchanged` | Keep external audit records. |
| Evidence memory and source provenance | NDNRA has strong exact-event provenance, correlation controls, and contradiction preservation. | `partially integrate` | Reuse provenance identities through typed links, not shared mutable storage. |
| Week 8 reusable `approach_and_push` skill | Distributed assemblies and ordered consequence chains are related but have not proved a compiled Nursery skill with preconditions, termination, generalisation, and reuse. | `partially integrate` | Keep the Week 8 objective. A future skill record may reference NDNRA assemblies, but NDNRA does not currently replace the compiler or skill registry. |
| Treating an NDNRA chain as automatic Week 8 completion | The evidence domains and pass gates differ. | `reject` | Require explicit Nursery skill acceptance. |
| Dormancy without deletion | Original memory and pruning language can be adapted to reversible access reduction. | `partially integrate` | Use dormancy for memory-bearing structures; preserve inspectability. |
| Permanent deletion of NDNRA memory-bearing neurons or synapses | Conflicts with the accepted NDNRA invariant. | `reject` | Permit archival or removal only for non-memory infrastructure or under a future replacement ADR. |

### 5.5 Learning, imagination, consolidation, and persistence

| Original component | NDNRA relationship | Classification | Decision |
| --- | --- | --- | --- |
| Immediate recurrent update and online predictive learning | NDNRA adds local eligibility and local effect updates. | `partially integrate` | Keep both learning timescales separate and measurable. |
| Native predictive losses | NDNRA does not replace PyTorch predictive training or its objective. | `retain unchanged` | Continue the predictive core as a baseline and production learner. |
| Local eligibility traces | NDNRA has completed deterministic delayed-credit evidence. | `partially integrate` | Candidate for later live cognitive learning behind a shadow gate. |
| Effort-based recall depth and measurable recall cost | Not present as an original explicit mechanism. | `partially integrate` | Add as a bounded recall mechanism without altering action authority. |
| Scheduled consolidation | NDNRA scheduling is proposal-only and caller-driven; execution requires explicit approval. | `adapt around NDNRA` | Replace fixed automatic timing assumptions with evidence-aware review proposals where later approved. |
| Retention-gated replay | NDNRA has bounded exact-source replay evidence. | `partially integrate` | Keep original retention thresholds and use replay only under explicit policy and authority gates. |
| Human-approved consolidation application | NDNRA proves a bounded research operation, not production action authority. | `keep isolated` | Preserve as research evidence until an integration decision specifically approves the runtime boundary. |
| Exact checkpoint restoration | NDNRA proves complete-state research restoration under permits. | `keep isolated` | Do not connect it to production restore controls without a separate safety decision. |
| Bounded imagination | NDNRA has a closed deterministic in-memory non-authoritative subsystem. | `keep isolated` | It remains non-persistent, non-evidentiary, and outside production curiosity. |
| Persisting bounded imagination | Explicitly outside the accepted closure. | `reject` | Do not add it to any runtime or proof checkpoint. |
| Original unified stable checkpoint objective | Current NDNRA acceptance and long-horizon stores are separate proofs, not a unified runtime state. | `adapt around NDNRA` | Design a future runtime checkpoint separately; keep proof stores isolated and referential only. |
| Merging the two NDNRA proof stores | Would erase their accepted evidence and authority separation. | `reject` | Preserve both isolated stores unchanged. |
| Semantic checkpoint migration into a complete cognitive runtime | No accepted design exists yet. | `postpone` | Require schema, atomicity, rollback, and authority review before implementation. |

### 5.6 Growth, retention, safety, and authority

| Original component | NDNRA relationship | Classification | Decision |
| --- | --- | --- | --- |
| Original diagnostic ladder | NDNRA local saturation solves only part of capacity diagnosis. | `retain unchanged` | Continue checking task clarity, exploration, memory, skills, strategy, teaching, prediction, and progress first. |
| Learning-progress plateau evidence | Both architectures use sustained unresolved evidence. | `partially integrate` | Combine only as inspectable evidence, not as an automatic growth trigger. |
| Original policy or skill expert growth | NDNRA v0.1 grows bounded specialist-interaction structures instead. | `adapt around NDNRA` | Keep policy experts as the original product baseline and compare them with NDNRA specialists. |
| NDNRA local saturation and specialist-interaction growth | Completed only in deterministic bounded research tasks. | `keep isolated` | No live automatic specialist creation is approved. |
| Unrestricted generic neuron creation | Explicitly outside v0.1 and outside the MVP non-goals. | `postpone` | Revisit only after product evidence and resource controls mature. |
| Growth acceptance, retention, safety, character, value, and efficiency gates | NDNRA supplies useful local and persistence evidence but not all product gates. | `partially integrate` | Preserve every original gate and add NDNRA-specific checks. |
| Protected safety supervisor | NDNRA cannot edit permissions, safety, resources, or action masks. | `retain unchanged` | Keep the supervisor external and authoritative. |
| Production action controller | NDNRA currently produces observer or shadow suggestions only. | `retain unchanged` | Controller and production curiosity remain the only current action path. |
| NDNRA recommendation, scheduling, execution, promotion, or action authority | Explicitly absent in closure. | `reject` | No implicit authority may arise from integration convenience. |
| Autonomous background workers, queues, or timers | Explicitly excluded from accepted NDNRA stages. | `reject` | Any future automation requires a separate ADR and bounded gate. |

### 5.7 Evaluation, observatory, packaging, and product evidence

| Original component | NDNRA relationship | Classification | Decision |
| --- | --- | --- | --- |
| Random, reactive, fixed-small, and fixed-large baselines | NDNRA needs the same comparisons plus memory and growth substrate controls. | `adapt around NDNRA` | Keep all baselines and add matched-state NDNRA comparisons. |
| No-ambition, no-human, no-replay, and no-diagnostic ablations | NDNRA consumes these signals and should not erase their scientific value. | `retain unchanged` | Preserve original ablations. |
| Original prediction, curiosity, ambition, apprenticeship, skill, contribution, growth, truth, and safety metrics | NDNRA covers only a subset. | `retain unchanged` | Continue reporting the full product metric set. |
| NDNRA recall, dormancy, saturation, provenance, interference, restart, and authority metrics | Adds new inspectable evidence. | `partially integrate` | Add to experiment reports and Observatory panels. |
| Observatory | NDNRA has graph, provenance, proposal, permit, and receipt evidence that can be visualised. | `adapt around NDNRA` | Extend, do not replace, the original environment, mind, human, development, and evidence panels. |
| Competition demo | NDNRA evidence may improve the story but can also distract from the visible developmental loop. | `adapt around NDNRA` | Show only one clear integrated mechanism if later approved and evidenced. |
| Claim that the 82% marker is original-roadmap completion | Closure explicitly rejects that interpretation. | `reject` | Keep 82% as an expanded architecture marker only. |

## 6. Original Week 1-14 roadmap mapping

| Week | Original objective | NDNRA relationship | Classification | Decision and retained pass gate |
| --- | --- | --- | --- | --- |
| 1 | Freeze architecture and build deterministic Nursery | NDNRA does not replace the Nursery or its contracts. | `retain unchanged` | Preserve playable ball and cube tasks and deterministic episodes. |
| 2 | Build predictive seed core and checkpoint resume | NDNRA local consequences complement the GRU but do not replace it. | `adapt around NDNRA` | Keep decreasing prediction error and hardware-fit gates; any NDNRA observer must preserve the same action and training-error timelines. |
| 3 | Body discovery and self-model | NDNRA can consume controllability and external-change evidence. | `partially integrate` | Keep above-random primitive body-effect prediction and self-model ownership. |
| 4 | Curiosity and experiment selection | NDNRA uses curiosity modulation and has bounded imagination, but no action authority. | `adapt around NDNRA` | Curiosity still selects production experiments and must outperform random without looping on noise. |
| 5 | Teacher observation and ambition formation | Ambition relevance can modulate local NDNRA learning. | `partially integrate` | Ambition adoption and persistence remain original Week 5 gates. |
| 6 | Human apprenticeship and help-seeking | Human signals can modulate local traces; NDNRA does not replace support policy. | `partially integrate` | Preserve help recall, unnecessary-help avoidance, and caregiver evidence. |
| 7 | Episodic memory and belief formation | SQLite remains audit and evidence; future action recall may move to NDNRA. | `adapt around NDNRA` | Significant event retrieval and belief revision remain required. SQLite must not become the future NDNRA cognitive action path. |
| 8 | Learn and compile first reusable skill | NDNRA assemblies and chains are possible internal ingredients, not a complete skill compiler. | `partially integrate` | Still require `approach_and_push`, explicit preconditions, termination, random-start generalisation, target success, and demonstrated reuse instead of rediscovery. |
| 9 | Human contribution and reduced support | NDNRA has no substitute for verified contribution or support promotion. | `retain unchanged` | Complete a familiar human request and reduce support only after evidence. |
| 10 | Developmental blockage and diagnosis | NDNRA supplies local saturation and unresolved-pressure evidence. | `partially integrate` | Keep the full diagnostic ladder and block immediate growth. |
| 11 | Candidate specialist and growth gate | Original policy expert and NDNRA specialist interaction are different growth mechanisms. | `keep isolated` | Compare them under equal task, capacity, retention, and cost budgets before selecting an integration path. No live automatic growth. |
| 12 | Consolidation and retention | NDNRA has bounded retention, replay, restoration, and human-approved research evidence. | `partially integrate` | Keep ball, navigation, help-seeking, character, safety, rollback, and stable-checkpoint gates. Proof stores remain isolated. |
| 13 | Experiments and evidence | NDNRA adds new baselines and matched-control requirements. | `adapt around NDNRA` | Preserve multi-seed reproducibility, learning curves, confidence intervals where practical, and honest limitations. |
| 14 | Competition packaging | NDNRA can support the technical narrative only if integrated evidence exists. | `retain unchanged` | Another person must run the demo, the story must fit three minutes, and every claim must match evidence. |

## 7. Overlap, complementarity, conflicts, and duplication

### 7.1 Direct overlap

Both architectures address:

- grounded learning from transitions;
- consequence prediction and uncertainty;
- curiosity and ambition relevance;
- multi-step behaviour;
- memory and recall;
- structural growth after sustained failure;
- consolidation, retention, replay, and rollback;
- human correction and approval;
- inspectable evidence and provenance;
- bounded resources and safety.

Overlap does not prove interchangeability. The original plan defines whole-product responsibilities. NDNRA v0.1 proves narrower local mechanisms under strict research boundaries.

### 7.2 Complementarity

The original plan uniquely supplies:

- the Nursery product environment;
- the body-facing perception and action contracts;
- the recurrent predictive seed baseline;
- the self-model;
- explicit curiosity action selection;
- ambition lifecycle and developmental milestones;
- human requests, help-seeking, teaching, and support progression;
- explicit reusable skill records;
- verified human contribution;
- protected production safety and action authority;
- competition evidence, Observatory, and commercial packaging.

NDNRA uniquely supplies bounded evidence for:

- local delayed credit through eligibility traces;
- need-pulse-driven distributed recall;
- reversible dormancy and effort-based recall depth;
- normalized competing recruitment;
- sparse multi-effect local consequence memory;
- exact provenance, correlation control, and contextual mastery;
- graph-local representational saturation;
- bounded specialist-interaction growth;
- retention-gated consolidation and exact restoration research operations;
- deterministic bounded imagination with explicit non-authority;
- strong corruption, migration, restart, and complete-fallback proof patterns.

### 7.3 Architectural conflicts

| Conflict | Required resolution |
| --- | --- |
| SQLite retrieval as cognitive action recall versus NDNRA local activation | SQLite remains audit and baseline; later replace only the cognitive lookup role after comparative live evidence. |
| Explicit compiled skills versus distributed action assemblies | Preserve explicit skill contracts; allow NDNRA-backed implementation only after Week 8 equivalence is proved. |
| Policy-expert growth versus interaction-neuron growth | Keep both isolated until a parameter-, task-, and retention-matched comparison identifies where each belongs. |
| Unified runtime checkpoint expectation versus isolated proof stores | Design a separate runtime checkpoint; never merge proof stores merely to simplify loading. |
| Fixed scheduled consolidation versus evidence-aware human-governed proposals | Preserve retention cadence for evaluation while requiring explicit evidence and authority for mutation. |
| Post-MVP pruning versus NDNRA no-deletion invariant | Use reversible dormancy for memory-bearing structures; prune only non-memory infrastructure unless a future ADR changes the invariant. |
| Multiple explicit drives versus one active NDNRA pulse | Keep multi-drive arbitration outside NDNRA and pass only the selected bounded pulse. |
| Semantic concept memory versus exact grounded contexts | Preserve symbolic beliefs and postpone NDNRA semantic abstraction. |
| NDNRA candidate generation versus production curiosity selection | Production curiosity remains authoritative; NDNRA stays shadow-only until a separate decision explicitly changes authority. |

### 7.4 Duplicated work to avoid

Do not build two independent authoritative versions of:

- production consequence selection;
- action ranking or route selection;
- growth approval;
- skill identity and success accounting;
- human permission interpretation;
- checkpoint restoration authority;
- contradiction truth status;
- production replay scheduling.

The acceptable pattern is one authoritative owner plus one bounded evidence or substrate role with explicit provenance.

## 8. Missing capabilities after NDNRA v0.1 closure

NDNRA v0.1 does not complete these original-plan capabilities:

- a Nursery-general reusable `approach_and_push` skill;
- explicit skill preconditions, termination, generalisation, and reuse metrics;
- verified human contribution and honest task completion reporting;
- full support-level progression and independence evidence;
- semantic concept abstraction above exact grounded contexts;
- learned context-similarity weights;
- multiple simultaneous need coordination;
- unrestricted or general policy-network growth;
- a unified production cognitive runtime checkpoint;
- production-ready integrated recall;
- production action selection or control;
- competition dashboard and end-to-end demonstration completion.

## 9. Safe future integration seams

These seams are acceptable subjects for a later design batch. They are not approved implementations in this audit.

1. **Typed observation seam** — copy validated `ObservationPacket`, executed primitive action, real outcome, and bounded developmental signals into NDNRA after production has fixed the action.
2. **Shadow recall seam** — compare NDNRA-recruited memories and candidate chains with the production baseline without changing execution.
3. **Provenance seam** — allow beliefs, skills, growth proposals, and consolidation records to reference immutable NDNRA event and assembly identities.
4. **Skill-substrate seam** — permit a future explicit `SkillRecord` to reference a validated NDNRA assembly or chain while retaining preconditions, termination, success, and support fields.
5. **Diagnostic seam** — expose graph-local saturation, interference, and recall-cost evidence to the original diagnostic ladder without granting growth authority.
6. **Consolidation-evidence seam** — allow NDNRA mastery and retention evidence to create review candidates while the original safety and human-approval layers retain mutation authority.
7. **Persistence sidecar seam** — reconstruct NDNRA graph state from a versioned atomic sidecar or bounded runtime checkpoint member while keeping proof stores separate and non-cognitive.
8. **Observatory seam** — display local assemblies, dormancy, recall depth, growth pressure, provenance, permits, receipts, and authority flags read-only.

## 10. Recommended integration decision

Accept the following decision:

1. The original master plan remains the governing SeedMind product and MVP roadmap.
2. NDNRA v0.1 is retained as a closed bounded research architecture and candidate cognitive substrate.
3. No full replacement of the predictive core, Nursery, curiosity policy, ambition engine, apprenticeship manager, skill compiler, action controller, safety supervisor, or product roadmap is justified.
4. The strongest future candidates for selective integration are local cognitive recall, local consequence memory, recall effort, local saturation evidence, retention evidence, and provenance.
5. The Week 8 reusable-skill objective remains mandatory and unsatisfied by NDNRA alone.
6. SQLite remains valid for audit, scientific evidence, beliefs, and comparison, but unrestricted SQLite lookup must not become the future NDNRA action-memory mechanism.
7. Production curiosity remains the sole production action authority.
8. NDNRA proof stores remain isolated, and bounded imagination remains non-persistent.
9. Integration implementation requires a separate explicit approval and a new bounded architecture decision.
10. The expanded developmental architecture marker remains 82%.

## 11. Decision criteria for any later integration approval

A later integration proposal must satisfy all criteria below before production influence is considered.

### 11.1 Scope and ownership

- Name exactly which original responsibility is retained, adapted, partially integrated, or replaced.
- Identify one authoritative owner for action selection, permission, growth, replay, restoration, and truth status.
- Preserve all closed NDNRA v0.1 boundaries unless a new ADR explicitly changes one.

### 11.2 Behavioural invariance

- A matched baseline and NDNRA-observed run must use identical scenario, model, trainer, curiosity, and random seeds.
- Shadow integration must preserve production actions, predictive-training errors, human-accounting state, safety state, and unrelated learning.
- Any difference must be expected, bounded, and approved by the relevant authority decision.

### 11.3 Scientific advantage

- NDNRA must outperform or complement the baseline on a named metric such as recall success, recall cost, retention, interference, sample efficiency, provenance, or capacity efficiency.
- Improvement must hold across multiple seeds where practical and include failure cases and resource cost.
- Synthetic heat-world evidence alone is insufficient for Nursery authority.

### 11.4 Week 8 skill equivalence

Before NDNRA may replace any skill-memory or skill-controller responsibility, it must demonstrate:

- a reusable Nursery skill identity;
- explicit preconditions;
- explicit termination;
- varied-start generalisation;
- target success threshold;
- reuse without rediscovery;
- known failure boundaries;
- retention after later learning;
- inspectable source provenance.

### 11.5 Persistence and restart safety

- Runtime persistence must have a named schema and version.
- Save must be atomic and load must be all-or-nothing.
- Missing, corrupt, stale, incompatible, or relationally invalid state must produce explicit safe fallback.
- Restart must preserve the same first eligible recall and subsequent deterministic behaviour.
- The two NDNRA proof stores must remain separate and must not be treated as runtime cognition.
- Bounded imagination must remain absent from persisted state.

### 11.6 Retention, rollback, and growth

- Old Nursery skills must remain within original degradation limits.
- Failed retention or safety gates must block or roll back the change.
- Growth must remain bounded, duplicate-protected, resource-capped, and causally justified.
- No specialist may gain authority merely because it was created or improved a synthetic score.

### 11.7 Human and safety authority

- The protected safety supervisor remains external and authoritative.
- Human correction, stop, permission, and approval remain protected typed inputs.
- No missing, stale, rejected, deferred, or corrupt review state may become implicit permission.
- No autonomous worker, queue, timer, scheduler, executor, or production action influence is introduced without explicit approval.

### 11.8 Compute and product fit

- The integrated path must fit the current hardware and deterministic evaluation budget.
- Observatory output must explain why a memory, skill, growth proposal, or consolidation change exists.
- Competition claims must remain understandable, reproducible, and narrower than the evidence.

## 12. Batch closure

This documentation-first comparison boundary is accepted.

The accepted result is a recommendation for selective, staged, evidence-gated partial integration while retaining the original plan as the product spine.

No integration implementation is approved by this audit. The next repository change affecting runtime integration requires Arash's separate explicit approval.
