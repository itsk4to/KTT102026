from __future__ import annotations


def defeat_penalty(realm_index: int) -> dict:
    """Non-permanent death: injury + small cultivation loss."""
    return {
        "injury": min(30, 5 + realm_index * 2),
        "cultivation_loss_pct": 0.02,
        "stones_loss_pct": 0.01,
    }


def apply_injury_cap(injury: int, cap: int = 100) -> int:
    return max(0, min(cap, injury))
