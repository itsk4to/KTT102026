"""Trang bị — 4 ô, mỗi ô một nhiệm vụ rõ.

  weapon    → công
  armor     → thủ + HP
  artifact  → cân bằng, một số kháng lôi
  accessory → chỉ số phụ nhẹ
"""
from __future__ import annotations

from game.content.items._schema import item

EQUIPMENT: dict[str, dict] = {
    # ----- Weapons (công) -----
    "qing_feng_kiem": item({
        "category": "Binh khí", "name": "Thanh Phong Kiếm", "rarity": "Phàm",
        "type": "equipment", "slot": "weapon", "role": "combat_weapon",
        "attack": 12, "defense": 0, "price": 5000,
        "description": "Kiếm nhập môn. Tăng công thuần.",
    }),
    "huyen_thiet_dao": item({
        "category": "Binh khí", "name": "Huyền Thiết Đao", "rarity": "Hoàng",
        "type": "equipment", "slot": "weapon", "role": "combat_weapon",
        "attack": 20, "defense": 1, "price": 12000,
        "description": "Đao nặng. Công cao hơn kiếm nhập môn.",
    }),
    "bach_van_kiem": item({
        "category": "Binh khí", "name": "Bạch Vân Kiếm", "rarity": "Huyền",
        "type": "equipment", "slot": "weapon", "role": "combat_weapon",
        "attack": 28, "defense": 2, "price": 28000,
        "description": "Kiếm bạch vân. Công ổn định bậc Huyền.",
    }),
    "long_van_kiem": item({
        "category": "Binh khí", "name": "Long Vân Kiếm", "rarity": "Địa",
        "type": "equipment", "slot": "weapon", "role": "combat_weapon",
        "attack": 36, "defense": 3, "price": 52000,
        "description": "Danh kiếm. Công mạnh cho trung–cao cảnh.",
    }),
    "thien_thanh_kiem": item({
        "category": "Binh khí", "name": "Thiên Thanh Kiếm", "rarity": "Thiên",
        "type": "equipment", "slot": "weapon", "role": "combat_weapon",
        "attack": 45, "defense": 4, "price": 90000,
        "description": "Bảo kiếm hiếm. Đỉnh công trong shop.",
    }),
    # ----- Armor (thủ + HP) -----
    "thanh_linh_y": item({
        "category": "Pháp bảo", "name": "Thanh Linh Y", "rarity": "Phàm",
        "type": "equipment", "slot": "armor", "role": "combat_armor",
        "attack": 0, "defense": 10, "max_hp": 15, "price": 5000,
        "description": "Áo giáp mỏng. Thủ và HP cơ bản.",
    }),
    "kim_cang_giap": item({
        "category": "Pháp bảo", "name": "Kim Cang Giáp", "rarity": "Hoàng",
        "type": "equipment", "slot": "armor", "role": "combat_armor",
        "attack": 0, "defense": 18, "max_hp": 25, "price": 14000,
        "description": "Giáp kim cang. Thủ rõ, tăng HP.",
    }),
    "huyen_vu_giap": item({
        "category": "Pháp bảo", "name": "Huyền Vũ Giáp", "rarity": "Huyền",
        "type": "equipment", "slot": "armor", "role": "combat_armor",
        "attack": 1, "defense": 26, "max_hp": 35, "price": 30000,
        "description": "Giáp huyền vũ. Phòng ngự bậc cao.",
    }),
    # ----- Artifacts (cân bằng / kháng lôi) -----
    "thanh_tam_ngoc_boi": item({
        "category": "Pháp bảo", "name": "Thanh Tâm Ngọc Bội", "rarity": "Hoàng",
        "type": "equipment", "slot": "artifact", "role": "combat_artifact",
        "attack": 4, "defense": 10, "max_hp": 8, "price": 10000,
        "description": "Ngọc bội hộ tâm. Cân bằng công–thủ nhẹ.",
    }),
    "huyen_thiet_linh_kinh": item({
        "category": "Pháp bảo", "name": "Huyền Thiết Linh Kính", "rarity": "Huyền",
        "type": "equipment", "slot": "artifact", "role": "combat_artifact",
        "attack": 6, "defense": 14, "thunder_resistance": 0.05, "price": 22000,
        "description": "Linh kính phản lôi. Kháng Cửu Lôi +5% khi trang bị.",
    }),
    "thien_loi_chau": item({
        "category": "Pháp bảo", "name": "Thiên Lôi Châu", "rarity": "Địa",
        "type": "equipment", "slot": "artifact", "role": "combat_artifact",
        "attack": 8, "defense": 12, "thunder_resistance": 0.10, "price": 45000,
        "description": "Châu hấp lôi. Kháng Cửu Lôi +10% — trang bị trước đột phá đại cảnh.",
    }),
    "tinh_van_bao_kien": item({
        "category": "Pháp bảo", "name": "Tinh Vân Bảo Kiện", "rarity": "Huyền",
        "type": "equipment", "slot": "artifact", "role": "combat_artifact",
        "attack": 7, "defense": 12, "max_hp": 12, "price": 26000,
        "description": "Bảo kiện cân bằng, không thiên lệch một chỉ số.",
    }),
    # ----- Accessories -----
    "linh_ngoc_gioi": item({
        "category": "Pháp bảo", "name": "Linh Ngọc Giới", "rarity": "Hoàng",
        "type": "equipment", "slot": "accessory", "role": "combat_accessory",
        "attack": 3, "defense": 3, "max_hp": 10, "price": 9000,
        "description": "Nhẫn linh ngọc. Chỉ số phụ nhẹ.",
    }),
    "tu_kim_gioi": item({
        "category": "Pháp bảo", "name": "Tử Kim Giới", "rarity": "Huyền",
        "type": "equipment", "slot": "accessory", "role": "combat_accessory",
        "attack": 5, "defense": 5, "max_hp": 15, "price": 20000,
        "description": "Nhẫn tử kim. Phụ kiện bậc Huyền.",
    }),
    "bich_ngoc_ho_tam": item({
        "category": "Pháp bảo", "name": "Bích Ngọc Hộ Tâm", "rarity": "Hoàng",
        "type": "equipment", "slot": "artifact", "role": "combat_artifact",
        "attack": 2, "defense": 12, "max_hp": 12, "price": 11000,
        "description": "Hộ tâm bích ngọc. Thiên về phòng thủ.",
    }),
}
