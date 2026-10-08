from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed, shop_embed
from ui.views.shop_view import ShopView
from game.utils import fmt_amount

async def cmd_shop(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    catalog = ctx.engine.economy.shop_catalog()
    await message.reply(embed=shop_embed(catalog), view=ShopView(ctx.engine, catalog))

async def cmd_buy(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.mua <item_id> [số_lượng]`"))
        return
    qty = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    try:
        r = ctx.engine.economy.buy(str(message.author.id), args[0], qty)
        await message.reply(embed=success_embed(
            "✅ Mua thành công",
            f"**{r['item']['name']}** ×{qty} — {fmt_amount(r['total'])} {EMOJI['spirit_stone']}",
        ))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_inventory(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        items = ctx.engine.economy.inventory(str(message.author.id))
        if not items:
            await message.reply(embed=base_embed(f"{EMOJI['item']} Túi đồ", "Trống."))
            return
        lines = [f"• **{it['name']}** ×{it['qty']} (`{it['id']}`)" for it in items]
        await message.reply(embed=base_embed(f"{EMOJI['item']} Túi đồ", "\n".join(lines)))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_use(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.dung <item_id> [sl]`"))
        return
    qty = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    try:
        r = ctx.engine.economy.use_item(str(message.author.id), args[0], qty)
        await message.reply(embed=success_embed("✅ Đã dùng", ", ".join(r["notes"]) or r["item"]["name"]))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_learn(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.hoc <item_id>`"))
        return
    try:
        r = ctx.engine.economy.learn_technique(str(message.author.id), args[0])
        await message.reply(embed=success_embed(
            f"{EMOJI['technique']} Học thành công",
            f"**{r['item']['name']}** · {r['stage']} (mastery {r['mastery']})",
        ))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_equip(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.trangbi <item_id>`"))
        return
    try:
        r = ctx.engine.economy.equip(str(message.author.id), args[0])
        await message.reply(embed=success_embed("✅ Trang bị", f"**{r['item']['name']}** → slot `{r['slot']}`"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_unequip(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        ctx.engine.economy.unequip(str(message.author.id))
        await message.reply(embed=success_embed("✅", "Đã tháo trang bị."))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_market(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    listings = ctx.engine.economy.market_browse()
    if not listings:
        await message.reply(embed=base_embed("🏪 Chợ", "Chưa có tin đăng."))
        return
    lines = [
        f"`#{L['id']}` **{L['name']}** ×{L['qty']} — {fmt_amount(L['price'])} {EMOJI['spirit_stone']}"
        for L in listings[:20]
    ]
    await message.reply(embed=base_embed("🏪 Chợ", "\n".join(lines)))

async def cmd_market_list(ctx, message: discord.Message, args: list[str]) -> None:
    if len(args) < 3:
        await message.reply(embed=error_embed("Dùng: `.dangban <item> <sl> <gia>`"))
        return
    try:
        r = ctx.engine.economy.market_list(str(message.author.id), args[0], int(args[1]), int(args[2]))
        await message.reply(embed=success_embed("✅ Đăng bán", f"#{r['listing_id']} **{r['item']['name']}** ×{r['qty']}"))
    except (GameError, ValueError) as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_market_buy(ctx, message: discord.Message, args: list[str]) -> None:
    if not args or not args[0].isdigit():
        await message.reply(embed=error_embed("Dùng: `.muacho <id>`"))
        return
    try:
        r = ctx.engine.economy.market_buy(str(message.author.id), int(args[0]))
        await message.reply(embed=success_embed("✅ Mua chợ", f"×{r['qty']} — trả {fmt_amount(r['total'])} (thuế {r['tax']})"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_market_cancel(ctx, message: discord.Message, args: list[str]) -> None:
    if not args or not args[0].isdigit():
        await message.reply(embed=error_embed("Dùng: `.huyban <id>`"))
        return
    try:
        r = ctx.engine.economy.market_cancel(str(message.author.id), int(args[0]))
        await message.reply(embed=success_embed("✅ Hủy bán", f"Hoàn ×{r['qty']} `{r['item_id']}`"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_transfer(ctx, message: discord.Message, args: list[str]) -> None:
    if len(message.mentions) < 1 or len(args) < 2:
        await message.reply(embed=error_embed("Dùng: `.chuyen @user <số>`"))
        return
    amount = next((int(a) for a in args if a.isdigit()), 0)
    try:
        ctx.engine.economy.transfer(str(message.author.id), str(message.mentions[0].id), amount)
        await message.reply(embed=success_embed("✅ Chuyển", f"{fmt_amount(amount)} {EMOJI['spirit_stone']}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_code(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Dùng: `.code <mã>`"))
        return
    try:
        r = ctx.engine.economy.redeem_code(str(message.author.id), args[0])
        await message.reply(embed=success_embed("🎁 Code", f"+{fmt_amount(r['stones'])} {EMOJI['spirit_stone']}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_gacha(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        r = ctx.engine.economy.gacha(str(message.author.id))
        name = r["item"].get("name", r["item_id"])
        await message.reply(embed=success_embed("🔮 Thiên Cơ", f"Nhận **{name}**"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))
