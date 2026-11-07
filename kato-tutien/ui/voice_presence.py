"""Keep the bot connected to a configured voice channel 24/7."""
from __future__ import annotations

import asyncio
import logging

import discord

import config
from ui.music.player import music_manager

logger = logging.getLogger("kato.voice")


async def connect_voice_channel(client: discord.Client) -> discord.VoiceClient | None:
    channel_id = int(getattr(config, "VOICE_CHANNEL_ID", 0) or 0)
    if not channel_id:
        return None
    channel = client.get_channel(channel_id)
    if channel is None:
        try:
            channel = await client.fetch_channel(channel_id)
        except Exception:
            logger.exception("Cannot fetch voice channel %s", channel_id)
            return None
    if not isinstance(channel, discord.VoiceChannel):
        logger.error("KATO_VOICE_CHANNEL_ID=%s is not a voice channel", channel_id)
        return None

    guild = channel.guild
    existing = guild.voice_client
    self_deaf = bool(getattr(config, "VOICE_SELF_DEAF", True))
    if existing and existing.is_connected():
        if existing.channel and existing.channel.id == channel.id:
            return existing
        # Do not yank the bot away while music is active in another channel.
        if music_manager.is_music_active(guild.id):
            logger.info("Skip voice move — music active in guild %s", guild.id)
            return existing
        try:
            await existing.move_to(channel)
            return existing
        except Exception:
            logger.exception("Failed to move voice client; reconnecting")
            try:
                await existing.disconnect(force=True)
            except Exception:
                pass

    try:
        vc = await channel.connect(reconnect=True, self_deaf=self_deaf, self_mute=False)
        logger.info("Joined voice channel %s (%s)", channel.name, channel.id)
        return vc
    except Exception:
        logger.exception("Failed to join voice channel %s", channel_id)
        return None


async def voice_keepalive_loop(client: discord.Client) -> None:
    """Reconnect periodically so the bot stays in voice around the clock."""
    await client.wait_until_ready()
    if not int(getattr(config, "VOICE_CHANNEL_ID", 0) or 0):
        logger.info("VOICE_CHANNEL_ID not set — voice presence disabled")
        return
    while not client.is_closed():
        try:
            await connect_voice_channel(client)
        except Exception:
            logger.exception("voice keepalive tick failed")
        await asyncio.sleep(45)


def start_voice_presence(client: discord.Client) -> asyncio.Task | None:
    if not int(getattr(config, "VOICE_CHANNEL_ID", 0) or 0):
        return None
    task = getattr(client, "_kato_voice_task", None)
    if task is not None and not task.done():
        return task
    task = client.loop.create_task(voice_keepalive_loop(client), name="kato-voice-keepalive")
    client._kato_voice_task = task  # type: ignore[attr-defined]
    return task
