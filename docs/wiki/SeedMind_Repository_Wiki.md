# SeedMind Repository Wiki

Last refreshed: 30 June 2026

## Current State

- Branch: `main`
- Push policy: do not push automatically.
- Latest completed main-roadmap milestone: original SeedMind Week 8 reusable skill.
- Latest completed NDNRA research stage: Developmental Network v0.2 Stage 8.
- Current operating mode: `production_with_ndnra_shadow`.
- Next main-roadmap target: Week 9 contribution and reduced support.
- NDNRA Stage 9: not authorised.

## Week 8 Main Skill Boundary

Week 8 is closed by the main `seedmind.skills` package, not by NDNRA research
contracts.

Implemented main skill:

- `approach_and_push`
- stable identity: `skill.main.approach_and_push.v1`
- version: `1.0.0`
- primitive policy: `axis_aligned_object_target_push_policy_v1`

The skill is compiled from repeated grounded production episodes and preserves
explicit preconditions, expected outcome, termination conditions, failure
conditions, evidence counts, reuse count, discovery count, validation status,
and deterministic snapshot.

## Week 8 Evidence

Training seeds:

```text
6, 7, 8, 11
```

Evaluation seeds:

```text
206, 207, 208, 211, 212, 213, 216, 217, 218, 231,
232, 233, 236, 237, 238, 241, 242, 243, 256, 257
```

Observed metrics:

```text
success_rate=1.0000
baseline_success_rate=1.0000
compilation_evidence_count=4
skill_invocation_count=352
reuse_count=20
discovery_count=0
authority_violations=0
ndnra_authority_violations=0
ndnra_automatic_promotions=0
pass_gate=true
```

Evidence files:

- `docs/architecture/SeedMind_Week8_Reusable_Skill_Evidence_2026-06-30.md`
- `docs/architecture/decisions/ADR-2026-06-30-seedmind-week8-reusable-skill-closure.md`

Generated local artifacts:

- `artifacts/week8_reusable_skill/approach_and_push_skill_record.json`
- `artifacts/week8_reusable_skill/week8_generalisation_report.json`

## Authority Boundary

- Production curiosity remains the only production action authority.
- The reusable skill emits primitive candidates and does not bypass production
  curiosity.
- NDNRA observes, suggests, and learns only as a non-authoritative shadow.
- NDNRA cannot execute, schedule, replace, promote, or select production
  actions.
- Automatic NDNRA component promotion remains disabled.

## Next Stage Boundary

Original SeedMind Week 9 may begin after this closure commit.

Week 9 scope:

- human request to move the ball;
- capability check;
- contribution verification;
- honest failure reporting;
- support-level promotion rules;
- independent familiar-request performance after teaching.

Explicitly not authorised by Week 8 closure:

- NDNRA Stage 9;
- production action replacement;
- internet access;
- shell access inside the seed;
- source self-modification;
- autonomous background workers;
- new specialist growth.
