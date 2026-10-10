from __future__ import annotations

import unicodedata
from game.content.items import ITEMS, SHOP_ORDER


def normalize_search(value: str) -> str:
    """Normalize an item name/ID for forgiving Vietnamese search."""
    text = unicodedata.normalize("NFD", str(value or "").casefold())
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn").replace("đ", "d").strip()


def search_items(query: str = "", limit: int = 15) -> list[tuple[str, dict]]:
    """Return catalog items matched by ID, name, category or type."""
    query = str(query or "").strip()
    if limit < 1:
        return []
    if not query:
        return list(ITEMS.items())[:limit]
    q = normalize_search(query)
    exact = []
    starts = []
    contains = []
    for item_id, item in ITEMS.items():
        fields = [item_id, item.get("name", ""), item.get("category", ""), item.get("type", "")]
        normalized = [normalize_search(field) for field in fields]
        if q == normalized[0] or q == normalized[1]:
            exact.append((item_id, item))
        elif any(field.startswith(q) for field in normalized):
            starts.append((item_id, item))
        elif any(q in field for field in normalized):
            contains.append((item_id, item))
    return (exact + starts + contains)[:limit]


def category_items(category: str) -> list[tuple[str, dict]]:
    """Return items in a known category, preserving the canonical catalog order."""
    if category not in SHOP_ORDER:
        return []
    return [(item_id, item) for item_id, item in ITEMS.items() if item.get("category") == category]


def item_effect_lines(item: dict) -> list[str]:
    labels = {
        "cultivation": "Tu vi", "heal": "Hồi HP", "max_hp": "HP tối đa",
        "attack": "Công", "defense": "Thủ", "root": "Căn cơ",
        "insight": "Ngộ tính", "luck": "May mắn", "fate": "Khí vận",
        "mind": "Đạo tâm", "breakthrough_bonus": "Tỷ lệ đột phá",
        "thunder_resistance": "Kháng lôi", "technique_bonus": "Chỉ số công pháp",
        "skill_power": "Hệ số kỹ năng",
    }
    lines = []
    for key, label in labels.items():
        value = item.get(key)
        if value in (None, 0, 0.0):
            continue
        if key in {"breakthrough_bonus", "thunder_resistance"}:
            rendered = f"{float(value) * 100:g}%"
        elif key == "skill_power":
            rendered = f"×{float(value):.2f}"
        else:
            rendered = str(value)
        lines.append(f"• {label}: **{rendered}**")
    if not lines:
        lines.append("• Xem mô tả để biết cách sử dụng.")
    return lines
