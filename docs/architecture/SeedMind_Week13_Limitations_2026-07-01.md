# SeedMind Week 13 Limitations and Claim Boundaries

**Date:** 1 July 2026  
**Status:** Authoritative Week 13 limitation boundary

## 1. Environment boundary

All Week 13 evidence comes from a small, symbolic, deterministic Nursery environment.

The environment uses discrete states, fixed primitive actions, bounded step budgets, designed scenario families, and reproducible seed-derived initial conditions. It does not include visual perception, physical dynamics, sensor noise, language, open-world uncertainty, internet access, or real human interaction.

Repeated success in this environment does not establish equivalent performance in robotics, games, software control, or other real-world domains.

## 2. Intelligence boundary

Week 13 does not demonstrate general intelligence, consciousness, sentience, human-like understanding, or open-ended autonomous development.

It demonstrates bounded engineering mechanisms:

- persistent ambition state;
- symbolic human apprenticeship and help resolution;
- reuse of a compiled object-pushing controller;
- evidence-gated structural-growth governance;
- deterministic rollback and auditability.

These mechanisms are components of the SeedMind hypothesis, not proof of artificial general intelligence.

## 3. Prediction boundary

SeedMind prediction in the current MVP is mainly local action-outcome prediction in a symbolic environment.

The evidence does not show broad world modelling, long-horizon causal reasoning, semantic understanding, or reliable prediction outside the Nursery transition rules.

## 4. Production-controller limitation

The rollback production controller achieved `36/100` on the Week 13 familiar round-object suite.

It also achieved only `15/40` on the broader Week 12 ball stress suite. The routed comparison produced the same `15/40`, with exact action and outcome trace equality and zero specialist selections.

Therefore:

- growth did not damage familiar behaviour;
- the controller is better than the declared random and reactive baselines on the Week 13 suite;
- the controller is not broadly reliable across all evaluated round-object layouts;
- a `36%` or `37.5%` result must not be described as mastery.

## 5. Specialist limitation

The rejected angular specialist achieved `52/52` on its original and mirrored or rotated narrow cohorts, but `0/32` on the broader solvable transfer suite.

An independent grounded search found solutions for all `32/32` broad cases within the same action budget. The failure is therefore a specialist capability failure, not evidence that the test layouts were impossible.

The specialist must not be described as a broadly transferable angular-object controller. Its proven scope is limited to the designed Week 11 families.

## 6. Repeated-seed limitation

The familiar task used 100 unique deterministic scenarios across five disjoint replications. Ambition and apprenticeship each used five deterministic replications.

Repeated seeds improve confidence that the implementation behaves consistently across the declared scenario distribution. They do not prove:

- real-world generalisation;
- robustness to continuous noise;
- robustness to adversarial or unexpected environments;
- transfer to unseen task classes;
- statistical independence from the scenario generator's design assumptions.

Zero variance in ambition and apprenticeship metrics reflects clean symbolic test cases and deterministic logic. It should not be interpreted as perfect robustness in natural human interaction.

## 7. Baseline limitation

The random primitive and fixed reactive baselines both scored `0/100`.

The random baseline is a floor. The reactive baseline is intentionally simple and stateless, and its failure shows that the evaluated layouts require more than its direct greedy heuristic. Week 13 does not establish superiority over strong planning, reinforcement-learning, imitation-learning, or large fixed-model baselines.

A future benchmark should include stronger parameter-matched and planner-based alternatives.

## 8. Ablation interpretation boundary

The no-ambition and no-human-teaching ablations isolate explicit SeedMind mechanisms while keeping the production controller fixed.

They support claims about persistence, teaching resolution, and support progression. They do not show that those mechanisms improve the controller's familiar-task success in this experiment.

The growth-without-replay condition is a decision ablation. It shows that relying on narrow evidence would have produced one invalid promotion. It is not a separately trained production system and does not prove that replay itself would repair the rejected specialist.

## 9. Checkpoint and authority boundary

The only authoritative production reference is the Week 12 rollback checkpoint:

`dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093`

It contains the general controller only, with the specialist inactive and the router unregistered.

The rejected specialist checkpoint:

`3d86d365496f16678363f9348280c9c102b1bfa98e3a000e23be775a989188b2`

is experimental comparison evidence only.

Rejected components remain experimental. They may not be presented as production-active, accepted growth, validated broad transfer, or part of the authoritative Week 14 action path.

## 10. Reproducibility boundary

The artifact package records source hashes, input hashes, seed declarations, payload hashes, and a deterministic aggregate digest. This supports exact reproduction on the current code, committed inputs, and compatible runtime.

It does not guarantee identical execution across arbitrary operating systems, Python versions, dependency versions, or future code changes unless those factors are also frozen and verified.

The complete repository pytest suite was subsequently executed through the durable async command path with isolated per-run temporary directories. It completed successfully with `1189 passed in 464.23s (0:07:44)`, exit code `0`, under run ID `20260702T022842Z_project_command_dafb975a`. This validates the current repository state but does not expand the scientific claim boundary beyond the declared symbolic experiments.

## 11. Week 14 claim boundary

Week 14 may show that, in the deterministic symbolic Nursery:

- a reusable skill beats the declared simple baselines;
- ambition persists across episodes and reload;
- human teaching resolves justified help and supports reduced dependence;
- broad transfer testing can reject an overfitted specialist;
- rollback preserves the authoritative production controller;
- every decision is backed by machine-readable evidence.

Week 14 must not claim:

- general intelligence;
- consciousness or emotion;
- broad real-world transfer;
- robust object manipulation;
- broad angular competence;
- successful production specialist growth;
- that complete SeedMind outperformed the rollback controller on familiar task execution;
- that repeated deterministic seeds prove real-world generalisation.
