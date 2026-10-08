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
