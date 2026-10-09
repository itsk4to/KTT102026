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
)


class PlayerMenuView(ThemedView):
    """Player dashboard with high-frequency quick actions."""

    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self._build()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def _build(self) -> None:
        self.clear_items()

        actions = [
            ("Tu luyện", "cultivate", discord.ButtonStyle.primary, EMOJI["cultivation"]),
            ("Đột phá", "breakthrough", discord.ButtonStyle.success, EMOJI["breakthrough"]),
            ("Thiên kiếp", "tribulation", discord.ButtonStyle.secondary, "⚡"),
            ("Daily", "daily", discord.ButtonStyle.secondary, "🎁"),
        ]
        for label, action, style, emoji in actions:
            button = discord.ui.Button(label=label, style=style, emoji=emoji, row=0)
            button.callback = self._action_callback(action)
            self.add_item(button)

        systems = [
            ("🎒 Túi", "inventory"),
            ("☯️ Đạo", "dao"),
            ("🧭 Trung tâm", "main"),
            ("✖️ Đóng", "close"),
        ]
        for label, action in systems:
            style = discord.ButtonStyle.danger if action == "close" else discord.ButtonStyle.secondary
            button = discord.ui.Button(label=label, style=style, row=1)
            button.callback = self._system_callback(action)
            self.add_item(button)

    def _action_callback(self, action: str):
        async def callback(interaction: discord.Interaction):
            if not self._guard(interaction):
                await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
                return
            await self._perform_action(interaction, action)

        return callback

    def _system_callback(self, action: str):
        async def callback(interaction: discord.Interaction):
            if not self._guard(interaction):
                await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
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
                    view=PlayerResultView(self.engine, self.user_id, "Tu luyện xong."),
                )
                return

            if action == "breakthrough":
                preview = self.engine.cultivation.breakthrough_preview(self.user_id)
                if not preview["ready"]:
                    await interaction.response.edit_message(
                        embed=cultivation_preview_embed(preview),
                        view=PlayerResultView(self.engine, self.user_id, "Chưa đủ điều kiện đột phá."),
                    )
                    return
                result = self.engine.cultivation.breakthrough(self.user_id)
                if result["success"]:
                    embed = success_embed(
                        f"{EMOJI['breakthrough']} Đột phá thành công",
                        f"**{result['realm']}** · tỷ lệ {result['chance']:.0%}",
                    )
                    notice = "Đột phá thành công."
                else:
                    embed = error_embed(
                        f"Đột phá thất bại (tỷ lệ {result['chance']:.0%}). Tu vi bị tổn thất.\n"
                        f"🩹 Hồi phục {result.get('recovery_seconds', 0)}s trước khi tiếp tục tu luyện."
                    )
                    notice = "Đột phá thất bại — đang hồi phục."
                await interaction.response.edit_message(
                    embed=embed,
                    view=PlayerResultView(self.engine, self.user_id, notice),
                )
                return

            if action == "tribulation":
                result = self.engine.cultivation.face_tribulation(self.user_id)
                if result["success"]:
                    embed = success_embed("⚡ Vượt kiếp thành công!", f"Cảnh giới: **{result['realm']}**")
                    notice = "Vượt kiếp thành công."
                else:
                    embed = error_embed(f"Kiếp nạn thất bại. {result['realm']}")
                    notice = "Kiếp nạn thất bại."
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
                    view=PlayerResultView(self.engine, self.user_id, "Đã nhận thưởng hằng ngày."),
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

        back = discord.ui.Button(label="Nhân vật", style=discord.ButtonStyle.primary, emoji=EMOJI["cultivator"], row=0)
        back.callback = self._player_callback
        self.add_item(back)

        main = discord.ui.Button(label="Trung tâm", style=discord.ButtonStyle.secondary, emoji="🧭", row=0)
        main.callback = self._main_callback
        self.add_item(main)

        close = discord.ui.Button(label="Đóng", style=discord.ButtonStyle.danger, emoji=EMOJI["close"], row=0)
        close.callback = self._close_callback
        self.add_item(close)

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    async def _player_callback(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=build_player_dashboard(self.engine, self.user_id, self.notice),
            view=PlayerMenuView(self.engine, self.user_id),
        )

    async def _main_callback(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed

        await interaction.response.edit_message(
            embed=build_main_embed(self.engine, self.user_id),
            view=MainMenuView(self.engine, self.user_id),
        )

    async def _close_callback(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(view=None)


def build_player_dashboard(engine, user_id: str, notice: str | None = None) -> discord.Embed:
    info = engine.players.info_text(user_id)
    player = info["player"]
    combat_stats = engine.combat.battle_stats(player)
    embed = player_embed(info, combat_stats=combat_stats)

    try:
        preview = engine.cultivation.breakthrough_preview(user_id)
    except Exception:
        preview = None

    status = [
        "Chọn **Tu luyện / Đột phá / Thiên kiếp / Daily** để thao tác ngay.",
        "",
        f"{EMOJI['spirit_stone']} **{fmt_amount(player.spirit_stones)}** linh thạch",
        f"{EMOJI['hp']} **{min(max(0, int(player.hp)), int(combat_stats.get('max_hp', player.max_hp)))}/{int(combat_stats.get('max_hp', player.max_hp))} HP thực chiến**",
    ]
    if player.dao_type:
        status.append(f"Đạo: **{player.dao_type}**")
    if preview:
        status.append(
            f"Tiến độ đột phá: **{fmt_amount(preview['cultivation'])}/{fmt_amount(preview['requirement'])}** · {preview['chance']:.0%}"
        )

    if notice:
        status.insert(0, f"✅ {notice}")

    embed.description = "\n".join(status)
    embed.set_footer(text="Lệnh nhanh vẫn dùng được: .tu · .dp · .tk · .dl")
    return embed
