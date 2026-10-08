from __future__ import annotations

import discord

from game.engine import GameEngine, GameError
from game.rules.cultivation_rules import realm_text
from ui.embeds import base_embed, error_embed, success_embed
from ui.emoji import EMOJI


class AdminLoginModal(discord.ui.Modal, title="🔐 Admin Login"):
    password = discord.ui.TextInput(
        label="Mật khẩu quản trị",
        placeholder="Nhập mật khẩu quản trị",
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=200,
    )

    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine

    async def on_submit(self, interaction: discord.Interaction) -> None:
        actor_id = str(interaction.user.id)
        if self.engine.admin_auth.too_many_failures(actor_id):
            await interaction.response.send_message(
                embed=error_embed("Thử quá nhiều lần. Hãy chờ vài phút."),
                ephemeral=True,
            )
            return
        if not self.engine.admin.authorize_session(actor_id, str(self.password)):
            await interaction.response.send_message(
                embed=error_embed("Mật khẩu quản trị không đúng."),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=base_embed("👑 Kato Admin", "Đăng nhập thành công."),
            view=AdminView(self.engine, actor_id),
            ephemeral=True,
        )


class AdminLoginView(discord.ui.View):
    def __init__(self, engine: GameEngine):
        super().__init__(timeout=180)
        self.engine = engine

    @discord.ui.button(label="Đăng nhập Admin", style=discord.ButtonStyle.primary, emoji="🔐")
    async def login(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        await interaction.response.send_modal(AdminLoginModal(self.engine))


class GrantStonesModal(discord.ui.Modal, title="💎 Cấp Linh Thạch"):
    user_id = discord.ui.TextInput(label="Discord User ID", required=True, max_length=32)
    amount = discord.ui.TextInput(label="Số lượng", required=True, max_length=20)

    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            amount = int(str(self.amount))
            player = self.engine.admin.grant_stones(
                str(interaction.user.id), str(self.user_id).strip(), amount
            )
            await interaction.response.send_message(
                embed=success_embed(
                    "💎 Đã cấp linh thạch",
                    f"<@{player.user_id}> hiện có **{player.spirit_stones}** {EMOJI['spirit_stone']}.",
                ),
                ephemeral=True,
            )
        except (GameError, ValueError) as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class AdminView(discord.ui.View):
    def __init__(self, engine: GameEngine, actor_id: str):
        super().__init__(timeout=300)
        self.engine = engine
        self.actor_id = actor_id

    def _check(self, interaction: discord.Interaction) -> None:
        if str(interaction.user.id) != self.actor_id:
            raise GameError("Đây không phải phiên Admin của ngươi.")

    @discord.ui.button(label="Tổng quan", style=discord.ButtonStyle.secondary, emoji="📊", row=0)
    async def overview(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            data = self.engine.admin.overview(self.actor_id)
            await interaction.response.edit_message(
                embed=base_embed(
                    "👑 KATO ADMIN",
                    f"👤 Người chơi: **{data['players']}**\n"
                    f"🏯 Tông môn: **{data['sects']}**\n"
                    f"🔐 Phiên: **{self.engine.admin_auth.has_session(self.actor_id)}**",
                ),
                view=self,
            )
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Cấp linh thạch", style=discord.ButtonStyle.success, emoji="💎", row=0)
    async def grant(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            self.engine.admin.ensure_access(self.actor_id)
            await interaction.response.send_modal(GrantStonesModal(self.engine))
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Audit", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def audit(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            rows = self.engine.admin.recent_audit(self.actor_id, 10)
            if not rows:
                body = "Chưa có audit log."
            else:
                body = "\n".join(
                    f"• `{r['action']}` · <@{r['actor_id']}> → {r.get('target_id') or '-'}"
                    for r in rows
                )
            await interaction.response.send_message(embed=base_embed("📜 Admin Audit", body), ephemeral=True)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Đóng", style=discord.ButtonStyle.danger, emoji="✖️", row=1)
    async def close(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            self.engine.admin_auth.clear(self.actor_id)
            await interaction.response.edit_message(embed=base_embed("👑 Admin", "Đã đóng phiên."), view=None)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
