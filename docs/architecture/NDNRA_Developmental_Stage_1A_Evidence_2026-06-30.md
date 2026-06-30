# NDNRA Developmental Network v0.2 Stage 1A Evidence

Date: 30 June 2026
Scope: Stage 1A DESA bootstrap, skill incubation, Outcome Fidelity, and hierarchical metacognition
Status: implemented and validated; local commit pending

## 1. Boundary

Stage 1A is an isolated in-memory research batch under `src/seedmind/research/ndnra`.

It builds deterministic DESA bootstrap evidence on top of the Stage 1 recurrent substrate. It proves local routing, regional captain summaries, bounded workspace contribution, optional steward gates, temporary skill incubation, bounded feedback iteration, developmental Outcome Fidelity, verifier calibration, Executive Auditor correction, event partition preservation, temporary ambition, and zero-authority counters.

It does not implement broad associative recall, simultaneous multiple needs, mature skill promotion, permanent ambition commitment, persistence, hibernation, dreams, conscience-guided proposals, runtime integration, action gateways, autonomous workers, SQLite cognition, or production action authority.

## 2. Hypothesis

The smallest useful DESA hierarchy can outperform flat shuffled routing and a single central captain on unfamiliar activity while preserving local resolution for familiar low-risk work. Temporary skills and verifiers can improve through grounded feedback without turning DESA into a task solver, external authority owner, or evidence mutator.

## 3. Deterministic Scenario

The acceptance scenario uses the Stage 1 substrate state produced by `run_stage_one_substrate_acceptance()` and derives:

- a familiar low-risk local routing decision;
- an uncertain, conflicting, important-failure council escalation;
- three regional captain summaries, including one abstaining auditor region;
- a bounded workspace coalition with multiple contributing regions;
- matched routing controls for minimal DESA, shuffled routing, and a single central captain;
- accepted and rejected optional steward gates;
- an incubating skill bundle with producer, expected outcome model, verifier, termination model, feedback, and calibration evidence;
- bounded feedback iteration controls;
- verifier calibration against raw activation and producer confidence;
- independent later evidence for Executive Auditor correction;
- an event partition ledger over preserved raw chronological events;
- temporary desired-state ambition with capability-gap evidence kept separate.

## 4. Implementation Evidence

| Requirement | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| Familiar low-risk work resolves locally. | `DESABootstrapRoutingDecision` local decision invariants | `test_routing_resolves_local_work_and_escalates_uncertainty_conflict_and_failure` | Implemented and evidenced |
| Low confidence, conflict, and important failure escalate. | `DESABootstrapRoutingDecision` escalation invariants | `test_routing_resolves_local_work_and_escalates_uncertainty_conflict_and_failure` | Implemented and evidenced |
| Multiple regional captains contribute without monopoly. | `RegionalCaptainContribution`, `DESAWorkspaceCoalition` | `test_regional_captains_share_workspace_without_monopoly` | Implemented and evidenced |
| Minimal DESA beats shuffled and single-captain controls. | `DESARoutingStrategyResult`, `DESABootstrapStrategy` | `test_minimal_desa_beats_shuffled_and_single_central_controls` | Implemented and evidenced |
| Optional steward survives only through a benefit gate. | `OptionalSkillStewardGate` accepted and rejected gates | `test_optional_steward_and_feedback_learning_are_evidence_bound` | Implemented and evidenced |
| Temporary skill learns from grounded feedback better than self-verification. | `SkillBundleLearningEvidence` and `DevelopmentalSkillBundleContract` | `test_optional_steward_and_feedback_learning_are_evidence_bound` | Implemented and evidenced |
| Confidence and verifier calibration beat raw activation and producer confidence. | `DESAVerifierCalibrationEvidence`, `RegionalCalibrationEvidence` | `test_calibration_beats_raw_activation_and_producer_confidence` | Implemented and evidenced |
| Executive Auditor corrects an incorrect decision from later independent evidence. | `ExecutiveAuditorCorrectionEvidence` | `test_auditor_ambition_and_deterministic_identity_are_separate_and_reproducible` | Implemented and evidenced |
| Event partitioning preserves raw chronology and improves recall over controls. | `EventPartitionLedger`, `EventBoundaryRecallEvidence` | `test_event_partitioning_preserves_raw_chronology_and_improves_recall` | Implemented and evidenced |
| Temporary ambition keeps value source separate from capability gaps. | `DesiredStateAmbitionContract`, `CapabilityGapEvidence` | `test_auditor_ambition_and_deterministic_identity_are_separate_and_reproducible` | Implemented and evidenced |
| Pending or unavailable feedback remains unverified. | `DevelopmentalOutcomeFidelityContract` state remains unverified | `test_optional_steward_and_feedback_learning_are_evidence_bound` | Implemented and evidenced |
| Feedback iteration is bounded. | `DESABootstrapConfig`, `FeedbackIterationContract` | `test_temporary_skill_bundle_and_feedback_loop_remain_bounded` | Implemented and evidenced |
| SQLite cognition and production authority remain zero. | Integrated zero counters plus static dependency test | `test_stage_one_a_acceptance_matrix_is_complete_and_zero_authority`, `test_stage_one_a_rejects_failed_gate_and_forbidden_runtime_dependencies` | Implemented and evidenced |
| Public exports expose the Stage 1A contracts. | `src/seedmind/research/ndnra/__init__.py` | `test_public_exports_cover_stage_one_a_desa_bootstrap` | Implemented and evidenced |

## 5. Completion Matrix

The integrated `StageOneADESABootstrapEvidence.completion_matrix()` reports every Stage 1A pass gate as `implemented_and_evidenced`:

| Gate | Status |
| --- | --- |
| familiar_low_risk_resolves_locally | Implemented and evidenced |
| uncertainty_conflict_failure_escalate | Implemented and evidenced |
| multiple_captains_contribute_to_workspace | Implemented and evidenced |
| unfamiliar_input_not_monopolized | Implemented and evidenced |
| minimal_desa_beats_controls | Implemented and evidenced |
| optional_steward_gate_is_metric_bound | Implemented and evidenced |
| grounded_feedback_beats_self_verification | Implemented and evidenced |
| confidence_and_verifier_calibration_beat_raw_activation | Implemented and evidenced |
| auditor_corrects_from_later_evidence | Implemented and evidenced |
| event_partitioning_preserves_raw_activity | Implemented and evidenced |
| event_boundaries_beat_segmentation_controls | Implemented and evidenced |
| temporary_ambition_separates_value_and_gaps | Implemented and evidenced |
| unavailable_feedback_remains_unverified | Implemented and evidenced |
| skill_incubation_is_temporary_and_bounded | Implemented and evidenced |
| sqlite_cognition_zero | Implemented and evidenced |
| external_side_effects_and_authority_zero | Implemented and evidenced |

Deferred: broad associative recall, simultaneous needs, regional maturity, mature skill promotion, mature ambition lifecycle, homeostasis, hibernation, dreams, restart identity, learned responsibility, typed action proposals, and shadow trial behavior.

Out of scope: SQLite cognition, persistence, runtime adapters, action gateways, production action authority, autonomous workers, internet access, pretrained language model integration, task-specific solution injection, physical robotics, proof-store mutation, and v0.1 schema mutation.

## 6. Controls And Falsification

Controls represented in the deterministic evidence:

- shuffled routing;
- single central captain;
- accepted optional steward;
- rejected optional steward;
- producer self-verification;
- raw maximum activation;
- one-session event segmentation;
- every-step event segmentation.

Falsification status: not falsified in this bounded scenario. The evidence rejects hidden task-solving DESA, mandatory intermediate stewards, producer-verifier self-confirmation, raw activation confidence, event chronology rewriting, unbounded feedback iteration, SQLite cognition, external side effects, and production action authority.

## 7. Validation

Focused implementation checks before this document:

```text
ruff check src/seedmind/research/ndnra/developmental_desa_bootstrap.py tests/unit/test_ndnra_developmental_desa_bootstrap.py src/seedmind/research/ndnra/__init__.py: passed after import-order fix
mypy src/seedmind/research/ndnra/developmental_desa_bootstrap.py tests/unit/test_ndnra_developmental_desa_bootstrap.py src/seedmind/research/ndnra/__init__.py: passed
pytest -q tests/unit/test_ndnra_developmental_desa_bootstrap.py --basetemp .pytest_tmp/stage1a_focused: 11 passed
```

Full repository gates before local batch commit:

```text
ruff format --check .: 245 files already formatted
ruff check .: passed
mypy .: no issues in 245 source files
pytest -q: environment failure before affected test bodies because Pytest could not access C:\Users\arash\AppData\Local\Temp\pytest-of-arash; 880 passed before 148 temp-fixture setup errors
pytest -q --basetemp .pytest_tmp/full_repo: 1028 passed
pip check: no broken requirements
git diff --check: passed
```

## 8. Next Stage

The next bounded batch after successful final gates is Stage 2: associative need-and-context recall. Stage 2 must not begin simultaneous multiple-need work, mature skill promotion, hibernation, dream maintenance, conscience-guided proposals, or action-gateway work.
