from __future__ import annotations

import discord

from game.content.items import ITEMS, SHOP_ORDER
from game.content.item_catalog import category_items, item_effect_lines
from ui.theme.views import ThemedView
from ui.embeds import base_embed
from game.utils import fmt_amount

_CATEGORY_EMOJI = {
    "Đan dược": "💊", "Bùa chú": "🔮", "Pháp bảo": "💠",
    "Binh khí": "⚔️", "Công pháp": "📜",
}


class ItemCatalogCategorySelect(discord.ui.Select):
    def __init__(self, owner: "ItemIdBrowserView"):
        self.owner = owner
        options = [discord.SelectOption(
            label=category,
            value=category,
            emoji=_CATEGORY_EMOJI.get(category, "📦"),
            description=f"{len(category_items(category))} vật phẩm",
            default=owner.category == category,
        ) for category in SHOP_ORDER]
        super().__init__(placeholder="Chọn danh mục vật phẩm…", options=options, row=0)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner.guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về bạn.", ephemeral=True)
            return
        self.owner.category = self.values[0]
        self.owner.selected_id = None
        self.owner.rebuild()
        await interaction.response.edit_message(embed=self.owner.build_embed(), view=self.owner)


class ItemCatalogItemSelect(discord.ui.Select):
    def __init__(self, owner: "ItemIdBrowserView"):
        self.owner = owner
        items = category_items(owner.category) if owner.category else []
        options = [discord.SelectOption(
            label=item.get("name", item_id)[:100],
            value=item_id,
            description=f"{item.get('rarity', 'Phàm')} phẩm · {fmt_amount(item.get('price', 0))} linh thạch"[:100],
            default=owner.selected_id == item_id,
        ) for item_id, item in items[:25]]
        super().__init__(placeholder="Chọn vật phẩm để xem ID…", options=options or [discord.SelectOption(label="Chọn danh mục trước", value="__empty__")], disabled=not options, row=1)

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner.guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về bạn.", ephemeral=True)
            return
        self.owner.selected_id = self.values[0]
        self.owner.rebuild()
        await interaction.response.edit_message(embed=self.owner.build_embed(), view=self.owner)


class ItemIdBrowserView(ThemedView):
    """Reusable GUI that exposes exact, copyable item IDs to players/admins."""
    def __init__(self, user_id: str | None = None, timeout: float = 240):
        super().__init__(timeout=timeout)
        self.user_id = str(user_id) if user_id is not None else None
        self.category: str | None = None
        self.selected_id: str | None = None
        self.rebuild()

    def guard(self, interaction: discord.Interaction) -> bool:
        return self.user_id is None or str(interaction.user.id) == self.user_id

    def build_embed(self):
        if not self.category:
            lines = [f"{_CATEGORY_EMOJI.get(cat, '📦')} **{cat}** · {len(category_items(cat))} món" for cat in SHOP_ORDER]
            body = (
                "Chọn danh mục rồi chọn vật phẩm để xem ID chính xác.\n\n"
                + "\n".join(lines)
                + "\n\nDùng ID hiển thị trong `.mua`, `.dung`, `.trangbi` và phần tạo Mật Lệnh."
            )
            return base_embed("🧾 Tra cứu ID vật phẩm", body)
        if not self.selected_id or self.selected_id not in ITEMS:
            return base_embed(f"🧾 Tra cứu ID · {self.category}", "Chọn vật phẩm ở danh sách bên dưới để xem mã ID.")
        item = ITEMS[self.selected_id]
        price = item.get("price", 0)
        body = (
            f"**Tên:** {item.get('name', self.selected_id)}\n"
            f"**ID cần sao chép:** `{self.selected_id}`\n"
            f"**Danh mục:** {item.get('category', 'Khác')} · **Phẩm cấp:** {item.get('rarity', 'Phàm')}\n"
            f"**Giá tham khảo:** {fmt_amount(price)} linh thạch\n\n"
            f"**Chỉ số / hiệu ứng**\n" + "\n".join(item_effect_lines(item))
            + f"\n\n📖 {item.get('description', 'Chưa có mô tả.')}"
        )
        return base_embed(f"🧾 {item.get('name', self.selected_id)}", body)

    def rebuild(self):
        self.clear_items()
        self.add_item(ItemCatalogCategorySelect(self))
        self.add_item(ItemCatalogItemSelect(self))
        close = discord.ui.Button(label="Đóng", emoji="✖️", style=discord.ButtonStyle.secondary, row=2)
        async def close_callback(interaction: discord.Interaction):
            if not self.guard(interaction):
                await interaction.response.send_message("Giao diện này không thuộc về bạn.", ephemeral=True)
                return
            await interaction.response.edit_message(view=None)
        close.callback = close_callback
        self.add_item(close)
