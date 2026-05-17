#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspect an OpenClaw feed-watcher webhook payload before running the Python tracker."
    )
    parser.add_argument("payload", type=Path)
    args = parser.parse_args()
    data = json.loads(args.payload.read_text(encoding="utf-8"))
    items = data.get("items", [])
    print(f"Feed: {data.get('feed', 'unknown')}")
    print(f"New items: {len(items)}")
    for item in items:
        print(f"- {item.get('title')} -> {item.get('link')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
