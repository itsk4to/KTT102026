from __future__ import annotations

import discord

from ui.theme.views import ThemedView
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


class SectRecruitModal(discord.ui.Modal, title="🏯 Tuyển Thành Viên"):
    target = discord.ui.TextInput(label="Người chơi", placeholder="@người_chơi hoặc User ID", min_length=2, max_length=32, required=True)

    def __init__(self, owner: "SectMenuView"):
        super().__init__()
        self.owner = owner

    async def on_submit(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.owner.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        raw = str(self.target.value).strip()
        target_id = raw.strip("<@!>") if raw.startswith("<@") else raw
        if not target_id.isdigit():
            await interaction.response.send_message(embed=error_embed("Hãy nhập mention hợp lệ hoặc User ID."), ephemeral=True)
            return
        try:
            r = self.owner.engine.sect.invite(self.owner.user_id, target_id)
            try:
                target = interaction.client.get_user(int(target_id)) or await interaction.client.fetch_user(int(target_id))
                from ui.views.sect_management_view import SectInviteNoticeView
                await target.send(
                    embed=SectInviteNoticeView.build_embed(self.owner.engine, r["invitation_id"]),
                    view=SectInviteNoticeView(self.owner.engine, target_id, r["invitation_id"]),
                )
            except (discord.Forbidden, discord.HTTPException):
                self.owner.engine.sect.cancel_invite(self.owner.user_id, r["invitation_id"])
                raise GameError("Không thể gửi DM. Lời mời đã được hủy; hãy bật DM rồi thử lại.")
            self.owner._build()
            await interaction.response.edit_message(
                embed=success_embed("🏯 Tuyển Thành Viên", f"Đã gửi lời mời tới <@{target_id}>."),
                view=self.owner,
            )
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class SectMenuView(ThemedView):
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
            ov_current = self.engine.sect.overview(self.user_id)
            my_role = ov_current.get("my_role")
            can_invite = my_role in {"Tông Chủ", "Phó Tông Chủ", "Trưởng Lão", "Chấp Sự"}
            recruit = discord.ui.Button(label="Tuyển thành viên", style=discord.ButtonStyle.primary, emoji=EMOJI["ok"], row=2, disabled=not can_invite)
            recruit.callback = self._recruit_modal
            self.add_item(recruit)
            inbox = discord.ui.Button(label="Duyệt / Lời mời", style=discord.ButtonStyle.secondary, emoji=EMOJI["item"], row=3)
            inbox.callback = self._inbox
            self.add_item(inbox)
            manage = discord.ui.Button(label="Quản trị thành viên", style=discord.ButtonStyle.secondary, emoji=EMOJI["sect"], row=3)
            manage.callback = self._manage_members
            self.add_item(manage)
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
        text = [f"**{s.name}** · Cấp {s.level}", f"Vai trò: **{ov['my_role']}**", f"Khố tông: **{fmt_amount(s.treasury)}** {EMOJI['spirit_stone']}", f"Đơn xin gia nhập: **{len(ov.get('applications', []))}**", "", "**Thành viên**"]
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

    async def _manage_members(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        from ui.views.sect_member_admin_view import SectMemberAdminView
        view = SectMemberAdminView(self.engine, self.user_id)
        await interaction.response.edit_message(embed=view.build_embed(), view=view)

    async def _inbox(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True); return
        from ui.views.sect_management_view import SectManagementView
        view=SectManagementView(self.engine,self.user_id)
        await interaction.response.edit_message(embed=view.build_embed(),view=view)

    async def _contribute_modal(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.send_modal(SectContributionModal(self))

    async def _recruit_modal(self, interaction: discord.Interaction):
        if str(interaction.user.id) != self.user_id:
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        await interaction.response.send_modal(SectRecruitModal(self))

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
            state = self.engine.sect_tower.mission_state(self.user_id)
            mission = state["mission"]
            progress = int(state["progress"])
            target = int(mission["target"])
            reward = int(mission["reward_contrib"])
            title = "📜 Nhiệm Vụ Tông Môn Hằng Ngày"

            if state["claimed"]:
                text = (
                    f"**Nhiệm vụ:** {mission['name']}\\n"
                    f"**Tiến độ:** {progress}/{target}\\n"
                    "**Trạng thái:** Đã nhận thưởng hôm nay.\\n"
                    f"**Phần thưởng:** {reward} điểm cống hiến và {reward * 2} kinh nghiệm tông môn.\\n"
                    f"**Ngày:** {state['day']}"
                )
                embed = success_embed(title, text)
            elif progress >= target:
                result = self.engine.sect_tower.claim_mission(self.user_id)
                mission = result["mission"]
                text = (
                    f"**Nhiệm vụ:** {mission['name']}\\n"
                    f"**Tiến độ:** {result['progress']}/{mission['target']}\\n"
                    "**Trạng thái:** Hoàn thành và đã nhận thưởng.\\n"
                    f"**Phần thưởng:** +{mission['reward_contrib']} điểm cống hiến, "
                    f"+{mission['reward_contrib'] * 2} kinh nghiệm tông môn.\\n"
                    f"**Ngày:** {state['day']}"
                )
                embed = success_embed(title, text)
            else:
                remaining = target - progress
                if mission.get("name") == "Cúng linh thạch":
                    instruction = f"Cống hiến thêm **{remaining:,} linh thạch** bằng nút **Cống hiến**."
                elif mission.get("name") == "Khám phá 3 lần":
                    instruction = f"Thực hiện thêm **{remaining} lượt khám phá**."
                elif mission.get("name") == "Tu luyện 10 lần":
                    instruction = f"Tu luyện thêm **{remaining} lần**."
                else:
                    instruction = f"Hoàn thành thêm **{remaining}** lượt hoạt động."
                text = (
                    f"**Nhiệm vụ hôm nay:** {mission['name']}\\n"
                    f"**Tiến độ:** `{progress}/{target}`\\n"
                    f"**Cần làm:** {instruction}\\n"
                    f"**Phần thưởng:** {reward} điểm cống hiến và {reward * 2} kinh nghiệm tông môn.\\n"
                    f"**Ngày làm mới:** {state['day']} (theo ngày máy chủ)\\n\\n"
                    "Tiến độ được ghi nhận tự động khi hệ thống xác nhận hoạt động tương ứng."
                )
                embed = base_embed(title, text)

            await interaction.response.edit_message(embed=embed, view=self)
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
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(embed=build_main_embed(self.engine, self.user_id), view=MainMenuView(self.engine, self.user_id))
