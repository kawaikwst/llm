# LLM YouTube Landscape Tracker

This repository contains a recruitment-exercise implementation for tracking the
large-language-model (LLM) YouTube landscape across six popular channels:

- Krish Naik
- Andrej Karpathy
- Yannic Kilcher
- Matthew Berman
- Nicholas Renotte
- COLE MEDIN

The project uses **OpenClaw** as the watcher workflow and **Python** for RSS
ingestion, SerpApi transcript retrieval, summarisation, and static-site
generation. The public output is a GitHub Pages-ready table in `docs/`.

## What it does

1. Watches YouTube channel RSS feeds for new videos.
2. Keeps videos whose YouTube title or description contains strong LLM-topic wording.
3. Sends each eligible YouTube video ID to SerpApi's YouTube Video Transcript API.
4. Keeps the row only when the transcript itself contains more than 20 total
   LLM-related keyword hits.
5. Produces concise LLM-topic summaries, topic labels, and transcript evidence
   with the Python pipeline.
6. Renders a browser-friendly landscape table that compares creators by speaker,
   topics, transcript evidence, and their role in the LLM conversation.
7. Updates daily at **08:00 UTC** through GitHub Actions.

## Quick start

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

# Configure SerpApi transcript retrieval.
export SERPAPI_API_KEY="your_serpapi_key"

# Build the initial transcript-grounded dataset:
# 6 channels x 5 latest transcript-backed LLM-description videos.
python scripts/update_tracker.py --mode initial --refresh --require-transcripts

# Open the generated page.
python -m http.server 8000 -d docs
```

Then visit <http://localhost:8000>.

## SerpApi transcript extraction

SerpApi is the production transcript source. The pipeline sends each eligible
YouTube video ID to SerpApi's `youtube_video_transcript` engine and stores
returned transcript text in the generated table.

```bash
export SERPAPI_API_KEY="your_serpapi_key"
export SERPAPI_TRANSCRIPT_LANGUAGE=en
python scripts/update_tracker.py --mode initial --refresh --require-transcripts
python scripts/check_readiness.py --expected-channels 6 --expected-min-videos 30 --min-transcript-rows 30
```

To verify the exact video URLs before transcription, list the latest 5 eligible
non-live, non-Short videos per channel:

```bash
python scripts/list_latest_video_urls.py --per-channel 5
```

## OpenClaw watcher workflow

OpenClaw setup notes and feed commands live in `openclaw/README.md`.

The intended exercise walkthrough is:

1. OpenClaw `feed-watcher` monitors the same six RSS feeds.
2. Python checks each video title or description for strong LLM-topic wording.
3. Python sends matching YouTube video IDs to SerpApi and requires transcript
   text before adding rows.
4. The Python pipeline performs repeatable data processing and static-site
   generation.
5. GitHub Actions runs the Python update every day at 08:00 UTC.

## Repository layout

```text
config/                  Channel and tracker settings
data/                    Generated tracker dataset
docs/                    Public GitHub Pages site
openclaw/                OpenClaw setup and watcher commands
scripts/                 CLI entry points
src/llm_youtube_tracker/ Python implementation
tests/                   Lightweight regression tests
REPORT.md                Markdown report for the exercise
```

## Scheduled updates

`.github/workflows/update-site.yml` runs daily:

```yaml
cron: "0 8 * * *"
```

The initial run processes the latest 5 transcript-backed videos per channel.
Daily updates check the latest 3 videos per channel, skip live/upcoming videos
and YouTube Shorts, require LLM-topic wording in the title or description, and
add only unseen videos where SerpApi returns transcript text with more than 20
LLM-related keyword hits.
