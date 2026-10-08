from __future__ import annotations

SECT_ROLES = [
    "Tông Chủ",
    "Phó Tông Chủ",
    "Trưởng Lão",
    "Chấp Sự",
    "Nội Môn Đệ Tử",
    "Ngoại Môn Đệ Tử",
    "Tạp Dịch",
]

# permission -> minimum roles that have it
SECT_PERMISSIONS = {
    "sect.invite": {"Tông Chủ", "Phó Tông Chủ", "Trưởng Lão", "Chấp Sự"},
    "sect.accept_application": {"Tông Chủ", "Phó Tông Chủ", "Trưởng Lão"},
    "sect.kick": {"Tông Chủ", "Phó Tông Chủ", "Trưởng Lão"},
    "sect.promote": {"Tông Chủ", "Phó Tông Chủ"},
    "sect.demote": {"Tông Chủ", "Phó Tông Chủ"},
    "sect.manage_treasury": {"Tông Chủ", "Phó Tông Chủ"},
    "sect.manage_facilities": {"Tông Chủ", "Phó Tông Chủ", "Trưởng Lão"},
    "sect.manage_missions": {"Tông Chủ", "Phó Tông Chủ", "Trưởng Lão", "Chấp Sự"},
    "sect.dissolve": {"Tông Chủ"},
}

SECT_MISSIONS = {
    "donate": {"name": "Cúng linh thạch", "target": 500, "reward_contrib": 50},
    "explore": {"name": "Khám phá 3 lần", "target": 3, "reward_contrib": 30},
    "cultivate": {"name": "Tu luyện 10 lần", "target": 10, "reward_contrib": 20},
}

SECT_TOWER = {"max_floor": 50, "base_hp": 100, "hp_scale": 1.15}
