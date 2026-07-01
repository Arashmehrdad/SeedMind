# SeedMind Repository Wiki

## Current State

- Repository: `D:\Github\SeedMind`
- Program: original SeedMind main-product roadmap only
- Current closed stage: corrected original Week 10 grounded capacity diagnosis
- Next main-roadmap target: original Week 11 candidate specialist and growth
  gate
- Week 11: not started
- NDNRA: frozen historical research snapshot only

## Week 10 Correction

The original `13140df` Week 10 evidence used scripted diagnostic timelines and
was not valid grounded evidence. The corrected implementation derives attempts,
progress, replay outcomes, demonstration effects, prediction evidence,
classification, and proposal generation from executed Nursery episodes.

Superseded scripted artifacts are preserved at:

```text
artifacts/week10_capacity_diagnosis/superseded_scripted_evidence/
```

## Corrected Week 10 Evidence

Week 10 is closed by the main `seedmind.growth` package:

- angular objects use raw flat-contact push resistance;
- round-object behavior and familiar Week 8 control remain retained;
- every active `LearningAttempt` references an executed episode trace;
- strategy variants execute primitive actions in Nursery episodes;
- memory replay retrieves events persisted from real Week 10 episodes;
- teacher demonstration traces execute in isolated Nursery clones;
- prediction evidence comes from predicted-versus-observed transition
  comparisons;
- the sustained proposal is derived from complete evidence;
- no specialist, router, parameters, production mutation, Week 11 work, or NDNRA
  dependency is introduced.

Executed seeds:

```text
control=206,207,208,211
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

Acceptance:

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

## Scenario Outcomes

- Familiar control: success rate `1.0000`; frozen Week 8 skill hash unchanged.
- Early evidence: `insufficient_evidence`; no proposal.
- Temporary failure: `improving`; grounded replay and teacher demonstration
  restore measured progress; no proposal.
- Sustained blockage: `sustained_blockage`; teacher proves reachability; learner
  remains blocked; exactly one non-authoritative proposal.
- Non-capacity blockage: ambiguous request, impossible geometry,
  resource-budget exhaustion, and unsafe/permission-blocked cases stop early
  without capacity-growth proposal.

## Proposal

```text
proposal_id=growth-week10-cube-policy-0001
status=proposed_not_authorised
candidate.type=skill_expert
candidate.parent_module=general_push_controller
candidate.created=false
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

## NDNRA Boundary

NDNRA remains frozen at
`b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a`. Future SeedMind work must not add
NDNRA dependencies, comparison requirements, Stage 9 work, promotion, production
authority, or closure evidence requirements.

## Week 11 Boundary

Original Week 11 may investigate a candidate specialist and growth gate after
corrected Week 10. Week 11 is not started by this closure.

Explicitly not authorised by Week 10:

- creating, training, accepting, routing, or deploying a specialist;
- production architecture mutation;
- NDNRA capability work inside SeedMind;
- NDNRA Stage 9;
- future acceptance depending on NDNRA evidence;
- internet access or shell access inside the seed;
- source self-modification;
- autonomous background workers.
