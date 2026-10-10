"""Repeatable and starter missions with bounded, transparent rewards."""
from __future__ import annotations

MISSIONS: dict[str, dict] = {
    # One-time onboarding tasks. Existing players may also claim these once.
    "starter_cultivate": {
        "group": "starter", "name": "Lần đầu tĩnh tu", "description": "Thực hiện tu luyện một lần.",
        "action": "cultivate", "target": 1, "stones": 300, "cultivation": 100,
    },
    "starter_explore": {
        "group": "starter", "name": "Bước chân đầu tiên", "description": "Khám phá thế giới một lần.",
        "action": "explore", "target": 1, "stones": 400, "cultivation": 120,
    },
    "starter_purchase": {
        "group": "starter", "name": "Ghé Tiên Phường", "description": "Mua một giao dịch vật phẩm bất kỳ.",
        "action": "purchase", "target": 1, "stones": 250, "cultivation": 50,
    },
    # Daily missions reset at midnight in Asia/Ho_Chi_Minh.
    "daily_cultivate": {
        "group": "daily", "name": "Tĩnh tu hằng ngày", "description": "Tu luyện thành công 3 lần.",
        "action": "cultivate", "target": 3, "stones": 700, "cultivation": 100,
    },
    "daily_explore": {
        "group": "daily", "name": "Dạo bước tìm duyên", "description": "Khởi hành khám phá 3 lần.",
        "action": "explore", "target": 3, "stones": 900, "cultivation": 150,
    },
    "daily_purchase": {
        "group": "daily", "name": "Chuẩn bị hành trang", "description": "Hoàn tất 1 giao dịch tại Tiên Phường.",
        "action": "purchase", "target": 1, "stones": 500, "cultivation": 75,
    },
    # Weekly missions are larger goals, not repeatable farming exploits.
    "weekly_cultivate": {
        "group": "weekly", "name": "Bền chí tu hành", "description": "Tu luyện thành công 10 lần trong tuần.",
        "action": "cultivate", "target": 10, "stones": 2500, "cultivation": 350,
    },
    "weekly_explore": {
        "group": "weekly", "name": "Lữ hành vạn dặm", "description": "Khởi hành khám phá 10 lần trong tuần.",
        "action": "explore", "target": 10, "stones": 3000, "cultivation": 450,
    },
    "weekly_purchase": {
        "group": "weekly", "name": "Nhà hành trang", "description": "Hoàn tất 5 giao dịch tại Tiên Phường trong tuần.",
        "action": "purchase", "target": 5, "stones": 2000, "cultivation": 300,
    },
}

GROUP_LABELS = {"starter": "🌱 Khởi hành", "daily": "☀️ Nhiệm vụ ngày", "weekly": "📅 Nhiệm vụ tuần"}
