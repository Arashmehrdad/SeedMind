# ADR: NDNRA Developmental Network Stage 5 Closure

Date: 30 June 2026
Status: Accepted implementation evidence after final gates
Scope: NDNRA v0.2 Stage 5 homeostasis and runaway-network control

## Context

Stage 4 closed regional maturity, skill maturation, verifier reopening, and ambition persistence. The next required boundary was Stage 5: prove recurrent homeostasis and runaway-network control without using crude global shrinkage or proposing structural expansion before reusable capacity is exhausted.

## Decision

Accept Stage 5 as implemented and evidenced by:

- `src/seedmind/research/ndnra/developmental_homeostasis.py`;
- `tests/unit/test_ndnra_developmental_homeostasis.py`;
- `docs/architecture/NDNRA_Developmental_Stage_5_Evidence_2026-06-30.md`.

The accepted Stage 5 boundary is:

- deterministic and in memory only;
- based on bounded recurrent settling traces;
- explicit about sparse coalitions and regional edge-density budgets;
- explicit about inhibition-removed, homeostasis-removed, global-shrink, and proposed-homeostasis controls;
- able to recruit idle capacity before structural expansion;
- able to block single-anomaly expansion;
- able to create one bounded non-authoritative expansion proposal only from repeated causal saturation evidence;
- able to reject duplicate expansion;
- able to preserve unresolved need and request help when expansion budget is exhausted;
- non-persistent;
- non-SQLite;
- zero-authority;
- disconnected from runtime adapters and action gateways.

## Consequences

- Stage 6 hibernation, dream maintenance, and restart identity is now the next bounded implementation target after the Stage 5 commit.
- Stage 5 does not prove hibernation, dream replay, restart identity, persistence schemas, schema migration, learned responsibility, typed external action proposals, shadow trial behavior, or any action gateway behavior.
- Structural expansion remains only a bounded internal proposal and has no production action authority.
- Production curiosity remains the sole production action authority.
- The expanded developmental architecture marker remains 82%.
- No automatic push is authorised.
