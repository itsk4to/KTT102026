from __future__ import annotations

from game.content.realms import REALMS, cultivation_requirement, minor_realm_name


# Hai phe dùng hệ thống bậc/lớp giống nhau để cân bằng, nhưng tên cảnh giới riêng.
MA_REALM_NAMES = (
    "Phàm Nhân", "Ma Khí", "Ma Cơ", "Ma Đan", "Ma Anh", "Hóa Ma",
    "Ma Hư", "Ma Hợp", "Ma Thừa", "Ma Kiếp", "Chân Ma", "Thiên Ma",
    "Ma Tôn", "Ma Đế",
)


def realm_text(realm_index: int, layer: int, path: str = "tien") -> str:
    if realm_index < 0 or realm_index >= len(REALMS):
        return "Không rõ"
    default_name, layers = REALMS[realm_index]
    name = MA_REALM_NAMES[realm_index] if path == "ma" else default_name
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


def bounded_cultivation_delta(current: int, requested: int, realm_index: int, layer: int) -> int:
    """Clamp a cultivation reward/loss to valid progress for the current stage.

    Positive rewards stop at the current breakthrough threshold. Negative deltas
    can reduce current cultivation but never below zero. Returns the actual delta.
    """
    current = max(0, int(current))
    requested = int(requested)
    if requested > 0:
        return min(requested, headroom(current, realm_index, layer))
    if requested < 0:
        return -min(current, abs(requested))
    return 0


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
    insight: int,
    luck: int,
    fate: int,
    mind: int,
    injury: int = 0,
    dao_stage: int = 0,
    foundation_bonus: float = 0.0,
) -> float:
    """Tỉ lệ đột phá từ đủ 5 chỉ số gốc của nhân vật.

    1. root    — Căn cơ
    2. insight — Ngộ tính
    3. luck    — Vận khí
    4. fate    — Mệnh số
    5. mind    — Đạo tâm

    dao_stage / foundation_bonus / injury vẫn điều chỉnh thêm.
    """
    # Nhân vật mới (5 chỉ số ~55) khoảng 60%. Mỗi chỉ số đều kéo tỉ lệ.
    base = (
        0.18
        + max(0, int(root)) * 0.0020      # Căn cơ
        + max(0, int(luck)) * 0.0018      # Vận khí
        + max(0, int(mind)) * 0.0016      # Đạo tâm
        + max(0, int(insight)) * 0.0014   # Ngộ tính
        + max(0, int(fate)) * 0.0012      # Mệnh số
        + max(0, int(dao_stage)) * 0.018
    )
    base += float(foundation_bonus)
    # Injury matters, but must not cancel pity one-for-one after every failure.
    # At 0.003 per injury point, +5 pity offsets the +5 injury from a normal
    # failure and still yields a net gain toward recovery.
    base -= max(0, min(100, int(injury))) * 0.003
    return max(0.10, min(0.92, base))


def cultivate_gain(root: int, insight: int, luck: int, talent_mult: float = 1.0) -> int:
    raw = 15 + root * 0.25 + insight * 0.15 + luck * 0.1
    return max(1, int(raw * talent_mult))
