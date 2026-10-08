from __future__ import annotations

import discord
from ui.colors import COLOR_MAIN, COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, COLOR_WARN
from ui.emoji import EMOJI
from game.utils import fmt_amount


def base_embed(title: str, description: str = "", color: int = COLOR_MAIN) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)


def player_embed(info: dict) -> discord.Embed:
    p = info["player"]
    e = base_embed(f"👤 {p.display_name}", color=COLOR_INFO)
    e.add_field(name="Cảnh giới", value=info["realm"], inline=True)
    e.add_field(name="Con đường", value="Tiên" if p.path == "tien" else "Ma", inline=True)
    e.add_field(name="Tu vi", value=fmt_amount(p.cultivation), inline=True)
    e.add_field(name=f"{EMOJI['spirit_stone']} Linh thạch", value=fmt_amount(p.spirit_stones), inline=True)
    e.add_field(name="Căn cơ", value=str(p.root), inline=True)
    e.add_field(name="Ngộ tính", value=str(p.insight), inline=True)
    e.add_field(name=f"{EMOJI['hp']} HP", value=f"{p.hp}/{p.max_hp}", inline=True)
    e.add_field(name=f"{EMOJI['att']} Công", value=str(p.attack), inline=True)
    e.add_field(name=f"{EMOJI['def']} Thủ", value=str(p.defense), inline=True)
    if p.dao_type:
        e.add_field(name="Đạo", value=p.dao_type, inline=True)
    return e


def error_embed(msg: str) -> discord.Embed:
    return base_embed("❌ Lỗi", msg, COLOR_ERROR)


def success_embed(title: str, msg: str) -> discord.Embed:
    return base_embed(title, msg, COLOR_SUCCESS)


def shop_embed(catalog: dict) -> discord.Embed:
    e = base_embed(f"{EMOJI['shop']} Tiên Phường", "Chọn danh mục bên dưới để xem và mua.")
    for cat in catalog.get("categories", []):
        lines = [f"• **{it['name']}** — {fmt_amount(it['price'])} {EMOJI['spirit_stone']}" for it in cat["items"][:8]]
        if lines:
            e.add_field(name=cat["name"], value="\n".join(lines), inline=False)
    return e


def combat_embed(enc) -> discord.Embed:
    color = COLOR_WARN if not enc.finished else (COLOR_SUCCESS if enc.victory else COLOR_ERROR)
    e = base_embed(f"{EMOJI['attack']} {enc.enemy_name}", color=color)
    e.add_field(name="Địch HP", value=f"{enc.enemy_hp}/{enc.enemy_max_hp}", inline=True)
    e.add_field(name="Bạn HP", value=f"{enc.player_hp}/{enc.player_max_hp}", inline=True)
    if enc.log:
        e.add_field(name="Diễn biến", value="\n".join(enc.log[-6:]), inline=False)
    return e
