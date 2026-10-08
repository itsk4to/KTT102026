from __future__ import annotations

STATUS_EFFECTS = {
    "burn": {"name": "Thiêu Đốt", "kind": "dot", "potency": 0.06, "duration": 3},
    "poison": {"name": "Trúng Độc", "kind": "dot", "potency": 0.05, "duration": 4},
    "bleed": {"name": "Xuất Huyết", "kind": "dot", "potency": 0.04, "duration": 3},
    "stun": {"name": "Choáng", "kind": "control", "potency": 1.0, "duration": 1},
    "slow": {"name": "Làm Chậm", "kind": "slow", "potency": 0.7, "duration": 2},
    "shield": {"name": "Hộ Thuẫn", "kind": "shield", "potency": 0.35, "duration": 2},
}

GACHA_TABLE = [
    ("tu_khi_dan", 40),
    ("hoi_khi_dan", 25),
    ("hoi_huyet_dan", 15),
    ("liet_hoa_phu", 8),
    ("thanh_tam_ngoc_boi", 5),
    ("kiem_tam_quyet", 4),
    ("hon_don_dao_kinh", 2),
    ("thien_kiem", 1),
]
