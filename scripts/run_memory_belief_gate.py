"""Run the Week 7 episodic-memory and belief-revision acceptance gate."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.contracts import PrimitiveAction
from seedmind.environment import NurseryRuntime, TeacherDemonstrationScenarioFactory
from seedmind.memory import (
    BeliefProposition,
    BeliefRegistry,
    EpisodicEventDraft,
    EpisodicEventType,
    EpisodicSQLiteStore,
    MemoryQuery,
    SignificanceFeatures,
    SignificanceScorer,
    export_belief_evidence_csv,
    export_memory_inspector_json,
)

_AMBITION_ID = "ambition-control-external-change"
_CONTEXT_CODE = "teacher-object-control"


def parse_args() -> argparse.Namespace:
    """Parse deterministic Week 7 evidence settings."""
    parser = argparse.ArgumentParser(
        description="Validate episodic retrieval and counterexample belief revision.",
    )
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("artifacts/memory_belief_gate"),
    )
    return parser.parse_args()


def main() -> int:
    """Store real events, revise a belief, reopen SQLite, and inspect evidence."""
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    database_path = args.output_dir / "episodic_memory.sqlite3"
    inspector_path = args.output_dir / "memory_inspector.json"
    evidence_path = args.output_dir / "belief_evidence.csv"
    database_path.unlink(missing_ok=True)

    scenario = TeacherDemonstrationScenarioFactory().create(args.seed)
    runtime = NurseryRuntime(
        initial_state=scenario.initial_state,
        episode_id=f"{scenario.scenario_id}-memory-gate",
        resource_state_provider=scenario.resource_state,
        world_processes=scenario.world_processes,
    )
    scorer = SignificanceScorer()
    proposition = BeliefProposition(
        subject_code="wait-during-teacher-demonstration",
        relation_code="causes",
        object_code="external-world-change",
        expected_value=True,
    )
    confidence_before_counterexample = 0.0
    confidence_after_counterexample = 0.0
    belief_id = ""

    with EpisodicSQLiteStore(database_path) as store:
        registry = BeliefRegistry(store)
        for step_index in range(1, 4):
            result = runtime.step(PrimitiveAction.WAIT)
            changed = result.external_world_changed
            event_id = f"teacher-memory-{step_index:04d}"
            event_type = (
                EpisodicEventType.EXTERNAL_CHANGE if changed else EpisodicEventType.COUNTEREXAMPLE
            )
            store.remember(
                EpisodicEventDraft(
                    event_id=event_id,
                    episode_id=runtime.episode_id,
                    step_index=step_index,
                    event_type=event_type,
                    ambition_id=_AMBITION_ID,
                    context_code=_CONTEXT_CODE,
                    action=PrimitiveAction.WAIT,
                    outcome_code=(
                        "external-world-change" if changed else "no-external-world-change"
                    ),
                    success=changed,
                    features=SignificanceFeatures(
                        prediction_error=0.85 if changed else 0.95,
                        novelty=0.90 if changed else 1.00,
                        learning_progress=0.60 if changed else 0.20,
                        ambition_relevance=1.00,
                        human_relevance=1.00,
                        outcome_magnitude=1.00 if changed else 0.90,
                    ),
                    payload=(
                        ("process_event_count", len(result.process_events)),
                        ("world_changed", changed),
                    ),
                ),
                scorer,
            )
            belief = registry.observe(
                proposition,
                event_id=event_id,
                observed_value=changed,
            )
            belief_id = belief.belief_id
            if step_index == 2:
                confidence_before_counterexample = belief.confidence
            if step_index == 3:
                confidence_after_counterexample = belief.confidence

        routine_result = runtime.step(PrimitiveAction.WAIT)
        store.remember(
            EpisodicEventDraft(
                event_id="teacher-memory-routine-0004",
                episode_id=runtime.episode_id,
                step_index=4,
                event_type=EpisodicEventType.ACTION,
                ambition_id=_AMBITION_ID,
                context_code=_CONTEXT_CODE,
                action=PrimitiveAction.WAIT,
                outcome_code="routine-no-change",
                success=routine_result.external_world_changed,
                features=SignificanceFeatures(
                    prediction_error=0.10,
                    novelty=0.05,
                    learning_progress=0.00,
                    ambition_relevance=0.20,
                    human_relevance=0.00,
                    outcome_magnitude=0.05,
                ),
            ),
            scorer,
        )
        store.remember(
            EpisodicEventDraft(
                event_id="unrelated-navigation-0001",
                episode_id="unrelated-navigation-episode",
                step_index=1,
                event_type=EpisodicEventType.SUCCESS,
                ambition_id="ambition-navigation",
                context_code="familiar-navigation",
                action=PrimitiveAction.MOVE_FORWARD,
                outcome_code="position-change",
                success=True,
                features=SignificanceFeatures(
                    prediction_error=0.80,
                    novelty=0.80,
                    learning_progress=0.70,
                    ambition_relevance=1.00,
                    human_relevance=0.20,
                    outcome_magnitude=0.80,
                ),
            ),
            scorer,
        )

    with EpisodicSQLiteStore(database_path) as reopened:
        restored_registry = BeliefRegistry(reopened)
        retrieved = reopened.retrieve(
            MemoryQuery(
                minimum_significance=0.70,
                ambition_id=_AMBITION_ID,
                context_code=_CONTEXT_CODE,
                limit=10,
            )
        )
        restored_belief = restored_registry.get(belief_id)
        if restored_belief is None:
            raise RuntimeError("belief was not restored after reopening SQLite")
        evidence = restored_registry.evidence_for_belief(belief_id)
        contradictions = restored_registry.contradictions_for_belief(belief_id)
        export_memory_inspector_json(reopened, restored_registry, inspector_path)
        export_belief_evidence_csv(reopened, restored_registry, evidence_path)
        schema_version = reopened.schema_version
        total_event_count = len(reopened.all_events())

    retrieved_by_context = all(
        event.ambition_id == _AMBITION_ID and event.context_code == _CONTEXT_CODE
        for event in retrieved
    )
    confidence_changed = confidence_after_counterexample < confidence_before_counterexample
    pass_gate = (
        len(retrieved) == 3
        and retrieved_by_context
        and confidence_changed
        and len(evidence) == 3
        and len(contradictions) == 1
        and restored_belief.confidence == confidence_after_counterexample
    )

    print(f"schema_version={schema_version}")
    print(f"total_event_count={total_event_count}")
    print(f"retrieved_significant_events={len(retrieved)}")
    print(f"retrieved_by_ambition_and_context={str(retrieved_by_context).lower()}")
    print(f"belief_id={belief_id}")
    print(f"belief_evidence_count={len(evidence)}")
    print(f"contradiction_count={len(contradictions)}")
    print(f"belief_confidence_before_counterexample={confidence_before_counterexample:.8f}")
    print(f"belief_confidence_after_counterexample={confidence_after_counterexample:.8f}")
    print(f"belief_status={restored_belief.status.value}")
    print(f"confidence_changed={str(confidence_changed).lower()}")
    print(f"pass_gate={str(pass_gate).lower()}")
    print(f"episodic_database={database_path}")
    print(f"memory_inspector_json={inspector_path}")
    print(f"belief_evidence_csv={evidence_path}")
    return 0 if pass_gate else 1


if __name__ == "__main__":
    raise SystemExit(main())
