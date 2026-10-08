from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ItemStack:
    item_id: str
    quantity: int
    meta: dict | None = None
