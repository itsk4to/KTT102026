from __future__ import annotations

import discord

from game.content.dao_paths import DAO_PATHS
from game.services.errors import GameError
from ui.embeds import base_embed, error_embed, success_embed
from ui.emoji import EMOJI


class DaoMenuView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self._build()

    def _build(self):
        self.clear_items()
        info = self.engine.dao.info(self.user_id)
        if not info:
            button_emojis = {
                "kiem": EMOJI["attack"],
                "dao": EMOJI["attack"],
                "phap": EMOJI["talisman"],
                "the": EMOJI["def"],
                "ma": EMOJI["demon"],
            }
            for index, (key, data) in enumerate(DAO_PATHS.items()):
                button = discord.ui.Button(
                    label=data["name"],
                    style=discord.ButtonStyle.primary,
                    emoji=button_emojis.get(key, EMOJI["dao"]),
                    row=index // 3,
                )
                button.callback = self._make_choose(key)
                self.add_item(button)
        back = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji="🏠", row=2 if not info else 1)
        back.callback = self._back
        self.add_item(back)

    def build_embed(self) -> discord.Embed:
        info = self.engine.dao.info(self.user_id)
        if not info:
            lines = [f"{v.get('emoji', '☯️')} **{v['name']}**" for v in DAO_PATHS.values()]
            return base_embed(f"{EMOJI['dao']} Đường Đạo", "Ngươi chưa nhập Đạo. Hãy chọn một Đạo để bước sâu hơn trên con đường tu hành.\n\n" + "\n".join(lines) + "\n\nChọn bằng menu phía dưới.")
        return base_embed(f"{EMOJI['dao']} {info['dao']['name']}", f"Tầng: **{info['stage_name']}**\nNgộ tính: **{info['insight']}/{info['next_threshold']}**")

    def _make_choose(self, key: str):
        async def callback(interaction: discord.Interaction):
            await self._choose(interaction, key)
        return callback

    async def _choose(self, interaction: discord.Interaction, key: str):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.dao.choose(self.user_id, key)
            self._build()
            await interaction.response.edit_message(embed=success_embed("☯️ Chọn Đạo", f"Đã bước lên **{r['dao']['name']}** · {r['stage']}"), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _back(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
