"""Text-to-speech in voice channel via edge-tts + FFmpeg."""
from __future__ import annotations

import asyncio
import logging
import os
import tempfile
from pathlib import Path

import discord

logger = logging.getLogger("kato.tts")

# Giọng tiếng Việt (Microsoft Edge neural)
DEFAULT_VOICE = "vi-VN-HoaiMyNeural"
ALT_VOICE = "vi-VN-NamMinhNeural"


async def synthesize_to_file(text: str, voice: str = DEFAULT_VOICE) -> str:
    try:
        import edge_tts
    except ImportError as exc:
        raise RuntimeError("Chưa cài **edge-tts**. Thêm vào requirements rồi redeploy.") from exc

    text = (text or "").strip()
    if not text:
        raise RuntimeError("Nội dung trống.")
    if len(text) > 500:
        raise RuntimeError("Tối đa 500 ký tự mỗi lần đọc.")

    fd, path = tempfile.mkstemp(suffix=".mp3", prefix="kato-tts-")
    os.close(fd)
    try:
        communicate = edge_tts.Communicate(text, voice)
        await communicate.save(path)
    except Exception:
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            pass
        raise
    return path


async def speak_in_channel(
    voice: discord.VoiceClient,
    text: str,
    *,
    voice_name: str = DEFAULT_VOICE,
) -> None:
    """Synthesize and play TTS; cleans up temp file when done."""
    path = await synthesize_to_file(text, voice=voice_name)

    done = asyncio.Event()

    def _after(err: Exception | None) -> None:
        if err:
            logger.warning("TTS playback error: %s", err)
        try:
            Path(path).unlink(missing_ok=True)
        except Exception:
            logger.exception("Could not delete TTS temp file")
        done.set()

    if voice.is_playing() or voice.is_paused():
        voice.stop()
        await asyncio.sleep(0.15)

    try:
        from ui.music.ffmpeg_util import get_ffmpeg_executable
        source = discord.FFmpegPCMAudio(path, executable=get_ffmpeg_executable())
        voice.play(source, after=_after)
    except Exception:
        Path(path).unlink(missing_ok=True)
        raise

    try:
        await asyncio.wait_for(done.wait(), timeout=120)
    except asyncio.TimeoutError:
        if voice.is_playing():
            voice.stop()
        Path(path).unlink(missing_ok=True)
