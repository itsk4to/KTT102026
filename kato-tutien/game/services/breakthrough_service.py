from __future__ import annotations

from game.repositories.inventory_repository import InventoryRepository
from game.services.errors import GameError


class BreakthroughService:
    """Transactional breakthrough facade. Item selection is preview-only;
    consumption happens only after the player confirms the breakthrough."""

    def __init__(self, cultivation, players, inventory):
        self.cultivation = cultivation
        self.players = players
        self.inventory = inventory

    def preview_item(self, user_id: str, item_id: str) -> dict:
        return self.cultivation.breakthrough_item_bonus(user_id, item_id)

    def breakthrough(self, user_id: str, bonus: float = 0.0, item_id: str | None = None) -> dict:
        with self.players.transaction():
            if item_id:
                meta = self.preview_item(user_id, item_id)
                if not self.inventory.remove(user_id, item_id, 1):
                    raise GameError("Không thể tiêu hao đạo cụ.")
                bonus = float(meta["bonus"])
            return self.cultivation.breakthrough(user_id, bonus)
