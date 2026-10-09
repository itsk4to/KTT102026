"""Static content for the timed Secret Realm cultivation loop."""
from __future__ import annotations

SECRET_REALMS: dict[str, dict] = {
    "thanh_van": {
        "key": "thanh_van",
        "name": "Bí Cảnh Thanh Vân",
        "emoji": "🌿",
        "min_realm": 1,
        "stones": (300, 600),
        "cultivation": (100, 200),
        "description": "Linh khí ôn hòa, thích hợp củng cố căn cơ và tích lũy tài nguyên.",
        "style": "Cân bằng",
    },
    "linh_thach": {
        "key": "linh_thach",
        "name": "Bí Cảnh Linh Thạch",
        "emoji": "💎",
        "min_realm": 2,
        "stones": (800, 1400),
        "cultivation": (200, 350),
        "description": "Mạch khoáng cổ đại dồi dào, thiên về linh thạch.",
        "style": "Thiên về linh thạch",
    },
    "loi_kiep": {
        "key": "loi_kiep",
        "name": "Bí Cảnh Lôi Kiếp",
        "emoji": "⚡",
        "min_realm": 3,
        "stones": (500, 1000),
        "cultivation": (500, 900),
        "description": "Lôi linh rèn luyện đạo tâm, thiên về tích lũy tu vi.",
        "style": "Thiên về tu vi",
    },
    "cam_dia": {
        "key": "cam_dia",
        "name": "Bí Cảnh Cấm Địa",
        "emoji": "🌑",
        "min_realm": 4,
        "stones": (1500, 3000),
        "cultivation": (900, 1600),
        "description": "Cấm địa nguy hiểm, linh lực dồi dào chỉ mở với người có cảnh giới cao.",
        "style": "Cấp cao",
    },
}

SECRET_REALM_CYCLE_SECONDS = 3 * 60 * 60
