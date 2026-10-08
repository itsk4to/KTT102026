from __future__ import annotations

# (name, layer_count)
REALMS: list[tuple[str, int]] = [
    ("Phàm Nhân", 1),
    ("Luyện Khí", 9),
    ("Trúc Cơ", 9),
    ("Kim Đan", 9),
    ("Nguyên Anh", 9),
    ("Hóa Thần", 9),
    ("Luyện Hư", 9),
    ("Hợp Thể", 9),
    ("Đại Thừa", 9),
    ("Độ Kiếp", 3),
    ("Chân Tiên", 9),
    ("Thiên Tiên", 9),
    ("Tiên Vương", 9),
    ("Tiên Đế", 9),
]

TRIBULATION_REALM_INDEX = 9  # Độ Kiếp

MINOR_REALM_NAMES = ("Sơ kỳ", "Trung kỳ", "Hậu kỳ", "Viên mãn")


def minor_realm_name(layer: int, layer_count: int) -> str:
    if layer_count <= 1 or layer <= 0:
        return MINOR_REALM_NAMES[0]
    span = max(1, layer_count)
    idx = min(3, int((max(0, layer) * 4) / span))
    return MINOR_REALM_NAMES[idx]


def cultivation_requirement(realm_index: int, layer: int) -> int:
    """Progressive threshold — grows with realm and layer."""
    base = 100 + realm_index * 180
    return int(base * (1 + 0.35 * max(0, layer - 1)) * (1 + realm_index * 0.12))
