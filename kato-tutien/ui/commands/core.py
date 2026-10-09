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
    # Compatibility alias: .menu now opens the same combined Help + main hub.
    await cmd_help(ctx, message, args)


async def cmd_help(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    quick_names = {
        "info", "bxh", "tu", "dotpha", "thienkiep", "daily", "chuyen", "code",
    }
    gui_names = {
        "tui", "shop", "khampha", "nhiemvu", "npc", "thegioi", "dao", "tongmon", "daolu",
    }
    advanced_names = {
        "mua", "dung", "hoc", "trangbi", "thao", "cho", "dangban", "muacho", "huyban", "pvp",
        "khu", "san", "taotong", "xintong", "congtong", "roitong", "gacha", "tutien", "songtu",
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
        "**Chào mừng đến với Kato Tu Tiên!**",
        "Người mới chỉ cần đi theo các bước dưới đây. Có thể bấm nút ở giao diện bên dưới để mở hệ thống, không cần nhớ hết lệnh.",
        "",
        "**🌱 BẮT ĐẦU TRONG 1 PHÚT**",
        "**1.** `.tutien` — tạo nhân vật, chọn **Tu Tiên** hoặc **Tu Ma**.",
        "**2.** `.info` — xem cảnh giới, linh thạch và thông tin nhân vật.",
        "**3.** `.tu` — tu luyện để tích lũy tu vi.",
        "**4.** `.khampha` — khám phá khu vực, gặp cơ duyên và thử thách.",
        "**5.** `.nhiemvu` — xem nhiệm vụ; `.shop` và `.tui` để mua/quản lý vật phẩm.",
        "**6.** Khi đủ điều kiện, dùng `.dotpha`; `.daily` để nhận thưởng hằng ngày.",
        "",
        "**🧭 CHỌN HỆ THỐNG BẰNG NÚT**",
        "Dùng menu bên dưới để mở Nhân vật, Túi, Tiên Phường, Khám phá, Nhiệm vụ, Tông môn và các hệ thống khác.",
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
        "**⚔️ PvP cược:** `.pvp @người_chơi linhthach <số> [50|45|55]` hoặc `.pvp @người_chơi vatpham <mã> <số> [50|45|55]`. Vật cược chỉ bị trừ khi đối thủ nhận lời; người thắng nhận toàn bộ cược.\n",
        "**💞 Đạo lữ:** `.ketduyen @người_chơi` gửi cầu duyên; `.daolu` xem quan hệ/lời mời; `.songtu` tăng duyên phận theo thời gian hồi phục.",
        "**💡 Mẹo:** `.help` là nơi hướng dẫn và mở menu tổng. `.menu` vẫn hoạt động như lệnh cũ.",
    ]
    await message.reply(
        embed=base_embed("📖 Hướng Dẫn & Menu Kato Tu Tiên", "\n".join(lines)),
        view=MainMenuView(ctx.engine, str(message.author.id)),
    )


async def cmd_info(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        info = ctx.engine.players.info_text(str(message.author.id))
        await message.reply(embed=player_embed(info))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_leaderboard(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    path = args[0].lower() if args and args[0].lower() in ("tien", "ma") else None

    def format_rows(rows) -> str:
        return "\n".join(
            f"**{i}.** {p.display_name} — {realm_text(p.realm_index, p.realm_layer)}"
            for i, p in enumerate(rows, 1)
        ) or "Chưa có người chơi trong bảng này."

    if path in ("tien", "ma"):
        title = "🏆 BXH Tu Tiên" if path == "tien" else "🏆 BXH Tu Ma"
        rows = ctx.engine.players.leaderboard(10, path)
        await message.reply(embed=base_embed(title, format_rows(rows)))
        return

    tien = ctx.engine.players.leaderboard(10, "tien")
    ma = ctx.engine.players.leaderboard(10, "ma")
    embed = base_embed("🏆 Bảng Xếp Hạng Hai Phe", "Dùng `.bxh tien` hoặc `.bxh ma` để xem riêng từng phe.")
    embed.add_field(name="🧘 Tu Tiên", value=format_rows(tien), inline=True)
    embed.add_field(name="👹 Tu Ma", value=format_rows(ma), inline=True)
    await message.reply(embed=embed)
