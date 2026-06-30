# ADR: NDNRA Developmental Network Stage 0 Closure

Date: 30 June 2026
Status: Accepted implementation evidence after final gates
Scope: NDNRA v0.2 Stage 0 identity, lifecycle, trace, and schema-separation contracts

## Context

Stage -1 closed the developmental constitution contracts for DESA, Nursery curricula, ambition, Outcome Fidelity, authority, integrity, and candidate causal responsibility.

The next required boundary was Stage 0: preserve the closed v0.1 evidence while defining a separate v0.2 developmental-network substrate identity layer. The work had to remain inside `src/seedmind/research/ndnra`, avoid runtime integration, avoid action gateways, avoid SQLite cognition, and grant no production action authority.

## Decision

Accept Stage 0 as implemented and evidenced by:

- `src/seedmind/research/ndnra/developmental_identity.py`;
- `tests/unit/test_ndnra_developmental_identity.py`;
- `docs/architecture/NDNRA_Developmental_Stage_0_Evidence_2026-06-30.md`.

The accepted Stage 0 contract boundary is:

- deterministic and in memory only;
- typed and publicly exported through `seedmind.research.ndnra`;
- separate from v0.1 persistence schema names;
- explicit about valid lifecycle transitions and rejected invalid transitions;
- traceable through canonical snapshots;
- zero-authority;
- disconnected from runtime adapters and action gateways;
- unable to mutate closed v0.1 proof stores.

## Consequences

- Stage 1 is now the next bounded implementation target.
- Stage 1 may implement the persistent recurrent experiential substrate in memory, but must not implement persistence save/load, SQLite cognition, runtime integration, action gateway behavior, structural neuron creation, or production action authority.
- Stage 0 does not prove recurrent settling, coalition behavior, DESA bootstrap learning, associative recall, simultaneous needs, maturity, hibernation, dreams, responsibility learning, action proposals, or shadow trial behavior.
- Production curiosity remains the sole production action authority.
- The expanded developmental architecture marker remains 82%.
- No automatic push is authorised.
