from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed, combat_embed
from ui.views.combat_view import CombatView
from ui.views.exploration_view import ExplorationChoiceView
from ui.views.exploration_view import ExplorationMenuView
from game.content.items import ITEMS

async def cmd_explore(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        user_id = str(message.author.id)
        view = ExplorationMenuView(ctx.engine, user_id)
        await message.reply(embed=view.build_embed(), view=view)
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))


async def cmd_zone(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        zones = ctx.engine.exploration.list_zones()
        lines = [f"{'🟢' if z['enabled'] else '🔒'} **{z['name']}** · `{z['key']}`\n{z['description']}\n*Yêu cầu: cảnh giới {z['min_realm']}*" for z in zones]
        e = base_embed("🗺️ Khu vực", "\n\n".join(lines))
        e.set_footer(text="Dùng .khu <mã> để chọn khu")
        await message.reply(embed=e)
        return
    try:
        r = ctx.engine.exploration.set_zone(str(message.author.id), args[0])
        await message.reply(embed=success_embed("Đã chọn khu", r["zone"]["name"]))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_hunt(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        user_id = str(message.author.id)
        r = ctx.engine.exploration.hunt(user_id)
        await message.reply(embed=combat_embed(r["encounter"], ctx.engine.players.get(user_id)), view=CombatView(ctx.engine, user_id))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))
