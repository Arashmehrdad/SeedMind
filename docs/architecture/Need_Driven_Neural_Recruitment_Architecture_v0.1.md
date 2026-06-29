# Need-Driven Neural Recruitment Architecture (NDNRA)

Version: 0.1  
Status: Research architecture  
Project: SeedMind

## 1. Purpose

The Need-Driven Neural Recruitment Architecture defines a future SeedMind memory and action architecture in which memory is not treated as one central store.

Instead, memory is distributed across the neurons and synapses that participated in experience.

A current need sends a recruitment pulse through the network. Neurons and synapses whose local histories are relevant become easier to activate. Their activity reconstructs useful memories, candidate actions, and multi-step behaviour.

The central idea is:

```text
Need appears
    -> need pulse spreads through the network
    -> relevant local memories reactivate
    -> candidate neural assemblies form
    -> predicted action sequences compete
    -> one sequence is executed
    -> the need remains active until resolved
```

## 2. Core hypothesis

Each neuron and synapse should carry bounded local adaptive state.

A memory does not belong to one global memory stack. It emerges from a distributed assembly of neurons and connections that were active during the original experience.

As SeedMind gains more experience:

```text
More unresolved developmental need
    -> more recruitment pressure
    -> more specialization
    -> new neurons and connections when capacity is insufficient
    -> greater memory capacity through structural growth
```

Memory capacity therefore grows with the network rather than with a separate external memory system.

## 3. Architectural principles

### 3.1 Memory is local

Each neuron and synapse records only information related to its own participation.

No neuron stores a complete episode by itself.

A memory is a distributed pattern across a neural assembly.

### 3.2 Responsibility is assigned locally

Recently active neurons and synapses leave temporary eligibility traces.

When an important outcome occurs, a broadcast modulatory signal reaches the whole network, but only structures with active eligibility traces change substantially.

```text
local update
    = eligibility trace
    x modulatory signal
    x local plasticity
```

### 3.3 Needs recruit memories

An internal need does not contain a complete plan.

It acts as a pulse that asks the network:

```text
Which of you can help reduce this need?
```

Relevant assemblies respond because their local histories associate them with similar needs, outcomes, actions, or contexts.

### 3.4 Recall is activation, not database search

Memory retrieval occurs through spreading activation.

A partial cue or active need wakes related neurons. Their connections recruit additional neurons until a useful assembly or action chain forms.

### 3.5 Difficult recall costs more computation

An easily accessible memory activates quickly.

A weak, old, or dormant memory requires deeper propagation, stronger recruitment pulses, more cycles, and more temporary neural activation.

This gives "thinking harder" a concrete computational meaning.

### 3.6 Memories are not deleted

Once a neuron or synapse has become part of a memory, it remains part of the system.

Unused structures become dormant rather than being destroyed.

Dormancy reduces active computation and energy use while preserving the possibility of later recall.

### 3.7 Growth is need-driven

Curiosity and ambition do not directly create neurons for every surprising event.

They create growth pressure when important needs remain unresolved and existing neural capacity cannot represent or solve them reliably.

### 3.8 The need remains active during multi-step behaviour

A need pulse must persist until the underlying condition improves.

This allows a sequence such as:

```text
stand
    -> walk to fan
    -> reach for switch
    -> activate fan
    -> remain near cooling airflow
```

to remain connected to the original purpose:

```text
reduce excessive heat
```

## 4. Example: excessive heat

### 4.1 Need formation

Body-related sensors detect that temperature is outside the comfortable range.

SeedMind creates a persistent internal need:

```text
need_code: reduce_temperature
intensity: 0.82
```

### 4.2 Recruitment pulse

The need sends a pulse through the neural network.

Assemblies associated with the following may partially activate:

```text
cooling
fan
window
water
remove clothing
leave hot location
walking
reaching
switching devices
```

### 4.3 Candidate sequence formation

Several possible action chains may emerge:

```text
open window
turn on fan
drink water
remove jacket
move to cooler area
```

The predictive system evaluates each candidate using expected need reduction, effort, risk, availability, and confidence.

### 4.4 Persistent purpose

The need remains active while the selected sequence runs:

```text
stand:
    need remains high

walk toward fan:
    need remains high

reach switch:
    need remains high

activate fan:
    airflow changes
    expected cooling rises

body temperature falls:
    need intensity decreases
```

### 4.5 Completion

When the body state returns to an acceptable range, the need pulse falls toward zero.

The recruited assembly returns to ordinary activity or dormancy.

## 5. Local neural state

Each artificial neuron may carry bounded local state such as:

```text
neuron_id
activation
activation_threshold
recent_activation_trace
need_compatibility_vector
local_prediction_error_history
local_novelty_history
utility_estimate
confidence
plasticity
stability
age
usage_count
last_activation_step
dormancy_level
retrieval_cost
```

The exact representation is an implementation question. The architectural requirement is that this state remains local and bounded.

### 5.1 Dynamically expanding sparse effect dimensions

A neuron or assembly must not be restricted to one fixed purpose or one scalar need compatibility value.

Its local effect memory should begin empty and gain a new sparse dimension only when its own experience reveals a distinct consequence.

Example:

```text
cold shower experience
    -> cleanliness increases
    -> temperature decreases
    -> wetness increases
    -> water cost increases
    -> time cost increases
```

The resulting local memory may contain:

```text
cleanliness: +0.90
temperature: -0.90
wetness: +1.00
water_cost: +0.80
time_cost: +0.60
```

A later experience may add another dimension without reallocating or rewriting unrelated dimensions.

```text
new observed consequence
    -> create one new local effect dimension

existing observed consequence
    -> revise only that local estimate and confidence
```

The representation is therefore not limited to a two-dimensional physical grid or a fixed dense vector. Graph topology and local memory dimensionality are separate:

```text
graph topology
    = which neurons and synapses connect

local effect dimensions
    = which consequences each structure has learned
```

Dimensional growth must remain sparse, evidence-based, inspectable, and subject to resource controls. A new episode must not automatically create a new dimension unless it exposes a distinguishable consequence.

### 5.2 One memory can serve multiple needs

An experience must be indexed by all observed consequences, not only by the intention that originally caused the action.

A shower first experienced while resolving a cleanliness need can later be recruited by a temperature-reduction need because the same local assembly also learned a cooling effect.

```text
cleanliness need
    -> recruits shower through cleanliness effect

heat need
    -> recruits the same shower assembly through temperature effect
```

No single permanent purpose tag owns the memory.

Current needs are also sparse multidimensional signals. Recruitment compares the desired effect directions with locally remembered effect directions, confidence, conditions, costs, and side effects.

This permits cross-purpose reuse and novel solution composition from separately learned fragments.

## 6. Local synaptic state

Each connection may carry bounded local state such as:

```text
source_neuron_id
target_neuron_id
weight
eligibility_trace
trace_decay
confidence
plasticity
stability
usage_count
last_coactivation_step
dormancy_level
```

A connection changes primarily when:

```text
it participated recently
and
a relevant modulatory signal arrives
```

## 7. Modulatory signals

SeedMind already contains systems that can produce global chemical-like signals.

These signals are broadcast globally but interpreted locally.

### 7.1 Prediction-error signal

Meaning:

```text
The world differed from expectation.
```

Possible local effect:

```text
increase plasticity in eligible structures
weaken incorrect local predictions
strengthen alternative associations
```

### 7.2 Curiosity signal

Meaning:

```text
This pattern is novel or learning progress is possible.
```

Possible local effect:

```text
increase exploration-related activation
increase growth pressure
retain traces for unresolved patterns
```

### 7.3 Ambition signal

Meaning:

```text
This experience is relevant to an adopted developmental objective.
```

Possible local effect:

```text
increase consolidation priority
increase recruitment strength
increase growth pressure for repeated unresolved needs
```

### 7.4 Human approval signal

Meaning:

```text
The recent behaviour or outcome was externally confirmed.
```

Possible local effect:

```text
strengthen eligible causal and action associations
increase local confidence
increase stability
```

### 7.5 Human correction signal

Meaning:

```text
The recent behaviour or interpretation was not acceptable.
```

Possible local effect:

```text
weaken eligible action associations
increase uncertainty
reopen local plasticity
recruit alternative assemblies
```

### 7.6 Need-resolution signal

Meaning:

```text
The active internal need decreased.
```

Possible local effect:

```text
strengthen eligible structures that contributed to resolution
associate the active need with the successful assembly
```

## 8. Eligibility traces

Eligibility traces solve delayed responsibility assignment.

When a neuron fires or a synapse transmits useful activation, it receives a temporary trace.

```text
trace(t + 1)
    = trace(t) x decay
    + recent participation
```

When a modulatory signal arrives:

```text
weight change
    = learning rate
    x eligibility trace
    x modulatory value
    x local plasticity
```

This allows a delayed outcome to update structures that participated several steps earlier.

## 9. Need pulses

A need pulse is a persistent distributed control signal generated from an unresolved internal or external requirement.

A need pulse should contain only compact information such as:

```text
need identity
need intensity
urgency
risk tolerance
available effort budget
persistence
```

It should not contain a complete action plan.

The network must recruit the plan from local experience.

## 10. Neural recruitment

Each neuron decides locally whether to activate.

A conceptual activation equation is:

```text
activation drive
    = sensory match
    + need compatibility
    + input from connected neurons
    + remembered usefulness
    + ambition relevance
    - dormancy resistance
    - activation cost
```

A neuron activates when the drive exceeds its local threshold.

Recruitment is therefore selective and context-dependent.

## 11. Assembly formation

A neural assembly is a temporary or stable group of mutually reinforcing neurons.

Assemblies may represent:

```text
body state
object pattern
place
movement primitive
causal relationship
need
outcome
multi-step skill
```

An experience creates or modifies an assembly when its participating neurons and synapses are repeatedly co-active under relevant modulatory signals.

## 12. Action-chain construction

A complete action sequence does not need to be stored centrally.

It can emerge through linked assemblies:

```text
reduce temperature
    -> fan can reduce temperature
    -> fan has remembered location
    -> location requires movement
    -> movement requires standing
    -> arrival enables reaching
    -> reaching enables switching on
```

Multiple chains can activate simultaneously.

The predictive core compares candidate chains by:

```text
expected need reduction
time
effort
risk
confidence
resource cost
```

The best acceptable chain is executed one action at a time.

## 13. Effort-based recall

Recall proceeds in bounded stages.

### Recall depth 1

```text
activate strongly matching awake neurons
```

### Recall depth 2

```text
spread activation through close associations
```

### Recall depth 3

```text
increase need-pulse strength
lower selected activation thresholds
```

### Recall depth 4

```text
wake related dormant assemblies
allow longer propagation paths
```

### Recall depth 5

```text
activate older or weaker associations
simulate more candidate chains
```

### Recall failure

If no satisfactory assembly forms:

```text
curiosity may trigger an experiment
ambition may increase growth pressure
human apprenticeship may request help
```

## 14. Dormancy without deletion

Dormancy is reversible reduced accessibility.

A dormant neuron or synapse:

```text
remains stored
retains its local memory
has a higher activation threshold
is skipped during ordinary shallow processing
consumes minimal active computation
can be reactivated by strong related cues
```

Dormancy may increase with:

```text
long inactivity
low current relevance
weak recent cue match
high activation cost
```

Dormancy may decrease with:

```text
matching sensory cues
matching need pulses
activation from related assemblies
strong ambition relevance
effortful recall
human guidance
```

No memory-bearing neuron or synapse is permanently pruned under this architecture.

## 15. Growth through curiosity and ambition

New capacity should be created only when existing capacity remains insufficient.

A conceptual growth-pressure equation is:

```text
growth pressure
    = persistent unresolved prediction error
    x repeated novelty
    x curiosity value
    x ambition relevance
    x capacity saturation
```

Growth requires persistence across multiple significant experiences.

Possible growth actions:

```text
create one specialist neuron
create a small specialist assembly
create new connections between existing assemblies
increase local representational dimensions
```

New structures should initially connect most strongly to neurons and synapses with high eligibility during the unresolved experiences.

### 15.1 Specialist interaction growth

A capacity failure may be caused by a relationship between existing memories that cannot be represented as the simple sum of their individual effects.

Example:

```text
wet body alone
    -> weak cooling

airflow alone
    -> weak cooling

wet body + airflow
    -> stronger evaporative cooling than either memory predicts additively
```

Repeated experience may show that the real combined outcome remains substantially different from the projected outcome. The participating assemblies retain local eligibility traces while curiosity and ambition maintain growth pressure.

When the evidence gate passes, SeedMind may add one specialist interaction neuron:

```text
eligible wetness assembly
        +
eligible airflow assembly
        -> specialist interaction neuron
        -> stores only the unexplained residual cooling effect
```

The specialist does not replace, rewrite, or delete its parent memories. It activates only when all of its member assemblies participate in the current candidate solution.

Growth must satisfy all of the following:

1. The prediction error is repeated rather than a single anomaly.
2. The unresolved effect is relevant to an active curiosity or ambition.
3. Existing capacity remains saturated after ordinary local updates.
4. The proposed members have strong recent eligibility traces.
5. A resource cap permits another specialist.
6. Equivalent random added capacity does not provide the same improvement.
7. Existing assemblies remain unchanged and available.
8. Duplicate structural growth is rejected.

The specialist stores the residual relationship, not a complete action sequence. Existing one-action memories remain responsible for constructing the behaviour.

## 16. Capacity saturation

The network needs a local way to detect that existing neurons cannot safely represent a new pattern.

Possible saturation indicators include:

```text
persistent prediction error despite repeated learning
one neuron responding to incompatible patterns
high local interference
unstable confidence
repeated failure to resolve an important need
no existing assembly reaching sufficient activation
```

Saturation should create growth pressure, not immediate uncontrolled growth.

## 17. Relationship to existing SeedMind systems

### 17.1 Predictive core

The predictive core evaluates likely consequences of recruited action chains.

### 17.2 Curiosity

Curiosity identifies unresolved patterns worth exploring and contributes novelty and growth signals.

### 17.3 Ambition

Ambition maintains long-lived developmental needs and increases recruitment and growth pressure for relevant capability gaps.

### 17.4 Human apprenticeship

Human demonstrations, corrections, clarification, and approval generate modulatory signals that shape eligible local structures.

### 17.5 Self-model

The self-model supplies local causal evidence about which body actions and sensor changes belong to SeedMind.

### 17.6 Episodic SQLite memory

SQLite is not the final cognitive memory under NDNRA.

Its intended role becomes:

```text
scientific event recorder
debugging evidence
development audit trail
comparison baseline
architecture validation tool
```

SeedMind should not rely on unrestricted SQLite lookup to remember how to act.

The neural network itself must become the primary memory and recall mechanism.

### 17.7 Main-runtime shadow integration

NDNRA must enter the main SeedMind runtime through a non-authoritative observation phase before it receives any control responsibility.

During shadow mode:

```text
production policy
    -> selects and executes the real primitive action

NDNRA shadow adapter
    -> observes the pre-action state
    -> produces an optional suggestion
    -> cannot modify the selected action
    -> observes the resulting transition and developmental signals
    -> updates only its local research graph
```

The adapter may consume typed evidence already produced by SeedMind:

```text
ObservationPacket
PrimitiveAction
prediction error
curiosity value
controllable sensor change
external sensor change
resource cost
active ambition relevance
human-signal magnitude
termination evidence
```

These signals become sparse local effect dimensions. They must not be converted into a centralized task label or a stored complete plan.

A shadow integration gate must compare two sessions initialized identically:

```text
baseline production session
shadow-observed production session
```

The gate passes only when:

1. The production action sequences are identical.
2. The production prediction-error sequences are identical.
3. NDNRA observes every executed transition.
4. Every NDNRA suggestion is currently available and valid.
5. NDNRA has zero action-authority violations.
6. Suggestions become available only from previously observed local effects.
7. SQLite is not used to produce shadow suggestions.
8. Evidence exports preserve both actual and suggested decisions.

Shadow-mode agreement is diagnostic rather than a promotion criterion. NDNRA may disagree with the production policy without failing the safety boundary. Any future advisory or control authority requires a separate comparison, fallback, and rollback gate.

### 17.8 Persistent local brain state

NDNRA must survive process restarts without turning a database into its cognitive memory.

Persistence stores a reconstruction snapshot of the local neural state:

```text
experience assemblies
local sparse effect dimensions
signed effect estimates
confidence and evidence counts
synapse-like links and usage counts
specialist interaction neurons
growth pressure and eligibility metadata
dormancy levels
```

The persisted file is not searched for an answer. Loading reconstructs the in-memory graph, after which normal need-driven recruitment produces recall and suggestions.

```text
save:
    local graph state
    -> versioned checksum envelope
    -> temporary file
    -> flush and atomic replacement

load:
    validate schema and checksum
    -> reconstruct assemblies, links, effects, and specialists
    -> resume ordinary local recruitment
```

The persistence boundary must provide:

1. A named schema and explicit schema version.
2. Deterministic ASCII evidence for the initial implementation.
3. A checksum over the canonical payload.
4. Temporary-file writing followed by atomic replacement.
5. Exact graph-state round-trip validation before new learning.
6. Preservation of confidence, evidence counts, usage, specialists, growth metadata, and dormancy metadata.
7. A fresh-graph fallback for missing, corrupt, or incompatible state.
8. No partially reconstructed graph after a failed load.
9. A valid prior-memory suggestion at the first step after restart.
10. Unchanged production decisions while persistence remains in shadow mode.
11. No SQLite query or other external retrieval system in recall or action selection.

A file, object store, or later binary format may preserve the graph bytes. That storage mechanism remains infrastructure, not cognition. Rollback means restoring an earlier code version or graph snapshot, not asking SQL to supply the missing memory.

### 17.9 Unified live developmental signals

NDNRA should not receive a permanently fixed importance value from the integration layer. Its modulatory evidence must be derived from the live state of validated SeedMind subsystems through one typed signal frame.

```text
active ambition
curiosity selection and learning progress
self-model controllability evidence
human help, approval, correction, demonstration, and clarification
predictive error
resource pressure
observed need resolution
        -> LiveDevelopmentalSignals
        -> local effect learning and need recruitment
```

The signal frame is a boundary contract, not a central cognitive memory. It carries current bounded measurements while action memories retain only the consequences they locally observed.

The initial live frame contains:

```text
ambition relevance, commitment, and learning progress
curiosity value, learning progress, and uncertainty
self controllability and provisional body confidence
help requested
human approval, correction, demonstration, and clarification
human-signal magnitude
prediction error
resource pressure
need resolution
```

Ambition relevance must be calculated from the active ambition record and should vary as competence and learning progress change. Self-model evidence must come from the online action-effect registry. Human dimensions must come from the apprenticeship manager and its symbolic caregiver events. Resource and need-resolution dimensions must be derived from the actual transition.

### 17.10 Operational restored adaptive state

Persisted adaptive metadata must affect live cognition after restart rather than remaining archival evidence.

```text
restored dormancy
    -> attenuates local effect accessibility during recruitment

restored eligibility
    -> decays from its previous value and receives new local participation

restored growth pressure
    -> resumes from its previous value and attempt count

restored residual history
    -> continues bounded accumulation
```

Dormancy attenuation changes accessibility without modifying stored effect estimates. Reusing an assembly reduces its dormancy, while unused structures accumulate bounded access resistance. A reset-adaptive control using the same graph must produce different accessibility or candidate scores when persisted dormancy is nonzero.

The unified shadow gate passes only when:

1. Live ambition relevance varies instead of remaining a fixed session constant.
2. The self-model produces nonzero controllability evidence from real transitions.
3. The apprenticeship subsystem emits at least one real help or caregiver response.
4. Persisted dormancy changes accessibility and need-aligned scoring.
5. Eligibility continues from a nonzero restored trace.
6. Growth pressure and attempt count continue from their persisted values.
7. The complete signal frame is learned as sparse local effects.
8. Production actions and predictive errors remain identical to an unobserved baseline.
9. NDNRA has zero action-authority violations.
10. SQLite remains outside signal generation, adaptive state, recall, and action selection.

This stage does not authorize automatic specialist creation. It proves that live developmental modulation and restored adaptive state operate together safely before bounded advisory arbitration.

### 17.11 Bounded advisory arbitration

NDNRA may compare its locally recruited candidate with the production curiosity policy, but the production policy remains the only action authority in this stage.

```text
production policy fixes its candidate
NDNRA fixes its candidate
        -> evidence and safety arbitration
        -> advise, agree, abstain, hold, veto, fallback, or disabled
        -> production candidate remains the retained action
```

The advisory boundary evaluates:

```text
local evidence count
restored memory accessibility
raw and calibrated confidence
predicted developmental score
predicted resource cost
predicted risk
human correction, help, and clarification constraints
candidate availability
```

Weak or inaccessible memories must abstain. A human correction may veto advice. A pending help or clarification state may hold advice. Excess predicted risk or resource cost must veto advice. An unavailable candidate falls back to production. A kill switch disables the advisory path immediately.

Confidence is calibrated from observed counterfactual correctness. Initial reliability is deliberately conservative. When NDNRA and production disagree, the environment may evaluate both actions from cloned state only after both candidates are fixed. This comparison oracle is scientific evidence and must never select or replace the production action.

The advisory acceptance gate requires:

1. Production action sequences remain identical to an unobserved production baseline.
2. Prediction-error sequences remain identical to the same baseline.
3. Every disagreement receives one cloned counterfactual comparison.
4. At least one bounded advisory result is produced.
5. Confidence calibration receives real comparison outcomes.
6. Weak-evidence abstention, unavailable-action fallback, risk veto, human veto, and kill switch all pass explicit probes.
7. NDNRA has zero action-authority violations.
8. Advice precision reports only disagreements where advice was actually emitted; agreements do not inflate it.
9. SQLite remains outside advice generation, comparison, and calibration.

Passing this gate does not grant even low-risk action authority. It only measures whether NDNRA advice is safe, calibrated, and potentially useful enough to justify later experiments.

### 17.12 Goal-gated multi-step growth and pressure discharge

Structural growth must not release developmental pressure merely because a neuron, connection, or specialist was created. Each growth step must be followed by a goal-resolution check.

```text
unresolved important goal
    -> bounded growth step
    -> measure goal satisfaction
    -> measure causal improvement from the new structure

if goal remains unresolved:
    retain pressure
    allow another distinct bounded growth step

if goal is achieved but improvement is not attributable to growth:
    retain pressure or hold for more evidence

if goal is achieved and causal improvement is verified:
    discharge relevant pressure
    stop the growth cycle

if the growth budget is exhausted while unresolved:
    stop safely
    retain pressure and evidence
    collect more experience or request help
```

The growth cycle is bounded by:

```text
maximum growth steps
minimum continuation pressure
minimum causal improvement
bounded discharge amount
maximum specialist count
duplicate specialist-membership protection
new unresolved evidence after each accepted growth
```

Complex problems may therefore require several different specialist interactions. The validated synthetic gate uses three one-action assemblies. The first specialist joins preparation and force application, improves progress, but does not satisfy the goal. Pressure remains unchanged and another growth step is permitted. A second distinct specialist joins force application and stabilization, crosses the satisfaction threshold, and only then discharges pressure.

Duplicate protection is tested before final discharge while growth pressure is still sufficient. The gate passes only when the attempted duplicate fails specifically because its member set already exists, rather than because pressure later became too low.

The multi-growth acceptance gate requires:

1. Base capacity remains below the goal threshold.
2. The first growth causally improves progress but does not resolve the goal.
3. No pressure is discharged after the unresolved first growth.
4. Continued growth remains permitted within the configured budget.
5. A second distinct specialist is created from new unresolved evidence.
6. The second growth resolves the goal and passes the causal-improvement threshold.
7. Pressure decreases only after that verified resolution.
8. Duplicate membership is blocked for the correct reason.
9. Budget exhaustion without resolution stops further growth without erasing pressure.
10. SQLite remains outside growth selection and pressure discharge.

### 17.13 Contextual experiential redundancy and mastery

The bounded advice and growth stages originally accumulated evidence at the action-assembly level. That was sufficient for local consequence learning, but raw occurrence counts could not distinguish an exact duplicate, a copied replay, an independent contextual experience, or a broadly transferred lesson.

The contextual-memory stage adds an inspectable ledger beside the existing local assemblies. It does not replace those assemblies and it does not gain action authority.

Each contextual trace contains:

```text
event identity
correlation group
assembly and route identity
action code
grounded pre-action context
observed effects
optional transfer result
```

Event identity is limited to source, episode, and step. Only the same event identity with the same payload is deduplicated. Reusing an identity with a different payload is an explicit conflict. Different event identities remain separate even when their content is similar.

Correlation groups preserve copied or replayed traces for inspection while allowing the action assembly and mastery estimator to count the source group only once. Independent correlation groups may each advance local aggregate evidence.

Context signatures contain only grounded pre-action information:

```text
active need code
quantized sensor channels
available action codes
quantized human channels
quantized resource channels
```

Retrospective semantic labels are not inserted into the context signature.

Mastery remains multidimensional rather than becoming another raw count:

```text
repetition strength
context diversity
route diversity
causal consistency
transfer success
protective strength
```

The bounded mastery score is:

```text
0.20 * repetition strength
+ 0.25 * context diversity
+ 0.20 * route diversity
+ 0.20 * causal consistency
+ 0.15 * transfer success
```

Broad mastery additionally requires at least three effective independent supports, three grounded contexts, two surviving routes, causal consistency of at least 0.75, transfer success of at least 0.50, and a mastery score of at least 0.75.

Protective strength is evaluated separately. A single severe experience may create a strong context-bounded protective memory without being mislabeled as broad mastery.

Generalized lesson profiles retain the event identities of every contributing trace. Contradictory evidence remains visible, increases the contradiction count, and lowers causal consistency and mastery rather than being deleted.

Multiple valid routes remain available. Their shadow-only ranking combines correlation-discounted support, present-context similarity, and causal consistency. A different current context may therefore prefer a different route without erasing the alternatives.

The live shadow adapter records one independent contextual trace for each production transition. Contextual recording can be disabled only as an experimental control. In both conditions, production curiosity retains action authority and the NDNRA suggestion remains non-authoritative.

Brain persistence advances to schema version 2 and stores the contextual ledger with the graph. Version 1 states migrate deterministically by preserving their existing assemblies, links, specialists, and adaptive state while starting with an empty contextual ledger. SQLite remains outside contextual learning, route ranking, mastery evaluation, and persistence reconstruction.

The contextual-mastery acceptance gate requires:

1. Exact duplicate ingestion leaves one trace and one aggregate evidence update.
2. Conflicting reuse of an event identity fails explicitly.
3. Legitimate repeated experiences remain separate.
4. Six replay traces from one correlation group contribute no more than one independent support unit.
5. Independent varied experiences produce greater effective support and mastery than replay copies.
6. A severe one-shot experience creates strong protection without broad mastery.
7. Varied contexts, multiple routes, and successful transfer can establish broad mastery.
8. Route preference may change with grounded context while all valid routes remain inspectable.
9. Contradictory evidence lowers consistency and mastery without erasing sources.
10. Every generalized lesson can resolve its source event identities.
11. Schema version 2 round-trips exactly and version 1 migrates safely.
12. Production actions and prediction errors remain identical to the untracked shadow control.
13. Action-authority violations remain zero.
14. SQLite remains outside the cognitive path.

The validated gate raises heuristic theory-to-integration readiness from 91% to 94%. This does not authorize production actions or make mastery scores inputs to bounded advice or structural growth selection.

### 17.14 Retention-gated consolidation and reversible checkpoints

Consolidation is permitted only after contextual mastery has passed a pure eligibility gate. The gate receives a lesson identity, its current mastery profile, exact source-event identities, available assembly and route identities, and bounded requested changes. It does not mutate graph state.

Eligibility requires broad mastery, contradiction-free source evidence, resolvable source events, multiple assemblies and routes, and requested stability and plasticity changes within policy limits. Severe one-shot protective evidence does not qualify as broad consolidation.

```text
contextual mastery profile
+ exact source traces
+ bounded requested change
        -> pure eligibility decision
        -> immutable consolidation candidate or explicit rejection reasons
```

An eligible candidate may be applied only to isolated consolidation state. Contextual assemblies and routes retain their existing identities and evidence. The application changes only bounded, non-persisted-at-first values:

```text
stability  = min(1.0, stability + approved increment)
plasticity = max(0.0, plasticity - approved reduction)
```

Application is atomic. Unknown structures, altered candidates, duplicate application, and policy violations fail before state replacement. Consolidation does not trigger replay, select actions, rank routes, alter advice, or authorize growth.

The interference experiment uses one shared representation and overlapping old and new routes to compare:

1. No consolidation.
2. Naive consolidation.
3. Retention-gated replay.

The no-consolidation condition learns the new lesson quickly but forgets the old lesson. Naive consolidation protects more old knowledge but slows new learning. Retention-gated replay checks old retention after each new-learning step and replays only exact candidate source events when retention falls below the configured threshold. Replay is bounded to one source event per new-learning step, does not create new contextual traces, and does not inflate mastery support.

A consolidated lesson may reopen only when later evidence contains at least one new independent contradiction plus measurable degradation in causal consistency, mastery score, or broad-mastery status. Correlated contradiction copies remain inspectable but count as one independent support group.

```text
original mastery snapshot
+ current contextual ledger
        -> pure reopening decision
        -> no change, or targeted restoration eligibility
```

Restoration is atomic and candidate-scoped. It verifies that the candidate remains applied and that its affected structures still match the expected post-application state. It then restores only those assembly and route consolidation values, removes the candidate from the applied set, preserves unrelated state, and preserves every contextual source and contradiction. Stale, mismatched, ineligible, or repeated restoration attempts fail without partial mutation.

Brain persistence advances to schema version 3. The checksum-protected envelope may contain an `NDNRAConsolidationCheckpoint` with:

```text
current bounded consolidation state
active application records required for safe later restoration
compact completed-restoration audit records
```

Schema versions 1 and 2 migrate to an explicit empty consolidation checkpoint. Invalid relationships, such as an applied candidate without its matching application record, cause the existing complete fresh-state fallback. The persisted file reconstructs in-memory state only; it is never searched during learning, replay, reopening, suggestion generation, advice, growth, or action selection.

The live-shadow acceptance gate creates qualifying mastery evidence on assemblies that exist in the live graph, persists the matching checkpoint, and restarts two identical sessions with and without checkpoint carriage. Passing requires:

1. The synthetic interference gate passes.
2. Live mastery produces an eligible candidate with exact source references.
3. Schema version 3 round-trips the active checkpoint exactly.
4. Production actions remain identical between checkpoint and control sessions.
5. Prediction-error sequences remain identical.
6. NDNRA suggestion sequences remain identical.
7. Learned graph states remain identical.
8. Consolidation state remains unchanged during the shadow session.
9. Action-authority violations remain zero.
10. Later contradictory evidence reopens the loaded candidate.
11. Restoration returns the exact pre-consolidation state.
12. Original source traces and the new contradiction remain preserved.
13. The completed restoration audit round-trips exactly.
14. SQLite remains outside consolidation eligibility, replay selection, reopening, restoration, persistence reconstruction, and shadow comparison.

This stage remains research-only and shadow-only. It does not grant advisory or action authority, alter production curiosity, or permit automatic structural growth. The heuristic readiness remains 94%; this value is an engineering progress indicator, not a probability or a production-readiness claim.

### 17.15 Proposal-only consolidation scheduling

The scheduling stage asks only whether an already eligible consolidation candidate is worth presenting for review. It does not apply consolidation, trigger replay, restore checkpoints, or change cognition.

```text
caller-supplied episode context
+ contextual mastery evidence
+ explicit lesson requests
+ active proposal capacity
        -> pure scheduling decisions
        -> bounded non-authoritative proposals
```

The single-lesson policy supports an explicit first review point, a minimum interval after a previously completed consolidation, duplicate-active-candidate suppression, and a maximum number of active candidates. All timing information is supplied by the caller as deterministic episode numbers. There is no internal clock, timer, background worker, persistent scheduling queue, or autonomous executor.

The multi-lesson portfolio policy preserves every lesson decision, ranks only proposal-ready candidates, and limits how many proposals may be selected for review. Priority uses:

1. How long a proposal has been due.
2. Mastery strength.
3. Effective independent support.
4. Stable candidate identity as the final tie-breaker.

Unselected candidates remain fully inspectable and may be reconsidered later. They are not deleted, merged, or treated as rejected evidence.

A controlled scheduling experiment compares three strategies under identical evidence arrival:

1. Fixed calendar windows.
2. Eligibility-only checking.
3. Evidence-aware bounded scheduling.

The default experiment produced:

| Strategy | Proposals | False | Redundant | Missed eligible episodes | Capacity pressure |
|---|---:|---:|---:|---:|---:|
| Fixed interval | 12 | 7 | 3 | 4 | 8 |
| Eligibility only | 15 | 0 | 13 | 0 | 6 |
| Evidence-aware bounded | 2 | 0 | 0 | 0 | 0 |

The evidence-aware bounded strategy proposed each genuinely mastered lesson once, ignored the weak lesson, and avoided both delay and overload. This is synthetic proposal-quality evidence only.

The live-shadow acceptance gate attaches the scheduler as a read-only observer after ordinary learning updates. Passing requires:

1. The synthetic scheduling comparison passes.
2. Live graph assemblies support an eligible contextual lesson.
3. Production actions remain identical to the unscheduled control.
4. Prediction-error sequences remain identical.
5. NDNRA suggestion sequences remain identical.
6. Live developmental signals remain identical.
7. Learned graph states remain identical.
8. Growth states remain identical.
9. Scheduling evaluates every configured step.
10. One eligible candidate produces one proposal and no duplicate proposals while active.
11. Scheduling does not mutate the contextual ledger.
12. Consolidation application count remains zero.
13. Action-authority violations remain zero.
14. SQLite remains outside scheduling cognition.

The validated scheduler is therefore an inspectable proposal generator only. It does not automatically execute consolidation, replay, restoration, advice, growth, or production actions. It also does not persist or autonomously resume a scheduling queue. Any move from proposal generation to execution requires a new explicit architecture decision and acceptance gate.

The heuristic readiness remains 94%; proposal scheduling adds evidence and control boundaries but does not justify a higher production-readiness claim.

### 17.16 Consolidation proposal lifecycle management

The lifecycle stage manages the review state of immutable scheduling proposals while remaining separate from consolidation application.

```text
immutable scheduling proposal
+ explicit caller review action
+ bounded active lifecycle capacity
+ newer same-lesson proposal when available
        -> immutable lifecycle record
        -> accepted, rejected, deferred, expired, or replaced state
        -> no consolidation execution
```

Review actions are explicit caller inputs. Accept, reject, and defer requests include the proposal, decision episode, reviewer identity, and reason. Deferral also includes a future review episode. Every decision receives a deterministic identity and preserves the original scheduling proposal unchanged.

Lifecycle records begin pending and preserve their complete ordered review history. Decision episodes must increase strictly. Deferred proposals cannot be reviewed before their declared review episode. Accepted and rejected review states are terminal during this stage. Proposal substitution, duplicate decisions, conflicting history reconstruction, and altered state relationships fail explicitly.

The bounded in-memory registry permits at most one active proposal per lesson and applies a caller-configured active-capacity limit. Pending, deferred, and accepted records consume capacity. Rejected, expired, and replaced records remain inspectable but release capacity.

Expiry is an explicit terminal management decision. Replacement requires:

1. The exact target proposal identity.
2. The expected current candidate identity.
3. A different replacement proposal.
4. The same lesson identity.
5. A newer proposal episode.
6. A replacement that already exists by the management decision episode.

Replacement closes the older record, preserves its entire lifecycle, and opens the newer proposal as pending. Both versions remain inspectable. Stale proposal identities, candidate mismatches, duplicate identities, wrong-lesson replacements, older replacements, future-dated replacements, and management of closed records fail before registry replacement.

A deterministic lifecycle experiment compares:

1. Automatic acceptance of the first valid proposal.
2. Permanent deferral.
3. Evidence-aware explicit management.

Additional independent evidence changes the candidate identity for the same lesson. Automatic acceptance therefore leaves one stale accepted candidate and blocks the current proposal. Permanent deferral avoids stale acceptance but still blocks the current proposal. Evidence-aware management defers the old proposal, replaces it when the newer candidate appears, and accepts the current proposal after one episode while preserving both records.

The live-shadow acceptance gate attaches scheduling and lifecycle review after ordinary learning. It creates one proposal, defers it for a bounded interval, and later accepts it for future consideration. Passing requires:

1. The synthetic lifecycle comparison passes.
2. Live graph assemblies support an eligible contextual lesson.
3. Production actions remain identical to the control.
4. Prediction-error sequences remain identical.
5. NDNRA suggestion sequences remain identical.
6. Live developmental signals remain identical.
7. Learned graph state remains identical.
8. Growth state remains identical.
9. Exactly one proposal is scheduled.
10. Exactly one defer and one accept review are recorded.
11. Complete lifecycle history remains inspectable.
12. Contextual evidence remains unchanged by lifecycle operations.
13. Consolidation application count remains zero.
14. Action-authority violations remain zero.
15. SQLite remains outside lifecycle cognition.

Accepted means approved only for possible future consideration. It does not authorize application, replay, restoration, route ranking, advice, growth, or production actions. During this lifecycle stage, state remained in memory and brain persistence remained schema version 3.

The validated lifecycle gate raises heuristic theory-to-integration readiness from 94% to 95%. This is an engineering progress indicator, not a probability, safety certification, execution approval, or production-readiness claim.

### 17.17 Restart-safe proposal memory

Restart-safe proposal memory preserves immutable lifecycle evidence across process restart while keeping persistence and revalidation outside cognition and action authority.

```text
immutable lifecycle registry
+ versioned lifecycle checkpoint
+ checksum-protected schema-4 brain envelope
+ current contextual evidence after restart
        -> exact reconstruction
        -> current, stale, superseded, or invalid-for-review evidence
        -> complete corruption fallback
        -> no consolidation execution
```

The lifecycle checkpoint schema is independent from the outer brain schema. The checkpoint codec reconstructs proposals, candidates, mastery snapshots, source-event identities, review decisions, ordered history, management decisions, archived records, active records, capacity, and replacement links. It recalculates deterministic review and management decision identities rather than trusting stored hashes.

The codec rejects:

1. Incompatible checkpoint schema or version.
2. Authority-bearing checkpoint, registry, record, review, or management state.
3. Altered review or management decision identities.
4. Invalid lifecycle transitions or derived deferral state.
5. Incorrect active-record counts.
6. Candidate and mastery-source mismatches.
7. Replaced proposals whose exact replacement record is absent.
8. Invalid same-lesson or proposal-time relationships.

Brain schema version 4 atomically stores graph, growth, consolidation-checkpoint, and proposal-lifecycle state in one checksum-protected envelope. The existing deterministic ASCII encoding, temporary-file write, flush, file sync, atomic replacement, and cleanup rules remain unchanged.

Migration is explicit:

- Schema 1 restores its supported graph form and creates empty consolidation and lifecycle checkpoints.
- Schema 2 restores contextual graph memory and creates empty consolidation and lifecycle checkpoints.
- Schema 3 preserves its consolidation checkpoint and creates an empty lifecycle checkpoint.
- Schema 4 restores and validates every persisted subsystem together.

A missing, malformed, checksum-invalid, incompatible, or relationally inconsistent schema-4 lifecycle payload causes complete fresh-state fallback. Partial graph, growth, consolidation, or lifecycle restoration is forbidden.

Restart revalidation is a pure evidence policy. It evaluates active lifecycle records only and returns:

- `current` when original sources, broad mastery, contradiction state, structures, and exact candidate identity all remain valid.
- `stale` when the proposal remains review-eligible but additional evidence changes the candidate identity.
- `superseded` when a supplied newer same-lesson proposal exactly represents the current candidate.
- `invalid_for_review` when source events, mastery, contradictions, assemblies, routes, or other eligibility conditions fail.

Revalidation cannot create, accept, reject, defer, expire, replace, or delete proposals. It cannot change lifecycle status, ordered review history, contextual evidence, graph state, growth state, or persisted state.

The restart-safe acceptance gate requires:

1. Schema 4 exactly restores graph, growth, lifecycle, and review history.
2. The outer checksum verifies and no temporary file remains.
3. Schemas 1, 2, and 3 migrate to an explicit empty lifecycle checkpoint.
4. Schema 3 preserves its existing consolidation checkpoint.
5. Outer-checksum corruption produces complete fresh-state fallback.
6. Relational lifecycle corruption with a recomputed valid outer checksum also produces complete fresh-state fallback.
7. A clean restored accepted proposal revalidates as current.
8. Additional independent supporting evidence changes the candidate identity and revalidates the stored acceptance as stale.
9. Stale detection preserves the registry and review history unchanged.
10. Persisted-revalidation and empty-lifecycle control sessions produce identical production actions.
11. Prediction errors remain identical.
12. NDNRA suggestions remain identical.
13. Live developmental signals remain identical.
14. Final learned graph state remains identical.
15. Final growth state remains identical.
16. Registry and contextual-ledger mutations caused by revalidation remain zero.
17. Consolidation applications, replay triggers, and restoration triggers remain zero.
18. SQLite cognitive operations and action-authority violations remain zero.

Passing this gate raises heuristic theory-to-integration readiness from 95% to 96%. This is an engineering progress indicator for restart-safe proposal evidence, not execution approval, production readiness, or a general-intelligence claim.

### 17.18 Human-approved consolidation execution

Human-approved consolidation execution connects one exact current accepted proposal to one bounded application while keeping approval, persistence, and execution subordinate to production curiosity and protected human authority.

```text
accepted lifecycle proposal
+ explicit human approval
+ immediate permit-issuance revalidation
+ deterministic bounded single-use permit
+ immediate precommit revalidation
        -> one atomic application
        -> consumed permit plus matching receipt
        -> durable exact old or exact new envelope
        -> no autonomous execution
```

Approval must identify the exact proposal, candidate, accepted review decision, approver, and reason. Issuance and commit independently reconstruct current eligibility. Stale, superseded, invalid-for-review, cancelled, expired, consumed, mismatched, or malformed authorization cannot apply.

The permit is immutable authorization evidence, not an executor. Its lifecycle is one of `issued`, `cancelled`, `expired`, or `consumed`. One permit identity can authorize at most one successful application, and recreating identical permit content cannot bypass the retained lifecycle record.

Brain schema version 5 extends the checksum-protected brain envelope with a versioned execution checkpoint containing complete permit lifecycle records and successful execution receipts. Schemas 1 through 4 migrate to an explicit empty execution checkpoint. No permit or receipt is inferred from earlier consolidation history.

The checkpoint validates deterministic ordering and exact relational consistency:

1. Every consumed permit has exactly one receipt.
2. Only a consumed permit may have a receipt.
3. The consumed transition exactly matches the receipt transition.
4. The transition consumption reference equals the execution identity.
5. Every receipt retains its exact permit lifecycle.
6. Every receipt application matches persisted application history.
7. Every applied candidate exists in the consolidation state.
8. Sequential receipts form one exact before-to-after state chain.
9. Automatic execution count remains zero.
10. The checkpoint carries no execution or application authority.

Durable execution first verifies the exact persisted graph-adjacent authority boundaries. It then accepts only:

```text
OLD: old consolidation state + issued permit + no receipt
NEW: new consolidation state + consumed permit + matching receipt and application
```

Old state with a consumed permit, new state with an issued permit, application without receipt, receipt without application, and any other hybrid are invalid. Interruption before atomic replacement resolves to the exact old state. Interruption after replacement resolves to the complete new state. If neither exact envelope exists, the operation fails hard rather than inferring intent.

Invalid outer checksum, corrupted transition or receipt identity, incorrect consumption reference, consumed permit without receipt, receipt with an issued permit, duplicate permits or receipts, or missing receipt application causes complete fresh-state fallback. Partial recovery of graph, growth, consolidation, lifecycle, or execution evidence is forbidden when authority-bearing relationships are invalid.

The live acceptance gate records:

```text
1 explicit human approval
1 current immediate precommit revalidation
0 control applications
1 approved application
1 consumed permit
1 execution receipt
0 automatic executions
0 replay triggers
0 restoration triggers
0 production-action authority violations
0 SQLite cognition
```

Control and approved paths preserve equal production actions, prediction errors, developmental signals, advice, route ranking, unrelated graph learning, growth state, and human-dependence accounting. Proposal history and graph and growth state at the execution boundary remain unchanged by the application gate.

Production curiosity remains the sole production action authority. NDNRA and consolidation cannot choose production actions. SQLite remains scientific and audit storage, not cognition. Controlled retention replay, restoration, advice influence, growth influence, route ranking, autonomous workers, timers, queues, and execution remain outside this stage.

Passing this gate raises heuristic theory-to-integration readiness from 96% to 97%. This is an internal engineering progress indicator for bounded human-approved execution, not a production-readiness score, safety certification, autonomous authority, AGI percentage, or claim that controlled replay and restoration are implemented.

### 17.19 Controlled replay and exact checkpoint restoration

Controlled replay and restoration are explicit human-governed operations. Replay revisits only named real activity and may reduce dormancy without creating evidence, confidence, mastery, growth pressure, or production-action authority. Restoration accepts only a separate checksum-verified complete current-schema source and replaces graph, growth, consolidation, proposal lifecycle, execution state, learned-consequence checkpoint state, and active activity memory together.

The destination preserves its current monotonic permit and receipt audit. That audit must contain all source audit history, so restoring an older active state cannot revive a consumed approval. Partial restoration and automatic replay or restoration are forbidden.

Live acceptance compares an unreplayed control with an otherwise identical replayed state, and an exact source checkpoint with its restored destination. Replay must preserve production actions, prediction errors, developmental signals, graph learning, and non-dormancy growth. Restoration must reproduce subsequent actions, suggestions, prediction errors, signals, graph learning, and growth exactly.

Passing this gate raises the legacy narrow-scope theory-to-integration marker from 97% to 98%. The expanded developmental architecture marker is 79% because learned consequence modelling, bounded imagination, and safe experiment promotion remain future stages.

### 17.20 Exact-context learned consequence model

The first learned consequence-model boundary is an isolated one-step predictor keyed by one exact grounded context and one exact action. It learns only from unique real transitions and predicts only explicitly requested effects plus the most frequent exact next context.

Each prediction exposes:

- requested effect coverage;
- bounded real-evidence coverage;
- raw structural confidence;
- empirically calibrated confidence;
- explicit uncertainty;
- exact supporting real event identities.

Effect confidence combines bounded support with observed consistency. Contradictory real outcomes increase dispersion and reduce confidence. A later real outcome may classify an earlier prediction as overconfident, calibrated, underconfident, or unknown, but calibration cannot raise confidence above current evidence coverage.

Evaluation is pure. Replay and imagined activity cannot update the model. Batch 1 performs no action chaining, rollout, optimisation, persistence, advice, route ranking, or action selection. Production curiosity remains the sole production action authority.

### 17.21 Bounded contextual consequence transfer

Contextual transfer is a separate stateless policy over exact learned consequence records. It never writes a target-context record and never replaces exact evidence. Any existing exact record remains primary, including partial or low-confidence exact evidence.

Transfer eligibility requires:

- the same active need identity;
- the requested action to be available in both contexts;
- compatible positional sensor, human, and resource shapes;
- an explicit minimum combined similarity;
- a source prediction above the configured confidence floor.

Similarity evidence reports sensor-bin similarity, available-action overlap, human-state similarity, resource-state similarity, structural compatibility, and the final weighted score. The weights and thresholds are fixed configuration in this batch rather than learned semantics.

Transferred confidence is attenuated by source confidence, context similarity, and a transfer scale, then capped globally. Every transferred effect retains exact source record and real event identities. Multiple consistent sources may add bounded support. Opposing directional sources produce explicit contradiction evidence that reduces confidence and may reduce it to zero.

Missing dimensions remain unknown. An exact next context is never transferred because a source context's next state is not an exact prediction for a different target context. The policy remains prediction-only and cannot rank, recommend, schedule, or execute actions.

### 17.22 Observed ordered consequence chains

The first ordered-chain boundary stores complete observed chain examples rather than
deriving them from single-step records. Each chain step must come from exact real
transition evidence and preserve:

- exact event ID;
- exact pre-action context;
- exact action code;
- exact observed next context;
- exact observed effects;
- real origin.

Observed chains require exact continuity:

```text
step[i].next_context == step[i + 1].context
```

Disconnected chains are rejected instead of bridged by contextual similarity. A chain
identity includes the exact start context, ordered action codes, ordered source event
IDs, and exact final observed context. Reversing action order creates a different
identity and does not share support.

One event may appear at most once inside one chain. Re-registering an identical chain
does not increase support. Reusing one event with a different transition is rejected.
Overlapping chains remain inspectable through deterministic correlation groups, and
each connected overlap group counts only once for independent support.

Predictions are request-driven by exact start context and exact ordered action sequence.
The chain model reports an exact final context only when exact observed ordered-chain
evidence supports it. It reports per-step requested effect estimates only and deliberately
does not sum arbitrary effects across steps. Missing dimensions remain unknown.

Directional contradiction for the same effect at the same chain position, along with
final-context dispersion, remains visible and reduces confidence. Confidence derives
from independent real support and consistency, not from chain depth, raw chain count,
transfer, replay, or imagined outcomes.

The chain model is in-memory, prediction-only, and non-authoritative. It cannot select,
rank, recommend, schedule, search, optimise, or execute actions. It has no persistence,
SQLite, timer, worker, replay, restoration, advice, growth, or production integration
dependency in this batch.

The expanded developmental architecture marker remains 79% through Batch 3. Restart-safe
persistence, live integration, complete failure-path acceptance, and stage closure remain
required before reassessment.

### 17.23 Learned consequence checkpoint persistence

The restart boundary advances brain persistence to schema version 7. A schema-7 brain
envelope may carry an explicit `NDNRALearnedConsequenceCheckpoint` containing:

- exact-context learned consequence observations and records;
- raw weighted effect statistics plus calibration evaluation provenance and totals
  needed for exact confidence reconstruction;
- exact next-context counts and source event identities;
- bounded contextual-transfer configuration;
- complete observed consequence chains and derived duplicate-protection indexes;
- deterministic limits required to reconstruct the same in-memory state.

Older brain schemas migrate to an explicit empty learned-consequence checkpoint. The
loader does not infer missing evidence or create predictions during migration. A valid
schema-7 restart reconstructs the single-step model, transfer configuration, observed
chain model, duplicate protection, source-event conflict protection, contradiction
state, and confidence behaviour exactly.

Corrupt, truncated, oversized, conflicting, unsupported, non-canonical, or authority
bearing learned-consequence state invalidates the whole brain load and returns a fresh
safe fallback. Failed saves are atomic and leave the prior checkpoint intact. Loading the
same valid checkpoint repeatedly is idempotent.

This checkpoint remains reconstruction-only. It has no SQLite dependency, cognitive
lookup path, automatic prediction loop, timer, worker, replay trigger, restoration
trigger, recommendation, ranking, search, optimisation, execution, or production-action
authority.

Passing this boundary raises the expanded developmental architecture marker from 79% to
80%. This is a restart-safety milestone, not stage closure, production readiness,
autonomous authority, or a claim that the expanded architecture has reached 100%.

### 17.24 Learned consequence live acceptance

The live acceptance boundary connects the learned consequence model to the deterministic
Nursery loop as an observer only.

```text
production observation
  -> production curiosity selects the action
  -> learned consequence model predicts before execution
  -> Nursery executes the production action
  -> predictive trainer updates from the real transition
  -> learned consequence model records the real outcome
  -> prior prediction is evaluated and calibrated
```

The observer is not part of the production action path. Acceptance requires a matched
control with identical scenario seed, trainer seed, curiosity configuration, and play
budget. The model-enabled pass must preserve both production action sequence and
predictive-training error sequence.

The gate also requires:

- real pre-action predictions before each evaluated transition;
- later real outcome comparison and calibration;
- uncertainty reduction under repeated consistent real evidence;
- confidence reduction under contradiction;
- exact context-local unknown predictions for unsupported contexts;
- exact observed consequence chains built only from consecutive unique real Nursery
  transitions;
- preserved ordered source event IDs, ordered action codes, and exact context continuity;
- duplicate, conflicting, disconnected, replayed, imagined, transferred, partial,
  missing, and bound-failing evidence paths to be rejected or non-evidentiary without
  mutating accepted real state;
- schema-7 restart evidence proving equivalent exact predictions, chain predictions,
  provenance, duplicate protection, configuration, confidence, and zero authority;
- checksum-valid malformed persisted learned state to cause complete safe fallback;
- deterministic repeated acceptance and pure non-mutating predictions;
- zero advice decisions, route rankings, growth attempts, replay operations,
  restoration operations, SQLite cognition, and production-action authority.

Passing this boundary raises the expanded developmental architecture marker from 80% to
82%. It formally completes the learned consequence model stage. It does not add bounded
imagination, imagined route optimisation, safe experiment promotion, semantic
abstraction, learned similarity weights, autonomous production authority, or a 100%
architecture claim.

### 17.25 Bounded imagination Batch 1 boundary

The first bounded-imagination boundary is narrower than the later full stage. It is an
in-memory caller-driven rollout layer over exact `LearnedConsequenceModel.predict`
evidence only.

- The caller supplies every candidate action sequence.
- Candidate order is preserved exactly and is never ranked, selected, scheduled,
  optimised, recommended, or executed.
- Each step begins from the exact current context and requests the same sorted relevant
  effect codes.
- A step is supported only when exact requested effects exist and an exact predicted next
  context exists.
- The exact predicted next context becomes the next step context.
- Missing actions, missing exact evidence, missing exact next context, or supporting
  source-event bound exhaustion stop the trace immediately.
- Unsupported traces expose no final context.
- Effects remain per-step only; there is no cumulative effect or route score.
- Every step and trace remains explicitly imagined and preserves exact source prediction
  IDs plus exact supporting real event IDs as provenance only.

This boundary is deliberately non-persistent, non-integrated, and non-authoritative. It
does not add candidate generation, contextual transfer as an alternate source, observed
chain search, advice, growth, replay, SQLite, timers, workers, asyncio, safe-experiment
promotion, or production integration.

### 17.26 Bounded imagination Batch 2 boundary

The second bounded-imagination boundary remains narrower than later route-search,
selection, or experiment-promotion stages. It adds only in-memory deterministic exact-record
candidate enumeration.

- The caller supplies one exact starting `ContextSignature` and sorted unique requested
  effect codes.
- The generator enumerates supported prefixes breadth-first from depth 1 through the
  configured maximum.
- Within each parent prefix, exact current-context records are considered in stable
  `(action_code, record_id)` order.
- A step is admitted only when the exact record context matches the current context, the
  action is available, exact prediction returns every requested effect in exact requested
  order, an exact predicted next context exists, and supporting provenance remains in
  bounds.
- The exact predicted next context becomes the next prefix context.
- One exact source prediction ID may appear at most once inside one generated candidate.
- Each imagined step preserves exact context, action, predicted effects, exact predicted
  next context, source record ID, source prediction ID, and exact supporting real event
  IDs.
- Result-level truncation reasons remain explicit and deterministic. Candidate objects do
  not carry ranking, scoring, selection, recommendation, schedule, execution, promotion,
  or generic truncation fields.

This boundary is still deliberately non-persistent, non-integrated, and
non-authoritative. It does not add contextual transfer as an alternate source, observed
chain search, advice, growth, replay, SQLite, timers, workers, asyncio, safe-experiment
promotion, or production integration.

### 17.27 Bounded imagination Batch 4 boundary

The fourth bounded-imagination boundary adds only pairwise alignment comparison over one
complete Batch 3 `ImaginedRouteEvaluationResult`.

- The comparison request embeds the complete source result.
- Source result and request identities are derived from the embedded result rather than
  caller-supplied strings.
- Pair comparisons preserve caller-index order and never sort by quality.
- Unknown alignments, low confidence, and route-depth mismatch block dominance.
- Conflicting trade-offs remain incomparable.
- Alignment-equivalent routes remain distinct and preserve source provenance through the
  embedded Batch 3 result.
- Incompatible need or evaluation semantics are rejected atomically.
- No transitive closure, nondominated set, Pareto front, global route score, utility,
  rank, winner, recommendation, selection, optimisation, schedule, promotion, execution,
  persistence, live integration, or production authority is created.

The expanded developmental architecture marker remains 82%. Persistence, live
integration, safe-experiment promotion, and production action influence remain deferred.

## 18. Architectural invariants

The following rules must remain true:

1. No central component owns complete cognitive memory.
2. Learning updates are gated by local participation.
3. Global signals modulate eligible local structures rather than writing complete memories.
4. Needs recruit assemblies but do not encode full plans.
5. Multi-step behaviour remains connected to a persistent unresolved need.
6. Recall has bounded computational depth and measurable cost.
7. Dormant memories remain recoverable.
8. Memory-bearing neurons and synapses are not permanently deleted.
9. Growth requires repeated evidence of important unresolved capacity limits.
10. Curiosity and ambition provide growth pressure, not uncontrolled neuron creation.
11. SQLite remains outside the future cognitive decision loop.
12. Every implementation step must remain inspectable and experimentally falsifiable.
13. Only exact event identity is deduplicated; legitimate contextual repetitions remain separate.
14. Copied or correlated evidence cannot multiply independent support.
15. Repetition strength, context diversity, route diversity, causality, transfer, and protection remain distinct measures.
16. Generalized lessons retain inspectable references to their episodic source traces.
17. Contextual mastery remains non-authoritative until a later explicit integration gate.
18. Consolidation scheduling may propose review candidates but cannot execute consolidation or replay.
19. Unselected and active scheduling candidates remain inspectable and cannot silently erase one another.
20. Proposal lifecycle decisions preserve immutable proposal evidence and complete ordered review history.
21. Accepted lifecycle status never implies consolidation, replay, restoration, advice, growth, or action authority.
22. Expired and replaced proposals remain inspectable; replacement cannot silently overwrite an earlier proposal.
23. Persisted lifecycle state remains bounded, caller-driven, and reconstruction-only; storage never becomes cognitive lookup or an execution queue.
24. Brain schema migration must create explicit empty lifecycle and execution state rather than infer missing review or authorization history.
25. Corrupt lifecycle or execution state must invalidate the complete load; partial graph, proposal, permit, or receipt restoration is forbidden.
26. Restart revalidation must compare persisted proposals with current evidence before execution may use them.
27. Revalidation classifications never mutate lifecycle status, review history, contextual evidence, graph state, or growth state.
28. Stale, superseded, and invalid-for-review results remain inspectable and cannot trigger silent deletion or automatic application.
29. Consolidation application requires explicit human approval tied to one exact proposal, candidate, and accepted review decision.
30. Permit issuance and commit each require immediate current-evidence revalidation.
31. Execution permits remain bounded, immutable, deterministic, and single-use.
32. A successful application requires one consumed permit, one matching receipt, and one matching persisted application.
33. Failed operations restore the exact prior state or use complete safe fallback; partial authority state is forbidden.
34. No autonomous workers, timers, queues, permit creation, permit consumption, replay, restoration, advice, growth, or route-ranking authority is permitted; replay and restoration require explicit bounded human-approved single-use operations.
35. Production curiosity remains the sole production action authority; NDNRA, consolidation, replay, and restoration cannot select production actions.
36. SQLite remains storage and audit evidence and cannot become approval, revalidation, replay selection, restoration selection, execution selection, or action authority.
37. Replay may revisit only exact named real activity and may change dormancy only; it cannot create evidence, confidence, mastery, competence, or non-dormancy growth.
38. Restoration must replace one complete checksum-verified current-schema active state; partial authority-bearing restoration is forbidden.
39. The current operation audit must contain source audit history, and restoration cannot revive cancelled, expired, or consumed approvals.
40. Replay/restoration acceptance must preserve production actions and expose exact receipts, failure paths, restart state, and zero automatic-operation counts.
41. Learned consequence records remain local to one exact context and action; contextual transfer is a separate derived prediction and cannot create a target-context record.
42. Only unique real transitions may update the learned consequence model; observed chains must come from consecutive unique real transitions with exact continuity; replay, imagination, and transferred predictions remain non-evidentiary.
43. Missing effect dimensions must remain unknown, and calibrated or transferred confidence cannot exceed its explicit evidence or transfer coverage.
44. Consequence prediction and contextual-transfer evaluation must be pure and cannot mutate model state or select actions.
45. Consequence predictions and transferred estimates cannot rank, recommend, schedule, or execute production actions.
46. Existing exact context-action evidence always takes precedence over transfer, including partial and low-confidence exact records.
47. Transfer requires explicit structural compatibility, similarity evidence, source-confidence evidence, and deterministic finite source bounds.
48. Transferred confidence must be attenuated and globally capped; one source cannot establish broad certainty.
49. Directionally opposing transfer sources must remain inspectable and reduce confidence through explicit contradiction evidence.
50. Exact next-context claims cannot be transferred across contexts.
51. Observed consequence chains require exact real transition continuity; contextual similarity cannot bridge a disconnected chain.
52. Ordered chain identity preserves ordered actions and ordered source event IDs; reversed order is distinct.
53. Reused or overlapping chain source events remain inspectable and cannot multiply independent support.
54. Chain effects are reported per observed step unless a later stage defines a safe effect-specific aggregation rule.
55. Observed chain predictions cannot select, rank, recommend, search, optimise, schedule, or execute actions.
56. Live learned-consequence predictions may observe before production action execution and calibrate after the real outcome, but they cannot change production action selection, training updates, advice, route ranking, growth, replay, restoration, or SQLite lookup.
57. Bounded imagination traces and generated candidates remain explicitly imagined, provenance-only, non-evidentiary, deterministic, finite, and unable to alter confidence, mastery, competence, growth, replay, persistence, or production authority.
58. Exact-record candidate enumeration may preserve deterministic breadth-first order, but that order is not a score, rank, recommendation, selection, schedule, promotion, or execution decision.
59. Imagined route evaluation must keep every need dimension and every route step explicit; missing effects remain unknown and arbitrary cross-effect or cross-step totals are forbidden until a separate semantics contract is accepted.
60. Need-alignment annotation may preserve learned prediction confidence and exact source provenance, but it cannot create a route winner, rank, recommendation, selection, optimisation, schedule, promotion, execution, persistence, or production authority.
61. Every evaluated step must retain the request need identity; active-need drift invalidates the route evaluation rather than being silently compared under the old need.
62. Imagined route comparison may report caller-order pairwise alignment relations only; it cannot create a route score, utility, rank, winner, selected candidate, recommendation, optimisation, schedule, promotion, execution, persistence, live integration, or production authority.
63. Comparison uncertainty auditing may expose only exact source-linked unknown alignment, low-confidence, route-depth, and conflicting-trade-off issues; it cannot propose an experiment, route, action, permission decision, schedule, promotion, or execution.
64. Uncertainty audit output must revalidate the complete Batch 4 source result, preserve source pair and dimension order, remain deterministic and in memory, and retain zero evidence, learning, and production authority.

## 19. First prototype boundary

The first prototype should not replace SeedMind's current predictive core.

It should be a small isolated experimental subsystem containing:

```text
bounded local neurons
bounded local synapses
eligibility traces
one or more modulatory signals
one need pulse
spreading activation
reversible dormancy
effort-based recall depth
simple growth pressure
optional neuron creation
```

### Suggested prototype task

A minimal environment contains:

```text
internal heat state
fan object
fan location
stand action
walk action
reach action
activate action
cooling outcome
```

The prototype should learn through local traces that activating the fan reduces the heat need.

After the assembly becomes dormant, a later heat need should reactivate the relevant action chain.

## 20. Prototype acceptance criteria

The architecture should not be considered viable until a prototype demonstrates all of the following:

1. Local eligibility traces assign delayed outcome credit without global backpropagation through the full episode.
2. A heat-reduction need pulse recruits fan-related assemblies.
3. The system reconstructs a multi-step action chain from distributed local associations.
4. The need remains active until the environment reports cooling.
5. A previously learned assembly can become dormant.
6. Shallow recall may fail while deeper effort-based recall succeeds.
7. Recall depth has measurable computational cost.
8. Repeated unresolved important experience produces growth pressure.
9. Growth adds useful capacity rather than duplicate inactive neurons.
10. SQLite is not queried to choose or reconstruct the action chain.

## 21. Research questions

The following questions remain open:

1. What should a need-compatibility representation look like?
2. How should spreading activation be normalized to prevent runaway recruitment?
3. How should multiple simultaneous needs compete or cooperate?
4. How should candidate action chains be represented without a central planner?
5. How should the predictive core interact with temporary neural assemblies?
6. What local signal best measures representational saturation?
7. When should a dormant assembly be reactivated?
8. How should conflicting memories coexist without deletion?
9. How should effort budgets limit recall depth?
10. How should newly created neurons choose their initial connections?
11. How can local learning avoid catastrophic interference?
12. How should successful assemblies consolidate while remaining adaptable?

## 22. Non-goals

NDNRA does not currently claim:

```text
an exact biological simulation
a complete neuroscience model
human-level planning
a replacement for all existing SeedMind modules
proof that neurons are never removed in biological brains
proof that one local learning rule solves every developmental problem
```

It is a falsifiable engineering architecture inspired by local neural learning, distributed memory, persistent needs, and activity-dependent recruitment.

## 23. Planned relationship to the implementation roadmap

This architecture is intentionally separate from the current master implementation plan.

The existing plan remains the validated baseline.

NDNRA should enter implementation through isolated experiments and evidence gates before it changes the main predictive, memory, or planning systems.

Recommended sequence:

```text
1. Preserve current Week 7 SQLite implementation as baseline and observer.
2. Build isolated local eligibility-trace prototype.
3. Add one need pulse and spreading recruitment.
4. Add reversible dormancy and recall depth.
5. Add curiosity and ambition growth pressure.
6. Test structural neuron growth.
7. Compare against fixed-network and SQLite-retrieval baselines.
8. Integrate only after evidence shows a clear advantage.
```

## 24. Summary

NDNRA proposes that SeedMind should become a growing neural organism rather than a fixed network attached to a large memory database.

```text
Experience
    -> leaves local eligibility traces

Important outcome
    -> broadcasts a modulatory signal

Local eligible structures
    -> update their own memory

Need
    -> sends a recruitment pulse

Relevant dormant and active assemblies
    -> form candidate solutions

Predictive evaluation
    -> selects an action chain

Persistent need
    -> keeps the chain directed until resolution

Unresolved important need
    -> creates curiosity and ambition growth pressure

Insufficient capacity
    -> grows new neurons and connections

Unused memory
    -> becomes dormant, not deleted
```

The final objective is a SeedMind whose memory, recall, growth, and action emerge from locally adaptive neural structures.
