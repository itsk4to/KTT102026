from __future__ import annotations

from dataclasses import dataclass


@dataclass
class MarketListing:
    id: int
    seller_id: str
    item_id: str
    quantity: int
    price: int
    created_at: int

    @classmethod
    def from_row(cls, row) -> "MarketListing":
        return cls(
            id=int(row["id"]),
            seller_id=row["seller_id"],
            item_id=row["item_id"],
            quantity=int(row["quantity"]),
            price=int(row["price"]),
            created_at=int(row["created_at"]),
        )
