"""Công pháp — học một lần: mở skill chiến đấu + chỉ số vĩnh viễn.

Mỗi công pháp gắn đúng một trong 5 chỉ số gốc (technique_stat).
"""
from __future__ import annotations

from game.content.items._schema import item

TECHNIQUES: dict[str, dict] = {
    "hon_don_dao_kinh": item({
        "category": "Công pháp", "name": "Hỗn Độn Đạo Kinh", "rarity": "Huyền",
        "type": "technique", "role": "technique", "price": 20000,
        "technique_stat": "root", "technique_bonus": 2, "skill_power": 1.20,
        "description": "Đạo kinh hỗn độn. Căn cơ +2 khi học; kỹ năng sát thương ×1.20.",
    }),
    "kiem_tam_quyet": item({
        "category": "Công pháp", "name": "Kiếm Tâm Quyết", "rarity": "Hoàng",
        "type": "technique", "role": "technique", "price": 14000,
        "technique_stat": "mind", "technique_bonus": 1, "skill_power": 1.15,
        "description": "Luyện kiếm tâm. Đạo tâm +1; skill ×1.15.",
    }),
    "ngu_hanh_quyet": item({
        "category": "Công pháp", "name": "Ngũ Hành Quyết", "rarity": "Hoàng",
        "type": "technique", "role": "technique", "price": 14000,
        "technique_stat": "insight", "technique_bonus": 1, "skill_power": 1.15,
        "description": "Ngũ hành tương sinh. Ngộ tính +1; skill ×1.15.",
    }),
    "linh_xa_bo": item({
        "category": "Công pháp", "name": "Linh Xà Bộ", "rarity": "Hoàng",
        "type": "technique", "role": "technique", "price": 14000,
        "technique_stat": "luck", "technique_bonus": 1, "skill_power": 1.12,
        "description": "Thân pháp linh xà. Vận khí +1; skill ×1.12.",
    }),
    "van_moc_tam_kinh": item({
        "category": "Công pháp", "name": "Vạn Mộc Tâm Kinh", "rarity": "Huyền",
        "type": "technique", "role": "technique", "price": 22000,
        "technique_stat": "fate", "technique_bonus": 2, "skill_power": 1.18,
        "description": "Tâm kinh vạn mộc. Mệnh số +2; skill ×1.18.",
    }),
    "phi_tinh_kiem_phap": item({
        "category": "Công pháp", "name": "Phi Tinh Kiếm Pháp", "rarity": "Huyền",
        "type": "technique", "role": "technique", "price": 24000,
        "technique_stat": "insight", "technique_bonus": 2, "skill_power": 1.25,
        "description": "Kiếm pháp phi tinh. Ngộ tính +2; skill mạnh ×1.25.",
    }),
    "kim_chung_quyet": item({
        "category": "Công pháp", "name": "Kim Chung Quyết", "rarity": "Huyền",
        "type": "technique", "role": "technique", "price": 22000,
        "technique_stat": "root", "technique_bonus": 2, "skill_power": 1.10,
        "description": "Hộ thể kim chung. Căn cơ +2; skill thiên phòng ×1.10.",
    }),
    "huyen_thuy_kinh": item({
        "category": "Công pháp", "name": "Huyền Thủy Kinh", "rarity": "Địa",
        "type": "technique", "role": "technique", "price": 40000,
        "technique_stat": "mind", "technique_bonus": 3, "skill_power": 1.22,
        "description": "Kinh huyền thủy. Đạo tâm +3; skill ×1.22.",
    }),
    "cuong_dao_quyet": item({
        "category": "Công pháp", "name": "Cương Đao Quyết", "rarity": "Hoàng",
        "type": "technique", "role": "technique", "price": 15000,
        "technique_stat": "luck", "technique_bonus": 1, "skill_power": 1.18,
        "description": "Đao quyết cương mãnh. Vận khí +1; skill ×1.18.",
    }),
    "thien_kiem": item({  # legacy id kept — was weapon name collision avoided as technique? keep as technique book
        "category": "Công pháp", "name": "Thiên Kiếm Tâm Pháp", "rarity": "Địa",
        "type": "technique", "role": "technique", "price": 45000,
        "technique_stat": "insight", "technique_bonus": 3, "skill_power": 1.30,
        "description": "Tâm pháp thiên kiếm. Ngộ tính +3; skill đỉnh ×1.30.",
    }),
}
