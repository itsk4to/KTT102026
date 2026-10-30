"""Manual Discord server moderation slash commands.

Registered as ``/mod ...`` on the existing app_commands.CommandTree. This
module intentionally contains no automatic message scanning or auto-punishment.
"""
from __future__ import annotations

import json
import logging
import time
from datetime import timedelta
from typing import Any

import discord
from discord import app_commands

import config
from game.moderation.service import ModerationService
from game.security.permissions import is_owner

logger = logging.getLogger("kato.moderation")


class ModerationGroup(app_commands.Group):
    def __init__(self, service: ModerationService):
        super().__init__(
            name="mod",
            description="Công cụ quản lý thủ công máy chủ Kato",
            guild_only=True,
        )
        self.service = service

    @staticmethod
    def _role_ids(member: discord.Member) -> set[int]:
        return {role.id for role in member.roles}

    @classmethod
    def _is_admin(cls, member: discord.Member, guild: discord.Guild) -> bool:
        return (
            member.id == guild.owner_id
            or is_owner(str(member.id))
            or member.guild_permissions.administrator
            or bool(cls._role_ids(member) & config.MOD_ADMIN_ROLE_IDS)
        )

    @classmethod
    def _is_moderator(cls, member: discord.Member, guild: discord.Guild) -> bool:
        if cls._is_admin(member, guild):
            return True
        if cls._role_ids(member) & config.MODERATOR_ROLE_IDS:
            return True
        # Native Discord moderation permissions are a safe fallback when role
        # IDs have not yet been configured in the host environment.
        perms = member.guild_permissions
        return any(
            (
                perms.moderate_members,
                perms.manage_messages,
                perms.kick_members,
                perms.ban_members,
                perms.manage_channels,
            )
        )

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.guild is None or not isinstance(interaction.user, discord.Member):
            await interaction.response.send_message(
                "Lệnh quản trị chỉ dùng được trong máy chủ Discord.", ephemeral=True
            )
            return False
        if not self._is_moderator(interaction.user, interaction.guild):
            await interaction.response.send_message(
                "Ngươi không có quyền Moderator/Admin để dùng nhóm lệnh này.",
                ephemeral=True,
            )
            return False
        return True

    async def on_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        original = getattr(error, "original", error)
        if isinstance(original, app_commands.AppCommandError):
            message = str(original) or "Không thể thực hiện lệnh quản trị này."
        elif isinstance(original, discord.Forbidden):
            message = "Discord từ chối thao tác. Hãy kiểm tra quyền của bot và thứ tự role."
        elif isinstance(original, discord.HTTPException):
            message = "Discord API gặp lỗi khi thực hiện thao tác. Chưa thể xác nhận thay đổi."
        else:
            logger.error(
                "Unhandled moderation command error",
                exc_info=(type(original), original, original.__traceback__),
            )
            message = "Lỗi hệ thống khi xử lý lệnh. Hãy kiểm tra log của bot."

        try:
            if interaction.response.is_done():
                await interaction.followup.send(message, ephemeral=True)
            else:
                await interaction.response.send_message(message, ephemeral=True)
        except discord.HTTPException:
            logger.exception("Could not send moderation error response")

    @staticmethod
    def _reason(reason: str | None) -> str:
        value = (reason or "Không nêu lý do").strip()
        return value[:500] or "Không nêu lý do"

    @staticmethod
    def _actor(interaction: discord.Interaction) -> discord.Member:
        # interaction_check has already validated this, but retain a defensive
        # runtime guard because command callbacks can be invoked in tests.
        if not isinstance(interaction.user, discord.Member):
            raise app_commands.AppCommandError("Không xác định được thành viên thực hiện lệnh.")
        return interaction.user

    @staticmethod
    def _guild(interaction: discord.Interaction) -> discord.Guild:
        if interaction.guild is None:
            raise app_commands.AppCommandError("Lệnh này chỉ dùng trong máy chủ.")
        return interaction.guild

    def _check_target(self, interaction: discord.Interaction, target: discord.Member) -> None:
        guild = self._guild(interaction)
        actor = self._actor(interaction)
        if target.id == actor.id:
            raise app_commands.AppCommandError("Không thể tự xử lý tài khoản của mình.")
        if target.id == guild.owner_id:
            raise app_commands.AppCommandError("Không thể xử lý chủ sở hữu máy chủ.")
        if actor.id != guild.owner_id and target.top_role >= actor.top_role:
            raise app_commands.AppCommandError(
                "Không thể xử lý thành viên có role ngang hoặc cao hơn role của ngươi."
            )
        bot_member = guild.me
        if bot_member is not None and target.top_role >= bot_member.top_role:
            raise app_commands.AppCommandError(
                "Role cao nhất của bot phải nằm trên role của thành viên mục tiêu."
            )

    def _check_actor_permissions(
        self, interaction: discord.Interaction, *permissions: str
    ) -> None:
        guild = self._guild(interaction)
        actor = self._actor(interaction)
        if self._is_admin(actor, guild) or self._role_ids(actor) & config.MODERATOR_ROLE_IDS:
            return
        actor_permissions = actor.guild_permissions
        if any(getattr(actor_permissions, permission, False) for permission in permissions):
            return
        names = " / ".join(permissions)
        raise app_commands.AppCommandError(
            f"Ngươi cần role Moderator hoặc quyền Discord phù hợp ({names})."
        )

    @staticmethod
    def _check_bot_permission(interaction: discord.Interaction, permission: str) -> None:
        permissions = interaction.app_permissions
        if not getattr(permissions, permission, False):
            raise app_commands.AppCommandError(
                f"Bot đang thiếu quyền Discord `{permission}` trong máy chủ này."
            )

    @staticmethod
    def _check_channel_bot_permission(
        channel: discord.TextChannel, permission: str
    ) -> None:
        bot_member = channel.guild.me
        permissions = channel.permissions_for(bot_member) if bot_member else None
        if permissions is None or not getattr(permissions, permission, False):
            raise app_commands.AppCommandError(
                f"Bot đang thiếu quyền Discord `{permission}` tại kênh {channel.mention}."
            )

    def _record(
        self,
        interaction: discord.Interaction,
        *,
        action: str,
        target_id: int | str,
        target_type: str,
        reason: str,
        expires_at: int | None = None,
        details: str = "",
    ) -> dict[str, Any]:
        guild = self._guild(interaction)
        actor = self._actor(interaction)
        return self.service.record_action(
            guild_id=str(guild.id),
            moderator_id=str(actor.id),
            target_id=str(target_id),
            target_type=target_type,
            action=action,
            reason=reason,
            expires_at=expires_at,
            details=details,
        )

    async def _post_log(self, interaction: discord.Interaction, case: dict[str, Any]) -> None:
        channel_id = config.MOD_LOG_CHANNEL_ID
        if not channel_id:
            return
        client = interaction.client
        channel = client.get_channel(channel_id)
        if channel is None:
            try:
                channel = await client.fetch_channel(channel_id)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                logger.warning("Cannot fetch moderation log channel %s", channel_id)
                return
        if getattr(channel, "guild", None) is None or channel.guild.id != interaction.guild_id:
            logger.warning("Configured moderation log channel %s is not in guild %s", channel_id, interaction.guild_id)
            return
        try:
            embed = discord.Embed(
                title=f"🛡️ Moderation Case #{case['case_id']}",
                color=discord.Color.blurple(),
                timestamp=discord.utils.utcnow(),
            )
            embed.add_field(name="Hành động", value=str(case["action"]).upper(), inline=True)
            embed.add_field(name="Đối tượng", value=f"{case['target_type']} · `{case['target_id']}`", inline=True)
            embed.add_field(name="Người thực hiện", value=f"<@{case['moderator_id']}>", inline=True)
            embed.add_field(name="Lý do", value=str(case["reason"])[:1024], inline=False)
            if case.get("expires_at"):
                embed.add_field(name="Hết hạn", value=f"<t:{int(case['expires_at'])}:F>", inline=True)
            if case.get("details"):
                embed.add_field(name="Chi tiết", value=str(case["details"])[:1024], inline=False)
            await channel.send(embed=embed, allowed_mentions=discord.AllowedMentions.none())
        except (discord.Forbidden, discord.NotFound, discord.HTTPException, AttributeError):
            logger.exception("Failed to send moderation case #%s to log channel", case["case_id"])

    async def _complete(
        self,
        interaction: discord.Interaction,
        *,
        action: str,
        target_id: int | str,
        target_type: str,
        reason: str,
        message: str,
        expires_at: int | None = None,
        details: str = "",
    ) -> None:
        case = self._record(
            interaction,
            action=action,
            target_id=target_id,
            target_type=target_type,
            reason=reason,
            expires_at=expires_at,
            details=details,
        )
        await interaction.response.send_message(
            f"{message}\nMã xử lý: **#{case['case_id']}**", ephemeral=True
        )
        await self._post_log(interaction, case)

    @app_commands.command(name="ban", description="Cấm một thành viên khỏi máy chủ")
    @app_commands.describe(member="Thành viên cần ban", reason="Lý do xử lý")
    async def ban(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Không nêu lý do",
    ) -> None:
        self._check_actor_permissions(interaction, "ban_members")
        self._check_target(interaction, member)
        self._check_bot_permission(interaction, "ban_members")
        reason = self._reason(reason)
        await member.ban(reason=f"Kato Mod | {reason}")
        await self._complete(
            interaction,
            action="ban",
            target_id=member.id,
            target_type="user",
            reason=reason,
            message=f"Đã ban {member.mention} khỏi máy chủ.",
        )

    @app_commands.command(name="unban", description="Gỡ ban theo Discord User ID")
    @app_commands.describe(user_id="Discord User ID của người cần gỡ ban", reason="Lý do gỡ ban")
    async def unban(
        self,
        interaction: discord.Interaction,
        user_id: str,
        reason: str = "Không nêu lý do",
    ) -> None:
        guild = self._guild(interaction)
        self._check_actor_permissions(interaction, "ban_members")
        self._check_bot_permission(interaction, "ban_members")
        if not user_id.isdigit() or len(user_id) < 15 or len(user_id) > 22:
            await interaction.response.send_message("Discord User ID không hợp lệ.", ephemeral=True)
            return
        reason = self._reason(reason)
        try:
            entry = await guild.fetch_ban(discord.Object(id=int(user_id)))
        except discord.NotFound:
            await interaction.response.send_message("Không tìm thấy lệnh ban cho User ID này.", ephemeral=True)
            return
        await guild.unban(entry.user, reason=f"Kato Mod | {reason}")
        await self._complete(
            interaction,
            action="unban",
            target_id=user_id,
            target_type="user",
            reason=reason,
            message=f"Đã gỡ ban cho `{user_id}`.",
        )

    @app_commands.command(name="kick", description="Mời một thành viên rời máy chủ")
    @app_commands.describe(member="Thành viên cần kick", reason="Lý do xử lý")
    async def kick(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Không nêu lý do",
    ) -> None:
        self._check_actor_permissions(interaction, "kick_members")
        self._check_target(interaction, member)
        self._check_bot_permission(interaction, "kick_members")
        reason = self._reason(reason)
        await member.kick(reason=f"Kato Mod | {reason}")
        await self._complete(
            interaction,
            action="kick",
            target_id=member.id,
            target_type="user",
            reason=reason,
            message=f"Đã kick {member.mention} khỏi máy chủ.",
        )

    @app_commands.command(name="timeout", description="Tạm hạn chế một thành viên")
    @app_commands.describe(member="Thành viên cần timeout", duration_minutes="Thời lượng từ 1 đến 40320 phút", reason="Lý do xử lý")
    async def timeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        duration_minutes: app_commands.Range[int, 1, 40320],
        reason: str = "Không nêu lý do",
    ) -> None:
        self._check_actor_permissions(interaction, "moderate_members")
        self._check_target(interaction, member)
        self._check_bot_permission(interaction, "moderate_members")
        reason = self._reason(reason)
        expires_at = int(time.time()) + int(duration_minutes) * 60
        await member.timeout(timedelta(minutes=int(duration_minutes)), reason=f"Kato Mod | {reason}")
        await self._complete(
            interaction,
            action="timeout",
            target_id=member.id,
            target_type="user",
            reason=reason,
            expires_at=expires_at,
            message=f"Đã timeout {member.mention} trong **{int(duration_minutes)} phút**.",
        )

    @app_commands.command(name="untimeout", description="Gỡ timeout cho một thành viên")
    @app_commands.describe(member="Thành viên cần gỡ timeout", reason="Lý do gỡ timeout")
    async def untimeout(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str = "Không nêu lý do",
    ) -> None:
        self._check_actor_permissions(interaction, "moderate_members")
        self._check_target(interaction, member)
        self._check_bot_permission(interaction, "moderate_members")
        reason = self._reason(reason)
        await member.timeout(None, reason=f"Kato Mod | {reason}")
        await self._complete(
            interaction,
            action="untimeout",
            target_id=member.id,
            target_type="user",
            reason=reason,
            message=f"Đã gỡ timeout cho {member.mention}.",
        )

    @app_commands.command(name="warn", description="Ghi nhận cảnh cáo cho thành viên")
    @app_commands.describe(member="Thành viên nhận cảnh cáo", reason="Lý do cảnh cáo")
    async def warn(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        reason: str,
    ) -> None:
        self._check_actor_permissions(
            interaction, "moderate_members", "manage_messages", "kick_members", "ban_members"
        )
        self._check_target(interaction, member)
        reason = self._reason(reason)
        count = self.service.count_warnings(str(interaction.guild_id), str(member.id)) + 1
        await self._complete(
            interaction,
            action="warn",
            target_id=member.id,
            target_type="user",
            reason=reason,
            message=f"Đã ghi cảnh cáo cho {member.mention}. Tổng cảnh cáo được lưu: **{count}**.",
        )

    @app_commands.command(name="warnings", description="Xem lịch sử cảnh cáo của thành viên")
    @app_commands.describe(member="Thành viên cần tra cứu")
    async def warnings(self, interaction: discord.Interaction, member: discord.Member) -> None:
        self._check_actor_permissions(
            interaction, "moderate_members", "manage_messages", "kick_members", "ban_members"
        )
        rows = self.service.list_warnings(str(interaction.guild_id), str(member.id), limit=10)
        total = self.service.count_warnings(str(interaction.guild_id), str(member.id))
        if not rows:
            body = f"{member.mention} hiện chưa có cảnh cáo nào được ghi nhận."
        else:
            body = "\n".join(
                f"`#{row['case_id']}` · <t:{row['created_at']}:d> · {str(row['reason'])[:180]}"
                for row in rows
            )
            body += f"\n\nTổng số cảnh cáo: **{total}** · Hiển thị tối đa 10 mục gần nhất."
        await interaction.response.send_message(body, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())

    @app_commands.command(name="purge", description="Xóa tối đa 100 tin nhắn trong một kênh")
    @app_commands.describe(channel="Kênh cần dọn", amount="Số tin nhắn từ 1 đến 100", reason="Lý do dọn kênh")
    async def purge(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        amount: app_commands.Range[int, 1, 100],
        reason: str = "Dọn dẹp kênh",
    ) -> None:
        self._check_actor_permissions(interaction, "manage_messages")
        if channel.guild.id != interaction.guild_id:
            await interaction.response.send_message("Kênh không thuộc máy chủ này.", ephemeral=True)
            return
        self._check_channel_bot_permission(channel, "manage_messages")
        reason = self._reason(reason)
        await interaction.response.defer(ephemeral=True, thinking=True)
        deleted = await channel.purge(limit=int(amount), reason=f"Kato Mod | {reason}")
        case = self._record(
            interaction,
            action="purge",
            target_id=channel.id,
            target_type="channel",
            reason=reason,
            details=f"Đã xóa {len(deleted)} tin nhắn (giới hạn yêu cầu: {int(amount)}).",
        )
        await interaction.followup.send(
            f"Đã xóa **{len(deleted)}** tin nhắn tại {channel.mention}. Mã xử lý: **#{case['case_id']}**",
            ephemeral=True,
        )
        await self._post_log(interaction, case)

    @app_commands.command(name="slowmode", description="Đặt tốc độ gửi tin nhắn cho một kênh")
    @app_commands.describe(channel="Kênh cần chỉnh", seconds="0 để tắt, tối đa 21600 giây")
    async def slowmode(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        seconds: app_commands.Range[int, 0, 21600],
        reason: str = "Điều chỉnh slowmode",
    ) -> None:
        self._check_actor_permissions(interaction, "manage_channels")
        if channel.guild.id != interaction.guild_id:
            await interaction.response.send_message("Kênh không thuộc máy chủ này.", ephemeral=True)
            return
        self._check_channel_bot_permission(channel, "manage_channels")
        reason = self._reason(reason)
        await channel.edit(slowmode_delay=int(seconds), reason=f"Kato Mod | {reason}")
        state = "đã tắt" if int(seconds) == 0 else f"đặt thành **{int(seconds)} giây**"
        await self._complete(
            interaction,
            action="slowmode",
            target_id=channel.id,
            target_type="channel",
            reason=reason,
            details=f"Slowmode {state}.",
            message=f"Slowmode tại {channel.mention} {state}.",
        )

    @app_commands.command(name="lock", description="Khóa quyền gửi tin nhắn của @everyone tại một kênh")
    @app_commands.describe(channel="Kênh cần khóa", reason="Lý do khóa kênh")
    async def lock(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        reason: str = "Khóa kênh theo yêu cầu quản trị",
    ) -> None:
        self._check_actor_permissions(interaction, "manage_channels")
        if channel.guild.id != interaction.guild_id:
            await interaction.response.send_message("Kênh không thuộc máy chủ này.", ephemeral=True)
            return
        self._check_channel_bot_permission(channel, "manage_channels")
        reason = self._reason(reason)
        latest_lock_event = self.service.latest_channel_lock_event(
            str(interaction.guild_id), str(channel.id)
        )
        latest_lock_state = latest_lock_event["action"] if latest_lock_event else None
        if latest_lock_state == "lock":
            await interaction.response.send_message(
                f"{channel.mention} đã có case khóa đang hoạt động. Dùng `/mod unlock` trước khi khóa lại.",
                ephemeral=True,
            )
            return

        overwrite = channel.overwrites_for(channel.guild.default_role)
        previous_send_messages = overwrite.send_messages
        await channel.set_permissions(
            channel.guild.default_role,
            send_messages=False,
            reason=f"Kato Mod | {reason}",
        )
        lock_state = json.dumps(
            {"previous_send_messages": previous_send_messages},
            separators=(",", ":"),
        )
        await self._complete(
            interaction,
            action="lock",
            target_id=channel.id,
            target_type="channel",
            reason=reason,
            details=lock_state,
            message=f"Đã khóa quyền gửi tin nhắn của @everyone tại {channel.mention}.",
        )

    @app_commands.command(name="unlock", description="Gỡ ghi đè khóa của @everyone tại một kênh")
    @app_commands.describe(channel="Kênh cần mở khóa", reason="Lý do mở khóa")
    async def unlock(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel,
        reason: str = "Mở khóa kênh theo yêu cầu quản trị",
    ) -> None:
        self._check_actor_permissions(interaction, "manage_channels")
        if channel.guild.id != interaction.guild_id:
            await interaction.response.send_message("Kênh không thuộc máy chủ này.", ephemeral=True)
            return
        self._check_channel_bot_permission(channel, "manage_channels")
        reason = self._reason(reason)
        active_lock = self.service.latest_channel_lock_event(
            str(interaction.guild_id), str(channel.id)
        )
        if active_lock is None or active_lock["action"] != "lock":
            await interaction.response.send_message(
                f"Không tìm thấy case khóa đang hoạt động cho {channel.mention}. Không thay đổi quyền để tránh mở nhầm kênh.",
                ephemeral=True,
            )
            return
        try:
            previous_state = json.loads(active_lock.get("details") or "{}")
            restore_value = previous_state["previous_send_messages"]
            if restore_value not in (None, True, False):
                raise ValueError("Invalid previous permission value")
        except (ValueError, TypeError, KeyError, json.JSONDecodeError):
            await interaction.response.send_message(
                "Không đọc được quyền trước khi khóa từ case lưu trữ. Hãy kiểm tra quyền kênh thủ công; bot không tự mở kênh.",
                ephemeral=True,
            )
            return

        await channel.set_permissions(
            channel.guild.default_role,
            send_messages=restore_value,
            reason=f"Kato Mod | {reason}",
        )
        await self._complete(
            interaction,
            action="unlock",
            target_id=channel.id,
            target_type="channel",
            reason=reason,
            details=f"Khôi phục send_messages về trạng thái trước case #{active_lock['case_id']}: {restore_value!r}.",
            message=f"Đã khôi phục quyền gửi tin của @everyone tại {channel.mention} về trạng thái trước khi khóa.",
        )

    @app_commands.command(name="logs", description="Xem các case xử lý gần đây trong máy chủ")
    @app_commands.describe(member="Lọc theo thành viên (tùy chọn)", limit="Số case cần xem, từ 1 đến 20")
    async def logs(
        self,
        interaction: discord.Interaction,
        member: discord.Member | None = None,
        limit: app_commands.Range[int, 1, 20] = 10,
    ) -> None:
        self._check_actor_permissions(
            interaction, "moderate_members", "manage_messages", "kick_members", "ban_members"
        )
        rows = self.service.recent_cases(
            str(interaction.guild_id),
            target_id=str(member.id) if member else None,
            limit=int(limit),
        )
        if not rows:
            await interaction.response.send_message("Chưa có moderation case nào.", ephemeral=True)
            return
        lines = [
            f"`#{row['case_id']}` **{str(row['action']).upper()}** · `{row['target_type']} {row['target_id']}` · <t:{row['created_at']}:R>"
            for row in rows
        ]
        title = f"Moderation Logs — {member.display_name}" if member else "Moderation Logs"
        embed = discord.Embed(title=title, description="\n".join(lines), color=discord.Color.blurple())
        embed.set_footer(text="Dùng /mod case để xem chi tiết từng case.")
        await interaction.response.send_message(embed=embed, ephemeral=True)

    @app_commands.command(name="case", description="Xem chi tiết một moderation case")
    @app_commands.describe(case_id="Mã case cần tra cứu")
    async def case(self, interaction: discord.Interaction, case_id: int) -> None:
        self._check_actor_permissions(
            interaction, "moderate_members", "manage_messages", "kick_members", "ban_members"
        )
        case = self.service.get_case(str(interaction.guild_id), int(case_id))
        if case is None:
            await interaction.response.send_message("Không tìm thấy case trong máy chủ này.", ephemeral=True)
            return
        embed = discord.Embed(
            title=f"Moderation Case #{case['case_id']}",
            color=discord.Color.blurple(),
            timestamp=discord.utils.utcnow(),
        )
        embed.add_field(name="Hành động", value=str(case["action"]).upper(), inline=True)
        embed.add_field(name="Đối tượng", value=f"{case['target_type']} · `{case['target_id']}`", inline=True)
        embed.add_field(name="Người thực hiện", value=f"<@{case['moderator_id']}>", inline=True)
        embed.add_field(name="Thời điểm", value=f"<t:{case['created_at']}:F>", inline=False)
        if case.get("expires_at"):
            embed.add_field(name="Hết hạn", value=f"<t:{case['expires_at']}:F>", inline=True)
        embed.add_field(name="Lý do", value=str(case["reason"])[:1024], inline=False)
        if case.get("details"):
            embed.add_field(name="Chi tiết", value=str(case["details"])[:1024], inline=False)
        await interaction.response.send_message(embed=embed, ephemeral=True, allowed_mentions=discord.AllowedMentions.none())


def register_moderation_commands(
    tree: app_commands.CommandTree,
    service: ModerationService,
) -> None:
    """Register ``/mod`` on Kato's existing discord.Client command tree."""
    tree.add_command(ModerationGroup(service))
