"""Prefix music commands: .join .play .skip .stop .queue .leave"""
from __future__ import annotations

import discord

from ui.embeds import base_embed, error_embed, success_embed
from ui.music.player import music_manager, resolve_track


def _fmt_duration(seconds: int | None) -> str:
    if not seconds:
        return "?:??"
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m}:{s:02d}"


async def _require_voice_member(message: discord.Message) -> discord.VoiceChannel | None:
    if message.guild is None:
        await message.reply(embed=error_embed("Chỉ dùng lệnh nhạc trong máy chủ."))
        return None
    member = message.author
    if not isinstance(member, discord.Member) or member.voice is None or member.voice.channel is None:
        await message.reply(embed=error_embed("Đạo hữu cần vào kênh thoại trước đã."))
        return None
    if not isinstance(member.voice.channel, discord.VoiceChannel):
        await message.reply(embed=error_embed("Chỉ hỗ trợ kênh thoại thường (không phải Stage)."))
        return None
    return member.voice.channel


async def cmd_join(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    channel = await _require_voice_member(message)
    if channel is None:
        return
    assert message.guild is not None
    player = music_manager.player(message.guild.id)
    try:
        await player.connect(channel)
    except Exception as exc:
        await message.reply(embed=error_embed(f"Không vào được kênh thoại: {exc}"))
        return
    await message.reply(embed=success_embed("Đã vào kênh", f"Bot đã join **{channel.name}**."))


async def cmd_leave(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    if message.guild is None:
        await message.reply(embed=error_embed("Chỉ dùng trong máy chủ."))
        return
    player = music_manager.player(message.guild.id)
    try:
        await player.leave()
    except Exception as exc:
        await message.reply(embed=error_embed(f"Không rời kênh được: {exc}"))
        return
    await message.reply(embed=success_embed("Đã rời kênh", "Bot đã ngắt kết nối thoại."))


async def cmd_play(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    if not args:
        await message.reply(embed=error_embed("Cách dùng: `.play <link YouTube hoặc tên bài>`"))
        return
    channel = await _require_voice_member(message)
    if channel is None:
        return
    assert message.guild is not None
    query = " ".join(args).strip()
    player = music_manager.player(message.guild.id)
    status = await message.reply(embed=base_embed("🎵 Nhạc", "Đang tìm nguồn…"))
    try:
        await player.connect(channel)
        track = await resolve_track(query, message.author.id)
        position = await player.enqueue(track)
    except Exception as exc:
        await status.edit(embed=error_embed(str(exc)))
        return

    if position <= 1 and player.current and player.current.webpage_url == track.webpage_url:
        body = (
            f"**Đang phát:** [{track.title}]({track.webpage_url})\n"
            f"Thời lượng: `{_fmt_duration(track.duration)}`\n"
            f"Yêu cầu bởi: <@{track.requester_id}>"
        )
        title = "🎵 Đang phát"
    else:
        body = (
            f"**Đã xếp hàng #{position}:** [{track.title}]({track.webpage_url})\n"
            f"Thời lượng: `{_fmt_duration(track.duration)}`\n"
            f"Yêu cầu bởi: <@{track.requester_id}>"
        )
        title = "🎵 Đã thêm vào hàng chờ"
    await status.edit(embed=base_embed(title, body))


async def cmd_skip(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    if message.guild is None:
        await message.reply(embed=error_embed("Chỉ dùng trong máy chủ."))
        return
    player = music_manager.player(message.guild.id)
    if not player.current and not player.queue:
        await message.reply(embed=error_embed("Không có bài nào đang phát."))
        return
    skipped = await player.skip()
    name = skipped.title if skipped else "bài hiện tại"
    await message.reply(embed=success_embed("Đã bỏ qua", f"Skip: **{name}**"))


async def cmd_stop(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    if message.guild is None:
        await message.reply(embed=error_embed("Chỉ dùng trong máy chủ."))
        return
    player = music_manager.player(message.guild.id)
    await player.stop()
    await message.reply(embed=success_embed("Đã dừng", "Dừng nhạc và xóa hàng chờ."))


async def cmd_queue(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    if message.guild is None:
        await message.reply(embed=error_embed("Chỉ dùng trong máy chủ."))
        return
    player = music_manager.player(message.guild.id)
    lines: list[str] = []
    if player.current:
        lines.append(
            f"**Đang phát:** [{player.current.title}]({player.current.webpage_url}) "
            f"`{_fmt_duration(player.current.duration)}`"
        )
    if player.queue:
        lines.append("**Hàng chờ:**")
        for i, track in enumerate(list(player.queue)[:15], start=1):
            lines.append(f"`{i}.` [{track.title}]({track.webpage_url}) `{_fmt_duration(track.duration)}`")
        if len(player.queue) > 15:
            lines.append(f"… và {len(player.queue) - 15} bài nữa")
    if not lines:
        await message.reply(embed=base_embed("🎵 Hàng chờ", "Trống."))
        return
    await message.reply(embed=base_embed("🎵 Hàng chờ", "\n".join(lines)))
