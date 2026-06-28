# SeedMind Learned Consequence Model Batch 3 Handover

Date: 29 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Batch: Learned Consequence Model Batch 3
Status: complete in the commit containing this handover
Push status: not pushed

## Outcome

Batch 3 adds bounded in-memory observed consequence chains.

SeedMind can now store exact real ordered action-chain examples and answer prediction
requests for an exact start context plus an exact ordered action sequence. The chain
model is research-only, prediction-only, and has no production action authority.

## Implemented contracts

- `ObservedConsequenceChainConfig`
- `ObservedConsequenceChainStep`
- `ObservedConsequenceChain`
- `ConsequenceChainPredictionRequest`
- `ConsequenceChainStepPrediction`
- `ConsequenceChainCorrelationGroup`
- `ConsequenceChainPrediction`
- `ObservedConsequenceChainUpdate`
- `ObservedConsequenceChainModel`

Implementation:

- `src/seedmind/research/ndnra/observed_consequence_chains.py`
- `src/seedmind/research/ndnra/__init__.py`

Tests:

- `tests/unit/test_ndnra_observed_consequence_chains.py`

## Design decisions

- Batch 3 stores complete observed chain examples instead of deriving chains on demand.
- Evidence-bearing chain steps must have `ExperienceOrigin.REAL`.
- Adjacent steps must satisfy exact context continuity:

```text
step[i].next_context == step[i + 1].context
```

- Chain identity uses exact start context, ordered action codes, ordered source event IDs,
  and exact final observed context.
- Reversed action order is a separate identity and does not share support.
- One event ID may appear at most once within one chain.
- Reusing an event ID with a different transition is rejected.
- Re-registering an identical chain is a duplicate and does not multiply support.
- Overlapping source-event sets form deterministic correlation groups.
- Each connected correlation group counts once for independent support.
- Predictions report per-step requested effect estimates only.
- Batch 3 does not sum arbitrary effects across steps.
- Exact final context is predicted only from exact observed ordered-chain evidence.
- Chain calibration is deferred to persistence/live integration.

Repository decision memory:

- `mem_0e51892c9ca7496bbbc9599f1cc44366`

## Authority boundary

Batch 3 does not provide:

- persistence;
- live production integration;
- action selection;
- action ranking;
- recommendations;
- route search;
- optimisation;
- execution;
- SQLite cognition;
- timers;
- workers;
- replay;
- restoration;
- dreaming;
- safe experiment promotion.

Prediction objects are evidence reports only.

## Validation

Focused validation:

```text
.venv\Scripts\python.exe -m pytest tests\unit\test_ndnra_observed_consequence_chains.py -q
20 passed

.venv\Scripts\python.exe -m pytest tests\unit\test_ndnra_learned_consequence_model.py tests\unit\test_ndnra_contextual_consequence_transfer.py tests\unit\test_ndnra_observed_consequence_chains.py -q
53 passed

.venv\Scripts\python.exe -m mypy src\seedmind\research\ndnra\observed_consequence_chains.py tests\unit\test_ndnra_observed_consequence_chains.py
Success: no issues found in 2 source files
```

Repository gates through CodexBridge:

```text
ruff_format
204 files left unchanged

ruff_check
All checks passed!

mypy
Success: no issues found in 204 source files

pytest
740 passed

pip_check
No broken requirements found.

git_diff_check
passed with exit code 0
warning: in the working copy of '.codexbridge/wiki/manifest.json', LF will be replaced by CRLF the next time Git touches it
```

CodexBridge wiki refresh:

```text
status: refreshed
source_file_count: 262
scan_truncated: false
```

## Progress

The expanded developmental architecture marker remains 79%.

Batch 3 is necessary evidence, but it does not complete restart-safe persistence, live
integration, full failure-path acceptance, or stage closure. Do not advance the marker
or claim 100% from this batch alone.

## Next batch

Next: Batch 4, persistence and deterministic restart reconstruction.

Batch 4 must persist only validated learned-consequence state, preserve duplicate and
source-event protection across restart, migrate older schemas to explicit empty
consequence-model state, and fail safely on corrupt, partial, duplicated, oversized, or
conflicting persisted data. It must not make SQLite or persistence a cognitive lookup or
operation trigger.
