#!/usr/bin/env python3
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm_youtube_tracker.config import load_config
from llm_youtube_tracker.render import render_site


def main() -> int:
    config = load_config()
    render_site(
        data_path=ROOT / "data/videos.json",
        channels=config.channels,
        settings=config.settings,
        docs_dir=ROOT / "docs",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
