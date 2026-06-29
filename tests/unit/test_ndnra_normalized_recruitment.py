"""Focused tests for normalized competing recruitment."""

from dataclasses import replace
from pathlib import Path

import pytest

from seedmind.research.ndnra import (
    HeatAction,
    HeatContext,
    LocalNeuralGraph,
    NeedPulse,
)
from seedmind.research.ndnra.normalized_recruitment import (
    OrderedLocalIncomingContribution,
    normalize_local_incoming_support,
)


def test_one_positive_contributor_matches_raw_support() -> None:
    evidence = normalize_local_incoming_support(
        target_neuron_id="action:stand",
        ordered_contributions=(
            OrderedLocalIncomingContribution(
                source_id="context:sitting_away", local_contribution=0.66
            ),
        ),
    )

    assert evidence.raw_positive_sum == 0.66
    assert evidence.positive_contributor_count == 1
    assert evidence.maximum_local_contribution == 0.66
    assert evidence.normalized_support == 0.66
    assert evidence.bounded


def test_zero_and_negative_contributors_do_not_inflate_support() -> None:
    evidence = normalize_local_incoming_support(
        target_neuron_id="action:walk",
        ordered_contributions=(
            OrderedLocalIncomingContribution(source_id="context:at_fan", local_contribution=0.25),
            OrderedLocalIncomingContribution(
                source_id="context:sitting_away", local_contribution=-0.40
            ),
            OrderedLocalIncomingContribution(
                source_id="context:standing_away", local_contribution=0.0
            ),
        ),
    )

    assert evidence.raw_positive_sum == 0.25
    assert evidence.positive_contributor_count == 1
    assert evidence.maximum_local_contribution == 0.25
    assert evidence.normalized_support == 0.25
    assert evidence.bounded


def test_duplicated_weaker_irrelevant_fan_in_cannot_beat_stronger_single_support() -> None:
    stronger = normalize_local_incoming_support(
        target_neuron_id="action:stand",
        ordered_contributions=(
            OrderedLocalIncomingContribution(
                source_id="context:sitting_away",
                local_contribution=0.80,
            ),
        ),
    )
    duplicated_weaker = normalize_local_incoming_support(
        target_neuron_id="action:activate",
        ordered_contributions=(
            OrderedLocalIncomingContribution(
                source_id="context:at_fan",
                local_contribution=0.40,
            ),
            OrderedLocalIncomingContribution(
                source_id="context:sitting_away",
                local_contribution=0.40,
            ),
            OrderedLocalIncomingContribution(
                source_id="context:standing_away",
                local_contribution=0.40,
            ),
        ),
    )

    assert duplicated_weaker.raw_positive_sum > stronger.raw_positive_sum
    assert duplicated_weaker.positive_contributor_count == 3
    assert duplicated_weaker.normalized_support == pytest.approx(0.40)
    assert stronger.normalized_support == pytest.approx(0.80)
    assert stronger.normalized_support > duplicated_weaker.normalized_support


def test_network_recall_uses_normalized_local_support() -> None:
    graph = LocalNeuralGraph()
    graph.synapse("context:sitting_away", "action:stand").weight = 0.90
    graph.synapse("context:sitting_away", "action:activate").weight = 0.40

    recall = graph.recall_action_with_normalization_evidence(
        need_pulse=NeedPulse(
            need_code="reduce_temperature",
            intensity=1.0,
            urgency=1.0,
            effort_budget=1,
        ),
        context=HeatContext.SITTING_AWAY,
        maximum_depth=1,
    )

    action_evidence = {
        item.target_neuron_id: item
        for item in recall.normalization_evidence.depth_evidence[0].neuron_evidence
        if item.target_neuron_id.startswith("action:")
    }
    assert action_evidence["action:stand"].normalized_support == 0.90
    assert action_evidence["action:activate"].normalized_support == 0.40
    assert recall.recall_result.selected_action is HeatAction.STAND


def test_equal_normalized_supports_remain_deterministic() -> None:
    graph = LocalNeuralGraph()
    graph.synapse("context:sitting_away", "action:stand").weight = 0.80
    graph.synapse("context:sitting_away", "action:walk").weight = 0.80

    recall = graph.recall_action(
        need_pulse=NeedPulse(
            need_code="reduce_temperature",
            intensity=1.0,
            urgency=1.0,
            effort_budget=1,
        ),
        context=HeatContext.SITTING_AWAY,
        maximum_depth=1,
    )

    assert recall.selected_action is HeatAction.STAND


def test_normalization_evidence_is_bounded_and_ordered() -> None:
    graph = LocalNeuralGraph()
    graph.synapse("context:sitting_away", "action:stand").weight = 0.90

    result = graph.recall_action_with_normalization_evidence(
        need_pulse=NeedPulse(
            need_code="reduce_temperature",
            intensity=1.0,
            urgency=1.0,
            effort_budget=1,
        ),
        context=HeatContext.SITTING_AWAY,
        maximum_depth=1,
    )

    stand_evidence = next(
        item
        for item in result.normalization_evidence.depth_evidence[0].neuron_evidence
        if item.target_neuron_id == "action:stand"
    )
    assert result.normalization_evidence.bounded
    assert stand_evidence.bounded
    assert tuple(item.source_id for item in stand_evidence.ordered_contributions) == (
        "context:at_fan",
        "context:cooled",
        "context:fan_on",
        "context:reaching_switch",
        "context:sitting_away",
        "context:standing_away",
    )
    assert stand_evidence.raw_positive_sum == 0.90
    assert stand_evidence.positive_contributor_count == 1
    assert stand_evidence.maximum_local_contribution == 0.90
    assert stand_evidence.normalized_support == 0.90


def test_unsorted_or_tampered_normalization_evidence_is_rejected() -> None:
    with pytest.raises(ValueError, match="unique sorted"):
        normalize_local_incoming_support(
            target_neuron_id="action:walk",
            ordered_contributions=(
                OrderedLocalIncomingContribution("context:standing_away", 0.40),
                OrderedLocalIncomingContribution("context:sitting_away", 0.60),
            ),
        )

    evidence = normalize_local_incoming_support(
        target_neuron_id="action:walk",
        ordered_contributions=(OrderedLocalIncomingContribution("context:sitting_away", 0.60),),
    )
    with pytest.raises(ValueError, match="normalized_support"):
        replace(evidence, normalized_support=0.90)


def test_normalized_recruitment_has_no_forbidden_runtime_dependencies() -> None:
    source = "\n".join(
        path.read_text(encoding="ascii").lower()
        for path in (
            Path("src/seedmind/research/ndnra/normalized_recruitment.py"),
            Path("src/seedmind/research/ndnra/network.py"),
        )
    )

    for forbidden in (
        "import sqlite3",
        "seedmind.integration",
        "asyncio",
        "threading",
        "subprocess",
        "schedule(",
        "execute(",
        "recommend(",
        "production_action_authority",
    ):
        assert forbidden not in source


def test_evidence_api_matches_recall_action_result_and_stays_bounded() -> None:
    graph = LocalNeuralGraph()
    train_need = NeedPulse(
        need_code="reduce_temperature",
        intensity=1.0,
        urgency=1.0,
        effort_budget=3,
    )
    graph.synapse("context:sitting_away", "action:stand").weight = 0.80

    recall_only = graph.recall_action(
        need_pulse=train_need,
        context=HeatContext.SITTING_AWAY,
        maximum_depth=1,
    )
    recall_with_evidence = graph.recall_action_with_normalization_evidence(
        need_pulse=train_need,
        context=HeatContext.SITTING_AWAY,
        maximum_depth=1,
    )

    assert recall_with_evidence.recall_result == recall_only
    assert recall_with_evidence.recall_result.propagation_cycles == 1
    assert recall_with_evidence.recall_result.neuron_evaluations == 11
    assert len(recall_with_evidence.normalization_evidence.depth_evidence) == 1
    assert recall_with_evidence.normalization_evidence.bounded
