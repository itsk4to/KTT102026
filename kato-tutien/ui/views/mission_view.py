from __future__ import annotations

import discord

from game.services.errors import GameError
from game.utils import fmt_amount
from ui.embeds import base_embed, error_embed, success_embed
from ui.theme.views import ThemedView
from ui.emoji import EMOJI


class PlayerMissionView(ThemedView):
    """UI for one-time starter, daily and weekly missions."""

    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = str(user_id)
        self.selected_id: str | None = None
        self._build()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def _missions(self) -> list[dict]:
        return self.engine.missions.list_missions(self.user_id)

    def build_embed(self, notice: str = "") -> discord.Embed:
        missions = self._missions()
        lines: list[str] = []
        last_group = None
        for mission in missions:
            if mission["group"] != last_group:
                if lines:
                    lines.append("")
                lines.append(f"**{mission['group_label']}**")
                last_group = mission["group"]
            if mission["claimed"]:
                state = "✅ Đã nhận"
            elif mission["claimable"]:
                state = "🎁 **Có thể nhận**"
            else:
                state = f"📈 {mission['progress']}/{mission['target']}"
            lines.append(
                f"• **{mission['name']}** — {state}\n"
                f"  {mission['description']}\n"
                f"  🎁 {fmt_amount(mission['stones'])} linh thạch · ✨ {fmt_amount(mission['cultivation'])} tu vi"
            )
        if notice:
            lines.insert(0, notice + "\n")
        lines.extend(["", "Chọn nhiệm vụ trong danh sách rồi bấm **Nhận thưởng** khi đủ tiến độ.", "Nhiệm vụ ngày làm mới lúc 00:00; nhiệm vụ tuần làm mới vào thứ Hai (giờ Việt Nam)."])
        embed = base_embed("📜 Nhật Ký Nhiệm Vụ", "\n".join(lines))
        embed.set_footer(text="Tiến độ được tự ghi khi hành động thành công; phần thưởng phải tự nhận.")
        return embed

    def _build(self):
        self.clear_items()
        missions = self._missions()
        options = []
        for mission in missions[:25]:
            prefix = {"starter": "🌱", "daily": "☀️", "weekly": "📅"}.get(mission["group"], "📜")
            state = "Đã nhận" if mission["claimed"] else ("Có thể nhận" if mission["claimable"] else f"{mission['progress']}/{mission['target']}")
            options.append(discord.SelectOption(
                label=f"{prefix} {mission['name']}"[:100],
                value=mission["id"],
                description=f"{state} · {mission['stones']} linh thạch"[:100],
                default=mission["id"] == self.selected_id,
            ))
        if options:
            select = discord.ui.Select(placeholder="Chọn nhiệm vụ muốn xem/nhận…", options=options, row=0)
            select.callback = self._select
            self.add_item(select)
        selected = next((m for m in missions if m["id"] == self.selected_id), None)
        claim = discord.ui.Button(
            label="Nhận thưởng", emoji=EMOJI.get("accept", "✅"), style=discord.ButtonStyle.success,
            row=1, disabled=not bool(selected and selected["claimable"]),
        )
        claim.callback = self._claim
        self.add_item(claim)
        refresh = discord.ui.Button(label="Làm mới", emoji="🔄", style=discord.ButtonStyle.secondary, row=1)
        refresh.callback = self._refresh
        self.add_item(refresh)
        back = discord.ui.Button(label="Về nhiệm vụ cốt truyện", emoji="📚", style=discord.ButtonStyle.secondary, row=1)
        back.callback = self._back
        self.add_item(back)

    async def _select(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.selected_id = interaction.data["values"][0]
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _claim(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        if not self.selected_id:
            await interaction.response.send_message(embed=error_embed("Hãy chọn nhiệm vụ trước."), ephemeral=True)
            return
        try:
            result = self.engine.missions.claim(self.user_id, self.selected_id)
            msg = (
                f"**{result['mission']['name']}**\n"
                f"+{fmt_amount(result['stones'])} linh thạch\n"
                f"+{fmt_amount(result['cultivation'])} tu vi"
            )
            if result["cultivation"] != result["cultivation_requested"]:
                msg += "\nTu vi đã chạm ngưỡng tầng hiện tại; phần dư không vượt qua đột phá."
            self._build()
            await interaction.response.edit_message(embed=self.build_embed("✅ Đã nhận thưởng: " + msg), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _refresh(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _back(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.quest_view import QuestMenuView
        view = QuestMenuView(self.engine, self.user_id)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
