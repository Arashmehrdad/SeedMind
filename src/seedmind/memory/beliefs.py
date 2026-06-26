"""Evidence-linked belief formation and contradiction detection."""

from __future__ import annotations

import hashlib
import sqlite3
from dataclasses import dataclass
from math import isfinite

from seedmind.memory.models import (
    BeliefEvidence,
    BeliefEvidencePolarity,
    BeliefProposition,
    BeliefRecord,
    BeliefStatus,
    ContradictionRecord,
)
from seedmind.memory.store import EpisodicSQLiteStore


@dataclass(frozen=True, slots=True)
class BeliefRegistryConfig:
    """Transparent priors and confidence-status thresholds."""

    prior_support_weight: float = 1.0
    prior_contradiction_weight: float = 1.0
    supported_threshold: float = 0.67
    challenged_threshold: float = 0.40

    def __post_init__(self) -> None:
        for weight_name, weight_value in (
            ("prior_support_weight", self.prior_support_weight),
            ("prior_contradiction_weight", self.prior_contradiction_weight),
        ):
            if not isfinite(weight_value) or weight_value <= 0.0:
                raise ValueError(f"{weight_name} must be finite and positive")
        for threshold_name, threshold_value in (
            ("supported_threshold", self.supported_threshold),
            ("challenged_threshold", self.challenged_threshold),
        ):
            if not isfinite(threshold_value) or not 0.0 <= threshold_value <= 1.0:
                raise ValueError(f"{threshold_name} must be between zero and one")
        if self.challenged_threshold >= self.supported_threshold:
            raise ValueError("challenged_threshold must be below supported_threshold")


class BeliefRegistry:
    """Create and revise beliefs only through linked episodic evidence."""

    def __init__(
        self,
        store: EpisodicSQLiteStore,
        config: BeliefRegistryConfig | None = None,
    ) -> None:
        self.store = store
        self.config = BeliefRegistryConfig() if config is None else config

    def observe(
        self,
        proposition: BeliefProposition,
        *,
        event_id: str,
        observed_value: bool,
        weight: float = 1.0,
    ) -> BeliefRecord:
        """Link one observation and revise confidence from support or contradiction."""
        if not event_id.strip():
            raise ValueError("event_id must not be empty")
        if not isfinite(weight) or weight <= 0.0:
            raise ValueError("weight must be finite and positive")
        if self.store.get_event(event_id) is None:
            raise ValueError("belief evidence must reference a stored episodic event")

        existing = self.get_by_proposition(proposition)
        belief_id = existing.belief_id if existing is not None else _belief_id(proposition)
        if self._evidence_exists(belief_id, event_id):
            raise ValueError("episodic event is already linked to this belief")

        polarity = (
            BeliefEvidencePolarity.SUPPORTS
            if observed_value == proposition.expected_value
            else BeliefEvidencePolarity.CONTRADICTS
        )
        support_weight = 0.0 if existing is None else existing.support_weight
        contradiction_weight = 0.0 if existing is None else existing.contradiction_weight
        if polarity is BeliefEvidencePolarity.SUPPORTS:
            support_weight += weight
        else:
            contradiction_weight += weight
        confidence = self._confidence(support_weight, contradiction_weight)
        status = self._status(confidence)
        revision_count = 1 if existing is None else existing.revision_count + 1
        created_event_id = event_id if existing is None else existing.created_event_id

        connection = self.store.connection
        try:
            with connection:
                if existing is None:
                    connection.execute(
                        """
                        INSERT INTO beliefs (
                            belief_id,
                            subject_code,
                            relation_code,
                            object_code,
                            expected_value,
                            confidence,
                            support_weight,
                            contradiction_weight,
                            status,
                            created_event_id,
                            last_evidence_event_id,
                            revision_count
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            belief_id,
                            proposition.subject_code,
                            proposition.relation_code,
                            proposition.object_code,
                            int(proposition.expected_value),
                            confidence,
                            support_weight,
                            contradiction_weight,
                            status.value,
                            created_event_id,
                            event_id,
                            revision_count,
                        ),
                    )
                else:
                    connection.execute(
                        """
                        UPDATE beliefs
                        SET confidence = ?,
                            support_weight = ?,
                            contradiction_weight = ?,
                            status = ?,
                            last_evidence_event_id = ?,
                            revision_count = ?
                        WHERE belief_id = ?
                        """,
                        (
                            confidence,
                            support_weight,
                            contradiction_weight,
                            status.value,
                            event_id,
                            revision_count,
                            belief_id,
                        ),
                    )
                connection.execute(
                    """
                    INSERT INTO belief_evidence (
                        belief_id,
                        event_id,
                        polarity,
                        weight,
                        observed_value
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        belief_id,
                        event_id,
                        polarity.value,
                        weight,
                        int(observed_value),
                    ),
                )
        except sqlite3.IntegrityError as error:
            raise ValueError("belief evidence could not be persisted") from error

        record = self.get(belief_id)
        if record is None:
            raise RuntimeError("updated belief could not be reloaded")
        return record

    def get(self, belief_id: str) -> BeliefRecord | None:
        """Return one belief by stable identifier."""
        if not belief_id.strip():
            raise ValueError("belief_id must not be empty")
        row = self.store.connection.execute(
            "SELECT * FROM beliefs WHERE belief_id = ?",
            (belief_id,),
        ).fetchone()
        return None if row is None else _belief_from_row(row)

    def get_by_proposition(
        self,
        proposition: BeliefProposition,
    ) -> BeliefRecord | None:
        """Return the current belief for one exact symbolic proposition."""
        row = self.store.connection.execute(
            """
            SELECT *
            FROM beliefs
            WHERE subject_code = ?
              AND relation_code = ?
              AND object_code = ?
              AND expected_value = ?
            """,
            (
                proposition.subject_code,
                proposition.relation_code,
                proposition.object_code,
                int(proposition.expected_value),
            ),
        ).fetchone()
        return None if row is None else _belief_from_row(row)

    def all_beliefs(self) -> tuple[BeliefRecord, ...]:
        """Return all beliefs in stable identifier order."""
        rows = self.store.connection.execute(
            "SELECT * FROM beliefs ORDER BY belief_id ASC"
        ).fetchall()
        return tuple(_belief_from_row(row) for row in rows)

    def evidence_for_belief(self, belief_id: str) -> tuple[BeliefEvidence, ...]:
        """Return evidence links in episodic insertion order."""
        if self.get(belief_id) is None:
            raise ValueError("unknown belief_id")
        rows = self.store.connection.execute(
            """
            SELECT evidence.*
            FROM belief_evidence AS evidence
            JOIN episodic_events AS event ON event.event_id = evidence.event_id
            WHERE evidence.belief_id = ?
            ORDER BY event.sequence_id ASC
            """,
            (belief_id,),
        ).fetchall()
        return tuple(_evidence_from_row(row) for row in rows)

    def contradictions_for_belief(
        self,
        belief_id: str,
    ) -> tuple[ContradictionRecord, ...]:
        """Return explicit counterexamples linked to one belief."""
        belief = self.get(belief_id)
        if belief is None:
            raise ValueError("unknown belief_id")
        return tuple(
            ContradictionRecord(
                belief_id=evidence.belief_id,
                event_id=evidence.event_id,
                expected_value=belief.proposition.expected_value,
                observed_value=evidence.observed_value,
                weight=evidence.weight,
            )
            for evidence in self.evidence_for_belief(belief_id)
            if evidence.polarity is BeliefEvidencePolarity.CONTRADICTS
        )

    def _evidence_exists(self, belief_id: str, event_id: str) -> bool:
        row = self.store.connection.execute(
            """
            SELECT 1
            FROM belief_evidence
            WHERE belief_id = ? AND event_id = ?
            """,
            (belief_id, event_id),
        ).fetchone()
        return row is not None

    def _confidence(self, support_weight: float, contradiction_weight: float) -> float:
        support_total = self.config.prior_support_weight + support_weight
        contradiction_total = self.config.prior_contradiction_weight + contradiction_weight
        return support_total / (support_total + contradiction_total)

    def _status(self, confidence: float) -> BeliefStatus:
        if confidence >= self.config.supported_threshold:
            return BeliefStatus.SUPPORTED
        if confidence <= self.config.challenged_threshold:
            return BeliefStatus.CHALLENGED
        return BeliefStatus.TENTATIVE


def _belief_id(proposition: BeliefProposition) -> str:
    encoded = "|".join(
        (
            proposition.subject_code,
            proposition.relation_code,
            proposition.object_code,
            str(int(proposition.expected_value)),
        )
    )
    digest = hashlib.sha256(encoded.encode("ascii")).hexdigest()[:12]
    return f"belief-{digest}"


def _belief_from_row(row: sqlite3.Row) -> BeliefRecord:
    return BeliefRecord(
        belief_id=str(row["belief_id"]),
        proposition=BeliefProposition(
            subject_code=str(row["subject_code"]),
            relation_code=str(row["relation_code"]),
            object_code=str(row["object_code"]),
            expected_value=bool(row["expected_value"]),
        ),
        confidence=float(row["confidence"]),
        support_weight=float(row["support_weight"]),
        contradiction_weight=float(row["contradiction_weight"]),
        status=BeliefStatus(str(row["status"])),
        created_event_id=str(row["created_event_id"]),
        last_evidence_event_id=str(row["last_evidence_event_id"]),
        revision_count=int(row["revision_count"]),
    )


def _evidence_from_row(row: sqlite3.Row) -> BeliefEvidence:
    return BeliefEvidence(
        belief_id=str(row["belief_id"]),
        event_id=str(row["event_id"]),
        polarity=BeliefEvidencePolarity(str(row["polarity"])),
        weight=float(row["weight"]),
        observed_value=bool(row["observed_value"]),
    )
