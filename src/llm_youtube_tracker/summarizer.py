from __future__ import annotations

import re
from collections import Counter
from typing import Any

LLM_TERMS = (
    "llm",
    "large language model",
    "language model",
    "gpt",
    "claude",
    "gemini",
    "llama",
    "transformer",
    "agent",
    "model",
    "ai",
    "reasoning",
)

STRONG_LLM_TERMS = (
    "llm",
    "llms",
    "large language model",
    "large language models",
    "language model",
    "language models",
    "chatgpt",
    "gpt",
    "openai",
    "anthropic",
    "claude",
    "gemini",
    "llama",
    "mistral",
    "deepseek",
    "qwen",
    "transformer",
    "transformers",
    "foundation model",
    "foundation models",
    "frontier model",
    "frontier models",
    "reasoning model",
    "reasoning models",
    "ai agent",
    "ai agents",
    "agentic ai",
    "generative ai",
    "machine learning model",
    "scaling law",
    "scaling laws",
    "mmlu",
    "simplebench",
    "rag",
    "retrieval augmented generation",
    "vector database",
    "vector databases",
    "embedding",
    "embeddings",
    "langchain",
    "langgraph",
    "crewai",
    "mcp",
    "model context protocol",
    "ai workflow",
    "ai workflows",
    "ai automation",
    "ai coding",
    "ai engineer",
    "ai engineering",
    "neural network",
    "neural networks",
    "deep learning",
    "nlp",
    "natural language processing",
    "recurrent neural network",
    "recurrent neural networks",
    "lstm",
    "attention",
    "self-attention",
)

WEAK_TOPIC_KEYWORDS = {
    "ai",
    "model",
    "models",
    "video",
    "image",
    "audio",
    "voice",
    "product",
    "market",
    "business",
    "code",
    "browser",
    "reasoning",
}

STOPWORDS = {
    "about",
    "after",
    "again",
    "also",
    "because",
    "been",
    "being",
    "from",
    "have",
    "into",
    "just",
    "like",
    "more",
    "much",
    "only",
    "over",
    "really",
    "some",
    "that",
    "their",
    "there",
    "these",
    "they",
    "this",
    "those",
    "very",
    "what",
    "when",
    "where",
    "which",
    "with",
    "would",
    "your",
}


def analyze_video(
    *,
    title: str,
    channel_name: str,
    primary_speaker: str,
    positioning: str,
    llm_role: str,
    transcript: str,
    description: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    text = transcript or description or title
    metadata_text = build_relevant_metadata_text(title, description)
    fallback_result = summarize_rule_based(
        title=title,
        channel_name=channel_name,
        text=text,
        settings=settings,
    )
    summary = fallback_result["summary"]
    topics = fallback_result["topics"]
    speaker = infer_speaker(title, channel_name, primary_speaker)

    return {
        "speaker": speaker,
        "topics": topics,
        "summary": summary,
        "summary_points": build_summary_points(text=text, topics=topics, settings=settings, anchor_text=metadata_text),
        "caption_evidence": extract_caption_evidence(text=text, topics=topics, settings=settings, anchor_text=metadata_text),
        "creator_positioning": positioning,
        "llm_landscape_role": llm_role,
        "summary_method": fallback_result["method"],
        "content_basis": "transcript" if transcript else "description/title only",
    }


def summarize_rule_based(
    *,
    title: str,
    channel_name: str,
    text: str,
    settings: dict[str, Any],
) -> dict[str, Any]:
    topics = detect_topics(f"{title} {text}", settings.get("topic_keywords", {}))
    summary = extractive_summary(title=title, channel_name=channel_name, text=text, topics=topics)
    return {"summary": summary, "topics": topics, "method": "python-rule-based"}


def detect_topics(text: str, topic_keywords: dict[str, list[str]], max_topics: int = 4) -> list[str]:
    scores: Counter[str] = Counter()
    for topic, keywords in topic_keywords.items():
        strong_score = 0
        weak_score = 0
        for keyword in keywords:
            count = count_keyword(text, keyword)
            if keyword.lower() in WEAK_TOPIC_KEYWORDS:
                weak_score += count
            else:
                strong_score += count
        # Generic words such as "video", "model", or "AI" are not enough by
        # themselves; they need at least one stronger topic-specific signal.
        if strong_score > 0:
            scores[topic] = strong_score * 3 + weak_score
    ranked = [topic for topic, score in scores.most_common(max_topics) if score > 0]
    return ranked or ["General AI/LLM discussion"]


def is_llm_relevant_text(text: str, settings: dict[str, Any] | None = None) -> bool:
    strong_hits = llm_keyword_count(text)
    if strong_hits > int(__import__("os").getenv("LLM_TRANSCRIPT_MIN_KEYWORD_HITS", "20")):
        return True
    if settings:
        topics = detect_topics(text, settings.get("topic_keywords", {}), max_topics=2)
        return topics != ["General AI/LLM discussion"]
    return False


def is_llm_relevant_metadata(title: str, description: str) -> bool:
    """Gate videos using only creator-provided title/description text."""
    metadata = build_relevant_metadata_text(title, description)
    return llm_keyword_count(metadata) > 0


def llm_keyword_count(text: str) -> int:
    return sum(count_keyword(text, keyword) for keyword in STRONG_LLM_TERMS)


def build_relevant_metadata_text(title: str, description: str) -> str:
    """Use title plus non-boilerplate description lines for LLM eligibility.

    YouTube descriptions often contain sponsor/contact/link sections. Those can
    include generic terms such as "AI agent" even when the actual video is about
    music, sports, or another non-LLM topic. This keeps metadata filtering tied
    to the creator's title and substantive description text.
    """
    clean_lines = []
    for line in description.splitlines():
        stripped = line.strip()
        if not stripped or _is_description_boilerplate(stripped):
            continue
        clean_lines.append(stripped)
    return f"{title} {' '.join(clean_lines[:8])}"


def _is_description_boilerplate(line: str) -> bool:
    lowered = line.lower()
    boilerplate_markers = (
        "http://",
        "https://",
        "www.",
        "sponsor",
        "sponsored",
        "go to ",
        "use code",
        "promo code",
        "subscribe",
        "newsletter",
        "discord",
        "instagram",
        "spotify",
        "twitter",
        "x.com",
        "contact",
        "feedback",
        "hiring",
        "transcript:",
        "timestamps",
        "chapters",
        "follow me",
        "my links",
        "blitzy",
        "betterhelp",
        "lmnt",
        "net suite",
        "netsuite",
        "fin:",
        "blitzy:",
        "eight sleep",
        "ground news",
        "masterclass",
    )
    if any(marker in lowered for marker in boilerplate_markers):
        return True
    # Lex-style sponsor/resource lines often look like "*Fin:* AI agent...";
    # those should not make a non-LLM interview pass.
    return bool(re.match(r"^\*[a-z0-9 ._-]{2,28}:\*\s", lowered))


def count_keyword(text: str, keyword: str) -> int:
    keyword = keyword.lower().strip()
    if not keyword:
        return 0
    escaped = re.escape(keyword)
    # Match whole phrases/tokens so "ai" does not match "said" and "video"
    # does not dominate unrelated creator interviews.
    return len(re.findall(rf"(?<![a-z0-9]){escaped}(?![a-z0-9])", text.lower()))


def extractive_summary(title: str, channel_name: str, text: str, topics: list[str]) -> str:
    sentences = split_sentences(text)
    scored: list[tuple[int, int, str]] = []
    for index, sentence in enumerate(sentences[:80]):
        score = sum(3 for term in LLM_TERMS if count_keyword(sentence, term))
        score += min(len(sentence), 240) // 80
        if score:
            scored.append((score, -index, sentence))
    chosen = [item[2] for item in sorted(scored, reverse=True)[:2]]
    if not chosen:
        chosen = sentences[:2]
    body = " ".join(chosen).strip()
    if len(body) > 420:
        body = body[:417].rsplit(" ", 1)[0] + "..."
    topic_text = ", ".join(topics[:3])
    if body:
        return f"{channel_name} covers {topic_text}. Transcript signal: {body}"
    return f"{channel_name} covers {topic_text} in '{title}'."


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    parts = re.split(r"(?<=[.!?])\s+", text)
    return [part.strip() for part in parts if len(part.strip()) > 30]


def extract_caption_evidence(text: str, topics: list[str], settings: dict[str, Any], anchor_text: str = "") -> str:
    sentences = split_sentences(text)
    if not sentences:
        return "No transcript evidence available."

    keywords = _evidence_keywords(topics, settings, anchor_text=anchor_text)
    phrase_counts = _repeated_llm_phrases(text, keywords)
    evidence_sentences = _top_evidence_sentences(sentences, keywords)

    parts: list[str] = []
    if phrase_counts:
        phrases = ", ".join(f'"{phrase}" ({count}x)' for phrase, count in phrase_counts[:4])
        parts.append(f"Frequent LLM phrases: {phrases}.")
    if evidence_sentences:
        parts.append("Representative caption lines: " + " ".join(f'"{sentence}"' for sentence in evidence_sentences[:2]))
    return " ".join(parts) or "Transcript available, but no repeated LLM-specific phrase dominated."


def build_summary_points(text: str, topics: list[str], settings: dict[str, Any], anchor_text: str = "") -> list[dict[str, str]]:
    sentences = split_sentences(text)
    if not sentences:
        return []

    topic_keywords = settings.get("topic_keywords", {})
    anchor_keywords = _metadata_keywords(anchor_text)
    points: list[dict[str, str]] = []
    used_evidence: set[str] = set()

    for keyword in anchor_keywords[:4]:
        evidence = _best_sentence_for_keywords(sentences, {keyword}, used_evidence)
        if not evidence:
            continue
        used_evidence.add(evidence)
        points.append(
            {
                "point": f"Expands on the video's stated LLM focus: {keyword}.",
                "evidence": evidence,
            }
        )
        if len(points) >= 4:
            return points

    for topic in topics[:4]:
        keywords = {keyword.lower() for keyword in topic_keywords.get(topic, [])}
        keywords.update(term for term in LLM_TERMS if term in {"llm", "gpt", "claude", "gemini", "llama", "agent", "reasoning", "model", "ai"})
        evidence = _best_sentence_for_keywords(sentences, keywords, used_evidence)
        if not evidence:
            continue
        used_evidence.add(evidence)
        points.append(
            {
                "point": f"Highlights {topic.lower()} as a key LLM theme in the discussion.",
                "evidence": evidence,
            }
        )

    if len(points) < 2:
        keywords = _evidence_keywords(topics, settings, anchor_text=anchor_text)
        for evidence in _top_evidence_sentences(sentences, keywords):
            if evidence in used_evidence:
                continue
            used_evidence.add(evidence)
            points.append(
                {
                    "point": "Adds transcript context on the creator's main LLM argument.",
                    "evidence": evidence,
                }
            )
            if len(points) >= 2:
                break

    if len(points) < 2:
        for sentence in sentences[:4]:
            evidence = _shorten_sentence(sentence)
            if evidence in used_evidence:
                continue
            used_evidence.add(evidence)
            points.append(
                {
                    "point": "Summarizes a recurring idea from the video transcript.",
                    "evidence": evidence,
                }
            )
            if len(points) >= 2:
                break

    return points[:4]


def _evidence_keywords(topics: list[str], settings: dict[str, Any], anchor_text: str = "") -> set[str]:
    topic_keywords = settings.get("topic_keywords", {})
    keywords = {term.lower() for term in LLM_TERMS}
    keywords.update(_metadata_keywords(anchor_text))
    for topic in topics:
        for keyword in topic_keywords.get(topic, []):
            keywords.add(keyword.lower())
    return {keyword for keyword in keywords if len(keyword) > 1}


def _metadata_keywords(anchor_text: str) -> list[str]:
    found = []
    for keyword in STRONG_LLM_TERMS:
        if count_keyword(anchor_text, keyword):
            found.append(keyword)
    # Prefer longer, more specific phrases before shorter substrings.
    return sorted(set(found), key=lambda value: (-len(value.split()), -len(value), value))


def _repeated_llm_phrases(text: str, keywords: set[str]) -> list[tuple[str, int]]:
    lowered = re.sub(r"[^a-z0-9\s-]", " ", text.lower())
    tokens = [token for token in lowered.split() if len(token) > 2 and token not in STOPWORDS]
    counts: Counter[str] = Counter()
    for ngram_size in (2, 3, 4):
        for index in range(0, max(0, len(tokens) - ngram_size + 1)):
            phrase_tokens = tokens[index : index + ngram_size]
            phrase = " ".join(phrase_tokens)
            if any(keyword in phrase for keyword in keywords):
                counts[phrase] += 1
    return [(phrase, count) for phrase, count in counts.most_common(8) if count > 1]


def _top_evidence_sentences(sentences: list[str], keywords: set[str]) -> list[str]:
    scored: list[tuple[int, int, str]] = []
    for index, sentence in enumerate(sentences[:120]):
        keyword_hits = sum(count_keyword(sentence, keyword) for keyword in keywords)
        if keyword_hits <= 0:
            continue
        score = keyword_hits * 4 + min(len(sentence), 240) // 80
        scored.append((score, -index, _shorten_sentence(sentence)))
    return [item[2] for item in sorted(scored, reverse=True)[:3]]


def _best_sentence_for_keywords(sentences: list[str], keywords: set[str], used: set[str]) -> str:
    scored: list[tuple[int, int, str]] = []
    for index, sentence in enumerate(sentences[:120]):
        shortened = _shorten_sentence(sentence)
        if shortened in used:
            continue
        keyword_hits = sum(count_keyword(sentence, keyword) for keyword in keywords if keyword)
        if keyword_hits <= 0:
            continue
        score = keyword_hits * 4 + min(len(sentence), 240) // 80
        scored.append((score, -index, shortened))
    return sorted(scored, reverse=True)[0][2] if scored else ""


def _shorten_sentence(sentence: str, limit: int = 260) -> str:
    sentence = re.sub(r"\s+", " ", sentence).strip()
    if len(sentence) <= limit:
        return sentence
    return sentence[: limit - 3].rsplit(" ", 1)[0] + "..."


def infer_speaker(title: str, channel_name: str, primary_speaker: str) -> str:
    if channel_name == "Lex Fridman":
        guest = title.split("|", 1)[0].strip()
        if guest and guest.lower() != "lex fridman":
            return f"Lex Fridman with {guest}"
    return primary_speaker
