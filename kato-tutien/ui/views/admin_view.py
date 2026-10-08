from __future__ import annotations

import discord

from game.engine import GameEngine, GameError
from game.database.schema import SCHEMA_VERSION
from game.version import version_status
from ui.embeds import base_embed, error_embed, success_embed
from ui.emoji import EMOJI


class AdminLoginModal(discord.ui.Modal, title="🔐 Đăng nhập quản trị"):
    password = discord.ui.TextInput(
        label="Mật khẩu quản trị",
        placeholder="Nhập mật khẩu quản trị",
        style=discord.TextStyle.short,
        required=True,
        min_length=1,
        max_length=200,
    )

    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine

    async def on_submit(self, interaction: discord.Interaction) -> None:
        actor_id = str(interaction.user.id)
        if self.engine.admin_auth.too_many_failures(actor_id):
            await interaction.response.send_message(
                embed=error_embed("Thử quá nhiều lần. Hãy chờ vài phút."),
                ephemeral=True,
            )
            return
        if not self.engine.admin.authorize_session(actor_id, str(self.password)):
            await interaction.response.send_message(
                embed=error_embed("Mật khẩu quản trị không đúng."),
                ephemeral=True,
            )
            return
        await interaction.response.send_message(
            embed=base_embed("👑 Quản trị Kato", "Đăng nhập thành công."),
            view=AdminView(self.engine, actor_id),
            ephemeral=True,
        )


class AdminLoginView(discord.ui.View):
    def __init__(self, engine: GameEngine):
        super().__init__(timeout=180)
        self.engine = engine

    @discord.ui.button(label="Đăng nhập quản trị", style=discord.ButtonStyle.primary, emoji="🔐")
    async def login(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        await interaction.response.send_modal(AdminLoginModal(self.engine))


class GrantStonesModal(discord.ui.Modal, title="💎 Cấp Linh Thạch"):
    user_id = discord.ui.TextInput(label="ID người dùng Discord", required=True, max_length=32)
    amount = discord.ui.TextInput(label="Số lượng", required=True, max_length=20)

    def __init__(self, engine: GameEngine):
        super().__init__()
        self.engine = engine

    async def on_submit(self, interaction: discord.Interaction) -> None:
        try:
            amount = int(str(self.amount))
            player = self.engine.admin.grant_stones(
                str(interaction.user.id), str(self.user_id).strip(), amount
            )
            await interaction.response.send_message(
                embed=success_embed(
                    "💎 Đã cấp linh thạch",
                    f"<@{player.user_id}> hiện có **{player.spirit_stones}** {EMOJI['spirit_stone']}.",
                ),
                ephemeral=True,
            )
        except (GameError, ValueError) as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class CreateCodeModal(discord.ui.Modal, title="🎟️ Tạo Mật Lệnh"):
    code = discord.ui.TextInput(label="Mã (để trống = tự sinh)", required=False, max_length=32)
    stones = discord.ui.TextInput(label="Linh thạch", default="0", required=True, max_length=12)
    item_id = discord.ui.TextInput(label="ID vật phẩm (tùy chọn)", required=False, max_length=64)
    qty = discord.ui.TextInput(label="Số vật phẩm", default="0", required=True, max_length=8)
    max_uses = discord.ui.TextInput(label="Số lượt dùng", default="1", required=True, max_length=8)

    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    async def on_submit(self, interaction):
        try:
            r = self.owner.engine.codes.create(self.owner.actor_id, str(self.code.value) or None, int(self.stones.value), str(self.item_id.value) or None, int(self.qty.value), int(self.max_uses.value))
            await interaction.response.send_message(embed=success_embed("🎟️ Đã tạo Mật Lệnh", f"Mã: **`{r['code']}`**\nLinh thạch: **{r['stones']}** · Vật phẩm: **{r['item'] or 'Không'} ×{r['qty']}** · Lượt: **{r['max_uses']}**"), ephemeral=True)
        except (GameError, ValueError) as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class HeavenlyRuleModal(discord.ui.Modal, title="☯️ Nhập Quy Tắc Đại Đạo"):
    key = discord.ui.TextInput(label="Mã quy tắc", placeholder="vd: no_free_breakthrough", required=True, max_length=64)
    rule = discord.ui.TextInput(label="Nội dung quy tắc", placeholder="Nhập luật Đại Đạo…", required=True, max_length=1000, style=discord.TextStyle.paragraph)

    def __init__(self, owner):
        super().__init__()
        self.owner = owner

    async def on_submit(self, interaction):
        try:
            r = self.owner.engine.heavenly_dao.set_rule(self.owner.actor_id, str(self.key.value), str(self.rule.value), True)
            await interaction.response.send_message(embed=success_embed("☯️ Đã ghi Đại Đạo", f"**{r['key']}**\n{r['text']}"), ephemeral=True)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class AdminView(discord.ui.View):
    def __init__(self, engine: GameEngine, actor_id: str):
        super().__init__(timeout=300)
        self.engine = engine
        self.actor_id = actor_id

    def _check(self, interaction: discord.Interaction) -> None:
        if str(interaction.user.id) != self.actor_id:
            raise GameError("Đây không phải phiên Admin của ngươi.")

    @discord.ui.button(label="Tổng quan", style=discord.ButtonStyle.secondary, emoji="📊", row=0)
    async def overview(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            data = self.engine.admin.overview(self.actor_id)
            await interaction.response.edit_message(
                embed=base_embed(
                    "👑 QUẢN TRỊ KATO",
                    f"👤 Người chơi: **{data['players']}**\n"
                    f"🏯 Tông môn: **{data['sects']}**\n"
                    f"🔐 Phiên: **{self.engine.admin_auth.has_session(self.actor_id)}**",
                ),
                view=self,
            )
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Cấp linh thạch", style=discord.ButtonStyle.success, emoji="💎", row=0)
    async def grant(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            self.engine.admin.ensure_access(self.actor_id)
            await interaction.response.send_modal(GrantStonesModal(self.engine))
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Nhật ký", style=discord.ButtonStyle.secondary, emoji="📜", row=1)
    async def audit(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            rows = self.engine.admin.recent_audit(self.actor_id, 10)
            if not rows:
                body = "Chưa có nhật ký nào."
            else:
                body = "\n".join(
                    f"• `{r['action']}` · <@{r['actor_id']}> → {r.get('target_id') or '-'}"
                    for r in rows
                )
            await interaction.response.send_message(embed=base_embed("📜 Nhật ký quản trị", body), ephemeral=True)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Phiên bản", style=discord.ButtonStyle.secondary, emoji="🧩", row=1)
    async def version(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            data = version_status()
            if data["consistent"]:
                state = "✅ Đồng bộ"
            else:
                state = "⚠️ Không đồng bộ"
            body = (
                f"**Đang chạy:** `v{data['version']}`\n"
                f"**pyproject.toml:** `v{data['pyproject_version']}`\n"
                f"**Database schema:** `v{SCHEMA_VERSION}`\n\n"
                f"Trạng thái: **{state}**"
            )
            await interaction.response.send_message(
                embed=base_embed("🧩 Kiểm tra phiên bản", body),
                ephemeral=True,
            )
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Thiên Đạo", style=discord.ButtonStyle.primary, emoji="☯️", row=2)
    async def heavenly(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            rules = self.engine.heavenly_dao.list_rules(self.actor_id)
            body = "\n".join(f"• **{r['rule_key']}** — {r['rule_text']}" for r in rules) or "Chưa có quy tắc Đại Đạo."
            await interaction.response.send_message(embed=base_embed("☯️ Thiên Đạo", body), view=HeavenlyAdminView(self.engine, self.actor_id), ephemeral=True)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Kho Mật Lệnh", style=discord.ButtonStyle.primary, emoji="🎟️", row=2)
    async def codes(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            await interaction.response.send_modal(CreateCodeModal(self))
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)

    @discord.ui.button(label="Đóng", style=discord.ButtonStyle.danger, emoji="✖️", row=3)
    async def close(self, interaction: discord.Interaction, _button: discord.ui.Button) -> None:
        try:
            self._check(interaction)
            self.engine.admin_auth.clear(self.actor_id)
            await interaction.response.edit_message(embed=base_embed("👑 Quản trị", "Đã đóng phiên."), view=None)
        except GameError as exc:
            await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


class HeavenlyAdminView(discord.ui.View):
    def __init__(self, engine, actor_id):
        super().__init__(timeout=180)
        self.engine = engine
        self.actor_id = actor_id

    @discord.ui.button(label="Nhập quy tắc", emoji="☯️", style=discord.ButtonStyle.primary)
    async def add_rule(self, interaction, _button):
        if str(interaction.user.id) != self.actor_id:
            return await interaction.response.send_message("Không phải phiên Admin của ngươi.", ephemeral=True)
        await interaction.response.send_modal(HeavenlyRuleModal(self))

    @discord.ui.button(label="Đóng", emoji="✖️", style=discord.ButtonStyle.danger)
    async def close_rule(self, interaction, _button):
        if str(interaction.user.id) != self.actor_id:
            return await interaction.response.send_message("Không phải phiên Admin của ngươi.", ephemeral=True)
        await interaction.response.edit_message(view=None)
