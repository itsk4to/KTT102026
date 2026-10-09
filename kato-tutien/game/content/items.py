from __future__ import annotations

EQUIP_SLOTS = ("weapon", "artifact", "armor", "accessory")

ITEMS: dict[str, dict] = {
    # --- Đan dược ---
    "tu_khi_dan": {
        "category": "Đan dược", "name": "Tụ Khí Đan", "rarity": "Phàm", "type": "consumable",
        "price": 1_000, "marketable": True, "cultivation": 250,
        "description": "Đan dược nhập môn, bổ sung linh khí.",
    },
    "hoi_khi_dan": {
        "category": "Đan dược", "name": "Hồi Khí Đan", "rarity": "Phàm", "type": "consumable",
        "price": 2_000, "marketable": True, "cultivation": 500,
        "description": "Hồi phục linh khí, tăng tu vi.",
    },
    "hoi_huyet_dan": {
        "category": "Đan dược", "name": "Hồi Huyết Đan", "rarity": "Hoàng", "type": "consumable",
        "price": 3_500, "marketable": True, "heal": 80,
        "description": "Hồi phục khí huyết trong và ngoài chiến đấu.",
    },
    "tru_co_dan": {
        "category": "Đan dược", "name": "Trúc Cơ Đan", "rarity": "Huyền", "type": "consumable",
        "price": 15_000, "marketable": True, "cultivation": 2_000, "root": 1, "breakthrough_bonus": 0.08,
        "description": "Hỗ trợ trúc cơ, tăng nhẹ căn cơ và giúp đột phá.",
    },
    "kim_dan_dai_duoc": {
        "category": "Đan dược", "name": "Kim Đan Đại Dược", "rarity": "Địa", "type": "consumable",
        "price": 50_000, "marketable": True, "cultivation": 5_000, "insight": 2, "breakthrough_bonus": 0.12,
        "description": "Đại dược hỗ trợ kết đan và tăng tỷ lệ đột phá.",
    },
    "loi_kiep_dan": {
        "category": "Đan dược", "name": "Lôi Kiếp Đan", "rarity": "Địa", "type": "consumable",
        "price": 42_000, "marketable": True, "thunder_resistance": 0.18,
        "description": "Uống trước khi đột phá, giảm 18% sát thương Cửu Lôi Kiếp trong lần hộ kiếp kế tiếp.",
    },
    # --- Bùa chú ---
    "liet_hoa_phu": {
        "category": "Bùa chú", "name": "Liệt Hỏa Phù", "rarity": "Huyền", "type": "consumable",
        "price": 12_000, "marketable": True, "cultivation": 1_300, "insight": 1,
        "description": "Hỏa lực tôi luyện ngộ tính.",
    },
    "bang_tam_phu": {
        "category": "Bùa chú", "name": "Băng Tâm Phù", "rarity": "Huyền", "type": "consumable",
        "price": 18_000, "marketable": True, "cultivation": 1_600, "mind": 2,
        "description": "Giữ tâm tĩnh, tăng đạo tâm.",
    },
    "cuu_loi_ho_than_phu": {
        "category": "Bùa chú", "name": "Cửu Lôi Hộ Thân Phù", "rarity": "Địa", "type": "consumable",
        "price": 32_000, "marketable": True, "thunder_resistance": 0.15,
        "description": "Linh phù che chở thân thể, giảm 15% sát thương Cửu Lôi Kiếp trong lần hộ kiếp kế tiếp.",
    },
    # --- Pháp bảo / trang bị ---
    "thanh_tam_ngoc_boi": {
        "category": "Pháp bảo", "name": "Thanh Tâm Ngọc Bội", "rarity": "Hoàng", "type": "equipment",
        "slot": "artifact", "attack": 20, "defense": 70, "price": 8_000, "marketable": True,
        "description": "Ngọc bội hộ tâm.",
    },
    "huyen_thiet_linh_kinh": {
        "category": "Pháp bảo", "name": "Huyền Thiết Linh Kính", "rarity": "Huyền", "type": "equipment",
        "slot": "artifact", "attack": 55, "defense": 120, "thunder_resistance": 0.08, "price": 25_000, "marketable": True,
        "description": "Linh kính phản chiếu linh lực, giảm 8% sát thương Cửu Lôi Kiếp khi trang bị.",
    },
    "thien_loi_chau": {
        "category": "Pháp bảo", "name": "Thiên Lôi Châu", "rarity": "Địa", "type": "equipment",
        "slot": "artifact", "attack": 20, "defense": 85, "thunder_resistance": 0.14, "price": 88_000, "marketable": True,
        "description": "Pháp bảo dẫn lôi nhập châu, giảm 14% sát thương Cửu Lôi Kiếp khi trang bị.",
    },
    "thien_kiem": {
        "category": "Binh khí", "name": "Thiên Kiếm", "rarity": "Huyền", "type": "equipment",
        "slot": "weapon", "attack": 90, "defense": 10, "price": 30_000, "marketable": True,
        "description": "Kiếm sắc, hợp Kiếm Đạo.",
    },
    "huyen_thiet_dao": {
        "category": "Binh khí", "name": "Huyền Thiết Đao", "rarity": "Huyền", "type": "equipment",
        "slot": "weapon", "attack": 95, "defense": 8, "price": 30_000, "marketable": True,
        "description": "Đao nặng, hợp Đao Đạo.",
    },
    "kim_cang_giap": {
        "category": "Pháp bảo", "name": "Kim Cang Giáp", "rarity": "Địa", "type": "equipment",
        "slot": "armor", "attack": 10, "defense": 200, "price": 60_000, "marketable": True,
        "description": "Giáp cứng như kim cang.",
    },
    "linh_ngoc_gioi": {
        "category": "Pháp bảo", "name": "Linh Ngọc Giới", "rarity": "Hoàng", "type": "equipment",
        "slot": "accessory", "attack": 15, "defense": 25, "price": 12_000, "marketable": True,
        "description": "Nhẫn ngọc tăng linh lực nhẹ.",
    },
    # --- Công pháp ---
    "hon_don_dao_kinh": {
        "category": "Công pháp", "name": "Hỗn Độn Đạo Kinh", "rarity": "Địa", "type": "technique",
        "price": 100_000, "marketable": True, "technique_stat": "insight", "technique_bonus": 3,
        "skill_power": 1.35, "description": "Công pháp thượng thừa, tăng ngộ tính.",
    },
    "kiem_tam_quyet": {
        "category": "Công pháp", "name": "Kiếm Tâm Quyết", "rarity": "Huyền", "type": "technique",
        "price": 40_000, "marketable": True, "technique_stat": "root", "technique_bonus": 2,
        "skill_power": 1.25, "description": "Kiếm tâm vững, tăng căn cơ.",
    },
    "cuong_dao_quyet": {
        "category": "Công pháp", "name": "Cuồng Đao Quyết", "rarity": "Huyền", "type": "technique",
        "price": 40_000, "marketable": True, "technique_stat": "root", "technique_bonus": 2,
        "skill_power": 1.28, "description": "Đao ý cuồng bạo.",
    },
    # --- Combat consumable ---
    "boom_heal_small": {
        "category": "Đan dược", "name": "Tiểu Hồi Huyết Đan", "rarity": "Phàm", "type": "combat_item",
        "price": 1_500, "marketable": True, "heal": 40,
        "description": "Hồi 40 HP trong chiến đấu.",
    },
}

SHOP_ORDER = ["Đan dược", "Bùa chú", "Pháp bảo", "Binh khí", "Công pháp"]
SHOP_CATEGORIES = {
    cat: [iid for iid, it in ITEMS.items() if it.get("category") == cat and it.get("price")]
    for cat in SHOP_ORDER
}


def item_slot(item_id: str) -> str | None:
    item = ITEMS.get(item_id) or {}
    return item.get("slot")
