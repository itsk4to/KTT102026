from __future__ import annotations

from game.database.connection import Database
from game.models.item import ItemStack


class InventoryRepository:
    def __init__(self, db: Database):
        self.db = db

    def get_count(self, user_id: str, item_id: str) -> int:
        row = self.db.fetchone(
            "SELECT quantity FROM inventory WHERE user_id=? AND item_id=?",
            (user_id, item_id),
        )
        return int(row["quantity"]) if row else 0

    def list_items(self, user_id: str) -> list[ItemStack]:
        rows = self.db.fetchall(
            "SELECT item_id, quantity FROM inventory WHERE user_id=? AND quantity>0",
            (user_id,),
        )
        return [ItemStack(item_id=r["item_id"], quantity=int(r["quantity"])) for r in rows]

    def add(self, user_id: str, item_id: str, qty: int = 1) -> int:
        current = self.get_count(user_id, item_id)
        new = current + qty
        self.db.execute(
            """INSERT INTO inventory(user_id, item_id, quantity) VALUES(?,?,?)
               ON CONFLICT(user_id, item_id) DO UPDATE SET quantity=excluded.quantity""",
            (user_id, item_id, new),
        )
        return new

    def remove(self, user_id: str, item_id: str, qty: int = 1) -> bool:
        current = self.get_count(user_id, item_id)
        if current < qty:
            return False
        new = current - qty
        if new <= 0:
            self.db.execute(
                "DELETE FROM inventory WHERE user_id=? AND item_id=?",
                (user_id, item_id),
            )
        else:
            self.db.execute(
                "UPDATE inventory SET quantity=? WHERE user_id=? AND item_id=?",
                (new, user_id, item_id),
            )
        return True
