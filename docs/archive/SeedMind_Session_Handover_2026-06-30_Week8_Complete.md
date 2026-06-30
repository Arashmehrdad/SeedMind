# SeedMind Session Handover — Week 8 Complete

Date: 30 June 2026
Purpose: continue in a fresh session with original SeedMind Week 9 only

## 1. Repository source of truth

- Repository alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Verified HEAD: `ade2c47da27e4ecbcc2b009737779064bd70a380`
- HEAD title: `Complete SeedMind Week 8 reusable skill`
- Verified working tree: clean
- Verified live status at handover creation: `## main...origin/main`
- Push policy: never push automatically

The earlier Week 8 completion report said the branch was ahead of `origin/main` by two commits. The live repository inspection performed for this handover no longer shows an ahead marker. Treat live Git state as authoritative and report any unexpected remote movement before implementation.

## 2. Completed milestone

Original SeedMind Master Implementation Plan Week 8 is closed.

Main SeedMind now owns the first reusable product skill:

```text
approach_and_push
```

Implementation:

- `src/seedmind/skills/__init__.py`
- `src/seedmind/skills/records.py`
- `src/seedmind/skills/approach_and_push.py`
- `src/seedmind/skills/week8.py`
- `scripts/run_week8_reusable_skill.py`

Evidence and decision:

- `docs/architecture/SeedMind_Week8_Reusable_Skill_Evidence_2026-06-30.md`
- `docs/architecture/decisions/ADR-2026-06-30-seedmind-week8-reusable-skill-closure.md`

## 3. Week 8 evidence

Training seeds:

```text
6, 7, 8, 11
```

Frozen evaluation seeds:

```text
206, 207, 208, 211, 212, 213, 216, 217, 218, 231,
232, 233, 236, 237, 238, 241, 242, 243, 256, 257
```

Observed metrics:

```text
success_rate=1.0000
primitive_rediscovery_baseline=1.0000
compilation_evidence_count=4
skill_invocation_count=352
reuse_count=20
discovery_count_during_frozen_evaluation=0
authority_violations=0
ndnra_shadow_observations=352
ndnra_authority_violations=0
ndnra_automatic_promotions=0
pass_gate=true
```

The main skill record preserves explicit preconditions, termination and failure conditions, grounded provenance, counters, validation state, and deterministic JSON representation.

The skill emits primitive candidates. Production curiosity remains the sole production action selector.

## 4. Validation baseline

```text
ruff format --check .: passed, 268 files formatted
ruff check .: passed
mypy .: passed, 268 source files
pytest -q --basetemp .tmp_pytest\full: 1133 passed
pip check: passed
git diff --check: passed with README CRLF normalization warning only
Week 8 runner: pass_gate=true
```

Focused Week 8 tests:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/skills -q --basetemp .tmp_pytest\week8-focused
16 passed
```

Skipped because not configured:

- Pylint
- pre-commit
- dedicated security-audit project command

## 5. Current architectural boundary

The canonical operating mode remains:

```text
production_with_ndnra_shadow
```

Rules that must remain true:

- Main SeedMind production curiosity selects the executed action.
- NDNRA observes the same state and grounded transition.
- NDNRA may suggest and learn but cannot execute, replace, schedule, or promote.
- Automatic NDNRA component promotion is disabled.
- Required disagreements remain auditable.
- Human stop, denial, correction, permission, and external safety controls remain authoritative.
- NDNRA Stage 8 is already closed and must not be reopened.
- NDNRA Stage 9 is unauthorised.
- Main and NDNRA persistence/proof boundaries remain separate.
- Bounded imagination cannot become factual experience.

Primary boundary documents:

- `docs/architecture/SeedMind_NDNRA_Parallel_Operating_Model_2026-06-30.md`
- `docs/architecture/decisions/ADR-2026-06-30-seedmind-ndnra-parallel-operation.md`

## 6. Live plan

`plans.md` is the single live continuation file.

It currently states:

- Week 8 is closed.
- Original SeedMind Week 9 is next.
- Week 9 was not started in the Week 8 run.
- Week 10 must not begin early.
- NDNRA Stage 9 remains unauthorised.

## 7. Next milestone — original SeedMind Week 9

Week 9 title:

```text
Contribution and reduced support
```

Original tasks:

1. Issue a human request to move the ball.
2. Add a capability check.
3. Add contribution verification.
4. Add honest failure reporting.
5. Add support-level promotion rules.
6. Test independent performance after teaching.

Deliverables:

- human contribution demo;
- support-level report;
- contribution history.

Pass gates:

1. SeedMind completes a familiar human request.
2. Support drops when competence is proven.

Source:

- `docs/archive/SeedMind_Master_Implementation_Plan_v0.1.md`, Week 9.

## 8. Week 9 implementation guidance

Before editing, inspect existing main-project implementations for:

- human requests and apprenticeship;
- ambition and target capabilities;
- skill capability records;
- contribution and verification concepts;
- support/help levels;
- honest failure and outcome reporting;
- persistence and restart boundaries;
- `approach_and_push` reuse;
- production-versus-NDNRA shadow auditing.

Do not create duplicate systems where an accepted main-project abstraction already exists.

Week 9 should use the closed Week 8 `approach_and_push` skill as the familiar capability for the human ball-moving request. It must not rediscover or recompile the skill during frozen contribution evaluation.

A support-level decrease must be earned from grounded verified competence, not from self-report, producer-verifier agreement, one lucky episode, NDNRA suggestion, or imagined evidence.

The system must remain able to:

- request help when capability or preconditions are insufficient;
- report failure honestly;
- preserve human stop and correction authority;
- avoid claiming contribution success without grounded verification;
- avoid reducing support after weak, stale, contradictory, or task-mismatched evidence;
- restore support when competence later degrades or the context becomes unfamiliar.

## 9. New-session starter prompt

Paste the following into a fresh ChatGPT/Codex session:

```text
Continue SeedMind from `docs/archive/SeedMind_Session_Handover_2026-06-30_Week8_Complete.md` as the source of truth.

Repository:
- Alias: `seedmind`
- Local path: `D:\Github\SeedMind`
- Branch: `main`
- Expected HEAD: `ade2c47da27e4ecbcc2b009737779064bd70a380`
- Expected working tree: clean
- Live handover-time status was `## main...origin/main`; verify remote divergence rather than assuming ahead/behind state
- Never push automatically

First:

1. Attach and verify CodexBridge/Universal Tool Runner.
2. Inspect Git status, HEAD, recent commits, and current diffs.
3. Verify commit `ade2c47` exists and is the Week 8 closure commit.
4. Read:
   - `plans.md`
   - `README.md`
   - `docs/archive/SeedMind_Session_Handover_2026-06-30_Week8_Complete.md`
   - `docs/archive/SeedMind_Master_Implementation_Plan_v0.1.md`, especially Week 9
   - `docs/architecture/SeedMind_Week8_Reusable_Skill_Evidence_2026-06-30.md`
   - `docs/architecture/decisions/ADR-2026-06-30-seedmind-week8-reusable-skill-closure.md`
   - `docs/architecture/SeedMind_NDNRA_Parallel_Operating_Model_2026-06-30.md`
   - `docs/architecture/decisions/ADR-2026-06-30-seedmind-ndnra-parallel-operation.md`
5. Report immediately if the repository is dirty, HEAD differs, a bridge command is missing, or live Git divergence differs from the handover.
6. Inspect existing human, apprenticeship, ambition, contribution, verification, support-level, skill, persistence, and shadow-integration code before proposing new abstractions.

Then complete ORIGINAL MAIN-ROADMAP WEEK 9 ONLY:

`Contribution and reduced support`

Required original tasks:
- issue a human request to move the ball;
- add a capability check;
- add contribution verification;
- add honest failure reporting;
- add support-level promotion rules;
- test independent performance after teaching.

Required deliverables:
- human contribution demo;
- support-level report;
- contribution history.

Required pass gates:
- SeedMind completes a familiar human request;
- support drops when competence is proven.

Use the closed Week 8 main-project `approach_and_push` skill as the familiar ball-moving capability. Do not reopen, replace, or recompile Week 8 unless a genuine regression is demonstrated. Frozen Week 9 evaluation must reuse the compiled skill without increasing its discovery count.

Critical evidence rules:

- Human requests must be typed, inspectable, and bound to a target capability and outcome.
- Capability checks must distinguish unavailable, unproven, degraded, context-mismatched, and verified capability.
- Contribution success must require grounded outcome verification.
- Producer-verifier agreement, NDNRA agreement, imagination, or self-report alone cannot certify success.
- Honest failure must preserve reason, attempted capability, precondition failure, interruption, uncertainty, and requested support.
- Support level must decrease only after repeated verified competence under declared thresholds.
- One lucky success cannot reduce support.
- Evaluation episodes cannot silently train, compile, or promote.
- Support must remain or increase when evidence is weak, stale, contradictory, degraded, unsafe, or outside the learned context.
- Human stop, denial, correction, clarification, permission, and demonstration remain authoritative.

Main-versus-NDNRA boundary:

- Production curiosity remains the sole production action selector.
- Main SeedMind owns the contribution workflow and support-level state.
- NDNRA remains a non-authoritative shadow observer.
- NDNRA may suggest and learn from the same grounded transitions.
- NDNRA cannot execute, replace, schedule, verify, promote, or lower support.
- Automatic NDNRA component promotion remains disabled.
- Record shadow observations, disagreements, comparisons, authority violations, and automatic promotions.
- Keep all authority-violation counts at zero.

Required falsification and adversarial tests should include at least:

- unfamiliar request does not claim capability;
- failed preconditions do not claim contribution success;
- one success does not lower support;
- unverified or imagined outcome does not lower support;
- contradictory or stale evidence blocks support reduction;
- task/context mismatch blocks capability reuse;
- human stop or denial interrupts contribution immediately;
- failure is reported honestly rather than hidden;
- frozen evaluation does not learn, compile, promote, or increase discovery;
- corrupted or incompatible contribution/support persistence fails safely;
- NDNRA cannot lower support or obtain action/verification authority;
- production action remains retained through the parallel-operation policy;
- competence degradation can restore a higher support level.

Define deterministic thresholds before tuning against final evaluation. Reuse existing project thresholds when available. Otherwise document defensible values for repeated verified competence, evaluation episode count, familiar-request success, support reduction, regression tolerance, and restoration behavior.

Implementation process:

- Work continuously through bounded increments; do not stop after planning.
- Preserve live repository changes and do not reset unfamiliar work.
- Avoid broad rewrites and duplicate systems.
- Do not install unnecessary dependencies.
- Do not add autonomous workers, queues, timers, or background agents.
- Do not modify closed NDNRA Stage 8 evidence or implement NDNRA Stage 9.
- Do not begin original SeedMind Week 10.
- Do not create another handover unless explicitly requested.
- Do not push.

Validation:

- run focused tests during implementation;
- run the Week 9 deterministic acceptance/demo runner;
- run `ruff format --check .`;
- run `ruff check .`;
- run `mypy .`;
- run the complete pytest suite;
- run `pip check`;
- run `git diff --check`.

If full pytest exceeds a command timeout, execute every test file through documented non-overlapping groups and report the exact total. Do not silently omit any tests.

Before committing, review the full diff for:

- Week 8 regression or rediscovery during frozen evaluation;
- unsupported competence claims;
- silent or dishonest failure handling;
- support reduction without grounded repeated evidence;
- human-authority bypass;
- NDNRA authority leakage;
- Week 10 work;
- NDNRA Stage 9 work;
- temporary or generated files.

After all gates pass:

- create one bounded local commit with a title similar to `Complete SeedMind Week 9 contribution`;
- do not push;
- update `plans.md`, `README.md`, Week 9 evidence, closure ADR, repository wiki, and repository decision memory;
- report exact changed files, thresholds, human-request flow, capability checks, contribution-verification evidence, honest-failure cases, support-level transitions, independent-performance metrics, Week 8 reuse/discovery counts, NDNRA shadow metrics, validation results, commit hash, and final Git status;
- explicitly confirm original Week 10 and NDNRA Stage 9 were not started.
```

## 10. Do not confuse these milestones

- NDNRA Stage 8: closed research shadow trial.
- Original SeedMind Week 8: closed reusable main-project skill.
- Original SeedMind Week 9: next contribution and support milestone.
- NDNRA Stage 9: unauthorised.
- Original SeedMind Week 10: not started and out of scope for the next session.
