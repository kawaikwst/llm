from __future__ import annotations

import datetime as dt
import re
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass

from .config import Channel

ATOM = "{http://www.w3.org/2005/Atom}"
MEDIA = "{http://search.yahoo.com/mrss/}"
YT = "{http://www.youtube.com/xml/schemas/2015}"


@dataclass(frozen=True)
class FeedVideo:
    video_id: str
    channel_id: str
    channel_name: str
    title: str
    url: str
    published: str
    updated: str
    description: str


def fetch_feed(channel: Channel, timeout: int = 30) -> str:
    request = urllib.request.Request(
        channel.feed_url,
        headers={"User-Agent": "llm-youtube-landscape-tracker/0.1"},
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


def parse_feed(xml_text: str, channel: Channel, limit: int) -> list[FeedVideo]:
    root = ET.fromstring(xml_text)
    videos: list[FeedVideo] = []
    for entry in root.findall(f"{ATOM}entry"):
        video_id = _text(entry, f"{YT}videoId")
        if not video_id:
            continue
        link = entry.find(f"{ATOM}link")
        media_group = entry.find(f"{MEDIA}group")
        description = ""
        if media_group is not None:
            description = _text(media_group, f"{MEDIA}description")
        videos.append(
            FeedVideo(
                video_id=video_id,
                channel_id=_text(entry, f"{YT}channelId") or channel.channel_id,
                channel_name=channel.name,
                title=_text(entry, f"{ATOM}title"),
                url=link.attrib.get("href", f"https://www.youtube.com/watch?v={video_id}")
                if link is not None
                else f"https://www.youtube.com/watch?v={video_id}",
                published=_text(entry, f"{ATOM}published"),
                updated=_text(entry, f"{ATOM}updated"),
                description=description,
            )
        )
        if len(videos) >= limit:
            break
    return videos


def get_recent_videos(channel: Channel, limit: int) -> list[FeedVideo]:
    return parse_feed(fetch_feed(channel), channel, limit)


def extract_video_id(url_or_id: str) -> str | None:
    if re.fullmatch(r"[\w-]{11}", url_or_id):
        return url_or_id
    patterns = [
        r"[?&]v=([\w-]{11})",
        r"youtu\.be/([\w-]{11})",
        r"/shorts/([\w-]{11})",
        r"/embed/([\w-]{11})",
    ]
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    return None


def normalize_datetime(value: str) -> str:
    if not value:
        return ""
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return value
    return parsed.astimezone(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def _text(element: ET.Element, selector: str) -> str:
    child = element.find(selector)
    return child.text.strip() if child is not None and child.text else ""
