# SeedMind Week 14 Competition Packaging Plan

Date: 2026-07-02
Status: Active — Batch 1 implementation

## Purpose

Week 14 packages the committed SeedMind evidence into a runnable, inspectable demonstration. It is not a new cognitive-capability stage and does not reopen training, growth, routing, or NDNRA integration.

## Authoritative inputs

- `artifacts/week8_reusable_skill/`
- `artifacts/week9_contribution/`
- `artifacts/week11_specialist_growth/`
- `artifacts/week12_consolidation/`
- `artifacts/week13_experiments/`
- `docs/architecture/SeedMind_Week13_Limitations_2026-07-01.md`
- Week 12 rollback checkpoint `dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093`

## Batch 1 deliverables

1. A dependency-light, read-only local Observatory served by Python's standard library.
2. A fixed scripted demonstration with a declared duration below three minutes.
3. A fail-closed claim verifier backed by committed evidence.
4. Deterministic ASCII JSON exports under `artifacts/week14_packaging/`.
5. A Windows operator runbook and narration script.
6. Focused tests for loading, HTTP serving, scope text, scene order, duration, fail-closed verification, and byte-identical exports.

## Mandatory claim boundary

The package must always present these facts together:

- Week 11 narrow specialist result: `52/52`.
- Week 12 broad angular result: `0/32`, with `32/32` oracle-solvable cases.
- Candidate decision: `reject_and_rollback`.
- Rejected specialist: inactive and non-production.
- Authoritative production path: general controller under `production_curiosity`.
- Familiar Week 13 result: `36/100`.
- Broader ball retention result: `15/40`.
- Complete SeedMind has no claimed task advantage over rollback on the familiar suite.
- Week 13 claim C5 remains unsupported.

## Architecture

`seedmind.observatory.data_sources` loads and validates committed artifacts into typed immutable records. `seedmind.observatory.view_model` creates curated snapshot and demo models. `seedmind.observatory.app` provides deterministic exports, claim checks, a standard-library HTTP server, and demo execution. Static HTML, JavaScript, and CSS render the local read-only view.

The Observatory does not execute production actions, mutate checkpoints, retrain models, call network services, or write into authoritative Week 8–13 evidence directories.

## Acceptance criteria

- All claim-verification checks pass against committed evidence.
- The demo manifest has a fixed scene order and total declared duration of at most 180 seconds.
- Fresh exports are byte-identical to committed Week 14 artifacts.
- No `.tmp` export files remain after successful atomic replacement.
- Ruff format, Ruff lint, strict mypy, focused tests, Week 13 regressions, pip check, and `git diff --check` pass.
- The complete repository test suite passes through the durable async pytest command.
- No source or behavior under frozen NDNRA changes.
- No external submission, recording, deployment, or push occurs automatically.

## Deferred Week 14 work

Presentation slides, architecture graphics, market/application copy, a backup recorded demo, and any human-controlled competition submission remain separate later batches.
