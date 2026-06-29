# ADR-2026-06-29 Normalized Competing Recruitment

## Status

Accepted

## Context

The retain-or-descope audit required local spreading-activation normalization under competing recruitment before standalone NDNRA v0.1 closure. The existing heat-fan prototype used a raw incoming weighted sum during recall. That made local support scale directly with the count of positive incoming contributors, which obscured whether one strong relevant contributor or several weaker irrelevant contributors won solely by fan-in.

Batch 1 is limited to normalized competing recruitment only. It must preserve deterministic heat-fan recall behaviour, dormancy behaviour, existing `RecallResult`, `NDNRAExperimentResult`, standalone acceptance payloads, and checkpoint schemas. It must not introduce saturation, SQLite authority, workers, timers, schedulers, recommendations, execution, integration, or production control.

## Decision

Add one isolated `normalized_recruitment.py` contract that:

- records deterministic ordered local incoming contributions per target neuron;
- sums only positive local incoming contributions;
- divides that sum by the positive contributor count;
- floors normalized support safely to zero when no positive contributor exists;
- exposes immutable evidence for ordered contributions, raw positive sum, positive contributor count, maximum local contribution, normalized support, and boundedness.

`LocalNeuralGraph.recall_action()` now uses that normalized local incoming support instead of the raw incoming sum while preserving the existing need drive, activation persistence, dormancy resistance, effort boost, thresholds, depth limits, and deterministic tie ordering.

A separate optional evidence API returns the unchanged `RecallResult` together with deterministic per-depth and per-neuron normalization evidence. The standard recall path remains backward compatible and unchanged at the persisted-contract boundary.

## Consequences

Positive consequences:

- Competing recruitment is normalized locally rather than by raw positive fan-in.
- A single strong contributor cannot be outvoted solely by duplicated weaker positive contributors.
- Zero or negative contributors do not inflate normalized support.
- Evidence remains deterministic, immutable, bounded, and inspectable.

Non-consequences:

- No graph-locally derived saturation is implemented in this batch.
- No persisted dataclass, standalone acceptance payload, or checkpoint schema changes occur.
- No SQLite, worker, timer, scheduler, recommendation, execution, live integration, or production authority is added.

## Next

Batch 2 remains graph-locally derived saturation and saturation-gated growth pressure.
