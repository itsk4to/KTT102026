from __future__ import annotations

import discord

from game.services.errors import GameError
from ui.embeds import base_embed, error_embed
from ui.views.quest_view import QuestOfferView, QuestChoiceView


class QuestMenuView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.selected_key: str | None = None
        self._build()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def _build(self):
        self.clear_items()
        active = self.engine.quests.active(self.user_id)
        available = self.engine.quests.list_available(self.user_id)
        combined = []
        seen = set()
        for item in active + available:
            key = item.get("key") or item.get("quest", {}).get("key")
            if key and key not in seen:
                combined.append((key, item))
                seen.add(key)
        if combined:
            options = []
            for key, item in combined[:25]:
                quest = item.get("quest") or item
                active_flag = item.get("row") is not None
                options.append(discord.SelectOption(
                    label=quest["name"][:100],
                    value=key,
                    emoji="📜",
                    description="Đang làm" if active_flag else "Có thể nhận",
                    default=key == self.selected_key,
                ))
            select = discord.ui.Select(placeholder="Chọn nhiệm vụ…", options=options, row=0)
            select.callback = self._select_callback
            self.add_item(select)
        detail = discord.ui.Button(label="Xem chi tiết", style=discord.ButtonStyle.primary, row=1, disabled=not self.selected_key)
        detail.callback = self._detail
        self.add_item(detail)
        back = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji="🏠", row=1)
        back.callback = self._back
        self.add_item(back)

    def build_embed(self) -> discord.Embed:
        active = self.engine.quests.active(self.user_id)
        available = self.engine.quests.list_available(self.user_id)
        lines = []
        if active:
            lines.append("**ĐANG LÀM**")
            lines.extend(f"📜 **{x['quest']['name']}** · {x['step']['label']} · {x['row']['progress']}/{x['step'].get('amount', 1)}" for x in active[:8])
        if available:
            lines.append("\n**CÓ THỂ NHẬN**")
            lines.extend(f"📜 **{x['name']}** · {x['npc']}" for x in available[:8])
        if not lines:
            lines.append("Chưa có nhiệm vụ. Hãy khám phá và gặp NPC.")
        return base_embed("📜 Nhật Ký Nhiệm Vụ", "\n".join(lines))

    async def _select_callback(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.selected_key = interaction.data["values"][0]
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _detail(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.quests.status(self.user_id, self.selected_key)
        except GameError:
            available = self.engine.quests.list_available(self.user_id)
            available_keys = {item.get("key") for item in available}
            if self.selected_key in available_keys:
                await interaction.response.edit_message(
                    embed=base_embed("📜 Nhận Nhiệm Vụ", "Nhiệm vụ này đang chờ ngươi nhận. Bấm nút bên dưới để bắt đầu."),
                    view=QuestOfferView(self.engine, self.user_id, [self.selected_key]),
                )
                return
            raise
        step = r["step"]
        text = f"{r['quest']['description']}\n\n**Mục tiêu:** {step['label']}"
        if step.get("choices"):
            text += "\n\n⚖️ **Đây là một quyết định quan trọng.**"
            await interaction.response.edit_message(embed=base_embed(f"📜 {r['quest']['name']}", text), view=QuestChoiceView(self.engine, self.user_id, self.selected_key, step["choices"]))
            return
        progress = r["row"]["progress"] if r.get("row") else 0
        amount = step.get("amount", 1)
        text += f"\nTiến độ: **{progress}/{amount}**"
        await interaction.response.edit_message(embed=base_embed(f"📜 {r['quest']['name']}", text), view=self)

    async def _back(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.gui_navigation import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
