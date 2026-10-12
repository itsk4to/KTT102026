from __future__ import annotations

import discord

from ui.theme.views import ThemedView
from game.services.errors import GameError
from game.utils import fmt_amount
from ui.emoji import EMOJI
from ui.embeds import (
    base_embed,
    error_embed,
    success_embed,
    cultivation_embed,
    cultivation_preview_embed,
    player_embed,
    progress_bar,
)


class PlayerActionSelect(discord.ui.Select):
    """Compact action directory; quick-action buttons stay below it."""

    def __init__(self, owner: "PlayerMenuView"):
        self.owner = owner
        options = [
            discord.SelectOption(
                label="Tu luyện", value="cultivate", emoji=EMOJI["cultivate"],
                description="Tĩnh tọa hấp thu linh khí, tích lũy tu vi.",
            ),
            discord.SelectOption(
                label="Đột phá", value="breakthrough", emoji=EMOJI["breakthrough"],
                description="Kiểm tra căn cơ và thử đột phá cảnh giới.",
            ),
            discord.SelectOption(
                label="Thiên kiếp", value="tribulation", emoji=EMOJI["heavenly_tribulation"],
                description="Ứng thiên kiếp khi đã đủ điều kiện.",
            ),
            discord.SelectOption(
                label="Điểm danh", value="daily", emoji=EMOJI.get("reward", "🎁"),
                description="Nhận phần thưởng hằng ngày.",
            ),
            discord.SelectOption(
                label="Túi Càn Khôn", value="inventory", emoji=EMOJI["item"],
                description="Kiểm tra và dùng vật phẩm trong túi.",
            ),
            discord.SelectOption(
                label="Đạo Lộ", value="dao", emoji=EMOJI.get("dao", "☯️"),
                description="Xem hoặc khai mở Đạo Lộ.",
            ),
        ]
        super().__init__(placeholder="Chọn thao tác đạo hữu…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        action = self.values[0]
        if action in {"cultivate", "breakthrough", "tribulation", "daily"}:
            await self.owner._perform_action(interaction, action)
        else:
            await self.owner._system_callback(action)(interaction)


class PlayerMenuView(ThemedView):
    """Player dashboard with high-frequency quick actions."""

    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self._build()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    async def _refresh_callback(self, interaction: discord.Interaction) -> None:
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=build_player_dashboard(self.engine, self.user_id),
            view=PlayerMenuView(self.engine, self.user_id),
        )

    def _build(self) -> None:
        """Mobile-first Đạo hữu panel.

        Row 0 — action select
        Row 1 — primary cultivation actions
        Row 2 — bag / dao
        Row 3 — navigation bar (thumb zone)
        """
        self.clear_items()
        self.add_item(PlayerActionSelect(self))

        # Row 1: core cultivation — one-tap
        actions = [
            ("Tu luyện", "cultivate", discord.ButtonStyle.primary, EMOJI["cultivate"]),
            ("Đột phá", "breakthrough", discord.ButtonStyle.success, EMOJI["breakthrough"]),
            ("Thiên kiếp", "tribulation", discord.ButtonStyle.secondary, EMOJI["heavenly_tribulation"]),
            ("Điểm danh", "daily", discord.ButtonStyle.secondary, EMOJI.get("reward", "🎁")),
        ]
        for label, action, style, emoji in actions:
            button = discord.ui.Button(label=label, style=style, emoji=emoji, row=1)
            button.callback = self._action_callback(action)
            self.add_item(button)

        # Row 2: inventory & path
        for label, action, emoji in (
            ("Túi Càn Khôn", "inventory", EMOJI["item"]),
            ("Đạo Lộ", "dao", EMOJI.get("dao", "☯️")),
        ):
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, emoji=emoji, row=2)
            button.callback = self._system_callback(action)
            self.add_item(button)

        # Row 3: always-on navigation
        main_btn = discord.ui.Button(
            label="Trung tâm",
            style=discord.ButtonStyle.secondary,
            emoji=EMOJI.get("home", "🏠"),
            row=3,
        )
        main_btn.callback = self._system_callback("main")
        self.add_item(main_btn)

        refresh_btn = discord.ui.Button(
            label="Làm mới",
            style=discord.ButtonStyle.secondary,
            emoji=EMOJI.get("refresh", "🔄"),
            row=3,
        )
        refresh_btn.callback = self._refresh_callback
        self.add_item(refresh_btn)

        close_btn = discord.ui.Button(
            label="Khép lại",
            style=discord.ButtonStyle.danger,
            emoji=EMOJI["close"],
            row=3,
        )
        close_btn.callback = self._system_callback("close")
        self.add_item(close_btn)

    def _action_callback(self, action: str):
        async def callback(interaction: discord.Interaction):
            if not self._guard(interaction):
                await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
                return
            await self._perform_action(interaction, action)

        return callback

    def _system_callback(self, action: str):
        async def callback(interaction: discord.Interaction):
            if not self._guard(interaction):
                await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
                return

            if action == "inventory":
                from ui.views.inventory_view import InventoryView
                from ui.embeds import inventory_embed

                try:
                    items = self.engine.economy.inventory(self.user_id)
                    view = InventoryView(self.engine, self.user_id, items)
                    await interaction.response.edit_message(embed=inventory_embed(items), view=view)
                except GameError as exc:
                    await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
                return

            if action == "dao":
                from ui.views.dao_view import DaoMenuView

                view = DaoMenuView(self.engine, self.user_id)
                await interaction.response.edit_message(embed=view.build_embed(), view=view)
                return

            if action == "main":
                from ui.views.main_menu_view import MainMenuView, build_main_embed

                await interaction.response.edit_message(
                    embed=build_main_embed(self.engine, self.user_id),
                    view=MainMenuView(self.engine, self.user_id),
                )
                return

            self.stop()
            await interaction.response.edit_message(view=None)

        return callback

    async def _perform_action(self, interaction: discord.Interaction, action: str) -> None:
        try:
            if action == "cultivate":
                result = self.engine.cultivation.cultivate(self.user_id)
                await interaction.response.edit_message(
                    embed=cultivation_embed(result),
                    view=PlayerResultView(self.engine, self.user_id, "Tu luyện hoàn tất."),
                )
                return

            if action == "breakthrough":
                preview = self.engine.cultivation.breakthrough_preview(self.user_id)
                if not preview["ready"]:
                    await interaction.response.edit_message(
                        embed=cultivation_preview_embed(preview),
                        view=PlayerResultView(self.engine, self.user_id, "Căn cơ chưa đủ, khó lòng đột phá."),
                    )
                    return
                result = self.engine.cultivation.breakthrough(self.user_id)
                if result["success"]:
                    embed = success_embed(
                        f"{EMOJI['breakthrough']} Đột phá thành công",
                        f"**{result['realm']}** · tỷ lệ {result['chance']:.0%}",
                    )
                    notice = "Đột phá thành công! Cảnh giới đã thăng."
                else:
                    embed = error_embed(
                        f"Đột phá thất bại (tỷ lệ {result['chance']:.0%}). Tu vi bị tổn thất.\n"
                        f"{EMOJI.get('recover', '🩹')} Hồi phục {result.get('recovery_seconds', 0)}s trước khi tiếp tục tu luyện."
                    )
                    notice = "Đột phá thất bại, thân thể tổn thương, cần thời gian hồi phục."
                await interaction.response.edit_message(
                    embed=embed,
                    view=PlayerResultView(self.engine, self.user_id, notice),
                )
                return

            if action == "tribulation":
                result = self.engine.cultivation.face_tribulation(self.user_id)
                if result["success"]:
                    embed = success_embed(f"{EMOJI['heavenly_tribulation']} Thiên kiếp đã qua!", f"Cảnh giới: **{result['realm']}**")
                    notice = "Thiên kiếp đã qua, đạo hữu thành công độ kiếp!"
                else:
                    embed = error_embed(f"Thiên kiếp chưa thể vượt qua. {result['realm']}")
                    notice = "Thiên kiếp chưa thể vượt qua."
                await interaction.response.edit_message(
                    embed=embed,
                    view=PlayerResultView(self.engine, self.user_id, notice),
                )
                return

            if action == "daily":
                result = self.engine.cultivation.claim_daily(self.user_id)
                embed = success_embed(
                    "🎁 Daily",
                    f"+**{fmt_amount(result['stones'])}** {EMOJI['spirit_stone']} · Chuỗi **{result['streak']}** ngày",
                )
                await interaction.response.edit_message(
                    embed=embed,
                    view=PlayerResultView(self.engine, self.user_id, "Đã nhận phần thưởng hôm nay."),
                )
                return

            raise GameError("Thao tác không tồn tại.")
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class PlayerResultView(ThemedView):
    def __init__(self, engine, user_id: str, notice: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.notice = notice

        back = discord.ui.Button(label="Đạo hữu", style=discord.ButtonStyle.primary, emoji=EMOJI["cultivator"], row=0)
        back.callback = self._player_callback
        self.add_item(back)

        main = discord.ui.Button(label="Trung tâm", style=discord.ButtonStyle.secondary, emoji=EMOJI.get("home", "🏠"), row=0)
        main.callback = self._main_callback
        self.add_item(main)

        close = discord.ui.Button(label="Khép lại", style=discord.ButtonStyle.danger, emoji=EMOJI["close"], row=0)
        close.callback = self._close_callback
        self.add_item(close)

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    async def _player_callback(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=build_player_dashboard(self.engine, self.user_id, self.notice),
            view=PlayerMenuView(self.engine, self.user_id),
        )

    async def _main_callback(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed

        await interaction.response.edit_message(
            embed=build_main_embed(self.engine, self.user_id),
            view=MainMenuView(self.engine, self.user_id),
        )

    async def _close_callback(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(view=None)


def build_player_dashboard(engine, user_id: str, notice: str | None = None) -> discord.Embed:
    info = engine.players.info_text(user_id)
    player = info["player"]
    combat_stats = engine.combat.battle_stats(player)
    embed = player_embed(info, combat_stats=combat_stats, show_currency=False)

    try:
        preview = engine.cultivation.breakthrough_preview(user_id)
    except Exception:
        preview = None

    status = [
        "Chạm nút bên dưới hoặc mở menu để tu luyện.",
        "",
        f"{EMOJI['hp']} **{min(max(0, int(player.hp)), int(combat_stats.get('max_hp', player.max_hp)))}/{int(combat_stats.get('max_hp', player.max_hp))} HP thực chiến**",
    ]
    if player.dao_type:
        status.append(f"Đạo: **{player.dao_type}**")
    if preview:
        current = int(preview.get("cultivation", player.cultivation))
        requirement = max(1, int(preview.get("requirement", max(current, 1))))
        progress = max(0.0, min(1.0, current / requirement))
        status.append(
            f"{EMOJI['cultivate']} **Tiến độ tu vi** `{progress_bar(current, requirement, 12)}` **{progress:.0%}**\n"
            f"{fmt_amount(current)} / {fmt_amount(requirement)} · Tỷ lệ đột phá hiện tại **{preview['chance']:.0%}**"
        )

    if notice:
        status.insert(0, f"{EMOJI.get('ok', '✅')} {notice}")

    embed.description = "\n".join(status)
    embed.set_footer(text="HỒ SƠ ĐẠO HỮU · .tu Tu luyện · .dp Đột phá · .tk Thiên kiếp · .dl Đạo Lữ")
    return embed
