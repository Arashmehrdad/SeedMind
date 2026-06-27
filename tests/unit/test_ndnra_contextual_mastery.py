"""Tests for contextual NDNRA redundancy and bounded mastery evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from seedmind.integration import (
    export_contextual_mastery_acceptance,
    run_contextual_mastery_acceptance,
)
from seedmind.research.ndnra import (
    ContextSignature,
    ContextualExperienceLedger,
    ContextualExperienceTrace,
    EffectObservation,
    EventIdentity,
    LessonIdentity,
    MultidimensionalExperienceGraph,
    run_contextual_mastery_experiment,
)


def test_contextual_mastery_experiment_distinguishes_replay_from_breadth() -> None:
    evidence = run_contextual_mastery_experiment()
    result = evidence.result

    assert result.exact_duplicate_ignored
    assert result.exact_duplicate_evidence_count == 1
    assert result.identity_conflict_blocked
    assert result.legitimate_context_preserved
    assert result.replay_trace_count == 6
    assert result.replay_effective_support <= 1.0
    assert result.replay_unique_context_count == 1
    assert result.replay_aggregate_evidence_count == 1
    assert result.independent_trace_count == 4
    assert result.independent_effective_support >= 4.0
    assert result.independent_unique_context_count >= 3
    assert result.independent_unique_route_count >= 2
    assert result.mastery_score_gain >= 0.30
    assert result.pass_gate


def test_one_shot_protection_and_varied_mastery_remain_distinct() -> None:
    result = run_contextual_mastery_experiment().result

    assert result.one_shot_protective_strength >= 0.90
    assert not result.one_shot_broad_mastery
    assert result.varied_heat_mastery_score >= 0.75
    assert result.varied_heat_broad_mastery
    assert result.route_switches_with_context


def test_contradiction_reduces_mastery_without_erasing_sources() -> None:
    result = run_contextual_mastery_experiment().result

    assert result.contradiction_count_after > result.contradiction_count_before
    assert result.causal_consistency_after < result.causal_consistency_before
    assert result.mastery_after_contradiction < result.mastery_before_contradiction
    assert result.source_traces_preserved


def test_event_identity_key_is_collision_safe() -> None:
    left = EventIdentity("a:b", "c", 1)
    right = EventIdentity("a", "b:c", 1)

    assert left != right
    assert left.key != right.key


def test_contradictory_effect_does_not_create_protective_strength() -> None:
    ledger = ContextualExperienceLedger()
    context = ContextSignature.from_values(
        active_need_code="avoid_heat_harm",
        sensor_values=(1.0,),
        available_action_codes=("withdraw",),
    )
    ledger.record(
        ContextualExperienceTrace(
            identity=EventIdentity("test", "contradiction", 0),
            correlation_group_id="group:contradiction",
            assembly_id="assembly:withdraw",
            route_id="route:withdraw",
            action_code="withdraw",
            context=context,
            observed_effects=(EffectObservation("protective_value", -1.0, 1.0),),
        )
    )

    profile = ledger.mastery_profile(LessonIdentity("avoid_heat_harm", "protective_value", 1.0))

    assert profile.protective_strength == 0.0
    assert profile.contradiction_count == 1


def test_contextual_recording_is_atomic_when_identity_validation_fails() -> None:
    graph = MultidimensionalExperienceGraph()
    context = ContextSignature.from_values(
        active_need_code="avoid_heat_harm",
        sensor_values=(1.0,),
        available_action_codes=("withdraw", "cool_surface"),
    )
    graph.learn_contextual_experience(
        identity=EventIdentity("test", "atomic", 0),
        correlation_group_id="group:atomic",
        assembly_id="assembly:withdraw",
        route_id="route:withdraw",
        action_code="withdraw",
        origin_need_code="avoid_heat_harm",
        required_facts=("heat_source_detected",),
        produced_facts=("withdrew",),
        context_signature=context,
        observed_effects=(EffectObservation("protective_value", 1.0, 1.0),),
    )

    with pytest.raises(ValueError, match="correlation group identity conflict"):
        graph.learn_contextual_experience(
            identity=EventIdentity("test", "atomic", 1),
            correlation_group_id="group:atomic",
            assembly_id="assembly:cool_surface",
            route_id="route:cool_surface",
            action_code="cool_surface",
            origin_need_code="avoid_heat_harm",
            required_facts=("heat_source_detected",),
            produced_facts=("surface_cooled",),
            context_signature=context,
            observed_effects=(EffectObservation("protective_value", 1.0, 1.0),),
        )

    with pytest.raises(ValueError, match="existing assembly cannot change its identity"):
        graph.learn_contextual_experience(
            identity=EventIdentity("test", "atomic", 2),
            correlation_group_id="group:independent",
            assembly_id="assembly:withdraw",
            route_id="route:withdraw",
            action_code="withdraw",
            origin_need_code="different_need",
            required_facts=("heat_source_detected",),
            produced_facts=("withdrew",),
            context_signature=context,
            observed_effects=(EffectObservation("protective_value", 1.0, 1.0),),
        )

    assert graph.contextual_memory.trace_count == 1
    assert graph.assembly_count == 1
    assert graph.assembly("assembly:withdraw").evidence_count == 1


def test_contextual_mastery_gate_preserves_shadow_and_persistence(
    tmp_path: Path,
) -> None:
    evidence = run_contextual_mastery_acceptance(tmp_path, play_budget=12)
    result = evidence.result

    assert result.synthetic_gate_passed
    assert result.production_actions_unchanged
    assert result.prediction_errors_unchanged
    assert result.authority_violation_count == 0
    assert result.tracked_trace_count == result.expected_trace_count
    assert result.graph_round_trip_exact
    assert result.contextual_round_trip_exact
    assert result.legacy_v1_migration_passed
    assert not result.sqlite_used_for_contextual_mastery
    assert result.pass_gate

    report, timeline, profiles, shadow = export_contextual_mastery_acceptance(
        evidence,
        tmp_path,
    )
    assert '"pass_gate": true' in report.read_text(encoding="ascii")
    assert timeline.read_text(encoding="ascii").startswith("scenario,event_key")
    assert '"varied_before_contradiction"' in profiles.read_text(encoding="ascii")
    assert '"production_actions_unchanged": true' in shadow.read_text(encoding="ascii")


def test_contextual_mastery_has_no_sqlite_cognitive_dependency() -> None:
    files = (
        Path("src/seedmind/research/ndnra/contextual_memory.py"),
        Path("src/seedmind/research/ndnra/contextual_mastery_experiment.py"),
        Path("src/seedmind/integration/contextual_mastery_acceptance.py"),
        Path("src/seedmind/integration/unified_shadow.py"),
    )
    source = "\n".join(path.read_text(encoding="utf-8") for path in files).lower()

    assert "import sqlite3" not in source
    assert "episodicsqlitestore" not in source
    assert "select " not in source
