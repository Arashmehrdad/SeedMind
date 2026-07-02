"""Focused tests for the Week 14 scripted demonstration manifest."""

from __future__ import annotations

from pathlib import Path

from seedmind.observatory import build_demo_manifest, write_demo_manifest

COMMITTED_PATH = Path("artifacts/week14_packaging/demo_manifest.json")


def test_demo_manifest_has_fixed_order_and_duration_bound() -> None:
    manifest = build_demo_manifest()
    scene_ids = [scene["scene_id"] for scene in manifest["scenes"]]

    assert scene_ids == [
        "scene_01_authority",
        "scene_02_skill_and_contribution",
        "scene_03_ambition_and_teaching",
        "scene_04_specialist_rejection",
        "scene_05_rollback_checkpoint",
        "scene_06_claims",
        "scene_07_limitations",
    ]
    assert manifest["declared_total_duration_seconds"] <= 180
    assert manifest["no_wait_supported"] is True


def test_demo_manifest_pairs_narrow_and_broad_results() -> None:
    manifest = build_demo_manifest()
    specialist_scene = manifest["scenes"][3]
    narration = specialist_scene["narration"]
    assert "52/52" in narration
    assert "0/32" in narration
    assert "rejected and rolled back" in narration


def test_committed_demo_manifest_matches_fresh_export(tmp_path: Path) -> None:
    write_demo_manifest(tmp_path)
    generated = (tmp_path / "artifacts/week14_packaging/demo_manifest.json").read_bytes()
    committed = COMMITTED_PATH.read_bytes()
    assert generated == committed
    assert not tuple((tmp_path / "artifacts/week14_packaging").glob("*.tmp"))
