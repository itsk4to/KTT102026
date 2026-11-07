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
            await message.reply(embed=player_embed(ctx.engine.players.info_text(p.user_id), combat_stats=ctx.engine.combat.battle_stats(p), show_currency=False))
        except GameError as e:
            await message.reply(embed=error_embed(str(e)))
        return
    from ui.views.start_path_view import PathChoiceView
    from ui import copy as T
    await message.reply(
        embed=base_embed(T.PATH_TITLE, T.PATH_BODY),
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

    from ui import copy as T

    category_pages = [
        (f"{EMOJI.get('technique', '📖')} {T.HELP_WELCOME_TITLE} · 1/3", "KHAI ĐẠO · TU LUYỆN · XUẤT HÀNH", {"start", "cultivation", "explore", "world"}),
        (f"{EMOJI.get('item', '📖')} {T.HELP_WELCOME_TITLE} · 2/3", "TÚI CÀN KHÔN · GIAO DỊCH · CHIẾN ĐẤU", {"trade", "combat"}),
        (f"{EMOJI.get('sect', '📖')} {T.HELP_WELCOME_TITLE} · 3/3", "TÔNG MÔN · ĐẠO QUẢ · HỆ THỐNG", {"sect", "dao", "social", "system"}),
    ]
    pages = []
    rendered_names: set[str] = set()

    for page_index, (title, heading, categories) in enumerate(category_pages):
        lines: list[str] = []
        if page_index == 0:
            lines.extend([T.HELP_WELCOME, ""])
        lines.append(f"**{heading}**")
        for spec in ctx.command_specs:
            if spec.category not in categories or spec.name in rendered_names:
                continue
            rendered_names.add(spec.name)
            aliases = [f".{alias}" for alias in spec.aliases if alias != spec.name]
            alias_text = f" · *cũng gọi:* {', '.join(aliases)}" if aliases else ""
            lines.append(f"**`{spec.usage}`** — {spec.description}{alias_text}")

        if page_index == 2:
            lines.extend([
                "",
                f"**{EMOJI.get('cultivator', '💞')} ĐẠO LỮ & SONG TU**",
                "`.ketduyen @đạo_hữu` gửi lời cầu duyên (đối phương phải nhận). "
                "`.daolu` xem duyên phận · `.songtu` cùng nhau tăng tu vi (mỗi cặp 60 phút một lần).",
                "",
                f"**{EMOJI.get('ok', '✅')} LỜI KHUYÊN**",
                "• Vào **`.menu`** trước — mọi cửa ải đều ở đó.",
                "• **`.help`** để xem lại cẩm nang (nút Trước / Sau).",
                "• **`.bxh tien`** / **`.bxh ma`** — Thiên Bảng theo đạo lộ.",
                "• **`.vatpham <tên>`** — tra đan dược, pháp bảo (không dấu cũng được).",
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

    prison_session = (
        ctx.engine.prison.get_active_session(str(message.guild.id), str(message.author.id))
        if message.guild is not None else None
    )
    if prison_session:
        await message.reply(embed=pages[0])
        return
    await message.reply(
        embed=pages[0],
        view=HelpView(pages, ctx.engine, str(message.author.id)),
    )


async def cmd_info(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    """`.info` — hồ sơ riêng chỉ người gọi thấy trong kênh; `.info @player` công khai."""
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
                await message.reply(embed=error_embed(
                    "Dùng **`.info`** để xem hồ sơ riêng (chỉ mình thấy), "
                    "hoặc **`.info @đạo_hữu`** để xem hồ sơ công khai."
                ))
                return

        if target_id:
            info = ctx.engine.players.info_text(target_id)
            stats = ctx.engine.combat.battle_stats(info["player"])
            await message.reply(embed=public_player_embed(info, combat_stats=stats))
            return

        info = ctx.engine.players.info_text(str(message.author.id))
        embed = player_embed(
            info,
            combat_stats=ctx.engine.combat.battle_stats(info["player"]),
            show_currency=True,
        )
        # Prefix commands cannot be truly ephemeral. Offer one-tap private reveal
        # so only the command user sees the full hồ sơ in this channel.
        view = _PrivateInfoView(str(message.author.id), embed)
        await message.reply(
            content="Hồ sơ riêng đã sẵn sàng — **chỉ đạo hữu** mở được (chạm nút bên dưới).",
            view=view,
            mention_author=False,
        )
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))


class _PrivateInfoView(discord.ui.View):
    """One-tap reveal: hồ sơ gửi ephemeral trong đúng kênh đang đứng."""

    def __init__(self, owner_id: str, embed: discord.Embed, timeout: float = 120):
        super().__init__(timeout=timeout)
        self.owner_id = owner_id
        self.embed = embed

    @discord.ui.button(label="Xem hồ sơ riêng", style=discord.ButtonStyle.primary, emoji="📜")
    async def reveal(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        if str(interaction.user.id) != self.owner_id:
            await interaction.response.send_message(
                "Hồ sơ này không thuộc về đạo hữu.",
                ephemeral=True,
            )
            return
        await interaction.response.send_message(embed=self.embed, ephemeral=True)

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
