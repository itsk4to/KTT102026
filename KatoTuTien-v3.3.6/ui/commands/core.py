from __future__ import annotations

import discord
from ui.emoji import EMOJI
from ui.embeds import base_embed, player_embed, error_embed
from ui.views.gui_navigation import MainMenuView, build_main_embed
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

async def cmd_menu(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    await message.reply(
        embed=build_main_embed(ctx.engine, str(message.author.id)),
        view=MainMenuView(ctx.engine, str(message.author.id)),
    )


async def cmd_help(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    quick_names = {
        "info", "bxh", "tu", "dotpha", "thienkiep", "daily",
        "mua", "dung", "hoc", "trangbi", "thao", "chuyen", "code", "gacha",
    }
    gui_names = {
        "menu", "tui", "shop", "khampha", "nhiemvu", "npc", "thegioi", "dao", "tongmon",
    }
    admin_names = {"admin"}
    by_cat: dict[str, list] = {}
    for s in ctx.command_specs:
        by_cat.setdefault(s.category, []).append(s)

    def render(specs: list) -> list[str]:
        lines = []
        for s in specs:
            aliases = ", ".join(f"`.{a}`" for a in s.aliases if a != s.name)
            alias_text = f" · tắt: {aliases}" if aliases else ""
            lines.append(f"`{s.usage}` — {s.description}{alias_text}")
        return lines

    lines = [
        "**Kato Tu Tiên**",
        "Chỉ cần nhớ: **lệnh = thao tác nhanh**, **GUI = chọn và thao tác bằng nút/menu**.",
        "",
        "**⚡ LỆNH NHANH**",
    ]
    quick_specs = [s for s in ctx.command_specs if s.name in quick_names]
    lines.extend(render(quick_specs))
    lines.extend(["", "**🖱️ GIAO DIỆN**"])
    gui_specs = [s for s in ctx.command_specs if s.name in gui_names]
    lines.extend(render(gui_specs))
    lines.extend(["", "**👑 QUẢN TRỊ**"])
    lines.extend(render([s for s in ctx.command_specs if s.name in admin_names]))
    lines.extend(["", "**Mẹo:** `.menu` mở Trung Tâm để đi tới toàn bộ hệ thống GUI."])
    await message.reply(embed=base_embed("📖 Sổ Tay", "\n".join(lines)))


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
