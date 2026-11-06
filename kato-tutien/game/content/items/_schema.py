"""Shared item schema — rarity ladder, slots, shop categories.

Update this file when adding a new item *kind*, not when adding a single item.
"""
from __future__ import annotations

EQUIP_SLOTS = ("weapon", "armor", "artifact", "accessory")

# Shop display order (also used by bag filters).
SHOP_ORDER = ["Đan dược", "Bùa chú", "Pháp bảo", "Binh khí", "Công pháp"]

RARITY_ORDER = ("Phàm", "Hoàng", "Huyền", "Địa", "Thiên")

# Role tags — used by docs/UI to explain *why* an item exists.
# Items should set exactly one primary purpose where possible.
ITEM_ROLES = {
    "cultivation": "Tăng tu vi (lấp đầy tầng trước khi đột phá)",
    "heal": "Hồi HP",
    "stat_root": "Củng cố Căn cơ",
    "stat_insight": "Củng cố Ngộ tính",
    "stat_luck": "Củng cố Vận khí",
    "stat_fate": "Củng cố Mệnh số",
    "stat_mind": "Củng cố Đạo tâm",
    "breakthrough": "Tăng tỉ lệ đột phá (chỉ dùng trong .dotpha)",
    "thunder_guard": "Giảm sát thương Cửu Lôi Kiếp",
    "combat_weapon": "Vũ khí — tăng công",
    "combat_armor": "Giáp — tăng thủ / HP",
    "combat_artifact": "Pháp bảo — cân bằng / kháng lôi",
    "combat_accessory": "Phụ kiện — chỉ số phụ",
    "technique": "Công pháp — kỹ năng chiến đấu + chỉ số vĩnh viễn",
    "combat_consumable": "Vật phẩm dùng trong trận",
}


def item(id_meta: dict) -> dict:
    """Normalize required fields and default flags."""
    data = dict(id_meta)
    data.setdefault("marketable", True)
    data.setdefault("description", "")
    return data
