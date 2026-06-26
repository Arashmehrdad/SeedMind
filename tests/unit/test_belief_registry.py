"""Tests for evidence-linked beliefs, contradictions, and inspection."""

from pathlib import Path

import pytest

from seedmind.contracts import PrimitiveAction
from seedmind.memory import (
    BeliefEvidencePolarity,
    BeliefProposition,
    BeliefRegistry,
    BeliefStatus,
    EpisodicEventDraft,
    EpisodicEventType,
    EpisodicSQLiteStore,
    SignificanceFeatures,
    SignificanceScorer,
    export_belief_evidence_csv,
    export_memory_inspector_json,
)


def memory_event(event_id: str, step_index: int, *, success: bool) -> EpisodicEventDraft:
    return EpisodicEventDraft(
        event_id=event_id,
        episode_id="belief-episode",
        step_index=step_index,
        event_type=(
            EpisodicEventType.EXTERNAL_CHANGE if success else EpisodicEventType.COUNTEREXAMPLE
        ),
        ambition_id="ambition-control",
        context_code="teacher-object-control",
        action=PrimitiveAction.WAIT,
        outcome_code="external-change" if success else "no-external-change",
        success=success,
        features=SignificanceFeatures(
            prediction_error=0.8,
            novelty=0.8,
            learning_progress=0.5,
            ambition_relevance=1.0,
            human_relevance=1.0,
            outcome_magnitude=0.9,
        ),
    )


def proposition() -> BeliefProposition:
    return BeliefProposition(
        subject_code="wait-during-teacher-demonstration",
        relation_code="causes",
        object_code="external-world-change",
        expected_value=True,
    )


def test_supporting_evidence_raises_belief_confidence(tmp_path: Path) -> None:
    with EpisodicSQLiteStore(tmp_path / "memory.sqlite3") as store:
        scorer = SignificanceScorer()
        store.remember(memory_event("support-1", 1, success=True), scorer)
        store.remember(memory_event("support-2", 2, success=True), scorer)
        registry = BeliefRegistry(store)

        first = registry.observe(
            proposition(),
            event_id="support-1",
            observed_value=True,
        )
        second = registry.observe(
            proposition(),
            event_id="support-2",
            observed_value=True,
        )

    assert first.confidence == pytest.approx(2.0 / 3.0)
    assert second.confidence == pytest.approx(0.75)
    assert second.status is BeliefStatus.SUPPORTED
    assert second.support_weight == 2.0
    assert second.contradiction_weight == 0.0


def test_counterexample_lowers_confidence_and_creates_contradiction(tmp_path: Path) -> None:
    with EpisodicSQLiteStore(tmp_path / "memory.sqlite3") as store:
        scorer = SignificanceScorer()
        for index in (1, 2):
            store.remember(memory_event(f"support-{index}", index, success=True), scorer)
        store.remember(memory_event("counterexample-1", 3, success=False), scorer)
        registry = BeliefRegistry(store)
        registry.observe(proposition(), event_id="support-1", observed_value=True)
        supported = registry.observe(
            proposition(),
            event_id="support-2",
            observed_value=True,
        )
        revised = registry.observe(
            proposition(),
            event_id="counterexample-1",
            observed_value=False,
        )
        contradictions = registry.contradictions_for_belief(revised.belief_id)
        evidence = registry.evidence_for_belief(revised.belief_id)

    assert revised.confidence < supported.confidence
    assert revised.confidence == pytest.approx(0.6)
    assert revised.status is BeliefStatus.TENTATIVE
    assert len(contradictions) == 1
    assert contradictions[0].event_id == "counterexample-1"
    assert tuple(item.polarity for item in evidence) == (
        BeliefEvidencePolarity.SUPPORTS,
        BeliefEvidencePolarity.SUPPORTS,
        BeliefEvidencePolarity.CONTRADICTS,
    )


def test_belief_and_evidence_persist_across_database_reopen(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.sqlite3"
    with EpisodicSQLiteStore(database_path) as store:
        scorer = SignificanceScorer()
        store.remember(memory_event("support-1", 1, success=True), scorer)
        registry = BeliefRegistry(store)
        created = registry.observe(
            proposition(),
            event_id="support-1",
            observed_value=True,
        )

    with EpisodicSQLiteStore(database_path) as reopened:
        restored_registry = BeliefRegistry(reopened)
        restored = restored_registry.get(created.belief_id)
        evidence = restored_registry.evidence_for_belief(created.belief_id)

    assert restored == created
    assert len(evidence) == 1
    assert evidence[0].event_id == "support-1"


def test_belief_rejects_missing_or_duplicate_evidence(tmp_path: Path) -> None:
    with EpisodicSQLiteStore(tmp_path / "memory.sqlite3") as store:
        registry = BeliefRegistry(store)
        with pytest.raises(ValueError, match="stored episodic event"):
            registry.observe(
                proposition(),
                event_id="missing-event",
                observed_value=True,
            )
        store.remember(
            memory_event("support-1", 1, success=True),
            SignificanceScorer(),
        )
        registry.observe(proposition(), event_id="support-1", observed_value=True)
        with pytest.raises(ValueError, match="already linked"):
            registry.observe(
                proposition(),
                event_id="support-1",
                observed_value=True,
            )


def test_memory_inspector_and_evidence_viewer_are_ascii(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.sqlite3"
    inspector_path = tmp_path / "memory_inspector.json"
    evidence_path = tmp_path / "belief_evidence.csv"
    with EpisodicSQLiteStore(database_path) as store:
        scorer = SignificanceScorer()
        store.remember(memory_event("support-1", 1, success=True), scorer)
        store.remember(memory_event("counterexample-1", 2, success=False), scorer)
        registry = BeliefRegistry(store)
        registry.observe(proposition(), event_id="support-1", observed_value=True)
        registry.observe(
            proposition(),
            event_id="counterexample-1",
            observed_value=False,
        )
        export_memory_inspector_json(store, registry, inspector_path)
        export_belief_evidence_csv(store, registry, evidence_path)

    inspector = inspector_path.read_text(encoding="ascii")
    evidence = evidence_path.read_text(encoding="ascii")
    assert '"belief_count": 1' in inspector
    assert '"contradictions"' in inspector
    assert '"event_count": 2' in inspector
    assert evidence.startswith("belief_id,subject_code,relation_code")
    assert "counterexample-1" in evidence
    assert "contradicts" in evidence
