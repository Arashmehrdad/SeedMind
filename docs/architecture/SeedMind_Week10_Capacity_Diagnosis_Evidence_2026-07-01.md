# SeedMind Week 10 Capacity Diagnosis Evidence

Date: 1 July 2026
Status: Passed
Scope: original SeedMind Master Implementation Plan Week 10 only

## Objective

Complete original Week 10: distinguish temporary failure from sustained
developmental blockage, and delay any capacity growth until non-growth checks are
exhausted.

Week 10 has diagnosed and proposed. It has not grown, trained, accepted, routed,
or deployed a specialist.

NDNRA remains frozen at source baseline
`b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a`. Week 10 does not import from,
modify, compare against, or require NDNRA.

## Implementation

Main Week 10 implementation:

- `src/seedmind/environment/transition.py` adds angular-object flat-contact
  push resistance while preserving round-object behavior.
- `src/seedmind/growth/stagnation.py` defines deterministic
  learning-progress windows and plateau classifications.
- `src/seedmind/growth/diagnostic_ladder.py` defines the typed diagnostic
  ladder and early-stop states.
- `src/seedmind/growth/proposal.py` defines non-authoritative growth proposal
  records.
- `src/seedmind/growth/week10.py` runs deterministic Week 10 scenarios and
  exports evidence.
- `scripts/run_week10_capacity_diagnosis.py` executes the Week 10 gate.

## Cube-Like Raw Behavior

The environment now treats raw angular movable objects differently from round
objects. Angular pushes require lateral clearance at the contact and destination
cells, representing flat contact geometry and wall/corner sticking.

Observed transition evidence:

```text
round_open_push=pushed
angular_open_push=pushed
angular_wall_push=push_ineffective_contact
```

The policy-facing observation remains numeric and raw. It exposes occupancy,
blocking, movability, and normalized shape channels, not a semantic `cube` label.

## Progress Windows

Predeclared thresholds:

```text
window_size=4
minimum_windows_for_blockage=3
minimum_attempts_for_blockage=12
improvement_threshold=0.10
progress_resume_threshold=0.20
sustained_success_rate_ceiling=0.25
sustained_progress_ceiling=0.30
```

Each window records scenario family, attempt range, attempts, successes, success
rate, mean task progress, mean steps, mean prediction error, invalid or
ineffective actions, help requests, strategy, replay/demonstration involvement,
improvement, and plateau classification.

## Required Scenarios

Familiar control:

```text
seeds=206,207,208,211
success_rate=1.0000
frozen_skill_sha256_before=884c91209314c00169aff0186971a51ca773724accec0b298263561d81ecbc8e
frozen_skill_sha256_after=884c91209314c00169aff0186971a51ca773724accec0b298263561d81ecbc8e
```

Early evidence:

```text
scenario_family=early_cube_evidence
classification=insufficient_evidence
proposal_generated=false
```

Temporary failure:

```text
scenario_family=temporary_cube_recovery
classification=improving
proposal_generated=false
replay_progress_resumed=true
teacher_demonstration_improved_performance=true
```

Sustained blockage:

```text
scenario_family=sustained_cube_blockage
classification=sustained_blockage
proposal_generated=true
diagnostic_ladder_completed=true
```

Non-capacity blockage:

```text
scenario_family=ambiguous_non_capacity_blockage
classification=insufficient_evidence
proposal_generated=false
reason=ambiguous_goal_resource_limit_or_impossible_geometry
```

## Diagnostic Ladder

The sustained-blockage scenario completed every required diagnostic step:

1. Confirm task and success condition.
2. Confirm sufficient safe exploration.
3. Retrieve relevant memories.
4. Attempt existing frozen skill.
5. Try bounded alternative strategies.
6. Request help or demonstration.
7. Attempt bounded memory replay.
8. Check prediction quality.
9. Check learning progress.
10. Infer possible policy-capacity limitation.
11. Produce non-authoritative growth proposal.

The early and non-capacity scenarios stop early, so they cannot produce growth.
The temporary-failure scenario remains improving after replay and demonstration,
so growth is blocked.

## Strategy Variants

Bounded variants tested:

```text
variant-01: behind_object, budget=4
variant-02: left_side, contact_offset=1, reposition_before_push=true, budget=4
variant-03: right_side, contact_offset=-1, reposition_before_push=true, budget=4
variant-04: retreat_reapproach, alignment_tolerance=1, budget=4
```

All variants used primitive actions and safety boundaries only. They created no
specialist, router, parameters, or frozen-skill mutation.

## Memory Replay

Replay used grounded main SeedMind episodic memory through
`EpisodicSQLiteStore`. Retrieved events used the cue:

```text
context_code=angular_contact
event_type=action
minimum_significance=0.20
```

Temporary recovery replay changed strategy and progress resumed. Sustained
blockage replay found relevant memories but did not restore progress.

No NDNRA recall, proof store, or historical shadow evidence was used.

## Help And Demonstration

Help used the existing human apprenticeship policy. Repeated blocked attempts
with high uncertainty produced a protected teacher demonstration response.

Temporary recovery:

```text
help_requested=true
demonstration_provenance=protected_teacher_response_policy
performance_improved_afterward=true
blockage_remained=false
```

Sustained blockage:

```text
help_requested=true
demonstration_attempted=true
performance_improved_afterward=false
blockage_remained=true
```

## Prediction Quality And Alternative Diagnoses

Prediction error decreased across both temporary and sustained series, showing
that raw contact effects were becoming more predictable. Temporary progress then
resumed, so it is not a capacity limit. Sustained blockage retained low progress
after strategy variants, replay, help, and demonstration.

The growth proposal rejects alternative explanations as less likely:

- insufficient exploration;
- missing experience;
- incorrect prediction;
- poor strategy;
- ambiguous goal;
- inadequate teaching;
- optimisation failure;
- impossible task;
- resource limitation.

The remaining diagnosis is a possible policy-capacity limitation in the general
push controller, not proof that growth is already accepted.

## Growth Proposal

The only proposal is:

```text
proposal_id=growth-week10-cube-policy-0001
trigger_ambition=control_angular_object_position
candidate.type=skill_expert
candidate.parent_module=general_push_controller
candidate.created=false
status=proposed_not_authorised
```

The proposal requests Week 11 investigation. It creates no specialist and grants
no authority.

## Acceptance Fields

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

## Artifacts

- `artifacts/week10_capacity_diagnosis/diagnostic_report.json`
- `artifacts/week10_capacity_diagnosis/growth_proposal_record.json`
- `artifacts/week10_capacity_diagnosis/learning_progress_windows.json`
- `artifacts/week10_capacity_diagnosis/plateau_visualisation.svg`
- `artifacts/week10_capacity_diagnosis/week10_acceptance_report.json`

The SVG is generated from the same learning-progress window evidence and makes
temporary recovery diverge from sustained blockage.

## Limitations

Week 10 uses deterministic symbolic scenarios and a bounded diagnostic harness.
It does not train a candidate specialist or prove that any future specialist
should be accepted. That belongs to original Week 11.

## Validation

```text
.\.venv\Scripts\python.exe scripts\run_week10_capacity_diagnosis.py: passed
.\.venv\Scripts\python.exe -m pytest tests\unit\growth tests\unit\test_transition_engine.py tests\unit\test_observation_adapter.py -q --basetemp .tmp_pytest\week10-env: 38 passed
.\.venv\Scripts\python.exe -m pytest tests\unit\skills tests\unit\contribution -q --basetemp .tmp_pytest\week8-week9-regression: 45 passed
.\.venv\Scripts\python.exe -m pytest -q --basetemp .tmp_pytest\full-week10: 1177 passed
.\.venv\Scripts\ruff.exe format --check .: 287 files already formatted
.\.venv\Scripts\ruff.exe check .: passed
.\.venv\Scripts\mypy.exe .: no issues in 287 source files
.\.venv\Scripts\python.exe -m pip check: no broken requirements
git diff --check: passed with line-ending normalization warnings for .gitignore and README.md only
```
