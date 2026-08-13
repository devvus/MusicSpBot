# Copyright (c) 2025 AnonymousX1025
# Licensed under the MIT License.
# This file is part of AnonXMusic

import os
import re
import asyncio
import aiohttp
import yt_dlp
from typing import Union
from pathlib import Path
from py_yt import Playlist, VideosSearch
from anony import config, logger
from anony.helpers import Track, utils

DOWNLOAD_DIR = "downloads"

class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = re.compile(
            r"(https?://)?(www\.|m\.|music\.)?"
            r"(youtube\.com/(watch\?v=|shorts/|playlist\?list=)|youtu\.be/)"
            r"([A-Za-z0-9_-]{11}|PL[A-Za-z0-9_-]+)([&?][^\s]*)?"
        )
        self.iregex = re.compile(
            r"https?://(?:www\.|m\.|music\.)?(?:youtube\.com|youtu\.be)"
            r"(?!/(watch\?v=[A-Za-z0-9_-]{11}|shorts/[A-Za-z0-9_-]{11}"
            r"|playlist\?list=PL[A-Za-z0-9_-]+|[A-Za-z0-9_-]{11}))\S*"
        )
        self.base_url = config.CUSTOM_YT_API
        self.api_key = config.CUSTOM_YT_KEY

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    async def _fetch_api(self, query_or_url: str):
        """Custom API se response lene ke liye inner function"""
        if not self.base_url:
            return None

        headers = {
            "x-api-key": self.api_key,
            "User-Agent": "Mozilla/5.0"
        }
        params = {
            "query": query_or_url,
            "api_key": self.api_key
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(self.base_url, params=params, headers=headers, timeout=15) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        return {
                            "stream_url": data.get("stream_url") or data.get("url") or data.get("download_url"),
                            "title": data.get("title", "Unknown Track"),
                            "duration": int(data.get("duration", 0)),
                            "thumb": data.get("thumbnail") or data.get("thumb", ""),
                            "vidid": data.get("id") or data.get("vidid", "custom_id")
                        }
            except Exception as e:
                logger.warning(f"[Custom YT API Error]: {e}")
        return None

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        # Step 1: Try Custom API Search first
        data = await self._fetch_api(query)
        if data:
            return Track(
                id=data["vidid"],
                channel_name="Custom API",
                duration=utils.to_min(data["duration"]),
                duration_sec=data["duration"],
                message_id=m_id,
                title=data["title"][:50],
                thumbnail=data["thumb"],
                url=f"{self.base}{data['vidid']}" if not data["stream_url"].startswith("http") else data["stream_url"],
                view_count="0",
                video=video,
            )

        # Step 2: Fallback to native yt-dlp ytsearch fallback
        search_query = query if self.valid(query) else f"{query} song lyrics"
        try:
            loop = asyncio.get_event_loop()
            def _search():
                ydl_opts = {'quiet': True, 'extract_flat': True, 'default_search': 'ytsearch'}
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(f"ytsearch:{search_query}", download=False)
            
            info = await loop.run_in_executor(None, _search)
            if info and "entries" in info and info["entries"]:
                entry = info["entries"][0]
                vid_id = entry.get("id")
                return Track(
                    id=vid_id,
                    channel_name=entry.get("uploader"),
                    duration=utils.to_min(entry.get("duration", 0)),
                    duration_sec=entry.get("duration", 0),
                    message_id=m_id,
                    title=entry.get("title")[:50],
                    thumbnail=entry.get("thumbnail"),
                    url=f"https://www.youtube.com/watch?v={vid_id}",
                    view_count=str(entry.get("view_count", "")),
                    video=video,
                )
        except Exception as e:
            logger.warning(f"yt-dlp search fallback failed: {e}")
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
                    duration_sec=utils.to_seconds(data.get("duration")),
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
        """Direct stream link retrieve karke PyTgCalls ko pass karega"""
        data = await self._fetch_api(video_id)
        if data and data.get("stream_url"):
            # Direct Stream URL return karega ffmpeg playback ke liye
            return data["stream_url"]
        
        # Fallback to local download if API fails to provide stream URL
        os.makedirs(DOWNLOAD_DIR, exist_ok=True)
        url = f"https://www.youtube.com/watch?v={video_id}"
        ydl_opts = {
            'format': 'bestvideo[ext=mp4]+bestaudio/best' if video else 'bestaudio/best',
            'outtmpl': os.path.join(DOWNLOAD_DIR, f"{video_id}.%(ext)s"),
            'quiet': True,
            'no_warnings': True,
            'nocheckcertificate': True,
            'geo_bypass': True,
            'extractor_args': {"youtube": {"player_client": ["android", "web", "mweb"]}},
        }

        loop = asyncio.get_event_loop()
        try:
            def _download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            await loop.run_in_executor(None, _download)
            for file in os.listdir(DOWNLOAD_DIR):
                if file.startswith(video_id):
                    return os.path.join(DOWNLOAD_DIR, file)
        except Exception as e:
            logger.warning(f"yt-dlp download fallback failed: {e}")
        return None
