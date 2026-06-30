# NDNRA Developmental Network v0.2 Stage 4 Evidence

Date: 30 June 2026
Scope: Stage 4 regional child-to-adult development, skill maturation, and ambition persistence
Status: implemented and validated; local commit pending

## 1. Boundary

Stage 4 is an isolated in-memory research batch under `src/seedmind/research/ndnra`.

It implements deterministic regional maturation evidence with child, mature, and relearning region states; maturity-dependent plasticity, exploration, teacher influence, permanence threshold, and inhibition; maturation controls; evidence-based skill promotion; developmental Outcome Fidelity; bounded verifier reopening; accepted desired-state ambition sources; capability-gap evidence kept separate from value; ambition pressure lifecycle evidence; exact rollback evidence; and zero-authority counters.

It does not implement homeostasis, hibernation, dream maintenance, restart persistence, conscience-guided proposals, runtime integration, action gateways, autonomous workers, SQLite cognition, or production action authority.

## 2. Hypothesis

Region-local maturity can allow child-like learning, mature retention, bounded local relearning, and persistent ambition without a global maturity switch. Skill promotion should require grounded verifier evidence rather than producer confidence, and persistent ambition should require an accepted desired-state source, progress, and feasible Nursery learning opportunities.

## 3. Deterministic Scenario

The canonical Stage 4 evidence contains:

- a child curiosity region with high plasticity and exploration;
- a mature task region with reduced plasticity, higher permanence, and protected core connections;
- a bounded task-region relearning zone for context drift;
- maturation controls for permanently high plasticity, permanently low plasticity, a global maturity state, and proposed regional developmental control;
- a mature skill bundle with verified grounded feedback and an explicit reopened verifier zone after correction or drift;
- accepted desired-state value sources for Nursery purpose, trusted teaching, mature prompt, and observed purpose-compatible outcome;
- capability-gap evidence from observed ability, failed request, and recognised mistake;
- ambition pressure evidence for candidate, accepted, paused, satisfied, and retired states;
- exact rollback checksum equivalence.

## 4. Implementation Evidence

| Requirement | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| Regional maturity state and maturity-dependent controls. | `RegionalMaturityProfile`, `RegionalMaturityState` | `test_child_and_mature_regions_use_distinct_local_maturity_controls` | Implemented and evidenced |
| Child mode learns faster than mature mode. | High-plasticity and low-plasticity controls | `test_maturation_controls_show_regional_control_beats_required_baselines` | Implemented and evidenced |
| Mature mode retains established associations under conflict. | Proposed regional control retention score | `test_maturation_controls_show_regional_control_beats_required_baselines` | Implemented and evidenced |
| Promotion requires varied-context success, retention, low interference, and reduced correction. | `SkillMaturationEvidence` | `test_promotion_requires_varied_context_retention_low_interference_and_low_correction` | Implemented and evidenced |
| Mature region opens bounded relearning without destabilising protected core. | `RelearningRollbackEvidence` | `test_relearning_zone_is_bounded_and_rollback_restores_exact_state` | Implemented and evidenced |
| New learning consolidates only after old-skill validation. | Skill and relearning validation flags | `test_promotion_requires_varied_context_retention_low_interference_and_low_correction` | Implemented and evidenced |
| Regions may have different maturity states. | Child curiosity and mature task profiles | `test_child_and_mature_regions_use_distinct_local_maturity_controls` | Implemented and evidenced |
| Four accepted desired-state sources can define grounded desired states. | `PersistentAmbitionEvidence.accepted_value_sources` | `test_value_sources_and_capability_gaps_are_complete_and_separate` | Implemented and evidenced |
| Capability gaps remain separate from value. | `CapabilityGapEvidence` from all accepted sources | `test_value_sources_and_capability_gaps_are_complete_and_separate` | Implemented and evidenced |
| Persistent ambition requires source, progress, and feasible Nursery opportunity. | `PersistentAmbitionEvidence` | `test_value_sources_and_capability_gaps_are_complete_and_separate`, `test_ambition_pressure_reduces_after_pause_satisfaction_and_retirement` | Implemented and evidenced |
| Skill verifier beats producer self-judgement and retains scope. | Verifier accuracy and scope codes | `test_skill_verifier_beats_producer_and_reopens_after_drift` | Implemented and evidenced |
| Mature skill can reopen a bounded verifier-learning zone after correction or drift. | Reopened skill bundle and verifier zone | `test_skill_verifier_beats_producer_and_reopens_after_drift` | Implemented and evidenced |
| Satisfaction, pause, or retirement reduces ambition pressure. | `pressure_by_state` | `test_ambition_pressure_reduces_after_pause_satisfaction_and_retirement` | Implemented and evidenced |
| Rollback restores the pre-consolidation state exactly. | Equal rollback checksums | `test_relearning_zone_is_bounded_and_rollback_restores_exact_state` | Implemented and evidenced |
| SQLite cognition and production authority remain zero. | Integrated zero counters plus static dependency test | `test_stage_four_acceptance_matrix_is_complete_and_zero_authority`, `test_developmental_maturation_has_no_forbidden_runtime_dependencies` | Implemented and evidenced |

## 5. Completion Matrix

The integrated `StageFourMaturationEvidence.completion_matrix()` reports every Stage 4 pass gate as `implemented_and_evidenced`:

| Gate | Status |
| --- | --- |
| child_mode_learns_faster_than_mature_mode | Implemented and evidenced |
| mature_mode_retains_established_associations | Implemented and evidenced |
| promotion_requires_varied_success_retention_low_interference_and_low_correction | Implemented and evidenced |
| mature_region_opens_bounded_relearning_without_core_destabilisation | Implemented and evidenced |
| new_learning_consolidates_only_after_old_skill_validation | Implemented and evidenced |
| regions_can_have_different_maturity_states | Implemented and evidenced |
| accepted_value_source_kinds_define_grounded_desired_state | Implemented and evidenced |
| capability_gaps_remain_separate_from_value_source | Implemented and evidenced |
| persistent_ambition_requires_source_progress_and_opportunity | Implemented and evidenced |
| skill_verifier_beats_producer_and_retains_scope | Implemented and evidenced |
| mature_skill_reopens_bounded_verifier_learning_zone | Implemented and evidenced |
| pause_satisfaction_or_retirement_reduces_ambition_pressure | Implemented and evidenced |
| rollback_restores_pre_consolidation_state_exactly | Implemented and evidenced |
| proposed_regional_control_beats_maturation_controls | Implemented and evidenced |
| zero_sqlite_side_effects_and_authority | Implemented and evidenced |

Deferred: homeostasis, activation normalization, hibernation, dreams, restart identity, learned responsibility, conscience-guided proposals, shadow trials, runtime integration, and action gateways.

Out of scope: SQLite cognition, persistence, runtime adapters, action gateways, production action authority, autonomous workers, internet access, pretrained language model integration, task-specific solution injection, physical robotics, proof-store mutation, and v0.1 schema mutation.

## 6. Controls And Falsification

Controls represented in the deterministic evidence:

- permanently high plasticity;
- permanently low plasticity;
- one global maturity state;
- proposed regional developmental control.

Falsification status: not falsified in this bounded scenario. The evidence rejects a global maturity switch, child regions with low plasticity, mature regions with excessive plasticity, promotion without varied context, promotion without old-skill validation, verifier acceptance from producer self-judgement alone, stale verifier maturity after drift, value-gap confusion, curiosity ownership of commitment, rollback mismatch, SQLite cognition, external side effects, and production action authority.

## 7. Validation

Focused implementation checks before this document:

```text
ruff format src/seedmind/research/ndnra/developmental_maturation.py src/seedmind/research/ndnra/__init__.py tests/unit/test_ndnra_developmental_maturation.py: passed
ruff check src/seedmind/research/ndnra/developmental_maturation.py src/seedmind/research/ndnra/__init__.py tests/unit/test_ndnra_developmental_maturation.py: passed
mypy src/seedmind/research/ndnra/developmental_maturation.py tests/unit/test_ndnra_developmental_maturation.py: passed
pytest -q tests/unit/test_ndnra_developmental_maturation.py --basetemp .pytest_tmp/stage4_focused: 12 passed
```

Full repository gates before local batch commit:

```text
ruff format --check .: 251 files already formatted
ruff check .: passed
mypy .: no issues in 251 source files
pytest -q --basetemp .pytest_tmp/full_repo_stage4_final: 1064 passed
pip check: no broken requirements
git diff --check: passed
```

## 8. Next Stage

The next bounded batch after successful final gates is Stage 5: homeostasis and runaway-network control. Stage 5 must not begin hibernation, dream maintenance, restart persistence, conscience-guided proposals, or action-gateway work.
