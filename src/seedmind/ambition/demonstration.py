"""Detect repeated goal-directed outcomes from raw teacher demonstrations."""

from __future__ import annotations

import json
from dataclasses import dataclass
from hashlib import sha256
from math import isfinite
from pathlib import Path
from statistics import fmean

from seedmind.ambition.engine import (
    AmbitionCandidate,
    AmbitionOrigin,
    MilestoneCode,
)
from seedmind.contracts import ObservationPacket


@dataclass(frozen=True, slots=True)
class DemonstrationDetectorConfig:
    """Evidence thresholds and budgets for demonstration-derived ambitions."""

    minimum_repetitions: int = 3
    body_channel_count: int = 6
    delta_threshold: float = 1e-6
    confirmation_threshold: float = 0.5
    quantization_digits: int = 6
    practice_budget: int = 64
    play_budget: int = 8

    def __post_init__(self) -> None:
        if self.minimum_repetitions <= 0:
            raise ValueError("minimum_repetitions must be positive")
        if self.body_channel_count < 0:
            raise ValueError("body_channel_count must not be negative")
        if not isfinite(self.delta_threshold) or self.delta_threshold < 0.0:
            raise ValueError("delta_threshold must be finite and non-negative")
        if (
            not isfinite(self.confirmation_threshold)
            or not 0.0 <= self.confirmation_threshold <= 1.0
        ):
            raise ValueError("confirmation_threshold must be between zero and one")
        if self.quantization_digits < 0:
            raise ValueError("quantization_digits must not be negative")
        if self.practice_budget <= 0:
            raise ValueError("practice_budget must be positive")
        if self.play_budget < 0:
            raise ValueError("play_budget must not be negative")


@dataclass(frozen=True, slots=True)
class ObservedDemonstration:
    """One bounded teacher episode represented by raw start and end packets."""

    episode_id: str
    start_observation: ObservationPacket
    end_observation: ObservationPacket
    external_change_steps: int
    outcome_signal: float

    def __post_init__(self) -> None:
        if not self.episode_id.strip():
            raise ValueError("episode_id must not be empty")
        if self.start_observation.episode_id != self.episode_id:
            raise ValueError("start observation episode does not match demonstration")
        if self.end_observation.episode_id != self.episode_id:
            raise ValueError("end observation episode does not match demonstration")
        if len(self.start_observation.sensor_values) != len(self.end_observation.sensor_values):
            raise ValueError("demonstration sensor widths must match")
        if self.end_observation.step_id <= self.start_observation.step_id:
            raise ValueError("demonstration must advance at least one step")
        if self.external_change_steps <= 0:
            raise ValueError("external_change_steps must be positive")
        if not isfinite(self.outcome_signal) or not 0.0 <= self.outcome_signal <= 1.0:
            raise ValueError("outcome_signal must be between zero and one")


@dataclass(frozen=True, slots=True)
class OutcomeSignature:
    """Stable raw external-change fingerprint with no semantic entity labels."""

    signature_id: str
    changed_channels: tuple[tuple[int, float], ...]

    def __post_init__(self) -> None:
        if not self.signature_id.strip():
            raise ValueError("signature_id must not be empty")
        if not self.changed_channels:
            raise ValueError("changed_channels must not be empty")
        indices = tuple(index for index, _ in self.changed_channels)
        if len(indices) != len(set(indices)):
            raise ValueError("changed channel indices must be unique")
        if any(index < 0 for index in indices):
            raise ValueError("changed channel indices must not be negative")


@dataclass(frozen=True, slots=True)
class DemonstrationEvidence:
    """Repeated observations supporting one raw goal-directed outcome."""

    signature: OutcomeSignature
    episode_ids: tuple[str, ...]
    confirmed_episode_count: int
    mean_outcome_signal: float
    mean_external_change_steps: float

    def __post_init__(self) -> None:
        if not self.episode_ids:
            raise ValueError("episode_ids must not be empty")
        if len(self.episode_ids) != len(set(self.episode_ids)):
            raise ValueError("episode_ids must be unique")
        if not 0 <= self.confirmed_episode_count <= len(self.episode_ids):
            raise ValueError("confirmed_episode_count must fit the evidence")
        if not 0.0 <= self.mean_outcome_signal <= 1.0:
            raise ValueError("mean_outcome_signal must be between zero and one")
        if self.mean_external_change_steps <= 0.0:
            raise ValueError("mean_external_change_steps must be positive")

    @property
    def repetition_count(self) -> int:
        """Return the number of distinct matching demonstrations."""
        return len(self.episode_ids)


@dataclass(slots=True)
class _EvidenceAccumulator:
    signature: OutcomeSignature
    episode_ids: list[str]
    confirmed_episode_count: int
    outcome_signals: list[float]
    external_change_steps: list[int]

    def snapshot(self) -> DemonstrationEvidence:
        return DemonstrationEvidence(
            signature=self.signature,
            episode_ids=tuple(self.episode_ids),
            confirmed_episode_count=self.confirmed_episode_count,
            mean_outcome_signal=fmean(self.outcome_signals),
            mean_external_change_steps=fmean(self.external_change_steps),
        )


class GoalDirectedOutcomeDetector:
    """Group repeated raw outcomes and propose a persistent capability ambition."""

    def __init__(self, config: DemonstrationDetectorConfig | None = None) -> None:
        self.config = DemonstrationDetectorConfig() if config is None else config
        self._evidence: dict[str, _EvidenceAccumulator] = {}
        self._seen_episode_ids: set[str] = set()

    @property
    def observed_episode_count(self) -> int:
        """Return the total number of distinct teacher episodes observed."""
        return len(self._seen_episode_ids)

    def observe(
        self,
        demonstration: ObservedDemonstration,
    ) -> AmbitionCandidate | None:
        """Update repeated-outcome evidence and emit a candidate when sufficient."""
        if demonstration.episode_id in self._seen_episode_ids:
            raise ValueError("demonstration episode has already been observed")
        self._seen_episode_ids.add(demonstration.episode_id)
        signature = self._signature(demonstration)
        if signature is None:
            return None
        accumulator = self._evidence.get(signature.signature_id)
        if accumulator is None:
            accumulator = _EvidenceAccumulator(
                signature=signature,
                episode_ids=[],
                confirmed_episode_count=0,
                outcome_signals=[],
                external_change_steps=[],
            )
            self._evidence[signature.signature_id] = accumulator
        accumulator.episode_ids.append(demonstration.episode_id)
        accumulator.outcome_signals.append(demonstration.outcome_signal)
        accumulator.external_change_steps.append(demonstration.external_change_steps)
        if demonstration.outcome_signal >= self.config.confirmation_threshold:
            accumulator.confirmed_episode_count += 1
        evidence = accumulator.snapshot()
        if evidence.repetition_count < self.config.minimum_repetitions:
            return None
        if evidence.confirmed_episode_count < self.config.minimum_repetitions:
            return None
        repeatability = min(
            evidence.repetition_count / self.config.minimum_repetitions,
            1.0,
        )
        efficiency = 1.0 / max(evidence.mean_external_change_steps, 1.0)
        attainability = min(0.55 + 0.25 * repeatability + 0.20 * efficiency, 1.0)
        return AmbitionCandidate(
            candidate_id=evidence.signature.signature_id,
            target_capability="control_external_change",
            origin=AmbitionOrigin.OBSERVED_DEMONSTRATION,
            source_evidence_id=evidence.signature.signature_id,
            evidence_count=evidence.repetition_count,
            purpose_relevance=evidence.mean_outcome_signal,
            expected_value=evidence.mean_outcome_signal,
            attainability=attainability,
            proposed_commitment=min(0.60 + 0.10 * evidence.repetition_count, 1.0),
            practice_budget=self.config.practice_budget,
            play_budget=self.config.play_budget,
            milestone_codes=(
                MilestoneCode.LOCATE_CAUSAL_SOURCE,
                MilestoneCode.PRODUCE_INTERACTION,
                MilestoneCode.PRODUCE_REPEATABLE_EXTERNAL_CHANGE,
                MilestoneCode.MATCH_DEMONSTRATED_OUTCOME,
            ),
        )

    def evidence(self) -> tuple[DemonstrationEvidence, ...]:
        """Return immutable evidence ordered by stable signature identifier."""
        return tuple(self._evidence[key].snapshot() for key in sorted(self._evidence))

    def _signature(
        self,
        demonstration: ObservedDemonstration,
    ) -> OutcomeSignature | None:
        start = demonstration.start_observation.sensor_values
        end = demonstration.end_observation.sensor_values
        if self.config.body_channel_count >= len(start):
            raise ValueError("body_channel_count must leave external sensor channels")
        changed = tuple(
            (index, round(end[index] - start[index], self.config.quantization_digits))
            for index in range(self.config.body_channel_count, len(start))
            if abs(end[index] - start[index]) > self.config.delta_threshold
        )
        if not changed:
            return None
        encoded = ";".join(f"{index}:{delta:.12g}" for index, delta in changed)
        signature_id = f"outcome-{sha256(encoded.encode('ascii')).hexdigest()[:12]}"
        return OutcomeSignature(
            signature_id=signature_id,
            changed_channels=changed,
        )


def export_demonstration_evidence(
    detector: GoalDirectedOutcomeDetector,
    path: Path,
) -> None:
    """Write repeated raw-outcome evidence as inspectable ASCII JSON."""
    payload = {
        "observed_episode_count": detector.observed_episode_count,
        "evidence": [
            {
                "signature_id": item.signature.signature_id,
                "changed_channels": [
                    {"sensor_index": index, "delta": delta}
                    for index, delta in item.signature.changed_channels
                ],
                "episode_ids": list(item.episode_ids),
                "repetition_count": item.repetition_count,
                "confirmed_episode_count": item.confirmed_episode_count,
                "mean_outcome_signal": item.mean_outcome_signal,
                "mean_external_change_steps": item.mean_external_change_steps,
            }
            for item in detector.evidence()
        ],
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_name(f"{path.name}.tmp")
    temporary_path.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary_path.replace(path)
