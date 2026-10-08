from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed
from game.utils import fmt_amount

async def cmd_sect(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        ov = ctx.engine.sect.overview(str(message.author.id))
        if not ov["in_sect"]:
            lines = [f"`{s['sect_id']}` **{s['name']}** Lv{s['level']}" for s in ov["sects"][:15]]
            await message.reply(embed=base_embed(
                f"{EMOJI['sect']} Tông môn",
                "Chưa gia nhập.\n`.taotong <tên>` · `.xintong <id>`\n\n" + ("\n".join(lines) or "Chưa có tông."),
            ))
            return
        s = ov["sect"]
        lines = [
            f"**{s.name}** Lv{s.level} · Khố {fmt_amount(s.treasury)}",
            f"Vai trò: **{ov['my_role']}**",
            "",
            "Thành viên:",
        ]
        for m in ov["members"][:10]:
            lines.append(f"• <@{m.user_id}> — {m.role} ({fmt_amount(m.contribution)})")
        await message.reply(embed=base_embed(f"{EMOJI['sect']} Nội Vụ", "\n".join(lines)))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_sect_create(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.taotong <tên>`"))
        return
    try:
        r = ctx.engine.sect.create(str(message.author.id), " ".join(args))
        await message.reply(embed=success_embed("🏯 Sáng lập", f"**{r['sect'].name}** (`{r['sect'].sect_id}`)"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_sect_apply(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.xintong <sect_id>`"))
        return
    try:
        r = ctx.engine.sect.apply(str(message.author.id), args[0])
        await message.reply(embed=success_embed("✅ Đã gửi đơn", f"Tới **{r['sect'].name}** · #{r['application_id']}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_sect_contribute(ctx, message: discord.Message, args: list[str]) -> None:
    if not args or not args[0].isdigit():
        await message.reply(embed=error_embed("Dùng: `.congtong <số>`"))
        return
    try:
        r = ctx.engine.sect.contribute(str(message.author.id), int(args[0]))
        await message.reply(embed=success_embed("✅ Cống hiến", f"+{fmt_amount(r['amount'])} · Tổng {fmt_amount(r['contribution'])}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_sect_leave(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        ctx.engine.sect.leave(str(message.author.id))
        await message.reply(embed=success_embed("✅", "Đã rời tông môn."))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))
