from __future__ import annotations

import random
from game.content.techniques import STATUS_EFFECTS


def hit_chance(accuracy: float, evasion: float) -> float:
    """Bounded 35%–97%."""
    raw = 0.75 + (accuracy - evasion) * 0.004
    return max(0.35, min(0.97, raw))


def calculate_damage(
    attack: int,
    defense: int,
    *,
    power: float = 1.0,
    variance: float = 0.12,
    rng: random.Random | None = None,
) -> int:
    rng = rng or random.Random()
    mitigated = max(1, attack - defense * 0.55)
    roll = 1.0 + rng.uniform(-variance, variance)
    return max(1, int(mitigated * power * roll))


def mastery_multiplier(mastery: int) -> float:
    return 1.0 + min(0.12, mastery * 0.01)


def mastery_stage(mastery: int) -> str:
    if mastery >= 12:
        return "Viên mãn"
    if mastery >= 8:
        return "Đại thành"
    if mastery >= 4:
        return "Tiểu thành"
    return "Nhập môn"


def status_on_hit_chance(base: float = 0.14) -> float:
    return base


def tick_dot(max_hp: int, potency: float) -> int:
    return max(1, int(max_hp * potency))


def apply_shield(damage: int, shield_factor: float) -> int:
    return max(1, int(damage * (1.0 - shield_factor)))
