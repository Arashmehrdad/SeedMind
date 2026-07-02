"""Focused tests for the Week 14 observatory packaging layer."""

from __future__ import annotations

import json
import threading
import urllib.request
from pathlib import Path

from seedmind.observatory import build_observatory_snapshot, create_observatory_server
from seedmind.observatory.app import write_observatory_snapshot

COMMITTED_PATH = Path("artifacts/week14_packaging/observatory_snapshot.json")


def test_observatory_snapshot_contains_required_boundaries() -> None:
    snapshot = build_observatory_snapshot()

    assert snapshot["snapshot_label"] == "Committed snapshot evidence only"
    assert snapshot["authority_checkpoint_sha256"] == (
        "dde86c0f167653e54db4db74b477fa271b1ee8a2b09e452d0aa622f80d049093"
    )
    assert snapshot["week14_capability_boundary"] == (
        "Week 14 is packaging rather than new cognitive capability."
    )
    metrics = {item["metric_id"]: item["value"] for item in snapshot["metrics"]}
    assert metrics["specialist_narrow"] == "52/52"
    assert metrics["specialist_broad"] == "0/32"
    section_ids = [section["section_id"] for section in snapshot["sections"]]
    assert section_ids == [
        "authority",
        "skill",
        "contribution",
        "ambition",
        "apprenticeship",
        "specialist",
        "rollback",
    ]


def test_observatory_server_serves_html_and_snapshot_api() -> None:
    snapshot = build_observatory_snapshot()
    server = create_observatory_server(snapshot, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    address = server.server_address
    host = address[0]
    port = address[1]
    assert isinstance(host, str)
    assert isinstance(port, int)
    try:
        html = urllib.request.urlopen(f"http://{host}:{port}/", timeout=5).read().decode("utf-8")
        payload = json.loads(
            urllib.request.urlopen(f"http://{host}:{port}/api/snapshot", timeout=5)
            .read()
            .decode("ascii")
        )
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)

    assert "SeedMind Week 14 Observatory" in html
    assert "Committed Snapshot Evidence Only" in html
    assert payload["title"] == "SeedMind Week 14 Observatory"


def test_week13_limitations_text_remains_visible_in_snapshot() -> None:
    snapshot = build_observatory_snapshot()
    limitations = "\n".join(snapshot["limitations"])
    assert "36/100" in limitations
    assert "15/40" in limitations
    assert "52/52" in limitations
    assert "0/32" in limitations
    assert "Week 14 packages evidence" in limitations


def test_committed_observatory_snapshot_matches_fresh_export(tmp_path: Path) -> None:
    write_observatory_snapshot(tmp_path)
    generated = (tmp_path / "artifacts/week14_packaging/observatory_snapshot.json").read_bytes()
    committed = COMMITTED_PATH.read_bytes()
    assert generated == committed
    assert not tuple((tmp_path / "artifacts/week14_packaging").glob("*.tmp"))
