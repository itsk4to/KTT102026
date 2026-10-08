from __future__ import annotations

import discord
from ui.emoji import EMOJI
from ui.embeds import combat_embed, error_embed
from game.services.errors import GameError


class CombatView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id

    async def _guard(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Không phải trận của bạn.", ephemeral=True)
            return False
        return True

    @discord.ui.button(label="Tấn công", emoji="⚔️", style=discord.ButtonStyle.danger)
    async def btn_attack(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        try:
            result = self.engine.combat.attack(self.user_id)
            await interaction.response.edit_message(embed=combat_embed(result["encounter"]), view=None if result.get("finished") else self)
        except GameError as e:
            await interaction.response.send_message(embed=error_embed(str(e)), ephemeral=True)

    @discord.ui.button(label="Rút lui", emoji="🏃", style=discord.ButtonStyle.secondary)
    async def btn_flee(self, interaction: discord.Interaction, button: discord.ui.Button):
        if not await self._guard(interaction):
            return
        try:
            result = self.engine.combat.flee(self.user_id)
            await interaction.response.edit_message(embed=combat_embed(result["encounter"]), view=None if result.get("fled") or result.get("finished") else self)
        except GameError as e:
            await interaction.response.send_message(embed=error_embed(str(e)), ephemeral=True)
