import os
import re
import aiohttp
from typing import Union
from pyrogram.types import Message
import config

class YouTubeAPI:
    def __init__(self):
        self.base_url = getattr(config, "API_URL", "https://apisparrow.site")
        self.api_key = getattr(config, "API_KEY", "sparrowwgZosKCACRJFCkQ7YT4uIU0B")

    async def _fetch_api(self, query_or_url: str):
        """Custom API se response lene ke liye inner function"""
        if not self.base_url:
            return None

        # Build endpoint URL and params for MusicSp / ApiSparrow
        endpoint = f"{self.base_url.rstrip('/')}/yt"
        headers = {
            "User-Agent": "Mozilla/5.0"
        }
        params = {
            "api_key": self.api_key,
            "query": query_or_url
        }

        async with aiohttp.ClientSession() as session:
            try:
                async with session.get(endpoint, params=params, headers=headers, timeout=20) as resp:
                    if resp.status == 200:
                        data = await resp.json()
                        
                        # Handle direct result or wrapped response
                        res = data.get("result") if "result" in data else data
                        
                        stream_url = (
                            res.get("stream_url") or 
                            res.get("download_url") or 
                            res.get("url") or 
                            res.get("link")
                        )
                        
                        return {
                            "stream_url": stream_url,
                            "title": res.get("title", "Music Track"),
                            "duration": int(res.get("duration", 0)),
                            "thumb": res.get("thumbnail") or res.get("thumb", ""),
                            "vidid": res.get("id") or res.get("vidid", "custom_id")
                        }
            except Exception as e:
                print(f"[MusicSp API Error]: {e}")
        return None

    async def exists(self, link: str, is_path=False):
        if is_path:
            return os.path.exists(link)
        if re.search(r"(?:youtu\.be\/|youtube\.com\/)", link):
            return True
        return False

    async def url(self, message: Message) -> Union[str, None]:
        if message.from_user and message.from_user.is_bot:
            return None
        text = message.text or message.caption
        if text:
            urls = re.findall(r'(https?://[^\s]+)', text)
            for u in urls:
                if await self.exists(u):
                    return u
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        data = await self._fetch_api(link)
        if data:
            return data["title"], data["duration"], data["thumb"], data["vidid"]
        return "Music Track", 0, "", "custom_id"

    async def title(self, link: str, videoid: Union[bool, str] = None):
        data = await self._fetch_api(link)
        return data["title"] if data else "Music Track"

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        data = await self._fetch_api(link)
        return data["duration"] if data else 0

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        data = await self._fetch_api(link)
        return data["thumb"] if data else ""

    async def download(
        self,
        link: str,
        mystic=None,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: str = None,
        title: str = None,
    ):
        """Direct stream link retreive karke PyTgCalls ko pass karega"""
        data = await self._fetch_api(link)
        if data and data.get("stream_url"):
            # Direct Stream URL return karega ffmpeg playback ke liye
            return data["stream_url"], True
        
        return None, False

# Export instance for bot compatibility
YouTube = YouTubeAPI()
