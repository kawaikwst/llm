from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class TranscriptResult:
    status: str
    text: str
    source: str
    language: str
    error: str = ""


@dataclass(frozen=True)
class JsonResponse:
    data: Any = None
    error: str = ""
    status_code: int = 0


def fetch_english_transcript(video_id: str, video_url: str | None = None) -> TranscriptResult:
    """Fetch YouTube transcript text through SerpApi's transcript engine."""
    api_key = os.getenv("SERPAPI_API_KEY", "")
    if not api_key:
        return TranscriptResult("missing", "", "serpapi", "", "SERPAPI_API_KEY is not set.")
    return fetch_with_serpapi(video_id=video_id, api_key=api_key)


def fetch_with_serpapi(video_id: str, api_key: str) -> TranscriptResult:
    endpoint = os.getenv("SERPAPI_ENDPOINT", "https://serpapi.com/search.json")
    params = {
        "engine": "youtube_video_transcript",
        "v": video_id,
        "api_key": api_key,
        "language_code": os.getenv("SERPAPI_TRANSCRIPT_LANGUAGE", "en"),
    }
    transcript_type = os.getenv("SERPAPI_TRANSCRIPT_TYPE", "")
    if transcript_type:
        params["type"] = transcript_type
    no_cache = os.getenv("SERPAPI_NO_CACHE", "")
    if no_cache:
        params["no_cache"] = no_cache

    url = f"{endpoint}?{urllib.parse.urlencode(params)}"
    response = _json_get(url, timeout=int(os.getenv("SERPAPI_TIMEOUT_SECONDS", "120")))
    if response.error:
        return TranscriptResult("missing", "", "serpapi", "", response.error)
    error = _extract_error(response.data)
    if error:
        return TranscriptResult("missing", "", "serpapi", "", error)

    text = _extract_transcript_text(response.data)
    if not text:
        return TranscriptResult("missing", "", "serpapi", "", f"No transcript text found in response: {response.data}")

    language = _extract_language(response.data) or params["language_code"]
    source = _extract_source(response.data)
    return TranscriptResult("available", text, source, language)


def _json_get(url: str, timeout: int) -> JsonResponse:
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "llm-youtube-landscape-tracker/0.1",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            raw = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        return JsonResponse(error=f"HTTP {exc.code}: {body or exc.reason}", status_code=exc.code)
    except Exception as exc:
        return JsonResponse(error=str(exc))

    try:
        return JsonResponse(data=json.loads(raw), status_code=200)
    except json.JSONDecodeError:
        return JsonResponse(error=f"Response was not JSON: {raw[:500]}", status_code=200)


def _extract_error(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    error = data.get("error")
    if isinstance(error, str) and error:
        return error
    metadata = data.get("search_metadata")
    if isinstance(metadata, dict):
        status = str(metadata.get("status", "")).lower()
        if status == "error":
            return str(metadata)
    return ""


def _extract_transcript_text(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    transcript = data.get("transcript")
    if isinstance(transcript, list):
        snippets = []
        for item in transcript:
            if isinstance(item, dict):
                snippet = item.get("snippet")
                if isinstance(snippet, str):
                    snippets.append(snippet)
            elif isinstance(item, str):
                snippets.append(item)
        return clean_transcript_text(" ".join(snippets))
    if isinstance(transcript, str):
        return clean_transcript_text(transcript)
    return ""


def _extract_language(data: Any) -> str:
    if not isinstance(data, dict):
        return ""
    params = data.get("search_parameters")
    if isinstance(params, dict):
        value = params.get("language_code")
        if isinstance(value, str):
            return value
    for item in data.get("available_transcripts", []) if isinstance(data.get("available_transcripts"), list) else []:
        if isinstance(item, dict) and item.get("selected"):
            value = item.get("language_code")
            if isinstance(value, str):
                return value
    return ""


def _extract_source(data: Any) -> str:
    if not isinstance(data, dict):
        return "serpapi"
    params = data.get("search_parameters")
    transcript_type = ""
    if isinstance(params, dict):
        transcript_type = str(params.get("type") or "")
    if transcript_type:
        return f"serpapi:{transcript_type}"
    for item in data.get("available_transcripts", []) if isinstance(data.get("available_transcripts"), list) else []:
        if isinstance(item, dict) and item.get("selected"):
            selected_type = item.get("type")
            if selected_type:
                return f"serpapi:{selected_type}"
    return "serpapi"


def clean_transcript_text(text: str) -> str:
    text = re.sub(r"\[[^\]]+\]", " ", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()
