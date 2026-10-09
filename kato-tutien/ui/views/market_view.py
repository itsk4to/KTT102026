from __future__ import annotations

import discord

from ui.theme.views import ThemedView
from game.content.items import ITEMS
from game.services.errors import GameError
from game.utils import fmt_amount
from ui.embeds import base_embed, error_embed, success_embed
from ui.emoji import EMOJI


class MarketView(ThemedView):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.listings: list[dict] = []
        self.selected_id: int | None = None
        self.rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def rebuild(self):
        self.clear_items()
        self.listings = self.engine.economy.market_browse(25)
        if self.listings:
            options = []
            for row in self.listings:
                label = f"#{row['id']} · {row['name']} ×{row['qty']}"[:100]
                desc = f"{fmt_amount(row['price_each'])}/cái · {fmt_amount(row['price_total'])} tổng"[:100]
                options.append(discord.SelectOption(label=label, value=str(row["id"]), description=desc, emoji=EMOJI["shop"]))
            select = discord.ui.Select(placeholder="Chọn tin đăng…", options=options, row=0)
            select.callback = self._select
            self.add_item(select)

        buy = discord.ui.Button(label="Mua tin đã chọn", emoji=EMOJI["shop"], style=discord.ButtonStyle.success, row=1, disabled=self.selected_id is None)
        buy.callback = self._buy
        self.add_item(buy)

        cancel = discord.ui.Button(label="Hủy tin của ta", emoji=EMOJI["no"], style=discord.ButtonStyle.danger, row=1, disabled=self.selected_id is None)
        cancel.callback = self._cancel
        self.add_item(cancel)

        refresh = discord.ui.Button(label="Làm mới", emoji=EMOJI["back"], style=discord.ButtonStyle.secondary, row=2)
        refresh.callback = self._refresh
        self.add_item(refresh)
        back = discord.ui.Button(label="Trung tâm", emoji=EMOJI["back"], style=discord.ButtonStyle.secondary, row=2)
        back.callback = self._back
        self.add_item(back)

    def build_embed(self):
        rows = self.listings
        if not rows:
            return base_embed("🏪 Chợ Người Chơi", "Chưa có tin đăng.")
        selected = next((r for r in rows if r["id"] == self.selected_id), None)
        lines = [
            f"`#{r['id']}` **{r['name']}** ×{r['qty']} · {fmt_amount(r['price_each'])}/cái · {fmt_amount(r['price_total'])} {EMOJI['spirit_stone']}"
            for r in rows[:15]
        ]
        if selected:
            lines += ["", f"Đang chọn: **#{selected['id']} {selected['name']}** ×{selected['qty']}", f"Tổng: **{fmt_amount(selected['price_total'])}** {EMOJI['spirit_stone']}"]
        return base_embed("🏪 Chợ Người Chơi", "\n".join(lines))

    async def _select(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.selected_id = int(interaction.data["values"][0])
        self.rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _buy(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        if self.selected_id is None:
            await interaction.response.send_message(embed=error_embed("Hãy chọn một tin đăng trước."), ephemeral=True)
            return
        try:
            r = self.engine.economy.market_buy(self.user_id, self.selected_id)
            self.selected_id = None
            self.rebuild()
            name = ITEMS.get(r["item_id"], {}).get("name", r["item_id"])
            await interaction.response.edit_message(
                embed=success_embed("🏪 Mua chợ thành công", f"**{name}** ×{r['qty']} · -{fmt_amount(r['total'])} {EMOJI['spirit_stone']}"),
                view=self,
            )
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _cancel(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        if self.selected_id is None:
            await interaction.response.send_message(embed=error_embed("Hãy chọn một tin đăng trước."), ephemeral=True)
            return
        try:
            r = self.engine.economy.market_cancel(self.user_id, self.selected_id)
            self.selected_id = None
            self.rebuild()
            name = ITEMS.get(r["item_id"], {}).get("name", r["item_id"])
            await interaction.response.edit_message(
                embed=success_embed("🏪 Đã hủy tin", f"Hoàn **{name}** ×{r['qty']}."),
                view=self,
            )
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _refresh(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _back(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
