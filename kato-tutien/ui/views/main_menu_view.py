from __future__ import annotations

import discord

from ui.theme.views import ThemedView
from game.services.errors import GameError
from game.content.dao_paths import DAO_PATHS
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, shop_embed, inventory_embed, progress_bar
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
from ui.theme.components import themed_button


class MainMenuView(ThemedView):
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

        # Row 1: primary gameplay destinations.
        primary = (
            ("Nhân vật", "player", "cultivator"),
            ("Túi Càn Khôn", "inventory", "item"),
            ("Tiên Phường", "shop", "shop"),
            ("Khám phá", "explore", "explore"),
            ("Bí cảnh", "secret_realm", "🌌"),
        )
        for label, action, icon_key in primary:
            button = themed_button(
                label, role="primary", emoji=EMOJI.get(icon_key, "•"), row=1,
                callback=self._button_callback(action),
            )
            self.add_item(button)

        # Row 2: progression, community and economy.
        social = (
            ("Nhiệm vụ", "quest", EMOJI["technique"]),
            ("NPC", "npc", "🧑"),
            ("Chợ", "market", "🪙"),
            ("Tông môn", "sect", EMOJI["sect"]),
        )
        for label, action, icon in social:
            self.add_item(themed_button(
                label, role="navigation", emoji=icon, row=2,
                callback=self._button_callback(action),
            ))

        # Row 3: deeper cultivation systems and rankings.
        advanced = (
            ("Đạo", "dao", EMOJI["dao"]),
            ("Đạo lữ", "dao_lu", "💞"),
            ("Thế giới", "world", "🌍"),
            ("Bảng xếp hạng", "leaderboard", "🏆"),
        )
        for label, action, icon in advanced:
            self.add_item(themed_button(
                label, role="navigation", emoji=icon, row=3,
                callback=self._button_callback(action),
            ))

        self.add_item(themed_button(
            "Đóng giao diện", role="danger", emoji=EMOJI["close"], row=4,
            callback=self._close_callback,
        ))

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
            discord.SelectOption(label="Bí cảnh", value="secret_realm", emoji="🌌", description="Tu luyện nhàn rỗi, nhận thưởng sau 3 giờ."),
            discord.SelectOption(label="Nhiệm vụ", value="quest", emoji=EMOJI["technique"], description="Theo dõi và nhận nhiệm vụ."),
            discord.SelectOption(label="NPC", value="npc", emoji="👤", description="Gặp gỡ người trong giang hồ."),
            discord.SelectOption(label="Tông môn", value="sect", emoji=EMOJI["sect"], description="Quản lý và xem tông môn."),
            discord.SelectOption(label="Đạo", value="dao", emoji=EMOJI["dao"], description="Chọn hoặc xem Đạo."),
            discord.SelectOption(label="Đạo lữ", value="dao_lu", emoji="💞", description="Cầu duyên và song tu."),
            discord.SelectOption(label="Thế giới", value="world", emoji="🌍", description="Xem biến động thiên hạ."),
            discord.SelectOption(label="BXH", value="leaderboard", emoji="🏆", description="Xem bảng xếp hạng."),
        ]
        super().__init__(placeholder="Chọn hệ thống…", min_values=1, max_values=1, options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await render_section(interaction, self.owner.engine, self.owner.user_id, self.values[0])


class BackToMainView(ThemedView):
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
    """Premium landing dashboard for the player's primary navigation hub."""
    try:
        p = engine.players.get(user_id)
    except Exception:
        p = None

    if not p:
        embed = base_embed(
            "✦ CỔNG KHAI ĐẠO",
            "Chào mừng đến với **Kato Tu Tiên**.\n\n"
            "*Hãy chọn con đường đầu tiên của ngươi; hành trình tu hành sẽ bắt đầu ngay sau đó.*",
        )
        embed.add_field(
            name="🌱 BƯỚC 01 · CHỌN ĐẠO",
            value="**`.tutien`** · Bước vào Tiên Đạo\n**`.tamuontutien`** · Bước vào Ma Đạo",
            inline=False,
        )
        embed.add_field(
            name="🧭 BƯỚC 02 · MỞ TRUNG TÂM",
            value="Sau khi tạo nhân vật, dùng `.menu` hoặc `.tutien` để mở toàn bộ hệ thống bằng giao diện.",
            inline=False,
        )
        return embed

    realm = realm_text(p.realm_index, p.realm_layer, p.path)
    path_label = (
        f"{EMOJI['faction_tien']} Tiên Đạo"
        if p.path == "tien"
        else f"{EMOJI['faction_ma']} Ma Đạo"
    )
    description = (
        f"**{p.display_name}** · {path_label}\n"
        "*Thiên địa rộng lớn, cơ duyên đang chờ. Chọn một khu vực bên dưới để tiếp tục đạo lộ.*\n\n"
        "**Lệnh nhanh**　`.tu`　·　`.dp`　·　`.tk`　·　`.dl`"
    )
    embed = base_embed("✦ ĐẠO LỘ · TRUNG TÂM HÀNH TRÌNH", description)
    embed.set_author(name=f"KATO TU TIÊN  ·  ĐẠO LỘ CỦA {p.display_name.upper()[:180]}")
    embed.add_field(name="🌌 CẢNH GIỚI", value=f"**{realm}**", inline=True)
    embed.add_field(name="🪙 LINH THẠCH", value=f"**{fmt_amount(p.spirit_stones)}**", inline=True)
    combat_stats = engine.combat.battle_stats(p)
    effective_max_hp = max(1, int(combat_stats.get("max_hp", p.max_hp)))
    displayed_hp = min(max(0, int(p.hp)), effective_max_hp)
    hp_ratio = max(0.0, min(1.0, displayed_hp / effective_max_hp))
    hp_bar = progress_bar(displayed_hp, effective_max_hp, size=8)
    embed.add_field(
        name="❤️ THỂ TRẠNG",
        value=f"{hp_bar} **{hp_ratio:.0%}**\n**{displayed_hp:,} / {effective_max_hp:,} HP**",
        inline=True,
    )
    try:
        preview = engine.cultivation.breakthrough_preview(user_id)
        current = int(preview.get("cultivation", p.cultivation))
        required = max(1, int(preview.get("requirement", max(current, 1))))
        progress_pct = max(0.0, min(1.0, current / required))
        progress_text = (
            f"{progress_bar(current, required, size=14)}\n"
            f"**{fmt_amount(current)} / {fmt_amount(required)}** · {progress_pct:.0%}"
        )
        if preview.get("recovery_remaining", 0) > 0:
            progress_text += f"\n🩹 Đang hồi phục · còn **{preview['recovery_remaining']}s**"
        elif preview.get("ready"):
            progress_text += "\n✨ Đã đủ tu vi để xem điều kiện đột phá."
        embed.add_field(name="🌱 TIẾN ĐỘ TU VI", value=progress_text, inline=False)
    except Exception:
        # Dashboard navigation must remain usable even if preview data is unavailable.
        embed.add_field(name="🌱 TU VI HIỆN TẠI", value=f"**{fmt_amount(p.cultivation)}**", inline=False)
    embed.add_field(
        name="⚔️ CHỈ SỐ CHIẾN ĐẤU",
        value=f"Công　**{int(combat_stats['attack']):,}**\nThủ　**{int(combat_stats['defense']):,}**",
        inline=True,
    )
    embed.add_field(
        name="🌱 THIÊN PHÚ",
        value=f"Căn cơ　**{p.root}**\nNgộ tính　**{p.insight}**",
        inline=True,
    )
    dao_name = DAO_PATHS.get(p.dao_type, {}).get("name", p.dao_type) if p.dao_type else "Chưa khai Đạo"
    embed.add_field(name="☯️ ĐẠO TÂM", value=f"**{dao_name}**", inline=True)
    embed.add_field(
        name="🗺️ ĐI TIẾP NHƯ THẾ NÀO?",
        value=(
            "`Nhân vật` · tu luyện và đột phá　　`Túi Càn Khôn` · vật phẩm\n"
            "`Tiên Phường` · mua sắm　　　　　`Khám phá` · săn yêu thú\n"
            "`Nhiệm vụ` · nhận thưởng　　　　 `Tông môn` · đồng đạo"
        ),
        inline=False,
    )
    return embed


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

        if action == "secret_realm":
            from ui.views.secret_realm_view import SecretRealmView
            view = SecretRealmView(engine, user_id)
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
                    f"**{i}.** {p.display_name} — {realm_text(p.realm_index, p.realm_layer, p.path)}"
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
