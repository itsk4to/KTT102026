from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import error_embed, success_embed, cultivation_embed, cultivation_preview_embed
from game.utils import fmt_amount

async def cmd_cultivate(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        r = ctx.engine.cultivation.cultivate(str(message.author.id))
        await message.reply(embed=cultivation_embed(r))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_breakthrough(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        preview = ctx.engine.cultivation.breakthrough_preview(str(message.author.id))
        if not preview["ready"]:
            await message.reply(embed=cultivation_preview_embed(preview))
            return
        from ui.views.breakthrough_view import BreakthroughView
        await message.reply(embed=cultivation_preview_embed(preview), view=BreakthroughView(ctx.engine, str(message.author.id)))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_tribulation(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        r = ctx.engine.cultivation.face_tribulation(str(message.author.id))
        if r["success"]:
            await message.reply(embed=success_embed("⚡ Vượt kiếp thành công!", f"Cảnh giới: **{r['realm']}**"))
        else:
            await message.reply(embed=error_embed(f"Kiếp nạn thất bại. {r['realm']}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_daily(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        r = ctx.engine.cultivation.claim_daily(str(message.author.id))
        await message.reply(embed=success_embed(
            "🎁 Daily",
            f"+**{fmt_amount(r['stones'])}** {EMOJI['spirit_stone']} · Chuỗi **{r['streak']}** ngày",
        ))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))
