# SeedMind Consequence, Imagination, and Memory-Maintenance Stage Plan

Date: 28 June 2026
Repository: `D:\Github\SeedMind`
Branch: `main`
Stage status: active

## 1. Why the scope changed

The earlier 97% marker measured completion of a narrower theory-to-integration programme. It did not mean that the complete developmental-mind design was 97% finished.

The expanded design now explicitly requires SeedMind to:

- make wrong actions matter to later decisions;
- keep competence local to an action and situation rather than global;
- compare expected consequences with observed consequences;
- distinguish real experience from replay and imagination;
- revisit real memories without treating repetition as new evidence;
- imagine untested action combinations and sequences;
- preserve useful pathways through bounded replay and imagination;
- prevent imagined outcomes from becoming accepted facts;
- propose safe real experiments for promising imagined solutions;
- learn both whether an action works and whether its predictions are accurate.

## 2. Recalculated progress

The expanded developmental architecture is estimated at **68% complete before this stage**.

This is a heuristic engineering marker, not scientific validation, production readiness, AGI progress, or a safety certification.

Weighted estimate:

| Area | Weight | Current completion | Weighted contribution |
| --- | ---: | ---: | ---: |
| Environment, observations, and primitive actions | 15% | 95% | 14.25% |
| Prediction and body/action-effect learning | 10% | 85% | 8.50% |
| Needs, curiosity, ambition, and human support | 10% | 80% | 8.00% |
| Contextual memory, effects, and action composition | 15% | 90% | 13.50% |
| Structural growth, consolidation, and safe persistence | 15% | 90% | 13.50% |
| Consequence-to-local-competence learning | 10% | 30% | 3.00% |
| Controlled replay and complete restoration | 10% | 40% | 4.00% |
| Internal consequence model and imagined rollouts | 10% | 10% | 1.00% |
| Safe experiment promotion and continuous maintenance | 5% | 35% | 1.75% |
| **Total** | **100%** |  | **67.50%**, rounded to **68%** |

The previous 97% marker remains historically valid for its old scope, but it must not be used as the overall SeedMind completion figure after this expansion.

## 3. Architectural rules

- A wrong action must change later trust in that action under a similar context.
- One failure must not globally condemn an action that works elsewhere.
- Prediction accuracy and action helpfulness are separate measurements.
- An accurately predicted harmful action is still a poor action for the active need.
- Real experience may update action competence.
- Replay may preserve accessibility and re-evaluate existing evidence, but cannot manufacture independent evidence.
- Imagination may create hypotheses and weak activity, but cannot prove an outcome.
- Imagined activity must not directly increase mastery, confidence, or production authority.
- Useful old pathways may receive bounded maintenance activity without being treated as newly verified.
- Dormancy must remain possible for irrelevant, repeatedly inaccurate, harmful, or redundant pathways.
- Safe real-world verification is required before an imagined action combination becomes trusted.
- High-impact experiments require explicit safety limits and, where configured, human approval.

## 4. Stage batches

### Batch 1 - real consequence and local competence

Status: implemented in the commit containing this plan.

Deliverables:

- Exact expected-versus-observed consequence comparison.
- Need-aligned classification: improved, unchanged, or worsened.
- Separate prediction accuracy and action helpfulness.
- Context-and-action-specific competence records.
- Duplicate real-event rejection.
- Explicit rejection of replay or imagination as new competence evidence.
- No action-selection or production authority.

### Batch 2 - activity source and dormancy maintenance

Status: implemented in the commit containing this update.

Deliverables:

- Separate real, replay, and imagined activity counters.
- Strong real activation, medium replay activation, and weak imagined activation.
- Replay and imagination require named supporting real events.
- Replay and imagination require minimum real-evidence strength.
- Activity may reduce dormancy without increasing factual confidence or mastery.
- Safety-critical and rare-use memories receive bounded maintenance floors.
- Harmful, irrelevant, or redundant pathways remain eligible for dormancy even when marked rare or safety-related.
- Low prediction accuracy and low helpfulness reduce maintenance strength.
- Exact duplicate activity cannot reduce dormancy twice.
- Per-event structure limits, per-cycle event limits, and total reactivation budgets.
- Dormancy maintenance leaves eligibility, growth pressure, residuals, and real last-active state unchanged.
- No action-selection or production-action authority.

Batch 2 is in-memory only. Persistence and restart reconstruction remain part of Batch 7.

### Batch 3 - controlled replay completion

Status: implemented with restart-safe durable replay and exact complete-envelope restoration.

Completed:

- Replay only exact named real activity.
- Immediate source, active-state, fresh-evidence, and permit revalidation.
- Explicit caller-supplied work items with strict bounds.
- No duplicate mastery, confidence, or independent-evidence inflation.
- Bounded accessibility maintenance using the existing replay strength.
- Exact deterministic receipts.
- Single-use permit consumption only after complete success.
- Atomic durable replay with exact old-or-new interruption resolution.
- Schema-6 persistence of active activity history, permits, and receipts.
- Exact full-state restoration of graph, growth, consolidation, proposal, execution, and active activity memory.
- Monotonic operation audit that prevents restoration from reviving used approvals.
- Separate active-state and complete-envelope checksums.

### Batch 4 - learned consequence model

Planned:

- Predict next relevant state and effects from context plus action.
- Represent action order and combinations.
- Report uncertainty and evidence coverage.
- Compare predictions with real outcomes.
- Correct overconfident and underconfident predictions.
- Keep the model inspectable and bounded for the MVP environment.

### Batch 5 - bounded imagination

Planned:

- Generate action candidates and short sequences from learned pieces.
- Simulate possible outcomes without changing the real environment.
- Keep imagined traces separate from real and replayed traces.
- Limit sequence depth, candidate count, rollout count, and computation.
- Trigger imagination from unresolved needs, surprise, contradiction, low confidence, or bounded idle periods.
- Reject unsupported chains and runaway self-confirmation.

### Batch 6 - safe experiment proposals

Planned:

- Convert promising imagined outcomes into explicit hypotheses.
- State predicted benefit, uncertainty, possible harm, stop conditions, reversibility, and required permission.
- Prefer low-impact information-gaining tests.
- Compare the real result with the imagined result.
- Update both action competence and model accuracy.

### Batch 7 - persistence, live integration, and acceptance

Planned:

- Persist consequence, competence, activity-source, replay, and imagination evidence.
- Restart without losing source distinctions or single-use guarantees.
- Demonstrate that imagined evidence cannot become real evidence after restart.
- Demonstrate memory maintenance without false mastery inflation.
- Demonstrate context-specific failure consequences.
- Preserve production-action authority boundaries until separately accepted.
- Recalculate progress only after complete repository gates and live evidence pass.

## 5. Batch 1 design

For one real event, SeedMind records:

- the exact pre-action context;
- the active need;
- the action;
- expected effects;
- observed effects;
- how much the action helped or worsened the need;
- how accurately the result was predicted;
- the exact real event identity.

The action competence record is keyed by both context and action. It tracks:

- real attempt count;
- improved, unchanged, and worsened outcomes;
- average need-aligned result;
- average prediction accuracy;
- evidence strength;
- bounded local competence.

A wrong outcome lowers local helpfulness and competence. It does not create emotional punishment, resentment, or a global loss of confidence.

## 6. Progress rule

The expanded marker started at 68% before Batch 1.

After Batch 1, the heuristic marker reached **71%**. Batch 2 raised it to **73%** by adding source-separated activity, bounded dormancy maintenance, duplicate protection, safety and rare-use floors, and explicit protection against false confidence or mastery gains. In-memory controlled replay raised it to **75%**. Restart-safe durable replay and exact complete-envelope restoration raise the expanded marker to **78%**.

The marker remains limited because SeedMind still does not provide a learned consequence model, dreaming, optimizer-driven route discovery, safe experiment promotion, persistence for every later imagination contract, or complete live integration.

No later percentage should be raised merely because contracts exist. Each capability requires behavioural evidence, failure-path tests, persistence evidence where applicable, and repository-wide quality gates.

## 7. Repository workflow

- Implement one bounded batch per commit.
- Keep real, replayed, and imagined evidence distinguishable in every contract.
- Run targeted tests during implementation and all repository quality gates before committing.
- Never push automatically.
