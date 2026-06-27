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

## `src/seedmind/integration/contextual_mastery_acceptance.py`

Acceptance gate for contextual NDNRA traces and bounded mastery evidence.

- Kind: python
- Classes: ContextualMasteryAcceptanceResult, ContextualMasteryAcceptanceEvidence
- Functions/symbols: run_contextual_mastery_acceptance, export_contextual_mastery_acceptance, _persistence_probes, _write_legacy_v1, _write_trace_timeline, _write_json, _canonical_bytes

## `src/seedmind/integration/developmental_signals.py`

Typed live developmental signals for non-authoritative NDNRA integration.

- Kind: python
- Classes: LiveDevelopmentalSignals, LiveDevelopmentalSignalProvider
- Functions/symbols: _ambition_relevance, _action_controllability, _resource_pressure, _mean_absolute, _clamp_unit, _validate_unit

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

## `src/seedmind/research/ndnra/adaptive.py`

Operational adaptive state restored alongside an NDNRA local graph.

- Kind: python
- Classes: AdaptiveRuntimeConfig, AdaptiveUpdate, PressureDischarge, NDNRARuntimeAdaptiveState
- Functions/symbols: _validate_unit, _validate_signed

## `src/seedmind/research/ndnra/composition.py`

Need-driven composition over local multidimensional experience assemblies.

- Kind: python
- Classes: ExperienceAssembly, SpecialistInteraction, MultidimensionalExperienceGraph, CompositionCandidate, CompositionResult, _SearchState, NeedDrivenComposer
- Functions/symbols: _scale_effects, _validate_code, _validate_facts

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
- Functions/symbols: _restore_graph, _restore_assembly, _restore_specialist, _checksum, _canonical_bytes, _require_mapping, _require_list, _require_string, _require_int, _require_float, _require_string_list, _require_numeric_list, _validate_code, _validate_unit, _validate_signed

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

## `tests/unit/test_ndnra_contextual_mastery.py`

Tests for contextual NDNRA redundancy and bounded mastery evidence.

- Kind: python
- Functions/symbols: test_contextual_mastery_experiment_distinguishes_replay_from_breadth, test_one_shot_protection_and_varied_mastery_remain_distinct, test_contradiction_reduces_mastery_without_erasing_sources, test_event_identity_key_is_collision_safe, test_contradictory_effect_does_not_create_protective_strength, test_contextual_recording_is_atomic_when_identity_validation_fails, test_contextual_mastery_gate_preserves_shadow_and_persistence, test_contextual_mastery_has_no_sqlite_cognitive_dependency

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

## `tests/unit/test_ndnra_recall.py`

Tests for need-driven recruitment, dormancy, and effort-based recall.

- Kind: python
- Functions/symbols: test_untrained_graph_cannot_reconstruct_cooling_chain, test_dormant_memory_requires_deeper_recall_and_resolves_need, test_complete_experiment_passes_local_memory_gate, test_growth_pressure_requires_all_developmental_factors

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
