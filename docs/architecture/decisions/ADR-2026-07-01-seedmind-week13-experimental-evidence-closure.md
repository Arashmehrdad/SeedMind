# ADR: Close SeedMind Week 13 With Bounded Experimental Support

**Date:** 1 July 2026  
**Status:** Accepted with explicit claim boundaries  
**Decision owner:** SeedMind project

## Context

Week 13 was required to answer one central question:

> Does complete SeedMind provide measurable benefits over simpler versions?

The experiment contract fixed the claims, baselines, ablations, random seeds, thresholds, authoritative checkpoint, and reproducibility rules before evidence interpretation.

The Week 12 rollback checkpoint remained the only production reference. The Week 11 angular specialist remained rejected and comparison-only.

## Decision

Close Week 13 as a passing experimental-evidence stage.

The pass is bounded. It supports four specific claims in the deterministic symbolic Nursery and rejects one broad-transfer claim. It does not establish general intelligence, real-world generalisation, broad manipulation competence, or successful production specialist growth.

The authoritative production checkpoint remains:

`dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093`

The rejected specialist checkpoint remains experimental only:

`3d86d365496f16678363f9348280c9c102b1bfa98e3a000e23be775a989188b2`

## Supported claims

### C1 - Reusable bounded skill

Supported.

The rollback production controller achieved `36/100` on the 100-scenario familiar round-object suite, compared with `0/100` for random primitive action. The `+0.36` gain exceeded the pre-registered `+0.20` threshold, with zero authority violations.

This supports a reusable bounded skill claim. It does not establish broad object-manipulation mastery.

### C2 - Ambition persistence

Supported.

Across five repeated trials, complete SeedMind generated, adopted, persisted, serialized, reloaded, and preserved one active ambition at rate `1.00`. The no-ambition ablation generated the candidate evidence but produced `0.00` adoption and persistence.

This supports persistent developmental commitment beyond transient detection.

### C3 - Human apprenticeship

Supported.

Complete SeedMind achieved help recall `1.00`, help avoidance `1.00`, teaching resolution `1.00`, and support promotion `1.00`. The no-human-teaching ablation retained help detection but produced teaching resolution `0.00`, support promotion `0.00`, and 25 unresolved justified-help events.

This supports the value of the protected symbolic human-teaching channel in the declared cases.

### C4 - Retention-gated growth governance

Supported.

The complete Week 12 governance path recorded zero invalid promotions, zero familiar-task degradation, exact rollback-checkpoint verification, and no production specialist activation.

The growth-without-replay decision ablation would have promoted the specialist from narrow `52/52` evidence despite `0/32` success on the broader solvable transfer suite. It therefore recorded one invalid promotion.

This supports replay, transfer evaluation, retention checks, and rollback as safeguards against overclaiming narrow specialist competence.

## Unsupported claim

### C5 - Broad angular transfer

Unsupported.

The rejected specialist achieved:

- narrow designed cohorts: `52/52`;
- broader transfer suite: `0/32`;
- broad gain over the general controller: `0.00`;
- independently solvable broad cases: `32/32`.

The specialist must not be described as broadly transferable or production-ready.

## Week 13 pass rule

Week 13 passes because:

- at least three core claims were required and four were supported;
- the unsupported broad-transfer claim was reported explicitly;
- no authority violation occurred;
- the Week 12 rollback checkpoint remained authoritative;
- the rejected specialist remained inactive;
- all required artifact classes were exported;
- reproducibility metadata and deterministic payload hashes were generated.

The acceptance decision is `week13_evidence_pass`.

## Week 14 demonstration permissions

Week 14 may demonstrate and state that, within the deterministic symbolic Nursery:

1. the reusable rollback skill beats the declared random and reactive baselines;
2. ambition persists across episodes and deterministic reload;
3. human teaching resolves justified help and enables support promotion;
4. the complete and rollback production action paths are exactly equivalent on the familiar suite;
5. broad transfer evaluation rejected an overfitted specialist;
6. rollback preserved the general controller and action authority;
7. the development and growth decisions are traceable to machine-readable evidence.

## Claims prohibited in Week 14

Week 14 must not claim:

- general intelligence or AGI;
- consciousness, emotion, or human-like understanding;
- broad real-world transfer;
- robust general object manipulation;
- broad angular-object competence;
- successful production specialist growth;
- that the rejected specialist is active or accepted;
- that complete SeedMind outperformed the rollback controller on familiar task execution;
- that `36/100` or `15/40` represents mastery;
- that repeated deterministic seeds prove real-world generalisation;
- that replay repaired the rejected specialist.

## Authoritative artifacts

Machine-readable authority, in order:

1. `artifacts/week13_experiments/experiment_manifest.json`
2. `artifacts/week13_experiments/repeated_seed_results.csv`
3. `artifacts/week13_experiments/baseline_results.csv`
4. `artifacts/week13_experiments/ablation_results.csv`
5. `artifacts/week13_experiments/aggregate_metrics.json`
6. `artifacts/week13_experiments/claim_evidence_matrix.json`
7. `artifacts/week13_experiments/reproducibility_report.json`
8. `artifacts/week13_experiments/week13_acceptance_report.json`

Explanatory authority:

- `docs/architecture/SeedMind_Week13_Experiments_Plan_2026-07-01.md`
- `docs/architecture/SeedMind_Week13_Experiments_Evidence_2026-07-01.md`
- `docs/architecture/SeedMind_Week13_Limitations_2026-07-01.md`
- this ADR.

Charts are explanatory renderings of the numeric artifacts and do not override them.

## Reproducibility note

The deterministic artifact payload digest is:

`2e492fdb89056dc48076831fc924f7ec8cb9d8f398c67e8035bc3b344bf36985`

The complete repository test suite was executed through CodexBridge's durable async command path using isolated per-run temporary and pytest base directories. Run `20260702T022842Z_project_command_dafb975a` completed with exit code `0`: `1189 passed in 464.23s (0:07:44)`. The repository-wide suite is therefore fully passed for this closure state, alongside the machine-readable reproducibility report and separate Ruff and mypy gates.

## Consequences

- Week 13 is closed.
- Week 14 packaging may begin using only the permitted claims above.
- The production registry remains rollback-only.
- The angular specialist remains rejected and experimental.
- The general controller's `36/100` familiar-suite and `15/40` broader-stress limitations must remain visible.
- Future specialist work requires a new diagnosis, incubation cycle, and fresh transfer partition.
- Future scientific work should add stronger parameter-matched, planning, and learned baselines.
