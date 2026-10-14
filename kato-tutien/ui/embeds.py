from __future__ import annotations

import discord
from ui.colors import COLOR_MAIN, COLOR_SUCCESS, COLOR_ERROR, COLOR_INFO, COLOR_WARN
from ui.theme.embeds import create_embed
from ui.emoji import EMOJI
from game.utils import fmt_amount


def base_embed(title: str, description: str = "", color: int | None = None) -> discord.Embed:
    """Compatibility facade applying the shared game palette to every screen."""
    return create_embed(title, description, color)


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
    if preview.get("recovery_remaining", 0) > 0:
        status = f"{EMOJI.get('recover', '🩹')} Đang hồi phục · còn **{preview['recovery_remaining']}s**"
    else:
        status = "✅ Đủ tu vi" if preview["ready"] else "⏳ Chưa đủ tu vi"
    e = base_embed(f"{EMOJI['breakthrough']} Đột phá", f"**{preview['realm']}**\n{status}")
    e.add_field(name="Tu vi", value=f"{progress_bar(current, maximum)}\n{fmt_amount(current)} / {fmt_amount(maximum)}", inline=False)
    e.add_field(name="Tỷ lệ", value=f"{preview['chance']:.0%}", inline=True)
    pity_points = max(0, min(20, int(preview.get("pity_points", 0))))
    e.add_field(name="Bảo hộ tích lũy", value=f"+{pity_points} điểm phần trăm\nThất bại +5 · tối đa +20", inline=True)
    if preview.get("needs_tribulation"):
        e.add_field(name="Thiên kiếp", value="Cần Ứng Thiên Kiếp", inline=True)
    if preview.get("needs_thunder_tribulation"):
        e.add_field(
            name="⚡ Cửu Lôi Kiếp",
            value=(
                "Đột phá đại cảnh giới từ Kim Đan trở đi sẽ chịu **9 tia sét**. "
                "Mỗi tia mạnh hơn tia trước; hãy chuẩn bị **Lôi Kiếp Đan**, "
                "**Cửu Lôi Hộ Thân Phù** hoặc pháp bảo có kháng lôi."
            ),
            inline=False,
        )
        e.add_field(name="Khí huyết trước kiếp", value=f"{preview.get('current_hp', 0)}/{preview.get('max_hp', 0)} HP", inline=True)
        resistance = float(preview.get("thunder_equipment_resistance", 0.0))
        e.add_field(name="Kháng lôi từ pháp bảo", value=f"{resistance:.0%}", inline=True)
    return e


def player_embed(
    info: dict, *, combat_stats: dict | None = None, show_currency: bool = False
) -> discord.Embed:
    """Player HUD; private currency is opt-in and reserved for the self /info command."""
    p = info["player"]
    path_name = f"{EMOJI['faction_tien']} Tiên Đạo" if p.path == "tien" else f"{EMOJI['faction_ma']} Ma Đạo"
    stats = combat_stats or {"max_hp": p.max_hp, "attack": p.attack, "defense": p.defense}
    effective_max_hp = max(1, int(stats.get("max_hp", p.max_hp)))
    displayed_hp = min(max(0, int(p.hp)), effective_max_hp)
    hp_ratio = max(0.0, min(1.0, displayed_hp / effective_max_hp))

    e = base_embed(f"🧑‍🚀 HỒ SƠ TU SĨ · {p.display_name}", f"**{info['realm']}**\n{path_name}  ·  *Hồ sơ nhân vật / chỉ số thực chiến*")
    e.add_field(name="🌌 Cảnh giới", value=f"**{info['realm']}**", inline=True)
    if show_currency:
        e.add_field(name="🪙 Linh thạch", value=f"**{fmt_amount(p.spirit_stones)}**", inline=True)
    e.add_field(name="☯️ Đạo lộ", value=f"**{p.dao_type or 'Chưa khai Đạo'}**", inline=True)
    e.add_field(
        name="❤️ Khí huyết",
        value=f"`{progress_bar(displayed_hp, effective_max_hp, 10)}` **{hp_ratio:.0%}**\n{displayed_hp:,} / {effective_max_hp:,} HP",
        inline=False,
    )
    e.add_field(
        name="⚔️ Chiến lực thực tế",
        value=f"{EMOJI['att']} Công **{int(stats.get('attack', p.attack)):,}**\n{EMOJI['def']} Thủ **{int(stats.get('defense', p.defense)):,}**",
        inline=True,
    )
    e.add_field(
        name="🌱 Thiên phú",
        value=f"Căn cơ **{p.root}**\nNgộ tính **{p.insight}**",
        inline=True,
    )
    e.add_field(
        name="✨ Tu vi hiện tại",
        value=f"**{fmt_amount(p.cultivation)}**\n*Tiếp tục tu luyện để tích lũy đạo hạnh.*",
        inline=True,
    )
    return e


def public_player_embed(info: dict, *, combat_stats: dict | None = None) -> discord.Embed:
    """Public, privacy-filtered player card: no currency, inventory, or private stats."""
    from game.content.items import ITEMS, EQUIP_SLOTS

    p = info["player"]
    stats = combat_stats or {
        "max_hp": getattr(p, "max_hp", 100),
        "attack": getattr(p, "attack", 10),
        "defense": getattr(p, "defense", 5),
    }
    path_name = f"{EMOJI['faction_tien']} Tiên Đạo" if p.path == "tien" else f"{EMOJI['faction_ma']} Ma Đạo"
    power = (
        int(stats.get("attack", getattr(p, "attack", 10))) * 2
        + int(stats.get("defense", getattr(p, "defense", 5))) * 2
        + int(stats.get("max_hp", getattr(p, "max_hp", 100))) // 10
    )
    e = base_embed(
        f"🧑‍🚀 HỒ SƠ CÔNG KHAI · {p.display_name}",
        f"**{info['realm']}**\n{path_name} · *Hồ sơ công khai*",
    )
    e.add_field(name="🌌 Cảnh giới", value=f"**{info['realm']}**", inline=True)
    e.add_field(name="⚔️ Chiến lực", value=f"**{power:,}**", inline=True)
    e.add_field(name="🏯 Tông môn", value=f"**{'Đã gia nhập' if p.sect_id else 'Tán tu'}**", inline=True)

    slot_names = {"weapon": "Vũ khí", "artifact": "Pháp bảo", "armor": "Giáp", "accessory": "Phụ kiện"}
    gear_lines = []
    loadout = p.loadout or {}
    for slot in EQUIP_SLOTS:
        item_id = loadout.get(slot)
        item = ITEMS.get(item_id, {}) if item_id else {}
        gear_lines.append(f"• **{slot_names.get(slot, slot.title())}:** {item.get('name', 'Chưa trang bị')}")
    e.add_field(name="🛡️ Trang bị đang mặc", value="\n".join(gear_lines), inline=False)
    e.set_footer(text="Hồ sơ đạo hữu · Linh thạch và Túi Càn Khôn được giữ riêng tư")
    return e


def error_embed(msg: str) -> discord.Embed:
    return base_embed("❌ Lỗi", msg, COLOR_ERROR)


def success_embed(title: str, msg: str) -> discord.Embed:
    return base_embed(title, msg, COLOR_SUCCESS)


def shop_embed(catalog: dict) -> discord.Embed:
    """Opening screen for the category-first shop GUI."""
    category_icons = {"Đan dược": "💊", "Bùa chú": "🔮", "Pháp bảo": "💠", "Binh khí": "⚔️", "Công pháp": "📜"}
    categories = catalog.get("categories", [])
    lines = [
        "Một mùi linh dược thoang thoảng trong không khí, các kệ bảo vật trải dài trước mắt.",
        "Chủ tiệm vuốt râu, cười nói:",
        '*"Đạo hữu ghé Tiên Phường rồi! Muốn mua thứ gì? Cứ chọn loại vật phẩm bên dưới, ta sẽ lấy hàng cho đạo hữu xem."*',
        "",
        "**📦 Các quầy hàng**",
    ]
    lines.extend(
        f"{category_icons.get(cat['name'], '📦')} **{cat['name']}** · {len(cat.get('items', []))} vật phẩm"
        for cat in categories
    )
    lines.extend(["", f"{EMOJI['spirit_stone']} Mọi giao dịch dùng linh thạch. Hãy chọn danh mục ở menu bên dưới."])
    return base_embed(f"{EMOJI['shop']} Tiên Phường · Chưởng quầy đón khách", "\n".join(lines))


def combat_embed(enc, player=None, *, combat_stats: dict | None = None) -> discord.Embed:
    """Compact battle HUD; combat rules and callbacks are intentionally untouched."""
    color = COLOR_WARN if not enc.finished else (COLOR_SUCCESS if enc.victory else COLOR_ERROR)
    threat_label = "👑 BOSS · " if getattr(enc, "is_boss", False) else ""
    e = base_embed(f"{EMOJI.get('attack', '⚔️')} {threat_label}{enc.enemy_name}", color=color)
    player_attack = int((combat_stats or {}).get("attack", getattr(player, "attack", 0)))
    player_defense = int((combat_stats or {}).get("defense", getattr(player, "defense", 0)))
    enemy_hp = max(0, int(enc.enemy_hp))
    enemy_max = max(1, int(enc.enemy_max_hp))
    player_hp = max(0, int(enc.player_hp))
    player_max = max(1, int(enc.player_max_hp))
    enemy_ratio = min(1.0, enemy_hp / enemy_max)
    player_ratio = min(1.0, player_hp / player_max)

    e.add_field(
        name=f"{EMOJI.get('demon', '👹')} Đối thủ · {enc.enemy_name}",
        value=(f"{EMOJI['hp']} `{progress_bar(enemy_hp, enemy_max, 10)}` **{enemy_ratio:.0%}**\n"
               f"**{enemy_hp:,} / {enemy_max:,} HP**\n"
               f"{EMOJI['att']} Công **{int(enc.enemy_attack):,}**  ·  {EMOJI['def']} Thủ **{int(enc.enemy_defense):,}**"),
        inline=True,
    )
    e.add_field(
        name=f"{EMOJI.get('cultivator', '🧘')} Đạo hữu · {getattr(player, 'display_name', 'Đạo hữu')}",
        value=(f"{EMOJI['hp']} `{progress_bar(player_hp, player_max, 10)}` **{player_ratio:.0%}**\n"
               f"**{player_hp:,} / {player_max:,} HP**\n"
               f"{EMOJI['att']} Công **{player_attack:,}**  ·  {EMOJI['def']} Thủ **{player_defense:,}**"),
        inline=True,
    )
    turn = getattr(enc, "turn_number", None)
    if turn is not None:
        e.add_field(name="Lượt chiến đấu", value=f"`{int(turn)}`", inline=True)
    if enc.log:
        e.add_field(name="📜 Diễn biến trận đấu", value="\n".join(enc.log[-6:])[:1024], inline=False)
    if enc.finished:
        e.add_field(name="Kết cục", value=(f"{EMOJI.get('victory', '✅')} Đã chiến thắng" if enc.victory else f"{EMOJI.get('defeat', '❌')} Trận đấu kết thúc"), inline=False)
    else:
        e.add_field(name="Mệnh lệnh chiến đấu", value="Chọn **Công Pháp** hoặc **vật phẩm** ở danh sách phía trên, hoặc sử dụng nút hành động bên dưới.", inline=False)
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
    "heal": "HP hồi phục",
    "max_hp": "HP tối đa",
    "root": "Căn cơ",
    "insight": "Ngộ tính",
    "luck": "May mắn",
    "fate": "Mệnh số",
    "mind": "Đạo tâm",
    "all_stats": "Toàn bộ thuộc tính",
}


def _item_effect_lines(item: dict) -> list[str]:
    lines: list[str] = []
    for key in ("cultivation", "heal", "max_hp", "root", "insight", "luck", "fate", "mind", "all_stats"):
        value = item.get(key)
        if value:
            sign = "+" if value > 0 else ""
            lines.append(f"{_STAT_NAMES[key]}: {sign}{value}")
    if item.get("attack"):
        lines.append(f"Công: +{item['attack']}")
    if item.get("defense"):
        lines.append(f"Thủ: +{item['defense']}")
    if item.get("thunder_resistance"):
        lines.append(f"Kháng lôi: +{item['thunder_resistance']:.0%}")
    if item.get("breakthrough_bonus"):
        lines.append(f"Tỷ lệ đột phá: +{item['breakthrough_bonus']:.0%}")
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
    page_size: int = 12,
    category: str = "Tất cả",
    selected: dict | None = None,
    notice: str | None = None,
) -> discord.Embed:
    total_quantity = sum(int(item.get("qty", 0)) for item in items)
    max_page = max(0, (len(items) - 1) // max(1, page_size))
    page = max(0, min(page, max_page))
    start = page * page_size
    visible = items[start:start + page_size]

    description = (
        f"**TÚI CÀN KHÔN**  ·  {category}\n"
        f"{len(items)} loại vật phẩm  ·  Tổng cộng **{total_quantity:,}** món\n"
        "*Chọn danh mục → chọn món → xem chỉ số → thao tác.*"
    )
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
        embed.add_field(name="🔎 Vật phẩm đang chọn", value="\n".join(details)[:1024], inline=False)

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
        embed.add_field(name=f"📦 Danh sách · {start + 1}–{start + len(visible)}", value="\n".join(lines)[:1024], inline=False)

    if max_page > 0:
        footer = f"TÚI CÀN KHÔN · Trang {page + 1}/{max_page + 1} · Chọn loại → chọn món → thao tác"
    else:
        footer = "TÚI CÀN KHÔN · Chọn loại → chọn món → thao tác nhanh"
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
    e.set_footer(text=f"ID: {item['id']}")
    return e
