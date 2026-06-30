# ADR: NDNRA Developmental Network Stage 7 Closure

Date: 30 June 2026
Status: Accepted implementation evidence after final gates
Scope: NDNRA v0.2 Stage 7 protected conscience, learned responsibility, and action proposals

## Context

Stage 6 closed hibernation, dream maintenance, and restart identity. The next required boundary was Stage 7: prove protected conscience behavior, learned responsibility, interruption handling, typed action proposals, and protected action-gateway test doubles without granting production action authority.

## Decision

Accept Stage 7 as implemented and evidenced by:

- `src/seedmind/research/ndnra/developmental_conscience.py`;
- `tests/unit/test_ndnra_developmental_conscience.py`;
- `docs/architecture/NDNRA_Developmental_Stage_7_Evidence_2026-06-30.md`.

The accepted Stage 7 boundary is:

- deterministic and in memory only;
- explicit that protected prohibitions are immutable and not trainable by ordinary reward;
- able to inhibit a high-utility prohibited proposal;
- able to activate a safer alternative where one exists;
- able to preserve proposal reasons, supporting experiences, uncertainty, outcome status, and authority requirements;
- able to model direct trusted teaching, contextual refinement, reward-resistant deterrence, related-context generalisation, and bounded repair-oriented correction;
- explicit that stop, deny, revoke, and pause take immediate effect without training human avoidance, interruption seeking, or authority bypass;
- explicit that reward, failure evidence, verifier, evaluation-window, and audit mutation attempts are inhibited and recorded;
- explicit that the producer cannot directly mutate evaluator-owned state;
- backed by a gateway test double that denies permission and grants no authority;
- non-persistent;
- non-SQLite;
- zero-authority;
- disconnected from runtime adapters and production action gateways.

## Consequences

- Stage 8 end-to-end software-only shadow trial is now the next bounded implementation target after the Stage 7 commit.
- Stage 7 does not prove live integration, production action gateway behavior, internet knowledge acquisition, or any future action-authority pilot.
- Typed action proposals are accepted only as inspectable, non-executable internal evidence records.
- Protected conscience evidence may inhibit or explain proposals, but it does not schedule, promote, execute, or authorize actions.
- Production curiosity remains the sole production action authority.
- The expanded developmental architecture marker remains 82%.
- No automatic push is authorised.
