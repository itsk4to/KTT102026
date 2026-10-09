from __future__ import annotations

import discord
from game.services.errors import GameError
from ui.emoji import EMOJI
from ui.embeds import base_embed, error_embed, success_embed, shop_embed, inventory_embed
from ui.views.shop_view import ShopView
from ui.views.inventory_view import InventoryView
from game.utils import fmt_amount
from game.content.items import ITEMS

async def cmd_shop(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    catalog = ctx.engine.economy.shop_catalog()
    await message.reply(embed=shop_embed(catalog), view=ShopView(ctx.engine, catalog, str(message.author.id)))

async def cmd_buy(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Cách dùng: `.mua <mã_vật_phẩm> [số_lượng]`"))
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
        user_id = str(message.author.id)
        items = ctx.engine.economy.inventory(user_id)
        if not items:
            await message.reply(embed=base_embed(f"{EMOJI['item']} Túi đồ", "Túi đồ đang trống."))
            return
        await message.reply(
            embed=inventory_embed(items),
            view=InventoryView(ctx.engine, user_id, items),
        )
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))


async def cmd_use(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Cách dùng: `.dung <mã_vật_phẩm> [số_lượng]`"))
        return
    qty = int(args[1]) if len(args) > 1 and args[1].isdigit() else 1
    try:
        r = ctx.engine.economy.use_item(str(message.author.id), args[0], qty)
        await message.reply(embed=success_embed("✅ Đã dùng", ", ".join(r["notes"]) or r["item"]["name"]))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_learn(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Cách dùng: `.hoc <mã_công_pháp>`"))
        return
    try:
        r = ctx.engine.economy.learn_technique(str(message.author.id), args[0])
        await message.reply(embed=success_embed(
            f"{EMOJI['technique']} Học thành công",
            f"**{r['item']['name']}** · {r['stage']} · Độ thành thạo {r['mastery']}",
        ))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_equip(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Cách dùng: `.trangbi <mã_vật_phẩm>`"))
        return
    try:
        r = ctx.engine.economy.equip(str(message.author.id), args[0])
        stats = r["power"]
        text = (
            f"**{r['item']['name']}** đã được trang bị vào ô `{r['slot']}`.\\n"
            "Vật phẩm đã chuyển khỏi túi và đang được tính vào chỉ số chiến đấu.\\n"
            f"⚔️ Công: **{stats['attack']}** · 🛡️ Thủ: **{stats['defense']}** · "
            f"❤️ HP tối đa: **{stats['max_hp']}**\\n"
            f"💥 Chiến lực: **{stats['power']}**"
        )
        if r.get("replaced_item_id"):
            previous = ITEMS.get(r["replaced_item_id"], {}).get("name", r["replaced_item_id"])
            text += f"\\nTrang bị cũ **{previous}** đã được trả về túi."
        await message.reply(embed=success_embed("✅ Trang bị thành công", text))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_unequip(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        slot = args[0].lower() if args and args[0].lower() not in ("all", "tatca", "tất-cả") else None
        r = ctx.engine.economy.unequip(str(message.author.id), slot)
        stats = r["power"]
        if slot:
            names = [ITEMS.get(i, {}).get("name", i) for i in r["removed"]]
            message_text = f"Đã tháo **{names[0]}** và trả vật phẩm về túi."
        else:
            message_text = f"Đã tháo **{len(r['removed'])}** trang bị và trả tất cả về túi."
        message_text += (
            f"\\n⚔️ Công: **{stats['attack']}** · 🛡️ Thủ: **{stats['defense']}** · "
            f"❤️ HP tối đa: **{stats['max_hp']}** · 💥 Chiến lực: **{stats['power']}**"
        )
        await message.reply(embed=success_embed("✅ Đã tháo trang bị", message_text))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_market(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    from ui.views.market_view import MarketView
    view = MarketView(ctx.engine, str(message.author.id))
    await message.reply(embed=view.build_embed(), view=view)

async def cmd_market_list(ctx, message: discord.Message, args: list[str]) -> None:
    if len(args) < 3:
        await message.reply(embed=error_embed("Cách dùng: `.dangban <vật_phẩm> <số_lượng> <giá_mỗi_cái>`"))
        return
    try:
        r = ctx.engine.economy.market_list(str(message.author.id), args[0], int(args[1]), int(args[2]))
        await message.reply(embed=success_embed("✅ Đăng bán", f"#{r['listing_id']} **{r['item']['name']}** ×{r['qty']} · {fmt_amount(r['price_each'])}/cái · {fmt_amount(r['total'])} tổng"))
    except (GameError, ValueError) as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_market_buy(ctx, message: discord.Message, args: list[str]) -> None:
    if not args or not args[0].isdigit():
        await message.reply(embed=error_embed("Cách dùng: `.muacho <mã_tin>`"))
        return
    try:
        r = ctx.engine.economy.market_buy(str(message.author.id), int(args[0]))
        await message.reply(embed=success_embed("✅ Mua chợ", f"×{r['qty']} — trả {fmt_amount(r['total'])} (thuế {r['tax']})"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_market_cancel(ctx, message: discord.Message, args: list[str]) -> None:
    if not args or not args[0].isdigit():
        await message.reply(embed=error_embed("Cách dùng: `.huyban <mã_tin>`"))
        return
    try:
        r = ctx.engine.economy.market_cancel(str(message.author.id), int(args[0]))
        item_name = ITEMS.get(r["item_id"], {}).get("name", r["item_id"])
        await message.reply(embed=success_embed("✅ Hủy bán", f"Hoàn **{item_name}** ×{r['qty']}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_transfer(ctx, message: discord.Message, args: list[str]) -> None:
    if len(message.mentions) < 1 or len(args) < 2:
        await message.reply(embed=error_embed("Cách dùng: `.chuyen @người_chơi <số_linh_thạch>`"))
        return
    amount = next((int(a) for a in args if a.isdigit()), 0)
    try:
        ctx.engine.economy.transfer(str(message.author.id), str(message.mentions[0].id), amount)
        await message.reply(embed=success_embed("✅ Chuyển", f"{fmt_amount(amount)} {EMOJI['spirit_stone']}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_code(ctx, message: discord.Message, args: list[str]) -> None:
    if not args:
        await message.reply(embed=error_embed("Cách dùng: `.code <mã_thưởng>`"))
        return
    try:
        r = ctx.engine.economy.redeem_code(str(message.author.id), args[0])
        await message.reply(embed=success_embed("🎁 Mã thưởng", f"+{fmt_amount(r['stones'])} {EMOJI['spirit_stone']}"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))

async def cmd_gacha(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    try:
        r = ctx.engine.economy.gacha(str(message.author.id))
        name = r["item"].get("name", r["item_id"])
        await message.reply(embed=success_embed("🔮 Thiên Cơ", f"Nhận **{name}**"))
    except GameError as e:
        await message.reply(embed=error_embed(str(e)))


async def cmd_pvp(ctx, message: discord.Message, args: list[str] | None = None) -> None:
    from ui.views.pvp_view import PvpChallengeView, challenge_embed
    args = [arg for arg in (args or []) if not arg.startswith("<@")]
    if not message.mentions:
        await message.reply(embed=error_embed(
            "Cách dùng PvP cược:\n"
            "• `.pvp @người_chơi linhthach <số_lượng> [50|45|55]`\n"
            "• `.pvp @người_chơi vatpham <mã_vật_phẩm> <số_lượng> [50|45|55]`\n"
            "50 = cược ngang nhau; 45/55 = bên thách đấu góp 45% hoặc 55% tổng giá trị cược."
        ))
        return
    target = message.mentions[0]
    if target.bot:
        await message.reply(embed=error_embed("Không thể thách đấu bot hoặc tài khoản bot."))
        return
    try:
        if not args:
            raise ValueError("Thiếu loại cược.")
        kind = args[0].lower()
        if kind in ("linhthach", "lt", "stones"):
            if len(args) < 2 or not args[1].isdigit():
                raise ValueError("Thiếu số linh thạch cược.")
            amount = int(args[1])
            share = int(args[2]) if len(args) > 2 else 50
            challenge = ctx.engine.pvp.challenge(str(message.author.id), str(target.id), "stones", amount, challenger_share=share)
        elif kind in ("vatpham", "item"):
            if len(args) < 3 or not args[2].isdigit():
                raise ValueError("Cần mã vật phẩm và số lượng.")
            amount = int(args[2])
            share = int(args[3]) if len(args) > 3 else 50
            challenge = ctx.engine.pvp.challenge(str(message.author.id), str(target.id), "item", amount, item_id=args[1], challenger_share=share)
        else:
            raise ValueError("Loại cược chỉ nhận `linhthach` hoặc `vatpham`.")
        view = PvpChallengeView(ctx.engine, challenge)
        sent = await message.reply(embed=challenge_embed(challenge), view=view)
        view.message = sent
    except (GameError, ValueError) as exc:
        await message.reply(embed=error_embed(str(exc)))
