# seedmind modules

## `scripts/run_ambition_formation.py`

Run the Week 5 teacher-demonstration ambition formation gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_body_discovery.py`

Run initial action-effect and body-channel discovery evidence.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_body_discovery_baseline.py`

Run the Week 3 targeted body-discovery comparison gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_curiosity_comparison.py`

Run the Week 4 curiosity-versus-random discovery comparison.

- Kind: python
- Functions/symbols: parse_args, build_trainer, main

## `scripts/run_curiosity_scoring.py`

Run a deterministic curiosity-scoring demonstration timeline.

- Kind: python
- Functions/symbols: parse_args, main, _prediction_error

## `scripts/run_familiar_training.py`

Run a reproducible SeedMind familiar-sequence training session.

- Kind: python
- Functions/symbols: parse_args, build_trainer, main

## `scripts/run_human_apprenticeship.py`

Run the Week 6 symbolic human-apprenticeship acceptance gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_live_curiosity_training.py`

Run curiosity-guided predictive training in the dynamic nursery.

- Kind: python
- Functions/symbols: parse_args, build_trainer, main

## `scripts/run_memory_belief_gate.py`

Run the Week 7 episodic-memory and belief-revision acceptance gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_ndnra_advice_gate.py`

Run bounded NDNRA advice and goal-gated repeated-growth acceptance.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_ndnra_contextual_mastery_gate.py`

Run contextual NDNRA redundancy and mastery acceptance.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_ndnra_heat_fan_gate.py`

Run the first NDNRA local-memory and need-recruitment acceptance gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_ndnra_multieffect_gate.py`

Run the NDNRA dynamic-effects and novel-composition acceptance gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_ndnra_persistent_shadow_gate.py`

Run the NDNRA non-SQL cross-session persistence acceptance gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_ndnra_shadow_integration_gate.py`

Run the NDNRA non-authoritative shadow-integration acceptance gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_ndnra_structural_growth_gate.py`

Run the NDNRA evidence-driven structural-growth acceptance gate.

- Kind: python
- Functions/symbols: parse_args, main

## `scripts/run_ndnra_unified_signals_gate.py`

Run the unified live-signal and restored-adaptive-state acceptance gate.

- Kind: python
- Functions/symbols: parse_args, main

## `src/seedmind/__init__.py`

SeedMind developmental intelligence runtime.

- Kind: python

## `src/seedmind/ambition/__init__.py`

Persistent developmental ambitions formed from grounded evidence.

- Kind: python

## `src/seedmind/ambition/demonstration.py`

Detect repeated goal-directed outcomes from raw teacher demonstrations.

- Kind: python
- Classes: DemonstrationDetectorConfig, ObservedDemonstration, OutcomeSignature, DemonstrationEvidence, _EvidenceAccumulator, GoalDirectedOutcomeDetector
- Functions/symbols: export_demonstration_evidence

## `src/seedmind/ambition/engine.py`

Persistent ambition records, commitment, budgets, and milestones.

- Kind: python
- Classes: AmbitionOrigin, AmbitionStatus, MilestoneStatus, MilestoneCode, AmbitionMilestone, AmbitionCandidate, AmbitionRecord, AmbitionManagerConfig, AmbitionManager
- Functions/symbols: save_ambition_manager, load_ambition_manager, export_ambition_dashboard, _config_payload, _record_payload, _record_from_payload, _required_mapping, _required_list, _required_str, _required_int, _required_float, _validate_identifier, _validate_score

## `src/seedmind/contracts/__init__.py`

Shared contracts between SeedMind, bodies, and environments.

- Kind: python

## `src/seedmind/contracts/action.py`

Primitive actions exposed by a SeedMind body adapter.

- Kind: python
- Classes: PrimitiveAction

## `src/seedmind/contracts/observation.py`

Body-independent observation contracts for SeedMind.

- Kind: python
- Classes: ObservationPacket
- Functions/symbols: _validate_channel

## `src/seedmind/contracts/spatial.py`

Body-independent spatial contracts for the symbolic nursery.

- Kind: python
- Classes: Direction, GridPosition

## `src/seedmind/core/__init__.py`

Predictive developmental core components for SeedMind.

- Kind: python

## `src/seedmind/core/prediction_error.py`

Prediction comparison and confidence objective for SeedMind.

- Kind: python
- Classes: PredictionComparison, PredictionLoss
- Functions/symbols: compare_prediction, prediction_objective

## `src/seedmind/core/predictive_state.py`

Recurrent predictive state core for SeedMind v0.1.

- Kind: python
- Classes: PredictiveCoreConfig, PredictiveCoreOutput, PredictiveSeedCore

## `src/seedmind/curiosity/__init__.py`

Learning-progress curiosity and bounded primitive experiment selection.

- Kind: python

## `src/seedmind/curiosity/comparison.py`

Matched live comparison of curiosity and random nursery exploration.

- Kind: python
- Classes: ScenarioFactory, PredictiveTrainer, TrainerFactory, CuriosityComparisonConfig, ExplorationActionCount, DiscoveryTimelinePoint, ExplorationTrialMetrics, CuriosityComparisonResult, CuriosityRandomComparisonExperiment
- Functions/symbols: export_curiosity_comparison_json, export_curiosity_comparison_csv, _trial_payload, _set_metrics

## `src/seedmind/curiosity/policy.py`

Bounded curiosity scoring and primitive experiment selection for SeedMind.

- Kind: python
- Classes: CuriosityConfig, CuriosityCandidate, CuriositySelection, CuriositySubsystem
- Functions/symbols: export_curiosity_timeline_json, export_curiosity_timeline_csv, _candidate_payload

## `src/seedmind/curiosity/session.py`

Live curiosity-guided predictive training in the SeedMind nursery.

- Kind: python
- Classes: ScenarioFactory, CuriosityTrainingConfig, CuriosityTrainingStepRecord, CuriosityTrainingResult, CuriosityTrainingSession
- Functions/symbols: export_curiosity_training_json, export_curiosity_training_csv

## `src/seedmind/environment/__init__.py`

Symbolic environment surrounding the SeedMind core.

- Kind: python

## `src/seedmind/environment/dynamic_scenario.py`

Reproducible Nursery v0 scenario with independent world processes.

- Kind: python
- Classes: DynamicNurseryScenarioFactory

## `src/seedmind/environment/entities.py`

Internal entities used by the symbolic SeedMind nursery.

- Kind: python
- Classes: EntityRole, ShapeCode, AgentState, EntityState

## `src/seedmind/environment/gymnasium_adapter.py`

Gymnasium adapter for the deterministic SeedMind Nursery runtime.

- Kind: python
- Classes: SeedMindNurseryEnv

## `src/seedmind/environment/observation.py`

Deterministic raw observation adapter for SeedMind Nursery v0.

- Kind: python
- Classes: NurseryObservationAdapter

## `src/seedmind/environment/processes.py`

Deterministic world processes that advance within a nursery tick.

- Kind: python
- Classes: WorldProcessOutcome, WorldProcessEvent, WorldProcessResult, WorldProcess, WorldProcessPipeline, CyclicEntityPatrolProcess, DirectionalFlowProcess, PeriodicBlockingToggleProcess
- Functions/symbols: _entity_by_id, _movement_blocked_outcome, _movement_event

## `src/seedmind/environment/runtime.py`

Runtime orchestration for SeedMind Nursery v0.

- Kind: python
- Classes: NurseryRuntimeStep, NurseryRuntime

## `src/seedmind/environment/scenario.py`

Deterministic scenario construction and evaluation for Nursery v0.

- Kind: python
- Classes: TargetOccupancy, NurseryScenario, NurseryScenarioFactory
- Functions/symbols: detect_target_occupancy

## `src/seedmind/environment/state.py`

Immutable deterministic world state for SeedMind Nursery v0.

- Kind: python
- Classes: NurseryState

## `src/seedmind/environment/teacher.py`

Deterministic teacher demonstrations for SeedMind Nursery v0.

- Kind: python
- Classes: TeacherPushDemonstrationProcess, TeacherDemonstrationScenarioFactory
- Functions/symbols: _entity_by_id

## `src/seedmind/environment/transition.py`

Deterministic primitive-action transitions for SeedMind Nursery v0.

- Kind: python
- Classes: TransitionOutcome, NurseryTransition, NurseryTransitionEngine

## `src/seedmind/human/__init__.py`

Symbolic human apprenticeship and calibrated help seeking.

- Kind: python

## `src/seedmind/human/apprenticeship.py`

Human apprenticeship, help seeking, caregiver memory, and metrics.

- Kind: python
- Classes: HelpReason, CaregiverEventType, HelpSeekingConfig, HelpContext, HelpDecision, TeacherResponse, CaregiverEvent, CaregiverMemory, ApprenticeshipMetrics, HelpSeekingPolicy, TeacherResponsePolicy, ApprenticeshipManager
- Functions/symbols: export_apprenticeship_report_json, export_apprenticeship_timeline_csv, _event_payload, _validate_unit_interval

## `src/seedmind/human/contracts.py`

Symbolic human-apprenticeship contracts and numeric signal encoding.

- Kind: python
- Classes: SupportLevel, HumanSignalCode, RequestIntentCode, VerificationRule, HumanRequest, HumanSignalFrame, HumanSignalCodec
- Functions/symbols: _validate_unit_interval

## `src/seedmind/integration/__init__.py`

Typed integration boundaries between validated SeedMind subsystems.

- Kind: python

## `src/seedmind/integration/advice_acceptance.py`

Acceptance gate for bounded NDNRA advice and goal-gated repeated growth.

- Kind: python
- Classes: AdviceTimelineRecord, AdviceAcceptanceResult, AdviceAcceptanceEvidence, _SafetyProbes
- Functions/symbols: run_advice_acceptance, export_advice_acceptance, _aggregate, _timeline_record, _growth_budget_exhaustion_probe_passed, _run_safety_probes, _write_json

## `src/seedmind/integration/advice_evidence.py`

Local evidence extraction for bounded NDNRA advice.

- Kind: python
- Functions/symbols: collect_local_evidence, _assemble_evidence, _positive

## `src/seedmind/integration/bounded_advice.py`

Bounded comparison of production and NDNRA candidates.

- Kind: python
- Classes: AdviceCode, AdviceConfig, AdviceEvidence, AdviceDecision, ConfidenceCalibration, BoundedAdvicePolicy
- Functions/symbols: _unit

## `src/seedmind/integration/candidate_session.py`

Live non-authoritative candidate comparison session.

- Kind: python
- Classes: CandidateStep, CandidateSessionResult
- Functions/symbols: run_candidate_session

## `src/seedmind/integration/comparison_oracle.py`

One-step outcome comparison that does not select production actions.

- Kind: python
- Classes: CandidateOutcome, CandidateComparison, NurseryOutcomeOracle
- Functions/symbols: _mean_change, _resource_cost, _transition_risk, _unit

## `src/seedmind/integration/consolidation_acceptance.py`

Live-shadow acceptance gate for persisted reversible NDNRA consolidation.

- Kind: python
- Classes: ConsolidationAcceptanceResult, ConsolidationAcceptanceEvidence
- Functions/symbols: run_consolidation_acceptance, export_consolidation_acceptance, _build_live_checkpoint, _record_later_contradiction, _action_value, _write_ascii_json

## `src/seedmind/integration/consolidation_proposal_lifecycle_acceptance.py`

Live-shadow acceptance for non-authoritative NDNRA proposal lifecycles.

- Kind: python
- Classes: ConsolidationProposalLifecycleShadowObservation, ConsolidationProposalLifecycleAcceptanceResult, ConsolidationProposalLifecycleAcceptanceEvidence, _LifecycleObservedShadowAdapter
- Functions/symbols: run_consolidation_proposal_lifecycle_acceptance, export_consolidation_proposal_lifecycle_acceptance, _build_live_lifecycle_request, _action_value, _write_ascii_json, _validate_code

## `src/seedmind/integration/consolidation_scheduling_acceptance.py`

Live-shadow acceptance for proposal-only NDNRA consolidation scheduling.

- Kind: python
- Classes: ConsolidationSchedulingShadowObservation, ConsolidationSchedulingAcceptanceResult, ConsolidationSchedulingAcceptanceEvidence, _SchedulingObservedShadowAdapter
- Functions/symbols: run_consolidation_scheduling_acceptance, export_consolidation_scheduling_acceptance, _build_live_schedule_request, _action_value, _write_ascii_json

## `src/seedmind/integration/contextual_mastery_acceptance.py`

Acceptance gate for contextual NDNRA traces and bounded mastery evidence.

- Kind: python
- Classes: ContextualMasteryAcceptanceResult, ContextualMasteryAcceptanceEvidence
- Functions/symbols: run_contextual_mastery_acceptance, export_contextual_mastery_acceptance, _persistence_probes, _write_legacy_v1, _write_trace_timeline, _write_json, _canonical_bytes

## `src/seedmind/integration/controlled_replay_restoration_acceptance.py`

Live acceptance for controlled replay and exact checkpoint restoration.

- Kind: python
- Classes: ControlledReplayRestorationAcceptanceResult, ControlledReplayRestorationAcceptanceEvidence
- Functions/symbols: run_controlled_replay_restoration_acceptance, export_controlled_replay_restoration_acceptance, _run_live_shadow, _approved_permit, _fresh_evidence, _stale_replay_is_rejected, _duplicate_replay_is_rejected, _replay_interruption_preserves_old, _terminal_lifecycle_evidence, _transition_request, _terminal_reuse_rejected, _corrupt_source_is_rejected, _restoration_interruption_recovers_new, _restoration_reuse_is_rejected, _active_state_equal, _with_dormancy, _growth_without_dormancy, _prediction_errors, _write_comparison_csv, _write_ascii_json, _raise_at

## `src/seedmind/integration/developmental_signals.py`

Typed live developmental signals for non-authoritative NDNRA integration.

- Kind: python
- Classes: LiveDevelopmentalSignals, LiveDevelopmentalSignalProvider
- Functions/symbols: _ambition_relevance, _action_controllability, _resource_pressure, _mean_absolute, _clamp_unit, _validate_unit

## `src/seedmind/integration/human_approved_consolidation_execution_acceptance.py`

Live acceptance for restart-safe human-approved NDNRA consolidation execution.

- Kind: python
- Classes: HumanApprovedConsolidationExecutionAcceptanceResult, HumanApprovedConsolidationExecutionAcceptanceEvidence
- Functions/symbols: run_human_approved_consolidation_execution_acceptance, export_human_approved_consolidation_execution_acceptance, _write_ascii_json

## `src/seedmind/integration/ndnra_shadow.py`

Non-authoritative NDNRA observation of the live SeedMind nursery loop.

- Kind: python
- Classes: ShadowScenarioFactory, NDNRAShadowConfig, ShadowSuggestion, ShadowStepRecord, NDNRAShadowSessionConfig, NDNRAShadowSessionResult, NDNRAShadowAdapter, NDNRAShadowSession
- Functions/symbols: _availability_fact, _assembly_id, _mean_absolute, _resource_cost, _clamp_unit, _validate_unit

## `src/seedmind/integration/persistent_shadow_experiment.py`

Cross-session NDNRA shadow-memory persistence acceptance experiment.

- Kind: python
- Classes: PersistentShadowResult, PersistentShadowEvidence
- Functions/symbols: run_persistent_shadow_experiment, export_persistent_shadow_evidence, _derive_growth_state, _total_assembly_evidence, _build_trainer, _write_ascii_json

## `src/seedmind/integration/restart_safe_proposal_memory_acceptance.py`

Restart and live-shadow acceptance for persisted NDNRA proposal memory.

- Kind: python
- Classes: RestartSafeProposalMemoryObservation, RestartSafeProposalMemoryAcceptanceResult, RestartSafeProposalMemoryAcceptanceEvidence, _RestartRevalidatingShadowAdapter
- Functions/symbols: run_restart_safe_proposal_memory_acceptance, export_restart_safe_proposal_memory_acceptance, _add_independent_lifecycle_evidence, _legacy_migration_is_empty, _checksum_corruption_falls_back, _relational_corruption_falls_back, _complete_fallback, _read_json_object, _require_object, _write_envelope, _write_ascii_json

## `src/seedmind/integration/shadow_experiment.py`

End-to-end baseline comparison for NDNRA shadow-mode integration.

- Kind: python
- Classes: ShadowComparisonResult
- Functions/symbols: run_shadow_comparison, export_shadow_comparison_evidence, _build_trainer, _write_ascii_json

## `src/seedmind/integration/unified_shadow.py`

Unified non-authoritative NDNRA shadow session with live developmental signals.

- Kind: python
- Classes: UnifiedShadowConfig, UnifiedShadowStepRecord, UnifiedShadowResult, NDNRALiveShadowAdapter, UnifiedDevelopmentalShadowSession
- Functions/symbols: _assembly_id, _availability_fact, _positive_intensity, _validate_unit

## `src/seedmind/integration/unified_signal_experiment.py`

End-to-end gate for live developmental signals and restored adaptive state.

- Kind: python
- Classes: UnifiedSignalExperimentResult, UnifiedSignalEvidence
- Functions/symbols: run_unified_signal_experiment, export_unified_signal_evidence, _build_signal_provider, _adopted_ambition_manager, _most_dormant_assembly, _build_trainer, _write_ascii_json

## `src/seedmind/memory/__init__.py`

Episodic SQLite memory, significance, retrieval, and beliefs.

- Kind: python

## `src/seedmind/memory/beliefs.py`

Evidence-linked belief formation and contradiction detection.

- Kind: python
- Classes: BeliefRegistryConfig, BeliefRegistry
- Functions/symbols: _belief_id, _belief_from_row, _evidence_from_row

## `src/seedmind/memory/inspector.py`

Inspectable JSON and CSV views for episodic memory and beliefs.

- Kind: python
- Functions/symbols: export_memory_inspector_json, export_belief_evidence_csv, _event_payload, _belief_payload, _evidence_payload

## `src/seedmind/memory/models.py`

Typed episodic-memory and belief records for SeedMind.

- Kind: python
- Classes: EpisodicEventType, BeliefEvidencePolarity, BeliefStatus, SignificanceFeatures, EpisodicEventDraft, EpisodicEvent, MemoryQuery, BeliefProposition, BeliefRecord, BeliefEvidence, ContradictionRecord
- Functions/symbols: _validate_identifier, _validate_unit_interval

## `src/seedmind/memory/significance.py`

Transparent significance scoring for episodic memory.

- Kind: python
- Classes: SignificanceConfig, SignificanceScorer

## `src/seedmind/memory/store.py`

Versioned SQLite episodic store and contextual retrieval.

- Kind: python
- Classes: EpisodicSQLiteStore
- Functions/symbols: _event_from_row, _payload_from_json, _optional_bool_to_database, _optional_bool_from_database

## `src/seedmind/perception/__init__.py`

Body-independent perception components for SeedMind.

- Kind: python

## `src/seedmind/perception/symbolic_encoder.py`

Learned encoding for raw symbolic SeedMind observations.

- Kind: python
- Classes: SymbolicInputSpec, SymbolicObservationEncoder

## `src/seedmind/research/__init__.py`

Isolated research prototypes that do not alter the production runtime.

- Kind: python

## `src/seedmind/research/ndnra/__init__.py`

Need-Driven Neural Recruitment Architecture research prototype.

- Kind: python

## `src/seedmind/research/ndnra/activity_maintenance.py`

Bounded memory accessibility maintenance from real, replayed, or imagined activity.

- Kind: python
- Classes: ActivityMaintenanceConfig, ActivityMaintenanceRequest, ActivityMaintenanceDecision, ActivityMaintenanceLedger
- Functions/symbols: _decision_id, _require_mapping, _require_list, _require_string, _require_int, _require_float, _require_bool, _require_string_list, _validate_sorted_unique_codes, _validate_code, _validate_unit

## `src/seedmind/research/ndnra/adaptive.py`

Operational adaptive state restored alongside an NDNRA local graph.

- Kind: python
- Classes: AdaptiveRuntimeConfig, AdaptiveUpdate, ActivityMaintenanceApplication, PressureDischarge, NDNRARuntimeAdaptiveState
- Functions/symbols: _validate_unit, _validate_signed

## `src/seedmind/research/ndnra/composition.py`

Need-driven composition over local multidimensional experience assemblies.

- Kind: python
- Classes: ExperienceAssembly, SpecialistInteraction, MultidimensionalExperienceGraph, CompositionCandidate, CompositionResult, _SearchState, NeedDrivenComposer
- Functions/symbols: _scale_effects, _validate_code, _validate_facts

## `src/seedmind/research/ndnra/consolidation.py`

Pure retention-gated consolidation eligibility contracts for NDNRA.

- Kind: python
- Classes: ConsolidationRejectionReason, ConsolidationCandidate, ConsolidationEligibilityPolicy, ConsolidationEligibility
- Functions/symbols: _append_profile_rejections, _validated_source_ids, _resolve_supporting_traces, _available_codes, _candidate_id, _add_reason, _valid_requested_change, _meets_minimum, _unit_meets_minimum, _count_meets_minimum, _is_finite_number, _validate_unit, _validate_positive_unit, _validate_sorted_unique_codes, _validate_code, _is_valid_code

## `src/seedmind/research/ndnra/consolidation_application.py`

Atomic bounded application of eligible NDNRA consolidation proposals.

- Kind: python
- Classes: ConsolidationStructureState, ConsolidationStateSnapshot, ConsolidationApplicationResult, ConsolidationApplicationState
- Functions/symbols: _validated_candidate, _updated_state, _validated_identifiers, _validated_states, _validate_state_collection, _validate_state_mapping, _validate_sorted_unique_codes, _find_state, _snapshot_ids, _validate_code, _validate_unit

## `src/seedmind/research/ndnra/consolidation_execution_approval.py`

Explicit human approval contracts for bounded NDNRA consolidation execution.

- Kind: python
- Classes: ConsolidationExecutionApprovalRequest, ConsolidationExecutionPermit, ConsolidationExecutionApprovalPolicy
- Functions/symbols: _permit_id, _validate_code, _validate_nonnegative_int

## `src/seedmind/research/ndnra/consolidation_execution_commit.py`

Atomic human-approved application of one current NDNRA consolidation permit.

- Kind: python
- Classes: ConsolidationApplicationTarget, ConsolidationExecutionCommitRequest, ConsolidationExecutionCommitReceipt, ConsolidationExecutionCommitResult, ConsolidationExecutionCommitPolicy
- Functions/symbols: _interrupt, _restore_failed_application, _execution_id, _normalized_codes, _validate_code, _validate_nonnegative_int

## `src/seedmind/research/ndnra/consolidation_execution_durable_commit.py`

Durable restart-safe commit of one explicitly approved consolidation execution.

- Kind: python
- Classes: ConsolidationExecutionDurableCommitResult, ConsolidationExecutionDurableCommitPolicy
- Functions/symbols: _matches_persisted_boundaries, _matches_loaded_result, _matches_expected, _restore_application_state, _interrupt

## `src/seedmind/research/ndnra/consolidation_execution_permit_lifecycle.py`

Immutable lifecycle state for human-approved NDNRA execution permits.

- Kind: python
- Classes: ConsolidationExecutionPermitLifecycleAction, ConsolidationExecutionPermitLifecycleStatus, ConsolidationExecutionPermitTransitionRequest, ConsolidationExecutionPermitTransitionDecision, ConsolidationExecutionPermitLifecycleRecord, ConsolidationExecutionPermitLifecycleRegistry
- Functions/symbols: _status_for, _validate_transition_episode, _transition_decision_id, _validate_code, _validate_nonnegative_int

## `src/seedmind/research/ndnra/consolidation_execution_persistence.py`

Versioned restart-safe persistence for bounded NDNRA execution evidence.

- Kind: python
- Classes: NDNRAExecutionCheckpoint
- Functions/symbols: _canonical_registry, _restore_registry, _restore_record, _restore_transition, _restore_permit, _restore_revalidation, _restore_receipt, _identity, _require_mapping, _require_list, _require_string, _require_int, _require_bool, _require_string_list

## `src/seedmind/research/ndnra/consolidation_interference_experiment.py`

Bounded experiment for consolidation, interference, and source-gated replay.

- Kind: python
- Classes: ConsolidationInterferenceCondition, ConsolidationInterferenceConfig, OverlappingLessonMemorySnapshot, ConsolidationInterferenceConditionResult, ConsolidationInterferenceExperimentResult, ConsolidationInterferenceExperimentEvidence, _OverlappingLessonMemory
- Functions/symbols: run_consolidation_interference_experiment, _build_old_lesson_ledger, _train_old_lesson, _run_condition, _aligned_lesson_target, _effective_learning_rate, _clamp_signed, _validate_code, _validate_unit, _validate_signed

## `src/seedmind/research/ndnra/consolidation_persistence.py`

Versioned persistence contracts for bounded NDNRA consolidation state.

- Kind: python
- Classes: ConsolidationRollbackAuditRecord, NDNRAConsolidationCheckpoint
- Functions/symbols: restore_consolidation_application, restore_consolidation_state_snapshot, _application_snapshot, _restore_application, _restore_candidate, _restore_mastery_profile, _restore_state_snapshot, _restore_structure_state, _state_identity_sets, _require_mapping, _require_list, _require_string, _require_bool, _require_int, _require_nonnegative_int, _require_float, _require_nonnegative_float, _require_unit, _require_string_list, _validate_sorted_unique_codes, _validate_code, _validate_unit

## `src/seedmind/research/ndnra/consolidation_portfolio.py`

Pure multi-lesson prioritisation for NDNRA consolidation proposals.

- Kind: python
- Classes: ConsolidationPortfolioItem, ConsolidationPortfolioItemDecision, ConsolidationPortfolioDecision, ConsolidationPortfolioPolicy
- Functions/symbols: _validated_items, _lesson_key, _priority_key

## `src/seedmind/research/ndnra/consolidation_proposal_history.py`

Immutable in-memory history for NDNRA consolidation proposal review.

- Kind: python
- Classes: ConsolidationProposalLifecycleRecord
- Functions/symbols: _validate_history

## `src/seedmind/research/ndnra/consolidation_proposal_lifecycle.py`

Pure review-only lifecycle decisions for NDNRA consolidation proposals.

- Kind: python
- Classes: ConsolidationProposalReviewAction, ConsolidationProposalLifecycleStatus, ConsolidationProposalReviewRequest, ConsolidationProposalReviewDecision, ConsolidationProposalReviewPolicy
- Functions/symbols: _status_for, _decision_id, _validate_code, _validate_nonnegative_int

## `src/seedmind/research/ndnra/consolidation_proposal_lifecycle_experiment.py`

Deterministic strategy comparison for NDNRA proposal lifecycle management.

- Kind: python
- Classes: ConsolidationProposalLifecycleStrategy, ConsolidationProposalLifecycleEvent, ConsolidationProposalLifecycleStrategyResult, ConsolidationProposalLifecycleExperimentResult
- Functions/symbols: run_consolidation_proposal_lifecycle_experiment, export_consolidation_proposal_lifecycle_experiment, _run_strategy, _strategy_result, _event, _review_request, _evolving_proposals, _trace, _validate_code, _validate_nonnegative_int

## `src/seedmind/research/ndnra/consolidation_proposal_management.py`

Bounded in-memory management for NDNRA consolidation proposal lifecycles.

- Kind: python
- Classes: ConsolidationProposalManagementAction, ConsolidationProposalDisposition, ConsolidationProposalManagementRequest, ConsolidationProposalManagementDecision, ConsolidationProposalManagedRecord, ConsolidationProposalLifecycleRegistry
- Functions/symbols: _validate_replacement, _management_decision, _disposition_for, _latest_lifecycle_episode, _validate_code, _validate_nonnegative_int, _validate_positive_int

## `src/seedmind/research/ndnra/consolidation_proposal_persistence.py`

Versioned checkpoint codec for restart-safe NDNRA proposal lifecycles.

- Kind: python
- Classes: NDNRAProposalLifecycleCheckpoint
- Functions/symbols: restore_consolidation_schedule_proposal, restore_consolidation_candidate, restore_mastery_profile, _restore_registry, _restore_managed_record, _restore_lifecycle_record, _restore_review_decision, _restore_management_decision, _restore_proposal, _restore_candidate, _restore_mastery_profile, _management_decision_id, _validate_replacement_links, _json_ready, _require_mapping, _require_list, _require_string, _require_bool, _require_int, _require_nonnegative_int, _require_positive_int, _require_float, _require_nonnegative_float, _require_unit, _require_string_list, _validate_sorted_unique_codes

## `src/seedmind/research/ndnra/consolidation_proposal_revalidation.py`

Pure restart-time revalidation for persisted NDNRA proposal lifecycles.

- Kind: python
- Classes: ConsolidationProposalRevalidationStatus, ConsolidationProposalRevalidationDecision, ConsolidationProposalRevalidationReport, ConsolidationProposalRevalidationPolicy
- Functions/symbols: _source_events_available, _validated_newer_proposals, _select_superseding_proposal, _normalized_codes, _add_reason, _decision_id, _validate_code, _validate_nonnegative_int

## `src/seedmind/research/ndnra/consolidation_reopening.py`

Pure contradiction-driven reopening and atomic consolidation rollback.

- Kind: python
- Classes: ConsolidationReopeningTrigger, ConsolidationReopeningPolicy, ConsolidationReopeningDecision, ConsolidationRollbackResult
- Functions/symbols: rollback_consolidation, _validate_trace_matches_candidate, _trace_is_contradictory, _rollback_id, _snapshot_payload, _state_payload, _snapshot_ids, _validate_sorted_unique_codes, _validate_code, _validate_unit

## `src/seedmind/research/ndnra/consolidation_scheduling.py`

Pure proposal-only scheduling policy for bounded NDNRA consolidation.

- Kind: python
- Classes: ConsolidationScheduleStatus, ConsolidationScheduleRequest, ConsolidationSchedulingContext, ConsolidationScheduleProposal, ConsolidationScheduleDecision, ConsolidationSchedulingPolicy
- Functions/symbols: _proposal_id, _validate_sorted_unique_codes, _validate_code, _validate_nonnegative_int, _validate_positive_int, _validate_positive_unit

## `src/seedmind/research/ndnra/consolidation_scheduling_experiment.py`

Deterministic proposal-only experiment for NDNRA consolidation scheduling.

- Kind: python
- Classes: ConsolidationSchedulingStrategy, ConsolidationSchedulingExperimentConfig, ConsolidationSchedulingProposalRecord, ConsolidationSchedulingStrategyResult, ConsolidationSchedulingExperimentResult
- Functions/symbols: run_consolidation_scheduling_experiment, export_consolidation_scheduling_experiment, _strategy_result, _candidate_for, _is_fixed_window, _lesson_key, _requests, _evidence_arrivals, _trace

## `src/seedmind/research/ndnra/contextual_consequence.py`

Real consequence comparison and context-specific action competence.

- Kind: python
- Classes: ExperienceOrigin, ConsequenceDirection, ActionConsequenceAssessment, ActionCompetenceUpdate, ContextualActionCompetenceRecord, ContextualActionCompetenceLedger
- Functions/symbols: _need_alignment, _record_id, _identity, _effect_snapshot, _validate_effects, _validate_code, _validate_unit

## `src/seedmind/research/ndnra/contextual_consequence_transfer.py`

Bounded contextual transfer over exact learned consequence records.

- Kind: python
- Classes: ConsequencePredictionMode, ContextualTransferConfig, ContextSimilarityEvidence, ContextTransferSourceEvidence, TransferredEffectEvidence, ContextualTransferPrediction, BoundedContextualTransferPolicy
- Functions/symbols: _vector_similarity, _set_similarity, _weighted_similarity, _context_id, _prediction_id, _identity, _effect_snapshot, _validate_effects, _validate_sorted_unique_codes, _validate_code, _validate_unit, _validate_signed_unit

## `src/seedmind/research/ndnra/contextual_mastery_experiment.py`

Bounded experiment for contextual redundancy, transfer, and mastery.

- Kind: python
- Classes: ContextualMasteryExperimentResult, ContextualMasteryExperimentEvidence
- Functions/symbols: run_contextual_mastery_experiment, _learn, _identity_conflict_is_blocked, _context, _route_switches, _route_snapshots

## `src/seedmind/research/ndnra/contextual_memory.py`

Contextual experience traces and bounded mastery evidence for NDNRA.

- Kind: python
- Classes: ContextualRecordCode, EventIdentity, ContextSignature, ContextualExperienceTrace, ContextualLearningResult, LessonIdentity, MasteryProfile, RouteSupport, _GroupEvidence, ContextualExperienceLedger
- Functions/symbols: _jaccard, _quantize, _validate_code, _require_mapping, _require_list, _require_string, _require_bool, _require_int, _require_float, _require_string_list, _require_int_list

## `src/seedmind/research/ndnra/controlled_checkpoint_restoration.py`

Exact durable restoration of one checksum-verified complete brain envelope.

- Kind: python
- Classes: ControlledCheckpointRestorationRequest, ControlledCheckpointRestorationDurableResult, ControlledCheckpointRestorationPolicy
- Functions/symbols: _validate_complete_loaded, _validate_request_against_target, _validate_fresh_evidence, _matches_restored_state, _same_complete_state, _interrupt, _validate_code, _validate_checksum, _validate_nonnegative_int

## `src/seedmind/research/ndnra/controlled_replay_restoration_approval.py`

Human approval contracts for bounded controlled replay and restoration.

- Kind: python
- Classes: ControlledReplayRestorationOperation, ControlledReplayRestorationTarget, ControlledReplayRestorationEvidence, ControlledReplayRestorationApprovalRequest, ControlledReplayRestorationPermit, ControlledReplayRestorationApprovalPolicy
- Functions/symbols: _validate_target_against_evidence, _identity, _validate_code, _validate_checksum, _validate_nonnegative_int, _validate_sorted_unique_codes

## `src/seedmind/research/ndnra/controlled_replay_restoration_permit_lifecycle.py`

Immutable lifecycle state for controlled replay and restoration permits.

- Kind: python
- Classes: ControlledReplayRestorationPermitLifecycleAction, ControlledReplayRestorationPermitLifecycleStatus, ControlledReplayRestorationPermitTransitionRequest, ControlledReplayRestorationPermitTransitionDecision, ControlledReplayRestorationPermitLifecycleRecord, ControlledReplayRestorationPermitLifecycleRegistry
- Functions/symbols: _validate_request_matches_permit, _status_for, _validate_transition_episode, _transition_decision_id, _reject_authority, _validate_code, _validate_checksum, _validate_nonnegative_int

## `src/seedmind/research/ndnra/controlled_replay_restoration_persistence.py`

Restart-safe persistence for controlled replay and restoration evidence.

- Kind: python
- Classes: ControlledCheckpointRestorationReceipt, NDNRAReplayRestorationCheckpoint
- Functions/symbols: _canonical_registry, _restore_registry, _restore_record, _restore_transition, _restore_permit, _restore_target, _restore_evidence, _restore_replay_receipt, _restore_replay_item_receipt, _restore_restoration_receipt, _identity, _reject_authority, _require_mapping, _require_list, _require_string, _require_int, _require_float, _require_bool, _require_string_list, _validate_code, _validate_checksum, _validate_nonnegative_int

## `src/seedmind/research/ndnra/controlled_retention_replay.py`

Single-use bounded replay of exact real activity for dormancy maintenance.

- Kind: python
- Classes: ControlledRetentionReplayWorkItem, ControlledRetentionReplayRequest, ControlledRetentionReplayItemReceipt, ControlledRetentionReplayReceipt, ControlledRetentionReplayResult, ControlledRetentionReplayOperation
- Functions/symbols: _item_receipt, _validate_request_against_target, _validate_fresh_evidence, _replay_activity_event_id, _receipt_id, _identity, _reject_authority, _validate_sorted_unique_codes, _validate_code, _validate_checksum, _validate_nonnegative_int, _validate_unit

## `src/seedmind/research/ndnra/controlled_retention_replay_durable.py`

Durable restart-safe commit of one controlled retention replay.

- Kind: python
- Classes: ControlledRetentionReplayDurableResult, ControlledRetentionReplayDurablePolicy
- Functions/symbols: _matches_persisted_boundaries, _matches_loaded_result, _matches_expected, _interrupt

## `src/seedmind/research/ndnra/effects.py`

Dynamically expanding sparse effect memory for NDNRA research.

- Kind: python
- Classes: EffectObservation, EffectEstimate, SparseEffectMemory, NeedDimension, EffectNeed, LocalEffectLink
- Functions/symbols: combine_projected_effects, _require_mapping, _require_string, _require_int, _require_float, _validate_code, _validate_unit_interval, _validate_signed_unit

## `src/seedmind/research/ndnra/experiment.py`

Training, evaluation, and evidence for the NDNRA heat-fan prototype.

- Kind: python
- Classes: RecallStepRecord, RecallEpisodeResult, TeacherTrainingResult, NDNRAExperimentResult
- Functions/symbols: train_teacher_demonstrations, evaluate_recall, run_ndnra_heat_fan_experiment, export_ndnra_evidence, _need_persisted_until_cooling, _failed_recall_cost, _write_ascii_json

## `src/seedmind/research/ndnra/growth.py`

Evidence-driven structural growth for the isolated NDNRA prototype.

- Kind: python
- Classes: StructuralGrowthConfig, GrowthAttemptRecord, GrowthOutcome, EvidenceDrivenGrowthController
- Functions/symbols: grow_random_specialist, _validate_unit, _validate_signed

## `src/seedmind/research/ndnra/growth_cycle.py`

Goal-gated multi-step structural growth and pressure discharge.

- Kind: python
- Classes: GrowthCycleConfig, GrowthResolution, GoalGatedGrowthCycle
- Functions/symbols: _validate_unit

## `src/seedmind/research/ndnra/growth_experiment.py`

Third NDNRA experiment: evidence-driven specialist neuron growth.

- Kind: python
- Classes: StructuralGrowthExperimentResult
- Functions/symbols: structural_cooling_need, build_capacity_limited_graph, run_ndnra_structural_growth_experiment, export_structural_growth_evidence, _duplicate_growth_is_blocked, _write_ascii_json

## `src/seedmind/research/ndnra/heat_world.py`

Deterministic heat-and-fan world for the NDNRA research prototype.

- Kind: python
- Classes: HeatWorldState, HeatTransition, HeatFanWorld

## `src/seedmind/research/ndnra/learned_consequence_model.py`

Bounded single-step consequence learning from exact real context-action evidence.

- Kind: python
- Classes: CalibrationDirection, LearnedConsequenceModelConfig, ConsequenceModelObservation, ConsequencePredictionRequest, ConsequencePrediction, ConsequencePredictionEvaluation, ConsequenceModelUpdate, _EffectStatistics, ContextActionConsequenceRecord, LearnedConsequenceModel
- Functions/symbols: _record_id, _context_id, _prediction_id, _identity, _effect_snapshot, _validate_effects, _validate_sorted_unique_codes, _validate_code, _validate_unit

## `src/seedmind/research/ndnra/models.py`

Local neural state and experiment records for the NDNRA prototype.

- Kind: python
- Classes: HeatAction, HeatContext, NeuronKind, LocalNeuron, LocalSynapse, NeedPulse, RecallResult, ModulationSummary, GrowthPressure
- Functions/symbols: _validate_unit_interval, _validate_signed_unit

## `src/seedmind/research/ndnra/multi_growth_experiment.py`

Goal-gated multi-step structural growth experiment.

- Kind: python
- Classes: MultiGrowthExperimentResult
- Functions/symbols: run_multi_growth_experiment, evaluate_unresolved_budget_exhaustion, _build_graph, _complex_need, _satisfaction, _duplicate_membership_is_blocked

## `src/seedmind/research/ndnra/multieffect_experiment.py`

Second NDNRA experiment: dynamic effects and novel solution composition.

- Kind: python
- Classes: MultieffectExperimentResult
- Functions/symbols: cooling_need, cleanliness_need, build_multieffect_graph, build_intended_effect_only_baseline, run_ndnra_multieffect_experiment, export_multieffect_evidence, _candidate_row, _write_ascii_json

## `src/seedmind/research/ndnra/network.py`

Sparse local neural graph for the isolated NDNRA heat-fan prototype.

- Kind: python
- Classes: LocalNeuralGraphConfig, LocalNeuralGraph
- Functions/symbols: _context_neuron_id, _action_neuron_id

## `src/seedmind/research/ndnra/persistence.py`

Versioned non-SQL persistence for reconstructing an NDNRA brain graph.

- Kind: python
- Classes: BrainLoadStatus, NDNRAGrowthState, BrainSaveResult, BrainLoadResult, NDNRABrainStore
- Functions/symbols: _interrupt, _restore_graph, _restore_assembly, _restore_specialist, _checksum, _canonical_bytes, _require_mapping, _require_list, _require_string, _require_int, _require_float, _require_string_list, _require_numeric_list, _validate_code, _validate_unit, _validate_signed

## `src/seedmind/safety/__init__.py`

SeedMind safety package.

- Kind: python

## `src/seedmind/self_model/__init__.py`

Online action-effect evidence and initial SeedMind self-model.

- Kind: python

## `src/seedmind/self_model/action_effects.py`

Action-effect evidence and initial self-model discovery for SeedMind.

- Kind: python
- Classes: SelfModelConfig, ActionEffectEstimate, BodySensorEstimate, SelfModelSnapshot, _ActionAccumulator, SelfModelRegistry
- Functions/symbols: export_self_model_json, export_action_effects_csv

## `src/seedmind/self_model/baseline.py`

Matched-budget body-discovery comparison against random exploration.

- Kind: python
- Classes: ScenarioFactory, BodyDiscoveryBaselineConfig, ActionSampleCount, BodyDiscoveryStrategyMetrics, BodyDiscoveryComparisonResult, BodyDiscoveryBaselineExperiment
- Functions/symbols: export_body_discovery_baseline_json, export_body_discovery_baseline_csv, _strategy_payload, _set_metrics

## `src/seedmind/training/__init__.py`

Experience collection and predictive training for SeedMind.

- Kind: python

## `src/seedmind/training/experience.py`

Sequential experience records collected from SeedMind Nursery v0.

- Kind: python
- Classes: ExperienceTransition
- Functions/symbols: collect_experience, _sensor_difference

## `src/seedmind/training/online_trainer.py`

One-step online predictive training for SeedMind.

- Kind: python
- Classes: OnlineTrainerConfig, OnlineTrainingMetrics, OnlinePredictiveTrainer

## `src/seedmind/training/session.py`

Reproducible familiar-sequence training sessions for SeedMind.

- Kind: python
- Classes: ScenarioFactory, FamiliarSequenceConfig, TrainingStepRecord, TrainingSessionResult, FamiliarSequenceTrainingSession
- Functions/symbols: save_training_checkpoint, load_training_checkpoint, export_training_history_csv, export_prediction_error_svg, _scenario_identity, _session_identity, _record_to_payload, _record_from_payload, _validate_checkpoint_progress, _required_int, _required_sequence, _required_mapping, _mapping_int, _mapping_float, _mapping_str, _mapping_bool

## `tests/unit/ndnra_controlled_replay_test_support.py`

Shared deterministic fixtures for durable controlled replay tests.

- Kind: python
- Classes: ReplayScenario
- Functions/symbols: build_replay_scenario, raise_at

## `tests/unit/ndnra_execution_test_support.py`

Shared deterministic fixtures for NDNRA execution persistence tests.

- Kind: python
- Classes: ExecutionSetup
- Functions/symbols: record_trace, build_proposal, build_setup, commit_request, save_initial, execute_loaded, raise_at, read_object, object_value, list_value, rewrite_checksum

## `tests/unit/test_action_contract.py`

Tests for primitive body actions.

- Kind: python
- Functions/symbols: test_primitive_action_values_are_stable, test_primitive_action_can_be_created_from_wire_value

## `tests/unit/test_ambition_engine.py`

Tests for demonstration-derived persistent ambitions.

- Kind: python
- Functions/symbols: observed_demo, adopted_manager, test_detector_requires_three_confirmed_repetitions, test_unconfirmed_repetition_does_not_form_candidate, test_ambition_persists_across_episodes, test_budget_and_milestone_progression, test_state_round_trip_and_dashboard, test_final_milestone_completes_ambition

## `tests/unit/test_apprenticeship.py`

Tests for calibrated help seeking and caregiver apprenticeship memory.

- Kind: python
- Functions/symbols: make_request, make_context, blocked_context, familiar_context, test_blocked_high_uncertainty_requests_help, test_familiar_low_risk_avoids_unnecessary_help, test_safe_low_cost_experiment_is_preferred_over_help, test_guided_learner_requires_more_uncertainty_than_dependent_level, test_teacher_demonstrates_blockage_and_clarifies_ambiguity, test_verified_familiar_approvals_promote_support_level, test_metrics_and_timeline_exports_pass_gate

## `tests/unit/test_belief_registry.py`

Tests for evidence-linked beliefs, contradictions, and inspection.

- Kind: python
- Functions/symbols: memory_event, proposition, test_supporting_evidence_raises_belief_confidence, test_counterexample_lowers_confidence_and_creates_contradiction, test_belief_and_evidence_persist_across_database_reopen, test_belief_rejects_missing_or_duplicate_evidence, test_memory_inspector_and_evidence_viewer_are_ascii

## `tests/unit/test_body_discovery_baseline.py`

Tests for matched-budget body discovery against random exploration.

- Kind: python
- Functions/symbols: create_config, test_targeted_body_probes_beat_random_exploration, test_comparison_is_reproducible, test_all_strategies_use_the_same_transition_budget, test_targeted_schedule_allocates_equal_probe_evidence, test_oracle_channels_are_derived_from_active_held_out_effects, test_baseline_reports_are_ascii_and_inspectable, test_baseline_config_rejects_invalid_values

## `tests/unit/test_curiosity_comparison.py`

Tests for curiosity versus random causal-discovery comparison.

- Kind: python
- Classes: TinyComparisonScenarioFactory, ControlledPredictiveTrainer
- Functions/symbols: create_trainer, create_config, test_curiosity_discovers_controllable_effects_faster_than_random, test_curiosity_avoids_persistent_wait_loop, test_comparison_uses_paired_models_and_matched_budgets, test_comparison_is_reproducible, test_comparison_exports_are_ascii_and_inspectable, test_comparison_rejects_budget_above_scenario_limit, test_comparison_rejects_noise_action_with_direct_effect, test_comparison_config_rejects_invalid_values

## `tests/unit/test_curiosity_policy.py`

Tests for learning-progress curiosity and bounded experiment selection.

- Kind: python
- Functions/symbols: create_config, candidate_for, test_learning_progress_is_positive_only_when_recent_error_improves, test_novelty_decays_with_repeated_observations, test_repetition_penalty_rotates_equal_unseen_candidates, test_stagnation_penalty_discounts_persistent_unlearnable_error, test_recent_prediction_error_is_normalized_as_uncertainty, test_selection_consumes_bounded_play_budget, test_unavailable_or_unconfigured_actions_are_not_candidates, test_curiosity_timeline_exports_are_ascii_and_inspectable, test_curiosity_config_rejects_invalid_values, test_observe_rejects_invalid_prediction_error

## `tests/unit/test_curiosity_session.py`

Tests for live curiosity-guided predictive training sessions.

- Kind: python
- Classes: TinyCuriosityScenarioFactory
- Functions/symbols: create_config, create_trainer, test_live_session_consumes_budget_and_trains_predictive_core, test_live_session_is_reproducible_for_identical_seeds, test_live_timeline_retains_pre_action_candidates_and_post_action_error, test_live_training_exports_are_ascii_and_inspectable, test_live_session_rejects_budget_above_scenario_limit, test_live_training_config_rejects_negative_seed

## `tests/unit/test_dynamic_scenario.py`

Tests for the reproducible dynamic nursery scenario.

- Kind: python
- Functions/symbols: entity_position, entity_blocks, test_same_seed_produces_identical_dynamic_scenario, test_dynamic_scenario_changes_during_wait, test_periodic_door_changes_on_second_tick, test_reset_restores_dynamic_world_and_process_phase, test_gymnasium_environment_carries_scenario_processes, test_dynamic_factory_rejects_invalid_configuration, test_dynamic_factory_rejects_negative_seed

## `tests/unit/test_entities.py`

Tests for nursery entities and agent body state.

- Kind: python
- Functions/symbols: test_agent_turns_without_changing_position, test_agent_moves_in_current_orientation, test_movable_entity_returns_updated_copy, test_non_movable_entity_rejects_movement, test_entity_requires_identifier

## `tests/unit/test_episodic_memory.py`

Tests for SQLite episodic storage, significance, and retrieval.

- Kind: python
- Functions/symbols: features, event_draft, test_significance_prioritizes_developmentally_relevant_event, test_store_persists_and_retrieves_by_ambition_and_context, test_retrieval_orders_significance_before_recency, test_duplicate_event_id_is_rejected, test_memory_query_can_filter_event_type, test_significance_config_rejects_invalid_weights

## `tests/unit/test_experience.py`

Tests for sequential SeedMind experience records.

- Kind: python
- Functions/symbols: create_runtime, create_dynamic_runtime, create_packet, test_collect_experience_connects_two_observations_with_one_action, test_collect_stop_records_episode_termination, test_sensor_change_is_next_minus_current, test_wait_separates_external_motion_from_controllable_change, test_move_separates_agent_and_external_changes, test_experience_rejects_invalid_transition_contract, test_experience_rejects_invalid_agent_snapshot, test_experience_rejects_action_unavailable_at_source

## `tests/unit/test_gymnasium_adapter.py`

Tests for the Gymnasium-compatible SeedMind Nursery adapter.

- Kind: python
- Functions/symbols: create_initial_state, create_env, test_reset_returns_float32_observation_inside_declared_space, test_step_maps_action_index_to_primitive_transition, test_stop_terminates_without_external_reward, test_deterministic_step_limit_truncates_episode, test_reset_clears_completion_and_can_change_episode_identifier, test_invalid_action_index_is_rejected, test_invalid_reset_episode_identifier_type_is_rejected, test_max_episode_steps_must_be_positive, test_adapter_passes_gymnasium_environment_checks, test_environment_can_be_created_from_reproducible_scenario

## `tests/unit/test_human_contracts.py`

Tests for symbolic human request and signal contracts.

- Kind: python
- Functions/symbols: make_request, test_request_signal_has_fixed_width_and_one_hot_code, test_caregiver_frame_encodes_demonstration, test_caregiver_frame_rejects_request_code, test_request_rejects_invalid_metadata

## `tests/unit/test_ndnra_activity_maintenance.py`

Tests for source-separated activity and bounded dormancy maintenance.

- Kind: python
- Functions/symbols: _graph, _runtime, _request, _ledger_with_real_support, test_real_replay_and_imagined_activity_have_ordered_strengths, test_replay_and_imagination_require_real_support, test_real_activity_requires_real_evidence_and_cannot_cite_other_events, test_harmful_redundant_and_irrelevant_pathways_remain_dormant, test_safety_critical_and_rare_use_memory_receive_bounded_floors, test_cycle_budget_limits_total_reactivation, test_event_budget_and_structure_budget_are_enforced, test_duplicate_activity_cannot_reduce_dormancy_twice, test_source_counters_remain_separate_and_inspectable, test_runtime_maintenance_only_reduces_dormancy, test_runtime_applies_real_more_than_replay_more_than_imagination, test_denied_or_duplicate_decision_does_not_change_runtime, test_unknown_structure_is_rejected_before_any_dormancy_change, test_activity_contract_rejects_confidence_mastery_and_authority_changes, test_activity_maintenance_has_no_execution_persistence_timer_or_sql_dependency

## `tests/unit/test_ndnra_consolidation.py`

Tests for pure retention-gated NDNRA consolidation eligibility.

- Kind: python
- Functions/symbols: _trace, _ledger, _valid_ledger, _evaluate, test_broad_mastery_is_eligible_deterministic_and_pure, test_copied_replay_volume_does_not_qualify_as_independent_support, test_one_shot_protection_is_not_broad_consolidation_mastery, test_single_context_repetition_is_rejected, test_single_route_learning_is_rejected, test_low_causal_consistency_and_contradictions_are_rejected, test_failed_transfer_is_rejected, test_supplied_mastery_fields_are_revalidated, test_missing_and_duplicate_source_events_are_rejected, test_unknown_or_unrelated_source_event_is_rejected, test_missing_assembly_and_route_registrations_are_rejected, test_invalid_stability_requests_are_rejected, test_invalid_plasticity_requests_are_rejected, test_non_finite_mastery_fields_cannot_bypass_the_gate, test_consolidation_eligibility_has_no_sqlite_cognitive_dependency

## `tests/unit/test_ndnra_consolidation_acceptance.py`

Tests for live-shadow acceptance of reversible consolidation checkpoints.

- Kind: python
- Functions/symbols: test_consolidation_acceptance_preserves_production_behavior, test_consolidation_acceptance_round_trips_live_checkpoint, test_loaded_checkpoint_reopens_and_restores_after_new_contradiction, test_consolidation_acceptance_exports_are_ascii_and_inspectable, test_consolidation_acceptance_has_no_sqlite_or_action_authority_dependency

## `tests/unit/test_ndnra_consolidation_application.py`

Tests for bounded atomic NDNRA consolidation proposal application.

- Kind: python
- Functions/symbols: _trace, _ledger, _eligibility, _state, test_eligible_candidate_applies_bounded_changes_and_preserves_evidence, test_non_target_structures_remain_unchanged, test_application_clamps_stability_and_plasticity_to_unit_bounds, test_missing_structure_fails_before_any_mutation, test_ineligible_result_fails_before_any_mutation, test_duplicate_candidate_application_is_blocked_atomically, test_tampered_request_above_policy_cap_is_rejected_atomically, test_tampered_lesson_or_mastery_snapshot_is_rejected, test_registration_rejects_duplicate_or_overlapping_identities, test_snapshot_is_immutable_and_deterministically_ordered, test_consolidation_application_has_no_sqlite_or_replay_dependency

## `tests/unit/test_ndnra_consolidation_execution_approval.py`

Tests for explicit human-approved NDNRA consolidation execution permits.

- Kind: python
- Functions/symbols: _trace, _ledger, _proposal, _accepted_registry, _request, _permit, test_current_accepted_proposal_receives_deterministic_human_permit, test_permit_validity_window_is_bounded_and_inspectable, test_approval_requires_explicit_human_identity, test_pending_deferred_and_rejected_records_cannot_receive_permits, test_stale_proposal_fails_immediate_revalidation, test_invalid_structure_or_contradiction_blocks_approval, test_mismatched_proposal_candidate_or_review_identity_is_rejected, test_approval_must_follow_review_and_use_short_validity, test_distinct_human_reason_produces_distinct_permit_identity, test_new_permit_rejects_preconsumed_or_direct_execution_state, test_approval_module_has_no_application_persistence_timer_or_sql_dependency

## `tests/unit/test_ndnra_consolidation_execution_commit.py`

Tests for atomic human-approved NDNRA consolidation execution.

- Kind: python
- Classes: _PostApplyFailureTarget
- Functions/symbols: _trace, _ledger, _proposal, _proposal_registry, _permit, _state, _setup, _request, _execute, test_successful_commit_applies_once_and_consumes_permit_atomically, test_commit_changes_only_candidate_structures_within_bounds, test_identical_fresh_commits_have_deterministic_execution_identity, test_cancelled_permit_blocks_commit_before_state_mutation, test_expired_or_out_of_window_permit_blocks_commit, test_consumed_permit_cannot_apply_twice, test_new_evidence_between_approval_and_commit_blocks_stale_permit, test_missing_application_structure_fails_without_consumption_or_mutation, test_mismatched_commit_identities_fail_before_application, test_commit_requires_bounded_execution_gate_identity, test_post_apply_failure_restores_exact_state_and_leaves_permit_issued, test_receipt_rejects_tampered_execution_or_transition_identity, test_execution_commit_has_no_replay_growth_advice_sql_or_action_path

## `tests/unit/test_ndnra_consolidation_execution_durable_commit.py`

Tests for durable single-use NDNRA consolidation execution.

- Kind: python
- Functions/symbols: test_successful_restart_blocks_replay_and_duplicate_reissued_permit, test_commit_interruption_restores_exact_old_state, test_after_application_before_save_restores_old_state, test_pre_replace_persistence_interruption_resolves_to_complete_old_state, test_after_replace_interruption_recovers_complete_new_state, test_new_evidence_after_restart_blocks_stale_permit_without_mutation, test_terminal_permit_status_blocks_execution_after_restart

## `tests/unit/test_ndnra_consolidation_execution_permit_lifecycle.py`

Tests for immutable NDNRA execution-permit lifecycle state.

- Kind: python
- Functions/symbols: _trace, _ledger, _proposal, _accepted_registry, _permit, _request, test_issued_record_is_immutable_and_non_authoritative, test_cancel_transition_is_terminal_and_preserves_issued_record, test_consume_transition_is_single_use_and_requires_reference, test_expiry_requires_episode_after_validity_window, test_cancel_or_consume_after_expiry_window_is_rejected, test_transition_must_follow_permit_issuance, test_nonconsume_transitions_reject_consumption_reference, test_mismatched_permit_proposal_or_candidate_is_rejected, test_terminal_records_reject_every_conflicting_transition, test_transition_identity_is_deterministic_and_tampering_is_rejected, test_reconstructed_record_rejects_mismatched_status_or_permit, test_registry_enforces_unique_permit_identity_and_preserves_other_records, test_permit_lifecycle_is_separate_from_proposal_lifecycle, test_permit_lifecycle_has_no_application_persistence_timer_or_sql_dependency

## `tests/unit/test_ndnra_consolidation_execution_persistence.py`

Tests for exact restart-safe NDNRA execution checkpoint persistence.

- Kind: python
- Functions/symbols: test_issued_checkpoint_round_trips_exactly_and_has_no_authority, test_schema_v5_round_trips_consumed_permit_receipt_and_application, test_schema_v4_migrates_to_empty_execution_without_inference, _corrupt_transition_identity, _corrupt_receipt_identity, _corrupt_consumption_reference, _remove_receipt, _make_receipt_without_consumed_permit, _duplicate_permit, _duplicate_receipt, _remove_applied_candidate, _execution, test_relational_corruption_causes_complete_fallback, test_outer_checksum_corruption_causes_complete_fallback, test_execution_checkpoint_rejects_authority_and_automatic_execution, test_execution_persistence_has_no_sqlite_replay_or_action_authority_path

## `tests/unit/test_ndnra_consolidation_interference.py`

Tests for bounded consolidation interference and source-gated replay.

- Kind: python
- Functions/symbols: test_old_lesson_is_mastered_and_eligible_before_interference, test_no_consolidation_learns_new_lesson_but_forgets_old_lesson, test_naive_consolidation_trades_new_learning_for_better_retention, test_retention_gated_replay_uses_only_candidate_sources_when_needed, test_replay_preserves_sources_without_inflating_mastery, test_retention_gated_replay_balances_retention_and_new_learning, test_experiment_is_exactly_deterministic, test_experiment_remains_non_authoritative_and_non_sql

## `tests/unit/test_ndnra_consolidation_persistence.py`

Tests for schema-v3 NDNRA consolidation checkpoint persistence.

- Kind: python
- Functions/symbols: _trace, _ledger, _application, _active_checkpoint, _rewrite_version, _rewrite_checksum, test_schema_v4_round_trips_active_consolidation_checkpoint, test_loaded_active_application_can_be_reopened_and_rolled_back, test_schema_v3_round_trips_compact_rollback_audit, test_schema_v2_migrates_to_explicit_empty_consolidation_checkpoint, test_default_schema_v3_save_uses_empty_checkpoint, test_inconsistent_checkpoint_falls_back_without_partial_state, test_schema_v3_checkpoint_encoding_is_deterministic, test_consolidation_persistence_has_no_sqlite_cognitive_dependency

## `tests/unit/test_ndnra_consolidation_portfolio.py`

Tests for pure multi-lesson consolidation proposal prioritisation.

- Kind: python
- Functions/symbols: _record_mastery, _request, _portfolio_fixture, test_portfolio_selects_most_overdue_ready_lesson, test_portfolio_preserves_ineligible_lesson_decision, test_equivalent_input_order_produces_identical_portfolio, test_proposal_limit_keeps_unselected_candidates_visible, test_remaining_active_capacity_bounds_portfolio_selection, test_portfolio_does_not_mutate_contextual_evidence, test_duplicate_lesson_requests_are_rejected, test_portfolio_requires_shared_evaluation_episode_and_active_candidates, test_portfolio_module_has_no_execution_or_integration_dependency

## `tests/unit/test_ndnra_consolidation_proposal_history.py`

Tests for immutable NDNRA consolidation proposal lifecycle history.

- Kind: python
- Functions/symbols: _proposal, _request, test_pending_record_preserves_original_proposal_without_authority, test_accept_returns_new_record_and_preserves_pending_record, test_rejected_and_accepted_records_are_terminal, test_deferred_record_can_be_reviewed_at_due_episode, test_deferred_record_rejects_early_or_non_increasing_review, test_record_rejects_review_for_different_proposal, test_constructor_rejects_duplicate_or_terminal_successor_history, test_constructor_rejects_status_mismatch_and_early_reconstruction, test_lifecycle_snapshot_preserves_complete_ascii_history, test_history_module_has_no_execution_persistence_timer_or_sql_dependency

## `tests/unit/test_ndnra_consolidation_proposal_lifecycle.py`

Tests for pure review-only consolidation proposal lifecycle decisions.

- Kind: python
- Functions/symbols: _proposal, test_accept_is_deterministic_and_non_authoritative, test_reject_preserves_proposal_and_reason, test_defer_requires_future_review_episode, test_non_deferred_review_rejects_defer_episode, test_review_cannot_precede_proposal, test_review_decision_rejects_execution_authority_and_status_mismatch, test_review_snapshot_is_ascii_inspectable, test_review_module_has_no_execution_timer_persistence_or_sql_dependency

## `tests/unit/test_ndnra_consolidation_proposal_lifecycle_acceptance.py`

Tests for live-shadow consolidation proposal lifecycle acceptance.

- Kind: python
- Functions/symbols: test_live_lifecycle_does_not_change_seedmind_behavior, test_live_lifecycle_defers_then_accepts_one_proposal, test_live_lifecycle_retains_history_without_execution, test_lifecycle_acceptance_exports_are_ascii_and_inspectable, test_lifecycle_acceptance_has_no_application_or_sqlite_path

## `tests/unit/test_ndnra_consolidation_proposal_lifecycle_experiment.py`

Tests for the NDNRA consolidation proposal lifecycle experiment.

- Kind: python
- Functions/symbols: _by_strategy, test_automatic_acceptance_keeps_a_stale_candidate, test_permanent_deferral_avoids_acceptance_but_delays_current_review, test_evidence_aware_strategy_replaces_then_accepts_current_proposal, test_experiment_is_exactly_deterministic, test_experiment_preserves_history_without_execution_or_sqlite, test_lifecycle_experiment_export_is_ascii_and_inspectable, test_lifecycle_experiment_has_no_application_persistence_or_integration_dependency

## `tests/unit/test_ndnra_consolidation_proposal_management.py`

Tests for bounded NDNRA consolidation proposal lifecycle management.

- Kind: python
- Functions/symbols: _proposal, _review_request, _management_request, test_registry_adds_pending_record_with_bounded_capacity, test_rejection_releases_capacity_but_preserves_record, test_accepted_record_continues_to_consume_capacity, test_deferred_record_can_be_reviewed_when_due_through_registry, test_expiry_is_deterministic_preserves_history_and_releases_capacity, test_replacement_preserves_old_and_new_proposals_with_one_active_record, test_replacement_rejects_wrong_lesson_old_or_future_proposal, test_registry_rejects_stale_target_and_candidate_mismatch, test_registry_rejects_management_of_closed_record, test_management_must_follow_latest_review_episode, test_registry_rejects_duplicate_proposal_and_active_lesson, test_management_request_and_decision_validate_replacement_contract, test_registry_snapshot_is_ascii_and_preserves_archived_records, test_managed_record_rejects_execution_authority, test_management_module_has_no_execution_persistence_timer_or_sql_dependency

## `tests/unit/test_ndnra_consolidation_proposal_persistence.py`

Tests for restart-safe NDNRA proposal lifecycle checkpoint encoding.

- Kind: python
- Functions/symbols: _proposal, _review, _managed_registry, _json_snapshot, test_empty_checkpoint_round_trips_exactly, test_complete_registry_round_trips_exactly, test_round_trip_preserves_all_review_and_management_identities, test_checkpoint_encoding_is_deterministic_and_ascii, test_checkpoint_rejects_incompatible_schema_or_version, test_checkpoint_rejects_tampered_review_identity_or_reason, test_checkpoint_rejects_tampered_management_identity, test_checkpoint_rejects_missing_replacement_record, test_checkpoint_rejects_derived_count_and_authority_tampering, test_checkpoint_constructor_rejects_unretained_replacement, test_checkpoint_codec_has_no_file_sql_execution_or_integration_dependency

## `tests/unit/test_ndnra_consolidation_proposal_revalidation.py`

Tests for pure restart-time proposal lifecycle revalidation.

- Kind: python
- Functions/symbols: _trace, _ledger, _proposal, _accepted_registry, _evaluate, test_unchanged_restored_proposal_is_current, test_additional_valid_evidence_marks_old_candidate_stale, test_matching_newer_same_lesson_proposal_marks_old_one_superseded, test_contradiction_makes_restored_proposal_invalid_for_review, test_missing_original_source_event_makes_proposal_invalid, test_missing_required_structure_makes_proposal_invalid, test_wrong_lesson_or_non_newer_superseding_input_is_rejected, test_closed_records_cannot_be_revalidated, test_registry_report_evaluates_only_active_records_and_preserves_archive, _graph_with_mastery, test_persisted_accepted_proposal_revalidates_current_after_restart, test_revalidation_is_deterministic_and_has_no_execution_or_sqlite_path

## `tests/unit/test_ndnra_consolidation_reopening.py`

Tests for contradiction-driven reopening and atomic consolidation rollback.

- Kind: python
- Functions/symbols: _trace, _mastered_ledger, _eligibility, _application, _add_contradiction, test_new_independent_contradiction_reopens_without_mutation, test_positive_new_evidence_does_not_reopen, test_small_contradiction_is_visible_but_below_reopening_threshold, test_correlated_contradiction_copies_do_not_inflate_independent_count, test_reopening_requires_original_candidate_sources_to_remain_resolvable, test_rollback_restores_candidate_state_and_preserves_unrelated_state, test_rollback_is_deterministic_for_identical_evidence, test_rollback_is_blocked_when_reopening_gate_does_not_pass, test_duplicate_rollback_is_blocked_without_further_mutation, test_stale_target_state_blocks_rollback_atomically, test_mismatched_decision_and_application_are_rejected, test_reopening_and_rollback_have_no_sql_or_integration_dependency

## `tests/unit/test_ndnra_consolidation_scheduling.py`

Tests for pure proposal-only NDNRA consolidation scheduling.

- Kind: python
- Functions/symbols: _trace, _mastered_ledger, _request, test_due_mastery_produces_deterministic_non_authoritative_proposal, test_before_first_window_exposes_eligibility_without_proposing, test_completed_episode_enforces_explicit_cooldown, test_due_but_unmastered_lesson_returns_eligibility_reasons, test_active_candidate_is_not_proposed_twice, test_active_capacity_blocks_unrelated_candidate_without_mutation, test_context_rejects_future_completion_episode, test_schedule_proposal_rejects_execution_authority, test_scheduling_module_has_no_timer_executor_sql_or_integration_dependency

## `tests/unit/test_ndnra_consolidation_scheduling_acceptance.py`

Tests for live-shadow consolidation scheduling acceptance.

- Kind: python
- Functions/symbols: test_live_scheduler_does_not_change_seedmind_behavior, test_live_scheduler_proposes_once_without_repetition, test_live_scheduler_remains_read_only_and_non_authoritative, test_scheduling_acceptance_exports_are_ascii_and_inspectable, test_scheduling_acceptance_has_no_application_or_sqlite_path

## `tests/unit/test_ndnra_consolidation_scheduling_experiment.py`

Tests for the proposal-only consolidation scheduling experiment.

- Kind: python
- Functions/symbols: _by_strategy, test_fixed_interval_creates_false_and_late_proposals, test_eligibility_only_is_precise_but_highly_repetitive, test_evidence_aware_scheduling_is_precise_bounded_and_non_redundant, test_controlled_evidence_arrival_has_two_mastered_lessons, test_experiment_is_exactly_deterministic, test_experiment_never_applies_or_authorizes_consolidation, test_experiment_export_is_ascii_and_inspectable, test_experiment_config_rejects_invalid_values, test_experiment_module_has_no_application_persistence_or_integration_dependency

## `tests/unit/test_ndnra_contextual_consequence.py`

Tests for real consequences and context-specific action competence.

- Kind: python
- Functions/symbols: _cooling_need, _context, _assessment, test_opening_window_into_hotter_air_is_a_real_worsened_consequence, test_wrong_action_creates_a_low_local_competence_record, test_same_action_remains_separate_across_different_contexts, test_later_failure_reduces_helpfulness_after_successes, test_prediction_accuracy_does_not_make_a_harmful_action_helpful, test_replay_and_imagination_cannot_become_new_competence_evidence, test_exact_duplicate_is_ignored_but_identity_conflict_is_rejected, test_missing_prediction_is_unknown_not_false_accuracy, test_effect_order_and_authority_contracts_are_enforced, test_snapshots_are_deterministic_ascii_and_non_executing, test_consequence_module_has_no_action_execution_persistence_or_timer_dependency

## `tests/unit/test_ndnra_contextual_consequence_transfer.py`

Tests for bounded contextual transfer over exact consequence records.

- Kind: python
- Functions/symbols: _context, _request, _observe, test_exact_context_evidence_always_wins_over_transfer, test_similar_context_produces_explicit_attenuated_transfer, test_exact_partial_record_is_not_silently_filled_from_transfer, test_need_action_and_shape_mismatches_remain_unknown, test_different_action_never_borrows_source_evidence, test_one_source_cannot_create_broad_certainty, test_consistent_sources_raise_support_but_respect_transfer_cap, test_opposing_sources_surface_contradiction_and_remove_confidence, test_missing_source_effect_dimension_remains_unknown, test_zero_confidence_source_cannot_support_transfer, test_transfer_prediction_is_pure_and_does_not_mutate_exact_model, test_candidate_and_source_limits_are_enforced_deterministically, test_transfer_snapshots_are_ascii_deterministic_and_inspectable, test_transfer_configuration_and_authority_contracts_are_enforced, test_transfer_module_has_no_execution_persistence_or_background_dependency

## `tests/unit/test_ndnra_contextual_mastery.py`

Tests for contextual NDNRA redundancy and bounded mastery evidence.

- Kind: python
- Functions/symbols: test_contextual_mastery_experiment_distinguishes_replay_from_breadth, test_one_shot_protection_and_varied_mastery_remain_distinct, test_contradiction_reduces_mastery_without_erasing_sources, test_event_identity_key_is_collision_safe, test_contradictory_effect_does_not_create_protective_strength, test_contextual_recording_is_atomic_when_identity_validation_fails, test_contextual_mastery_gate_preserves_shadow_and_persistence, test_contextual_mastery_has_no_sqlite_cognitive_dependency

## `tests/unit/test_ndnra_controlled_checkpoint_restoration.py`

Tests for exact restart-safe complete checkpoint restoration.

- Kind: python
- Classes: _Scenario
- Functions/symbols: _graph, _activity, _growth, _scenario, _raise_at, _restore, test_restoration_replaces_complete_active_brain_and_preserves_audit, test_restoration_audit_survives_restart_and_blocks_permit_reuse, test_interruption_before_save_preserves_exact_current_envelope, test_interruption_after_replace_recovers_complete_restored_envelope, test_restoration_rejects_same_path_or_corrupt_source_without_mutation, test_restoration_replaces_every_persisted_active_component, test_restoration_rejects_migrated_source_without_mutation, test_restoration_rejects_fresh_evidence_drift_and_expired_permit, test_restoration_rejects_source_audit_not_contained_by_current, _rewrite_as_schema_5

## `tests/unit/test_ndnra_controlled_replay_persistence.py`

Tests for schema-6 durable controlled replay persistence.

- Kind: python
- Functions/symbols: _canonical_checksum, test_schema_6_round_trips_issued_permit_and_activity_history, test_audit_only_permit_save_does_not_change_active_state_checksum, test_activity_ledger_and_replay_checkpoint_reconstruct_exactly, test_active_state_checksum_detects_tampering_even_with_valid_outer_checksum, test_schema_5_migrates_to_empty_replay_checkpoint

## `tests/unit/test_ndnra_controlled_replay_restoration_acceptance.py`

Tests for live controlled replay and restoration stage acceptance.

- Kind: python
- Functions/symbols: evidence, test_acceptance_consumes_exactly_one_replay_and_restoration_permit, test_replay_changes_only_bounded_non_authoritative_accessibility, test_restoration_reproduces_source_state_and_live_behaviour, test_acceptance_exercises_all_failure_and_restart_paths, test_acceptance_exports_ascii_inspectable_evidence, test_acceptance_has_no_autonomous_or_sqlite_operation_path

## `tests/unit/test_ndnra_controlled_replay_restoration_approval.py`

Tests for human-approved controlled replay and restoration permits.

- Kind: python
- Functions/symbols: _evidence, _replay_target, _restoration_target, _request, _permit, test_replay_permit_is_deterministic_bounded_and_non_executable, test_restoration_permit_binds_exact_complete_checkpoint_envelope, test_permit_validity_window_is_short_and_inspectable, test_approval_requires_immediate_current_evidence, test_approval_window_cannot_exceed_policy_limit, test_approval_requires_explicit_human_identity, test_unverified_or_fallback_checkpoint_evidence_is_rejected, test_target_requires_exact_current_and_source_checkpoint_identities, test_target_requires_all_exact_source_evidence, test_operation_specific_target_bounds_are_enforced, test_target_and_permit_reject_all_authority_bearing_state, test_distinct_human_reason_produces_distinct_permit_identity, test_approval_module_has_no_execution_persistence_timer_or_sql_dependency

## `tests/unit/test_ndnra_controlled_replay_restoration_permit_lifecycle.py`

Tests for immutable controlled replay/restoration permit lifecycles.

- Kind: python
- Functions/symbols: _evidence, _target, _permit, _request, test_issued_record_is_immutable_and_non_authoritative, test_cancel_transition_is_terminal_and_preserves_issued_record, test_consume_transition_requires_operation_actor_and_receipt_reference, test_expiry_requires_episode_after_validity_window, test_cancel_or_consume_after_expiry_window_is_rejected, test_transition_must_follow_permit_issuance, test_nonconsume_transitions_reject_consumption_reference, test_transition_requires_every_exact_authority_identity, test_terminal_records_reject_all_conflicting_transitions, test_transition_identity_is_deterministic_and_tampering_is_rejected, test_registry_enforces_unique_permits_and_tracks_operation_counts, test_reconstructed_record_rejects_mismatched_status_or_permit, test_lifecycle_objects_reject_all_authority_bearing_state, test_lifecycle_has_no_operation_persistence_timer_or_sql_dependency

## `tests/unit/test_ndnra_controlled_retention_replay.py`

Tests for single-use bounded replay of exact real activity.

- Kind: python
- Functions/symbols: _graph, _activity_ledger, _runtime, _evidence, _target, _permit, _registry, _items, _request, _execute, test_success_replays_exact_real_activity_and_consumes_one_permit, test_success_is_deterministic_from_identical_inputs, test_restoration_permit_cannot_execute_retention_replay, test_replay_requires_fresh_same_episode_verified_nonfallback_evidence, test_checkpoint_and_source_evidence_drift_are_rejected, test_request_must_match_every_permit_and_fresh_evidence_identity, test_cancelled_consumed_and_expired_permits_cannot_run, test_work_items_are_explicit_unique_sorted_and_bounded, test_work_items_must_use_approved_exact_real_activity, test_midoperation_failure_preserves_exact_original_state, test_denied_replay_preserves_exact_original_state, test_receipt_identity_and_authority_contracts_are_enforced, test_replay_module_has_no_persistence_timer_sql_integration_or_action_execution

## `tests/unit/test_ndnra_controlled_retention_replay_durable.py`

Tests for restart-safe durable controlled retention replay.

- Kind: python
- Functions/symbols: _execute, test_durable_replay_round_trips_consumed_permit_receipt_and_activity, test_restart_retains_single_use_and_blocks_replay_again, test_interruption_before_save_preserves_exact_old_envelope, test_interruption_after_atomic_replace_recovers_complete_new_envelope, test_durable_replay_rejects_state_or_caller_boundary_drift

## `tests/unit/test_ndnra_human_approved_consolidation_execution_acceptance.py`

Tests for live acceptance of restart-safe human-approved execution.

- Kind: python
- Functions/symbols: test_one_human_approval_produces_one_durable_application, test_approved_execution_preserves_live_seedmind_cognition, test_live_acceptance_receipt_and_persisted_state_are_exact, test_live_acceptance_exports_ascii_inspectable_evidence, test_live_acceptance_has_no_autonomous_or_sqlite_execution_path

## `tests/unit/test_ndnra_learned_consequence_model.py`

Tests for the bounded exact-context learned consequence model.

- Kind: python
- Functions/symbols: _context, _observation, _request, test_unknown_context_action_reports_complete_uncertainty, test_one_real_transition_creates_a_single_step_prediction, test_consistent_real_outcomes_increase_support_and_correct_underconfidence, test_contradiction_reduces_confidence_and_marks_prior_overconfidence, test_most_frequent_exact_next_context_is_predicted_deterministically, test_contexts_and_actions_never_share_model_evidence, test_missing_requested_dimension_stays_unknown_and_limits_coverage, test_zero_confidence_effect_does_not_increase_effect_support, test_unobserved_outcome_dimension_remains_unknown_during_evaluation, test_prediction_request_respects_effect_dimension_bound, test_prediction_evaluation_is_pure_and_requires_exact_real_transition, test_replay_and_imagination_cannot_update_the_model, test_exact_duplicate_is_ignored_and_identity_conflict_is_rejected, test_record_and_observation_bounds_fail_before_model_insertion, test_effect_dimension_and_next_context_bounds_are_atomic, test_stable_ordering_and_authority_contracts_are_enforced, test_snapshots_are_deterministic_ascii_and_non_authoritative, test_model_has_no_execution_persistence_timer_or_imagination_dependency

## `tests/unit/test_ndnra_local_learning.py`

Tests for local eligibility traces and delayed modulatory credit.

- Kind: python
- Functions/symbols: test_delayed_cooling_updates_only_eligible_local_structures, test_earlier_steps_receive_less_credit_from_trace_decay, test_prototype_has_no_torch_or_sqlite_cognitive_dependency

## `tests/unit/test_ndnra_multieffect.py`

Tests for dynamic local dimensions and undemonstrated solution composition.

- Kind: python
- Functions/symbols: test_sparse_effect_memory_gains_dimensions_from_experience, test_shower_memory_keeps_all_observed_effects_on_neuron_and_link, test_shower_learned_for_cleaning_is_recruited_for_cooling, test_separate_window_memories_compose_an_unseen_cooling_solution, test_composition_respects_conditions_and_rejects_hot_shower_for_cooling, test_intended_effect_only_baseline_cannot_reuse_shower_for_cooling, test_complete_multieffect_gate_passes_without_sqlite, test_multieffect_prototype_has_no_sqlite_dependency

## `tests/unit/test_ndnra_persistence.py`

Tests for versioned non-SQL NDNRA brain-state persistence.

- Kind: python
- Functions/symbols: test_brain_store_round_trips_graph_specialist_and_adaptive_state, test_missing_corrupt_and_incompatible_states_fall_back_fresh, test_checksum_tampering_falls_back_without_partial_graph, test_cross_session_shadow_uses_prior_local_memory_at_step_zero, test_persistence_path_has_no_sqlite_cognitive_dependency

## `tests/unit/test_ndnra_proposal_lifecycle_brain_persistence.py`

Tests for schema-v4 proposal lifecycle persistence in the NDNRA brain store.

- Kind: python
- Functions/symbols: _proposal, _consolidation_checkpoint, _lifecycle_checkpoint, _rewrite_as_legacy, _rewrite_checksum_payload, test_schema_v4_round_trips_lifecycle_with_other_brain_state, test_default_schema_v4_save_uses_empty_lifecycle_checkpoint, test_legacy_schemas_migrate_to_empty_lifecycle_checkpoint, test_schema_v4_missing_lifecycle_payload_falls_back_completely, test_schema_v4_inconsistent_lifecycle_falls_back_without_partial_graph, test_schema_v4_outer_checksum_tampering_discards_lifecycle, test_schema_v4_lifecycle_encoding_is_deterministic, test_schema_v4_lifecycle_persistence_has_no_sqlite_or_execution_dependency

## `tests/unit/test_ndnra_recall.py`

Tests for need-driven recruitment, dormancy, and effort-based recall.

- Kind: python
- Functions/symbols: test_untrained_graph_cannot_reconstruct_cooling_chain, test_dormant_memory_requires_deeper_recall_and_resolves_need, test_complete_experiment_passes_local_memory_gate, test_growth_pressure_requires_all_developmental_factors

## `tests/unit/test_ndnra_restart_safe_proposal_memory_acceptance.py`

Tests for restart-safe proposal memory acceptance.

- Kind: python
- Functions/symbols: evidence, test_restart_acceptance_round_trips_exact_state, test_restart_acceptance_migrates_and_falls_back_safely, test_restart_acceptance_detects_stale_accepted_proposal, test_restart_revalidation_does_not_change_live_seedmind, test_restart_acceptance_retains_zero_authority, test_restart_acceptance_exports_are_ascii_and_inspectable, test_restart_acceptance_has_no_execution_replay_or_sqlite_path

## `tests/unit/test_ndnra_shadow_integration.py`

Tests for non-authoritative NDNRA integration with the live nursery loop.

- Kind: python
- Functions/symbols: test_shadow_comparison_preserves_production_actions_and_training, test_shadow_learns_effects_and_emits_only_valid_suggestions, test_shadow_gate_advances_integration_without_action_authority, test_shadow_suggestion_rejects_action_authority, test_shadow_config_rejects_multi_action_control_depth, test_shadow_exports_are_ascii_and_inspectable, test_shadow_integration_has_no_sqlite_decision_dependency

## `tests/unit/test_ndnra_structural_growth.py`

Tests for evidence-driven NDNRA specialist-neuron growth.

- Kind: python
- Functions/symbols: test_interaction_specialist_adds_non_additive_effect_once, test_growth_does_not_trigger_from_one_failure, test_targeted_growth_uses_high_eligibility_members, test_targeted_growth_solves_blockage_and_random_capacity_does_not, test_old_assemblies_are_preserved_without_pruning, test_complete_structural_growth_gate_passes, test_structural_growth_prototype_has_no_sqlite_dependency, test_base_graph_still_fails_without_specialist

## `tests/unit/test_ndnra_unified_signals.py`

Tests for live developmental signals and operational restored NDNRA state.

- Kind: python
- Functions/symbols: _signals, _shadow_graph, test_restored_dormancy_changes_live_action_accessibility_and_score, test_restored_eligibility_and_pressure_continue_instead_of_resetting, test_unified_live_signal_gate_passes_without_changing_production, test_unified_live_signal_exports_are_ascii_and_inspectable, test_complex_goal_retains_pressure_until_second_growth, test_bounded_advice_gate_retains_production, test_unified_integration_has_no_sqlite_cognitive_dependency

## `tests/unit/test_nursery_runtime.py`

Integration tests for the SeedMind Nursery runtime boundary.

- Kind: python
- Functions/symbols: create_initial_state, test_runtime_step_connects_state_transition_and_observation, test_reset_restores_identical_initial_observation, test_reset_can_start_a_new_named_episode, test_runtime_passes_auxiliary_channels_to_new_observation, test_stop_terminates_and_restricts_next_available_action, test_repeated_stop_after_termination_is_stable, test_runtime_rejects_invalid_reset_baseline, test_runtime_rejects_empty_episode_identifier, test_invalid_reset_episode_identifier_does_not_mutate_runtime, test_runtime_derives_resource_state_from_current_world_state

## `tests/unit/test_nursery_state.py`

Tests for deterministic Nursery v0 world state.

- Kind: python
- Functions/symbols: create_state, test_state_finds_entities_in_stable_order, test_state_finds_blocking_entity, test_state_replaces_entity_deterministically, test_state_advances_one_step, test_state_rejects_duplicate_entity_ids, test_state_rejects_out_of_bounds_agent, test_replacement_must_preserve_identity

## `tests/unit/test_observation_adapter.py`

Tests for the deterministic nursery observation adapter.

- Kind: python
- Functions/symbols: create_state, test_adapter_emits_fixed_deterministic_layout, test_adapter_passes_through_raw_auxiliary_channels, test_active_state_exposes_all_primitive_actions_in_enum_order, test_terminated_state_exposes_only_stop, test_adapter_rejects_state_with_different_dimensions, test_sensor_values_do_not_expose_entity_identity_or_role

## `tests/unit/test_observation_contract.py`

Tests for the body-independent observation packet.

- Kind: python
- Functions/symbols: create_packet, test_packet_preserves_raw_channels, test_packet_rejects_invalid_required_values, test_packet_rejects_duplicate_actions, test_packet_rejects_non_finite_channels

## `tests/unit/test_online_trainer.py`

Tests for one-step online predictive training.

- Kind: python
- Functions/symbols: create_runtime, create_trainer, test_train_transition_updates_parameters_and_returns_metrics, test_trainer_reports_external_change_for_dynamic_wait, test_trainer_consumes_scenario_resource_channel, test_trainer_preserves_recurrent_state_across_ordered_experience, test_reset_episode_clears_short_term_state_and_sequence_identity, test_trainer_rejects_temporal_discontinuity, test_trainer_rejects_episode_change_without_reset, test_termination_requires_episode_reset_before_more_training, test_reset_allows_training_a_new_episode, test_trainer_rejects_incompatible_input_specification, test_trainer_rejects_action_count_mismatch, test_trainer_config_rejects_invalid_values

## `tests/unit/test_prediction_error.py`

Tests for prediction error and confidence calibration.

- Kind: python
- Functions/symbols: create_core, test_exact_prediction_has_zero_error_and_full_confidence_target, test_prediction_comparison_reports_per_feature_and_reduced_error, test_prediction_objective_is_differentiable_without_task_reward, test_prediction_objective_rejects_negative_confidence_weight, test_prediction_objective_rejects_negative_change_weight, test_prediction_objective_rejects_current_sensor_shape_mismatch, test_controllable_loss_excludes_external_world_change, test_prediction_objective_requires_both_causal_sensors, test_prediction_comparison_rejects_shape_mismatch

## `tests/unit/test_predictive_state.py`

Tests for the recurrent SeedMind predictive core.

- Kind: python
- Functions/symbols: create_config, test_core_output_shapes_and_ranges, test_core_accepts_single_observation_and_no_action, test_recurrent_state_updates_across_timesteps, test_identical_seed_produces_identical_initial_predictions, test_core_rejects_invalid_action, test_core_rejects_invalid_observation_and_state_shapes, test_core_rejects_invalid_config_dimensions, test_initial_state_matches_model_dtype

## `tests/unit/test_scenario_factory.py`

Tests for deterministic Nursery v0 scenario construction.

- Kind: python
- Functions/symbols: test_same_seed_produces_identical_scenario, test_different_seeds_produce_different_layouts, test_factory_does_not_mutate_global_random_state, test_factory_builds_valid_perimeter_and_distinct_interior_layout, test_scenario_contains_two_raw_shape_objects_and_two_targets, test_resource_state_tracks_normalized_remaining_budget, test_target_occupancy_detects_object_on_target, test_target_occupancy_requires_at_least_one_target_for_completion, test_minimum_supported_factory_dimensions, test_factory_rejects_invalid_configuration, test_factory_rejects_negative_seed, test_scenario_rejects_invalid_metadata, test_scenario_resource_evaluation_is_state_based

## `tests/unit/test_self_model.py`

Tests for online action-effect evidence and body discovery.

- Kind: python
- Functions/symbols: create_packet, create_experience, test_registry_separates_repeatable_body_effect_from_external_change, test_wait_with_external_motion_does_not_create_body_sensor, test_support_prevents_single_effect_from_becoming_body_evidence, test_dynamic_world_body_candidates_remain_in_anonymous_body_channels, test_snapshot_reports_action_coverage, test_registry_rejects_different_sensor_width, test_self_model_exports_are_ascii_and_inspectable, test_self_model_config_rejects_invalid_values

## `tests/unit/test_spatial_contract.py`

Tests for symbolic spatial contracts.

- Kind: python
- Functions/symbols: test_turning_right_cycles_clockwise, test_turning_left_cycles_counterclockwise, test_position_moves_one_cell, test_position_is_immutable

## `tests/unit/test_symbolic_encoder.py`

Tests for raw symbolic observation encoding.

- Kind: python
- Functions/symbols: create_packet, test_input_spec_vectorizes_raw_channels_in_contract_order, test_input_spec_rejects_channel_size_mismatch, test_input_spec_rejects_invalid_dimensions, test_encoder_accepts_single_vector_and_batch, test_encoder_parameters_receive_gradients, test_encoder_rejects_invalid_observation_shape

## `tests/unit/test_teacher_demonstration.py`

Tests for deterministic repeatable teacher demonstrations.

- Kind: python
- Functions/symbols: entity_position, test_teacher_demonstration_moves_object_to_target_in_two_steps, test_teacher_demonstration_is_repeatable_after_reset, test_teacher_process_rejects_misaligned_initial_geometry, test_teacher_process_rejects_empty_identifier, test_teacher_factory_rejects_small_budget

## `tests/unit/test_training_session.py`

Tests for reproducible familiar-sequence training sessions.

- Kind: python
- Classes: TinyScenarioFactory
- Functions/symbols: create_trainer, test_familiar_sequence_prediction_error_decreases, test_checkpoint_resume_matches_uninterrupted_training, test_history_and_prediction_chart_exports, test_resume_rejects_different_action_sequence, test_resume_rejects_changed_scenario, test_familiar_sequence_config_rejects_invalid_values

## `tests/unit/test_transition_engine.py`

Tests for deterministic Nursery v0 primitive-action transitions.

- Kind: python
- Functions/symbols: make_entity, make_state, test_turn_changes_orientation_and_advances_one_step, test_move_forward_changes_position, test_move_is_blocked_by_boundary, test_move_is_blocked_by_entity, test_push_moves_adjacent_movable_entity_without_moving_agent, test_push_can_move_object_onto_non_blocking_target_cell, test_push_failure_outcomes, test_non_physical_actions_advance_without_world_change, test_stop_terminates_episode, test_terminated_state_is_stable, test_same_state_and_action_produce_identical_transition

## `tests/unit/test_world_processes.py`

Tests for deterministic independent world processes.

- Kind: python
- Functions/symbols: make_entity, make_state, test_wait_tick_can_contain_teacher_motion, test_flow_moves_object_without_agent_contact, test_processes_run_in_stable_order, test_world_process_pipeline_does_not_advance_time, test_periodic_mechanism_toggles_only_on_scheduled_ticks, test_same_state_and_processes_produce_identical_result, test_pipeline_rejects_duplicate_process_identifiers
