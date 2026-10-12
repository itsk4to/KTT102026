from __future__ import annotations

import discord
from ui.emoji import EMOJI
from ui.embeds import base_embed, player_embed, public_player_embed, error_embed
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
        (f"{EMOJI.get('technique', '📖')} Cẩm Nang · 1/3", "BƯỚC ĐẦU & TU LUYỆN", {"start", "cultivation", "explore", "world"}),
        (f"{EMOJI.get('item', '📖')} Cẩm Nang · 2/3", "TÚI, GIAO DỊCH & CHIẾN ĐẤU", {"trade", "combat"}),
        (f"{EMOJI.get('sect', '📖')} Cẩm Nang · 3/3", "TÔNG MÔN, ĐẠO & HỆ THỐNG", {"sect", "dao", "social", "system"}),
    ]
    pages = []
    rendered_names: set[str] = set()

    for page_index, (title, heading, categories) in enumerate(category_pages):
        lines: list[str] = []
        if page_index == 0:
            lines.extend([
                f"**Chào mừng đạo hữu đến Kato Tu Tiên!**",
                "Có thể gõ lệnh nhanh **hoặc** mở `.menu` rồi chạm nút trên giao diện.",
                "",
                f"**{EMOJI.get('cultivate', '🌱')} LỘ TRÌNH NGƯỜI MỚI (5 BƯỚC)**",
                f"1. `{EMOJI.get('cultivator', '🧘')}` **`.tutien`** — chọn **Tiên Đạo** hoặc **Ma Đạo**.",
                f"2. **`.menu`** — mở **Trung tâm** (HUD + mọi hệ thống).",
                f"3. **`.tu`** — tu luyện tích lũy tu vi · **`.daily`** điểm danh.",
                f"4. **`.dotpha`** khi đủ tu vi · **`.tk`** nếu cần thiên kiếp.",
                f"5. **`.khampha`** xuất hành · **`.bicanh`** bí cảnh 3 giờ · **`.shop`** / **`.tui`**.",
                "",
                "*Gợi ý:* trên điện thoại hãy dùng **nút** trong `.menu` thay vì nhớ hết lệnh.",
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
                f"**{EMOJI.get('cultivator', '💞')} ĐẠO LỮ & SONG TU**",
                "`.ketduyen @đạo_hữu` gửi cầu duyên (đối phương phải đồng ý). "
                "`.daolu` mở giao diện · `.songtu` cả hai nhận tu vi (hồi 60 phút/cặp).",
                "",
                f"**{EMOJI.get('ok', '✅')} MẸO NHANH**",
                "• `.menu` = Trung tâm game (nên dùng trước).",
                "• `.help` = cẩm nang này (lật trang bằng nút **Trước / Sau**).",
                "• `.bxh tien` / `.bxh ma` — Thiên Bảng theo phe.",
                "• `.vatpham <tên|ID>` — tra vật phẩm (chấp nhận không dấu).",
                "• `.thao` tháo hết trang bị · `.thao <ô>` tháo một ô.",
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
    """`.info` sends own details by DM; `.info @player` shows a safe public card."""
    try:
        target_id = None
        if args:
            import re
            match = re.fullmatch(r"<@!?(\d+)>", args[0])
            if match:
                target_id = match.group(1)
            elif args[0].isdigit():
                target_id = args[0]
            else:
                await message.reply(embed=error_embed("Hãy dùng `.info` để xem hồ sơ riêng hoặc `.info @player` để xem hồ sơ công khai."))
                return

        if target_id:
            info = ctx.engine.players.info_text(target_id)
            stats = ctx.engine.combat.battle_stats(info["player"])
            await message.reply(embed=public_player_embed(info, combat_stats=stats))
            return

        info = ctx.engine.players.info_text(str(message.author.id))
        embed = player_embed(info, combat_stats=ctx.engine.combat.battle_stats(info["player"]))
        try:
            await message.author.send(embed=embed)
        except discord.Forbidden:
            await message.reply(embed=error_embed("Mình không thể gửi tin nhắn riêng cho bạn. Hãy bật DM từ thành viên máy chủ hoặc dùng lệnh slash `/info` để xem hồ sơ riêng."))
            return
        await message.reply("📩 Mình đã gửi hồ sơ riêng qua DM.", mention_author=False)
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_leaderboard(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    path = args[0].lower() if args and args[0].lower() in ("tien", "ma") else None

    def format_rows(rows) -> str:
        return "\n".join(
            f"**{i}.** {p.display_name} — {realm_text(p.realm_index, p.realm_layer, p.path)}"
            for i, p in enumerate(rows, 1)
        ) or "Chưa có đạo hữu trên Thiên Bảng."

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
