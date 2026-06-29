# SeedMind Session Handover — 29 June 2026

Superseded for learned-consequence continuation by
`docs/SeedMind_Session_Handover_2026-06-29_Learned_Consequence_Closure.md`.

Repository: `D:\Github\SeedMind`
CodexBridge repository alias: `seedmind`
Branch: `main`
Working tree before this handover: clean
Git relationship before this handover commit: `main...origin/main [ahead 7]`
Expected relationship after this handover commit: `main...origin/main [ahead 8]`
Latest implementation commit: `f71ee85548d4e33489263d71784f7e15666375b8`
Push status: not pushed
Current stage: Learned Consequence Model
Stage progress: Learned Consequence Model stage complete
Legacy narrow-scope theory-to-integration marker: 98%
Expanded developmental architecture marker: 82%

## 1. New-session continuation instruction

Start from this document and inspect the repository before editing.

Recommended opening prompt:

> Continue SeedMind from `docs/SeedMind_Session_Handover_2026-06-29_Learned_Consequence_Closure.md`. Verify that `main` is clean and ahead of `origin/main`, then plan the bounded-imagination stage only. Preserve imagined evidence as non-factual and non-authoritative. Do not push. Do not begin safe-experiment proposals.

Immediate task:

> Plan the first bounded-imagination sub-batch. Do not implement safe-experiment proposals in that first pass.

## 2. Repository state and recent commits

Current recent sequence:

```text
f71ee85 feat: add bounded contextual consequence transfer
08e39ac feat: add exact-context consequence model
a83f4ba docs: close controlled replay restoration stage
f0d5ba2 feat: restore exact complete brain checkpoints
24bd2b7 fix: narrow durable replay to accepted scope
88943dd fix: retain restoration audit in schema 6
0d53286 feat: persist replay and restore complete checkpoints
8a9d887 feat: execute bounded controlled retention replay
3cd385b feat: add source-aware memory maintenance
25ee2cc feat: make real action consequences affect local competence
8612595 feat: add controlled operation permit lifecycle
84027a3 feat: authorize controlled replay restoration
```

Never push automatically. The user manually pushes when ready:

```powershell
Set-Location "D:\Github\SeedMind"
git push
```

## 3. Product intent that must remain visible

The long-term intent for dreaming is not merely idle activation. It is meant to:

- revisit real memories and learned pathways;
- compare routes and action combinations;
- search for better ideas and more effective routes like a bounded optimiser;
- preserve useful pathways through weak rehearsal;
- generate hypotheses that later require real verification.

Core rule:

```text
dreaming says "this might work"
real evidence says "this did work"
```

Dreaming is not implemented yet. Batch 3 is groundwork: SeedMind first needs trustworthy representations of real action order and real short consequence chains before imagined chains can be safe or meaningful.

Do not introduce a global pride or self-worth scalar. Consequences, competence, prediction accuracy, and confidence remain local to context, action, route, or skill. Harm and safety belong in gates and permissions, not in an emotional reward shortcut.

## 4. Current learned consequence-model stage

Stage plan:

- `docs/SeedMind_Learned_Consequence_Model_Stage_Plan_2026-06-28.md`

Status:

```text
Batch 1 — exact-context single-step consequence model: complete
Batch 2 — bounded contextual transfer: complete
Batch 3 — ordered actions and short consequence chains: complete
Batch 4 — persistence and restart reconstruction: complete
Batch 5 — live integration, acceptance, and closure: complete
```

The expanded developmental architecture marker is now 82% after learned-consequence persistence, live acceptance, restart evidence, failure-path evidence, and closure.

## 5. Batch 1 — exact-context single-step model

Commit:

```text
08e39ace826d42dc33416505ef13630965eecbba
feat: add exact-context consequence model
```

Implementation:

- `src/seedmind/research/ndnra/learned_consequence_model.py`
- `tests/unit/test_ndnra_learned_consequence_model.py`

Public contracts:

- `CalibrationDirection`
- `LearnedConsequenceModelConfig`
- `ConsequenceModelObservation`
- `ConsequencePredictionRequest`
- `ConsequencePrediction`
- `ConsequencePredictionEvaluation`
- `ConsequenceModelUpdate`
- `ContextActionConsequenceRecord`
- `LearnedConsequenceModel`

Behaviour:

- Learns only from unique real transitions.
- Keys evidence by exact `ContextSignature` and exact action.
- Predicts requested effects and the most frequent exact next context.
- Reports effect coverage, evidence coverage, raw confidence, calibrated confidence, uncertainty, and exact supporting real event IDs.
- Repeated consistent outcomes increase bounded support.
- Contradictory outcomes increase dispersion and reduce confidence.
- A prior prediction may be classified as overconfident, calibrated, underconfident, or unknown after a later real outcome.
- Calibration cannot exceed current evidence coverage.
- Zero-confidence effect observations do not increase effect support.
- Missing dimensions remain unknown.
- Partial outcomes may be inspected but cannot calibrate a prediction unless every predicted effect used by the request was observed.
- Exact duplicates are ignored; conflicting reuse of an event identity is rejected.
- Record, observation, effect-dimension, next-context, and request bounds are explicit and atomic.

Important read-only API added for Batch 2:

```python
LearnedConsequenceModel.records
```

It returns a deterministic tuple of exact records. It does not expose a mutable model mapping.

## 6. Batch 2 — bounded contextual transfer

Commit:

```text
f71ee85548d4e33489263d71784f7e15666375b8
feat: add bounded contextual consequence transfer
```

Implementation:

- `src/seedmind/research/ndnra/contextual_consequence_transfer.py`
- `tests/unit/test_ndnra_contextual_consequence_transfer.py`

Public contracts:

- `ConsequencePredictionMode`
- `ContextualTransferConfig`
- `ContextSimilarityEvidence`
- `ContextTransferSourceEvidence`
- `TransferredEffectEvidence`
- `ContextualTransferPrediction`
- `BoundedContextualTransferPolicy`

Non-negotiable transfer rules:

1. Existing exact context-action evidence always wins, including partial and low-confidence exact evidence.
2. Transfer is a separate stateless derived prediction. It never creates a target-context record.
3. Source records must use the exact requested action.
4. Active need identity must match.
5. The action must be available in both source and target contexts.
6. Sensor, human, and resource vector shapes must be positionally compatible.
7. Similarity is explicit and component-level:
   - sensor-bin similarity;
   - available-action overlap;
   - human-state similarity;
   - resource-state similarity;
   - combined weighted similarity.
8. Similarity weights and thresholds are fixed configuration in Batch 2; they are not learned semantics.
9. Source confidence, candidate count, admitted source count, and transferred confidence are bounded.
10. Every transferred effect retains exact source record IDs and supporting real event IDs.
11. Missing source dimensions remain unknown.
12. An exact next context is never transferred across contexts.
13. Multiple consistent sources may add bounded support.
14. Opposing directional sources produce explicit contradiction evidence and may reduce confidence to zero.
15. A single source cannot create broad certainty.
16. Transfer prediction is pure and cannot mutate the exact model.

Default transfer configuration implemented:

```text
minimum_context_similarity = 0.75
transfer_confidence_scale = 0.50
maximum_transferred_confidence = 0.60
minimum_source_confidence = 0.05
maximum_transfer_sources = 4
maximum_contexts_considered = 64
context_bin_distance_scale = 10.0
sensor_weight = 0.50
action_weight = 0.20
human_weight = 0.15
resource_weight = 0.15
neutral_effect_tolerance = 0.05
```

These are bounded research defaults, not scientifically validated final values.

## 7. Batch 3 target — ordered actions and short consequence chains

The stage plan currently requires:

- explicit action order;
- short observed action transitions and combinations;
- finite chain depth, branch count, and effect dimensions;
- exact source-transition provenance;
- protection against repeated reuse of one event multiplying support;
- prediction only, with no action ranking or execution.

Recommended first bounded design to evaluate before editing:

### 7.1 Evidence source

Start with real observed transitions only.

A chain should preserve, for every step:

- exact event ID;
- exact pre-action context;
- exact action code;
- exact observed next context;
- exact observed effects;
- origin, which must be `REAL` for evidence-bearing chains.

Replay, transferred predictions, and imagined outcomes must not become chain evidence.

### 7.2 Exact continuity

For an observed chain:

```text
step[i].next_context == step[i + 1].context
```

Reject disconnected transitions. Do not silently use contextual similarity to bridge a broken real chain in the first sub-batch.

### 7.3 Order identity

Action order is meaningful:

```text
(open_window, start_fan) != (start_fan, open_window)
```

Chain identity should include ordered action codes, ordered source event IDs, start context, and final observed context. Reversing order must create a different identity and must not share support automatically.

### 7.4 Duplicate and correlation protection

- One exact event ID may appear at most once in one chain.
- Re-registering the same chain must not multiply support.
- A conflicting chain identity must be rejected.
- Overlapping chains that reuse source events must remain visibly correlated rather than counted as independent evidence.
- Prefer an explicit source-event union and independent-chain grouping over simple chain-count confidence.

### 7.5 Initial finite bounds

Choose conservative values after inspecting repository conventions. A reasonable first proposal is:

```text
maximum_chain_depth = 3
maximum_chains = 256
maximum_effect_dimensions = 16
maximum_candidates_per_request = 16
```

These are design suggestions, not yet accepted code constants. Record the final decision in the stage plan and repository decision memory.

### 7.6 Prediction boundary

The first chain predictor should:

- accept an exact start context;
- accept an exact ordered action sequence;
- report only chains supported by real observed continuity;
- expose exact source events and coverage;
- report aggregate or final effects with uncertainty;
- expose contradictions between chains;
- remain prediction-only.

Do not add free search over action sequences in Batch 3. Enumerating or optimising candidate routes belongs to later bounded imagination and optimiser work.

### 7.7 Questions the next session must resolve in its plan

Before implementation, decide and document:

1. Whether Batch 3 stores complete observed chain examples or derives chains on demand from single-step observations.
2. How overlapping event sets affect independent support.
3. Whether effects are reported per step, cumulatively, or both.
4. How cumulative effects are bounded when effect semantics are not strictly additive.
5. Whether the final exact context is predicted only for an exact previously observed ordered chain.
6. How contradiction is measured across chains with the same start context and action order.
7. Whether chain calibration is deferred until persistence/live integration or included as a pure in-memory comparison.

Prefer the smallest falsifiable contract. Do not solve persistence, dreaming, or optimiser search in the same commit.

## 8. Batch 3 adversarial tests expected

At minimum, test:

1. A valid two-step real chain preserves exact order and provenance.
2. Reversed action order is a distinct chain.
3. Disconnected contexts are rejected atomically.
4. One event cannot appear twice in one chain.
5. An exact duplicate chain does not multiply support.
6. Conflicting reuse of a chain identity is rejected.
7. Replay, imagined, and transferred data cannot become real chain evidence.
8. Chain depth and total-chain bounds fail before mutation.
9. Missing effect dimensions remain unknown.
10. Contradictory chains lower confidence and remain inspectable.
11. Overlapping chains do not count as fully independent evidence.
12. Unknown action sequences return complete uncertainty.
13. Exact observed order may predict an exact final context; transferred or bridged order may not.
14. Chain prediction does not mutate the single-step model or transfer policy.
15. No ranking, recommendation, execution, persistence, SQLite, timer, worker, rollout, optimiser, or integration dependency exists.
16. Snapshots and identities are deterministic and ASCII-safe.

## 9. Authority and cognition boundaries

These remain mandatory across every next batch:

- Production curiosity is the sole production action authority.
- The consequence model, transfer policy, and future chain model cannot select, rank, recommend, schedule, or execute production actions.
- Prediction objects are evidence reports, not instructions.
- Only unique real outcomes may update factual consequence evidence.
- Replay preserves accessibility but does not manufacture evidence.
- Imagination creates hypotheses, not facts.
- Transferred predictions are non-evidentiary.
- Persistence reconstructs validated state; it is not cognition.
- SQLite remains storage and audit infrastructure only.
- No timers, background workers, queues, automatic replay, automatic restoration, or autonomous experiment execution.
- Failed bounded operations must leave exact prior state or complete safe fallback.
- Missing evidence remains unknown rather than being inferred as neutral success.
- Source identity and contradiction must remain inspectable.

## 10. Controlled replay and restoration status

The preceding controlled replay/restoration stage is complete.

Handover:

- `docs/SeedMind_Controlled_Replay_Restoration_Stage_Handover_2026-06-28.md`

Key closure commit:

```text
a83f4ba081d7e64335c89e4e3a8093cbaef60b15
docs: close controlled replay restoration stage
```

Historical note superseded by the learned-consequence closure handover: brain
persistence is now schema 7 for learned-consequence checkpoints, and the Learned
Consequence Model stage is formally complete.

Do not modify persistence during Batch 3 unless the Batch 3 plan explicitly proves it is unavoidable. The expected boundary is in-memory chain contracts first, persistence later.

## 11. Last complete validation

After Batch 2:

```text
Ruff formatting: 202 files passed
Ruff lint: passed
Mypy: no issues in 202 source files
Pytest: 720 passed
pip check: no broken requirements
git diff --check: passed
```

Re-run the complete repository gates before committing Batch 3:

```text
ruff_format
ruff_check
mypy
pytest
pip_check
git_diff_check
```

Use the repository's allowlisted CodexBridge command IDs rather than inventing shell commands.

## 12. Files to inspect first in the new session

Primary:

- `docs/SeedMind_Session_Handover_2026-06-29.md`
- `docs/SeedMind_Learned_Consequence_Model_Stage_Plan_2026-06-28.md`
- `src/seedmind/research/ndnra/learned_consequence_model.py`
- `src/seedmind/research/ndnra/contextual_consequence_transfer.py`
- `tests/unit/test_ndnra_learned_consequence_model.py`
- `tests/unit/test_ndnra_contextual_consequence_transfer.py`
- `src/seedmind/research/ndnra/__init__.py`

Supporting architecture:

- `docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md`
- `docs/SeedMind_Consequence_Imagination_Stage_Plan_2026-06-28.md`
- `src/seedmind/research/ndnra/contextual_memory.py`
- `src/seedmind/research/ndnra/effects.py`
- `src/seedmind/research/ndnra/composition.py`

## 13. Known cautions for the next implementation

- `ContextSignature` uses quantised positional bins. Matching vector lengths does not prove semantic equivalence; Batch 2 deliberately uses explicit bounded component similarity rather than learned semantics.
- Do not use token Jaccard alone for chain continuity. Real chains require exact context continuity.
- Do not treat the most frequent next context from one step as a verified second-step starting context unless the real event chain proves that continuity.
- Do not sum arbitrary effect dimensions without an explicit semantic rule. Some effects may be cumulative, final-state, maximum, minimum, or non-additive.
- Do not let a chain's depth manufacture confidence. Confidence must derive from unique real support and consistency.
- Do not count transferred estimates or repeated source events as independent chain evidence.
- Do not silently fill partial exact chain evidence from contextual transfer.
- Do not allow the chain subsystem to become an action-sequence search engine yet.
- Keep output deterministic so later persistence can round-trip it safely.

## 14. Completion standard for Batch 3

Batch 3 is complete only when:

- contracts are bounded and documented;
- action order is explicit and identity-stable;
- exact real continuity is enforced;
- all source events remain inspectable;
- duplicate and correlated evidence cannot inflate support;
- contradictions remain visible and reduce confidence;
- unknown sequences remain uncertain;
- no action authority or optimiser behaviour is introduced;
- focused and repository-wide tests pass;
- the stage plan, architecture, master plan, session handover, decision memory, and wiki are updated as justified;
- one bounded commit is created;
- nothing is pushed automatically.
