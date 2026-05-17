# Recruitment Exercise Report: LLM YouTube Landscape Tracker
Live table: https://kawaikwst.github.io/llm/

## Problem Statement

The exercise asks for an automated watcher that follows popular YouTube channels
covering large language models (LLMs), extracts what creators actually say from
video transcripts or reliable captions, and publishes a concise browser-visible
table. The table should categorise each video by speaker, LLM topics, transcript
evidence, and how each creator relates to the broader LLM landscape.

This implementation tracks six channels:

1. Krish Naik
2. Andrej Karpathy
3. Yannic Kilcher
4. Matthew Berman
5. Nicholas Renotte
6. COLE MEDIN

## Methodology

The solution combines OpenClaw and Python:

- **OpenClaw feed-watcher** is used as the automated watcher pattern for the
  six YouTube RSS feeds.
- **Python** performs the repeatable hosted transcription pipeline:
  1. read channel configuration from `config/channels.json`;
  2. fetch latest videos from YouTube RSS feeds without a YouTube API key;
  3. skip live/upcoming videos and YouTube Shorts;
  4. require strong LLM-topic wording in the YouTube title or description;
  5. send each eligible YouTube video ID to SerpApi's YouTube Video Transcript
     API and require returned transcript text;
  6. verify the transcript contains more than 20 total LLM-related keyword hits;
  7. generate topic labels, summary bullets, and evidence snippets from
     transcript text with the Python pipeline;
  8. write `data/videos.json`; and
  9. render the GitHub Pages site in `docs/`.

The update schedule is daily at **08:00 UTC**. The initial dataset processes the
latest **5 eligible videos per channel**. Daily updates check the latest **3
videos per channel**, skip live/upcoming videos and YouTube Shorts, require
LLM-topic wording in the title or description, and only add unseen videos where
SerpApi returns transcript text with more than 20 total LLM-related keyword hits.

## Evaluation Dataset

The live dataset is generated from public YouTube RSS feeds:

| Channel | Feed |
| --- | --- |
| Krish Naik | `https://www.youtube.com/feeds/videos.xml?channel_id=UCNU_lfiiWBdtULKOw6X0Dig` |
| Andrej Karpathy | `https://www.youtube.com/feeds/videos.xml?channel_id=UCPk8m_r6fkUSYmvgCBwq-sw` |
| Yannic Kilcher | `https://www.youtube.com/feeds/videos.xml?channel_id=UCZHmQk67mSJgfCCTn7xBfew` |
| Matthew Berman | `https://www.youtube.com/feeds/videos.xml?channel_id=UCawZsQWqfGSbCI5yjkdVkTA` |
| Nicholas Renotte | `https://www.youtube.com/feeds/videos.xml?channel_id=UCHXa4OpASJEwrHrLeIzw7Yg` |
| COLE MEDIN | `https://www.youtube.com/feeds/videos.xml?channel_id=UCMwVTLZIRRUyyVrkjDpn4pA` |

Each row stores video metadata, detected LLM topics, summary method, caption
status, caption source, caption character count, and a transcript excerpt as
evidence.

## Evaluation Methods

The project evaluates the pipeline through practical checks:

1. **Feed coverage**: each configured channel returns recent RSS entries.
2. **Transcript availability**: each video records whether SerpApi returned
   transcript text.
3. **Topic relevance**: summaries are grounded in transcript text, with topic
   labels produced from LLM-specific keyword groups.
4. **Update idempotency**: already-seen video IDs are not duplicated during
   daily runs.
5. **Site rendering**: `docs/index.html` is regenerated from the JSON dataset
   and can be opened directly in a browser or hosted through GitHub Pages.

## Experimental Results

The generated table provides:

- a cross-channel comparison of creator positioning;
- transcript-grounded summaries for each tracked video;
- topic tags such as agents, frontier models, evaluations, safety, open-source
  models, coding, and research papers;
- evidence from the SerpApi transcript source;
  and
- a daily automation path through GitHub Actions.

The project intentionally avoids OpenAI because an API key is not available.
The Python summarization and topic-label pipeline keeps the public GitHub Pages
update reliable in CI.

SerpApi is used as the hosted transcript provider so the table can be updated
from GitHub Actions without manual copying.

## How to Reproduce

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export SERPAPI_API_KEY="your_serpapi_key"
python scripts/update_tracker.py --mode initial --refresh --require-transcripts
python -m http.server 8000 -d docs
```

Then open <http://localhost:8000>.

For OpenClaw setup, see `openclaw/README.md`.
