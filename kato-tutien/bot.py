"""Kato Tu Tiên v3.0+ Discord entry point.

Only Discord transport lives here:
- client startup
- command routing
- slash-command wiring

Gameplay stays in game/, presentation in ui/.
"""
from __future__ import annotations

import logging
import os

import discord
from discord import app_commands

import config
from game.engine import GameEngine, GameError
from ui.commands import CommandContext, COMMAND_LOOKUP, COMMAND_SPECS
from ui.commands.moderation import register_moderation_commands
from ui.commands.prison import recover_prison_workflows, handle_prisoner_rejoin
from ui.embeds import base_embed, error_embed, player_embed, public_player_embed
from ui.views.admin_view import AdminLoginView, AdminView
from game.security.permissions import is_owner
from game.version import VERSION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kato")

intents = discord.Intents.default()
intents.message_content = True
intents.members = True  # Used to restore prison status when a member rejoins.
client = discord.Client(intents=intents)


class KatoCommandTree(app_commands.CommandTree):
    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        guild = interaction.guild
        try:
            session = engine.prison.get_active_session_for_user(str(interaction.user.id))
        except Exception:
            logger.exception("Could not verify prison state for slash interaction")
            await interaction.response.send_message(
                "Không thể xác minh trạng thái lao tù lúc này. Lệnh bị chặn an toàn; hãy thử lại sau.",
                ephemeral=True,
            )
            return False
        command_name = str((getattr(interaction, "data", None) or {}).get("name", ""))
        jail_context = bool(
            session and guild is not None
            and str(guild.id) == str(session["guild_id"])
            and interaction.channel_id == config.PRISON_CHANNEL_ID
        )
        if session and (command_name != "help" or not jail_context):
            await interaction.response.send_message(
                "⛓️ Ngươi đang chịu phạt tù Thiên Đạo. Chỉ được dùng `.tutien`, `.kthac` và `/help` trong kênh lao ngục.",
                ephemeral=True,
            )
            return False
        return True


tree = KatoCommandTree(client)

engine = GameEngine(config.DB_PATH)
ctx = CommandContext(engine=engine, command_specs=COMMAND_SPECS, client=client)
register_moderation_commands(tree, engine.moderation, engine)


@tree.command(name="help", description="Cẩm nang lệnh Kato Tu Tiên")
async def help_slash(interaction: discord.Interaction) -> None:
    """Mobile-friendly slash help reusing the existing prefix command registry."""
    from ui.views.help_view import HelpView
    from ui.embeds import base_embed

    user = interaction.user
    guild = interaction.guild
    permissions = getattr(user, "guild_permissions", None)
    is_admin = bool(
        guild is not None and (
            user.id == guild.owner_id
            or getattr(permissions, "administrator", False)
            or bool({role.id for role in getattr(user, "roles", [])} & config.MOD_ADMIN_ROLE_IDS)
            or is_owner(str(user.id))
        )
    )

    groups = [
        ("📖 BẮT ĐẦU & TU LUYỆN", {"start", "cultivation"}),
        ("🌏 KHÁM PHÁ & THẾ GIỚI", {"explore", "world"}),
        ("🎒 TÚI & GIAO DỊCH", {"trade"}),
        ("⚔️ CHIẾN ĐẤU", {"combat"}),
        ("🏯 TÔNG MÔN, ĐẠO & HỆ THỐNG", {"sect", "dao", "social", "system"}),
    ]
    pages = []
    show_admin_page = False
    if isinstance(user, discord.Member):
        permissions_for_help = user.guild_permissions
        show_admin_page = is_admin or any((
            permissions_for_help.kick_members, permissions_for_help.ban_members,
            permissions_for_help.moderate_members, permissions_for_help.manage_messages,
            permissions_for_help.manage_channels, permissions_for_help.manage_roles,
        ))
    total_pages = len(groups) + (1 if show_admin_page else 0)
    for index, (heading, categories) in enumerate(groups, 1):
        lines = [f"**{heading}**"]
        for spec in COMMAND_SPECS:
            if spec.category not in categories:
                continue
            if spec.name == "admin" and not is_admin:
                continue
            aliases = [f".{alias}" for alias in spec.aliases if alias != spec.name]
            alias_text = f" · Bí danh: {', '.join(aliases)}" if aliases else ""
            lines.append(f"**`{spec.usage}`** — {spec.description}{alias_text}")
        pages.append(base_embed(f"📘 Cẩm Nang · {index}/{total_pages}", "\n".join(lines)))

    if guild is not None and isinstance(user, discord.Member):
        perms = user.guild_permissions
        moderation_lines = []
        command_permissions = [
            ("/kick", "kick_members"), ("/ban · /unban", "ban_members"),
            ("/timeout · /untimeout", "moderate_members"), ("/warn · /warnings · /logs · /case", "manage_messages"),
            ("/purge", "manage_messages"), ("/slowmode · /lock · /unlock", "manage_channels"),
            ("/phattu", "admin"),
        ]
        for label, permission in command_permissions:
            has_scope = is_admin if permission == "admin" else getattr(perms, permission, False)
            if permission == "moderate_members":
                has_scope = has_scope or perms.manage_messages or perms.kick_members or perms.ban_members
            if is_admin or has_scope:
                moderation_lines.append(label)
        if is_admin:
            moderation_lines.append("/tha_tu")
        if moderation_lines:
            pages.append(base_embed(
                "🛡️ Cẩm Nang · Quản Trị",
                "**LỆNH MODERATION CẤP GỐC**\n" + "\n".join(f"• `{item}`" for item in moderation_lines)
                + "\n\nModerator role không tự cấp toàn bộ quyền; từng lệnh vẫn kiểm tra quyền Discord tương ứng.",
            ))

    is_prisoner = bool(guild is not None and engine.prison.get_active_session(str(guild.id), str(user.id)))
    if is_prisoner:
        await interaction.response.send_message(embed=pages[0], ephemeral=True)
        return
    view = HelpView(pages, engine, str(user.id))
    await interaction.response.send_message(embed=pages[0], view=view, ephemeral=True)


@tree.command(name="info", description="Xem hồ sơ riêng hoặc hồ sơ công khai của người chơi")
@app_commands.describe(player="Bỏ trống để xem hồ sơ riêng của bạn; chọn người chơi để xem hồ sơ công khai")
async def info_slash(interaction: discord.Interaction, player: discord.Member | None = None) -> None:
    """Private own profile; public filtered profile when a player is selected."""
    target = player or interaction.user
    user_id = str(target.id)
    try:
        info = engine.players.info_text(user_id)
        stats = engine.combat.battle_stats(info["player"])
        if player is None:
            await interaction.response.send_message(
                embed=player_embed(info, combat_stats=stats, show_currency=True), ephemeral=True
            )
        else:
            await interaction.response.send_message(
                embed=public_player_embed(info, combat_stats=stats), ephemeral=False
            )
    except GameError as exc:
        await interaction.response.send_message(embed=error_embed(str(exc)), ephemeral=True)


@tree.command(name="admin", description="Mở bảng quản trị Kato Tu Tiên")
async def admin_slash(interaction: discord.Interaction) -> None:
    actor_id = str(interaction.user.id)
    if is_owner(actor_id) or engine.admin_auth.has_session(actor_id):
        await interaction.response.send_message(
            embed=base_embed("👑 Kato Admin", "Bảng điều khiển quản trị."),
            view=AdminView(engine, actor_id),
            ephemeral=True,
        )
        return
    await interaction.response.send_message(
        embed=base_embed("🔐 Kato Admin", "Đăng nhập bằng nút bên dưới."),
        view=AdminLoginView(engine),
        ephemeral=True,
    )


@client.event
async def on_ready() -> None:
    logger.info("Logged in as %s (v%s)", client.user, VERSION)
    try:
        await tree.sync()
    except Exception:
        logger.exception("slash sync failed")
    try:
        await recover_prison_workflows(client, engine)
    except Exception:
        logger.exception("prison recovery failed during startup")


@client.event
async def on_member_join(member: discord.Member) -> None:
    try:
        await handle_prisoner_rejoin(member, client, engine)
    except Exception:
        logger.exception("Could not restore prison state for rejoining member %s", member.id)


@client.event
async def on_message(message: discord.Message) -> None:
    if message.author.bot or not message.content.startswith("."):
        return
    raw = message.content[1:].strip()
    if not raw:
        return

    parts = raw.split()
    key = parts[0].lower()
    spec = COMMAND_LOOKUP.get(key)
    if not spec:
        return

    args = parts[1:]
    try:
        user_id = str(message.author.id)
        prison_session = engine.prison.get_active_session_for_user(user_id)
        if prison_session:
            allowed_prison_commands = {"tutien", "help", "kthac"}
            is_prison_channel = bool(
                message.guild is not None
                and str(message.guild.id) == str(prison_session["guild_id"])
                and message.channel.id == config.PRISON_CHANNEL_ID
            )
            if not is_prison_channel or spec.name not in allowed_prison_commands:
                await message.reply("⛓️ Ngươi đang chịu phạt tù Thiên Đạo. Chỉ được dùng `.tutien`, `.kthac` và `.help` trong kênh lao ngục.")
                return

        # A prisoner without a character may still register inside the prison channel.
        public_commands = {"tutien", "help", "menu", "bxh", "admin"}
        if spec.name not in public_commands and not engine.players.exists(user_id):
            await message.reply(embed=base_embed(
                "🌱 Hãy Khai Đạo Trước",
                "Ngươi chưa tạo nhân vật.\n\n"
                "🧘 Muốn **Tu Tiên**, hãy nhập `.tutien` hoặc `.tamuontutien`.\n"
                "👹 Muốn **Tu Ma**, cũng nhập `.tutien` rồi chọn nút **Tu Ma**.\n"
                "Sau khi tạo nhân vật, dùng `.help` để xem hướng dẫn."
            ))
            return
        if spec.takes_args:
            await spec.handler(ctx, message, args)
        else:
            await spec.handler(ctx, message, args)
    except GameError as exc:
        await message.reply(embed=error_embed(str(exc)))
    except Exception:
        logger.exception("command failed: %s", key)
        await message.reply(embed=error_embed("Lỗi hệ thống. Thử lại sau."))


def main() -> None:
    token = config.TOKEN or os.getenv("DISCORD_TOKEN", "")
    if not token:
        raise SystemExit("Missing DISCORD_TOKEN")
    if not config.ADMIN_PASSWORD:
        logger.warning("KATO_ADMIN_PASSWORD not set — password login disabled")
    client.run(token)


if __name__ == "__main__":
    main()
