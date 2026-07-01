# SeedMind Week 12 Consolidation and Retention Evidence

**Date:** 1 July 2026  
**Execution status:** Week 12 consolidation workflow completed  
**Growth decision:** Reject `skill.expert.angular_push.v1` and restore the pre-growth registry  
**Production activation:** Not authorised

## 1. Decision in plain language

Week 12 did not promote the Week 11 angular-push specialist.

The specialist retained perfect performance on the exact Week 11 problem families, but failed all 32 new larger-grid angular-object cases. An independent state-space search found grounded solutions for all 32 cases within the same step budget. The failure therefore cannot be dismissed as an impossible-test problem.

The correct Week 12 action was to reject the candidate, remove its router registration, and save the exact pre-growth registry as the stable MVP checkpoint.

`week12_main_milestone_pass` is `false` because the candidate failed promotion. This does not mean that the Week 12 implementation failed: scheduling, replay, evaluation, character and safety checks, checkpointing, and rollback all executed and produced deterministic evidence.

## 2. What was tested

| Evaluation | What the test means | Baseline | Candidate/post-growth result | Decision meaning |
|---|---|---:|---:|---|
| Original Week 8 ball replay | Can the active router preserve the previously accepted familiar ball cohort while the angular specialist abstains? | Accepted Week 8 behaviour | `20/20`; zero specialist selections | Replay retained |
| Week 11 angular replay | Does the candidate still solve the original and mirrored/rotated Week 11 families after consolidation? | Week 11 accepted checkpoint | `52/52` across the `20` original and `32` holdout episodes | Narrow accepted behaviour retained |
| New ball stress suite | Does adding the router or specialist change the frozen controller on 40 previously unused ball starts? | `15/40` | `15/40`; exact action/outcome trace match `40/40`; zero specialist selections | No growth interference, but exposes a pre-existing general-controller weakness |
| Angular transfer suite | Can the candidate handle eight named larger-grid contact-block families over 32 disjoint starts and orientations? | General controller `0/32` | Candidate `0/32`; gain `0.00` | Promotion gate failed |
| Independent solvability oracle | Were the transfer failures caused by impossible layouts? | Grounded breadth-first search over primitive Nursery transitions | Solutions found for `32/32` cases | Confirms the candidate, not the test feasibility, failed |
| Navigation regression | Does the active growth router alter unrelated navigation behaviour? | Deterministic pre-growth navigation traces | Exact match on all five named cases, including one honest unreachable case | No navigation interference |
| Help-seeking regression | Are uncertainty-sensitive help and independence decisions preserved? | Six predeclared expected decisions | `6/6` matched | Help-seeking preserved |
| Human correction | Does a corrected goal remove inappropriate specialist routing? | Specialist selected before correction | Specialist abstained and general fallback was exposed after correction | Correction remains effective |
| Character and safety | Are abstention, shutdown, proposal-only authority, external success verification, and zero authority violations preserved? | Declared Week 12 gates | All passed | Safety did not cause rejection |
| Rollback | Can a provisionally active specialist be removed exactly? | Pre-growth registry | Structured registry and digest restored exactly | Stable rollback accepted |

## 3. Consolidation schedule and replay

Week 12 implemented the master-plan schedule as an inspectable episode-`1,000` full-consolidation event:

- lightweight update interval: every episode;
- short consolidation interval: every `100` episodes;
- full retention interval: every `1,000` episodes;
- structural evaluation permitted only after the Week 10 diagnosis and Week 11 incubation gates;
- stable checkpoints recorded before and after the proposed structural change.

Replay was read-only. It did not tune the candidate or change the six accepted policy scalars. This prevents evaluation data from becoming hidden training data.

## 4. Ball retention interpretation

The original authoritative Week 8 cohort remained successful at `20/20`, and the specialist was never selected for those round-object tasks.

The new 40-seed stress suite produced a different but important result:

- frozen general controller: `15/40`;
- routed post-growth system: `15/40`;
- exact action and outcome trace matches: `40/40`;
- specialist selections: `0`;
- degradation: `0.00`;
- diagnostic success target: `0.90`, not met by either system.

Therefore the growth candidate did not damage ball behaviour. However, the broader suite shows that the existing general controller is not as broadly reliable as the original `20/20` cohort suggested. This weakness belongs to the frozen baseline and must not be hidden by calling the non-interference gate a general ball-capability pass.

## 5. Angular transfer failure

The transfer suite used eight named larger-grid families. Each family places a blocker so that a direct push toward the target has ineffective angular contact, requiring a longer sequence of repositioning and pushes. Thirty-two disjoint seeds vary agent start and orientation.

Results:

- oracle-solvable layouts: `32/32`;
- general-controller successes: `0/32`;
- routed specialist successes: `0/32`;
- candidate success floor: `0.80`;
- required gain over general controller: `+0.20`;
- actual gain: `0.00`;
- action-authority violations: `0`.

The candidate continued to be selected and emit actions, but its local clearance-aware choice did not produce complete plans for the longer multi-push transfer tasks. The Week 11 name `angular_push` therefore described a broader capability than the evidence supports. Its proven scope is limited to the original blockage family and its designed rotations or mirrors.

No parameter tuning was performed after seeing this failure. Any replacement candidate requires a new diagnosis, incubation partition, and evaluation cycle.

## 6. Character, safety, and authority

The rejection was caused only by capability transfer failure. The following remained intact:

- out-of-scope and unavailable-action abstention;
- specialist confidence above the router threshold only on eligible in-scope proposals;
- all six predeclared help-seeking decisions;
- immediate routing change after human correction;
- shutdown through the general path;
- proposal-only router and specialist contracts;
- `production_curiosity` as the sole action authority;
- environment-state success verification rather than module self-report;
- zero action-authority violations;
- unchanged frozen Week 8 skill bytes;
- unchanged Week 11 candidate identity and policy version;
- frozen, uninvolved NDNRA boundary.

## 7. Stable checkpoint and rollback

The final stable checkpoint is a rollback checkpoint, not a grown architecture.

- Stable checkpoint SHA-256: `dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093`
- Candidate status: `rejected_after_week12`
- Candidate active: `false`
- Router active: `false`
- Router registered in final registry: `false`
- General controller active: `true`
- Production action authority: `production_curiosity`

Discarding the provisionally active specialist reproduced the pre-growth registry exactly, including its deterministic digest.

## 8. Acceptance fields

All Week 12 fields passed except `angular_transfer_pass`:

- scheduled consolidation: pass;
- ball replay: pass;
- angular replay: pass;
- ball non-interference retention: pass;
- angular transfer: **fail**;
- navigation regression: pass;
- help-seeking regression: pass;
- human correction: pass;
- character gate: pass;
- safety gate: pass;
- authoritative Week 11 input: pass;
- candidate identity: pass;
- implementation provenance: pass;
- disjoint evaluation partitions: pass;
- frozen skill preservation: pass;
- frozen NDNRA boundary: pass;
- exact rollback: pass;
- stable checkpoint reload: pass.

The deterministic acceptance decision is `reject_and_rollback`.

## 9. Evidence locations

- `artifacts/week12_consolidation/scenario_catalogue.json`
- `artifacts/week12_consolidation/consolidation_schedule.json`
- `artifacts/week12_consolidation/replay_report.json`
- `artifacts/week12_consolidation/retention_report.json`
- `artifacts/week12_consolidation/navigation_regression.json`
- `artifacts/week12_consolidation/help_seeking_regression.json`
- `artifacts/week12_consolidation/character_safety_report.json`
- `artifacts/week12_consolidation/growth_audit.json`
- `artifacts/week12_consolidation/week12_acceptance_report.json`
- `artifacts/week12_consolidation/stable_mvp_checkpoint.json`
- `artifacts/week12_consolidation/checkpoints/final_registry.json`
- `artifacts/week12_consolidation/checkpoints/rollback_checkpoint.json`

## 10. Limitations and next stage

- The environment remains deterministic, symbolic, and small.
- The solvability oracle verifies these 32 layouts, not arbitrary worlds.
- The transfer suite covers eight designed blocker families.
- Confidence checks enforce routing discipline but are not probabilistic calibration.
- The new ball stress suite reveals weak baseline coverage that needs separate investigation.
- Week 13 may use the rejected candidate and rollback outcome in baselines and ablations, but must not treat the specialist as a production component.
