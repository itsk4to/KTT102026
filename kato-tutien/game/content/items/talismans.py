"""Bùa chú — hỗ trợ dài hạn hoặc hộ kiếp, không trộn tu vi lung tung.

Nhánh:
  • stat_*         — phù vĩnh viễn (+1/+2 một chỉ số)
  • breakthrough   — tăng tỉ lệ đột phá
  • thunder_guard  — kháng lôi
"""
from __future__ import annotations

from game.content.items._schema import item

TALISMANS: dict[str, dict] = {
    # Stat seals — one clear target each
    "qing_moc_phu": item({
        "category": "Bùa chú", "name": "Thanh Mộc Phù", "rarity": "Phàm",
        "type": "consumable", "role": "stat_root", "price": 3500,
        "root": 1,
        "description": "Linh phù củng cố Căn cơ (+1).",
    }),
    "ngung_than_phu": item({
        "category": "Bùa chú", "name": "Ngưng Thần Phù", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_insight", "price": 7000,
        "insight": 2,
        "description": "Ngưng thần tĩnh trí. Ngộ tính +2.",
    }),
    "liet_hoa_phu": item({
        "category": "Bùa chú", "name": "Liệt Hỏa Phù", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_luck", "price": 7000,
        "luck": 2,
        "description": "Lửa tôi luyện khí vận. Vận khí +2.",
    }),
    "tran_tam_phu": item({
        "category": "Bùa chú", "name": "Trấn Tâm Phù", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_fate", "price": 7000,
        "fate": 2,
        "description": "Trấn giữ thiên mệnh. Mệnh số +2.",
    }),
    "kien_tam_phu": item({
        "category": "Bùa chú", "name": "Kiên Tâm Phù", "rarity": "Hoàng",
        "type": "consumable", "role": "stat_mind", "price": 7000,
        "mind": 2,
        "description": "Kiên định đạo tâm. Đạo tâm +2.",
    }),
    "bang_tam_phu": item({
        "category": "Bùa chú", "name": "Băng Tâm Phù", "rarity": "Huyền",
        "type": "consumable", "role": "stat_mind", "price": 12000,
        "mind": 3,
        "description": "Băng tẩy tạp niệm. Đạo tâm +3 — hữu ích trước đột phá lớn.",
    }),
    # Breakthrough / thunder only
    "ho_mach_phu": item({
        "category": "Bùa chú", "name": "Hộ Mạch Phù", "rarity": "Huyền",
        "type": "consumable", "role": "breakthrough", "price": 14000,
        "breakthrough_bonus": 0.05,
        "description": "Dùng trong .dotpha. +5% tỉ lệ đột phá một lần.",
    }),
    "tinh_loi_phu": item({
        "category": "Bùa chú", "name": "Tĩnh Lôi Phù", "rarity": "Huyền",
        "type": "consumable", "role": "thunder_guard", "price": 18000,
        "thunder_resistance": 0.08,
        "description": "Giảm 8% sát thương Cửu Lôi Kiếp trong lần hộ kiếp.",
    }),
    "cuu_loi_ho_than_phu": item({
        "category": "Bùa chú", "name": "Cửu Lôi Hộ Thân Phù", "rarity": "Địa",
        "type": "consumable", "role": "thunder_guard", "price": 32000,
        "thunder_resistance": 0.12,
        "description": "Hộ thân trước chín đạo thiên lôi. Kháng lôi +12%.",
    }),
}
