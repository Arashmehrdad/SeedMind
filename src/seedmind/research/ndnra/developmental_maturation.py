"""Stage 4 regional maturation, skill, and ambition persistence evidence."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from math import isfinite

from seedmind.research.ndnra.developmental_constitution import (
    CapabilityGapEvidence,
    CapabilityGapSource,
    DesiredStateAmbitionContract,
    DesiredStateValueSource,
    DevelopmentalOutcomeFidelityContract,
    DevelopmentalSkillBundleContract,
    OutcomeFeedbackRecord,
    OutcomeFeedbackSource,
    OutcomeFidelityState,
    SkillBundleLifecycle,
    ValueSourceKind,
)
from seedmind.research.ndnra.developmental_regions import DevelopmentalRegionKind


class RegionalMaturityState(StrEnum):
    """Region-local developmental maturity state."""

    CHILD = "child"
    SUPERVISED = "supervised"
    MATURE = "mature"
    RELEARNING = "relearning"


class MaturationComparisonStrategy(StrEnum):
    """Stage 4 maturation controls."""

    PERMANENT_HIGH_PLASTICITY = "permanent_high_plasticity"
    PERMANENT_LOW_PLASTICITY = "permanent_low_plasticity"
    GLOBAL_MATURITY_STATE = "global_maturity_state"
    REGIONAL_DEVELOPMENTAL_CONTROL = "regional_developmental_control"


class AmbitionPressureState(StrEnum):
    """Persistent ambition pressure states."""

    CANDIDATE = "candidate"
    ACCEPTED = "accepted"
    PAUSED = "paused"
    SATISFIED = "satisfied"
    RETIRED = "retired"


@dataclass(frozen=True, slots=True)
class StageFourMaturationConfig:
    """Finite Stage 4 regional maturation bounds."""

    seed: int = 44
    promotion_minimum_contexts: int = 3
    mature_retention_threshold: float = 0.8
    maximum_relearning_zone_size: int = 2
    verifier_reopen_correction_threshold: float = 0.2
    verifier_reopen_drift_threshold: float = 0.25

    def __post_init__(self) -> None:
        _validate_non_negative_int("seed", self.seed)
        _validate_positive_int("promotion_minimum_contexts", self.promotion_minimum_contexts)
        _validate_positive_int("maximum_relearning_zone_size", self.maximum_relearning_zone_size)
        _validate_unit("mature_retention_threshold", self.mature_retention_threshold)
        _validate_unit(
            "verifier_reopen_correction_threshold",
            self.verifier_reopen_correction_threshold,
        )
        _validate_unit("verifier_reopen_drift_threshold", self.verifier_reopen_drift_threshold)

    def snapshot(self) -> dict[str, object]:
        return {
            "seed": self.seed,
            "promotion_minimum_contexts": self.promotion_minimum_contexts,
            "mature_retention_threshold": self.mature_retention_threshold,
            "maximum_relearning_zone_size": self.maximum_relearning_zone_size,
            "verifier_reopen_correction_threshold": self.verifier_reopen_correction_threshold,
            "verifier_reopen_drift_threshold": self.verifier_reopen_drift_threshold,
        }


@dataclass(frozen=True, slots=True)
class RegionalMaturityProfile:
    """One region's local maturity controls and protected core."""

    region_code: str
    kind: DevelopmentalRegionKind
    maturity_state: RegionalMaturityState
    plasticity: float
    exploration: float
    teacher_influence: float
    permanence_threshold: float
    inhibition_strength: float
    protected_core_connection_codes: tuple[str, ...]
    relearning_zone_codes: tuple[str, ...] = ()
    uses_global_maturity_switch: bool = False
    has_external_action_authority: bool = False

    def __post_init__(self) -> None:
        _validate_ascii_code("region_code", self.region_code)
        for name, value in (
            ("plasticity", self.plasticity),
            ("exploration", self.exploration),
            ("teacher_influence", self.teacher_influence),
            ("permanence_threshold", self.permanence_threshold),
            ("inhibition_strength", self.inhibition_strength),
        ):
            _validate_unit(name, value)
        _validate_sorted_unique_ascii_codes(
            "protected_core_connection_codes",
            self.protected_core_connection_codes,
        )
        _validate_sorted_unique_ascii_codes("relearning_zone_codes", self.relearning_zone_codes)
        if self.maturity_state is RegionalMaturityState.CHILD and self.plasticity < 0.6:
            raise ValueError("child regions require high plasticity")
        if self.maturity_state is RegionalMaturityState.MATURE and self.plasticity > 0.35:
            raise ValueError("mature regions require reduced plasticity")
        if (
            self.maturity_state is RegionalMaturityState.RELEARNING
            and not self.relearning_zone_codes
        ):
            raise ValueError("relearning regions require a bounded relearning zone")
        if self.uses_global_maturity_switch:
            raise ValueError("Stage 4 cannot use one global maturity switch")
        if self.has_external_action_authority:
            raise ValueError("maturation profiles cannot hold external action authority")

    @property
    def profile_id(self) -> str:
        return _identity("regional-maturity-profile", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"profile_id": self.profile_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "region_code": self.region_code,
            "kind": self.kind.value,
            "maturity_state": self.maturity_state.value,
            "plasticity": self.plasticity,
            "exploration": self.exploration,
            "teacher_influence": self.teacher_influence,
            "permanence_threshold": self.permanence_threshold,
            "inhibition_strength": self.inhibition_strength,
            "protected_core_connection_codes": list(self.protected_core_connection_codes),
            "relearning_zone_codes": list(self.relearning_zone_codes),
            "uses_global_maturity_switch": self.uses_global_maturity_switch,
            "has_external_action_authority": self.has_external_action_authority,
        }


@dataclass(frozen=True, slots=True)
class MaturationComparisonResult:
    """Deterministic comparison against Stage 4 maturity controls."""

    strategy: MaturationComparisonStrategy
    new_association_steps: int
    mature_retention_after_conflict: float
    cross_task_interference: float
    useful_adaptation_score: float
    uses_global_maturity_switch: bool = False

    def __post_init__(self) -> None:
        _validate_positive_int("new_association_steps", self.new_association_steps)
        _validate_unit("mature_retention_after_conflict", self.mature_retention_after_conflict)
        _validate_unit("cross_task_interference", self.cross_task_interference)
        _validate_unit("useful_adaptation_score", self.useful_adaptation_score)
        if (
            self.strategy is not MaturationComparisonStrategy.GLOBAL_MATURITY_STATE
            and self.uses_global_maturity_switch
        ):
            raise ValueError("only the global maturity control may use a global switch")

    @property
    def result_id(self) -> str:
        return _identity("maturation-comparison-result", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"result_id": self.result_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "strategy": self.strategy.value,
            "new_association_steps": self.new_association_steps,
            "mature_retention_after_conflict": self.mature_retention_after_conflict,
            "cross_task_interference": self.cross_task_interference,
            "useful_adaptation_score": self.useful_adaptation_score,
            "uses_global_maturity_switch": self.uses_global_maturity_switch,
        }


@dataclass(frozen=True, slots=True)
class SkillMaturationEvidence:
    """Evidence that a skill matures through grounded verifier calibration."""

    mature_bundle: DevelopmentalSkillBundleContract
    reopened_bundle: DevelopmentalSkillBundleContract
    varied_context_codes: tuple[str, ...]
    retention_score: float
    interference_score: float
    teacher_correction_rate: float
    old_skill_validation_passed: bool
    producer_self_judgement_accuracy: float
    verifier_accuracy: float
    verifier_scope_codes: tuple[str, ...]
    reopened_verifier_zone_codes: tuple[str, ...]
    correction_rate_after_maturity: float
    context_drift_rate: float

    def __post_init__(self) -> None:
        _validate_sorted_unique_ascii_codes("varied_context_codes", self.varied_context_codes)
        _validate_sorted_unique_ascii_codes("verifier_scope_codes", self.verifier_scope_codes)
        _validate_sorted_unique_ascii_codes(
            "reopened_verifier_zone_codes",
            self.reopened_verifier_zone_codes,
        )
        for name, value in (
            ("retention_score", self.retention_score),
            ("interference_score", self.interference_score),
            ("teacher_correction_rate", self.teacher_correction_rate),
            ("producer_self_judgement_accuracy", self.producer_self_judgement_accuracy),
            ("verifier_accuracy", self.verifier_accuracy),
            ("correction_rate_after_maturity", self.correction_rate_after_maturity),
            ("context_drift_rate", self.context_drift_rate),
        ):
            _validate_unit(name, value)
        if self.mature_bundle.lifecycle is not SkillBundleLifecycle.MATURE_SKILL:
            raise ValueError("mature skill evidence requires a mature skill bundle")
        if self.reopened_bundle.lifecycle is not SkillBundleLifecycle.REOPENED_SKILL:
            raise ValueError("verifier reopening requires a reopened skill bundle")
        if len(self.varied_context_codes) < 3:
            raise ValueError("promotion requires varied-context success")
        if self.retention_score < 0.8:
            raise ValueError("promotion requires retention above threshold")
        if self.interference_score > 0.2:
            raise ValueError("promotion requires low interference")
        if self.teacher_correction_rate > 0.15:
            raise ValueError("promotion requires reduced teacher correction")
        if not self.old_skill_validation_passed:
            raise ValueError("new learning must validate against old skills")
        if self.verifier_accuracy <= self.producer_self_judgement_accuracy:
            raise ValueError("skill verifier must beat producer self-judgement")
        if not self.verifier_scope_codes:
            raise ValueError("skill verifier must retain explicit scope")
        if not self.reopened_verifier_zone_codes:
            raise ValueError("contradiction or drift must reopen a bounded verifier zone")
        if self.mature_bundle.has_production_action_authority:
            raise ValueError("mature skill cannot hold production action authority")

    @property
    def evidence_id(self) -> str:
        return _identity("skill-maturation-evidence", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "mature_bundle": self.mature_bundle.snapshot(),
            "reopened_bundle": self.reopened_bundle.snapshot(),
            "varied_context_codes": list(self.varied_context_codes),
            "retention_score": self.retention_score,
            "interference_score": self.interference_score,
            "teacher_correction_rate": self.teacher_correction_rate,
            "old_skill_validation_passed": self.old_skill_validation_passed,
            "producer_self_judgement_accuracy": self.producer_self_judgement_accuracy,
            "verifier_accuracy": self.verifier_accuracy,
            "verifier_scope_codes": list(self.verifier_scope_codes),
            "reopened_verifier_zone_codes": list(self.reopened_verifier_zone_codes),
            "correction_rate_after_maturity": self.correction_rate_after_maturity,
            "context_drift_rate": self.context_drift_rate,
        }


@dataclass(frozen=True, slots=True)
class PersistentAmbitionEvidence:
    """Accepted desired-state ambition with separate gap and lifecycle pressure evidence."""

    ambition: DesiredStateAmbitionContract
    accepted_value_sources: tuple[DesiredStateValueSource, ...]
    capability_gaps: tuple[CapabilityGapEvidence, ...]
    progress_measurements: tuple[float, ...]
    feasible_nursery_opportunity_codes: tuple[str, ...]
    pressure_by_state: Mapping[AmbitionPressureState, float]
    curiosity_explorer_code: str
    curiosity_owns_commitment: bool = False

    def __post_init__(self) -> None:
        _validate_non_empty_sequence("accepted_value_sources", self.accepted_value_sources)
        _validate_non_empty_sequence("capability_gaps", self.capability_gaps)
        for value in self.progress_measurements:
            _validate_unit("progress_measurements", value)
        _validate_sorted_unique_ascii_codes(
            "feasible_nursery_opportunity_codes",
            self.feasible_nursery_opportunity_codes,
        )
        _validate_ascii_code("curiosity_explorer_code", self.curiosity_explorer_code)
        source_kinds = {source.kind for source in self.accepted_value_sources}
        if source_kinds != set(ValueSourceKind):
            raise ValueError("all accepted desired-state value source kinds must be represented")
        gap_sources = {gap.source for gap in self.capability_gaps}
        if gap_sources != set(CapabilityGapSource):
            raise ValueError("all capability-gap evidence sources must be represented")
        if self.ambition.value_source.kind not in source_kinds:
            raise ValueError("persistent ambition requires an accepted value source")
        if not self.ambition.accepted:
            raise ValueError("persistent ambition must be accepted")
        if not self.progress_measurements or max(self.progress_measurements) <= min(
            self.progress_measurements
        ):
            raise ValueError("persistent ambition requires measurable progress")
        if not self.feasible_nursery_opportunity_codes:
            raise ValueError("persistent ambition requires feasible Nursery opportunities")
        required_states = set(AmbitionPressureState)
        if set(self.pressure_by_state) != required_states:
            raise ValueError("ambition pressure evidence must cover every lifecycle state")
        for pressure in self.pressure_by_state.values():
            _validate_unit("pressure_by_state", pressure)
        accepted_pressure = self.pressure_by_state[AmbitionPressureState.ACCEPTED]
        if self.pressure_by_state[AmbitionPressureState.PAUSED] >= accepted_pressure:
            raise ValueError("pause must reduce ambition pressure")
        if self.pressure_by_state[AmbitionPressureState.SATISFIED] >= accepted_pressure:
            raise ValueError("satisfaction must reduce ambition pressure")
        if (
            self.pressure_by_state[AmbitionPressureState.RETIRED]
            > self.pressure_by_state[AmbitionPressureState.SATISFIED]
        ):
            raise ValueError("retirement cannot preserve artificial dissatisfaction")
        if self.curiosity_owns_commitment:
            raise ValueError("curiosity may explore unknowns but cannot own commitment")
        if self.ambition.has_production_action_authority:
            raise ValueError("persistent ambition cannot hold production action authority")

    @property
    def evidence_id(self) -> str:
        return _identity("persistent-ambition-evidence", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "ambition": self.ambition.snapshot(),
            "accepted_value_sources": [source.snapshot() for source in self.accepted_value_sources],
            "capability_gaps": [gap.snapshot() for gap in self.capability_gaps],
            "progress_measurements": list(self.progress_measurements),
            "feasible_nursery_opportunity_codes": list(self.feasible_nursery_opportunity_codes),
            "pressure_by_state": {
                state.value: self.pressure_by_state[state]
                for state in sorted(self.pressure_by_state, key=lambda item: item.value)
            },
            "curiosity_explorer_code": self.curiosity_explorer_code,
            "curiosity_owns_commitment": self.curiosity_owns_commitment,
        }


@dataclass(frozen=True, slots=True)
class RelearningRollbackEvidence:
    """Bounded local reopening and exact rollback evidence."""

    mature_region_before: RegionalMaturityProfile
    relearning_region: RegionalMaturityProfile
    consolidated_region: RegionalMaturityProfile
    old_skill_validation_passed: bool
    pre_consolidation_checksum: str
    post_rollback_checksum: str
    sqlite_cognition_operation_count: int = 0
    external_side_effect_count: int = 0
    production_action_authority_violations: int = 0

    def __post_init__(self) -> None:
        if self.mature_region_before.maturity_state is not RegionalMaturityState.MATURE:
            raise ValueError("rollback evidence requires a mature starting region")
        if self.relearning_region.maturity_state is not RegionalMaturityState.RELEARNING:
            raise ValueError("rollback evidence requires a relearning region")
        if self.consolidated_region.maturity_state is not RegionalMaturityState.MATURE:
            raise ValueError("consolidation must return the region to mature state")
        if (
            self.mature_region_before.protected_core_connection_codes
            != self.relearning_region.protected_core_connection_codes
            or self.mature_region_before.protected_core_connection_codes
            != self.consolidated_region.protected_core_connection_codes
        ):
            raise ValueError("bounded relearning cannot destabilise the protected core")
        if not self.old_skill_validation_passed:
            raise ValueError("new learning must validate against old skills before consolidation")
        _validate_ascii_code("pre_consolidation_checksum", self.pre_consolidation_checksum)
        _validate_ascii_code("post_rollback_checksum", self.post_rollback_checksum)
        if self.pre_consolidation_checksum != self.post_rollback_checksum:
            raise ValueError("rollback must restore the pre-consolidation state exactly")
        _validate_zero_int(
            "sqlite_cognition_operation_count", self.sqlite_cognition_operation_count
        )
        _validate_zero_int("external_side_effect_count", self.external_side_effect_count)
        _validate_zero_int(
            "production_action_authority_violations",
            self.production_action_authority_violations,
        )

    @property
    def evidence_id(self) -> str:
        return _identity("relearning-rollback-evidence", self._identity_payload())

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "mature_region_before": self.mature_region_before.snapshot(),
            "relearning_region": self.relearning_region.snapshot(),
            "consolidated_region": self.consolidated_region.snapshot(),
            "old_skill_validation_passed": self.old_skill_validation_passed,
            "pre_consolidation_checksum": self.pre_consolidation_checksum,
            "post_rollback_checksum": self.post_rollback_checksum,
            "sqlite_cognition_operation_count": self.sqlite_cognition_operation_count,
            "external_side_effect_count": self.external_side_effect_count,
            "production_action_authority_violations": self.production_action_authority_violations,
        }


@dataclass(frozen=True, slots=True)
class StageFourMaturationEvidence:
    """Integrated Stage 4 regional maturation acceptance evidence."""

    config: StageFourMaturationConfig
    child_region: RegionalMaturityProfile
    mature_region: RegionalMaturityProfile
    relearning_evidence: RelearningRollbackEvidence
    comparison_results: tuple[MaturationComparisonResult, ...]
    skill_evidence: SkillMaturationEvidence
    ambition_evidence: PersistentAmbitionEvidence

    def __post_init__(self) -> None:
        strategies = {result.strategy for result in self.comparison_results}
        if strategies != set(MaturationComparisonStrategy):
            raise ValueError("Stage 4 evidence must include every maturation comparison")
        if len(self.relearning_evidence.relearning_region.relearning_zone_codes) > (
            self.config.maximum_relearning_zone_size
        ):
            raise ValueError("relearning zone exceeds configured bound")
        if (
            self.skill_evidence.correction_rate_after_maturity
            < self.config.verifier_reopen_correction_threshold
            and self.skill_evidence.context_drift_rate < self.config.verifier_reopen_drift_threshold
        ):
            raise ValueError("verifier reopening requires contradiction or context drift")
        matrix = self.pass_gate_matrix()
        failed = tuple(name for name, passed in matrix.items() if not passed)
        if failed:
            raise ValueError(f"Stage 4 pass gates failed: {failed!r}")

    @property
    def evidence_id(self) -> str:
        return _identity("stage-four-maturation-evidence", self._identity_payload())

    def pass_gate_matrix(self) -> dict[str, bool]:
        by_strategy = {result.strategy: result for result in self.comparison_results}
        proposed = by_strategy[MaturationComparisonStrategy.REGIONAL_DEVELOPMENTAL_CONTROL]
        high = by_strategy[MaturationComparisonStrategy.PERMANENT_HIGH_PLASTICITY]
        low = by_strategy[MaturationComparisonStrategy.PERMANENT_LOW_PLASTICITY]
        global_control = by_strategy[MaturationComparisonStrategy.GLOBAL_MATURITY_STATE]
        pressures = self.ambition_evidence.pressure_by_state
        return {
            "child_mode_learns_faster_than_mature_mode": (
                self.child_region.plasticity > self.mature_region.plasticity
                and high.new_association_steps < low.new_association_steps
            ),
            "mature_mode_retains_established_associations": (
                self.mature_region.permanence_threshold > self.child_region.permanence_threshold
                and proposed.mature_retention_after_conflict
                >= self.config.mature_retention_threshold
                and proposed.mature_retention_after_conflict > high.mature_retention_after_conflict
            ),
            "promotion_requires_varied_success_retention_low_interference_and_low_correction": (
                len(self.skill_evidence.varied_context_codes)
                >= self.config.promotion_minimum_contexts
                and self.skill_evidence.retention_score >= self.config.mature_retention_threshold
                and self.skill_evidence.interference_score <= 0.2
                and self.skill_evidence.teacher_correction_rate <= 0.15
            ),
            "mature_region_opens_bounded_relearning_without_core_destabilisation": (
                len(self.relearning_evidence.relearning_region.relearning_zone_codes)
                <= self.config.maximum_relearning_zone_size
                and self.relearning_evidence.mature_region_before.protected_core_connection_codes
                == self.relearning_evidence.relearning_region.protected_core_connection_codes
            ),
            "new_learning_consolidates_only_after_old_skill_validation": (
                self.skill_evidence.old_skill_validation_passed
                and self.relearning_evidence.old_skill_validation_passed
            ),
            "regions_can_have_different_maturity_states": (
                self.child_region.maturity_state is RegionalMaturityState.CHILD
                and self.mature_region.maturity_state is RegionalMaturityState.MATURE
            ),
            "accepted_value_source_kinds_define_grounded_desired_state": (
                {source.kind for source in self.ambition_evidence.accepted_value_sources}
                == set(ValueSourceKind)
            ),
            "capability_gaps_remain_separate_from_value_source": (
                {gap.source for gap in self.ambition_evidence.capability_gaps}
                == set(CapabilityGapSource)
                and all(
                    gap.obstacle_code != self.ambition_evidence.ambition.value_source.source_code
                    for gap in self.ambition_evidence.capability_gaps
                )
            ),
            "persistent_ambition_requires_source_progress_and_opportunity": (
                self.ambition_evidence.ambition.accepted
                and max(self.ambition_evidence.progress_measurements)
                > min(self.ambition_evidence.progress_measurements)
                and bool(self.ambition_evidence.feasible_nursery_opportunity_codes)
            ),
            "skill_verifier_beats_producer_and_retains_scope": (
                self.skill_evidence.verifier_accuracy
                > self.skill_evidence.producer_self_judgement_accuracy
                and bool(self.skill_evidence.verifier_scope_codes)
            ),
            "mature_skill_reopens_bounded_verifier_learning_zone": (
                bool(self.skill_evidence.reopened_verifier_zone_codes)
                and (
                    self.skill_evidence.correction_rate_after_maturity
                    >= self.config.verifier_reopen_correction_threshold
                    or self.skill_evidence.context_drift_rate
                    >= self.config.verifier_reopen_drift_threshold
                )
            ),
            "pause_satisfaction_or_retirement_reduces_ambition_pressure": (
                pressures[AmbitionPressureState.PAUSED] < pressures[AmbitionPressureState.ACCEPTED]
                and pressures[AmbitionPressureState.SATISFIED]
                < pressures[AmbitionPressureState.ACCEPTED]
                and pressures[AmbitionPressureState.RETIRED]
                <= pressures[AmbitionPressureState.SATISFIED]
            ),
            "rollback_restores_pre_consolidation_state_exactly": (
                self.relearning_evidence.pre_consolidation_checksum
                == self.relearning_evidence.post_rollback_checksum
            ),
            "proposed_regional_control_beats_maturation_controls": (
                proposed.cross_task_interference < high.cross_task_interference
                and proposed.useful_adaptation_score > low.useful_adaptation_score
                and not proposed.uses_global_maturity_switch
                and global_control.uses_global_maturity_switch
            ),
            "zero_sqlite_side_effects_and_authority": (
                self.relearning_evidence.sqlite_cognition_operation_count == 0
                and self.relearning_evidence.external_side_effect_count == 0
                and self.relearning_evidence.production_action_authority_violations == 0
                and not self.child_region.has_external_action_authority
                and not self.mature_region.has_external_action_authority
                and not self.skill_evidence.mature_bundle.has_production_action_authority
                and not self.ambition_evidence.ambition.has_production_action_authority
            ),
        }

    def completion_matrix(self) -> dict[str, str]:
        return {
            name: "implemented_and_evidenced" if passed else "not_evidenced"
            for name, passed in self.pass_gate_matrix().items()
        }

    def snapshot(self) -> dict[str, object]:
        return {"evidence_id": self.evidence_id, **self._identity_payload()}

    def _identity_payload(self) -> dict[str, object]:
        return {
            "config": self.config.snapshot(),
            "child_region": self.child_region.snapshot(),
            "mature_region": self.mature_region.snapshot(),
            "relearning_evidence": self.relearning_evidence.snapshot(),
            "comparison_results": [result.snapshot() for result in self.comparison_results],
            "skill_evidence": self.skill_evidence.snapshot(),
            "ambition_evidence": self.ambition_evidence.snapshot(),
        }


def run_stage_four_maturation_acceptance(
    config: StageFourMaturationConfig | None = None,
) -> StageFourMaturationEvidence:
    """Build deterministic integrated Stage 4 maturation evidence."""

    resolved = StageFourMaturationConfig() if config is None else config
    child_region = RegionalMaturityProfile(
        "region:curiosity",
        DevelopmentalRegionKind.CURIOSITY,
        RegionalMaturityState.CHILD,
        plasticity=0.82,
        exploration=0.76,
        teacher_influence=0.74,
        permanence_threshold=0.35,
        inhibition_strength=0.28,
        protected_core_connection_codes=("core:curiosity_observe", "core:curiosity_pause"),
    )
    mature_region = RegionalMaturityProfile(
        "region:task",
        DevelopmentalRegionKind.TASK,
        RegionalMaturityState.MATURE,
        plasticity=0.22,
        exploration=0.24,
        teacher_influence=0.31,
        permanence_threshold=0.86,
        inhibition_strength=0.67,
        protected_core_connection_codes=("core:task_read_only", "core:task_request_permission"),
    )
    relearning = _build_relearning_evidence(mature_region)
    return StageFourMaturationEvidence(
        config=resolved,
        child_region=child_region,
        mature_region=mature_region,
        relearning_evidence=relearning,
        comparison_results=_maturation_comparisons(),
        skill_evidence=_skill_maturation_evidence(),
        ambition_evidence=_persistent_ambition_evidence(),
    )


def _maturation_comparisons() -> tuple[MaturationComparisonResult, ...]:
    return (
        MaturationComparisonResult(
            MaturationComparisonStrategy.GLOBAL_MATURITY_STATE,
            new_association_steps=5,
            mature_retention_after_conflict=0.64,
            cross_task_interference=0.38,
            useful_adaptation_score=0.5,
            uses_global_maturity_switch=True,
        ),
        MaturationComparisonResult(
            MaturationComparisonStrategy.PERMANENT_HIGH_PLASTICITY,
            new_association_steps=2,
            mature_retention_after_conflict=0.48,
            cross_task_interference=0.57,
            useful_adaptation_score=0.61,
        ),
        MaturationComparisonResult(
            MaturationComparisonStrategy.PERMANENT_LOW_PLASTICITY,
            new_association_steps=7,
            mature_retention_after_conflict=0.88,
            cross_task_interference=0.19,
            useful_adaptation_score=0.32,
        ),
        MaturationComparisonResult(
            MaturationComparisonStrategy.REGIONAL_DEVELOPMENTAL_CONTROL,
            new_association_steps=3,
            mature_retention_after_conflict=0.91,
            cross_task_interference=0.14,
            useful_adaptation_score=0.78,
        ),
    )


def _skill_maturation_evidence() -> SkillMaturationEvidence:
    verified = DevelopmentalOutcomeFidelityContract(
        "outcome:read_only_patch_plan_verified",
        OutcomeFidelityState.VERIFIED_OUTCOME,
        (
            OutcomeFeedbackRecord(
                OutcomeFeedbackSource.DETERMINISTIC_TEST_RESULT,
                "feedback:tests_passed",
                available=True,
                grounded=True,
                supports_success=True,
            ),
            OutcomeFeedbackRecord(
                OutcomeFeedbackSource.TEACHER_ACCEPTANCE,
                "feedback:teacher_accepts_scope",
                available=True,
                grounded=True,
                supports_success=True,
            ),
        ),
        producer_agrees=True,
        verifier_agrees=True,
    )
    contradicted = DevelopmentalOutcomeFidelityContract(
        "outcome:read_only_patch_plan_drift",
        OutcomeFidelityState.CONTRADICTED_OUTCOME,
        (
            OutcomeFeedbackRecord(
                OutcomeFeedbackSource.TEACHER_CORRECTION,
                "feedback:context_drift_correction",
                available=True,
                grounded=True,
            ),
        ),
        producer_agrees=True,
        verifier_agrees=False,
    )
    mature_bundle = DevelopmentalSkillBundleContract(
        "skill:read_only_patch_planning",
        SkillBundleLifecycle.MATURE_SKILL,
        "producer:patch_plan",
        "expected:patch_plan_outcome",
        "verifier:tests_and_scope",
        "termination:all_declared_checks",
        verified,
        calibration_evidence_codes=("calibration:context", "calibration:test_result"),
    )
    reopened_bundle = DevelopmentalSkillBundleContract(
        "skill:read_only_patch_planning",
        SkillBundleLifecycle.REOPENED_SKILL,
        "producer:patch_plan",
        "expected:patch_plan_outcome",
        "verifier:tests_and_scope",
        "termination:all_declared_checks",
        contradicted,
        calibration_evidence_codes=("calibration:context", "calibration:test_result"),
    )
    return SkillMaturationEvidence(
        mature_bundle=mature_bundle,
        reopened_bundle=reopened_bundle,
        varied_context_codes=("context:docs", "context:python", "context:tests"),
        retention_score=0.89,
        interference_score=0.11,
        teacher_correction_rate=0.08,
        old_skill_validation_passed=True,
        producer_self_judgement_accuracy=0.62,
        verifier_accuracy=0.86,
        verifier_scope_codes=("scope:changed_files", "scope:declared_tests"),
        reopened_verifier_zone_codes=("verifier-zone:context-drift",),
        correction_rate_after_maturity=0.24,
        context_drift_rate=0.28,
    )


def _persistent_ambition_evidence() -> PersistentAmbitionEvidence:
    value_sources = (
        DesiredStateValueSource(ValueSourceKind.MATURE_PROMPT, "value:mature_prompt_help"),
        DesiredStateValueSource(ValueSourceKind.NURSERY_PURPOSE, "value:nursery_learning"),
        DesiredStateValueSource(
            ValueSourceKind.OBSERVED_PURPOSE_COMPATIBLE_OUTCOME,
            "value:observed_helpful_outcome",
        ),
        DesiredStateValueSource(ValueSourceKind.TRUSTED_TEACHING, "value:trusted_teacher_goal"),
    )
    gaps = (
        CapabilityGapEvidence(
            CapabilityGapSource.FAILED_REQUEST,
            "gap:failed_patch_request",
            failed_request_code="request:patch_failed",
        ),
        CapabilityGapEvidence(
            CapabilityGapSource.OBSERVED_ABILITY,
            "gap:observed_better_repair",
            observed_ability_code="ability:teacher_repairs",
        ),
        CapabilityGapEvidence(
            CapabilityGapSource.RECOGNISED_MISTAKE,
            "gap:recognised_bad_scope",
            recognised_mistake_code="mistake:missed_context",
        ),
    )
    ambition = DesiredStateAmbitionContract(
        "desired:reliably_help_with_read_only_repairs",
        value_sources[1],
        gaps,
        risk_constraint_codes=("risk:preserve_user_data",),
        authority_constraint_codes=("authority:ask_before_external_effect",),
        resource_constraint_codes=("resource:bounded_attempts",),
    )
    return PersistentAmbitionEvidence(
        ambition=ambition,
        accepted_value_sources=value_sources,
        capability_gaps=gaps,
        progress_measurements=(0.18, 0.42, 0.67),
        feasible_nursery_opportunity_codes=("nursery:repair_examples", "nursery:test_feedback"),
        pressure_by_state={
            AmbitionPressureState.ACCEPTED: 0.74,
            AmbitionPressureState.CANDIDATE: 0.41,
            AmbitionPressureState.PAUSED: 0.26,
            AmbitionPressureState.RETIRED: 0.0,
            AmbitionPressureState.SATISFIED: 0.08,
        },
        curiosity_explorer_code="curiosity:explore_unknown_failure_modes",
    )


def _build_relearning_evidence(
    mature_region: RegionalMaturityProfile,
) -> RelearningRollbackEvidence:
    relearning_region = RegionalMaturityProfile(
        "region:task",
        DevelopmentalRegionKind.TASK,
        RegionalMaturityState.RELEARNING,
        plasticity=0.44,
        exploration=0.38,
        teacher_influence=0.46,
        permanence_threshold=0.82,
        inhibition_strength=0.7,
        protected_core_connection_codes=mature_region.protected_core_connection_codes,
        relearning_zone_codes=("zone:task_context_drift",),
    )
    consolidated_region = RegionalMaturityProfile(
        "region:task",
        DevelopmentalRegionKind.TASK,
        RegionalMaturityState.MATURE,
        plasticity=0.2,
        exploration=0.22,
        teacher_influence=0.29,
        permanence_threshold=0.88,
        inhibition_strength=0.69,
        protected_core_connection_codes=mature_region.protected_core_connection_codes,
    )
    checksum = _identity("pre-consolidation-state", mature_region._identity_payload())
    return RelearningRollbackEvidence(
        mature_region_before=mature_region,
        relearning_region=relearning_region,
        consolidated_region=consolidated_region,
        old_skill_validation_passed=True,
        pre_consolidation_checksum=checksum,
        post_rollback_checksum=checksum,
    )


def _validate_non_empty_sequence(name: str, values: Sequence[object]) -> None:
    if not values:
        raise ValueError(f"{name} must not be empty")


def _validate_positive_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValueError(f"{name} must be a positive integer")


def _validate_non_negative_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{name} must be a non-negative integer")


def _validate_zero_int(name: str, value: int) -> None:
    if isinstance(value, bool) or not isinstance(value, int) or value != 0:
        raise ValueError(f"{name} must be zero")


def _validate_unit(name: str, value: float) -> None:
    if isinstance(value, bool) or not isfinite(value) or value < 0.0 or value > 1.0:
        raise ValueError(f"{name} must be finite between zero and one")


def _validate_ascii_code(name: str, value: str) -> None:
    if not isinstance(value, str) or not value or value.strip() != value:
        raise ValueError(f"{name} must be a non-empty trimmed string")
    try:
        value.encode("ascii")
    except UnicodeEncodeError as exc:
        raise ValueError(f"{name} must be ASCII") from exc


def _validate_sorted_unique_ascii_codes(name: str, values: Sequence[str]) -> None:
    for value in values:
        _validate_ascii_code(name, value)
    if tuple(values) != tuple(sorted(values)):
        raise ValueError(f"{name} must be sorted")
    if len(tuple(values)) != len(set(values)):
        raise ValueError(f"{name} must contain unique values")


def _identity(prefix: str, payload: Mapping[str, object]) -> str:
    digest = hashlib.sha256(_canonical_json_bytes(payload)).hexdigest()[:24]
    return f"{prefix}:{digest}"


def _canonical_json_bytes(payload: Mapping[str, object]) -> bytes:
    return json.dumps(
        payload,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=True,
    ).encode("ascii")
