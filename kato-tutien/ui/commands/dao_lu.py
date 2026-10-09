from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.views.dao_lu_view import DaoLuView, DaoLuRequestView
from ui.embeds import error_embed, success_embed


async def cmd_dao_lu(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    user_id = str(message.author.id)
    if args and message.mentions:
        target = message.mentions[0]
        target_id = str(target.id)
        try:
            ctx.engine.dao_lu.request(user_id, target_id)
            try:
                await target.send(
                    embed=DaoLuRequestView.build_request_embed(message.author.display_name),
                    view=DaoLuRequestView(ctx.engine, target_id, user_id, message.author.display_name),
                )
                await message.reply(embed=success_embed("💞 Cầu Duyên", f"Đã gửi lời cầu duyên tới **{target.display_name}**. Họ sẽ nhận được giao diện để đồng ý hoặc từ chối."))
            except (discord.Forbidden, discord.HTTPException):
                ctx.engine.dao_lu.cancel_request(user_id, target_id)
                await message.reply(embed=error_embed("Không thể gửi tin nhắn riêng tới đạo hữu này. Lời cầu duyên đã được hủy, hãy bật DM rồi thử lại."))
        except GameError as exc:
            await message.reply(embed=error_embed(str(exc)))
        return

    try:
        view = DaoLuView(ctx.engine, user_id)
        await message.reply(embed=view.build_embed(), view=view)
    except GameError as exc:
        await message.reply(embed=error_embed(str(exc)))


async def cmd_song_tu(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    """Quick command for the existing Dao Lữ song-cultivation action."""
    try:
        result = ctx.engine.dao_lu.song_tu(str(message.author.id))
        await message.reply(embed=success_embed(
            "💞 Song Tu Thành Công",
            f"Duyên phận tăng lên **{result['intimacy']}**. Dùng `.daolu` để xem quan hệ và lời cầu duyên.",
        ))
    except GameError as exc:
        await message.reply(embed=error_embed(str(exc)))
