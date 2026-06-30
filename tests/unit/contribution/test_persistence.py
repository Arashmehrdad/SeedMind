"""Focused tests for Week 9 contribution persistence."""

from __future__ import annotations

import json
from pathlib import Path

from seedmind.contribution import (
    ContributionEngine,
    SupportState,
    load_contribution_history,
    load_support_state,
    save_contribution_history,
    save_support_state,
)
from seedmind.contribution.week9 import _build_request, _scenario_context
from seedmind.skills import Week8ScenarioFactory, read_skill_record


def test_missing_or_corrupt_persistence_falls_back_conservatively(tmp_path: Path) -> None:
    support_path = tmp_path / "support_level_report.json"
    history_path = tmp_path / "contribution_history.json"

    assert load_support_state(support_path).current_level.value == 4
    assert load_contribution_history(history_path) == ()

    support_path.write_text("{bad json", encoding="ascii")
    history_path.write_text("{bad json", encoding="ascii")

    assert load_support_state(support_path).current_level.value == 4
    assert load_contribution_history(history_path) == ()

    support_payload = {
        "schema_version": 999,
        "payload_type": "support_state",
        "payload": {},
        "checksum": "0" * 64,
    }
    support_path.write_text(json.dumps(support_payload, ensure_ascii=True), encoding="ascii")

    assert load_support_state(support_path).current_level.value == 4


def test_persistence_round_trip_and_checksum_guard(tmp_path: Path) -> None:
    engine = ContributionEngine()
    result = engine.evaluate_request(
        contribution_id="persist-001",
        request=_build_request(request_id="request-persist"),
        skill_record=read_skill_record(
            Path("artifacts/week8_reusable_skill/approach_and_push_skill_record.json")
        ),
        scenario=Week8ScenarioFactory().create(301),
        scenario_context=_scenario_context(301),
        support_state=SupportState.fresh(),
    )
    history_path = tmp_path / "contribution_history.json"
    support_path = tmp_path / "support_level_report.json"

    save_contribution_history(history_path, (result.record,))
    save_support_state(support_path, result.support_state)
    save_contribution_history(history_path, (result.record,))
    save_support_state(support_path, result.support_state)

    assert not history_path.with_name(f"{history_path.name}.tmp").exists()
    assert not support_path.with_name(f"{support_path.name}.tmp").exists()
    assert load_contribution_history(history_path)[0].contribution_id == "persist-001"
    assert load_support_state(support_path).current_level == result.support_state.current_level

    payload = json.loads(support_path.read_text(encoding="ascii"))
    payload["payload"]["support_state"]["current_level"] = 3
    support_path.write_text(json.dumps(payload, ensure_ascii=True), encoding="ascii")

    assert load_support_state(support_path).current_level.value == 4

    history_payload = json.loads(history_path.read_text(encoding="ascii"))
    history_payload["checksum"] = "0" * 64
    history_path.write_text(json.dumps(history_payload, ensure_ascii=True), encoding="ascii")

    assert load_contribution_history(history_path) == ()
