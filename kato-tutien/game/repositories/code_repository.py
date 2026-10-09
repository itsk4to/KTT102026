from __future__ import annotations

from game.database.connection import Database


class CodeRepository:
    def __init__(self, db: Database):
        self.db = db

    def get(self, code: str):
        row = self.db.fetchone("SELECT * FROM redeem_codes WHERE code=?", (code,))
        return dict(row) if row else None

    def exists(self, code: str) -> bool:
        return self.get(code) is not None

    def create(self, code: str, stones: int, item_id: str | None, qty: int, max_uses: int) -> None:
        self.db.execute(
            "INSERT INTO redeem_codes(code,reward_stones,reward_item,reward_qty,max_uses,used_count) VALUES(?,?,?,?,?,0)",
            (code, stones, item_id, qty, max_uses),
        )

    def increment_used(self, code: str) -> None:
        self.db.execute("UPDATE redeem_codes SET used_count=used_count+1 WHERE code=?", (code,))

    def disable(self, code: str) -> bool:
        cur = self.db.execute(
            "UPDATE redeem_codes SET enabled=0 WHERE code=? AND enabled=1",
            (code,),
        )
        return cur.rowcount > 0
