# NDNRA Developmental Network v0.2 Stage 1 Evidence

Date: 30 June 2026
Scope: Stage 1 persistent recurrent experiential substrate
Status: implemented and validated; local commit pending

## 1. Boundary

Stage 1 is an isolated in-memory research batch under `src/seedmind/research/ndnra`.

It implements a deterministic fixed reusable neuron pool, signed recurrent connections, distributed experience coalitions, exact episode provenance, and bounded recurrent replay. It does not implement persistence save/load, SQLite cognition, runtime integration, action gateways, live Nursery integration, autonomous workers, structural neuron creation, proof-store merging, or production action authority.

## 2. Implementation Evidence

| Requirement | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| Fixed initial sparse reusable neuron pool. | `DevelopmentalNetworkConfig`, `DevelopmentalNeuronState`, `create_developmental_network_state` | `tests/unit/test_ndnra_developmental_network.py::test_substrate_rejects_structural_neuron_creation_and_full_pool_coalitions` | Implemented and evidenced |
| Excitatory and inhibitory weighted recurrent connections. | `DevelopmentalConnectionState`, `_connections_for_new_coalition` | `test_contradictory_contexts_create_inhibitory_connections_without_erasing_details` | Implemented and evidenced |
| Local thresholds, excitability, eligibility, plasticity, maturity, dormancy, usage, and provenance. | `DevelopmentalNeuronState` and deterministic neuron updates | `test_stage_one_acceptance_matrix_is_complete_and_zero_authority`, `test_episode_encoding_is_deterministic_and_duplicate_safe` | Implemented and evidenced |
| Distributed episode coalitions formed from co-activation. | `DevelopmentalExperienceEpisode`, `DevelopmentalCoalition`, `encode_developmental_episode` | `test_overlapping_episodes_share_neurons_without_merging_identity_or_outcome` | Implemented and evidenced |
| Distinct episode identities even when coalitions overlap. | Episode IDs, coalition IDs, per-episode outcomes, provenance event IDs | `test_overlapping_episodes_share_neurons_without_merging_identity_or_outcome` | Implemented and evidenced |
| Replaying one episode activates its coalition more than an unrelated coalition. | `replay_developmental_episode`, `DevelopmentalReplayResult` | `test_replay_activates_target_coalition_more_than_unrelated` | Implemented and evidenced |
| Contradictory episode details remain inspectable. | Separate `outcome_code`, `context_code`, `action_code`, and coalition records | `test_contradictory_contexts_create_inhibitory_connections_without_erasing_details` | Implemented and evidenced |
| Recurrent activity settles within the configured compute budget. | `DevelopmentalRecurrentTraceStep`, bounded replay loop | `test_replay_activates_target_coalition_more_than_unrelated` | Implemented and evidenced |
| No coalition recruits the full neuron pool and no structural neuron creation occurs. | `DevelopmentalNetworkState` invariants | `test_substrate_rejects_structural_neuron_creation_and_full_pool_coalitions` | Implemented and evidenced |
| Fixed seed reconstructs the same state. | Canonical deterministic state IDs | `test_fixed_seed_reconstructs_same_state_and_different_seed_changes_it` | Implemented and evidenced |
| SQLite cognition and production action authority remain zero. | State and replay counters plus static import test | `test_stage_one_acceptance_matrix_is_complete_and_zero_authority`, `test_developmental_network_has_no_forbidden_runtime_dependencies` | Implemented and evidenced |
| Public exports expose the Stage 1 substrate contracts. | `src/seedmind/research/ndnra/__init__.py` | `test_public_exports_cover_stage_one_substrate` | Implemented and evidenced |

## 3. Completion Matrix

The integrated `StageOneSubstrateEvidence.completion_matrix()` reports every Stage 1 pass gate as `implemented_and_evidenced`:

| Gate | Status |
| --- | --- |
| experiences_overlap_without_identity_merge | Implemented and evidenced |
| target_replay_exceeds_unrelated_coalition | Implemented and evidenced |
| contradictory_episode_details_remain_inspectable | Implemented and evidenced |
| recurrent_activity_settles_within_budget | Implemented and evidenced |
| no_coalition_uses_entire_pool | Implemented and evidenced |
| fixed_seed_reconstructs_same_state | Implemented and evidenced |
| sqlite_and_authority_counts_zero | Implemented and evidenced |

Deferred: DESA bootstrap learning, broad associative recall, simultaneous needs, regional maturity, local reopening, homeostasis, hibernation, dreams, learned responsibility, typed action proposals, shadow trial behavior, and persistence implementation.

Out of scope: structural neuron creation, SQLite cognition, runtime adapter, action gateway, production action authority, autonomous workers, live Nursery authority, physical robotics, and v0.1 proof-store mutation.

## 4. Validation

Focused implementation checks before this document:

```text
ruff format src/seedmind/research/ndnra/developmental_network.py tests/unit/test_ndnra_developmental_network.py src/seedmind/research/ndnra/__init__.py: applied formatting
ruff check src/seedmind/research/ndnra/developmental_network.py tests/unit/test_ndnra_developmental_network.py src/seedmind/research/ndnra/__init__.py: passed
mypy src/seedmind/research/ndnra/developmental_network.py tests/unit/test_ndnra_developmental_network.py src/seedmind/research/ndnra/__init__.py: passed
pytest -q tests/unit/test_ndnra_developmental_network.py: 9 passed
```

Full repository gates before local batch commit:

```text
ruff format --check .: 243 files already formatted
ruff check .: passed
mypy: no issues in 243 source files
pytest -q: 1017 passed
pip check: no broken requirements
git diff --check: passed
```

## 5. Next Stage

The next bounded batch is Stage 1A: DESA bootstrap and hierarchical metacognition over the proven Stage 1 substrate. It must not begin broad associative recall, simultaneous multiple-need work, mature ambition commitment, dreaming, conscience-guided proposals, internet knowledge acquisition, or action-gateway work.
