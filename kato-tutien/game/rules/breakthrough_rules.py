from __future__ import annotations

import math

from game.content.realms import REALMS, TRIBULATION_REALM_INDEX

# Failed breakthroughs impose a recovery lock before the cultivator can
# cultivate again. Durations are intentionally data-driven by major realm.
# The lock is based on the realm being attempted, not the realm after success.
RECOVERY_SECONDS_BY_REALM = {
    0: 0,       # Phàm Nhân
    1: 60,      # Luyện Khí
    2: 120,     # Trúc Cơ
    3: 300,     # Kim Đan
    4: 600,     # Nguyên Anh
    5: 900,     # Hóa Thần
    6: 1200,    # Luyện Hư
    7: 1800,    # Hợp Thể
    8: 3600,    # Đại Thừa
    9: 7200,    # Độ Kiếp
    10: 10800,  # Chân Tiên
    11: 14400,  # Thiên Tiên
    12: 21600,  # Tiên Vương
    13: 28800,  # Tiên Đế
}


def breakthrough_recovery_seconds(realm_index: int, realm_layer: int = 1, *, tribulation: bool = False) -> int:
    """Return the recovery lock after a failed breakthrough.

    Higher major realms require longer recovery. Near the end of a realm,
    failure is slightly more taxing, so the final layer adds 25%. Tribulation
    failure is more severe and adds another 50%.
    """
    base = int(RECOVERY_SECONDS_BY_REALM.get(int(realm_index), 28800))
    if base <= 0:
        return 0
    # Only the final layer gets the extra penalty; avoid punishing every layer.
    if int(realm_layer) >= 9:
        base = int(base * 1.25)
    if tribulation:
        base = int(base * 1.50)
    return base


def apply_failure_injury(current: int, base_penalty: int, multiplier: float = 1.0) -> int:
    """Return clamped injury after a failed breakthrough."""
    return max(0, min(100, int(current) + max(0, round(int(base_penalty) * float(multiplier)))))


def requires_nine_thunder_tribulation(realm_index: int, realm_layer: int) -> bool:
    """Whether this is a major-realm breakthrough subject to Cửu Lôi Kiếp.

    The first thunder tribulation is Kim Đan -> Nguyên Anh. The same rule
    applies to both cultivation paths because both use the canonical realm tree.
    Độ Kiếp's final ascension remains on the separate Ứng Thiên Kiếp flow.
    """
    index = int(realm_index)
    layer = int(realm_layer)
    if index < 3 or index >= TRIBULATION_REALM_INDEX or index >= len(REALMS):
        return False
    _, layer_count = REALMS[index]
    return layer >= int(layer_count)


def thunder_strike_damage(
    max_hp: int, target_realm_index: int, strike_number: int,
    defense: int = 0, resistance: float = 0.0, previous_damage: int = 0,
) -> int:
    """Calculate a rising but predictable Cửu Lôi strike after protection.

    Each later strike gains 3.5% raw force. Defense mitigates part of the
    impact, while consumables/equipment contribute explicit resistance.
    """
    hp = max(1, int(max_hp))
    target_index = max(1, int(target_realm_index))
    strike = max(1, min(9, int(strike_number)))
    base_ratio = 0.08 + target_index * 0.014
    raw = math.ceil(hp * base_ratio * (1.0 + (strike - 1) * 0.035))
    defense_value = max(0, int(defense))
    defense_reduction = min(0.35, defense_value / (defense_value + 280 + target_index * 30))
    total_reduction = min(0.65, max(0.0, float(resistance)) + defense_reduction)
    mitigated = max(1, math.ceil(raw * (1.0 - total_reduction)))
    # Even a heavily protected cultivator can see each successive strike rise.
    return max(mitigated, int(previous_damage) + 1)
