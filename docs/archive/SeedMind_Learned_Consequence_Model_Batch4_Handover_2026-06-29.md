# SeedMind Learned Consequence Model Batch 4 Handover

Date: 29 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Batch: Learned Consequence Model Batch 4
Status: complete in the commit containing this handover
Push status: not pushed

## Outcome

Batch 4 adds restart-safe learned-consequence persistence.

Brain persistence advances to schema version 7 and can carry an explicit
`NDNRALearnedConsequenceCheckpoint`. The checkpoint stores only validated learned
consequence state and reconstructs the in-memory single-step model, contextual-transfer
configuration, and observed-chain model exactly after restart.

## Implemented contracts

- `LEARNED_CONSEQUENCE_SCHEMA`
- `LEARNED_CONSEQUENCE_SCHEMA_VERSION`
- `NDNRALearnedConsequenceCheckpoint`

Implementation:

- `src/seedmind/research/ndnra/learned_consequence_persistence.py`
- `src/seedmind/research/ndnra/persistence.py`
- restore paths in:
  - `src/seedmind/research/ndnra/learned_consequence_model.py`
  - `src/seedmind/research/ndnra/contextual_consequence_transfer.py`
  - `src/seedmind/research/ndnra/observed_consequence_chains.py`
  - `src/seedmind/research/ndnra/__init__.py`

Tests:

- `tests/unit/test_ndnra_learned_consequence_persistence.py`

## Design decisions

- The checkpoint stores validated consequence model observations, exact records, raw
  weighted effect statistics, calibration evaluation provenance and totals,
  next-context counts, transfer
  configuration, observed chains, and source-event provenance.
- Brain schemas 1 through 6 migrate to an explicit empty learned-consequence checkpoint.
- Schema 6 active-state checksum verification remains compatible and does not include
  the learned-consequence checkpoint.
- Schema 7 active-state checksum verification includes the learned-consequence
  checkpoint snapshot.
- Restore paths reject non-canonical snapshots instead of silently normalizing them.
- Loading cannot create predictions, events, evidence, confidence, chains, replay,
  restoration, timers, workers, SQLite lookup, or action authority.
- Failed saves leave the previous checkpoint intact.

## Validation

Focused validation:

```text
.venv\Scripts\python.exe -m pytest tests\unit\test_ndnra_learned_consequence_model.py tests\unit\test_ndnra_observed_consequence_chains.py tests\unit\test_ndnra_learned_consequence_persistence.py -q --basetemp .pytest_tmp\batch4-focus
44 passed

.venv\Scripts\python.exe -m mypy src\seedmind\research\ndnra\learned_consequence_model.py src\seedmind\research\ndnra\contextual_consequence_transfer.py src\seedmind\research\ndnra\observed_consequence_chains.py src\seedmind\research\ndnra\learned_consequence_persistence.py src\seedmind\research\ndnra\persistence.py tests\unit\test_ndnra_learned_consequence_persistence.py
Success: no issues found in 6 source files

.venv\Scripts\python.exe -m pytest tests\unit\test_ndnra_persistence.py tests\unit\test_ndnra_consolidation_persistence.py tests\unit\test_ndnra_proposal_lifecycle_brain_persistence.py tests\unit\test_ndnra_consolidation_execution_persistence.py tests\unit\test_ndnra_controlled_replay_persistence.py tests\unit\test_ndnra_controlled_checkpoint_restoration.py tests\unit\test_ndnra_learned_consequence_persistence.py -q --basetemp .pytest_tmp\batch4-persistence
57 passed

.venv\Scripts\python.exe -m pytest tests\unit\test_ndnra_learned_consequence_persistence.py tests\unit\test_ndnra_consolidation_execution_durable_commit.py -q --basetemp .pytest_tmp\batch4-durable
21 passed

.venv\Scripts\python.exe -m pytest tests\unit\test_ndnra_learned_consequence_persistence.py tests\unit\test_ndnra_learned_consequence_model.py -q --basetemp .pytest_tmp\batch4-calibration
27 passed
```

Repository gates:

```text
.venv\Scripts\python.exe -m ruff format
2 files reformatted, 204 files left unchanged

.venv\Scripts\python.exe -m ruff check --fix
Found 2 errors (2 fixed, 0 remaining).

.venv\Scripts\python.exe -m ruff check
All checks passed!

.venv\Scripts\python.exe -m mypy
Success: no issues found in 189 source files

.venv\Scripts\python.exe -m pytest -q --basetemp .pytest_tmp\full
749 passed

.venv\Scripts\python.exe -m pip check
No broken requirements found.

git diff --check
passed
```

## Progress

The expanded developmental architecture marker advances from 79% to 80%.

Batch 4 is necessary restart-safety evidence, but it does not complete live integration,
full stage acceptance, bounded imagination, imagined route optimisation, safe experiment
promotion, or a 100% architecture claim.

## Next batch

Next: Batch 5, live integration, acceptance, and closure.

Batch 5 must compare model-enabled shadow operation with an identical control,
demonstrate real pre-action prediction followed by later outcome comparison, show
uncertainty reduction under consistent real evidence, show confidence reduction under
contradiction, prove context-local failure consequences, and demonstrate no production
action authority or cognitive SQLite dependency.
