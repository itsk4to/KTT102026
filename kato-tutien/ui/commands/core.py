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
    """Open the actual navigation dashboard (not the Help command list)."""
    user_id = str(message.author.id)
    await message.reply(
        embed=build_main_embed(ctx.engine, user_id),
        view=MainMenuView(ctx.engine, user_id),
    )


async def cmd_help(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    """Show a paginated help guide, keeping every embed under Discord limits."""
    from ui.views.help_view import HelpView

    category_pages = [
        ("📖 Cẩm Nang · 1/3", "LÀM QUEN & TU LUYỆN", {"start", "cultivation", "explore", "world"}),
        ("📖 Cẩm Nang · 2/3", "VẬT PHẨM, GIAO DỊCH & CHIẾN ĐẤU", {"trade", "combat"}),
        ("📖 Cẩm Nang · 3/3", "TÔNG MÔN, ĐẠO & HỆ THỐNG", {"sect", "dao", "social", "system"}),
    ]
    pages = []
    rendered_names: set[str] = set()

    for page_index, (title, heading, categories) in enumerate(category_pages):
        lines: list[str] = []
        if page_index == 0:
            lines.extend([
                "**Chào mừng đến với Kato Tu Tiên!**",
                "Dùng lệnh nhanh hoặc chọn hệ thống từ `.menu` để mở giao diện.",
                "",
                "**🚀 LỘ TRÌNH NGƯỜI MỚI**",
                "1. `.tutien` → chọn Tiên hoặc Ma.",
                "2. `.info` → xem nhân vật; `.tu` → tích lũy tu vi.",
                "3. `.dotpha` → đột phá khi đủ điều kiện; `.daily` → điểm danh.",
                "4. `.khampha` / `.bicanh` → khám phá hoặc tu luyện bí cảnh 3 giờ.",
                "5. `.shop` / `.tui` → mua sắm và quản lý vật phẩm.",
                "",
            ])
        lines.append(f"**{heading}**")
        for spec in ctx.command_specs:
            if spec.category not in categories or spec.name in rendered_names:
                continue
            rendered_names.add(spec.name)
            aliases = [f".{alias}" for alias in spec.aliases if alias != spec.name]
            alias_text = f" · *Bí danh:* {', '.join(aliases)}" if aliases else ""
            lines.append(f"**`{spec.usage}`** — {spec.description}{alias_text}")

        if page_index == 2:
            lines.extend([
                "",
                "**💞 ĐẠO LỮ & SONG TU**",
                "`.ketduyen @người_chơi` gửi lời cầu duyên; người nhận phải đồng ý. `.daolu` mở giao diện quan hệ; `.songtu` giúp cả hai nhận tu vi. Hồi chiêu theo cặp: 60 phút.",
                "",
                "**🧰 MẸO NHANH**",
                "• `.thao` tháo toàn bộ trang bị; `.thao <ô>` tháo riêng một ô.",
                "• `.bxh tien` / `.bxh ma` xem bảng xếp hạng từng phe.",
                "• `.vatpham <tên|ID>` tra ID vật phẩm, chấp nhận tên không dấu.",
                "• `.menu` mở Trung Tâm; `.help` mở cẩm nang này.",
            ])
        pages.append(base_embed(title, "\n".join(lines)))

    # If future commands add a category, surface them instead of silently hiding them.
    missing = [spec for spec in ctx.command_specs if spec.name not in rendered_names]
    if missing:
        lines = ["**LỆNH KHÁC**"]
        for spec in missing:
            aliases = [f".{alias}" for alias in spec.aliases if alias != spec.name]
            suffix = f" · *Bí danh:* {', '.join(aliases)}" if aliases else ""
            lines.append(f"**`{spec.usage}`** — {spec.description}{suffix}")
        pages.append(base_embed(f"📖 Cẩm Nang · {len(pages)+1}/{len(pages)+1}", "\n".join(lines)))

    await message.reply(
        embed=pages[0],
        view=HelpView(pages, ctx.engine, str(message.author.id)),
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
