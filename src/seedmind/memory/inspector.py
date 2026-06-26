"""Inspectable JSON and CSV views for episodic memory and beliefs."""

from __future__ import annotations

import csv
import json
from pathlib import Path

from seedmind.memory.beliefs import BeliefRegistry
from seedmind.memory.models import BeliefEvidence, BeliefRecord, EpisodicEvent
from seedmind.memory.store import EpisodicSQLiteStore


def export_memory_inspector_json(
    store: EpisodicSQLiteStore,
    registry: BeliefRegistry,
    path: Path,
) -> None:
    """Write complete episodic, belief, contradiction, and evidence state."""
    beliefs = registry.all_beliefs()
    payload = {
        "schema_version": store.schema_version,
        "database_path": str(store.path),
        "event_count": len(store.all_events()),
        "belief_count": len(beliefs),
        "events": [_event_payload(event) for event in store.iter_events()],
        "beliefs": [
            {
                **_belief_payload(belief),
                "evidence": [
                    _evidence_payload(evidence)
                    for evidence in registry.evidence_for_belief(belief.belief_id)
                ],
                "contradictions": [
                    {
                        "event_id": contradiction.event_id,
                        "expected_value": contradiction.expected_value,
                        "observed_value": contradiction.observed_value,
                        "weight": contradiction.weight,
                    }
                    for contradiction in registry.contradictions_for_belief(belief.belief_id)
                ],
            }
            for belief in beliefs
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)


def export_belief_evidence_csv(
    store: EpisodicSQLiteStore,
    registry: BeliefRegistry,
    path: Path,
) -> None:
    """Write one row per belief-event evidence link."""
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    with temporary_path.open("w", encoding="ascii", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            (
                "belief_id",
                "subject_code",
                "relation_code",
                "object_code",
                "expected_value",
                "belief_confidence",
                "belief_status",
                "event_id",
                "episode_id",
                "step_index",
                "context_code",
                "outcome_code",
                "event_significance",
                "polarity",
                "observed_value",
                "weight",
            )
        )
        for belief in registry.all_beliefs():
            for evidence in registry.evidence_for_belief(belief.belief_id):
                event = store.get_event(evidence.event_id)
                if event is None:
                    raise RuntimeError("belief evidence references a missing event")
                writer.writerow(
                    (
                        belief.belief_id,
                        belief.proposition.subject_code,
                        belief.proposition.relation_code,
                        belief.proposition.object_code,
                        str(belief.proposition.expected_value).lower(),
                        belief.confidence,
                        belief.status.value,
                        event.event_id,
                        event.episode_id,
                        event.step_index,
                        event.context_code,
                        event.outcome_code,
                        event.significance,
                        evidence.polarity.value,
                        str(evidence.observed_value).lower(),
                        evidence.weight,
                    )
                )
    temporary_path.replace(path)


def _event_payload(event: EpisodicEvent) -> dict[str, object]:
    return {
        "sequence_id": event.sequence_id,
        "event_id": event.event_id,
        "episode_id": event.episode_id,
        "step_index": event.step_index,
        "event_type": event.event_type.value,
        "ambition_id": event.ambition_id,
        "context_code": event.context_code,
        "action": event.action.value if event.action is not None else None,
        "outcome_code": event.outcome_code,
        "success": event.success,
        "significance": event.significance,
        "features": {
            "prediction_error": event.features.prediction_error,
            "novelty": event.features.novelty,
            "learning_progress": event.features.learning_progress,
            "ambition_relevance": event.features.ambition_relevance,
            "human_relevance": event.features.human_relevance,
            "outcome_magnitude": event.features.outcome_magnitude,
        },
        "payload": dict(event.payload),
    }


def _belief_payload(belief: BeliefRecord) -> dict[str, object]:
    return {
        "belief_id": belief.belief_id,
        "subject_code": belief.proposition.subject_code,
        "relation_code": belief.proposition.relation_code,
        "object_code": belief.proposition.object_code,
        "expected_value": belief.proposition.expected_value,
        "confidence": belief.confidence,
        "support_weight": belief.support_weight,
        "contradiction_weight": belief.contradiction_weight,
        "status": belief.status.value,
        "created_event_id": belief.created_event_id,
        "last_evidence_event_id": belief.last_evidence_event_id,
        "revision_count": belief.revision_count,
    }


def _evidence_payload(evidence: BeliefEvidence) -> dict[str, object]:
    return {
        "event_id": evidence.event_id,
        "polarity": evidence.polarity.value,
        "observed_value": evidence.observed_value,
        "weight": evidence.weight,
    }
