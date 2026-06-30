# SeedMind

SeedMind is a developmental intelligence runtime.

The competition MVP begins as a small symbolic agent with primitive actions,
prediction, curiosity, ambition, human apprenticeship, memory, skill formation,
controlled specialist growth, and retention-gated consolidation.

## Current phase

The authorised NDNRA Developmental Network v0.2 research programme is closed through Stage 8. The main SeedMind product roadmap has closed corrected Week 9 by using the frozen `approach_and_push` skill for verified human contribution and evidence-gated support reduction while collecting fair Default-vs-goal-conditioned-NDNRA comparative evidence.

The canonical operating mode is `production_with_ndnra_shadow`:

- production curiosity selects the only action executed by the runtime;
- NDNRA receives the same typed contribution goal and relational pre-action state context, emits an optional internal suggestion, and learns only in sandbox/adaptive diagnostics from NDNRA-executed transitions;
- frozen held-out counterfactual comparisons score the fixed Default action and the NDNRA proposal from cloned states without evaluation learning;
- frozen and adaptive NDNRA-only rollouts measure task completion without giving NDNRA production authority;
- the production action is always retained;
- NDNRA has no execution, scheduling, replacement, promotion, or production action authority;
- automatic component promotion is disabled;
- Stage 9 remains unauthorised.

A specific NDNRA component may be considered later only after repeated multi-task evidence, resource and interference checks, rollback and kill-switch coverage, and a separate accepted ADR. The original SeedMind plan, including reusable-skill formation, remains the product and MVP spine.

See `docs/architecture/SeedMind_NDNRA_Parallel_Operating_Model_2026-06-30.md` for the full operating boundary.

## Current main-roadmap evidence

SeedMind Week 9 is closed by the main `seedmind.contribution` implementation:

- typed human requests bind the target capability, expected outcome, object, target, context, permission, and verification rule;
- capability checks distinguish unavailable, unproven, degraded, context-mismatched, and verified states;
- contribution success requires grounded runtime state and actual-transition evidence;
- self-report, imagination, producer-verifier agreement, and NDNRA agreement cannot certify success;
- support reduces from Level 4 to Level 3 only after five verified independent familiar successes, at least `0.80` success, and three distinct familiar contexts;
- two consecutive grounded familiar failures restore Level 4, and re-promotion requires five fresh post-regression successes;
- deterministic Default evaluation completed `10/12` requests for an independent success rate of `0.8333`;
- fair comparison integrity, Default competence, blocked-scenario handling, authority containment, and Week 9 main-milestone gates pass separately;
- NDNRA competence is reported separately and currently fails honestly;
- held-out solvable completion is Default `10/10`, frozen NDNRA `0/10`, and adaptive NDNRA `0/10`;
- intentionally blocked scenarios are reported separately as `2/2` Default honest failures and `2/2` NDNRA honest failures;
- counterfactual task-progress categories are Default better `23`, NDNRA better `0`, equivalent `85`, generic-score-only `64`, and not comparable `0`;
- all `172` executed primitive actions remained Default actions;
- Week 8 discovery delta, compilation, training, and component promotion remain `0`;
- production, verification, support, and NDNRA authority violations remain `0`.

Run the deterministic gate with:

```text
.\.venv\Scripts\python.exe scripts\run_week9_contribution.py
```

Evidence is documented in `docs/architecture/SeedMind_Week9_Contribution_Evidence_2026-06-30.md`, with the fair comparison timeline in `artifacts/week9_contribution/default_vs_ndnra_fair_comparison.json` and the superseded old comparison marker in `artifacts/week9_contribution/default_vs_ndnra_comparison.json`. Week 8 remains closed separately in `docs/architecture/SeedMind_Week8_Reusable_Skill_Evidence_2026-06-30.md`.

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
