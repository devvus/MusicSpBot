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
        try:
            async with aiohttp.ClientSession() as session:
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
                            return file_path
                    else:
                        logger.warning(f"Custom API download returned status {resp.status}, falling back to yt-dlp")
        except Exception as e:
            logger.warning(f"Custom API audio download failed: {e}")

    # Advanced yt-dlp Fallback with bypass options
    try:
        import yt_dlp
        ydl_opts = {
            "format": "bestaudio/best",
            "outtmpl": file_path,
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
            "extractor_args": {"youtube": {"player_client": ["android", "web", "mweb", "ios"]}},
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
            }
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
    except Exception as e:
        logger.error(f"yt-dlp fallback download failed: {e}")
        if os.path.exists(file_path):
            try: os.remove(file_path)
            except: pass
    return None

async def download_video(video_id: str) -> str:
    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.mp4")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    url = f"https://www.youtube.com/watch?v={video_id}"

    if API_URL:
        try:
            async with aiohttp.ClientSession() as session:
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
                            return file_path
        except Exception as e:
            logger.warning(f"Custom API video download failed: {e}")

    try:
        import yt_dlp
        ydl_opts = {
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
            "outtmpl": file_path,
            "quiet": True,
            "no_warnings": True,
            "geo_bypass": True,
            "nocheckcertificate": True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            await asyncio.to_thread(ydl.download, [url])
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            return file_path
    except Exception as e:
        logger.error(f"Native video download failed: {e}")
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
        # Smart search supporting title or partial lyrics via ytsearch fallback
        queries_to_try = [query]
        if not query.startswith("http"):
            if len(query.split()) > 3:
                queries_to_try.insert(0, f"ytsearch:{query} lyrics")
                queries_to_try.insert(1, f"{query} song")
            else:
                queries_to_try.append(f"{query} song")

        data = None
        for q in queries_to_try:
            if q.startswith("ytsearch:"):
                try:
                    import yt_dlp
                    ydl_opts = {"quiet": True, "extract_flat": True, "default_search": "ytsearch"}
                    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                        info = await asyncio.to_thread(ydl.extract_info, q, download=False)
                        if info and "entries" in info and info["entries"]:
                            entry = info["entries"][0]
                            data = {
                                "id": entry.get("id"),
                                "title": entry.get("title"),
                                "duration": utils.to_min(entry.get("duration", 0)),
                                "url": f"https://www.youtube.com/watch?v={entry.get('id')}",
                                "thumbnail": entry.get("thumbnail"),
                                "channel": entry.get("uploader"),
                                "views": str(entry.get("view_count", ""))
                            }
                            break
                except Exception as e:
                    logger.warning(f"ytsearch failed: {e}")
            else:
                data = await self.fetch_custom_yt_data(q)
                if data:
                    break

        if not data:
            try:
                _search = VideosSearch(query, limit=1, with_live=False)
                results = await _search.next()
                if results and results["result"]:
                    res = results["result"][0]
                    data = {
                        "id": res.get("id"),
                        "title": res.get("title"),
                        "duration": res.get("duration"),
                        "url": res.get("link"),
                        "thumbnail": res.get("thumbnails", [{}])[-1].get("url").split("?")[0],
                        "channel": res.get("channel", {}).get("name"),
                        "views": res.get("viewCount", {}).get("short")
                    }
            except Exception as e:
                logger.warning(f"Native search failed: {e}")

        if data:
            try:
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
                    title=data.get("title")[:50],
                    thumbnail=data.get("thumbnail"),
                    url=vid_url or f"{self.base}{vid_id}",
                    view_count=data.get("views"),
                    video=video,
                )
            except Exception as e:
                logger.warning(f"Failed to map response: {e}")
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
                    title=data.get("title")[:50],
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
        if video:
            return await download_video(video_id)
        else:
            return await download_song(video_id)
