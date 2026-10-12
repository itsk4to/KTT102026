from __future__ import annotations

import discord

from game.content.secret_realms import SECRET_REALMS, SECRET_REALM_CYCLE_SECONDS
from game.services.errors import GameError
from game.rules.cultivation_rules import cultivation_requirement, realm_text
from ui.embeds import base_embed, error_embed, progress_bar
from ui.theme.views import ThemedView
from ui.emoji import EMOJI


def _duration(seconds: int) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    return f"{hours:02d}:{minutes:02d}:{seconds:02d}"


class SecretRealmView(ThemedView):
    """A GUI to pick, track, and claim persisted Secret Realm cycles."""

    def __init__(self, engine, user_id: str, timeout: float = 24 * 60 * 60):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.user_id = str(user_id)
        self.realm_key: str | None = None
        self.last_notice: str | None = None
        status = self.engine.secret_realm.status(self.user_id)
        if status.get("session"):
            self.realm_key = status["session"]["realm_key"]
        else:
            unlocked = next((r for r in status["realms"] if r["unlocked"]), None)
            self.realm_key = unlocked["key"] if unlocked else next(iter(SECRET_REALMS))
        self._rebuild()

    def _guard(self, interaction: discord.Interaction) -> bool:
        return str(interaction.user.id) == self.user_id

    def build_embed(self) -> discord.Embed:
        status = self.engine.secret_realm.status(self.user_id)
        session = status["session"]
        if not session:
            embed = base_embed(
                "🌌 BÍ CẢNH TU LUYỆN",
                "Chọn một bí cảnh rồi bắt đầu chu kỳ 3 giờ. Khi đủ thời gian, nhận linh thạch và tu vi tại đây.",
            )
            for realm in status["realms"][:20]:
                unlocked = bool(realm["unlocked"])
                state = "✅ Đã mở" if unlocked else "🔒 Bị khóa"
                if realm["key"] == self.realm_key:
                    state = "🔹 Đang chọn · " + state
                embed.add_field(
                    name=f"{realm['emoji']} {realm['name']} · {state}",
                    value=(f"**Yêu cầu:** {realm['required_realm']} · **Phong cách:** {realm['style']}\n"
                           f"{EMOJI['spirit_stone']} {realm['stones'][0]:,}–{realm['stones'][1]:,} linh thạch\n"
                           f"✨ {realm['cultivation'][0]:,}–{realm['cultivation'][1]:,} tu vi\n"
                           f"*{realm['description']}*"),
                    inline=True,
                )
            embed.add_field(name="⏳ Chu kỳ", value="**03:00:00** mỗi lần nhận thưởng", inline=True)
            embed.add_field(name="📌 Quy tắc", value="Một bí cảnh tại một thời điểm. Rời giữa chu kỳ sẽ mất tiến độ chưa hoàn thành; thời gian bỏ qua không cộng dồn nhiều lượt.", inline=True)
        else:
            realm = status["realm"]
            remaining = int(status["remaining"] or 0)
            elapsed = max(0, SECRET_REALM_CYCLE_SECONDS - remaining)
            percent = min(100, int(elapsed * 100 / SECRET_REALM_CYCLE_SECONDS))
            state_line = (
                "✅ **ĐÃ ĐỦ THỜI GIAN — CÓ THỂ NHẬN THƯỞNG**"
                if status["ready"] else "🧘 Đang hấp thu linh khí..."
            )
            desc = (
                f"{realm['description']}\n\n{state_line}\n\n"
                f"`{_duration(elapsed)}` {progress_bar(elapsed, SECRET_REALM_CYCLE_SECONDS, 14)} "
                f"`{_duration(remaining)}` còn lại\n"
                f"**Tiến độ:** {percent}% · **Chu kỳ:** 3 giờ"
            )
            embed = base_embed(f"{realm['emoji']} {realm['name'].upper()}", desc)
            embed.add_field(
                name="🎁 Thưởng mỗi chu kỳ",
                value=(f"{EMOJI['spirit_stone']} **{realm['stones'][0]:,}–{realm['stones'][1]:,}** linh thạch\n"
                       f"✨ **{realm['cultivation'][0]:,}–{realm['cultivation'][1]:,}** tu vi"),
                inline=True,
            )
            player = status["player"]
            requirement = cultivation_requirement(player.realm_index, player.realm_layer)
            room = max(0, requirement - player.cultivation)
            realm_label = realm_text(player.realm_index, player.realm_layer, player.path)
            embed.add_field(
                name=f"{EMOJI.get('cultivator', '📜')} Hồ sơ đạo hữu",
                value=(f"**Cảnh giới:** {realm_label}\n"
                       f"**Linh thạch:** {player.spirit_stones:,}\n"
                       f"**Tu vi:** {player.cultivation:,}/{requirement:,}"),
                inline=True,
            )
            if room == 0:
                embed.add_field(
                    name="⚠️ Tu vi đã đầy",
                    value="Thưởng tu vi được giới hạn theo tầng hiện tại để không vượt qua đột phá. Hãy đột phá khi đã đủ điều kiện.",
                    inline=False,
                )
            embed.add_field(name="Số chu kỳ đã nhận", value=f"**{session.get('claims', 0)}**", inline=True)
        if self.last_notice:
            embed.add_field(name="📜 Ghi nhận gần nhất", value=self.last_notice[:1024], inline=False)
        embed.set_footer(text="Bí Cảnh · trạng thái lưu qua restart · chu kỳ 3 giờ")
        return embed

    def _rebuild(self) -> None:
        """Mobile-first Bí Cảnh panel.

        Row 0 — chọn bí cảnh
        Row 1 — hành động chính (vào / nhận / rời)
        Row 3 — điều hướng
        """
        self.clear_items()
        self.add_item(SecretRealmSelect(self))
        active = bool(self.engine.secret_realm.status(self.user_id).get("session"))

        # Row 1 — primary actions
        start = discord.ui.Button(
            label="Vào Bí Cảnh",
            style=discord.ButtonStyle.primary,
            emoji=EMOJI.get("secret_realm", "🌌"),
            row=1,
            disabled=active,
        )
        start.callback = self._select_realm
        self.add_item(start)

        claim = discord.ui.Button(
            label="Nhận thưởng",
            style=discord.ButtonStyle.success,
            emoji=EMOJI.get("reward", "🎁"),
            row=1,
            disabled=not active,
        )
        claim.callback = self._claim
        self.add_item(claim)

        leave = discord.ui.Button(
            label="Rời Bí Cảnh",
            style=discord.ButtonStyle.danger,
            emoji=EMOJI.get("flee", "🚪"),
            row=1,
            disabled=not active,
        )
        leave.callback = self._leave
        self.add_item(leave)

        # Row 3 — navigation
        refresh = discord.ui.Button(
            label="Làm mới",
            style=discord.ButtonStyle.secondary,
            emoji=EMOJI.get("refresh", "🔄"),
            row=3,
        )
        refresh.callback = self._refresh
        self.add_item(refresh)

        back = discord.ui.Button(
            label="Trung tâm",
            style=discord.ButtonStyle.secondary,
            emoji=EMOJI.get("home", "🏠"),
            row=3,
        )
        back.callback = self._back
        self.add_item(back)

        close = discord.ui.Button(
            label="Khép lại",
            style=discord.ButtonStyle.danger,
            emoji=EMOJI.get("close", "✖️"),
            row=3,
        )
        close.callback = self._close
        self.add_item(close)

    async def _select_realm(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        try:
            result = self.engine.secret_realm.select(self.user_id, self.realm_key or "")
            self.last_notice = f"Đã bắt đầu **{result['realm']['name']}**. Hãy trở lại sau 3 giờ để nhận thưởng."
            self._rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _claim(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        try:
            result = self.engine.secret_realm.claim(self.user_id)
            self.last_notice = (
                f"**{result['realm']['name']}** · +**{result['stones']:,}** linh thạch · "
                f"+**{result['cultivation']:,}** tu vi. Chu kỳ mới đã bắt đầu."
            )
            if result["clamped_cultivation"]:
                self.last_notice += "\nTu vi nhận được đã giới hạn theo tiến độ cảnh giới hiện tại."
            self._rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _leave(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        try:
            result = self.engine.secret_realm.leave(self.user_id)
            self.last_notice = f"Đã rời **{result['realm']['name']}**. Tiến độ chu kỳ còn {_duration(result['remaining_lost'])} đã bị hủy."
            self.realm_key = next(
                (realm["key"] for realm in self.engine.secret_realm.list_realms(self.user_id) if realm["unlocked"]),
                next(iter(SECRET_REALMS)),
            )
            self._rebuild()
            await interaction.response.edit_message(embed=self.build_embed(), view=self)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    async def _refresh(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        self.last_notice = None
        status = self.engine.secret_realm.status(self.user_id)
        if status.get("session"):
            self.realm_key = status["session"]["realm_key"]
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

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
        from ui.views.main_menu_view import MainMenuView, build_main_embed
        await interaction.response.edit_message(
            embed=build_main_embed(self.engine, self.user_id),
            view=MainMenuView(self.engine, self.user_id),
        )


class SecretRealmSelect(discord.ui.Select):
    def __init__(self, owner: SecretRealmView):
        self.owner = owner
        options = []
        for realm in owner.engine.secret_realm.list_realms(owner.user_id):
            locked = not realm["unlocked"]
            options.append(discord.SelectOption(
                label=realm["name"][:100],
                value=realm["key"],
                description=f"Cần {realm['required_realm']} · {realm['style']}"[:100],
                emoji="🔒" if locked else realm["emoji"],
                default=realm["key"] == owner.realm_key,
            ))
        super().__init__(placeholder="Chọn Bí Cảnh để luyện khí…", min_values=1, max_values=1, options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về đạo hữu.", ephemeral=True)
            return
        current = self.owner.engine.secret_realm.status(self.owner.user_id).get("session")
        if current and self.values[0] != current["realm_key"]:
            await interaction.response.send_message(
                embed=error_embed("Ngươi đang ở một bí cảnh khác. Hãy nhận thưởng khi đủ 3 giờ, hoặc rời bí cảnh hiện tại để đổi nơi; tiến độ chưa hoàn thành sẽ mất."),
                ephemeral=True,
            )
            return
        self.owner.realm_key = self.values[0]
        self.owner.last_notice = f"Đã chọn **{SECRET_REALMS[self.values[0]]['name']}**. Bấm **Bắt đầu / Chọn** để xác nhận; chọn lại cùng bí cảnh không đặt lại giờ."
        self.owner._rebuild()
        await interaction.response.edit_message(embed=self.owner.build_embed(), view=self.owner)
