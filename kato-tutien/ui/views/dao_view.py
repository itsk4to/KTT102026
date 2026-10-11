from __future__ import annotations

import discord

from ui.theme.views import ThemedView
from game.content.dao_paths import DAO_PATHS
from game.services.errors import GameError
from ui.embeds import base_embed, error_embed, success_embed
from ui.emoji import EMOJI


DAO_PATH_DESCRIPTIONS = {
    "kiem": "Công kích và độ chính xác cân bằng · ATK ×1,12 · Chính xác ×1,08.",
    "dao": "Thiên về sát thương bùng nổ · ATK ×1,15 · Phòng ngự ×0,92.",
    "phap": "Thiên về pháp thuật và linh lực · ATK ×1,08 · Linh lực ×1,15.",
    "the": "Lối tu hành bền bỉ · HP ×1,12 · Phòng ngự ×1,18.",
    "ma": "Đánh đổi phòng ngự để lấy sức công phá · ATK ×1,20 · Bạo kích ×1,10.",
}


class DaoPathSelect(discord.ui.Select):
    def __init__(self, owner: "DaoMenuView"):
        self.owner = owner
        options = [
            discord.SelectOption(
                label=data["name"][:100],
                value=key,
                emoji=data.get("emoji", "☯️"),
                description=DAO_PATH_DESCRIPTIONS.get(key, f"Chọn {data['name']} làm con đường tu hành.")[:100],
                default=key == owner.selected_key,
            )
            for key, data in DAO_PATHS.items()
        ][:25]
        super().__init__(placeholder="Chọn con đường Đại Đạo…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.owner.selected_key = self.values[0]
        self.owner._build()
        await interaction.response.edit_message(embed=self.owner.build_embed(), view=self.owner)


class DaoMenuView(ThemedView):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.selected_key: str | None = None
        self._build()

    def _build(self):
        self.clear_items()
        info = self.engine.dao.info(self.user_id)
        if not info:
            self.add_item(DaoPathSelect(self))
            choose = discord.ui.Button(label="Chọn Đạo", style=discord.ButtonStyle.primary, emoji=EMOJI["dao"], row=1, disabled=not self.selected_key)
            choose.callback = self._choose_selected
            self.add_item(choose)
        back = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji="🏠", row=1)
        back.callback = self._back
        self.add_item(back)

    def build_embed(self) -> discord.Embed:
        info = self.engine.dao.info(self.user_id)
        if not info:
            e = base_embed(f"{EMOJI['dao']} KHỞI MỞ ĐẠI ĐẠO", "Ngươi hãy chọn một con đường để định hình phong cách tu hành. Lựa chọn này gắn với hồ sơ nhân vật; hãy xem mô tả trước khi xác nhận.")
            for key, data in DAO_PATHS.items():
                e.add_field(name=f"{data.get('emoji', '☯️')} {data['name']}", value=DAO_PATH_DESCRIPTIONS.get(key, data.get("description", "Một con đường lĩnh ngộ riêng biệt.")), inline=True)
            if self.selected_key in DAO_PATHS:
                e.add_field(name="Đang chọn", value=f"**{DAO_PATHS[self.selected_key]['name']}**\nBấm **Chọn Đạo** để xác nhận.", inline=False)
            e.set_footer(text="ĐẠI ĐẠO · Chọn trong danh sách rồi xác nhận")
            return e
        e = base_embed(f"{EMOJI['dao']} {info['dao']['name']}", "*Hành trình lĩnh ngộ Đại Đạo của ngươi.*")
        e.add_field(name="Tầng Đạo", value=f"**{info['stage_name']}**", inline=True)
        e.add_field(name="Ngộ tính", value=f"**{info['insight']} / {info['next_threshold']}**", inline=True)
        e.add_field(name="Tiến độ lĩnh ngộ", value=f"`{'▰' * min(12, int(info['insight'] * 12 / max(1, info['next_threshold'])))}{'▱' * (12 - min(12, int(info['insight'] * 12 / max(1, info['next_threshold']))))}`", inline=False)
        return e

    async def _choose_selected(self, interaction: discord.Interaction):
        if not self.selected_key:
            await interaction.response.send_message("Hãy chọn một Đạo trong danh sách trước.", ephemeral=True)
            return
        await self._choose(interaction, self.selected_key)

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
