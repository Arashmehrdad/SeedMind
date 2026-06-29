# ADR: Explicit Training Review Gate and Non-Training Bypass Policy

Date: 29 June 2026
Status: accepted
Scope: SeedMind bounded imagination

## Context

Batch 7 records optional training-time human review for one exact imagined safe-experiment proposal. That review must remain available during supervised training without becoming a permanent runtime dependency. A later non-training path therefore needs an explicit way to state that the training review gate is being bypassed, while preserving the rule that missing, rejected, or deferred review evidence is never an implicit bypass.

## Decision

Batch 8 resolves one complete revalidated Batch 6 `ImaginedSafeExperimentProposalResult` through one of two explicit paths:

- training or reviewed operation, optionally carrying one exact Batch 7 permission result; or
- non-training operation with an explicitly enabled bypass policy, an explicit bypass request, and an ASCII policy identity beginning with `runtime-policy:`.

The resolver emits one of these exact statuses:

- `review_required`;
- `review_approved`;
- `review_rejected`;
- `review_deferred`;
- `explicit_non_training_bypass`.

A bypass is valid only when all of the following are true:

- mode is explicitly `non_training`;
- policy configuration explicitly allows non-training bypass;
- the caller explicitly requests bypass;
- an exact runtime-policy code is supplied;
- no Batch 7 permission result is supplied on the same path.

If no permission result and no valid explicit bypass are supplied, the outcome is `review_required`. Missing review evidence is never interpreted as permission or bypass.

The review-gate result is descriptive policy evidence only. It does not authorize scheduling, execution, persistence, live integration, action selection, recommendation, promotion, or production control.

## Consequences

- Human review remains enforceable during training.
- Non-training operation is not permanently coupled to Batch 7.
- Review and bypass paths are mutually exclusive and auditable.
- Rejected or deferred training review cannot silently become runtime bypass.
- Any future experiment permit or executor remains a separate architecture boundary.
- The expanded developmental architecture marker remains 82%.
