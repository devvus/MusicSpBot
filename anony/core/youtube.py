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

# Custom API settings from MusicSpBot logic
# Priority: config.py -> MusicSp environment variables -> Default values
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

    url = f"https://www.youtube.com/watch?v={video_id}"
    
    # Try Custom API First
    if API_URL:
        logger.info(f"Attempting Custom API download for: {video_id}")
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(
                    f"{API_URL}/download",
                    params={"url": url, "type": "audio", "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=600)
                ) as resp:
                    if resp.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in resp.content.iter_chunked(131072):
                                f.write(chunk)
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            logger.info(f"Custom API download successful: {video_id}")
                            return file_path
                    else:
                        logger.warning(f"Custom API returned status {resp.status} for {video_id}")
        except Exception as e:
            logger.warning(f"Custom API failed for {video_id}: {e}")

    # Native Fallback (yt-dlp)
    logger.info(f"Using Native Fallback for: {video_id}")
    try:
        import yt_dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logger.info(f"Native download successful: {video_id}")
            return file_path
    except Exception as e:
        logger.error(f"Native download failed for {video_id}: {e}")
        
    return None

async def download_video(video_id: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    url = f"https://www.youtube.com/watch?v={video_id}"

    # Try Custom API First
    if API_URL:
        logger.info(f"Attempting Custom API video download for: {video_id}")
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(
                    f"{API_URL}/download",
                    params={"url": url, "type": "video", "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=900)
                ) as resp:
                    if resp.status == 200:
                        with open(file_path, "wb") as f:
                            async for chunk in resp.content.iter_chunked(131072):
                                f.write(chunk)
                        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
                            logger.info(f"Custom API video download successful: {video_id}")
                            return file_path
                    else:
                        logger.warning(f"Custom API returned status {resp.status} for {video_id}")
        except Exception as e:
            logger.warning(f"Custom API video failed for {video_id}: {e}")

    # Native Fallback (yt-dlp)
    logger.info(f"Using Native Fallback for video: {video_id}")
    try:
        import yt_dlp
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": file_path,
            "quiet": True,
            "no_warnings": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logger.info(f"Native video download successful: {video_id}")
            return file_path
    except Exception as e:
        logger.error(f"Native video download failed for {video_id}: {e}")

    return None

class YouTube:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.cookies = []
        self.checked = False
        self.cookie_dir = "anony/cookies"
        self.warned = False
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

    def valid(self, url: str) -> bool:
        return bool(re.match(self.regex, url))

    def invalid(self, url: str) -> bool:
        return bool(re.match(self.iregex, url))

    async def fetch_custom_yt_data(self, query: str) -> dict | None:
        if not API_URL or not API_KEY:
            return None
        
        try:
            async with aiohttp.ClientSession(connector=aiohttp.TCPConnector(ssl=False)) as session:
                async with session.get(
                    f"{API_URL}/search",
                    params={"q": query, "api_key": API_KEY},
                    timeout=aiohttp.ClientTimeout(total=15)
                ) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        logger.info(f"Custom API search result for '{query}': {data}")
                        if data and "results" in data and data["results"]:
                            return data["results"][0]
                    else:
                        logger.warning(f"Custom API search returned status {resp.status} for '{query}'")
        except Exception as e:
            logger.warning(f"Custom YouTube API search failed for '{query}': {e}")
        return None

    async def search(self, query: str, m_id: int, video: bool = False) -> Track | None:
        # Step 5: Primary Search Engine (Custom API)
        data = await self.fetch_custom_yt_data(query)
        
        if data:
            try:
                # Extract video ID from URL if not present
                vid_url = data.get("url")
                vid_id = data.get("id")
                if not vid_id and vid_url:
                    if "v=" in vid_url:
                        vid_id = vid_url.split("v=")[-1].split("&")[0]
                    else:
                        vid_id = vid_url.split("/")[-1]
                
                return Track(
                    id=vid_id,
                    channel_name=data.get("channel"),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnail"),
                    url=vid_url or f"{self.base}{vid_id}",
                    view_count=data.get("views"),
                    video=video,
                )
            except Exception as e:
                logger.warning(f"Failed to map custom API response: {e}")

        # Step 6: Fallback to native search (py_yt)
        try:
            _search = VideosSearch(query, limit=1, with_live=False)
            results = await _search.next()
            if results and results["result"]:
                data = results["result"][0]
                return Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name"),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    message_id=m_id,
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                    url=data.get("link"),
                    view_count=data.get("viewCount", {}).get("short"),
                    video=video,
                )
        except Exception as e:
            logger.warning(f"Native search failed: {e}")
        return None

    async def playlist(self, limit: int, user: str, url: str, video: bool) -> list[Track | None]:
        tracks = []
        try:
            plist = await Playlist.get(url)
            for data in plist["videos"][:limit]:
                track = Track(
                    id=data.get("id"),
                    channel_name=data.get("channel", {}).get("name", ""),
                    duration=data.get("duration"),
                    duration_sec=utils.to_seconds(data.get("duration")),
                    title=data.get("title")[:25],
                    thumbnail=data.get("thumbnails")[-1].get("url").split("?")[0],
                    url=data.get("link").split("&list=")[0],
                    user=user,
                    view_count="",
                    video=video,
                )
                tracks.append(track)
        except Exception:
            pass
        return tracks

    async def download(self, video_id: str, video: bool = False) -> str | None:
        # Use custom API logic for downloading
        if video:
            return await download_video(video_id)
        else:
            return await download_song(video_id)
