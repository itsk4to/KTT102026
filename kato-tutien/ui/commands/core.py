from __future__ import annotations

import discord
from ui.emoji import EMOJI
from ui.embeds import base_embed, player_embed, error_embed
from game.rules.cultivation_rules import realm_text
from game.services.errors import GameError

async def cmd_create(ctx, message: discord.Message, args: list[str]) -> None:
    if not args or args[0].lower() not in ("tien", "ma"):
        await message.reply(embed=base_embed("Khai Đạo", "Dùng: `.tutien tien` hoặc `.tutien ma`"))
        return
    try:
        p = ctx.engine.players.create(str(message.author.id), message.author.display_name, args[0].lower())
        info = ctx.engine.players.info_text(p.user_id)
        await message.reply(embed=player_embed(info))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_help(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    lines = ["**Kato Tu Tiên v3** — lệnh chính:\n"]
    by_cat: dict[str, list] = {}
    for s in ctx.command_specs:
        by_cat.setdefault(s.category, []).append(s)
    for cat, specs in by_cat.items():
        lines.append(f"**{cat}**")
        for s in specs:
            lines.append(f"`{s.usage}` — {s.description}")
        lines.append("")
    await message.reply(embed=base_embed("📖 Sổ tay", "\n".join(lines)))

async def cmd_info(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        info = ctx.engine.players.info_text(str(message.author.id))
        await message.reply(embed=player_embed(info))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_leaderboard(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    path = args[0].lower() if args and args[0].lower() in ("tien", "ma") else None
    rows = ctx.engine.players.leaderboard(10, path)
    lines = [f"**{i}.** {p.display_name} — {realm_text(p.realm_index, p.realm_layer)}" for i, p in enumerate(rows, 1)]
    await message.reply(embed=base_embed("🏆 BXH", "\n".join(lines) or "Trống."))
