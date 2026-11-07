"""In-Discord cấu hình máy chủ: role/kênh lao ngục, log… — không cần sửa code."""
from __future__ import annotations

import discord

from ui.theme.views import ThemedView
from ui.embeds import base_embed, error_embed, success_embed
from game.moderation.guild_settings import (
    GuildSettingsRepository,
    KEY_MOD_LOG_CHANNEL_ID,
    KEY_PRISON_ANNOUNCE_CHANNEL_ID,
    KEY_PRISON_CHANNEL_ID,
    KEY_PRISON_ROLE_ID,
    settings_summary,
)
from game.security.permissions import is_owner
import config


def _is_guild_admin(member: discord.Member, guild: discord.Guild) -> bool:
    return (
        member.id == guild.owner_id
        or is_owner(str(member.id))
        or member.guild_permissions.administrator
        or bool({role.id for role in member.roles} & config.MOD_ADMIN_ROLE_IDS)
    )


def build_settings_embed(engine, guild: discord.Guild) -> discord.Embed:
    data = settings_summary(engine.db, guild.id)
    role = guild.get_role(int(data["prison_role_id"])) if data["prison_role_id"] else None
    jail = guild.get_channel(int(data["prison_channel_id"])) if data["prison_channel_id"] else None
    announce = guild.get_channel(int(data["prison_announce_channel_id"])) if data["prison_announce_channel_id"] else None
    mod_log = guild.get_channel(int(data["mod_log_channel_id"])) if data["mod_log_channel_id"] else None

    def _ch(obj) -> str:
        return obj.mention if obj is not None else "*Chưa đặt*"

    def _role(obj) -> str:
        return obj.mention if obj is not None else "*Chưa đặt*"

    body = (
        "Thiết lập **Thiên Đạo / Lao ngục** ngay trong Discord.\n"
        "Chọn role và kênh bên dưới — bot lưu theo máy chủ, không cần sửa file code.\n\n"
        f"**Role tù nhân:** {_role(role)}\n"
        f"**Kênh lao ngục:** {_ch(jail)}\n"
        f"**Kênh thông báo mãn hạn:** {_ch(announce)}\n"
        f"**Kênh nhật ký moderation:** {_ch(mod_log)}\n"
        f"**Cooldown `.kthac`:** {data['prison_cooldown_seconds']}s\n"
        f"**Trần linh thạch lao dịch:** {data['prison_max_required_stones']:,}"
    )
    return base_embed("⚙️ Cấu hình máy chủ · Thiên Đạo", body)


class AdminSettingsView(ThemedView):
    def __init__(self, engine, actor_id: str, guild_id: int, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.engine = engine
        self.actor_id = str(actor_id)
        self.guild_id = int(guild_id)
        self._build()

    def _guard(self, interaction: discord.Interaction) -> bool:
        if str(interaction.user.id) != self.actor_id:
            return False
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            return False
        return _is_guild_admin(interaction.user, interaction.guild)

    def _build(self) -> None:
        self.clear_items()
        self.add_item(_PrisonRoleSelect(self))
        self.add_item(_PrisonChannelSelect(self))
        self.add_item(_AnnounceChannelSelect(self))
        self.add_item(_ModLogChannelSelect(self))
        refresh = discord.ui.Button(label="Làm mới", style=discord.ButtonStyle.secondary, row=4)
        refresh.callback = self._refresh
        self.add_item(refresh)
        close = discord.ui.Button(label="Đóng", style=discord.ButtonStyle.danger, row=4)
        close.callback = self._close
        self.add_item(close)

    async def _refresh(self, interaction: discord.Interaction) -> None:
        if not self._guard(interaction):
            await interaction.response.send_message("Không có quyền.", ephemeral=True)
            return
        assert interaction.guild is not None
        await interaction.response.edit_message(
            embed=build_settings_embed(self.engine, interaction.guild),
            view=self,
        )

    async def _close(self, interaction: discord.Interaction) -> None:
        if not self._guard(interaction):
            await interaction.response.send_message("Không có quyền.", ephemeral=True)
            return
        self.stop()
        await interaction.response.edit_message(view=None)

    def _repo(self) -> GuildSettingsRepository:
        return GuildSettingsRepository(self.engine.db)


class _PrisonRoleSelect(discord.ui.RoleSelect):
    def __init__(self, owner: AdminSettingsView):
        super().__init__(placeholder="Chọn role tù nhân…", min_values=1, max_values=1, row=0)
        self.owner = owner

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Không có quyền cấu hình.", ephemeral=True)
            return
        role = self.values[0]
        self.owner._repo().set(self.owner.guild_id, KEY_PRISON_ROLE_ID, role.id)
        assert interaction.guild is not None
        await interaction.response.edit_message(
            embed=build_settings_embed(self.owner.engine, interaction.guild),
            view=self.owner,
        )
        await interaction.followup.send(
            embed=success_embed("Đã lưu", f"Role tù nhân: {role.mention}"),
            ephemeral=True,
        )


class _PrisonChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, owner: AdminSettingsView):
        super().__init__(
            placeholder="Chọn kênh lao ngục (text)…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=1,
        )
        self.owner = owner

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Không có quyền cấu hình.", ephemeral=True)
            return
        channel = self.values[0]
        self.owner._repo().set(self.owner.guild_id, KEY_PRISON_CHANNEL_ID, channel.id)
        assert interaction.guild is not None
        await interaction.response.edit_message(
            embed=build_settings_embed(self.owner.engine, interaction.guild),
            view=self.owner,
        )
        await interaction.followup.send(
            embed=success_embed("Đã lưu", f"Kênh lao ngục: <#{channel.id}>"),
            ephemeral=True,
        )


class _AnnounceChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, owner: AdminSettingsView):
        super().__init__(
            placeholder="Chọn kênh thông báo mãn hạn…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=2,
        )
        self.owner = owner

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Không có quyền cấu hình.", ephemeral=True)
            return
        channel = self.values[0]
        self.owner._repo().set(self.owner.guild_id, KEY_PRISON_ANNOUNCE_CHANNEL_ID, channel.id)
        assert interaction.guild is not None
        await interaction.response.edit_message(
            embed=build_settings_embed(self.owner.engine, interaction.guild),
            view=self.owner,
        )
        await interaction.followup.send(
            embed=success_embed("Đã lưu", f"Kênh thông báo: <#{channel.id}>"),
            ephemeral=True,
        )


class _ModLogChannelSelect(discord.ui.ChannelSelect):
    def __init__(self, owner: AdminSettingsView):
        super().__init__(
            placeholder="Chọn kênh nhật ký moderation…",
            channel_types=[discord.ChannelType.text],
            min_values=1,
            max_values=1,
            row=3,
        )
        self.owner = owner

    async def callback(self, interaction: discord.Interaction) -> None:
        if not self.owner._guard(interaction):
            await interaction.response.send_message("Không có quyền cấu hình.", ephemeral=True)
            return
        channel = self.values[0]
        self.owner._repo().set(self.owner.guild_id, KEY_MOD_LOG_CHANNEL_ID, channel.id)
        assert interaction.guild is not None
        await interaction.response.edit_message(
            embed=build_settings_embed(self.owner.engine, interaction.guild),
            view=self.owner,
        )
        await interaction.followup.send(
            embed=success_embed("Đã lưu", f"Kênh log: <#{channel.id}>"),
            ephemeral=True,
        )
