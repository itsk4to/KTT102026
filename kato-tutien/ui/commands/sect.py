from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed
from game.utils import fmt_amount
from ui.views.sect_view import SectMenuView

async def cmd_sect(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        view = SectMenuView(ctx.engine, str(message.author.id))
        await message.reply(embed=view.build_embed(), view=view)
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))


async def cmd_sect_create(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.taotong <tên>`"))
        return
    try:
        r = ctx.engine.sect.create(str(message.author.id), " ".join(args))
        await message.reply(embed=success_embed("🏯 Sáng lập", f"**{r['sect'].name}** (`{r['sect'].sect_id}`)"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_sect_apply(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.xintong <sect_id>`"))
        return
    try:
        r = ctx.engine.sect.apply(str(message.author.id), args[0])
        await message.reply(embed=success_embed("✅ Đã gửi đơn", f"Tới **{r['sect'].name}** · #{r['application_id']}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_sect_contribute(ctx, message: discord.Message, args: list[str]) -> None:
    if not args or not args[0].isdigit():
        await message.reply(embed=error_embed("Dùng: `.congtong <số>`"))
        return
    try:
        r = ctx.engine.sect.contribute(str(message.author.id), int(args[0]))
        await message.reply(embed=success_embed("✅ Cống hiến", f"+{fmt_amount(r['amount'])} · Tổng {fmt_amount(r['contribution'])}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_sect_leave(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        ctx.engine.sect.leave(str(message.author.id))
        await message.reply(embed=success_embed("✅", "Đã rời tông môn."))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))
