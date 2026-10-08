from __future__ import annotations

import time

from game.database.connection import Database


class QuestRepository:
    def __init__(self, db: Database):
        self.db = db

    def active(self, user_id: str) -> list[dict]:
        rows = self.db.fetchall("SELECT * FROM player_quests WHERE user_id=? AND status='active' ORDER BY started_at", (user_id,))
        return [dict(r) for r in rows]

    def get(self, user_id: str, quest_key: str) -> dict | None:
        row = self.db.fetchone("SELECT * FROM player_quests WHERE user_id=? AND quest_key=?", (user_id, quest_key))
        return dict(row) if row else None

    def start(self, user_id: str, quest_key: str) -> None:
        now = int(time.time())
        self.db.execute(
            "INSERT OR REPLACE INTO player_quests(user_id, quest_key, status, step, progress, started_at, completed_at) VALUES(?,?, 'active', 0, 0, ?, 0)",
            (user_id, quest_key, now),
        )

    def update(self, user_id: str, quest_key: str, step: int, progress: int) -> None:
        self.db.execute("UPDATE player_quests SET step=?, progress=? WHERE user_id=? AND quest_key=?", (step, progress, user_id, quest_key))

    def complete(self, user_id: str, quest_key: str) -> None:
        self.db.execute("UPDATE player_quests SET status='completed', completed_at=? WHERE user_id=? AND quest_key=?", (int(time.time()), user_id, quest_key))

    def has_completed(self, user_id: str, quest_key: str) -> bool:
        row = self.db.fetchone("SELECT 1 FROM player_quests WHERE user_id=? AND quest_key=? AND status='completed'", (user_id, quest_key))
        return row is not None
