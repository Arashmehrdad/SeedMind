# SeedMind Week 14 Competition Packaging Evidence

Date: 2026-07-02
Stage: Week 14 Batch 1 — Observatory, scripted demo, and claim verification
Decision: Accepted — Week 14 Batch 1 closed

## Scope

This batch packages committed Week 8–13 evidence. It does not add cognitive capability, train a specialist, alter routing, modify a production checkpoint, reopen NDNRA, deploy externally, record a video, create presentation slides, or submit an application.

## Implemented surface

- `src/seedmind/observatory/data_sources.py`: typed fail-closed loaders for authoritative evidence.
- `src/seedmind/observatory/view_model.py`: deterministic Observatory and demo view models.
- `src/seedmind/observatory/app.py`: local read-only HTTP server, deterministic exports, scripted demo execution, and public-claim verification.
- `src/seedmind/observatory/static/`: dependency-light HTML, JavaScript, and CSS.
- `scripts/run_week14_observatory.py`: local server and export-only entry point.
- `scripts/run_week14_demo.py`: timed and `--no-wait` demo entry point.
- `scripts/verify_week14_claims.py`: fail-closed claim-verification entry point.
- `docs/competition/Week14_Operator_Runbook.md`: third-party operating instructions.
- `docs/competition/Week14_Demo_Script.md`: fixed 166-second narration.

## Derived artifacts

- `artifacts/week14_packaging/observatory_snapshot.json`
- `artifacts/week14_packaging/demo_manifest.json`
- `artifacts/week14_packaging/claim_verification_report.json`

The committed artifacts were rebuilt from the current deterministic builders and verified byte-stable. Fresh-export tests exercise the normal atomic writer in isolated temporary directories.

## Claim-verification result

The machine-readable report records `all_passed: true`, `failure_count: 0`, and checkpoint:

`dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093`

The verifier checks:

1. Week 12 and Week 13 use the same authoritative rollback checkpoint.
2. Week 12 checkpoint bytes and Week 13 aggregate/claim bytes match the committed Week 13 reproducibility manifest.
3. Production authority remains `production_curiosity` with the general controller only.
4. The rejected specialist remains inactive and non-production.
5. Week 11 narrow `52/52` is inseparable from Week 12 broad `0/32`, `32/32` oracle solvability, and `reject_and_rollback`.
6. C1–C4 remain supported and C5 remains unsupported.
7. The complete condition makes no familiar-task advantage claim over rollback.
8. The public package retains the symbolic and empirical limitations.

## Demo evidence

The demo manifest has seven fixed scenes and a declared duration of 166 seconds:

1. Authority and scope.
2. Reusable skill and contribution.
3. Ambition and apprenticeship.
4. Narrow specialist rejection.
5. Rollback checkpoint.
6. Week 13 claim status.
7. Limitations and close.

The manifest supports `--no-wait` validation and includes exact evidence references for every scene.

## Preserved limitations

- Familiar Week 13 result: `36/100`.
- Broader ball-retention result: `15/40`.
- Narrow specialist evidence: `52/52`.
- Broad angular transfer: `0/32` despite `32/32` oracle-solvable cases.
- Complete SeedMind has no claimed task-success advantage over rollback on the familiar suite.
- The environment is a deterministic symbolic Nursery, not robotics or open-world deployment.
- No general-intelligence, robust real-world transfer, or accepted production specialist-growth claim is authorised.

## Validation

```text
ruff format --check .: 323 files already formatted
ruff check .: passed
mypy .: no issues in 323 source files
python -m pip check: no broken requirements
git diff --check: passed; line-ending warnings only
pytest -q: 1200 passed in 403.98s (0:06:43)
durable async run: 20260702T034211Z_project_command_56dd91b8
```

## Acceptance boundary

Batch 1 is closed because the durable full-suite run passed with `1200 passed in 403.98s`, all static gates passed, the claim verifier reports zero failures, the scripted demonstration remains within 166 seconds, and the live continuation plan records the result. Later Week 14 batches may create presentation assets and a backup recording workflow, but external submission remains human-controlled and no later packaging task may change the authority or scientific claim boundaries above.
