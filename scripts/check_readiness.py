#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Check whether the generated tracker data is submission-ready.")
    parser.add_argument("--data", default="data/videos.json")
    parser.add_argument("--expected-channels", type=int, default=6)
    parser.add_argument("--expected-min-videos", type=int, default=30)
    parser.add_argument("--min-transcript-rows", type=int, default=30)
    args = parser.parse_args()

    videos = json.loads(Path(args.data).read_text(encoding="utf-8")).get("videos", [])
    channels = Counter(video.get("channel", "") for video in videos)
    transcript_rows = [
        video for video in videos
        if video.get("transcript_status") == "available" and video.get("content_basis") == "transcript"
    ]

    print(f"Videos: {len(videos)}")
    print(f"Channels: {len(channels)} -> {dict(channels)}")
    print(f"Transcript-grounded rows: {len(transcript_rows)}")

    failures: list[str] = []
    if len(channels) < args.expected_channels:
        failures.append(f"Expected at least {args.expected_channels} channels.")
    if len(videos) < args.expected_min_videos:
        failures.append(f"Expected at least {args.expected_min_videos} videos.")
    if len(transcript_rows) < args.min_transcript_rows:
        failures.append(f"Expected at least {args.min_transcript_rows} transcript-grounded rows.")

    if failures:
        for failure in failures:
            print(f"FAIL: {failure}", file=sys.stderr)
        return 1
    print("Readiness check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
