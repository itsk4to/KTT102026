from __future__ import annotations

DESTINIES = ["Bình Thường", "Thiên Kiêu", "Vạn Trung Nhất", "Tuyệt Thế", "Nghịch Thiên"]
DESTINY_DESCRIPTIONS = {
    "Bình Thường": "Số phận ổn định, không có thiên lệch đặc biệt.",
    "Thiên Kiêu": "Tu luyện và đột phá thuận lợi hơn.",
    "Vạn Trung Nhất": "Cân bằng giữa chiến đấu và cơ duyên.",
    "Tuyệt Thế": "Thiên phú chiến đấu nổi bật, nhưng thử thách cũng khắc nghiệt hơn.",
    "Nghịch Thiên": "Cơ duyên cực mạnh, đổi lại dễ gặp biến cố hơn.",
}
DESTINY_MODS = {
    "Bình Thường": {"cultivation": 1.00, "breakthrough": 0.00, "luck": 0.00},
    "Thiên Kiêu": {"cultivation": 1.10, "breakthrough": 0.05, "luck": 0.02},
    "Vạn Trung Nhất": {"cultivation": 1.05, "breakthrough": 0.02, "luck": 0.05},
    "Tuyệt Thế": {"cultivation": 1.12, "breakthrough": 0.03, "luck": 0.03},
    "Nghịch Thiên": {"cultivation": 1.15, "breakthrough": 0.07, "luck": 0.08},
}
PATH_TALENTS = {
    "tien": ["Thanh Tâm", "Linh Căn", "Tiên Duyên", "Đạo Tâm"],
    "ma": ["Ma Tâm", "Huyết Mạch", "Sát Phạt", "Nuôi Ma"],
}
TALENT_DESCRIPTIONS = {
    "Thanh Tâm": "Tu luyện ổn định, giảm nhẹ ảnh hưởng thương thế khi đột phá.",
    "Linh Căn": "Thu hoạch tu vi từ tu luyện cao hơn.",
    "Tiên Duyên": "Tăng tỷ lệ cơ duyên hiếm.",
    "Đạo Tâm": "Tăng tỷ lệ đột phá.",
    "Ma Tâm": "Tăng tấn công chiến đấu.",
    "Huyết Mạch": "Tăng HP tối đa.",
    "Sát Phạt": "Tăng tỷ lệ chí mạng.",
    "Nuôi Ma": "Tăng sức mạnh kỹ năng và tu vi nhận từ chiến thắng.",
}
TALENT_MODS = {
    "Thanh Tâm": {"cultivation": 1.04, "breakthrough": 0.03, "injury_mult": 0.90},
    "Linh Căn": {"cultivation": 1.12},
    "Tiên Duyên": {"rare_event": 0.08, "breakthrough": 0.02},
    "Đạo Tâm": {"cultivation": 1.02, "breakthrough": 0.06},
    "Ma Tâm": {"combat_atk": 1.06},
    "Huyết Mạch": {"combat_hp": 1.10},
    "Sát Phạt": {"combat_crit": 0.08},
    "Nuôi Ma": {"skill_power": 1.06, "cultivation_on_victory": 1.08},
}
REDEEM_CODES = {
    "KATO2026": {"stones": 5000, "item": "tu_khi_dan", "qty": 5, "max_uses": 1000},
    "TUTIEN": {"stones": 2000, "max_uses": 500},
}
def talent_mod(talent: str, key: str, default=0): return TALENT_MODS.get(talent, {}).get(key, default)
def destiny_mod(destiny: str, key: str, default=0): return DESTINY_MODS.get(destiny, {}).get(key, default)
