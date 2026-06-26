"""Tests for SQLite episodic storage, significance, and retrieval."""

from pathlib import Path

import pytest

from seedmind.contracts import PrimitiveAction
from seedmind.memory import (
    EpisodicEventDraft,
    EpisodicEventType,
    EpisodicSQLiteStore,
    MemoryQuery,
    SignificanceConfig,
    SignificanceFeatures,
    SignificanceScorer,
)


def features(
    *,
    prediction_error: float = 0.8,
    novelty: float = 0.8,
    learning_progress: float = 0.6,
    ambition_relevance: float = 1.0,
    human_relevance: float = 0.5,
    outcome_magnitude: float = 0.9,
) -> SignificanceFeatures:
    return SignificanceFeatures(
        prediction_error=prediction_error,
        novelty=novelty,
        learning_progress=learning_progress,
        ambition_relevance=ambition_relevance,
        human_relevance=human_relevance,
        outcome_magnitude=outcome_magnitude,
    )


def event_draft(
    event_id: str,
    *,
    episode_id: str = "episode-001",
    step_index: int = 1,
    ambition_id: str | None = "ambition-control",
    context_code: str = "object-control-practice",
    event_type: EpisodicEventType = EpisodicEventType.EXTERNAL_CHANGE,
    event_features: SignificanceFeatures | None = None,
) -> EpisodicEventDraft:
    return EpisodicEventDraft(
        event_id=event_id,
        episode_id=episode_id,
        step_index=step_index,
        event_type=event_type,
        ambition_id=ambition_id,
        context_code=context_code,
        action=PrimitiveAction.WAIT,
        outcome_code="external-change",
        success=True,
        features=features() if event_features is None else event_features,
        payload=(("channel_count", 2), ("verified", True)),
    )


def test_significance_prioritizes_developmentally_relevant_event() -> None:
    scorer = SignificanceScorer()
    significant = scorer.score(features())
    routine = scorer.score(
        features(
            prediction_error=0.1,
            novelty=0.1,
            learning_progress=0.0,
            ambition_relevance=0.0,
            human_relevance=0.0,
            outcome_magnitude=0.1,
        )
    )

    assert significant > 0.7
    assert routine < 0.2
    assert significant > routine


def test_store_persists_and_retrieves_by_ambition_and_context(tmp_path: Path) -> None:
    database_path = tmp_path / "memory.sqlite3"
    scorer = SignificanceScorer()
    with EpisodicSQLiteStore(database_path) as store:
        important = store.remember(event_draft("event-important"), scorer)
        store.remember(
            event_draft(
                "event-routine",
                step_index=2,
                event_features=features(
                    prediction_error=0.1,
                    novelty=0.1,
                    learning_progress=0.0,
                    ambition_relevance=0.2,
                    human_relevance=0.0,
                    outcome_magnitude=0.1,
                ),
            ),
            scorer,
        )
        store.remember(
            event_draft(
                "event-other-context",
                context_code="familiar-navigation",
            ),
            scorer,
        )
        assert important.payload == (("channel_count", 2), ("verified", True))
        assert store.schema_version == 1

    with EpisodicSQLiteStore(database_path) as reopened:
        retrieved = reopened.retrieve(
            MemoryQuery(
                minimum_significance=0.6,
                ambition_id="ambition-control",
                context_code="object-control-practice",
            )
        )

    assert tuple(event.event_id for event in retrieved) == ("event-important",)


def test_retrieval_orders_significance_before_recency(tmp_path: Path) -> None:
    scorer = SignificanceScorer()
    with EpisodicSQLiteStore(tmp_path / "memory.sqlite3") as store:
        first = store.remember(event_draft("event-high"), scorer)
        second = store.remember(
            event_draft(
                "event-medium",
                step_index=2,
                event_features=features(novelty=0.3, outcome_magnitude=0.4),
            ),
            scorer,
        )
        retrieved = store.retrieve(MemoryQuery(limit=2))

    assert first.significance > second.significance
    assert tuple(event.event_id for event in retrieved) == (
        "event-high",
        "event-medium",
    )


def test_duplicate_event_id_is_rejected(tmp_path: Path) -> None:
    scorer = SignificanceScorer()
    with EpisodicSQLiteStore(tmp_path / "memory.sqlite3") as store:
        store.remember(event_draft("event-duplicate"), scorer)
        with pytest.raises(ValueError, match="could not be inserted"):
            store.remember(event_draft("event-duplicate"), scorer)


def test_memory_query_can_filter_event_type(tmp_path: Path) -> None:
    scorer = SignificanceScorer()
    with EpisodicSQLiteStore(tmp_path / "memory.sqlite3") as store:
        store.remember(event_draft("event-change"), scorer)
        store.remember(
            event_draft(
                "event-guidance",
                step_index=2,
                event_type=EpisodicEventType.HUMAN_GUIDANCE,
            ),
            scorer,
        )
        retrieved = store.retrieve(MemoryQuery(event_type=EpisodicEventType.HUMAN_GUIDANCE))

    assert tuple(event.event_id for event in retrieved) == ("event-guidance",)


@pytest.mark.parametrize(
    "kwargs",
    [
        {"prediction_error_weight": -0.1},
        {
            "prediction_error_weight": 0.0,
            "novelty_weight": 0.0,
            "learning_progress_weight": 0.0,
            "ambition_relevance_weight": 0.0,
            "human_relevance_weight": 0.0,
            "outcome_magnitude_weight": 0.0,
        },
    ],
)
def test_significance_config_rejects_invalid_weights(
    kwargs: dict[str, float],
) -> None:
    with pytest.raises(ValueError, match=r"significance weight|at least one"):
        SignificanceConfig(**kwargs)
