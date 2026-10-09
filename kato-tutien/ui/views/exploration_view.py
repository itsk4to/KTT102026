from ui.emoji import EMOJI
from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.embeds import base_embed, error_embed


class ExplorationChoiceView(discord.ui.View):
    def __init__(self, engine, user_id: str, event: dict, zone: dict, timeout: float = 180):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.event = event
        self.zone = zone
        for choice in event.get("choices", []):
            button = discord.ui.Button(label=choice["label"][:80], style=discord.ButtonStyle.primary)
            button.callback = self._callback(choice["id"])
            self.add_item(button)

    def _callback(self, choice_id: str):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("Không phải cơ duyên của ngươi.", ephemeral=True)
                return
            try:
                r = self.engine.exploration.choose(self.user_id, choice_id)
                lines = [f"**{r['selected']['label']}**", r.get("text", "").strip()]
                if r.get("stones") is not None: lines.append(f"💰 Linh thạch: {r['stones']:+d}")
                if r.get("cultivation") is not None: lines.append(f"✨ Tu vi: {r['cultivation']:+d}")
                if r.get("injury") is not None and r["injury"]: lines.append(f"🩸 Thương thế: +{r['injury']}")
                if r.get("item"): lines.append(f"🎁 Nhận: `{r['item']}`")
                if r.get("insight"): lines.append(f"🧠 Ngộ tính: {r['insight']:+d}")
                if r.get("fate"): lines.append(f"☯️ Mệnh số: {r['fate']:+d}")
                if r.get("discovery"): lines.append("📖 Một phát hiện mới đã được ghi vào nhân sinh.")
                embed = base_embed("🌌 Cơ duyên đã định", "\n".join(x for x in lines if x))
                await interaction.response.edit_message(embed=embed, view=None)
            except GameError as e:
                await interaction.response.send_message(embed=error_embed(str(e)), ephemeral=True)
        return callback

class ExplorationMenuView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.zone_key = None
        self._rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def build_embed(self) -> discord.Embed:
        zones = self.engine.exploration.list_zones()
        current = self.zone_key or next((z["key"] for z in zones if z.get("enabled")), None)
        zone = next((z for z in zones if z["key"] == current), None)
        if not zone:
            return base_embed("🗺️ Khám Phá", "Chưa có khu vực khả dụng.")
        path_label = {"tien": "Tiên đạo", "ma": "Ma đạo", "both": "Tiên / Ma"}.get(zone.get("path", "both"), "Tiên / Ma")
        lines = [
            f"**{zone['name']}**",
            zone["description"],
            f"{EMOJI['cultivator']} Tu vi tối thiểu: **{realm_text(zone['min_realm'], 1)}**",
            f"Con đường: **{path_label}**",
            "",
            "Chọn khu bằng menu, sau đó bấm **Khám phá** để bắt đầu.",
        ]
        return base_embed(f"{EMOJI['explore']} Khám Phá", "\n".join(lines))

    def _rebuild(self):
        self.clear_items()
        self.add_item(ExplorationZoneSelect(self))
        explore = discord.ui.Button(label="Khám phá", style=discord.ButtonStyle.primary, emoji=EMOJI["explore"], row=1)
        explore.callback = self._explore
        self.add_item(explore)
        hunt = discord.ui.Button(label="Săn yêu thú", style=discord.ButtonStyle.danger, emoji=EMOJI["attack"], row=1)
        hunt.callback = self._hunt
        self.add_item(hunt)
        back = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji="🏠", row=1)
        back.callback = self._back
        self.add_item(back)

    async def _explore(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.exploration.explore(self.user_id, self.zone_key)
            if r.get("choice"):
                event = r["event"]
                await interaction.response.edit_message(
                    embed=base_embed(f"🌌 {event.get('title', 'Cơ duyên xuất hiện')}", f"{event.get('text', '')}\n\n*Không phải mọi cơ duyên đều có một đáp án đúng.*"),
                    view=ExplorationChoiceView(self.engine, self.user_id, event, r["zone"]),
                )
                return
            if r.get("combat"):
                await interaction.response.edit_message(embed=combat_embed(r["encounter"], self.engine.players.get(self.user_id)), view=CombatView(self.engine, self.user_id))
                return
            rewards = []
            if "stones" in r:
                rewards.append(f"+{r['stones']} {EMOJI['spirit_stone']}")
            if "cultivation" in r:
                rewards.append(f"+{r['cultivation']} tu vi")
            if r.get("item"):
                item_id = r["item"]
                rewards.append(f"{EMOJI['item']} {ITEMS.get(item_id, {}).get('name', item_id)}")
            if r.get("injury"):
                rewards.append(f"+{r['injury']} thương thế")
            text = r.get("text", "")
            if rewards:
                text += "\n\n**Thu hoạch** · " + " · ".join(rewards)
            await interaction.response.edit_message(embed=base_embed(f"{EMOJI['explore']} {r['zone']['name']}", text), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _hunt(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.exploration.hunt(self.user_id)
            await interaction.response.edit_message(embed=combat_embed(r["encounter"], self.engine.players.get(self.user_id)), view=CombatView(self.engine, self.user_id))
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _back(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))


class ExplorationZoneSelect(discord.ui.Select):
    def __init__(self, owner: ExplorationMenuView):
        self.owner = owner
        zones = owner.engine.exploration.list_zones()
        options = [
            discord.SelectOption(
                label=z["name"][:100],
                value=z["key"],
                description=f"Cần {z['min_realm']} · {z.get('path', 'both')}",
                emoji="🟢" if z.get("enabled") else "🔒",
                default=z["key"] == owner.zone_key,
            )
            for z in zones[:25]
        ]
        super().__init__(placeholder="Chọn khu vực…", min_values=1, max_values=1, options=options, row=0)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.owner.zone_key = self.values[0]
        self.owner._rebuild()
        await interaction.response.edit_message(embed=self.owner.build_embed(), view=self.owner)
