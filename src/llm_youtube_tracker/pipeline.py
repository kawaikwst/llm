from __future__ import annotations

import argparse
import datetime as dt
from pathlib import Path
from typing import Any

from .config import Channel, load_config
from .render import render_site
from .store import load_records, save_records
from .summarizer import analyze_video, is_llm_relevant_metadata, is_llm_relevant_text
from .transcripts import fetch_english_transcript
from .youtube_rss import FeedVideo, get_recent_videos, normalize_datetime


def run_update(args: argparse.Namespace) -> int:
    tracker_config = load_config()
    output_path = Path(args.output)
    existing_records = load_records(output_path)
    existing_by_id = {record["video_id"]: record for record in existing_records}
    limit = _video_limit(args.mode, tracker_config.settings)

    records = list(existing_records)
    if args.refresh and args.mode == "initial":
        records = []
        existing_by_id = {}

    for channel in tracker_config.channels:
        selected_for_channel = 0
        try:
            candidate_videos = get_recent_videos(channel, limit=_candidate_limit(limit))
        except Exception as exc:
            print(f"Skipping channel feed after fetch error: {channel.name} ({exc})")
            continue
        for video in candidate_videos:
            if is_obvious_live_or_upcoming(video):
                print(f"Skipping live/upcoming video: {channel.name} - {video.title}")
                continue
            if is_youtube_short(video):
                print(f"Skipping YouTube Short: {channel.name} - {video.title}")
                continue
            if not is_llm_relevant_metadata(video.title, video.description):
                print(f"Skipping non-LLM metadata: {channel.name} - {video.title}")
                continue
            if video.video_id in existing_by_id and existing_by_id[video.video_id].get("transcript_status") != "available":
                records = [item for item in records if item["video_id"] != video.video_id]
                existing_by_id.pop(video.video_id, None)
            if video.video_id in existing_by_id and not args.refresh:
                selected_for_channel += 1
                if selected_for_channel >= limit:
                    break
                continue
            record = build_record(
                channel=channel,
                video=video,
                settings=tracker_config.settings,
                previous=existing_by_id.get(video.video_id),
                require_transcript=args.require_transcripts,
            )
            if record is None:
                continue
            if video.video_id in existing_by_id:
                records = [item for item in records if item["video_id"] != video.video_id]
            records.append(record)
            existing_by_id[video.video_id] = record
            selected_for_channel += 1
            if selected_for_channel >= limit:
                break

    records = keep_latest_per_channel(
        records=records,
        channels=tracker_config.channels,
        per_channel=int(tracker_config.settings["initial_videos_per_channel"]),
    )
    save_records(output_path, records)
    render_site(
        data_path=output_path,
        channels=tracker_config.channels,
        settings=tracker_config.settings,
        docs_dir=Path(args.docs_dir),
    )
    return 0


def build_record(
    *,
    channel: Channel,
    video: FeedVideo,
    settings: dict[str, Any],
    previous: dict[str, Any] | None = None,
    require_transcript: bool = False,
) -> dict[str, Any] | None:
    transcript_result = fetch_english_transcript(video.video_id, video.url)
    if require_transcript and transcript_result.status != "available":
        reason = transcript_result.error or transcript_result.source
        print(f"Skipping video without transcript: {video.channel_name} - {video.title} ({reason[:220]})")
        return None
    transcript_text = transcript_result.text
    if not transcript_text and previous:
        transcript_text = previous.get("transcript_excerpt", "")
    if not is_llm_relevant_text(transcript_text, settings):
        print(f"Skipping non-LLM video: {video.channel_name} - {video.title}")
        return None

    analysis = analyze_video(
        title=video.title,
        channel_name=channel.name,
        primary_speaker=channel.primary_speaker,
        positioning=channel.positioning,
        llm_role=channel.llm_role,
        transcript=transcript_text,
        description=video.description,
        settings=settings,
    )
    return {
        "video_id": video.video_id,
        "channel_id": video.channel_id,
        "channel": channel.name,
        "speaker": analysis["speaker"],
        "title": video.title,
        "url": video.url,
        "published": normalize_datetime(video.published),
        "updated": normalize_datetime(video.updated),
        "topics": analysis["topics"],
        "summary": analysis["summary"],
        "summary_points": analysis["summary_points"],
        "caption_evidence": analysis["caption_evidence"],
        "creator_positioning": analysis["creator_positioning"],
        "llm_landscape_role": analysis["llm_landscape_role"],
        "summary_method": analysis["summary_method"],
        "content_basis": analysis["content_basis"],
        "transcript_status": transcript_result.status,
        "transcript_source": transcript_result.source,
        "transcript_language": transcript_result.language,
        "transcript_chars": len(transcript_result.text),
        "transcript_excerpt": transcript_result.text[:900],
        "transcript_error": transcript_result.error[:300],
        "processed_at": dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z"),
    }


def _video_limit(mode: str, settings: dict[str, Any]) -> int:
    if mode == "daily":
        return int(settings["daily_check_videos_per_channel"])
    return int(settings["initial_videos_per_channel"])


def _candidate_limit(target_limit: int) -> int:
    return max(target_limit * 8, target_limit + 30)


def keep_latest_per_channel(
    *,
    records: list[dict[str, Any]],
    channels: list[Channel],
    per_channel: int,
) -> list[dict[str, Any]]:
    channel_names = {channel.name for channel in channels}
    kept: list[dict[str, Any]] = []
    for channel in channels:
        channel_records = [record for record in records if record.get("channel") == channel.name]
        channel_records.sort(key=lambda record: record.get("published", ""), reverse=True)
        kept.extend(channel_records[:per_channel])

    # Drop rows for removed channels, and keep unrelated rows out of the public table.
    return [record for record in kept if record.get("channel") in channel_names]


def is_obvious_live_or_upcoming(video: FeedVideo) -> bool:
    text = f"{video.title} {video.description}".lower()
    markers = (
        "🔴live",
        "live event will begin",
        "will begin in a few moments",
        "upcoming live",
        "live stream",
        " live -",
        " live:",
        "premiere will begin",
        "waiting room",
    )
    return any(marker in text for marker in markers)


def is_youtube_short(video: FeedVideo) -> bool:
    text = f"{video.url} {video.description}".lower()
    markers = (
        "/shorts/",
        "youtube.com/shorts",
        "#shorts",
        " #short ",
    )
    return any(marker in text for marker in markers)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Update the LLM YouTube landscape tracker.")
    parser.add_argument("--mode", choices=["initial", "daily"], default="daily")
    parser.add_argument("--output", default="data/videos.json")
    parser.add_argument("--docs-dir", default="docs")
    parser.add_argument(
        "--refresh",
        action="store_true",
        help="Reprocess existing videos instead of only adding unseen feed entries.",
    )
    parser.add_argument(
        "--require-transcripts",
        action="store_true",
        help="Only include rows where transcript text is available.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    return run_update(parser.parse_args(argv))
