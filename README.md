# SeedMind

SeedMind is a developmental intelligence runtime.

The competition MVP begins as a small symbolic agent with primitive actions,
prediction, curiosity, ambition, human apprenticeship, memory, skill formation,
controlled specialist growth, and retention-gated consolidation.

## Current phase

Original SeedMind Weeks 11–13 are closed. Week 11 produced a narrow angular specialist result of `52/52`; Week 12 then measured `0/32` broad transfer on `32/32` oracle-solvable cases, rejected the candidate, and restored rollback checkpoint `dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093` as the sole production controller authority. Week 13 completed preregistered baselines, ablations, repeated seeds, charts, limitations, and reproducibility evidence. Four bounded claims passed and broad angular transfer remained explicitly unsupported.

Week 14 competition packaging is active. Its Observatory, demo, and claim verifier are read-only presentation layers over committed evidence; they do not train models, activate the rejected specialist, change action authority, or add cognitive capability.

NDNRA remains frozen inside this repository at source baseline `b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a`. No Week 14 code may depend on it or grant it production authority. See `docs/architecture/NDNRA_Freeze_and_Extraction_Boundary_2026-07-01.md`.

## Historical Week 10 closure evidence

SeedMind Week 10 is closed by the hardened main `seedmind.growth` implementation.

Correction note: the original `13140df` Week 10 evidence used scripted diagnostic timelines and was not valid grounded evidence. Commit `ea15047` replaced those timelines with executed episodes, but a follow-up audit found that scenario seeds still produced identical states, replay and demonstration plans were assigned before evidence derivation, several variant labels shared the frozen policy, the prediction gate accepted any non-negative error, and teacher traces shifted learner attempt indexes. The current implementation corrects those remaining integrity defects.

- angular movable objects now have raw flat-contact push resistance while familiar round-object behavior is retained;
- policy-facing observations expose numeric geometry, movability, and shape channels, not a privileged `cube` label;
- learning-progress windows use predeclared thresholds: window size `4`, minimum `3` windows, minimum `12` attempts, and improvement threshold `0.10`;
- every active Week 10 `LearningAttempt` references a grounded episode trace with primitive actions, transition outcomes, state digests, measured progress, prediction evidence, and trace digest;
- deterministic seeds now produce multiple distinct initial Nursery states rather than changing identifiers only;
- replay-influenced action plans are derived from retrieved source traces, demonstration-guided plans are derived from the executed teacher trace, and the sustained strategy variants have distinct primitive-action signatures;
- prediction evidence must be present and remain within the declared mean-absolute-error ceiling of `0.05`;
- early evidence remains `insufficient_evidence` and cannot produce growth;
- temporary cube-like failure recovers to `improving` after executable strategy, grounded replay, and measured teacher-demonstration evidence, with no growth proposal;
- sustained cube-like blockage remains plateaued after executed variants, grounded replay, and a reachability-proving teacher trace, then produces exactly one proposal;
- ambiguous, impossible, unsafe, or resource-limited cases stop early and do not masquerade as capacity limits;
- the proposal status is `proposed_not_authorised`, with `candidate.created=false`;
- no specialist, router, parameter growth, production mutation, Week 11 gate, or NDNRA dependency is introduced;
- frozen Week 8 skill record hash is preserved.

Run the deterministic gate with:

```text
.\.venv\Scripts\python.exe scripts\run_week10_capacity_diagnosis.py
```

Week 10 evidence is documented in `docs/architecture/SeedMind_Week10_Capacity_Diagnosis_Evidence_2026-07-01.md`, with deterministic artifacts under `artifacts/week10_capacity_diagnosis/`, including `grounded_episode_traces.json`. The superseded scripted `13140df` artifacts are preserved under `artifacts/week10_capacity_diagnosis/superseded_scripted_evidence/`. Week 9 and Week 8 remain closed separately, while the active NDNRA freeze is documented in `docs/architecture/NDNRA_Freeze_and_Extraction_Boundary_2026-07-01.md`.

## Week 14 competition packaging

Verify the public claim boundary:

```powershell
.\.venv\Scripts\python.exe scripts\verify_week14_claims.py
```

Run the fixed narration without delays:

```powershell
.\.venv\Scripts\python.exe scripts\run_week14_demo.py --no-wait
```

Start the local read-only Observatory:

```powershell
.\.venv\Scripts\python.exe scripts\run_week14_observatory.py
```

Open `http://127.0.0.1:8000/`. Full instructions are in `docs/competition/Week14_Operator_Runbook.md`. The presentation must retain the `36/100` familiar result, `15/40` broader retention result, narrow `52/52` paired with broad `0/32`, the `reject_and_rollback` decision, and unsupported claim C5.

## Development order

1. Environment
2. Prediction
3. Body discovery
4. Curiosity
5. Ambition
6. Human apprenticeship
7. Memory
8. Skill formation
9. Contribution
10. Capacity diagnosis
11. Specialist growth
12. Consolidation
13. Competition evidence
14. Competition packaging

## Environment

- Python 3.12
- PyTorch
- Gymnasium
- Windows 11
- NVIDIA RTX 4060 Laptop GPU

## Quality checks

Run Ruff, Mypy, Pytest, and pip check before completing changes.
