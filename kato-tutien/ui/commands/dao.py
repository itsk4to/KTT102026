from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed
from ui.views.dao_gui import DaoMenuView
from game.content.dao_paths import DAO_PATHS

async def cmd_dao(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    uid = str(message.author.id)
    if not args:
        view = DaoMenuView(ctx.engine, uid)
        await message.reply(embed=view.build_embed(), view=view)
        return
    if args and args[0] in DAO_PATHS:
        try:
            r = ctx.engine.dao.choose(uid, args[0])
            await message.reply(embed=success_embed(f"{EMOJI['dao']} Chọn Đạo", r["dao"]["name"]))
        except GameError as e:
            await message.reply(embed=error_embed(str(e)))
        return
    info = ctx.engine.dao.info(uid)
    if not info:
        lines = [f"`{k}` — {v['name']}" for k, v in DAO_PATHS.items()]
        await message.reply(embed=base_embed(f"{EMOJI['dao']} Đạo", "Chưa chọn. Dùng `.dao <id>`\n" + "\n".join(lines)))
        return
    await message.reply(embed=base_embed(
        f"{EMOJI['dao']} {info['dao']['name']}",
        f"Tầng: **{info['stage_name']}** · Insight {info['insight']}/{info['next_threshold']}",
    ))
