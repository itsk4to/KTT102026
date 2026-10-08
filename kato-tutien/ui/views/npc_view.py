from __future__ import annotations

import discord

from game.services.errors import GameError
from ui.embeds import base_embed, error_embed
from ui.views.quest_view import QuestOfferView


class NPCMenuView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.selected_key: str | None = None
        self._build()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def _build(self):
        self.clear_items()
        npcs = self.engine.npc.list_npcs(self.user_id)
        options = [discord.SelectOption(label=n["name"][:100], value=n["key"], description=n["title"][:100], emoji="👤") for n in npcs[:25]]
        if options:
            select = discord.ui.Select(placeholder="Chọn NPC…", options=options, row=0)
            select.callback = self._select
            self.add_item(select)
        talk = discord.ui.Button(label="Nói chuyện", style=discord.ButtonStyle.primary, row=1, disabled=not self.selected_key)
        talk.callback = self._talk
        self.add_item(talk)
        back = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji="🏠", row=1)
        back.callback = self._back
        self.add_item(back)

    def build_embed(self) -> discord.Embed:
        npcs = self.engine.npc.list_npcs(self.user_id)
        if not npcs:
            return base_embed("👤 NPC", "Khu vực hiện tại chưa có người quen nào đáng chú ý.")
        lines = [f"👤 **{n['name']}** · {n['title']}" for n in npcs[:10]]
        return base_embed("👤 Người Trong Giang Hồ", "\n".join(lines) + "\n\nChọn một NPC rồi bấm **Nói chuyện**.")

    async def _select(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.selected_key = interaction.data["values"][0]
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _talk(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.npc.talk(self.user_id, self.selected_key)
            npc = r["npc"]
            desc = f"**{npc['title']}**\n{npc['greeting']}"
            if r.get("memory"):
                desc += f"\n\nQuan hệ: **{r['memory'].get('affinity', 0):+d}** · Gặp **{r['memory'].get('encounters', 0)}** lần"
            if r["quests"]:
                desc += "\n\n📜 Người này có chuyện muốn nhờ ngươi."
                await interaction.response.edit_message(embed=base_embed(f"👤 {npc['name']}", desc), view=QuestOfferView(self.engine, self.user_id, r["quests"]))
            else:
                desc += "\n\n*Hiện chưa có nhiệm vụ mới.*"
                self._build()
                await interaction.response.edit_message(embed=base_embed(f"👤 {npc['name']}", desc), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _back(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
