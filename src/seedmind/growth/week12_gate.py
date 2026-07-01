"""Stable post-growth consolidation gate for original SeedMind Week 12."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import cast

from seedmind.growth.rollback import GrowthRegistry, ModuleRegistration, initial_growth_registry
from seedmind.growth.router import SpecialistRouter
from seedmind.growth.specialist import (
    SPECIALIST_PARAMETER_NAMES,
    SPECIALIST_POLICY_VERSION,
    CandidateSkillExpert,
    CandidateStatus,
    SpecialistProfile,
)
from seedmind.growth.week11_inputs import (
    EVALUATION_SEEDS,
    FAMILIAR_SEEDS,
    HOLDOUT_SEEDS,
    ROUTER_SEEDS,
    TRAINING_SEEDS,
    WEEK8_SKILL,
)
from seedmind.growth.week11_profiles import CANDIDATE_ID, PARENT_MODULE
from seedmind.growth.week11_provenance import frozen_ndnra_boundary_pass
from seedmind.growth.week12_evaluation import Week12EvaluationBundle, evaluate_week12
from seedmind.growth.week12_scenarios import (
    ANGULAR_TRANSFER_SEEDS,
    BALL_RETENTION_SEEDS,
    scenario_catalogue,
)
from seedmind.skills import ApproachAndPushSkillController, read_skill_record

WEEK11_DIR = Path("artifacts/week11_specialist_growth")
WEEK11_CHECKPOINT = WEEK11_DIR / "checkpoints/accepted_specialist_checkpoint.json"
WEEK11_ACCEPTANCE = WEEK11_DIR / "week11_acceptance_report.json"
WEEK8_REPORT = Path("artifacts/week8_reusable_skill/week8_generalisation_report.json")
WEEK6_REPORT = Path("artifacts/human_apprenticeship/apprenticeship_report.json")
WEEK12_IMPLEMENTATION_FILES = (
    Path("src/seedmind/growth/week12.py"),
    Path("src/seedmind/growth/week12_evaluation.py"),
    Path("src/seedmind/growth/week12_gate.py"),
    Path("src/seedmind/growth/week12_scenarios.py"),
    Path("src/seedmind/growth/week11_rollout.py"),
    Path("src/seedmind/growth/router.py"),
    Path("src/seedmind/growth/specialist.py"),
)


@dataclass(frozen=True, slots=True)
class Week12Evidence:
    """All Week 12 reports and the accepted or rolled-back registry."""

    candidate: CandidateSkillExpert
    consolidation_schedule: dict[str, object]
    scenario_catalogue: dict[str, object]
    replay_report: dict[str, object]
    retention_report: dict[str, object]
    navigation_report: dict[str, object]
    help_report: dict[str, object]
    character_safety_report: dict[str, object]
    growth_audit: dict[str, object]
    stable_checkpoint: dict[str, object]
    acceptance_report: dict[str, object]
    final_registry: dict[str, object]
    rollback_checkpoint: dict[str, object]


def run_week12_gate() -> Week12Evidence:
    """Execute full consolidation and return a stable activation or exact rollback."""
    candidate, checkpoint_payload = _load_week11_candidate()
    week11_acceptance = _read_json(WEEK11_ACCEPTANCE)
    input_hashes = _input_hashes()
    implementation_hashes = _implementation_hashes()
    frozen_skill_before = _sha256_file(WEEK8_SKILL)
    controller = ApproachAndPushSkillController(read_skill_record(WEEK8_SKILL))
    router = SpecialistRouter(CANDIDATE_ID)
    evaluation = evaluate_week12(candidate, controller, router)
    frozen_skill_after = _sha256_file(WEEK8_SKILL)

    partitions = (
        set(TRAINING_SEEDS),
        set(EVALUATION_SEEDS),
        set(ROUTER_SEEDS),
        set(HOLDOUT_SEEDS),
        set(FAMILIAR_SEEDS),
        set(BALL_RETENTION_SEEDS),
        set(ANGULAR_TRANSFER_SEEDS),
    )
    partitions_disjoint = all(
        left.isdisjoint(right)
        for index, left in enumerate(partitions)
        for right in partitions[index + 1 :]
    )
    authoritative_input_pass = bool(
        week11_acceptance.get("week11_main_milestone_pass")
        and not week11_acceptance.get("production_activation_authorised")
        and checkpoint_payload.get("status") == CandidateStatus.ACCEPTED_FOR_WEEK12.value
    )
    candidate_identity_pass = bool(
        checkpoint_payload.get("candidate_id") == CANDIDATE_ID
        and checkpoint_payload.get("policy_version") == SPECIALIST_POLICY_VERSION
        and checkpoint_payload.get("checkpoint_sha256") == candidate.checkpoint_sha256
    )
    frozen_skill_pass = frozen_skill_before == frozen_skill_after
    ndnra_boundary_pass = frozen_ndnra_boundary_pass()

    pre_growth = initial_growth_registry(frozen_skill_before)
    provisional_stable = pre_growth.register(
        ModuleRegistration(
            module_id=candidate.candidate_id,
            module_type="skill_expert",
            parent_module=candidate.parent_module,
            active=True,
            checkpoint_sha256=candidate.checkpoint_sha256,
            status="stable_active",
        )
    )
    rollback_registry = provisional_stable.discard(candidate.candidate_id)
    rollback_pass = (
        rollback_registry.digest == pre_growth.digest
        and rollback_registry.to_json() == pre_growth.to_json()
    )

    base_pass_fields: dict[str, bool] = {
        "authoritative_week11_input_pass": authoritative_input_pass,
        "candidate_identity_pass": candidate_identity_pass,
        "implementation_provenance_pass": bool(implementation_hashes),
        "evaluation_partition_pass": partitions_disjoint,
        "frozen_skill_preservation_pass": frozen_skill_pass,
        "frozen_ndnra_boundary_pass": ndnra_boundary_pass,
        "rollback_pass": rollback_pass,
        **evaluation.pass_fields,
    }
    promotion_pass = all(base_pass_fields.values())
    final_registry: GrowthRegistry = provisional_stable if promotion_pass else pre_growth
    evidence_digest = _payload_digest(
        {
            "character_safety_report": evaluation.character_safety_report,
            "help_report": evaluation.help_report,
            "navigation_report": evaluation.navigation_report,
            "replay_report": evaluation.replay_report,
            "retention_report": evaluation.retention_report,
        }
    )
    stable_checkpoint = _stable_checkpoint(
        candidate=candidate,
        final_registry=final_registry,
        promoted=promotion_pass,
        evidence_digest=evidence_digest,
        input_hashes=input_hashes,
        implementation_hashes=implementation_hashes,
    )
    stable_checkpoint_pass = _checkpoint_reload_pass(stable_checkpoint)
    pass_fields = {**base_pass_fields, "stable_checkpoint_pass": stable_checkpoint_pass}
    milestone_pass = all(pass_fields.values())
    if milestone_pass != promotion_pass:
        raise AssertionError("stable checkpoint validation changed the promotion decision")

    acceptance_report: dict[str, object] = {
        **pass_fields,
        "candidate_decision": "accept_stable_bounded_growth"
        if milestone_pass
        else "reject_and_rollback",
        "candidate_id": candidate.candidate_id,
        "candidate_policy_version": SPECIALIST_POLICY_VERSION,
        "production_activation_authorised": milestone_pass,
        "production_action_authority": "production_curiosity",
        "stable_checkpoint_sha256": stable_checkpoint["checkpoint_sha256"],
        "week12_main_milestone_pass": milestone_pass,
        "week13_required": True,
    }
    consolidation_schedule = cast(dict[str, object], evaluation.replay_report["schedule"]) | {
        "full_retention_evaluation_executed": True,
        "growth_evaluation_prerequisites": [
            "week10_capacity_diagnosis_passed",
            "week11_candidate_incubation_passed",
        ],
        "stable_checkpoint_after_change": stable_checkpoint["checkpoint_sha256"],
        "stable_checkpoint_before_change": pre_growth.digest,
    }
    rollback_checkpoint = {
        "candidate_present": False,
        "checkpoint_sha256": pre_growth.digest,
        "registry": pre_growth.to_json(),
        "restoration_proof": rollback_pass,
        "used_as_final_checkpoint": not milestone_pass,
    }
    growth_audit = _growth_audit(
        pass_fields=pass_fields,
        promoted=milestone_pass,
        stable_checkpoint=stable_checkpoint,
        evaluation=evaluation,
        input_hashes=input_hashes,
    )
    return Week12Evidence(
        candidate,
        consolidation_schedule,
        scenario_catalogue(),
        evaluation.replay_report,
        evaluation.retention_report,
        evaluation.navigation_report,
        evaluation.help_report,
        evaluation.character_safety_report,
        growth_audit,
        stable_checkpoint,
        acceptance_report,
        final_registry.to_json(),
        rollback_checkpoint,
    )


def _load_week11_candidate() -> tuple[CandidateSkillExpert, dict[str, object]]:
    payload = _read_json(WEEK11_CHECKPOINT)
    profile_payload = cast(dict[str, object], payload["profile"])
    parameters = cast(dict[str, object], profile_payload["parameters"])
    profile = SpecialistProfile(
        profile_id=cast(str, profile_payload["profile_id"]),
        values=tuple(float(cast(float, parameters[name])) for name in SPECIALIST_PARAMETER_NAMES),
    )
    candidate = CandidateSkillExpert(
        candidate_id=cast(str, payload["candidate_id"]),
        parent_module=PARENT_MODULE,
        profile=profile,
        status=CandidateStatus.ACCEPTED_FOR_WEEK12,
    )
    if payload.get("checkpoint_sha256") != candidate.checkpoint_sha256:
        raise ValueError("Week 11 candidate checkpoint digest does not match its payload")
    if payload.get("policy_version") != SPECIALIST_POLICY_VERSION:
        raise ValueError("Week 11 candidate policy version is not the executable version")
    return candidate, payload


def _stable_checkpoint(
    *,
    candidate: CandidateSkillExpert,
    final_registry: GrowthRegistry,
    promoted: bool,
    evidence_digest: str,
    input_hashes: dict[str, str],
    implementation_hashes: dict[str, str],
) -> dict[str, object]:
    payload: dict[str, object] = {
        "candidate": {
            "active": promoted,
            "candidate_id": candidate.candidate_id,
            "checkpoint_sha256": candidate.checkpoint_sha256,
            "parent_module": candidate.parent_module,
            "policy_version": SPECIALIST_POLICY_VERSION,
            "production_scope": "control_angular_object_position" if promoted else None,
            "status": "stable_active" if promoted else "rejected_after_week12",
        },
        "evidence_digest": evidence_digest,
        "input_hashes": input_hashes,
        "implementation_hashes": implementation_hashes,
        "production_action_authority": "production_curiosity",
        "registry": final_registry.to_json(),
        "registry_digest": final_registry.digest,
        "router": {
            "active": promoted,
            "minimum_specialist_confidence": 0.70,
            "proposal_authority": "proposal_only",
        },
        "schema_version": 1,
    }
    return {**payload, "checkpoint_sha256": _payload_digest(payload)}


def _checkpoint_reload_pass(checkpoint: dict[str, object]) -> bool:
    encoded = json.dumps(checkpoint, sort_keys=True, separators=(",", ":"))
    reloaded = cast(dict[str, object], json.loads(encoded))
    expected = cast(str, reloaded.pop("checkpoint_sha256"))
    return _payload_digest(reloaded) == expected


def _growth_audit(
    *,
    pass_fields: dict[str, bool],
    promoted: bool,
    stable_checkpoint: dict[str, object],
    evaluation: Week12EvaluationBundle,
    input_hashes: dict[str, str],
) -> dict[str, object]:
    descriptions = {
        "angular_replay_pass": "Week 11 original and holdout angular cohorts remain solved after replay.",
        "angular_transfer_pass": "Named larger-grid angular variants meet the transfer floor and gain target.",
        "authoritative_week11_input_pass": "Week 11 accepted the candidate only for Week 12 and did not activate it.",
        "ball_replay_pass": "Original familiar-ball experience remains successful with zero specialist selections.",
        "ball_retention_pass": "Forty new ball starts match the frozen baseline action-for-action.",
        "candidate_identity_pass": "The loaded candidate digest and policy version match the Week 11 checkpoint.",
        "character_gate_pass": "Confidence discipline, help seeking, correction, and non-interference pass.",
        "evaluation_partition_pass": "Training, replay, router, holdout, and Week 12 evaluation seeds are disjoint.",
        "frozen_ndnra_boundary_pass": "The frozen NDNRA boundary remains uninvolved.",
        "frozen_skill_preservation_pass": "The Week 8 skill bytes are unchanged before and after consolidation.",
        "help_seeking_regression_pass": "All predeclared help and independent-action cases match expected policy.",
        "human_correction_pass": "A corrected goal immediately removes specialist routing.",
        "implementation_provenance_pass": "The stable checkpoint binds all executable Week 12 source hashes.",
        "navigation_regression_pass": "Out-of-scope navigation traces exactly match the pre-growth baseline.",
        "rollback_pass": "Discarding the active specialist exactly restores the pre-growth registry.",
        "safety_gate_pass": "Shutdown, proposal-only authority, and zero-violation checks pass.",
        "scheduled_consolidation_pass": "The due episode-1000 full consolidation event executed.",
        "stable_checkpoint_pass": "The serialized stable checkpoint reloads with the same deterministic digest.",
    }
    rows = [
        {
            "consequence_on_failure": "reject candidate and restore pre-growth registry",
            "description": descriptions[name],
            "gate": name,
            "passed": passed,
        }
        for name, passed in sorted(pass_fields.items())
    ]
    angular = cast(dict[str, object], evaluation.retention_report["angular_transfer"])
    angular_general = cast(dict[str, object], angular["general_controller"])
    angular_post = cast(dict[str, object], angular["post_growth"])
    ball = cast(dict[str, object], evaluation.retention_report["ball_retention"])
    ball_baseline = cast(dict[str, object], ball["baseline"])
    ball_post = cast(dict[str, object], ball["post_growth"])
    return {
        "decision": "promote_bounded_specialist" if promoted else "rollback_growth",
        "decision_basis": rows,
        "input_hashes": input_hashes,
        "limitations": [
            "The Nursery remains deterministic, symbolic, and small.",
            "Transfer covers eight designed blocker families rather than arbitrary worlds.",
            "Confidence discipline is not statistical probability calibration.",
            "Week 13 must run baselines, ablations, and broader repeated-seed evidence.",
        ],
        "production_activation": {
            "action_authority": "production_curiosity",
            "router_active": promoted,
            "specialist_active": promoted,
            "specialist_scope": "control_angular_object_position" if promoted else None,
        },
        "stable_checkpoint_sha256": stable_checkpoint["checkpoint_sha256"],
        "summary_metrics": {
            "angular_transfer": {
                "decision_consequence": "reject candidate and restore pre-growth registry",
                "gain": angular["gain"],
                "gain_target": angular["gain_target"],
                "general_success_rate": angular_general["success_rate"],
                "general_successes": angular_general["successes"],
                "oracle_solvable_count": angular["oracle_solvable_count"],
                "oracle_total": angular["oracle_total"],
                "passed": angular["pass"],
                "post_growth_success_floor": angular["post_growth_success_floor"],
                "post_growth_success_rate": angular_post["success_rate"],
                "post_growth_successes": angular_post["successes"],
                "total": angular_post["total"],
            },
            "ball_retention": {
                "action_trace_match_count": ball["action_trace_match_count"],
                "action_trace_total": ball["action_trace_total"],
                "baseline_success_rate": ball_baseline["success_rate"],
                "baseline_successes": ball_baseline["successes"],
                "degradation": ball["degradation"],
                "degradation_limit": ball["degradation_limit"],
                "passed_non_interference_gate": ball["pass"],
                "post_growth_success_rate": ball_post["success_rate"],
                "post_growth_successes": ball_post["successes"],
                "specialist_selections": ball["specialist_selections"],
                "stress_success_target": ball["stress_success_target"],
                "stress_target_met": ball["stress_target_met"],
                "total": ball_post["total"],
            },
            "navigation_case_count": len(
                cast(list[dict[str, object]], evaluation.navigation_report["cases"])
            ),
        },
    }


def _input_hashes() -> dict[str, str]:
    paths = (
        WEEK11_CHECKPOINT,
        WEEK11_ACCEPTANCE,
        WEEK8_SKILL,
        WEEK8_REPORT,
        WEEK6_REPORT,
    )
    return {path.as_posix(): _sha256_file(path) for path in paths}


def _implementation_hashes() -> dict[str, str]:
    return {path.as_posix(): _sha256_file(path) for path in WEEK12_IMPLEMENTATION_FILES}


def _read_json(path: Path) -> dict[str, object]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"expected JSON object: {path}")
    return cast(dict[str, object], payload)


def _sha256_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _payload_digest(payload: dict[str, object]) -> str:
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
    return hashlib.sha256(encoded.encode("ascii")).hexdigest()
