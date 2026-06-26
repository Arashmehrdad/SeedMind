"""Versioned SQLite episodic store and contextual retrieval."""

from __future__ import annotations

import json
import sqlite3
from collections.abc import Iterator
from math import isfinite
from pathlib import Path
from typing import Any, cast

from seedmind.contracts import PrimitiveAction
from seedmind.memory.models import (
    EpisodicEvent,
    EpisodicEventDraft,
    EpisodicEventType,
    EventPayloadValue,
    MemoryQuery,
    SignificanceFeatures,
)
from seedmind.memory.significance import SignificanceScorer

_SCHEMA_VERSION = 1


class EpisodicSQLiteStore:
    """Persist episodic events and evidence-linked beliefs in one database."""

    def __init__(self, path: Path) -> None:
        if path.name in ("", ".", ".."):
            raise ValueError("SQLite path must identify a database file")
        path.parent.mkdir(parents=True, exist_ok=True)
        self.path = path
        self._connection = sqlite3.connect(path)
        self._connection.row_factory = sqlite3.Row
        self._connection.execute("PRAGMA foreign_keys = ON")
        self._initialize_schema()

    @property
    def schema_version(self) -> int:
        """Return the SQLite user-version applied to this store."""
        row = self._connection.execute("PRAGMA user_version").fetchone()
        assert row is not None
        return int(row[0])

    @property
    def connection(self) -> sqlite3.Connection:
        """Return the package-internal connection used by the belief registry."""
        return self._connection

    def __enter__(self) -> EpisodicSQLiteStore:
        return self

    def __exit__(self, exc_type: object, exc_value: object, traceback: object) -> None:
        self.close()

    def close(self) -> None:
        """Close the SQLite connection after committing completed writes."""
        self._connection.close()

    def remember(
        self,
        draft: EpisodicEventDraft,
        scorer: SignificanceScorer,
    ) -> EpisodicEvent:
        """Score and atomically persist one event."""
        return self.record(draft, significance=scorer.score(draft.features))

    def record(
        self,
        draft: EpisodicEventDraft,
        *,
        significance: float,
    ) -> EpisodicEvent:
        """Atomically persist one already scored event and return its row."""
        if not isfinite(significance) or not 0.0 <= significance <= 1.0:
            raise ValueError("significance must be between zero and one")
        payload_json = json.dumps(
            dict(draft.payload),
            ensure_ascii=True,
            separators=(",", ":"),
            sort_keys=True,
        )
        try:
            with self._connection:
                cursor = self._connection.execute(
                    """
                    INSERT INTO episodic_events (
                        event_id,
                        episode_id,
                        step_index,
                        event_type,
                        ambition_id,
                        context_code,
                        action,
                        outcome_code,
                        success,
                        prediction_error,
                        novelty,
                        learning_progress,
                        ambition_relevance,
                        human_relevance,
                        outcome_magnitude,
                        significance,
                        payload_json
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        draft.event_id,
                        draft.episode_id,
                        draft.step_index,
                        draft.event_type.value,
                        draft.ambition_id,
                        draft.context_code,
                        draft.action.value if draft.action is not None else None,
                        draft.outcome_code,
                        _optional_bool_to_database(draft.success),
                        draft.features.prediction_error,
                        draft.features.novelty,
                        draft.features.learning_progress,
                        draft.features.ambition_relevance,
                        draft.features.human_relevance,
                        draft.features.outcome_magnitude,
                        significance,
                        payload_json,
                    ),
                )
                if cursor.lastrowid is None:
                    raise RuntimeError("SQLite insert did not return a sequence id")
                sequence_id = cursor.lastrowid
        except sqlite3.IntegrityError as error:
            raise ValueError(f"episodic event could not be inserted: {draft.event_id}") from error
        event = self.get_event(draft.event_id)
        if event is None or event.sequence_id != sequence_id:
            raise RuntimeError("inserted episodic event could not be reloaded")
        return event

    def get_event(self, event_id: str) -> EpisodicEvent | None:
        """Return one event by stable identifier."""
        if not event_id.strip():
            raise ValueError("event_id must not be empty")
        row = self._connection.execute(
            "SELECT * FROM episodic_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
        return None if row is None else _event_from_row(row)

    def retrieve(self, query: MemoryQuery) -> tuple[EpisodicEvent, ...]:
        """Retrieve significant events by ambition and contextual filters."""
        clauses = ["significance >= ?"]
        parameters: list[object] = [query.minimum_significance]
        if query.ambition_id is not None:
            clauses.append("ambition_id = ?")
            parameters.append(query.ambition_id)
        if query.context_code is not None:
            clauses.append("context_code = ?")
            parameters.append(query.context_code)
        if query.event_type is not None:
            clauses.append("event_type = ?")
            parameters.append(query.event_type.value)
        parameters.append(query.limit)
        rows = self._connection.execute(
            f"""
            SELECT *
            FROM episodic_events
            WHERE {" AND ".join(clauses)}
            ORDER BY significance DESC, sequence_id DESC
            LIMIT ?
            """,
            parameters,
        ).fetchall()
        return tuple(_event_from_row(row) for row in rows)

    def all_events(self) -> tuple[EpisodicEvent, ...]:
        """Return complete episodic history in insertion order."""
        rows = self._connection.execute(
            "SELECT * FROM episodic_events ORDER BY sequence_id ASC"
        ).fetchall()
        return tuple(_event_from_row(row) for row in rows)

    def iter_events(self) -> Iterator[EpisodicEvent]:
        """Yield complete episodic history without materializing a second tuple."""
        rows = self._connection.execute("SELECT * FROM episodic_events ORDER BY sequence_id ASC")
        for row in rows:
            yield _event_from_row(row)

    def _initialize_schema(self) -> None:
        current_version = self.schema_version
        if current_version not in (0, _SCHEMA_VERSION):
            raise ValueError(f"Unsupported episodic-memory schema version: {current_version}")
        with self._connection:
            self._connection.executescript(
                """
                CREATE TABLE IF NOT EXISTS episodic_events (
                    sequence_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT NOT NULL UNIQUE,
                    episode_id TEXT NOT NULL,
                    step_index INTEGER NOT NULL CHECK (step_index >= 0),
                    event_type TEXT NOT NULL,
                    ambition_id TEXT,
                    context_code TEXT NOT NULL,
                    action TEXT,
                    outcome_code TEXT NOT NULL,
                    success INTEGER,
                    prediction_error REAL NOT NULL,
                    novelty REAL NOT NULL,
                    learning_progress REAL NOT NULL,
                    ambition_relevance REAL NOT NULL,
                    human_relevance REAL NOT NULL,
                    outcome_magnitude REAL NOT NULL,
                    significance REAL NOT NULL,
                    payload_json TEXT NOT NULL
                );

                CREATE INDEX IF NOT EXISTS idx_events_ambition_context_significance
                ON episodic_events (ambition_id, context_code, significance DESC);

                CREATE INDEX IF NOT EXISTS idx_events_episode_step
                ON episodic_events (episode_id, step_index);

                CREATE TABLE IF NOT EXISTS beliefs (
                    belief_id TEXT PRIMARY KEY,
                    subject_code TEXT NOT NULL,
                    relation_code TEXT NOT NULL,
                    object_code TEXT NOT NULL,
                    expected_value INTEGER NOT NULL,
                    confidence REAL NOT NULL,
                    support_weight REAL NOT NULL,
                    contradiction_weight REAL NOT NULL,
                    status TEXT NOT NULL,
                    created_event_id TEXT NOT NULL,
                    last_evidence_event_id TEXT NOT NULL,
                    revision_count INTEGER NOT NULL,
                    UNIQUE (subject_code, relation_code, object_code, expected_value),
                    FOREIGN KEY (created_event_id) REFERENCES episodic_events (event_id),
                    FOREIGN KEY (last_evidence_event_id) REFERENCES episodic_events (event_id)
                );

                CREATE TABLE IF NOT EXISTS belief_evidence (
                    belief_id TEXT NOT NULL,
                    event_id TEXT NOT NULL,
                    polarity TEXT NOT NULL,
                    weight REAL NOT NULL,
                    observed_value INTEGER NOT NULL,
                    PRIMARY KEY (belief_id, event_id),
                    FOREIGN KEY (belief_id) REFERENCES beliefs (belief_id) ON DELETE CASCADE,
                    FOREIGN KEY (event_id) REFERENCES episodic_events (event_id)
                );

                CREATE INDEX IF NOT EXISTS idx_belief_evidence_event
                ON belief_evidence (event_id);
                """
            )
            self._connection.execute(f"PRAGMA user_version = {_SCHEMA_VERSION}")


def _event_from_row(row: sqlite3.Row) -> EpisodicEvent:
    action_value = cast(str | None, row["action"])
    return EpisodicEvent(
        sequence_id=int(row["sequence_id"]),
        event_id=str(row["event_id"]),
        episode_id=str(row["episode_id"]),
        step_index=int(row["step_index"]),
        event_type=EpisodicEventType(str(row["event_type"])),
        ambition_id=cast(str | None, row["ambition_id"]),
        context_code=str(row["context_code"]),
        action=PrimitiveAction(action_value) if action_value is not None else None,
        outcome_code=str(row["outcome_code"]),
        success=_optional_bool_from_database(row["success"]),
        features=SignificanceFeatures(
            prediction_error=float(row["prediction_error"]),
            novelty=float(row["novelty"]),
            learning_progress=float(row["learning_progress"]),
            ambition_relevance=float(row["ambition_relevance"]),
            human_relevance=float(row["human_relevance"]),
            outcome_magnitude=float(row["outcome_magnitude"]),
        ),
        significance=float(row["significance"]),
        payload=_payload_from_json(str(row["payload_json"])),
    )


def _payload_from_json(payload_json: str) -> tuple[tuple[str, EventPayloadValue], ...]:
    decoded = json.loads(payload_json)
    if not isinstance(decoded, dict):
        raise ValueError("episodic payload must decode to an object")
    payload: list[tuple[str, EventPayloadValue]] = []
    for key, value in sorted(decoded.items()):
        if not isinstance(key, str):
            raise ValueError("episodic payload keys must be strings")
        if value is not None and not isinstance(value, (str, int, float, bool)):
            raise ValueError("episodic payload values must be scalar JSON values")
        if isinstance(value, float) and not isfinite(value):
            raise ValueError("episodic payload floats must be finite")
        payload.append((key, value))
    return tuple(payload)


def _optional_bool_to_database(value: bool | None) -> int | None:
    return None if value is None else int(value)


def _optional_bool_from_database(value: Any) -> bool | None:
    if value is None:
        return None
    if value not in (0, 1):
        raise ValueError("SQLite boolean value must be zero, one, or null")
    return bool(value)
