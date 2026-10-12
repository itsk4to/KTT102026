from __future__ import annotations

import discord

from game.services.errors import GameError
from game.utils import fmt_amount
from ui.embeds import base_embed, error_embed, success_embed, progress_bar
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
        claimable = sum(1 for mission in missions if mission["claimable"])
        claimed = sum(1 for mission in missions if mission["claimed"])
        e = base_embed(
            "📜 NHẬT KÝ NHIỆM VỤ",
            "Theo dõi tiến độ hành trình, hoàn thành mục tiêu và tự nhận phần thưởng khi đủ điều kiện.",
        )
        if notice:
            e.add_field(name="🧾 Ghi nhận gần nhất", value=notice[:1024], inline=False)
        e.add_field(
            name="📊 Tổng quan",
            value=f"🎁 Có thể nhận **{claimable}**  ·  ✅ Đã nhận **{claimed}**  ·  📜 Tổng **{len(missions)}**",
            inline=False,
        )
        groups = (
            ("starter", "🌱 NHIỆM VỤ KHỞI HÀNH"),
            ("daily", "☀️ NHIỆM VỤ HẰNG NGÀY"),
            ("weekly", "📅 NHIỆM VỤ HẰNG TUẦN"),
        )
        for group_key, group_label in groups:
            rows = [mission for mission in missions if mission["group"] == group_key]
            if not rows:
                continue
            lines = []
            for mission in rows[:8]:
                target = max(1, int(mission["target"]))
                progress = max(0, min(target, int(mission["progress"])))
                if mission["claimed"]:
                    state = "✅ Đã nhận"
                elif mission["claimable"]:
                    state = "🎁 **Có thể nhận**"
                else:
                    state = f"{progress}/{target}"
                lines.append(
                    f"**{mission['name']}** · {state}\n"
                    f"`{progress_bar(progress, target, 8)}`\n"
                    f"💎 {fmt_amount(mission['stones'])} linh thạch · ✨ {fmt_amount(mission['cultivation'])} tu vi"
                )
            e.add_field(name=group_label, value="\n\n".join(lines)[:1024], inline=False)

        selected = next((mission for mission in missions if mission["id"] == self.selected_id), None)
        if selected:
            target = max(1, int(selected["target"]))
            progress = max(0, min(target, int(selected["progress"])))
            status = "Đã nhận thưởng" if selected["claimed"] else ("Sẵn sàng nhận thưởng" if selected["claimable"] else "Đang thực hiện")
            e.add_field(
                name=f"🔎 Nhiệm vụ đã chọn · {selected['name']}",
                value=(f"{selected['description']}\n\n**Trạng thái:** {status}\n"
                       f"`{progress_bar(progress, target, 12)}` **{progress}/{target}**\n"
                       f"🎁 {fmt_amount(selected['stones'])} linh thạch · {fmt_amount(selected['cultivation'])} tu vi"),
                inline=False,
            )
        e.add_field(
            name="🕰️ Lịch làm mới",
            value="Nhiệm vụ ngày: 00:00 · Nhiệm vụ tuần: thứ Hai · Giờ Việt Nam (UTC+7).",
            inline=False,
        )
        e.set_footer(text="Chọn nhiệm vụ trong danh sách, sau đó nhận thưởng")
        return e

    def _build(self):
        """Mobile-first sứ mệnh ngày / tuần / khởi hành.

        Row 0 — chọn nhiệm vụ
        Row 1 — nhận thưởng · làm mới
        Row 3 — về cốt truyện · trung tâm · khép lại
        """
        self.clear_items()
        missions = self._missions()
        options = []
        for mission in missions[:25]:
            prefix = {"starter": "🌱", "daily": "☀️", "weekly": "📅"}.get(mission["group"], "📜")
            state = (
                "Đã nhận" if mission["claimed"]
                else ("Có thể nhận" if mission["claimable"] else f"{mission['progress']}/{mission['target']}")
            )
            options.append(discord.SelectOption(
                label=f"{prefix} {mission['name']}"[:100],
                value=mission["id"],
                description=f"{state} · {mission['stones']} linh thạch"[:100],
                default=mission["id"] == self.selected_id,
                emoji=EMOJI.get("reward", "🎁") if mission.get("claimable") else EMOJI.get("technique", "📜"),
            ))
        if options:
            select = discord.ui.Select(
                placeholder="Chọn sứ mệnh ngày / tuần…",
                options=options,
                row=0,
            )
            select.callback = self._select
            self.add_item(select)

        selected = next((m for m in missions if m["id"] == self.selected_id), None)

        claim = discord.ui.Button(
            label="Nhận thưởng",
            emoji=EMOJI.get("reward", "✅"),
            style=discord.ButtonStyle.success,
            row=1,
            disabled=not bool(selected and selected["claimable"]),
        )
        claim.callback = self._claim
        self.add_item(claim)

        refresh = discord.ui.Button(
            label="Làm mới",
            emoji=EMOJI.get("refresh", "🔄"),
            style=discord.ButtonStyle.secondary,
            row=1,
        )
        refresh.callback = self._refresh
        self.add_item(refresh)

        back = discord.ui.Button(
            label="Cốt truyện",
            emoji=EMOJI.get("technique", "📚"),
            style=discord.ButtonStyle.secondary,
            row=3,
        )
        back.callback = self._back
        self.add_item(back)

        home = discord.ui.Button(
            label="Trung tâm",
            emoji=EMOJI.get("home", "🏠"),
            style=discord.ButtonStyle.secondary,
            row=3,
        )
        home.callback = self._home
        self.add_item(home)

        close = discord.ui.Button(
            label="Khép lại",
            emoji=EMOJI.get("close", "✖️"),
            style=discord.ButtonStyle.danger,
            row=3,
        )
        close.callback = self._close
        self.add_item(close)

    async def _select(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        self.selected_id = interaction.data["values"][0]
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _claim(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
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
            await interaction.response.edit_message(embed=self.build_embed(f"{EMOJI.get('ok', '✅')} Đã nhận thưởng: " + msg), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _refresh(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _home(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(
            embed=build_main_embed(self.engine, self.user_id),
            view=MainMenuView(self.engine, self.user_id),
        )

    async def _close(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(view=None)

    async def _back(self, interaction: discord.Interaction):

        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        from ui.views.quest_view import QuestMenuView
        view = QuestMenuView(self.engine, self.user_id)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)
