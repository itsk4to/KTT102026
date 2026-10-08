from __future__ import annotations

import discord

from game.security.permissions import is_owner
from ui.embeds import base_embed, error_embed
from ui.views.admin_view import AdminLoginView, AdminView


async def cmd_admin(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    actor_id = str(message.author.id)
    if is_owner(actor_id) or ctx.engine.admin_auth.has_session(actor_id):
        await message.reply(
            embed=base_embed("👑 Quản trị Kato", "Bảng điều khiển quản trị."),
            view=AdminView(ctx.engine, actor_id),
        )
        return
    await message.reply(
        embed=base_embed("🔐 Quản trị Kato", "Bấm nút bên dưới để đăng nhập an toàn."),
        view=AdminLoginView(ctx.engine),
    )
