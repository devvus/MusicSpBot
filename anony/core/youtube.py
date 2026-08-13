# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import random
import asyncio
import aiohttp
from pathlib import Path
from py_yt import Playlist, VideosSearch
from anony import config, logger
from anony.helpers import Track, utils

# Custom API settings
API_URL = config.YOUTUBE_API_URL or os.environ.get("MusicSp_API_URL", "https://apisparrow.site/")
API_KEY = config.YOUTUBE_API_KEY or os.environ.get("MusicSp_API_KEY", "sparrowwgZosKCACRJFCkQ7YT4uIU0B")

if API_URL:
    API_URL = API_URL.rstrip("/")

DOWNLOAD_DIR = "downloads"

async def download_song(video_id: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp3")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    if not API_URL:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params={"url": video_id, "type": "audio", "api_key": API_KEY},
                timeout=aiohttp.ClientTimeout(total=600)
            ) as resp:
                if resp.status != 200:
                    logger.warning(f"Custom API download returned status {resp.status}")
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception as e:
        logger.warning(f"Custom API audio download failed: {e}")
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
        return None

async def download_video(video_id: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    if not API_URL:
        return None

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(
                f"{API_URL}/download",
                params={"url": video_id, "type": "video", "api_key": API_KEY},
                timeout=aiohttp.ClientTimeout(total=900)
            ) as resp:
                if resp.status != 200:
                    return None
                with open(file_path, "wb") as f:
                    async for chunk in resp.content.iter_chunked(131072):
                        f.write(chunk)
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
        return None
    except Exception as e:
        logger.warning(f"Custom API video download failed: {e}")
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
        return None

class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return not self.valid(url)

    async def save_cookies(self, url: str):
        """Placeholder for cookie saving logic if needed"""
        logger.info(f"DEBUG: save_cookies called with {url}")
        pass

    async def fetch_custom_yt_data(self, query: str) -> dict | None:
        if not API_URL or not API_KEY:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{API_URL}/search",
                    params={"q": query, "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and "results" in data and data["results"]:
                            return data["results"][0]
        except Exception as e:
            logger.warning(f"Custom YouTube API search failed: {e}")
        return None

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        # Try custom API first
        data = await self.fetch_custom_yt_data(query)
        
        if data:
            try:
                vid_url = data.get("url")
                vid_id = data.get("id") or data.get("video_id")
                if not vid_id and vid_url:
                    if "v=" in vid_url:
                        vid_id = vid_url.split("v=")[-1].split("&")[0]
                    else:
                        vid_id = vid_url.split("/")[-1]
                
                return Track(
                    id=vid_id,
                    channel_name=data.get("channel", "Unknown"),
                    duration=data.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                    message_id=m_id,
                    title=data.get("title", "Unknown Track")[:50],
                    thumbnail=data.get("thumbnail", ""),
                    url=vid_url or f"{self.base}{vid_id}",
                    view_count=data.get("views", "0"),
                    video=video,
                )
            except Exception as e:
                logger.warning(f"Failed to map custom API response: {e}")

        # Fallback to native search
        try:
            _search = VideosSearch(query, limit=1)
            results = await _search.next()
            if results and results.get("result"):
                res = results["result"][0]
                return Track(
                    id=res.get("id"),
                    channel_name=res.get("channel", {}).get("name", "Unknown"),
                    duration=res.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(res.get("duration", "0:00")),
                    message_id=m_id,
                    title=res.get("title", "Unknown Track")[:50],
                    thumbnail=res.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
                    url=res.get("link", f"{self.base}{res.get('id')}"),
                    view_count=res.get("viewCount", {}).get("short", "0"),
                    video=video,
                )
        except Exception as e:
            logger.warning(f"Native search failed: {e}")
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            if plist and "videos" in plist:
                for data in plist["videos"][:limit]:
                    track = Track(
                        id=data.get("id"),
                        channel_name=data.get("channel", {}).get("name", ""),
                        duration=data.get("duration", "0:00"),
                        duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                        title=data.get("title", "Unknown")[:50],
                        thumbnail=data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
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
        if video:
            return await download_video(video_id)
        else:
            return await download_song(video_id)
