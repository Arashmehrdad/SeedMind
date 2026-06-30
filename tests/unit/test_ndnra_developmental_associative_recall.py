"""Tests for NDNRA v0.2 Stage 2 associative recall evidence."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    AssociativeRecallControl,
    AssociativeRecallCue,
    AssociativeRecallLink,
    AssociativeRecallLinkKind,
    RecallCostMeasurement,
    build_stage_two_associative_links,
    build_stage_two_associative_state,
    run_associative_recall,
    run_stage_two_associative_recall_acceptance,
)


def _warm_sunny_cue() -> AssociativeRecallCue:
    return AssociativeRecallCue(
        cue_code="cue:warm_sunny_cooling",
        need_code="need:cool",
        current_context_code="context:warm_sunny_room",
        partial_context_codes=("context:sunny_room", "context:warm_room"),
        maximum_depth=3,
    )


def test_stage_two_acceptance_matrix_is_complete_and_zero_authority() -> None:
    evidence = run_stage_two_associative_recall_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.state.sqlite_cognition_operation_count == 0
    assert evidence.state.production_action_authority_violations == 0
    assert evidence.warm_sunny_recall.sqlite_cognition_operation_count == 0
    assert evidence.warm_sunny_recall.external_side_effect_count == 0
    assert evidence.warm_sunny_recall.production_action_authority_violations == 0


def test_need_relevant_experiences_exceed_unrelated_without_merging_identity() -> None:
    evidence = run_stage_two_associative_recall_acceptance()
    unrelated = evidence.warm_sunny_recall.score_for_episode_code(evidence.unrelated_episode_code)
    relevant_scores = [
        evidence.warm_sunny_recall.score_for_episode_code(code)
        for code in evidence.relevant_episode_codes
    ]

    assert min(relevant_scores) > unrelated
    assert len(evidence.state.episodes) == 5
    assert len({episode.episode_id for episode in evidence.state.episodes}) == 5
    assert len({episode.coalition_id for episode in evidence.state.coalitions}) == 5


def test_partial_context_changes_order_and_beats_exact_context_only() -> None:
    evidence = run_stage_two_associative_recall_acceptance()
    controls = {result.control: result for result in evidence.controls}
    exact_context = controls[AssociativeRecallControl.EXACT_CONTEXT_ONLY]

    assert evidence.warm_sunny_recall.activation_order[0] == "episode:cool_sunny_blinds"
    assert evidence.humid_recall.activation_order[0] == "episode:cool_humid_vent"
    assert exact_context.activation_order[0] != evidence.warm_sunny_recall.activation_order[0]
    assert evidence.warm_sunny_recall.dominant_score > exact_context.dominant_score


def test_compatible_multi_experience_coalition_beats_one_winner_control() -> None:
    evidence = run_stage_two_associative_recall_acceptance()
    controls = {result.control: result for result in evidence.controls}
    dominant_codes = {
        activation.episode_code
        for activation in evidence.warm_sunny_recall.activations
        if activation.episode_id in evidence.warm_sunny_recall.dominant_episode_ids
    }

    assert dominant_codes == {"episode:cool_sunny_blinds", "episode:cool_warm_fan"}
    assert len(evidence.warm_sunny_recall.dominant_episode_ids) == 2
    assert len(controls[AssociativeRecallControl.ONE_WINNER_ONLY].dominant_episode_ids) == 1
    assert (
        evidence.warm_sunny_recall.dominant_score
        > controls[AssociativeRecallControl.ONE_WINNER_ONLY].dominant_score
    )


def test_contradictory_experience_remains_available_but_inhibited() -> None:
    evidence = run_stage_two_associative_recall_acceptance()
    controls = {result.control: result for result in evidence.controls}
    contradictory = evidence.warm_sunny_recall.activation_for_episode_code("episode:cool_warm_wait")
    uninhibited = controls[AssociativeRecallControl.INHIBITION_REMOVED].activation_for_episode_code(
        "episode:cool_warm_wait"
    )

    assert contradictory.final_score > evidence.warm_sunny_recall.score_for_episode_code(
        "episode:clean_dirty_wipe"
    )
    assert contradictory.inhibition > 0.0
    assert contradictory.final_score < evidence.warm_sunny_recall.score_for_episode_code(
        "episode:cool_warm_fan"
    )
    assert uninhibited.final_score > contradictory.final_score


def test_partial_cue_beats_shuffled_need_removed_and_context_removed_controls() -> None:
    evidence = run_stage_two_associative_recall_acceptance()
    controls = {result.control: result for result in evidence.controls}

    assert (
        evidence.warm_sunny_recall.dominant_score
        > controls[AssociativeRecallControl.SHUFFLED_LINKS].dominant_score
    )
    assert evidence.warm_sunny_recall.score_for_episode_code("episode:cool_humid_vent") > controls[
        AssociativeRecallControl.NEED_REMOVED
    ].score_for_episode_code("episode:cool_humid_vent")
    assert evidence.warm_sunny_recall.score_for_episode_code(
        "episode:cool_sunny_blinds"
    ) > controls[AssociativeRecallControl.CONTEXT_REMOVED].score_for_episode_code(
        "episode:cool_sunny_blinds"
    )


def test_false_coactivation_and_recall_cost_stay_bounded() -> None:
    evidence = run_stage_two_associative_recall_acceptance()
    first, deeper, dormant = evidence.cost_measurements

    assert (
        evidence.warm_sunny_recall.false_coactivation_rate
        <= evidence.config.false_coactivation_threshold
    )
    assert first.effort_cost < deeper.effort_cost < dormant.effort_cost
    with pytest.raises(ValueError, match="dormancy"):
        RecallCostMeasurement("cost:bad", recall_depth=1, dormancy=1.5, effort_cost=1.0)


def test_stage_two_links_cover_required_association_types_and_reject_bad_links() -> None:
    state = build_stage_two_associative_state()
    links = build_stage_two_associative_links(state)
    target_episode_id = state.episode_by_code("episode:cool_warm_fan").episode_id

    assert {link.kind for link in links} == set(AssociativeRecallLinkKind)
    with pytest.raises(ValueError, match="inhibition links"):
        AssociativeRecallLink(
            AssociativeRecallLinkKind.INHIBITION,
            source_code=target_episode_id,
            target_episode_id=target_episode_id,
            weight=0.1,
            provenance_episode_ids=(target_episode_id,),
        )
    with pytest.raises(ValueError, match="target episode"):
        AssociativeRecallLink(
            AssociativeRecallLinkKind.NEED_TO_EXPERIENCE,
            source_code="need:cool",
            target_episode_id=target_episode_id,
            weight=0.1,
            provenance_episode_ids=("other:episode",),
        )


def test_recall_is_deterministic_and_rejects_invalid_cues_and_mutated_results() -> None:
    first = run_stage_two_associative_recall_acceptance()
    second = run_stage_two_associative_recall_acceptance()

    assert first.evidence_id == second.evidence_id
    assert first.snapshot() == second.snapshot()
    with pytest.raises(ValueError, match="current context"):
        AssociativeRecallCue(
            cue_code="cue:bad",
            need_code="need:cool",
            current_context_code="context:warm_room",
            partial_context_codes=("context:warm_room",),
        )
    with pytest.raises(ValueError, match="production_action_authority_violations"):
        replace(first.warm_sunny_recall, production_action_authority_violations=1)
    with pytest.raises(ValueError, match="must be present"):
        replace(first.warm_sunny_recall, dominant_episode_ids=("missing:episode",))


def test_run_associative_recall_rejects_unencoded_link_targets() -> None:
    state = build_stage_two_associative_state()
    links = build_stage_two_associative_links(state)
    bad_link = replace(
        links[0],
        target_episode_id="missing:episode",
        provenance_episode_ids=("missing:episode",),
    )

    with pytest.raises(ValueError, match="target encoded episodes"):
        run_associative_recall(state, (bad_link, *links[1:]), _warm_sunny_cue())


def test_public_exports_cover_stage_two_associative_recall() -> None:
    exported = set(ndnra.__all__)

    assert "AssociativeRecallConfig" in exported
    assert "AssociativeRecallLinkKind" in exported
    assert "AssociativeRecallResult" in exported
    assert "StageTwoAssociativeRecallEvidence" in exported
    assert "run_stage_two_associative_recall_acceptance" in exported


def test_stage_two_associative_recall_has_no_forbidden_runtime_dependencies() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_associative_recall.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_roots = {"asyncio", "concurrent", "queue", "sqlite3", "threading", "time"}
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module.split(".")[0])

    assert imports.isdisjoint(forbidden_roots)
    assert "seedmind.integration" not in source
    assert "ActionGateway" not in source
    assert "bounded_imagination" not in source
