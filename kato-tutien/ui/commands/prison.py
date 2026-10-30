"""Discord adapter for the Heavenly Dao prison workflow."""
from __future__ import annotations

import json
import logging
from typing import Any

import discord

import config
from game.moderation.prison_repository import PrisonError

logger = logging.getLogger("kato.prison")


def _member_overwrite_payload(channel: Any, member: discord.Member) -> dict[str, int] | None:
    overwrite = getattr(channel, "overwrites", {}).get(member)
    if overwrite is None:
        return None
    allow, deny = overwrite.pair()
    return {"allow": int(allow.value), "deny": int(deny.value)}


def _capture_permissions(guild: discord.Guild, member: discord.Member, role: discord.Role) -> dict[str, Any]:
    """Snapshot member-specific overwrites so other prisoners never affect each other."""
    snapshots: dict[str, Any] = {}
    for channel in guild.channels:
        if not hasattr(channel, "set_permissions"):
            continue
        snapshots[str(channel.id)] = _member_overwrite_payload(channel, member)
    return {"role_id": role.id, "member_id": member.id, "channels": snapshots}


def _permission_from_payload(value: dict[str, int] | None) -> discord.PermissionOverwrite | None:
    if value is None:
        return None
    allow = discord.Permissions(int(value.get("allow", 0)))
    deny = discord.Permissions(int(value.get("deny", 0)))
    return discord.PermissionOverwrite.from_pair(allow, deny)


async def _apply_prison_restrictions(
    guild: discord.Guild, member: discord.Member, prison_channel_id: int, reason: str
) -> None:
    # Member-specific overwrites are necessary: another role's channel allow
    # must not override the prisoner's restriction. The shared prison role is
    # used as a marker and is deliberately not modified per-session.
    for channel in guild.channels:
        if not hasattr(channel, "set_permissions"):
            continue
        overwrite = channel.overwrites_for(member)
        if channel.id == prison_channel_id:
            overwrite.view_channel = True
            overwrite.send_messages = True
            overwrite.read_message_history = True
            overwrite.add_reactions = False
        else:
            overwrite.view_channel = False
            overwrite.send_messages = False
            overwrite.add_reactions = False
            overwrite.connect = False
            overwrite.speak = False
        await channel.set_permissions(member, overwrite=overwrite, reason=f"Kato Prison | {reason[:350]}")


async def _restore_permissions(
    guild: discord.Guild, member: discord.Member, snapshot: dict[str, Any]
) -> None:
    channels = snapshot.get("channels", {})
    if not isinstance(channels, dict):
        raise RuntimeError("Snapshot quyền kênh bị hỏng; không thể khôi phục an toàn.")
    for channel_id, value in channels.items():
        channel = guild.get_channel(int(channel_id))
        if channel is None or not hasattr(channel, "set_permissions"):
            # A deleted channel has no remaining permissions to restore.
            continue
        overwrite = _permission_from_payload(value)
        await channel.set_permissions(
            member,
            overwrite=overwrite,
            reason="Kato Prison | Khôi phục quyền thành viên trước khi phạt tù",
        )


async def _reapply_restrictions_safely(guild: discord.Guild, member: discord.Member) -> None:
    """Fail closed if release restored only some member overwrites."""
    try:
        await _apply_prison_restrictions(
            guild, member, config.PRISON_CHANNEL_ID, "Khôi phục giới hạn sau thao tác thả tù lỗi"
        )
    except Exception:
        logger.exception("Unable to reapply prison restrictions in guild %s", guild.id)


async def _configured_entities(guild: discord.Guild) -> tuple[discord.Role, discord.TextChannel, discord.TextChannel | None]:
    if not config.PRISON_ROLE_ID or not config.PRISON_CHANNEL_ID:
        raise PrisonError("Thiếu cấu hình KATO_PRISON_ROLE_ID hoặc KATO_PRISON_CHANNEL_ID.")
    role = guild.get_role(config.PRISON_ROLE_ID)
    prison_channel = guild.get_channel(config.PRISON_CHANNEL_ID)
    announce_channel = guild.get_channel(config.PRISON_ANNOUNCE_CHANNEL_ID) if config.PRISON_ANNOUNCE_CHANNEL_ID else None
    if role is None:
        raise PrisonError("Không tìm thấy role tù nhân. Hãy kiểm tra KATO_PRISON_ROLE_ID.")
    if not isinstance(prison_channel, discord.TextChannel):
        raise PrisonError("Không tìm thấy kênh văn bản lao ngục. Hãy kiểm tra KATO_PRISON_CHANNEL_ID.")
    if not isinstance(announce_channel, discord.TextChannel):
        raise PrisonError("Hãy cấu hình KATO_PRISON_ANNOUNCE_CHANNEL_ID bằng ID một kênh văn bản.")
    bot_member = guild.me
    if bot_member is None:
        raise PrisonError("Không xác định được thành viên bot trong máy chủ.")
    jail_permissions = prison_channel.permissions_for(bot_member)
    announce_permissions = announce_channel.permissions_for(bot_member)
    if not jail_permissions.view_channel or not jail_permissions.send_messages:
        raise PrisonError("Bot cần quyền View Channel và Send Messages trong kênh lao ngục.")
    if not announce_permissions.view_channel or not announce_permissions.send_messages:
        raise PrisonError("Bot cần quyền View Channel và Send Messages trong kênh thông báo mãn hạn tù.")
    return role, prison_channel, announce_channel


async def _release_session(guild: discord.Guild, client: discord.Client, engine, session: dict[str, Any]) -> dict[str, Any]:
    """Restore Discord access first, then atomically pay the community once."""
    fresh = engine.prison.get_session(int(session["session_id"]))
    if fresh is None:
        raise PrisonError("Không tìm thấy phiên tù cần khôi phục.")
    if fresh["status"] == "completed":
        payout = engine.prison.finalize_payout(int(fresh["session_id"]))
    else:
        if fresh["status"] != "release_pending":
            raise PrisonError("Phiên tù chưa ở trạng thái chờ thả.")
        role = guild.get_role(int(config.PRISON_ROLE_ID)) if config.PRISON_ROLE_ID else None
        if role is None:
            raise PrisonError("Không tìm thấy role tù nhân; chưa thể thả tù an toàn.")
        bot_member = guild.me
        if bot_member is None or not bot_member.guild_permissions.manage_roles or not bot_member.guild_permissions.manage_channels:
            raise PrisonError("Bot cần quyền Manage Roles và Manage Channels để khôi phục quyền tù nhân.")
        snapshot = engine.prison.permission_snapshot(fresh)
        if not snapshot or "channels" not in snapshot:
            raise PrisonError("Thiếu snapshot quyền trước khi phạt tù; bot từ chối tự mở kênh.")
        member = guild.get_member(int(fresh["user_id"]))
        if member is None:
            try:
                member = await guild.fetch_member(int(fresh["user_id"]))
            except discord.NotFound:
                member = None
        if member is None:
            raise PrisonError("Tù nhân hiện không còn trong máy chủ. Quyền chưa thể khôi phục; phiên tù vẫn chờ xử lý đến khi người này quay lại.")
        try:
            await _restore_permissions(guild, member, snapshot)
            if role in member.roles:
                await member.remove_roles(role, reason="Kato Prison | Hoàn thành lao dịch")
        except Exception:
            await _reapply_restrictions_safely(guild, member)
            logger.exception("Prison release Discord step failed for session %s", fresh["session_id"])
            raise PrisonError("Discord chưa khôi phục đủ quyền. Phiên tù vẫn được giữ ở trạng thái chờ xử lý; có thể thử lại.")
        try:
            payout = engine.prison.finalize_payout(int(fresh["session_id"]))
        except Exception as exc:
            # If Discord access was restored but the DB payout failed, reapply
            # the jail restriction and role before leaving the session pending.
            try:
                await _apply_prison_restrictions(
                    guild, member, config.PRISON_CHANNEL_ID,
                    "Khôi phục giới hạn do quyết toán lao dịch chưa hoàn tất",
                )
                if role not in member.roles:
                    await member.add_roles(role, reason="Kato Prison | Giữ trạng thái tù khi payout lỗi")
            except Exception:
                logger.exception("Could not reapply prison state after payout failure for session %s", fresh["session_id"])
            logger.exception("Prison payout transaction failed for session %s", fresh["session_id"])
            raise PrisonError(
                "Đã khôi phục quyền Discord nhưng quyết toán quỹ lao dịch gặp lỗi. Bot đã thử khóa lại trạng thái tù; phiên vẫn chờ xử lý an toàn."
            ) from exc

    # Announcement is deliberately separate from the DB payout transaction.
    # The payout itself is idempotent even if sending an announcement needs retry.
    completed = engine.prison.get_session(int(fresh["session_id"])) or fresh
    if not int(completed.get("announcement_sent_at") or 0) and config.PRISON_ANNOUNCE_CHANNEL_ID:
        channel = guild.get_channel(config.PRISON_ANNOUNCE_CHANNEL_ID)
        if channel is None:
            try:
                channel = await client.fetch_channel(config.PRISON_ANNOUNCE_CHANNEL_ID)
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                logger.exception("Could not fetch prison announcement channel")
                return payout
        if isinstance(channel, discord.TextChannel) and channel.guild.id == guild.id:
            prisoner_row = engine.db.fetchone("SELECT display_name FROM players WHERE user_id=?", (str(fresh["user_id"]),))
            display_name = str(prisoner_row["display_name"]) if prisoner_row else f"<@{fresh['user_id']}>"
            message = (
                "⛓️ **THIÊN ĐẠO CÔNG BỐ — LAO DỊCH HOÀN TẤT**\n\n"
                f"Đạo hữu **{discord.utils.escape_markdown(display_name)[:80]}** cuối cùng cũng đã trả xong nợ với Thiên Đạo!\n"
                "Thiên Đạo ghi nhận tinh thần lao động... và quyết định đem thành quả chia cho toàn thể đạo hữu. 😂\n\n"
                f"• Chỉ tiêu: **{int(fresh['required_stones']):,}** linh thạch\n"
                f"• Tổng khai thác: **{int(payout['total_stones']):,}** linh thạch\n"
                f"• Số người nhận thưởng: **{int(payout['recipient_count'])}**\n"
                f"• Mỗi người nhận: **{int(payout['per_player_reward']):,}** linh thạch\n"
                f"• Số dư quỹ cộng đồng: **{int(payout['remainder']):,}** linh thạch\n\n"
                "🎁 Linh thạch đã được phân phát cho các đạo hữu đủ điều kiện!"
            )
            try:
                await channel.send(message, allowed_mentions=discord.AllowedMentions.none())
                engine.prison.mark_announcement_sent(int(fresh["session_id"]))
            except (discord.Forbidden, discord.NotFound, discord.HTTPException):
                logger.exception("Prison payout succeeded but announcement delivery failed for session %s", fresh["session_id"])
    return payout


async def start_prison(
    interaction: discord.Interaction,
    *,
    engine,
    member: discord.Member,
    required_stones: int,
    reason: str,
) -> dict[str, Any]:
    guild = interaction.guild
    if guild is None:
        raise PrisonError("Lệnh phạt tù chỉ dùng trong máy chủ Discord.")
    role, prison_channel, _ = await _configured_entities(guild)
    bot_member = guild.me
    if bot_member is None or not bot_member.guild_permissions.manage_roles or not bot_member.guild_permissions.manage_channels:
        raise PrisonError("Bot cần quyền Manage Roles và Manage Channels trước khi phạt tù.")
    if role >= bot_member.top_role:
        raise PrisonError("Role bot phải nằm cao hơn role Tù Nhân trong Server Settings.")
    if role in member.roles:
        raise PrisonError("Thành viên đã có role tù nhân; hãy kiểm tra phiên tù hiện tại.")
    session = engine.prison.create_session(
        guild_id=str(guild.id), user_id=str(member.id), actor_id=str(interaction.user.id),
        required_stones=int(required_stones), reason=reason,
    )
    session_id = int(session["session_id"])
    snapshot = _capture_permissions(guild, member, role)
    engine.prison.set_permission_snapshot(session_id, snapshot)
    role_added = False
    try:
        await member.add_roles(role, reason=f"Kato Prison | {reason[:350]}")
        role_added = True
        await _apply_prison_restrictions(guild, member, prison_channel.id, reason)
        engine.prison.activate(session_id)
    except Exception as exc:
        rollback_ok = True
        try:
            await _restore_permissions(guild, member, snapshot)
        except Exception:
            rollback_ok = False
            logger.exception("Prison setup rollback could not restore all overwrites")
        if role_added:
            try:
                await member.remove_roles(role, reason="Kato Prison | Rollback thiết lập thất bại")
            except Exception:
                rollback_ok = False
                logger.exception("Prison setup rollback could not remove prisoner role")
        if rollback_ok:
            engine.prison.mark_failed(session_id, str(exc))
        raise PrisonError("Không thể thiết lập quyền lao ngục. Bot đã thử hoàn tác; kiểm tra log và quyền Discord trước khi thử lại.") from exc

    engine.moderation.record_action(
        guild_id=str(guild.id), moderator_id=str(interaction.user.id), target_id=str(member.id),
        target_type="user", action="prison", reason=reason,
        details=json.dumps({"session_id": session_id, "required_stones": required_stones, "status": "active"}),
    )
    return engine.prison.get_session(session_id) or session


async def release_prison_for_member(guild: discord.Guild, client: discord.Client, engine, member: discord.Member) -> dict[str, Any]:
    session = engine.prison.get_active_session(str(guild.id), str(member.id))
    if session is None:
        raise PrisonError("Thành viên này không có phiên tù đang hoạt động.")
    session = engine.prison.request_release(int(session["session_id"]))
    return await _release_session(guild, client, engine, session)


async def release_completed_prison(guild: discord.Guild, client: discord.Client, engine, session_id: int) -> dict[str, Any]:
    session = engine.prison.get_session(session_id)
    if session is None:
        raise PrisonError("Không tìm thấy phiên tù cần hoàn tất.")
    return await _release_session(guild, client, engine, session)


async def recover_prison_workflows(client: discord.Client, engine) -> None:
    """Retry interrupted setup rollbacks and releases after a bot restart."""
    for session in engine.prison.get_preparing_sessions():
        guild = client.get_guild(int(session["guild_id"]))
        if guild is None or not config.PRISON_ROLE_ID:
            continue
        role = guild.get_role(config.PRISON_ROLE_ID)
        if role is None:
            continue
        snapshot = engine.prison.permission_snapshot(session)
        if not snapshot or "channels" not in snapshot:
            logger.error("Preparing prison session %s has no permission snapshot; no Discord restrictions were safely initialized", session["session_id"])
            engine.prison.mark_failed(
                int(session["session_id"]),
                "Thiếu snapshot quyền trước khi bắt đầu; đánh dấu thất bại để tránh khóa người chơi vĩnh viễn.",
            )
            continue
        member = guild.get_member(int(session["user_id"]))
        if member is None:
            try:
                member = await guild.fetch_member(int(session["user_id"]))
            except discord.NotFound:
                member = None
        if member is None:
            continue
        try:
            await _restore_permissions(guild, member, snapshot)
            if role in member.roles:
                await member.remove_roles(role, reason="Kato Prison | Khôi phục sau khởi động lại")
            engine.prison.mark_failed(int(session["session_id"]), "Đã hoàn tác phiên thiết lập dở dang sau khi bot khởi động lại.")
        except Exception:
            logger.exception("Failed recovering preparing prison session %s", session["session_id"])

    for session in engine.prison.get_pending_releases():
        guild = client.get_guild(int(session["guild_id"]))
        if guild is None:
            continue
        try:
            await _release_session(guild, client, engine, session)
        except Exception:
            logger.exception("Failed recovering prison release session %s", session["session_id"])

    # A successful payout is never repeated; only an undelivered announcement is retried.
    for session in engine.prison.get_unannounced_completed():
        guild = client.get_guild(int(session["guild_id"]))
        if guild is None:
            continue
        try:
            await _release_session(guild, client, engine, session)
        except Exception:
            logger.exception("Failed retrying prison announcement for session %s", session["session_id"])


async def handle_prisoner_rejoin(member: discord.Member, client: discord.Client, engine) -> None:
    """Reapply an active sentence or finish a pending release when a member rejoins."""
    session = engine.prison.get_active_session(str(member.guild.id), str(member.id))
    if session is None:
        return
    if session["status"] in ("preparing", "release_pending"):
        await recover_prison_workflows(client, engine)
        return
    role, prison_channel, _ = await _configured_entities(member.guild)
    bot_member = member.guild.me
    if bot_member is None or not bot_member.guild_permissions.manage_roles or not bot_member.guild_permissions.manage_channels:
        raise PrisonError("Bot thiếu Manage Roles hoặc Manage Channels để khôi phục trạng thái tù.")
    if role not in member.roles:
        await member.add_roles(role, reason="Kato Prison | Khôi phục phiên tù khi thành viên quay lại")
    await _apply_prison_restrictions(
        member.guild, member, prison_channel.id, "Khôi phục hạn chế khi tù nhân quay lại máy chủ"
    )


async def cmd_prison_mine(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    """Prefix command `.kthac`; each accepted message contributes exactly 10."""
    from ui.embeds import error_embed

    if message.guild is None:
        await message.reply(embed=error_embed("Lệnh này chỉ dùng trong máy chủ lao ngục."))
        return
    try:
        result = ctx.engine.prison.mine(
            guild_id=str(message.guild.id),
            user_id=str(message.author.id),
            channel_id=str(message.channel.id),
            expected_channel_id=str(config.PRISON_CHANNEL_ID),
            event_id=str(message.id),
            cooldown_seconds=config.PRISON_COOLDOWN_SECONDS,
        )
    except PrisonError as exc:
        await message.reply(embed=error_embed(str(exc)))
        return

    await message.reply(
        "⛏️ **Lao dịch hoàn tất!**\n"
        f"• Vừa khai thác: **{result['amount']}** linh thạch\n"
        f"• Tích lũy: **{result['total_stones']:,} / {result['required_stones']:,}**\n"
        f"• Còn thiếu: **{result['remaining_stones']:,}**\n"
        "Linh thạch lao dịch không cộng vào ví cá nhân."
    )
    if result["release_due"]:
        try:
            payout = await release_completed_prison(
                message.guild, ctx.client, ctx.engine, int(result["session"]["session_id"])
            )
            ctx.engine.moderation.record_action(
                guild_id=str(message.guild.id), moderator_id="0",
                target_id=str(message.author.id), target_type="user",
                action="prison_release", reason="Hoàn thành chỉ tiêu lao dịch",
                details=json.dumps({
                    "session_id": result["session"]["session_id"],
                    "total_stones": payout["total_stones"],
                    "recipient_count": payout["recipient_count"],
                    "per_player_reward": payout["per_player_reward"],
                    "remainder": payout["remainder"],
                }),
            )
        except Exception:
            logger.exception("Automatic prison release failed for user %s", message.author.id)
            await message.reply(
                "Thiên Đạo đã ghi nhận đủ chỉ tiêu, nhưng Discord chưa khôi phục hoàn toàn quyền truy cập. "
                "Phiên thả tù đang chờ xử lý; hãy báo Admin kiểm tra lệnh `/tha_tu`."
            )
