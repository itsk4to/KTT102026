from __future__ import annotations

import discord

from ui.embeds import base_embed, error_embed
from ui.views.secret_realm_view import SecretRealmView
from game.services.errors import GameError


async def cmd_secret_realm(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    user_id = str(message.author.id)
    try:
        view = SecretRealmView(ctx.engine, user_id)
        await message.reply(embed=view.build_embed(), view=view)
    except GameError as exc:
        await message.reply(embed=error_embed(str(exc)))
