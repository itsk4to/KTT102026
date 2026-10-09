from __future__ import annotations

import discord

from game.content.secret_realms import SECRET_REALMS, SECRET_REALM_CYCLE_SECONDS
from game.services.errors import GameError
from game.rules.cultivation_rules import cultivation_requirement, realm_text
from ui.embeds import base_embed, error_embed, progress_bar
from ui.theme.views import ThemedView


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
            lines = [
                "Chọn một bí cảnh để bắt đầu chu kỳ tu luyện **3 giờ**. Khi đủ thời gian, hãy nhận cả linh thạch và tu vi.",
                "Chỉ có **một bí cảnh đang hoạt động**; đổi nơi giữa chu kỳ sẽ mất tiến độ chưa hoàn thành.",
                "Mỗi lần chỉ nhận **một phần thưởng**; thời gian bỏ qua không cộng dồn thành nhiều phần thưởng.",
                "",
            ]
            for realm in status["realms"]:
                lock = "✅" if realm["unlocked"] else "🔒"
                lines.append(
                    f"{lock} {realm['emoji']} **{realm['name']}** · {realm['style']}\n"
                    f"   Yêu cầu: {realm['required_realm']}\n"
                    f"   💎 {realm['stones'][0]:,}–{realm['stones'][1]:,} linh thạch · "
                    f"✨ {realm['cultivation'][0]:,}–{realm['cultivation'][1]:,} tu vi\n"
                    f"   *{realm['description']}*"
                )
            embed = base_embed("🌌 BÍ CẢNH TU LUYỆN", "\n\n".join(lines))
            embed.add_field(name="Chu kỳ", value="03:00:00", inline=True)
            embed.add_field(name="Trạng thái", value="Chưa chọn bí cảnh", inline=True)
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
            embed = base_embed(f"{realm['emoji']} {realm['name']}", desc)
            embed.add_field(
                name="🎁 Thưởng mỗi chu kỳ",
                value=(f"💎 **{realm['stones'][0]:,}–{realm['stones'][1]:,}** linh thạch\n"
                       f"✨ **{realm['cultivation'][0]:,}–{realm['cultivation'][1]:,}** tu vi"),
                inline=True,
            )
            player = status["player"]
            requirement = cultivation_requirement(player.realm_index, player.realm_layer)
            room = max(0, requirement - player.cultivation)
            realm_label = realm_text(player.realm_index, player.realm_layer, player.path)
            embed.add_field(
                name="📜 Nhân vật",
                value=(f"**Cảnh giới:** {realm_label}\n"
                       f"**Linh thạch:** {player.spirit_stones:,}\n"
                       f"**Tu vi:** {player.cultivation:,}/{requirement:,}"),
                inline=True,
            )
            if room == 0:
                embed.add_field(
                    name="⚠️ Lưu ý tu vi",
                    value="Tu vi hiện tại đã đầy. Thưởng tu vi sẽ được giới hạn để không bỏ qua đột phá; hãy đột phá khi đủ điều kiện.",
                    inline=False,
                )
            embed.add_field(name="Số chu kỳ đã nhận", value=str(session.get("claims", 0)), inline=True)
        if self.last_notice:
            embed.add_field(name="📜 Ghi nhận gần nhất", value=self.last_notice, inline=False)
        embed.set_footer(text="KATO TU TIÊN  •  Thưởng được lưu trong database, không mất khi bot khởi động lại")
        return embed

    def _rebuild(self) -> None:
        self.clear_items()
        self.add_item(SecretRealmSelect(self))
        active = bool(self.engine.secret_realm.status(self.user_id).get("session"))

        start = discord.ui.Button(label="Bắt đầu / Chọn", style=discord.ButtonStyle.primary, emoji="🌌", row=1)
        start.callback = self._select_realm
        self.add_item(start)

        claim = discord.ui.Button(label="Nhận thưởng", style=discord.ButtonStyle.success, emoji="🎁", row=1, disabled=not active)
        claim.callback = self._claim
        self.add_item(claim)

        leave = discord.ui.Button(label="Rời bí cảnh", style=discord.ButtonStyle.danger, emoji="🚪", row=1, disabled=not active)
        leave.callback = self._leave
        self.add_item(leave)

        refresh = discord.ui.Button(label="Làm mới", style=discord.ButtonStyle.secondary, emoji="🔄", row=1)
        refresh.callback = self._refresh
        self.add_item(refresh)

        back = discord.ui.Button(label="Trang chính", style=discord.ButtonStyle.secondary, emoji="🏠", row=2)
        back.callback = self._back
        self.add_item(back)

    async def _select_realm(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
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
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
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
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
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
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
            return
        self.last_notice = None
        status = self.engine.secret_realm.status(self.user_id)
        if status.get("session"):
            self.realm_key = status["session"]["realm_key"]
        self._rebuild()
        await interaction.response.edit_message(embed=self.build_embed(), view=self)

    async def _back(self, interaction: discord.Interaction):
        if not self._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
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
        super().__init__(placeholder="Chọn bí cảnh...", min_values=1, max_values=1, options=options[:25], row=0)

    async def callback(self, interaction: discord.Interaction):
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Giao diện này không thuộc về ngươi.", ephemeral=True)
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
