#!/usr/bin/env python3
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm_youtube_tracker.config import load_config
from llm_youtube_tracker.pipeline import is_obvious_live_or_upcoming, is_youtube_short
from llm_youtube_tracker.summarizer import is_llm_relevant_metadata
from llm_youtube_tracker.youtube_rss import get_recent_videos


def main() -> int:
    parser = argparse.ArgumentParser(description="List latest eligible YouTube URLs per configured channel.")
    parser.add_argument("--per-channel", type=int, default=5)
    parser.add_argument("--candidates", type=int, default=40)
    parser.add_argument("--urls-only", action="store_true")
    args = parser.parse_args()

    config = load_config()
    all_urls: list[str] = []
    for channel in config.channels:
        selected = []
        for video in get_recent_videos(channel, limit=args.candidates):
            if is_obvious_live_or_upcoming(video) or is_youtube_short(video):
                continue
            if not is_llm_relevant_metadata(video.title, video.description):
                continue
            selected.append(video)
            if len(selected) >= args.per_channel:
                break
        if not args.urls_only:
            print(f"\n{channel.name}")
            print("-" * len(channel.name))
        for video in selected:
            all_urls.append(video.url)
            if args.urls_only:
                print(video.url)
            else:
                print(f"{video.published[:10]}\t{video.title}\t{video.url}")

    if not args.urls_only:
        print("\nURLs only:")
        for url in all_urls:
            print(url)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
