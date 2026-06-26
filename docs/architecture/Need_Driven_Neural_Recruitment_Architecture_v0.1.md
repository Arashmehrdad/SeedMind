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