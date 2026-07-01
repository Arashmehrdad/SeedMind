# SeedMind

SeedMind is a developmental intelligence runtime.

The competition MVP begins as a small symbolic agent with primitive actions,
prediction, curiosity, ambition, human apprenticeship, memory, skill formation,
controlled specialist growth, and retention-gated consolidation.

## Current phase

SeedMind continues on its original main-product roadmap. Original Week 9 is closed through verified human contribution, grounded outcome verification, and evidence-gated support reduction.

NDNRA is frozen inside this repository at source baseline `b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a` and will continue, if at all, as a separate project. Its source, tests, documents, ADRs, and artifacts remain only as a preserved research snapshot and extraction source.

For future SeedMind work:

- `production_with_ndnra_shadow` is not the canonical operating mode;
- NDNRA comparison is not a product acceptance requirement;
- no NDNRA Stage 9 or component promotion is authorised here;
- no new SeedMind code may depend on NDNRA;
- historical NDNRA runners and artifacts remain available only for reproducibility;
- original Week 10 capacity diagnosis proceeds without NDNRA participation.

See `docs/architecture/NDNRA_Freeze_and_Extraction_Boundary_2026-07-01.md` for the active boundary.

## Current main-roadmap evidence

SeedMind Week 9 is closed by the main `seedmind.contribution` implementation:

- typed human requests bind the target capability, expected outcome, object, target, context, permission, and verification rule;
- capability checks distinguish unavailable, unproven, degraded, context-mismatched, and verified states;
- contribution success requires grounded runtime state and actual-transition evidence;
- self-report, imagination, producer-verifier agreement, and NDNRA agreement cannot certify success;
- support reduces from Level 4 to Level 3 only after five verified independent familiar successes, at least `0.80` success, and three distinct familiar contexts;
- two consecutive grounded familiar failures restore Level 4, and re-promotion requires five fresh post-regression successes;
- deterministic Default evaluation completed `10/12` requests for an independent success rate of `0.8333`;
- deterministic solvable Default evaluation completed `10/10` tasks, while two intentionally blocked scenarios remained honest failures;
- historical NDNRA comparison artifacts are preserved for audit but are not treated as competence evidence about the complete NDNRA architecture or as future SeedMind product gates;
- all `172` executed primitive actions remained Default actions;
- Week 8 discovery delta, compilation, training, and component promotion remain `0`;
- production, verification, support, and NDNRA authority violations remain `0`.

Run the deterministic gate with:

```text
.\.venv\Scripts\python.exe scripts\run_week9_contribution.py
```

Week 9 evidence is documented in `docs/architecture/SeedMind_Week9_Contribution_Evidence_2026-06-30.md`. Historical comparison artifacts remain under `artifacts/week9_contribution/`, while the active NDNRA freeze is documented in `docs/architecture/NDNRA_Freeze_and_Extraction_Boundary_2026-07-01.md`. Week 8 remains closed separately in `docs/architecture/SeedMind_Week8_Reusable_Skill_Evidence_2026-06-30.md`.

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
