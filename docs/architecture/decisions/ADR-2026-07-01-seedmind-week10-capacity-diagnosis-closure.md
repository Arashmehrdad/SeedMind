# ADR: SeedMind Week 10 Capacity Diagnosis Closure

Date: 1 July 2026
Status: Accepted
Scope: original SeedMind Master Implementation Plan Week 10

## Context

Original Week 10 must diagnose developmental blockage without immediately adding
capacity. Failure alone is insufficient evidence for growth. SeedMind must first
rule out insufficient exploration, missing grounded memory, poor strategy,
ambiguous requests, inadequate teaching, prediction issues, impossible geometry,
unsafe conditions, and resource limits.

NDNRA is frozen in this repository and is not part of Week 10 acceptance.

## Decision

Accept `seedmind.growth` as the original Week 10 diagnostic layer.

The accepted design:

1. Adds raw angular-object push resistance to the main Nursery environment while
   preserving round-object behavior.
2. Keeps policy-facing observations numeric and raw, without semantic cube
   labels.
3. Aggregates deterministic learning-progress windows with predeclared
   thresholds.
4. Distinguishes `insufficient_evidence`, `improving`, `temporary_failure`, and
   `sustained_blockage`.
5. Requires repeated windows, sufficient attempts, exhausted bounded strategy
   variants, memory replay, help or demonstration consideration, prediction
   check, ambiguity resolution, safety/permission clearance, and no resource
   limit before sustained blockage can produce a proposal.
6. Uses grounded main SeedMind memory for replay evidence.
7. Uses the protected human apprenticeship policy for help and demonstration.
8. Generates only a non-authoritative proposal for the sustained-blockage case.
9. Creates no specialist, router, parameters, production mutation, or Week 11
   growth gate.

## Evidence

Observed environment behavior:

```text
round_open_push=pushed
angular_open_push=pushed
angular_wall_push=push_ineffective_contact
```

Observed progress-window thresholds:

```text
window_size=4
minimum_windows_for_blockage=3
minimum_attempts_for_blockage=12
improvement_threshold=0.10
progress_resume_threshold=0.20
sustained_success_rate_ceiling=0.25
sustained_progress_ceiling=0.30
```

Observed scenario outcomes:

```text
familiar_control_success_rate=1.0000
early_cube_evidence=insufficient_evidence,no_proposal
temporary_cube_recovery=improving,no_proposal
sustained_cube_blockage=sustained_blockage,proposal_generated
ambiguous_non_capacity_blockage=insufficient_evidence,no_proposal
```

Observed proposal:

```text
proposal_id=growth-week10-cube-policy-0001
candidate.type=skill_expert
candidate.parent_module=general_push_controller
candidate.created=false
status=proposed_not_authorised
```

Observed acceptance:

```text
environment_extension_pass=true
learning_progress_pass=true
temporary_failure_classification_pass=true
sustained_blockage_classification_pass=true
diagnostic_ladder_pass=true
non_capacity_blockage_pass=true
growth_delay_pass=true
growth_proposal_pass=true
frozen_skill_preservation_pass=true
frozen_ndnra_boundary_pass=true
week10_main_milestone_pass=true
specialist_created=false
router_created=false
week11_started=false
ndnra_required=false
```

Artifacts:

- `artifacts/week10_capacity_diagnosis/diagnostic_report.json`
- `artifacts/week10_capacity_diagnosis/growth_proposal_record.json`
- `artifacts/week10_capacity_diagnosis/learning_progress_windows.json`
- `artifacts/week10_capacity_diagnosis/plateau_visualisation.svg`
- `artifacts/week10_capacity_diagnosis/week10_acceptance_report.json`
- `docs/architecture/SeedMind_Week10_Capacity_Diagnosis_Evidence_2026-07-01.md`

## Consequences

- Original SeedMind Week 10 is closed.
- Original Week 11 specialist growth is now the next main-roadmap stage but is
  not started by this decision.
- The sustained blockage has one proposed Week 11 investigation target.
- No specialist, router, grown parameters, production mutation, or NDNRA
  dependency exists.
- NDNRA remains frozen for separate-project extraction.
