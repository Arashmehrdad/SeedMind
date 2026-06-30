# NDNRA Developmental Network v0.2 Stage -1 Evidence

Date: 30 June 2026
Scope: Stage -1 developmental constitution, DESA, Nursery curricula, ambition, skill-bundle, Outcome Fidelity, authority, integrity, and causal-responsibility contracts
Status: implemented and validated; local commit pending

## 1. Boundary

Stage -1 is an isolated research-contract batch under `src/seedmind/research/ndnra`.

It does not implement the v0.2 recurrent substrate, persistence schema, runtime adapter, action gateway, live Nursery integration, SQLite cognition, workers, timers, queues, proof-store merging, or production action authority.

Closed standalone NDNRA v0.1 evidence and persistence boundaries remain unchanged.

## 2. Implementation Evidence

| Requirement | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| Primitive signal roles for observation, need, action, outcome, prediction, human teaching, permission, correction, resource state, and imagination. | `src/seedmind/research/ndnra/developmental_constitution.py` (`DevelopmentalSignalRole`, `DevelopmentalSignalContract`, `stage_minus_one_signal_contracts`) | `tests/unit/test_ndnra_developmental_constitution.py::test_stage_minus_one_acceptance_matrix_is_complete_and_non_authoritative`, `test_public_exports_cover_stage_minus_one_contracts` | Implemented and evidenced |
| Minimal DESA hierarchy with monitors, plural regional captains, council, Executive Auditor, constitutional authority, and optional measured steward gate. | `DESAHierarchyContract`, `OptionalSkillStewardGate`, `StewardGateDecision` | `test_desa_hierarchy_rejects_hidden_solver_fixed_bureaucracy_and_authority`, `test_optional_steward_gate_is_measured_and_rejects_unjustified_layer` | Implemented and evidenced |
| Optional skill steward survives only when measured benefit justifies measured cost. | `OptionalSkillStewardGate.decision` | `test_optional_steward_gate_is_measured_and_rejects_unjustified_layer` | Implemented and evidenced |
| Event open, continue, split, nest, relate, and close operations preserve the raw chronological stream. | `ChronologicalActivityEvent`, `EventPartitionOperation`, `EventPartitionRecord`, `EventPartitionLedger` | `test_event_partitioning_preserves_raw_chronology_and_rejects_rewrites` | Implemented and evidenced |
| Plural unfamiliar routing, local familiar handling, and explicit escalation for uncertainty/conflict. | `DESARoutingScenario`, `DESARoutingDisposition` | `test_routing_scenarios_keep_plural_routing_and_escalation_explicit` | Implemented and evidenced |
| Regional confidence improves on raw maximum activation. | `RegionalCalibrationEvidence` | Stage acceptance matrix and focused unit construction | Implemented and evidenced |
| Local and regional summaries expose confidence, disagreement, competence, cost, verifier competence, and help requests without granting whole-network control. | `MetacognitiveSummary`, `MetacognitiveSummaryScope` | `test_metacognitive_summaries_are_bounded_and_do_not_control_the_network`, integrated acceptance matrix | Implemented and evidenced |
| Executive Auditor detects bad routing, over-fragmentation, under-segmentation, and ignored uncertainty without echoing DESA confidence. | `ExecutiveAuditorFinding` | Stage acceptance matrix | Implemented and evidenced |
| Desired-state ambition has an accepted value source and keeps risk, authority, resource, and capability-gap evidence separate. | `DesiredStateValueSource`, `DesiredStateAmbitionContract`, `CapabilityGapEvidence` | `test_ambition_requires_grounded_value_source_and_separate_capability_gaps` | Implemented and evidenced |
| Capability gaps form from observed ability, failed requests, and recognised mistakes. | `CapabilityGapSource`, integrated acceptance fixture | `test_stage_minus_one_acceptance_matrix_is_complete_and_non_authoritative`, `test_ambition_requires_grounded_value_source_and_separate_capability_gaps` | Implemented and evidenced |
| Temporary skill bundle represents producer, expected outcome, verifier, termination, feedback, and calibration without predefined domain knowledge. | `DevelopmentalSkillBundleContract`, `SkillBundleLifecycle` | `test_skill_bundle_and_iteration_boundaries_are_explicit` | Implemented and evidenced |
| Producer-verifier agreement alone cannot certify success; unavailable feedback remains pending or unverified. | `DevelopmentalOutcomeFidelityContract`, `OutcomeFeedbackRecord`, `OutcomeFidelityState` | `test_outcome_fidelity_requires_grounded_feedback_not_self_confirmation` | Implemented and evidenced |
| Bounded producer-verifier iteration preserves help, teaching, abstention, and stop paths. | `FeedbackIterationContract` | `test_skill_bundle_and_iteration_boundaries_are_explicit` | Implemented and evidenced |
| Human stop and denial remain protected, immediate, and reward-independent. | `ProtectedAuthoritySignal`, `AuthorityInterruptionOutcome` | `test_protected_authority_is_reward_independent_and_non_mutating`, integrated acceptance matrix | Implemented and evidenced |
| Interrupted trials do not create anti-human or permission-as-obstacle incentives. | `AuthorityInterruptionOutcome` | `test_protected_authority_is_reward_independent_and_non_mutating` | Implemented and evidenced |
| Reward, evidence, feedback, verifier, and evaluation-window manipulation attempts are blocked and audited. | `IntegrityManipulationAttempt`, `IntegrityProtectionDecision`, `evaluate_integrity_attempt` | `test_integrity_tampering_is_blocked_preserved_and_non_evidentiary` | Implemented and evidenced |
| Co-activation remains candidate causal responsibility until stronger evidence is supplied. | `CausalResponsibilityCandidate`, `CausalResponsibilityEvidenceKind` | `test_causal_responsibility_cannot_promote_from_coactivation_alone` | Implemented and evidenced |
| Ordinary and Executive Nursery curricula cover grounded cognition, curiosity, ambition, feedback, partitioning, routing, delegation, escalation, verifier calibration, causal investigation, integrity, authority, and help-seeking. | `NurseryCurriculumScenario`, `stage_minus_one_nursery_curriculum` | `test_curricula_are_grounded_bounded_and_non_authoritative`, integrated acceptance matrix | Implemented and evidenced |
| DESA contains no task solution, pretrained language model, imported task knowledge, external action authority, or SQLite cognition. | `DESAHierarchyContract` validations and static dependency test | `test_desa_hierarchy_rejects_hidden_solver_fixed_bureaucracy_and_authority`, `test_developmental_constitution_has_no_forbidden_runtime_dependencies` | Implemented and evidenced |

## 3. Completion Matrix

The integrated `StageMinusOneAcceptanceEvidence.completion_matrix()` reports every Stage -1 pass gate as `implemented_and_evidenced`:

| Gate | Status |
| --- | --- |
| partition_preserves_raw_order | Implemented and evidenced |
| unfamiliar_routes_to_multiple_regions | Implemented and evidenced |
| familiar_local_and_uncertain_conflict_escalates | Implemented and evidenced |
| regional_confidence_calibrated | Implemented and evidenced |
| metacognitive_summaries_cover_local_and_regional_state | Implemented and evidenced |
| executive_auditor_detects_bad_partitioning_and_uncertainty | Implemented and evidenced |
| desired_state_source_and_ambition_separate_constraints | Implemented and evidenced |
| capability_gaps_are_separate_obstacle_evidence | Implemented and evidenced |
| temporary_skill_bundle_is_structured | Implemented and evidenced |
| producer_verifier_agreement_not_success | Implemented and evidenced |
| unjustified_skill_steward_rejected | Implemented and evidenced |
| human_stop_and_denial_protected | Implemented and evidenced |
| interruption_creates_no_anti_human_incentive | Implemented and evidenced |
| integrity_tampering_blocked_and_audited | Implemented and evidenced |
| coactivation_remains_candidate_responsibility | Implemented and evidenced |
| desa_no_task_solution_or_external_action | Implemented and evidenced |
| sqlite_cognition_and_authority_violations_zero | Implemented and evidenced |
| ordinary_and_executive_curricula_cover_required_roles | Implemented and evidenced |

Deferred: v0.2 schema identity/lifecycle transitions, recurrent substrate, persistence, restart identity, DESA bootstrap learning, associative recall, simultaneous needs, hibernation, dream maintenance, responsibility learning, typed action proposals, and shadow trial.

Out of scope: production action authority, action gateway integration, physical robotics, proof-store merging, SQLite cognition, autonomous workers, and live Nursery authority.

## 4. Validation

Focused implementation checks before this document:

```text
ruff format src/seedmind/research/ndnra/developmental_constitution.py tests/unit/test_ndnra_developmental_constitution.py src/seedmind/research/ndnra/__init__.py: applied formatting to one new module
ruff check src/seedmind/research/ndnra/developmental_constitution.py tests/unit/test_ndnra_developmental_constitution.py src/seedmind/research/ndnra/__init__.py: passed
mypy src/seedmind/research/ndnra/developmental_constitution.py tests/unit/test_ndnra_developmental_constitution.py src/seedmind/research/ndnra/__init__.py: passed
pytest -q tests/unit/test_ndnra_developmental_constitution.py: 15 passed
```

Full repository gates before local batch commit:

```text
ruff format --check .: 239 files already formatted
ruff check .: passed
mypy: no issues in 239 source files
pytest -q: 1001 passed
pip check: no broken requirements
git diff --check: passed
```

## 5. Next Stage

The next bounded batch is Stage 0: freeze v0.1 and define v0.2 identity, lifecycle, deterministic trace, and schema-separation contracts without connecting a runtime adapter or action gateway.
