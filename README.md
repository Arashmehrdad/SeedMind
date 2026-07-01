# SeedMind

SeedMind is a developmental intelligence runtime.

The competition MVP begins as a small symbolic agent with primitive actions,
prediction, curiosity, ambition, human apprenticeship, memory, skill formation,
controlled specialist growth, and retention-gated consolidation.

## Current phase

SeedMind continues on its original main-product roadmap. Original Week 10 is closed through corrected grounded developmental blockage diagnosis, learning-progress windows, diagnostic-ladder evidence, and one non-authoritative growth proposal for later Week 11 investigation.

NDNRA is frozen inside this repository at source baseline `b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a` and will continue, if at all, as a separate project. Its source, tests, documents, ADRs, and artifacts remain only as a preserved research snapshot and extraction source.

For future SeedMind work:

- `production_with_ndnra_shadow` is not the canonical operating mode;
- NDNRA comparison is not a product acceptance requirement;
- no NDNRA Stage 9 or component promotion is authorised here;
- no new SeedMind code may depend on NDNRA;
- historical NDNRA runners and artifacts remain available only for reproducibility;
- original Week 11 specialist growth remains the next stage and has not started.

See `docs/architecture/NDNRA_Freeze_and_Extraction_Boundary_2026-07-01.md` for the active boundary.

## Current main-roadmap evidence

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

## Environment

- Python 3.12
- PyTorch
- Gymnasium
- Windows 11
- NVIDIA RTX 4060 Laptop GPU

## Quality checks

Run Ruff, Mypy, Pytest, and pip check before completing changes.
