"""Vật phẩm dùng trong trận — tách riêng khỏi đan dược shop."""
from __future__ import annotations

from game.content.items._schema import item

COMBAT_ITEMS: dict[str, dict] = {
    "boom_heal_small": item({
        "category": "Đan dược", "name": "Hồi Huyết Tán", "rarity": "Phàm",
        "type": "combat_item", "role": "combat_consumable", "price": 800,
        "heal": 40,
        "description": "Tán dược chiến đấu. Hồi 40 HP trong trận.",
    }),
}
