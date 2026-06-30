# NDNRA Developmental Network v0.2 Stage 2 Evidence

Date: 30 June 2026
Scope: Stage 2 associative need-and-context recall
Status: implemented and validated; local commit pending

## 1. Boundary

Stage 2 is an isolated in-memory research batch under `src/seedmind/research/ndnra`.

It implements deterministic associative recall over the Stage 1 recurrent substrate while preserving separate episode identity. It adds typed need-to-experience, context-to-experience, experience-to-experience, action-to-experience, outcome-to-experience, and inhibitory links; partial-cue activation; local pattern completion; context-sensitive competition; bounded compatible coalition selection; matched controls; and explicit recall-depth and dormancy effort evidence.

It does not implement simultaneous multiple needs, region-local pools, mature skill promotion, mature ambition lifecycle, persistence, hibernation, dreams, conscience-guided proposals, runtime integration, action gateways, autonomous workers, SQLite cognition, or production action authority.

## 2. Hypothesis

Need and context associations can generalise from distinct experiences without merging them. A partial unseen context should recruit useful need-relevant experiences, change ordering when the present context changes, suppress contradictory experience through inhibition, outperform shuffled and ablated controls, and keep resource cost bounded by recall depth and dormancy.

## 3. Deterministic Scenario

The canonical scenario trains four distinct cooling experiences plus one unrelated cleaning experience in the Stage 1 substrate:

- `episode:cool_warm_fan`;
- `episode:cool_sunny_blinds`;
- `episode:cool_humid_vent`;
- `episode:cool_warm_wait`;
- `episode:clean_dirty_wipe`.

The warm-sunny cue is an unseen context:

```text
need:cool
current context: context:warm_sunny_room
partial contexts: context:sunny_room, context:warm_room
```

The humid cue changes the present context to `context:humid_shadow_room` with partial context `context:humid_room`.

## 4. Implementation Evidence

| Requirement | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| Learned need, context, experience, action, outcome, and inhibition links. | `AssociativeRecallLinkKind`, `AssociativeRecallLink`, `build_stage_two_associative_links` | `test_stage_two_links_cover_required_association_types_and_reject_bad_links` | Implemented and evidenced |
| Partial-cue activation and local pattern completion. | `AssociativeRecallCue`, `run_associative_recall`, `_settle_associative_scores` | `test_partial_context_changes_order_and_beats_exact_context_only` | Implemented and evidenced |
| Need-relevant experiences exceed unrelated controls. | `StageTwoAssociativeRecallEvidence.pass_gate_matrix` | `test_need_relevant_experiences_exceed_unrelated_without_merging_identity` | Implemented and evidenced |
| Present context changes response ordering. | Warm-sunny and humid recall results | `test_partial_context_changes_order_and_beats_exact_context_only` | Implemented and evidenced |
| Useful compatible coalition dominates one-winner control. | `AssociativeRecallResult.dominant_episode_ids`, `ONE_WINNER_ONLY` control | `test_compatible_multi_experience_coalition_beats_one_winner_control` | Implemented and evidenced |
| Original experience identity remains inspectable. | `DevelopmentalNetworkState.episodes`, coalitions, episode IDs | `test_need_relevant_experiences_exceed_unrelated_without_merging_identity` | Implemented and evidenced |
| Contradictory experience remains available but inhibited. | `INHIBITION` links and `INHIBITION_REMOVED` control | `test_contradictory_experience_remains_available_but_inhibited` | Implemented and evidenced |
| Partial cue beats shuffled, need-removed, and context-removed controls. | Matched `AssociativeRecallControl` results | `test_partial_cue_beats_shuffled_need_removed_and_context_removed_controls` | Implemented and evidenced |
| False co-activation remains below threshold. | `AssociativeRecallResult.false_coactivation_rate` | `test_false_coactivation_and_recall_cost_stay_bounded` | Implemented and evidenced |
| Recall cost rises with depth and dormancy. | `RecallCostMeasurement` | `test_false_coactivation_and_recall_cost_stay_bounded` | Implemented and evidenced |
| Deterministic evidence identity and public exports. | `StageTwoAssociativeRecallEvidence.evidence_id`, `__init__.py` exports | `test_recall_is_deterministic_and_rejects_invalid_cues_and_mutated_results`, `test_public_exports_cover_stage_two_associative_recall` | Implemented and evidenced |
| SQLite cognition and production authority remain zero. | Integrated zero counters plus static dependency test | `test_stage_two_acceptance_matrix_is_complete_and_zero_authority`, `test_stage_two_associative_recall_has_no_forbidden_runtime_dependencies` | Implemented and evidenced |

## 5. Completion Matrix

The integrated `StageTwoAssociativeRecallEvidence.completion_matrix()` reports every Stage 2 pass gate as `implemented_and_evidenced`:

| Gate | Status |
| --- | --- |
| need_relevant_experiences_exceed_unrelated | Implemented and evidenced |
| present_context_changes_response_ordering | Implemented and evidenced |
| compatible_context_coalition_dominates | Implemented and evidenced |
| original_experience_identities_remain_inspectable | Implemented and evidenced |
| contradictory_experience_available_but_inhibited | Implemented and evidenced |
| partial_cue_beats_shuffled_control | Implemented and evidenced |
| false_coactivation_below_threshold | Implemented and evidenced |
| recall_cost_rises_with_depth_and_dormancy | Implemented and evidenced |
| sqlite_and_authority_counts_zero | Implemented and evidenced |

Deferred: simultaneous multiple needs, region-local pools, regional specialization, mature skill promotion, mature ambition lifecycle, homeostasis, hibernation, dreams, restart identity, learned responsibility, typed action proposals, and shadow trial behavior.

Out of scope: SQLite cognition, persistence, runtime adapters, action gateways, production action authority, autonomous workers, internet access, pretrained language model integration, task-specific solution injection, physical robotics, proof-store mutation, and v0.1 schema mutation.

## 6. Controls And Falsification

Controls represented in the deterministic evidence:

- need connection removed;
- context connection removed;
- inhibition removed;
- recurrent links shuffled;
- one-winner-only recall;
- exact-context-only recall.

Falsification status: not falsified in this bounded scenario. The evidence rejects exact-context-only recall, shuffled association, no-need support, no-context support, no-inhibition contradiction handling, one-winner-only coalition selection, false co-activation above threshold, unbounded recall effort, SQLite cognition, external side effects, and production action authority.

## 7. Validation

Focused implementation checks before this document:

```text
ruff format --check src/seedmind/research/ndnra/developmental_associative_recall.py tests/unit/test_ndnra_developmental_associative_recall.py src/seedmind/research/ndnra/__init__.py: passed
ruff check src/seedmind/research/ndnra/developmental_associative_recall.py tests/unit/test_ndnra_developmental_associative_recall.py src/seedmind/research/ndnra/__init__.py: passed
mypy src/seedmind/research/ndnra/developmental_associative_recall.py tests/unit/test_ndnra_developmental_associative_recall.py src/seedmind/research/ndnra/__init__.py: passed
pytest -q tests/unit/test_ndnra_developmental_associative_recall.py --basetemp .pytest_tmp/stage2_focused: 12 passed
```

Full repository gates before local batch commit:

```text
ruff format --check .: 247 files already formatted
ruff check .: passed
mypy .: no issues in 247 source files
pytest -q --basetemp .pytest_tmp/full_repo_stage2_final: 1040 passed
pip check: no broken requirements
git diff --check: passed
```

## 8. Next Stage

The next bounded batch after successful final gates is Stage 3: specialised concurrent regions and multiple needs. Stage 3 must not begin mature skill promotion, mature ambition lifecycle, hibernation, dream maintenance, conscience-guided proposals, or action-gateway work.
