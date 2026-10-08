from __future__ import annotations

from config import MARKET_TAX_RATE


def seller_gain(total: int) -> int:
    return int(total * (1.0 - MARKET_TAX_RATE))


def tax_amount(total: int) -> int:
    return total - seller_gain(total)


def can_afford(balance: int, cost: int) -> bool:
    return balance >= cost and cost >= 0
