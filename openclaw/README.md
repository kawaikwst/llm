# OpenClaw watcher setup

This project uses OpenClaw for the local watcher part of the exercise and Python
for repeatable processing and site generation.

## Install OpenClaw skills

From the repository root:

```bash
npx playbooks add skill openclaw/skills --skill feed-watcher
```

The skill maps to the exercise as follows:

- `feed-watcher`: monitors the six YouTube RSS feeds and detects new videos.

## Feed watcher commands

Register the six feeds:

```bash
node index.js add "Krish Naik" "https://www.youtube.com/feeds/videos.xml?channel_id=UCNU_lfiiWBdtULKOw6X0Dig"
node index.js add "Andrej Karpathy" "https://www.youtube.com/feeds/videos.xml?channel_id=UCPk8m_r6fkUSYmvgCBwq-sw"
node index.js add "Yannic Kilcher" "https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew"
node index.js add "Matthew Berman" "https://www.youtube.com/feeds/videos.xml?channel_id=UCawZsQWqfGSbCI5yjkdVkTA"
node index.js add "Nicholas Renotte" "https://www.youtube.com/feeds/videos.xml?channel_id=UCHXa4OpASJEwrHrLeIzw7Yg"
node index.js add "COLE MEDIN" "https://www.youtube.com/feeds/videos.xml?channel_id=UCMwVTLZIRRUyyVrkjDpn4pA"
```

Scan for updates:

```bash
node index.js scan
```

For a local always-on watcher, add a cron entry like:

```cron
0 8 * * * cd /path/to/feed-watcher && DATA_DIR=/path/to/repo/openclaw/.state node index.js scan >> /path/to/repo/openclaw/feed-watcher.log 2>&1
```

GitHub Actions already performs the hosted daily update at 08:00 UTC, so this
local OpenClaw watcher is mainly for the live walkthrough and for demonstrating
the automated-watcher component.

## Transcript extraction

The Python pipeline sends each YouTube video ID discovered from RSS/OpenClaw to
SerpApi's YouTube Video Transcript API and requires returned transcript text
before publishing a row. A video must first contain strong LLM-topic wording in
its YouTube title or description, and the returned transcript must also be
LLM-relevant:

```bash
export SERPAPI_API_KEY="your_serpapi_key"
python scripts/update_tracker.py --mode initial --refresh --require-transcripts
```

To inspect the exact links sent to SerpApi:

```bash
python scripts/list_latest_video_urls.py --per-channel 5
```
