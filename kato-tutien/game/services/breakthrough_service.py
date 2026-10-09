from __future__ import annotations

from game.content.items import ITEMS
from game.services.errors import GameError


class BreakthroughService:
    """Transactional breakthrough facade.

    Breakthrough support items are consumed when the player confirms. Thunder
    protection is only consumed if the normal breakthrough roll succeeds and
    Cửu Lôi Kiếp actually starts.
    """

    def __init__(self, cultivation, players, inventory):
        self.cultivation = cultivation
        self.players = players
        self.inventory = inventory

    def preview_item(self, user_id: str, item_id: str) -> dict:
        return self.cultivation.breakthrough_item_bonus(user_id, item_id)

    @staticmethod
    def stacked_thunder_resistance(base_resistance: float, quantity: int) -> float:
        """Additional doses stack with diminishing returns (50% per extra dose)."""
        doses = max(1, min(3, int(quantity)))
        return min(0.40, max(0.0, float(base_resistance)) * (1 + 0.5 * (doses - 1)))

    def thunder_protection_items(self, user_id: str) -> list[dict]:
        """List owned consumables that can protect against Cửu Lôi Kiếp."""
        result = []
        for stack in self.inventory.list_items(user_id):
            item = ITEMS.get(stack.item_id, {})
            resistance = float(item.get("thunder_resistance", 0.0))
            if item.get("type") == "consumable" and resistance > 0:
                result.append({
                    "id": stack.item_id,
                    "name": item.get("name", stack.item_id),
                    "qty": int(stack.quantity),
                    "resistance": resistance,
                    "item": item,
                })
        return result

    def breakthrough(
        self, user_id: str, bonus: float = 0.0, item_id: str | None = None,
        thunder_items: list[str] | None = None,
    ) -> dict:
        with self.players.transaction():
            selected_thunder_items = list(thunder_items or [])
            protection = []
            seen_item_ids = set()
            for selection in selected_thunder_items:
                if "::" in selection:
                    selected_id, quantity_text = selection.rsplit("::", 1)
                    try:
                        quantity = int(quantity_text)
                    except ValueError as exc:
                        raise GameError("Số lượng vật phẩm hộ kiếp không hợp lệ.") from exc
                else:
                    selected_id, quantity = selection, 1
                if selected_id in seen_item_ids:
                    raise GameError("Hãy chọn một mức số lượng duy nhất cho mỗi loại đan/bùa.")
                seen_item_ids.add(selected_id)
                meta = ITEMS.get(selected_id) or {}
                base_resistance = float(meta.get("thunder_resistance", 0.0))
                if meta.get("type") != "consumable" or base_resistance <= 0:
                    raise GameError("Vật phẩm được chọn không có tác dụng hộ Cửu Lôi Kiếp.")
                if quantity < 1 or quantity > 3:
                    raise GameError("Mỗi loại đan/bùa chỉ có thể dùng tối đa 3 liều trong một lần hộ kiếp.")
                if self.inventory.get_count(user_id, selected_id) < quantity:
                    raise GameError(f"Không đủ **{meta.get('name', selected_id)}** trong túi.")
                resistance = self.stacked_thunder_resistance(base_resistance, quantity)
                protection.append({
                    "id": selected_id,
                    "quantity": quantity,
                    "name": meta.get("name", selected_id),
                    "resistance": resistance,
                    "base_resistance": base_resistance,
                })

            if item_id:
                meta = self.preview_item(user_id, item_id)
                if not self.inventory.remove(user_id, item_id, 1):
                    raise GameError("Không thể tiêu hao đạo cụ.")
                bonus = float(meta["bonus"])

            result = self.cultivation.breakthrough(
                user_id,
                bonus,
                thunder_resistance=sum(x["resistance"] for x in protection),
                thunder_item_names=[f"{x['name']} ×{x['quantity']}" for x in protection],
            )
            thunder = result.get("thunder_tribulation")
            if thunder and thunder.get("attempted"):
                consumed = []
                for entry in protection:
                    if not self.inventory.remove(user_id, entry["id"], entry["quantity"]):
                        raise GameError(f"Không thể tiêu hao **{entry['name']}** để hộ kiếp.")
                    consumed.append(f"{entry['name']} ×{entry['quantity']}")
                result["consumed_thunder_items"] = consumed
            else:
                result["consumed_thunder_items"] = []
            return result
