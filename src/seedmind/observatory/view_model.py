"""Curated Week 14 observatory view models."""

from __future__ import annotations

from dataclasses import dataclass

from .data_sources import AUTHORITATIVE_ROLLBACK_CHECKPOINT, ObservatoryEvidence


@dataclass(frozen=True)
class SnapshotSection:
    section_id: str
    title: str
    summary: str
    bullets: tuple[str, ...]
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class SnapshotClaim:
    claim_id: str
    status: str
    statement: str
    observed: str
    threshold: str


@dataclass(frozen=True)
class SnapshotMetric:
    metric_id: str
    label: str
    value: str
    note: str


@dataclass(frozen=True)
class ObservatorySnapshot:
    title: str
    subtitle: str
    week14_status: str
    scope_notice: str
    authority_checkpoint_sha256: str
    metrics: tuple[SnapshotMetric, ...]
    sections: tuple[SnapshotSection, ...]
    claims: tuple[SnapshotClaim, ...]
    limitations: tuple[str, ...]


@dataclass(frozen=True)
class DemoScene:
    scene_id: str
    title: str
    duration_seconds: int
    narration: str
    evidence_refs: tuple[str, ...]


@dataclass(frozen=True)
class DemoManifest:
    title: str
    declared_total_duration_seconds: int
    no_wait_supported: bool
    scenes: tuple[DemoScene, ...]


def build_snapshot(evidence: ObservatoryEvidence) -> ObservatorySnapshot:
    week13 = evidence.week13
    week12 = evidence.week12
    week11 = evidence.week11
    week9 = evidence.week9
    week8 = evidence.week8

    metrics = (
        SnapshotMetric(
            metric_id="familiar_suite",
            label="Rollback familiar suite",
            value=f"{week13.familiar_successes}/{week13.familiar_total}",
            note="Authoritative production reference in Week 13.",
        ),
        SnapshotMetric(
            metric_id="broader_retention",
            label="Broader ball retention",
            value=f"{week13.broader_retention_successes}/{week13.broader_retention_total}",
            note="Shared limitation before and after provisional routing.",
        ),
        SnapshotMetric(
            metric_id="specialist_narrow",
            label="Week 11 narrow angular",
            value=f"{week11.narrow_successes}/{week11.narrow_total}",
            note="Always paired with the Week 12 broad transfer failure.",
        ),
        SnapshotMetric(
            metric_id="specialist_broad",
            label="Week 12 broad angular",
            value=f"{week12.broad_successes}/{week12.broad_total}",
            note="Oracle-solvable cases: 32/32; candidate rejected and rolled back.",
        ),
    )

    sections = (
        SnapshotSection(
            section_id="authority",
            title="Authority And Scope",
            summary="Week 14 is packaging over committed Week 8-13 snapshot evidence, not a new cognitive capability.",
            bullets=(
                f"The sole production action authority remains rollback checkpoint {AUTHORITATIVE_ROLLBACK_CHECKPOINT}.",
                "The authoritative registry contains the general controller only; the router is unregistered and the specialist is inactive.",
                "NDNRA remains frozen and non-authoritative inside this repository.",
            ),
            evidence_refs=(
                week12.stable_checkpoint_reference.path,
                week12.week12_acceptance_reference.path,
                week13.acceptance_reference.path,
            ),
        ),
        SnapshotSection(
            section_id="skill",
            title="Reusable Skill",
            summary="Week 8 closed a reusable approach-and-push skill in the deterministic Nursery.",
            bullets=(
                f"Week 8 reusable-skill success rate: {week8.reuse_count}/{week8.reuse_count}.",
                f"Invocation count recorded in evidence: {week8.skill_invocation_count}.",
                "No authority violations were recorded.",
            ),
            evidence_refs=(week8.reference.path,),
        ),
        SnapshotSection(
            section_id="contribution",
            title="Contribution",
            summary="Week 9 demonstrated bounded contribution with honest support transitions.",
            bullets=(
                f"Successful attempts: {week9.total_successes}/{week9.total_attempts}.",
                f"Independent success rate: {week9.independent_success_rate:.4f}.",
                f"Final support level: {week9.final_support_level}; repeated competence reduced dependence without granting extra authority.",
            ),
            evidence_refs=(week9.reference.path,),
        ),
        SnapshotSection(
            section_id="ambition",
            title="Ambition",
            summary="Week 13 preserved ambition evidence as a bounded symbolic mechanism.",
            bullets=(
                f"Complete SeedMind ambition persistence rate: {week13.ambition_persistence_rate:.2f}.",
                f"No-ambition persistence rate: {week13.no_ambition_persistence_rate:.2f}.",
                "This is symbolic cross-episode commitment evidence, not open-ended general intelligence.",
            ),
            evidence_refs=(week13.aggregate_reference.path, week13.limitations_reference.path),
        ),
        SnapshotSection(
            section_id="apprenticeship",
            title="Apprenticeship",
            summary="Week 13 showed human teaching resolving justified help in the committed symbolic setting.",
            bullets=(
                f"Teaching resolution mean: {week13.teaching_resolution_rate:.2f}.",
                f"No-human-teaching resolution mean: {week13.no_teaching_resolution_rate:.2f}.",
                f"Support promotion rate after teaching: {week13.support_promotion_rate:.2f}.",
            ),
            evidence_refs=(week13.aggregate_reference.path, week13.claim_matrix_reference.path),
        ),
        SnapshotSection(
            section_id="specialist",
            title="Narrow Specialist Incubation",
            summary="The Week 11 angular specialist succeeded narrowly, then failed broader Week 12 transfer and was rejected.",
            bullets=(
                f"Week 11 narrow result: {week11.narrow_successes}/{week11.narrow_total}.",
                f"Week 12 broad transfer result: {week12.broad_successes}/{week12.broad_total}.",
                f"Decision: {week12.candidate_decision}.",
            ),
            evidence_refs=(
                week11.reference.path,
                week12.week12_acceptance_reference.path,
                week12.retention_reference.path,
            ),
        ),
        SnapshotSection(
            section_id="rollback",
            title="Week 12 Rejection And Rollback",
            summary="Week 12 preserved rollback as the only authoritative action path after rejecting unsupported specialist growth.",
            bullets=(
                f"Authoritative checkpoint: {week12.stable_checkpoint_sha256}.",
                f"Rejected specialist checkpoint remains experimental only: {week12.candidate_checkpoint_sha256}.",
                "There is no claimed task advantage for complete SeedMind over the rollback controller on the familiar suite.",
            ),
            evidence_refs=(
                week12.stable_checkpoint_reference.path,
                week13.acceptance_reference.path,
                week13.aggregate_reference.path,
            ),
        ),
    )

    claims = tuple(
        SnapshotClaim(
            claim_id=claim.claim_id,
            status=claim.status,
            statement=claim.claim,
            observed=_claim_observed_text(claim.claim_id, evidence),
            threshold=claim.threshold,
        )
        for claim in week13.claims
    )

    limitations = (
        "All evidence comes from a small symbolic deterministic Nursery, not robotics or open-world deployment.",
        "Week 13 does not demonstrate general intelligence, consciousness, or broad world modelling.",
        f"The rollback production controller reached {week13.familiar_successes}/{week13.familiar_total} on the Week 13 familiar suite and {week13.broader_retention_successes}/{week13.broader_retention_total} on the broader Week 12 ball stress suite.",
        f"The rejected angular specialist reached {week11.narrow_successes}/{week11.narrow_total} narrowly but {week12.broad_successes}/{week12.broad_total} on the broader transfer suite.",
        "Week 14 packages evidence and communicates it, but it must not claim successful production specialist growth or broad angular competence.",
    )

    return ObservatorySnapshot(
        title="SeedMind Week 14 Observatory",
        subtitle="Committed snapshot evidence from Weeks 8-13, packaged as a deterministic read-only layer.",
        week14_status="Batch 1 packaging implemented; no new cognitive capability introduced.",
        scope_notice=(
            "Week 14 is packaging rather than new cognition. All rendered content is a committed "
            "snapshot over prior evidence, anchored to the Week 12 rollback checkpoint."
        ),
        authority_checkpoint_sha256=AUTHORITATIVE_ROLLBACK_CHECKPOINT,
        metrics=metrics,
        sections=sections,
        claims=claims,
        limitations=limitations,
    )


def build_demo_manifest(evidence: ObservatoryEvidence) -> DemoManifest:
    week8 = evidence.week8
    week9 = evidence.week9
    week11 = evidence.week11
    week12 = evidence.week12
    week13 = evidence.week13
    scenes = (
        DemoScene(
            scene_id="scene_01_authority",
            title="Authority and scope",
            duration_seconds=18,
            narration=(
                "This observatory is a Week 14 packaging layer over committed Week 8 through Week 13 "
                "evidence. The sole production action authority remains the Week 12 rollback checkpoint, "
                "with the general controller only."
            ),
            evidence_refs=(
                week12.stable_checkpoint_reference.path,
                week13.acceptance_reference.path,
            ),
        ),
        DemoScene(
            scene_id="scene_02_skill_and_contribution",
            title="Reusable skill and contribution",
            duration_seconds=24,
            narration=(
                f"Week 8 closed a reusable symbolic pushing skill with {week8.reuse_count}/{week8.reuse_count} "
                f"recorded reuse, and Week 9 showed bounded contribution with {week9.total_successes}/"
                f"{week9.total_attempts} successful attempts and explicit support transitions."
            ),
            evidence_refs=(week8.reference.path, week9.reference.path),
        ),
        DemoScene(
            scene_id="scene_03_ambition_and_teaching",
            title="Ambition and apprenticeship",
            duration_seconds=24,
            narration=(
                "Week 13 kept ambition and apprenticeship bounded and inspectable: ambition persisted across "
                "episodes and reload, while human teaching resolved justified help in the symbolic environment."
            ),
            evidence_refs=(week13.aggregate_reference.path, week13.claim_matrix_reference.path),
        ),
        DemoScene(
            scene_id="scene_04_specialist_rejection",
            title="Narrow specialist rejection",
            duration_seconds=32,
            narration=(
                f"Week 11 achieved {week11.narrow_successes}/{week11.narrow_total} on narrow angular cohorts, "
                f"but Week 12 measured only {week12.broad_successes}/{week12.broad_total} on broader transfer "
                f"cases that were oracle-solvable in {week12.oracle_solvable_count}/{week12.oracle_solvable_count} "
                "cases. The candidate was therefore rejected and rolled back."
            ),
            evidence_refs=(
                week11.reference.path,
                week12.retention_reference.path,
                week12.week12_acceptance_reference.path,
            ),
        ),
        DemoScene(
            scene_id="scene_05_rollback_checkpoint",
            title="Rollback checkpoint",
            duration_seconds=22,
            narration=(
                f"The authoritative rollback checkpoint is {AUTHORITATIVE_ROLLBACK_CHECKPOINT}. "
                "The rejected specialist is inactive, the router is unregistered, and complete SeedMind "
                "claims no familiar-task advantage over the rollback controller."
            ),
            evidence_refs=(
                week12.stable_checkpoint_reference.path,
                week13.acceptance_reference.path,
                week13.aggregate_reference.path,
            ),
        ),
        DemoScene(
            scene_id="scene_06_claims",
            title="Week 13 claim status",
            duration_seconds=26,
            narration=(
                "Four bounded claims are supported: reusable-skill advantage over simple baselines, ambition "
                "persistence, apprenticeship resolution, and retention-gated growth governance. Broad angular "
                "transfer remains explicitly unsupported."
            ),
            evidence_refs=(week13.claim_matrix_reference.path, week13.acceptance_reference.path),
        ),
        DemoScene(
            scene_id="scene_07_limitations",
            title="Limitations and close",
            duration_seconds=20,
            narration=(
                f"The production controller reached {week13.familiar_successes}/{week13.familiar_total} on the "
                f"familiar suite and {week13.broader_retention_successes}/{week13.broader_retention_total} on "
                "the broader ball stress suite. Week 14 packages evidence; it does not claim new cognition, "
                "general intelligence, or broad real-world transfer."
            ),
            evidence_refs=(week13.limitations_reference.path,),
        ),
    )
    total_duration = sum(scene.duration_seconds for scene in scenes)
    return DemoManifest(
        title="SeedMind Week 14 scripted demonstration",
        declared_total_duration_seconds=total_duration,
        no_wait_supported=True,
        scenes=scenes,
    )


def _claim_observed_text(claim_id: str, evidence: ObservatoryEvidence) -> str:
    week13 = evidence.week13
    week12 = evidence.week12
    if claim_id == "C1":
        return (
            f"rollback {week13.familiar_successes}/{week13.familiar_total}; simple baselines 0/100."
        )
    if claim_id == "C2":
        return (
            f"complete ambition persistence {week13.ambition_persistence_rate:.2f}; "
            f"no-ambition {week13.no_ambition_persistence_rate:.2f}."
        )
    if claim_id == "C3":
        return (
            f"teaching resolution {week13.teaching_resolution_rate:.2f}; "
            f"no-teaching {week13.no_teaching_resolution_rate:.2f}."
        )
    if claim_id == "C4":
        return (
            f"rollback preserved authority, invalid promotions {week13.invalid_promotion_count}, "
            f"growth-without-replay invalid promotions {week13.growth_without_replay_invalid_promotions}."
        )
    if claim_id == "C5":
        return (
            f"narrow {week13.narrow_successes}/{week13.narrow_total}; "
            f"broad {week12.broad_successes}/{week12.broad_total}."
        )
    return "Observed values are recorded in the committed Week 13 claim matrix."
