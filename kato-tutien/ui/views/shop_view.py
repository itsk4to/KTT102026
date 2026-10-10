from __future__ import annotations

import discord
from ui.theme.views import ThemedView
from game.services.errors import GameError
from game.utils import fmt_amount
from ui.embeds import base_embed, error_embed, success_embed
from ui.emoji import EMOJI


_CATEGORY_ICONS = {
    "Đan dược": EMOJI["pill"],
    "Bùa chú": EMOJI["talisman"],
    "Pháp bảo": EMOJI["artifact"],
    "Binh khí": EMOJI["attack"],
    "Công pháp": EMOJI["technique"],
}


class ShopQuantityModal(discord.ui.Modal, title="Mua vật phẩm"):
    quantity = discord.ui.TextInput(label="Số lượng", placeholder="Ví dụ: 10", min_length=1, max_length=4, required=True)

    def __init__(self, owner: "ShopView"):
        super().__init__()
        self.owner = owner

    async def on_submit(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            qty = int(str(self.quantity.value).strip())
            if qty < 1:
                raise ValueError
        except ValueError:
            await interaction.response.send_message(embed=error_embed("Số lượng phải là số nguyên lớn hơn 0."), ephemeral=True)
            return
        await self.owner.purchase(interaction, qty)


class ShopCategorySelect(discord.ui.Select):
    def __init__(self, owner: "ShopView"):
        self.owner = owner
        options = [
            discord.SelectOption(
                label=c["name"],
                value=c["name"],
                emoji=_CATEGORY_ICONS.get(c["name"], EMOJI["item"]),
                description=f"{len(c['items'])} vật phẩm",
            )
            for c in owner.catalog.get("categories", [])
        ]
        super().__init__(placeholder="Chọn danh mục vật phẩm…", options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.owner.category = self.values[0]
        self.owner.selected_id = None
        self.owner.rebuild()
        await interaction.response.edit_message(embed=self.owner.build_embed(), view=self.owner)


class ShopItemSelect(discord.ui.Select):
    def __init__(self, owner: "ShopView"):
        self.owner = owner
        items = owner.selected_items
        options = [
            discord.SelectOption(
                label=it["name"][:100],
                value=it["id"],
                emoji=it.get("emoji", _CATEGORY_ICONS.get(it.get("category"), EMOJI["item"])),
                description=f"{it.get('rarity_emoji', '⚪')} {it['rarity']} · {fmt_amount(it['price'])} linh thạch",
            )
            for it in items[:25]
        ]
        if not options:
            options = [discord.SelectOption(label="Danh mục trống", value="__empty__", emoji=EMOJI["no"])]
        super().__init__(placeholder="Chọn vật phẩm…", options=options, disabled=not items, row=1)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.owner.selected_id = self.values[0]
        self.owner.rebuild()
        await interaction.response.edit_message(embed=self.owner.build_embed(), view=self.owner)


class ShopView(ThemedView):
    def __init__(self, engine, catalog: dict, user_id: str | None = None, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.catalog = catalog
        self.user_id = user_id
        self.category: str | None = None
        self.selected_id: str | None = None
        self.last_purchase_notice: str = ""
        self._build_controls()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return self.user_id is None or str(interaction.user.id) == self.user_id

    @property
    def selected_category(self):
        return next((c for c in self.catalog.get("categories", []) if c["name"] == self.category), None)

    @property
    def selected_items(self):
        return (self.selected_category or {}).get("items", [])

    @property
    def selected_item(self):
        return next((i for i in self.selected_items if i["id"] == self.selected_id), None)

    def build_embed(self):
        if not self.category:
            lines = [f"{_CATEGORY_ICONS.get(c['name'], EMOJI['item'])} **{c['name']}** · {len(c['items'])} vật phẩm" for c in self.catalog.get("categories", [])]
            balance = 0
            try:
                player = self.engine.players.get(str(self.user_id)) if self.user_id else None
                balance = int(player.spirit_stones) if player else 0
            except Exception:
                balance = 0
            text = "Chọn danh mục trước, sau đó chọn **một vật phẩm** để xem công dụng và chỉ số đầy đủ.\n\n" + "\n".join(lines)
            text += f"\n\n{EMOJI['spirit_stone']} Số dư: **{fmt_amount(balance)}** linh thạch."
            if self.last_purchase_notice:
                text = self.last_purchase_notice + "\n\n" + text
            return base_embed(f"{EMOJI['shop']} Tiên Phường", text)
        item = self.selected_item
        if not item:
            balance = 0
            try:
                player = self.engine.players.get(str(self.user_id)) if self.user_id else None
                balance = int(player.spirit_stones) if player else 0
            except Exception:
                balance = 0
            text = (f"Danh mục **{self.category}** có **{len(self.selected_items)}** món.\n"
                    "Chọn một món trong menu vật phẩm bên dưới để xem công dụng, giá và ID.\n\n"
                    f"{EMOJI['spirit_stone']} Số dư hiện tại: **{fmt_amount(balance)}** linh thạch.")
            return base_embed(f"{EMOJI['shop']} Tiên Phường · {self.category}", text)
        player = self.engine.players.get(str(self.user_id)) if self.user_id else None
        balance = int(player.spirit_stones) if player else 0
        detail = (
            f"Danh mục: **{self.category}** · ID: `{item['id']}`\n"
            f"Phẩm cấp: {item.get('rarity_emoji', '⚪')} **{item['rarity']} phẩm**\n"
            f"Giá: **{fmt_amount(item['price'])}** {EMOJI['spirit_stone']}\n"
            f"Số dư: **{fmt_amount(balance)}** linh thạch\n"
            f"\n**✨ Tác dụng**\n" + "\n".join(f"• {effect}" for effect in item.get("effects", [])) +
            f"\n\n📖 {item['description']}"
        )
        if self.last_purchase_notice:
            detail += f"\n\n{self.last_purchase_notice}"
        return base_embed(f"{item.get('emoji', _CATEGORY_ICONS.get(self.category, EMOJI['item']))} {item['name']}", detail)

    def _build_controls(self):
        self.clear_items()
        self.add_item(ShopCategorySelect(self))
        if self.category:
            self.add_item(ShopItemSelect(self))
            for qty, label in ((1, "Mua ×1"), (5, "Mua ×5"), (10, "Mua ×10")):
                btn = discord.ui.Button(label=label, emoji=EMOJI["item"], style=discord.ButtonStyle.primary, row=2, disabled=self.selected_item is None)
                btn.callback = self._make_buy(qty)
                self.add_item(btn)
            custom = discord.ui.Button(label="Số khác", emoji=EMOJI["quantity"], style=discord.ButtonStyle.secondary, row=2, disabled=self.selected_item is None)
            custom.callback = self._custom_quantity
            self.add_item(custom)
        back = discord.ui.Button(label="Trung tâm", emoji=EMOJI["back"], style=discord.ButtonStyle.secondary, row=3)
        back.callback = self._back
        self.add_item(back)

    def rebuild(self):
        self._build_controls()

    def _make_buy(self, qty: int):
        async def callback(interaction: discord.Interaction):
            if not self._guard(interaction):
                await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
                return
            await self.purchase(interaction, qty)
        return callback

    async def _custom_quantity(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.send_modal(ShopQuantityModal(self))

    async def purchase(self, interaction: discord.Interaction, qty: int):
        if not self.selected_item:
            await interaction.response.send_message(embed=error_embed("Hãy chọn vật phẩm trước."), ephemeral=True)
            return
        try:
            result = self.engine.economy.buy(str(interaction.user.id), self.selected_item["id"], qty)
            item = result["item"]
            self.last_purchase_notice = (
                f"✅ Đã mua **{item['name']} ×{qty}** với giá **{fmt_amount(result['total'])}** linh thạch."
                f"\nSố dư còn lại: **{fmt_amount(result['player'].spirit_stones)}** linh thạch."
            )
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _back(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
