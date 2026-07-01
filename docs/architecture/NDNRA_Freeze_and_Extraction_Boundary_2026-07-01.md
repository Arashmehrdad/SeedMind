# NDNRA Freeze and Extraction Boundary

Date: 1 July 2026  
Status: Active freeze boundary  
Source baseline: `b9a2ae678938ae1d3dc5e5f4568714dd070a6e2a`

## Decision

The Need-Driven Neural Recruitment Architecture is frozen inside the SeedMind repository and will continue, if at all, as a separate project.

SeedMind no longer treats NDNRA as:

- an active shadow controller;
- a mandatory comparison target;
- a candidate component for the current product roadmap;
- a requirement for Week 10 or later acceptance;
- an authorised Stage 9 programme;
- a production integration path.

The NDNRA implementation, tests, documents, decisions, and evidence remain in this repository only as a preserved research snapshot and extraction source. The machine-readable freeze declaration is `docs/architecture/NDNRA_Freeze_Manifest_2026-07-01.json`.

## Frozen scope

The frozen snapshot includes:

- `src/seedmind/research/ndnra/`;
- NDNRA-specific integration and shadow adapters already present at the source baseline;
- NDNRA unit and acceptance tests;
- NDNRA architecture, evidence, audit, and ADR documents;
- NDNRA research artifacts and historical Week 9 comparison artifacts.

Existing historical runners may remain executable for reproducibility, but they are not part of ongoing SeedMind product acceptance.

## SeedMind boundary after the freeze

From original Week 10 onward:

1. SeedMind follows the original main-product roadmap independently.
2. No SeedMind milestone requires NDNRA proposals, comparisons, training, or competence evidence.
3. No new SeedMind implementation may import or depend on NDNRA for product behavior.
4. NDNRA cannot own action selection, verification, support decisions, memory, planning, growth, consolidation, or safety authority in SeedMind.
5. Existing production authority remains with the established SeedMind components and protected human/safety control planes.
6. Historical NDNRA code must not be silently modified while implementing ordinary SeedMind work.

## Allowed changes inside SeedMind

Changes to the frozen NDNRA snapshot are limited to:

- extraction packaging requested explicitly by Arash;
- security or secret-removal corrections;
- repository-wide mechanical compatibility fixes that do not change NDNRA behavior;
- preservation fixes required to keep historical evidence readable;
- an explicit rollback of accidental post-freeze modification.

Any such change must be labelled as freeze maintenance, not NDNRA development.

The following are prohibited in this repository:

- NDNRA Stage 9 or later stages;
- new NDNRA capabilities, experiments, adapters, training protocols, or promotion gates;
- additional Default-vs-NDNRA product comparisons;
- NDNRA production integration;
- presenting an adapter or heuristic as the NDNRA architecture;
- using NDNRA evidence to complete a SeedMind milestone;
- making future SeedMind code depend on NDNRA modules.

## Extraction rule

A future separate NDNRA project should begin from the preserved source baseline and copy the relevant source, tests, documents, ADRs, and artifacts with provenance intact.

The separate project must establish its own:

- repository and roadmap;
- architecture authority;
- test and evidence baselines;
- packaging and persistence boundaries;
- integration policy, if any;
- product claims.

No future work in the separate NDNRA project automatically changes SeedMind.

## Historical evidence

Week 9 Default and contribution results remain valid for SeedMind.

The committed NDNRA comparison artifacts remain historical records of the experiments that were run. They do not establish NDNRA competence, do not make NDNRA part of the SeedMind product, and do not create an obligation to continue comparison work in this repository.

## Continuation

The next authorised SeedMind work is original Week 10 capacity diagnosis without NDNRA participation or dependency.
