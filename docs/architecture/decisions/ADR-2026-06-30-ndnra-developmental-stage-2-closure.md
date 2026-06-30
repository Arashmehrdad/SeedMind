# ADR: NDNRA Developmental Network Stage 2 Closure

Date: 30 June 2026
Status: Accepted implementation evidence after final gates
Scope: NDNRA v0.2 Stage 2 associative need-and-context recall

## Context

Stage 1A closed DESA bootstrap and hierarchical metacognition over the Stage 1 recurrent substrate. The next required boundary was Stage 2: prove associative need-and-context recall without merging distinct experiences into one abstract record and without beginning simultaneous multiple-need or region-specialization work.

## Decision

Accept Stage 2 as implemented and evidenced by:

- `src/seedmind/research/ndnra/developmental_associative_recall.py`;
- `tests/unit/test_ndnra_developmental_associative_recall.py`;
- `docs/architecture/NDNRA_Developmental_Stage_2_Evidence_2026-06-30.md`.

The accepted Stage 2 boundary is:

- deterministic and in memory only;
- layered on the Stage 1 substrate;
- based on typed need, context, experience, action, outcome, and inhibition links;
- able to complete partial cues without exact context equality;
- explicit about shuffled, need-removed, context-removed, inhibition-removed, exact-context-only, and one-winner-only controls;
- non-persistent;
- non-SQLite;
- zero-authority;
- disconnected from runtime adapters and action gateways.

## Consequences

- Stage 3 specialised concurrent regions and multiple needs is now the next bounded implementation target after the Stage 2 commit.
- Stage 2 does not prove simultaneous multiple needs, region-local pools, regional maturity, mature skill promotion, mature ambition lifecycle, homeostasis, hibernation, dreaming, restart identity, learned responsibility, typed action proposals, shadow trial behavior, or any action gateway behavior.
- Generalisation is accepted only as associative recruitment among inspectable separate episodes, not as semantic record merging.
- Production curiosity remains the sole production action authority.
- The expanded developmental architecture marker remains 82%.
- No automatic push is authorised.
