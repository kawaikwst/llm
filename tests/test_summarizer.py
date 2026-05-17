import unittest
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from llm_youtube_tracker.summarizer import build_relevant_metadata_text, build_summary_points, count_keyword, detect_topics, extract_caption_evidence, infer_speaker, is_llm_relevant_metadata, is_llm_relevant_text, llm_keyword_count, split_sentences


class SummarizerTests(unittest.TestCase):
    def test_detect_topics_scores_keyword_groups(self):
        settings_topics = {
            "Agents and tool use": ["agent", "tool use"],
            "Safety and alignment": ["safety", "alignment"],
        }

        topics = detect_topics("This agent uses tool use, but safety also matters.", settings_topics)

        self.assertEqual(topics[0], "Agents and tool use")
        self.assertIn("Safety and alignment", topics)

    def test_infer_lex_guest_from_title(self):
        speaker = infer_speaker(
            "Demis Hassabis: Google DeepMind | Lex Fridman Podcast #475",
            "Lex Fridman",
            "Lex Fridman and guest",
        )

        self.assertEqual(speaker, "Lex Fridman with Demis Hassabis: Google DeepMind")

    def test_split_sentences_filters_short_fragments(self):
        sentences = split_sentences("Short. This is a longer sentence about a language model. Another useful sentence follows.")

        self.assertEqual(len(sentences), 2)

    def test_extract_caption_evidence_prefers_repeated_llm_phrases(self):
        settings_topics = {
            "Agents and tool use": ["agent", "tool use"],
        }
        text = (
            "This agent workflow uses tool use for coding. "
            "The agent workflow improves planning. "
            "A language model can call tools. "
            "The agent workflow is the repeated theme."
        )

        evidence = extract_caption_evidence(text, ["Agents and tool use"], settings_topics)

        self.assertIn("agent workflow", evidence)
        self.assertIn("Representative caption lines", evidence)

    def test_keyword_matching_uses_boundaries(self):
        self.assertEqual(count_keyword("said again", "ai"), 0)
        self.assertEqual(count_keyword("AI agents use tools", "ai"), 1)

    def test_non_llm_music_interview_is_not_relevant(self):
        text = (
            "Rick Beato is a musician with a YouTube channel about great guitarists. "
            "They discuss perfect pitch, songs, musical ideas, and interviews with musicians."
        )

        self.assertFalse(is_llm_relevant_text(text))

    def test_strong_llm_terms_are_relevant(self):
        text = " ".join(["OpenAI released a new GPT reasoning model for AI agents."] * 6)

        self.assertTrue(is_llm_relevant_text(text))

    def test_metadata_gate_requires_strong_llm_terms(self):
        self.assertFalse(is_llm_relevant_metadata("Greatest guitarists of all time", "A conversation about songs and perfect pitch."))
        self.assertTrue(is_llm_relevant_metadata("GPT 5.5 arrives", "OpenAI and Claude competition intensifies."))

    def test_metadata_gate_accepts_title_or_description(self):
        self.assertTrue(is_llm_relevant_metadata("GPT agents tutorial", "A normal tutorial description."))
        self.assertTrue(is_llm_relevant_metadata("A normal tutorial title", "This lesson builds a RAG app with OpenAI, LLMs, and AI agents."))
        self.assertFalse(is_llm_relevant_metadata("Greatest guitarists", "A conversation about songs and perfect pitch."))

    def test_metadata_gate_ignores_sponsor_ai_terms(self):
        title = "Rick Beato: Greatest Guitarists of All Time, History & Future of Music"
        description = (
            "Go to https://lexfridman.com/s/fin for Fin: AI agent for customer service.\n"
            "*Blitzy:* AI agent for large enterprise codebases.\n"
            "Rick Beato celebrates great musicians, songs, perfect pitch, and guitar solos."
        )

        self.assertFalse(is_llm_relevant_metadata(title, description))

    def test_metadata_builder_keeps_substantive_description(self):
        metadata = build_relevant_metadata_text(
            "A vague video title",
            "Sponsor: https://example.com AI agent\nThis episode discusses OpenAI and Claude model releases.",
        )

        self.assertIn("OpenAI", metadata)
        self.assertNotIn("example.com", metadata)

    def test_generic_video_word_does_not_create_multimodal_topic(self):
        settings_topics = {
            "Multimodal AI": ["multimodal", "vision", "image", "audio", "video", "speech", "voice"],
        }

        topics = detect_topics("This video is about guitarists and music videos.", settings_topics)

        self.assertEqual(topics, ["General AI/LLM discussion"])

    def test_summary_points_anchor_to_metadata_terms(self):
        text = (
            "OpenAI is competing with Anthropic on enterprise adoption. "
            "Claude is gaining traction as a frontier model in coding workflows. "
            "The rest of the conversation compares revenue and adoption."
        )
        points = build_summary_points(
            text,
            ["Frontier models"],
            {"topic_keywords": {"Frontier models": ["openai", "anthropic", "claude"]}},
            anchor_text="OpenAI vs Anthropic and Claude adoption",
        )

        joined = " ".join(point["evidence"] for point in points)
        self.assertIn("OpenAI", joined)
        self.assertIn("Claude", joined)

    def test_transcript_relevance_requires_more_than_twenty_hits(self):
        self.assertEqual(llm_keyword_count("OpenAI GPT Claude"), 3)
        self.assertFalse(is_llm_relevant_text("OpenAI GPT Claude"))
        self.assertTrue(is_llm_relevant_text(" ".join(["OpenAI GPT Claude"] * 8)))


if __name__ == "__main__":
    unittest.main()
