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
            await message.reply(embed=player_embed(ctx.engine.players.info_text(p.user_id), combat_stats=ctx.engine.combat.battle_stats(p)))
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
    # Help is intentionally grouped by player journey, with concise examples first.
    categories = [
        ("🌱 BẮT ĐẦU", {"tutien", "info", "help", "menu"}),
        ("🧘 TU LUYỆN & ĐỘT PHÁ", {"tu", "dotpha", "thienkiep", "daily", "bxh"}),
        ("🗺️ KHÁM PHÁ & NHIỆM VỤ", {"khampha", "khu", "san", "bicanh", "npc", "nhiemvu", "thegioi"}),
        ("🎒 VẬT PHẨM & GIAO DỊCH", {"shop", "mua", "tui", "dung", "hoc", "trangbi", "thao", "cho", "dangban", "muacho", "huyban", "chuyen", "code", "gacha"}),
        ("⚔️ CHIẾN ĐẤU", {"pvp"}),
        ("🏯 TÔNG MÔN", {"tongmon", "taotong", "xintong", "congtong", "roitong"}),
        ("☯️ ĐẠO & ĐẠO LỮ", {"dao", "daolu", "ketduyen", "songtu"}),
        ("🛠️ QUẢN TRỊ", {"admin"}),
    ]

    specs_by_name = {spec.name: spec for spec in ctx.command_specs}

    def render(names: set[str]) -> list[str]:
        lines = []
        for spec in ctx.command_specs:
            if spec.name not in names:
                continue
            aliases = [f".{a}" for a in spec.aliases if a != spec.name]
            alias_text = f" · Bí danh: `{', '.join(aliases)}`" if aliases else ""
            lines.append(f"**`{spec.usage}`**\n{spec.description}{alias_text}")
        return lines

    lines = [
        "**Chào mừng đến với Kato Tu Tiên!**",
        "Dùng các lệnh bên dưới hoặc nhấn nút ở menu. Lệnh có dấu `<...>` cần thay bằng giá trị thật.",
        "",
        "**🚀 LỘ TRÌNH NHANH CHO NGƯỜI MỚI**",
        "① `.tutien` → chọn Tiên hoặc Ma.",
        "② `.info` → xem nhân vật và cảnh giới.",
        "③ `.tu` → tích lũy tu vi; đủ tu vi thì dùng `.dotpha`.",
        "④ `.khampha` → kiếm tài nguyên; `.bicanh` → nhận linh thạch và tu vi theo chu kỳ 3 giờ; `.nhiemvu` → theo dõi mục tiêu.",
        "⑤ `.shop` → mua đồ; `.tui` → xem túi; `.trangbi <mã>` → mặc trang bị.",
        "⑥ `.help` → quay lại hướng dẫn này bất cứ lúc nào.",
        "",
    ]
    for title, names in categories:
        rendered = render(names)
        if rendered:
            lines.extend([f"**{title}**", *rendered, ""])

    lines.extend([
        "**💞 ĐẠO LỮ & SONG TU**",
        "`.ketduyen @người_chơi` gửi lời cầu duyên; người nhận phải đồng ý. `.daolu` mở giao diện quan hệ; `.songtu` để cả hai cùng nhận thêm tu vi và tăng duyên phận. Mỗi cặp có thời gian hồi phục 60 phút.",
        "",
        "**🧰 MẸO DÙNG LỆNH**",
        "• `.thao` tháo tất cả trang bị; `.thao <ô_trang_bị>` tháo riêng một ô.",
        "• `.bxh tien` và `.bxh ma` xem bảng xếp hạng từng phe.",
        "• `.menu` vẫn hoạt động như lệnh mở menu tổng.",
    ])
    await message.reply(
        embed=base_embed("📖 Cẩm Nang Tu Tiên · Help", "\\n".join(lines)),
        view=MainMenuView(ctx.engine, str(message.author.id)),
    )


async def cmd_info(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        info = ctx.engine.players.info_text(str(message.author.id))
        await message.reply(embed=player_embed(info, combat_stats=ctx.engine.combat.battle_stats(info["player"])))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_leaderboard(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    path = args[0].lower() if args and args[0].lower() in ("tien", "ma") else None

    def format_rows(rows) -> str:
        return "\n".join(
            f"**{i}.** {p.display_name} — {realm_text(p.realm_index, p.realm_layer, p.path)}"
            for i, p in enumerate(rows, 1)
        ) or "Chưa có người chơi trong bảng này."

    if path in ("tien", "ma"):
        title = f"🏆 {EMOJI['faction_tien']} BXH Tu Tiên" if path == "tien" else f"🏆 {EMOJI['faction_ma']} BXH Tu Ma"
        rows = ctx.engine.players.leaderboard(10, path)
        await message.reply(embed=base_embed(title, format_rows(rows)))
        return

    tien = ctx.engine.players.leaderboard(10, "tien")
    ma = ctx.engine.players.leaderboard(10, "ma")
    embed = base_embed("🏆 Bảng Xếp Hạng Hai Phe", "Dùng `.bxh tien` hoặc `.bxh ma` để xem riêng từng phe.")
    embed.add_field(name=f"{EMOJI['faction_tien']} Tu Tiên", value=format_rows(tien), inline=True)
    embed.add_field(name=f"{EMOJI['faction_ma']} Tu Ma", value=format_rows(ma), inline=True)
    await message.reply(embed=embed)
