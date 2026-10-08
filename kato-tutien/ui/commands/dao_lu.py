from __future__ import annotations
import discord
from ui.views.dao_lu_view import DaoLuView
from ui.embeds import error_embed
from game.services.errors import GameError

async def cmd_dao_lu(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        view = DaoLuView(ctx.engine, str(message.author.id))
        await message.reply(embed=view.build_embed(), view=view)
    except GameError as exc:
        await message.reply(embed=error_embed(str(exc)))
