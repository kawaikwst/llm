import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm_youtube_tracker.config import Channel
from llm_youtube_tracker.render import build_channel_relationships


class RenderTests(unittest.TestCase):
    def test_channel_relationships_compare_channels(self):
        channels = [
            Channel(
                name="Krish Naik",
                channel_id="UC1",
                feed_url="https://example.test",
                primary_speaker="Krish",
                positioning="Education",
                llm_role="Education role",
            ),
            Channel(
                name="COLE MEDIN",
                channel_id="UC2",
                feed_url="https://example.test",
                primary_speaker="Cole",
                positioning="Agents",
                llm_role="Agent role",
            ),
        ]

        relationships = build_channel_relationships(channels)

        self.assertIn("data-science", relationships["Krish Naik"])
        self.assertIn("Agent-automation", relationships["COLE MEDIN"])


if __name__ == "__main__":
    unittest.main()
