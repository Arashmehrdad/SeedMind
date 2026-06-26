"""Tests for local eligibility traces and delayed modulatory credit."""

from pathlib import Path

import pytest

from seedmind.research.ndnra import HeatFanWorld, LocalNeuralGraph


def test_delayed_cooling_updates_only_eligible_local_structures() -> None:
    graph = LocalNeuralGraph()
    world = HeatFanWorld()
    graph.reset_episode_traces()

    while not world.state.resolved:
        pulse = world.need_pulse(effort_budget=5)
        source_context = world.state.context
        action = world.teacher_action()
        transition = world.step(action)
        graph.observe_transition(
            need_pulse=pulse,
            source_context=source_context,
            action=action,
            target_context=transition.state.context,
        )
        if transition.need_reduction == 0.0:
            assert graph.synapse("context:sitting_away", "action:stand").weight == 0.0
        else:
            graph.mark_cooling_outcome()
            summary = graph.broadcast_modulatory_signal(transition.need_reduction)

    earliest = graph.synapse("context:sitting_away", "action:stand")
    latest = graph.synapse("context:fan_on", "action:wait")
    irrelevant = graph.synapse("context:sitting_away", "action:activate")

    assert summary.updated_synapse_count == 10
    assert earliest.weight > 0.0
    assert latest.weight > earliest.weight
    assert irrelevant.weight == 0.0
    assert irrelevant.eligibility_trace == 0.0
    assert graph.neuron("action:stand").utility > 0.0
    assert graph.neuron("action:activate").need_compatibility > 0.0


def test_earlier_steps_receive_less_credit_from_trace_decay() -> None:
    graph = LocalNeuralGraph()
    world = HeatFanWorld()
    graph.reset_episode_traces()

    while not world.state.resolved:
        pulse = world.need_pulse(effort_budget=5)
        source = world.state.context
        action = world.teacher_action()
        transition = world.step(action)
        graph.observe_transition(
            need_pulse=pulse,
            source_context=source,
            action=action,
            target_context=transition.state.context,
        )
        if transition.need_reduction > 0.0:
            graph.mark_cooling_outcome()
            graph.broadcast_modulatory_signal(1.0)

    expected_earliest = graph.config.synapse_learning_rate * (0.85**4)
    expected_latest = graph.config.synapse_learning_rate
    assert graph.synapse(
        "context:sitting_away",
        "action:stand",
    ).weight == pytest.approx(expected_earliest)
    assert graph.synapse(
        "context:fan_on",
        "action:wait",
    ).weight == pytest.approx(expected_latest)


def test_prototype_has_no_torch_or_sqlite_cognitive_dependency() -> None:
    package = Path("src/seedmind/research/ndnra")
    source = "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(package.glob("*.py"))
    ).lower()

    assert "import torch" not in source
    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
