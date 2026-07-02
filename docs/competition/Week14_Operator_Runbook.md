# SeedMind Week 14 Operator Runbook

## Scope

This runbook starts a local, read-only presentation of committed Week 8–13 evidence. It does not train SeedMind, activate the rejected specialist, alter the rollback checkpoint, or use NDNRA as a production component.

## Prerequisites

- Windows 11
- Repository at `D:\Github\SeedMind`
- Repository-local Python environment at `.venv`
- Current working directory set to the repository root

## 1. Verify public claims

```powershell
.\.venv\Scripts\python.exe scripts\verify_week14_claims.py
```

Expected result:

```text
Week 14 claim verification: pass (0 failing checks)
```

Stop the demonstration if verification fails. Do not work around a missing, malformed, contradictory, or mismatched artifact.

## 2. Rehearse the scripted demo without delays

```powershell
.\.venv\Scripts\python.exe scripts\run_week14_demo.py --no-wait
```

The manifest contains seven fixed scenes with a declared total duration below 180 seconds. The narration must retain the failed broad-transfer result and all stated limitations.

## 3. Start the local Observatory

```powershell
.\.venv\Scripts\python.exe scripts\run_week14_observatory.py
```

Open:

```text
http://127.0.0.1:8000/
```

Stop the server with `Ctrl+C`.

To regenerate only the deterministic snapshot without starting the server:

```powershell
.\.venv\Scripts\python.exe scripts\run_week14_observatory.py --export-only
```

## 4. Run the timed narration

```powershell
.\.venv\Scripts\python.exe scripts\run_week14_demo.py
```

The command prints each scene, its evidence references, and waits for the scene's declared duration.

## Evidence to show

1. Authority and scope: the Week 12 rollback checkpoint is authoritative.
2. Reusable skill and contribution: bounded Week 8 and Week 9 evidence.
3. Ambition and apprenticeship: bounded symbolic Week 13 ablations.
4. Specialist result: Week 11 `52/52` narrow evidence paired with Week 12 `0/32` broad transfer.
5. Rollback: candidate `reject_and_rollback`, specialist inactive, router unregistered.
6. Claims: C1–C4 supported; C5 unsupported.
7. Limitations: symbolic Nursery, `36/100` familiar result, `15/40` broader ball retention, no claimed task advantage over rollback.

## Failure handling

- Claim verification failure: stop and inspect `artifacts/week14_packaging/claim_verification_report.json`.
- Missing evidence: restore the committed artifact; do not substitute a hand-authored value.
- Port 8000 unavailable: rerun with `--port <unused-port>`.
- Browser unavailable: use the console demo and committed JSON artifacts.
- Demonstration interruption: restart from scene 1 so the narrow success is never separated from the broad failure and rollback decision.

## Non-authorised actions

Do not activate the rejected specialist, register its router, modify the authoritative checkpoint, retrain or regenerate Weeks 8–13, claim general intelligence, omit C5, push automatically, deploy externally, or submit to a competition from this workflow.
