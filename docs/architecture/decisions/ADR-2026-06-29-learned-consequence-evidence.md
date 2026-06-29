# ADR: Learned Consequence Evidence Is Restart-Safe, Live Accepted, Prediction-Only

Date: 29 June 2026
Status: accepted
Scope: SeedMind repository

## Context

The learned consequence model now has exact one-step records, bounded contextual
transfer, observed consequence chains, schema-7 checkpoint persistence, and live Nursery
acceptance evidence.

The closure correction required the live accepted model to prove exact observed
consequence-chain evidence, restart equivalence, malformed-state fallback, and unchanged
production action authority before the stage could close.

## Decision

Learned consequence evidence is accepted only when it is grounded in unique real Nursery
transitions. Observed consequence chains are accepted only when they are built from
consecutive unique real transitions with exact context continuity.

The learned consequence checkpoint is restart-safe through brain schema 7. A valid
restart must preserve exact predictions, chain predictions, provenance, duplicate
protection, configuration, confidence, and zero authority. Malformed persisted learned
state causes complete safe fallback.

Learned consequence predictions are prediction-only. They have no production action
authority and cannot select, rank, recommend, schedule, search, optimize, execute,
trigger growth, replay, restore, or promote experiments.

Replay, imagined, transferred, disconnected, duplicate, conflicting, partial, missing,
and bound-failing evidence paths cannot enter the real learned-consequence evidence
model.

## Consequences

- Bounded imagination may use learned consequence predictions only as non-authoritative
  hypotheses.
- Imagined evidence remains non-factual until verified by later real Nursery
  transitions.
- Safe-experiment proposals remain out of scope until bounded imagination has its own
  accepted boundary.
- Any future integration that gives learned consequence outputs action influence must
  create a new explicit architecture decision and acceptance gate.
