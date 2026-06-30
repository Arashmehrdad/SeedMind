# SeedMind Week 8 Reusable Skill Evidence

Date: 30 June 2026
Status: Passed
Scope: original SeedMind Master Implementation Plan Week 8 only

## Objective

Complete the main SeedMind Week 8 milestone: learn, compile, and reuse the first
main-project reusable skill, `approach_and_push`.

NDNRA remains a non-authoritative shadow. This evidence does not reopen NDNRA
Stage 8 and does not begin NDNRA Stage 9.

## Implementation

Main reusable skill implementation:

- `src/seedmind/skills/records.py`
- `src/seedmind/skills/approach_and_push.py`
- `src/seedmind/skills/week8.py`
- `scripts/run_week8_reusable_skill.py`

The reusable skill record preserves:

- stable identity: `skill.main.approach_and_push.v1`
- name: `approach_and_push`
- version: `1.0.0`
- schema version: `1`
- grounded production provenance episodes and seeds
- explicit preconditions
- deterministic primitive policy
- expected outcome
- termination and failure conditions
- success and attempt evidence counts
- compilation threshold
- reuse and discovery counts
- last validation status
- deterministic snapshot

## Compilation Evidence

Training seeds:

```text
6, 7, 8, 11
```

Compilation threshold:

```text
3 repeated successful grounded production episodes
```

Observed compilation evidence:

```text
success_evidence_count=4
attempt_evidence_count=4
```

The compiler rejects:

- one successful sequence;
- incomplete sequences;
- contradictory target tasks;
- unsafe or unavailable primitive actions;
- bounded imagination as factual experience;
- evaluation episodes as training evidence.

## Reuse And Evaluation

Evaluation seeds:

```text
206, 207, 208, 211, 212, 213, 216, 217, 218, 231,
232, 233, 236, 237, 238, 241, 242, 243, 256, 257
```

Training and evaluation seed overlap:

```text
0
```

Pass target:

```text
at least 20 unseen deterministic eligible random-start episodes
at least 80% success
no discovery during frozen evaluation
reuse count increases during evaluation
authority violations remain zero
NDNRA automatic promotions remain zero
```

Observed result:

```text
success_rate=1.0000
baseline_success_rate=1.0000
skill_invocation_count=352
reuse_count=20
discovery_count=0
authority_violations=0
evaluation_learning_attempts=0
```

The primitive rediscovery baseline also solved the eligible deterministic starts
at `1.0000`, so the compiled skill is not worse than baseline. The important Week
8 distinction is that frozen evaluation reused the compiled skill record and did
not increase discovery count.

## NDNRA Shadow Boundary

NDNRA was not granted production authority.

Observed shadow metrics:

```text
ndnra_shadow_observation_count=352
ndnra_suggestion_count=0
ndnra_disagreement_count=0
ndnra_authority_violations=0
ndnra_automatic_promotions=0
```

The main SeedMind skill owns the reusable production skill. NDNRA evidence is
reported only as shadow comparison metadata.

## Artifacts

Inspectable skill record:

```text
artifacts/week8_reusable_skill/approach_and_push_skill_record.json
```

Generalisation report:

```text
artifacts/week8_reusable_skill/week8_generalisation_report.json
```

## Validation

Focused Week 8 tests:

```text
.\.venv\Scripts\python.exe -m pytest tests/unit/skills -q --basetemp .tmp_pytest\week8-focused
16 passed
```

Week 8 runner:

```text
.\.venv\Scripts\python.exe scripts\run_week8_reusable_skill.py
pass_gate=true
```

Full repository validation is recorded in the final run report for this commit.
