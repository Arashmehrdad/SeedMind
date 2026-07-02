"""Run the fixed Week 14 scripted demonstration."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from seedmind.observatory import write_demo_manifest
from seedmind.observatory.app import run_demo


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-wait", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()

    manifest = write_demo_manifest(args.root)
    # The demo runs from the committed manifest export, not a regenerated in-memory variant.
    run_demo(json.loads(json.dumps(manifest, ensure_ascii=True)), no_wait=args.no_wait)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
