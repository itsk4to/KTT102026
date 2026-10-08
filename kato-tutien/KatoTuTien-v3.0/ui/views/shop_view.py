from __future__ import annotations

import discord
from ui.embeds import shop_embed, success_embed, error_embed
from ui.emoji import EMOJI
from game.services.errors import GameError
from game.utils import fmt_amount


class ShopCategorySelect(discord.ui.Select):
    def __init__(self, engine, catalog: dict):
        self.engine = engine
        self.catalog = catalog
        options = [
            discord.SelectOption(label=c["name"], value=c["name"])
            for c in catalog.get("categories", [])
        ]
        super().__init__(placeholder="Chọn danh mục…", options=options[:25])

    async def callback(self, interaction: discord.Interaction):
        cat_name = self.values[0]
        cat = next(c for c in self.catalog["categories"] if c["name"] == cat_name)
        view = discord.ui.View(timeout=120)
        view.add_item(ShopItemSelect(self.engine, cat["items"]))
        embed = discord.Embed(title=f"{EMOJI['shop']} {cat_name}")
        for it in cat["items"]:
            embed.add_field(
                name=f"{it['name']} ({it['rarity']})",
                value=f"{fmt_amount(it['price'])} {EMOJI['spirit_stone']}\n{it['description'][:80]}",
                inline=False,
            )
        await interaction.response.edit_message(embed=embed, view=view)


class ShopItemSelect(discord.ui.Select):
    def __init__(self, engine, items: list[dict]):
        self.engine = engine
        self.items = {it["id"]: it for it in items}
        options = [
            discord.SelectOption(label=f"{it['name']} — {it['price']}", value=it["id"])
            for it in items[:25]
        ]
        super().__init__(placeholder="Mua vật phẩm…", options=options)

    async def callback(self, interaction: discord.Interaction):
        item_id = self.values[0]
        try:
            result = self.engine.economy.buy(str(interaction.user.id), item_id, 1)
            it = result["item"]
            await interaction.response.send_message(
                embed=success_embed(
                    "✅ Mua thành công",
                    f"Nhận **{it['name']}** ×1\nCòn {fmt_amount(result['player'].spirit_stones)} {EMOJI['spirit_stone']}",
                ),
                ephemeral=True,
            )
        except GameError as e:
            await interaction.response.send_message(embed=error_embed(str(e)), ephemeral=True)


class ShopView(discord.ui.View):
    def __init__(self, engine, catalog: dict, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.add_item(ShopCategorySelect(engine, catalog))
