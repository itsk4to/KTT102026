from __future__ import annotations

import discord

from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import error_embed, inventory_embed, inventory_item_icon


_PAGE_SIZE = 20
_CATEGORY_ALL = "Tất cả"
_CATEGORY_ORDER = ("Đan dược", "Bùa chú", "Pháp bảo", "Binh khí", "Công pháp")


class InventoryCategorySelect(discord.ui.Select):
    def __init__(self, owner: "InventoryView"):
        self.owner = owner
        options = [
            discord.SelectOption(
                label=_CATEGORY_ALL,
                value=_CATEGORY_ALL,
                emoji=EMOJI["all"],
                default=owner.category == _CATEGORY_ALL,
                description="Hiển thị toàn bộ vật phẩm.",
            )
        ]
        categories = []
        for item in owner.all_items:
            category = str(item.get("meta", {}).get("category", "Vật phẩm"))
            if category not in categories:
                categories.append(category)
        ordered = [c for c in _CATEGORY_ORDER if c in categories]
        ordered.extend(c for c in categories if c not in ordered)
        icon_map = {
            "Đan dược": EMOJI["consumable"],
            "Bùa chú": EMOJI["talisman"],
            "Pháp bảo": EMOJI["artifact"],
            "Binh khí": EMOJI["weapon"],
            "Công pháp": EMOJI["technique"],
        }
        for category in ordered[:24]:
            options.append(
                discord.SelectOption(
                    label=category,
                    value=category,
                    emoji=icon_map.get(category, EMOJI["unknown"]),
                    default=owner.category == category,
                    description=f"Xem {category.lower()} trong túi.",
                )
            )
        super().__init__(
            placeholder="Chọn loại vật phẩm…",
            min_values=1,
            max_values=1,
            options=options,
            row=0,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Túi đồ này không thuộc về bạn.", ephemeral=True)
            return
        self.owner.message = interaction.message
        self.owner.category = self.values[0]
        self.owner.page = 0
        self.owner.selected_id = None
        self.owner.rebuild()
        await interaction.response.edit_message(
            embed=self.owner.build_embed(),
            view=self.owner,
        )


class InventoryItemSelect(discord.ui.Select):
    def __init__(self, owner: "InventoryView"):
        self.owner = owner
        items = owner.filtered_items
        start = owner.page * _PAGE_SIZE
        current = items[start:start + _PAGE_SIZE]
        options = [
            discord.SelectOption(
                label=item["name"][:100],
                value=item["id"],
                description=f"×{item['qty']} · {item.get('meta', {}).get('rarity', 'Phàm')}"[:100],
                emoji=inventory_item_icon(item),
                default=item["id"] == owner.selected_id,
            )
            for item in current
        ]
        if not options:
            options = [
                discord.SelectOption(
                    label="Không có vật phẩm",
                    value="__empty__",
                    description="Không có vật phẩm trong loại này.",
                    emoji=EMOJI["no"],
                )
            ]
        super().__init__(
            placeholder="Chọn vật phẩm để thao tác nhanh…",
            min_values=1,
            max_values=1,
            options=options[:25],
            row=1,
            disabled=not items,
        )

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Túi đồ này không thuộc về bạn.", ephemeral=True)
            return
        self.owner.message = interaction.message
        value = self.values[0]
        if value == "__empty__":
            await interaction.response.send_message("Loại vật phẩm này hiện không có đồ.", ephemeral=True)
            return
        self.owner.selected_id = value
        self.owner.rebuild()
        await interaction.response.edit_message(
            embed=self.owner.build_embed(),
            view=self.owner,
        )


class InventoryQuantityModal(discord.ui.Modal, title="Chọn số lượng"):
    quantity = discord.ui.TextInput(
        label="Số lượng muốn dùng",
        placeholder="Ví dụ: 10",
        min_length=1,
        max_length=3,
        required=True,
    )

    def __init__(self, owner: "InventoryView"):
        super().__init__()
        self.owner = owner

    async def on_submit(self, interaction: discord.Interaction) -> None:
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Túi đồ này không thuộc về bạn.", ephemeral=True)
            return
        try:
            quantity = int(str(self.quantity.value).strip())
        except ValueError:
            await interaction.response.send_message(embed=error_embed("Số lượng phải là số nguyên."), ephemeral=True)
            return
        if quantity < 1:
            await interaction.response.send_message(embed=error_embed("Số lượng phải lớn hơn 0."), ephemeral=True)
            return
        await self.owner.perform_action(interaction, "use", quantity, from_modal=True)


class InventoryView(discord.ui.View):
    def __init__(
        self,
        engine,
        user_id: str,
        items: list[dict],
        *,
        category: str = _CATEGORY_ALL,
        page: int = 0,
        selected_id: str | None = None,
        timeout: float = 180,
    ):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.all_items = list(items)
        self.category = category
        self.page = page
        self.selected_id = selected_id
        self.message = None
        self._use_buttons: dict[int, discord.ui.Button] = {}
        self._custom_button: discord.ui.Button | None = None
        self._action_button: discord.ui.Button | None = None
        self._build_controls()

    @property
    def filtered_items(self) -> list[dict]:
        if self.category == _CATEGORY_ALL:
            return list(self.all_items)
        return [
            item for item in self.all_items
            if item.get("meta", {}).get("category") == self.category
        ]

    @property
    def selected(self) -> dict | None:
        if not self.selected_id:
            return None
        return next((item for item in self.all_items if item.get("id") == self.selected_id), None)

    @property
    def max_page(self) -> int:
        return max(0, (len(self.filtered_items) - 1) // _PAGE_SIZE)

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def build_embed(self, notice: str | None = None) -> discord.Embed:
        self.page = max(0, min(self.page, self.max_page))
        return inventory_embed(
            self.filtered_items,
            page=self.page,
            page_size=_PAGE_SIZE,
            category=self.category,
            selected=self.selected,
            notice=notice,
        )

    def _build_controls(self) -> None:
        self.clear_items()

        self.add_item(InventoryCategorySelect(self))
        self.add_item(InventoryItemSelect(self))

        selected = self.selected
        item_type = selected.get("meta", {}).get("type") if selected else None
        quantity = int(selected.get("qty", 0)) if selected else 0

        for qty, label, emoji in (
            (1, "Dùng ×1", "1️⃣"),
            (5, "Dùng ×5", "5️⃣"),
            (10, "Dùng ×10", "🔟"),
        ):
            button = discord.ui.Button(
                label=label,
                style=discord.ButtonStyle.primary,
                emoji=emoji,
                row=2,
                disabled=not (selected and item_type == "consumable" and quantity >= qty),
            )
            button.callback = self._make_action_callback("use", qty)
            self._use_buttons[qty] = button
            self.add_item(button)

        self._custom_button = discord.ui.Button(
            label="Số khác",
            style=discord.ButtonStyle.secondary,
            emoji=EMOJI["quantity"],
            row=2,
            disabled=not (selected and item_type == "consumable" and quantity > 0),
        )
        self._custom_button.callback = self._custom_quantity_callback
        self.add_item(self._custom_button)

        if selected and item_type == "equipment":
            action_label, action_emoji, action_name = "Trang bị", EMOJI["equip"], "equip"
        elif selected and item_type == "technique":
            action_label, action_emoji, action_name = "Học công pháp", EMOJI["learn"], "learn"
        else:
            action_label, action_emoji, action_name = "Trang bị/Học", EMOJI["item"], ""
        self._action_button = discord.ui.Button(
            label=action_label,
            style=discord.ButtonStyle.success,
            emoji=action_emoji,
            row=2,
            disabled=not action_name,
        )
        self._action_button.callback = self._make_action_callback(action_name, 0)
        self.add_item(self._action_button)

        previous = discord.ui.Button(
            label="Trang trước",
            style=discord.ButtonStyle.secondary,
            emoji=EMOJI["previous"],
            row=3,
            disabled=self.page == 0,
        )
        previous.callback = self._page_callback(-1)
        self.add_item(previous)

        next_button = discord.ui.Button(
            label="Trang sau",
            style=discord.ButtonStyle.secondary,
            emoji=EMOJI["next"],
            row=3,
            disabled=self.page >= self.max_page,
        )
        next_button.callback = self._page_callback(1)
        self.add_item(next_button)

        refresh = discord.ui.Button(
            label="Làm mới",
            style=discord.ButtonStyle.secondary,
            emoji=EMOJI["refresh"],
            row=3,
        )
        refresh.callback = self._refresh_callback
        self.add_item(refresh)

        close = discord.ui.Button(
            label="Đóng",
            style=discord.ButtonStyle.danger,
            emoji=EMOJI["close"],
            row=3,
        )
        close.callback = self._close_callback
        self.add_item(close)

    def rebuild(self) -> None:
        self._build_controls()

    def _make_action_callback(self, action: str, quantity: int):
        async def callback(interaction: discord.Interaction) -> None:
            if not self._guard(interaction):
                await interaction.response.send_message("Túi đồ này không thuộc về bạn.", ephemeral=True)
                return
            self.message = interaction.message
            await self.perform_action(interaction, action, quantity)
        return callback

    async def perform_action(self, interaction: discord.Interaction, action: str, quantity: int, *, from_modal: bool = False) -> None:
        selected = self.selected
        if not selected:
            await interaction.response.send_message(embed=error_embed("Hãy chọn một vật phẩm trước."), ephemeral=True)
            return
        try:
            item_id = selected["id"]
            if action == "use":
                result = self.engine.economy.use_item(self.user_id, item_id, quantity)
                notes = ", ".join(result["notes"]) or result["item"]["name"]
                notice = f"{EMOJI['ok']} Đã dùng **{result['item']['name']}** ×{quantity} · {notes}"
            elif action == "equip":
                result = self.engine.economy.equip(self.user_id, item_id)
                notice = f"{EMOJI['ok']} Đã trang bị **{result['item']['name']}**."
            elif action == "learn":
                result = self.engine.economy.learn_technique(self.user_id, item_id)
                notice = f"{EMOJI['ok']} Đã học **{result['item']['name']}** · {result['stage']} · Độ thành thạo {result['mastery']}."
            else:
                raise GameError("Thao tác không hợp lệ.")

            self.all_items = self.engine.economy.inventory(self.user_id)
            if not any(item.get("id") == item_id for item in self.all_items):
                self.selected_id = None
            self.page = min(self.page, self.max_page)
            self.rebuild()
            if from_modal and self.message is not None:
                await interaction.response.defer()
                await self.message.edit(embed=self.build_embed(notice), view=self)
            else:
                await interaction.response.edit_message(embed=self.build_embed(notice), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _custom_quantity_callback(self, interaction: discord.Interaction) -> None:
        if not self._guard(interaction):
            await interaction.response.send_message("Túi đồ này không thuộc về bạn.", ephemeral=True)
            return
        if not self.selected:
            await interaction.response.send_message(embed=error_embed("Hãy chọn một vật phẩm trước."), ephemeral=True)
            return
        self.message = interaction.message
        await interaction.response.send_modal(InventoryQuantityModal(self))

    def _page_callback(self, delta: int):
        async def callback(interaction: discord.Interaction) -> None:
            if not self._guard(interaction):
                await interaction.response.send_message("Túi đồ này không thuộc về bạn.", ephemeral=True)
                return
            self.message = interaction.message
            self.page = max(0, min(self.page + delta, self.max_page))
            self.rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        return callback

    async def _refresh_callback(self, interaction: discord.Interaction) -> None:
        if not self._guard(interaction):
            await interaction.response.send_message("Túi đồ này không thuộc về bạn.", ephemeral=True)
            return
        self.message = interaction.message
        self.all_items = self.engine.economy.inventory(self.user_id)
        if self.selected_id and not any(item.get("id") == self.selected_id for item in self.all_items):
            self.selected_id = None
        self.page = min(self.page, self.max_page)
        self.rebuild()
        await interaction.response.edit_message(embed=self.build_embed("Túi đồ đã được làm mới."), view=self)

    async def _close_callback(self, interaction: discord.Interaction) -> None:
        if not self._guard(interaction):
            await interaction.response.send_message("Túi đồ này không thuộc về bạn.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(view=None)
