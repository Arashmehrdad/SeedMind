# ADR: NDNRA Developmental Network Stage 1 Closure

Date: 30 June 2026
Status: Accepted implementation evidence after final gates
Scope: NDNRA v0.2 Stage 1 recurrent experiential substrate

## Context

Stage 0 closed the v0.2 identity, lifecycle, trace, and schema-separation contract layer. The next required boundary was Stage 1: represent experiences as distributed coalitions inside a reusable recurrent neuron pool without creating one neuron per experience and without connecting to persistence, runtime adapters, action gateways, SQLite cognition, or production authority.

## Decision

Accept Stage 1 as implemented and evidenced by:

- `src/seedmind/research/ndnra/developmental_network.py`;
- `tests/unit/test_ndnra_developmental_network.py`;
- `docs/architecture/NDNRA_Developmental_Stage_1_Evidence_2026-06-30.md`.

The accepted Stage 1 boundary is:

- deterministic and in memory only;
- based on a fixed reusable neuron pool;
- capable of overlapping coalitions with distinct episode identities;
- explicit about excitatory and inhibitory signed connections;
- bounded by a configured recurrent settling budget;
- non-persistent;
- non-SQLite;
- zero-authority;
- disconnected from runtime adapters and action gateways.

## Consequences

- Stage 1A is now the next bounded implementation target.
- Stage 1A may use the Stage 1 substrate for DESA bootstrap and hierarchical metacognition tests.
- Stage 1 does not prove broad associative recall, simultaneous needs, mature ambition commitment, skill maturation, hibernation, dreaming, learned responsibility, typed action proposals, or shadow trial behavior.
- Structural neuron creation remains disabled.
- Production curiosity remains the sole production action authority.
- The expanded developmental architecture marker remains 82%.
- No automatic push is authorised.
