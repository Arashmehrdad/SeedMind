# SeedMind Week 10 Capacity Diagnosis Evidence

Date: 1 July 2026
Status: Corrected grounded evidence passed
Scope: original SeedMind Master Implementation Plan Week 10 only

## Correction Notice

The original `13140df` Week 10 evidence used scripted diagnostic timelines and
was not valid grounded evidence. The corrected implementation derives attempts,
progress, replay outcomes, demonstration effects, prediction evidence,
classification, and proposal generation from executed Nursery episodes.

The superseded scripted artifacts are preserved for audit under:

```text
artifacts/week10_capacity_diagnosis/superseded_scripted_evidence/
```

Those artifacts are marked
`valid_for_grounded_capacity_diagnosis=false`.

## Objective

Week 10 distinguishes temporary failure from sustained developmental blockage
and delays capacity growth until non-growth checks are exhausted. It diagnoses
and proposes only. It does not create, train, accept, route, or deploy a
specialist.

NDNRA remains frozen at source baseline
`b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a`. Corrected Week 10 does not import
from, modify, compare against, or require NDNRA.

## Implementation

Main corrected implementation:

- `src/seedmind/environment/transition.py` keeps angular flat-contact push
  resistance while preserving round-object behavior.
- `src/seedmind/growth/stagnation.py` keeps pure learning-progress window
  classification, with optional grounded provenance on attempts.
- `src/seedmind/growth/diagnostic_ladder.py` records the diagnostic ladder.
- `src/seedmind/growth/proposal.py` now requires evidence-derived proposal
  inputs and rejects incomplete evidence.
- `src/seedmind/growth/week10.py` executes bounded Nursery episodes, records
  action/outcome traces, persists real episodic memories, retrieves replay
  evidence, measures teacher demonstration effects, and exports grounded
  artifacts.
- `scripts/run_week10_capacity_diagnosis.py` reports separate runtime,
  repository, and boundary fields.

## Executed Seeds

```text
familiar_control=206,207,208,211
early=310,311,312,313
temporary=410,411,412,413,414,415,416,417,418,419,420,421
sustained=510,511,512,513,514,515,516,517,518,519,520,521
non_capacity=610,611,612,613
teacher_demonstration=900,901
```

Episode counts:

```text
early_cube_evidence=4
temporary_cube_recovery=13
sustained_cube_blockage=13
non_capacity_blockage=4
```

The temporary and sustained counts include isolated protected teacher
demonstration traces. All learning attempts reference entries in
`grounded_episode_traces.json`.

## Grounded Trace Evidence

Each committed Week 10 learning attempt now includes:

- episode ID;
- scenario seed and family;
- initial-state digest;
- object and target IDs;
- strategy ID;
- primitive action timeline;
- transition outcomes;
- initial/final object-target distance;
- measured progress;
- measured success;
- steps used;
- invalid or ineffective action count;
- prediction trace IDs and errors;
- help, replay, and demonstration influence;
- termination reason;
- trace digest.

Progress is calculated from actual geometry:

```text
progress=(initial_distance-final_distance)/initial_distance
```

## Scenario Results

Familiar control:

```text
success_rate=1.0000
frozen_skill_sha256_before=884c91209314c00169aff0186971a51ca773724accec0b298263561d81ecbc8e
frozen_skill_sha256_after=884c91209314c00169aff0186971a51ca773724accec0b298263561d81ecbc8e
```

Early evidence:

```text
classification=insufficient_evidence
proposal_generated=false
episodes=4
```

Temporary failure:

```text
classification=improving
proposal_generated=false
replay_progress_resumed=true
teacher_demonstration_completed_task=true
learner_before_mean_progress=0.1111111111111111
learner_after_mean_progress=1.0
```

Sustained blockage:

```text
classification=sustained_blockage
proposal_generated=true
diagnostic_ladder_completed=true
teacher_demonstration_completed_task=true
learner_before_mean_progress=0.0
learner_after_mean_progress=0.0
blockage_remained=true
```

Non-capacity blockage:

```text
classification=insufficient_evidence
proposal_generated=false
cases=ambiguous_request,impossible_geometry,resource_budget_exhaustion,unsafe_permission_blocked
```

## Replay And Demonstration

Replay uses the main SeedMind `EpisodicSQLiteStore` with events persisted from
actual Week 10 episode traces. Retrieved event IDs resolve back to source
episodes present in `grounded_episode_traces.json`.

Teacher demonstration uses the existing human-apprenticeship help contracts. The
teacher trace is executed in an isolated Nursery clone and completes the task in
both temporary and sustained families. Temporary learner performance improves
after replay/demonstration. Sustained learner performance remains blocked after
the demonstration, so reachability is proven without silently turning the
teacher trace into a specialist.

## Prediction Evidence

Every primitive action step records a real prediction comparison through
`seedmind.core.compare_prediction`. The diagnostic path uses a persistence
baseline prediction and compares it with the actual next Nursery observation.
Prediction evidence is therefore derived from predicted-versus-observed
transition data, not manually entered values.

## Proposal Derivation

The proposal is generated only for the sustained blockage case after evidence
proves:

- sustained blockage across three real progress windows;
- complete diagnostic ladder;
- grounded replay attempt;
- teacher reachability demonstration;
- no ongoing competence improvement;
- no ambiguity, safety, impossibility, or resource-budget cause;
- real prediction evidence;
- bounded strategy variants executed without creating capacity.

The resulting proposal remains:

```text
proposal_id=growth-week10-cube-policy-0001
status=proposed_not_authorised
candidate.type=skill_expert
candidate.parent_module=general_push_controller
candidate.created=false
```

## Acceptance

```text
environment_extension_pass=true
grounded_attempt_provenance_pass=true
learning_progress_pass=true
temporary_failure_classification_pass=true
sustained_blockage_classification_pass=true
diagnostic_ladder_pass=true
memory_replay_grounding_pass=true
teacher_demonstration_grounding_pass=true
prediction_evidence_pass=true
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

## Active Artifacts

```text
artifacts/week10_capacity_diagnosis/grounded_episode_traces.json
artifacts/week10_capacity_diagnosis/diagnostic_report.json
artifacts/week10_capacity_diagnosis/growth_proposal_record.json
artifacts/week10_capacity_diagnosis/learning_progress_windows.json
artifacts/week10_capacity_diagnosis/plateau_visualisation.svg
artifacts/week10_capacity_diagnosis/week10_acceptance_report.json
```

## Remaining Limits

Week 10 does not train a candidate specialist or prove that any future
specialist should be accepted. That belongs to original Week 11, which remains
not started. The prediction evidence is sufficient for Week 10 diagnosis but
uses a persistence baseline rather than a fully matured angular-contact
predictor.

## Validation

```text
.\.venv\Scripts\python.exe scripts\run_week10_capacity_diagnosis.py: passed
.\.venv\Scripts\python.exe -m pytest tests\unit\growth -q --basetemp .tmp_pytest\week10-grounded: 15 passed
.\.venv\Scripts\python.exe -m pytest tests\unit\test_transition_engine.py tests\unit\test_observation_adapter.py -q --basetemp .tmp_pytest\week10-env: 23 passed
.\.venv\Scripts\python.exe -m pytest tests\unit\skills tests\unit\contribution -q --basetemp .tmp_pytest\week8-week9-regression: 45 passed
.\.venv\Scripts\python.exe -m pytest -q --basetemp .tmp_pytest\full-week10-grounded: 1177 passed
.\.venv\Scripts\ruff.exe format --check .: 287 files already formatted
.\.venv\Scripts\ruff.exe check .: passed
.\.venv\Scripts\mypy.exe .: passed, no issues in 287 source files
.\.venv\Scripts\python.exe -m pip check: no broken requirements
git diff --check: passed with line-ending warnings for .gitignore and README.md only
```

Additional boundary checks:

```text
no .tmp artifact files
no temporary .tmp_pytest directory retained
no changes under src/seedmind/research/ndnra/
no Week 10 NDNRA, parallel_comparison, or parallel_operation import lines
no src/seedmind/growth/week11.py
no scripts/run_week11_specialist_growth.py
pylint not configured or installed
pre-commit not configured
```
