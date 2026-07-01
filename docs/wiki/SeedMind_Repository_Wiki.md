# SeedMind Repository Wiki

Last refreshed: 1 July 2026

## Current State

- Branch: `main`
- Push policy: do not push automatically.
- Latest completed main-roadmap milestone: original SeedMind Week 10 capacity
  diagnosis.
- NDNRA status: frozen at source baseline
  `b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a` for separate-project extraction.
- Current operating mode: original SeedMind product path without NDNRA
  dependency or mandatory comparison.
- Next main-roadmap target: original Week 11 candidate specialist and growth
  gate.
- Original Week 11 is not started; NDNRA Stage 9 is permanently unauthorised in
  this repository.

## Week 10 Capacity Diagnosis

Week 10 is closed by the main `seedmind.growth` package.

Implemented behavior:

- raw angular-object flat-contact push resistance in the Nursery transition
  engine;
- numeric policy-facing observations with no privileged `cube` label;
- deterministic learning-progress windows;
- typed diagnostic ladder with early stops;
- bounded general strategy variants;
- grounded main-memory replay attempts;
- protected help and teacher-demonstration attempts;
- one non-authoritative growth proposal only for sustained blockage.

Observed metrics:

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
familiar_control_success_rate=1.0000
specialist_created=false
router_created=false
week11_started=false
ndnra_required=false
```

Progress-window thresholds:

```text
window_size=4
minimum_windows_for_blockage=3
minimum_attempts_for_blockage=12
improvement_threshold=0.10
progress_resume_threshold=0.20
sustained_success_rate_ceiling=0.25
sustained_progress_ceiling=0.30
```

Scenario outcomes:

```text
early_cube_evidence=insufficient_evidence,no_proposal
temporary_cube_recovery=improving,no_proposal
sustained_cube_blockage=sustained_blockage,proposal_generated
ambiguous_non_capacity_blockage=insufficient_evidence,no_proposal
```

Growth proposal:

```text
proposal_id=growth-week10-cube-policy-0001
candidate.type=skill_expert
candidate.parent_module=general_push_controller
candidate.created=false
status=proposed_not_authorised
```

Evidence files:

- `docs/architecture/SeedMind_Week10_Capacity_Diagnosis_Evidence_2026-07-01.md`
- `docs/architecture/decisions/ADR-2026-07-01-seedmind-week10-capacity-diagnosis-closure.md`
- `artifacts/week10_capacity_diagnosis/diagnostic_report.json`
- `artifacts/week10_capacity_diagnosis/growth_proposal_record.json`
- `artifacts/week10_capacity_diagnosis/learning_progress_windows.json`
- `artifacts/week10_capacity_diagnosis/plateau_visualisation.svg`
- `artifacts/week10_capacity_diagnosis/week10_acceptance_report.json`

## Frozen NDNRA Boundary

- NDNRA is not an active SeedMind subsystem or shadow requirement.
- No future SeedMind milestone may depend on NDNRA modules, proposals, training,
  comparison, or promotion.
- Existing NDNRA source, tests, documents, and artifacts remain read-only
  research history and extraction material.
- No NDNRA Stage 9, production integration, component promotion, or new
  comparison work is authorised in SeedMind.

## Week 11 Boundary

Original SeedMind Week 11 may investigate a candidate specialist and growth gate
after this closure. It was not started by Week 10.

Explicitly not authorised by Week 10 closure:

- creating, training, accepting, routing, or deploying a specialist;
- production architecture mutation;
- NDNRA capability work inside SeedMind;
- NDNRA Stage 9;
- making future acceptance depend on NDNRA evidence;
- internet access or shell access inside the seed;
- source self-modification;
- autonomous background workers.
