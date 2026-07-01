"""Evidence-derived specialist growth gate for original SeedMind Week 11."""

from __future__ import annotations

from dataclasses import dataclass
from typing import cast

import torch

from seedmind.contracts import PrimitiveAction
from seedmind.core import PredictiveCoreConfig, PredictiveSeedCore
from seedmind.environment import NurseryRuntime
from seedmind.growth.rollback import ModuleRegistration, initial_growth_registry
from seedmind.growth.router import SpecialistRouter
from seedmind.growth.specialist import (
    SPECIALIST_POLICY_VERSION,
    CandidateSkillExpert,
    CandidateStatus,
)
from seedmind.growth.week11_evaluation import (
    CUBE_GAIN_TARGET,
    FAMILIAR_RETENTION_FLOOR,
    HOLDOUT_GAIN_TARGET,
    HOLDOUT_SUCCESS_FLOOR,
    evaluate_candidate,
)
from seedmind.growth.week11_inputs import (
    EVALUATION_SEEDS,
    FAMILIAR_SEEDS,
    HOLDOUT_SEEDS,
    ROUTER_SEEDS,
    TRAINING_SEEDS,
    WEEK8_SKILL,
    cube_like_state,
)
from seedmind.growth.week11_profile_comparison import ProfileRow, compare_candidate_profiles
from seedmind.growth.week11_profiles import CANDIDATE_ID, PARENT_MODULE
from seedmind.growth.week11_provenance import (
    authoritative_hashes,
    frozen_ndnra_boundary_pass,
    implementation_hashes,
    validate_week10_proposal,
)
from seedmind.growth.week11_selection import candidate_profiles
from seedmind.perception import SymbolicInputSpec
from seedmind.skills import ApproachAndPushSkillController, read_skill_record

PARAMETER_CAP_RATIO = 0.25


@dataclass(frozen=True, slots=True)
class Week11Evidence:
    candidate: CandidateSkillExpert
    candidate_manifest: dict[str, object]
    incubation_report: dict[str, object]
    candidate_evaluation: dict[str, object]
    router_evaluation: dict[str, object]
    parameter_budget_report: dict[str, object]
    rollback_report: dict[str, object]
    brain_graph: dict[str, object]
    architecture_manifest: dict[str, object]
    acceptance_report: dict[str, object]
    pre_growth_registry: dict[str, object]
    grown_registry: dict[str, object]


def run_week11_gate() -> Week11Evidence:
    """Execute Week 11 comparison, gating, and exact restoration proof."""
    proposal = validate_week10_proposal()
    input_hashes = authoritative_hashes()
    implementation_provenance = implementation_hashes()
    skill_hash_before = input_hashes[WEEK8_SKILL.as_posix()]
    candidate, incubation = compare_candidate_profiles()
    controller = ApproachAndPushSkillController(read_skill_record(WEEK8_SKILL))
    router = SpecialistRouter(CANDIDATE_ID)
    evaluation = evaluate_candidate(candidate, controller, router)

    seed_parameters = _seed_parameter_count()
    added_parameters = candidate.added_parameter_count
    parameter_cap = int(seed_parameters * PARAMETER_CAP_RATIO)
    parameter_pass = added_parameters <= parameter_cap
    profiles = cast(list[ProfileRow], incubation["profiles"])
    parameter_report: dict[str, object] = {
        "actual_added_parameters": added_parameters,
        "candidate_parameter_bytes_float32": added_parameters * 4,
        "parameter_kind": "bounded_policy_scalars",
        "cap_ratio": PARAMETER_CAP_RATIO,
        "cap_violations": int(not parameter_pass),
        "compute_and_memory_cost": {
            "holdout_episode_count": len(HOLDOUT_SEEDS) * 2,
            "incubation_episode_count": sum(len(row["episodes"]) for row in profiles),
            "parameter_bytes": added_parameters * 4,
        },
        "parameter_cap": parameter_cap,
        "resource_efficiency": {
            "cube_gain_per_added_parameter": (evaluation.cube_gain / max(1, added_parameters)),
            "within_cap": parameter_pass,
        },
        "seed_parameter_count": seed_parameters,
    }

    pre_growth = initial_growth_registry(skill_hash_before)
    failed_candidate = CandidateSkillExpert(
        candidate_id="skill.expert.angular_push.failed_direct.v1",
        parent_module=PARENT_MODULE,
        profile=candidate_profiles()[0],
        status=CandidateStatus.REJECTED,
    )
    failed_registered = pre_growth.register(_registration(failed_candidate, active=False))
    restored = failed_registered.discard(failed_candidate.candidate_id)
    exact_restoration = (
        restored.digest == pre_growth.digest and restored.to_json() == pre_growth.to_json()
    )
    skill_hash_after = authoritative_hashes()[WEEK8_SKILL.as_posix()]
    rollback_report: dict[str, object] = {
        "discarded_candidate_id": failed_candidate.candidate_id,
        "exact_restoration_proof": exact_restoration,
        "failed_candidate_disposal": {
            "candidate_checkpoint_sha256": failed_candidate.checkpoint_sha256,
            "candidate_status": failed_candidate.status.value,
            "present_after_discard": any(
                module.module_id == failed_candidate.candidate_id for module in restored.modules
            ),
        },
        "frozen_skill_sha256_after": skill_hash_after,
        "frozen_skill_sha256_before": skill_hash_before,
        "module_registry_cleanup": restored.to_json(),
        "post_discard_registry_digest": restored.digest,
        "pre_growth_checkpoint": pre_growth.to_json(),
        "pre_growth_checkpoint_digest": pre_growth.digest,
        "router_cleanup": not restored.router_registered,
    }

    direct_rate = profiles[0]["success_rate"]
    selected_rate = max(row["success_rate"] for row in profiles)
    selected_checkpoint = cast(str, incubation["selected_checkpoint_sha256"])
    evaluation_partitions = (
        set(TRAINING_SEEDS),
        set(EVALUATION_SEEDS),
        set(ROUTER_SEEDS),
        set(HOLDOUT_SEEDS),
        set(FAMILIAR_SEEDS),
    )
    partitions_disjoint = all(
        left.isdisjoint(right)
        for index, left in enumerate(evaluation_partitions)
        for right in evaluation_partitions[index + 1 :]
    )
    repeated_seed_summary = cast(
        dict[str, object], evaluation.candidate_report["repeated_seed_summary"]
    )
    pass_fields: dict[str, bool] = {
        "authoritative_input_pass": bool(input_hashes) and bool(proposal.get("proposal_id")),
        "implementation_provenance_pass": bool(implementation_provenance),
        "module_contract_pass": added_parameters == 6,
        "incubation_provenance_pass": (
            selected_rate > direct_rate
            and selected_checkpoint == candidate.checkpoint_sha256
            and candidate.profile.profile_id != profiles[0]["profile"]["profile_id"]
        ),
        "evaluation_partition_pass": partitions_disjoint,
        "capability_gain_pass": evaluation.cube_gain >= CUBE_GAIN_TARGET,
        "holdout_generalisation_pass": (
            evaluation.holdout_candidate_rate >= HOLDOUT_SUCCESS_FLOOR
            and evaluation.holdout_gain >= HOLDOUT_GAIN_TARGET
        ),
        "repeated_seed_evaluation_pass": (int(cast(int, repeated_seed_summary["seed_count"])) >= 5),
        "preliminary_familiar_retention_pass": (
            evaluation.familiar_rate >= FAMILIAR_RETENTION_FLOOR
        ),
        "router_scope_pass": evaluation.router_scope_pass,
        "router_fallback_pass": evaluation.router_fallback_pass,
        "router_property_pass": evaluation.router_property_pass,
        "parameter_budget_pass": parameter_pass,
        "rollback_pass": exact_restoration,
        "failed_candidate_disposal_pass": not any(
            module.module_id == failed_candidate.candidate_id for module in restored.modules
        ),
        "frozen_skill_preservation_pass": skill_hash_before == skill_hash_after,
        "authority_containment_pass": evaluation.authority_violations == 0,
        "frozen_ndnra_boundary_pass": frozen_ndnra_boundary_pass(),
    }
    milestone_pass = all(pass_fields.values())
    final_status = (
        CandidateStatus.ACCEPTED_FOR_WEEK12 if milestone_pass else CandidateStatus.REJECTED
    )
    final_candidate = candidate.with_status(final_status)
    grown = pre_growth.register(_registration(final_candidate, active=False))

    candidate_manifest = {
        "candidate_id": CANDIDATE_ID,
        "creation_provenance": {
            "authoritative_input_hashes": input_hashes,
            "implementation_hashes": implementation_provenance,
            "growth_proposal_id": proposal["proposal_id"],
            "selected_incubation_checkpoint": selected_checkpoint,
        },
        "inputs": [
            "latent_state",
            "current_goal",
            "relevant_memory_summary",
            "available_actions",
        ],
        "outputs": [
            "action_proposal",
            "confidence",
            "expected_result",
            "predicted_goal_progress",
            "abstain",
        ],
        "parameter_count": added_parameters,
        "policy_version": SPECIALIST_POLICY_VERSION,
        "parent_module": PARENT_MODULE,
        "production_authority": False,
        "status": final_candidate.status.value,
        "training_configuration": {
            "profile": final_candidate.profile.to_json(),
            "training_method": "bounded_grounded_parameter_profile_comparison",
            "training_seeds": list(TRAINING_SEEDS),
        },
        "evaluation_configuration": {
            "authoritative_cube_seeds": list(EVALUATION_SEEDS),
            "familiar_retention_seeds": list(FAMILIAR_SEEDS),
            "holdout_geometry_count": 7,
            "holdout_seeds": list(HOLDOUT_SEEDS),
            "router_seeds": list(ROUTER_SEEDS),
        },
        "type": "skill_expert",
    }
    acceptance: dict[str, object] = {
        **pass_fields,
        "candidate_decision": ("accept_for_week12_retention" if milestone_pass else "reject"),
        "candidate_id": CANDIDATE_ID,
        "cube_like_success_gain": evaluation.cube_gain,
        "familiar_ball_preliminary_success_rate": evaluation.familiar_rate,
        "holdout_cube_success_gain": evaluation.holdout_gain,
        "holdout_cube_success_rate": evaluation.holdout_candidate_rate,
        "production_activation_authorised": False,
        "week11_main_milestone_pass": milestone_pass,
        "week12_required": True,
    }
    graph = {
        "edges": [
            {"from": "predictive_seed_core", "to": "specialist_router"},
            {"from": "specialist_router", "to": PARENT_MODULE},
            {"from": "specialist_router", "to": CANDIDATE_ID},
            {"from": PARENT_MODULE, "relation": "parent", "to": CANDIDATE_ID},
        ],
        "nodes": [
            {
                "active_in_sandbox": True,
                "id": "predictive_seed_core",
                "production_active": True,
                "type": "shared_state",
            },
            {
                "active_in_sandbox": milestone_pass,
                "id": "specialist_router",
                "production_active": False,
                "type": "proposal_router",
            },
            {
                "active_in_sandbox": True,
                "id": PARENT_MODULE,
                "production_active": True,
                "type": "general_controller",
            },
            {
                "active_in_sandbox": milestone_pass,
                "id": CANDIDATE_ID,
                "production_active": False,
                "type": "temporary_skill_expert",
            },
        ],
        "production_action_authority": "production_curiosity",
    }
    architecture = {
        "accepted_candidate_checkpoint_sha256": final_candidate.checkpoint_sha256,
        "checkpoint_references": {
            "accepted_candidate": "checkpoints/accepted_specialist_checkpoint.json",
            "accepted_registry": "checkpoints/accepted_candidate_registry.json",
            "pre_growth_registry": "checkpoints/pre_growth_registry.json",
        },
        "general_controller": {
            "active": True,
            "checkpoint_sha256": skill_hash_before,
            "module_id": PARENT_MODULE,
            "production_active": True,
        },
        "module_relationships": graph["edges"],
        "parameter_totals": {
            "added_specialist_parameters": added_parameters,
            "combined_seed_and_specialist_parameters": seed_parameters + added_parameters,
            "seed_parameters": seed_parameters,
        },
        "registry": grown.to_json(),
        "router": {"active_in_sandbox": milestone_pass, "production_active": False},
        "temporary_specialist": {
            "active_in_sandbox": milestone_pass,
            "module_id": CANDIDATE_ID,
            "policy_version": SPECIALIST_POLICY_VERSION,
            "production_active": False,
            "status": final_candidate.status.value,
        },
    }
    rollback_report["accepted_candidate_registration_digest"] = grown.digest
    return Week11Evidence(
        final_candidate,
        candidate_manifest,
        incubation,
        evaluation.candidate_report,
        evaluation.router_report,
        parameter_report,
        rollback_report,
        graph,
        architecture,
        acceptance,
        pre_growth.to_json(),
        grown.to_json(),
    )


def _registration(candidate: CandidateSkillExpert, *, active: bool) -> ModuleRegistration:
    return ModuleRegistration(
        candidate.candidate_id,
        "skill_expert",
        candidate.parent_module,
        active,
        candidate.checkpoint_sha256,
        candidate.status.value,
    )


def _seed_parameter_count() -> int:
    observation = NurseryRuntime(cube_like_state(700), "week11-parameter-count").observe()
    spec = SymbolicInputSpec(
        sensor_size=len(observation.sensor_values),
        human_signal_size=len(observation.human_signal),
        resource_state_size=len(observation.resource_state),
    )
    torch.manual_seed(11)
    core = PredictiveSeedCore(
        PredictiveCoreConfig(
            observation_input_size=spec.input_size,
            sensor_size=spec.sensor_size,
            action_count=len(PrimitiveAction),
        )
    )
    return sum(parameter.numel() for parameter in core.parameters())
