# SeedMind

SeedMind is a developmental intelligence runtime.

The competition MVP begins as a small symbolic agent with primitive actions,
prediction, curiosity, ambition, human apprenticeship, memory, skill formation,
controlled specialist growth, and retention-gated consolidation.

## Current phase

The authorised NDNRA Developmental Network v0.2 research programme is closed through Stage 8. The main SeedMind product roadmap has now closed Week 8 with the first reusable product skill, `approach_and_push`, while NDNRA continues beside it in non-authoritative shadow mode.

The canonical operating mode is `production_with_ndnra_shadow`:

- production curiosity selects the only action executed by the runtime;
- NDNRA observes the same state, emits an optional internal suggestion, and learns from the actual grounded transition;
- agreements and disagreements are recorded for comparison;
- the production action is always retained;
- NDNRA has no execution, scheduling, replacement, promotion, or production action authority;
- automatic component promotion is disabled;
- Stage 9 remains unauthorised.

A specific NDNRA component may be considered later only after repeated multi-task evidence, resource and interference checks, rollback and kill-switch coverage, and a separate accepted ADR. The original SeedMind plan, including reusable-skill formation, remains the product and MVP spine.

See `docs/architecture/SeedMind_NDNRA_Parallel_Operating_Model_2026-06-30.md` for the full operating boundary.

## Current main-roadmap evidence

SeedMind Week 8 is closed by the main `seedmind.skills` implementation:

- `approach_and_push` is compiled from repeated grounded production episodes;
- frozen evaluation reuses the compiled skill across 20 unseen deterministic eligible starts;
- evaluation success rate is `1.0000`;
- primitive rediscovery baseline success rate is `1.0000`;
- evaluation discovery count remains `0`;
- production action-authority violations remain `0`;
- NDNRA automatic promotions remain `0`.

Run the deterministic gate with:

```text
.\.venv\Scripts\python.exe scripts\run_week8_reusable_skill.py
```

Evidence is documented in `docs/architecture/SeedMind_Week8_Reusable_Skill_Evidence_2026-06-30.md`.

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
