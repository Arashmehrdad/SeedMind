# NDNRA Developmental Network v0.2 Stage 3 Evidence

Date: 30 June 2026
Scope: Stage 3 specialised concurrent regions and multiple needs
Status: implemented and validated; local commit pending

## 1. Boundary

Stage 3 is an isolated in-memory research batch under `src/seedmind/research/ndnra`.

It implements deterministic software-only regional concurrency evidence with region-local neuron pools, region-local plasticity controls, simultaneous need pulses, typed cross-region messages, local internal proposal formation, compatibility support, conflict inhibition, protected safety and permission participation, dormant need re-emergence, and explicit uniform-network interference controls.

It does not implement mature ambition commitment, mature skill promotion, mature verifier reopening, homeostasis, hibernation, dream maintenance, conscience-guided proposals, persistence, runtime integration, action gateways, autonomous workers, SQLite cognition, or production action authority.

## 2. Hypothesis

Specialised concurrent regions can preserve several compatible needs at the same time, cooperate through typed messages, inhibit incompatible proposals through protected safety and permission needs, and reduce cross-task interference versus a uniform-network control without collapsing all needs into one permanent global scalar.

## 3. Deterministic Scenarios

The canonical Stage 3 evidence contains three bounded scenarios:

- `scenario:task_resource_clarity`: task completion, resource conservation, and clarity needs remain represented together and form compatible internal proposals.
- `scenario:repair_permission_preservation`: repair, user-data preservation, and permission needs demonstrate protected inhibition of a destructive internal proposal while preserving a read-only diagnostic proposal.
- `scenario:stop_then_curiosity_reemerges`: a protected stop need pauses curiosity, and curiosity re-emerges after the stop condition is resolved.

All scenarios use the same deterministic region set:

- `region:task`;
- `region:resource`;
- `region:safety_permission`;
- `region:clarity`;
- `region:preservation`;
- `region:curiosity`.

## 4. Implementation Evidence

| Requirement | Implementation evidence | Test evidence | Status |
| --- | --- | --- | --- |
| Region-local neuron pools and plasticity controls. | `DevelopmentalRegionState`, `build_stage_three_region_states` | `test_region_local_pools_are_distinct_and_safety_region_is_protected` | Implemented and evidenced |
| Multiple simultaneous need pulses. | `ConcurrentNeedPulse`, `ConcurrentNeedActivationResult.represented_need_codes` | `test_compatible_needs_remain_simultaneous_and_cooperate_without_erasure` | Implemented and evidenced |
| Compatible regional coalitions cooperate. | `CrossRegionMessageKind.COMPATIBILITY_SUPPORT`, supported internal proposals | `test_compatible_needs_remain_simultaneous_and_cooperate_without_erasure` | Implemented and evidenced |
| Protected safety or permission need inhibits incompatible task proposal. | `PERMISSION_CONSTRAINT`, `CONFLICT_INHIBITION`, protected requirement codes | `test_protected_need_inhibits_incompatible_task_without_action_authority` | Implemented and evidenced |
| Dormant need re-emerges after blocking need resolves. | `dormant_need_codes`, `reemerged_need_codes`, stop-signal scenario | `test_dormant_need_reemerges_after_blocking_need_resolves` | Implemented and evidenced |
| Region-local learning beats uniform-network control. | `region_local_interference < uniform_network_interference` in all scenarios | `test_stage_three_rejects_global_scalar_and_worse_region_local_control` | Implemented and evidenced |
| Cross-region messages remain typed and inspectable. | `CrossRegionMessage`, `CrossRegionMessageKind`, deterministic message IDs | `test_cross_region_messages_are_typed_inspectable_and_validated` | Implemented and evidenced |
| No permanent global scalar collapse. | `permanent_global_scalar_used=False`, rejecting mutated scalar use | `test_stage_three_rejects_global_scalar_and_worse_region_local_control` | Implemented and evidenced |
| Internal proposals remain non-authoritative. | `RegionalProposal.typed_internal_only`, zero authority counters | `test_proposals_and_need_pulses_reject_authority_and_ambiguous_conflicts`, `test_stage_three_acceptance_matrix_is_complete_and_zero_authority` | Implemented and evidenced |
| Deterministic evidence identity and public exports. | `StageThreeRegionalConcurrencyEvidence.evidence_id`, `__init__.py` exports | `test_stage_three_acceptance_is_deterministic_and_config_bounded`, `test_public_exports_cover_stage_three_regional_concurrency` | Implemented and evidenced |
| SQLite cognition and production authority remain zero. | Integrated zero counters plus static dependency test | `test_stage_three_acceptance_matrix_is_complete_and_zero_authority`, `test_developmental_regions_has_no_forbidden_runtime_dependencies` | Implemented and evidenced |

## 5. Completion Matrix

The integrated `StageThreeRegionalConcurrencyEvidence.completion_matrix()` reports every Stage 3 pass gate as `implemented_and_evidenced`:

| Gate | Status |
| --- | --- |
| independent_compatible_needs_remain_simultaneous | Implemented and evidenced |
| compatible_regions_cooperate_without_erasure | Implemented and evidenced |
| protected_need_inhibits_incompatible_task | Implemented and evidenced |
| dormant_need_reemerges_after_blocking_need_resolves | Implemented and evidenced |
| region_local_learning_reduces_interference | Implemented and evidenced |
| cross_region_messages_are_typed_and_inspectable | Implemented and evidenced |
| no_region_gains_external_action_authority | Implemented and evidenced |
| no_permanent_global_scalar_collapse | Implemented and evidenced |

Deferred: regional maturity state, maturity-dependent plasticity, mature skill promotion, persistent desired-state ambition, developmental Outcome Fidelity maturity, verifier reopening, homeostasis, hibernation, dreams, restart identity, learned responsibility, typed external action proposals, and shadow trial behavior.

Out of scope: SQLite cognition, persistence, runtime adapters, action gateways, production action authority, autonomous workers, internet access, pretrained language model integration, task-specific solution injection, physical robotics, proof-store mutation, and v0.1 schema mutation.

## 6. Controls And Falsification

Controls represented in the deterministic evidence:

- uniform-network interference control for every scenario;
- explicit rejection of permanent global scalar collapse;
- protected permission and preservation inhibition control against a direct destructive proposal;
- dormant curiosity re-emergence after stop resolution.

Falsification status: not falsified in this bounded scenario. The evidence rejects one global winner erasing other needs, missing typed cross-region messages, unsafe direct destructive proposal activation, hidden external action authority, SQLite cognition, external side effects, and region-local interference that fails to beat the uniform-network control.

## 7. Validation

Focused implementation checks before this document:

```text
ruff format src/seedmind/research/ndnra/developmental_regions.py src/seedmind/research/ndnra/__init__.py tests/unit/test_ndnra_developmental_regions.py: passed
ruff check src/seedmind/research/ndnra/developmental_regions.py src/seedmind/research/ndnra/__init__.py tests/unit/test_ndnra_developmental_regions.py: passed
mypy src/seedmind/research/ndnra/developmental_regions.py tests/unit/test_ndnra_developmental_regions.py: passed
pytest -q tests/unit/test_ndnra_developmental_regions.py --basetemp .pytest_tmp/stage3_focused: 12 passed
```

Full repository gates before local batch commit:

```text
ruff format --check .: 249 files already formatted
ruff check .: passed
mypy .: no issues in 249 source files
pytest -q --basetemp .pytest_tmp/full_repo_stage3_final: 1052 passed
pip check: no broken requirements
git diff --check: passed
```

## 8. Next Stage

The next bounded batch after successful final gates is Stage 4: regional child-to-adult development, skill maturation, and ambition persistence. Stage 4 must not begin homeostasis, hibernation, dream maintenance, conscience-guided proposals, or action-gateway work.
