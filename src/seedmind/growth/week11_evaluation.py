"""Repeated-seed candidate and router evaluation for SeedMind Week 11."""

from dataclasses import dataclass

from seedmind.contracts import PrimitiveAction
from seedmind.environment import NurseryRuntime
from seedmind.growth.router import SpecialistRouter
from seedmind.growth.specialist import CandidateSkillExpert, ExpertModuleOutput
from seedmind.growth.week11_inputs import (
    EVALUATION_SEEDS,
    FAMILIAR_SEEDS,
    HOLDOUT_SEEDS,
    ROUTER_SEEDS,
    cube_like_holdout_state,
    cube_like_state,
)
from seedmind.growth.week11_metrics import rollout_summary, success_rate
from seedmind.growth.week11_profiles import CANDIDATE_ID, PARENT_MODULE
from seedmind.growth.week11_rollout import (
    abstaining_output,
    build_module_input,
    run_general,
    run_routed,
    run_specialist,
)
from seedmind.skills import ApproachAndPushSkillController, Week8ScenarioFactory

CUBE_GAIN_TARGET = 0.20
FAMILIAR_RETENTION_FLOOR = 0.90
HOLDOUT_SUCCESS_FLOOR = 0.80
HOLDOUT_GAIN_TARGET = 0.20


@dataclass(frozen=True, slots=True)
class EvaluationBundle:
    candidate_report: dict[str, object]
    router_report: dict[str, object]
    cube_gain: float
    familiar_rate: float
    holdout_candidate_rate: float
    holdout_gain: float
    authority_violations: int
    router_scope_pass: bool
    router_fallback_pass: bool
    router_property_pass: bool


def evaluate_candidate(
    candidate: CandidateSkillExpert,
    controller: ApproachAndPushSkillController,
    router: SpecialistRouter,
) -> EvaluationBundle:
    general = tuple(
        run_general(
            cube_like_state(seed),
            seed,
            f"week11-general-cube-{seed}",
            controller,
        )
        for seed in EVALUATION_SEEDS
    )
    specialist = tuple(
        run_specialist(
            cube_like_state(seed),
            seed,
            f"week11-candidate-cube-{seed}",
            candidate,
        )
        for seed in EVALUATION_SEEDS
    )
    holdout_general = tuple(
        run_general(
            cube_like_holdout_state(seed),
            seed,
            f"week11-general-holdout-{seed}",
            controller,
        )
        for seed in HOLDOUT_SEEDS
    )
    holdout_specialist = tuple(
        run_specialist(
            cube_like_holdout_state(seed),
            seed,
            f"week11-candidate-holdout-{seed}",
            candidate,
        )
        for seed in HOLDOUT_SEEDS
    )
    routed_cube = tuple(
        run_routed(
            cube_like_state(seed),
            seed,
            f"week11-router-cube-{seed}",
            "control_angular_object_position",
            controller,
            candidate,
            router,
        )
        for seed in ROUTER_SEEDS
    )
    factory = Week8ScenarioFactory()
    familiar = tuple(
        run_routed(
            factory.create(seed).initial_state,
            seed,
            f"week11-router-familiar-{seed}",
            "control_familiar_object_position",
            controller,
            candidate,
            router,
        )
        for seed in FAMILIAR_SEEDS
    )
    cube_gain = success_rate(specialist) - success_rate(general)
    familiar_rate = success_rate(familiar)
    holdout_candidate_rate = success_rate(holdout_specialist)
    holdout_gain = holdout_candidate_rate - success_rate(holdout_general)
    cube_specialist = sum(
        module == CANDIDATE_ID for record in routed_cube for module in record.selected_modules
    )
    cube_general = sum(
        module == PARENT_MODULE for record in routed_cube for module in record.selected_modules
    )
    familiar_specialist = sum(
        module == CANDIDATE_ID for record in familiar for module in record.selected_modules
    )
    familiar_general = sum(
        module == PARENT_MODULE for record in familiar for module in record.selected_modules
    )
    general_stub = ExpertModuleOutput(
        PrimitiveAction.MOVE_FORWARD,
        0.75,
        "general_stub",
        0.10,
        False,
        "router_property_general",
    )
    specialist_stub = ExpertModuleOutput(
        PrimitiveAction.MOVE_FORWARD,
        0.95,
        "specialist_stub",
        0.20,
        False,
        "router_property_specialist",
    )
    low_confidence_stub = ExpertModuleOutput(
        PrimitiveAction.MOVE_FORWARD,
        0.69,
        "specialist_stub",
        0.20,
        False,
        "router_property_low_confidence",
    )
    unregistered = router.route(
        general_proposal=general_stub,
        specialist_proposal=specialist_stub,
        specialist_registered=False,
        specialist_active=True,
    )
    inactive = router.route(
        general_proposal=general_stub,
        specialist_proposal=specialist_stub,
        specialist_registered=True,
        specialist_active=False,
    )
    below_threshold = router.route(
        general_proposal=general_stub,
        specialist_proposal=low_confidence_stub,
        specialist_registered=True,
        specialist_active=True,
    )
    mislabeled_round_runtime = NurseryRuntime(
        factory.create(FAMILIAR_SEEDS[0]).initial_state,
        "week11-router-mislabeled-round",
    )
    mislabeled_round_proposal = candidate.propose(
        build_module_input(mislabeled_round_runtime, "control_angular_object_position")
    )
    mislabeled_round = router.route(
        general_proposal=general_stub,
        specialist_proposal=mislabeled_round_proposal,
        specialist_registered=True,
        specialist_active=True,
    )
    explicit_abstention = router.route(
        general_proposal=abstaining_output("general_out_of_scope"),
        specialist_proposal=abstaining_output("specialist_out_of_scope"),
        specialist_registered=True,
        specialist_active=True,
    )
    property_decisions = (
        unregistered,
        inactive,
        below_threshold,
        mislabeled_round,
        explicit_abstention,
    )
    router_property_checks = {
        "all_modules_abstain": explicit_abstention.abstained,
        "below_threshold_falls_back": below_threshold.selected_module == PARENT_MODULE,
        "inactive_specialist_cannot_activate": inactive.selected_module == PARENT_MODULE,
        "mislabeled_round_abstains": (
            mislabeled_round_proposal.abstain and mislabeled_round.selected_module == PARENT_MODULE
        ),
        "unregistered_specialist_cannot_activate": unregistered.selected_module == PARENT_MODULE,
    }
    router_property_pass = all(router_property_checks.values())
    authority_violations = sum(
        record.authority_violations
        for record in (
            *general,
            *specialist,
            *holdout_general,
            *holdout_specialist,
            *routed_cube,
            *familiar,
        )
    ) + sum(int(decision.action_authority_violation) for decision in property_decisions)
    candidate_report = {
        "authority_violations": authority_violations,
        "candidate": rollout_summary(specialist),
        "cube_like_success_gain": cube_gain,
        "evaluation_seeds": list(EVALUATION_SEEDS),
        "familiar_ball_preliminary_retention": {
            "floor": FAMILIAR_RETENTION_FLOOR,
            "seeds": list(FAMILIAR_SEEDS),
            "success_rate": familiar_rate,
        },
        "general_controller": rollout_summary(general),
        "holdout_generalisation": {
            "candidate": rollout_summary(holdout_specialist),
            "candidate_success_floor": HOLDOUT_SUCCESS_FLOOR,
            "general_controller": rollout_summary(holdout_general),
            "gain": holdout_gain,
            "gain_target": HOLDOUT_GAIN_TARGET,
            "seeds": list(HOLDOUT_SEEDS),
        },
        "repeated_seed_summary": {
            "candidate_successes": sum(record.success for record in specialist),
            "general_successes": sum(record.success for record in general),
            "seed_count": len(EVALUATION_SEEDS),
        },
        "target_margin": CUBE_GAIN_TARGET,
    }
    router_report = {
        "abstentions": int(explicit_abstention.abstained),
        "cube_episodes": [record.to_json() for record in routed_cube],
        "fallback_behaviour": {
            "familiar_fallback_count": sum(record.fallback_count for record in familiar),
            "general_available_after_specialist_abstention": familiar_general > 0,
        },
        "general_controller_selections": cube_general + familiar_general,
        "incorrect_routing": {
            "general_selected_for_cube_while_specialist_available": cube_general,
            "specialist_selected_for_familiar_ball": familiar_specialist,
        },
        "property_checks": router_property_checks,
        "routing_inputs": [
            "latent_state",
            "current_goal",
            "relevant_memory_summary",
            "available_actions",
        ],
        "specialist_selections": cube_specialist + familiar_specialist,
        "familiar_episodes": [record.to_json() for record in familiar],
    }
    return EvaluationBundle(
        candidate_report,
        router_report,
        cube_gain,
        familiar_rate,
        holdout_candidate_rate,
        holdout_gain,
        authority_violations,
        cube_specialist > 0 and cube_general == 0 and familiar_specialist == 0,
        familiar_general > 0 and explicit_abstention.abstained,
        router_property_pass,
    )
