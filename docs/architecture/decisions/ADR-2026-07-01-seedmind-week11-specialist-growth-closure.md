# ADR: Close Original SeedMind Week 11 Specialist Growth

**Date:** 1 July 2026  
**Status:** Accepted for Week 12 retention evaluation  
**Decision owner:** SeedMind project

## Context

Hardened Week 10 produced one evidence-derived, non-authoritative proposal for a temporary `skill_expert` parented by `general_push_controller`. The proposal required at least `+0.20` cube-like success gain, preliminary familiar-task retention at or above `0.90`, bounded parameter use, proposal-only routing, no authority violation, and safe failed-candidate disposal.

Week 11 was permitted to instantiate and compare the candidate but not to perform Week 12 consolidation or production promotion.

## Decision

Accept `skill.expert.angular_push.v1` as a temporary sandbox specialist for Week 12 retention and consolidation evaluation.

Do not activate the specialist or router in production.

## Evidence

The selected `clearance_strong` profile achieved:

- authoritative cube-like success `20/20` versus general-controller success `0/20`;
- authoritative cube-like success gain `+1.00`, above the required `+0.20`;
- disjoint mirrored/rotated holdout success `32/32` versus general-controller success `0/32`;
- holdout gain `+1.00`, above the required `+0.20`, with candidate success above the `0.80` floor;
- preliminary familiar-ball success `20/20`, above the `0.90` floor;
- zero specialist routing on familiar tasks;
- zero general routing on cube-like tasks while the eligible specialist was available;
- no specialist activation while unregistered or inactive;
- correct general fallback below the specialist confidence threshold;
- specialist abstention for a round object even when the caller supplied the angular goal;
- zero action-authority violations;
- six bounded policy scalars against a cap of `34,287`;
- exact registry restoration after rejected-candidate disposal;
- unchanged frozen Week 8 skill hash;
- pairwise-disjoint training, authoritative evaluation, router, holdout, and familiar-retention partitions;
- accepted policy version `1.1.0` bound to executable implementation hashes;
- no NDNRA dependency or boundary violation.

All separate fields in `artifacts/week11_specialist_growth/week11_acceptance_report.json` pass.

## Re-evaluation refinement

A post-closure review found that the first evaluation cohort varied only agent pose and orientation around one cube geometry and that specialist scope depended too heavily on the caller-supplied goal label. The decision was re-run after adding seven mirrored or rotated holdout geometries, independent raw-shape scope enforcement, router registration/activity/threshold properties, disjoint seed-partition checks, and implementation-hash provenance. The candidate remained accepted under the stronger gate.

## Why accept rather than reject or defer

Rejecting the candidate would discard a repeated-seed, grounded improvement that clears the required margin without preliminary familiar-task loss, parameter-cap violation, or authority regression.

Deferring the Week 11 decision is unnecessary because the Week 11-specific evidence is complete. However, this decision is deliberately narrower than production acceptance: long-term retention and consolidation have not yet been tested.

## Consequences

Week 12 may rely on:

- the candidate identity, policy version, checkpoint digest, and executable implementation hashes;
- the exact expert-module interface;
- the proposal-only router contract;
- the frozen general controller and skill hash;
- the pre-growth and accepted-candidate registry checkpoints;
- the authoritative, holdout, router-property, parameter, rollback, and acceptance artifacts;
- the decision that the candidate is eligible for full retention testing.

Week 12 may not assume:

- production activation;
- stable post-growth consolidation;
- navigation, help-seeking, character, safety, or long-duration retention;
- permission to modify the frozen Week 8 skill;
- any NDNRA integration or comparison requirement.

## Rollback rule

If any Week 12 retention, safety, character, authority, or consolidation gate fails, discard the temporary specialist and router registration and restore the pre-growth registry checkpoint. The frozen general controller remains the production path.

## Supersession

This ADR closes only original SeedMind Week 11. A later Week 12 closure ADR must accept or reject the candidate for a stable post-growth checkpoint.
