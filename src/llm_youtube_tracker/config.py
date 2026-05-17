from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Channel:
    name: str
    channel_id: str
    feed_url: str
    primary_speaker: str
    positioning: str
    llm_role: str


@dataclass(frozen=True)
class TrackerConfig:
    channels: list[Channel]
    settings: dict[str, Any]


def read_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_config(
    channels_path: Path = Path("config/channels.json"),
    settings_path: Path = Path("config/settings.json"),
) -> TrackerConfig:
    channel_payload = read_json(channels_path)
    settings = read_json(settings_path)
    channels = [Channel(**item) for item in channel_payload["channels"]]
    return TrackerConfig(channels=channels, settings=settings)
