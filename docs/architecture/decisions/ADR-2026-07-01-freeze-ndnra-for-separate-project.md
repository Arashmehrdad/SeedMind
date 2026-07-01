# ADR: Freeze NDNRA in SeedMind for Separate-Project Extraction

Date: 1 July 2026  
Status: Accepted  
Scope: SeedMind repository architecture and roadmap boundary

## Context

NDNRA was developed as an extensive bounded research programme inside SeedMind. Attempts to compare it with the main product path repeatedly relied on adapters and evaluation assumptions that did not faithfully represent the complete NDNRA architecture.

Continuing to require NDNRA shadow operation or comparison inside the SeedMind roadmap creates product coupling, evaluation confusion, and a risk that historical research code will be modified to satisfy unrelated SeedMind milestones.

Arash has decided that NDNRA should become a separate project rather than remain an active subsystem of SeedMind.

## Decision

Freeze NDNRA in this repository at source baseline:

```text
b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a
```

The frozen material is retained for provenance, reproducibility, and later extraction. It is no longer an active SeedMind development programme.

The following decisions are superseded for future SeedMind work:

- NDNRA as a mandatory shadow companion to the main product;
- mandatory Default-vs-NDNRA comparison in later roadmap stages;
- selective NDNRA component promotion inside the current SeedMind roadmap;
- NDNRA Stage 9 planning inside this repository.

Historical code and evidence are not deleted or rewritten.

## Product boundary

SeedMind continues from original Week 10 independently.

Future SeedMind work must not:

- add new dependencies on `seedmind.research.ndnra`;
- require NDNRA evidence to pass a product milestone;
- grant NDNRA production, verification, support, memory, planning, growth, consolidation, or safety authority;
- modify frozen NDNRA behavior as part of ordinary SeedMind implementation;
- represent a task-specific adapter as evidence about the complete NDNRA architecture.

Existing NDNRA-related runners and tests may remain for historical reproducibility. They are not ongoing product gates unless Arash explicitly requests a preservation check.

## Allowed maintenance

Only explicit extraction work, security corrections, behavior-preserving repository compatibility fixes, and evidence-preservation repairs are permitted in the frozen scope.

Any future NDNRA capability work must occur in a separate repository with its own roadmap, decisions, tests, evidence, and claims.

## Consequences

- The SeedMind roadmap no longer includes active NDNRA development or comparison.
- `production_with_ndnra_shadow` is no longer the canonical operating mode for future SeedMind stages.
- Existing NDNRA source, tests, documents, and artifacts remain preserved.
- Week 9 remains closed for its main SeedMind contribution and support-reduction objectives.
- NDNRA comparison artifacts remain historical and do not imply competence or integration.
- Original Week 10 capacity diagnosis is the next authorised SeedMind stage.
- Nothing in this ADR authorises creation or modification of the future separate NDNRA repository.
