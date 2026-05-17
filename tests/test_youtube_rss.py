import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm_youtube_tracker.config import Channel
from llm_youtube_tracker.youtube_rss import extract_video_id, parse_feed


class YoutubeRssTests(unittest.TestCase):
    def test_extract_video_id_from_watch_url(self):
        self.assertEqual(extract_video_id("https://www.youtube.com/watch?v=abcdefghijk"), "abcdefghijk")

    def test_parse_feed_reads_video_entries(self):
        channel = Channel(
            name="Example",
            channel_id="UC123",
            feed_url="https://example.test/feed.xml",
            primary_speaker="Example Speaker",
            positioning="Example positioning",
            llm_role="Example role",
        )
        xml = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns:yt="http://www.youtube.com/xml/schemas/2015"
      xmlns:media="http://search.yahoo.com/mrss/"
      xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <yt:videoId>abcdefghijk</yt:videoId>
    <yt:channelId>UC123</yt:channelId>
    <title>Example LLM video</title>
    <link rel="alternate" href="https://www.youtube.com/watch?v=abcdefghijk"/>
    <published>2026-05-16T08:00:00+00:00</published>
    <updated>2026-05-16T08:05:00+00:00</updated>
    <media:group>
      <media:description>Transcript-relevant description.</media:description>
    </media:group>
  </entry>
</feed>"""

        videos = parse_feed(xml, channel, limit=5)

        self.assertEqual(len(videos), 1)
        self.assertEqual(videos[0].title, "Example LLM video")
        self.assertEqual(videos[0].description, "Transcript-relevant description.")


if __name__ == "__main__":
    unittest.main()
