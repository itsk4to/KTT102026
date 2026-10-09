from __future__ import annotations

import discord

from ui.theme.views import ThemedView
from game.content.sects_content import SECT_ROLES
from game.services.errors import GameError
from ui.embeds import base_embed, error_embed, success_embed
from ui.emoji import EMOJI


class SectMemberAdminView(ThemedView):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.selected_id: str | None = None
        self.rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def _members(self):
        ov = self.engine.sect.overview(self.user_id)
        return ov.get("members", []) if ov.get("in_sect") else []

    def rebuild(self):
        self.clear_items()
        members = [m for m in self._members() if m.user_id != self.user_id]
        if members:
            options = []
            for m in members[:25]:
                player = self.engine.players.get(m.user_id)
                name = (player.display_name if player and player.display_name else f"Người chơi {m.user_id[-4:]}").strip()
                options.append(discord.SelectOption(
                    label=f"{name} · {m.role}"[:100],
                    value=str(m.user_id),
                    description=f"Cống hiến {m.contribution:,}",
                    emoji=EMOJI["cultivator"],
                ))
            select = discord.ui.Select(placeholder="Chọn thành viên…", options=options, row=0)
            select.callback = self._select
            self.add_item(select)

        promote = discord.ui.Button(label="Thăng chức", emoji=EMOJI["accept"], style=discord.ButtonStyle.success, row=1, disabled=self.selected_id is None)
        promote.callback = self._promote
        self.add_item(promote)
        demote = discord.ui.Button(label="Giáng chức", emoji=EMOJI["reject"], style=discord.ButtonStyle.secondary, row=1, disabled=self.selected_id is None)
        demote.callback = self._demote
        self.add_item(demote)
        kick = discord.ui.Button(label="Khai trừ", emoji=EMOJI["no"], style=discord.ButtonStyle.danger, row=1, disabled=self.selected_id is None)
        kick.callback = self._kick
        self.add_item(kick)
        transfer = discord.ui.Button(label="Nhường Tông Chủ", emoji=EMOJI["accept"], style=discord.ButtonStyle.primary, row=2, disabled=self.selected_id is None)
        transfer.callback = self._transfer
        self.add_item(transfer)
        dissolve = discord.ui.Button(label="Giải tán tông", emoji=EMOJI["no"], style=discord.ButtonStyle.danger, row=2)
        dissolve.callback = self._dissolve
        self.add_item(dissolve)
        back = discord.ui.Button(label="Quay lại", emoji=EMOJI["back"], style=discord.ButtonStyle.secondary, row=3)
        back.callback = self._back
        self.add_item(back)

    def build_embed(self):
        members = self._members()
        lines = []
        for m in members[:15]:
            player = self.engine.players.get(m.user_id)
            name = (player.display_name if player and player.display_name else f"Người chơi {m.user_id[-4:]}").strip()
            lines.append(f"**{name}** — {m.role} · {m.contribution:,} cống hiến")
        return base_embed("🏯 Quản trị thành viên", "\n".join(lines) or "Tông môn chưa có thành viên khác.")

    async def _select(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.selected_id = interaction.data["values"][0]
        self.rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    def _target_member(self):
        if self.selected_id is None:
            raise GameError("Hãy chọn một thành viên trước.")
        return next((m for m in self._members() if str(m.user_id) == str(self.selected_id)), None)

    async def _promote(self, interaction: discord.Interaction):
        await self._change_role(interaction, promote=True)

    async def _demote(self, interaction: discord.Interaction):
        await self._change_role(interaction, promote=False)

    async def _change_role(self, interaction: discord.Interaction, *, promote: bool):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            member = self._target_member()
            if not member:
                raise GameError("Thành viên không còn tồn tại.")
            idx = SECT_ROLES.index(member.role)
            new_idx = idx - 1 if promote else idx + 1
            if not (0 <= new_idx < len(SECT_ROLES)):
                raise GameError("Thành viên đã ở cấp chức vụ phù hợp nhất.")
            new_role = SECT_ROLES[new_idx]
            self.engine.sect.change_role(self.user_id, self.selected_id, new_role)
            self.selected_id = None
            self.rebuild()
            await interaction.response.edit_message(embed=success_embed("🏯 Chức vụ", f"Đã đổi thành **{new_role}**."), view=self)
        except (GameError, ValueError) as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _kick(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            member = self._target_member()
            self.engine.sect.kick(self.user_id, member.user_id if member else "")
            self.selected_id = None
            self.rebuild()
            await interaction.response.edit_message(embed=success_embed("🏯 Khai trừ", "Đã đưa thành viên ra khỏi tông môn."), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _transfer(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            member = self._target_member()
            if not member:
                raise GameError("Thành viên không còn tồn tại.")
            self.engine.sect.transfer_leadership(self.user_id, member.user_id)
            self.selected_id = None
            self.rebuild()
            await interaction.response.edit_message(embed=success_embed("🏯 Tông Chủ", f"Đã nhường chức cho <@{member.user_id}>."), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _dissolve(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            self.engine.sect.dissolve(self.user_id)
            await interaction.response.edit_message(embed=success_embed("🏯 Giải tán", "Tông môn đã được giải tán."), view=None)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _back(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.sect_view import SectMenuView
        view = SectMenuView(self.engine, self.user_id)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
