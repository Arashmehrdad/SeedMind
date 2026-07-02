# SeedMind Week 13 Experiments Plan

**Date:** 1 July 2026  
**Stage:** Original SeedMind Week 13  
**Status:** Pre-registered before Week 13 execution  
**Authoritative production reference:** Week 12 rollback checkpoint `dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093`

## 1. Purpose

Week 13 asks one primary question:

> Does complete SeedMind provide measurable benefits over simpler versions?

The answer must distinguish task capability from developmental-control benefits. The Week 12 rollback checkpoint contains the frozen general controller as the only production module. Therefore complete SeedMind and the frozen-controller reference are expected to share the same familiar-task action path. Week 13 must not manufacture a task-success advantage by assigning the rejected specialist to the complete system.

The rejected Week 11 specialist `skill.expert.angular_push.v1`, checkpoint `3d86d365496f16678363f9348280c9c102b1bfa98e3a000e23be775a989188b2`, is comparison-only. It is never an authoritative production checkpoint.

## 2. Claims under test

### Claim C1 - Reusable production skill

The rollback production controller should complete familiar round-object tasks more often than a random primitive-action baseline under equal step budgets.

**Support threshold:** mean success-rate gain at least `+0.20`, with no action-authority violations.

This claim is about the compiled skill, not the complete architecture as a whole.

### Claim C2 - Ambition persistence

Repeated teacher evidence plus the ambition manager should create one persistent capability ambition that survives subsequent episodes and deterministic reload. Removing ambition should remove that persistence while leaving the production controller unchanged.

**Support threshold:** complete SeedMind persistence rate `1.00`; no-ambition persistence rate `0.00`; gain `+1.00`.

This claim does not require a familiar-task success increase, because the action controller is held constant.

### Claim C3 - Human apprenticeship

Complete SeedMind should request help in blocked high-uncertainty cases, avoid unnecessary help on familiar low-risk cases, and receive a teaching response that resolves the escalation. The no-human-teaching ablation may still request help but cannot count an unresolved request as teaching success.

**Support thresholds:** help recall at least `0.70`; help avoidance at least `0.70`; complete teaching-resolution rate `1.00`; no-human-teaching teaching-resolution rate `0.00`.

### Claim C4 - Retention-gated growth governance

The complete Week 12 process should reject unsupported growth after broad transfer testing, while a growth-without-replay condition should expose how narrow Week 11 success could have caused an invalid promotion.

**Support thresholds:**

- complete SeedMind invalid-promotion count `0`;
- growth-without-replay invalid-promotion count at least `1`;
- complete familiar-task degradation no more than `0.10`;
- complete production checkpoint remains the Week 12 rollback checkpoint.

This is a governance and evidence-quality claim. It is not evidence that replay improved the rejected specialist's task competence.

### Claim C5 - Broad angular transfer

The rejected specialist should solve the Week 12 broader angular transfer suite.

**Support threshold:** success at least `0.80` and gain at least `+0.20` over the frozen general controller.

Week 12 already indicates this claim is likely unsupported. Week 13 repeats and packages the comparison rather than changing the candidate.

## 3. Systems and conditions

### Baseline A - Random primitive controller

- Uses the same Nursery states and step budgets as the production controller.
- Selects only currently available primitive actions.
- Uses a deterministic condition-and-seed-derived random generator.
- Receives no learned skill, ambition, teaching, growth, or replay.

### Baseline B - Fixed reactive controller

- Uses a stateless direct object-to-target heuristic.
- Has no ambition, caregiver state, replay, or growth gate.
- Exists to distinguish a simple engineered controller from random action.

### Baseline C - Frozen rollback production controller

- Loads the Week 8 `approach_and_push` skill referenced by the Week 12 rollback checkpoint.
- Uses `production_curiosity` as action authority.
- Has no active specialist or router.
- Is the authoritative production reference.

### Experimental comparison - Rejected angular specialist

- Loads the unchanged Week 11 specialist checkpoint.
- Runs only as an explicitly labelled experimental comparison.
- Never replaces Baseline C as the production reference.

### Ablation E - No ambition

- Uses the same rollback production controller and Nursery scenarios as complete SeedMind.
- Removes ambition detection, adoption, persistence, and practice-state carryover.
- Human apprenticeship remains available.

### Ablation F - No human teaching

- Keeps the rollback production controller and ambition machinery.
- Allows help decisions to be measured.
- Suppresses teacher demonstrations, corrections, clarifications, and approvals.
- Unanswered help requests remain unresolved.

### Ablation G - Growth without replay

- Uses the rejected specialist and its Week 11 narrow evidence.
- Omits the Week 12 replay, broad transfer, retention, and rollback decision gate.
- Records whether narrow success would incorrectly authorise promotion.
- Remains experimental and cannot alter the production registry.

### Complete SeedMind

- Starts from the Week 12 rollback production checkpoint.
- Includes the existing curiosity authority, persistent ambition, human apprenticeship, reusable skill, diagnostic growth history, consolidation evidence, retention gate, and exact rollback decision.
- Does not reactivate the rejected specialist.

## 4. Scenarios and random seeds

### 4.1 Familiar round-object repeated-seed suite

The Week 8 scenario factory has a deterministic period of 100 unique seed/orientation combinations. Week 13 uses exactly those 100 disjoint scenarios once:

- repetition 1: seeds `2000-2019`;
- repetition 2: seeds `2020-2039`;
- repetition 3: seeds `2040-2059`;
- repetition 4: seeds `2060-2079`;
- repetition 5: seeds `2080-2099`.

Each system receives identical initial states and the Week 8 `96`-step budget.

### 4.2 Ambition repeated-seed suite

Five teacher-demonstration replications use scenario seeds:

`2100, 2101, 2102, 2103, 2104`

Each replication observes three repeated demonstrations, carries the adopted ambition across five later episodes, serializes it, reloads it, and checks identity and status.

### 4.3 Apprenticeship repeated-seed suite

Five replications use scenario seeds:

`2200, 2201, 2202, 2203, 2204`

Each replication contains four blocked high-uncertainty cases, four familiar low-risk cases, and one ambiguous case. Complete and no-human-teaching conditions receive identical case definitions.

### 4.4 Growth and retention suite

Week 13 reuses the authoritative Week 12 named suites without tuning:

- familiar ball stress seeds `1200-1239`;
- broad angular transfer seeds `1300-1331`;
- Week 11 narrow angular replay cohorts;
- five navigation cases;
- six help-policy cases.

Reusing these suites is intentional because Week 13 is packaging and statistically summarising the already closed Week 12 decision. They are not used to tune the candidate.

## 5. Metrics

### Task metrics

- success rate;
- success count and episode count;
- mean and median steps;
- per-repetition success rate;
- gain over matched baseline;
- Wilson 95 percent interval for binary success;
- authority violations.

### Ambition metrics

- ambition adoption rate;
- persistence across later episodes;
- reload identity match;
- active-status preservation;
- practice budget retained;
- persistence gain over no ambition.

### Human-teaching metrics

- help recall;
- help avoidance;
- teaching-response count;
- teaching-resolution rate;
- support promotion rate;
- unresolved justified-help count.

### Growth and retention metrics

- narrow angular success;
- broad angular transfer success;
- broad transfer gain;
- familiar-task degradation;
- exact action/outcome trace match;
- specialist selections on round-object tasks;
- invalid promotion count;
- rollback correctness.

### Reproducibility metrics

- deterministic artifact digest;
- authoritative checkpoint digest match;
- input and implementation hashes;
- seed-set equality;
- fresh-export byte equality;
- rerun metric equality.

## 6. Statistical summaries

For each repeated condition, Week 13 reports:

- count;
- mean;
- median;
- population standard deviation;
- minimum and maximum;
- Wilson 95 percent interval for pooled binary outcomes where applicable.

Five deterministic replications improve confidence in consistency across the declared symbolic scenario distribution. They do not establish real-world generalisation.

## 7. Learning curves and retention charts

The evidence package must export deterministic SVG charts:

- cumulative familiar-task success by evaluated episode for random, reactive, rollback production, and complete SeedMind;
- ambition persistence by subsequent episode for complete and no-ambition conditions;
- apprenticeship resolution by case index for complete and no-human-teaching conditions;
- familiar-task retention before and after experimental growth;
- narrow versus broad angular success for the rejected specialist.

Charts are explanatory views of machine-readable CSV and JSON data. Numeric artifacts remain authoritative.

## 8. Pass and fail rules

A claim is supported only when its pre-registered threshold is met.

Week 13 passes as an evidence stage when all of the following are true:

1. At least three of Claims C1-C4 are supported.
2. Claim C5 is reported honestly, whether supported or not.
3. No authority violation occurs in complete SeedMind evaluation.
4. The authoritative production checkpoint is the Week 12 rollback checkpoint.
5. The rejected specialist is never marked production-active.
6. Every required artifact is exported.
7. A fresh run reproduces committed artifacts byte-for-byte.

Week 13 passing does not mean every SeedMind claim passed. The closure ADR must list supported and unsupported claims separately.

## 9. Authoritative artifacts

Numeric and decision authority, in order:

1. `artifacts/week13_experiments/experiment_manifest.json`
2. `artifacts/week13_experiments/repeated_seed_results.csv`
3. `artifacts/week13_experiments/baseline_results.csv`
4. `artifacts/week13_experiments/ablation_results.csv`
5. `artifacts/week13_experiments/aggregate_metrics.json`
6. `artifacts/week13_experiments/claim_evidence_matrix.json`
7. `artifacts/week13_experiments/reproducibility_report.json`
8. `artifacts/week13_experiments/week13_acceptance_report.json`

The evidence report and charts explain these files but do not override them.

## 10. Reproducibility checks

A fresh execution must verify:

- the Week 12 stable checkpoint SHA-256 equals `dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093`;
- its registry contains only `general_push_controller` and has `router_registered: false`;
- the rejected specialist checkpoint identity is unchanged;
- all declared seed groups are pairwise disjoint where required;
- source and input hashes are recorded;
- repeated execution produces identical CSV, JSON, and SVG bytes;
- no temporary files remain.

## 11. Interpretation boundary

Week 13 may support claims about deterministic symbolic development, persistence, human-teaching response, reusable skill performance, evidence-gated growth, and rollback. It cannot support claims of general intelligence, consciousness, open-world transfer, real-world robotics performance, or broad neural generalisation.
