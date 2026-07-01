"""Tests for original SeedMind Week 11 specialist growth."""

import filecmp
from functools import lru_cache
from pathlib import Path
from typing import cast

from seedmind.growth.week11 import export_week11_evidence
from seedmind.growth.week11_gate import Week11Evidence, run_week11_gate


@lru_cache(maxsize=1)
def _evidence() -> Week11Evidence:
    return run_week11_gate()


def test_week11_gate_meets_separate_acceptance_fields() -> None:
    evidence = _evidence()
    report = evidence.acceptance_report

    assert report["authoritative_input_pass"] is True
    assert report["implementation_provenance_pass"] is True
    assert report["module_contract_pass"] is True
    assert report["incubation_provenance_pass"] is True
    assert report["evaluation_partition_pass"] is True
    assert report["capability_gain_pass"] is True
    assert report["holdout_generalisation_pass"] is True
    assert report["repeated_seed_evaluation_pass"] is True
    assert report["preliminary_familiar_retention_pass"] is True
    assert report["router_scope_pass"] is True
    assert report["router_fallback_pass"] is True
    assert report["router_property_pass"] is True
    assert report["parameter_budget_pass"] is True
    assert report["rollback_pass"] is True
    assert report["failed_candidate_disposal_pass"] is True
    assert report["frozen_skill_preservation_pass"] is True
    assert report["authority_containment_pass"] is True
    assert report["frozen_ndnra_boundary_pass"] is True
    assert report["week11_main_milestone_pass"] is True
    assert report["production_activation_authorised"] is False
    assert report["candidate_decision"] == "accept_for_week12_retention"


def test_candidate_gain_router_scope_and_familiar_retention() -> None:
    evidence = _evidence()

    assert cast(float, evidence.candidate_evaluation["cube_like_success_gain"]) >= 0.20
    retention = evidence.candidate_evaluation["familiar_ball_preliminary_retention"]
    assert isinstance(retention, dict)
    assert retention["success_rate"] >= 0.90
    holdout = evidence.candidate_evaluation["holdout_generalisation"]
    assert isinstance(holdout, dict)
    candidate_holdout = holdout["candidate"]
    assert isinstance(candidate_holdout, dict)
    assert candidate_holdout["success_rate"] >= 0.80
    assert holdout["gain"] >= 0.20
    incorrect = evidence.router_evaluation["incorrect_routing"]
    assert isinstance(incorrect, dict)
    assert incorrect["general_selected_for_cube_while_specialist_available"] == 0
    assert incorrect["specialist_selected_for_familiar_ball"] == 0
    property_checks = evidence.router_evaluation["property_checks"]
    assert isinstance(property_checks, dict)
    assert property_checks
    assert all(property_checks.values())
    assert evidence.candidate_evaluation["authority_violations"] == 0


def test_parameter_cap_and_exact_failed_candidate_disposal() -> None:
    evidence = _evidence()

    assert evidence.parameter_budget_report["actual_added_parameters"] == 6
    assert evidence.parameter_budget_report["parameter_kind"] == "bounded_policy_scalars"
    assert evidence.parameter_budget_report["cap_violations"] == 0
    assert evidence.rollback_report["exact_restoration_proof"] is True
    disposal = evidence.rollback_report["failed_candidate_disposal"]
    assert isinstance(disposal, dict)
    assert disposal["present_after_discard"] is False
    assert evidence.rollback_report["router_cleanup"] is True
    provenance = evidence.candidate_manifest["creation_provenance"]
    assert isinstance(provenance, dict)
    implementation_hashes = provenance["implementation_hashes"]
    assert isinstance(implementation_hashes, dict)
    assert implementation_hashes
    assert evidence.candidate_manifest["policy_version"] == "1.1.0"
    assert (
        evidence.rollback_report["frozen_skill_sha256_before"]
        == evidence.rollback_report["frozen_skill_sha256_after"]
    )


def test_week11_export_is_deterministic(tmp_path: Path) -> None:
    first = tmp_path / "first"
    second = tmp_path / "second"
    evidence = _evidence()
    first_paths = export_week11_evidence(evidence, first)
    second_paths = export_week11_evidence(evidence, second)

    relative_paths = tuple(path.relative_to(first) for path in first_paths)
    assert relative_paths
    assert relative_paths == tuple(path.relative_to(second) for path in second_paths)
    committed = Path("artifacts/week11_specialist_growth")
    for relative_path in relative_paths:
        assert filecmp.cmp(first / relative_path, second / relative_path, shallow=False)
        assert filecmp.cmp(first / relative_path, committed / relative_path, shallow=False)
    assert not tuple(first.rglob("*.tmp"))
    assert not tuple(second.rglob("*.tmp"))
