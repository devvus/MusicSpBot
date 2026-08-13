# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import asyncio
import aiohttp
from py_yt import Playlist, VideosSearch
from anony import config, logger
from anony.helpers import Track, utils

# Custom API settings from config
API_URL = config.API_URL or os.environ.get("MusicSp_API_URL", "https://apisparrow.site")
API_KEY = config.API_KEY or os.environ.get("MusicSp_API_KEY", "sparrowwgZosKCACRJFCkQ7YT4uIU0B")

if API_URL:
    API_URL = API_URL.rstrip("/")

DOWNLOAD_DIR = "downloads"

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
        pass

    async def fetch_custom_yt_data(self, query: str) -> dict | None:
        if not API_URL or not API_KEY:
            return None
        
        try:
            async with aiohttp.ClientSession() as session:
                # Search endpoint: /search?q={query}&api_key={key}
                async with session.get(
                    f"{API_URL}/search",
                    params={"q": query, "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        if data and "results" in data and data["results"]:
                            return data["results"][0]
        except Exception as e:
            logger.warning(f"Custom YouTube API search failed: {e}")
        return None

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        # Advanced Search: Check if it's a URL or search query
        if self.valid(query):
            # If it's a URL, we still might want to get metadata
            # For now, let's treat it as a search for the ID
            vid_id = query.split("v=")[-1].split("&")[0] if "v=" in query else query.split("/")[-1]
            query = vid_id

        # Try custom API first
        data = await self.fetch_custom_yt_data(query)
        
        if data:
            try:
                vid_id = data.get("id") or data.get("video_id")
                # Construct direct stream URL
                # The user said: "Direct URL return karne ki waja se local server par song download karne ki zaroorat nahi padegi"
                # We will use the /download endpoint as the direct stream URL
                stream_url = f"{API_URL}/download?url={vid_id}&type={'video' if video else 'audio'}&api_key={API_KEY}"
                
                return Track(
                    id=vid_id,
                    channel_name=data.get("channel", "Unknown"),
                    duration=data.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                    message_id=m_id,
                    title=data.get("title", "Unknown Track")[:50],
                    thumbnail=data.get("thumbnail", ""),
                    url=stream_url, # Use direct stream URL
                    view_count=data.get("views", "0"),
                    video=video,
                )
            except Exception as e:
                logger.warning(f"Failed to map custom API response: {e}")

        # Fallback to native search
        try:
            enhanced_query = f"{query} official audio" if not self.valid(query) else query
            _search = VideosSearch(enhanced_query, limit=1)
            results = await _search.next()
            if results and results.get("result"):
                res = results["result"][0]
                vid_id = res.get("id")
                # Even for native search, we can try to use our custom API for streaming
                stream_url = f"{API_URL}/download?url={vid_id}&type={'video' if video else 'audio'}&api_key={API_KEY}"
                
                return Track(
                    id=vid_id,
                    channel_name=res.get("channel", {}).get("name", "Unknown"),
                    duration=res.get("duration", "0:00"),
                    duration_sec=utils.to_seconds(res.get("duration", "0:00")),
                    message_id=m_id,
                    title=res.get("title", "Unknown Track")[:50],
                    thumbnail=res.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
                    url=stream_url,
                    view_count=res.get("viewCount", {}).get("short", "0"),
                    video=video,
                )
        except Exception as e:
            logger.error(f"YouTube Search Error: {e}")
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            if plist and "videos" in plist:
                for data in plist["videos"][:limit]:
                    vid_id = data.get("id")
                    stream_url = f"{API_URL}/download?url={vid_id}&type={'video' if video else 'audio'}&api_key={API_KEY}"
                    track = Track(
                        id=vid_id,
                        channel_name=data.get("channel", {}).get("name", ""),
                        duration=data.get("duration", "0:00"),
                        duration_sec=utils.to_seconds(data.get("duration", "0:00")),
                        title=data.get("title", "Unknown")[:50],
                        thumbnail=data.get("thumbnails", [{}])[-1].get("url", "").split("?")[0],
                        url=stream_url,
                        user=user,
                        view_count="",
                        video=video,
                    )
                    tracks.append(track)
        except Exception as e:
            logger.warning(f"Playlist error: {e}")
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        # Since we are using direct streaming, we just return the URL
        # But for compatibility with existing play.py logic which expects a local file path if it calls download()
        # we will return the direct stream URL itself.
        return f"{API_URL}/download?url={video_id}&type={'video' if video else 'audio'}&api_key={API_KEY}"
