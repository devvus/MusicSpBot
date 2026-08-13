# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import asyncio
import aiohttp
import yt_dlp
from typing import Union
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch, Playlist
from anony import config, logger
from anony.helpers import Track, utils

# --- API SPARROW / MUSICSP API CONFIGURATION ---
API_URL = os.environ.get("MusicSp_API_URL", "https://apisparrow.site")
API_KEY = os.environ.get("MusicSp_API_KEY", "sparrowwgZosKCACRJFCkQ7YT4uIU0B")

DOWNLOAD_DIR = "downloads"

def time_to_seconds(time):
    stringt = str(time)
    if not stringt or ":" not in stringt:
        return 0
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))

def seconds_to_min(seconds: int) -> str:
    if not seconds:
        return "0:00"
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"

async def download_song(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL.rstrip('/')}/yt",
                params={"query": video_id, "type": "audio", "api_key": API_KEY},
                timeout=aiohttp.ClientTimeout(total=300)
            ) as resp:
                if resp.status != 200:
                    return None
                
                if "application/json" in resp.headers.get("Content-Type", ""):
                    data = await resp.json()
                    res = data.get("result", data)
                    stream_url = res.get("stream_url") or res.get("download_url") or res.get("url") or res.get("link")
                    if stream_url:
                        async with session.get(stream_url) as stream_resp:
                            with open(file_path, "wb") as f:
                                async for chunk in stream_resp.content.iter_chunked(131072):
                                    f.write(chunk)
                else:
                    with open(file_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(131072):
                            f.write(chunk)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception as e:
        logger.warning(f"Download song failed: {e}")
        return None

async def download_video(link: str) -> str:
    video_id = link.split("v=")[-1].split("&")[0] if "v=" in link else link
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL.rstrip('/')}/yt",
                params={"query": video_id, "type": "video", "api_key": API_KEY},
                timeout=aiohttp.ClientTimeout(total=600)
            ) as resp:
                if resp.status != 200:
                    return None

                if "application/json" in resp.headers.get("Content-Type", ""):
                    data = await resp.json()
                    res = data.get("result", data)
                    stream_url = res.get("stream_url") or res.get("download_url") or res.get("url") or res.get("link")
                    if stream_url:
                        async with session.get(stream_url) as stream_resp:
                            with open(file_path, "wb") as f:
                                async for chunk in stream_resp.content.iter_chunked(131072):
                                    f.write(chunk)
                else:
                    with open(file_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(131072):
                            f.write(chunk)

        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception as e:
        logger.warning(f"Download video failed: {e}")
        return None

class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.listbase = "https://youtube.com/playlist?list="

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    async def fetch_custom_yt_data(self, query: str) -> dict | None:
        # Try /search endpoint first
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL.rstrip('/')}/search",
                    params={"q": query, "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and "results" in data and data["results"]:
                            return data["results"][0]
        except Exception:
            pass
        
        # Try /yt endpoint as fallback
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL.rstrip('/')}/yt",
                    params={"query": query, "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        res = data.get("result", data)
                        if res and (res.get("id") or res.get("title")):
                            return res
        except Exception:
            pass
        return None

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        search_query = query if self.valid(query) else f"{query}"

        # Layer 1: Custom API Search
        data = await self.fetch_custom_yt_data(search_query)
        if not data and not self.valid(query):
            data = await self.fetch_custom_yt_data(f"{search_query} song")

        if data:
            try:
                vid_url = data.get("url") or data.get("link")
                vid_id = data.get("id") or data.get("vidid")
                if not vid_id and vid_url:
                    vid_id = vid_url.split("v=")[-1].split("&")[0] if "v=" in vid_url else vid_url.split("/")[-1]
                
                return Track(
                    id=vid_id,
                    channel_name=data.get("channel", "YouTube"),
                    duration=data.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(str(data.get("duration", "0:00"))),
                    message_id=m_id,
                    title=data.get("title", "Unknown")[:50],
                    thumbnail=data.get("thumbnail") or data.get("thumb"),
                    url=vid_url or f"{self.base}{vid_id}",
                    view_count=data.get("views", "0"),
                    video=video,
                )
            except Exception as e:
                logger.warning(f"Failed to map API response: {e}")

        # Layer 2: Native py_yt VideosSearch Fallback
        try:
            results = VideosSearch(search_query, limit=1)
            for result in (await results.next())["result"]:
                dur_str = result.get("duration", "0:00")
                return Track(
                    id=result["id"],
                    channel_name=result.get("channel", {}).get("name", "Unknown"),
                    duration=dur_str,
                    duration_sec=int(time_to_seconds(dur_str)),
                    message_id=m_id,
                    title=result["title"][:50],
                    thumbnail=result["thumbnails"][0]["url"].split("?")[0],
                    url=f"{self.base}{result['id']}",
                    view_count=result.get("viewCount", {}).get("short", "0"),
                    video=video,
                )
        except Exception as e:
            logger.warning(f"Native search fallback failed: {e}")

        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist.get("videos", [])[:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=int(time_to_seconds(data.get("duration"))) if data.get("duration") else 0,
                    title=data.get("title")[:50],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link", "").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception as e:
            logger.warning(f"Playlist error: {e}")
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        link = f"{self.base}{video_id}"
        if video:
            return await download_video(link)
        else:
            return await download_song(link)

    async def url(self, message: Message) -> Union[str, None]:
        if message.from_user and message.from_user.is_bot:
            return None
        text = message.text or message.caption
        if text:
            urls = re.findall(r'(https?://[^\s]+)', text)
            for u in urls:
                if self.valid(u):
                    return u
        return None
