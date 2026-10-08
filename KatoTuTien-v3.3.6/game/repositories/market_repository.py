from __future__ import annotations

import time
from game.database.connection import Database
from game.models.economy import MarketListing


class MarketRepository:
    def __init__(self, db: Database):
        self.db = db

    def list_all(self, limit: int = 50) -> list[MarketListing]:
        rows = self.db.fetchall(
            "SELECT * FROM market_listings ORDER BY id DESC LIMIT ?",
            (limit,),
        )
        return [MarketListing.from_row(r) for r in rows]

    def get(self, listing_id: int) -> MarketListing | None:
        row = self.db.fetchone("SELECT * FROM market_listings WHERE id=?", (listing_id,))
        return MarketListing.from_row(row) if row else None

    def create(self, seller_id: str, item_id: str, quantity: int, price: int) -> int:
        cur = self.db.execute(
            "INSERT INTO market_listings(seller_id, item_id, quantity, price, created_at) VALUES(?,?,?,?,?)",
            (seller_id, item_id, quantity, price, int(time.time())),
        )
        return int(cur.lastrowid)

    def delete(self, listing_id: int) -> None:
        self.db.execute("DELETE FROM market_listings WHERE id=?", (listing_id,))
