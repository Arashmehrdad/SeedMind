"""Export and optionally serve the Week 14 read-only observatory."""

from __future__ import annotations

import argparse
from pathlib import Path

from seedmind.observatory import create_observatory_server, write_observatory_snapshot


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    parser.add_argument("--export-only", action="store_true")
    parser.add_argument("--root", type=Path, default=None)
    args = parser.parse_args()

    snapshot = write_observatory_snapshot(args.root)
    if args.export_only:
        print("Exported observatory snapshot.")
        return 0

    server = create_observatory_server(snapshot, host=args.host, port=args.port)
    print(f"Serving SeedMind Week 14 Observatory at http://{args.host}:{args.port}/")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        return 0
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
