from __future__ import annotations

EXPLORE_ZONES = {
    "hoangnguyen": {
        "name": "Hoang Nguyên", "min_realm": 0, "path": "both", "enabled": True,
        "description": "Đồng hoang sơ khai, yêu thú yếu.",
    },
    "yeuthusonmach": {
        "name": "Yêu Thú Sơn Mạch", "min_realm": 1, "path": "both", "enabled": True,
        "description": "Núi rừng đầy yêu thú.",
    },
    "dongphu": {
        "name": "Cổ Động Phủ", "min_realm": 3, "path": "tien", "enabled": True,
        "description": "Di tích cổ, cơ duyên và nguy hiểm.",
    },
    "haivuc": {
        "name": "Hải Vực", "min_realm": 5, "path": "both", "enabled": True,
        "description": "Biển sâu, thủy tộc và bảo vật.",
    },
    "mavuc": {
        "name": "Ma Vực", "min_realm": 7, "path": "ma", "enabled": True,
        "description": "Vùng đất ma khí nồng đậm.",
    },
}

WORLD_REGIONS = {
    "pham_gioi": ["hoangnguyen", "yeuthusonmach", "dongphu"],
    "hai_vuc": ["haivuc"],
    "ma_vuc": ["mavuc"],
}
