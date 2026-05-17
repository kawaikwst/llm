import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm_youtube_tracker.transcripts import (
    _extract_language,
    _extract_source,
    _extract_transcript_text,
    clean_transcript_text,
    TranscriptResult,
)


class TranscriptTests(unittest.TestCase):
    def test_clean_transcript_text_removes_noise(self):
        text = clean_transcript_text("hello   [music]\nworld")

        self.assertEqual(text, "hello world")

    def test_extracts_text_from_serpapi_segments(self):
        payload = {"transcript": [{"snippet": "Hello"}, {"snippet": "world"}]}

        self.assertEqual(_extract_transcript_text(payload), "Hello world")

    def test_extracts_language(self):
        self.assertEqual(_extract_language({"search_parameters": {"language_code": "en"}}), "en")

    def test_extracts_serpapi_source_type(self):
        payload = {"search_parameters": {"type": "asr"}}

        self.assertEqual(_extract_source(payload), "serpapi:asr")


if __name__ == "__main__":
    unittest.main()
