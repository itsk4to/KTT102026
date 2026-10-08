from __future__ import annotations

QUESTS = {
    "mon_no_cua_lao_truong": {
        "name": "Món Nợ Của Lão Trương",
        "npc": "lao_truong",
        "description": "Tìm hiểu chuyện một món đồ bị cướp ở vùng Hoang Nguyên.",
        "min_realm": 0,
        "steps": [
            {"key": "investigate", "label": "Khám phá Hoang Nguyên 2 lần", "kind": "explore_zone", "target": "hoangnguyen", "amount": 2},
            {"key": "find_clue", "label": "Tìm được manh mối", "kind": "discovery", "target": "nguoi_la_bi_mat", "amount": 1},
            {
                "key": "judgement",
                "label": "Quyết định số phận món nợ",
                "choices": [
                    {"id": "return", "label": "🤝 Trả món đồ cho Lão Trương", "effect": {"stones": 600, "fate": 2, "npc_affinity": 6, "flag": "returned_debt"}},
                    {"id": "keep", "label": "💰 Giữ lại một phần", "condition": {"luck": 60}, "effect": {"stones": 1400, "fate": -2, "npc_affinity": -5, "flag": "kept_debt"}},
                    {"id": "investigate", "label": "🕵️ Tiếp tục điều tra kẻ đứng sau", "condition": {"insight": 60}, "effect": {"cultivation": 250, "insight": 2, "npc_affinity": 4, "flag": "investigated_debt", "discover": "ke_ke_sau_mon_no"}},
                ],
            },
        ],
        "reward": {"stones": 1200, "cultivation": 180, "fate": 2, "reputation": 2, "npc_affinity": 2, "title": "Khách Quen Của Lão Trương"},
    },
    "kiem_am_trong_da": {
        "name": "Kiếm Âm Trong Đá",
        "npc": "co_nu",
        "description": "Lần theo kiếm ý cổ xưa trong Cổ Động Phủ.",
        "min_realm": 3,
        "steps": [
            {"key": "enter", "label": "Khám phá Cổ Động Phủ", "kind": "explore_zone", "target": "dongphu", "amount": 1},
            {"key": "discover", "label": "Phát hiện kiếm ý", "kind": "discovery", "target": "dong_phu_kiem_y", "amount": 1},
        ],
        "reward": {"stones": 2500, "cultivation": 400, "insight": 3, "title": "Người Nghe Kiếm"},
    },
}
