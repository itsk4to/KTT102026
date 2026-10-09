from __future__ import annotations

import discord

from game.services.errors import GameError
from game.content.dao_paths import DAO_PATHS
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, shop_embed, inventory_embed
from ui.views.inventory_view import InventoryView
from ui.views.shop_view import ShopView
from ui.views.market_view import MarketView
from ui.views.exploration_view import ExplorationMenuView
from ui.views.quest_view import QuestMenuView
from ui.views.npc_view import NPCMenuView
from ui.views.sect_view import SectMenuView
from ui.views.world_view import WorldMenuView
from ui.views.dao_view import DaoMenuView
from ui.views.player_view import PlayerMenuView, build_player_dashboard
from ui.views.dao_lu_view import DaoLuView
from game.rules.cultivation_rules import realm_text
from game.utils import fmt_amount


class MainMenuView(discord.ui.View):
    """Player-facing navigation hub.

    Commands remain the fast path. This view is the discovery path for multi-step systems.
    """

    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.message: discord.Message | None = None
        self._build()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def _build(self) -> None:
        self.clear_items()
        self.add_item(MainMenuSelect(self))

        for row, entries in enumerate((("Nhân vật", "player", "cultivator"), ("Túi", "inventory", "item"), ("Tiên Phường", "shop", "shop"), ("Khám phá", "explore", "explore"))):
            label, action, icon_key = entries
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.primary, emoji=EMOJI.get(icon_key, "•"), row=1 + row // 2)
            button.callback = self._button_callback(action)
            self.add_item(button)

        extras = (("Nhiệm vụ", "quest"), ("NPC", "npc"), ("Chợ", "market"), ("Tông môn", "sect"), ("Đạo", "dao"), ("Đạo lữ", "dao_lu"), ("Thế giới", "world"), ("BXH", "leaderboard"))
        for idx, (label, action) in enumerate(extras):
            button = discord.ui.Button(label=label, style=discord.ButtonStyle.secondary, row=3 if idx < 5 else 4)
            button.callback = self._button_callback(action)
            self.add_item(button)

        close = discord.ui.Button(label="Đóng", style=discord.ButtonStyle.danger, emoji=EMOJI["close"], row=4)
        close.callback = self._close_callback
        self.add_item(close)

    def _button_callback(self, action: str):
        async def callback(interaction: discord.Interaction):
            if not self._guard(interaction):
                await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
                return
            await render_section(interaction, self.engine, self.user_id, action)
        return callback

    async def _close_callback(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(view=None)


class MainMenuSelect(discord.ui.Select):
    def __init__(self, owner: MainMenuView):
        self.owner = owner
        options = [
            discord.SelectOption(label="Nhân vật", value="player", emoji=EMOJI["cultivator"], description="Xem thuộc tính và thao tác nhanh."),
            discord.SelectOption(label="Túi Càn Khôn", value="inventory", emoji=EMOJI["item"], description="Xem và sử dụng vật phẩm."),
            discord.SelectOption(label="Tiên Phường", value="shop", emoji=EMOJI["shop"], description="Xem và mua vật phẩm."),
            discord.SelectOption(label="Khám phá", value="explore", emoji=EMOJI["explore"], description="Chọn khu và bắt đầu hành trình."),
            discord.SelectOption(label="Nhiệm vụ", value="quest", emoji=EMOJI["technique"], description="Theo dõi và nhận nhiệm vụ."),
            discord.SelectOption(label="NPC", value="npc", emoji="👤", description="Gặp gỡ người trong giang hồ."),
            discord.SelectOption(label="Tông môn", value="sect", emoji=EMOJI["sect"], description="Quản lý và xem tông môn."),
            discord.SelectOption(label="Đạo", value="dao", emoji=EMOJI["dao"], description="Chọn hoặc xem Đạo."),
            discord.SelectOption(label="Đạo lữ", value="dao_lu", emoji="💞", description="Cầu duyên và song tu."),
            discord.SelectOption(label="Thế giới", value="world", emoji="🌍", description="Xem biến động thiên hạ."),
            discord.SelectOption(label="BXH", value="leaderboard", emoji="🏆", description="Xem bảng xếp hạng."),
        ]
        super().__init__(placeholder="Chọn hệ thống…", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await render_section(interaction, self.owner.engine, self.owner.user_id, self.values[0])


class BackToMainView(discord.ui.View):
    def __init__(self, engine, user_id: str, child_view: discord.ui.View | None = None, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.child_view = child_view
        button = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji="🏠")
        button.callback = self._callback
        self.add_item(button)

    async def _callback(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.edit_message(
            embed=build_main_embed(self.engine, self.user_id),
            view=MainMenuView(self.engine, self.user_id),
        )


def build_main_embed(engine, user_id: str) -> discord.Embed:
    try:
        p = engine.players.get(user_id)
    except Exception:
        p = None
    if not p:
        return base_embed("🧭 Kato Tu Tiên", "Hãy mở `.tutien` và chọn **Tu Tiên** hoặc **Tu Ma** bằng nút.")
    realm = realm_text(p.realm_index, p.realm_layer)
    lines = [
        f"{EMOJI['cultivator']} **{p.display_name}**",
        f"Cảnh giới: **{realm}**",
        f"{EMOJI['spirit_stone']} Linh thạch: **{fmt_amount(p.spirit_stones)}**",
        "",
        "Chọn một hệ thống bên dưới để thao tác bằng menu và nút.",
        "",
        "**Lệnh nhanh** · `.tu` · `.dp` · `.tk` · `.dl`",
    ]
    if p.dao_type:
        lines.append(f"Đạo: **{DAO_PATHS[p.dao_type]['name']}**")
    return base_embed("🧭 Đạo Lộ — Trung Tâm", "\n".join(lines))


async def render_section(interaction: discord.Interaction, engine, user_id: str, action: str) -> None:
    try:
        if action != "leaderboard" and not engine.players.exists(user_id):
            from ui.views.start_path_view import PathChoiceView
            await interaction.response.edit_message(
                embed=base_embed(
                    "🌱 Hãy Khai Đạo Trước",
                    "Ngươi chưa tạo nhân vật. Chọn phe bằng nút bên dưới, hoặc nhập `.tutien` / `.tamuontutien`."
                ),
                view=PathChoiceView(engine, user_id, "Đạo hữu"),
            )
            return

        if action == "player":
            view = PlayerMenuView(engine, user_id)
            await interaction.response.edit_message(embed=build_player_dashboard(engine, user_id), view=view)
            return

        if action == "inventory":
            items = engine.economy.inventory(user_id)
            view = InventoryView(engine, user_id, items)
            await interaction.response.edit_message(embed=inventory_embed(items), view=view)
            return

        if action == "shop":
            catalog = engine.economy.shop_catalog()
            await interaction.response.edit_message(embed=shop_embed(catalog), view=ShopView(engine, catalog, user_id))
            return

        if action == "market":
            view = MarketView(engine, user_id)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            return

        if action == "explore":
            view = ExplorationMenuView(engine, user_id)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            return

        if action == "quest":
            view = QuestMenuView(engine, user_id)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            return

        if action == "npc":
            view = NPCMenuView(engine, user_id)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            return

        if action == "sect":
            view = SectMenuView(engine, user_id)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            return

        if action == "dao":
            view = DaoMenuView(engine, user_id)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            return

        if action == "dao_lu":
            view = DaoLuView(engine, user_id)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            return

        if action == "world":
            view = WorldMenuView(engine, user_id)
            await interaction.response.edit_message(embed=view.build_embed(), view=view)
            return

        if action == "leaderboard":
            def ranking(path: str) -> str:
                rows = engine.players.leaderboard(10, path)
                return "\n".join(
                    f"**{i}.** {p.display_name} — {realm_text(p.realm_index, p.realm_layer)}"
                    for i, p in enumerate(rows, 1)
                ) or "Chưa có người chơi."
            embed = base_embed("🏆 Bảng Xếp Hạng Hai Phe", "Dùng `.bxh tien` hoặc `.bxh ma` để xem riêng từng phe.")
            embed.add_field(name="🧘 Tu Tiên", value=ranking("tien"), inline=True)
            embed.add_field(name="👹 Tu Ma", value=ranking("ma"), inline=True)
            await interaction.response.edit_message(embed=embed, view=BackToMainView(engine, user_id))
            return

        raise GameError("Giao diện không tồn tại.")
    except GameError as exc:
        await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)
