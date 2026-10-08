from __future__ import annotations

EXPLORATION_EVENTS = [
    {"key": "linh_thach_nho", "weight": 30, "stones": (50, 150), "text": "Nhặt được vài viên linh thạch."},
    {"key": "tu_vi_nho", "weight": 25, "cultivation": (30, 80), "text": "Ngộ ra một tia đạo lý."},
    {"key": "yeu_thu", "weight": 20, "combat": True, "text": "Gặp yêu thú!"},
    {"key": "co_duyen", "weight": 10, "stones": (200, 500), "item": "tu_khi_dan", "text": "Cơ duyên nhỏ xuất hiện."},
    {"key": "thuong_the", "weight": 8, "injury": (5, 15), "text": "Vấp phải trận pháp cũ, bị thương nhẹ."},
    {"key": "truyen_thua", "weight": 5, "cultivation": (100, 300), "insight": 1, "text": "Linh cảm truyền thừa thoáng qua."},
    {"key": "khong", "weight": 12, "text": "Lặng lẽ đi một vòng, không có gì đặc biệt."},
]

INHERITANCE_EVENTS = [
    {"key": "kiem_y", "dao": "kiem", "insight": 15, "text": "Kiếm ý cổ xưa thấm vào tâm can."},
    {"key": "dao_y", "dao": "dao", "insight": 15, "text": "Đao hồn trấn áp hư không."},
    {"key": "phap_y", "dao": "phap", "insight": 15, "text": "Pháp tắc vận hành trong đan điền."},
    {"key": "the_y", "dao": "the", "insight": 15, "text": "Thể xác như được tôi luyện."},
]
