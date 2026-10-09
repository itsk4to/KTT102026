from __future__ import annotations
import discord
from ui.theme.views import ThemedView
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed


class DaoLuView(ThemedView):
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
            accept = discord.ui.Button(label="Chấp nhận lời cầu duyên", emoji=EMOJI["accept"], style=discord.ButtonStyle.success, row=2)
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
            text = (
                f"Duyên phận tăng lên **{r['intimacy']}**.\\n"
                f"Tu vi của ngươi: **+{r['gain_self']:,}**\\n"
                f"Tu vi đạo lữ: **+{r['gain_partner']:,}**\\n"
                f"Cảnh giới: **{r['realm_self']}** · Đạo lữ: **{r['realm_partner']}**\\n"
                "Hai bên cùng nhận tu vi; cặp đạo lữ hồi phục sau 60 phút."
            )
            await interaction.response.edit_message(embed=success_embed("💞 Song Tu Thành Công", text), view=self)
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
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))


class DaoLuRequestView(ThemedView):
    def __init__(self, engine, target_id: str, requester_id: str, requester_name: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.target_id = target_id
        self.requester_id = requester_id
        self.requester_name = requester_name

        accept = discord.ui.Button(label="Đồng ý", emoji=EMOJI["accept"], style=discord.ButtonStyle.success)
        reject = discord.ui.Button(label="Từ chối", emoji=EMOJI["reject"], style=discord.ButtonStyle.danger)
        accept.callback = self._accept
        reject.callback = self._reject
        self.add_item(accept)
        self.add_item(reject)

    @staticmethod
    def build_request_embed(requester_name: str) -> discord.Embed:
        return base_embed("💞 Lời Cầu Duyên", f"**{requester_name}** muốn kết duyên cùng ngươi.\n\nNgươi có đồng ý trở thành đạo lữ không?")

    def _guard(self, interaction):
        return str(interaction.user.id) == self.target_id

    async def _accept(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Lời cầu duyên này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            self.engine.dao_lu.accept(self.target_id, self.requester_id)
            self.stop()
            await interaction.response.edit_message(embed=success_embed("💞 Kết Duyên Thành Công", f"Ngươi và **{self.requester_name}** đã trở thành đạo lữ."), view=None)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _reject(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Lời cầu duyên này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            self.engine.dao_lu.reject(self.target_id, self.requester_id)
            self.stop()
            await interaction.response.edit_message(embed=base_embed("💞 Cầu Duyên", "Ngươi đã từ chối lời cầu duyên."), view=None)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
