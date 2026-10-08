from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.embeds import base_embed, error_embed


class QuestOfferView(discord.ui.View):
    def __init__(self, engine, user_id: str, quest_keys: list[str], timeout: float = 120):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        for key in quest_keys[:5]:
            button = discord.ui.Button(label="📜 Nhận nhiệm vụ", style=discord.ButtonStyle.success)
            button.callback = self._callback(key)
            self.add_item(button)

    def _callback(self, quest_key: str):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("Đây không phải lời mời dành cho ngươi.", ephemeral=True)
                return
            try:
                r = self.engine.quests.start(self.user_id, quest_key)
                q = r["quest"]
                await interaction.response.edit_message(
                    embed=base_embed(f"📜 {q['name']}", f"{q['description']}\n\n**Mục tiêu:** {r['step']['label']}"),
                    view=None,
                )
            except GameError as e:
                await interaction.response.send_message(embed=error_embed(str(e)), ephemeral=True)
        return callback


class QuestChoiceView(discord.ui.View):
    def __init__(self, engine, user_id: str, quest_key: str, choices: list[dict], timeout: float = 120):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.quest_key = quest_key
        for choice in choices[:5]:
            button = discord.ui.Button(label=choice["label"][:80], style=discord.ButtonStyle.primary)
            button.callback = self._callback(choice["id"])
            self.add_item(button)

    def _callback(self, choice_id: str):
        async def callback(interaction: discord.Interaction):
            if str(interaction.user.id) != self.user_id:
                await interaction.response.send_message("Đây không phải lựa chọn dành cho ngươi.", ephemeral=True)
                return
            try:
                r = self.engine.quests.choose(self.user_id, self.quest_key, choice_id)
                text = r["choice"].get("effect", {}).get("text", "") or "Quyết định của ngươi đã được ghi vào nhân sinh."
                if r["changes"]:
                    text += "\n\n" + "\n".join(f"• {x}" for x in r["changes"])
                if r["status"]["done"]:
                    text += "\n\n✨ **Nhiệm vụ đã hoàn thành.**"
                else:
                    text += f"\n\n📜 **Mục tiêu tiếp theo:** {r['status']['step']['label']}"
                await interaction.response.edit_message(embed=base_embed(f"📜 {r['quest']['name']}", text), view=None)
            except GameError as e:
                await interaction.response.send_message(embed=error_embed(str(e)), ephemeral=True)
        return callback
