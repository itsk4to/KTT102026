from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed, combat_embed
from ui.views.combat_view import CombatView

async def cmd_explore(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        zone = args[0] if args else None
        r = ctx.engine.exploration.explore(str(message.author.id), zone)
        if r.get("combat"):
            await message.reply(embed=combat_embed(r["encounter"]), view=CombatView(engine, str(message.author.id)))
            return
        parts = [r.get("text", "")]
        if "stones" in r:
            parts.append(f"+{r['stones']} {EMOJI['spirit_stone']}")
        if "cultivation" in r:
            parts.append(f"+{r['cultivation']} tu vi")
        if "item" in r:
            parts.append(f"Nhận vật phẩm `{r['item']}`")
        if "injury" in r:
            parts.append(f"Thương thế +{r['injury']}")
        await message.reply(embed=base_embed(f"{EMOJI['explore']} {r['zone']['name']}", "\n".join(parts)))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_zone(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        zones = ctx.engine.exploration.list_zones()
        lines = [
            f"`{z['key']}` — **{z['name']}** (realm≥{z['min_realm']}) {'✅' if z['enabled'] else '🔒'}"
            for z in zones
        ]
        await message.reply(embed=base_embed("🗺️ Khu vực", "\n".join(lines)))
        return
    try:
        r = ctx.engine.exploration.set_zone(str(message.author.id), args[0])
        await message.reply(embed=success_embed("Đã chọn khu", r["zone"]["name"]))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_hunt(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        r = ctx.engine.exploration.hunt(str(message.author.id))
        await message.reply(embed=combat_embed(r["encounter"]), view=CombatView(engine, str(message.author.id)))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))
