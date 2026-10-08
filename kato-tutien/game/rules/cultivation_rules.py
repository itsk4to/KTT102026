from __future__ import annotations

from game.content.realms import REALMS, cultivation_requirement, minor_realm_name


def realm_text(realm_index: int, layer: int) -> str:
    if realm_index < 0 or realm_index >= len(REALMS):
        return "Không rõ"
    name, layers = REALMS[realm_index]
    if layers <= 1:
        return name
    return f"{name} · {minor_realm_name(layer, layers)}"


def is_max_realm(realm_index: int, layer: int) -> bool:
    if realm_index >= len(REALMS) - 1:
        name, layers = REALMS[-1]
        return layer >= layers
    return False


def headroom(cultivation: int, realm_index: int, layer: int) -> int:
    req = cultivation_requirement(realm_index, layer)
    return max(0, req - cultivation)


def soft_cap_stat(current: int, requested: int, hard_cap: int = 100) -> int:
    if current >= hard_cap:
        return 0
    room = hard_cap - current
    if current >= 80:
        requested = max(1, requested // 3)
    elif current >= 60:
        requested = max(1, requested // 2)
    return min(room, max(0, requested))


def breakthrough_chance(
    *,
    root: int,
    mind: int,
    insight: int,
    injury: int,
    dao_stage: int,
    foundation_bonus: float = 0.0,
) -> float:
    base = 0.35 + root * 0.004 + mind * 0.003 + insight * 0.002 + dao_stage * 0.02
    base += foundation_bonus
    base -= injury * 0.01
    return max(0.05, min(0.92, base))


def cultivate_gain(root: int, insight: int, luck: int, talent_mult: float = 1.0) -> int:
    raw = 15 + root * 0.25 + insight * 0.15 + luck * 0.1
    return max(1, int(raw * talent_mult))
