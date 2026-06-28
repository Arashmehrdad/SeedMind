# seedmind architecture

## Detected entry points

- No conventional entry point was detected.

## Local dependency map

```mermaid
graph LR
    repo[Repository] --> modules[Modules]
```

## Architectural module summary

- `scripts/run_ambition_formation.py` — functions: parse_args, main
- `scripts/run_body_discovery.py` — functions: parse_args, main
- `scripts/run_body_discovery_baseline.py` — functions: parse_args, main
- `scripts/run_curiosity_comparison.py` — functions: parse_args, build_trainer, main
- `scripts/run_curiosity_scoring.py` — functions: parse_args, main, _prediction_error
- `scripts/run_familiar_training.py` — functions: parse_args, build_trainer, main
- `scripts/run_human_apprenticeship.py` — functions: parse_args, main
- `scripts/run_live_curiosity_training.py` — functions: parse_args, build_trainer, main
- `scripts/run_memory_belief_gate.py` — functions: parse_args, main
- `scripts/run_ndnra_advice_gate.py` — functions: parse_args, main
- `scripts/run_ndnra_contextual_mastery_gate.py` — functions: parse_args, main
- `scripts/run_ndnra_heat_fan_gate.py` — functions: parse_args, main
- `scripts/run_ndnra_multieffect_gate.py` — functions: parse_args, main
- `scripts/run_ndnra_persistent_shadow_gate.py` — functions: parse_args, main
- `scripts/run_ndnra_shadow_integration_gate.py` — functions: parse_args, main
- `scripts/run_ndnra_structural_growth_gate.py` — functions: parse_args, main
- `scripts/run_ndnra_unified_signals_gate.py` — functions: parse_args, main
- `src/seedmind/__init__.py` — SeedMind developmental intelligence runtime.
- `src/seedmind/ambition/__init__.py` — Persistent developmental ambitions formed from grounded evidence.
- `src/seedmind/ambition/demonstration.py` — classes: DemonstrationDetectorConfig, ObservedDemonstration, OutcomeSignature, DemonstrationEvidence, _EvidenceAccumulator, GoalDirectedOutcomeDetector; functions: export_demonstration_evidence
- `src/seedmind/ambition/engine.py` — classes: AmbitionOrigin, AmbitionStatus, MilestoneStatus, MilestoneCode, AmbitionMilestone, AmbitionCandidate, AmbitionRecord, AmbitionManagerConfig; functions: save_ambition_manager, load_ambition_manager, export_ambition_dashboard, _config_payload, _record_payload, _record_from_payload, _required_mapping, _required_list, _required_str, _required_int
- `src/seedmind/contracts/__init__.py` — Shared contracts between SeedMind, bodies, and environments.
- `src/seedmind/contracts/action.py` — classes: PrimitiveAction
- `src/seedmind/contracts/observation.py` — classes: ObservationPacket; functions: _validate_channel
- `src/seedmind/contracts/spatial.py` — classes: Direction, GridPosition
- `src/seedmind/core/__init__.py` — Predictive developmental core components for SeedMind.
- `src/seedmind/core/prediction_error.py` — classes: PredictionComparison, PredictionLoss; functions: compare_prediction, prediction_objective
- `src/seedmind/core/predictive_state.py` — classes: PredictiveCoreConfig, PredictiveCoreOutput, PredictiveSeedCore
- `src/seedmind/curiosity/__init__.py` — Learning-progress curiosity and bounded primitive experiment selection.
- `src/seedmind/curiosity/comparison.py` — classes: ScenarioFactory, PredictiveTrainer, TrainerFactory, CuriosityComparisonConfig, ExplorationActionCount, DiscoveryTimelinePoint, ExplorationTrialMetrics, CuriosityComparisonResult; functions: export_curiosity_comparison_json, export_curiosity_comparison_csv, _trial_payload, _set_metrics
- `src/seedmind/curiosity/policy.py` — classes: CuriosityConfig, CuriosityCandidate, CuriositySelection, CuriositySubsystem; functions: export_curiosity_timeline_json, export_curiosity_timeline_csv, _candidate_payload
- `src/seedmind/curiosity/session.py` — classes: ScenarioFactory, CuriosityTrainingConfig, CuriosityTrainingStepRecord, CuriosityTrainingResult, CuriosityTrainingSession; functions: export_curiosity_training_json, export_curiosity_training_csv
- `src/seedmind/environment/__init__.py` — Symbolic environment surrounding the SeedMind core.
- `src/seedmind/environment/dynamic_scenario.py` — classes: DynamicNurseryScenarioFactory
- `src/seedmind/environment/entities.py` — classes: EntityRole, ShapeCode, AgentState, EntityState
- `src/seedmind/environment/gymnasium_adapter.py` — classes: SeedMindNurseryEnv
- `src/seedmind/environment/observation.py` — classes: NurseryObservationAdapter
- `src/seedmind/environment/processes.py` — classes: WorldProcessOutcome, WorldProcessEvent, WorldProcessResult, WorldProcess, WorldProcessPipeline, CyclicEntityPatrolProcess, DirectionalFlowProcess, PeriodicBlockingToggleProcess; functions: _entity_by_id, _movement_blocked_outcome, _movement_event
- `src/seedmind/environment/runtime.py` — classes: NurseryRuntimeStep, NurseryRuntime
- `src/seedmind/environment/scenario.py` — classes: TargetOccupancy, NurseryScenario, NurseryScenarioFactory; functions: detect_target_occupancy
- `src/seedmind/environment/state.py` — classes: NurseryState
- `src/seedmind/environment/teacher.py` — classes: TeacherPushDemonstrationProcess, TeacherDemonstrationScenarioFactory; functions: _entity_by_id
- `src/seedmind/environment/transition.py` — classes: TransitionOutcome, NurseryTransition, NurseryTransitionEngine
- `src/seedmind/human/__init__.py` — Symbolic human apprenticeship and calibrated help seeking.
- `src/seedmind/human/apprenticeship.py` — classes: HelpReason, CaregiverEventType, HelpSeekingConfig, HelpContext, HelpDecision, TeacherResponse, CaregiverEvent, CaregiverMemory; functions: export_apprenticeship_report_json, export_apprenticeship_timeline_csv, _event_payload, _validate_unit_interval
- `src/seedmind/human/contracts.py` — classes: SupportLevel, HumanSignalCode, RequestIntentCode, VerificationRule, HumanRequest, HumanSignalFrame, HumanSignalCodec; functions: _validate_unit_interval
- `src/seedmind/integration/__init__.py` — Typed integration boundaries between validated SeedMind subsystems.
- `src/seedmind/integration/advice_acceptance.py` — classes: AdviceTimelineRecord, AdviceAcceptanceResult, AdviceAcceptanceEvidence, _SafetyProbes; functions: run_advice_acceptance, export_advice_acceptance, _aggregate, _timeline_record, _growth_budget_exhaustion_probe_passed, _run_safety_probes, _write_json
- `src/seedmind/integration/advice_evidence.py` — functions: collect_local_evidence, _assemble_evidence, _positive
- `src/seedmind/integration/bounded_advice.py` — classes: AdviceCode, AdviceConfig, AdviceEvidence, AdviceDecision, ConfidenceCalibration, BoundedAdvicePolicy; functions: _unit
- `src/seedmind/integration/candidate_session.py` — classes: CandidateStep, CandidateSessionResult; functions: run_candidate_session
- `src/seedmind/integration/comparison_oracle.py` — classes: CandidateOutcome, CandidateComparison, NurseryOutcomeOracle; functions: _mean_change, _resource_cost, _transition_risk, _unit
- `src/seedmind/integration/consolidation_acceptance.py` — classes: ConsolidationAcceptanceResult, ConsolidationAcceptanceEvidence; functions: run_consolidation_acceptance, export_consolidation_acceptance, _build_live_checkpoint, _record_later_contradiction, _action_value, _write_ascii_json
- `src/seedmind/integration/consolidation_proposal_lifecycle_acceptance.py` — classes: ConsolidationProposalLifecycleShadowObservation, ConsolidationProposalLifecycleAcceptanceResult, ConsolidationProposalLifecycleAcceptanceEvidence, _LifecycleObservedShadowAdapter; functions: run_consolidation_proposal_lifecycle_acceptance, export_consolidation_proposal_lifecycle_acceptance, _build_live_lifecycle_request, _action_value, _write_ascii_json, _validate_code
- `src/seedmind/integration/consolidation_scheduling_acceptance.py` — classes: ConsolidationSchedulingShadowObservation, ConsolidationSchedulingAcceptanceResult, ConsolidationSchedulingAcceptanceEvidence, _SchedulingObservedShadowAdapter; functions: run_consolidation_scheduling_acceptance, export_consolidation_scheduling_acceptance, _build_live_schedule_request, _action_value, _write_ascii_json
- `src/seedmind/integration/contextual_mastery_acceptance.py` — classes: ContextualMasteryAcceptanceResult, ContextualMasteryAcceptanceEvidence; functions: run_contextual_mastery_acceptance, export_contextual_mastery_acceptance, _persistence_probes, _write_legacy_v1, _write_trace_timeline, _write_json, _canonical_bytes
- `src/seedmind/integration/developmental_signals.py` — classes: LiveDevelopmentalSignals, LiveDevelopmentalSignalProvider; functions: _ambition_relevance, _action_controllability, _resource_pressure, _mean_absolute, _clamp_unit, _validate_unit
- `src/seedmind/integration/human_approved_consolidation_execution_acceptance.py` — classes: HumanApprovedConsolidationExecutionAcceptanceResult, HumanApprovedConsolidationExecutionAcceptanceEvidence; functions: run_human_approved_consolidation_execution_acceptance, export_human_approved_consolidation_execution_acceptance, _write_ascii_json
- `src/seedmind/integration/ndnra_shadow.py` — classes: ShadowScenarioFactory, NDNRAShadowConfig, ShadowSuggestion, ShadowStepRecord, NDNRAShadowSessionConfig, NDNRAShadowSessionResult, NDNRAShadowAdapter, NDNRAShadowSession; functions: _availability_fact, _assembly_id, _mean_absolute, _resource_cost, _clamp_unit, _validate_unit
- `src/seedmind/integration/persistent_shadow_experiment.py` — classes: PersistentShadowResult, PersistentShadowEvidence; functions: run_persistent_shadow_experiment, export_persistent_shadow_evidence, _derive_growth_state, _total_assembly_evidence, _build_trainer, _write_ascii_json
- `src/seedmind/integration/restart_safe_proposal_memory_acceptance.py` — classes: RestartSafeProposalMemoryObservation, RestartSafeProposalMemoryAcceptanceResult, RestartSafeProposalMemoryAcceptanceEvidence, _RestartRevalidatingShadowAdapter; functions: run_restart_safe_proposal_memory_acceptance, export_restart_safe_proposal_memory_acceptance, _add_independent_lifecycle_evidence, _legacy_migration_is_empty, _checksum_corruption_falls_back, _relational_corruption_falls_back, _complete_fallback, _read_json_object, _require_object, _write_envelope
- `src/seedmind/integration/shadow_experiment.py` — classes: ShadowComparisonResult; functions: run_shadow_comparison, export_shadow_comparison_evidence, _build_trainer, _write_ascii_json
- `src/seedmind/integration/unified_shadow.py` — classes: UnifiedShadowConfig, UnifiedShadowStepRecord, UnifiedShadowResult, NDNRALiveShadowAdapter, UnifiedDevelopmentalShadowSession; functions: _assembly_id, _availability_fact, _positive_intensity, _validate_unit
- `src/seedmind/integration/unified_signal_experiment.py` — classes: UnifiedSignalExperimentResult, UnifiedSignalEvidence; functions: run_unified_signal_experiment, export_unified_signal_evidence, _build_signal_provider, _adopted_ambition_manager, _most_dormant_assembly, _build_trainer, _write_ascii_json
- `src/seedmind/memory/__init__.py` — Episodic SQLite memory, significance, retrieval, and beliefs.
- `src/seedmind/memory/beliefs.py` — classes: BeliefRegistryConfig, BeliefRegistry; functions: _belief_id, _belief_from_row, _evidence_from_row
- `src/seedmind/memory/inspector.py` — functions: export_memory_inspector_json, export_belief_evidence_csv, _event_payload, _belief_payload, _evidence_payload
- `src/seedmind/memory/models.py` — classes: EpisodicEventType, BeliefEvidencePolarity, BeliefStatus, SignificanceFeatures, EpisodicEventDraft, EpisodicEvent, MemoryQuery, BeliefProposition; functions: _validate_identifier, _validate_unit_interval
- `src/seedmind/memory/significance.py` — classes: SignificanceConfig, SignificanceScorer
- `src/seedmind/memory/store.py` — classes: EpisodicSQLiteStore; functions: _event_from_row, _payload_from_json, _optional_bool_to_database, _optional_bool_from_database
- `src/seedmind/perception/__init__.py` — Body-independent perception components for SeedMind.
- `src/seedmind/perception/symbolic_encoder.py` — classes: SymbolicInputSpec, SymbolicObservationEncoder
- `src/seedmind/research/__init__.py` — Isolated research prototypes that do not alter the production runtime.
- `src/seedmind/research/ndnra/__init__.py` — Need-Driven Neural Recruitment Architecture research prototype.
- `src/seedmind/research/ndnra/adaptive.py` — classes: AdaptiveRuntimeConfig, AdaptiveUpdate, PressureDischarge, NDNRARuntimeAdaptiveState; functions: _validate_unit, _validate_signed
- `src/seedmind/research/ndnra/composition.py` — classes: ExperienceAssembly, SpecialistInteraction, MultidimensionalExperienceGraph, CompositionCandidate, CompositionResult, _SearchState, NeedDrivenComposer; functions: _scale_effects, _validate_code, _validate_facts
- `src/seedmind/research/ndnra/consolidation.py` — classes: ConsolidationRejectionReason, ConsolidationCandidate, ConsolidationEligibilityPolicy, ConsolidationEligibility; functions: _append_profile_rejections, _validated_source_ids, _resolve_supporting_traces, _available_codes, _candidate_id, _add_reason, _valid_requested_change, _meets_minimum, _unit_meets_minimum, _count_meets_minimum
- `src/seedmind/research/ndnra/consolidation_application.py` — classes: ConsolidationStructureState, ConsolidationStateSnapshot, ConsolidationApplicationResult, ConsolidationApplicationState; functions: _validated_candidate, _updated_state, _validated_identifiers, _validated_states, _validate_state_collection, _validate_state_mapping, _validate_sorted_unique_codes, _find_state, _snapshot_ids, _validate_code
- `src/seedmind/research/ndnra/consolidation_execution_approval.py` — classes: ConsolidationExecutionApprovalRequest, ConsolidationExecutionPermit, ConsolidationExecutionApprovalPolicy; functions: _permit_id, _validate_code, _validate_nonnegative_int
- `src/seedmind/research/ndnra/consolidation_execution_commit.py` — classes: ConsolidationApplicationTarget, ConsolidationExecutionCommitRequest, ConsolidationExecutionCommitReceipt, ConsolidationExecutionCommitResult, ConsolidationExecutionCommitPolicy; functions: _interrupt, _restore_failed_application, _execution_id, _normalized_codes, _validate_code, _validate_nonnegative_int
- `src/seedmind/research/ndnra/consolidation_execution_durable_commit.py` — classes: ConsolidationExecutionDurableCommitResult, ConsolidationExecutionDurableCommitPolicy; functions: _matches_persisted_boundaries, _matches_loaded_result, _matches_expected, _restore_application_state, _interrupt
- `src/seedmind/research/ndnra/consolidation_execution_permit_lifecycle.py` — classes: ConsolidationExecutionPermitLifecycleAction, ConsolidationExecutionPermitLifecycleStatus, ConsolidationExecutionPermitTransitionRequest, ConsolidationExecutionPermitTransitionDecision, ConsolidationExecutionPermitLifecycleRecord, ConsolidationExecutionPermitLifecycleRegistry; functions: _status_for, _validate_transition_episode, _transition_decision_id, _validate_code, _validate_nonnegative_int
- `src/seedmind/research/ndnra/consolidation_execution_persistence.py` — classes: NDNRAExecutionCheckpoint; functions: _canonical_registry, _restore_registry, _restore_record, _restore_transition, _restore_permit, _restore_revalidation, _restore_receipt, _identity, _require_mapping, _require_list
- `src/seedmind/research/ndnra/consolidation_interference_experiment.py` — classes: ConsolidationInterferenceCondition, ConsolidationInterferenceConfig, OverlappingLessonMemorySnapshot, ConsolidationInterferenceConditionResult, ConsolidationInterferenceExperimentResult, ConsolidationInterferenceExperimentEvidence, _OverlappingLessonMemory; functions: run_consolidation_interference_experiment, _build_old_lesson_ledger, _train_old_lesson, _run_condition, _aligned_lesson_target, _effective_learning_rate, _clamp_signed, _validate_code, _validate_unit, _validate_signed
- `src/seedmind/research/ndnra/consolidation_persistence.py` — classes: ConsolidationRollbackAuditRecord, NDNRAConsolidationCheckpoint; functions: restore_consolidation_application, restore_consolidation_state_snapshot, _application_snapshot, _restore_application, _restore_candidate, _restore_mastery_profile, _restore_state_snapshot, _restore_structure_state, _state_identity_sets, _require_mapping
- `src/seedmind/research/ndnra/consolidation_portfolio.py` — classes: ConsolidationPortfolioItem, ConsolidationPortfolioItemDecision, ConsolidationPortfolioDecision, ConsolidationPortfolioPolicy; functions: _validated_items, _lesson_key, _priority_key
- `src/seedmind/research/ndnra/consolidation_proposal_history.py` — classes: ConsolidationProposalLifecycleRecord; functions: _validate_history
- `src/seedmind/research/ndnra/consolidation_proposal_lifecycle.py` — classes: ConsolidationProposalReviewAction, ConsolidationProposalLifecycleStatus, ConsolidationProposalReviewRequest, ConsolidationProposalReviewDecision, ConsolidationProposalReviewPolicy; functions: _status_for, _decision_id, _validate_code, _validate_nonnegative_int
- `src/seedmind/research/ndnra/consolidation_proposal_lifecycle_experiment.py` — classes: ConsolidationProposalLifecycleStrategy, ConsolidationProposalLifecycleEvent, ConsolidationProposalLifecycleStrategyResult, ConsolidationProposalLifecycleExperimentResult; functions: run_consolidation_proposal_lifecycle_experiment, export_consolidation_proposal_lifecycle_experiment, _run_strategy, _strategy_result, _event, _review_request, _evolving_proposals, _trace, _validate_code, _validate_nonnegative_int
- `src/seedmind/research/ndnra/consolidation_proposal_management.py` — classes: ConsolidationProposalManagementAction, ConsolidationProposalDisposition, ConsolidationProposalManagementRequest, ConsolidationProposalManagementDecision, ConsolidationProposalManagedRecord, ConsolidationProposalLifecycleRegistry; functions: _validate_replacement, _management_decision, _disposition_for, _latest_lifecycle_episode, _validate_code, _validate_nonnegative_int, _validate_positive_int
- `src/seedmind/research/ndnra/consolidation_proposal_persistence.py` — classes: NDNRAProposalLifecycleCheckpoint; functions: restore_consolidation_schedule_proposal, restore_consolidation_candidate, restore_mastery_profile, _restore_registry, _restore_managed_record, _restore_lifecycle_record, _restore_review_decision, _restore_management_decision, _restore_proposal, _restore_candidate
- `src/seedmind/research/ndnra/consolidation_proposal_revalidation.py` — classes: ConsolidationProposalRevalidationStatus, ConsolidationProposalRevalidationDecision, ConsolidationProposalRevalidationReport, ConsolidationProposalRevalidationPolicy; functions: _source_events_available, _validated_newer_proposals, _select_superseding_proposal, _normalized_codes, _add_reason, _decision_id, _validate_code, _validate_nonnegative_int
- `src/seedmind/research/ndnra/consolidation_reopening.py` — classes: ConsolidationReopeningTrigger, ConsolidationReopeningPolicy, ConsolidationReopeningDecision, ConsolidationRollbackResult; functions: rollback_consolidation, _validate_trace_matches_candidate, _trace_is_contradictory, _rollback_id, _snapshot_payload, _state_payload, _snapshot_ids, _validate_sorted_unique_codes, _validate_code, _validate_unit
- `src/seedmind/research/ndnra/consolidation_scheduling.py` — classes: ConsolidationScheduleStatus, ConsolidationScheduleRequest, ConsolidationSchedulingContext, ConsolidationScheduleProposal, ConsolidationScheduleDecision, ConsolidationSchedulingPolicy; functions: _proposal_id, _validate_sorted_unique_codes, _validate_code, _validate_nonnegative_int, _validate_positive_int, _validate_positive_unit
- `src/seedmind/research/ndnra/consolidation_scheduling_experiment.py` — classes: ConsolidationSchedulingStrategy, ConsolidationSchedulingExperimentConfig, ConsolidationSchedulingProposalRecord, ConsolidationSchedulingStrategyResult, ConsolidationSchedulingExperimentResult; functions: run_consolidation_scheduling_experiment, export_consolidation_scheduling_experiment, _strategy_result, _candidate_for, _is_fixed_window, _lesson_key, _requests, _evidence_arrivals, _trace
- `src/seedmind/research/ndnra/contextual_mastery_experiment.py` — classes: ContextualMasteryExperimentResult, ContextualMasteryExperimentEvidence; functions: run_contextual_mastery_experiment, _learn, _identity_conflict_is_blocked, _context, _route_switches, _route_snapshots
- `src/seedmind/research/ndnra/contextual_memory.py` — classes: ContextualRecordCode, EventIdentity, ContextSignature, ContextualExperienceTrace, ContextualLearningResult, LessonIdentity, MasteryProfile, RouteSupport; functions: _jaccard, _quantize, _validate_code, _require_mapping, _require_list, _require_string, _require_bool, _require_int, _require_float, _require_string_list
- `src/seedmind/research/ndnra/effects.py` — classes: EffectObservation, EffectEstimate, SparseEffectMemory, NeedDimension, EffectNeed, LocalEffectLink; functions: combine_projected_effects, _require_mapping, _require_string, _require_int, _require_float, _validate_code, _validate_unit_interval, _validate_signed_unit
- `src/seedmind/research/ndnra/experiment.py` — classes: RecallStepRecord, RecallEpisodeResult, TeacherTrainingResult, NDNRAExperimentResult; functions: train_teacher_demonstrations, evaluate_recall, run_ndnra_heat_fan_experiment, export_ndnra_evidence, _need_persisted_until_cooling, _failed_recall_cost, _write_ascii_json
- `src/seedmind/research/ndnra/growth.py` — classes: StructuralGrowthConfig, GrowthAttemptRecord, GrowthOutcome, EvidenceDrivenGrowthController; functions: grow_random_specialist, _validate_unit, _validate_signed
- `src/seedmind/research/ndnra/growth_cycle.py` — classes: GrowthCycleConfig, GrowthResolution, GoalGatedGrowthCycle; functions: _validate_unit
- `src/seedmind/research/ndnra/growth_experiment.py` — classes: StructuralGrowthExperimentResult; functions: structural_cooling_need, build_capacity_limited_graph, run_ndnra_structural_growth_experiment, export_structural_growth_evidence, _duplicate_growth_is_blocked, _write_ascii_json
- `src/seedmind/research/ndnra/heat_world.py` — classes: HeatWorldState, HeatTransition, HeatFanWorld
- `src/seedmind/research/ndnra/models.py` — classes: HeatAction, HeatContext, NeuronKind, LocalNeuron, LocalSynapse, NeedPulse, RecallResult, ModulationSummary; functions: _validate_unit_interval, _validate_signed_unit
- `src/seedmind/research/ndnra/multi_growth_experiment.py` — classes: MultiGrowthExperimentResult; functions: run_multi_growth_experiment, evaluate_unresolved_budget_exhaustion, _build_graph, _complex_need, _satisfaction, _duplicate_membership_is_blocked
- `src/seedmind/research/ndnra/multieffect_experiment.py` — classes: MultieffectExperimentResult; functions: cooling_need, cleanliness_need, build_multieffect_graph, build_intended_effect_only_baseline, run_ndnra_multieffect_experiment, export_multieffect_evidence, _candidate_row, _write_ascii_json
- `src/seedmind/research/ndnra/network.py` — classes: LocalNeuralGraphConfig, LocalNeuralGraph; functions: _context_neuron_id, _action_neuron_id
- `src/seedmind/research/ndnra/persistence.py` — classes: BrainLoadStatus, NDNRAGrowthState, BrainSaveResult, BrainLoadResult, NDNRABrainStore; functions: _interrupt, _restore_graph, _restore_assembly, _restore_specialist, _checksum, _canonical_bytes, _require_mapping, _require_list, _require_string, _require_int
- `src/seedmind/safety/__init__.py` — SeedMind safety package.
- `src/seedmind/self_model/__init__.py` — Online action-effect evidence and initial SeedMind self-model.
- `src/seedmind/self_model/action_effects.py` — classes: SelfModelConfig, ActionEffectEstimate, BodySensorEstimate, SelfModelSnapshot, _ActionAccumulator, SelfModelRegistry; functions: export_self_model_json, export_action_effects_csv
- `src/seedmind/self_model/baseline.py` — classes: ScenarioFactory, BodyDiscoveryBaselineConfig, ActionSampleCount, BodyDiscoveryStrategyMetrics, BodyDiscoveryComparisonResult, BodyDiscoveryBaselineExperiment; functions: export_body_discovery_baseline_json, export_body_discovery_baseline_csv, _strategy_payload, _set_metrics
- `src/seedmind/training/__init__.py` — Experience collection and predictive training for SeedMind.
- `src/seedmind/training/experience.py` — classes: ExperienceTransition; functions: collect_experience, _sensor_difference
- `src/seedmind/training/online_trainer.py` — classes: OnlineTrainerConfig, OnlineTrainingMetrics, OnlinePredictiveTrainer
- `src/seedmind/training/session.py` — classes: ScenarioFactory, FamiliarSequenceConfig, TrainingStepRecord, TrainingSessionResult, FamiliarSequenceTrainingSession; functions: save_training_checkpoint, load_training_checkpoint, export_training_history_csv, export_prediction_error_svg, _scenario_identity, _session_identity, _record_to_payload, _record_from_payload, _validate_checkpoint_progress, _required_int
- `tests/unit/ndnra_execution_test_support.py` — classes: ExecutionSetup; functions: record_trace, build_proposal, build_setup, commit_request, save_initial, execute_loaded, raise_at, read_object, object_value, list_value
- `tests/unit/test_action_contract.py` — functions: test_primitive_action_values_are_stable, test_primitive_action_can_be_created_from_wire_value
- `tests/unit/test_ambition_engine.py` — functions: observed_demo, adopted_manager, test_detector_requires_three_confirmed_repetitions, test_unconfirmed_repetition_does_not_form_candidate, test_ambition_persists_across_episodes, test_budget_and_milestone_progression, test_state_round_trip_and_dashboard, test_final_milestone_completes_ambition
- `tests/unit/test_apprenticeship.py` — functions: make_request, make_context, blocked_context, familiar_context, test_blocked_high_uncertainty_requests_help, test_familiar_low_risk_avoids_unnecessary_help, test_safe_low_cost_experiment_is_preferred_over_help, test_guided_learner_requires_more_uncertainty_than_dependent_level, test_teacher_demonstrates_blockage_and_clarifies_ambiguity, test_verified_familiar_approvals_promote_support_level
