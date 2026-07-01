# ADR: SeedMind Week 8 Reusable Skill Closure

Date: 30 June 2026
Status: Accepted
Scope: original SeedMind Master Implementation Plan Week 8

## Context

The original SeedMind roadmap requires Week 8 to learn and compile the first
reusable skill. NDNRA Stage 8 is already closed separately and cannot be used as
proof that the main product skill exists.

Week 8 must therefore add a main SeedMind reusable skill implementation while
preserving the then-current `production_with_ndnra_shadow` operating model, later superseded by `ADR-2026-07-01-freeze-ndnra-for-separate-project.md`:

- production curiosity remains the production action authority;
- NDNRA remains non-authoritative;
- automatic NDNRA component promotion remains disabled;
- Stage 9 remains unauthorised.

## Decision

Accept the main SeedMind `approach_and_push` reusable skill as the Week 8
milestone closure.

The implementation is the main `seedmind.skills` package:

- `records.py` defines deterministic skill records and strict JSON loading;
- `approach_and_push.py` defines compilation and reusable primitive candidates;
- `week8.py` defines deterministic training, frozen evaluation, baseline
  comparison, and report export;
- `scripts/run_week8_reusable_skill.py` runs the Week 8 gate.

The compiled skill is not a hidden executor. It emits primitive production
candidates, and each retained primitive action passes through the production
curiosity boundary.

## Evidence

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

Artifacts:

- `artifacts/week8_reusable_skill/approach_and_push_skill_record.json`
- `artifacts/week8_reusable_skill/week8_generalisation_report.json`
- `docs/architecture/SeedMind_Week8_Reusable_Skill_Evidence_2026-06-30.md`

## Consequences

- Original SeedMind Week 8 is closed.
- Main SeedMind now owns the first reusable product skill.
- Frozen evaluation reuses the compiled skill instead of increasing discovery
  count.
- NDNRA remains side by side as a shadow observer only.
- No NDNRA Stage 9 work is authorised or started by this decision.
- Week 9 contribution work may be planned next, but is not included here.
