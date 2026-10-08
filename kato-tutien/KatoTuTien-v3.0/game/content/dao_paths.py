from __future__ import annotations

DAO_PATHS = {
    "kiem": {"name": "Kiếm Đạo", "emoji": "⚔️", "atk": 1.12, "def": 0.95, "acc": 1.08},
    "dao": {"name": "Đao Đạo", "emoji": "🗡️", "atk": 1.15, "def": 0.92, "acc": 1.02},
    "phap": {"name": "Pháp Đạo", "emoji": "🔮", "atk": 1.08, "def": 0.98, "spirit": 1.15},
    "the": {"name": "Thể Đạo", "emoji": "🛡️", "atk": 0.95, "def": 1.18, "hp": 1.12},
    "ma": {"name": "Ma Đạo", "emoji": "👹", "atk": 1.20, "def": 0.88, "crit": 1.10},
}

DAO_STAGE_NAMES = ("Khí", "Ý", "Thế", "Tâm")
DAO_STAGE_THRESHOLD = 100  # insight per stage
