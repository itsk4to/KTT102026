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
from ui.embeds import base_embed, error_embed
from ui.views.admin_view import AdminLoginView, AdminView
from game.security.permissions import is_owner
from game.version import VERSION

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kato")

intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)
tree = app_commands.CommandTree(client)

engine = GameEngine(config.DB_PATH)
ctx = CommandContext(engine=engine, command_specs=COMMAND_SPECS)


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
        # Let new players learn/create their character and view the public leaderboard.
        # All other gameplay commands receive a consistent, actionable onboarding hint.
        public_commands = {"tutien", "help", "menu", "bxh", "admin"}
        if spec.name not in public_commands and not engine.players.exists(str(message.author.id)):
            await message.reply(embed=base_embed(
                "🌱 Hãy Khai Đạo Trước",
                "Ngươi chưa tạo nhân vật.\n\n"
                "🧘 Muốn **Tu Tiên**, hãy nhập `.tutien` hoặc `.tamuontutien`.\n"
                "👹 Muốn **Tu Ma**, cũng nhập `.tutien` rồi chọn nút **Tu Ma**.\n"
                "Sau khi tạo nhân vật, dùng `.help` để xem hướng dẫn và menu tổng."
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
