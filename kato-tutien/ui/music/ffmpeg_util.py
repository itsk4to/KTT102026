"""Locate an FFmpeg binary — system PATH first, then bundled imageio-ffmpeg."""
from __future__ import annotations

import logging
import shutil

logger = logging.getLogger("kato.ffmpeg")

_cached: str | None = None


def get_ffmpeg_executable() -> str:
    """Return path to ffmpeg. Raises RuntimeError if none is available."""
    global _cached
    if _cached:
        return _cached

    found = shutil.which("ffmpeg")
    if found:
        _cached = found
        logger.info("Using system FFmpeg: %s", found)
        return found

    try:
        import imageio_ffmpeg

        found = imageio_ffmpeg.get_ffmpeg_exe()
        if found:
            _cached = found
            logger.info("Using bundled imageio-ffmpeg: %s", found)
            return found
    except Exception:
        logger.exception("imageio-ffmpeg not available")

    raise RuntimeError(
        "Không tìm thấy **FFmpeg**.\n"
        "• Deploy đã kèm `imageio-ffmpeg` — hãy redeploy bản mới.\n"
        "• Hoặc cài FFmpeg trên host (`apt install ffmpeg` / nixpacks)."
    )
