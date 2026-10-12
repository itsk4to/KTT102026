from __future__ import annotations

import time
import discord

from ui.theme.views import ThemedView
from game.services.errors import GameError
from ui.embeds import base_embed, error_embed
from ui.emoji import EMOJI


class WorldMenuView(ThemedView):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.selected_key: str | None = None
        self._build()

    def _build(self):
        self.clear_items()
        events = self.engine.world.active()
        if events:
            options = [discord.SelectOption(label=e["event_key"][:100], value=e["event_key"], description=f"{e['progress']}/{e['target']} tiến độ", emoji="🌟") for e in events[:25]]
            select = discord.ui.Select(placeholder="Chọn biến động…", options=options, row=0)
            select.callback = self._select
            self.add_item(select)
        join = discord.ui.Button(label="Góp sức", style=discord.ButtonStyle.success, emoji=EMOJI["ok"], row=1, disabled=not self.selected_key)
        join.callback = self._join
        self.add_item(join)
        refresh = discord.ui.Button(label="Làm mới", style=discord.ButtonStyle.secondary, emoji=EMOJI["refresh"], row=1)
        refresh.callback = self._refresh
        self.add_item(refresh)
        back = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji=EMOJI.get("home", "🏠"), row=1)
        back.callback = self._back
        self.add_item(back)

    def build_embed(self) -> discord.Embed:
        events = self.engine.world.active()
        if not events:
            return base_embed("🌍 BIẾN ĐỘNG THIÊN HẠ", "Thiên địa hiện đang yên tĩnh. Khi có biến động, nơi đây sẽ hiển thị mục tiêu, tiến độ và thời gian còn lại.")
        embed = base_embed("🌍 BIẾN ĐỘNG THIÊN HẠ", "Các sự kiện đang diễn ra trên thế giới. Chọn một biến động rồi bấm **Góp sức** để đóng góp.")
        for event in events[:10]:
            mins = max(0, int((int(event["expires_at"]) - time.time()) // 60))
            target = max(1, int(event["target"]))
            progress = max(0, min(target, int(event["progress"])))
            ratio = progress / target
            filled = round(ratio * 10)
            bar = "▰" * filled + "▱" * (10 - filled)
            embed.add_field(
                name=f"🌟 {event['event_key']}",
                value=(f"`{bar}` **{ratio:.0%}** · {progress}/{target}\n"
                       f"Khu vực: `{event['zone_key']}` · Còn **{mins} phút**"),
                inline=True,
            )
        embed.set_footer(text="Chọn một biến động để góp sức")
        return embed

    async def _select(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        self.selected_key = interaction.data["values"][0]
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _join(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        try:
            r = self.engine.world.contribute(self.user_id, self.selected_key)
            text = f"Đã góp sức cho **{r['event']['name']}**.\n\nTiến độ: **{r['progress']}/{r['target']}**\n+{r['stones']} {EMOJI['spirit_stone']} · +{r['cultivation']} tu vi."
            if r.get("cultivation") != r.get("cultivation_requested"):
                text += "\nTu vi thưởng đã được giới hạn ở ngưỡng tầng hiện tại."
            if r["finished"]:
                text += "\n\n🌟 **Sự kiện thế giới đã kết thúc!**"
            self._build()
            await interaction.response.edit_message(embed=base_embed("🌍 Thế Giới", text), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _refresh(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _back(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
