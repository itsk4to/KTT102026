"""Item catalog aggregate.

Thêm vật phẩm mới: sửa đúng file con (pills / talismans / equipment / …),
không nhét vào một file khổng lồ.

Public API giữ nguyên: ITEMS, SHOP_ORDER, SHOP_CATEGORIES, EQUIP_SLOTS, item_slot.
"""
from __future__ import annotations

from game.content.items._schema import EQUIP_SLOTS, SHOP_ORDER, ITEM_ROLES
from game.content.items.pills import PILLS
from game.content.items.talismans import TALISMANS
from game.content.items.equipment import EQUIPMENT
from game.content.items.techniques import TECHNIQUES
from game.content.items.combat_items import COMBAT_ITEMS

ITEMS: dict[str, dict] = {}
ITEMS.update(PILLS)
ITEMS.update(TALISMANS)
ITEMS.update(EQUIPMENT)
ITEMS.update(TECHNIQUES)
ITEMS.update(COMBAT_ITEMS)

SHOP_CATEGORIES = {
    cat: [iid for iid, it in ITEMS.items() if it.get("category") == cat and it.get("price")]
    for cat in SHOP_ORDER
}


def item_slot(item_id: str) -> str | None:
    item = ITEMS.get(item_id) or {}
    return item.get("slot")


__all__ = [
    "ITEMS",
    "SHOP_ORDER",
    "SHOP_CATEGORIES",
    "EQUIP_SLOTS",
    "ITEM_ROLES",
    "item_slot",
    "PILLS",
    "TALISMANS",
    "EQUIPMENT",
    "TECHNIQUES",
    "COMBAT_ITEMS",
]
