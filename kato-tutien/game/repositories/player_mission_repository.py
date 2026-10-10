from __future__ import annotations

import time
from game.database.connection import Database


class PlayerMissionRepository:
    """Persistent progress for one-time, daily and weekly player missions."""

    def __init__(self, db: Database):
        self.db = db

    def get(self, user_id: str, mission_id: str, period_key: str) -> dict | None:
        row = self.db.fetchone(
            "SELECT * FROM player_mission_progress WHERE user_id=? AND mission_id=? AND period_key=?",
            (str(user_id), mission_id, period_key),
        )
        return dict(row) if row else None

    def add_progress(self, user_id: str, mission_id: str, period_key: str, amount: int, target: int) -> None:
        now = int(time.time())
        self.db.execute(
            """INSERT INTO player_mission_progress(user_id, mission_id, period_key, progress, claimed, updated_at)
               VALUES(?,?,?,?,0,?)
               ON CONFLICT(user_id, mission_id, period_key) DO UPDATE SET
                   progress=MIN(?, player_mission_progress.progress + excluded.progress),
                   updated_at=excluded.updated_at
               WHERE player_mission_progress.claimed=0 AND player_mission_progress.progress < ?""",
            (str(user_id), mission_id, period_key, min(max(0, int(amount)), target), now, target, target),
        )

    def mark_claimed(self, user_id: str, mission_id: str, period_key: str, target: int) -> bool:
        cursor = self.db.execute(
            """UPDATE player_mission_progress SET claimed=1, updated_at=?
               WHERE user_id=? AND mission_id=? AND period_key=? AND claimed=0 AND progress>=?""",
            (int(time.time()), str(user_id), mission_id, period_key, int(target)),
        )
        return cursor.rowcount == 1
