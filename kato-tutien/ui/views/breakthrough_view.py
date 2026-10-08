from __future__ import annotations

import discord

from game.content.items import ITEMS
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import error_embed, success_embed, cultivation_preview_embed


class BreakthroughItemSelect(discord.ui.Select):
    def __init__(self, owner: "BreakthroughView"):
        self.owner = owner
        inventory = owner.engine.economy.inventory(owner.user_id)
        items = [
            x for x in inventory
            if x.get("meta", {}).get("type") == "consumable"
            and x.get("meta", {}).get("breakthrough_bonus")
        ]
        options = [
            discord.SelectOption(
                label=x["name"][:100], value=x["id"],
                description=f"×{x['qty']} · +{x['meta']['breakthrough_bonus']:.0%} tỷ lệ",
                emoji=EMOJI["pill"],
            ) for x in items[:25]
        ] or [discord.SelectOption(label="Không có đạo cụ hỗ trợ đột phá", value="__empty__", emoji=EMOJI["no"])]
        super().__init__(placeholder="Chọn đạo cụ hỗ trợ…", options=options, row=1, disabled=not items)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        if self.values[0] == "__empty__":
            await interaction.response.send_message("Ngươi chưa có đạo cụ hỗ trợ đột phá.", ephemeral=True)
            return
        try:
            r = self.owner.engine.breakthrough.preview_item(self.owner.user_id, self.values[0])
            self.owner.selected_item = self.values[0]
            self.owner.bonus = r["bonus"]
            self.owner.rebuild()
            await interaction.response.edit_message(embed=cultivation_preview_embed(self.owner.engine.cultivation.breakthrough_preview(self.owner.user_id, self.owner.bonus)), view=self.owner)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class BreakthroughView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.bonus = 0.0
        self.selected_item: str | None = None
        self.rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def rebuild(self):
        self.clear_items()
        self.add_item(BreakthroughItemSelect(self))

        accept = discord.ui.Button(label="Đồng ý đột phá", emoji=EMOJI["accept"], style=discord.ButtonStyle.success, row=2)
        accept.callback = self._accept
        self.add_item(accept)
        reject = discord.ui.Button(label="Từ chối", emoji=EMOJI["reject"], style=discord.ButtonStyle.secondary, row=2)
        reject.callback = self._reject
        self.add_item(reject)
        use = discord.ui.Button(label="Dùng đạo cụ", emoji=EMOJI["item"], style=discord.ButtonStyle.primary, row=2)
        use.callback = self._use_hint
        self.add_item(use)

    async def _accept(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.breakthrough.breakthrough(self.user_id, self.bonus, self.selected_item)
            if r["success"]:
                await interaction.response.edit_message(embed=success_embed(f"{EMOJI['breakthrough']} Đột phá thành công", f"Cảnh giới: **{r['realm']}** · tỷ lệ **{r['chance']:.0%}**"), view=None)
            else:
                await interaction.response.edit_message(embed=error_embed(f"Đột phá thất bại · tỷ lệ **{r['chance']:.0%}**\nTu vi bị tổn thất."), view=None)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _reject(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(embed=success_embed("Đã từ chối đột phá", "Ngươi giữ nguyên cảnh giới và tiếp tục chuẩn bị."), view=None)

    async def _use_hint(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.send_message("Đạo cụ chỉ được tiêu hao khi ngươi bấm **Đồng ý đột phá**.", ephemeral=True)
