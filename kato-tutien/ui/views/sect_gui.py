from __future__ import annotations

import discord

from game.services.errors import GameError
from game.utils import fmt_amount
from ui.embeds import base_embed, error_embed, success_embed
from ui.emoji import EMOJI


class SectContributionModal(discord.ui.Modal, title="Cống hiến linh thạch"):
    amount = discord.ui.TextInput(label="Số linh thạch", placeholder="Ví dụ: 1000", min_length=1, max_length=9, required=True)

    def __init__(self, owner: "SectMenuView"):
        super().__init__()
        self.owner = owner

    async def on_submit(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            amount = int(str(self.amount.value).strip())
        except ValueError:
            await interaction.response.send_message(embed=error_embed("Số linh thạch phải là số nguyên."), ephemeral=True)
            return
        try:
            r = self.owner.engine.sect.contribute(self.owner.user_id, amount)
            self.owner._build()
            await interaction.response.edit_message(
                embed=success_embed("🏯 Cống Hiến", f"-{fmt_amount(r['amount'])} {EMOJI['spirit_stone']} · Tổng cống hiến **{fmt_amount(r['contribution'])}**"),
                view=self.owner,
            )
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class SectCreateModal(discord.ui.Modal, title="🏯 Sáng lập Tông Môn"):
    name = discord.ui.TextInput(label="Tên tông môn", placeholder="Nhập tên tông môn", min_length=2, max_length=32, required=True)
    description = discord.ui.TextInput(label="Tông quy", placeholder="Giới thiệu ngắn", max_length=200, required=False, style=discord.TextStyle.paragraph)

    def __init__(self, owner: "SectMenuView"):
        super().__init__()
        self.owner = owner

    async def on_submit(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.owner.engine.sect.create(self.owner.user_id, str(self.name.value), str(self.description.value))
            self.owner._build()
            await interaction.response.edit_message(embed=success_embed("🏯 Sáng lập Tông Môn", f"**{r['sect'].name}** đã được lập. Phí sáng lập: 10.000 {EMOJI['spirit_stone']}."), view=self.owner)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class SectMenuView(discord.ui.View):
    def __init__(self, engine, user_id: str, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = user_id
        self.selected_sect: str | None = None
        self._build()

    def _build(self):
        self.clear_items()
        ov = self.engine.sect.overview(self.user_id)
        if not ov["in_sect"]:
            options = [discord.SelectOption(label=s["name"][:100], value=s["sect_id"], description=f"Cấp {s['level']}", emoji=EMOJI["sect"]) for s in ov["sects"][:25]]
            if options:
                select = discord.ui.Select(placeholder="Chọn tông môn để xem…", options=options, row=0)
                select.callback = self._select_sect
                self.add_item(select)
            create_btn = discord.ui.Button(label="Tạo Tông Môn", style=discord.ButtonStyle.primary, emoji=EMOJI["sect"], row=1)
            create_btn.callback = self._create_modal
            self.add_item(create_btn)
            apply_btn = discord.ui.Button(label="Xin gia nhập", style=discord.ButtonStyle.success, emoji=EMOJI["ok"], row=1, disabled=not self.selected_sect)
            apply_btn.callback = self._apply
            self.add_item(apply_btn)
        else:
            contribute = discord.ui.Button(label="Cống hiến", style=discord.ButtonStyle.success, emoji=EMOJI["spirit_stone"], row=1)
            contribute.callback = self._contribute_modal
            self.add_item(contribute)
            leave = discord.ui.Button(label="Rời tông", style=discord.ButtonStyle.danger, emoji=EMOJI["no"], row=1)
            leave.callback = self._leave
            self.add_item(leave)
            tower = discord.ui.Button(label="Tông Tháp", style=discord.ButtonStyle.primary, emoji="🏯", row=2)
            tower.callback = self._tower
            self.add_item(tower)
            mission = discord.ui.Button(label="Nhiệm vụ Tông Môn", style=discord.ButtonStyle.secondary, emoji="📜", row=2)
            mission.callback = self._mission
            self.add_item(mission)
            lingmai = discord.ui.Button(label="Linh Mạch", style=discord.ButtonStyle.secondary, emoji="🌿", row=2)
            lingmai.callback = self._lingmai
            self.add_item(lingmai)
        back = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji="🏠", row=2)
        back.callback = self._back
        self.add_item(back)

    def build_embed(self) -> discord.Embed:
        ov = self.engine.sect.overview(self.user_id)
        if not ov["in_sect"]:
            lines = [f"{EMOJI['sect']} **{s['name']}** · Cấp {s['level']}" for s in ov["sects"][:12]]
            lines.append("\nChọn một tông môn rồi bấm **Xin gia nhập**.")
            return base_embed(f"{EMOJI['sect']} Tông Môn", "\n".join(lines) or "Chưa có tông môn.")
        s = ov["sect"]
        text = [f"**{s.name}** · Cấp {s.level}", f"Vai trò: **{ov['my_role']}**", f"Khố tông: **{fmt_amount(s.treasury)}** {EMOJI['spirit_stone']}", "", "**Thành viên**"]
        text.extend(f"• <@{m.user_id}> — {m.role} · {fmt_amount(m.contribution)}" for m in ov["members"][:10])
        return base_embed(f"{EMOJI['sect']} Nội Vụ Tông Môn", "\n".join(text))

    async def _select_sect(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.selected_sect = interaction.data["values"][0]
        self._build()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _apply(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.sect.apply(self.user_id, self.selected_sect)
            self._build()
            await interaction.response.edit_message(embed=success_embed("🏯 Đã gửi đơn", f"Tới **{r['sect']['name']}** · mã đơn #{r['application_id']}"), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _contribute_modal(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.send_modal(SectContributionModal(self))

    async def _create_modal(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.send_modal(SectCreateModal(self))

    async def _tower(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.sect_tower.challenge(self.user_id)
            title = "🏯 Tông Tháp"
            text = f"Tầng hiện tại: **{r['floor']}** · Tỷ lệ: **{r['chance']:.0%}**"
            await interaction.response.edit_message(embed=success_embed(title, text) if r['success'] else error_embed(title + " — Thất bại", text), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _mission(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.sect_tower.claim_mission(self.user_id)
            m = r['mission']
            title = "📜 Nhiệm Vụ Tông Môn"
            text = f"{m['name']} · **{r['progress']}/{m['target']}**"
            if r['complete']:
                text += f"\nHoàn thành · +{m['reward_contrib']} cống hiến"
            await interaction.response.edit_message(embed=success_embed(title, text) if r['complete'] else base_embed(title, text), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _lingmai(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            r = self.engine.sect_tower.upgrade_lingmai(self.user_id)
            await interaction.response.edit_message(embed=success_embed("🌿 Linh Mạch", f"Linh Mạch tăng lên **cấp {r['level']}** · -{fmt_amount(r['cost'])} {EMOJI['spirit_stone']}."), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _leave(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        try:
            self.engine.sect.leave(self.user_id)
            self._build()
            await interaction.response.edit_message(embed=success_embed("🏯 Đã rời tông môn", "Con đường phía trước lại do ngươi tự chọn."), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _back(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.gui_navigation import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
