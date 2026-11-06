"""Đan dược — mỗi viên một vai trò rõ.

Nhánh:
  • cultivation  — lấp tu vi trước đột phá (3 bậc)
  • heal         — hồi HP
  • stat_*       — +1 chỉ số gốc vĩnh viễn (mỗi chỉ số 1 đan)
  • breakthrough — chỉ dùng trong UI đột phá
  • thunder_guard — hộ Cửu Lôi Kiếp
"""
from __future__ import annotations

from game.content.items._schema import item

PILLS: dict[str, dict] = {
    # ----- Tu vi (lấp tầng) -----
    "tu_khi_dan": item({
        "category": "Đan dược", "name": "Tụ Khí Đan", "rarity": "Phàm",
        "type": "consumable", "role": "cultivation", "price": 1000,
        "cultivation": 180,
        "description": "Đan nhập môn. Dùng để lấp tu vi tầng hiện tại trước khi đột phá.",
    }),
    "hoi_khi_dan": item({
        "category": "Đan dược", "name": "Hồi Khí Đan", "rarity": "Hoàng",
        "type": "consumable", "role": "cultivation", "price": 2500,
        "cultivation": 400,
        "description": "Đan bậc trung. Bổ sung tu vi nhanh hơn Tụ Khí Đan.",
    }),
    "linh_tuy_dan": item({
        "category": "Đan dược", "name": "Linh Tủy Đan", "rarity": "Huyền",
        "type": "consumable", "role": "cultivation", "price": 8000,
        "cultivation": 900,
        "description": "Đan bậc cao. Dùng khi tầng tu vi cần lượng lớn để đầy.",
    }),
    # ----- Hồi phục -----
    "hoi_huyet_dan": item({
        "category": "Đan dược", "name": "Hồi Huyết Đan", "rarity": "Hoàng",
        "type": "consumable", "role": "heal", "price": 3500,
        "heal": 80,
        "description": "Hồi khí huyết. Dùng ngoài trận hoặc trong chiến đấu.",
    }),
    "duong_huyet_dan": item({
        "category": "Đan dược", "name": "Dưỡng Huyết Đan", "rarity": "Huyền",
        "type": "consumable", "role": "heal", "price": 7000,
        "heal": 160,
        "description": "Hồi HP mạnh. Phù hợp sau thất bại hoặc lôi kiếp.",
    }),
    # ----- 5 chỉ số gốc (mỗi loại đúng 1 chỉ số, +1 vĩnh viễn, chịu soft-cap) -----
    "can_co_dan": item({
        "category": "Đan dược", "name": "Căn Cơ Đan", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_root", "price": 6000,
        "root": 1,
        "description": "Củng cố Căn cơ (+1). Ảnh hưởng tỉ lệ đột phá và thể chất.",
    }),
    "minh_tam_dan": item({
        "category": "Đan dược", "name": "Minh Tâm Đan", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_insight", "price": 6000,
        "insight": 1,
        "description": "Khai sáng Ngộ tính (+1). Giúp cảm đạo và đột phá.",
    }),
    "van_khi_dan": item({
        "category": "Đan dược", "name": "Vận Khí Đan", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_luck", "price": 6000,
        "luck": 1,
        "description": "Tăng Vận khí (+1). May mắn khi vượt cảnh và khám phá.",
    }),
    "menh_so_dan": item({
        "category": "Đan dược", "name": "Mệnh Số Đan", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_fate", "price": 6000,
        "fate": 1,
        "description": "Bổ sung Mệnh số (+1). Thiên mệnh hỗ trợ đột phá nhẹ.",
    }),
    "dao_tam_dan": item({
        "category": "Đan dược", "name": "Đạo Tâm Đan", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_mind", "price": 6000,
        "mind": 1,
        "description": "Rèn Đạo tâm (+1). Giữ tâm không loạn khi đột phá.",
    }),
    # ----- Đột phá / Lôi kiếp (chỉ có ý nghĩa trong flow đột phá) -----
    "tru_co_dan": item({
        "category": "Đan dược", "name": "Trúc Cơ Đan", "rarity": "Huyền",
        "type": "consumable", "role": "breakthrough", "price": 15000,
        "breakthrough_bonus": 0.05,
        "description": "Dùng trong .dotpha. +5% tỉ lệ đột phá cho đúng một lần thử.",
    }),
    "kim_dan_dai_duoc": item({
        "category": "Đan dược", "name": "Kim Đan Đại Dược", "rarity": "Địa",
        "type": "consumable", "role": "breakthrough", "price": 50000,
        "breakthrough_bonus": 0.10,
        "description": "Dùng trong .dotpha. +10% tỉ lệ đột phá cho đúng một lần thử.",
    }),
    "loi_kiep_dan": item({
        "category": "Đan dược", "name": "Lôi Kiếp Đan", "rarity": "Địa",
        "type": "consumable", "role": "thunder_guard", "price": 42000,
        "thunder_resistance": 0.12,
        "description": "Hộ Cửu Lôi Kiếp: giảm 12% sát thương lôi trong lần đột phá đại cảnh.",
    }),
}
