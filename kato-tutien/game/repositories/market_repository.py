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

    def create(self, seller_id: str, item_id: str, quantity: int, price_total: int, unit_price: int) -> int:
        cur = self.db.execute(
            "INSERT INTO market_listings(seller_id, item_id, quantity, price, unit_price, created_at) VALUES(?,?,?,?,?,?)",
            (seller_id, item_id, quantity, price_total, unit_price, int(time.time())),
        )
        return int(cur.lastrowid)

    def delete(self, listing_id: int) -> bool:
        """Delete by id. Returns True only when a row was actually removed."""
        cur = self.db.execute("DELETE FROM market_listings WHERE id=?", (listing_id,))
        return cur.rowcount == 1

    def claim(self, listing_id: int) -> MarketListing | None:
        """Atomically take ownership of a listing for purchase/cancel.

        SELECT + DELETE under the same write transaction / process lock.
        Returns None if the listing is already gone (prevents double-buy).
        """
        row = self.db.fetchone("SELECT * FROM market_listings WHERE id=?", (listing_id,))
        if not row:
            return None
        cur = self.db.execute("DELETE FROM market_listings WHERE id=?", (listing_id,))
        if cur.rowcount != 1:
            return None
        return MarketListing.from_row(row)

    def claim_owned(self, listing_id: int, seller_id: str) -> MarketListing | None:
        """Claim a listing only if it still belongs to seller_id."""
        row = self.db.fetchone(
            "SELECT * FROM market_listings WHERE id=? AND seller_id=?",
            (listing_id, seller_id),
        )
        if not row:
            return None
        cur = self.db.execute(
            "DELETE FROM market_listings WHERE id=? AND seller_id=?",
            (listing_id, seller_id),
        )
        if cur.rowcount != 1:
            return None
        return MarketListing.from_row(row)
