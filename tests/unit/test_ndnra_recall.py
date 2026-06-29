"""Tests for need-driven recruitment, dormancy, and effort-based recall."""

from seedmind.research.ndnra import (
    GrowthPressure,
    HeatAction,
    HeatContext,
    LocalNeuralGraph,
    NeedPulse,
    evaluate_recall,
    run_ndnra_heat_fan_experiment,
    train_teacher_demonstrations,
)


def test_untrained_graph_cannot_reconstruct_cooling_chain() -> None:
    graph = LocalNeuralGraph()
    result = evaluate_recall(graph, maximum_depth=5)

    assert not result.success
    assert result.actions == ()
    assert result.failed_context is not None


def test_dormant_memory_requires_deeper_recall_and_resolves_need() -> None:
    graph = LocalNeuralGraph()
    train_teacher_demonstrations(graph, demonstration_count=6)
    neuron_ids_before = tuple(neuron.neuron_id for neuron in graph.neurons)
    synapse_ids_before = tuple(synapse.synapse_id for synapse in graph.synapses)
    graph.enter_dormancy(0.80)

    shallow = evaluate_recall(graph, maximum_depth=1)
    deep = evaluate_recall(graph, maximum_depth=5)

    assert not shallow.success
    assert deep.success
    assert deep.actions == (
        HeatAction.STAND,
        HeatAction.WALK,
        HeatAction.REACH,
        HeatAction.ACTIVATE,
        HeatAction.WAIT,
    )
    assert all(record.need_after == 1.0 for record in deep.records[:-1])
    assert deep.records[-1].need_before == 1.0
    assert deep.records[-1].need_after == 0.0
    assert deep.maximum_depth_used > 1
    assert deep.total_computational_cost > 0
    assert tuple(neuron.neuron_id for neuron in graph.neurons) == neuron_ids_before
    assert tuple(synapse.synapse_id for synapse in graph.synapses) == synapse_ids_before


def test_complete_experiment_passes_local_memory_gate() -> None:
    result, _ = run_ndnra_heat_fan_experiment()

    assert result.pass_gate
    assert not result.baseline_recall.success
    assert not result.shallow_recall.success
    assert result.deep_recall.success
    assert result.training.earliest_action_weight > 0.0
    assert result.training.latest_action_weight > result.training.earliest_action_weight
    assert result.training.irrelevant_action_weight == 0.0
    assert result.neuron_count_before_dormancy == result.neuron_count_after_dormancy
    assert result.synapse_count_before_dormancy == result.synapse_count_after_dormancy
    assert result.growth_pressure >= 0.80
    assert not result.sqlite_used_for_recall


def test_recall_normalization_evidence_is_deterministic_and_preserves_chain() -> None:
    graph = LocalNeuralGraph()
    train_teacher_demonstrations(graph, demonstration_count=6)
    graph.enter_dormancy(0.80)
    need_pulse = NeedPulse(
        need_code="reduce_temperature",
        intensity=1.0,
        urgency=1.0,
        effort_budget=5,
    )

    first = graph.recall_action_with_normalization_evidence(
        need_pulse=need_pulse,
        context=HeatContext.SITTING_AWAY,
        maximum_depth=5,
    )
    second = graph.recall_action_with_normalization_evidence(
        need_pulse=need_pulse,
        context=HeatContext.SITTING_AWAY,
        maximum_depth=5,
    )

    assert first.recall_result == second.recall_result
    assert first.normalization_evidence == second.normalization_evidence
    assert first.recall_result.selected_action is HeatAction.STAND
    assert first.normalization_evidence.bounded


def test_growth_pressure_requires_all_developmental_factors() -> None:
    pressure = GrowthPressure()
    no_curiosity = pressure.update(
        unresolved_error=1.0,
        curiosity=0.0,
        ambition_relevance=1.0,
        capacity_saturation=1.0,
    )
    with_all_factors = pressure.update(
        unresolved_error=1.0,
        curiosity=1.0,
        ambition_relevance=1.0,
        capacity_saturation=1.0,
    )

    assert no_curiosity == 0.0
    assert with_all_factors > no_curiosity
