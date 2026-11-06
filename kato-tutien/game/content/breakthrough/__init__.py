"""Breakthrough content & item roles.

Logic tính tỉ lệ: game.rules.cultivation_rules.breakthrough_chance
Flow thực thi: game.services.cultivation_service / breakthrough_service

Vật phẩm liên quan chỉ có 2 vai trò:
  • foundation  → field breakthrough_bonus (dùng trong UI .dotpha)
  • thunder     → field thunder_resistance (hộ Cửu Lôi khi đột phá đại cảnh)
"""
from __future__ import annotations

from game.content.items import ITEMS

# 5 chỉ số gốc quyết định tỉ lệ đột phá (thứ tự trọng số trong rules).
BREAKTHROUGH_STATS = ("root", "luck", "mind", "insight", "fate")

STAT_LABELS = {
    "root": "Căn cơ",
    "insight": "Ngộ tính",
    "luck": "Vận khí",
    "fate": "Mệnh số",
    "mind": "Đạo tâm",
}


def foundation_items() -> list[tuple[str, dict]]:
    return [
        (iid, it) for iid, it in ITEMS.items()
        if float(it.get("breakthrough_bonus") or 0) > 0
    ]


def thunder_guard_items() -> list[tuple[str, dict]]:
    return [
        (iid, it) for iid, it in ITEMS.items()
        if float(it.get("thunder_resistance") or 0) > 0 and it.get("type") == "consumable"
    ]


__all__ = [
    "BREAKTHROUGH_STATS",
    "STAT_LABELS",
    "foundation_items",
    "thunder_guard_items",
]
