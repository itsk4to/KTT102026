from __future__ import annotations

import discord
from ui.emoji import EMOJI
from ui.embeds import base_embed, player_embed, error_embed
from ui.views.main_menu_view import MainMenuView, build_main_embed
from game.rules.cultivation_rules import realm_text
from game.services.errors import GameError

async def cmd_create(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    # Legacy args remain supported for compatibility; normal players use buttons.
    if args and args[0].lower() in ("tien", "ma"):
        try:
            p = ctx.engine.players.create(str(message.author.id), message.author.display_name, args[0].lower())
            await message.reply(embed=player_embed(ctx.engine.players.info_text(p.user_id)))
        except GameError as e:
            await message.reply(embed=error_embed(str(e)))
        return
    from ui.views.start_path_view import PathChoiceView
    await message.reply(
        embed=base_embed("Khai Đạo", "Ngươi đứng trước ngã rẽ đầu tiên. Chọn con đường muốn bước lên."),
        view=PathChoiceView(ctx.engine, str(message.author.id), message.author.display_name),
    )

async def cmd_menu(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    await message.reply(
        embed=build_main_embed(ctx.engine, str(message.author.id)),
        view=MainMenuView(ctx.engine, str(message.author.id)),
    )


async def cmd_help(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    quick_names = {
        "info", "bxh", "tu", "dotpha", "thienkiep", "daily", "chuyen", "code",
    }
    gui_names = {
        "menu", "tui", "shop", "khampha", "nhiemvu", "npc", "thegioi", "dao", "tongmon", "daolu",
    }
    advanced_names = {
        "mua", "dung", "hoc", "trangbi", "thao", "cho", "dangban", "muacho", "huyban",
        "khu", "san", "taotong", "xintong", "congtong", "roitong", "gacha", "tutien",
    }

    def render(names: set[str]) -> list[str]:
        specs = [s for s in ctx.command_specs if s.name in names]
        lines = []
        for s in specs:
            aliases = ", ".join(f"`.{a}`" for a in s.aliases if a != s.name)
            alias_text = f" · {aliases}" if aliases else ""
            lines.append(f"`{s.usage}` — {s.description}{alias_text}")
        return lines

    lines = [
        "**Kato Tu Tiên**",
        "⚡ Lệnh dùng nhanh · 🖱️ GUI dùng để chọn và thao tác bằng nút.",
        "",
        "**⚡ LỆNH NHANH**",
        *render(quick_names),
        "",
        "**🖱️ GIAO DIỆN**",
        *render(gui_names),
        "",
        "**🧰 THAO TÁC NÂNG CAO**",
        *render(advanced_names),
        "",
        "**💞 Đạo lữ:** `.ketduyen @người_chơi` để gửi lời cầu duyên; người kia sẽ nhận GUI Đồng ý/Từ chối.",
        "**🧭 Trung tâm:** `.menu` mở toàn bộ hệ thống GUI.",
    ]
    await message.reply(embed=base_embed("📖 Sổ Tay Kato Tu Tiên", "\n".join(lines)))


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
