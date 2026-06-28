# SeedMind Learned Consequence Model Stage Plan

Date: 28 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Stage status: active
Authority: research-only, prediction-only, no action-selection or production-action authority
Expanded developmental architecture progress at stage start: 79%

## 1. Stage objective

This stage will give SeedMind a bounded internal model that predicts relevant one-step consequences from context plus action, reports uncertainty and evidence coverage, compares those predictions with later real outcomes, and corrects confidence without treating prediction or imagination as fact.

The intended first-step learning loop is:

```text
exact pre-action context
+ exact action
+ unique real observed transition
        -> local one-step consequence record
        -> predicted relevant effects
        -> predicted exact next context
        -> explicit evidence coverage and uncertainty
        -> later real comparison and calibration
        -> no action authority
```

The stage must remain separate from action selection, dreaming, route optimisation, safe experiment promotion, persistence, and production integration until each later boundary has its own contracts and evidence.

## 2. Mandatory invariants

- Production curiosity remains the sole production action authority.
- The consequence model cannot select, execute, rank, recommend, or schedule production actions.
- Only unique real observations may update model evidence.
- Replay and imagined activity cannot become model evidence.
- Exact event identity is deduplicated; conflicting reuse of one event identity is rejected.
- Context and action remain local. Evidence for one context-action pair cannot silently generalise to another.
- Missing effect dimensions remain unknown rather than being manufactured as zero-confidence facts.
- Confidence cannot exceed actual evidence coverage.
- Repeated consistent outcomes may increase support.
- Contradictory outcomes must increase uncertainty or reduce confidence.
- Calibration uses only a prediction made before the real outcome.
- Evaluation is pure and cannot itself mutate the model.
- Model records, observations, predictions, and evaluations carry no action-selection or production-action authority.
- No persistence, SQLite, timers, workers, queues, rollouts, optimisers, or integration actions are permitted in Batch 1.

## 3. Stage batches

### Batch 1 - exact-context single-step consequence model

Status: implemented in the commit containing this plan.

Deliverables:

- Exact `ContextSignature` plus action-scoped records.
- Unique real transition observations with exact next context and observed effects.
- Explicit relevant-effect prediction requests.
- Predictions containing:
  - known requested effects only;
  - most frequent exact next context;
  - effect coverage;
  - evidence coverage;
  - raw confidence;
  - calibrated confidence;
  - uncertainty;
  - exact supporting real event identities.
- Weighted mean and dispersion for each effect dimension.
- Finite record, observation, dimension, and next-context bounds.
- Pure prior-prediction versus later-real-outcome evaluation.
- Overconfident, calibrated, underconfident, and unknown calibration classifications.
- Confidence calibration capped by available evidence coverage.
- Exact duplicate rejection without double learning.
- Atomic bound failures that leave retained state unchanged.
- Deterministic ASCII-safe snapshots.
- No sequence modelling, generalisation, persistence, dreaming, or action authority.

Implementation:

- `src/seedmind/research/ndnra/learned_consequence_model.py`

Tests:

- `tests/unit/test_ndnra_learned_consequence_model.py`

### Batch 2 - bounded contextual transfer

Status: implemented in the commit containing this update.

Deliverables:

- Separate stateless transfer policy over exact learned consequence records.
- Exact-context evidence always wins, including partial or low-confidence exact records.
- Structured similarity evidence for active need, sensor bins, available actions, human state, and resource state.
- Required active-need, action-availability, and positional-shape compatibility before transfer.
- Explicit minimum similarity threshold, source-confidence threshold, source limit, candidate limit, and confidence cap.
- Conservative confidence attenuation by context similarity and transfer scale.
- Transferred effects retain exact source record IDs and real event IDs.
- Missing source effect dimensions remain unknown.
- Exact next context is never transferred across contexts.
- Per-effect directional contradiction evidence reduces transferred confidence and can reduce it to zero.
- One source cannot create broad certainty, while multiple consistent sources may add bounded support.
- Candidate selection is deterministic and inspectable.
- Transfer prediction is pure and cannot create an exact target-context record.
- No sequence modelling, persistence, dreaming, optimisation, ranking, recommendation, or action authority.

Implementation:

- `src/seedmind/research/ndnra/contextual_consequence_transfer.py`

Tests:

- `tests/unit/test_ndnra_contextual_consequence_transfer.py`

### Batch 3 - ordered actions and short consequence chains

Planned:

- Represent action order explicitly.
- Learn short observed action transitions and combinations.
- Limit chain depth, branch count, and effect dimensions.
- Preserve every real source transition used by a chain.
- Prevent repeated reuse of one event from multiplying support.
- Produce predictions only; no action ranking or execution.

### Batch 4 - persistence and restart reconstruction

Planned:

- Persist model observations, records, calibration state, and source identities.
- Add an explicit versioned consequence-model checkpoint.
- Migrate older brain schemas to an explicit empty model checkpoint.
- Preserve exact duplicate protection across restart.
- Reject relational or checksum corruption with complete safe fallback.
- Keep persistence reconstruction-only and outside cognition.

### Batch 5 - live integration, acceptance, and closure

Planned:

- Compare model-enabled shadow operation with an identical control.
- Demonstrate real pre-action prediction followed by later outcome comparison.
- Demonstrate uncertainty reduction under consistent real evidence.
- Demonstrate confidence reduction under contradiction.
- Demonstrate context-local failure consequences.
- Demonstrate no production-action, advice, route-ranking, growth, replay, restoration, or SQLite cognitive influence.
- Export inspectable observatory evidence.
- Run complete repository quality gates.
- Reassess the expanded progress marker only after all gates pass.

## 4. Public contracts

Batch 1:

- `CalibrationDirection`
- `LearnedConsequenceModelConfig`
- `ConsequenceModelObservation`
- `ConsequencePredictionRequest`
- `ConsequencePrediction`
- `ConsequencePredictionEvaluation`
- `ConsequenceModelUpdate`
- `ContextActionConsequenceRecord`
- `LearnedConsequenceModel`

Batch 2:

- `ConsequencePredictionMode`
- `ContextualTransferConfig`
- `ContextSimilarityEvidence`
- `ContextTransferSourceEvidence`
- `TransferredEffectEvidence`
- `ContextualTransferPrediction`
- `BoundedContextualTransferPolicy`

## 5. Confidence and uncertainty design

For one requested effect dimension, Batch 1 tracks:

```text
weighted observed mean
weighted observed variance
consistency = 1 - sqrt(variance)
support = min(1, summed observation confidence / evidence target)
raw effect confidence = support x consistency
```

Next-context confidence combines:

```text
exact next-context frequency
x
bounded real-observation support
```

Request-level evidence coverage includes both requested effect support and next-context support. Calibration blends structural confidence with empirical prior-prediction accuracy but is capped by current evidence coverage.

Therefore:

- calibration cannot create confidence for missing evidence;
- consistent evidence can increase support;
- contradictory evidence reduces consistency;
- prior overconfidence can be corrected downward;
- unknown predictions remain explicitly uncertain.

## 6. Explicit current exclusions

Batches 1 and 2 do not provide:

- semantic abstraction beyond explicit grounded component similarity;
- learned similarity weights;
- transfer of an exact next context;
- multi-action sequences;
- action combinations;
- imagined rollouts;
- dreaming;
- optimiser-driven search;
- action recommendation;
- action ranking;
- production integration;
- persistence;
- timers, queues, or background workers;
- SQLite cognition;
- safe experiment proposals;
- competence or mastery updates from predictions.

## 7. Progress rule

The expanded developmental architecture marker remains **79%** through Batch 2. The new contracts and behavioural tests are necessary but do not complete persistence, sequence modelling, live integration, or end-to-end acceptance.

No percentage should increase merely because a prediction object exists. Later progress requires behavioural evidence, failure-path tests, restart safety where applicable, live invariance, and complete repository quality gates.

## 8. Repository workflow

- Keep each batch bounded and independently reviewable.
- Preserve real, replayed, and imagined source distinctions.
- Run targeted and repository-wide quality gates before committing.
- Never push automatically.
