"""Tests for NDNRA v0.2 Stage 1 recurrent experiential substrate."""

from __future__ import annotations

import ast
from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research import ndnra
from seedmind.research.ndnra import (
    DevelopmentalExperienceEpisode,
    DevelopmentalNetworkConfig,
    create_developmental_network_state,
    encode_developmental_episode,
    run_stage_one_substrate_acceptance,
)


def _episode(code: str = "episode:test") -> DevelopmentalExperienceEpisode:
    return DevelopmentalExperienceEpisode(
        episode_code=code,
        context_code="context:test",
        action_code="action:test",
        outcome_code="outcome:test",
        feature_codes=("action:test", "context:test", "need:test"),
        provenance_event_id=f"real:{code}",
    )


def test_stage_one_acceptance_matrix_is_complete_and_zero_authority() -> None:
    evidence = run_stage_one_substrate_acceptance()

    assert set(evidence.pass_gate_matrix().values()) == {True}
    assert set(evidence.completion_matrix().values()) == {"implemented_and_evidenced"}
    assert evidence.state.structural_neuron_creation_count == 0
    assert evidence.state.sqlite_cognition_operation_count == 0
    assert evidence.target_replay.sqlite_cognition_operation_count == 0
    assert evidence.target_replay.production_action_authority_violations == 0


def test_overlapping_episodes_share_neurons_without_merging_identity_or_outcome() -> None:
    evidence = run_stage_one_substrate_acceptance()
    first = evidence.state.coalition_for_episode(evidence.overlapping_episode_ids[0])
    second = evidence.state.coalition_for_episode(evidence.overlapping_episode_ids[1])
    first_episode = next(
        episode for episode in evidence.state.episodes if episode.episode_id == first.episode_id
    )
    second_episode = next(
        episode for episode in evidence.state.episodes if episode.episode_id == second.episode_id
    )

    assert set(first.neuron_ids) & set(second.neuron_ids)
    assert first.coalition_id != second.coalition_id
    assert first_episode.episode_id != second_episode.episode_id
    assert first_episode.outcome_code != second_episode.outcome_code
    assert first_episode.context_code == second_episode.context_code


def test_replay_activates_target_coalition_more_than_unrelated() -> None:
    evidence = run_stage_one_substrate_acceptance()

    target_score = evidence.target_replay.score_for(evidence.target_replay.target_episode_id)
    unrelated_score = evidence.target_replay.score_for(evidence.unrelated_episode_id)

    assert evidence.target_replay.settled
    assert (
        evidence.target_replay.settled_cycle_count <= evidence.state.config.maximum_settling_cycles
    )
    assert target_score > unrelated_score
    assert len(evidence.target_replay.trace) <= evidence.state.config.maximum_settling_cycles + 1


def test_contradictory_contexts_create_inhibitory_connections_without_erasing_details() -> None:
    evidence = run_stage_one_substrate_acceptance()
    inhibitory = tuple(
        connection for connection in evidence.state.connections if connection.inhibitory
    )
    outcomes = {episode.outcome_code for episode in evidence.state.episodes}

    assert inhibitory
    assert {"outcome:cooler", "outcome:warmer"}.issubset(outcomes)
    assert all(connection.weight < 0.0 for connection in inhibitory)


def test_fixed_seed_reconstructs_same_state_and_different_seed_changes_it() -> None:
    first = run_stage_one_substrate_acceptance(DevelopmentalNetworkConfig(seed=19)).state
    second = run_stage_one_substrate_acceptance(DevelopmentalNetworkConfig(seed=19)).state
    different = run_stage_one_substrate_acceptance(DevelopmentalNetworkConfig(seed=23)).state

    assert first.state_id == second.state_id
    assert first.state_id != different.state_id


def test_substrate_rejects_structural_neuron_creation_and_full_pool_coalitions() -> None:
    with pytest.raises(ValueError, match="coalition_size"):
        DevelopmentalNetworkConfig(neuron_count=6, coalition_size=6)

    state = create_developmental_network_state(DevelopmentalNetworkConfig(neuron_count=12))
    encoded = encode_developmental_episode(state, _episode())

    assert len(encoded.neurons) == len(state.neurons)
    assert all(
        len(coalition.neuron_ids) < encoded.config.neuron_count for coalition in encoded.coalitions
    )
    with pytest.raises(ValueError, match="structural_neuron_creation_count"):
        replace(encoded, structural_neuron_creation_count=1)


def test_episode_encoding_is_deterministic_and_duplicate_safe() -> None:
    state = create_developmental_network_state()
    episode = _episode()
    encoded_once = encode_developmental_episode(state, episode)
    encoded_twice = encode_developmental_episode(create_developmental_network_state(), episode)

    assert encoded_once.state_id == encoded_twice.state_id
    with pytest.raises(ValueError, match="already encoded"):
        encode_developmental_episode(encoded_once, episode)
    with pytest.raises(ValueError, match="feature_codes must be sorted"):
        DevelopmentalExperienceEpisode(
            episode_code="episode:bad",
            context_code="context:test",
            action_code="action:test",
            outcome_code="outcome:test",
            feature_codes=("need:test", "action:test"),
            provenance_event_id="real:bad",
        )


def test_public_exports_cover_stage_one_substrate() -> None:
    exported = set(ndnra.__all__)

    assert "DevelopmentalNetworkConfig" in exported
    assert "DevelopmentalNetworkState" in exported
    assert "StageOneSubstrateEvidence" in exported
    assert "run_stage_one_substrate_acceptance" in exported
    assert "replay_developmental_episode" in exported


def test_developmental_network_has_no_forbidden_runtime_dependencies() -> None:
    module_path = (
        Path(__file__).parents[2]
        / "src"
        / "seedmind"
        / "research"
        / "ndnra"
        / "developmental_network.py"
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
