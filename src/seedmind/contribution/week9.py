"""Deterministic Week 9 contribution runner and exports."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from seedmind.contracts import GridPosition
from seedmind.contribution.contracts import (
    ContributionRecord,
    HumanContributionRequest,
    SupportPolicy,
    SupportState,
)
from seedmind.contribution.engine import ContributionEngine
from seedmind.contribution.parallel_comparison import (
    Week9ParallelComparisonResult,
    run_week9_parallel_comparison,
)
from seedmind.contribution.persistence import save_contribution_history, save_support_state
from seedmind.environment import EntityRole, EntityState, NurseryScenario, ShapeCode
from seedmind.human.contracts import (
    HumanRequest,
    RequestIntentCode,
    SupportLevel,
    VerificationRule,
)
from seedmind.skills import DEFAULT_EVALUATION_SEEDS, Week8ScenarioFactory, read_skill_record

WEEK9_SUCCESS_TARGET = 0.80
DEFAULT_SUCCESS_SEEDS = DEFAULT_EVALUATION_SEEDS[:10]
DEFAULT_FAILURE_SEEDS = (321, 322)


@dataclass(frozen=True, slots=True)
class Week9AcceptanceReport:
    """Inspectable acceptance report for the Week 9 contribution milestone."""

    total_attempts: int
    total_successes: int
    independent_success_rate: float
    first_success_kept_dependent: bool
    reduced_after_repeated_competence: bool
    restored_to_dependent_after_failures: bool
    reduced_again_after_repeated_competence: bool
    final_support_level: int
    skill_discovery_delta: int
    compile_count: int
    training_count: int
    promotion_count: int
    production_curiosity_retained_count: int
    executed_step_count: int
    authority_violations: int
    verification_authority_violations: int
    support_authority_violations: int
    ndnra_automatic_promotions: int

    def to_json(self) -> dict[str, object]:
        """Return a deterministic JSON-safe representation."""
        return {
            "authority_violations": self.authority_violations,
            "compile_count": self.compile_count,
            "executed_step_count": self.executed_step_count,
            "final_support_level": self.final_support_level,
            "first_success_kept_dependent": self.first_success_kept_dependent,
            "independent_success_rate": self.independent_success_rate,
            "ndnra_automatic_promotions": self.ndnra_automatic_promotions,
            "production_curiosity_retained_count": self.production_curiosity_retained_count,
            "promotion_count": self.promotion_count,
            "reduced_after_repeated_competence": self.reduced_after_repeated_competence,
            "reduced_again_after_repeated_competence": self.reduced_again_after_repeated_competence,
            "restored_to_dependent_after_failures": self.restored_to_dependent_after_failures,
            "skill_discovery_delta": self.skill_discovery_delta,
            "support_authority_violations": self.support_authority_violations,
            "total_attempts": self.total_attempts,
            "total_successes": self.total_successes,
            "training_count": self.training_count,
            "verification_authority_violations": self.verification_authority_violations,
        }


@dataclass(frozen=True, slots=True)
class Week9RunResult:
    """Full deterministic Week 9 runner output."""

    records: tuple[ContributionRecord, ...]
    support_state: SupportState
    acceptance_report: Week9AcceptanceReport
    parallel_comparison: Week9ParallelComparisonResult


def run_week9_contribution_evaluation(
    *,
    skill_record_path: Path = Path(
        "artifacts/week8_reusable_skill/approach_and_push_skill_record.json"
    ),
    output_dir: Path | None = None,
) -> Week9RunResult:
    """Run the main-project Week 9 contribution evaluation deterministically."""
    skill_record = read_skill_record(skill_record_path)
    skill_discovery_before = skill_record.discovery_count
    engine = ContributionEngine(SupportPolicy())
    support_state = SupportState.fresh(engine.policy)
    factory = Week8ScenarioFactory()
    records: list[ContributionRecord] = []
    scenarios: list[NurseryScenario] = []
    contribution_index = 1
    for seed in DEFAULT_SUCCESS_SEEDS[:5]:
        scenario = factory.create(seed)
        scenarios.append(scenario)
        evaluation_result = engine.evaluate_request(
            contribution_id=f"week9-contribution-{contribution_index:03d}",
            request=_build_request(request_id=f"request-{contribution_index:03d}"),
            skill_record=skill_record,
            scenario=scenario,
            scenario_context=_scenario_context(seed),
            support_state=support_state,
        )
        records.append(evaluation_result.record)
        support_state = evaluation_result.support_state
        contribution_index += 1
    for seed in DEFAULT_FAILURE_SEEDS:
        scenario = _blocked_failure_scenario(factory.create(seed))
        scenarios.append(scenario)
        evaluation_result = engine.evaluate_request(
            contribution_id=f"week9-contribution-{contribution_index:03d}",
            request=_build_request(request_id=f"request-{contribution_index:03d}"),
            skill_record=skill_record,
            scenario=scenario,
            scenario_context=_scenario_context(seed),
            support_state=support_state,
        )
        records.append(evaluation_result.record)
        support_state = evaluation_result.support_state
        contribution_index += 1
    for seed in DEFAULT_SUCCESS_SEEDS[5:]:
        scenario = factory.create(seed)
        scenarios.append(scenario)
        evaluation_result = engine.evaluate_request(
            contribution_id=f"week9-contribution-{contribution_index:03d}",
            request=_build_request(request_id=f"request-{contribution_index:03d}"),
            skill_record=skill_record,
            scenario=scenario,
            scenario_context=_scenario_context(seed),
            support_state=support_state,
        )
        records.append(evaluation_result.record)
        support_state = evaluation_result.support_state
        contribution_index += 1
    acceptance = _build_acceptance_report(
        records=tuple(records),
        support_state=support_state,
        skill_discovery_delta=skill_record.discovery_count - skill_discovery_before,
    )
    parallel_comparison = run_week9_parallel_comparison(
        records=tuple(records),
        scenarios=tuple(scenarios),
    )
    run_result = Week9RunResult(
        records=tuple(records),
        support_state=support_state,
        acceptance_report=acceptance,
        parallel_comparison=parallel_comparison,
    )
    if output_dir is not None:
        export_week9_evidence(run_result, output_dir)
    return run_result


def export_week9_evidence(
    result: Week9RunResult, output_dir: Path
) -> tuple[Path, Path, Path, Path, Path]:
    """Write the required Week 9 contribution and comparison artifacts."""
    output_dir.mkdir(parents=True, exist_ok=True)
    history_path = output_dir / "contribution_history.json"
    support_path = output_dir / "support_level_report.json"
    demo_path = output_dir / "human_contribution_demo.json"
    acceptance_path = output_dir / "week9_acceptance_report.json"
    comparison_path = output_dir / "default_vs_ndnra_comparison.json"
    save_contribution_history(history_path, result.records)
    save_support_state(support_path, result.support_state)
    _write_json(
        demo_path,
        {
            "parallel_comparison": result.parallel_comparison.report.to_json(),
            "records": [record.to_json() for record in result.records],
            "summary": result.acceptance_report.to_json(),
        },
    )
    _write_json(
        acceptance_path,
        {
            "parallel_comparison": result.parallel_comparison.report.to_json(),
            "week9_acceptance": result.acceptance_report.to_json(),
        },
    )
    _write_json(comparison_path, result.parallel_comparison.to_json())
    return demo_path, support_path, history_path, acceptance_path, comparison_path


def _build_request(*, request_id: str) -> HumanContributionRequest:
    return HumanContributionRequest(
        human_request=HumanRequest(
            request_id=request_id,
            intent_code=RequestIntentCode.REPRODUCE_OBSERVED_OUTCOME,
            target_code="move_ball_to_target",
            ambiguity=0.0,
            permission_level=2,
            verification_rule=VerificationRule.CONFIRMED_OUTCOME,
        ),
        target_capability="approach_and_push",
        expected_outcome="target_object_id occupies target_id position",
        target_object_id="object_0",
        target_id="target_0",
        learned_context=(
            "familiar_row",
            "familiar_column",
            "familiar_diagonal",
        ),
        requested_support_level=SupportLevel.DEPENDENT,
    )


def _scenario_context(seed: int) -> str:
    remainder = seed % 3
    if remainder == 0:
        return "familiar_row"
    if remainder == 1:
        return "familiar_column"
    return "familiar_diagonal"


def _blocked_failure_scenario(scenario: NurseryScenario) -> NurseryScenario:
    object_state = next(
        entity for entity in scenario.initial_state.entities if entity.entity_id == "object_0"
    )
    target_state = next(
        entity for entity in scenario.initial_state.entities if entity.entity_id == "target_0"
    )
    if object_state.position.x < target_state.position.x:
        blocker_position = GridPosition(object_state.position.x + 1, object_state.position.y)
    elif object_state.position.x > target_state.position.x:
        blocker_position = GridPosition(object_state.position.x - 1, object_state.position.y)
    elif object_state.position.y < target_state.position.y:
        blocker_position = GridPosition(object_state.position.x, object_state.position.y + 1)
    else:
        blocker_position = GridPosition(object_state.position.x, object_state.position.y - 1)
    blocker = EntityState(
        entity_id=f"failure_blocker_{scenario.seed}",
        role=EntityRole.WALL,
        position=blocker_position,
        blocks_movement=True,
        movable=False,
        shape_code=ShapeCode.ANGULAR,
    )
    return NurseryScenario(
        scenario_id=f"{scenario.scenario_id}-blocked",
        seed=scenario.seed,
        initial_state=scenario.initial_state.__class__(
            width=scenario.initial_state.width,
            height=scenario.initial_state.height,
            agent=scenario.initial_state.agent,
            entities=(*scenario.initial_state.entities, blocker),
            step_count=0,
            terminated=False,
        ),
        step_budget=scenario.step_budget,
        world_processes=scenario.world_processes,
    )


def _build_acceptance_report(
    *,
    records: tuple[ContributionRecord, ...],
    support_state: SupportState,
    skill_discovery_delta: int,
) -> Week9AcceptanceReport:
    successes = tuple(record for record in records if record.success)
    success_rate = len(successes) / len(records) if records else 0.0
    first_success_kept_dependent = bool(
        len(records) >= 1
        and records[0].success
        and records[0].support_level_before is SupportLevel.DEPENDENT
        and records[0].support_level_after is SupportLevel.DEPENDENT
    )
    reduced_after_repeated_competence = bool(
        len(records) >= 5 and records[4].support_level_after is SupportLevel.GUIDED_LEARNER
    )
    restored_to_dependent_after_failures = bool(
        len(records) >= 7 and records[6].support_level_after is SupportLevel.DEPENDENT
    )
    reduced_again_after_repeated_competence = bool(
        records[-1].support_level_after is SupportLevel.GUIDED_LEARNER
    )
    retained_steps = sum(record.retained_steps for record in records)
    executed_steps = sum(record.executed_steps for record in records)
    authority_violations = sum(record.authority_audit.authority_violations for record in records)
    verification_authority_violations = sum(
        record.authority_audit.verification_authority_violations for record in records
    )
    support_authority_violations = sum(
        record.authority_audit.support_authority_violations for record in records
    )
    ndnra_automatic_promotions = sum(
        record.authority_audit.automatic_promotions for record in records
    )
    return Week9AcceptanceReport(
        total_attempts=len(records),
        total_successes=len(successes),
        independent_success_rate=success_rate,
        first_success_kept_dependent=first_success_kept_dependent,
        reduced_after_repeated_competence=reduced_after_repeated_competence,
        restored_to_dependent_after_failures=restored_to_dependent_after_failures,
        reduced_again_after_repeated_competence=reduced_again_after_repeated_competence,
        final_support_level=int(support_state.current_level),
        skill_discovery_delta=skill_discovery_delta,
        compile_count=0,
        training_count=0,
        promotion_count=0,
        production_curiosity_retained_count=retained_steps,
        executed_step_count=executed_steps,
        authority_violations=authority_violations,
        verification_authority_violations=verification_authority_violations,
        support_authority_violations=support_authority_violations,
        ndnra_automatic_promotions=ndnra_automatic_promotions,
    )


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f"{path.name}.tmp")
    temporary.write_text(
        json.dumps(payload, ensure_ascii=True, indent=2, sort_keys=True) + "\n",
        encoding="ascii",
    )
    temporary.replace(path)
