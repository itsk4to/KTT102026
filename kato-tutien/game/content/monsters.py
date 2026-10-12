from __future__ import annotations

"""Exploration bestiary. Zone-specific entries are preferred in their home region."""

MONSTERS = [
    # Common creatures found throughout the mortal realm.
    {"name": "Yêu Thỏ", "hp": 40, "attack": 8, "defense": 3, "min_realm": 0},
    {"name": "Linh Xà", "hp": 55, "attack": 12, "defense": 5, "min_realm": 0},
    {"name": "Hắc Lang", "hp": 80, "attack": 18, "defense": 8, "min_realm": 1},
    {"name": "Thạch Hổ", "hp": 120, "attack": 25, "defense": 15, "min_realm": 2},
    {"name": "Huyết Ưng", "hp": 150, "attack": 32, "defense": 12, "min_realm": 3},
    {"name": "Ma Hầu", "hp": 200, "attack": 40, "defense": 20, "min_realm": 4},
    {"name": "Huyền Giáp Thú", "hp": 280, "attack": 48, "defense": 35, "min_realm": 5},
    {"name": "Lôi Giao", "hp": 360, "attack": 60, "defense": 28, "min_realm": 6},

    # Hoang Nguyên.
    {"name": "Linh Thạch Khuyển", "hp": 62, "attack": 13, "defense": 6, "min_realm": 0, "zones": ["hoangnguyen"]},
    {"name": "Bụi Linh Thể", "hp": 48, "attack": 15, "defense": 3, "min_realm": 0, "zones": ["hoangnguyen"]},
    {"name": "Hắc Nha Cự Thử", "hp": 108, "attack": 23, "defense": 9, "min_realm": 1, "zones": ["hoangnguyen"]},

    # Yêu Thú Sơn Mạch.
    {"name": "Thanh Mộc Lang", "hp": 118, "attack": 25, "defense": 11, "min_realm": 1, "zones": ["yeuthusonmach"]},
    {"name": "Hỏa Văn Hổ", "hp": 188, "attack": 37, "defense": 18, "min_realm": 2, "zones": ["yeuthusonmach"]},
    {"name": "Độc Giác Man Ngưu", "hp": 265, "attack": 48, "defense": 25, "min_realm": 3, "zones": ["yeuthusonmach"]},
    {"name": "Bách Trùng Mẫu", "hp": 350, "attack": 54, "defense": 28, "min_realm": 4, "zones": ["yeuthusonmach"]},

    # Ancient cave estate.
    {"name": "Khôi Lỗi Hộ Phủ", "hp": 305, "attack": 46, "defense": 36, "min_realm": 3, "zones": ["dongphu"]},
    {"name": "Cổ Mộ Kiếm Vệ", "hp": 395, "attack": 59, "defense": 34, "min_realm": 4, "zones": ["dongphu"]},
    {"name": "Tàn Hồn Đạo Nhân", "hp": 370, "attack": 63, "defense": 25, "min_realm": 4, "zones": ["dongphu"]},

    # Sea realm.
    {"name": "Lam Lân Thủy Yêu", "hp": 425, "attack": 66, "defense": 33, "min_realm": 5, "zones": ["haivuc"]},
    {"name": "Hải Xà Song Đầu", "hp": 520, "attack": 78, "defense": 40, "min_realm": 6, "zones": ["haivuc"]},
    {"name": "San Hô Cự Quy", "hp": 650, "attack": 82, "defense": 55, "min_realm": 7, "zones": ["haivuc"]},

    # Demon realm and higher-end regions.
    {"name": "Huyết Nha Dạ Xoa", "hp": 690, "attack": 96, "defense": 46, "min_realm": 7, "zones": ["mavuc"]},
    {"name": "U Minh Quỷ Tướng", "hp": 830, "attack": 112, "defense": 60, "min_realm": 8, "zones": ["mavuc", "vancotlang"]},
    {"name": "Bạch Cốt Cương Thi", "hp": 880, "attack": 118, "defense": 66, "min_realm": 8, "zones": ["vancotlang"]},
    {"name": "Cốt Long Tàn Hồn", "hp": 1120, "attack": 132, "defense": 72, "min_realm": 9, "zones": ["vancotlang"]},
    {"name": "Hư Không Liệt Thú", "hp": 1350, "attack": 148, "defense": 82, "min_realm": 10, "zones": ["hukhong"]},
    {"name": "Tinh Không Thôn Phệ Giả", "hp": 1580, "attack": 165, "defense": 96, "min_realm": 11, "zones": ["hukhong"]},

    # Additional bestiary — tougher regional variants and late-game threats.
    # Hoang Nguyên.
    {"name": "Sa Mạc Độc Hạt", "hp": 78, "attack": 18, "defense": 8, "min_realm": 0, "zones": ["hoangnguyen"]},
    {"name": "Cự Thạch Tích Dịch", "hp": 142, "attack": 29, "defense": 16, "min_realm": 1, "zones": ["hoangnguyen"]},
    {"name": "Hoang Nguyên Lang Vương", "hp": 255, "attack": 41, "defense": 20, "min_realm": 2, "zones": ["hoangnguyen"]},

    # Yêu Thú Sơn Mạch.
    {"name": "Phong Nha Báo", "hp": 178, "attack": 35, "defense": 14, "min_realm": 2, "zones": ["yeuthusonmach"]},
    {"name": "Xích Diệm Hùng", "hp": 305, "attack": 51, "defense": 26, "min_realm": 3, "zones": ["yeuthusonmach"]},
    {"name": "Thiết Giáp Địa Long", "hp": 465, "attack": 67, "defense": 42, "min_realm": 4, "zones": ["yeuthusonmach"]},

    # Cổ Động Phủ.
    {"name": "Âm Khôi Thủ Vệ", "hp": 438, "attack": 62, "defense": 46, "min_realm": 3, "zones": ["dongphu"]},
    {"name": "Kiếm Trủng Oán Linh", "hp": 625, "attack": 82, "defense": 39, "min_realm": 5, "zones": ["dongphu"]},
    {"name": "Thạch Môn Cự Linh", "hp": 805, "attack": 93, "defense": 70, "min_realm": 6, "zones": ["dongphu"]},

    # Hải Vực.
    {"name": "Bích Lân Hải Xà", "hp": 605, "attack": 87, "defense": 48, "min_realm": 5, "zones": ["haivuc"]},
    {"name": "Huyết San Hô Yêu", "hp": 835, "attack": 101, "defense": 70, "min_realm": 7, "zones": ["haivuc"]},
    {"name": "Thâm Uyên Kình Thú", "hp": 1130, "attack": 122, "defense": 85, "min_realm": 8, "zones": ["haivuc"]},

    # Ma Vực.
    {"name": "Hắc Viêm Ma Khuyển", "hp": 925, "attack": 127, "defense": 60, "min_realm": 7, "zones": ["mavuc"]},
    {"name": "Huyết Ngục Tu La", "hp": 1200, "attack": 148, "defense": 78, "min_realm": 9, "zones": ["mavuc"]},
    {"name": "Ma Cốt Chiến Tướng", "hp": 1510, "attack": 167, "defense": 96, "min_realm": 10, "zones": ["mavuc"]},

    # Vạn Cốt Lăng.
    {"name": "U Minh Cốt Tượng", "hp": 1160, "attack": 142, "defense": 91, "min_realm": 8, "zones": ["vancotlang"]},
    {"name": "Cửu U Đăng Quỷ", "hp": 1450, "attack": 159, "defense": 102, "min_realm": 10, "zones": ["vancotlang"]},
    {"name": "Vạn Cốt Long Tướng", "hp": 1830, "attack": 189, "defense": 123, "min_realm": 11, "zones": ["vancotlang"]},

    # Hư Không Cổ Giới — includes dedicated threats for the final realms.
    {"name": "Hư Không Liêm Thú", "hp": 1740, "attack": 188, "defense": 108, "min_realm": 10, "zones": ["hukhong"]},
    {"name": "Tinh Hạch Thôn Phệ Thú", "hp": 2190, "attack": 212, "defense": 129, "min_realm": 12, "zones": ["hukhong"]},
    {"name": "Diệt Giới Tinh Ma", "hp": 2780, "attack": 238, "defense": 151, "min_realm": 13, "zones": ["hukhong"]},
]

BOSS_MONSTERS = [
    {"name": "Sơn Quân", "hp": 650, "attack": 72, "defense": 42, "min_realm": 2, "zones": ["yeuthusonmach"]},
    {"name": "Sơn Mạch Thú Hoàng", "hp": 1050, "attack": 92, "defense": 58, "min_realm": 4, "zones": ["yeuthusonmach"]},
    {"name": "Cổ Mộ Kiếm Linh", "hp": 850, "attack": 78, "defense": 48, "min_realm": 3, "zones": ["dongphu"]},
    {"name": "Hỏa Vân Cự Điểu", "hp": 1150, "attack": 95, "defense": 55, "min_realm": 4, "zones": ["dongphu"]},
    {"name": "Hải Vương", "hp": 1400, "attack": 110, "defense": 70, "min_realm": 5, "zones": ["haivuc"]},
    {"name": "Lôi Hải Giao Hoàng", "hp": 1650, "attack": 125, "defense": 80, "min_realm": 6, "zones": ["haivuc"]},
    {"name": "Bạch Cốt Long", "hp": 1850, "attack": 135, "defense": 85, "min_realm": 7, "zones": ["haivuc", "vancotlang"]},
    {"name": "Huyết Hà Ma Chủ", "hp": 1800, "attack": 135, "defense": 90, "min_realm": 7, "zones": ["mavuc"]},
    {"name": "Ma Tôn Phân Thân", "hp": 2200, "attack": 150, "defense": 100, "min_realm": 8, "zones": ["mavuc"]},
    {"name": "Cốt Long Vương", "hp": 2350, "attack": 155, "defense": 108, "min_realm": 8, "zones": ["vancotlang"]},
    {"name": "Cửu U Quỷ Đế", "hp": 2650, "attack": 165, "defense": 112, "min_realm": 9, "zones": ["vancotlang"]},
    {"name": "Hư Không Cổ Thú", "hp": 3100, "attack": 185, "defense": 125, "min_realm": 10, "zones": ["hukhong"]},
    {"name": "Thiên Ngoại Tà Thần", "hp": 3700, "attack": 205, "defense": 140, "min_realm": 11, "zones": ["hukhong"]},

    # Additional regional bosses for longer exploration progression.
    {"name": "Huyết Hỏa Sơn Chủ", "hp": 1420, "attack": 128, "defense": 78, "min_realm": 5, "zones": ["yeuthusonmach"]},
    {"name": "Thái Hư Kiếm Chủ", "hp": 1880, "attack": 151, "defense": 108, "min_realm": 6, "zones": ["dongphu"]},
    {"name": "Vạn Triều Hải Thần", "hp": 2670, "attack": 180, "defense": 145, "min_realm": 8, "zones": ["haivuc"]},
    {"name": "Vô Tướng Ma Hoàng", "hp": 3020, "attack": 210, "defense": 142, "min_realm": 9, "zones": ["mavuc"]},
    {"name": "Vạn Cốt Ma Long", "hp": 3490, "attack": 231, "defense": 175, "min_realm": 10, "zones": ["vancotlang"]},
    {"name": "Hư Không Chúa Tể", "hp": 4350, "attack": 263, "defense": 196, "min_realm": 12, "zones": ["hukhong"]},
    {"name": "Thiên Ngoại Cổ Thần", "hp": 5250, "attack": 294, "defense": 225, "min_realm": 13, "zones": ["hukhong"]},
]
