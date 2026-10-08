from __future__ import annotations
import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed


class DaoLuView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.selected = None
        self.rebuild()

    def _guard(self, interaction):
        return str(interaction.user.id) == self.user_id

    def build_embed(self):
        partner = self.engine.dao_lu.partner(self.user_id)
        pending = self.engine.dao_lu.pending(self.user_id)
        lines = ["Chọn một đạo hữu để gửi lời cầu duyên."]
        if partner:
            p = self.engine.players.get(partner["user_id"])
            lines = [f"Đạo lữ: **{p.display_name if p else partner['user_id']}**", f"Duyên phận: **{partner['intimacy']}**"]
        if pending:
            lines.append(f"\nLời cầu duyên đang chờ: **{len(pending)}**")
        return base_embed("💞 Đạo Lữ", "\n".join(lines))

    def rebuild(self):
        self.clear_items()
        candidates = self.engine.dao_lu.candidates(self.user_id)
        if candidates:
            options = [discord.SelectOption(label=f"{x['display_name'][:70]}", value=x["user_id"], emoji=EMOJI["cultivator"]) for x in candidates[:25]]
            select = discord.ui.Select(placeholder="Chọn đạo hữu…", options=options, row=0)
            select.callback = self._select
            self.add_item(select)
        request = discord.ui.Button(label="Cầu duyên", emoji=EMOJI["accept"], style=discord.ButtonStyle.success, row=1)
        request.callback = self._request
        self.add_item(request)
        song = discord.ui.Button(label="Song tu", emoji=EMOJI["cultivation"], style=discord.ButtonStyle.primary, row=1)
        song.callback = self._song
        self.add_item(song)
        if self.engine.dao_lu.pending(self.user_id):
            accept = discord.ui.Button(label="Chấp nhận lời cầu duyên", emoji=EMOJI["ok"], style=discord.ButtonStyle.success, row=2)
            accept.callback = self._accept_pending
            self.add_item(accept)
        back = discord.ui.Button(label="Trung tâm", emoji="🏠", style=discord.ButtonStyle.secondary, row=3)
        back.callback = self._back
        self.add_item(back)

    async def _select(self, interaction):
        if not self._guard(interaction): return await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
        self.selected = interaction.data["values"][0]
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _request(self, interaction):
        if not self._guard(interaction): return await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
        if not self.selected: return await interaction.response.send_message("Hãy chọn một đạo hữu trước.", ephemeral=True)
        try:
            self.engine.dao_lu.request(self.user_id, self.selected)
            await interaction.response.edit_message(embed=success_embed("💞 Đã gửi cầu duyên", "Lời cầu duyên đã được gửi tới đạo hữu."), view=self)
        except GameError as exc: await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _song(self, interaction):
        if not self._guard(interaction): return await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
        try:
            r = self.engine.dao_lu.song_tu(self.user_id)
            await interaction.response.edit_message(embed=success_embed("💞 Song tu", f"Duyên phận tăng lên **{r['intimacy']}**."), view=self)
        except GameError as exc: await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _accept_pending(self, interaction):
        if not self._guard(interaction): return await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
        pending = self.engine.dao_lu.pending(self.user_id)
        if not pending: return await interaction.response.send_message("Không còn lời cầu duyên.", ephemeral=True)
        try:
            self.engine.dao_lu.accept(self.user_id, pending[0]["requester_id"])
            self.rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except GameError as exc: await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _back(self, interaction):
        if not self._guard(interaction): return await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
        from ui.views.gui_navigation import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
