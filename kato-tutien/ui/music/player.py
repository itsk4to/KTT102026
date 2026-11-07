"""Simple guild music player — YouTube links via yt-dlp + FFmpeg."""
from __future__ import annotations

import asyncio
import logging
from collections import deque
from dataclasses import dataclass
from typing import Any

import discord

logger = logging.getLogger("kato.music")

YTDL_OPTS = {
    "format": "bestaudio/best",
    "quiet": True,
    "no_warnings": True,
    "default_search": "ytsearch",
    "source_address": "0.0.0.0",
    "noplaylist": True,
    "extract_flat": False,
}

FFMPEG_OPTS = {
    "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
    "options": "-vn",
}


@dataclass
class Track:
    title: str
    url: str
    webpage_url: str
    duration: int | None
    requester_id: int


def _ytdlp():
    try:
        import yt_dlp
    except ImportError as exc:
        raise RuntimeError(
            "Chưa cài **yt-dlp**. Thêm `yt-dlp` vào requirements và redeploy."
        ) from exc
    return yt_dlp


async def resolve_track(query: str, requester_id: int) -> Track:
    ytdlp = _ytdlp()

    def _extract() -> dict[str, Any]:
        with ytdlp.YoutubeDL(YTDL_OPTS) as ydl:
            info = ydl.extract_info(query, download=False)
            if info is None:
                raise RuntimeError("Không lấy được thông tin nguồn nhạc.")
            if "entries" in info:
                entries = [e for e in (info.get("entries") or []) if e]
                if not entries:
                    raise RuntimeError("Không tìm thấy bài hát.")
                info = entries[0]
            # Prefer a direct URL; fallback to webpage
            stream_url = info.get("url")
            if not stream_url:
                raise RuntimeError("Không lấy được luồng audio.")
            return {
                "title": info.get("title") or "Không rõ tên",
                "url": stream_url,
                "webpage_url": info.get("webpage_url") or query,
                "duration": info.get("duration"),
            }

    data = await asyncio.to_thread(_extract)
    return Track(
        title=str(data["title"])[:200],
        url=str(data["url"]),
        webpage_url=str(data["webpage_url"]),
        duration=int(data["duration"]) if data.get("duration") else None,
        requester_id=int(requester_id),
    )


class GuildMusicPlayer:
    def __init__(self, guild_id: int):
        self.guild_id = guild_id
        self.queue: deque[Track] = deque()
        self.current: Track | None = None
        self.voice: discord.VoiceClient | None = None
        self._lock = asyncio.Lock()
        self._play_next_handle: asyncio.Task | None = None

    @property
    def is_active(self) -> bool:
        return bool(self.current or self.queue or (self.voice and self.voice.is_playing()))

    async def connect(self, channel: discord.VoiceChannel) -> discord.VoiceClient:
        guild = channel.guild
        vc = guild.voice_client
        if vc and vc.is_connected():
            if vc.channel and vc.channel.id != channel.id:
                await vc.move_to(channel)
            self.voice = vc
            return vc
        self.voice = await channel.connect(reconnect=True, self_deaf=True)
        return self.voice

    async def enqueue(self, track: Track) -> int:
        async with self._lock:
            self.queue.append(track)
            position = len(self.queue)
            should_start = self.current is None and not (self.voice and self.voice.is_playing())
        if should_start:
            await self._play_next()
        return position

    async def skip(self) -> Track | None:
        async with self._lock:
            skipped = self.current
            if self.voice and (self.voice.is_playing() or self.voice.is_paused()):
                self.voice.stop()  # triggers after callback -> _play_next
            elif self.queue:
                # nothing playing but queue has items
                pass
            return skipped

    async def stop(self) -> None:
        async with self._lock:
            self.queue.clear()
            self.current = None
            if self.voice and (self.voice.is_playing() or self.voice.is_paused()):
                self.voice.stop()

    async def leave(self) -> None:
        await self.stop()
        if self.voice and self.voice.is_connected():
            await self.voice.disconnect(force=True)
        self.voice = None

    async def _play_next(self) -> None:
        async with self._lock:
            if not self.queue:
                self.current = None
                return
            if self.voice is None or not self.voice.is_connected():
                return
            track = self.queue.popleft()
            self.current = track

        try:
            source = discord.FFmpegPCMAudio(track.url, **FFMPEG_OPTS)
            # Volume transform optional
            self.voice.play(source, after=lambda err: self._on_track_end(err))
        except Exception:
            logger.exception("Failed to start track %s", track.title)
            self.current = None
            await self._play_next()

    def _on_track_end(self, error: Exception | None) -> None:
        if error:
            logger.warning("Track ended with error: %s", error)
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            return
        loop.call_soon_threadsafe(lambda: asyncio.create_task(self._play_next()))


class MusicManager:
    def __init__(self) -> None:
        self._players: dict[int, GuildMusicPlayer] = {}

    def player(self, guild_id: int) -> GuildMusicPlayer:
        if guild_id not in self._players:
            self._players[guild_id] = GuildMusicPlayer(guild_id)
        return self._players[guild_id]

    def is_music_active(self, guild_id: int) -> bool:
        p = self._players.get(guild_id)
        return bool(p and p.is_active)


music_manager = MusicManager()
