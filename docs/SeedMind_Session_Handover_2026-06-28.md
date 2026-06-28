# SeedMind Session Handover — 28 June 2026

Repository: `D:\Github\SeedMind`  
CodexBridge repository alias: `seedmind`  
Branch: `main`  
Working tree at handover: clean  
Git relationship at handover: `main...origin/main [ahead 1]` before this handover document is committed  
Current implementation commit: `8f83f0d0edcbd2135e68798b70db40bae4482dbc`  
Current stage: Human-Approved Consolidation Execution  
Stage progress: 3 of 5 batches complete  
Current NDNRA heuristic theory-to-integration readiness: 96%  
Target after complete stage acceptance: 97%

---

## 1. Continuation instruction for the next session

Use this handover as the source of truth, then inspect the repository before editing.

Recommended opening instruction:

> Continue SeedMind from `docs/SeedMind_Session_Handover_2026-06-28.md`. Attach CodexBridge to repository alias `seedmind`, inspect repository status, and begin Human-Approved Consolidation Execution Batch 4. Do not push. Preserve every authority and cognition boundary documented in the handover.

The immediate next task is:

> Implement Batch 4: restart-safe permit and execution persistence, interruption safety, duplicate/replayed-permit protection after restart, stale-between-approval-and-commit acceptance, corruption fallback, and live acceptance. Keep readiness at 96% until Batch 5 formally closes the stage.

---

## 2. Repository workflow rules

- Use CodexBridge repository alias `seedmind` for repository work.
- Local repository path is `D:\Github\SeedMind`.
- Never push automatically.
- Commit only files belonging to the current bounded batch.
- The user manually runs `git push`.
- Before implementation, inspect repository status and relevant files.
- After implementation, run the complete repository quality gates.
- Report exact commit hashes, tests, and branch-ahead count.
- Preserve repository-scoped project knowledge; do not mix SeedMind decisions with other repositories.
- Production curiosity remains the sole production action authority.

Manual push command:

```powershell
Set-Location "D:\Github\SeedMind"
git push
```

At the start of this handover, the code branch was ahead by one unpushed implementation commit:

```text
8f83f0d feat: commit human-approved NDNRA consolidation atomically
```

Committing this handover document will increase the ahead count by one unless the implementation commit is pushed first.

---

## 3. SeedMind product and research boundary

SeedMind is a developmental intelligence runtime. It is not intended to become:

- A chatbot wrapper.
- An LLM memory layer.
- A database-driven cognition system.
- An unrestricted autonomous agent.
- An NDNRA-only research repository.

The main MVP story remains:

1. SeedMind starts without task-specific knowledge.
2. It discovers primitive controls.
3. It observes a useful human or teacher capability.
4. It forms persistent ambition.
5. It creates milestones and experiments.
6. It learns a reusable object-pushing capability.
7. It completes a human request using the learned capability.
8. A second object exposes a limitation.
9. SeedMind follows a diagnostic ladder.
10. It creates a small specialist module.
11. It improves the new task without losing the old task.
12. Human dependence falls as competence rises.
13. It explains why each skill and module exists through an audit trail.

NDNRA exists to support this main SeedMind story. It must not displace it.

---

## 4. Core NDNRA architecture

The Need-Driven Neural Recruitment Architecture currently follows these principles:

- An unresolved need emits recruitment pressure.
- Locally relevant neurons, synapses, assemblies, routes, and experiences become easier to activate.
- Recently active structures leave temporary eligibility traces.
- Important outcomes broadcast modulatory signals.
- Only eligible structures change strongly.
- A need persists until resolved.
- Old or unused structures become dormant rather than permanently pruned.
- Repeated important unresolved needs can create structural growth pressure.
- Predictions evaluate expected need reduction, effort, risk, availability, and confidence.
- Curiosity and ambition create novelty and developmental pressure.
- Human demonstration, correction, and approval are explicit modulatory evidence.

The NDNRA path is research-only unless a separately validated gate explicitly grants a bounded capability.

---

## 5. Terminology decision: pulse and spark

A terminology discussion occurred near the end of the previous stage.

Decision:

- Keep **Need Pulse** for the recurring or persistent signal emitted while a need remains unresolved.
- Reserve **Recruitment Spark** for the threshold event where locally relevant structures ignite into coordinated activity.
- Reserve **Intelligence Spark** for the first independently reconstructed and usefully applied capability.

Conceptual narrative:

> A need creates the pulse. The pulse creates the spark. The spark becomes intelligence.

This terminology has not yet been implemented as a code or documentation rename. Do not globally replace `NeedPulse` with `Spark`. Any implementation should preserve the distinction between an ongoing pulse and a threshold-crossing spark.

---

## 6. Non-negotiable cognition and authority boundaries

These constraints apply to all future work:

### Action authority

- Production curiosity remains the sole production action authority.
- NDNRA cannot select production actions.
- Consolidation cannot silently affect action choice.
- Execution receipts must explicitly report no production-action authority.

### Persistence

- Persistence stores and reconstructs validated evidence.
- Persistence is not cognition.
- Persistence cannot rank routes, choose memories, select actions, schedule review, or discharge needs.
- SQLite remains audit and storage infrastructure only.
- SQLite must not become eligibility computation, replay selection, consolidation selection, lifecycle control, or action authority.

### Proposal lifecycle

- Accepted means approved for possible future consideration only.
- Proposal status and permit status are separate.
- A stale proposal is not silently deleted, rejected, expired, replaced, or executed.
- Exact identities and immutable history must be preserved.

### Consolidation execution

- Execution requires explicit human approval.
- Approval alone is insufficient; immediate revalidation is mandatory.
- A permit authorizes one possible bounded application.
- The permit object itself is immutable issuance evidence and remains `consumed = false`.
- Permit lifecycle state is authoritative for issued, cancelled, expired, and consumed status.
- A consumed permit cannot be used twice.
- No automatic execution, timer, background worker, or persistent autonomous queue is permitted.
- No automatic replay is permitted in the current stage.
- No advice, growth, route-ranking, or production-action influence is permitted in the current stage.
- Failure must preserve or restore exact prior state.

### Evidence

- Preserve source-event identities.
- Preserve contradictions rather than overwriting them.
- Preserve routes and assemblies.
- Correlated copies must not count as independent evidence.
- Severe one-shot evidence may protect state but must not create broad mastery by itself.
- Evidence dimensions remain separate.

---

## 7. Readiness roadmap

The current engineering indicator is deliberately narrow:

```text
94% — knows when consolidation may be useful
95% — proposal lifecycle is validated
96% — proposal memory survives restart safely
97% — human-approved consolidation execution is validated
98% — controlled replay and restoration
99% — cross-system shadow integration
100% — end-to-end research acceptance
```

Meaning of 100%:

- The theory-to-integration research roadmap is complete.
- It does not mean AGI.
- It does not mean commercial production readiness.
- It does not mean unrestricted autonomy.
- It does not mean all safety concerns are solved.

The current indicator remains 96% because the execution stage is not complete.

---

## 8. Previously completed stages

### 8.1 Consolidation scheduling stage

Status: complete.  
Purpose: determine when consolidation may be useful without applying it.

Key boundary:

- Proposal-only.
- No timers.
- No background workers.
- No executors.
- No automatic application.
- No persistent execution queue.

Handover:

- `docs/SeedMind_Consolidation_Scheduling_Stage_Handover_2026-06-27.md`

### 8.2 Proposal lifecycle stage

Status: complete.  
Readiness increase: 94% to 95%.

Capabilities:

- Accept, reject, and defer review.
- Immutable review history.
- Explicit expiry and replacement.
- Stale controller and UI identity rejection.
- Bounded active capacity.
- Synthetic lifecycle comparison.
- Live-shadow behavioural invariance.

Important commits:

```text
00ac54c feat: add NDNRA proposal review lifecycle
ab5167e feat: add NDNRA proposal lifecycle history
2d5f3c8 feat: manage NDNRA proposal lifecycles
```

Handover:

- `docs/SeedMind_Proposal_Lifecycle_Stage_Handover_2026-06-27.md`

### 8.3 Restart-safe proposal memory stage

Status: complete.  
Readiness increase: 95% to 96%.

Capabilities:

- Exact proposal-lifecycle checkpoint codec.
- Brain schema 4.
- Exact graph, growth, consolidation, and proposal-lifecycle restoration.
- Migration from brain schemas 1, 2, and 3.
- Complete fallback on checksum corruption.
- Complete fallback on relational lifecycle corruption.
- Restart-time current, stale, superseded, and invalid-for-review classifications.
- Live-shadow invariance.

Implementation commits:

```text
555efe7 — exact lifecycle checkpoint codec
2b0fb0a — schema-4 brain persistence and migrations
b1ec4a3 — restart-time proposal revalidation
7280954 — complete restart and live-shadow acceptance
7d6b46b — documentation and closure
```

Handover:

- `docs/SeedMind_Restart_Safe_Proposal_Memory_Stage_Handover_2026-06-28.md`

Brain schema at this point:

```text
BRAIN_SCHEMA_VERSION = 4
```

Schema 4 stores:

- Learned graph.
- Growth state.
- Consolidation checkpoint.
- Proposal lifecycle checkpoint.

Execution permits and execution receipts are not yet persisted.

---

## 9. Current stage: Human-Approved Consolidation Execution

Stage plan:

- `docs/SeedMind_Human_Approved_Consolidation_Execution_Stage_Plan_2026-06-28.md`

Status:

```text
Batch 1 complete
Batch 2 complete
Batch 3 complete
Batch 4 next
Batch 5 pending
```

Target after complete stage acceptance:

```text
NDNRA heuristic readiness = 97%
```

Do not increase readiness during Batch 4. Reassess only during Batch 5 closure.

---

## 10. Batch 1 — explicit human approval and execution permits

Commit:

```text
f163793 feat: add human-approved consolidation permits
```

Main implementation:

- `src/seedmind/research/ndnra/consolidation_execution_approval.py`

Tests:

- `tests/unit/test_ndnra_consolidation_execution_approval.py`

Public API:

- `ConsolidationExecutionApprovalRequest`
- `ConsolidationExecutionApprovalPolicy`
- `ConsolidationExecutionPermit`

Approval requirements:

- One active proposal lifecycle record.
- Proposal lifecycle status must be accepted.
- Latest review decision must be acceptance.
- Exact proposal ID.
- Exact candidate ID.
- Exact accepted review-decision ID.
- Approval episode must follow review episode.
- Explicit human approver identity using the `human:` prefix.
- Explicit reason.
- Bounded validity window.
- Immediate revalidation must return `current`.

Default approval window policy:

```text
maximum_validity_episodes = 1
```

A new permit contains:

```text
authorizes_one_application = true
single_use = true
consumed = false
application_count = 0
has_direct_execution_authority = false
```

Permit identity is deterministic and includes:

- Complete proposal snapshot.
- Accepted review decision ID.
- Immediate revalidation snapshot.
- Issue and expiry episodes.
- Approver identity.
- Reason.

Blocked approval cases include:

- Pending proposal.
- Deferred proposal.
- Rejected proposal.
- Closed proposal.
- Stale proposal.
- Superseded proposal.
- Invalid-for-review evidence.
- Missing assemblies or routes.
- Mismatched proposal, candidate, or review identity.
- Non-human approver.
- Overlong validity.
- Approval at or before the accepted review episode.

Batch 1 does not consume permits or apply consolidation.

---

## 11. Batch 2 — immutable permit lifecycle

Commit:

```text
663a4df feat: add NDNRA execution permit lifecycle
```

Main implementation:

- `src/seedmind/research/ndnra/consolidation_execution_permit_lifecycle.py`

Tests:

- `tests/unit/test_ndnra_consolidation_execution_permit_lifecycle.py`

Public API:

- `ConsolidationExecutionPermitLifecycleAction`
- `ConsolidationExecutionPermitLifecycleStatus`
- `ConsolidationExecutionPermitTransitionRequest`
- `ConsolidationExecutionPermitTransitionDecision`
- `ConsolidationExecutionPermitLifecycleRecord`
- `ConsolidationExecutionPermitLifecycleRegistry`

Lifecycle:

```text
ISSUED
  -> CANCELLED
  -> EXPIRED
  -> CONSUMED
```

Rules:

- Exactly one terminal transition is permitted.
- Cancellation and consumption must occur after issuance.
- Cancellation and consumption require an unexpired permit.
- Expiry may be recorded only after the validity window.
- Consumption requires an explicit consumption reference.
- Terminal records reject all later transitions.
- Decision identities are deterministic.
- Tampered decision identities are rejected.
- Registry permit identities are unique.
- Duplicate consumption through a second lifecycle record is blocked.
- Proposal lifecycle history remains unchanged.

Critical distinction:

```text
permit.consumed = false
```

The permit object remains immutable issuance evidence. The lifecycle record is authoritative for whether the permit was consumed.

Batch 2 does not apply consolidation.

---

## 12. Batch 3 — atomic human-approved consolidation commit

Commit:

```text
8f83f0d0edcbd2135e68798b70db40bae4482dbc
feat: commit human-approved NDNRA consolidation atomically
```

Main implementation:

- `src/seedmind/research/ndnra/consolidation_execution_commit.py`

Tests:

- `tests/unit/test_ndnra_consolidation_execution_commit.py`

Public API:

- `ConsolidationApplicationTarget`
- `ConsolidationExecutionCommitRequest`
- `ConsolidationExecutionCommitReceipt`
- `ConsolidationExecutionCommitResult`
- `ConsolidationExecutionCommitPolicy`

### 12.1 Commit request

A commit request contains:

- Exact permit ID.
- Exact proposal ID.
- Exact candidate ID.
- Execution episode.
- Executor identity.
- Reason.

Executor identity must use the `execution:` prefix.

### 12.2 Preconditions

The commit gate requires:

- Permit lifecycle record exists.
- Permit status is `ISSUED`.
- Issued record contains no terminal decisions.
- Request identities match the permit exactly.
- Execution follows permit issuance.
- Permit is inside its validity window.
- Proposal lifecycle record is active.
- Proposal lifecycle status is accepted.
- Permit proposal equals active lifecycle proposal.
- Latest proposal review remains accepted.
- Permit references that exact accepted review decision.

### 12.3 Immediate pre-commit revalidation

Immediately before application, the gate revalidates using the current:

- Contextual ledger.
- Assembly identities.
- Route identities.
- Proposal lifecycle record.

Required result:

```text
ConsolidationProposalRevalidationStatus.CURRENT
```

The exact candidate is then reconstructed through the same eligibility policy used by revalidation.

If the candidate differs from the permitted candidate, execution is blocked.

### 12.4 Atomic transaction sequence

The in-memory transaction is:

1. Capture contextual ledger snapshot.
2. Capture proposal lifecycle snapshot.
3. Capture original permit registry snapshot.
4. Capture complete consolidation state snapshot.
5. Perform immediate revalidation.
6. Reconstruct exact current eligibility.
7. Compute deterministic execution ID.
8. Construct the consumed permit registry locally and immutably.
9. Apply the consolidation candidate.
10. Verify application `before` equals the captured state.
11. Verify application `after` equals the actual committed state.
12. Verify exact candidate identity.
13. Verify ledger unchanged.
14. Verify proposal lifecycle unchanged.
15. Verify original permit registry unchanged.
16. Construct receipt.
17. Return receipt and consumed registry together.

The consumed registry is not returned if application fails.

### 12.5 Execution identity

The execution ID is deterministic and hashes:

- Complete permit snapshot.
- Immediate revalidation snapshot.
- Complete pre-commit consolidation state.
- Execution episode.
- Executor identity.
- Reason.

Format:

```text
consolidation-execution:<sha256>
```

The permit consumption reference must equal the execution ID.

### 12.6 Successful receipt

A successful receipt includes:

- Exact permit.
- Immediate revalidation.
- Exact application before and after snapshots.
- Matching consumed permit transition.
- Execution episode.
- Executor identity.
- Reason.

Successful receipt invariants:

```text
application_count = 1
replay_trigger_count = 0
restoration_trigger_count = 0
has_production_action_authority = false
```

### 12.7 Failure restoration

`ConsolidationApplicationTarget` is a protocol requiring:

- `snapshot()`
- `apply(eligibility)`
- `restore_snapshot(expected_current, replacement)`

If an exception occurs after application begins:

- The current state is compared with the pre-commit snapshot.
- If changed, exact restoration is attempted.
- The restored state must equal the pre-commit state.
- If restoration itself cannot reproduce the prior state, a chained `RuntimeError` is raised.
- The original permit registry remains issued because only the local immutable consumed-registry result was created.

An injected test applies the candidate, raises immediately afterward, and proves exact restoration.

### 12.8 Blocked paths

The commit gate blocks before mutation when:

- Permit is cancelled.
- Permit is expired.
- Permit is already consumed.
- Permit is outside the validity window.
- Proposal ID mismatches.
- Candidate ID mismatches.
- Accepted review identity mismatches.
- Proposal lifecycle is inactive.
- Proposal is no longer accepted.
- New evidence makes the proposal stale.
- Current eligibility differs from the permitted candidate.
- Application state lacks a candidate assembly or route.
- Executor identity is not the bounded execution gate.

### 12.9 Batch 3 architectural caveat

Batch 3 is atomic within the current process and call boundary, but it is not yet restart-safe.

The caller must adopt both returned objects together:

- The mutated consolidation application state.
- The returned consumed permit registry and receipt.

A process crash between in-memory application and durable persistence could otherwise produce split state.

Closing that crash window is the primary purpose of Batch 4.

---

## 13. Current code and persistence relationships

### Existing consolidation state

Implementation:

- `src/seedmind/research/ndnra/consolidation_application.py`

Key types:

- `ConsolidationStructureState`
- `ConsolidationStateSnapshot`
- `ConsolidationApplicationResult`
- `ConsolidationApplicationState`

The state stores:

- Assembly stability and plasticity.
- Route stability and plasticity.
- Applied candidate IDs.

Application is bounded and exactly-once by candidate ID.

### Existing consolidation checkpoint

Implementation:

- `src/seedmind/research/ndnra/consolidation_persistence.py`

Key type:

- `NDNRAConsolidationCheckpoint`

It currently stores:

- Consolidation state snapshot.
- Active consolidation applications.
- Rollback audit records.

### Existing proposal lifecycle checkpoint

Implementation:

- `src/seedmind/research/ndnra/consolidation_proposal_persistence.py`

Key type:

- `NDNRAProposalLifecycleCheckpoint`

### Existing brain persistence

Implementation:

- `src/seedmind/research/ndnra/persistence.py`

Current schema version:

```text
4
```

Schema 4 combines:

- Learned graph.
- Growth state.
- Consolidation checkpoint.
- Proposal lifecycle checkpoint.

It does not yet combine:

- Execution permit lifecycle registry.
- Execution receipts.
- Execution interruption state.

---

## 14. Batch 4 objective

Batch 4 must prove that human-approved execution remains correct across persistence, restart, interruption, stale evidence, corruption, and live use.

Stage-plan requirements:

- Approval and permit state survive restart exactly.
- Interrupted pre-commit execution performs no application.
- Failed application restores exact prior state.
- Duplicate or replayed permits cannot apply twice.
- Stale evidence between approval and commit blocks application.
- Live-shadow execution preserves production action authority and unrelated learning.
- No SQLite cognition or autonomous execution occurs.

Batch 3 already proves several of these in memory. Batch 4 must prove their restart-safe and integrated forms.

---

## 15. Recommended Batch 4 design

The next session must inspect the repository before finalising this design, but the following structure is recommended.

### 15.1 New execution checkpoint codec

Likely new module:

- `src/seedmind/research/ndnra/consolidation_execution_persistence.py`

Possible public types:

- `EXECUTION_SCHEMA`
- `EXECUTION_SCHEMA_VERSION`
- `NDNRAExecutionCheckpoint`

The checkpoint should preserve:

- Complete permit lifecycle registry.
- Successful execution receipts.
- Exact relationship between consumed permit transition and execution receipt.
- Exact relationship between execution receipt and active consolidation application.
- Deterministic ordering.
- No authority-bearing state.

Recommended validation rules:

1. Every permit identity is unique.
2. Every transition identity reconstructs exactly.
3. Every consumed permit has exactly one matching execution receipt.
4. Every receipt references the exact consumed transition.
5. Consumption reference equals execution ID.
6. Receipt candidate equals permit candidate.
7. Receipt application candidate equals permit candidate.
8. Receipt application `after` is consistent with the persisted consolidation state.
9. Applied candidate IDs match active application history.
10. Cancelled and expired permits have no execution receipt.
11. Issued permits have no execution receipt.
12. Duplicate execution IDs are forbidden.
13. Duplicate candidate application through another permit is forbidden.
14. No permit, lifecycle record, checkpoint, or receipt has production-action authority.
15. No receipt reports replay during this stage.

### 15.2 Brain schema migration

A likely clean boundary is brain schema 5, but the next session must inspect all current schema tests and migration patterns before changing it.

Possible schema 5 contents:

- Learned graph.
- Growth state.
- Consolidation checkpoint.
- Proposal lifecycle checkpoint.
- Execution checkpoint.

Migration should be explicit:

```text
Schema 1 -> supported graph + empty consolidation + empty proposal lifecycle + empty execution
Schema 2 -> contextual graph + empty consolidation + empty proposal lifecycle + empty execution
Schema 3 -> graph/growth/consolidation + empty proposal lifecycle + empty execution
Schema 4 -> graph/growth/consolidation/proposal lifecycle + empty execution
Schema 5 -> restore and validate all subsystems
```

Do not infer permit or receipt state from consolidation history during migration.

### 15.3 Atomic persistence boundary

Batch 4 must close the split-state risk between:

- Mutated consolidation state.
- Consumed permit lifecycle.
- Execution receipt.

The durable write should persist them in one checksum-protected brain envelope.

The safe durable outcome is either:

```text
old state + issued permit + no receipt
```

or:

```text
new consolidation state + consumed permit + matching receipt
```

The following durable combinations must be rejected or prevented:

```text
new state + issued permit
old state + consumed permit
consumed permit + missing receipt
receipt + issued permit
receipt + missing applied candidate
applied candidate + missing receipt
```

Use the existing atomic brain-store pattern:

- Deterministic ASCII-safe encoding.
- Temporary file.
- Flush.
- File sync.
- Atomic replace.
- Outer checksum.
- Complete fallback on corruption.

### 15.4 Interruption tests

Required interruption points should include:

1. Before immediate revalidation.
2. After revalidation but before application.
3. After local consumed-registry preparation but before application.
4. During application before state publication.
5. After state application but before durable save.
6. During temporary-file write.
7. After temporary-file write but before atomic replace.
8. After atomic replace before process continuation.

Expected restart outcomes must always be one complete state, never a hybrid.

Where direct process interruption is impractical, use controlled fault injection around the storage boundary.

### 15.5 Duplicate and replayed permit protection

After successful save and restart:

- The permit must load as consumed.
- The receipt must load exactly.
- The consolidation candidate must be applied exactly once.
- A replayed commit request using the same permit must fail before mutation.
- Recreating an identical permit object must not bypass lifecycle identity.
- A second permit for an already applied candidate must not create a second application without a separately designed and approved policy.

### 15.6 Stale-between-approval-and-commit acceptance

Batch 3 already blocks this in memory.

Batch 4 should prove it across restart:

1. Persist accepted proposal and issued permit.
2. Restart.
3. Add independent evidence that changes candidate identity.
4. Attempt execution.
5. Immediate revalidation returns `stale`.
6. Application state remains unchanged.
7. Permit remains issued unless an explicit caller separately cancels or expires it.
8. Proposal lifecycle and review history remain unchanged.

### 15.7 Corruption tests

At minimum test:

- Outer checksum corruption.
- Permit decision identity corruption with recomputed valid outer checksum.
- Execution receipt identity corruption.
- Consumption-reference mismatch.
- Consumed permit without receipt.
- Receipt without consumed permit.
- Receipt candidate mismatch.
- Consolidation state missing the receipt candidate.
- Duplicate execution IDs.
- Duplicate permit IDs.

Corrupt combined state should produce complete safe fallback according to the brain-store policy. Do not partially restore graph, consolidation, proposal, permit, or execution state from an invalid envelope.

### 15.8 Live acceptance

Recommended integration module:

- `src/seedmind/integration/human_approved_consolidation_execution_acceptance.py`

Recommended test:

- `tests/unit/test_ndnra_human_approved_consolidation_execution_acceptance.py`

Compare a controlled SeedMind session with and without one explicit human-approved consolidation event.

The approved session may differ only in the bounded consolidation subsystem and its audit evidence.

The following should remain exactly equal:

- Production actions.
- Prediction errors.
- Ordinary NDNRA suggestion sequence, unless the test explicitly observes the research-only consolidation state separately.
- Developmental signals.
- Learned graph state unrelated to the bounded consolidation checkpoint.
- Growth state.
- Advice output.
- Route ranking.
- Human-dependence accounting.

The accepted execution path should show:

```text
1 explicit human approval
1 current pre-commit revalidation
1 bounded consolidation application
1 consumed permit
1 execution receipt
0 automatic executions
0 replay triggers
0 production-action authority violations
0 SQLite cognitive operations
```

A control with no explicit approval must show zero applications.

### 15.9 Evidence exports

Use deterministic ASCII-safe exports, likely:

- Summary JSON.
- Execution and permit decision JSON.
- Timeline CSV.
- Corruption and interruption case JSON.

Do not make exports authoritative. They are inspection evidence only.

---

## 16. Batch 4 files likely to inspect first

Read these before editing:

```text
src/seedmind/research/ndnra/persistence.py
src/seedmind/research/ndnra/consolidation_persistence.py
src/seedmind/research/ndnra/consolidation_proposal_persistence.py
src/seedmind/research/ndnra/consolidation_execution_approval.py
src/seedmind/research/ndnra/consolidation_execution_permit_lifecycle.py
src/seedmind/research/ndnra/consolidation_execution_commit.py
src/seedmind/research/ndnra/consolidation_application.py
src/seedmind/research/ndnra/consolidation_proposal_revalidation.py
src/seedmind/integration/restart_safe_proposal_memory_acceptance.py
src/seedmind/research/ndnra/__init__.py
```

Relevant tests:

```text
tests/unit/test_ndnra_proposal_lifecycle_brain_persistence.py
tests/unit/test_ndnra_consolidation_proposal_persistence.py
tests/unit/test_ndnra_restart_safe_proposal_memory_acceptance.py
tests/unit/test_ndnra_consolidation_execution_approval.py
tests/unit/test_ndnra_consolidation_execution_permit_lifecycle.py
tests/unit/test_ndnra_consolidation_execution_commit.py
```

Relevant documents:

```text
docs/SeedMind_Human_Approved_Consolidation_Execution_Stage_Plan_2026-06-28.md
docs/SeedMind_Restart_Safe_Proposal_Memory_Stage_Handover_2026-06-28.md
docs/SeedMind_Master_Implementation_Plan_v0.1.md
docs/architecture/Need_Driven_Neural_Recruitment_Architecture_v0.1.md
```

---

## 17. Batch 4 acceptance checklist

Do not mark Batch 4 complete unless all relevant items pass.

### Persistence

- [ ] Execution checkpoint round-trips exactly.
- [ ] Permit lifecycle registry round-trips exactly.
- [ ] Execution receipts round-trip exactly.
- [ ] Consumed transition and receipt relationships are exact.
- [ ] Consolidation application and receipt relationships are exact.
- [ ] Brain schema migration is explicit.
- [ ] Atomic save leaves no temporary file.
- [ ] Outer checksum verifies.

### Interruption and corruption

- [ ] Pre-commit interruption performs no application.
- [ ] Post-application failure restores exact prior state.
- [ ] Durable save never creates split state.
- [ ] Checksum corruption causes complete fallback.
- [ ] Relational execution corruption causes complete fallback.
- [ ] No partial subsystem restoration occurs.

### Permit safety

- [ ] Cancelled permit cannot execute after restart.
- [ ] Expired permit cannot execute after restart.
- [ ] Consumed permit cannot execute after restart.
- [ ] Replayed identical permit cannot execute twice.
- [ ] Duplicate execution ID is rejected.
- [ ] Stale proposal after restart cannot execute.

### Live acceptance

- [ ] No approval means no application.
- [ ] One explicit approval creates one application.
- [ ] Production actions remain under curiosity authority.
- [ ] Prediction errors remain invariant outside the bounded subsystem.
- [ ] Developmental signals remain invariant.
- [ ] Graph learning remains invariant outside persisted consolidation evidence.
- [ ] Growth remains invariant.
- [ ] Advice and route ranking remain unaffected.
- [ ] Replay count remains zero.
- [ ] SQLite cognition count remains zero.
- [ ] Automatic execution count remains zero.

### Quality

- [ ] Ruff format passes.
- [ ] Ruff lint passes.
- [ ] Mypy passes.
- [ ] Full Pytest suite passes.
- [ ] Pip check passes.
- [ ] Git diff check passes.
- [ ] Working tree is clean after commit.
- [ ] One bounded Batch 4 commit is created.
- [ ] Nothing is pushed automatically.

---

## 18. Batch 5 after Batch 4

Batch 5 will:

- Update README.
- Update the master implementation plan.
- Update NDNRA architecture.
- Close the execution stage plan.
- Produce a detailed human-approved execution stage handover.
- Refresh the repository wiki.
- Run all quality gates.
- Formally reassess readiness from 96% to 97%.

Do not start replay or restoration work during Batch 5. Those belong to the separate 98% stage.

---

## 19. Latest validation state

After Batch 3 implementation:

```text
Pytest: 563 passed
Ruff format: 172 files already formatted
Ruff lint: all checks passed
Mypy: no issues in 172 source files
Pip check: no broken requirements
Git diff check: passed
Working tree: clean
```

The Batch 3 validation includes:

- Successful one-time application.
- Exact consumed permit transition.
- Deterministic execution identity.
- Bounded structure changes.
- Untouched unrelated structures.
- Cancelled permit rejection.
- Expired permit rejection.
- Consumed permit duplicate rejection.
- Stale evidence rejection.
- Missing application structure rejection.
- Mismatched identity rejection.
- Bounded executor identity requirement.
- Injected post-application failure.
- Exact restoration after injected failure.
- Tampered execution identity rejection.
- Tampered transition identity rejection.
- Static exclusion of replay, growth, advice, SQLite, and production-action paths.

---

## 20. Recent commit sequence

Most relevant recent commits:

```text
8f83f0d feat: commit human-approved NDNRA consolidation atomically
663a4df feat: add NDNRA execution permit lifecycle
f163793 feat: add human-approved consolidation permits
7d6b46b docs: close restart-safe NDNRA proposal memory stage
7280954 feat: validate restart-safe NDNRA proposal memory
b1ec4a3 feat: revalidate NDNRA proposals after restart
2b0fb0a feat: persist NDNRA proposal lifecycle in brain schema 4
555efe7 feat: add restart-safe NDNRA proposal lifecycle checkpoint
```

Use full hashes from Git when reporting final commits.

---

## 21. Known implementation details and caveats

### Immutable original registries

The permit lifecycle registry is immutable. Batch 3 constructs a consumed registry as a new value. It verifies the original registry remains unchanged.

This is deliberate. Persistence must explicitly adopt the returned consumed registry together with the new consolidation state.

### Permit object versus permit record

The permit object always represents issuance evidence and rejects construction with `consumed = true`.

Do not mutate the permit object to represent consumption.

Consumption belongs to:

- `ConsolidationExecutionPermitLifecycleRecord`
- `ConsolidationExecutionPermitLifecycleRegistry`

### Failure receipt

Batch 3 raises on failure and does not return a successful receipt.

A future audit design may record failed attempts, but such records must not resemble successful application receipts and must not cause permit consumption unless a separately validated rule requires it.

Do not add failure logging in Batch 4 in a way that becomes execution authority.

### Successful restoration count

A successful receipt has:

```text
restoration_trigger_count = 0
```

The injected failure test performs restoration but returns no success receipt. This is expected.

### Current brain schema

Brain schema remains 4 until Batch 4 deliberately changes it.

Do not change the schema version casually. Follow existing migration and corruption tests.

### Current replay boundary

No retention replay occurs after successful application yet.

Replay and controlled restoration are the 98% stage. Keep replay count zero throughout the current execution stage.

---

## 22. CodexBridge operating notes

Common repository operations:

- `inspect_repo_status`
- `read_repo_file`
- `read_repo_files`
- `search_repo_text`
- `list_repo_files`
- `preview_repo_patch`
- `apply_repo_patch`
- `create_repo_file`
- `delete_repo_file`
- `run_project_command`
- `remember_repo_decision`
- `commit_selected_files`

Discover exact schemas with `api_tool.list_resources` before invoking a direct CodexBridge function if it has not already been loaded in the session.

Allowed project command IDs used successfully:

```text
ruff_format_check
ruff_check
mypy
pytest
pip_check
git_diff_check
```

The repository command allowlist does not expose a direct Ruff formatting command. The established workaround is:

1. Create a temporary Pytest file that invokes:
   - `python -m ruff check --fix <changed files>`
   - `python -m ruff format <changed files>`
2. Run full Pytest.
3. Delete the temporary test file.
4. Rerun all real quality gates.

Never commit the temporary formatter test.

---

## 23. Expected Batch 4 final report format

The next session should report:

- Batch 4 completed.
- Exact persistence schema and migration behaviour.
- Exact interruption outcomes.
- Exact corruption outcomes.
- Duplicate/replay protection.
- Stale-after-restart behaviour.
- Live acceptance invariants.
- Zero autonomous execution.
- Zero replay.
- Zero SQLite cognition.
- Full test count.
- Ruff, Mypy, Pip, and Git checks.
- Exact commit hash.
- Branch-ahead count.
- Manual push command.
- Progress changed to 4 of 5.
- Readiness remains 96%.
- Next task is Batch 5 closure.

---

## 24. Final state summary

At handover:

```text
Repository: seedmind
Branch: main
Working tree: clean
Latest implementation commit: 8f83f0d
Branch ahead before handover commit: 1
Human-approved execution stage: 3/5
Current readiness: 96%
Next batch: persistence, interruption, and live acceptance
Automatic push: forbidden
```

The core engineering objective for the next session is not to add more authority. It is to prove that the authority already bounded by explicit human approval remains exact, single-use, corruption-safe, and non-autonomous across restart and process interruption.
