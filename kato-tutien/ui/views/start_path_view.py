from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, player_embed


class PathChoiceView(discord.ui.View):
    def __init__(self, engine, user_id: str, display_name: str, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.display_name = display_name

    async def _choose(self, interaction: discord.Interaction, path: str):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            p = self.engine.players.create(self.user_id, self.display_name, path)
            await interaction.response.edit_message(embed=player_embed(self.engine.players.info_text(self.user_id)), view=None)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Tu Tiên", style=discord.ButtonStyle.success, emoji=EMOJI["cultivator"], row=0)
    async def choose_tien(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._choose(interaction, "tien")

    @discord.ui.button(label="Tu Ma", style=discord.ButtonStyle.danger, emoji=EMOJI["demon"], row=0)
    async def choose_ma(self, interaction: discord.Interaction, _button: discord.ui.Button):
        await self._choose(interaction, "ma")

    @discord.ui.button(label="Từ chối", style=discord.ButtonStyle.secondary, emoji=EMOJI["reject"], row=1)
    async def reject(self, interaction: discord.Interaction, _button: discord.ui.Button):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(embed=base_embed("Khai Đạo", "Ngươi tạm thời chưa bước lên con đường tu hành."), view=None)
