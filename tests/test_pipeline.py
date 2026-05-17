import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm_youtube_tracker.config import Channel
from llm_youtube_tracker.pipeline import _candidate_limit, is_obvious_live_or_upcoming, is_youtube_short, keep_latest_per_channel
from llm_youtube_tracker.youtube_rss import FeedVideo


class PipelineTests(unittest.TestCase):
    def test_live_waiting_room_is_skipped(self):
        video = FeedVideo(
            video_id="DNajvkqfobY",
            channel_id="UC123",
            channel_name="Example",
            title="Traditional Holiday Live Stream",
            url="https://www.youtube.com/watch?v=DNajvkqfobY",
            published="2026-05-16T08:00:00Z",
            updated="2026-05-16T08:00:00Z",
            description="This live event will begin in a few moments.",
        )

        self.assertTrue(is_obvious_live_or_upcoming(video))

    def test_recorded_live_wording_is_not_skipped(self):
        video = FeedVideo(
            video_id="abcdefghijk",
            channel_id="UC123",
            channel_name="Example",
            title="AI conference live recording",
            url="https://www.youtube.com/watch?v=abcdefghijk",
            published="2026-05-16T08:00:00Z",
            updated="2026-05-16T08:00:00Z",
            description="A recorded discussion about LLMs.",
        )

        self.assertFalse(is_obvious_live_or_upcoming(video))

    def test_candidate_limit_backfills_skipped_items(self):
        self.assertEqual(_candidate_limit(5), 40)

    def test_youtube_short_url_is_skipped(self):
        video = FeedVideo(
            video_id="abcdefghijk",
            channel_id="UC123",
            channel_name="Example",
            title="Short LLM clip",
            url="https://www.youtube.com/shorts/abcdefghijk",
            published="2026-05-16T08:00:00Z",
            updated="2026-05-16T08:00:00Z",
            description="",
        )

        self.assertTrue(is_youtube_short(video))

    def test_non_llm_metadata_would_be_skipped_by_gate(self):
        # Pipeline calls is_llm_relevant_metadata before transcript retrieval;
        # this regression protects against unrelated interviews entering the table.
        from llm_youtube_tracker.summarizer import is_llm_relevant_metadata

        self.assertFalse(is_llm_relevant_metadata("Rick Beato: Greatest Guitarists", "Music, songs, and perfect pitch."))

    def test_keep_latest_per_channel_prunes_old_rows(self):
        channels = [
            Channel(
                name="Example",
                channel_id="UC123",
                feed_url="https://example.test/feed.xml",
                primary_speaker="Example Speaker",
                positioning="Example positioning",
                llm_role="Example role",
            )
        ]
        records = [
            {"channel": "Example", "video_id": "old", "published": "2026-01-01T00:00:00Z"},
            {"channel": "Example", "video_id": "new", "published": "2026-02-01T00:00:00Z"},
            {"channel": "Removed", "video_id": "removed", "published": "2026-03-01T00:00:00Z"},
        ]

        kept = keep_latest_per_channel(records=records, channels=channels, per_channel=1)

        self.assertEqual([record["video_id"] for record in kept], ["new"])

    def test_keep_latest_per_channel_keeps_available_existing_rows(self):
        channels = [
            Channel(
                name="Example",
                channel_id="UC123",
                feed_url="https://example.test/feed.xml",
                primary_speaker="Example Speaker",
                positioning="Example positioning",
                llm_role="Example role",
            )
        ]
        records = [
            {
                "channel": "Example",
                "video_id": "new",
                "published": "2026-02-01T00:00:00Z",
                "transcript_status": "available",
            }
        ]

        kept = keep_latest_per_channel(records=records, channels=channels, per_channel=5)

        self.assertEqual(len(kept), 1)

    def test_existing_removed_channel_rows_are_pruned(self):
        channels = [
            Channel(
                name="Current",
                channel_id="UC123",
                feed_url="https://example.test/feed.xml",
                primary_speaker="Example Speaker",
                positioning="Example positioning",
                llm_role="Example role",
            )
        ]
        records = [
            {"channel": "Removed", "video_id": "rick", "published": "2026-02-01T00:00:00Z"},
            {"channel": "Current", "video_id": "llm", "published": "2026-03-01T00:00:00Z"},
        ]

        kept = keep_latest_per_channel(records=records, channels=channels, per_channel=5)

        self.assertEqual([record["video_id"] for record in kept], ["llm"])


if __name__ == "__main__":
    unittest.main()
