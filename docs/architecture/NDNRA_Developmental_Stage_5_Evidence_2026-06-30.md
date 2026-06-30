# NDNRA Developmental Network v0.2 Stage 5 Evidence

Date: 30 June 2026
Scope: Stage 5 homeostasis and runaway-network control
Status: implemented and validated; local commit pending

## 1. Boundary

Stage 5 is an isolated in-memory research batch under `src/seedmind/research/ndnra`.

It implements deterministic homeostasis evidence with bounded recurrent settling traces, sparse coalition checks, regional edge-density budgets, selectivity and stability controls, idle-capacity recruitment before expansion, repeated saturation observations, one bounded non-authoritative structural expansion proposal, duplicate expansion rejection, and exhausted-budget unresolved/help behavior.

It does not implement hibernation, dream maintenance, restart persistence, conscience-guided proposals, runtime integration, action gateways, autonomous workers, SQLite cognition, or production action authority.

## 2. Hypothesis

Homeostatic controls can keep recurrent activity selective and stable without globally shrinking all weights to near zero or proposing structural growth before existing capacity is exhausted. Expansion should require repeated causal saturation evidence, reject duplicates, and preserve unresolved needs with help requests when budget is exhausted.

## 3. Deterministic Scenario

The canonical Stage 5 evidence contains:

- task and resource coalitions with bounded activation traces;
- sparse active neuron sets and edge density within regional budget;
- unrelated-context activation below relevant-context activation;
- controls for proposed homeostasis, inhibition removed, homeostasis removed, and global shrink only;
- idle task-region neurons recruited before any expansion proposal;
- three repeated saturation observations with exact causal evidence;
- one separate anomaly observation that cannot trigger expansion;
- one candidate expansion proposal;
- one duplicate expansion proposal rejected against the candidate;
- one exhausted-budget proposal that preserves the unresolved need and requests help.

## 4. Implementation Evidence

| Requirement | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| Activation settles under repeated recurrent stimulation. | `HomeostaticCoalitionState.activation_trace`, `settled` | `test_activation_settles_and_coalitions_remain_sparse_within_edge_budget` | Implemented and evidenced |
| Relevant coalitions remain sparse. | `HomeostaticCoalitionState.sparsity` | `test_activation_settles_and_coalitions_remain_sparse_within_edge_budget` | Implemented and evidenced |
| Prior strength does not dominate unrelated contexts. | `unrelated_context_activation` | `test_activation_settles_and_coalitions_remain_sparse_within_edge_budget` | Implemented and evidenced |
| Edge density remains within regional budget. | `edge_density`, `regional_edge_density_budget` | `test_activation_settles_and_coalitions_remain_sparse_within_edge_budget`, `test_homeostatic_coalition_rejects_capacity_and_edge_violations` | Implemented and evidenced |
| Removing inhibition or homeostasis worsens selectivity or stability. | `HomeostasisControlResult` controls | `test_homeostasis_controls_show_inhibition_and_homeostasis_are_needed` | Implemented and evidenced |
| Existing idle capacity is recruited before expansion. | `IdleCapacityRecruitmentEvidence` | `test_idle_capacity_is_recruited_before_structural_expansion` | Implemented and evidenced |
| One anomaly cannot trigger expansion. | `single_anomaly_observation` kept out of proposal evidence | `test_one_anomaly_cannot_trigger_expansion_but_repeated_saturation_can` | Implemented and evidenced |
| Persistent saturation creates one bounded expansion proposal. | `SaturationObservation`, `StructuralExpansionProposal` | `test_one_anomaly_cannot_trigger_expansion_but_repeated_saturation_can` | Implemented and evidenced |
| Duplicate expansion is rejected. | `ExpansionProposalStatus.DUPLICATE_REJECTED` | `test_duplicate_expansion_is_rejected_and_budget_exhaustion_preserves_need` | Implemented and evidenced |
| Exhausted budget preserves unresolved need and requests help. | `ExpansionProposalStatus.BUDGET_EXHAUSTED_UNRESOLVED` | `test_duplicate_expansion_is_rejected_and_budget_exhaustion_preserves_need` | Implemented and evidenced |
| Homeostasis does not destroy relative preferences. | Proposed versus global-shrink control | `test_homeostasis_controls_show_inhibition_and_homeostasis_are_needed` | Implemented and evidenced |
| SQLite cognition and production authority remain zero. | Integrated zero counters plus static dependency test | `test_stage_five_acceptance_matrix_is_complete_and_zero_authority`, `test_developmental_homeostasis_has_no_forbidden_runtime_dependencies` | Implemented and evidenced |

## 5. Completion Matrix

The integrated `StageFiveHomeostasisEvidence.completion_matrix()` reports every Stage 5 pass gate as `implemented_and_evidenced`:

| Gate | Status |
| --- | --- |
| activation_settles_under_repeated_recurrent_stimulation | Implemented and evidenced |
| relevant_coalitions_remain_sparse | Implemented and evidenced |
| prior_strength_does_not_dominate_unrelated_contexts | Implemented and evidenced |
| edge_density_within_regional_budget | Implemented and evidenced |
| removing_inhibition_or_homeostasis_worsens_stability | Implemented and evidenced |
| idle_capacity_recruited_before_expansion | Implemented and evidenced |
| one_anomaly_cannot_trigger_expansion | Implemented and evidenced |
| persistent_saturation_creates_one_bounded_expansion_proposal | Implemented and evidenced |
| duplicate_expansion_is_rejected | Implemented and evidenced |
| exhausted_budget_preserves_unresolved_need_and_requests_help | Implemented and evidenced |
| homeostasis_does_not_destroy_relative_preferences | Implemented and evidenced |
| zero_sqlite_side_effects_and_authority | Implemented and evidenced |

Deferred: hibernation, dream maintenance, restart identity, protected dream replay, persistence, schema migration, learned responsibility, conscience-guided proposals, runtime integration, and action gateways.

Out of scope: SQLite cognition, persistence, runtime adapters, action gateways, production action authority, autonomous workers, internet access, pretrained language model integration, task-specific solution injection, physical robotics, proof-store mutation, and v0.1 schema mutation.

## 6. Controls And Falsification

Controls represented in the deterministic evidence:

- proposed homeostasis;
- inhibition removed;
- homeostasis removed;
- global shrink only.

Falsification status: not falsified in this bounded scenario. The evidence rejects unsettled activation, dense coalitions, prior-strength domination of unrelated contexts, edge-budget overflow, expansion before idle capacity is recruited, anomaly-only expansion, duplicate expansion, exhausted-budget erasure, global shrink that destroys relative preferences, SQLite cognition, external side effects, and production action authority.

## 7. Validation

Focused implementation checks before this document:

```text
ruff format src/seedmind/research/ndnra/developmental_homeostasis.py src/seedmind/research/ndnra/__init__.py tests/unit/test_ndnra_developmental_homeostasis.py: passed
ruff check src/seedmind/research/ndnra/developmental_homeostasis.py src/seedmind/research/ndnra/__init__.py tests/unit/test_ndnra_developmental_homeostasis.py: passed
mypy src/seedmind/research/ndnra/developmental_homeostasis.py tests/unit/test_ndnra_developmental_homeostasis.py: passed
pytest -q tests/unit/test_ndnra_developmental_homeostasis.py --basetemp .pytest_tmp/stage5_focused: 12 passed
```

Full repository gates before local batch commit:

```text
ruff format --check .: 253 files already formatted
ruff check .: passed
mypy .: no issues in 253 source files
pytest -q --basetemp .pytest_tmp/full_repo_stage5_final: 1076 passed
pip check: no broken requirements
git diff --check: passed
```

## 8. Next Stage

The next bounded batch after successful final gates is Stage 6: hibernation, dream maintenance, and restart identity. Stage 6 must not begin conscience-guided proposals, internet knowledge acquisition, or action-gateway work.
