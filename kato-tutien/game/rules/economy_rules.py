from __future__ import annotations

from config import MARKET_TAX_RATE


def seller_gain(total: int) -> int:
    return int(total * (1.0 - MARKET_TAX_RATE))


def tax_amount(total: int) -> int:
    return total - seller_gain(total)


def can_afford(balance: int, cost: int) -> bool:
    return balance >= cost and cost >= 0


def stone_loot_multiplier(luck: int | float) -> float:
    """Bound luck's extra stone yield to +25% to avoid runaway currency inflation."""
    return 1.0 + min(0.25, max(0.0, float(luck)) / 400.0)
