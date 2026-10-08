from __future__ import annotations

import discord
from ui.colors import COLOR_MAIN, COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, COLOR_WARN
from ui.emoji import EMOJI
from game.utils import fmt_amount


def base_embed(title: str, description: str = "", color: int = COLOR_MAIN) -> discord.Embed:
    return discord.Embed(title=title, description=description, color=color)


def progress_bar(current: int, maximum: int, size: int = 10) -> str:
    maximum = max(1, maximum)
    ratio = max(0.0, min(1.0, current / maximum))
    filled = int(ratio * size)
    return "▰" * filled + "▱" * (size - filled)


def cultivation_embed(result: dict, *, action: str = "Tu luyện") -> discord.Embed:
    p = result["player"]
    current = int(result.get("cultivation", p.cultivation))
    maximum = int(result.get("requirement", max(current, 1)))
    e = base_embed(f"{EMOJI['cultivate']} {action}", f"**{result.get('realm', 'Tu sĩ')}**")
    e.add_field(name="Tu vi", value=f"{progress_bar(current, maximum)}\n**{fmt_amount(current)}** / {fmt_amount(maximum)}", inline=False)
    if result.get("gain") is not None:
        e.add_field(name="Thu hoạch", value=f"+{fmt_amount(result['gain'])} tu vi", inline=True)
    e.add_field(name="Cảnh giới", value=result.get("realm", "—"), inline=True)
    return e


def cultivation_preview_embed(preview: dict) -> discord.Embed:
    current = int(preview["cultivation"])
    maximum = int(preview["requirement"])
    status = "✅ Đủ tu vi" if preview["ready"] else "⏳ Chưa đủ tu vi"
    e = base_embed(f"{EMOJI['breakthrough']} Đột phá", f"**{preview['realm']}**\n{status}")
    e.add_field(name="Tu vi", value=f"{progress_bar(current, maximum)}\n{fmt_amount(current)} / {fmt_amount(maximum)}", inline=False)
    e.add_field(name="Tỷ lệ", value=f"{preview['chance']:.0%}", inline=True)
    if preview.get("needs_tribulation"):
        e.add_field(name="Thiên kiếp", value="Cần Ứng Thiên Kiếp", inline=True)
    return e


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

_ITEM_TYPE_NAMES = {
    "consumable": "Đan dược / vật phẩm dùng",
    "combat_item": "Vật phẩm chiến đấu",
    "equipment": "Trang bị",
    "technique": "Công pháp",
}
_SLOT_NAMES = {
    "weapon": "Vũ khí",
    "artifact": "Pháp bảo",
    "armor": "Hộ giáp",
    "accessory": "Phụ kiện",
}
_STAT_NAMES = {
    "cultivation": "Tu vi",
    "heal": "HP",
    "root": "Căn cơ",
    "insight": "Ngộ tính",
    "luck": "May mắn",
    "fate": "Mệnh số",
    "mind": "Đạo tâm",
    "all_stats": "Toàn bộ thuộc tính",
}


def _item_effect_lines(item: dict) -> list[str]:
    lines: list[str] = []
    for key in ("cultivation", "heal", "root", "insight", "luck", "fate", "mind", "all_stats"):
        value = item.get(key)
        if value:
            sign = "+" if value > 0 else ""
            lines.append(f"{_STAT_NAMES[key]}: {sign}{value}")
    if item.get("attack"):
        lines.append(f"Công: +{item['attack']}")
    if item.get("defense"):
        lines.append(f"Thủ: +{item['defense']}")
    if item.get("technique_stat") and item.get("technique_bonus"):
        stat_name = _STAT_NAMES.get(item["technique_stat"], item["technique_stat"])
        lines.append(f"Học được: +{item['technique_bonus']} {stat_name}")
    if item.get("skill_power"):
        lines.append(f"Sức mạnh kỹ năng: ×{item['skill_power']:.2f}")
    return lines


def inventory_item_icon(item: dict) -> str:
    meta = item.get("meta", {})
    item_type = meta.get("type")
    if item_type == "technique":
        return EMOJI["technique"]
    if item_type == "equipment":
        slot = meta.get("slot")
        if slot == "weapon":
            return EMOJI["weapon"]
        return EMOJI["equipment"]
    if item_type in {"consumable", "combat_item"}:
        return EMOJI["combat_item"] if item_type == "combat_item" else EMOJI["consumable"]
    if meta.get("category") == "Bùa chú":
        return EMOJI["talisman"]
    return EMOJI["unknown"]


def inventory_embed(
    items: list[dict],
    *,
    page: int = 0,
    page_size: int = 20,
    category: str = "Tất cả",
    selected: dict | None = None,
    notice: str | None = None,
) -> discord.Embed:
    total_quantity = sum(int(item.get("qty", 0)) for item in items)
    max_page = max(0, (len(items) - 1) // max(1, page_size))
    page = max(0, min(page, max_page))
    start = page * page_size
    visible = items[start:start + page_size]

    description = f"Loại vật phẩm: **{category}**\n\n**{len(items)} loại vật phẩm** · {total_quantity} món"
    if notice:
        description = f"{notice}\n\n{description}"

    embed = base_embed(f"{EMOJI['item']} TÚI CÀN KHÔN", description)

    if selected:
        icon = inventory_item_icon(selected)
        meta = selected.get("meta", {})
        rarity = meta.get("rarity", "Phàm")
        details = [
            f"{icon} **{selected['name']}** ×{selected['qty']} · {rarity}",
            meta.get("description", "Không có mô tả."),
        ]
        effects = _item_effect_lines(meta)
        if effects:
            details.append("\n".join(f"• {line}" for line in effects[:5]))
        embed.add_field(name="Vật phẩm đang chọn", value="\n".join(details), inline=False)

    if not visible:
        embed.add_field(name="Kho đồ", value="Túi đồ đang trống.", inline=False)
    else:
        lines = []
        for offset, item in enumerate(visible, start=start + 1):
            meta = item.get("meta", {})
            rarity = meta.get("rarity", "Phàm")
            icon = inventory_item_icon(item)
            marker = " ◀" if selected and item.get("id") == selected.get("id") else ""
            lines.append(f"`{offset:02d}` {icon} **{item['name']}** ×{item['qty']} · {rarity}{marker}")
        embed.add_field(name="Danh sách vật phẩm", value="\n".join(lines), inline=False)

    if max_page > 0:
        footer = f"Trang {page + 1}/{max_page + 1} · Chọn loại → chọn vật phẩm → thao tác"
    else:
        footer = "Chọn loại → chọn vật phẩm → thao tác nhanh"
    embed.set_footer(text=footer)
    return embed


def inventory_item_embed(item: dict) -> discord.Embed:
    meta = item.get("meta", {})
    item_type = _ITEM_TYPE_NAMES.get(meta.get("type"), "Vật phẩm")
    e = base_embed(f"{inventory_item_icon(item)} {item['name']}", meta.get("description", "Không có mô tả."))
    e.add_field(name="Phẩm chất", value=meta.get("rarity", "Phàm"), inline=True)
    e.add_field(name="Loại", value=item_type, inline=True)
    e.add_field(name="Số lượng", value=f"×{item['qty']}", inline=True)

    if meta.get("slot"):
        e.add_field(name="Vị trí", value=_SLOT_NAMES.get(meta["slot"], meta["slot"]), inline=True)

    effects = _item_effect_lines(meta)
    if effects:
        e.add_field(name="Tác dụng", value="\n".join(f"• {line}" for line in effects), inline=False)
    e.set_footer(text=f"Mã vật phẩm: {item['id']}")
    return e
