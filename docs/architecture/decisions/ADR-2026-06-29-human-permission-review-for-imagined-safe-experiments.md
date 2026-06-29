# ADR: Human Permission Review for Imagined Safe Experiments

Date: 29 June 2026
Status: accepted
Scope: SeedMind bounded imagination

## Context

Batch 6 can preserve a caller-authored safe-experiment proposal against one exact audited uncertainty issue. During training, a separate boundary is required before any proposal can be considered human-approved. That training boundary must not become an execution, scheduling, persistence, recommendation, promotion, or production-action path, and it must not become a permanent mandatory dependency for future runtime operation.

## Decision

Batch 7 consumes exactly one complete revalidated Batch 6 `ImaginedSafeExperimentProposalResult`. The human reviewer must provide:

- the exact expected proposal identity;
- the exact expected required-permission value;
- an explicit `approve`, `reject`, or `defer` action;
- a reviewer identity beginning with `human:`;
- an explicit reason code;
- explicit acknowledgements of predicted benefit, uncertainty, possible harm, reversibility, and stop conditions when approving.

Approval records training-time human permission evidence only. Rejection and deferral remain explicit non-permission outcomes. The review policy performs no inference, recommendation, ranking, route selection, experiment selection, scheduling, execution, persistence, live integration, or production action. Future non-training runtime paths may bypass this review only through a separate explicit configured policy; missing review evidence is never itself a bypass signal.

The complete Batch 6 result remains canonical provenance and is revalidated before review. Request, decision, and result identities use canonical ASCII JSON plus SHA-256. Inputs and source snapshot size remain explicitly bounded.

## Consequences

- In training mode, a proposal cannot be approved by a non-human policy identity.
- Training approval requires acknowledgement of every declared benefit, uncertainty, harm, reversibility, and stop-condition field.
- An approved decision does not authorize scheduling or execution.
- Batch 7 remains optional outside training and must be bypassable only by an explicit future runtime policy boundary.
- Any future experiment permit, executor, persistence layer, or live Nursery integration requires a separately approved architecture boundary.
- The expanded developmental architecture marker remains 82%.
